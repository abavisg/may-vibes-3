# 📥 Smart Inbox Cleaner

A local desktop-like productivity tool that helps you triage your inbox using GTD principles. Now available as both a web app (Streamlit) and a native desktop app (Electron).

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
- **IMAP Folder Creation**: Automatically creates necessary `SmartInbox/` subfolders if they don't exist.
- **Desktop App Feel**: Uses Streamlit's wide layout and custom styling for a cleaner interface.
- **Authentication:** `google-auth-oauthlib`, `google-api-python-client`
- **LLM Integration:** `ollama` (via local Ollama instance)
- **Manual Selection Moving**: Allows manually selecting specific emails (via checkboxes) from Action, Read, or Events categories to be moved.

## Tech stack

- **Language:** Python 3.11+
- **UI Framework:** Streamlit
- **Email Protocol:** IMAP (via `imapclient` library)
- **Data Handling:** Pandas
- **Environment Variables:** `python-dotenv` (Minimal usage now.

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
- **Configuration**: Uses inline entry of Google OAuth credentials for setup and stores refresh tokens securely for future sessions.
- **Data Flow**:
    1. User clicks "Login with Google", initiating OAuth flow via `auth.py`.
    2. Browser opens for Google authentication.
    3. Upon success, credentials (including access/refresh tokens) are obtained and stored.
    4. `email_client.py` uses credentials to establish IMAP connection.
    5. Emails are fetched and displayed in the app UI.
    6. User triggers categorization or manual edits, updating the email list in the app.
    7. User triggers email move, which interacts with the IMAP server via `email_mover.py` using the established client.

## Project Structure

- `smart-inbox-cleaner/`: Python backend and Streamlit UI
- `desktop/`: Electron desktop wrapper (Node.js)
- `gmail-oauth/`: Google OAuth credentials and token storage

## Setup the application

### 1. Clone the repository
```bash
git clone <repository_url>
cd <repository_directory>
```

### 2. Set up the Python backend
```bash
cd smart-inbox-cleaner
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Set up Ollama (Required for LLM Categorization)
*   Install [Ollama](https://ollama.com/) on your system if you haven't already.
*   Ensure the Ollama application/server is running.
*   Pull the models you want to use. The default is `llama3`. You might also want `deepseek-coder` or others.
    ```bash
    ollama pull llama3
    ollama pull deepseek-coder 
    # etc.
    ```

### 4. Set up Google Cloud Project & Credentials
*   Go to the [Google Cloud Console](https://console.cloud.google.com/).
*   Create a new project (or select an existing one).
*   Enable the **Gmail API** for your project.
*   Go to "Credentials" -> "Create Credentials" -> "OAuth client ID".
*   Select **"Desktop app"** as the Application type.
*   Give it a name (e.g., "Smart Inbox Cleaner Local").
*   Click "Create".
*   Copy your client ID and client secret. You will enter these directly into the app when prompted.

### 6. Verify .gitignore
*   Ensure your .gitignore file (at the root) includes entries to ignore the token file:
  ```gitignore
  # ... other entries
  gmail-oauth/token.json
  # ... other entries
  ```
*   This prevents accidentally committing sensitive files.

### 7. (Optional) Set up the Electron Desktop App
If you want to use the app as a native desktop application:

```bash
cd ../desktop
npm install
```

---

## Run the application

### Option 1: Run as a Web App (Streamlit)

1. Activate your Python virtual environment:
   ```bash
   cd smart-inbox-cleaner
   source venv/bin/activate
   ```
2. (If using LLM Categorization) Ensure Ollama is running.
3. Run the Streamlit app:
   ```bash
   streamlit run main.py
   ```
4. The app will open in your browser.

### Option 2: Run as a Desktop App (Electron)

1. Make sure you have completed the Python backend setup above (including virtualenv and requirements).
2. In a new terminal, go to the `desktop` directory and install dependencies:
   ```bash
   cd desktop
   npm install
   ```
3. Start the desktop app in development mode:
   ```bash
   npm run dev
   ```
   This will launch the Electron app, which will start the Python backend and open the UI in a native window.

#### Notes:
- The Electron app will attempt to find and launch your Streamlit backend. If you use a virtual environment, ensure the correct Python/Streamlit path is set in `desktop/main.js` (see troubleshooting below).
- If you see an error like `spawn streamlit ENOENT`, follow the troubleshooting steps below to set the correct path to your Streamlit executable.

---

## Build and Distribute the Desktop App

To package the app for distribution (macOS, Windows, Linux):

```bash
cd desktop
npm run dist
```

- The distributable files will be created in the `desktop/dist/` folder.
- For macOS, you will get a `.dmg` and `.zip` file. For Windows, an `.exe` installer and portable `.exe`. For Linux, `.AppImage` and `.deb`.

### Distributing on macOS

- For personal/development use: Use the generated DMG or ZIP file as is. Users may need to right-click and select "Open" to bypass Gatekeeper warnings.
- For production: You will need an Apple Developer account to sign and notarize the app. See Apple documentation for details.

---

## How the Desktop App Works

- The Electron application launches a local Streamlit server (the Smart Inbox Cleaner Python app).
- It opens a browser window pointing to the Streamlit interface.
- It handles communication between the UI and Python backend.
- It packages everything together in a distributable application.

---

## Note on Icons

- The current icon is generated using the `generate-icon.js` script in the `desktop` folder.
- For production, consider creating a proper `.icns` file (macOS) or `.ico` file (Windows) with multiple resolutions.

---

## Streamlit Path Configuration & Troubleshooting (Desktop App)

The packaged Smart Inbox Cleaner desktop app requires the Streamlit executable to be available on your system. If you see an error like:

    Error: spawn streamlit ENOENT

it means the app cannot find Streamlit in your system PATH.

### How to Fix

1. **Find the full path to your Streamlit executable:**
   Open your terminal and run:
   ```bash
   which streamlit
   ```
   Example output:
   ```
   /Library/Frameworks/Python.framework/Versions/3.12/bin/streamlit
   ```
2. **Edit `main.js` in the desktop app:**
   In the `startPythonBackend` function, update the path checks so your path is first:
   ```js
   let command = '/Library/Frameworks/Python.framework/Versions/3.12/bin/streamlit'; // <-- your path
   if (!fs.existsSync(command)) {
     command = '/usr/local/bin/streamlit';
   }
   if (!fs.existsSync(command)) {
     command = '/opt/homebrew/bin/streamlit';
   }
   if (!fs.existsSync(command)) {
     command = 'streamlit';
   }
   ```
3. **Rebuild the app:**
   After editing, rebuild the Electron app so the new path is used.

#### Additional Troubleshooting
- If you still get the ENOENT error, double-check the path and make sure Streamlit is installed and executable.
- You can also use the full path to your Python executable and run Streamlit as a module:
  ```js
  let pythonBin = '/usr/local/bin/python3';
  let command = pythonBin;
  let args = ['-m', 'streamlit', 'run', 'main.py', ...];
  ```
- If you use a virtual environment, make sure the app points to the correct Python/Streamlit inside that environment.

If you have any issues, please check the logs and ensure the correct path is set in `main.js`.