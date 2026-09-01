# Task Context: medical_monitoring_protocol_evidence_bool_20260803

Created: 2026-08-03 10:50:27
Objective: Harden protocol-preparation evidence primary-match and eligibility Boolean boundaries with deterministic regressions while keeping B6/C14, providers, browser, services, and real projects stopped.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench source under `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Primary module: `services/api/app/monitoring_protocol_preparation_service.py`.
- Primary regression: `tests/test_monitoring_protocol_preparation.py`.
- P10 authority: `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md` and
  `REQUIREMENTS_TRACEABILITY.md`.
- Gate authority: B6 `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
  is `pending_review`; C14 `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/B6_TO_C13_ACTIVATION_GATE_REPORT.json`
  is `blocked_pending_b6_review`.

## Scope

- In scope: strict runtime Boolean validation for the protocol-preparation
  evidence-context fields `primary_match` and `eligible_for_rule_fact`; preserve
  intentional missing-field defaults; add deterministic malformed-value regressions;
  run focused, adjacent, full monitoring tests and static checks; record evidence.
- Out of scope: B6 reviewer outcomes, C14 activation, CAS/source-token writes,
  provider calls, browser/API login, service starts, real-project data, schema or
  migration work, frontend changes, medical conclusions, and broad unrelated flag
  audits.

## Success Criteria

- A persisted or AI-supplied truthy string/number cannot qualify a protocol span as
  a primary eligible rule-fact evidence span.
- Actual Booleans keep existing behavior; absent `primary_match` remains fail-closed
  in the eligibility predicate while absent `eligible_for_rule_fact` preserves the
  existing intentional default of `True`.
- Malformed evidence flags raise the existing preparation-domain error before a
  packet or AI job can be admitted; synthetic tests cover both flags and valid paths.
- Focused and adjacent protocol tests, the full `tests/test_monitoring*.py` suite,
  Ruff check and compile pass without formatter churn.
- Review record and metrics pass the Hermes workflow review-gate; P10 ledger and
  traceability receive a compact 4.88 entry.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- No B6 outcome may be created or inferred; all activation/event/projection/write
  flags remain false. Keep 8911/5174 stopped and leave unrelated port 8900 untouched.
- Synthetic temporary fixtures are allowed only for deterministic contract tests;
  no provider, browser, API, SQLite/CAS project operation or real-project data.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 10:50:27: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Audited the sole remaining direct `bool(...)` flag bridge in protocol
  preparation. `_has_eligible_primary_match` currently coerces `"false"` to true;
  `_with_default_evidence_context` intentionally defaults missing `primary_match`
  to true and topic gating sets `eligible_for_rule_fact` to explicit Booleans.
- 2026-08-03: Added `_strict_evidence_bool`, validated both evidence-context
  fields before topic gating, and added four malformed string/integer regressions.
- 2026-08-03: Focused 5/44 passed; adjacent 524 passed; full monitoring suite
  1813 passed with 25 warnings in 476.20s. Ruff check and compile passed;
  formatter baseline was preserved. Review-gate is the next record action.
