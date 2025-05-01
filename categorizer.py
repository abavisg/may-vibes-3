import re

def categorize_email(email_data):
    """Categorizes a single email based on simple rules."""
    subject = email_data.get('subject', '').lower()
    sender = email_data.get('from', '').lower()

    # --- Rule Definitions ---

    # Action: Keywords suggesting tasks, meetings, urgent requests
    action_keywords = ['meeting', 'invite', 'schedule', 'urgent', 'request', 'action required', 'task', 'confirm']
    if any(keyword in subject for keyword in action_keywords):
        return "Action"

    # Read: Keywords suggesting newsletters, updates, blogs, digests
    read_review_keywords = ['newsletter', 'update', 'digest', 'blog', 'weekly', 'daily', 'report', 'summary']
    if any(keyword in subject for keyword in read_review_keywords):
        return "Read"

    # Information: Keywords/Senders suggesting notifications, alerts, confirmations (less interactive)
    info_keywords = ['notification', 'alert', 'confirmation', 'receipt', 'statement']
    info_senders = ['no-reply', 'noreply', 'support@', 'billing@', 'notifications@']
    if any(keyword in subject for keyword in info_keywords) or \
       any(sender_part in sender for sender_part in info_senders):
        return "Information"

    # Default category - changed to Uncategorised
    return "Uncategorised"

def categorize_emails(emails):
    """Adds a 'category' key to each email dictionary in a list."""
    for email in emails:
        email['category'] = categorize_email(email)
    return emails # Return the modified list 