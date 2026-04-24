# BuildLeads VPS Setup — Windows Server
# Run this script on the VPS after SSH-ing in.
# Assumes: Python 3.11+ in PATH, git in PATH.

param(
    [string]$DeployDir = "C:\BuildLeads",
    [string]$RepoUrl   = "https://github.com/KemiworldSolutions/buildleads-ie.git",
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "=== BuildLeads VPS Setup ===" -ForegroundColor Cyan

# 1. Clone or update repo
if (Test-Path "$DeployDir\.git") {
    Write-Host "[1/5] Updating existing repo at $DeployDir"
    Push-Location $DeployDir
    git pull origin main
    Pop-Location
} else {
    Write-Host "[1/5] Cloning repo to $DeployDir"
    git clone $RepoUrl $DeployDir
}

Set-Location $DeployDir

# 2. Create venv (separate from KW Signal Dashboard's venv)
Write-Host "[2/5] Creating Python venv at $DeployDir\.venv"
if (-not (Test-Path ".venv")) {
    & $PythonExe -m venv .venv
}

# 3. Install dependencies
Write-Host "[3/5] Installing requirements"
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
& ".\.venv\Scripts\pip.exe" install -r requirements.txt --quiet
Write-Host "  Dependencies installed OK"

# 4. Create .env if it doesn't exist
Write-Host "[4/5] Checking .env"
if (-not (Test-Path ".env")) {
    Write-Host "  .env not found — creating from .env.example"
    Copy-Item ".env.example" ".env"
    Write-Host "  ACTION REQUIRED: edit C:\BuildLeads\.env and fill in your credentials"
    Write-Host "    notepad C:\BuildLeads\.env"
} else {
    Write-Host "  .env already exists — skipping"
}

# 5. Create output directories
Write-Host "[5/5] Creating output directories"
New-Item -ItemType Directory -Force -Path "$DeployDir\out\raw"       | Out-Null
New-Item -ItemType Directory -Force -Path "$DeployDir\out\structured" | Out-Null
New-Item -ItemType Directory -Force -Path "$DeployDir\out\digests"    | Out-Null
New-Item -ItemType Directory -Force -Path "$DeployDir\logs"           | Out-Null

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit .env:        notepad C:\BuildLeads\.env"
Write-Host "  2. Test pipeline:    cd C:\BuildLeads && .\.venv\Scripts\python.exe -m src.pipeline --limit 5"
Write-Host "  3. Register task:    C:\BuildLeads\deploy\register_task.ps1"
