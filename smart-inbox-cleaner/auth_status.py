import streamlit as st

def show_auth_status(email: str) -> None:
    """Display the current authentication status in the Streamlit UI.
    
    Args:
        email: The email address of the authenticated user
    """
    st.success(f"✅ Authenticated as: {email}")

def show_auth_error(error_message: str) -> None:
    """Display authentication error in the Streamlit UI.
    
    Args:
        error_message: The error message to display
    """
    st.error(f"❌ Authentication error: {error_message}") 