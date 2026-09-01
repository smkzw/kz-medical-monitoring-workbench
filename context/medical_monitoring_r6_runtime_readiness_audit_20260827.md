# R6 synthetic/offline runtime 实施前审计（2026-08-27）

状态：`READY_AFTER_R5_S7_HY3_GATE`

## 目标与当前门

本记录把已经接受的 R6 v0.1 合同转换为下一条可执行纵切的最小实施清单，不创建
runtime，不启动服务，不读取真实报告或真实项目。R5-S7 的 Codex 26 行浏览器、身份、
网络和性能测量已经闭合；唯一前置门是 HY3 原 session
`1d2324eb-0ec4-4466-a8e4-73c47aed9378` 在 2026-08-27 21:31:55 CST 后完成最终重放。

## 当前文件系统事实

- `poc/medical_monitoring_ai_native_r6/` 当前不存在；没有未报告 R6 runtime 局部实现。
- R1 `report_review.py` 只支持每个 unit 零或一个 claim，不能直接作为 R6 canonical
  多对多 claim/unit runtime；可复用其 fail-closed coverage 思路，不复用该限制。
- R1/R2 `modes.py` 已有三模式与新 Run/显式 carry-forward 基础，但 R6 必须增加
  output-kind、report revision、coverage/QC、固定 cutoff 和跨输出 authority 一致性门。
- R6 v0.1 合同：3 modes、3 pieces、9 report-unit types、8 claim statuses、5 coverage
  statuses、16 output kinds、11 validators、16 prohibitions。
- 挑战矩阵：86 个唯一单变异行，12 个类别，49 个场景诊断码；阶段仍为
  `metadata_only_pre_runtime`。
- 医学写作保护面：542 files，aggregate SHA-256
  `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- 8911、5174 无监听。
- 阶段性清理：11 个 R1/R2 `__pycache__` 目录（合计 5,724 KiB）已移入 macOS
  废纸篓，可恢复；复核后两个 POC 树内剩余 `__pycache__` 目录为 0。未删除源码、
  测试、合同、证据、运行记录或医学写作文件。

## 第一纵切的最小实现范围

R5-S7 总关闭后，只实现“机器合同可执行化”，不提前实现报告解析、DOCX/PDF/HTML、
产品页面或真实模型：

1. 只读加载已接受 `contract.json` 与 `challenge_matrix.json`，核对 raw SHA、合同身份、
   枚举、计数、validator/error map 和 86 行唯一性。
2. 生成 deterministic synthetic fixture catalog；每个 fixture 的 JSON Pointer 在变异前
   必须存在并等于 `baseline_value`，未变异字段保持冻结。
3. 用 Python stdlib 实现 11 个 validator 的最小确定性 dispatcher；输出 canonical
   failure code、blocking 和 projection，不产生医学结论。
4. 对 86 行各执行一次且只执行一次 RFC 6902 replace，验证 expected outcome/error/
   projection；正向行同时验证无 blocking 诊断。
5. 输出一份只读 evidence receipt，绑定合同/矩阵 SHA、Python 版本、86 行结果和医学写作
   聚合哈希；不把 receipt 当作 runtime/产品接受。

## 建议 create-only 路径

正式执行合同冻结时应再次核定路径；当前最小建议为：

```text
poc/medical_monitoring_ai_native_r6/src/mm_r6/__init__.py
poc/medical_monitoring_ai_native_r6/src/mm_r6/contracts.py
poc/medical_monitoring_ai_native_r6/src/mm_r6/fixtures.py
poc/medical_monitoring_ai_native_r6/src/mm_r6/validator.py
poc/medical_monitoring_ai_native_r6/tests/test_contracts.py
poc/medical_monitoring_ai_native_r6/tests/test_validator.py
poc/medical_monitoring_ai_native_r6/tests/test_challenge_matrix.py
poc/medical_monitoring_ai_native_r6/evidence/r6_contract_runtime_receipt.json
```

不另建 repository、database、service、API、frontend、parser 抽象、插件框架或模型适配层。

## 完成门

- normal、`-O`、`-OO` 与至少三个 `PYTHONHASHSEED` 下 86/86 一致；
- fixture catalog 双遍字节一致，所有 JSON Pointer/baseline/precondition 闭合；
- 49 个诊断码全部映射到 11 个 validator，禁止未声明诊断和静默接受；
- 16 项 prohibition、三模式 output scope、cutoff/revision/carry-forward、raw/display
  数值与 not_evaluable 非零值语义均实际执行；
- exact create-only 路径、R1-R5 输入哈希、542 文件医学写作聚合和 8911/5174 停止门通过；
- 独立 verifier 接受后，才进入第二纵切：ReportSourceRevision、ReportUnit、
  ReportClaim/ReviewIssue 多对多与 ClaimCoverageLedger runtime。

## 下一动作

在 HY3 原会话门关闭前保持只读。门关闭后先冻结 governed execution packet 与 exact
create-only allowlist，再实施上述第一纵切；不得从本审计直接跳到产品或真实报告。
