# R6 synthetic/offline runtime 第三纵切验收记录（2026-08-28）

状态：`ACCEPT_R6_RUNTIME_SLICE_03_SYNTHETIC_OFFLINE`

## 接受范围

接受 synthetic/offline JSON 的 ReportReviewBundle、18 字段共享身份、内容寻址、
sidecar 批注投影、anchor map、可选 DRAFT 清洁稿、IssueTransition 和跨修订 diff。

不接受：产品 runtime、真实报告/项目、医学或监管结论、DOCX/PDF/HTML 解析与渲染、
前端/浏览器、R6 总体或医学写作子系统。

## Codex 纠偏与会商闭环

受治理执行完成三个 worker 后，Codex 与独立会商逐项关闭以下失败开放：

- 派生 piece/bundle ID 不可由调用方伪造，必须按当前内容重算；
- annotation 必须完整覆盖 matrix issue，并沿用权威 evidence/locator；
- caller 布尔值不能充当无损原位批注证明，本纵切只有 sidecar；
- DRAFT 必须精确保留未决 issue、冲突、不可评价和 cutoff/version gap；
- lifecycle-only 或 evidence-only 变化不能成为 `resolved`；
- 同 identity 多实例无显式 transition 时不按列表位置配对；
- merge/split 必须验证所有 source-target 组合；
- 遗漏单元或 claim 改挂到其他已覆盖对象不能关闭原缺口；
- 页码/显示顺序、纯页码路径和纯段落/章节/表/图/脚注序号不能冒充内容锚点；
- 投影 `payload_role` 使用 canonical `projection`。

Grok Build 保持同一 session 完成多轮反例与纠偏复核，最终确认遗漏单元 relink
失败闭合、指定伪锚点失败闭合且真正 open-to-claimed 的正向 `resolved` 路径未破坏。
Codex 又按权威合同“段落序号不能单独决定身份”收紧 ordinal-only locator 并补充测试。

## 决定性证据

- focused：`71 passed`。
- full R6 POC：`377 passed`。
- normal/`-O`/`-OO` × `PYTHONHASHSEED=0/1/42`：9/9 单元均为
  `71 passed`。
- slice-01 oracle 与 slice-02 adjacency 继续通过。
- 医学写作保护面：542 文件，aggregate
  `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`。
- 8911/5174 无监听；未启动服务、未使用真实项目。
- receipt：`poc/medical_monitoring_ai_native_r6/evidence/r6_report_bundle_runtime_receipt.json`。
- conference review：`reviews/codex_conference_mm_r6_runtime_slice_03_acceptance_20260827_review.md`。

## 最终 SHA-256

```text
0f496c6aaf6dec917099a21d5221de8cae68ef48e740444166294265635e457a  report_bundle.py
0ad83f97171fd63b94deb5046f254211b45ef1e383db36ffe90ce67aa394ca2b  test_report_bundle.py
20b102b6bd08ffafc01d5517d2e35a7dc5dc6f29e4d3f5d6a3f9475057e0a4e7  test_report_review.py
5531ae46bd6d552d213c25020357dcbb49cd3fdc3fda977e27be2c8f36f35fe6  test_challenge_matrix.py
78a107fd22c44e0dbcf5d320ed56e90d54cb2f4de4fb4d083b701851a1d307e7  __init__.py
5e49860081f52b462caf62e2728563df43766cc87f28a530813ef02ddf724b95  README.md
```

## 已接受残余边界

1. 本纵切不解析真实文件，locator/anchor 只在 canonical JSON 内验证。
2. 无字节/容器级 fidelity proof，因此不提供 `in_place_copy`。
3. `resolved` 是本合同内证据与覆盖闭合状态，不等于医学人员确认或外部 Query 关闭。
4. 无格式感知渲染、真实报告三件套或用户界面接受。

## 下一安全动作

另立 R6 下一纵切合同，优先实现日常增量摘要/受影响 Query 与三模式输出结构，或先冻结
真实文件 parser/renderer 边界；任何真实报告、DOCX/PDF/HTML 或产品接入均需独立门禁。
8911/5174 在需要真实浏览器验收前继续停止，医学写作子系统继续冻结保护。

Agent Harness 模型接入作为后续独立合同记录：默认目标为
`mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`，并保留、验证
`deepseek/DeepSeek V4 flash:max` 的接入和实际应用能力；本纵切未实现或声称该能力。
