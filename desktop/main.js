const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
let pythonProcess = null;
let mainWindow = null;

// Handle creating/removing shortcuts on Windows when installing/uninstalling
if (require('electron-squirrel-startup')) {
  app.quit();
}

const createWindow = () => {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    title: 'Smart Inbox Cleaner',
    icon: path.join(__dirname, 'build', 'icon.png'),
  });

  // Give the Streamlit server a moment to start up
  setTimeout(() => {
    // Load the Streamlit web interface
    mainWindow.loadURL('http://localhost:8501');

    // Open DevTools in development mode
    if (process.env.NODE_ENV === 'development') {
      mainWindow.webContents.openDevTools();
    }
  }, 2000); // 2 second delay before loading URL
};

// Start Python backend
const startPythonBackend = () => {
  // Get the path to the Python app directory
  const pythonAppPath = path.join(__dirname, '..', 'smart-inbox-cleaner');
  
  console.log('Starting Python backend with Streamlit...');
  console.log(`Python app path: ${pythonAppPath}`);
  
  // Start the Python application with streamlit run
  // Use a shell on Windows to avoid issues with the command
  const useShell = process.platform === 'win32';
  
  // Determine the streamlit command method based on platform
  let command;
  let args;
  
  if (useShell) {
    // On Windows, use a shell command
    command = 'streamlit';
    args = ['run', 'main.py', '--server.headless=true', '--browser.serverAddress=localhost', '--server.port=8501'];
  } else {
    // On Mac/Linux, use the direct command
    command = 'streamlit';
    args = ['run', 'main.py', '--server.headless=true', '--browser.serverAddress=localhost', '--server.port=8501'];
  }
  
  pythonProcess = spawn(command, args, {
    cwd: pythonAppPath,
    shell: useShell,
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data}`);
    if (mainWindow) {
      mainWindow.webContents.send('python-output', data.toString());
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
    if (mainWindow) {
      mainWindow.webContents.send('python-error', data.toString());
    }
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    
    // Update main window with exit code
    if (mainWindow) {
      mainWindow.webContents.send('python-output', `Python process exited with code ${code}`);
    }
  });
};

// This method will be called when Electron has finished initialization
app.on('ready', () => {
  createWindow();
  startPythonBackend();
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On macOS re-create a window when dock icon is clicked and no other windows open
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Clean up the Python process on app quit
app.on('quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// IPC handlers for communication with the renderer process
ipcMain.on('restart-python', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  startPythonBackend();
}); 