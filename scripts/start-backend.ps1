$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Create .venv and install Python dependencies first. See README.md."
}

Set-Location $Root
& $Python -m uvicorn app.main:app --app-dir backend --reload --port 8001

exit $LASTEXITCODE
