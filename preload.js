const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld(
  'api', {
    // Send methods
    sendToPython: (message) => {
      ipcRenderer.send('send-to-python', message);
    },
    restartPython: () => {
      ipcRenderer.send('restart-python');
    },
    
    // Receive methods
    onPythonOutput: (callback) => {
      ipcRenderer.on('python-output', (event, ...args) => callback(...args));
    },
    onPythonError: (callback) => {
      ipcRenderer.on('python-error', (event, ...args) => callback(...args));
    },
    
    // Update-related methods
    onUpdateStatus: (callback) => {
      ipcRenderer.on('update-status', (event, ...args) => callback(...args));
    },
    checkForUpdates: () => {
      ipcRenderer.send('check-for-updates');
    }
  }
); 