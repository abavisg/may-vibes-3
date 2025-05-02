import os
import base64 # Needed for XOAUTH2
from imapclient import IMAPClient
from .auth import get_credentials # Import from our new auth module

def connect_oauth():
    """Connects to Gmail IMAP using OAuth 2.0 credentials and returns the client or None."""
    print("Attempting to get Google credentials for IMAP...")
    creds = get_credentials()

    if not creds or not creds.valid:
        print("Failed to get valid credentials.")
        return None, "Failed to obtain valid Google credentials. Please check logs or run authentication."

    # Check if token needs refreshing (though get_credentials should handle it)
    # if creds.expired and creds.refresh_token:
    #     try:
    #         creds.refresh(Request())
    #     except Exception as e:
    #         print(f"Failed to refresh token: {e}")
    #         return None, f"Failed to refresh token: {e}"

    imap_host = 'imap.gmail.com'
    user_email = creds.id_token_jwt['email'] # Get email from ID token if available
                                           # Or find another way if not using id_token scope
                                           # Fallback might be needed if email isn't in the token
                                           # user_email = "YOUR_GMAIL_ADDRESS" # temporary fallback if needed
    access_token = creds.token

    print(f"Attempting IMAP connection to {imap_host} for user {user_email}...")

    try:
        # Construct the XOAUTH2 authentication string
        # Format: "user=" + user + "\1auth=Bearer " + access_token + "\1\1"
        auth_string = f'user={user_email}\1auth=Bearer {access_token}\1\1'
        auth_bytes = base64.b64encode(auth_string.encode('utf-8'))

        server = IMAPClient(imap_host, ssl=True) # Ensure SSL is True for Gmail
        server.oauth2_login(user_email, access_token)
        # server.authenticate(b'XOAUTH2', lambda response: auth_bytes) # Alternative using authenticate

        print(f'IMAP OAuth2 connection successful to {imap_host} as {user_email}')
        return server, f'Connected to {imap_host} as {user_email}' # Return client and status message

    except Exception as e:
        print(f"IMAP OAuth2 connection failed: {e}")
        # Attempt to close server if partially opened
        try:
            if 'server' in locals() and server.is_connected():
                server.logout()
        except Exception as logout_e:
            print(f"Error during logout after connection failure: {logout_e}")
        return None, f'IMAP Connection failed: {e}' # Return None and error message
