import streamlit as st
from streamlit_modal import Modal
from typing import Optional, Union, Dict, Any
import logging

class EmailModal:
    """
    Custom modal component for Smart Inbox Cleaner that adds additional functionality
    on top of streamlit-modal.
    """
    
    def __init__(
        self,
        title: str,
        key: str,
        padding: int = 20,
        max_width: int = 600,
        hide_close_button: bool = True
    ):
        """
        Initialize the modal component with customized styling.
        
        Args:
            title: The title of the modal
            key: A unique key for the modal
            padding: Padding inside the modal in pixels
            max_width: Maximum width of the modal in pixels
            hide_close_button: When True, hides the X button via CSS (not supported directly by Modal)
        """
        # Store parameters
        self.title = title
        self.key = key
        self.padding = padding
        self.max_width = max_width
        self.hide_close_button = hide_close_button
        
        # Create the underlying Modal instance
        self.modal = Modal(
            title=title,
            key=key,
            padding=padding,
            max_width=max_width
        )
        
        # Apply custom styling if hiding X button
        if hide_close_button:
            # Use custom CSS to hide the close button and remove the grey line
            st.markdown(
                """
                <style>
                /* Hide the X button */
                [data-testid="stModal"] [data-testid="TextElement"] ~ button {
                    display: none !important;
                }
                
                /* Remove the grey border line */
                [data-testid="stModal"] > div > div:first-child {
                    border-bottom: none !important;
                }
                
                /* Clean up spacing in the modal header */
                [data-testid="stModal"] [data-testid="TextElement"] {
                    padding-bottom: 10px;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
    
    def open(self) -> None:
        """Open the modal dialog."""
        self.modal.open()
    
    def close(self) -> None:
        """Close the modal dialog."""
        self.modal.close()
    
    def is_open(self) -> bool:
        """Check if the modal is currently open."""
        return self.modal.is_open()
    
    def container(self) -> Any:
        """Get the container to render content inside the modal."""
        return self.modal.container() 