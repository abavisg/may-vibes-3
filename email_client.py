import os
from imapclient import IMAPClient

def connect_imap():
    imap_host = os.getenv('EMAIL_HOST', 'imap.gmail.com')
    imap_user = os.getenv('EMAIL_USERNAME', os.getenv('GMAIL_ADDRESS', 'Not set'))
    imap_pass = os.getenv('EMAIL_PASSWORD', None)

    if imap_user and imap_pass:
        try:
            with IMAPClient(imap_host) as server:
                server.login(imap_user, imap_pass)
                print(f'Connected to {imap_host} as {imap_user}')
                return f'Connected to {imap_host} as {imap_user}'
        except Exception as e:
            return f'Connection failed: {e}'
    else:
        return 'IMAP credentials not set in .env file.'
