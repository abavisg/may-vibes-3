import streamlit as st
import logging # Use logging
# Removed os import
from email_client import connect_oauth
from email_mover import move_emails
from email_fetcher import fetch_inbox_emails
from categorizer import (
    categorize_emails as categorize_emails_rules, # Rename for clarity
    CAT_ACTION, CAT_READ, CAT_EVENTS, CAT_INFO, CAT_UNCATEGORISED, # Import constants
    MOVE_CATEGORIES, RULE_CATEGORIES
)
# Import the new LLM categorizer function
from llm_categorizer import categorize_emails_llm, DEFAULT_MODEL
import pandas as pd
import ollama # Import ollama to list models

# --- Setup Logging (Optional: Configure Streamlit's logger if needed) ---
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 
# Streamlit might configure logging, check behaviour if duplicating.

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

# --- Constants ---
CAT_METHOD_LLM = "LLM Categorization"
CAT_METHOD_RULES = "Rule-Based Categorization"

# --- Helper Function to Get Ollama Models (Moved Here) ---
def get_ollama_models():
    """Fetches the list of available Ollama models."""
    try:
        models_info = ollama.list()
        # Return model names, handling potential variations in key casing or structure
        return sorted([model.get('name') for model in models_info.get('models', []) if model.get('name')])
    except Exception as e:
        # Use logging instead of st.warning here as it might be called before UI is fully ready
        logging.warning(f"Could not fetch Ollama models. Is Ollama running? Error: {e}")
        return [DEFAULT_MODEL] # Fallback to default

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

# Removed Load Environment Variables
# gmail_address = os.getenv('GMAIL_ADDRESS', 'Not set') # No longer needed here

# --- App Header ---
st.title('📥 Smart Inbox Cleaner')

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
    st.success(f"Status: {st.session_state.connection_status}")

    # --- Categorization Method Selector ---
    st.sidebar.title("Settings")
    st.session_state.categorization_method = st.sidebar.radio(
        "Categorization Method",
        [CAT_METHOD_LLM, CAT_METHOD_RULES],
        index=0 if st.session_state.categorization_method == CAT_METHOD_LLM else 1,
        key="cat_method_selector"
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
             
        st.session_state.selected_llm_model = st.sidebar.selectbox(
            "Select LLM Model (Ollama)",
            options=available_models,
            index=default_index,
            key="llm_model_selector",
            help="Ensure the selected model is available in your local Ollama instance."
        )

    # --- REMOVED: Test Mode Toggle ---
    # No longer needed as limit is controlled by .env

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
                        temp_df = temp_df.sort_values(by='date', ascending=False)
                        # Define initial column order
                        st.session_state.df = temp_df[['Select', 'date', 'from', 'subject', 'category', 'uid']]
                    else:
                        st.write("No emails fetched or inbox is empty.")
                else:
                    st.error("IMAP client not available. Cannot fetch emails.")
            except Exception as e:
                st.error(f"Error fetching emails: {e}")
                # Log out on critical fetch error?
                # st.session_state.logged_in = False
                # st.session_state.imap_client = None
                # st.rerun()

    # --- Display Area ---
    st.header("Inbox Emails")

    # --- Main Action Buttons (Hidden in Manual Selection Mode) ---
    if not st.session_state.manual_selection_mode:
        action_col, move_col = st.columns([1, 3]) # Main columns for Actions and Move
        
        # Categorization Section
        with action_col:
            st.write("**Categorize**")
            st.caption(f"Using: {st.session_state.categorization_method}")
            if st.session_state.categorization_method == CAT_METHOD_LLM:
                 st.caption(f"Model: {st.session_state.selected_llm_model}")

            # Create columns for the button and the progress bar
            button_col, progress_col = st.columns([1, 2]) # Sub-columns within action_col

            with button_col:
                button_placeholder = st.empty()
            with progress_col:
                # Placeholder for the progress bar - defined in the right column
                progress_bar_placeholder = st.empty()

            # --- Button Logic --- 
            if st.session_state.categorization_running:
                 # Show Stop button if running
                 # Use the button placeholder directly
                 if button_placeholder.button("⏹️ Stop", key="stop_cat_button", help="Stop categorization after the current email."):
                      st.session_state.categorization_running = False # Signal stop
                      st.warning("Stop requested. Categorization cancelled.")
                      progress_bar_placeholder.empty() # Clear progress bar
                      st.rerun()
            else:
                 # Show Run button if not running
                 # Use the button placeholder directly
                 if button_placeholder.button("▶️ Run", key="run_cat_button", help="Start categorization process."):
                      if not st.session_state.emails:
                           st.warning("No emails fetched to categorize.")
                      else:
                           st.session_state.categorization_running = True
                           # Rerun to switch button and start processing below
                           st.rerun() 
                           
            # --- Processing Logic (Runs only if currently running) ---
            if st.session_state.categorization_running:
                 # This block runs *after* the rerun triggered by the Run button
                 start_time = pd.Timestamp.now()
                 progress_bar = None 
                 if st.session_state.categorization_method == CAT_METHOD_LLM:
                      progress_bar = progress_bar_placeholder.progress(0, text="Starting LLM categorization...")
                 
                 # --- Callbacks --- 
                 def update_progress(current, total):
                     if progress_bar:
                         progress_text = f"Processing email {current}/{total}..."
                         progress_value = current / total
                         try:
                             progress_bar.progress(progress_value, text=progress_text)
                         except Exception as e:
                             logging.warning(f"Could not update progress bar: {e}")
                 
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
                     
                     if was_stopped:
                         logging.info("Categorization stopped by user.") # Added logging
                         pass 
                     elif categorized_email_list is None and st.session_state.categorization_method == CAT_METHOD_LLM:
                         st.warning("Categorization stopped or failed unexpectedly.")
                         progress_bar_placeholder.empty()
                     elif categorized_email_list:
                         # -- START Added Logging --
                         logging.info(f"Categorization successful. Received {len(categorized_email_list)} emails back.")
                         if len(categorized_email_list) > 0:
                             # Log categories from the first few results
                             try:
                                 categories_sample = [e.get('category', 'MISSING') for e in categorized_email_list[:5]]
                                 logging.info(f"Sample categories from result list: {categories_sample}")
                             except Exception as log_err:
                                 logging.error(f"Error logging category sample: {log_err}")
                         # -- END Added Logging --
                         
                         # ... (update dataframe logic) ...
                         temp_df = pd.DataFrame(categorized_email_list)
                         temp_df['Select'] = False
                         temp_df['date'] = pd.to_datetime(temp_df['date'])
                         temp_df = temp_df.sort_values(by='date', ascending=False)
                         # Ensure 'category' column exists before selecting it
                         if 'category' not in temp_df.columns:
                             logging.error("'category' column missing from DataFrame after categorization!")
                             temp_df['category'] = CAT_UNCATEGORISED # Add default if missing
                             
                         st.session_state.df = temp_df[['Select', 'date', 'from', 'subject', 'category', 'uid']]
                         # -- START Added Logging --
                         logging.info(f"Updated st.session_state.df. Shape: {st.session_state.df.shape}")
                         if not st.session_state.df.empty:
                             logging.info(f"First 5 rows of updated st.session_state.df:\n{st.session_state.df.head().to_string()}")
                         # -- END Added Logging --
                         
                         st.session_state.categorization_run = True
                         st.session_state.show_move_confirmation = False
                         duration = pd.Timestamp.now() - start_time
                         st.toast(f"Categorization complete in {duration.total_seconds():.2f}s!")
                         if progress_bar: progress_bar.progress(1.0, text="Categorization complete!") 
                     else: # Completed but no results
                         logging.warning("Categorization function returned an empty list or None (and wasn't stopped).") # Added logging
                         st.warning("Categorization ran but produced no results.")
                         progress_bar_placeholder.empty()
                 
                     # Remove the final rerun - let Streamlit handle update based on state changes
                     # if final_rerun_needed:
                     #      st.rerun()

        # Move Emails Section (Keep in second column)
        with move_col:
             st.write("**Move Emails**") # Add subheader
             # Determine enabled state for moving
             move_button_disabled = True
             if st.session_state.categorization_run and not st.session_state.df.empty:
                 category_counts = st.session_state.df['category'].value_counts()
                 relevant_present = any(cat in category_counts for cat in MOVE_CATEGORIES if category_counts.get(cat, 0) > 0)
                 if relevant_present:
                     move_button_disabled = False
 
             if st.button("Move All Categorized", disabled=move_button_disabled, key="move_all_button"):
                 current_counts = st.session_state.df['category'].value_counts()
                 st.session_state.move_counts = {cat: current_counts.get(cat, 0) for cat in MOVE_CATEGORIES if cat in current_counts and current_counts.get(cat, 0) > 0}
                 if st.session_state.move_counts:
                      st.session_state.show_move_confirmation = True
                      st.rerun()
                 else:
                      st.toast(f"No emails found in {', '.join(MOVE_CATEGORIES)} categories to move.")
                      st.session_state.show_move_confirmation = False

    # --- Move Confirmation Dialog (Inline, conditional display) ---
    if st.session_state.show_move_confirmation and not st.session_state.manual_selection_mode:
        confirm_items = [f"{cat}: {count}" for cat, count in st.session_state.move_counts.items() if count > 0]
        confirm_text = " | ".join(confirm_items)
        st.warning(f"Confirm moving all applicable emails? -> {confirm_text}")
        col_confirm_yes, col_confirm_no, col_confirm_manual = st.columns(3)
        with col_confirm_yes:
            if st.button("✅ Yes, Move All"):
                if not st.session_state.imap_client:
                    st.error("IMAP client not available. Cannot move emails.")
                else:
                    with st.spinner("Moving emails..."):
                        relevant_df = st.session_state.df[st.session_state.df['category'].isin(MOVE_CATEGORIES)].copy() # Use constant
                        if not relevant_df.empty:
                            uids_to_move = relevant_df['uid'].tolist()
                            category_map = pd.Series(relevant_df.category.values, index=relevant_df.uid).to_dict()
                            # Pass the IMAP client from session state
                            moved_uids = move_emails(st.session_state.imap_client, uids_to_move, category_map)
                            if moved_uids is not None: # Check if move was attempted (even if 0 moved)
                                st.toast(f"Moved {len(moved_uids)} email(s). Test mode might be active.")
                                # Update state immediately
                                st.session_state.df = st.session_state.df[~st.session_state.df['uid'].isin(moved_uids)]
                                st.session_state.emails = [email for email in st.session_state.emails if email['uid'] not in moved_uids]
                            else:
                                st.error("Move operation failed. Check logs.")
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
                if not st.session_state.imap_client:
                    st.error("IMAP client not available. Cannot move emails.")
                elif not st.session_state.df.empty:
                    selected_df = st.session_state.df[st.session_state.df['Select'] == True]
                    # relevant_categories_to_move = ["Action", "Read", "Events"] # Use constant list
                    selected_to_move = selected_df[selected_df['category'].isin(MOVE_CATEGORIES)].copy() # Use constant
                    if not selected_to_move.empty:
                        uids_to_move = selected_to_move['uid'].tolist()
                        category_map = pd.Series(selected_to_move.category.values, index=selected_to_move.uid).to_dict()
                        with st.spinner("Moving selected emails..."):
                            # Pass the IMAP client from session state
                            moved_uids = move_emails(st.session_state.imap_client, uids_to_move, category_map)
                            if moved_uids is not None:
                                st.toast(f"Moved {len(moved_uids)} selected email(s). Test mode might be active.")
                                # Update state immediately
                                st.session_state.df = st.session_state.df[~st.session_state.df['uid'].isin(moved_uids)]
                                st.session_state.emails = [email for email in st.session_state.emails if email['uid'] not in moved_uids]
                            else:
                                st.error("Move operation failed. Check logs.")
                        st.session_state.manual_selection_mode = False
                        st.rerun()
                    else:
                        st.warning(f"No valid emails selected (must be {', '.join(MOVE_CATEGORIES)}).") # Use constants
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
                # Use all defined rule categories + Uncategorised for the dropdown
                options=[CAT_UNCATEGORISED] + RULE_CATEGORIES, 
                required=True,
            ),
            "date": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD HH:mm:ss"),
            "from": "From",
            "subject": "Subject",
            "Select": None # Default to hidden unless in manual mode
        }
        # Base columns that are always disabled from direct editing
        disabled_columns = ["date", "from", "subject", "uid"]

        if st.session_state.manual_selection_mode:
            column_config["Select"] = st.column_config.CheckboxColumn("Select", default=False)
            # Allow editing Select, but still disable category dropdown in manual mode?
            # Or allow both? For now, let category be editable unless in manual mode.
            # disabled_columns.append("category")
        else:
            # Allow editing category dropdown only when NOT in manual selection mode
            disabled_columns.append("Select") # Ensure Select is disabled if column exists but hidden

        edited_df = st.data_editor(
            st.session_state.df,
            use_container_width=True,
            height=600,
            column_config=column_config,
            disabled=disabled_columns,
            key="data_editor",
            on_change=None # Clear any previous callbacks if needed
        )

        # Update session state if edits were made (category or selection changes)
        if not edited_df.equals(st.session_state.df):
            st.session_state.df = edited_df
            # Optional: Add a subtle toast or indicator that changes are saved
            # st.toast("Changes saved in table.")
            st.rerun() # Rerun to reflect changes immediately

        # --- Category Summary ---
        category_counts = st.session_state.df['category'].value_counts().sort_index()
        summary_items = [f"{cat}: {count}" for cat, count in category_counts.items()]
        summary_text = " | ".join(summary_items)
        st.markdown(f"**Inbox Status:** {summary_text}")

    elif st.session_state.logged_in:
        # Show only if logged in but no emails were found/loaded
        st.write("No emails to display.")

    # Add a logout button
    if st.button("Logout"):
        if st.session_state.imap_client:
            try:
                st.session_state.imap_client.logout()
                logging.info("IMAP client logged out.") # Use logging
            except Exception as e:
                logging.error(f"Error during IMAP logout: {e}") # Use logging
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
