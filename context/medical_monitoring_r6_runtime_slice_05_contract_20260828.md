# R6 第五纵切执行合同（2026-08-28）

状态：`READY_FOR_GOVERNED_EXECUTION`

## 目标

在已接受的 slice-01 至 slice-04 上，实现 synthetic/offline 的锁库前模式专属输出内容：
`full_risk`、`revision_impact`、`check_package`、`query_revision_package`。
四类输出必须绑定同一 pre_lock Run、cutoff/source revision、authority/coverage/QC，
不得伪造 Query 已发送/已关闭、PD 已登记/已关闭或用户已确认。

## 权威来源

1. `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §§6.4、14。
2. `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R6 步骤 10。
3. `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md` §8。
4. `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json`
   中 pre_lock mode contract、ModeOutput 与 numeric reconciliation policy。
5. `context/medical_monitoring_r6_runtime_slice_04_acceptance_record_20260828.md`。

## 三个串行工作项

1. **锁库前四输出构建/校验**：复用 `ModeOutput` envelope，增加
   `build_pre_lock_mode_outputs(...)` 与 payload validator；不新建第二套身份/资格框架。
2. **失败关闭测试**：覆盖四输出正向、同一 authority/cutoff/revision、revision source/target、
   checklist coverage、Query revision draft-only、数字/风险一致、tamper、跨 mode 混用。
3. **独立验证与 receipt**：focused、全 POC、normal/`-O`/`-OO` × 3 hash seeds、
   slice-01 至 04 邻接、医学写作 aggregate 与 8911/5174 停止。

## 内容下限

### `full_risk`

- `risks` 可为空；定量风险必须使用 slice-04 的 `metric_id` → numeric raw 对账。
- 绑定 `population_scope`、`data_cutoff`、`source_revision_id` 和 authority digest。
- 不创建处置状态、用户确认或医学终结状态。

### `revision_impact`

- 明确 `from_source_revision_id`、`to_source_revision_id`、`revision_reason`。
- 每个 impact 项必须有稳定 `impact_id`、`impact_kind`、受影响 scope、evidence refs。
- `to_source_revision_id` 必须等于当前 Run；from/to 不得相同；不得把知识/规则变化冒充临床数据变化。

### `check_package`

- 包含项目、中心、受试者三层 `check_items`；每项有 `check_id`、`level`、`check_kind`、
  `status`、evidence/locator。
- 本纵切只允许 `status=ready|blocked|not_applicable`；无覆盖或证据冲突必须 blocked，
  不允许伪造 completed/passed/user_confirmed。
- `coverage_summary` 必须与 check_items 确定性重算一致。

### `query_revision_package`

- 只聚合结构化 Query 草稿及其 `query_draft_id`、issue/risk/scope/evidence/cutoff/revision。
- 每条 revision entry 明确 `previous_query_draft_id`（可空表示新建）与
  `revision_kind=new|updated|unchanged|withdrawn_draft`。
- `withdrawn_draft` 只表示本地草稿退出当前包，不等于 Query 已关闭或外部撤回。
- 全包 `is_sent=false`、`is_closed=false`、`is_user_confirmed=false`、
  `pd_registration_allowed=false`、`external_dispatch_allowed=false`。

## 允许路径

允许修改：

- `poc/medical_monitoring_ai_native_r6/src/mm_r6/mode_output.py`
- `poc/medical_monitoring_ai_native_r6/src/mm_r6/__init__.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_mode_output.py`
- `poc/medical_monitoring_ai_native_r6/README.md`
- `poc/medical_monitoring_ai_native_r6/tests/test_challenge_matrix.py`（仅 receipt allowlist）
- `poc/medical_monitoring_ai_native_r6/tests/test_report_review.py`（仅 receipt allowlist）
- `poc/medical_monitoring_ai_native_r6/tests/test_report_bundle.py`（仅 receipt allowlist）

允许创建：

- `poc/medical_monitoring_ai_native_r6/evidence/r6_pre_lock_output_runtime_receipt.json`
- 本 task 的 context/plan/prompt/run/log/metrics/review/archive 文件。

## 禁止边界

- 不修改 frontend/services/packages/runtime/deploy、R1-R5 或医学写作。
- 不读取/运行真实项目；不启动 8911/5174、浏览器、OCR、模型/provider。
- 不实现 post_lock 深层输出、Agent Harness、真实文件 parser/renderer。
- 不发送 Query、不跟踪外部回复、不登记/关闭 PD、不创建待办或用户确认。
- 不生成 DOCX/PDF/HTML，不声称产品/医学/真实项目接受。
- 不引入第三方依赖、数据库、服务或新抽象层；复用 slice-04。

## 完成门

- pre_lock 四输出 payload 内容真实、身份一致、失败关闭且输入不变。
- revision impact、check coverage、Query revision lifecycle、数字风险对账有可重算验证。
- focused、full POC、9 宫格通过；医学写作 aggregate 不变；8911/5174 停止。
- execution audit、独立 conference、Codex review-gate 通过后才能接受。

## 明确非目标

本纵切不实现也不声称内置 Agent Harness。后续 adapter 默认目标仍为
`mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`，并必须保留、真实验证
`deepseek/DeepSeek V4 flash:max`；配置文本存在不等于接入成功。
