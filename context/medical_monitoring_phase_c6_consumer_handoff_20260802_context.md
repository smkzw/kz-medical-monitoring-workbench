# Task Context: medical_monitoring_phase_c6_consumer_handoff_20260802

Created: 2026-08-02 01:08:48
Objective: Define and test a source-preserving consumer handoff from the C5 clinical read model to Timeline, Patient Profile, safety observation metrics and risk drilldown consumers without frontend/runtime integration
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_clinical_event_contract.py` (C4 event/observation)
- `services/api/app/monitoring_clinical_projection_contract.py` (C5 read model)
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`
  and `MedicalMonitoringSubjectViews.jsx` (existing consumer field/lane shapes)
- `frontend/src/features/medical-monitoring/medicalMonitoringRiskProjection.mjs`
  (B7 risk drilldown/progressive disclosure expectations)
- The three skill contracts already read in this turn: subject timeline builder,
  patient profile HTML and AE risk assessment
- Current filesystem is authoritative; no real listing, browser, service,
  runtime database, adapter invocation or product AI output is in scope.

## Scope

- In scope: a pure source-preserving handoff from a C5 read model to consumer
  records for Timeline, Patient Profile, safety observation metrics and risk
  drilldown. It must preserve event/observation/risk IDs, date precision/raw date,
  visit/USV state, raw and normalized values, units/ranges, evidence locators,
  rule bindings, completeness/uncertainty and project/site/subject rollup IDs.
- Out of scope: React/UI edits, API/router wiring, HTML generation, source parsing,
  CTCAE/risk adjudication, baseline inference, adapter invocation, persistence,
  migration, runtime services and real-project data.

## Success Criteria

- One C5 read model produces all consumer records; no consumer record invents a
  clinical fact or becomes a second source of truth.
- Timeline events keep planned/unplanned state and evidence locators; profile
  catalog and metric points remain traceable to event/observation IDs; risk links
  remain explicit IDs rather than severity heuristics.
- Safety metrics are emitted only for explicit AE/LAB/VITALS/ECG observations;
  missing or unsupported domains are represented as unavailable/empty, not guessed.
- Project/site/subject conservation survives handoff; duplicate IDs, mixed study
  identity, missing source trace and malformed scope fail closed.
- Deterministic serialization/hash and focused/relevant tests, pycompile, Ruff and
  review gate pass without frontend/runtime changes.

## Risk Boundaries

- Do not write to production/runtime paths; this slice is limited to the
  source-preserving contract and its tests.
- Codex is the implementation, review and acceptance authority; no delegated
  agent, Hermes route or conference was used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 01:08:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 01:09: direct task contract filled; Codex direct only; handoff will
  consume C5 output and mirror the existing frontend consumer shapes without
  changing them.
- 2026-08-02 01:19: C6 implementation and focused tests completed. The handoff
  emits Timeline records, explicit AE/LAB/VITALS/ECG safety metrics, subject
  consumer records, risk drilldown records and existing site/project rollups
  from one C5 model. Event/observation hashes, dates, visit/USV state, raw and
  normalized values, ranges, evidence ID→locator alignment, rule IDs,
  completeness and uncertainty are retained; risk links remain explicit and
  no free-text risk is created.
- 2026-08-02 01:19: A hardening pass added fail-closed project/trial identity
  checks, event-type/domain checks, metric identity checks, evidence alignment
  conflict detection and deterministic handoff hashing. A focused regression
  caught and fixed unordered risk locators so evidence IDs remain paired with
  their original locators.
- 2026-08-02 01:19: C6 focused **6 passed**; C1-C6 contract files **61 passed**;
  pycompile and Ruff passed. No service, adapter, frontend, browser, runtime
  database, source listing or product-AI invocation occurred. Next safe slice is
  C7 offline consumer fixture/adapter handoff and frontend contract review;
  B6 reviewer outcome and all runtime/real-project gates remain pending.
