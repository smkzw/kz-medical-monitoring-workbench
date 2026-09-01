# Conference Context: mm_r7_slice08d_contract_20260830

Created: 2026-08-30 09:20:42 CST
Objective: 独立挑战并冻结R7 Slice-08D三模式synthetic综合回归合同，核对三模式语义、确定性、故障恢复、相邻回归、用户中文边界和P0-P4完成门；不修改产品、不启动服务/真实项目/模型、不触碰医学写作
Task type: `stage_review_plan`
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

- Linked execution task: `mm_r7_slice08d_contract_20260830`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_1_20260830.md`
- `reviews/medical_monitoring_r7_slice08_three_mode_carry_forward_contract_v0_2_20260829.md`
- `context/medical_monitoring_r7_phase_review_after_slice08c4_and_slice08d_plan_20260830.md`
- `context/medical_monitoring_r7_slice08a_continuity_acceptance_record_20260829.md`
- `context/medical_monitoring_r7_slice08b_authority_artifact_bridge_acceptance_record_20260829.md`
- `context/medical_monitoring_r7_slice08c4_visual_acceptance_record_20260830.md`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/{continuity.py,continuity_bridge.py,launch_registry.py}`
- directly related synthetic/offline tests under `poc/medical_monitoring_ai_native_r7/tests/` and `tests/test_medical_monitoring_r7_product_router.py`

## Scope

- In scope: independently challenge the v0.1 contract for three-mode completeness, independent-oracle quality, deterministic subprocess coverage, failure/rollback semantics, adjacent regressions, Chinese audience boundaries, P0-P4 definitions, and minimal implementation shape. Return ACCEPT or exact revisions.
- Out of scope: product edits, service/browser/model startup, real-project or real-listing reads, UI/visual redesign, system-security work, medical-writing files, R7/R8 overall acceptance.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- The participant explicitly identifies any missing matrix cell or overfitted/non-independent oracle risk and proposes exact contract text.
- Contract acceptance requires zero unresolved semantic ambiguity that would change 08D implementation or its pass/fail meaning.

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

- 2026-08-30 09:20:42 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
