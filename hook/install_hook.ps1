param(
    [string]$PythonPath = "",
    [string]$CodexHomePath = "$env:USERPROFILE\.codex"
)
$ErrorActionPreference = "Stop"
$HookRoot = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $HookRoot
$HookScript = Join-Path $HookRoot "prompt_hook.py"
$WindowsLauncher = Join-Path $HookRoot "run_prompt_hook.cmd"
if (-not $PythonPath) {
    $PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $PythonPath)) {
        $PythonPath = (Get-Command python -ErrorAction Stop).Source
    }
}
$PythonPath = (Resolve-Path -LiteralPath $PythonPath).Path
$HooksPath = Join-Path $CodexHomePath "hooks.json"
$Handler = [ordered]@{
    type = "command"
    command = "`"$PythonPath`" `"$HookScript`""
    commandWindows = "cmd.exe /d /s /c `"`"$WindowsLauncher`" `"$PythonPath`"`""
    timeout = 3
}
$BackupPath = $null
if (Test-Path -LiteralPath $HooksPath) {
    $Document = [System.IO.File]::ReadAllText($HooksPath) | ConvertFrom-Json
    $BackupPath = "$HooksPath.$([guid]::NewGuid().ToString('N')).bak"
    Copy-Item -LiteralPath $HooksPath -Destination $BackupPath
} else {
    $Document = [pscustomobject]@{ description = "Local Prompt History hooks"; hooks = [pscustomobject]@{} }
}
if (-not $Document.hooks) {
    $Document | Add-Member -NotePropertyName hooks -NotePropertyValue ([pscustomobject]@{}) -Force
}
foreach ($EventName in @("SessionStart", "UserPromptSubmit", "PostToolUse", "SessionEnd")) {
    $Groups = @()
    foreach ($ExistingGroup in @($Document.hooks.$EventName)) {
        if ($null -eq $ExistingGroup) { continue }
        $Remaining = @($ExistingGroup.hooks | Where-Object {
            -not ([string]$_.command).Contains($HookScript) -and
            -not ([string]$_.commandWindows).Contains($WindowsLauncher)
        })
        if ($Remaining.Count) {
            $ExistingGroup.hooks = $Remaining
            $Groups += $ExistingGroup
        }
    }
    $Groups += [pscustomobject]@{ hooks = @($Handler) }
    $Document.hooks | Add-Member -NotePropertyName $EventName -NotePropertyValue $Groups -Force
}
$Json = $Document | ConvertTo-Json -Depth 32
New-Item -ItemType Directory -Force -Path $CodexHomePath | Out-Null
$Utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($HooksPath, $Json, $Utf8WithoutBom)
Write-Output "Installed Prompt History hooks: $HooksPath"
if ($BackupPath) { Write-Output "Previous configuration backup: $BackupPath" }
Write-Output "Existing unrelated handlers are preserved. Restart the client and review its hook configuration."
