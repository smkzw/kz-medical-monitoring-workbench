同一 worker_01 session 定向修复，只改 `deploy/medical_monitoring_local/manage.py` 和必要中文 README，不扩大范围。

Codex 发现：`stop --root <过宽目录>` 在没有合法 `runtime_config.json` 时仍会把该根目录下任意 listener 视为“本应用”，存在误终止相邻工作台进程的风险。请在任何终止动作前要求当前 root 的运行配置存在且 schema 为 `mm-monitoring-local-runtime-v1`；缺失/错误返回 2，不 kill。`status` 只读可继续显示未启动或未就绪，但不得扩大 owned 判断。

同时核对 8984：它是可检查的辅助入口，不应在未配置辅助进程时让主工作台永远无法达到“已启动”。以运行配置中的显式 `aux_enabled=true` 决定 8984 是否为 required owned port；无该字段时 required 为 8911+5174，但仍检查 8984 的 foreign ownership。保持 frozen contract 三端口检查语义。

补充最小自检并报告。不得启动服务、改测试文件、改医学写作或真实项目。

