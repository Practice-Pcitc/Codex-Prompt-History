# 提示词工作台

## 分层

`app/api/v1/endpoints/workbench.py` 声明协议与响应模型；`services/workbench.py` 管理收藏和设置事务；`repositories/workbench.py` 执行数据库查询。`services/collector.py` 是只读会话适配器，由 FastAPI lifespan 启动，每 5 秒扫描一次，退出时停止。

前端 `views/Workbench.vue` 展示页面，`components/WorkbenchDialogs.vue` 展示设置与详情，`composables/useWorkbench.ts` 管理交互与轮询，`api/workbench.ts` 封装请求与类型。`/history` 重定向到新版，旧诊断页仅在 `/diagnostics` 保留。

## 采集语义

默认没有选中项目。选中目录及其子目录可导入历史用户消息，排除目录优先。暂停区间保存在数据库，恢复后跳过这些区间内的消息；普通停机不产生暂停区间。文件签名变化时重新解析，消息来源键用于幂等去重，删除来源键保留为 tombstone。

桌面格式只接受明确标记为 `user.text` 的内容段，不把 role=user 的所有附加材料当成用户输入；旧格式使用 user_message 事件。有桌面用户段时优先使用该表示，避免两份表示重复导入。忽略尚未写完的最后一行，下次文件变化再读取。

读取任何消息前先检查 session_meta.source。目前支持 cli、vscode 两种主任务来源。source.subagent（包含 guardian 审批任务及 thread_spawn）或 parent_thread_id 标记的内部任务整份跳过，其他未知来源暂不导入。不能仅凭 role=user 或 user.text 判断是否为人类提问。清理旧误收数据根据已确认的内部 session_id 与 codex-local-session 来源进行，不按英文前缀删除；用户自己引用相同文字仍被保留。独立收藏副本保留，原始 Codex 文件只读。

左侧项目列表合并发现的主任务目录与已保存记录目录，显示当前启用状态和记录数。选择项目只筛选视图，点击“启用这个项目”才扩大采集范围。默认按任务浏览，全文通过详情打开。

启用工作台设置后，旧 Hook 不再往同一数据库写入，避免绕过范围、暂停及产生双份数据。收藏和模板为独立副本，删除原记录会解除关联但保留副本。

## API

统一前缀 `/api/v1/workbench`，响应为 `{ "data": ... }`；列表分页 `{ items, pagination: { page, pageSize, total } }`。字段输出使用 camelCase。列表查询参数为 snake_case，page 从 1 开始，page_size 为 1～100。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET / PUT | `/settings` | 读取/更新 enabled、projects、excludedProjects、redact |
| GET | `/status` | 来源、状态、扫描/入库时间、可选项目、错误 |
| GET | `/overview` | 已保存提问、任务、收藏数量，以及各目录的记录统计 |
| GET | `/records` | keyword、session_id、project、hide_brief 过滤 |
| GET | `/tasks` | keyword、project 过滤，同任务按完整上下文聚合 |
| GET | `/library` | keyword、kind、tag 过滤 |
| POST | `/records/{id}/favorites` | 幂等收藏原始消息 |
| DELETE | `/records/{id}` | 删除原始消息并记住来源键 |
| PUT / DELETE | `/library/{id}` | 编辑/删除独立副本 |
| POST | `/library/{id}/templates` | 生成可编辑模板副本 |

收藏编辑字段为 title、content、tags、note。模板变量采用 `{{名称}}`，浏览器填入后复制，不改变保存的模板。生成仅做本地替换，不调用 AI，也不声称已验证提示词有效。

## 迁移与限制

002 迁移为 prompt_records 增加唯一 source_key，新增 collector_settings、collector_files、deleted_prompts、prompt_library。已有数据保留。升级前建议用 SQLite backup API 备份数据，不能用正在写入的数据库文件副本代替可靠备份。

本地会话格式可能随客户端变化；不读取其他电脑、ChatGPT 网页、助手全文或附件。默认脱敏只作用于新采集副本，不保证识别所有秘密。采集配置与私人数据不属于 Git 发布内容。
