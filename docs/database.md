# 数据库与迁移

默认 SQLite 位于项目根目录 data/prompt_history.db，Hook 和 API 使用相同解析规则。
环境变量 PROMPT_HISTORY_DB 可指定绝对路径或相对于项目根目录的路径。
历史版本若产生 server/data/prompt_history.db，可显式指定原文件；
重命名目录后的对应位置为 backend/data/prompt_history.db。整理过程不合并私人数据库。

表包括 prompt_records（追加记录）、codex_sessions（可更新会话摘要）、
codex_tool_events（追加事件）和 schema_migrations（迁移版本）。
追加记录使用 created_at，会话使用 started_at、ended_at、updated_at；
追加数据没有单独的 updated_at，因为本项目不提供编辑用例。
现有列与数据保持兼容，迁移 001 仅将初始表结构纳入版本管理。

迁移唯一来源为 backend/history_core/migrations/NNN_description.sql。
由 history_core.database.initialize_schema 在 Hook/API 启动时应用，
事务中执行 SQL 并记录版本，失败时回滚。已存在的初始表通过 IF NOT EXISTS 保留。
不要改写已应用的 SQL，新增变化使用下一个编号，并补充兼容和回滚测试。
每个 SQL 语句以分号结束，完整语句后换行；不在脚本中手动 BEGIN/COMMIT。

Hook 每个事件使用一个显式事务：建立或更新会话、写记录、递增计数一起提交。
失败时全部回滚，连接最终关闭。API Repository 只查询，不隐式提交或每次建表。
SQLite 启用 WAL 与有限锁等待，迁移和采集失败遵守 Hook 不阻塞客户端的行为。

整理前若有重要数据，升级前先关闭写入进程并做数据库备份。
不要仅复制仍在写入的 .db 而遗漏 WAL；可使用 SQLite 备份接口。
迁移版本不自动实现降级或数据清理，本次也未运行真实历史数据删除。

记录默认无限期保留，本项目暂不自动清理历史；可关闭采集并自行备份管理。
