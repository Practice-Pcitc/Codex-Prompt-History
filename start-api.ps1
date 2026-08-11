$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Uvicorn = Join-Path $Root ".venv\Scripts\uvicorn.exe"

if (-not (Test-Path -LiteralPath $Uvicorn)) {
    throw "请先按照 README.md 创建 .venv 并安装 Python 依赖。"
}

Set-Location $Root
& $Uvicorn app.main:app --app-dir server --reload --port 8001
