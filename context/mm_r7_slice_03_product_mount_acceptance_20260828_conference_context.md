# Conference Context: mm_r7_slice_03_product_mount_acceptance_20260828

Created: 2026-08-28 05:51:18
Objective: 独立审阅 R7 Slice-03 产品挂载是否符合冻结合同：检查产品路由、主应用最小接线、测试与证据；重点寻找 bootstrap 唯一创建边界、项目/Run 身份与自动 scope、中文局部错误、连接关闭、MTPLX medium 默认及显式 DeepSeek V4 Flash max 接入能力中的 P0-P2 缺陷。禁止修改任何文件、启动服务、调用模型或真实项目；输出可定位发现与接受/拒绝建议。
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair. The effective visual participant chain is ``; it is filtered against the actual execution route nodes recorded below before dispatch.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex, logic-heavy, evidence-sensitive, artifact-heavy, code-review, and high-risk contradiction work uses a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/google-antigravity `gemini-3.7-flash` (high) -> Pi/OpenCode Go `muse-spark-1.2-contributor` (high) -> Kimi Code `k3-256k` (medium) -> Codex subAgent `gpt-5.6-luna` (max). Participant 2 is Grok Build `grok-4.6` (medium) -> Pi/Cursor `cursor-grok-4.6` (medium) -> Pi/cms-router `minimax-m3` (high). Codex remains the final authority.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice_03_product_mount_implementation_20260828`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `cursor-cli/auto`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `context/medical_monitoring_r7_slice_03_product_mount_contract_20260828.md` — 冻结合同，SHA256 `23a01f905fa1d19566873b0f04bd8a55f38f37e9ce28529a09a39a1f75f89b9b`。
- `services/api/app/medical_monitoring_r7_product_router.py` — 待验收产品薄适配。
- `services/api/app/main.py` 第 350-365、3405-3428 行 — 产品最小 import/include 接线；不得通读或修改医学写作区域。
- `tests/test_medical_monitoring_r7_product_router.py` — 14 项产品合同回归。
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/run_entry.py`、`profile_store.py`、`run_binding.py`、`api.py` — 已冻结 R7 核心公共接口。
- `poc/medical_monitoring_ai_native_r7/evidence/r7_product_mount_receipt.json` — Codex 更新后的离线证据。
- `runs/execution/mm_r7_slice_03_product_mount_implementation_20260828/worker_01.md`、`worker_02.md`、`worker_03.md` — 执行交接，仅作证据而非验收结论。
- 已观测验证：产品聚焦 14 passed；R7 93 passed；R6 763 passed；相邻产品合同 132 passed；专属改动文件 Ruff/compileall 通过；8911/5174 无监听。

## Scope

- In scope: 只读代码/合同一致性审阅；寻找 P0-P2 缺陷，特别是项目规范化先于工作区写入、bootstrap 唯一创建、局部中文错误、两库连接关闭、自动 project/run scope、MTPLX 默认和名称型 DeepSeek 选择。
- Out of scope: 修改文件；启动 8911/5174 或其他服务；调用真实 VLM/LLM；读取真实临床项目；前端/Patient Journey；安全专项重构；医学写作子系统；R7 后续后台执行/进度功能。

## Success Criteria

- 每个参与者给出带文件/行号或函数定位的独立发现，区分证据、推断与建议。
- 未发现未处置 P0-P2 才建议 Slice-03 受限接受；P3/P4 可记录为后续非阻断优化。
- 参与者不得把测试通过、worker 自报或 receipt 非空当作独立验收本身。
- 不修改任何文件、不启动服务、不调用模型、不读取真实项目或医学写作内容；Codex 保留最终接受权。

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. A catalog/auth/transport health preflight timeout or malformed response is diagnostic and must still allow one live route attempt; explicit user routes also proceed when the catalog is stale or incomplete, while a genuinely missing CLI or native transport boundary may block. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-08-28 05:51:18: Conference initialized by `hermes_workflow_guard.py init-conference`.
