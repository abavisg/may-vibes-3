import streamlit as st
import logging
import os
import email
import pandas as pd
import ollama

# Import from local modules
from email_client import connect_oauth
from email_mover import move_emails
from email_fetcher import fetch_inbox_emails
from llm_categorizer import categorize_emails_llm, DEFAULT_MODEL
from email_modal import EmailModal
from status_component import setup_status_component, is_electron

# Import from new utility modules
from constants import (
    CAT_METHOD_LLM, 
    CAT_METHOD_RULES,
    CAT_ACTION, 
    CAT_READ, 
    CAT_EVENTS, 
    CAT_INFO, 
    CAT_UNCATEGORISED,
    MOVE_CATEGORIES,
    RULE_CATEGORIES
)
from categorizer import categorize_emails as categorize_emails_rules
from helper_functions import decode_subject, get_ollama_models
from styles import get_app_styles, get_debug_styles, get_row_style_html
from html_generators import (
    generate_status_html, 
    generate_progress_html, 
    generate_complete_html, 
    generate_category_pill_js,
    generate_email_table_html
)

# --- Setup Logging ---
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 

# --- Modal Factory Pattern ---
class ModalFactory:
    """Factory class for creating and handling different types of confirmation modals"""
    
    @staticmethod
    def create_confirmation_message(confirmation_type, **kwargs):
        """Create a confirmation message based on the confirmation type and additional data"""
        if confirmation_type == "move":
            move_counts = kwargs.get('move_counts', {})
            confirmation_msg = "Are you sure you want to move: <br>"
            move_details = []
            
            for cat, count in move_counts.items():
                if count > 0:
                    # Add category-specific styling with colors matching the UI
                    if cat == "Action":
                        color = "#ff4c4c"
                    elif cat == "Read":
                        color = "#4c7bff"
                    elif cat == "Information":
                        color = "#4cd97b"
                    elif cat == "Events":
                        color = "#ff9e4c"
                    else:
                        color = "#e0e0e0"
                    
                    styled_cat = f'<span style="color: {color}; font-weight: 500;">{cat}</span>'
                    move_details.append(f"{count} {'email' if count == 1 else 'emails'} to {styled_cat}")
            
            confirmation_msg += "<br>".join(move_details)
            return confirmation_msg
            
        elif confirmation_type == "archive":
            info_count = kwargs.get('info_count', 0)
            confirmation_msg = "Are you sure you want to archive: <br>"
            # Style for Information category
            color = "#4cd97b"  # Green for Information
            styled_cat = f'<span style="color: {color}; font-weight: 500;">@Information</span>'
            confirmation_msg += f"{info_count} {'email' if info_count == 1 else 'emails'} with {styled_cat}"
            return confirmation_msg
            
        else:
            # Default message
            return "Are you sure you want to proceed?"
    
    @staticmethod
    def show_modal_content(modal, confirmation_type, imap_client, df, emails):
        """Display the appropriate modal content based on confirmation type"""
        with modal.container():
            # Get the confirmation message from session state
            confirmation_msg = st.session_state.get('confirmation_message', "Are you sure you want to proceed?")
            
            # Display the confirmation message with HTML formatting
            st.markdown(
                f'<div style="font-size: 16px; margin-bottom: 20px; line-height: 1.5;">{confirmation_msg}</div>', 
                unsafe_allow_html=True
            )
            
            # Create columns for the confirmation buttons
            confirm_cols = st.columns([1, 1])
            
            # Different actions based on confirmation type
            if confirmation_type == "move":
                # Move emails confirmation
                with confirm_cols[0]:
                    if st.button("Yes, Move Emails", key="modal_confirm_move_btn", 
                               use_container_width=True,
                               type="primary", 
                               help="Move the emails to their category folders"):
                        ModalFactory.handle_move_confirmation(imap_client, df, emails)
                        # Close the modal and rerun to refresh the UI
                        modal.close()
                        st.rerun()
            
            elif confirmation_type == "archive":
                # Archive Information emails confirmation
                with confirm_cols[0]:
                    if st.button("Yes, Archive", key="modal_confirm_archive_btn", 
                               use_container_width=True,
                               type="primary", 
                               help="Archive all Information emails"):
                        ModalFactory.handle_archive_confirmation(imap_client, df, emails)
                        # Close the modal and rerun to refresh the UI
                        modal.close()
                        st.rerun()
            
            # Cancel button (same for all confirmation types)
            with confirm_cols[1]:
                if st.button("Cancel", key="modal_confirm_cancel_btn", type="secondary", use_container_width=True):
                    # Close the modal and rerun to refresh the UI
                    modal.close()
                    st.rerun()
    
    @staticmethod
    def handle_move_confirmation(imap_client, df, emails):
        """Handle the confirmation to move emails"""
        if not imap_client:
            st.error("IMAP client not available. Cannot move emails.")
            return
            
        with st.spinner("Moving emails..."):
            relevant_df = df[df['category'].isin(MOVE_CATEGORIES)].copy()
            if not relevant_df.empty:
                uids_to_move = relevant_df['uid'].tolist()
                category_map = pd.Series(relevant_df.category.values, index=relevant_df.uid).to_dict()
                moved_uids = move_emails(imap_client, uids_to_move, category_map)
                if moved_uids is not None:
                    st.toast(f"Moved {len(moved_uids)} email(s).")
                    st.session_state.df = df[~df['uid'].isin(moved_uids)]
                    st.session_state.emails = [email for email in emails if email['uid'] not in moved_uids]
                else:
                    st.error("Move operation failed. Check logs.")
            else:
                st.toast("No relevant emails found to move.")
    
    @staticmethod
    def handle_archive_confirmation(imap_client, df, emails):
        """Handle the confirmation to archive Information emails"""
        if not imap_client:
            st.error("IMAP client not available. Cannot move emails.")
            return
            
        with st.spinner("Archiving Information emails..."):
            # Filter to Information category only
            info_df = df[df['category'] == CAT_INFO].copy()
            
            if not info_df.empty:
                uids_to_move = info_df['uid'].tolist()
                # Create a map where all are Information category
                category_map = {uid: CAT_INFO for uid in uids_to_move}
                
                # Use the existing move_emails function
                moved_uids = move_emails(imap_client, uids_to_move, category_map)
                
                if moved_uids is not None:
                    st.success(f"Archived {len(moved_uids)} Information email(s) successfully!")
                    # Remove moved emails from dataframe and email list
                    st.session_state.df = df[~df['uid'].isin(moved_uids)]
                    st.session_state.emails = [email for email in emails if email['uid'] not in moved_uids]
                else:
                    st.error("Archive operation failed. Check logs.")
            else:
                st.info("No Information emails found to archive.")

# --- Page Configuration ---
st.set_page_config(
    page_title="Smart Inbox Cleaner",
    page_icon="📥",
    layout="wide"
)

# --- Apply CSS Styles ---
st.markdown(get_app_styles(), unsafe_allow_html=True)

# Add the debug CSS separately when enabled
if st.session_state.get('debug_layout', False):
    st.markdown(get_debug_styles(), unsafe_allow_html=True)

# --- Initialize Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'imap_client' not in st.session_state:
    st.session_state.imap_client = None
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "Not connected"
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
if 'categorization_method' not in st.session_state:
    st.session_state.categorization_method = CAT_METHOD_LLM # Default to LLM
if 'selected_llm_model' not in st.session_state:
    st.session_state.selected_llm_model = DEFAULT_MODEL # Default LLM model
if 'categorization_running' not in st.session_state:
    st.session_state.categorization_running = False
if 'table_editable' not in st.session_state:
    st.session_state.table_editable = True # Controls whether the table is editable
if 'progress_text' not in st.session_state:
    st.session_state.progress_text = None # Stores current progress text
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# --- App Header ---
st.markdown("<h1 style='text-align: left; margin-bottom: 30px;'>📥 Smart Inbox Cleaner</h1>", unsafe_allow_html=True)

# --- Add Categorise Inbox Button below the title ---
if st.session_state.logged_in:
    # Create a layout with columns for left alignment of the button and progress text
    left_col, progress_col = st.columns([1, 3])
    
    # Categorise Inbox button in the left column
    with left_col:
        if not st.session_state.categorization_running:
            if st.button("Categorise Inbox", key="process_inbox_button", type="primary", use_container_width=True):
                if not st.session_state.emails:
                    st.warning("No emails fetched to categorize.")
                else:
                    st.session_state.categorization_running = True
                    st.session_state.table_editable = False # Make table non-editable during processing
                    # Initialize progress info in session state
                    st.session_state.progress_text = "Categorising 0 out of 0 emails (0%)"
                    # Rerun to switch button and start processing below
                    st.rerun()
        else:
            if st.button("Stop Categorising", key="stop_process_button", type="secondary", use_container_width=True):
                st.session_state.categorization_running = False # Signal stop
                st.session_state.table_editable = True # Make table editable again
                
                # Reset categorization state to initial state
                st.session_state.categorization_run = False
                
                # Reset all emails to uncategorized state if any were processed
                if not st.session_state.df.empty:
                    st.session_state.df['category'] = CAT_UNCATEGORISED
                
                st.warning("Processing stopped. Changes cancelled.")
                st.rerun()
    
    # Display progress text in the right column when processing
    with progress_col:
        if st.session_state.categorization_running:
            # Create a placeholder for progress updates
            progress_placeholder = st.empty()
            # Initialize with the current progress text
            progress_text = st.session_state.get('progress_text', 'Categorising 0 out of 0 emails (0%)')
            progress_placeholder.markdown(generate_progress_html(progress_text), unsafe_allow_html=True)
            
            # Store the placeholder in session state for the callback to use
            st.session_state.progress_placeholder = progress_placeholder
        elif st.session_state.get('progress_text') and st.session_state.categorization_run:
            # Show a success message briefly, then clear it on the next rerun
            st.markdown(generate_complete_html(st.session_state.get('progress_text')), unsafe_allow_html=True)
            # Clear the progress text for future runs
            st.session_state.progress_text = None
    
    # Add spacing after the button
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# --- Login Section ---
if not st.session_state.logged_in:
    st.info("Please log in with your Google account to access your Gmail inbox.")
    if st.button("Login with Google"):
        with st.spinner("Attempting Google Login and IMAP Connection..."):
            client, status = connect_oauth()
            if client:
                st.session_state.logged_in = True
                st.session_state.imap_client = client
                st.session_state.connection_status = status
                st.success("Login Successful! " + status)
                st.rerun() # Rerun to hide login button and show main app
            else:
                st.session_state.logged_in = False
                st.session_state.imap_client = None
                st.session_state.connection_status = status
                st.error(f"Login Failed: {status}")
    # Display status if login hasn't been attempted or failed
    st.write(f"Current Status: {st.session_state.connection_status}")

# --- Main Application UI (Show only if logged in) ---
else:
    # --- Categorization Method Selector ---
    st.sidebar.title("Settings")
    
    # --- Connection Status in Sidebar ---
    connection_status_container = st.sidebar.container()
    with connection_status_container:
        # Get email address from connection status
        email_address = ""
        status_parts = st.session_state.connection_status.split(" as ")
        if len(status_parts) > 1:
            email_address = status_parts[1]
        
        # Display email address in a cleaner format
        st.sidebar.markdown(f"### {email_address}")
        
        # Logout button moved to bottom of sidebar

    st.sidebar.markdown("---")
    
    # --- Categorization Method Selector ---
    st.sidebar.markdown("### Categorization")
    st.session_state.categorization_method = st.sidebar.radio(
        "",
        [CAT_METHOD_LLM, CAT_METHOD_RULES],
        index=0 if st.session_state.categorization_method == CAT_METHOD_LLM else 1,
        key="cat_method_selector",
        label_visibility="collapsed"
    )

    # --- LLM Model Selector (Conditional) ---
    if st.session_state.categorization_method == CAT_METHOD_LLM:
        # Call the function now that it's defined
        available_models = get_ollama_models()
        # Ensure the currently selected model is in the list, add if not (might be manually entered)
        if st.session_state.selected_llm_model not in available_models:
             available_models.append(st.session_state.selected_llm_model)
        
        # Find the index of the currently selected model
        try:
             default_index = available_models.index(st.session_state.selected_llm_model)
        except ValueError:
             default_index = 0 # Fallback if model somehow isn't in list
             st.session_state.selected_llm_model = available_models[0] # Reset selection
        
        st.sidebar.markdown("### LLM Model")
        st.session_state.selected_llm_model = st.sidebar.selectbox(
            "",
            options=available_models,
            index=default_index,
            key="llm_model_selector",
            label_visibility="collapsed"
        )
        
    # --- Debug Mode Toggle ---
    with st.sidebar.expander("Developer Options", expanded=False):
        st.session_state.debug_mode = st.checkbox(
            "Debug Mode", 
            value=st.session_state.debug_mode,
            help="Show additional debugging information"
        )
        
        # Add layout debug toggle with a callback to force rerun
        if 'debug_layout' not in st.session_state:
            st.session_state.debug_layout = False
        
        # Helper function to toggle debug layout and force rerun
        def toggle_debug_layout():
            st.session_state.debug_layout = not st.session_state.debug_layout
            st.rerun()
            
        st.button(
            f"{'Disable' if st.session_state.debug_layout else 'Enable'} Debug Layout", 
            on_click=toggle_debug_layout,
            help="Show colored backgrounds for layout debugging"
        )
        
        if st.session_state.debug_mode:
            st.write("App Environment:")
            st.json({
                "ELECTRON_APP_VERSION": os.environ.get("ELECTRON_APP_VERSION", "Not set"),
                "ELECTRON_RUN_AS_NODE": os.environ.get("ELECTRON_RUN_AS_NODE", "Not set"),
                "Is Electron (detected)": is_electron()
            })
    
    # --- Add Status Component to Sidebar ---
    setup_status_component()
    
    # --- Add Logout Button at the very bottom of the sidebar ---
    logout_container = st.sidebar.container()
    if logout_container.button("⚪ Logout", key="sidebar_logout", type="secondary", use_container_width=True):
        if st.session_state.imap_client:
            try:
                st.session_state.imap_client.logout()
                logging.info("IMAP client logged out.")
            except Exception as e:
                logging.error(f"Error during IMAP logout: {e}")
        
        # Clear session state related to login
        st.session_state.logged_in = False
        st.session_state.imap_client = None
        st.session_state.connection_status = "Logged out."
        st.session_state.emails = []
        st.session_state.df = pd.DataFrame()
        st.session_state.categorization_run = False
        st.session_state.show_move_confirmation = False
        st.session_state.manual_selection_mode = False
        st.toast("You have been logged out.")
        st.rerun()

    # --- Fetch Emails (Only if not already fetched) ---
    if not st.session_state.emails:
        with st.spinner("Fetching initial emails..."):
            try:
                if st.session_state.imap_client:
                    st.session_state.emails = fetch_inbox_emails(st.session_state.imap_client)
                    if st.session_state.emails:
                        temp_df = pd.DataFrame(st.session_state.emails)
                        temp_df['category'] = CAT_UNCATEGORISED # Use constant
                        temp_df['Select'] = False
                        temp_df['date'] = pd.to_datetime(temp_df['date']) # Ensure date is datetime type
                        
                        # Decode encoded email subjects - only if they contain encoding patterns
                        temp_df['subject'] = temp_df['subject'].apply(lambda s: decode_subject(s) if isinstance(s, str) and "=?UTF-8?" in s else s)
                        
                        temp_df = temp_df.sort_values(by='date', ascending=False)
                        # Define initial column order
                        st.session_state.df = temp_df[['Select', 'date', 'from', 'subject', 'category', 'uid']]
                    else:
                        st.write("No emails fetched or inbox is empty.")
                else:
                    st.error("IMAP client not available. Cannot fetch emails.")
            except Exception as e:
                st.error(f"Error fetching emails: {e}")

    # Update original email list to have decoded subjects
    for email in st.session_state.emails:
        if 'subject' in email and isinstance(email['subject'], str) and "=?UTF-8?" in email['subject']:
            email['subject'] = decode_subject(email['subject'])

    # Any time we update the dataframe, ensure subjects are decoded
    if not st.session_state.df.empty and 'subject' in st.session_state.df.columns:
        st.session_state.df['subject'] = st.session_state.df['subject'].apply(lambda s: decode_subject(s) if isinstance(s, str) and "=?UTF-8?" in s else s)

    # --- Processing Logic (Only runs when Process Inbox button is clicked) ---
    if st.session_state.categorization_running:
        # This block runs after the rerun triggered by the Process Inbox button
        start_time = pd.Timestamp.now()
        
        # --- Callbacks --- 
        def update_progress(current, total):
            # Update the progress text in session state
            progress_text = f"Categorising {current} out of {total} emails ({int(current/total*100)}%)"
            st.session_state.progress_text = progress_text
            
            # Update the progress placeholder if it exists
            if 'progress_placeholder' in st.session_state:
                progress_placeholder = st.session_state.progress_placeholder
                progress_placeholder.markdown(generate_progress_html(progress_text), unsafe_allow_html=True)
            
        def check_if_stopped():
            return not st.session_state.categorization_running
        
        # --- Run Categorization --- 
        categorized_email_list = None
        process_completed = False
        try:
            # Only use spinner for the fast rule-based method
            if st.session_state.categorization_method == CAT_METHOD_LLM:
                categorized_email_list = categorize_emails_llm(
                    st.session_state.emails.copy(), 
                    model_name=st.session_state.selected_llm_model,
                    progress_callback=update_progress,
                    stop_checker=check_if_stopped
                )
                process_completed = categorized_email_list is not None
            else: # Rule-Based
                spinner_text = f"Running {st.session_state.categorization_method}..."
                with st.spinner(spinner_text): 
                    categorized_email_list = categorize_emails_rules(
                        st.session_state.emails.copy()
                    )
                process_completed = True
        except Exception as e:
            logging.error(f"Error during categorization: {e}", exc_info=True)
            st.error(f"An error occurred during categorization: {e}")
            process_completed = False
        finally:
            # --- Handle Results & State Reset --- 
            was_stopped = not st.session_state.categorization_running # Check if stop was clicked during run
            st.session_state.categorization_running = False # Ensure state is reset
            st.session_state.table_editable = True # Make table editable again
            
            if was_stopped:
                logging.info("Categorization stopped by user.")
                st.session_state.progress_text = "Categorisation cancelled."
                # Clear the progress placeholder if we're stopping from user action
                if 'progress_placeholder' in st.session_state:
                    st.session_state.pop('progress_placeholder')
                pass 
            elif categorized_email_list is None and st.session_state.categorization_method == CAT_METHOD_LLM:
                # Reset to initial state when categorization fails
                st.session_state.categorization_run = False
                # Reset emails to uncategorized state
                if not st.session_state.df.empty:
                    st.session_state.df['category'] = CAT_UNCATEGORISED
                
                st.session_state.progress_text = "Categorisation failed."
                # Clear the progress placeholder
                if 'progress_placeholder' in st.session_state:
                    st.session_state.pop('progress_placeholder')
                st.warning("Categorization stopped or failed unexpectedly.")
            elif categorized_email_list:
                logging.info(f"Categorization successful. Received {len(categorized_email_list)} emails back.")
                
                # Decode all subjects in the categorized list - only if they contain encoding patterns
                for email in categorized_email_list:
                    if 'subject' in email and isinstance(email['subject'], str) and "=?UTF-8?" in email['subject']:
                        email['subject'] = decode_subject(email['subject'])
                
                # Create a mapping of UIDs to categories from the categorized results
                categorized_uids = set()
                category_map = {}
                for email in categorized_email_list:
                    if 'uid' in email and 'category' in email and email['category'] is not None:
                        uid = email['uid']
                        categorized_uids.add(uid)
                        category_map[uid] = email['category']
                
                # Preserve original categories for emails not in the categorized batch
                if not st.session_state.df.empty:
                    for idx, row in st.session_state.df.iterrows():
                        uid = row['uid']
                        if uid not in categorized_uids and row['category'] != CAT_UNCATEGORISED:
                            # Find the corresponding email in the list and preserve its category
                            for email in categorized_email_list:
                                if email['uid'] == uid and ('category' not in email or email['category'] is None):
                                    email['category'] = row['category']
                
                # Create DataFrame with the updated data
                temp_df = pd.DataFrame(categorized_email_list)
                temp_df['Select'] = False
                temp_df['date'] = pd.to_datetime(temp_df['date'])
                temp_df = temp_df.sort_values(by='date', ascending=False)
                
                # Ensure 'category' column exists before selecting it
                if 'category' not in temp_df.columns:
                    logging.error("'category' column missing from DataFrame after categorization!")
                    temp_df['category'] = CAT_UNCATEGORISED # Add default if missing
                else:
                    # Fill any None/NaN values with Uncategorised
                    temp_df['category'].fillna(CAT_UNCATEGORISED, inplace=True)
                    
                # Create the dataframe with selected columns
                st.session_state.df = temp_df[['Select', 'date', 'from', 'subject', 'category', 'uid']]
                
                st.session_state.categorization_run = True
                st.session_state.show_move_confirmation = False
                duration = pd.Timestamp.now() - start_time
                st.session_state.progress_text = f"Categorisation complete in {duration.total_seconds():.2f}s"
                # Clear the progress placeholder
                if 'progress_placeholder' in st.session_state:
                    st.session_state.pop('progress_placeholder')
                st.toast(f"Complete in {duration.total_seconds():.2f}s")
                st.rerun()  # Add rerun to refresh the UI state
            else: # Completed but no results
                # Reset to initial state when no results are produced
                st.session_state.categorization_run = False
                # Reset emails to uncategorized state
                if not st.session_state.df.empty:
                    st.session_state.df['category'] = CAT_UNCATEGORISED
                    
                st.session_state.progress_text = "Categorisation completed with no results."
                logging.warning("Categorization function returned an empty list or None (and wasn't stopped).")
                st.warning("Categorisation ran but produced no results.")
                # Force a rerun to reset the UI
                st.rerun()

    # --- Email Editor Table ---
    if not st.session_state.df.empty:
        # Ensure latest emails are always at the top before display
        st.session_state.df = st.session_state.df.sort_values(by='date', ascending=False)

        # Add batch information (similar to the design)
        total_emails = len(st.session_state.emails)
        current_batch_size = min(250, len(st.session_state.df))
        
        # Get category counts 
        category_counts = st.session_state.df['category'].value_counts().sort_index()
        
        # Generate and display the status HTML
        status_html = generate_status_html(category_counts, current_batch_size, total_emails)
        st.markdown(status_html, unsafe_allow_html=True)

        # Add row styling CSS
        st.markdown(get_row_style_html(), unsafe_allow_html=True)

        # Create a loading overlay for the table when processing
        table_disabled = False
        if st.session_state.categorization_running:
            # Add a class to mark the table as disabled instead of adding an overlay element
            st.markdown('<div class="disabled-table">', unsafe_allow_html=True)
            table_disabled = True

        # Create a temporary dataframe without the color column
        display_df = st.session_state.df.copy()

        # Before displaying the table, ensure subjects are decoded
        if not display_df.empty and 'subject' in display_df.columns:
            # Only decode if subject is a string and contains encoding pattern
            display_df['subject'] = display_df['subject'].apply(lambda s: decode_subject(s) if isinstance(s, str) and "=?UTF-8?" in s else s)
        
        # Display the custom HTML table instead of the data editor
        # Only include the columns we want to display in the HTML table
        display_cols = ['date', 'from', 'subject', 'category']
        html_display_df = display_df[display_cols].copy() if not display_df.empty else pd.DataFrame(columns=display_cols)
        
        # Generate and display the HTML table
        email_table_html = generate_email_table_html(html_display_df)
        
        # Display the HTML table using components.v1.html
        st.components.v1.html(email_table_html, height=600, scrolling=True)
        
        # Handle category changes from HTML dropdown
        # This uses URL query parameters which will be updated via JavaScript
        params = st.query_params
        if 'email_id' in params and 'category' in params:
            try:
                # Extract the email_id index and category from the parameters
                email_idx = int(params['email_id'].replace('email_', ''))
                new_category = params['category']
                
                # Find and update the appropriate email in the dataframe
                if email_idx < len(st.session_state.df):
                    st.session_state.df.iloc[email_idx, st.session_state.df.columns.get_loc('category')] = new_category
                    
                    # Clear the parameters to avoid repeated updates
                    params.clear()
                    
                    # Refresh the page to show the updated categories
                    st.rerun()
            except (ValueError, KeyError, IndexError) as e:
                st.error(f"Error processing category update: {e}")
                params.clear()
        
        # Close the disabled-table div if it was opened
        if table_disabled:
            st.markdown('</div>', unsafe_allow_html=True)

        # --- Action Buttons Row (only show when categorization is completed) ---
        if st.session_state.categorization_run and not st.session_state.categorization_running:
            # Move to the bottom of the UI with some space
            st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
            
            # Initialize the modal component
            if 'confirm_modal' not in st.session_state:
                st.session_state.confirm_modal = EmailModal(
                    "Moving emails confirmation", 
                    key="confirm_move_modal",
                    padding=20,
                    max_width=600,
                    hide_close_button=True
                )
            
            # Update modal title based on confirmation type
            def update_modal_title(modal, title):
                """Update the title of the modal"""
                # Access the internal title of the modal
                modal._title = title
            
            # Initialize confirmation type state if not exists
            if 'confirmation_type' not in st.session_state:
                st.session_state.confirmation_type = None
            
            # Add custom CSS to reduce button spacing
            st.markdown("""
            <style>
            .button-row {
                display: flex;
                align-items: center;
                margin-bottom: 16px;
            }
            .button-row > div {
                padding: 0 !important;
                margin: 0 !important;
            }
            .button-row button {
                margin: 0 !important;
            }
            .confirm-button {
                padding-right: 4px !important;
            }
            .archive-button {
                padding-left: 4px !important;
                padding-right: 10px !important;
            }
            .next-button {
                padding-left: 10px !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Open the button row container
            st.markdown('<div class="button-row">', unsafe_allow_html=True)
            
            # Create three-column layout with custom widths
            button_cols = st.columns([1.1, 1.8, 1.1])
            
            # Confirm button in first column
            with button_cols[0]:
                st.markdown('<div class="confirm-button">', unsafe_allow_html=True)
                # Only enable after categorization has run
                confirm_disabled = not st.session_state.categorization_run
                        
                if st.button("Confirm & Move", key="confirm_move_btn", type="primary", disabled=confirm_disabled, use_container_width=True):
                    # Calculate email counts by category
                    current_counts = st.session_state.df['category'].value_counts()
                    st.session_state.move_counts = {cat: current_counts.get(cat, 0) for cat in MOVE_CATEGORIES if cat in current_counts and current_counts.get(cat, 0) > 0}
                    
                    if st.session_state.move_counts:
                        # Create confirmation message with better formatting and styling
                        confirmation_msg = ModalFactory.create_confirmation_message(
                            "move",
                            move_counts=st.session_state.move_counts
                        )
                        
                        # Store for use in modal
                        st.session_state.confirmation_message = confirmation_msg
                        st.session_state.confirmation_type = "move"
                        
                        # Set the modal title
                        update_modal_title(st.session_state.confirm_modal, "Moving emails confirmation")
                        
                        # Open the modal
                        st.session_state.confirm_modal.open()
                        st.rerun()
                    else:
                        st.toast(f"No emails found in {', '.join(MOVE_CATEGORIES)} categories to move.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Archive Information Emails button in second column
            with button_cols[1]:
                st.markdown('<div class="archive-button">', unsafe_allow_html=True)
                # Only enable after categorization has run
                archive_disabled = not st.session_state.categorization_run
                
                if st.button("Archive Information Emails", key="archive_info_btn", type="secondary", disabled=archive_disabled, use_container_width=True):
                    # Count Information emails
                    info_count = len(st.session_state.df[st.session_state.df['category'] == CAT_INFO])
                    
                    if info_count > 0:
                        # Create confirmation message with better formatting and styling
                        confirmation_msg = ModalFactory.create_confirmation_message(
                            "archive",
                            info_count=info_count
                        )
                        
                        # Store for use in modal
                        st.session_state.confirmation_message = confirmation_msg
                        st.session_state.confirmation_type = "archive"
                        
                        # Set the modal title
                        update_modal_title(st.session_state.confirm_modal, "Archive emails confirmation")
                        
                        # Open the modal
                        st.session_state.confirm_modal.open()
                        st.rerun()
                    else:
                        st.toast("No Information emails to archive.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Next Batch button in third column
            with button_cols[2]:
                st.markdown('<div class="next-button">', unsafe_allow_html=True)
                if st.button("Next Batch", key="next_batch_btn", type="secondary", use_container_width=True):
                    # Implementation could be added later
                    st.toast("Next batch functionality would be implemented here")
                st.markdown('</div>', unsafe_allow_html=True)
                
            # Close the button row container
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Modal content setup
            if st.session_state.confirm_modal.is_open():
                # Use the factory to handle modal content
                confirmation_type = st.session_state.get('confirmation_type')
                ModalFactory.show_modal_content(
                    st.session_state.confirm_modal,
                    confirmation_type,
                    st.session_state.imap_client,
                    st.session_state.df,
                    st.session_state.emails
                )

    elif st.session_state.logged_in:
        # Show only if logged in but no emails were found/loaded
        st.write("No emails to display.")
