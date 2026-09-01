# Task Context: medical_monitoring_consumer_handoff_determinism_20260805

Created: 2026-08-05 01:06 (Asia/Shanghai)
Objective: Make clinical consumer handoff risk and subject index collections
deterministic for stable audit hashes and UI ordering
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes workflow guard because it
touches a source-preserving clinical consumer boundary and its downstream
hash/visual ordering contract.

## Source Of Truth

- `services/api/app/monitoring_clinical_consumer_handoff.py`
- `tests/test_monitoring_clinical_consumer_handoff.py`
- adjacent clinical projection and frontend consumer-conservation tests
- current P10 ledger and completion audit under `records/active_slices/`

## Scope

- In scope: sort set-derived risk event/observation/subject/site/rule and
  subject safety-metric collections; add regressions that prove repeated
  handoff construction is byte/hash and ordering stable.
- Out of scope: source parsing, clinical inference, severity calculation,
  persistence migration, provider calls, service/API startup,
  browser/Playwright tests, real projects, B6/C14 review or activation,
  medical conclusions and unrelated UI or medical-writing files.

## Success Criteria

- Handoff output has stable ordering regardless of set insertion order.
- Existing consumer/projection/adapter tests remain green; compile, Ruff and
  reserved-port checks pass.
- Evidence keeps runtime and release gates unchanged and closed.

## Risk Boundaries

- Do not start or connect to 8911, 5174, 8910 or 4173; do not touch runtime
  databases or real projects.
- No external model dispatch; Codex remains final authority.
- Preserve source identity and existing public schema.

## Timeout Policy

- This is a direct bounded Codex change; no provider or sub-agent is used.

## Loop Log

- 2026-08-05 01:06: initialized task after source audit found direct tuple
  conversion from set-backed risk and subject index collections.
- 2026-08-05 01:07-01:09: sorted all set-derived risk drilldown and subject
  metric-index collections, added reverse-input/hash/order regressions, and
  completed focused, adjacent and decisive offline checks.

Created: 2026-08-05 01:06:32
Objective: Make clinical consumer handoff risk and subject index collections deterministic for stable audit hashes and UI ordering
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- TODO: Add authoritative local files, extracts, datasets, screenshots, URLs, or user-provided materials.
- Do not add production paths unless the user has explicitly authorized reading them for this task.

## Scope

- In scope: TODO
- Out of scope: TODO

## Success Criteria

- TODO

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 01:06:32: Task initialized by `tools/hermes_workflow_guard.py init-task`.
