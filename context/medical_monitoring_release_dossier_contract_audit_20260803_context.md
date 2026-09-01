# Task Context: medical_monitoring_release_dossier_contract_audit_20260803

Created: 2026-08-03 17:19:41
Objective: 只读审查医学监查 release dossier/release gate 汇总是否把独立AI、B6/CAS/source-token、浏览器科学性、性能与保护面区分清楚，修正可证明的误报缺口
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench release contracts: `services/api/app/monitoring_release_gate.py`,
  `services/api/app/monitoring_release_dossier.py`,
  `services/api/app/monitoring_release_dossier_revalidation.py`,
  `services/api/app/monitoring_release_evidence_revalidation.py` and their focused tests.
- Current release coverage: `records/active_slices/medical_monitoring_release_evidence_coverage_20260802/CURRENT_RELEASE_COVERAGE.json`.
- Current release-evidence revalidation:
  `records/active_slices/medical_monitoring_release_evidence_revalidation_20260803/RELEASE_EVIDENCE_REVALIDATION.json`.
- Current dossier revalidation:
  `records/active_slices/medical_monitoring_release_dossier_revalidation_20260803/RELEASE_DOSSIER_REVALIDATION.json`.
- Upstream B6/C14 bytes: `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
  and `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/B6_TO_C13_ACTIVATION_GATE_REPORT.json`.
- Current filesystem is final truth. No service, provider, browser, API login, real project,
  SQLite, runtime write or medical authority action is in scope for this audit.

## Scope

- In scope: static release-gate/dossier contract review, persisted artifact re-open, focused
  deterministic tests and negative probes; a minimal fail-closed repair where a source path or
  derived decision could otherwise be treated as fresh without cross-field consistency.
- Out of scope: B6 reviewer outcomes, C14 activation, aggregate/CAS replay, source-token
  synthesis, provider/model calls, service startup, Playwright login, real-project ingestion,
  medical confirmation, UAT or release signoff.

## Success Criteria

- Confirm the 16 commercial gates remain explicit and the current snapshot is blocked.
- Confirm a missing persisted dossier remains blocked and non-authoritative.
- Ensure release evidence paths are clean workspace-relative non-symlink paths and that decision
  status, readiness, unmet gates, reasons and B6 projection are derived consistently from the
  hash-bound rows/current B6/C14 snapshot.
- Pass the focused release/dossier/AI/nonfunctional regression and re-open the current snapshot
  as fresh evidence with `release_decision_status=blocked`, `release_ready_observed=false`.
- Record the exact residual evidence boundary: freshness is not reviewer approval, runtime
  readiness, browser/scientific acceptance, UAT or commercial release.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep all services and ports 8911/5174/8910/4173 stopped; do not touch real study folders.
- Do not create synthetic release/UAT/B6 outcomes or mutate persisted release/B6/C14 artifacts.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 17:19:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 17:20–17:27: Reopened current release coverage and both revalidation artifacts.
  Coverage revalidation was fresh (six source files and 16 gate rows hash-bound) but the
  decision remained `blocked`, B6 remained `pending_review`, and the dossier revalidation was
  intentionally blocked because no persisted commercial dossier JSON is declared.
- 2026-08-03 17:22: Focused release/dossier/AI/nonfunctional suite passed 53 tests before the
  bounded repair. Static review found that `sources[].path` was not constrained to the workbench
  and the persisted release revalidation did not compare derived decision fields to gate/B6
  inputs.
- 2026-08-03 17:23: Hardened `monitoring_release_evidence_revalidation.py` with clean
  workspace-relative non-symlink source paths, valid gate-status checks, full decision-row
  equality and derived status/readiness/unmet/reason/B6 consistency checks. Added traversal,
  symlink, unknown-status and decision-tamper regressions; no release/B6/C14 artifact was edited.
- 2026-08-03 17:24–17:27: Focused release suite passed 73 tests; current coverage re-opened as
  `fresh`, zero issues, six source matches, 16 gate bindings, `blocked` decision and
  `release_ready_observed=false`. `py_compile` passed; local Ruff binary was unavailable.
- 2026-08-03 17:28: Hermes workflow-guard review gate passed with `ok=true` and no warnings or
  errors.
