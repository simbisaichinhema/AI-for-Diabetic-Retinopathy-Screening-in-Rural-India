<# 
  Cross-platform start script for Windows (PowerShell).
  Starts FastAPI backend + Vite dev server.
  Usage: .\start.ps1
#>
$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceDir = Split-Path -Parent $ProjectDir
$VenvScripts = Join-Path $WorkspaceDir ".venv" "Scripts"
$Uvicorn = Join-Path $VenvScripts "uvicorn.exe"
$Python = Join-Path $VenvScripts "python.exe"

if (-not (Test-Path $Uvicorn)) {
    Write-Host "Missing Python environment: $(Join-Path $WorkspaceDir '.venv')" -ForegroundColor Red
    Write-Host "Create it with: python -m venv $(Join-Path $WorkspaceDir '.venv')"
    exit 1
}

if (-not (Test-Path (Join-Path $ProjectDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    npm ci --prefix $ProjectDir
}

Write-Host "Starting FastAPI backend and loading the Hugging Face model..." -ForegroundColor Cyan

$backend = Start-Process -FilePath $Uvicorn -ArgumentList "backend.app:app","--app-dir","$ProjectDir","--host","0.0.0.0","--port","8000" -PassThru -NoNewWindow

$ready = $false
for ($i = 0; $i -lt 120; $i++) {
    try {
        $res = Invoke-WebRequest -Uri "http://localhost:8000/api/models/status" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($res.Content -match '"classifier":true') {
            $ready = $true
            break
        }
    } catch {}
    if ($backend.HasExited) {
        Write-Host "Backend stopped during startup. Check Python dependencies." -ForegroundColor Red
        exit 1
    }
    Start-Sleep -Seconds 1
}

if (-not $ready) {
    Write-Host "Backend did not load the model within 120 seconds." -ForegroundColor Red
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "Backend ready: http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend starting: http://localhost:5173" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop both services."

try {
    npm run dev --prefix $ProjectDir -- --host 0.0.0.0
} finally {
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
}
