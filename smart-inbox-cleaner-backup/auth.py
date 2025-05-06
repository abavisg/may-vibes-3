import os
import json
import logging # Use logging instead of print for status/errors
from typing import Tuple, Optional, List # For type hinting

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants ---
# Determine the script's directory and the project root relative to it
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # Assumes script is in smart-inbox-cleaner directory
GMAIL_OAUTH_DIR = os.path.join(PROJECT_ROOT, 'gmail-oauth')

CLIENT_SECRETS_PATH = os.path.join(GMAIL_OAUTH_DIR, 'client_secret.json')
TOKEN_PATH = os.path.join(GMAIL_OAUTH_DIR, 'token.json')

# Scopes define the level of access requested.
SCOPES: List[str] = [
    'https://mail.google.com/',      # Gmail access
    'openid',                      # Standard OIDC scope
    'https://www.googleapis.com/auth/userinfo.email', # Get user's email address
    'https://www.googleapis.com/auth/userinfo.profile' # Get user's basic profile info
]

# --- Functions ---

def get_credentials() -> Tuple[Optional[Credentials], Optional[str]]:
    """Gets user credentials and email for Google API access.

    Handles the OAuth 2.0 flow: loads existing token, refreshes if needed,
    or runs the full auth flow. Also fetches the user's email via People API.

    Returns:
        Tuple containing the Credentials object and user email string, 
        or (None, None) if authentication fails.
    """
    creds: Optional[Credentials] = None

    # Ensure token directory exists
    if not os.path.exists(GMAIL_OAUTH_DIR):
         try:
             os.makedirs(GMAIL_OAUTH_DIR, exist_ok=True)
         except OSError as e:
             logging.error(f"Error creating directory {GMAIL_OAUTH_DIR}: {e}")
             return None, None

    # Load token if it exists
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            logging.info(f"Loaded credentials from {TOKEN_PATH}")
        except json.JSONDecodeError:
            logging.error(f"Error reading token file: {TOKEN_PATH}. Deleting and re-authenticating.")
            os.remove(TOKEN_PATH) # Delete corrupted token file
            creds = None
        except ValueError as e:
             logging.error(f"Error loading credentials from token file: {e}. Deleting and re-authenticating.")
             os.remove(TOKEN_PATH)
             creds = None
        except Exception as e: # Catch other potential file errors
            logging.error(f"Unexpected error loading token file {TOKEN_PATH}: {e}")
            creds = None

    # If no valid credentials, attempt refresh or run full flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logging.info("Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                logging.info("Credentials refreshed.")
                # Save the refreshed credentials
                with open(TOKEN_PATH, 'w') as token_file:
                    token_file.write(creds.to_json())
                logging.info(f"Refreshed credentials saved to {TOKEN_PATH}")
            except Exception as e:
                logging.error(f"Error refreshing token: {e}")
                if os.path.exists(TOKEN_PATH):
                    try:
                        os.remove(TOKEN_PATH)
                    except OSError as del_e:
                         logging.error(f"Error deleting token file after refresh failure: {del_e}")
                logging.warning("Could not refresh token. Please re-authenticate.")
                creds = None # Force re-authentication

        # Run full auth flow if still no valid creds
        if not creds or not creds.valid:
            logging.info("No valid credentials found or refresh failed, initiating OAuth flow...")
            if not os.path.exists(CLIENT_SECRETS_PATH):
                logging.error(f"CRITICAL: Client secrets file not found at {CLIENT_SECRETS_PATH}")
                logging.error("Please download from Google Cloud Console -> Credentials -> OAuth 2.0 Client IDs")
                logging.error(f"Place it in the '{os.path.basename(GMAIL_OAUTH_DIR)}' folder next to the '{os.path.basename(SCRIPT_DIR)}' directory.")
                return None, None
            
            logging.info(f"Using client secrets file: {CLIENT_SECRETS_PATH}")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRETS_PATH, SCOPES
                )
                creds = flow.run_local_server(
                    port=0,
                    prompt='consent',
                    authorization_prompt_message="Please authorize Smart Inbox Cleaner in the browser:\n{url}",
                    success_message="Authentication successful! You can close the browser tab.",
                    open_browser=True
                    )
                logging.info("OAuth flow completed.")
            except FileNotFoundError: # Should be caught above, but belt-and-suspenders
                 logging.error(f"Error during OAuth: Client secrets file not found at {CLIENT_SECRETS_PATH}")
                 return None, None
            except Exception as e:
                logging.error(f"An error occurred during the OAuth flow: {e}", exc_info=True)
                return None, None

            # Save the new credentials
            if creds:
                try:
                    with open(TOKEN_PATH, 'w') as token_file:
                        token_file.write(creds.to_json())
                    logging.info(f"Credentials saved to {TOKEN_PATH}")
                except Exception as e:
                     logging.error(f"Error saving token: {e}")
                     # Decide if this is fatal? If token not saved, next run fails.
                     # For now, proceed but log error.

    # Final check if we have credentials
    if not creds or not creds.valid:
         logging.error("Failed to obtain valid credentials after completing authentication steps.")
         return None, None

    logging.info("Credentials obtained successfully.")

    # --- Fetch User Email using People API ---
    user_email: Optional[str] = None
    try:
        logging.info("Fetching user email using People API...")
        # Use discovery cache to potentially speed up subsequent runs
        # Consider adding `cache_discovery=False` if API definition changes often
        service = build('people', 'v1', credentials=creds, cache_discovery=True)
        profile = service.people().get(
            resourceName='people/me',
            personFields='emailAddresses' # Request only email addresses
        ).execute()
        
        emails = profile.get('emailAddresses')
        if emails:
            # Find the primary email address
            for email_entry in emails:
                if email_entry.get('metadata', {}).get('primary'):
                    user_email = email_entry.get('value')
                    break
            # If no primary found, fallback to the first email in the list
            if not user_email:
                 user_email = emails[0].get('value')
            
            if user_email:
                 logging.info(f"Successfully fetched email: {user_email}")
            else:
                 logging.warning("Found email entries but couldn't extract an email address value.")
        else:
            logging.warning("Could not find email address field in People API response.")

    except HttpError as err:
        logging.error(f"An HTTP error occurred calling People API: {err}")
        # Check for common permission errors
        if err.resp.status == 403:
             logging.error("Permission denied for People API. Ensure it's enabled in Google Cloud Console.")
    except Exception as e:
        logging.error(f"An unexpected error occurred fetching email via People API: {e}", exc_info=True)

    if not user_email:
         logging.warning("Could not determine user email. IMAP connection might fail or use incorrect user.")
         # Return credentials but no email, let caller handle?
         # For now, returning None email as per function signature.
    
    return creds, user_email

if __name__ == '__main__':
    # Example usage: Try to get credentials when the script is run directly
    print("--- Running auth.py directly for testing ---")
    logging.info("Attempting to get Google credentials...")
    
    credentials, email = get_credentials()
    
    if credentials and email:
        logging.info(f"Successfully obtained credentials for user: {email}")
        logging.info(f"Token valid: {credentials.valid}")
        logging.info(f"Refresh token present: {'Yes' if credentials.refresh_token else 'No'}")
    elif credentials:
        logging.warning("Successfully obtained credentials, but failed to get email address.")
    else:
        logging.error("Failed to get credentials.")
    print("--- Finished auth.py test run ---") 