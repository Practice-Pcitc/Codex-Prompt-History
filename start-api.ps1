$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Create .venv and install Python dependencies first. See README.md."
}

Set-Location $Root
& $Python -m uvicorn app.main:app --app-dir server --reload --port 8001
