import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# --- Constants ---
# Path to the client secrets JSON file downloaded from Google Cloud Console
# Assumes auth.py is in smart-inbox-cleaner, and gmail-oauth is at the root
CLIENT_SECRETS_PATH = os.path.join('..', 'gmail-oauth', 'client_secret.json')
# Path to store the user's refresh token
TOKEN_PATH = os.path.join('..', 'gmail-oauth', 'token.json')
# Scopes define the level of access requested. For IMAP/Gmail, use mail.google.com
SCOPES = ['https://mail.google.com/']
# Redirect URI configured in Google Cloud Console (often http://localhost:port for desktop apps)
# This needs to match exactly what you set up in your credentials.
# The port number will be assigned automatically by InstalledAppFlow if not set here.
REDIRECT_URI = 'http://localhost:8080' # Example, adjust if needed

# --- Functions ---

def get_credentials():
    """Gets user credentials for Google API access.

    Handles the OAuth 2.0 flow, including storing/refreshing tokens.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    token_dir = os.path.dirname(TOKEN_PATH)
    if not os.path.exists(token_dir):
         os.makedirs(token_dir, exist_ok=True) # Ensure directory exists before checking file

    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            print(f"Loaded credentials from {TOKEN_PATH}")
        except json.JSONDecodeError:
            print(f"Error reading token file: {TOKEN_PATH}. Deleting and re-authenticating.")
            os.remove(TOKEN_PATH) # Delete corrupted token file
            creds = None
        except ValueError as e:
             # Handle cases where the token file is valid JSON but doesn't contain expected fields
             print(f"Error loading credentials from token file: {e}. Deleting and re-authenticating.")
             os.remove(TOKEN_PATH)
             creds = None


    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing expired credentials...")
                creds.refresh(Request())
                print("Credentials refreshed.")
                # Save the refreshed credentials
                with open(TOKEN_PATH, 'w') as token_file:
                    token_file.write(creds.to_json())
                print(f"Refreshed credentials saved to {TOKEN_PATH}")
            except Exception as e:
                print(f"Error refreshing token: {e}")
                # If refresh fails, delete the token file and force re-login
                if os.path.exists(TOKEN_PATH):
                    os.remove(TOKEN_PATH)
                print("Could not refresh token. Please re-authenticate.")
                creds = None # Ensure we proceed to re-authentication

        # Only initiate the flow if we don't have valid or refreshed creds
        if not creds or not creds.valid:
            print("No valid credentials found or refresh failed, initiating OAuth flow...")
            client_secrets_abs_path = os.path.abspath(CLIENT_SECRETS_PATH)
            print(f"Looking for client secrets file at: {client_secrets_abs_path}")
            if not os.path.exists(CLIENT_SECRETS_PATH):
                # Try absolute path as fallback if relative path failed
                 if not os.path.exists(client_secrets_abs_path):
                     print(f"Error: Client secrets file not found at relative path {CLIENT_SECRETS_PATH} or absolute path {client_secrets_abs_path}")
                     print("Please download it from Google Cloud Console and place it correctly in the 'gmail-oauth' folder.")
                     return None # Cannot proceed without client secrets
                 else:
                    secrets_path_to_use = client_secrets_abs_path
            else:
                 secrets_path_to_use = CLIENT_SECRETS_PATH

            print(f"Using client secrets file: {secrets_path_to_use}")
            try:
                # Use redirect_uri only if it's configured in your client secrets JSON
                # If your client secrets file uses "urn:ietf:wg:oauth:2.0:oob" or similar,
                # you might not need to specify launch_browser=False or redirect_uri.
                # Check your client_secret.json configuration.
                flow = InstalledAppFlow.from_client_secrets_file(
                    secrets_path_to_use, SCOPES # redirect_uri=REDIRECT_URI # Add if needed
                )

                # Run local server flow, this will attempt to open a browser
                # For environments without a browser, consider device flow or manual copy/paste
                # Using port=0 finds an available port automatically. The server will print the URL.
                creds = flow.run_local_server(
                    port=0,
                    prompt='consent', # Force consent screen every time initially
                    authorization_prompt_message="Please authorize Smart Inbox Cleaner:\n{url}",
                    success_message="Authentication successful! You can close this tab.",
                    open_browser=True # Default is True
                    )
                print("OAuth flow completed.")
            except FileNotFoundError:
                 print(f"Error during OAuth: Client secrets file not found at {secrets_path_to_use}")
                 return None
            except Exception as e:
                print(f"An error occurred during the OAuth flow: {e}")
                # Specific handling for common errors like misconfigured redirect URI might be needed
                return None


        # Save the credentials for the next run
        if creds:
            try:
                # Ensure the directory exists (redundant check, but safe)
                os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
                with open(TOKEN_PATH, 'w') as token_file:
                    token_file.write(creds.to_json())
                print(f"Credentials saved to {TOKEN_PATH}")
            except Exception as e:
                 print(f"Error saving token: {e}")


    if not creds or not creds.valid:
         print("Failed to obtain valid credentials after OAuth flow.")
         return None

    print("Credentials obtained successfully.")
    return creds

if __name__ == '__main__':
    # Example usage: Try to get credentials when the script is run directly
    print("Attempting to get Google credentials...")
    # Ensure relative paths work correctly when running directly from smart-inbox-cleaner dir
    # Adjust CWD temporarily if needed, or rely on absolute paths internally
    # For now, assuming script is run from project root or handles paths correctly.
    credentials = get_credentials()
    if credentials:
        print("Successfully obtained credentials.")
        # You could potentially print the access token expiry here for info
        # print(f"Access token expires at: {credentials.expiry}")
        # Test token validity (optional)
        # print(f"Token valid: {credentials.valid}")
        # print(f"Refresh token present: {'Yes' if credentials.refresh_token else 'No'}")
    else:
        print("Failed to get credentials.") 