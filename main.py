import streamlit as st
from dotenv import load_dotenv
import os
from email_client import connect_imap # Only import connect_imap
from email_mover import move_emails # Import from new file
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
if 'categorization_run' not in st.session_state: # Add flag
    st.session_state.categorization_run = False
if 'show_move_confirmation' not in st.session_state: # Flag for confirmation
    st.session_state.show_move_confirmation = False
if 'move_counts' not in st.session_state: # Store counts for confirmation message
    st.session_state.move_counts = {}
if 'manual_selection_mode' not in st.session_state: # For manual selection
    st.session_state.manual_selection_mode = False

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
                temp_df['category'] = 'Uncategorised'
                temp_df['Select'] = False # Add Select column
                temp_df['date'] = pd.to_datetime(temp_df['date'])
                temp_df = temp_df.sort_values(by='date', ascending=False)
                st.session_state.df = temp_df[['Select', 'date', 'from', 'subject', 'category', 'uid']] # Add Select first
            else:
                st.write("No emails fetched or inbox is empty.")
        except Exception as e:
            st.error(f"Error fetching emails: {e}")
elif "Connected to" not in connection_status:
    st.warning("Cannot fetch emails. Please check IMAP connection.")

# --- Display Area ---
st.header("Inbox Emails")

# Only show main buttons if NOT in manual selection mode
if not st.session_state.manual_selection_mode:
    col1, col2 = st.columns(2)
    # --- Categorization Button --- (In first column)
    with col1:
        if st.button("Categorize Emails"):
            if not st.session_state.emails:
                st.warning("No emails fetched to categorize.")
            else:
                with st.spinner("Categorizing..."):
                    categorized_email_list = categorize_emails(st.session_state.emails.copy())
                    temp_df = pd.DataFrame(categorized_email_list)
                    temp_df['Select'] = False # Ensure Select column exists after categorize
                    temp_df['date'] = pd.to_datetime(temp_df['date'])
                    temp_df = temp_df.sort_values(by='date', ascending=False)
                    st.session_state.df = temp_df[['Select', 'date', 'from', 'subject', 'category', 'uid']]
                    st.session_state.categorization_run = True
                    st.session_state.show_move_confirmation = False # Hide confirmation if open
                    st.toast("Categorization applied for this session!")

    # --- Move Emails Button --- (In second column)
    with col2:
        # Determine if Move Button should be enabled (logic needed before button display)
        move_button_disabled = True
        if st.session_state.categorization_run and not st.session_state.df.empty:
            category_counts = st.session_state.df['category'].value_counts()
            relevant_categories = ["Action", "Read", "Events"]
            relevant_present = any(cat in category_counts for cat in relevant_categories)
            if relevant_present:
                move_button_disabled = False

        if st.button("Move Emails to Folders", disabled=move_button_disabled):
            relevant_categories_to_move = ["Action", "Read", "Events"]
            current_counts = st.session_state.df['category'].value_counts()
            st.session_state.move_counts = {cat: current_counts.get(cat, 0) for cat in relevant_categories_to_move if cat in current_counts and current_counts.get(cat, 0) > 0}
            if st.session_state.move_counts:
                 st.session_state.show_move_confirmation = True
            else:
                 st.toast("No emails found in Action, Read, or Events categories to move.")
                 st.session_state.show_move_confirmation = False

# --- Move Confirmation Dialog --- (Display conditionally, and not in manual mode)
if st.session_state.show_move_confirmation and not st.session_state.manual_selection_mode:
    confirm_items = [f"{cat}: {count}" for cat, count in st.session_state.move_counts.items() if count > 0]
    confirm_text = " | ".join(confirm_items)
    st.warning(f"Confirm moving emails? -> {confirm_text}")
    col_confirm_yes, col_confirm_no, col_confirm_manual = st.columns(3)
    with col_confirm_yes:
        if st.button("✅ Yes, Move All"):
            with st.spinner("Moving emails..."):
                # Filter DataFrame for relevant categories
                relevant_df = st.session_state.df[st.session_state.df['category'].isin(["Action", "Read", "Events"])].copy()
                if not relevant_df.empty:
                    uids_to_move = relevant_df['uid'].tolist()
                    category_map = pd.Series(relevant_df.category.values, index=relevant_df.uid).to_dict()
                    
                    # Call the move function
                    moved_uids = move_emails(uids_to_move, category_map)

                    if moved_uids:
                        st.toast(f"Moved {len(moved_uids)} email(s). Test mode might be active.")
                        # Remove moved emails from session state df and emails list
                        st.session_state.df = st.session_state.df[~st.session_state.df['uid'].isin(moved_uids)]
                        st.session_state.emails = [email for email in st.session_state.emails if email['uid'] not in moved_uids]
                    else:
                        st.toast("Move operation attempted, but no emails were moved.")
                else:
                    st.toast("No relevant emails found to move.")
            st.session_state.show_move_confirmation = False
            st.rerun()
    with col_confirm_no:
        if st.button("❌ No, Cancel"):
            st.session_state.show_move_confirmation = False
    with col_confirm_manual:
        if st.button("✍️ No, select manually"):
            st.session_state.manual_selection_mode = True # Enable manual mode
            st.session_state.show_move_confirmation = False # Hide confirmation
            st.rerun() # Rerun to update UI for manual mode

# --- Manual Selection Move Button --- (Only show in manual mode)
if st.session_state.manual_selection_mode:
    st.info("Manual Selection Mode: Select emails to move using the checkboxes.")
    if st.button("Move Selected Emails"):
        if not st.session_state.df.empty:
            selected_df = st.session_state.df[st.session_state.df['Select'] == True]
            relevant_categories_to_move = ["Action", "Read", "Events"]
            selected_to_move = selected_df[selected_df['category'].isin(relevant_categories_to_move)].copy()
            
            if not selected_to_move.empty:
                uids_to_move = selected_to_move['uid'].tolist()
                category_map = pd.Series(selected_to_move.category.values, index=selected_to_move.uid).to_dict()
                
                with st.spinner("Moving selected emails..."):
                    # Call the move function
                    moved_uids = move_emails(uids_to_move, category_map)

                    if moved_uids:
                        st.toast(f"Moved {len(moved_uids)} selected email(s). Test mode might be active.")
                        # Remove moved emails from session state df and emails list
                        st.session_state.df = st.session_state.df[~st.session_state.df['uid'].isin(moved_uids)]
                        st.session_state.emails = [email for email in st.session_state.emails if email['uid'] not in moved_uids]
                    else:
                        st.toast("Move operation attempted, but no emails were moved.")
                st.session_state.manual_selection_mode = False
                st.rerun()
            else:
                st.warning("No emails selected from Action, Read, or Events categories.")
        else:
            st.warning("No emails loaded.")
    if st.button("Cancel Manual Selection"):
        st.session_state.manual_selection_mode = False
        # Reset select column if needed
        # st.session_state.df['Select'] = False
        st.rerun()

# --- Email Editor Table ---
if not st.session_state.df.empty:
    # --- Ensure latest emails are always at the top before display ---
    st.session_state.df = st.session_state.df.sort_values(by='date', ascending=False)

    # Define base column configuration
    column_config = {
        "uid": None, # Always hide UID
        "category": st.column_config.SelectboxColumn(
            "Category",
            options=["Uncategorised", "Action", "Read", "Events", "Information"],
            required=True,
        ),
        # Define other columns if needed for width etc.
    }
    # Define columns to disable editing (base)
    disabled_columns = ["date", "from", "subject", "uid", "category"]

    # Conditionally add the 'Select' column configuration
    if st.session_state.manual_selection_mode:
        column_config["Select"] = st.column_config.CheckboxColumn(
            "Select",
            help="Select emails to move",
            default=False,
        )
        # Allow editing the Select column only in manual mode
        # No change needed to disabled_columns as 'Select' is not in the base list
    else:
        # Hide the Select column if not in manual mode
        column_config["Select"] = None
        # Add Select to disabled if it exists but shouldn't be editable (belt-and-braces)
        # disabled_columns.append("Select") # Not strictly needed if hidden

    edited_df = st.data_editor(
        st.session_state.df, # Pass the potentially re-sorted DataFrame
        use_container_width=True,
        height=600,
        column_config=column_config, # Pass the dynamic config
        disabled=disabled_columns, # Pass the appropriate disabled list
        key="data_editor"
    )

    # Update session state if edits were made
    if not edited_df.equals(st.session_state.df):
        st.session_state.df = edited_df
        # Don't show toast for selection changes, only category?
        # Check which column changed if necessary

    # --- Category Summary --- (Ensure it recalculates)
    if not st.session_state.df.empty:
        category_counts = st.session_state.df['category'].value_counts().sort_index()
        summary_items = [f"{cat}: {count}" for cat, count in category_counts.items()]
        summary_text = " | ".join(summary_items)
        st.markdown(f"**Inbox Status:** {summary_text}")

else:
    st.write("No emails to display.")
