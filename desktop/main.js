const { app, BrowserWindow, ipcMain, Menu, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const { autoUpdater } = require('electron-updater');
const log = require('electron-log');

// Configure logging
log.transports.file.level = 'info';
log.info('Application starting...');

// Auto-updater logging
autoUpdater.logger = log;
autoUpdater.logger.transports.file.level = 'info';

let pythonProcess = null;
let mainWindow = null;

// Handle creating/removing shortcuts on Windows when installing/uninstalling
if (require('electron-squirrel-startup')) {
  app.quit();
}

// Setup auto-updater events
function setupAutoUpdater() {
  autoUpdater.on('checking-for-update', () => {
    log.info('Checking for update...');
    sendStatusToWindow('Checking for update...');
  });
  
  autoUpdater.on('update-available', (info) => {
    log.info('Update available.', info);
    sendStatusToWindow('Update available. Downloading...');
  });
  
  autoUpdater.on('update-not-available', (info) => {
    log.info('Update not available.', info);
    sendStatusToWindow('You have the latest version.');
  });
  
  autoUpdater.on('error', (err) => {
    log.error('Error in auto-updater.', err);
    sendStatusToWindow(`Error in auto-updater: ${err.toString()}`);
  });
  
  autoUpdater.on('download-progress', (progressObj) => {
    let message = `Download speed: ${progressObj.bytesPerSecond} - Downloaded ${progressObj.percent}%`;
    log.info(message);
    sendStatusToWindow(message);
  });
  
  autoUpdater.on('update-downloaded', (info) => {
    log.info('Update downloaded', info);
    
    // Prompt user to restart the app
    dialog.showMessageBox({
      type: 'info',
      title: 'Application Update',
      message: 'A new version has been downloaded. Restart the application to apply the updates.',
      buttons: ['Restart', 'Later']
    }).then((returnValue) => {
      if (returnValue.response === 0) {
        autoUpdater.quitAndInstall();
      }
    });
  });
}

// Send messages to the renderer process
function sendStatusToWindow(text) {
  log.info(text);
  if (mainWindow) {
    mainWindow.webContents.send('update-status', text);
  }
}

// Create application menu
const createAppMenu = () => {
  const isMac = process.platform === 'darwin';
  
  const template = [
    // App menu (macOS only)
    ...(isMac ? [{
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    }] : []),
    
    // File menu
    {
      label: 'File',
      submenu: [
        {
          label: 'Refresh Inbox',
          accelerator: 'CmdOrCtrl+R',
          click: () => {
            mainWindow.webContents.reload();
          }
        },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit' }
      ]
    },
    
    // Edit menu
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        ...(isMac ? [
          { role: 'pasteAndMatchStyle' },
          { role: 'delete' },
          { role: 'selectAll' },
          { type: 'separator' },
          {
            label: 'Speech',
            submenu: [
              { role: 'startSpeaking' },
              { role: 'stopSpeaking' }
            ]
          }
        ] : [
          { role: 'delete' },
          { type: 'separator' },
          { role: 'selectAll' }
        ])
      ]
    },
    
    // View menu
    {
      label: 'View',
      submenu: [
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
        { type: 'separator' },
        {
          label: 'Developer Tools',
          accelerator: isMac ? 'Alt+Command+I' : 'Ctrl+Shift+I',
          click: () => { mainWindow.webContents.toggleDevTools(); }
        }
      ]
    },
    
    // Help menu
    {
      role: 'help',
      submenu: [
        {
          label: 'Learn More',
          click: async () => {
            await shell.openExternal('https://github.com/your-username/smart-inbox-cleaner');
          }
        },
        {
          label: 'Restart Python Backend',
          click: () => {
            if (pythonProcess) {
              pythonProcess.kill();
            }
            startPythonBackend();
          }
        }
      ]
    }
  ];
  
  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
};

// When we need to inject custom CSS to the loaded Streamlit page
const injectCustomCSS = () => {
  const cssContent = `
    /* Hide Streamlit's native menu and footer */
    header[data-testid="stHeader"] {
      display: none !important;
    }
    footer {
      display: none !important;
    }
    
    /* Add padding for the custom titlebar */
    .main .block-container {
      padding-top: 10px;
    }
    
    /* Improved button styling */
    .stButton > button {
      border-radius: 8px;
      transition: all 0.2s ease;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* Card-like styling for widgets */
    div[data-testid="stForm"], div.stAlert {
      border-radius: 10px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
      transition: all 0.3s ease;
    }
    
    /* Improved scrollbar */
    ::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }
    
    ::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
      background: #c1c1c1;
      border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
      background: #a8a8a8;
    }
    
    /* Animation for content loading */
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    
    .stApp {
      animation: fadeIn 0.3s ease-in-out;
    }
  `;
  
  // Inject the CSS once the page has loaded
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.insertCSS(cssContent).catch(err => {
      console.error('Failed to inject CSS:', err);
    });
  });
};

const createWindow = () => {
  // Create the browser window with frameless design for macOS
  const isMac = process.platform === 'darwin';
  
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
    backgroundColor: '#f5f5f5', // Match Streamlit background color
    minWidth: 800,
    minHeight: 600,
    
    // Modern UI with native look
    frame: false, // Frameless window
    titleBarStyle: isMac ? 'hiddenInset' : 'hidden',
    trafficLightPosition: { x: 12, y: 12 },
    
    // Show gracefully
    show: false, // Don't show until ready
  });

  // Show window when ready to avoid flickering
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Set up error handling for the window
  mainWindow.webContents.on('did-fail-load', () => {
    console.log('Window failed to load, retrying...');
    setTimeout(() => {
      // Try to load custom error page first
      mainWindow.loadFile(path.join(__dirname, 'index.html'));
      
      // Then retry connecting to streamlit
      setTimeout(() => {
        mainWindow.loadURL('http://localhost:8501');
      }, 3000);
    }, 1000);
  });

  // Create application menu
  createAppMenu();
  
  // Set up custom CSS for the Streamlit UI
  injectCustomCSS();

  // Initially load our loading page
  mainWindow.loadFile(path.join(__dirname, 'index.html'));
  
  // Give the Streamlit server a moment to start up
  setTimeout(() => {
    // Load the Streamlit web interface
    mainWindow.loadURL('http://localhost:8501');

    // Open DevTools in development mode
    if (process.env.NODE_ENV === 'development') {
      mainWindow.webContents.openDevTools();
    }
  }, 3000); // 3 second delay before loading URL to ensure server is ready
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
    args = [
      'run', 
      'main.py', 
      '--server.headless=true', 
      '--browser.serverAddress=localhost', 
      '--server.port=8501',
      '--theme.primaryColor=#4285F4',
      '--theme.backgroundColor=#f5f5f5',
      '--theme.secondaryBackgroundColor=#ffffff',
      '--theme.textColor=#333333',
      '--theme.font=sans-serif'
    ];
  } else {
    // On Mac/Linux, use the direct command
    command = 'streamlit';
    args = [
      'run', 
      'main.py', 
      '--server.headless=true', 
      '--browser.serverAddress=localhost', 
      '--server.port=8501',
      '--theme.primaryColor=#4285F4',
      '--theme.backgroundColor=#f5f5f5',
      '--theme.secondaryBackgroundColor=#ffffff',
      '--theme.textColor=#333333',
      '--theme.font=sans-serif'
    ];
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
  // Setup auto-updater before creating window
  setupAutoUpdater();
  
  // Create the main window
  createWindow();
  
  // Start the Python backend
  startPythonBackend();
  
  // Check for updates after startup (production builds only)
  if (process.env.NODE_ENV !== 'development') {
    setTimeout(() => {
      autoUpdater.checkForUpdatesAndNotify();
    }, 10000); // Check after 10 seconds to allow app to fully start
  }
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