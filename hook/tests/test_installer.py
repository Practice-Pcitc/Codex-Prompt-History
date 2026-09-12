import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(os.name != "nt", reason="Windows installer")
def test_installer_preserves_handlers_and_is_idempotent(tmp_path):
    shell = shutil.which("pwsh") or shutil.which("powershell")
    assert shell
    root = Path(__file__).resolve().parents[2]
    home = tmp_path / "temporary home"
    home.mkdir()
    path = home / "hooks.json"
    original = {
        "hooks": {
            "SessionStart": [
                {"matcher": "*", "hooks": [{"type": "command", "command": "echo unrelated"}]}
            ]
        }
    }
    path.write_text(json.dumps(original), encoding="utf-8")
    command = [
        shell,
        "-NoProfile",
        "-File",
        str(root / "hook/install_hook.ps1"),
        "-PythonPath",
        sys.executable,
        "-CodexHomePath",
        str(home),
    ]
    for _ in range(2):
        subprocess.run(command, check=True, capture_output=True, timeout=15)
    document = json.loads(path.read_text(encoding="utf-8-sig"))
    groups = document["hooks"]["SessionStart"]
    assert len(groups) == 2
    assert groups[0]["hooks"][0]["command"] == "echo unrelated"
    assert groups[0]["matcher"] == "*"
    assert sys.executable in groups[1]["hooks"][0]["commandWindows"]
    assert len(list(home.glob("*.bak"))) == 2
    env = dict(
        os.environ,
        PROMPT_HISTORY_DB=str(tmp_path / "history.db"),
        PROMPT_HOOK_LOG=str(tmp_path / "hook.log"),
    )
    result = subprocess.run(
        groups[1]["hooks"][0]["commandWindows"],
        input="{}",
        text=True,
        capture_output=True,
        timeout=10,
        env=env,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
