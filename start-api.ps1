$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Uvicorn = Join-Path $Root ".venv\Scripts\uvicorn.exe"

if (-not (Test-Path -LiteralPath $Uvicorn)) {
    throw "Create .venv and install Python dependencies first. See README.md."
}

Set-Location $Root
& $Uvicorn app.main:app --app-dir server --reload --port 8001
