# API 约定

新版前缀为 `/api/v1`；保留 `/api` HTTP 兼容入口，OpenAPI 仅列新版。
Python 内部旧 app.database/app.repository 模块已移除，代码统一使用分层模块。

| GET 路径 | 用途 |
| --- | --- |
| /health | 健康状态 |
| /prompt-history | Prompt 分页查询 |
| /prompt-history/{record_id} | Prompt 详情 |
| /prompt-history/sessions | 会话分页查询 |
| /prompt-history/tool-events | 工具事件分页查询 |
| /prompt-history/stats | 统计 |
| /prompt-history/projects | 项目筛选选项（完整小型选项集合，无分页） |

记录列表统一返回 `data.items` 与 `data.pagination`（page、pageSize、total）。
页码从 1 开始，pageSize 为 1～100，默认 20。项目选项仍保留原数组协议，
以兼容前端筛选器；未来项目规模增长时应同时升级该接口和选项加载方式。

共用筛选：projectId、projectName、sessionId、startTime、endTime。
Prompt 支持 keyword，会话支持 active/ended 状态，工具支持 toolName 及 success/failed。
时间必须为带时区 ISO 8601，startTime 不晚于 endTime。

错误返回 `error.code`、`error.message`、`error.details`、`error.request_id`。
参数错误为 422，记录不存在为 404，存储不可用为 503，未处理异常为 500。
不返回查询、文件路径或异常堆栈。响应头带 X-Request-ID，日志只记录
方法、路由模板、状态码、耗时和请求标识，不记录查询参数或正文。

无身份认证，默认仅本机访问。CORS 仅允许本机前端的 localhost/127.0.0.1:5174。
