# 架构与目录

```text
Codex-Prompt-History/
├── backend/
│   ├── app/
│   │   ├── api/deps.py                 Service 依赖注入
│   │   ├── api/v1/router.py            路由汇总
│   │   ├── api/v1/endpoints/           HTTP 参数与响应
│   │   ├── core/                      配置、连接、异常映射与请求日志
│   │   ├── schemas/                   请求、响应和分页模型
│   │   ├── repositories/              只读 SQLite 查询
│   │   ├── services/                  查询用例与存储异常转换
│   │   └── main.py                    应用装配与生命周期
│   ├── history_core/                 Hook/API 共用的标准库存储基础模块
│   │   └── migrations/               编号 SQL 迁移
│   ├── tests/{unit,integration,api}/   分层回归测试
│   ├── pyproject.toml                 后端包与依赖
│   └── .env.example
├── frontend/
│   ├── src/{api,components,views,stores,types,router,utils,styles}/
│   ├── tests/{unit,e2e}/
│   ├── package.json
│   ├── package-lock.json
│   └── .env.example
├── hook/                             独立事件采集入口与存储适配器
│   └── tests/
├── scripts/                          安装、启动与统一检查
├── docs/
├── pyproject.toml                    全仓库测试与 Ruff 配置（不重复定义依赖）
├── .env.example                      Hook 环境变量参考
├── .gitignore
├── CHANGELOG.md
└── README.md
```

正式项目保存在 `D:\Code\02-Projects\Codex-Prompt-History`。
`.git` 负责版本历史；`.venv`、node_modules 和缓存是忽略的本地生成目录。
保留项目根目录名称及 hook/ 的安装路径，避免已有 Hook 绝对路径失效。

后端依赖方向为 API → Service → Repository → SQLite。
API 声明 Pydantic 请求和响应，Service 不依赖 FastAPI，Repository 不处理 HTTP。
`history_core` 只使用标准库，供后端和独立 Hook 共享配置及数据库迁移。
Hook 入口负责识别事件、组装记录并控制单个事件事务；存储适配器不隐式提交。

前端页面组合组件，Pinia 管理查询状态，api/client.ts 管理连接，
api/promptApi.ts 管理接口，utils/format.ts 管理通用展示格式。
列表及详情通过请求序号丢弃过期响应，避免快速操作时覆盖较新的数据。

没有模型调用、RAG、MCP、ORM、上传或用户登录功能，因此不创建相应空目录。
本地开发脚本是当前实际运行方式，不添加没有验证用途的 Docker 和部署骨架。
