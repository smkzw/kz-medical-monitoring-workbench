# R6 第三纵切执行合同（2026-08-27）

状态：`ACCEPT_R6_RUNTIME_SLICE_03_SYNTHETIC_OFFLINE`（见
`context/medical_monitoring_r6_runtime_slice_03_acceptance_record_20260828.md`）

## 目标

在已接受的 slice-02 报告矩阵/覆盖账基座上，实现 synthetic/offline 的
ReportReviewBundle 共享身份封装、旁注 annotation map/锚点质量门、可选
DRAFT 清洁稿 provenance，以及跨报告修订的 IssueTransition/diff。本纵切仅生成
canonical JSON 对象，不解析或渲染 DOCX/PDF/HTML。

## 权威来源

1. `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md` §7。
2. `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json`
   的 `IssueTransition`、`ReportReviewBundle`、`three_piece_bundle` 与 R6-C-BUNDLE-001。
3. `context/medical_monitoring_r6_runtime_slice_02_acceptance_record_20260827.md` 及已接受 POC。

## 三个独立工作项

1. **Bundle/批注投影**：实现共享 identity envelope、issue/evidence/locator 一致性、
   `annotation_mode=sidecar|in_place_copy`、原始字节 hash 保持、matrix/anchor map hash 和
   verified anchor 门。无法确定性证明无损原位批注时必须 sidecar。
2. **清洁稿/修订 diff**：实现可选 `report_clean_draft`，强制可见 `DRAFT`、
   `is_final=false`、`is_user_confirmed=false`、before/after 与 issue 引用；实现
   IssueTransition 的 reclassified/merge/split 和 new/unchanged/unresolved/partially_resolved/
   resolved/reopened/superseded/not_evaluable diff，不静默删除旧 issue。
3. **独立验证**：阳性、阴性、tamper、锚点、三件 identity 混用、未决冲突/
   not_evaluable 保留、原件不覆盖、normal/`-O`/`-OO` × 3 hash seeds、
   slice-01/02 相邻回归、医学写作边界和端口停止。

## 最小 API

- `build_annotated_projection(matrix, report_source, annotations, *, lossless_in_place_proven) -> dict`
- `build_clean_draft(matrix, report_source, modifications, *, requested) -> dict | None`
- `build_issue_transition(spec, from_issues, to_issues) -> dict`
- `build_revision_diff(previous_matrix, current_matrix, transitions=()) -> list[dict]`
- `build_report_review_bundle(matrix, annotated_projection, clean_draft=None) -> dict`
- `validate_report_review_bundle(bundle, matrix, annotated_projection, clean_draft=None) -> tuple[str, ...]`

所有输入不原位修改；输出 canonical JSON 可序列化；诊断保留全部原因，使用
`bundle_identity_mismatch`、`annotation_anchor_invalid` 及已冻结的相邻 canonical code，
不造同义 token。

## 允许路径

允许修改：

- `poc/medical_monitoring_ai_native_r6/src/mm_r6/__init__.py`
- `poc/medical_monitoring_ai_native_r6/README.md`
- `poc/medical_monitoring_ai_native_r6/tests/test_challenge_matrix.py`（仅 allowlist 添加本纵切三文件）

允许创建：

- `poc/medical_monitoring_ai_native_r6/src/mm_r6/report_bundle.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_report_bundle.py`
- `poc/medical_monitoring_ai_native_r6/evidence/r6_report_bundle_runtime_receipt.json`

以及本 task 的 context/plan/prompt/run/log/metrics/review/archive 过程文件。slice-01/02 其他
源码、测试与 receipt 保持只读。

## 禁止边界

- 不修改 frontend/services/packages/runtime/deploy、R1-R5 或医学写作。
- 不读取/运行真实项目或报告；不启动 8911/5174、浏览器、OCR、模型/provider。
- 不生成真实 DOCX/PDF/HTML，不覆盖原件，不声称原位批注已实现。
- 不把外部 claim/issue 提升为医学事实/风险/用户确认；不建 Query 发送、
  PD 关闭或待办。
- 不引入第三方依赖、数据库、服务或抽象框架。

## 完成门

- bundle 的 18 个 shared identity field 与 matrix/source 一致；三件共用 issue set/
  evidence/locator，不独立发明或删除 issue。
- 原始 source hash 保留；未证明无损原位时自动且明确使用 sidecar；所有 annotation
  绑定 issue/matrix/source revision/已验证 locator。
- 清洁稿仅在 requested 时生成，可见 DRAFT，不是 final/user-confirmed，每个修改关联
  issue，未决冲突/不可评价/cutoff 缺口不被删除。
- issue transition 保留全部 source/target ID 及 evidence；身份/cutoff/revision 不可比时为
  `not_evaluable`，不得伪装 `resolved`。
- `bundle_state=qc_passed` 仅当 matrix coverage/output 门、共享 identity、锚点和投影完整性
  均通过；否则 `qc_blocked`并保留所有阻断。
- 新测试、slice-01/02 相邻回归、normal/`-O`/`-OO` × 3 hash seeds 全通过；
  医学写作 542 文件聚合 SHA 不变；8911/5174 停止；独立 verifier 接受。
