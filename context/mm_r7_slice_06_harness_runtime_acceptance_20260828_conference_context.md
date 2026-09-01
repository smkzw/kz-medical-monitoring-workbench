# Conference Context: mm_r7_slice_06_harness_runtime_acceptance_20260828

Created: 2026-08-28 17:05:34
Objective: 独立审查纠偏后的 R7 Slice-06 synthetic/offline harness 调用、有限重试与恢复实现，逐项挑战冻结合同矩阵、状态机、身份/租约边界、公开泄漏与回归证据；不得运行真实模型、服务、真实项目或修改产品文件。
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
- The route catalog also retains the `cursor-cli` compatibility label; this
  packet's actual Grok fallback transport is the declared Pi provider `cursor`,
  and no Cursor fallback was used.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice_06_harness_runtime_implementation_20260828`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `codex/gpt-5.6-luna`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- Frozen contract and matrix:
  `context/medical_monitoring_r7_slice_06_harness_attempt_recovery_contract_20260828.md`
  (SHA-256 `3c879889e30541b2556bc8c2643758029b52e7cc9876f9b27d7e0e5b73bbbc21`).
- Pause/recovery truth:
  `context/medical_monitoring_r7_slice_06_immediate_pause_20260828.md`.
- Current corrected R7 sources:
  `poc/medical_monitoring_ai_native_r7/src/mm_r7/harness_runtime.py`,
  `background_recovery.py`, `runtime_progress.py`, `__init__.py`.
- Current focused/product tests:
  `poc/medical_monitoring_ai_native_r7/tests/test_harness_runtime.py`,
  `fake_harness.py`, `test_determinism_adjacent.py`, and
  `tests/test_medical_monitoring_r7_product_router.py`.
- Worker evidence and Codex adjudication:
  `poc/medical_monitoring_ai_native_r7/evidence/r7_harness_attempt_recovery_receipt.json`,
  `context/medical_monitoring_r7_slice_06_harness_runtime_implementation_stage_record_20260828.md`,
  `reviews/codex_execution_mm_r7_slice_06_harness_runtime_implementation_20260828_review.md`,
  and the three restored execution reports/logs.
- R1/R6 adjacent source may be read only to verify public controller/runtime/adapter
  contracts; frontend and medical-writing trees are boundary checks only.

## Scope

- In scope: read-only contradiction review of contract matrix 1–16, dual identity,
  preflight zero-dispatch, status mapping, bounded retry, stop/rebuild semantics,
  run/attempt lease ownership, public leakage and the stated offline regression evidence.
- In scope: identify P0–P2 correctness gaps with exact file/function/test evidence and
  propose the smallest repair; explicitly assess Codex's timeout-plus-identity-drift fix.
- Out of scope: source edits, real model/catalog/OMP calls, services, ports, browser,
  frontend/visual review, real projects, medical conclusions, security design/testing,
  or later Slice/Phase work.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Each participant independently returns either an explicit bounded acceptance or
  actionable findings tied to current bytes and a missing/insufficient test.
- Any finding is replayed by Codex before acceptance. Offline acceptance requires no
  remaining P0/P1/P2 defect in the frozen Slice-06 scope.
- 8911/5174 remain stopped and no real model/project/service invocation occurs.

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
- Participants are read-only and must not run excluded listener/Seatbelt probes merely
  to reproduce known environment limitations.

## Loop Log

- 2026-08-28 17:05:34: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-28 17:06: execution evidence was restored from the recoverable archive solely
  because route-dedup requires original runner stdout; execution was not re-dispatched.
- 2026-08-28 17:19: Pi completed one terminal high-effort pass with no fallback;
  Grok completed one terminal medium-effort pass with no fallback.
- 2026-08-28 17:24: Codex reproduced both Grok P1 candidates. Claim-before-bind
  recovery passed and disproved the pending-zombie inference. The retry-exhausted
  overlay hid a legal `继续` action and was repaired with one runnable-work flag
  plus a two-unit regression.
- 2026-08-28 17:31: focused/adjacent gates passed at harness 32, product 33,
  R7 157, R1 311/4 deselected, and R6 758/5 deselected. Grok used the same
  session for round 2, retracted the false P1, accepted the repair, and reported
  no open frozen-scope P0/P1/P2. Offline conference passed to matrix 14 only.
