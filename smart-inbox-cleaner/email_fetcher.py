from imapclient import IMAPClient
import logging
from typing import List, Dict, Any
import email.header

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def decode_header_text(text):
    """Properly decode email header texts that might be encoded."""
    if not text:
        return ""
    
    try:
        decoded_parts = email.header.decode_header(text)
        result = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result += part.decode(encoding or 'utf-8', errors='replace')
            else:
                result += str(part)
        return result
    except Exception as e:
        logging.warning(f"Error decoding header text: {e}")
        if isinstance(text, bytes):
            return text.decode('utf-8', errors='replace')
        return text

def fetch_inbox_emails(server: IMAPClient, batch_size: int = 250) -> List[Dict[str, Any]]:
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
                # Properly decode subject using our helper function
                raw_subject = envelope.subject
                subject = decode_header_text(raw_subject) if raw_subject else ''
                
                # Properly decode from address
                from_addr = ""
                if envelope.from_ and len(envelope.from_) > 0:
                    sender = envelope.from_[0]
                    if hasattr(sender, 'name') and sender.name:
                        from_name = decode_header_text(sender.name)
                        from_addr = from_name
                    elif hasattr(sender, 'mailbox') and hasattr(sender, 'host'):
                        mailbox = sender.mailbox.decode('utf-8', errors='replace') if isinstance(sender.mailbox, bytes) else sender.mailbox
                        host = sender.host.decode('utf-8', errors='replace') if isinstance(sender.host, bytes) else sender.host
                        from_addr = f"{mailbox}@{host}"
                    else:
                        from_addr = str(sender)

                emails.append({
                    'uid': uid,
                    'subject': subject,
                    'from': from_addr, 
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