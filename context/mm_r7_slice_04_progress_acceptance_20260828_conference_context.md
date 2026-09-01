# Conference Context: mm_r7_slice_04_progress_acceptance_20260828

Created: 2026-08-28 09:16:42
Objective: 对 R7 Slice-04 耐久运行进度实现进行独立只读验收：逐条核对冻结契约、身份隔离、零I/O边界、幂等与回退阻断、post_lock冻结、中文产品投影、测试与证据真实性；仅报告可复现缺陷，不修改文件，不启动服务/模型/真实项目，不触碰医学写作子系统。
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair. The effective visual participant chain is ``; it is filtered against the actual execution route nodes recorded below before dispatch.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex, logic-heavy, evidence-sensitive, artifact-heavy, code-review, and high-risk contradiction work uses a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/google-antigravity `gemini-3.7-flash` (high) -> Pi/OpenCode Go `muse-spark-1.2-contributor` (high) -> Kimi Code `k3-256k` (medium) -> Codex subAgent `gpt-5.6-luna` (max). Participant 2 is Grok Build `grok-4.6` (medium) -> Pi/Cursor `cursor-grok-4.6` (medium) -> Pi/cms-router `minimax-m3` (high). Codex remains the final authority.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice_04_progress_implementation_20260828`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `codex/gpt-5.6-luna`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `context/medical_monitoring_r7_slice_04_durable_run_progress_contract_20260828.md`（冻结契约，SHA256 `a5033b871ffd025cc5dd6345fb9a1bd214e41f01e3893ef2f94ca7ac6d830745`）
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/runtime_progress.py`
- `services/api/app/medical_monitoring_r7_product_router.py`
- `poc/medical_monitoring_ai_native_r7/tests/test_runtime_progress.py`
- `tests/test_medical_monitoring_r7_product_router.py`
- `poc/medical_monitoring_ai_native_r7/tests/test_determinism_adjacent.py`
- `poc/medical_monitoring_ai_native_r7/README.md`
- `poc/medical_monitoring_ai_native_r7/evidence/r7_durable_progress_receipt.json`
- R1/R6 既有实现与测试仅用于相邻回归核对，不允许修改。

## Scope

- In scope: Slice-04 代码与测试的只读契约审查；可运行不启动服务的离线 pytest/静态检查；报告具体文件、触发条件和建议修复。
- Out of scope: 修改任何文件；启动 8911/5174；真实模型调用；真实临床项目；前端/视觉验收；医学写作子系统；Slice-05 以后能力。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- 上述授权工作台范围内仅只读；不触碰真实项目或医学写作文件；Codex retains final acceptance.

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

- 2026-08-28 09:16:42: Conference initialized by `hermes_workflow_guard.py init-conference`.
