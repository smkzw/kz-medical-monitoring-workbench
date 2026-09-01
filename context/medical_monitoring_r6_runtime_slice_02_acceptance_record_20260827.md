# R6 synthetic/offline runtime 第二纵切验收记录（2026-08-27）

状态：`ACCEPT_R6_RUNTIME_SLICE_02_SYNTHETIC_OFFLINE`

## 接受范围

接受 R6 v0.1 的报告来源/对象/覆盖账最小运行时：原始字节 SHA、同项目+
同报告谱系去重、不可变修订与 parent lineage、Run/report source 分离、
ReportUnit/ReportClaim/ReviewIssue 多对多、冻结 expected review surface、反向遗漏映射、
ClaimCoverageLedger 以及 `coverage_closed` / `full_report_reviewed_eligible`
双门。数据仅为 synthetic/offline。

不接受：真实报告/项目、文件解析、三件套生成与渲染、产品/API/前端、
医学结论、Patient Journey UI 或 R6 总体。

## Codex 纠偏与会商闭环

受治理 worker_02 因长任务边界只留下 coverage 常量，未完成三个覆盖 API。
Codex 直接实现矩阵/账本/验证器并修正 slice-01 只读 allowlist 与新增文件
的集成矛盾；该例外仅增加三个已授权 slice-02 路径，不声称测试文件字节不变。

独立 Grok 首轮发现反向 `not_evaluable_exception` 缺少 `report_scope`
仍可获得“全报告已审阅资格”的 fail-open。Codex 继续关闭：

- 空白/缺失 report scope、空壳 evidence ref 及 link-level 空证据；
- 非法 expectation kind；
- `no_claim` 同时存在 claim 链接；
- 父单元循环；
- 同项目跨报告谱系的错误去重；
- issue identity scope 静默默认；
- 报告制品 ID 与子对象 locator 不一致。

同 session 第三轮 Grok 复核确认未再发现本纵切双门/反向遗漏范围的
runtime fail-open，建议有边界接受。Gemini 输出作为辅助审阅；其对中间树的
部分描述已过时，未作为最终证据。

## 决定性证据

- focused：`63 passed`。
- full R6 POC：`306 passed`。
- normal/`-O`/`-OO` × `PYTHONHASHSEED=0/1/42`：9/9 单元均运行完整
  `test_report_review.py`，每单元 `63 passed`，包含 coverage/双门测试。
- slice-01 oracle：86 行、0 mismatch。
- 医学写作保护面：542 文件，aggregate
  `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- 8911/5174 无监听。
- execution audit 与 conference review-gate 均通过。
- receipt：`poc/medical_monitoring_ai_native_r6/evidence/r6_report_review_runtime_receipt.json`。

## 最终 SHA-256

```text
cd96d8479d9ce6c8c720961e2a57513c8d339b4ccd59ccc7e9e543dd8811abab  report_review.py
1dc7514acf6b01897ef401fea1ab205081050c85f86d424489ef00925936600c  test_report_review.py
f8becd256c09bb8d3be4a6a5cc2fdb00aef7e82a90ac09160dce258127ce9195  test_challenge_matrix.py
897c941b5e05f6447f7e4958c8927c291e0b73742cc1250deb30c44b30351a51  __init__.py
e66c6b155586b288b45138b87579fce7e9bb4f8ff46881382e2c4c99494568b3  README.md
```

## 已接受残余边界

1. 本纵切以 `units` 参数作为已冻结 expected unit set；独立 parser manifest 后续实现。
2. 无原始字节封印时，无法证伪 source 与所有 locator 一致伪造的 artifact ID。
3. `qc.state` 仅是 matrix-local QC，不是三件套或渲染 QC。
4. `coverage_incomplete` 为双门资格诊断扩展；不借此扩大医学含义。

## 下一安全动作

冻结 R6 第三纵切合同：仅实现三件套共享身份封装、批注 anchor/旁注结构、
可选清洁稿 provenance 与修订 issue diff，继续 synthetic/offline；不接真实文件、
不做 DOCX/PDF/HTML 渲染、不启动 8911/5174。
