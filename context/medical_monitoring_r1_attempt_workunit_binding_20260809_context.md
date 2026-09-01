# Task Context: medical_monitoring_r1_attempt_workunit_binding_20260809

Created: 2026-08-09 22:04:53
Objective: 在隔离R1 synthetic/offline POC中将manifest work-unit execution identity自动绑定到application-owned capability attempt journal/profile，拒绝调用方伪造、错配、跨revision或迟到身份；不触碰产品、医学写作、8911、真实provider/harness/project
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §§5, 9, 12:
  application-owned state, frozen execution profile, truthful progress and retry/recovery.
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R1 steps 6-8 and
  its current recovery anchor.
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`, `store.py`,
  `capability_runtime.py`, `adapters.py`: current manifest/work-unit, capability attempt journal,
  profile and immutable binding contracts.
- `poc/medical_monitoring_ai_native_r1/tests/test_authoritative_progress.py` and
  `tests/test_capability_runtime.py`: current offline acceptance contracts.
- `poc/medical_monitoring_ai_native_r1/docs/R1_AUTHORITATIVE_PROGRESS_EVIDENCE.md` and
  prior attempt/isolation evidence: accepted boundary and residual that caller-supplied
  work-unit identity is not yet journal-bound.
- Same-day primary-source discovery already selected application-owned manifest/SQLite state and
  rejected a new scheduling dependency. This slice joins two accepted local authorities and does
  not change that assumption, so no new library/framework scan is required.

## Scope

- In scope: durable, revision-bound association between an AI work unit and one or more immutable
  capability attempts; execution identity derived only from the attempt request/profile binding;
  explicit continuation-chain checks; fail-closed terminal status projection; migration and
  corruption tests; structured progress remains Chinese audience-readable and omits raw logs/secrets.
- In scope: deterministic work units retain the existing direct begin/complete contract; AI work
  units use the capability-bound contract. Retry attempts may replace the current internal identity
  only through `continued_from` and preserved binding history.
- Out of scope: controller loop, background service, UI rendering, real provider/harness/project,
  credentials, production sandbox choice, 8911 and all product/medical-writing source.

## Success Criteria

- AI work-unit callers cannot supply provider/model/attempt identity directly or bypass a bound
  capability attempt at completion.
- Binding rejects unknown attempt, wrong run/node/revision, deterministic node, duplicate use by a
  second work unit, invalid request/binding identity and broken continuation chains.
- First binding begins the work unit atomically; a continuation attempt updates the current internal
  identity while preserving immutable attempt history and emits a structured retry transition.
- Completion is accepted only from the latest bound attempt after its durable journal state is
  terminal/interrupted; `complete` maps to passed, interrupted to blocked, and all other terminal
  transport outcomes fail closed to failed.
- Manifest/ledger/audit/binding/journal projections reconcile exactly and detect direct corruption.
- Focused, adjacent and full R1 tests, Ruff and compileall pass; fresh-context reviewer accepts the
  frozen slice before Codex marks it complete.

## Risk Boundaries

- Allowed writes are only the isolated R1 POC source/tests/docs and this task's existing
  `context/`, `reviews/`, `metrics/`, `prompts/` records. Do not edit runner-owned `runs/` files.
- Preserve the medical-writing subsystem, product source and unrelated concurrent changes.
- Port 8911 stays stopped. Do not start a service, install a dependency, execute a provider/harness,
  or read a real project.
- Internal execution identity is audit metadata, not a user-facing label. Future UI must keep
  Chinese clinical language and must not show provider/model/backend jargon to the medical monitor.
- Independent fresh-context review owns the slice verdict; Codex owns final acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-09 22:04:53: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-09 22:08 CST: Re-anchored from the accepted authoritative-progress slice and the durable
  capability attempt journal. Selected a schema-v6 association ledger rather than trusting a caller
  identity or assuming one attempt forever: one logical AI work unit may bind a strictly ordered
  `continued_from` chain while deterministic units retain their direct path. No new dependency or
  external runtime is introduced.
- 2026-08-09 22:25 CST: Implemented schema v6 `work_unit_capability_attempts`, journal-derived
  execution identity, direct-path rejection for AI work units, atomic first binding, ordered retry
  bindings, fail-closed outcome mapping and five-way manifest/row/binding/journal/audit projection
  reconciliation. Internal retry identity may change only through an exact latest-attempt
  `continued_from` edge; every prior attempt remains immutable.
- 2026-08-09 22:25 CST: Added synthetic tests for identity forgery/bypass, all terminal mappings,
  retry chain, duplicate attempt, cross-revision and deterministic-node mismatch, binding corruption,
  two-connection contention and v5-to-v6 migration. Frozen pre-review anchors pass: focused 30/30,
  adjacent 103/103, capability 51/51, R1 core 184/184, Ruff and compileall. Independent fresh-context
  review remains pending; no slice acceptance is claimed yet.
- 2026-08-09 22:38 CST: Independent Luna session `019fe6e5-48b2-7292-ba62-f8ed6ad64a5d`
  returned VETO after reproducing two missing fail-closed boundaries: public Store lifecycle methods
  could synthesize a successful terminal attempt, and a rehashed terminal journal row was not
  reconciled with capability lifecycle audit events. It also identified the stale 170-vs-184 core
  count in the implementation anchor.
- 2026-08-09 22:52 CST: Remediated without expanding the product boundary. Capability lifecycle
  mutation moved behind the runtime-only private facade; public audit append now reserves the four
  authoritative capability lifecycle events; every journal row is reconciled against its lifecycle;
  and terminal attempts must present a request/binding/raw-output/work-event/candidate/transport
  evidence envelope before binding authoritative progress. The reviewer probes are permanent tests.
  Re-frozen local anchors: focused 37/37, adjacent 110/110, capability 51/51, R1 core 191/191,
  Ruff and compileall pass. Same-session independent follow-up remains required.
- 2026-08-09 23:05 CST: Same Luna session completed its remediation follow-up with ACCEPT. It
  independently reproduced 37 focused, 110 adjacent and 51 capability passes; Ruff/compileall;
  absence of all four public Store lifecycle mutators; rejection of all four reserved capability
  lifecycle events; and stable start/end hashes. P0-P3 are zero. Accepted only for this isolated
  synthetic/offline slice; real providers, harnesses, services/8911, product integration, hostile
  same-process callers and long-running recovery remain outside the claim.
