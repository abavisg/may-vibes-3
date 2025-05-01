import os
from imapclient import IMAPClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Safety flag for testing
TEST_MODE_MOVE_ONE = True

# Target folder mapping
TARGET_FOLDER_MAP = {
    "Action": "SmartInbox/Action",
    "Read": "SmartInbox/Read",
    "Events": "SmartInbox/Events",
    "Information": "SmartInbox/Information"
}

def move_emails(uids_to_move, category_map):
    """Moves emails specified by UIDs to folders based on their category."""
    imap_host = os.getenv('EMAIL_HOST', 'imap.gmail.com')
    imap_user = os.getenv('EMAIL_USERNAME', os.getenv('GMAIL_ADDRESS', 'Not set'))
    imap_pass = os.getenv('EMAIL_PASSWORD', None)
    moved_uids = []

    if not uids_to_move:
        logging.info("Move requested, but no UIDs provided.")
        return moved_uids
    
    if not imap_user or not imap_pass or imap_user == 'Not set':
        logging.error("IMAP credentials not set in .env file. Cannot move emails.")
        return moved_uids

    try:
        with IMAPClient(imap_host) as server:
            server.login(imap_user, imap_pass)
            server.select_folder('INBOX', readonly=False) # Need write access
            logging.info(f"Attempting to move UIDs: {uids_to_move}")

            for uid in uids_to_move:
                category = category_map.get(uid)
                if not category or category not in TARGET_FOLDER_MAP:
                    logging.warning(f"UID {uid} has invalid or missing category '{category}'. Skipping.")
                    continue

                target_folder = TARGET_FOLDER_MAP[category]

                # Ensure target folder exists
                try:
                    if not server.folder_exists(target_folder):
                        logging.info(f"Creating folder: {target_folder}")
                        server.create_folder(target_folder)
                except Exception as folder_e:
                    logging.error(f"Error checking/creating folder {target_folder} for UID {uid}: {folder_e}")
                    continue # Skip this email if folder handling fails

                # Move the email
                try:
                    logging.info(f"Moving UID {uid} ({category}) to {target_folder}...")
                    server.move([uid], target_folder)
                    logging.info(f"Successfully moved UID {uid}.")
                    moved_uids.append(uid)

                    # Apply safety flag
                    if TEST_MODE_MOVE_ONE:
                        logging.warning("TEST_MODE_MOVE_ONE enabled. Stopping after first successful move.")
                        break # Stop after moving one email

                except Exception as move_e:
                    logging.error(f"Error moving UID {uid} to {target_folder}: {move_e}")
                    # Decide whether to continue or stop on error

    except Exception as e:
        logging.error(f"General error during email moving: {e}", exc_info=True)

    logging.info(f"Move operation complete. Successfully moved UIDs: {moved_uids}")
    return moved_uids 