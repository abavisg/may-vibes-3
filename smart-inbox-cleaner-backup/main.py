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

# --- Page Configuration ---
st.set_page_config(
    page_title="Smart Inbox Cleaner",
    page_icon="📥",
    layout="wide"
)

