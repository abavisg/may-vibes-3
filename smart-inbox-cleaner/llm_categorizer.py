import logging
import ollama
import json
from typing import Dict, Any, List, Optional, Callable

# Import category constants from the rule-based categorizer
# Using direct import as script is run directly via streamlit
from categorizer import (
    CAT_ACTION, CAT_READ, CAT_EVENTS, CAT_INFO, CAT_UNCATEGORISED,
    RULE_CATEGORIES
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Combine all possible categories for the LLM prompt
ALL_CATEGORIES = RULE_CATEGORIES + [CAT_UNCATEGORISED]
VALID_CATEGORY_SET = set(ALL_CATEGORIES)

DEFAULT_MODEL = "llama3" # Default model to use if not specified

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
    stop_checker: Optional[Callable[[], bool]] = None,
    limit: Optional[int] = None
) -> Optional[List[Dict[str, Any]]]:
    """Adds a 'category' key to each email dictionary using an LLM.
    
    Optionally processes only the first `limit` emails.
    Checks a `stop_checker` function before processing each email.
    Returns `None` if the process was stopped early via the checker.
    
    Args:
        emails: List of email dictionaries.
        model_name: Name of the Ollama model to use.
        progress_callback: Optional function for progress updates.
        stop_checker: Optional function that returns True if processing should stop.
        limit: Optional integer to process only the first N emails.
    """
    if not emails:
        return []
    
    # Determine the list of emails to process based on the limit
    emails_to_process = emails[:limit] if limit is not None and limit > 0 else emails
    total_to_process = len(emails_to_process)
    
    if total_to_process == 0:
        logging.info("No emails to process after applying limit.")
        return emails # Return original list unmodified
        
    logging.info(f"Starting LLM categorization for {total_to_process} emails (Limit: {limit}) using model '{model_name}'.")
    
    try:
         ollama.ps()
         logging.info("Ollama server detected.")
    except Exception as e:
         logging.error(f"Ollama server not reachable: {e}. Cannot perform LLM categorization.")
         # Apply Uncategorised only to the emails we intended to process
         for i, email in enumerate(emails):
              if limit is None or i < limit:
                   email['category'] = CAT_UNCATEGORISED
              # Keep original category for emails beyond the limit
         return emails 

    processed_count = 0
    # Iterate only through the emails_to_process list
    for i, email in enumerate(emails_to_process):
        # --- Check for stop signal --- 
        if stop_checker and stop_checker():
             logging.warning(f"Stop requested after processing {processed_count} emails, halting LLM categorization.")
             # Return the *original* full list, as changes are partial and shouldn't be saved
             # Or should we return the partially modified list? Returning None signals stop.
             return None # Signal that process was stopped
             
        uid = email.get('uid', 'N/A')
        email['category'] = categorize_email_llm(email, model_name)
        processed_count += 1
        
        if progress_callback:
            try:
                # Report progress based on total_to_process
                progress_callback(processed_count, total_to_process)
            except Exception as cb_err:
                 logging.error(f"Error in progress callback: {cb_err}")
        
    logging.info(f"Finished LLM categorization for {processed_count}/{total_to_process} emails.")
    # Return the original list with modifications applied to the processed slice
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
        
    print("--- Testing LLM Categorizer with Limit --- ")
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
    test_limit = 2 # Test limiting to first 2 emails
    print(f"Testing with model: {model_to_test}, Limit: {test_limit}")
    
    # Create a fresh copy for testing
    emails_copy = [e.copy() for e in test_emails]

    # Pass the limit
    categorized_results = categorize_emails_llm(
        emails_copy, 
        model_name=model_to_test, 
        limit=test_limit
    )
    
    if categorized_results is None:
         print("\n--- Categorization Result: Error or Stop? (Should not happen in limit test) ---")
    else:
        print("\n--- Categorization Results (Completed with Limit) ---")
        for email in categorized_results:
            # Note: Emails beyond the limit will retain original/no category
            print(f"UID: {email['uid']}, Subject: \"{email['subject']}\", Category: {email.get('category', 'Not Processed')}")

    print("\n--- Finished Test --- ") 