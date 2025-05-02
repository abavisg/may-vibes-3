from imapclient import IMAPClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_inbox_emails(server: IMAPClient, batch_size=250):
    """Fetch metadata for the latest batch_size emails from the INBOX using the provided client."""
    # Removed internal connection logic

    emails = []
    try:
        # Assume server is already connected and logged in
        server.select_folder('INBOX', readonly=True)
        messages = server.search(['ALL'])
        logging.info(f"Found {len(messages)} total messages in INBOX.")

        if not messages:
            logging.info("No messages found in INBOX.")
            return []

        latest_uids = messages[-batch_size:]
        logging.info(f"Fetching details for {len(latest_uids)} messages (UIDs: {latest_uids[:5]}...).")
        # Fetch ENVELOPE data
        response = server.fetch(latest_uids, ['ENVELOPE'])

        for uid, data in response.items():
            if b'ENVELOPE' in data:
                envelope = data[b'ENVELOPE']
                subject = envelope.subject.decode(errors='ignore') if envelope.subject else ''
                from_addr = str(envelope.from_[0]) if envelope.from_ else ''
                # Attempt to decode From address properly if needed (more complex)
                # Example: Use email.header.decode_header if complex encoding
                # decoded_from = decode_header(from_addr)
                # from_addr = ... processed decoded_from ...

                emails.append({
                    'uid': uid,
                    'subject': subject,
                    'from': from_addr, # Simpler from representation
                    'date': envelope.date
                })
            else:
                logging.warning(f"No ENVELOPE data found for UID {uid}")
        logging.info(f"Successfully fetched details for {len(emails)} emails.")
    except Exception as e:
        logging.error(f"Error fetching emails: {e}", exc_info=True)
        # Do not return partial list on error, return empty
        return []

    return emails 