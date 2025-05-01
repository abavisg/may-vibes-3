from imapclient import IMAPClient
import os

def fetch_inbox_emails(batch_size=250):
    """Fetch metadata for the latest batch_size emails from the INBOX."""
    imap_host = os.getenv('EMAIL_HOST', 'imap.gmail.com')
    imap_user = os.getenv('EMAIL_USERNAME', os.getenv('GMAIL_ADDRESS', 'Not set'))
    imap_pass = os.getenv('EMAIL_PASSWORD', None)
    with IMAPClient(imap_host) as server:
        server.login(imap_user, imap_pass)
        server.select_folder('INBOX', readonly=True)
        messages = server.search(['ALL'])
        latest_uids = messages[-batch_size:] if len(messages) > batch_size else messages
        response = server.fetch(latest_uids, ['ENVELOPE'])
        emails = []
        for uid, data in response.items():
            envelope = data[b'ENVELOPE']
            emails.append({
                'uid': uid,
                'subject': envelope.subject.decode() if envelope.subject else '',
                'from': str(envelope.from_[0].mailbox.decode() + '@' + envelope.from_[0].host.decode()) if envelope.from_ else '',
                'date': envelope.date
            })
        print(f"Fetched {len(emails)} emails from INBOX.")
        for i, email in enumerate(emails[:5]):
            print(f"{i+1}. Subject: {email['subject']}, From: {email['from']}, Date: {email['date']}")
        return emails 