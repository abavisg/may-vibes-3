"""
Status Component for Smart Inbox Cleaner
This module adds a status component to the Streamlit sidebar.
"""

import streamlit as st
import json
from typing import Dict, Optional, Any
import os

# Check if running in Electron environment
def is_electron() -> bool:
    """Detects if the app is running inside Electron."""
    # Check for Electron-specific environment variables
    electron_run_as_node = os.environ.get('ELECTRON_RUN_AS_NODE') is not None
    electron_no_asar = os.environ.get('ELECTRON_NO_ASAR') is not None
    electron_app_version = os.environ.get('ELECTRON_APP_VERSION') is not None
    
    # For debugging
    if st.session_state.get('debug_mode', False):
        st.sidebar.write("Electron env vars:", {
            'ELECTRON_RUN_AS_NODE': os.environ.get('ELECTRON_RUN_AS_NODE'),
            'ELECTRON_NO_ASAR': os.environ.get('ELECTRON_NO_ASAR'),
            'ELECTRON_APP_VERSION': os.environ.get('ELECTRON_APP_VERSION')
        })
    
    # Consider it Electron if any of these variables are set
    return electron_run_as_node or electron_no_asar or electron_app_version

def inject_electron_communication():
    """Inject JavaScript to enable communication with Electron."""
    # Always inject the JavaScript, it will handle the case when not in Electron
    # by checking for window.api
        
    # JavaScript to communicate with Electron preload API
    js_code = """
    <script>
    // This script handles communication with the Electron main process
    document.addEventListener('DOMContentLoaded', function() {
        console.log("Checking for Electron API...");
        
        // Function to receive messages from Electron main process
        if (window.api) {
            console.log("Electron API detected");
            
            // Listen for update status messages
            window.api.onUpdateStatus(function(message) {
                console.log("Update status:", message);
                
                // Update the status field
                const statusElement = document.getElementById('electron-status');
                if (statusElement) {
                    statusElement.innerText = message;
                    statusElement.style.display = 'block';
                }
            });
        } else {
            console.log("Not running in Electron or API not available");
            // Optionally hide the update button when not in Electron
            const updateButton = document.getElementById('update-button');
            if (updateButton) {
                updateButton.style.display = 'none';
            }
        }
    });
    
    // Function to check for updates
    function checkForUpdates() {
        if (window.api) {
            window.api.checkForUpdates();
            
            const statusElement = document.getElementById('electron-status');
            if (statusElement) {
                statusElement.innerText = "Checking for updates...";
                statusElement.style.display = 'block';
            }
        } else {
            console.log("Cannot check for updates - API not available");
        }
    }
    </script>
    """
    
    # Inject the JavaScript
    st.sidebar.markdown(js_code, unsafe_allow_html=True)

def add_status_sidebar():
    """Add a status section to the Streamlit sidebar."""
    # Only add version info if we're running in Electron
    is_electron_app = is_electron()
    
    st.sidebar.markdown("---")

    # Add a container for status messages with styling
    status_html = f"""
    <div style="margin-bottom: 15px;">
        <div id="electron-status" 
             style="display: none; 
                    padding: 8px 12px; 
                    background-color: #f0f2f6; 
                    border-radius: 4px; 
                    font-size: 14px; 
                    margin-bottom: 10px;
                    border-left: 3px solid #4285F4;">
            Ready
        </div>
        <button id="update-button"
                onclick="checkForUpdates()" 
                style="background-color: #4285F4; 
                       color: white; 
                       border: none; 
                       padding: 5px 10px; 
                       border-radius: 4px; 
                       cursor: pointer; 
                       font-size: 12px;
                       width: 100%;
                       display: {'' if is_electron_app else 'none'};">
            Check for Updates
        </button>
    </div>
    """
    
    st.sidebar.markdown(status_html, unsafe_allow_html=True)
    
    # Add the footer section with version and copyright at the very bottom
    # We add some space to push it to the bottom
    st.sidebar.markdown("""
    <div style="margin-top: 50px;"></div>
    """, unsafe_allow_html=True)
    
    # Get version from environment variable or use default
    version = os.environ.get('ELECTRON_APP_VERSION', '1.0.0')
    
    # Add version and copyright info
    st.sidebar.markdown("---")
    st.sidebar.caption(f"v{version}")
    st.sidebar.caption("© 2024 Smart Inbox Cleaner")

def setup_status_component():
    """Initialize the status component with Electron communication."""
    # Inject JavaScript for communication
    inject_electron_communication()
    
    # Add the status UI components
    add_status_sidebar()

if __name__ == "__main__":
    # Test the component
    st.title("Status Component Test")
    setup_status_component()
    st.write("This is a test of the status component.") 