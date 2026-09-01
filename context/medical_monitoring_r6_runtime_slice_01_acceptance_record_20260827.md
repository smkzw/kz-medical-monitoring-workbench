# R6 synthetic/offline runtime 第一纵切验收记录（2026-08-27）

状态：`ACCEPT_R6_RUNTIME_SLICE_01_SYNTHETIC_OFFLINE`

## 接受范围

本记录接受 R6 v0.1 合同的第一条机器可执行纵切：冻结 prose/machine contract/
challenge matrix 的只读校验、86 个确定性 synthetic fixture、11 个 validator 注册、
10 个内容 validator 全量调度、单次 RFC 6902 replace、metadata-oracle 对账、优化模式/
哈希种子复现和只读 evidence receipt。

不接受也未运行：报告解析、真实外部报告、真实项目、OCR/模型/provider、产品/API/
前端、DOCX/PDF/HTML 格式渲染、医学结论或 R6 阶段总体。

## Codex 纠偏

初版执行器把 `challenge_matrix_binding.category_validator_map` 当作验证器过滤器，
但冻结合同明确 `category_validator_map_normative=false`。这会让场景 category 抑制
跨类诊断。Codex 改为每行运行全部 10 个内容 validator，boundary validator 继续由
governed audit 验收；同时把 canonical publication `analysis_state` 保持为 `running`，
只在文档状态真实成为 `complete + partial + evidence complete` 时产生
`REPORT_PARTIAL_OUTPUT`，不再依赖 category。

独立 verifier 同一有效 Cursor session 首轮补充复核发现残余 category gate（P2）；
第二轮确认关闭并返回
`ACCEPT_R6_SLICE_01_AFTER_NON_NORMATIVE_DISPATCH_FIX`，无剩余 P0-P4。由于 guard
要求续轮 effective route 等于初始 Pi route，而初始 Pi 因内存门自动落到 Cursor，
补充复核的原始 prompt/run/log 已不改写地归档至
`records/supplemental_reviews/mm_r6_runtime_slice_01_20260827/`；不伪造路由或日志。
主三工项执行包自身 `audit-execution` 和 review-gate 均通过。

## 决定性证据

- pytest：`243 passed`。
- metadata oracle：`86/86`，每行 `mutations_applied=1`。
- 正向行：18 行无 blocking finding。
- category 抑制门：68 个错误行 × 12 个 category = `816/816` 均保留预期诊断。
- raise-based：normal/`-O`/`-OO` × `PYTHONHASHSEED=0/1/42`，`9/9` 通过。
- 诊断/验证器/禁止边界：49/49、11、16；boundary 由 execution audit 通过。
- frozen input SHA：contract `0fca738c...0ed1d7`，matrix `cb5b30bc...44b2dc`，
  prose `1c6fc588...f2f1acd`，均未改变。
- fixture catalog/template SHA：`76b43076...940b53` / `84747420...7daf0e`。
- 医学写作保护面：542 文件，aggregate
  `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- R6 POC 精确 10 个 allowlist 文件；8911/5174 无监听。
- receipt：`poc/medical_monitoring_ai_native_r6/evidence/r6_contract_runtime_receipt.json`。

## 最终源码 SHA-256

```text
f5ce93629bd008d438095fd9b23ab1f335b951087bf916b85ac990a350e8fcfa  contracts.py
e8064ad358e0a215d6b428bc1c48e97a4ef55a20131261e5b6a9c21eac44e56c  fixtures.py
8c9bb8c60c64c1a102d37f5e4e49263844061fd5b37cce01060bbd4133d891d0  validator.py
7aca01900e608e3dc367eccc7ad323dc3268f5938095fed5e1234524204dcf07  test_contracts.py
48f1a0024773ef7dacfc44d4558ff6d2950137792ad66f8176954a993768f689  test_validator.py
f93a4dcdff14f0906e552a93513fc93c8a59c047da75f961f39ccc4d53dc2cb9  test_challenge_matrix.py
```

## 下一安全动作

进入 R6 第二纵切前先冻结 create-only 合同，范围只包括
`ReportSourceRevision`、`ReportUnit`、`ReportClaim/ReviewIssue` 多对多关系和
`ClaimCoverageLedger` runtime；继续使用 synthetic/offline 数据，保持产品、真实报告/
项目、医学写作、8911/5174 停止。第二纵切不得提前接 DOCX/PDF/HTML 或产品页面。
