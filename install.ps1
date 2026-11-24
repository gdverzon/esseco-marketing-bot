$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.10 or newer is required. Install it from python.org and enable Add Python to PATH."
}

python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Installation complete." -ForegroundColor Green
Write-Host "Ensure the Codex CLI is installed and authenticated with: codex login"
Write-Host "Start Codex Bot with: .\run.ps1"

