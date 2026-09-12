# Prompt History Hook

采集 SessionStart、UserPromptSubmit、PostToolUse、SessionEnd 四类事件。
Prompt、会话摘要和工具元数据分别保存；工具输入输出不持久化。
默认数据库为项目根目录 data/prompt_history.db，日志为 logs/prompt-hook.log。
不调用模型或网络，不执行 Prompt 内容；入口捕获异常并正常退出。

从项目根目录安装：

```powershell
.\hook\install_hook.ps1
```

安装器写入用户级 hooks.json，为已有配置创建唯一 .bak，保留无关处理器。
重复安装仅替换当前项目的处理器。可传入 -PythonPath 指定解释器，
-CodexHomePath 指定配置目录。安装后重启客户端并检查、信任配置。
是否支持这些生命周期事件取决于实际使用的客户端。

Windows 启动器优先使用传入解释器，再使用项目 .venv，最后回退 python。
Hook 从相邻 backend/ 加载仅依赖标准库的 history_core；必须保留整个项目结构。

环境变量参考根目录 .env.example，程序不会自动读取 .env。
PROMPT_HOOK_ENABLED 关闭或启用采集；PROMPT_REDACTION_ENABLED 控制常见密钥脱敏，
默认关闭，启用也不能保证覆盖所有敏感数据。
PROMPT_HISTORY_DB、PROMPT_HOOK_LOG、CALLSCOPE_PROJECT_DB 可自定义路径，
相对路径均从项目根目录解析。可选项目数据库不存在时按工作目录识别项目。

单个事件中会话写入、记录插入和计数更新在同一事务中提交，失败全部回滚。
日志只包含状态与记录标识，不含 Prompt 正文。真实数据不提交 Git。
# 新版工作台说明

新版后端启动后使用本地会话采集模式，同一数据库的 Hook 会跳过写入。普通用户请按根目录 [README](../README.md) 使用“采集设置”，无需安装 Hook 或寻找 `/hooks`。以下内容仅供维护旧 Hook 集成参考。
