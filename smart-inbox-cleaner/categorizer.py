def categorize_email(email_data):
    """Categorizes a single email based on simple rules."""
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
            return "Events"

    # 2. Action: Keywords suggesting direct tasks (excluding event invites handled above)
    action_keywords = ['meeting', 'schedule', 'urgent', 'request', 'action required', 'task', 'confirm', 'follow up', 'respond', 'please']
    # Avoid classifying simple event confirmations as actions if already caught
    if any(keyword in subject for keyword in action_keywords):
        # Check again to ensure it wasn't explicitly skipped by the non_invite_keywords
        if not any(keyword in subject for keyword in non_invite_keywords):
             return "Action"

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
        return "Read"

    # Default category
    return "Uncategorised"

def categorize_emails(emails):
    """Adds a 'category' key to each email dictionary in a list."""
    for email in emails:
        email['category'] = categorize_email(email)
    return emails # Return the modified list 