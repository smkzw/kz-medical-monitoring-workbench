# R6 第四纵切执行合同（2026-08-28）

状态：`READY_FOR_GOVERNED_EXECUTION`

## 目标

在已接受的 R6 slice-01/02/03 上，实现 synthetic/offline 的三模式
`ModeContract`、不可变 mode output envelope、daily 四类输出和结构化 Query 草稿。
本纵切只处理 canonical JSON，不接真实项目、模型、文件解析、服务或前端。

## 权威来源

1. `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md` §8。
2. `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json`
   的 `ModeContract`、`ModeOutput`、`mode_contracts`、`output_contract`。
3. `context/medical_monitoring_r6_runtime_slice_03_acceptance_record_20260828.md`。
4. 用户已确认的 Query 文案合同：`依据`＋`发现`＋`行动项`；PD/禁用药等问题也生成
   Query 草稿，不在医学监查子系统中登记或关闭 PD。

## 三个独立工作项

1. **模式合同与 Run 门**：构建/验证 daily、pre_lock、post_lock_pre_cfdi 的不可变
   ModeContract；校验 execution basis、entry conditions、cutoff/source revision、显式
   carry-forward、固定总量和 silent mode conversion。
2. **输出与 Query 投影**：实现通用 ModeOutput identity/eligibility；先落 daily 的
   `change_summary`、`current_full_risk`、`affected_query_draft`、
   `data_knowledge_rule_model_change_note`。Query 每条必须结构化保留依据/发现/行动项，
   中文展示文本由三分句顺序确定生成；不得带 sent/closed/PD-recorded 等外部状态。
3. **独立验证**：模式阳性/阴性、跨模式/跨 cutoff/revision 混用、carry-forward、
   producer_kind、authority/coverage/QC、数字一致性、Query 三分句和禁用状态、tamper、
   normal/`-O`/`-OO` × 3 hash seeds、slice-01/02/03 相邻回归、医学写作边界与端口停止。

## 最小 API

- `build_mode_contract(mode) -> dict`
- `validate_mode_contract(mode_contract) -> tuple[str, ...]`
- `build_mode_output(run_binding, mode_contract, output_spec, *, authority_refs, coverage_refs, qc_refs) -> dict`
- `build_affected_query_draft(run_binding, findings) -> dict`
- `validate_mode_output(output, run_binding, mode_contract) -> tuple[str, ...]`

输出必须 canonical JSON 可序列化，输入不得原位修改。仅使用冻结 canonical code：
`mode_entry_blocked`、`silent_mode_conversion`、`output_not_eligible`、
`authority_mismatch` 及已接受相邻 identity/cutoff/revision code。

## Query 草稿最小结构

每条 Query draft 必须包含：

- `query_draft_id`、`finding_id`、`risk_id`、`project_id`、`run_id`、受试者/中心 scope；
- `basis`（依据）、`finding`（发现）、`action`（行动项）；
- `display_text = basis + finding + action` 的确定性中文三分句投影；
- evidence/locator、cutoff/source revision、issue/risk identity；
- `draft_state=draft`、`is_sent=false`、`is_closed=false`、`is_user_confirmed=false`。

依据、发现或行动项任一缺失、证据/定位不可核对、身份/cutoff 漂移均阻断输出。

## 允许路径

允许修改：

- `poc/medical_monitoring_ai_native_r6/src/mm_r6/__init__.py`
- `poc/medical_monitoring_ai_native_r6/README.md`
- `poc/medical_monitoring_ai_native_r6/tests/test_report_bundle.py`（仅 slice-04 allowlist）

允许创建：

- `poc/medical_monitoring_ai_native_r6/src/mm_r6/mode_output.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_mode_output.py`
- `poc/medical_monitoring_ai_native_r6/evidence/r6_mode_output_runtime_receipt.json`

以及本 task 的 context/plan/prompt/run/log/metrics/review/archive 文件。其他已接受
slice-01/02/03 源码、测试、receipt 只读。

## 禁止边界

- 不修改 frontend/services/packages/runtime/deploy、R1-R5 或医学写作。
- 不读取/运行真实项目；不启动 8911/5174、浏览器、OCR、模型/provider。
- 不实现 Agent Harness；其默认 MTPLX 与 DeepSeek V4 Flash 双路约束留给独立 adapter 合同。
- 不发送 Query、不跟踪外部回复、不登记/关闭 PD、不创建待办或用户确认。
- 不生成 DOCX/PDF/HTML，不声称产品/医学/真实项目接受。
- 不引入第三方依赖、数据库、服务或抽象框架。

## 完成门

- 三模式合同字节稳定，Run/mode/basis/cutoff/revision/carry-forward 不可静默漂移；
- daily 四输出均绑定同一 authority/coverage/QC 和版本身份；
- Query 草稿三分句完整、中文顺序稳定、PD 类发现可进入草稿但无登记/关闭语义；
- external_report_review 与 system_monitoring_output 不混淆；
- 不满足 entry/analysis/evidence/coverage/QC/issue policy 时输出失败关闭；
- focused、全 POC、normal/`-O`/`-OO` × 3 hash seeds 通过；医学写作 aggregate
  不变；8911/5174 停止；独立 verifier 与 Codex 接受。
