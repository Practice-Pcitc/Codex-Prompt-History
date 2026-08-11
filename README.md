# Codex Prompt History

这是从 CallScope 中拆出的独立本地项目，用于记录 Codex 生命周期事件并查看历史记录。

## 组成

- `hook/`：`SessionStart`、`UserPromptSubmit`、`PostToolUse`、`SessionEnd` Hook。
- `server/`：独立 FastAPI 查询服务，默认端口 `8001`。
- `viewer/`：Vue3 Prompt History 页面，默认端口 `5174`。
- `data/`：本地 SQLite 数据，不提交到 Git。
- `logs/`：本地运行日志，不提交到 Git。

## 首次安装

```powershell
Set-Location '项目绝对路径'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Set-Location viewer
npm.cmd install
```

安装 Codex Hook：

```powershell
Set-Location '项目绝对路径'
.\hook\install_hook.ps1
```

重新启动 Codex CLI，在 `/hooks` 中检查四个生命周期 Hook 并信任配置。

## 启动

后端窗口：

```powershell
Set-Location '项目绝对路径'
.\.venv\Scripts\uvicorn.exe app.main:app --app-dir server --reload --port 8001
```

前端窗口：

```powershell
Set-Location '项目绝对路径\viewer'
npm.cmd run dev
```

打开 `http://localhost:5174/prompt-history`。

## 本地数据

默认数据库：`data/prompt_history.db`。

默认日志：`logs/prompt-hook.log`。

可以通过 `PROMPT_HISTORY_DB` 和 `PROMPT_HOOK_LOG` 修改路径。Hook 失败时保持 fail-open，不能阻塞 Codex。

如果需要与 CallScope 项目表进行可选关联，可以设置 `CALLSCOPE_PROJECT_DB` 指向 CallScope 的 SQLite 数据库；不设置时按工作目录名称记录项目。
