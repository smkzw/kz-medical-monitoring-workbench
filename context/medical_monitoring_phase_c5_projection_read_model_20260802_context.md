# Task Context: medical_monitoring_phase_c5_projection_read_model_20260802

Created: 2026-08-02 00:53:30
Objective: Define and test a read-only projection contract over the C4 clinical event/observation contract for concise Timeline, Patient Profile, AE/lab/vitals/ECG and risk views, preserving source evidence, uncertainty, population scope and aggregate conservation without runtime integration
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_clinical_event_contract.py` and
  `tests/test_monitoring_clinical_event_contract.py` (C4 source contract)
- `frontend/src/features/medical-monitoring/medicalMonitoringRiskProjection.mjs`
  and `medical_risk_authority.py` (existing B7 risk-shaped projection and
  authority boundaries)
- `services/api/app/monitoring_source_fragment.py` (source locator conventions)
- `services/api/app/monitoring_study_config.py`,
  `monitoring_study_adapter_contract.py`, and
  `monitoring_adapter_mapping_plan.py` (C1-C3 project/mapping contracts)
- `reviews/medical_monitoring_system_retro_roadmap_20260801.md` and the three
  requested skill contracts: `subject-timeline-builder`,
  `clinical-patient-profile-html`, and `ae-risk-assessment`
- Current filesystem is authoritative; no runtime database, real project listing,
  browser, service or external AI output is in scope.

## Scope

- In scope: a pure read-only projection contract that consumes validated C4 events
  and emits concise subject timeline entries, subject profile summaries, AE/lab/
  vitals/ECG observation cards and project/site/subject risk rollups. Every
  projection must retain event/evidence/rule identities, source locators, date
  precision, completeness and uncertainty; aggregate counts must conserve unique
  `event_id`/`risk_instance_id` identities; population and USV scope are explicit.
- Out of scope: source parsing, rule/CTCAE adjudication, event inference,
  adapter invocation, API/frontend wiring, persistence, migration, real listings,
  browser/service execution, AI calls and medical conclusions.

## Success Criteria

- Timeline/profile/observation/risk views are separate projections over one event
  contract; no projection becomes a second source of truth.
- Concise display fields are deterministic and preserve raw evidence locators,
  rule bindings, date precision, missingness and uncertainty.
- Project/site/subject rollups conserve unique event and risk identities; filters
  cannot silently change population scope or include/exclude USV.
- AE/lab/vitals/ECG categories remain explicit, and risk links are IDs only.
- Malformed events, duplicate identity, inconsistent scope and hash tampering fail
  closed; serialization is deterministic and round-trippable.
- Focused/relevant tests, pycompile, Ruff and `review-gate --require-verification`
  pass without runtime writes or service starts.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 00:53:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 00:54: direct task contract filled; Codex direct only, with C4 as the
  sole event source and the three skill contracts used as projection requirements.
- 2026-08-02 00:55-01:06: Added
  `services/api/app/monitoring_clinical_projection_contract.py` and
  `tests/test_monitoring_clinical_projection_contract.py`. The read-only model
  binds source-derived population membership and planned/unplanned visit status
  to each C4 event; emits deterministic Timeline and AE/lab/vitals/ECG
  observations, subject profiles and site/project rollups; retains event hashes,
  evidence IDs/locators, rule/threshold bindings, completeness and uncertainty;
  and rejects mixed studies, duplicate identity, scope ambiguity, unbound
  classification evidence and tampered payloads. No parser, inference, API,
  frontend, database or runtime integration was added.
- Verification: C5 focused **12 passed**; C1-C5 contracts plus mapping
  semantic-quality regressions **143 passed**; pycompile and Ruff passed. Source
  hash `be40f2538c9474d15091bbd61b7e7a8ee58c6b4120300a31302a6ab48b6d1579`;
  test hash `cb971ba8dd9ad2fe9b438574aab8403f0cadaa7fb1e1f0c161adecf973b72760`.
