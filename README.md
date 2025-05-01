# 📥 Smart Inbox Cleaner

A local desktop-like productivity tool that helps you triage your inbox using GTD principles. 

## Features

- **IMAP Connectivity**: Connects securely to your Gmail inbox (using App Passwords).
- **Email Display**: Fetches and displays the latest 250 emails in a sortable table (Date, From, Subject).
- **Automatic Categorization**: Applies rule-based logic (keywords, senders) to suggest categories (Action, Read, Events, Uncategorised) upon button click.
- **Manual Categorization**: Allows overriding the suggested category via a dropdown in the table.
- **Category Summary**: Shows a live count of emails per category below the table.
- **Bulk Email Moving**: Moves all emails categorized as Action, Read, or Events to corresponding `SmartInbox/` subfolders (with confirmation).
- **Manual Selection Moving**: Allows manually selecting specific emails (via checkboxes) from Action, Read, or Events categories to be moved.
- **IMAP Folder Creation**: Automatically creates necessary `SmartInbox/` subfolders if they don't exist.
- **Test Mode Safety**: Includes a flag (`TEST_MODE_MOVE_ONE` in `email_mover.py`) to only move one email at a time during testing.
- **Desktop App Feel**: Uses Streamlit's wide layout and custom styling for a cleaner interface.

## Tech stack

- **Language:** Python 3.11+
- **UI Framework:** Streamlit
- **Email Protocol:** IMAP (via `imapclient` library)
- **Data Handling:** Pandas
- **Environment Variables:** `python-dotenv`

## Architecture

This is a monolithic desktop-like application running locally using Streamlit.

- **`main.py`**: Serves as the entry point and UI layer.
- **UI Interaction**: Uses Streamlit widgets (`st.button`, `st.data_editor`, etc.) and `st.session_state` to manage user interaction and application state.
- **Backend Logic Modules**:
    - `email_client.py`: Handles IMAP connection.
    - `email_fetcher.py`: Fetches email data from the IMAP server.
    - `categorizer.py`: Applies rules to categorize emails.
    - `email_mover.py`: Executes IMAP commands to move emails.
- **Configuration**: Reads sensitive credentials and settings from a `.env` file.
- **Data Flow**: 
    1. Connect to IMAP.
    2. Fetch emails into a Pandas DataFrame stored in session state.
    3. Display DataFrame in `st.data_editor`.
    4. User triggers categorization or manual edits, updating the DataFrame in session state.
    5. User triggers email move, which reads the DataFrame state and interacts with the IMAP server via `email_mover.py`.

## Setup the application

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file** in the root folder with your email credentials. 
    *   For Gmail, you'll need an [App Password](https://support.google.com/accounts/answer/185833?hl=en) if you use 2-Step Verification.
    *   Make sure IMAP is enabled in your Gmail settings.
    *   **Important:** Add `.env` to your `.gitignore` file to avoid committing your credentials!

    Example `.env` content:
    ```plaintext
    EMAIL_HOST=imap.gmail.com
    EMAIL_USERNAME=your_email@gmail.com
    EMAIL_PASSWORD=your_16_digit_app_password
    GMAIL_ADDRESS=your_email@gmail.com # Optional, used for display
    ```

## Run the application

1.  Make sure your virtual environment is activated.
2.  Run the Streamlit app:
    ```bash
    streamlit run main.py
    ```
3.  The application should open in your default web browser.

## Things to improve

- Google login (OAuth 2.0) to replace the need for App Passwords.
- Further UI/UX improvements (e.g., pagination, advanced filtering, custom themes).
- LLM Categorisation: Integrate local LLMs (e.g., via Ollama with Deepseek/Llama models) for more nuanced categorization.
- Packaging: Bundle the application as a standalone desktop app (e.g., using PyInstaller or similar), or explore web/mobile deployment options.

## License
MIT