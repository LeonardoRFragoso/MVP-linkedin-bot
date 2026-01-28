const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;
let frontendProcess;

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    title: 'LinkedIn Bot - Automatize suas candidaturas',
    autoHideMenuBar: true,
  });

  // Load the app
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadURL('http://localhost:3000');
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

function startBackend() {
  const pythonPath = isDev 
    ? path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe')
    : path.join(process.resourcesPath, 'python', 'python.exe');
  
  const backendPath = isDev
    ? path.join(__dirname, '..')
    : process.resourcesPath;

  console.log('Starting backend server...');
  
  backendProcess = spawn(pythonPath, [
    '-m', 'uvicorn', 
    'backend.api.main:app', 
    '--host', '127.0.0.1', 
    '--port', '8002'
  ], {
    cwd: backendPath,
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
  });
}

function startFrontend() {
  if (isDev) {
    // In development, frontend should already be running via npm run dev
    console.log('Development mode: Connect to existing frontend at localhost:3000');
    return;
  }

  const npmPath = process.platform === 'win32' ? 'npm.cmd' : 'npm';
  const frontendPath = path.join(process.resourcesPath, 'frontend');

  console.log('Starting frontend server...');
  
  frontendProcess = spawn(npmPath, ['start'], {
    cwd: frontendPath,
    env: { ...process.env, PORT: '3000' },
    shell: true,
  });

  frontendProcess.stdout.on('data', (data) => {
    console.log(`Frontend: ${data}`);
  });

  frontendProcess.stderr.on('data', (data) => {
    console.error(`Frontend Error: ${data}`);
  });
}

function waitForServer(url, maxAttempts = 30) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const http = require('http');
    
    const check = () => {
      attempts++;
      http.get(url, (res) => {
        resolve(true);
      }).on('error', () => {
        if (attempts < maxAttempts) {
          setTimeout(check, 1000);
        } else {
          reject(new Error('Server did not start in time'));
        }
      });
    };
    
    check();
  });
}

app.whenReady().then(async () => {
  // Check if backend is already running
  let backendRunning = false;
  try {
    await waitForServer('http://127.0.0.1:8002/health', 3);
    console.log('Backend already running!');
    backendRunning = true;
  } catch {
    console.log('Backend not running, starting...');
    startBackend();
  }
  
  // Wait for backend to be ready
  try {
    console.log('Waiting for backend server...');
    await waitForServer('http://127.0.0.1:8002/health');
    console.log('Backend server is ready!');
  } catch (error) {
    console.error('Failed to start backend:', error);
  }

  // Check if frontend is already running (in dev mode)
  if (isDev) {
    try {
      console.log('Checking if frontend is running...');
      await waitForServer('http://localhost:3000', 5);
      console.log('Frontend already running!');
    } catch {
      console.error('Frontend not running! Please start it with: cd frontend && npm run dev');
    }
  } else {
    startFrontend();
    try {
      console.log('Waiting for frontend server...');
      await waitForServer('http://localhost:3000');
      console.log('Frontend server is ready!');
    } catch (error) {
      console.error('Failed to start frontend:', error);
    }
  }

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // Kill backend process
  if (backendProcess) {
    backendProcess.kill();
  }
  
  // Kill frontend process
  if (frontendProcess) {
    frontendProcess.kill();
  }

  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for communication with renderer
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('get-platform', () => {
  return process.platform;
});
