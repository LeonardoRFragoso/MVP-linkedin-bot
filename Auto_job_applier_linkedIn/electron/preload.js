const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getPlatform: () => ipcRenderer.invoke('get-platform'),
  
  // Add more IPC methods as needed
  onBotStatus: (callback) => ipcRenderer.on('bot-status', callback),
  onBotLog: (callback) => ipcRenderer.on('bot-log', callback),
});

// Indicate that we're running in Electron
contextBridge.exposeInMainWorld('isElectron', true);
