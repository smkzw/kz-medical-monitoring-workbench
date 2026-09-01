# Task Context: monitoring_site_applicability_p7

Created: 2026-07-29 20:12:45
Objective: 为医学监查建立中心/受试者级方案版本适用性矩阵与关闭式规则选版，兼容现有项目级规则包并保护医学写作共享状态
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `kimi-code` / `kimi-code/k3-256k` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rules.py`
- `services/api/app/monitoring_protocol_rule_repository.py`
- `services/api/app/monitoring_rule_authoring_service.py`
- `services/api/app/monitoring_rule_lifecycle_service.py`
- `services/api/app/monitoring_protocol_rule_service.py`
- `services/api/app/monitoring_batch_rule_runner.py`
- `services/api/app/monitoring_daily_run_service.py`
- `services/api/app/medical_monitoring_router.py`
- `services/api/app/main.py`
- `tests/test_monitoring_protocol_rule_repository_hardening.py`
- `tests/test_monitoring_rule_authoring_service.py`
- `tests/test_monitoring_protocol_rule_api.py`
- `tests/test_monitoring_batch_rule_runner.py`
- `tests/test_monitoring_daily_run_service.py`
- `records/active_slices/medical_monitoring_goal_p7_20260729/TASK_CONTEXT.md`
- Latest global and workspace `AGENTS.md` rules supplied by Codex.
- External primary-source decision basis: ICH E6(R3) Step 4 final guideline and
  NMPA/CDE requirements that protocol conduct and amendments require applicable
  ethics review/approval. These sources do not establish a universal
  project-level operational effective date for a multicentre amendment.

## Scope

- In scope:
  - Add an immutable, auditable protocol applicability assignment model for
    centre scope and optional subject override scope.
  - Preserve leading zeros and exact centre/subject identifiers.
  - Require a confirmed operational effective interval and traceable evidence
    before an assignment can select a protocol version.
  - Detect overlapping assignments for the same scope and close on conflict.
  - Resolve by project, centre, subject and event date with subject override
    taking precedence over centre assignment.
  - Return explicit unresolved/conflict diagnostics rather than choosing by
    version date, ethics date, training date, first observed use or file name.
  - Permit a `site_specific` rule pack to reach publication only when the
    associated protocol version has at least one confirmed applicability
    assignment and the strict existing fact/rule/gold/shadow lifecycle passes.
  - Keep existing `project_effective_confirmed` behavior backward compatible.
  - Add product API endpoints for list/create/confirm/retire/resolve operations
    with optimistic state version checks and medical-manager-readable states.
  - Add focused repository/service/API tests, including cross-project, overlap,
    stale-state, missing-evidence and no-fallback cases.
  - If the current runner contract can be extended without weakening its
    immutable snapshot identity, propose and implement the smallest resolver
    seam needed for later record-level rule selection. Otherwise stop after the
    repository/API slice and return an explicit runner migration plan.
- Out of scope:
  - Inventing actual effective dates for RUX, MG-K10 or MY009.
  - Converting ethics approval, protocol date, training date, first observed
    use or CSR amendment date into operational effective evidence.
  - Automatically medically confirming assignments generated from listing.
  - Editing medical-writing business state, shared AI role settings or corpus.
  - Reworking unrelated monitoring UI, risk rules or batch mapping.
  - Security/backdoor audits.

## Success Criteria

- Existing project-level lifecycle tests remain green.
- A confirmed subject assignment overrides a centre assignment only for that
  exact subject and date; otherwise the centre assignment is selected.
- Missing centre, event date, evidence, interval or confirmed assignment closes
  with a stable diagnostic and never falls back to version date.
- Two confirmed intervals for the same scope cannot overlap across versions.
- Candidate/unconfirmed/retired assignments never select a version.
- `site_specific` publication cannot proceed on an empty or candidate-only
  matrix; a fully confirmed matrix plus existing strict shadow evidence can
  proceed.
- Public responses show evidence text and medical meaning first; hashes remain
  internal audit data.
- No write or schema change touches medical-writing data stores or selector
  roles.
- Changed files and exact tests are listed in the executor handoff.

## Risk Boundaries

- Write only inside the workbench repository. Do not modify runtime databases;
  migrations are exercised against temporary test databases until Codex review.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not relax any existing publication, gold-case, shadow, CAS, source or
  project-boundary gate.
- Do not create implicit "best effort" protocol version selection.
- CM remains non-investigational medication/treatment; this slice must not
  merge EC/EX/DA/IP into CM.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 20:12:45: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29 20:16: Current real-project evidence for RUX, MG-K10 and MY009
  does not establish one project-wide amendment effective date. The product
  must represent unresolved/site-specific applicability rather than bypass the
  existing publication gate.
- 2026-07-29 20:24: The primary Kimi Code route was rejected before a usable
  session was created because its provider concurrent-request limit was
  reached. No delegated source changes were produced. Per the declared
  long-horizon route, the implementation slice was re-dispatched to the
  Pi/Alibaba manager fallback with the same write boundary and acceptance
  contract.
- 2026-07-29 20:33: The Pi/Alibaba fallback was rejected before any model
  output or tool call because the provider five-hour quota was exhausted until
  20:50 CST. The runner's generic success envelope contained only the 429
  diagnostic and is not accepted as execution evidence. The same bounded slice
  therefore moved to the next declared cross-provider manager fallback,
  Cursor CLI/auto.
