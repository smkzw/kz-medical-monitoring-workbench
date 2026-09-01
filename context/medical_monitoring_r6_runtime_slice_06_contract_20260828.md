# R6 第六纵切执行合同（2026-08-28）

状态：`READY_FOR_GOVERNED_EXECUTION`

## 目标

在已接受的 slice-01 至 slice-05 上，实现 synthetic/offline 的锁库后—CFDI 核查前
固定总量专属输出：`full_project_report`、`site_materials`、`subject_materials`、
`checklist`。四类输出必须绑定同一 `post_lock_pre_cfdi` Run、锁定 snapshot、
cutoff/source revision、authority/coverage/QC，并可相互确定性对账；旧草稿或导出物不可覆盖。

## 权威来源

1. `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §§6.4、14。
2. `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R6 步骤 11。
3. `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md` §8.4-8.5。
4. `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json`
   中 `post_lock_pre_cfdi`、ModeOutput 和固定版本规则。
5. `context/medical_monitoring_r6_runtime_slice_05_acceptance_record_20260828.md`。

## 三个串行工作项

1. **四输出构建/校验**：复用 `ModeOutput`、Run gate、authority 和 slice-05 的
   canonical/失败关闭工具；不得新建第二套身份框架。
2. **固定总量与跨输出对账测试**：覆盖锁定版本身份、项目/中心/受试者数量、风险引用、
   Profile/Timeline 入口、checklist 层级和状态、旧 artifact 不覆盖、tamper 与跨 mode 混用。
3. **独立验证与 receipt**：focused、全 POC、normal/`-O`/`-OO` × 3 hash seeds、
   slice-01 至 05 邻接、医学写作 aggregate 与 8911/5174 停止。

## 共同固定版本身份

每个 payload 必须显式包含并与 Run/authority 完全一致：

- `output_kind`、`project_id`、`run_id`、`data_cutoff`、`source_revision_id`；
- `authority_digest`、`locked_snapshot_hash`、`acceptance_evidence_hash`；
- `fixed_total=true`；
- `population_totals`：至少包含 `site_count`、`subject_count`、`risk_count`，均为非负整数，
  且不可把 `bool` 当整数；四输出必须完全一致。

任一锁定身份、固定总量、引用或计数缺失/漂移都失败关闭。输入对象不可被修改；输出和
条目顺序必须 canonical、跨 hash seed/optimizer 稳定。

## 内容下限

### `full_project_report`

- `report_id` 由 canonical 内容生成；`report_version` 必须显式且非空。
- 包含 `project_summary`、`risk_summary`、`site_material_ids`、`subject_material_ids`、
  `checklist_id`、`evidence_refs`。
- `risk_summary` 至少有中/高/低风险计数及 `risk_ids`，总数与 `population_totals.risk_count`
  一致；风险 ID 去重。
- 仅为系统自产固定版本草稿：`is_user_confirmed=false`、`is_signed=false`、
  `is_sent=false`、`external_dispatch_allowed=false`；不得冒充外部报告审阅 bundle。

### `site_materials`

- `materials` 可为空；每项有稳定 `site_material_id`、`site_id`、`subject_ids`、
  `risk_ids`、`evidence_refs`、可核查 `locator`。
- site/material/subject/risk 身份不可重复；`material_count` 和唯一 site 数必须与
  `population_totals.site_count` 一致。
- 所有 subject/risk 引用必须能在同批 `subject_materials`/全量风险集合中对账。

### `subject_materials`

- `materials` 可为空；每项有稳定 `subject_material_id`、`subject_id`、`site_id`、
  `profile_ref`、`timeline_ref`、`risk_ids`、`evidence_refs`、可核查 `locator`。
- `profile_ref`/`timeline_ref` 只是既有完整 Profile/Timeline 的入口，不在本纵切复制内容。
- subject/material 身份不可重复；`material_count` 与
  `population_totals.subject_count` 一致；site 必须存在于同批 `site_materials`。

### `checklist`

- `checklist_id` 稳定；包含项目、中心、受试者三层 `check_items`，每项有稳定
  `check_id`、`level`、`check_kind`、`scope_id`、`status`、`risk_ids`、
  `evidence_refs`、可核查 `locator`。
- 仅允许 `status=ready|blocked|not_applicable`；缺覆盖或证据冲突必须 `blocked`；
  不允许 `completed/passed/user_confirmed/done/closed/sent`。
- `coverage_summary` 和 `item_count` 必须由条目确定性重算；site/subject scope 必须能在
  同批材料中对账。

## 跨输出确定性门

- `full_project_report.site_material_ids` 精确等于 `site_materials` 全部 ID；
- `full_project_report.subject_material_ids` 精确等于 `subject_materials` 全部 ID；
- `full_project_report.checklist_id` 精确等于 `checklist.checklist_id`；
- 四输出 `population_totals`、锁定身份、authority digest 完全一致；
- site→subject 引用、subject→site 归属、风险 ID 集合和项目风险计数闭合；
- 旧 `output_id`、`report_id`、material/check ID 不得由 caller 复用到不同 canonical 内容；
- supplied payload 即使重算外层 `output_id`，嵌套 tamper 仍须失败关闭。

## 允许路径

允许修改：

- `poc/medical_monitoring_ai_native_r6/src/mm_r6/mode_output.py`
- `poc/medical_monitoring_ai_native_r6/src/mm_r6/__init__.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_mode_output.py`
- `poc/medical_monitoring_ai_native_r6/README.md`
- 既有 receipt allowlist 测试（仅增加 slice-06 receipt allowlist）。

允许创建：

- `poc/medical_monitoring_ai_native_r6/evidence/r6_post_lock_output_runtime_receipt.json`
- 本 task 的 context/plan/prompt/run/log/metrics/review/archive 文件。

## 禁止边界

- 不修改 frontend/services/packages/runtime/deploy、R1-R5 或医学写作。
- 不读取/运行真实项目；不启动 8911/5174、浏览器、OCR、模型/provider。
- 不实现 Agent Harness、真实文件 parser/renderer、DOCX/PDF/HTML。
- 不发送 Query、不跟踪回复、不登记/关闭 PD、不签署/外发、不创建待办或用户确认。
- 不改写旧 artifact；本纵切只验证 append-only 身份与拒绝覆盖元数据。
- 不引入第三方依赖、数据库、服务或新抽象层；复用现有 `mode_output.py`。
- 不声称产品、医学、真实项目、报告格式或 R6 总体接受。

## 完成门

- 四输出内容、固定版本身份、总量和交叉引用可重算且失败关闭。
- focused、全 POC、9 宫格通过；slice-01 至 05 邻接通过；医学写作 aggregate 不变；
  8911/5174 停止。
- execution audit、独立 conference、Codex review-gate 通过后才能接受。

## 明确非目标

本纵切不实现内置 Agent Harness。后续 adapter 默认仍为
`mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`，并保留和真实验证
`deepseek/DeepSeek V4 flash:max`；配置文本存在不等于接入成功。
