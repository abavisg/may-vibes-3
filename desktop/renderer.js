// DOM Elements
const statusElement = document.getElementById('status');
const consoleElement = document.getElementById('console');
const restartButton = document.getElementById('restart-btn');

// Update console with messages
function appendToConsole(message, type = 'info') {
  const timestamp = new Date().toLocaleTimeString();
  const formattedMessage = `[${timestamp}] [${type}] ${message}`;
  
  // Append to console
  consoleElement.textContent += formattedMessage + '\n';
  
  // Auto-scroll to bottom
  consoleElement.scrollTop = consoleElement.scrollHeight;
}

// Update status
function updateStatus(message) {
  statusElement.textContent = message;
  appendToConsole(`Status changed: ${message}`);
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
  appendToConsole('Application initialized');
  updateStatus('Waiting for Python backend...');
  
  // Setup event listeners for Python process output
  if (window.api) {
    window.api.onPythonOutput((data) => {
      appendToConsole(data, 'python');
      
      // Update status based on Python output
      if (data.includes('Server running')) {
        updateStatus('Python backend running');
      }
    });
    
    window.api.onPythonError((data) => {
      appendToConsole(data, 'error');
      updateStatus('Error in Python backend');
    });
    
    // Setup restart button
    restartButton.addEventListener('click', () => {
      updateStatus('Restarting Python backend...');
      window.api.restartPython();
    });
  } else {
    updateStatus('API not available. Running in development mode?');
    appendToConsole('window.api is not available. This may be because the preload script is not working correctly.', 'error');
  }
}); 