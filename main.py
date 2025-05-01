import streamlit as st
from dotenv import load_dotenv
import os
from email_client import connect_imap
from email_fetcher import fetch_inbox_emails
from categorizer import categorize_emails # Import categorizer
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

# --- Initialize Session State ---
if 'emails' not in st.session_state:
    st.session_state.emails = [] # Raw fetched email list
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame() # DataFrame for display/editing

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

# --- Fetch Emails (Only if not already fetched) ---
if "Connected to" in connection_status and not st.session_state.emails:
    with st.spinner("Fetching initial emails..."):
        try:
            st.session_state.emails = fetch_inbox_emails()
            if st.session_state.emails:
                temp_df = pd.DataFrame(st.session_state.emails)
                temp_df['category'] = 'Uncategorised' # Add default category
                st.session_state.df = temp_df[['date', 'from', 'subject', 'category', 'uid']] # Add category, keep uid hidden later
            else:
                st.write("No emails fetched or inbox is empty.")
        except Exception as e:
            st.error(f"Error fetching emails: {e}")
elif "Connected to" not in connection_status:
    st.warning("Cannot fetch emails. Please check IMAP connection.")

# --- Display Area ---
st.header("Inbox Emails")

# --- Categorization Button --- (Place before editor for better flow)
if st.button("Categorize Emails"):
    if not st.session_state.emails:
        st.warning("No emails fetched to categorize.")
    else:
        with st.spinner("Categorizing..."):
            # Run categorization on a copy of the raw email list
            categorized_email_list = categorize_emails(st.session_state.emails.copy())
            # Create a new DataFrame with the results
            temp_df = pd.DataFrame(categorized_email_list)
            # Re-order columns and update the session state DataFrame
            # This makes the categorization visible but doesn't alter the base emails list
            # Manual edits from before categorization will be overwritten here.
            st.session_state.df = temp_df[['date', 'from', 'subject', 'category', 'uid']]
            st.toast("Categorization applied for this session!")

# --- Email Editor Table ---
if not st.session_state.df.empty:
    # Define categories for the dropdown
    categories = ["Uncategorised", "Action", "Read", "Events", "Information"]

    edited_df = st.data_editor(
        st.session_state.df,
        use_container_width=True,
        height=600,
        column_config={
            "uid": None, # Hide UID column
            "category": st.column_config.SelectboxColumn(
                "Category",
                help="Select the email category",
                width="medium",
                options=categories, # Use updated list without Other
                required=True,
            )
        },
        disabled=["date", "from", "subject", "uid"], # Disable editing for other columns
        key="data_editor"
    )

    # Update session state if edits were made
    if not edited_df.equals(st.session_state.df):
        st.session_state.df = edited_df
        st.toast("Manual category change saved!")

    # --- Category Summary --- Display counts based on the current state of the DataFrame
    if not st.session_state.df.empty:
        category_counts = st.session_state.df['category'].value_counts().sort_index()
        summary_items = [f"{cat}: {count}" for cat, count in category_counts.items()]
        summary_text = " | ".join(summary_items)
        st.markdown(f"**Inbox Status:** {summary_text}")

else:
    st.write("No emails to display.")
