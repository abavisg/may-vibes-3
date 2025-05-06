import logging # Add logging
from typing import Dict, Any, List # Add typing

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Category Constants ---
CAT_ACTION = "Action"
CAT_READ = "Read"
CAT_EVENTS = "Events"
CAT_INFO = "Information" # Currently disabled in rules
CAT_UNCATEGORISED = "Uncategorised"

# List of categories used in rules (excluding Uncategorised)
RULE_CATEGORIES = [CAT_ACTION, CAT_READ, CAT_EVENTS, CAT_INFO]
# Categories that are moved by default
MOVE_CATEGORIES = [CAT_ACTION, CAT_READ, CAT_EVENTS]

def categorize_email(email_data: Dict[str, Any]) -> str:
    """Categorizes a single email based on simple rules, returning a category string."""
    subject = email_data.get('subject', '').lower()
    sender = email_data.get('from', '').lower()

    # --- Rule Definitions (Order matters) ---

    # 1. Events: Focus on new calendar invitations.
    # Keywords indicating it's likely NOT a new invite to ignore
    non_invite_keywords = ['accepted:', 'tentative:', 'declined:', 'canceled:', 'updated invitation', 'reminder:']
    if any(keyword in subject for keyword in non_invite_keywords):
        pass # Skip to the next rule if it's likely an update/response
    else:
        # Keywords strongly suggesting a new invite
        invite_keywords = ['invitation', 'invite', 'calendar invite', 'please respond', 'rsvp', 'appointment request']
        # Senders often sending invites
        invite_senders = ['calendar-notification@google.com', '@calendly.com', '@savvycal.com']
        # Check subject for invite keywords OR sender is a known invite source
        if any(keyword in subject for keyword in invite_keywords) or \
           any(sender_part in sender for sender_part in invite_senders):
            return CAT_EVENTS

    # 2. Action: Keywords suggesting direct tasks (excluding event invites handled above)
    action_keywords = ['meeting', 'schedule', 'urgent', 'request', 'action required', 'task', 'confirm', 'follow up', 'respond', 'please']
    # Avoid classifying simple event confirmations as actions if already caught
    if any(keyword in subject for keyword in action_keywords):
        # Check again to ensure it wasn't explicitly skipped by the non_invite_keywords
        if not any(keyword in subject for keyword in non_invite_keywords):
             return CAT_ACTION

    # 3. Information: Notifications, alerts, receipts (often no-reply) - DISABLED
    # info_keywords = ['notification', 'alert', 'confirmation', 'receipt', 'statement', 'security alert', 'delivery status', 'invoice']
    # info_senders = ['no-reply', 'noreply', 'support@', 'billing@', 'notifications@', 'accounts@', '@service.', '@alert.', '@github.com', '@aws.']
    # if any(keyword in subject for keyword in info_keywords) or \
    #    any(sender_part in sender for sender_part in info_senders):
    #     return "Information"

    # 4. Read: Newsletters, updates, blogs, digests (often from specific platforms)
    read_keywords = ['newsletter', 'update', 'digest', 'blog', 'weekly', 'daily', 'report', 'summary', 'announcement', 'issue #']
    read_senders = ['@substack.com', 'updates@', '@medium.com', 'digest@']
    if any(keyword in subject for keyword in read_keywords) or \
       any(sender_part in sender for sender_part in read_senders):
        return CAT_READ

    # Default category
    return CAT_UNCATEGORISED

def categorize_emails(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Adds a 'category' key to each email dictionary in a list."""
    logging.info(f"Starting categorization for {len(emails)} emails.")
    categorized_count = 0
    for email in emails:
        category = categorize_email(email)
        email['category'] = category
        if category != CAT_UNCATEGORISED:
             categorized_count += 1
    logging.info(f"Finished categorization. {categorized_count} emails assigned a category other than '{CAT_UNCATEGORISED}'.")
    return emails 