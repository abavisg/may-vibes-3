const { app, BrowserWindow, ipcMain, Menu, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
// // Removed autoUpdater dependency
const log = require('electron-log');

// Configure logging
log.transports.file.level = 'info';
log.info('Application starting...');

// Auto-updater logging
// autoUpdater.logger = log;
// autoUpdater.logger.transports.file.level = "info";

let pythonProcess = null;
let mainWindow = null;

// Handle creating/removing shortcuts on Windows when installing/uninstalling
// Windows installer code commented out
// // Windows installer code commented out
// if (require('electron-squirrel-startup')) {
//   app.quit();
// }
//   app.quit();
// }
//   app.quit();
// }
// 
// // // Setup auto-updater events
// // function setupAutoUpdater() {
//   log.info("Auto-updater disabled");
// //   autoUpdater.on('checking-for-update', () => {
// //     log.info('Checking for update...');
// //     sendStatusToWindow('Checking for update...');
// //   });
// //   
// //   autoUpdater.on('update-available', (info) => {
// //     log.info('Update available.', info);
// //     sendStatusToWindow('Update available. Downloading...');
// //   });
// //   
// //   autoUpdater.on('update-not-available', (info) => {
// //     log.info('Update not available.', info);
// //     sendStatusToWindow('You have the latest version.');
// //   });
// //   
// //   autoUpdater.on('error', (err) => {
// //     log.error('Error in auto-updater.', err);
// //     sendStatusToWindow(`Error in auto-updater: ${err.toString()}`);
// //   });
// //   
// //   autoUpdater.on('download-progress', (progressObj) => {
// //     let message = `Download speed: ${progressObj.bytesPerSecond} - Downloaded ${progressObj.percent}%`;
// //     log.info(message);
// //     sendStatusToWindow(message);
// //   });
// //   
// //   autoUpdater.on('update-downloaded', (info) => {
// //     log.info('Update downloaded', info);
// //     
// //     // Prompt user to restart the app
// //     dialog.showMessageBox({
// //       type: 'info',
// //       title: 'Application Update',
// //       message: 'A new version has been downloaded. Restart the application to apply the updates.',
// //       buttons: ['Restart', 'Later']
// //     }).then((returnValue) => {
//       if (returnValue.response === 0) {
//         autoUpdater.quitAndInstall();
//       }
//     });
//  });
// }

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
      log.error('Failed to inject CSS:', err);
    });
  });
};

const createWindow = () => {
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
    backgroundColor: '#f5f5f5',
    minWidth: 800,
    minHeight: 600,
    frame: false,
    titleBarStyle: isMac ? 'hiddenInset' : 'hidden',
    trafficLightPosition: { x: 12, y: 12 },
    show: false,
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.webContents.on('did-fail-load', () => {
    log.info('Window failed to load, retrying...');
    // Try to load custom error page first
    mainWindow.loadFile(path.join(__dirname, 'index.html'));
    // Then retry connecting to streamlit after 3 seconds
    setTimeout(() => {
      mainWindow.loadURL('http://localhost:8501');
    }, 3000);
  });

  createAppMenu();
  injectCustomCSS();

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  // Give the Streamlit server a moment to start up
  setTimeout(() => {
    mainWindow.loadURL('http://localhost:8501');
    if (process.env.NODE_ENV === 'development') {
      mainWindow.webContents.openDevTools();
    }
  }, 3000);
};

// Start Python backend
const startPythonBackend = () => {
  // Get the path to the Python app directory
  // When packaged, the resources folder contains our app
  let pythonAppPath;
  
  if (app.isPackaged) {
    // In production, look for the app in the resources folder
    pythonAppPath = path.join(process.resourcesPath, 'smart-inbox-cleaner');
  } else {
    // In development, look for the app in the parent directory
    pythonAppPath = path.join(__dirname, '..', 'smart-inbox-cleaner');
  }
  
  log.info('Starting Python backend with Streamlit...');
  log.info(`Python app path: ${pythonAppPath}`);
  
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
      'smart-inbox-cleaner/main.py',
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
    // On Mac/Linux, use the full path to Streamlit if possible
    command = '/Library/Frameworks/Python.framework/Versions/3.12/bin/streamlit';
    if (!fs.existsSync(command)) {
      command = '/usr/local/bin/streamlit';
    }
    if (!fs.existsSync(command)) {
      command = '/opt/homebrew/bin/streamlit';
    }
    if (!fs.existsSync(command)) {
      command = 'streamlit';
    }
    if (command !== 'streamlit' && !fs.existsSync(command)) {
      log.error(`Streamlit not found at ${command}`);
      dialog.showErrorBox('Streamlit Not Found', `Could not find Streamlit at ${command}. Please install Streamlit and try again.`);
      return;
    }
    args = [
      'run', 
      'smart-inbox-cleaner/main.py',
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
  
  log.info(`Spawning: ${command} ${args.join(' ')} in ${pythonAppPath}`);

  try {
    // Add detailed logging before spawning the process
    const projectRoot = path.join(__dirname, '..');
    log.info('Project root directory:', projectRoot);
    log.info('Current working directory:', process.cwd());
    
    pythonProcess = spawn(command, args, {
      cwd: path.join(__dirname, '..'),
      shell: useShell,
      env: {
        ...process.env,
        ELECTRON_APP_VERSION: app.getVersion(),
        ELECTRON_RUN_AS_NODE: '1',
        // Add logging level for Python
        PYTHONUNBUFFERED: '1',
        STREAMLIT_LOG_LEVEL: 'debug'
      },
    });

    pythonProcess.stdout.on('data', (data) => {
      log.info(`Python stdout: ${data}`);
      if (mainWindow) {
        mainWindow.webContents.send('python-output', data.toString());
      }
    });

    pythonProcess.stderr.on('data', (data) => {
      log.error(`Python stderr: ${data}`);
      if (mainWindow) {
        mainWindow.webContents.send('python-error', data.toString());
      }
    });

    pythonProcess.on('close', (code) => {
      log.info(`Python process exited with code ${code}`);
      
      // Update main window with exit code
      if (mainWindow) {
        mainWindow.webContents.send('python-output', `Python process exited with code ${code}`);
      }
    });
  } catch (error) {
    log.error('Error starting Python backend:', error);
    if (mainWindow) {
      mainWindow.webContents.send('python-error', `Error starting Python backend: ${error.toString()}`);
    }
  }
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