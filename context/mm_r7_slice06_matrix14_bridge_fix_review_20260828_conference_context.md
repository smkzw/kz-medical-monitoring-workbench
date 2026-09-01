# Conference Context: mm_r7_slice06_matrix14_bridge_fix_review_20260828

Created: 2026-08-28 17:50:03
Objective: Independently review the R7-to-R6 invocation ID mapping and deterministic output-contract repair after the first matrix-14 MTPLX smoke exposed invalid_invocation_id. Verify R6 and R1 remain unchanged, the mapping is deterministic and collision-resistant enough for bounded runtime identity, classifier equality uses the mapped ID, the prompt is deterministic and carries exact expected coverage without provider/model identity, tests cover the live failure mode, and decide whether one controlled MTPLX retry may proceed before DeepSeek. Do not modify files or call models.
Task type: `code_open_audit`
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

- Linked execution task: `mm_r7_slice_06_matrix14_live_smoke_20260828`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `codebuddy-cli/hy3-x`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- Current R7 bridge and focused tests:
  `poc/medical_monitoring_ai_native_r7/src/mm_r7/harness_runtime.py` and
  `poc/medical_monitoring_ai_native_r7/tests/test_harness_runtime.py`.
- Frozen adjacent contracts:
  `poc/medical_monitoring_ai_native_r6/src/mm_r6/agent_harness.py` and
  `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`.
- First failure evidence:
  `runs/execution/mm_r7_slice_06_matrix14_live_smoke_20260828/worker_02.md`.
- Matrix-14 execution context and plan under the matching context/plan paths.

## Scope

- In scope: invocation ID mapping, classifier symmetry, deterministic output
  contract, exact coverage, identity leakage, frozen R1/R6 hashes, focused and
  adjacent offline tests, and the decision on one controlled MTPLX retry.
- Out of scope: source edits by participants, real model calls, real projects,
  product services, browser/frontend, DeepSeek execution and production acceptance.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.

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

- 2026-08-28 17:50:03: Conference initialized by `hermes_workflow_guard.py init-conference`.
- Both participants completed without fallback. Codex accepted Grok's real-R6
  grammar-test gap, remediated it, reran offline suites, and accepted the bridge
  repair. The later MTPLX retry timed out, so matrix-14 stayed blocked.
