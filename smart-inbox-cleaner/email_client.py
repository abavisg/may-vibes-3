import logging
from typing import Tuple, Optional
from imapclient import IMAPClient
from imapclient.exceptions import LoginError # More specific error
from auth import get_credentials

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Google's IMAP host
IMAP_HOST = 'imap.gmail.com'

def connect_oauth() -> Tuple[Optional[IMAPClient], str]:
    """Connects to Gmail IMAP using OAuth 2.0 credentials.

    Fetches credentials using auth.get_credentials() and attempts login.

    Returns:
        A tuple containing the connected IMAPClient instance and a status message,
        or (None, error_message) if connection fails.
    """
    logging.info("Attempting to get Google credentials and user email...")
    creds, user_email = get_credentials()

    if not creds or not creds.valid:
        error_msg = "Failed to obtain valid Google credentials. Please check logs or run authentication."
        logging.error(error_msg)
        return None, error_msg

    if not user_email:
        error_msg = "Failed to obtain user email address via People API. Cannot proceed with IMAP login."
        logging.error(error_msg)
        return None, error_msg

    access_token = creds.token
    server: Optional[IMAPClient] = None # Initialize server to None

    logging.info(f"Attempting IMAP connection to {IMAP_HOST} for user {user_email} using OAuth2...")

    try:
        server = IMAPClient(IMAP_HOST, ssl=True)
        logging.info(f"IMAPClient created for {IMAP_HOST}")
        server.oauth2_login(user_email, access_token)
        status_message = f'Connected to {IMAP_HOST} as {user_email}'
        logging.info(f'IMAP OAuth2 login successful to {IMAP_HOST} as {user_email}')
        return server, status_message

    except LoginError as login_err:
        error_msg = f"IMAP Login Error: {login_err}"
        logging.error(error_msg, exc_info=True)
        # Attempt logout only if server object was successfully created
        if server:
            try:
                server.logout()
            except Exception as logout_e:
                logging.error(f"Error during logout after login failure: {logout_e}")
        return None, error_msg
    except ConnectionRefusedError as conn_err: # Specific network error
         error_msg = f"IMAP Connection Refused for {IMAP_HOST}: {conn_err}"
         logging.error(error_msg)
         return None, error_msg
    except Exception as e: # Catch other potential errors (socket errors, etc.)
        error_msg = f"General IMAP connection/login failed: {e}"
        logging.error(error_msg, exc_info=True)
        if server:
            try:
                if server.is_connected(): # Check if connected before logout
                    server.logout()
            except Exception as logout_e:
                logging.error(f"Error during logout after general failure: {logout_e}")
        return None, error_msg
