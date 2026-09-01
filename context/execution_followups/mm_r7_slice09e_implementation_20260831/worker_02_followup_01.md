同一 worker_02 session 定向修复，只改 `deploy/medical_monitoring_local/distribution.py`，不扩大范围。

Codex 已复现：两个不同绝对安装根、只要目录末级同名，就会得到相同 `root_identity_digest` 与 `plan_sha256`。请修复为摘要绑定规范化绝对 distribution/data roots，但输出 JSON 仍不得暴露绝对路径。

另有真实并发竞态：当前 prepare-upgrade 在创建 `in_progress.json` 后释放 09A gate 再执行备份；第二调用可获取 gate，并把第一调用仍活跃的 staging 当“陈旧”删除。请保持 09A `ProjectBackupManager.backup` 为备份唯一语义，同时用最小 stdlib 机制让整个 prepare-upgrade 单写者成立：活跃同项目第二调用稳定返回 5，不删除第一调用 staging；崩溃遗留可安全回收；不要复制备份/迁移实现。建议原子 staging marker 带当前 PID，活进程=busy，死进程=回收，再让 09A gate/backup继续负责项目数据互斥。

补充最小自检，报告精确变更、竞态复现与修复证据。不得改测试文件、医学写作、真实项目或启动端口。

