import streamlit as st
import logging # Use logging
import os  # Added back for env vars
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
# Import the status component module
from status_component import setup_status_component, is_electron

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
/* Global styling */
html, body, [class*="st-"] {
    font-size: 16px !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif !important;
}

/* Main app container */
.main .block-container {
    padding: 1rem 1rem 1rem 1rem !important;
    max-width: 100% !important;
}

/* Card styling for the entire app */
.main .block-container {
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

/* Category pills styling */
.stDataFrame [data-testid="StyledDataFrameDataCell"]:has(div:contains("Action")) div {
    background-color: #ff4c4c !important;
    color: white !important;
    padding: 2px 10px;
    border-radius: 12px;
    font-weight: 500;
    display: inline-block;
}

.stDataFrame [data-testid="StyledDataFrameDataCell"]:has(div:contains("Read")) div {
    background-color: #4c7bff !important;
    color: white !important;
    padding: 2px 10px;
    border-radius: 12px;
    font-weight: 500;
    display: inline-block;
}

.stDataFrame [data-testid="StyledDataFrameDataCell"]:has(div:contains("Info")) div {
    background-color: #4cd97b !important;
    color: white !important;
    padding: 2px 10px;
    border-radius: 12px;
    font-weight: 500;
    display: inline-block;
}

.stDataFrame [data-testid="StyledDataFrameDataCell"]:has(div:contains("Uncategorized")) div {
    background-color: #e0e0e0 !important;
    color: #555 !important;
    padding: 2px 10px;
    border-radius: 12px;
    font-weight: 500;
    display: inline-block;
}

/* Button styling */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.08) !important;
    margin-right: 10px !important;
    margin-bottom: 10px !important;
    border: none !important;
}

.stButton > button[kind="primary"] {
    background-color: #4c7bff !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: white;
    padding: 2rem 1rem;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}

[data-testid="stSidebar"] .block-container {
    margin-top: 1rem;
}

/* Table styling */
.stDataFrame {
    width: 100%;
}

.stDataFrame [data-testid="StyledDataFrameDataCell"] {
    font-size: 0.9rem !important;
    padding: 0.5rem 0.75rem !important;
}

.stDataFrame [data-testid="StyledDataFrameRowHeader"] {
    display: none;
}

.stDataFrame thead th {
    background-color: #f8f9fa;
    font-weight: 600 !important;
    padding: 0.75rem !important;
    text-transform: none !important;
    border-bottom: 1px solid #eaeaea !important;
}

.stDataFrame tbody tr {
    border-bottom: 1px solid #f0f0f0;
}

.stDataFrame tbody tr:hover {
    background-color: #f9f9f9;
}

/* Processing overlay styling */
.processing-overlay {
    position: relative;
    z-index: 1000;
    background-color: rgba(245, 245, 250, 0.95);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 15px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(0, 0, 0, 0.05);
}

/* Disabled table styling during processing */
.disabled-table [data-testid="stDataFrame"] {
    opacity: 0.8;
    position: relative;
    transition: all 0.3s ease;
}

.disabled-table [data-testid="stDataFrame"]::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(245, 245, 250, 0.4);
    border-radius: 8px;
    pointer-events: none;
    z-index: 1;
}

/* Inbox status styling */
.inbox-status {
    text-align: left;
    margin-bottom: 1rem;
}

/* Remove padding from header */
header {
    display: none;
}
</style>
""", unsafe_allow_html=True)

# Add the debug CSS separately when enabled
if st.session_state.get('debug_layout', False):
    st.markdown("""
    <style>
    /* Debug layout style rules for containers */
    div[data-testid="stVerticalBlock"] {
        background-color: rgba(255, 200, 200, 0.2) !important;
        border: 1px dashed rgba(255, 0, 0, 0.3) !important;
        padding: 2px !important;
        margin-bottom: 5px !important;
    }
    
    div[data-testid="stHorizontalBlock"] {
        background-color: rgba(200, 200, 255, 0.2) !important;
        border: 1px dashed rgba(0, 0, 255, 0.3) !important;
        padding: 2px !important;
    }
    
    div.element-container, div.stColumn, div.stButton, div.row-widget {
        background-color: rgba(200, 255, 200, 0.2) !important;
        border: 1px dashed rgba(0, 150, 0, 0.3) !important;
        padding: 2px !important;
        margin-bottom: 2px !important;
    }
    
    .stDataFrame {
        border: 2px solid rgba(128, 0, 128, 0.5) !important;
    }
    
    div.stMarkdown {
        background-color: rgba(255, 255, 200, 0.3) !important;
        border: 1px dashed rgba(100, 100, 0, 0.3) !important;
    }
    
    /* Sidebar debug styling */
    [data-testid="stSidebar"] > div {
        background-color: rgba(255, 200, 0, 0.1) !important;
        border: 1px dashed rgba(255, 150, 0, 0.4) !important;
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
if 'table_editable' not in st.session_state:
    st.session_state.table_editable = True # Controls whether the table is editable
if 'progress_text' not in st.session_state:
    st.session_state.progress_text = None # Stores current progress text
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# Removed Load Environment Variables
# gmail_address = os.getenv('GMAIL_ADDRESS', 'Not set') # No longer needed here

# --- App Header with better styling ---
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
            progress_placeholder.markdown(f"""
            <div style="padding-top: 8px; color: #555; display: flex; align-items: center;">
                <div style="width: 12px; height: 12px; background-color: #4c7bff; border-radius: 50%; margin-right: 8px;"></div>
                {progress_text}
            </div>
            """, unsafe_allow_html=True)
            
            # Store the placeholder in session state for the callback to use
            st.session_state.progress_placeholder = progress_placeholder
        elif st.session_state.get('progress_text') and st.session_state.categorization_run:
            # Show a success message briefly, then clear it on the next rerun
            st.markdown(f"""
            <div style="padding-top: 8px; color: #4cd97b; display: flex; align-items: center;">
                <div style="width: 12px; height: 12px; background-color: #4cd97b; border-radius: 50%; margin-right: 8px;"></div>
                {st.session_state.get('progress_text')}
            </div>
            """, unsafe_allow_html=True)
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
                        temp_df = temp_df.sort_values(by='date', ascending=False)
                        # Define initial column order
                        st.session_state.df = temp_df[['Select', 'date', 'from', 'subject', 'category', 'uid']]
                    else:
                        st.write("No emails fetched or inbox is empty.")
                else:
                    st.error("IMAP client not available. Cannot fetch emails.")
            except Exception as e:
                st.error(f"Error fetching emails: {e}")

    # --- Processing Logic (Only runs when Process Inbox button is clicked) ---
    if st.session_state.categorization_running:
        # This block runs after the rerun triggered by the Process Inbox button
        start_time = pd.Timestamp.now()
        progress_bar = None 
        if st.session_state.categorization_method == CAT_METHOD_LLM:
            # Progress bar is now shown in the table overlay
            pass
        
        # --- Callbacks --- 
        def update_progress(current, total):
            # Update the progress text in session state
            progress_text = f"Categorising {current} out of {total} emails ({int(current/total*100)}%)"
            st.session_state.progress_text = progress_text
            
            # Update the progress placeholder if it exists
            if 'progress_placeholder' in st.session_state:
                progress_placeholder = st.session_state.progress_placeholder
                progress_placeholder.markdown(f"""
                <div style="padding-top: 8px; color: #555; display: flex; align-items: center;">
                    <div style="width: 12px; height: 12px; background-color: #4c7bff; border-radius: 50%; margin-right: 8px;"></div>
                    {progress_text}
                </div>
                """, unsafe_allow_html=True)
            
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
                
                temp_df = pd.DataFrame(categorized_email_list)
                temp_df['Select'] = False
                temp_df['date'] = pd.to_datetime(temp_df['date'])
                temp_df = temp_df.sort_values(by='date', ascending=False)
                # Ensure 'category' column exists before selecting it
                if 'category' not in temp_df.columns:
                    logging.error("'category' column missing from DataFrame after categorization!")
                    temp_df['category'] = CAT_UNCATEGORISED # Add default if missing
                    
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
        
        # Build status display with styled category pills and batch info
        status_html = '<div class="inbox-status">'
        status_html += '<div style="font-weight: 500; margin-bottom: 5px;">Inbox Status:</div>'
        status_html += '<div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">'
        
        # Add a pill for each category with the appropriate color
        for cat, count in category_counts.items():
            if cat == "Action":
                color = "#ff4c4c"
                text_color = "white"
            elif cat == "Read":
                color = "#4c7bff"
                text_color = "white"
            elif cat == "Info":
                color = "#4cd97b"
                text_color = "white"
            elif cat == "Events":
                color = "#ff9e4c"
                text_color = "white"
            else:  # Uncategorized or any other
                color = "#e0e0e0"
                text_color = "#555"
                
            status_html += f'<div style="background-color: {color}; color: {text_color}; border-radius: 12px; padding: 3px 12px; font-size: 0.9rem;">{cat}: {count}</div>'
        
        # Add batch info at the end of the category pills
        status_html += f'<div style="margin-left: auto; color: #666; font-size: 0.9rem;">Batch: {current_batch_size} of {total_emails}</div>'
        
        status_html += '</div></div>'
        
        # Add the status HTML above the table
        st.markdown(status_html, unsafe_allow_html=True)

        # Create a loading overlay for the table when processing
        table_disabled = False
        if st.session_state.categorization_running:
            # Add a class to mark the table as disabled instead of adding an overlay element
            st.markdown('<div class="disabled-table">', unsafe_allow_html=True)
            table_disabled = True

        # Dynamically configure columns
        column_config = {
            "uid": None, # Hide UID
            "category": st.column_config.SelectboxColumn(
                "Category",
                # Use all defined rule categories + Uncategorised for the dropdown
                options=[CAT_UNCATEGORISED] + RULE_CATEGORIES, 
                required=True,
                width="medium"
            ),
            "date": st.column_config.DatetimeColumn(
                "Date", 
                format="MM-DD-YY HH:mm",
                width="small"
            ),
            "from": st.column_config.TextColumn(
                "From",
                width="medium"
            ),
            "subject": st.column_config.TextColumn(
                "Subject",
                width="large"
            ),
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
        
        # When categorization is running, disable the entire table 
        if not st.session_state.table_editable:
            disabled_columns.append("category") # Disable category editing during processing

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
            
        # Close the disabled-table div if it was opened
        if table_disabled:
            st.markdown('</div>', unsafe_allow_html=True)

        # --- Action Buttons Row (only show when categorization is completed) ---
        if st.session_state.categorization_run and not st.session_state.categorization_running:
            # Move to the bottom of the UI with some space
            st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
            
            # Create columns for the buttons
            button_cols = st.columns([1, 1, 1])
            
            # Confirm button (styled like in design)
            with button_cols[0]:
                # Only enable after categorization has run
                confirm_disabled = not st.session_state.categorization_run
                        
                if st.button("Confirm & Move", key="confirm_move_btn", type="primary", disabled=confirm_disabled):
                    current_counts = st.session_state.df['category'].value_counts()
                    st.session_state.move_counts = {cat: current_counts.get(cat, 0) for cat in MOVE_CATEGORIES if cat in current_counts and current_counts.get(cat, 0) > 0}
                    if st.session_state.move_counts:
                        # Create confirmation message
                        confirmation_msg = "Are you sure you want to move: "
                        move_details = []
                        for cat, count in st.session_state.move_counts.items():
                            if count > 0:
                                move_details.append(f"{count} {'email' if count == 1 else 'emails'} to {cat}")
                        confirmation_msg += ", ".join(move_details)
                        
                        # Show confirmation dialog
                        if st.session_state.get('show_confirmation_dialog', False):
                            st.markdown(f"<div style='padding: 15px; background-color: #f8f9fa; border-radius: 8px; margin-bottom: 20px; border: 1px solid #eaeaea;'>{confirmation_msg}</div>", unsafe_allow_html=True)
                            
                            confirm_cols = st.columns([1, 1, 2])
                            with confirm_cols[0]:
                                if st.button("Yes, Move Emails", key="confirm_yes_btn", type="primary"):
                                    if not st.session_state.imap_client:
                                        st.error("IMAP client not available. Cannot move emails.")
                                    else:
                                        with st.spinner("Moving emails..."):
                                            relevant_df = st.session_state.df[st.session_state.df['category'].isin(MOVE_CATEGORIES)].copy()
                                            if not relevant_df.empty:
                                                uids_to_move = relevant_df['uid'].tolist()
                                                category_map = pd.Series(relevant_df.category.values, index=relevant_df.uid).to_dict()
                                                moved_uids = move_emails(st.session_state.imap_client, uids_to_move, category_map)
                                                if moved_uids is not None:
                                                    st.toast(f"Moved {len(moved_uids)} email(s).")
                                                    st.session_state.df = st.session_state.df[~st.session_state.df['uid'].isin(moved_uids)]
                                                    st.session_state.emails = [email for email in st.session_state.emails if email['uid'] not in moved_uids]
                                                else:
                                                    st.error("Move operation failed. Check logs.")
                                            else:
                                                st.toast("No relevant emails found to move.")
                                    st.session_state.show_confirmation_dialog = False
                                    st.rerun()
                            with confirm_cols[1]:
                                if st.button("Cancel", key="confirm_no_btn", type="secondary"):
                                    st.session_state.show_confirmation_dialog = False
                                    st.rerun()
                        else:
                            # Show the confirmation dialog
                            st.session_state.show_confirmation_dialog = True
                            st.rerun()
                    else:
                        st.toast(f"No emails found in {', '.join(MOVE_CATEGORIES)} categories to move.")
                
            # Next Batch button
            with button_cols[2]:
                if st.button("Next Batch", key="next_batch_btn", type="secondary"):
                    # Implementation could be added later
                    st.toast("Next batch functionality would be implemented here")

    elif st.session_state.logged_in:
        # Show only if logged in but no emails were found/loaded
        st.write("No emails to display.")
