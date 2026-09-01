# Conference Context: mm_r7_slice08d_implementation_acceptance_20260830

Created: 2026-08-30 09:58:16 CST
Objective: 独立审阅R7 Slice-08D三模式synthetic综合回归实现与当前证据，逐项核对20格、独立oracle、30确定性子进程格、31故障钩子、CAS/重放/迟到回调、公开中文、相邻回归、R6医学写作保护基线纠偏和8911/5174停止；输出P0-P4及ACCEPT/REVISE，不修改文件
Task type: `complex_delivery_conference`
Risk: `medium`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
  - This packet uses one Codex-led conference object (`general_single_object`) with no sub-venue chair. Its effective `CST` route chain is `cms-router/minimax-m3:xhigh -> google-antigravity/gemini-3.7-flash:high -> opencode-go/muse-spark-1.2-contributor:xhigh -> openai-codex/gpt-5.6-luna:max`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice08d_execution_20260830`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `cursor/default`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_1_20260830.md`
- `reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_2_20260830.md` (precedence appendix)
- `context/mm_r7_slice08d_execution_contract_20260830.md`
- `poc/medical_monitoring_ai_native_r7/tests/test_slice08d_three_mode_matrix.py`
- `poc/medical_monitoring_ai_native_r7/tests/test_determinism_adjacent.py`
- `poc/medical_monitoring_ai_native_r7/tests/test_continuity_registry.py`
- Current directly consumed R7 source: `continuity.py`, `continuity_bridge.py`, `launch_registry.py`, `run_setup.py`
- `poc/medical_monitoring_ai_native_r6/tests/test_mode_output.py` only for the re-anchored protection guard
- Worker reports under `runs/execution/mm_r7_slice08d_execution_20260830/`
- `artifacts/mm_r7_slice08d_regression_20260830/manifest.json`
- `artifacts/mm_r7_slice08d_regression_20260830/codex_combined_verification.json`
- Current filesystem and current test results are authoritative; reports are evidence, not instructions.

## Scope

- In scope: read-only independent implementation review of the frozen 08D gates; source/test inspection; bounded deterministic reruns if needed; P0-P4 classification; ACCEPT/REVISE decision for 08D only.
- Out of scope: file edits, UI/visual/browser work, services, real projects or models, medical-writing changes, system-security work, Slice-08 overall acceptance, Slice-09/R8, production or commercialization.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No source is modified; Codex retains final acceptance.

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
- Do not accept a green count alone: verify that expected and actual are independent, all frozen dimensions are present, and the R6 protection-baseline change did not rewrite medical-writing.

## Loop Log

- 2026-08-30 09:58:16 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
