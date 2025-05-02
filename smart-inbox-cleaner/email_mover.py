import os
from imapclient import IMAPClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Safety flag for testing
# Consider making this configurable via UI or config file instead of hardcoding
TEST_MODE_MOVE_ONE = os.getenv("TEST_MODE_MOVE_ONE", "True").lower() == "true"

# Target folder mapping
TARGET_FOLDER_MAP = {
    "Action": "SmartInbox/Action",
    "Read": "SmartInbox/Read",
    "Events": "SmartInbox/Events",
    "Information": "SmartInbox/Information"
}

def move_emails(server: IMAPClient, uids_to_move, category_map):
    """Moves emails specified by UIDs to folders based on their category using the provided client."""
    # Removed internal connection logic
    moved_uids = []
    operation_failed = False # Flag to indicate if any move failed

    if not server or not server.is_connected():
        logging.error("Invalid or disconnected IMAP client provided. Cannot move emails.")
        return None # Return None to indicate failure

    if not uids_to_move:
        logging.info("Move requested, but no UIDs provided.")
        return [] # Return empty list, not an error

    try:
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
                    # Optionally select the folder after creating to ensure it's usable immediately
                    # server.select_folder(target_folder)
                    # server.select_folder('INBOX', readonly=False) # Re-select INBOX
            except Exception as folder_e:
                logging.error(f"Error checking/creating folder {target_folder} for UID {uid}: {folder_e}")
                operation_failed = True
                continue # Skip this email if folder handling fails

            # Move the email
            try:
                logging.info(f"Moving UID {uid} ({category}) to {target_folder}...")
                server.move([uid], target_folder)
                logging.info(f"Successfully moved UID {uid}.")
                moved_uids.append(uid)

                # Apply safety flag
                if TEST_MODE_MOVE_ONE:
                    logging.warning("TEST_MODE_MOVE_ONE enabled via env var. Stopping after first successful move.")
                    break # Stop after moving one email

            except Exception as move_e:
                logging.error(f"Error moving UID {uid} to {target_folder}: {move_e}")
                operation_failed = True
                # Decide whether to continue or stop on error (currently continues)

    except Exception as e:
        logging.error(f"General error during email moving: {e}", exc_info=True)
        operation_failed = True # Mark as failed on general error

    if operation_failed:
        logging.warning(f"Move operation completed with errors. Successfully moved UIDs: {moved_uids}")
        # Return None if the overall operation had issues, even if some succeeded?
        # Or return the list of successfully moved UIDs? Returning moved_uids for now.
        # Consider returning a tuple: (success_bool, moved_uids)
        return None # Indicate failure in main UI
    else:
        logging.info(f"Move operation complete. Successfully moved UIDs: {moved_uids}")
        return moved_uids # Return list of UIDs successfully moved 