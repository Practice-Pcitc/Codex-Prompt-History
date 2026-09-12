$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
Push-Location $Root
try {
    & $Python -m ruff check hook backend
    if ($LASTEXITCODE) { throw "Python lint failed" }
    & $Python -m ruff format --check hook backend
    if ($LASTEXITCODE) { throw "Python formatting failed" }
    & $Python -m pytest
    if ($LASTEXITCODE) { throw "Python tests failed" }
    npm.cmd --prefix frontend run test
    if ($LASTEXITCODE) { throw "Frontend tests failed" }
    npm.cmd --prefix frontend run format:check
    if ($LASTEXITCODE) { throw "Frontend formatting failed" }
    npm.cmd --prefix frontend run build
    if ($LASTEXITCODE) { throw "Frontend build failed" }
} finally { Pop-Location }
