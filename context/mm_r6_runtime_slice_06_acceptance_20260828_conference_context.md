# Conference Context: mm_r6_runtime_slice_06_acceptance_20260828

Created: 2026-08-28 02:44:45
Objective: Independently challenge and decide limited synthetic/offline acceptance readiness of R6 slice-06 post_lock_pre_cfdi fixed-total outputs against the frozen contract, focusing on fail-open identity, totals, nested references, immutable draft boundaries, and test adequacy.
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

- Linked execution task: `mm_r6_runtime_slice_06_20260828`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `cursor-cli/auto`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `context/medical_monitoring_r6_runtime_slice_06_contract_20260828.md`。
- `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md` §8.4-8.5。
- `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json`。
- `poc/medical_monitoring_ai_native_r6/src/mm_r6/mode_output.py`，SHA-256
  `29ae558fbf976ed63b886053351f47a7ef9e4dcc88299eb3a8ab84a0f2c11c24`。
- `poc/medical_monitoring_ai_native_r6/tests/test_mode_output.py`，SHA-256
  `3169d4930a09b631e165496d215a213b3b54b1a6beaa6bfdae8303405edf277a`。
- `poc/medical_monitoring_ai_native_r6/evidence/r6_post_lock_output_runtime_receipt.json`。
- 三个执行 worker 报告及其 stdout，仅用于核对路由、修改和验证，不作为接受权威。

## Scope

- In scope：只读审查 synthetic/offline `post_lock_pre_cfdi` 四输出的锁定身份、固定总量、
  嵌套 ID、Profile/Timeline 受试者绑定、项目/中心/受试者/风险/checklist 交叉对账、
  draft-only 与 append-only 边界、输入不变和测试充分性；可运行 POC 测试或只读 probe。
- Out of scope：任何写文件、产品/前端/服务、真实项目/报告、医学结论、格式渲染、
  Agent Harness、Query/PD/签署/外发、安全性功能。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- 每席必须尝试找到至少一个具体失败开放反例；不能仅依据 313/690 计数同意。
- 明确给出 `accept_limited`、`repair_then_recheck` 或 `reject` 建议及可复现实证。
- 8911/5174 保持停止，医学写作 542 文件边界不变。

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

- 2026-08-28 02:44:45: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-28: Round 1 returned repair; same Cursor sessions closed duplicate/count/scope/envelope-claim/check-ID/Profile/Timeline gaps.
- 2026-08-28: Round 2 found envelope identity was discarded by the public set gate; same sessions added envelope-aware validation and 14 regressions.
- 2026-08-28: Round 3 accepted source `58cbcb0f…`, tests `a9bc5a7d…`, receipt `8372f0de…`; both seats returned `accept_limited`.
