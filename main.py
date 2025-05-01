import streamlit as st
from dotenv import load_dotenv
import os
from email_client import connect_imap
from email_fetcher import fetch_inbox_emails
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="Smart Inbox Cleaner",
    page_icon="📥",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
/* Base font size */
html, body, [class*="st-"], .stDataFrame {
    font-size: 18px !important;
}
/* Make dataframe take full width */
.stDataFrame {
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# --- Load Environment Variables ---
load_dotenv()
gmail_address = os.getenv('GMAIL_ADDRESS', 'Not set') # Used in expander

# --- App Header ---
st.title('📥 Smart Inbox Cleaner')

# --- Connection Status Expander ---
with st.expander("Connection Details", expanded=False):
    st.write(f'Connected Gmail address: {gmail_address}')
    # Check connection status directly here
    connection_status = connect_imap()
    st.write(f'IMAP Connection Status: {connection_status}')

# --- Email Fetching and Display ---
st.header("Inbox Emails")

if "Connected to" in connection_status:
    with st.spinner("Fetching emails..."):
        try:
            fetched_emails = fetch_inbox_emails()
            if fetched_emails:
                df = pd.DataFrame(fetched_emails)
                df = df.sort_values(by='date', ascending=False)
                df = df[['date', 'from', 'subject']]
                st.dataframe(df, use_container_width=True, height=600)

                # --- Categorization Button ---
                if st.button("Categorize Emails (Placeholder)"):
                    st.toast("Categorization logic not implemented yet.")
                    # Placeholder for future categorization call
                    pass
            else:
                st.write("No emails fetched or inbox is empty.")
        except Exception as e:
            st.error(f"Error fetching emails: {e}")
else:
    st.warning("Cannot fetch emails. Please check IMAP connection.")
