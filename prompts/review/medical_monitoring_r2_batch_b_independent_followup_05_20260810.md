# R2 Batch B 同会话最终定向复验 follow-up 05

继续同一 Luna 独立验收会话，对 follow-up 04 唯一 P1 的修复做第二次且最终的同会话恢复复验。你仍只按实际工件、验收标准和真实对象链给 ACCEPT/VETO，不接收修复者私有推理。

Read these files only:

- `poc/medical_monitoring_ai_native_r2/README.md`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py`
- `poc/medical_monitoring_ai_native_r2/tests/test_r2_b_risk.py`
- `runs/medical_monitoring_r2_batch_b_independent_followup_04_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_b_followup04_remediation_20260810.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`

Write exactly one output file: `runs/medical_monitoring_r2_batch_b_independent_followup_05_20260810.md`

## Hard boundaries

- 不得修改 R2 POC、产品、医学写作、真实项目、R1 或共享运行库；不得写上述唯一报告以外的文件。
- 不得启动服务、读取真实项目或让 8911 出现监听。
- 只复验 synthetic/offline Batch B 的中文 SAE/AESI 语义根因及既有回归，不扩展到系统安全设计/测试、Batch C、R2 总体、产品或生产。
- 开始记录 `risk.py`、风险测试与 R2 全树 SHA，结束时复核。

## 必须独立重放

1. follow-up 04 的七个失败例，以及“并非没有、不一定没有、不能确认术语不存在、未能确认没有、难以确认没有”等同根不确定/双重否定变体，必须形成 SAE/AESI 标记并被真实机器关闭门拒绝。
2. 明确缺如表达必须仍可合法关闭，至少覆盖句首直接否定、目前没有发生、截至目前尚未发生任何、该受试者无任何、经核查术语不存在及 SAE/AESI 两类。
3. 至少重放一组“一个明确缺如 + 另一个疑似/未排除”的混合句，确认未否定风险不被掩盖。
4. 使用真实 `RiskInstance → coverage → adjudication → close`，不得只测私有 helper 或 classifier 返回值。重跑风险聚焦、全部 Batch B、R2 全量、内存 compile、cache 与 8911；确认历史回归未缩减。

只在上述直接/同根边界全部符合、无 P1/P2、全量门通过且首尾 SHA 稳定时给 `ACCEPT`；否则给 `VETO` 并附最小真实复现。报告须明确此次结论仅针对 Batch B，持久化、跨进程身份与真实用户事件仍未验证；不要扩展新的系统安全审阅范围。
