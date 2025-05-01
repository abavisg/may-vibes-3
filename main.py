import streamlit as st
from dotenv import load_dotenv
import os
from email_client import connect_imap
from email_fetcher import fetch_inbox_emails

# Load environment variables from .env file
load_dotenv()

gmail_address = os.getenv('GMAIL_ADDRESS', 'Not set')

st.title('Smart Inbox Cleaner')
st.write(f'Connected Gmail address: {gmail_address}')

# Check connection status
connection_status = connect_imap()
st.write(f'IMAP Connection Status: {connection_status}')

# If connected, fetch emails
if "Connected to" in connection_status:
    st.info("Fetching emails...")
    try:
        fetched_emails = fetch_inbox_emails()
        st.success(f"Email fetching attempt complete. Check terminal logs.")
        # Optional: Display count in UI
        st.write(f"Fetched {len(fetched_emails)} emails.")
    except Exception as e:
        st.error(f"Error fetching emails: {e}")
else:
    st.warning("Cannot fetch emails. Please check IMAP connection.")
