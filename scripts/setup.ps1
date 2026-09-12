param([string]$PythonPath = "")

$ErrorActionPreference = "Stop"
$Root = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$VenvDirectory = Join-Path $Root '.venv'
$VenvPython = Join-Path $VenvDirectory 'Scripts\python.exe'
$Node = Get-Command node -ErrorAction SilentlyContinue
$Npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $Node -or -not $Npm) { throw 'Install Node.js LTS from https://nodejs.org/ then reopen PowerShell.' }
& $Node.Source -e 'const [a,b]=process.versions.node.split(".").map(Number);process.exit((a===20&&b>=19)||(a===22&&b>=12)||a>22?0:1)'
if ($LASTEXITCODE) { throw 'Node.js 20.19+ or 22.12+ is required. Install Node.js LTS and reopen PowerShell.' }

function Test-Python([string]$Candidate) {
    if (-not $Candidate -or -not (Test-Path -LiteralPath $Candidate)) { return $false }
    try {
        & $Candidate -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>$null
        return $LASTEXITCODE -eq 0
    } catch { return $false }
}

$PythonCommand = $null
if ($PythonPath) {
    if (-not (Test-Python $PythonPath)) { throw 'The supplied -PythonPath must point to a working Python 3.11+ executable.' }
    $PythonCommand = (Resolve-Path -LiteralPath $PythonPath).Path
} elseif (Test-Python $VenvPython) {
    $PythonCommand = $VenvPython
} else {
    $Launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($Launcher) {
        try {
            $Candidate = & $Launcher.Source -3 -c 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0 -and (Test-Python $Candidate)) { $PythonCommand = $Candidate }
        } catch { }
    }
    if (-not $PythonCommand) {
        $Python = Get-Command python.exe -ErrorAction SilentlyContinue
        if ($Python -and (Test-Python $Python.Source)) { $PythonCommand = $Python.Source }
    }
}
if (-not $PythonCommand) {
    throw 'Install Python 3.11+ from https://www.python.org/downloads/windows/ (include Python Launcher), reopen PowerShell, and rerun setup. Alternatively use .\scripts\setup.ps1 -PythonPath C:\path\to\python.exe.'
}

Push-Location $Root
try {
    if ((Test-Path -LiteralPath $VenvDirectory) -and -not (Test-Python $VenvPython)) {
        $ResolvedVenv = (Resolve-Path -LiteralPath $VenvDirectory).Path
        if ($ResolvedVenv -ne (Join-Path $Root '.venv')) { throw 'Unexpected virtual environment path.' }
        $Backup = Join-Path $Root ('.venv-backup-' + [guid]::NewGuid().ToString('N'))
        Move-Item -LiteralPath $ResolvedVenv -Destination $Backup
        Write-Output "Preserved unusable environment at $Backup"
    }
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        & $PythonCommand -m venv $VenvDirectory
        if ($LASTEXITCODE) { throw 'Could not create .venv. Any previous environment is preserved in its backup directory.' }
    }
    & $VenvPython -m pip install -e './backend[dev]'
    if ($LASTEXITCODE) { throw 'Python dependency installation failed. Check network access and rerun setup.' }
    $Cache = Join-Path $Root 'frontend\.npm-cache-standalone'
    & $Npm.Source --prefix frontend --cache $Cache ci
    if ($LASTEXITCODE) { throw 'Frontend dependency installation failed. Check network access and rerun setup.' }
    Write-Output 'Setup complete. In two PowerShell windows at this repository, run:'
    Write-Output '  .\scripts\start-backend.ps1'
    Write-Output '  .\scripts\start-frontend.ps1'
    Write-Output 'Open http://localhost:5174/prompt-history and choose projects in collection settings.'
} finally { Pop-Location }
