# 📥 Smart Inbox Cleaner

A local desktop-like productivity tool that helps you triage your inbox using GTD principles. 

## Features

- **Google OAuth 2.0 Login**: Connects securely to your Gmail inbox using Google Sign-In (OAuth 2.0) via a browser-based flow.
- **IMAP Connectivity**: Uses the obtained OAuth token for secure IMAP access (XOAUTH2).
- **Email Display**: Fetches and displays the latest 250 emails in a sortable table (Date, From, Subject).
- **Choice of Categorization**: 
    - **LLM-Based (Default)**: Uses a local LLM via Ollama (e.g., `llama3`, `deepseek-coder`) to suggest categories based on email subject and sender.
    - **Rule-Based**: Applies simple keyword/sender logic (`categorizer.py`) to suggest categories.
- **Categorization Selector**: Sidebar options allow switching between LLM and Rule-Based categorization, and selecting the Ollama model.
- **Manual Categorization**: Allows overriding the suggested category via a dropdown in the table.
- **Category Summary**: Shows a live count of emails per category below the table.
- **Bulk Email Moving**: Moves all emails categorized as Action, Read, or Events to corresponding `SmartInbox/` subfolders (with confirmation).
- **Manual Selection Moving**: Allows manually selecting specific emails (via checkboxes) from Action, Read, or Events categories to be moved.
- **IMAP Folder Creation**: Automatically creates necessary `SmartInbox/` subfolders if they don't exist.
- **Test Mode Safety**: Includes a flag (`TEST_MODE_MOVE_ONE` in `email_mover.py`) to only move one email at a time during testing.
- **Desktop App Feel**: Uses Streamlit's wide layout and custom styling for a cleaner interface.
- **Authentication:** `google-auth-oauthlib`, `google-api-python-client`
- **LLM Integration:** `ollama` (via local Ollama instance)

## Tech stack

- **Language:** Python 3.11+
- **UI Framework:** Streamlit
- **Email Protocol:** IMAP (via `imapclient` library)
- **Data Handling:** Pandas
- **Environment Variables:** `python-dotenv` (Minimal usage now, primarily for optional settings like `TEST_MODE_MOVE_ONE`).

## Architecture

This is a monolithic desktop-like application running locally using Streamlit.

- **`main.py`**: Serves as the entry point and UI layer.
- **UI Interaction**: Uses Streamlit widgets (`st.button`, `st.data_editor`, etc.) and `st.session_state` to manage user interaction and application state.
- **Backend Logic Modules**:
    - `auth.py`: Handles Google OAuth 2.0 flow and token management.
    - `email_client.py`: Handles IMAP connection using OAuth tokens.
    - `email_fetcher.py`: Fetches email data from the IMAP server.
    - `categorizer.py`: Applies rule-based logic to categorize emails.
    - `llm_categorizer.py`: Uses Ollama to categorize emails via LLM.
    - `email_mover.py`: Executes IMAP commands to move emails.
- **Configuration**: Uses `client_secret.json` for OAuth setup and stores refresh tokens in `token.json` (both within `gmail-oauth/` folder).
- **Data Flow**:
    1. User clicks "Login with Google", initiating OAuth flow via `auth.py`.
    2. Browser opens for Google authentication.
    3. Upon success, credentials (including access/refresh tokens) are obtained and stored.
    4. `email_client.py` uses credentials to establish IMAP connection.
    5. Fetch emails into a Pandas DataFrame stored in session state.
    6. Display DataFrame in `st.data_editor`.
    7. User triggers categorization or manual edits, updating the DataFrame in session state.
    8. User triggers email move, which reads the DataFrame state and interacts with the IMAP server via `email_mover.py` using the established client.

## Setup the application

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    cd smart-inbox-cleaner
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

4.  **Setup Ollama (Required for LLM Categorization)**:
    *   Install [Ollama](https://ollama.com/) on your system if you haven't already.
    *   Ensure the Ollama application/server is running.
    *   Pull the models you want to use. The default is `llama3`. You might also want `deepseek-coder` or others.
        ```bash
        ollama pull llama3
        ollama pull deepseek-coder 
        # etc.
        ```

5.  **Set up Google Cloud Project & Credentials**:
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project (or select an existing one).
    *   Enable the **Gmail API** for your project.
    *   Go to "Credentials" -> "Create Credentials" -> "OAuth client ID".
    *   Select **"Desktop app"** as the Application type.
    *   Give it a name (e.g., "Smart Inbox Cleaner Local").
    *   Click "Create".
    *   Download the JSON file containing your client ID and client secret. Rename this file to `client_secret.json`.

6.  **Place Credentials File**:
    *   Create a folder named `gmail-oauth` in the root directory of the cloned repository (i.e., at the same level as the `smart-inbox-cleaner` folder).
    *   Place the downloaded `client_secret.json` file inside this `gmail-oauth` folder.
    *   The final path should be `<repository_root>/gmail-oauth/client_secret.json`.

7.  **Verify `.gitignore`**:
    *   Ensure your `.gitignore` file (at the root) includes entries to ignore the credentials and token files:
      ```gitignore
      # ... other entries
      gmail-oauth/client_secret.json
      gmail-oauth/token.json
      # ... other entries
      ```
    *   This prevents accidentally committing sensitive files.

8.  **(Optional) Configure Test Mode**: You can create a `.env` file in the `smart-inbox-cleaner` directory to control the test mode flag:
    ```plaintext
    # Set to False to move all matched emails at once
    TEST_MODE_MOVE_ONE=True
    ```

## Run the application

1.  Make sure your virtual environment is activated (`source venv/bin/activate`).
2.  Navigate into the application directory:
    ```bash
    cd smart-inbox-cleaner
    ```
3.  **(If using LLM Categorization) Ensure Ollama is running.**
4.  Run the Streamlit app:
    ```bash
    streamlit run main.py
    ```
5.  The application should open in your default web browser, presenting a "Login with Google" button.
6.  Click the button. Your browser should open a Google login page.
7.  Choose your account and grant the requested permission (to view and manage your email, view profile info).
8.  After successful authentication, the browser tab may show a success message, and the Streamlit app should proceed to load your emails.
9.  Use the sidebar options to choose your preferred categorization method (LLM or Rule-Based) and select an Ollama model if using LLM.
10. Click "Run Categorization".
11. A `token.json` file will be created in the `gmail-oauth` folder to store your refresh token for future sessions.

## Things to improve

- **LLM Prompt Engineering**: Refine the prompt in `llm_categorizer.py` for better accuracy and handling of edge cases.
- **LLM Body Analysis**: Fetch email body snippets (requires additional scope like `gmail.readonly`) to provide more context to the LLM.
- **LLM Error Handling**: Improve parsing of LLM responses and handling of Ollama errors.
- **Performance**: Parallelize LLM calls in `llm_categorizer.py` for faster processing of many emails.
- Further UI/UX improvements (e.g., pagination, advanced filtering, custom themes).
- Packaging: Bundle the application as a standalone desktop app (e.g., using PyInstaller or similar), or explore web/mobile deployment options.
- Robust Error Handling: Improve handling of potential API/network errors during OAuth or IMAP operations.

## License
MIT