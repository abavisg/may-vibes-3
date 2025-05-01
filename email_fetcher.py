from imapclient import IMAPClient
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_inbox_emails(batch_size=250):
    """Fetch metadata for the latest batch_size emails from the INBOX."""
    imap_host = os.getenv('EMAIL_HOST', 'imap.gmail.com')
    imap_user = os.getenv('EMAIL_USERNAME', os.getenv('GMAIL_ADDRESS', 'Not set'))
    imap_pass = os.getenv('EMAIL_PASSWORD', None)

    emails = []
    try:
        with IMAPClient(imap_host) as server:
            server.login(imap_user, imap_pass)
            server.select_folder('INBOX', readonly=True)
            messages = server.search(['ALL'])
            logging.info(f"Found {len(messages)} total messages in INBOX.")

            if not messages:
                logging.info("No messages found in INBOX.")
                return []

            latest_uids = messages[-batch_size:]
            logging.info(f"Fetching details for {len(latest_uids)} messages (UIDs: {latest_uids[:5]}...).")
            response = server.fetch(latest_uids, ['ENVELOPE'])

            for uid, data in response.items():
                if b'ENVELOPE' in data:
                    envelope = data[b'ENVELOPE']
                    emails.append({
                        'uid': uid,
                        'subject': envelope.subject.decode(errors='ignore') if envelope.subject else '',
                        'from': str(envelope.from_[0]) if envelope.from_ else '', # Simpler from representation
                        'date': envelope.date
                    })
                else:
                    logging.warning(f"No ENVELOPE data found for UID {uid}")
            logging.info(f"Successfully fetched details for {len(emails)} emails.")
    except Exception as e:
        logging.error(f"Error fetching emails: {e}", exc_info=True)

    return emails 