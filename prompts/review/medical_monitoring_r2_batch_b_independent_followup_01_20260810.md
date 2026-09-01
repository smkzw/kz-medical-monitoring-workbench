# R2 Batch B 独立纠偏复验

你是前次独立验收者。本轮是同一验收任务的 actionable-gap follow-up，只读复验全部原 VETO 及其相邻合同；不得因为修复者测试通过而默认接受。

Read these files only:
- `poc/medical_monitoring_ai_native_r2/README.md`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/__init__.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/baselines.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/modes.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/diff.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py`
- `poc/medical_monitoring_ai_native_r2/tests/test_r2_b_baselines.py`
- `poc/medical_monitoring_ai_native_r2/tests/test_r2_b_modes.py`
- `poc/medical_monitoring_ai_native_r2/tests/test_r2_b_diff.py`
- `poc/medical_monitoring_ai_native_r2/tests/test_r2_b_risk.py`
- `runs/medical_monitoring_r2_batch_b_independent_review_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_b_veto3_remediation_20260810.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`

Write exactly one output file: `runs/medical_monitoring_r2_batch_b_independent_followup_01_20260810.md`

## Hard boundaries

- 不得修改 `poc/medical_monitoring_ai_native_r2/` 或任何其他产品、医学写作、真实项目文件。
- 除唯一 follow-up 报告外不得创建、修改、移动或删除文件。
- 不得启动服务，不得接触真实项目，不得让 8911 出现监听。
- 不得覆盖或删除首次 VETO 报告。
- 结论只限 synthetic/offline Batch B，不扩大为 Batch C、R2 总体、产品或生产验收。

先记录十个冻结工件和 R2 全树 SHA，结束时复核。逐条重放首次报告的六类反例，并检查相邻绕过：裁决在任意中间状态后的重放、目标集合与版本排序、来源服务与后续 coverage 的同一性/顺序/阻断、SAE/AESI 大小写和 signal-type 继承、merge/split 多祖先确认与 flags、selection 直接构造/恶意子类/跨 manager/跨 snapshot/跨 project/旧布尔参数、FieldChange/impact-domain 顺序与内容敏感性。检查新字段是否进入相应 canonical hash，失败路径是否原子。

执行 Batch B、R2 全量、内存 compile、cache 与 8911 检查。无 P1/P2、原六类及相邻攻击均 fail closed、首尾 SHA 稳定时才给 `ACCEPT`；否则给 `VETO` 并提供可复现命令、输出、文件与行号。报告还须明确 in-memory AcceptanceService 对象绑定与 local-user selection 只是 R2 POC 权威边界，持久化/跨进程身份与用户事件将在 Batch C/产品层验证。
