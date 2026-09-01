# R2 Batch B 同会话独立纠偏复验 follow-up 04

继续你刚完成 follow-up 03 的同一 Luna 独立复核会话。你仍是验收者，不接收修复者私有推理；只依据实际工件、既有 VETO、纠偏说明、验收标准与可重放证据给出 ACCEPT/VETO。不得因测试绿灯默认接受。

Read these files only:

- `poc/medical_monitoring_ai_native_r2/README.md`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py`
- `poc/medical_monitoring_ai_native_r2/tests/test_r2_b_risk.py`
- `runs/medical_monitoring_r2_batch_b_independent_followup_03_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_b_followup03_remediation_20260810.md`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/baselines.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/modes.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/diff.py`
- `poc/medical_monitoring_ai_native_r2/tests/test_r2_b_baselines.py`
- `poc/medical_monitoring_ai_native_r2/tests/test_r2_b_modes.py`
- `poc/medical_monitoring_ai_native_r2/tests/test_r2_b_diff.py`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`

Write exactly one output file: `runs/medical_monitoring_r2_batch_b_independent_followup_04_20260810.md`

## Hard boundaries

- 不得修改 R2 POC、产品、医学写作、真实项目、R1 或共享运行库；不得创建上述唯一报告以外的文件。
- 不得启动服务、读取真实项目或让 8911 出现监听。
- 只验收 synthetic/offline Batch B；不得外推为 Batch C、R2 总体、产品或生产验收。
- 开始记录 `risk.py`、风险测试与 R2 全树 SHA，结束时复核稳定性。

## 必须独立重放

1. follow-up 03 的四个直接失败例，以及相邻的“没有发生、未有、不含、不包含、无任何、术语不存在”和 SAE/AESI 对应变体，必须保持无临床高风险标记，并经真实 `RiskInstance`、后续 coverage、裁决和 close gate 完成合法低风险关闭。
2. 反向攻击“未报告严重不良事件、没有排除严重不良事件、未排除特别关注不良事件、疑似特别关注不良事件”必须仍形成 SAE/AESI 标记，并被真实机器关闭门拒绝。自行增加至少一组同句混合否定与阳性术语，证明任一未否定术语不会被前一个否定短语掩盖。
3. 检查否定匹配仅限明确语法边界，不得以一般性的 `未`、`没有` 子串吞掉漏报、未排除或其他风险语义；若发现相邻 P1/P2，给出真实复现。
4. 重跑风险聚焦、全部 Batch B 与 R2 全量测试，执行内存 compile、cache 与 8911 检查；确认 follow-up 03 已通过的 merge/split、原子性、历史攻击没有因本轮两文件修改发生回退。

只有直接及相邻攻击全部符合、无新增 P1/P2、全量门通过且首尾 SHA 稳定时才给 `ACCEPT`；否则给 `VETO`。报告必须列出命令、实际输出、文件/行号、无问题范围与残余边界，并明确持久化、跨进程身份与真实用户事件仍属于 Batch C/产品层未验证范围。
