# 安装与排错参考

日常操作先看 [README](../README.md)。本文提供完整环境处理、配置和维护说明。

## 安装与启动（Windows）

### 1. 准备环境与代码

安装 [Python 3.11 或更高版本](https://www.python.org/downloads/windows/)（包含 Python Launcher）和 [Node.js LTS](https://nodejs.org/)（22.12+）。需要联网下载依赖。安装后重新打开 PowerShell。

从本仓库页面点击 **Code → Download ZIP**，解压到自己有写入权限的目录；或者使用 Git：

```powershell
git clone https://github.com/Practice-Pcitc/Codex-Prompt-History.git
cd Codex-Prompt-History
```

下载 ZIP 的用户：进入解压后能看到 README.md、backend、frontend、scripts 的文件夹，在资源管理器地址栏输入 `powershell` 并回车。后续命令都在这个目录执行，不需要修改源码或照抄作者电脑的磁盘路径。

### 2. 安装依赖

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup.ps1
```

脚本自动检查 Node/Python，创建 `.venv`，安装前后端依赖。优先复用可用的项目 Python 环境；失效或过旧的环境会保留为 `.venv-backup-*`，再重新创建。npm 使用项目自己的缓存，避免全局缓存目录权限错误。

如果 Python 安装在自定义位置且没有注册 Launcher，可显式传入已经安装的解释器路径，例如：

```powershell
.\scripts\setup.ps1 -PythonPath 'C:\Python312\python.exe'
```

此参数不能把 Python 3.10 变成 3.11。

### 3. 启动服务

在仓库目录打开两个 PowerShell 窗口，分别执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\start-backend.ps1
```

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\start-frontend.ps1
```

打开 [提示词工作台](http://localhost:5174/prompt-history)。保持两个终端运行；按 `Ctrl+C` 停止。下次直接执行上述启动命令，无需重新安装。升级后重新执行 setup，再重启两个服务。

### 4. 选择项目并开始使用

1. 启动后自动补录本机所有项目的历史用户提问，无需逐个启用项目。
2. 点击左侧项目名称，查看该项目下的对话列表。
3. 点击 **打开对话**，按发送顺序阅读完整提示词；长对话可翻页，点击 **返回本项目对话列表** 可查看另一段对话。
4. 新项目和新对话自动同步。如需缩小范围，在 **采集设置** 中关闭“自动记录所有项目”并选择目录；排除目录始终优先。
5. 在 **收藏与模板** 中点击 **生成模板**，检查并编辑变量，例如 `{{项目路径}}`。以后点击 **填写变量并复制** 即可复用。

**不需要打开本工具的项目文件夹才能记录其他项目；需要保持本工具的后端运行，默认无需设置项目范围。** 网页只是查看入口，关闭网页不会停止仍在运行的后端。后端停止期间的消息，下次启动会补录；主动点击“暂停记录”期间的消息，恢复后不会补录。

## 哪些内容会记录

| 内容 | 行为 |
| --- | --- |
| 所有未排除项目里，你输入的需求、补充、纠错、解释性问题 | 记录 |
| “继续”“好的”等简短回复 | 记录并默认显示 |
| 排除目录（或指定项目模式下未选中目录）中的消息 | 不采集 |
| Codex 自动附加的环境说明、系统/开发者指令 | 不作为用户提问采集 |
| 内部审批（guardian）与子代理任务，即使其中消息角色是 user | 不采集；修复版会清理同一数据库中此前误收的内部记录 |
| AI 回答、工具输入输出、图片二进制、附件正文 | 本版不采集 |
| ChatGPT 网页、其他电脑或未写入本机会话文件的对话 | 不采集 |

来源为 `CODEX_HOME` 下的 `sessions` 与 `archived_sessions`，默认是当前用户目录的 `.codex`。适配器支持带 `user.text` 标记的用户消息，以及旧格式的 `event_msg/user_message`。**本地会话格式不是稳定的公开接口**，客户端升级可能需要更新适配器；页面会显示读取异常。参考 [Codex Hook 文档](https://developers.openai.com/codex/hooks) 对 transcript 格式的说明。

本版主流程不需要安装 Hook，也不需要寻找 `/hooks` 页面。首次启动新版后端会为数据库启用本地会话采集模式；同一数据库的旧 Hook 自动停止新增写入，避免重复记录或绕过暂停设置。旧数据仍可在新版查看，旧地址 `/history` 自动跳转到新版；维护人员可访问 `/diagnostics` 查看旧诊断页。[Hook 说明](../hook/README.md) 供维护旧集成参考。

## 数据与隐私

- 默认数据库是项目的 `data/prompt_history.db`，采集范围、收藏、模板也保存在这里。数据库、缓存和环境文件已忽略，不应上传 GitHub。
- 默认对**新入库**的常见 `password`、`token`、`api_key`、`secret` 字段和 Bearer 凭据脱敏；不能覆盖所有敏感内容，不会重写 Codex 原始文件或追溯修改已有记录。
- 删除原始记录后，后续会话同步不会再次导入该条；独立收藏、模板和 Codex 原始会话仍保留，需分别管理。
- 取消勾选只停止后续采集，不删除旧记录。模板生成是本地文字替换，不会自动判断效果好坏。
- 这是无账号认证的本机工具，启动脚本仅监听本机，请勿直接公开到公网。

可选环境变量：`PROMPT_HISTORY_DB` 指定数据库；`CODEX_HOME` 指定 Codex 数据目录。后端不会自动加载 `.env`，如需覆盖，在启动后端的同一 PowerShell 窗口设置 `$env:变量名 = '值'`。普通使用不需要设置。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| 页面可打开但零记录 | 查看采集状态与来源目录；默认全项目自动同步，请确认该对话保存在本机 |
| 未找到会话来源 | 确认本机 Codex 已产生会话；自定义 CODEX_HOME 时，让后端使用同一目录 |
| 暂停后没有新增 | 点击恢复；暂停期间的内容不会补录 |
| Python 版本错误或虚拟环境失效 | 安装 Python 3.11+，重开终端运行 setup；自定义安装可用 -PythonPath |
| npm EPERM 指向全局缓存 | 使用新版 setup，它明确指定项目缓存；检查项目目录可写、没有其他安装进程占用 |
| 后端连接失败 | 检查后端窗口是否仍运行；查看 [健康检查](http://localhost:8001/api/v1/health) |
| 端口被占用 | 在占用本工具端口的旧终端按 Ctrl+C，再启动，避免同时运行多份 |

## 开发与检查

```powershell
.\scripts\check.ps1
npm.cmd --prefix frontend run test:e2e
```

检查包括 Python 静态/格式检查、后端与 Hook 测试、前端单元测试、格式检查和生产构建。浏览器测试在 Windows 使用本机 Edge，CI 使用 Chromium；测试采用合成数据和临时数据库。

- [架构与目录](architecture.md)
- [工作台行为与接口](workbench.md)
- [数据库与迁移](database.md)
- [开发规范](development.md)
- [变更记录](../CHANGELOG.md)
