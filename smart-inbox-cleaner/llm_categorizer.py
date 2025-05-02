import logging
import ollama
import json
import os  # Added
from dotenv import load_dotenv  # Added
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime # Added

# Import category constants from the rule-based categorizer
# Using direct import as script is run directly via streamlit
from categorizer import (
    CAT_ACTION, CAT_READ, CAT_EVENTS, CAT_INFO, CAT_UNCATEGORISED,
    RULE_CATEGORIES
)

# --- Load environment variables ---
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Combine all possible categories for the LLM prompt
ALL_CATEGORIES = RULE_CATEGORIES + [CAT_UNCATEGORISED]
VALID_CATEGORY_SET = set(ALL_CATEGORIES)

DEFAULT_MODEL = "llama3" # Default model to use if not specified

# --- Helper to safely parse date for sorting ---
def safe_parse_date(date_input: Optional[Any]) -> datetime:
    """Handles datetime objects, strings, or None, returns epoch on failure."""
    if isinstance(date_input, datetime):
        return date_input # Already a datetime object
    
    if date_input is None:
        logging.debug("Date input is None, using epoch for sorting.")
        return datetime.min # Assign oldest possible time if None
        
    if isinstance(date_input, str):
        try:
            # Try parsing string as ISO format
            return datetime.fromisoformat(date_input)
        except ValueError:
            # Add more string formats here if needed (e.g., using email.utils.parsedate_to_datetime)
            logging.warning(f"Could not parse date string '{date_input}' using isoformat. Using epoch for sorting.")
            return datetime.min # Fallback to epoch for unparsed strings
        except Exception as e:
            logging.error(f"Unexpected error parsing date string '{date_input}': {e}. Using epoch.")
            return datetime.min
    else:
        # Handle other unexpected types
        logging.error(f"Unexpected type for date input: {type(date_input)}. Value: '{date_input}'. Using epoch.")
        return datetime.min

def format_llm_prompt(email_data: Dict[str, Any]) -> str:
    """Formats the prompt for the LLM based on email data."""
    subject = email_data.get('subject', 'No Subject')
    sender = email_data.get('from', 'Unknown Sender')
    
    # Basic prompt structure - can be refined significantly
    prompt = f"""Analyze the following email metadata and classify it into ONE of the following categories based on GTD principles:
{', '.join(ALL_CATEGORIES)}

Category Meanings:
- {CAT_ACTION}: Requires a specific action or response from me.
- {CAT_READ}: Informational content like newsletters, articles, updates that I should read when I have time.
- {CAT_EVENTS}: Relates to a specific invitation to an event, meeting, or calendar item (invitations, updates, reminders). It needs to be an event that I have responded YES.
- {CAT_INFO}: Purely informational updates like notifications, confirmations, alerts (often automated).
- {CAT_UNCATEGORISED}: Does not clearly fit into the other categories or requires manual review.

Email Metadata:
Subject: {subject}
From: {sender}

Output ONLY the single category name from the list above that best fits this email.
Category:"""
    return prompt

def parse_llm_response(response_text: str) -> str:
    """Parses the LLM response to extract a valid category."""
    # Simple parsing: assumes the model outputs the category name directly.
    cleaned_response = response_text.strip().replace("\"", "") # Remove leading/trailing spaces and quotes
    logging.debug(f"Parsing LLM response. Original: '{response_text}', Cleaned: '{cleaned_response}'")
    
    if cleaned_response in VALID_CATEGORY_SET:
        return cleaned_response
    
    for category in ALL_CATEGORIES:
        # Check if the cleaned response contains a category name (case-insensitive)
        # Be careful with substring matching (e.g., "Action Required" vs "Action")
        if category.lower() == cleaned_response.lower(): # Prefer exact case-insensitive match
            return category
        # Optional: Add more robust fuzzy matching if needed

    logging.warning(f"LLM response '{response_text}' did not match valid categories. Defaulting to {CAT_UNCATEGORISED}.")
    return CAT_UNCATEGORISED

def categorize_email_llm(email_data: Dict[str, Any], model_name: str = DEFAULT_MODEL) -> str:
    """Categorizes a single email using the specified Ollama LLM model."""
    prompt = format_llm_prompt(email_data)
    category = CAT_UNCATEGORISED
    
    try:
        logging.debug(f"Sending prompt to Ollama model '{model_name}':\n------PROMPT START------\n{prompt}\n------PROMPT END------")
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}]
        )
        response_content = response['message']['content']
        logging.debug(f"Raw response from Ollama model '{model_name}': {response_content}")
        category = parse_llm_response(response_content)
    except ollama.ResponseError as e:
         if hasattr(e, 'error') and isinstance(e.error, str) and "model not found" in e.error.lower():
              logging.error(f"Ollama model '{model_name}' not found. Pull it using `ollama pull {model_name}`")
         else:
             logging.error(f"Ollama API response error (Model: '{model_name}'): {e}")
             if hasattr(e, 'status_code'):
                  logging.error(f"Status code: {e.status_code}")
    except Exception as e:
        logging.error(f"Error during LLM categorization (Model: '{model_name}'): {e}", exc_info=True)
    return category

def categorize_emails_llm(
    emails: List[Dict[str, Any]], 
    model_name: str = DEFAULT_MODEL, 
    progress_callback: Optional[Callable[[int, int], None]] = None,
    stop_checker: Optional[Callable[[], bool]] = None
) -> Optional[List[Dict[str, Any]]]:
    """Adds a 'category' key to each email dictionary using an LLM.
    
    Sorts emails by date (newest first) before applying the limit from the
    LLM_CATEGORIZATION_LIMIT environment variable (0 means no limit).
    Checks a `stop_checker` function before processing each email.
    Returns `None` if the process was stopped early via the checker.
    
    Args:
        emails: List of email dictionaries (original order is preserved).
        model_name: Name of the Ollama model to use.
        progress_callback: Optional function for progress updates.
        stop_checker: Optional function that returns True if processing should stop.
    """
    if not emails:
        return []

    # --- Read limit from environment variable ---
    limit_str = os.environ.get('LLM_CATEGORIZATION_LIMIT', '0')
    try:
        limit = int(limit_str)
        if limit < 0:
             logging.warning(f"Invalid negative LLM_CATEGORIZATION_LIMIT ('{limit_str}'). Setting limit to 0 (no limit).")
             limit = 0 # Treat negative as no limit
    except ValueError:
        logging.warning(f"Invalid LLM_CATEGORIZATION_LIMIT ('{limit_str}'). Must be an integer. Setting limit to 0 (no limit).")
        limit = 0 # Default to no limit if not a valid integer

    # --- Sort emails by date (newest first) BEFORE applying limit ---
    try:
        # Use a stable sort based on parsed date, newest first
        # This creates a new sorted list of references
        sorted_email_refs = sorted(emails, key=lambda e: safe_parse_date(e.get('date')), reverse=True)
        logging.info("Successfully sorted emails by date for processing.")
    except Exception as sort_err:
        logging.error(f"Error sorting emails by date: {sort_err}. Processing in original fetch order.", exc_info=True)
        sorted_email_refs = emails # Fallback to original order if sorting fails
        
    # --- Determine the list of emails to process based on the limit applied to the SORTED list ---
    emails_to_process = sorted_email_refs[:limit] if limit > 0 else sorted_email_refs
    total_to_process = len(emails_to_process)
    
    if total_to_process == 0:
        # This case should ideally not happen if limit > 0 and emails exist, but handle it.
        logging.info("No emails selected for processing after sorting and applying limit.")
        return emails # Return original list unmodified

    limit_info = f"Limit: {limit} (from env, applied to newest)" if limit > 0 else "Limit: None (processing all)"
    logging.info(f"Starting LLM categorization for {total_to_process} emails ({limit_info}) using model '{model_name}'.")
    
    try:
         ollama.ps()
         logging.info("Ollama server detected.")
    except Exception as e:
         logging.error(f"Ollama server not reachable: {e}. Cannot perform LLM categorization.")
         # Apply Uncategorised only to the emails we intended to process
         # Need to iterate through emails_to_process refs here
         for email_ref in emails_to_process:
              email_ref['category'] = CAT_UNCATEGORISED
         return emails # Return original list with defaults applied to target emails

    processed_count = 0
    # --- Iterate only through the emails selected for processing (sorted newest first if applicable) ---
    for email in emails_to_process: # These are references to dicts in the original 'emails' list
        # --- Check for stop signal --- 
        if stop_checker and stop_checker():
             logging.warning(f"Stop requested after processing {processed_count} emails, halting LLM categorization.")
             # Return original list - changes are partial. None signals stop.
             return None 
             
        uid = email.get('uid', 'N/A')
        # --- Apply category TO THE ORIGINAL EMAIL DICT via the reference --- 
        email['category'] = categorize_email_llm(email, model_name)
        processed_count += 1
        
        if progress_callback:
            try:
                # Report progress based on total_to_process
                progress_callback(processed_count, total_to_process)
            except Exception as cb_err:
                 logging.error(f"Error in progress callback: {cb_err}")
        
    logging.info(f"Finished LLM categorization for {processed_count}/{total_to_process} emails.")
    # Return the original list reference. 
    # The category has been updated in the dictionaries referenced by emails_to_process.
    return emails 

# Example usage
if __name__ == '__main__':
    # Define a simple progress printer for testing
    def print_progress(current, total):
         print(f"  Progress: {current}/{total}")
         
    # --- Add stop checker simulation for testing ---
    stop_after_n = 2 # Simulate stopping after N emails
    emails_processed_count = 0
    def test_stop_checker():
        global emails_processed_count # Use global or pass as arg if needed, here global for simplicity
        emails_processed_count += 1 
        if emails_processed_count > stop_after_n:
            print(f"--- TEST STOP CHECKER RETURNING TRUE (Processed count: {emails_processed_count}) ---")
            return True
        return False
        
    print("--- Testing LLM Categorizer (Limit from .env) --- ")
    # Ensure Ollama server is running and the model is pulled (e.g., `ollama pull llama3`)
    
    test_emails = [
        {
            'uid': 1,
            'subject': "Action Required: Submit timesheet by Friday",
            'from': "hr@example.com"
        },
        {
            'uid': 2,
            'subject': "Invitation: Project Kick-off @ Tue May 7, 2024 10am - 11am (PDT)",
            'from': "calendar-notification@google.com"
        },
        {
            'uid': 3,
             'subject': "Tech Newsletter - Issue #123",
             'from': "newsletter@techreads.com"
        },
        {
            'uid': 4,
             'subject': "!!! URGENT WINNER NOTIFICATION !!!",
             'from': "lottery@spam.info"
        }
    ]

    model_to_test = DEFAULT_MODEL
    # test_limit removed - limit is read from .env inside the function
    print(f"Testing with model: {model_to_test}. Limit will be read from .env")
    
    # Create a fresh copy for testing
    emails_copy = [e.copy() for e in test_emails]

    # limit argument removed from the call
    categorized_results = categorize_emails_llm(
        emails_copy, 
        model_name=model_to_test
        # Removed: limit=test_limit 
    )
    
    if categorized_results is None:
         print("\n--- Categorization Result: Error or Stop? ---")
    else:
        print("\n--- Categorization Results (Completed with Limit from .env) ---")
        for email in categorized_results:
            # Note: Emails beyond the limit (if any) will retain original/no category
            print(f"UID: {email['uid']}, Subject: \"{email['subject']}\", Category: {email.get('category', 'Not Processed')}")

    print("\n--- Finished Test --- ") 