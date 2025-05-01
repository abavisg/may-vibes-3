import streamlit as st
from dotenv import load_dotenv
import os
from email_client import connect_imap
from email_mover import move_emails
from email_fetcher import fetch_inbox_emails
from categorizer import categorize_emails
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
    st.session_state.emails = [] # Raw list of dicts from fetcher
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame() # DataFrame for display/editing
if 'categorization_run' not in st.session_state:
    st.session_state.categorization_run = False # Track if auto-categorization ran
if 'show_move_confirmation' not in st.session_state:
    st.session_state.show_move_confirmation = False # Controls visibility of inline confirmation
if 'move_counts' not in st.session_state:
    st.session_state.move_counts = {} # Stores counts for confirmation message
if 'manual_selection_mode' not in st.session_state:
    st.session_state.manual_selection_mode = False # Controls visibility of selection checkboxes

# --- Load Environment Variables ---
load_dotenv()
gmail_address = os.getenv('GMAIL_ADDRESS', 'Not set')

# --- App Header ---
st.title('📥 Smart Inbox Cleaner')

# --- Connection Status Expander ---
with st.expander("Connection Details", expanded=False):
    st.write(f'Connected Gmail address: {gmail_address}')
    connection_status = connect_imap()
    st.write(f'IMAP Connection Status: {connection_status}')

# --- Fetch Emails (Only if not already fetched and connection is OK) ---
if "Connected to" in connection_status and not st.session_state.emails:
    with st.spinner("Fetching initial emails..."):
        try:
            st.session_state.emails = fetch_inbox_emails()
            if st.session_state.emails:
                temp_df = pd.DataFrame(st.session_state.emails)
                temp_df['category'] = 'Uncategorised'
                temp_df['Select'] = False
                temp_df['date'] = pd.to_datetime(temp_df['date']) # Ensure date is datetime type
                temp_df = temp_df.sort_values(by='date', ascending=False)
                # Define initial column order
                st.session_state.df = temp_df[['Select', 'date', 'from', 'subject', 'category', 'uid']]
            else:
                st.write("No emails fetched or inbox is empty.")
        except Exception as e:
            st.error(f"Error fetching emails: {e}")
elif "Connected to" not in connection_status:
    # Display warning only if emails haven't been fetched previously
    if not st.session_state.emails:
        st.warning("Cannot fetch emails. Please check IMAP connection.")

# --- Display Area ---
st.header("Inbox Emails")

# --- Main Action Buttons (Hidden in Manual Selection Mode) ---
if not st.session_state.manual_selection_mode:
    col1, col2 = st.columns(2)
    # Categorization Button
    with col1:
        if st.button("Categorize Emails"):
            if not st.session_state.emails:
                st.warning("No emails fetched to categorize.")
            else:
                with st.spinner("Categorizing..."):
                    categorized_email_list = categorize_emails(st.session_state.emails.copy())
                    temp_df = pd.DataFrame(categorized_email_list)
                    temp_df['Select'] = False # Keep select column
                    temp_df['date'] = pd.to_datetime(temp_df['date'])
                    temp_df = temp_df.sort_values(by='date', ascending=False)
                    # Update session df, preserving column order
                    st.session_state.df = temp_df[['Select', 'date', 'from', 'subject', 'category', 'uid']]
                    st.session_state.categorization_run = True
                    st.session_state.show_move_confirmation = False # Reset confirmation
                    st.toast("Categorization applied for this session!")
    # Move Emails Button
    with col2:
        # Determine enabled state
        move_button_disabled = True
        if st.session_state.categorization_run and not st.session_state.df.empty:
            category_counts = st.session_state.df['category'].value_counts()
            relevant_categories = ["Action", "Read", "Events"]
            relevant_present = any(cat in category_counts for cat in relevant_categories if category_counts.get(cat, 0) > 0)
            if relevant_present:
                move_button_disabled = False

        if st.button("Move All Categorized", disabled=move_button_disabled):
            relevant_categories_to_move = ["Action", "Read", "Events"]
            current_counts = st.session_state.df['category'].value_counts()
            st.session_state.move_counts = {cat: current_counts.get(cat, 0) for cat in relevant_categories_to_move if cat in current_counts and current_counts.get(cat, 0) > 0}
            if st.session_state.move_counts:
                 st.session_state.show_move_confirmation = True
            else:
                 st.toast("No emails found in Action, Read, or Events categories to move.")
                 st.session_state.show_move_confirmation = False

# --- Move Confirmation Dialog (Inline, conditional display) ---
if st.session_state.show_move_confirmation and not st.session_state.manual_selection_mode:
    confirm_items = [f"{cat}: {count}" for cat, count in st.session_state.move_counts.items() if count > 0]
    confirm_text = " | ".join(confirm_items)
    st.warning(f"Confirm moving all applicable emails? -> {confirm_text}")
    col_confirm_yes, col_confirm_no, col_confirm_manual = st.columns(3)
    with col_confirm_yes:
        if st.button("✅ Yes, Move All"):
            with st.spinner("Moving emails..."):
                relevant_df = st.session_state.df[st.session_state.df['category'].isin(["Action", "Read", "Events"])].copy()
                if not relevant_df.empty:
                    uids_to_move = relevant_df['uid'].tolist()
                    category_map = pd.Series(relevant_df.category.values, index=relevant_df.uid).to_dict()
                    moved_uids = move_emails(uids_to_move, category_map)
                    if moved_uids:
                        st.toast(f"Moved {len(moved_uids)} email(s). Test mode might be active.")
                        # Update state immediately
                        st.session_state.df = st.session_state.df[~st.session_state.df['uid'].isin(moved_uids)]
                        st.session_state.emails = [email for email in st.session_state.emails if email['uid'] not in moved_uids]
                    else:
                        st.toast("Move operation attempted, but no emails were moved. Check logs.")
                else:
                    st.toast("No relevant emails found to move.")
            st.session_state.show_move_confirmation = False
            st.rerun()
    with col_confirm_no:
        if st.button("❌ No, Cancel"):
            st.session_state.show_move_confirmation = False
            st.rerun()
    with col_confirm_manual:
        if st.button("✍️ No, Select Manually"):
            st.session_state.manual_selection_mode = True
            st.session_state.show_move_confirmation = False
            st.rerun()

# --- Manual Selection Mode UI ---
if st.session_state.manual_selection_mode:
    st.info("Manual Selection Mode: Select specific emails using the checkboxes.")
    col_move_sel, col_cancel_sel = st.columns(2)
    with col_move_sel:
        if st.button("Move Selected Emails"):
            if not st.session_state.df.empty:
                selected_df = st.session_state.df[st.session_state.df['Select'] == True]
                relevant_categories_to_move = ["Action", "Read", "Events"]
                selected_to_move = selected_df[selected_df['category'].isin(relevant_categories_to_move)].copy()
                if not selected_to_move.empty:
                    uids_to_move = selected_to_move['uid'].tolist()
                    category_map = pd.Series(selected_to_move.category.values, index=selected_to_move.uid).to_dict()
                    with st.spinner("Moving selected emails..."):
                        moved_uids = move_emails(uids_to_move, category_map)
                        if moved_uids:
                            st.toast(f"Moved {len(moved_uids)} selected email(s). Test mode might be active.")
                            # Update state immediately
                            st.session_state.df = st.session_state.df[~st.session_state.df['uid'].isin(moved_uids)]
                            st.session_state.emails = [email for email in st.session_state.emails if email['uid'] not in moved_uids]
                        else:
                            st.toast("Move operation attempted, but no emails were moved. Check logs.")
                    st.session_state.manual_selection_mode = False
                    st.rerun()
                else:
                    st.warning("No valid emails selected (must be Action, Read, or Events).")
            else:
                st.warning("No emails loaded.")
    with col_cancel_sel:
        if st.button("Cancel Manual Selection"):
            st.session_state.manual_selection_mode = False
            # Reset selection checkboxes in the DataFrame
            if not st.session_state.df.empty:
                 st.session_state.df['Select'] = False
            st.rerun()

# --- Email Editor Table ---
if not st.session_state.df.empty:
    # Ensure latest emails are always at the top before display
    st.session_state.df = st.session_state.df.sort_values(by='date', ascending=False)

    # Dynamically configure columns
    column_config = {
        "uid": None, # Hide UID
        "category": st.column_config.SelectboxColumn(
            "Category",
            options=["Uncategorised", "Action", "Read", "Events", "Information"],
            required=True,
        ),
        "date": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD HH:mm:ss"),
        "from": "From",
        "subject": "Subject",
        "Select": None # Default to hidden unless in manual mode
    }
    disabled_columns = ["date", "from", "subject", "uid", "category"]

    if st.session_state.manual_selection_mode:
        column_config["Select"] = st.column_config.CheckboxColumn("Select", default=False)
        # Allow editing Select only
    else:
        disabled_columns.append("Select") # Ensure Select is disabled if column exists but hidden

    edited_df = st.data_editor(
        st.session_state.df,
        use_container_width=True,
        height=600,
        column_config=column_config,
        disabled=disabled_columns,
        key="data_editor"
    )

    # Update session state if edits were made (primarily selection changes)
    if not edited_df.equals(st.session_state.df):
        st.session_state.df = edited_df
        # Avoid toast messages for simple checkbox clicks

    # --- Category Summary ---
    category_counts = st.session_state.df['category'].value_counts().sort_index()
    summary_items = [f"{cat}: {count}" for cat, count in category_counts.items()]
    summary_text = " | ".join(summary_items)
    st.markdown(f"**Inbox Status:** {summary_text}")

elif "Connected to" in connection_status:
    # Show only if connection is OK but no emails were found/loaded
    st.write("No emails to display.")

# Final check for connection warning if nothing else displayed
# (This might be redundant depending on above logic)
# elif "Connected to" not in connection_status and not st.session_state.emails:
#    st.warning("Cannot fetch emails. Please check IMAP connection.")
