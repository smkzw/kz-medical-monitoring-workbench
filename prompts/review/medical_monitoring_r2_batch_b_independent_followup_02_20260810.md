# R2 Batch B 独立纠偏复验 follow-up 02

你是前两轮独立验收者。本轮是同一验收任务第二次 actionable-gap follow-up。保持 fresh verifier judgment，只读复验 follow-up 01 新发现的两个 P1、原六类 VETO 及相邻攻击；不得因为修复者测试通过而默认接受。

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
- `runs/medical_monitoring_r2_batch_b_independent_followup_01_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_b_veto3_remediation_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_b_followup01_remediation_20260810.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`

Write exactly one output file: `runs/medical_monitoring_r2_batch_b_independent_followup_02_20260810.md`

## Hard boundaries

- 不得修改 `poc/medical_monitoring_ai_native_r2/` 或任何其他产品、医学写作、真实项目文件。
- 除唯一 follow-up 02 报告外不得创建、修改、移动或删除文件。
- 不得启动服务，不得接触真实项目，不得让 8911 出现监听。
- 不得覆盖或删除既有 VETO/ACCEPT/修复报告。
- 结论只限 synthetic/offline Batch B，不扩大为 Batch C、R2 总体、产品或生产验收。

先记录十个冻结工件和 R2 全树 SHA，结束时复核。至少独立重放：

1. high+medium merge 显式 low、无 severity、不同 risk 输入顺序、payload severity/classifier 错配、额外 payload 字段、缺失 payload；确认不能丢失最高风险谱系且失败原子。
2. high split 显式 low、混合 high/low children、缺失 severity、新 classifier 引入 SAE/AESI；确认不能降级且失败原子，后续机器关闭 fail closed。
3. SAE/AESI 的 exact、camel-case、snake-case、空格/连字符完整英文术语、常用中文名称、大小写组合；同时用无关相近词检查不过度匹配。
4. 首次报告的旧裁决重放、coverage 来源/顺序/阻断、merge/split 人工确认、locked selection、FieldChange/impact-domain 规范化与失败原子性。

检查新 merge payload 是否进入裁决 canonical hash，merge/split 的 severity/flags 是否进入真实 RiskInstance 与后续 close gate，而非仅测试辅助逻辑。执行 Batch B、R2 全量、内存 compile、cache 与 8911 检查。无 P1/P2、全部攻击均 fail closed、首尾 SHA 稳定时才给 `ACCEPT`；否则给 `VETO` 并提供可复现命令、输出、文件与行号。

报告须继续明确：in-memory AcceptanceService 对象绑定与 local-user selection 只是 R2 POC 权威边界；持久化、跨进程身份与真实用户事件仍属于 Batch C/产品层未验证边界。
