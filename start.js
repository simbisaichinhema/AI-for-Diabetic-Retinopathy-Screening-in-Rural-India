#!/usr/bin/env node
/**
 * Cross-platform start script — works on Linux, macOS, and Windows.
 * Starts FastAPI backend + Vite dev server, waits for model warmup.
 */
import { spawn, execSync } from 'child_process';
import { existsSync } from 'fs';
import { join, resolve } from 'path';
import { fileURLToPath } from 'url';
import http from 'http';

const __dirname = resolve(fileURLToPath(import.meta.url), '..');
const WORKSPACE = resolve(__dirname, '..');

// Detect Windows
const isWin = process.platform === 'win32';

// Python / uvicorn paths
const venvBin = isWin ? join(WORKSPACE, '.venv', 'Scripts') : join(WORKSPACE, '.venv', 'bin');
const uvicorn = join(venvBin, isWin ? 'uvicorn.exe' : 'uvicorn');

if (!existsSync(uvicorn)) {
  console.error(`Missing Python environment: ${join(WORKSPACE, '.venv')}`);
  console.error(`Create it with: python -m venv ${join(WORKSPACE, '.venv')}`);
  process.exit(1);
}

// Install node_modules if missing
if (!existsSync(join(__dirname, 'node_modules'))) {
  console.log('Installing frontend dependencies...');
  execSync('npm ci', { cwd: __dirname, stdio: 'inherit' });
}

// Health check helper
function checkHealth(url) {
  return new Promise((resolve) => {
    const req = http.get(url, { timeout: 2000 }, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => resolve(data));
    });
    req.on('error', () => resolve(null));
    req.on('timeout', () => { req.destroy(); resolve(null); });
  });
}

// Start backend
console.log('Starting FastAPI backend and loading the Hugging Face model...');
const backend = spawn(uvicorn, ['backend.app:app', '--app-dir', __dirname, '--host', '0.0.0.0', '--port', '8000'], {
  stdio: 'inherit',
  shell: isWin,
});

let backendRunning = true;
backend.on('error', (err) => {
  console.error('Backend failed to start:', err.message);
  backendRunning = false;
});
backend.on('close', (code) => {
  if (backendRunning) console.error(`Backend exited with code ${code}`);
  backendRunning = false;
});

// Wait for backend model to be ready
async function waitForBackend() {
  for (let i = 0; i < 120; i++) {
    const res = await checkHealth('http://localhost:8000/api/models/status');
    if (res && res.includes('"classifier":true')) {
      console.log('Backend ready: http://localhost:8000');
      return true;
    }
    if (!backendRunning) {
      console.error('Backend stopped during startup. Check Python dependencies.');
      return false;
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
  console.error('Backend did not load the model within 120 seconds.');
  return false;
}

const ready = await waitForBackend();
if (!ready) process.exit(1);

// Start frontend
console.log('Frontend starting: http://localhost:5173');
console.log('Press Ctrl+C to stop both services.');

const frontend = spawn('npm', ['run', 'dev', '--', '--host', '0.0.0.0'], {
  cwd: __dirname,
  stdio: 'inherit',
  shell: isWin,
});

frontend.on('error', (err) => {
  console.error('Frontend failed to start:', err.message);
  backend.kill();
  process.exit(1);
});

// Graceful shutdown
function cleanup() {
  frontend.kill();
  backend.kill();
}
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
if (isWin) process.on('close', cleanup);
