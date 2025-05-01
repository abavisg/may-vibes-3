import streamlit as st
from dotenv import load_dotenv
import os
from email_client import connect_imap

# Load environment variables from .env file
load_dotenv()

gmail_address = os.getenv('GMAIL_ADDRESS', 'Not set')

st.title('Smart Inbox Cleaner')
st.write(f'Connected Gmail address: {gmail_address}')
st.write(f'IMAP Connection Status: {connect_imap()}')

st.info('Environment and Streamlit are set up! Ready to build.') 