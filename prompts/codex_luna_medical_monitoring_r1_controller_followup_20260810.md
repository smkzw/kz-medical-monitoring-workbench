继续你在同一会话 `019fe746-ded2-7b83-9636-ff75466cacd2` 中对 R1 capability/work-unit controller 的独立只读审阅。你上一轮给出 VETO：P2 为 Store 终态接口可绕过 `persist_capability_attempt`，P3 为已 claim attempt 可绕过 controller assignment 直接绑定。作者已只修复这两项；请勿修改任何文件。

工作区：当前工作区 `.`

Read these files only:

- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/controller.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_authoritative_progress.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_controller.py`
- `context/medical_monitoring_r1_controller_binding_20260809_context.md`

Write exactly one output file: `runs/codex_medical_monitoring_r1_controller_binding_20260809_followup.md`

Hard boundaries:

- 只读审阅输入文件；不得修改产品源码、测试、context、设计或计划。
- 唯一允许的输出是上述 review 文件，由 CLI `-o` 写入；不得通过工具写其他文件。
- 不启动服务、8911、浏览器、真实模型或 endpoint，不读取真实项目或医学写作子系统。
- 只运行 synthetic/offline、无缓存的只读检查；不得安装依赖。

本次修复合同：

1. Store 在绑定 AI 工作项时必须重新验证版本 1 的不可变 `capability_work_assignment`、其完整 request/identity、审计证据及目标 work unit；无分配即失败关闭。
2. Store 在 terminal attempt 推进工作项前，不信任调用方的 evidence_count，而是逐项验证 `persist_capability_attempt` 应产生的 raw output、adapter binding/run/analysis、execution profile、attempt request、全部 work events，以及存在时的 candidate artifact；缺任一项即不能 passed/failed。
3. interrupted attempt 仍可闭合为 blocked，证据数必须为 0；retry/continued_from、并发 assignment、claim 门保持不变。
4. AI 输出仍 candidate-only，不形成 canonical facts；不启动服务、8911、浏览器、真实模型或真实项目。

主会场刚完成的决定性检查：

- 四个关键测试文件：`170 passed in 4.12s`
- R1 全量：`273 passed in 4.95s`
- scoped Ruff：`All checks passed!`
- compileall：exit 0
- `lsof -nP -iTCP:8911 -sTCP:LISTEN`：exit 1、无输出，即无监听

请优先亲自复现你上轮两个绕过路径，并检查新逻辑是否会误伤 terminal replay、partial/failed 后 resume、candidate-only artifact、并发 assignment 或 authoritative progress 审计投影。若临时目录仍受限，可使用工作区内只读/不生成缓存的检查；不要因为环境限制重复报告已由主会场锚定的完整回归为产品缺陷。

输出必须以 `VERDICT: ACCEPT` 或 `VERDICT: VETO` 开头。VETO 只列仍真实存在的 P0-P4、精确定位和复现；ACCEPT 列出亲自验证的修复点、命令/输出、未验证范围和残余风险。不得提前接受，不得修改文件。
