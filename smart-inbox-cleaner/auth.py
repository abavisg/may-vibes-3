import os
import json
import logging
from typing import Tuple, Optional, List
import platform
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants ---
def get_app_data_dir() -> str:
    """Get the appropriate application data directory for the current platform."""
    system = platform.system()
    if system == 'Darwin':  # macOS
        return os.path.expanduser('~/Library/Application Support/Smart Inbox Cleaner')
    elif system == 'Windows':
        return os.path.join(os.environ.get('APPDATA', ''), 'Smart Inbox Cleaner')
    else:  # Linux and others
        return os.path.expanduser('~/.config/smart-inbox-cleaner')

# Set up paths for OAuth credentials
APP_DATA_DIR = get_app_data_dir()
GMAIL_OAUTH_DIR = os.path.join(APP_DATA_DIR, 'gmail-oauth')
TOKEN_PATH = os.path.join(GMAIL_OAUTH_DIR, 'token.json')

# OAuth 2.0 client configuration
CLIENT_CONFIG = {
    "installed": {
        "client_id": "712053337554-hbrf45h3h2bsmga1up7jtedpjtqbr2u2.apps.googleusercontent.com",
        "project_id": "smart-inbox-cleaner",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",  # Need a more secure solution as this identifies the google cloud console app
        "redirect_uris": ["http://localhost"]
    }
}

# Scopes define the level of access requested.
SCOPES = [
    'https://mail.google.com/',      # Gmail access
    'openid',                      # Standard OIDC scope
    'https://www.googleapis.com/auth/userinfo.email', # Get user's email address
    'https://www.googleapis.com/auth/userinfo.profile' # Get user's basic profile info
]

def get_credentials() -> Tuple[Optional[Credentials], Optional[str]]:
    """Gets user credentials and email for Google API access."""
    creds = None

    # Ensure token directory exists
    try:
        os.makedirs(GMAIL_OAUTH_DIR, exist_ok=True)
    except OSError as e:
        logging.error(f"Error creating directory {GMAIL_OAUTH_DIR}: {e}")
        return None, None

    # Load token if it exists
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            logging.error(f"Error loading token: {e}")
            if os.path.exists(TOKEN_PATH):
                os.remove(TOKEN_PATH)
            creds = None

    # If no valid credentials, attempt refresh or run full flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logging.error(f"Error refreshing token: {e}")
                creds = None

        # Run full auth flow if still no valid creds
        if not creds or not creds.valid:
            try:
                flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
                creds = flow.run_local_server(port=0)
                
                # Save the credentials
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logging.error(f"Error during OAuth flow: {e}")
                return None, None

    # Get user email
    user_email = None
    if creds and creds.valid:
        try:
            service = build('people', 'v1', credentials=creds)
            profile = service.people().get(
                resourceName='people/me',
                personFields='emailAddresses'
            ).execute()
            
            emails = profile.get('emailAddresses', [])
            for email in emails:
                if email.get('metadata', {}).get('primary'):
                    user_email = email.get('value')
                    break
            if not user_email and emails:
                user_email = emails[0].get('value')
        except Exception as e:
            logging.error(f"Error fetching user email: {e}")
    
    return creds, user_email