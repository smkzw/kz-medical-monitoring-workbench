# Task Context: medical_monitoring_assurance_audit_row_revalidation_20260805

Created: 2026-08-05 05:19:34
Objective: Fail closed on assurance audit-chain row metadata or project/task binding drift
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `alibaba` / `qwen3.8-max` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_assurance_repository.py`
  (`_audit_event_from_payload`, `_append_audit_event`, `list_audit_events` and
  the audit-chain schema).
- `services/api/app/monitoring_audit_contract.py` and
  `tests/test_monitoring_assurance_principal_route.py` audit-chain suites.
- Current filesystem state and
  `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`.
- Real-loop and release gates remain authoritative and blocked; this slice is
  source-only and cannot activate runtime or external providers.

## Scope

- In scope: validate persisted audit row hash/prev-hash/project/task/timestamp
  metadata against the canonical event and requested task; preserve the
  independent chain verification and write path; add focused tamper
  regressions, run assurance adjacency, compile/Ruff, hashes, evidence and
  review gate.
- Out of scope: services, ports, browsers/Playwright, real project data,
  external providers, medical judgments, new audit hash/schema schemes,
  authority artifacts and runtime/release activation.

## Success Criteria

- Valid audit events round-trip and the project chain remains verifiable across
  task modes.
- Row metadata drift or event project/task/timestamp binding drift fails closed
  before callers receive the audit chain.
- Focused/adjacent tests, compileall, Ruff and reserved-port checks pass; the
  evidence records exact counts, hashes, warnings and residual limits.
- Review gate reports `ok: true` with no warnings/errors.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 05:19:34: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Codex direct source-only implementation selected; no Hermes
  execution session, provider call or sub-agent dispatch.
- 2026-08-05: Hardened audit-row metadata/project-task binding reads and
  preserved detailed drift errors; added four isolated tamper regressions.
  Focused 96 and adjacent 216 passed; compileall/Ruff passed; ports remained
  free; Hermes review gate returned `ok: true`.
- **Residual/next**: audit-row integrity does not prove formal B6 review,
  signed-chain semantic completeness beyond this read boundary, clinical
  correctness, provider output, browser usability, C14 activation or
  commercial release. Continue with a bounded structural P7/P8/P9 source-only
  gap; keep runtime gates closed.
