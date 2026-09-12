# 开发与规范对照

依据 D:/Code/RULES_ALL.md 和 D:/Code/RULES_IN.md 整理。

| 规范范围 | 落地方式 |
| --- | --- |
| 项目存放、独立仓库 | D:/Code/02-Projects/Codex-Prompt-History |
| 顶层结构 | backend、frontend、hook、scripts、docs |
| 后端分层 | API / Service / Repository / schemas / core |
| 前端职责 | API 客户端、Pinia、页面、组件、通用 utils |
| 参数与错误 | Pydantic 筛选模型、分页限制、带时区时间、结构化错误 |
| 数据库 | 共用 SQL 迁移、事件事务、连接释放与回滚测试 |
| 日志 | 请求标识、路由模板、耗时；Hook 不记录 Prompt 正文 |
| 配置 | 分别提供示例；环境变量与数据库不提交 Git |
| 检查 | Ruff、pytest、Vitest、Prettier、TypeScript、Vite、Playwright |
| 自动验证 | .github/workflows/check.yml，在推送或 PR 时执行 |

规范要求按实际功能创建模块：本项目不增加空的 Agent/RAG/ORM/Docker 目录。
项目选项接口与追加记录时间字段的兼容例外见 api.md 和 database.md。

## 本地开发

根目录 `.venv` 是独立 Python 环境。backend/pyproject.toml 是依赖唯一来源，
根 pyproject.toml 只定义全仓库工具配置，frontend/package-lock.json 记录前端锁定版本。
安装：运行 `./scripts/setup.ps1`。该脚本创建 `.venv`、安装 backend 可编辑包，
并执行 `npm --prefix frontend ci`；frontend/.npmrc 将缓存固定在项目内，
不依赖机器级 npm 缓存。旧安装也应重新运行该脚本，避免引用已移除的旧目录。

`./scripts/check.ps1` 遇到任一步失败即停止。`npm --prefix frontend run test:e2e`
另行运行浏览器测试，Windows 使用已安装 Edge，Linux CI 使用安装的 Chromium。
浏览器测试使用拦截的合成 API 响应；Hook/API 数据链路由 Python 集成测试验证。
实际客户端 Hook 事件触发仍需在客户端安装配置后确认。

## Git 与升级

当前开发分支保留。先看 git status、git diff，明确暂存相关文件并检查暂存区后提交。
目录迁移在未暂存时可能显示为旧文件删除和新目录未跟踪，Git 提交时会按内容识别重命名。
.gitignore 不影响已有跟踪文件，所以仍需检查暂存区。
禁止上传数据库、日志、.env、缓存和虚拟环境；仅共享合成测试数据。
本次整理不自动安装用户级 Hook，不创建提交、不推送 GitHub。

启动入口改为 scripts/start-backend.ps1 和 scripts/start-frontend.ps1。
Hook 安装入口仍为 hook/install_hook.ps1：合并同名事件中的无关处理器，
仅替换本项目处理器，并创建唯一备份；测试只操作临时配置目录。

本轮实际验证结果见 [validation.md](validation.md)。
