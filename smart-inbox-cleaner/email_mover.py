import os
import logging
from typing import List, Dict, Optional, Any # Add typing
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError # Base IMAP exception
# Import category constants
from categorizer import CAT_ACTION, CAT_READ, CAT_EVENTS, CAT_INFO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Safety flag for testing: If True, only move one email per execution.
# Controlled by environment variable TEST_MODE_MOVE_ONE (defaults to True).
# Set TEST_MODE_MOVE_ONE=False in your environment (e.g., .env file) to disable.
TEST_MODE_MOVE_ONE = os.getenv("TEST_MODE_MOVE_ONE", "True").lower() == "true"

# Target folder mapping using constants
TARGET_FOLDER_MAP: Dict[str, str] = {
    CAT_ACTION: "SmartInbox/Action",
    CAT_READ: "SmartInbox/Read",
    CAT_EVENTS: "SmartInbox/Events",
    CAT_INFO: "SmartInbox/Information"
}

def move_emails(server: IMAPClient, uids_to_move: List[int], category_map: Dict[int, str]) -> Optional[List[int]]:
    """Moves emails specified by UIDs to folders based on their category using the provided client.

    Args:
        server: The connected and authenticated IMAPClient instance.
        uids_to_move: A list of email UIDs to attempt moving.
        category_map: A dictionary mapping UID to its category string.

    Returns:
        A list of UIDs that were successfully moved, or None if a critical error occurred 
        during the operation (e.g., connection issue, folder creation failure).
        An empty list is returned if no UIDs were provided or none were moved successfully
        without critical errors.
    """
    moved_uids: List[int] = []
    operation_failed = False # Flag to indicate if any move failed critically

    # Check only if the server object exists; connection errors handled later
    if not server:
        logging.error("Invalid IMAP client object provided (None). Cannot move emails.")
        return None # Indicate critical failure

    if not uids_to_move:
        logging.info("Move requested, but no UIDs provided.")
        return [] # Not an error, just nothing to do

    try:
        # Ensure we are in INBOX and have write access before looping
        server.select_folder('INBOX', readonly=False)
        logging.info(f"Attempting to move UIDs: {uids_to_move}")

        processed_uids = 0
        for uid in uids_to_move:
            category = category_map.get(uid)
            if not category or category not in TARGET_FOLDER_MAP:
                logging.warning(f"UID {uid} has invalid or missing category '{category}'. Skipping.")
                continue

            target_folder = TARGET_FOLDER_MAP[category]

            # Ensure target folder exists
            try:
                if not server.folder_exists(target_folder):
                    logging.info(f"Target folder '{target_folder}' does not exist. Creating...")
                    server.create_folder(target_folder)
                    logging.info(f"Successfully created folder: {target_folder}")
            except IMAPClientError as folder_e: # Catch specific IMAP errors
                logging.error(f"IMAP Error checking/creating folder {target_folder} for UID {uid}: {folder_e}")
                operation_failed = True
                # Treat folder error as critical? Maybe stop the whole process?
                # For now, just mark as failed and skip this UID.
                continue 
            except Exception as folder_e: # Catch other potential errors
                logging.error(f"Unexpected error checking/creating folder {target_folder} for UID {uid}: {folder_e}", exc_info=True)
                operation_failed = True
                continue

            # Move the email
            try:
                logging.info(f"Moving UID {uid} (Category: {category}) to folder '{target_folder}'...")
                server.move([uid], target_folder)
                logging.info(f"Successfully moved UID {uid}.")
                moved_uids.append(uid)
                processed_uids += 1

                # Apply safety flag (stop after first successful move if enabled)
                if TEST_MODE_MOVE_ONE:
                    logging.warning("TEST_MODE_MOVE_ONE enabled via env var. Stopping after first successful move.")
                    break # Exit loop after moving one email

            except IMAPClientError as move_e:
                 logging.error(f"IMAP Error moving UID {uid} to {target_folder}: {move_e}")
                 # Don't mark operation_failed=True here? Allows other emails to be tried.
                 # Logged as error, but not critical failure for the whole batch.
            except Exception as move_e:
                logging.error(f"Unexpected error moving UID {uid} to {target_folder}: {move_e}", exc_info=True)

    except IMAPClientError as select_e: # Error selecting INBOX
         logging.error(f"IMAP Error selecting INBOX for moving: {select_e}")
         operation_failed = True # Mark as failed on general error
    except Exception as e: # Other general errors (e.g., connection drop)
        logging.error(f"General error during email moving process: {e}", exc_info=True)
        operation_failed = True

    # Determine final return value based on critical failures
    if operation_failed:
        logging.warning(f"Move operation completed but encountered critical errors. Successfully moved UIDs: {moved_uids}")
        return None # Indicate critical failure to main UI
    else:
        logging.info(f"Move operation complete. Successfully moved {len(moved_uids)} out of {processed_uids} processed emails. Moved UIDs: {moved_uids}")
        return moved_uids # Return list of UIDs successfully moved 