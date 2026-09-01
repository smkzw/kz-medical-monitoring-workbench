# Task Context: medical_monitoring_phase_c7_frontend_consumer_contract_20260802

Created: 2026-08-02 01:24:57
Objective: Define and test a source-preserving C6 consumer handoff fixture contract for existing Timeline/Profile/risk frontend consumers without UI, API, runtime or real-project integration
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_clinical_consumer_handoff.py` and its C6 tests
  (source-preserving handoff contract)
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
  and `medicalMonitoringRiskProjection.mjs` (existing Timeline/Profile/risk
  consumer vocabulary and read-only projection expectations)
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`
  and `medicalMonitoringRiskProjection.test.mjs` (existing fixture/test style)
- The three named skill contracts already read this turn: subject timeline
  builder, clinical patient profile HTML and AE risk assessment
- Current filesystem is authoritative. No real listing, browser, service,
  runtime database, adapter invocation or product-AI output is in scope.

## Scope

- In scope: a pure frontend-facing fixture/contract adapter for a serialized C6
  handoff. It may validate canonical snake_case handoff fields and expose raw
  Timeline/Profile/safety metric/risk-link records in the field vocabulary used
  by the existing frontend, while retaining every source locator and explicit
  limitation.
- Out of scope: React/App edits, CSS, API/router wiring, HTML generation,
  source parsing, severity/CTCAE/baseline inference, canonical risk authority
  rows, persistence, migration, runtime services and real-project data.

## Success Criteria

- One validated C6 payload produces deterministic subject/profile fixtures and
  an explicit risk-link fixture without inventing risk severity, status,
  normality, baseline, study day or clinical interpretation.
- Timeline preserves event IDs/hashes, frontend event types, source-domain
  labels, date precision/raw dates, visit/USV, explicit risk IDs, evidence
  IDs/locators and rule/completeness/uncertainty fields.
- Safety metric points preserve raw/normalized values, unit/range, assessment
  date/precision, visit, evidence/rule IDs and explicit limitations; unsupported
  domains remain unavailable rather than becoming guessed metrics.
- Subject/site/project identity, evidence ID→locator alignment, duplicate IDs,
  mixed projects and tampered fixture hashes fail closed. Round-trip and
  focused Node tests pass without changing existing frontend consumers.

## Risk Boundaries

- Do not write to production/runtime paths; this slice is a contract/fixture
  boundary only.
- Codex is the implementation, review and acceptance authority; no delegated
  agent, Hermes route or conference is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 01:24:57: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 01:25: direct task contract filled; the adapter will mirror existing
  frontend consumer field names but retain C6 source fields and limitations.
- 2026-08-02 01:31: added pure frontend
  `medicalMonitoringConsumerContract.mjs` plus a fixture test. It validates one
  serialized C6 handoff, maps explicit clinical domains to the existing
  Timeline/Profile source-domain vocabulary, preserves event/observation/risk
  IDs, hashes, dates, visit/USV, raw/normalized values, ranges, evidence
  ID→locator pairs, rule IDs, completeness/uncertainty and limitations, and
  emits raw profile/safety metric/risk-link fixtures. It deliberately does not
  create canonical risk severity/status, normality, baseline, study day,
  clinical interpretation or efficacy data.
- 2026-08-02 01:31: C7 focused Node test **13 passed**; the existing medical
  monitoring frontend sweep of **14 test files** passed (0 failures); module and
  test `node --check` passed. No React/App/CSS/API/runtime/source files were
  changed, no browser/service/adapter/real-project run occurred. Next safe
  slice is C8 only after review gate: read-only adapter fixture matrix and
  explicit source/field coverage, still without runtime registration.
