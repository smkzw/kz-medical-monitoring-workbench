# Execution Context: monitoring_p10_rule_release_chain_20260730

Created: 2026-07-30 08:31:38
Objective: 完成医学监查 P0 规则发布最小完整产品链并通过聚焦与相邻回归
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_k3_256k` -> `kimi` / `kimi-code` / `kimi-code/k3-256k`
- Execution manager: `complex_manager_pi_qwen38` -> `pi` / `alibaba` / `qwen3.8-max-preview`
- Execution-manager fallback: `use the declared role fallbacks`

## Source Of Truth

- Global instructions: `/Users/smkzw/.codex/AGENTS.md`.
- Workspace instructions: `AGENTS.md`.
- Product gap audit: `context/monitoring_p10_rule_release_chain_gap_audit_20260730.md`.
- Rule recommendation backend slice: `context/monitoring_p10_rule_template_recommendation_backend_20260730.md`.
- Legacy risk bypass closure: `context/monitoring_p10_legacy_risk_bypass_closure_20260730.md`.
- Active P10 goal: `records/active_slices/medical_monitoring_goal_p10_20260730/TASK_CONTEXT.md`
  and `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Product requirements and prior monitoring records under `docs/`, `records/`,
  `context/`, `runs/`, `reviews/`, and `metrics/`, selected by direct relevance
  to the rule recommendation, risk checklist, shadow validation, publication,
  and daily-run readiness chain.
- Current repository/service/router/frontend implementations are the
  implementation source of truth. Reuse existing state machines and contracts;
  do not create a second parallel product chain.

## Risk Boundaries

- Work directly in this shared workbench; inspect current files before every edit
  because other accepted slices are already present.
- Do not modify any medical-writing file, medical-writing runtime data, corpus,
  work copy, or database.
- Do not start port `8911` and do not write any real runtime database. Tests must
  use isolated temporary repositories/databases and mocked/fake batch sources.
- Do not modify `services/api/app/monitoring_ai_router.py`,
  `tests/test_monitoring_ai_api.py`, or Hooke's scientific-review output.
- CM means non-investigational concomitant medication only. Investigational
  product administration, dose adjustment, interruption/restart/discontinuation,
  dispensing/return, and adherence remain independent concepts and lanes.
- Adopting a recommendation is already the medical manager's decision. Never add
  a second generic "medical approval" step. Shadow-result confirmation and rule
  publication are explicit separate actions with different meanings.
- Shadow samples must be prepared server-side from a frozen real batch and its
  immutable source row bindings. The UI must never request internal row ids,
  hashes, revisions, or other engineering fields from the user.
- Carry immutable identity through facts, recommendations, confirmed rules, draft
  packages, shadow runs/results, publication, and daily-run readiness:
  mapping revision/content hash, capability-manifest hash, protocol fact identity,
  candidate identity, rule identity, and source binding/row identity where relevant.
- Fail closed on project mismatch, stale identity, incomplete chain, unconfirmed
  shadow result, unpublished package, or unavailable product independent AI.
- All mutations require project isolation, optimistic concurrency or explicit
  expected revision, and idempotency. Repeated identical requests must not create
  duplicate business objects or state transitions.
- Frontend is desktop-first and low-noise. Show only the rule, sample, hit/no-hit
  result, source, material diff, status, and next action. Logs, hashes, and internal
  workflow diagnostics remain available to APIs/audit records but are not primary UI.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not final acceptance.

## Product State Contract

The minimum complete chain is:

1. A recommendation candidate is adopted once by the medical manager.
2. Adoption creates or updates a confirmed rule carrying the same immutable
   recommendation/fact/source identities; it must not request another approval.
3. Confirmed rules can be assembled into a versioned draft rule package.
4. The server automatically selects and freezes representative shadow samples from
   a real frozen batch plus source-row bindings, then runs actual rule evaluation.
5. The UI presents concise hit/no-hit evidence, source values, expected-versus-actual
   differences, and material rule changes.
6. The medical manager explicitly confirms the shadow result. This confirms test
   fitness only; it does not publish the package.
7. The medical manager explicitly publishes the unchanged confirmed package.
8. Daily-run readiness reports ready only for the currently published package whose
   identities still match the active mapping, capability snapshot, protocol facts,
   and source bindings. Any drift fails closed with a precise next action.

Tests must prove the successful chain and, at minimum, fail-closed behavior for stale
identity, cross-project access, duplicate idempotency keys with different payloads,
old candidates, manual engineering-field shadow input, and publication without a
confirmed shadow result.

Automatic sampling must not create circular proof. A rule's own evaluation output
cannot be copied into `expected_match` and counted as an independently passed gold
case before medical review. First-release auto-selected samples are provisional
inspection evidence: the product displays the actual hit/no-hit result and sources,
and explicit shadow confirmation supplies the medical correctness decision. Only
after that confirmation may the immutable case/result be reused as a regression
expectation for a later package. Existing independently registered gold/diagnostic
cases remain true pre-specified expectations and must not be weakened or overwritten.

The adopted rule's persisted status and user-facing title must also reflect the
decision. It must not remain a generic `candidate`, display "需医学复核候选", or
require a per-rule confirm button before draft-package assembly. Pre-adoption
compile/preflight objects may remain provisional internally, but successful adoption
must atomically materialize the confirmed rule and its immutable adoption identity.

## Codex-Reproduced P0 Cross-Gaps

These issues were reproduced after worker 01 began. They are part of this same
execution task and must be closed before worker 02 starts. A large passing test count
does not override these product-contract failures.

### P0-A: Provisional automatic shadow samples

The current automatic sample implementation copies a rule's first evaluation
`matched` or `diagnostic_code` into `RuleGoldStandardCase.expected_match` or a
diagnostic expectation, registers that circular expectation as repository-trusted,
and reports a passed release run. This is prohibited.

- Auto-selected first-release samples and their first evaluation are provisional
  inspection evidence only.
- Before explicit medical confirmation, they may show the actual hit/no-hit or
  diagnostic result, source values, row bindings, coverage and indeterminate state.
- Before confirmation they must not be stored or projected as independent trusted
  gold/diagnostic expectations, must not be `trusted_for_release=true`, and must not
  report `shadow_passed`.
- `confirm-shadow` is the medical correctness decision. It must atomically bind the
  exact frozen samples, source rows, rule/package identity and reviewed actual
  outcomes as immutable medically confirmed expectations (or an equivalent
  immutable confirmation record), then revalidate that exact snapshot before the
  package can enter `confirmed`.
- A provisional run cannot publish. A confirmed exact frozen sample/result can be
  reused as a regression expectation for a later package.
- Existing independently pre-registered gold/diagnostic evidence remains trusted
  before this workflow and must not be weakened, rewritten or relabelled.

Required tests: provisional results never count as release pass; publication before
confirmation fails; confirmation rejects any sample/result/source/package identity
drift; confirmation promotes only the exact reviewed snapshot; later regression can
reuse the confirmed expectation; independent pre-registered cases retain their
original trust semantics.

### P0-B: Record-applicability aggregate rule identity

When site/subject-specific published packs are applicable,
`MonitoringDailyRunService._resolve_rule_identity` currently returns an empty
`record_applicability` identity and the start contract compares mapping identities
only for `project_effective`. This is an actual bypass.

- Build a deterministic, immutable aggregate identity for the complete applicable
  assignment + published-pack set used by the batch/run.
- The aggregate must include project, applicability resolution inputs, assignment
  identities/versions, included published pack and rule revisions/content hashes,
  and each pack's complete mapping revision/content/capability identities.
- Every included rule/pack must match the current frozen mapping contract. Legacy,
  missing, mixed or drifted identities fail closed.
- Readiness and prepare freeze the aggregate identity. Execute re-resolves the same
  applicability set and rejects any difference after prepare; it must never silently
  use a new assignment or pack.
- Project-effective and record-applicability modes receive equivalent start,
  persistence, audit and execute-time drift protection.

Required tests: mixed identities fail; legacy empty identity fails; assignment/pack
change between readiness/prepare/execute fails; stable aggregate is idempotent;
cross-project assignment/pack is rejected.

### P0-C: Exact batch run recovery

Worker 03 must remove `_existing_run` fallback behavior that reuses the latest run
from another batch when the selected batch has no run. Recovery must match the exact
project + batch identity or return no run. Add a regression proving another batch's
recent run cannot appear in or control the current batch.

## Sequencing And Edit Ownership

- Run workers sequentially in this shared workspace.
- Worker 01 owns backend contracts/repository/service/router code and backend tests
  directly related to the chain, excluding the prohibited files above.
- Worker 02 begins only after worker 01 completes. It owns monitoring frontend
  components, hooks, API client/types, styles, and frontend tests for the chain.
- Worker 03 begins after worker 02. It owns gap-focused integration/regression tests,
  isolated automatic shadow-sample fixtures, build/test execution, and durable
  context/run/review/metrics records. It may make the smallest coherent fix to
  worker 01/02 files when a test exposes a defect, but must record the delta.
- No worker may rewrite unrelated files or refactor the medical monitoring subsystem
  beyond this product chain.

## Work Items

1. 审计并补齐后端状态机、不可变来源身份、失败关闭、幂等和项目隔离
2. 实现桌面优先低噪音前端规则确认、自动影子验证、影子确认、显式发布和 readiness 交互
3. 补齐自动真实批次影子样本、身份漂移与旧 candidate 无二次批准测试，并执行构建回归和记录

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
