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

// Add handler for checking updates manually
ipcMain.on('check-for-updates', () => {
  log.info('Manual update check requested');
  sendStatusToWindow('Checking for updates...');
  autoUpdater.checkForUpdatesAndNotify()
    .catch(err => {
      log.error('Error checking for updates:', err);
      sendStatusToWindow(`Error checking for updates: ${err.message}`);
    });
});

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
      '--theme.font=sans serif'
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
      '--theme.font=sans serif'
    ];
  }
  
  // Set environment variables for the Python process
  const env = { 
    ...process.env,
    ELECTRON_APP_VERSION: app.getVersion(),
    ELECTRON_RUN_AS_NODE: '1'  // Signal to Python that we're running in Electron
  };
  
  pythonProcess = spawn(command, args, {
    cwd: pythonAppPath,
    shell: useShell,
    env: env
  });
} 