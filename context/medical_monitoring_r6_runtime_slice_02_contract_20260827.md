# R6 第二纵切执行合同（2026-08-27）

状态：`READY_FOR_GOVERNED_EXECUTION`

## 目标

在第一纵切已接受的冻结合同/fixture/validator 基座上，实现外部报告审阅的最小
canonical object runtime：不可变报告来源修订、报告结构单元、claim/issue 多对多、
冻结 expected review surface、反向遗漏链接和 `ClaimCoverageLedger` 的“覆盖账闭合”/
“全报告已审阅资格”双门。只使用 synthetic/offline 数据，不解析真实文件。

## 权威来源

1. `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md` §§3–6。
2. `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json`。
3. `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/challenge_matrix.json`。
4. `context/medical_monitoring_r6_runtime_slice_01_acceptance_record_20260827.md` 及已接受 R6 POC。

## 三个独立工作项

1. 来源与对象：实现 report raw-byte SHA、同哈希去重、新内容/版本新 revision、parent
   lineage、Run source 与 report source 分离，以及 ReportUnit/Claim/Issue 的确定性构造。
2. 覆盖与反向遗漏：实现 expected unit set、claim-unit/issue-unit 多对多、父单元、
   expected review surface/reverse link 一一对应、全部 blocking reasons 的确定性汇总，
   并区分 `coverage_closed` 与 `full_report_reviewed_eligible`。
3. 独立验证：覆盖阳性、阴性、边界、tamper、重复/缺失/孤儿、not_evaluable reason、
   partial/truncated、anchor/cutoff/revision/comparison、反向遗漏空映射、跨项目/跨修订、
   normal/`-O`/`-OO`、多 hash seed、R1-R5/医学写作只读及端口停止。

## 最小 API 合同

- `register_report_source(raw_bytes, descriptor, existing_revisions=()) -> dict`
- `build_report_review_matrix(binding, report_source, units, claims, issues,
  expected_review_surface, reverse_coverage_links) -> dict`
- `build_claim_coverage_ledger(matrix) -> dict`
- `validate_report_review_matrix(matrix) -> tuple[str, ...]`

函数必须返回 canonical JSON 可序列化对象；输入不原位修改；错误 fail-closed；诊断使用
冻结 canonical failure code，不造同义 token。coverage validator 必须保留所有阻断原因，
不得 first-error-only。

## 允许路径

允许修改：

- `poc/medical_monitoring_ai_native_r6/src/mm_r6/__init__.py`
- `poc/medical_monitoring_ai_native_r6/README.md`

允许创建：

- `poc/medical_monitoring_ai_native_r6/src/mm_r6/report_review.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_report_review.py`
- `poc/medical_monitoring_ai_native_r6/evidence/r6_report_review_runtime_receipt.json`

以及本 task 的 `context/plan/prompt/run/log/metrics/review/archive` 过程文件。第一纵切
`contracts.py`、`fixtures.py`、`validator.py` 和既有 tests/receipt 保持只读。

## 禁止边界

- 不修改 frontend/services/packages/runtime/deploy、R1-R5 或医学写作。
- 不读取/运行真实项目或真实报告；不启动 8911/5174、浏览器、OCR、模型/provider。
- 不实现 DOCX/PDF/HTML parser/renderer、批注副本、清洁稿、三模式导出或产品页面。
- 不把外部 claim/issue 提升为 canonical fact/risk，不建立 Query 回复/PD 关闭/待办。
- 不引入第三方依赖、数据库、服务、插件或可扩展框架。

## 完成门

- 同 raw hash 幂等去重；新内容/修订产生新 identity 且 parent 可重建；Run 与 report
  source identity 不混用。
- unit expected set 非空且一一对应；claim-unit/issue-unit 多对多、父单元、locator、
  反向遗漏映射和跨引用闭合。
- `coverage_closed=true` 允许 reasoned `not_evaluable`，但
  `full_report_reviewed_eligible=false`；partial/truncated/missing/duplicate/orphan/
  unverified anchor/cutoff/revision/comparison/reverse omission 全部阻断完整审阅。
- 全部 blocking reasons 稳定、去重、顺序确定；输入/输出 canonical bytes 双遍一致。
- 新测试、R6 第一纵切相邻回归、normal/`-O`/`-OO` × ≥3 hash seed 全通过。
- 医学写作 542 文件聚合 SHA 不变；R1-R5 冻结输入不变；8911/5174 停止；独立 verifier 接受。
