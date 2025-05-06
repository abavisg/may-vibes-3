"""
Helper functions for Smart Inbox Cleaner
"""

import logging
import email.header
import ollama
from llm_categorizer import DEFAULT_MODEL

def decode_subject(subject):
    """Decode email subjects encoded with =?UTF-8?Q?...?= format."""
    if not subject:
        return ""
        
    try:
        # Check if it's an encoded string that needs decoding
        if isinstance(subject, str) and "=?UTF-8?" in subject:
            # Use proper email.header module to decode
            decoded_parts = email.header.decode_header(subject)
            result = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    result += part.decode(encoding or 'utf-8', errors='replace')
                else:
                    result += str(part)
            return result
        return subject  # Return as-is if not encoded or not a string
    except Exception as e:
        logging.warning(f"Error decoding subject '{subject}': {str(e)}")
        # Return the original if decoding fails
        if isinstance(subject, str):
            return subject
        elif isinstance(subject, bytes):
            return subject.decode('utf-8', errors='replace')
        else:
            return str(subject)

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