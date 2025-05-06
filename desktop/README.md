# Smart Inbox Cleaner - Desktop Application

This is the desktop wrapper for the Smart Inbox Cleaner application, built with Electron.

## Prerequisites

- Node.js (v16 or higher)
- npm (v7 or higher)
- Python 3.8+ with pip installed
- Streamlit (installed via pip)

## Project Structure

- `main.js`: Main Electron process
- `preload.js`: Preload script for securely exposing APIs to the renderer
- `build/icon.png`: Application icon
- `dist/`: Contains the packaged application builds

## Setup and Development

1. Install dependencies:
   ```
   npm install
   ```

2. Make sure the Python backend dependencies are installed:
   ```
   cd .. && pip install -r requirements.txt
   ```

3. Run the application in development mode:
   ```
   npm run dev
   ```

## Building for Distribution

To build the application for distribution:

```
npm run dist
```

This will create distributable packages in the `dist` folder based on your current platform:

- macOS: `Smart Inbox Cleaner-1.0.0-arm64.dmg` and `Smart Inbox Cleaner-1.0.0-arm64-mac.zip` 
- Windows: `Smart Inbox Cleaner Setup 1.0.0.exe` (NSIS installer) and `Smart Inbox Cleaner 1.0.0.exe` (portable)
- Linux: `smart-inbox-cleaner-desktop_1.0.0_amd64.deb` and `Smart Inbox Cleaner-1.0.0.AppImage`

## Distributing on macOS

For distribution on macOS:

1. **For personal/development use**:
   - Use the generated DMG or ZIP file as is
   - Users may need to right-click and select "Open" to bypass Gatekeeper warnings

2. **For production distribution**:
   - You'll need an Apple Developer account ($99/year)
   - Sign the app with your Developer ID
   - Notarize the app with Apple
   - Add notarization ticket to your DMG

## How It Works

The Electron application:

1. Launches a local Streamlit server (the Smart Inbox Cleaner Python app)
2. Opens a browser window pointing to the Streamlit interface
3. Handles communication between the UI and Python backend
4. Packages everything together in a distributable application

## Note on Icons

The current icon is generated using the `generate-icon.js` script. For production use, consider creating a proper `.icns` file (macOS) or `.ico` file (Windows) with multiple resolutions.

## Streamlit Path Configuration (IMPORTANT)

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

### Troubleshooting
- If you still get the ENOENT error, double-check the path and make sure Streamlit is installed and executable.
- You can also use the full path to your Python executable and run Streamlit as a module:
  ```js
  let pythonBin = '/usr/local/bin/python3';
  let command = pythonBin;
  let args = ['-m', 'streamlit', 'run', 'main.py', ...];
  ```
- If you use a virtual environment, make sure the app points to the correct Python/Streamlit inside that environment.

---
If you have any issues, please check the logs and ensure the correct path is set in `main.js`. 