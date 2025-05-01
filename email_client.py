import os
from imapclient import IMAPClient

def connect_imap():
    """Connects to IMAP server using credentials from .env and returns status."""
    imap_host = os.getenv('EMAIL_HOST', 'imap.gmail.com')
    imap_user = os.getenv('EMAIL_USERNAME', os.getenv('GMAIL_ADDRESS', 'Not set'))
    imap_pass = os.getenv('EMAIL_PASSWORD', None)

    if not imap_user or not imap_pass or imap_user == 'Not set':
        return 'IMAP credentials not set in .env file.'

    try:
        with IMAPClient(imap_host) as server:
            server.login(imap_user, imap_pass)
            print(f'IMAP connection successful to {imap_host} as {imap_user}') # Log success
            return f'Connected to {imap_host} as {imap_user}'
    except Exception as e:
        print(f"IMAP connection failed: {e}") # Log failure
        return f'Connection failed: {e}'
