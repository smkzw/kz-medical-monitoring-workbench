# Task Context: medical_monitoring_phase_c4_clinical_event_contract_20260802

Created: 2026-08-02 00:39:34
Objective: Define and test a shared project-neutral clinical event and observation contract linking source rows, dates, visits, raw values, treatment identities, risk evidence, rule bindings, completeness and uncertainty without runtime integration
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `packages/contracts/workbench_contracts/models.py` Timeline/Profile model shapes
- `services/api/app/monitoring_ai_risk_packet.py` source/evidence identity boundaries
- `services/api/app/monitoring_source_fragment.py` locator conventions
- C1/C2/C3 contracts:
  `services/api/app/monitoring_study_config.py`,
  `services/api/app/monitoring_study_adapter_contract.py`,
  `services/api/app/monitoring_adapter_mapping_plan.py`
- `reviews/medical_monitoring_system_retro_roadmap_20260801.md` Phase C and shared
  Timeline/Profile/AE/observation requirements
- Current filesystem is authoritative; runtime data and services are out of scope.

## Scope

- In scope: a pure `MonitoringClinicalEvent` / `MonitoringClinicalObservation`
  contract with source-row identity, partial dates/visits, raw values/units/ranges,
  explicit AE/MH/CM/IP/Finding/PD/risk links, evidence/rule bindings, completeness,
  uncertainty, deterministic serialization/hash and focused tests.
- Out of scope: adapter invocation, real listing/protocol reads, API/frontend wiring,
  runtime database writes, migration, AI calls, browser/service execution and
  medical-writing changes.

## Success Criteria

- Project/trial/site/subject and source revision/row identity are explicit and validated.
- Dates/precision, raw values/units/ranges, visits and treatment/clinical links remain
  separate fields; no free-text link inference is possible.
- Evidence locators and rule/threshold bindings are explicit and cannot be local paths.
- Partial/missing completeness and uncertainty are visible and fail closed when malformed.
- Event/observation hashes are deterministic and round-trip preserves the contract.
- Focused/relevant tests, pycompile, Ruff and review gate pass without runtime writes.

## Risk Boundaries

- Codex direct only; no Hermes route, conference or sub-agent.
- This is a shared data contract, not a runtime event store or clinical adjudication result.
- Preserve `main.py`, adapters, frontend, medical-writing files and runtime data unchanged.
- Codex owns final verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 00:39:34: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 00:40: Direct task contract filled; implementation will remain a pure
  event/observation serialization boundary with no runtime integration.
- 2026-08-02 00:41-00:49: Added
  `services/api/app/monitoring_clinical_event_contract.py` and
  `tests/test_monitoring_clinical_event_contract.py`. The contract now keeps
  project/trial/site/subject and source-row identity separate from dates, values,
  visits, clinical/treatment/risk links, evidence and rule bindings; it rejects
  local-path locators, CM/IP cross-links, undeclared nested references and
  malformed completeness/uncertainty. Partial date precision, real calendar-date
  validation, numeric zero values, canonical JSON snapshots, deterministic event
  SHA-256 and round-trip reconstruction are covered. No parser, inference,
  persistence, adapter call or runtime integration was added.
- Verification: C4 focused tests **18 passed**; C1-C4 contract tests plus mapping
  semantic-quality regressions **131 passed**; pycompile and Ruff passed. Source
  hash `038149cbfc30e835c6e1792e6b74d6bead816120e40adaf3465f7c33216815f8`;
  test hash `b2ec5fe04757afaae5d23c9a0d500a3e80615ef6e79817ef7ba1d69409aaaf96`.
  `review-gate --require-verification` passed with no warnings/errors. 8911/5174
  remain stopped; no database, browser, adapter or real-project run.
