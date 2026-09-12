@echo off
setlocal
set "PYTHONUTF8=1"
set "HOOK_ROOT=%~dp0"
set "PYTHON_EXE=%~1"
if not defined PYTHON_EXE set "PYTHON_EXE=%HOOK_ROOT%..\.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
  "%PYTHON_EXE%" "%HOOK_ROOT%prompt_hook.py"
) else (
  python "%HOOK_ROOT%prompt_hook.py"
)
rem A recorder failure must never block the calling client.
exit /b 0
