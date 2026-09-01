# R2 Batch B fresh-context 独立纠偏复验 follow-up 03

你是新的独立验收者，不接收修复者私有推理。请仅依据实际工件、设计/计划、既有 VETO 报告、验收标准和可重放证据，对当前冻结快照做只读 ACCEPT/VETO。不得因为既有测试通过而默认接受。

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
- `runs/medical_monitoring_r2_batch_b_independent_followup_02_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_b_followup02_remediation_20260810.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`

Write exactly one output file: `runs/medical_monitoring_r2_batch_b_independent_followup_03_20260810.md`

## Hard boundaries

- 不得修改 `poc/medical_monitoring_ai_native_r2/` 或产品、医学写作、真实项目、R1、共享运行库。
- 除唯一 follow-up 03 报告外不得创建、修改、移动或删除文件。
- 不得启动服务、读取真实项目或让 8911 出现监听。
- 只验收 synthetic/offline Batch B；不得扩大为 Batch C、R2 总体、产品或生产验收。

先记录十项工件与 R2 全树 SHA，结束时复核。独立重放前三轮全部 P1/P2，重点挑战：

1. SAE/AESI exact/mixed-case/camel/全大写/全小写连接、snake/space/hyphen 完整英文术语、有无“的”的中文名称；检查显式英文/中文否定、复数、相似普通单词不过度匹配。每个结论必须经真实 RiskInstance 与后续 close gate 验证。
2. merge 同一 target set 的正逆序、不同 scope、不同 severity、不同 flags、不同 source snapshot；检查 merged scope、identity、severity、flags、lineage、supersede transition 顺序不依赖调用方列表顺序。
3. merge 缺失/额外/错配 payload、high downgrade；split high downgrade、mixed-case classifier、人工确认继承；全部失败路径必须原子。
4. 旧裁决重放、coverage 来源/顺序/阻断、locked selection、FieldChange/impact-domain 规范化及原 VETO 相邻攻击。

执行风险聚焦、Batch B、R2 全量、内存 compile、cache、8911 检查。无 P1/P2、全部攻击 fail closed、首尾 SHA 稳定时才给 `ACCEPT`；否则给 `VETO`，附可复现命令、实际输出、文件与行号。

报告须明确 in-memory AcceptanceService 与 local-user selection 仍只是 R2 POC 权威边界；持久化、跨进程身份与真实用户事件属于 Batch C/产品层未验证范围。
