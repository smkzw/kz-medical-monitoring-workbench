# Codex Review: medical_monitoring_phase_c5_projection_read_model_20260802

Date: 2026-08-02 01:06 CST
Execution: Codex direct; no Hermes route, conference, or sub-agent was used.

Changed source/test:
- `services/api/app/monitoring_clinical_projection_contract.py`
- `tests/test_monitoring_clinical_projection_contract.py`

## Verdict

Pass for the offline read-only projection/read-model contract. It is not UI/API
integration, real-project onboarding, risk authority migration, or a commercial
release decision.

## Boundary Check

- The implementation consumes only validated C4 events and explicit projection
  scope/context classifications. It does not parse listings, infer medical links,
  run CTCAE/risk rules, call adapters, write a database or start a service.
- `main.py`, existing adapters, frontend, runtime database, services and
  medical-writing files were not changed. Ports 8911/5174 remain stopped and
  unrelated 18911/PID 43191 was not touched.
- The three requested skills were used as requirements: source-grounded mapping,
  explicit population/USV scope, date/visit fidelity, evidence handoff, and
  rendered views as projections rather than a second fact source.

## Codex Verification

- `MonitoringClinicalProjectionScope` binds project/trial, all-subjects versus
  randomized-only versus allowlist scope, site filters and explicit USV inclusion.
- `MonitoringClinicalProjectionContext` binds source-derived population and
  planned/unplanned visit classification to the exact C4 event hash and declared
  evidence IDs; unknown classifications cannot be silently used to exclude data.
- Timeline projections retain event hash, source date precision/raw date, visit,
  evidence IDs/locators, rule IDs/thresholds, risk IDs, completeness and
  uncertainty. Observation projections retain raw/normalized values, unit/range,
  event hash, evidence locators, rule IDs, missingness and uncertainty.
- AE, LAB, VITALS and ECG observation cards are explicit domain projections;
  other domains remain in Timeline and are not silently treated as safety cards.
- Subject profiles and site/project rollups conserve unique event, observation and
  risk identities; duplicate event contexts, observation reuse, subject/site
  drift, mixed project/trial identities and tampered hashes fail closed.
- C5 focused tests: **12 passed**.
- C1-C5 contracts plus mapping semantic-quality regressions: **143 passed**.
- `python3 -m py_compile` and `python3 -m ruff check` passed for the C5 source/test.
- No browser/PPT/PDF/live authority check was applicable; no service, database,
  adapter or real-project run occurred.

## Delegated-Agent Output Review

- No delegated output exists because the user required Codex direct execution.
  Source and tests were reviewed against C4, C1-C3, B7 projection boundaries and
  the three skill contracts.
- The read model contains no generated clinical title, inferred relationship,
  guessed baseline, CTCAE grade or risk severity. It carries source-derived IDs
  and values forward for future UI consumers.
- Progressive disclosure remains a consumer concern for C6/UI wiring; this slice
  supplies the evidence-rich projection needed to implement it without creating a
  parallel fact source.

## Residual Risk

- C5 does not prove that RUX/MY009/MG-K10 adapters can populate every context,
  population classification, visit classification, baseline, unit or evidence
  field. C3 remains review-only and B6/B4 authority blockers remain open.
- Real Timeline/Profile/AE/lab/vitals/ECG UI, project/site/subject charts, risk
  authority linkage, API versioning, browser acceptance and performance are still
  pending. No dual-read, migration, write path or real-project canary is allowed
  from this slice.
- Next safe action: C6 offline consumer contract/fixture matrix or, after an
  explicit B6 outcome, a separately authorized read-only adapter fixture; preserve
  this evidence before any runtime work.
