# Task Context: medical_monitoring_phase_c8_adapter_consumer_coverage_20260802

Created: 2026-08-02 01:35:39
Objective: Create and verify a review-only adapter source-to-consumer coverage matrix over the existing C3 inventory without activating mappings or touching runtime
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_adapter_mapping_plan.py` and
  `runs/execution/medical_monitoring_phase_c3_mapping_inventory_20260802/OBSERVED_ADAPTER_MAPPING_INVENTORY.json`
  (46 review-only source-surface observations)
- `services/api/app/monitoring_clinical_event_contract.py`,
  `monitoring_clinical_projection_contract.py`,
  `monitoring_clinical_consumer_handoff.py` and the C7 frontend fixture contract
- The three named skill contracts already read this turn: subject timeline
  builder, clinical patient profile HTML and AE risk assessment
- Current filesystem is authoritative. C3 inventory is evidence of observed
  adapter code surfaces only; it is not a medical-approved mapping or live data.

## Scope

- In scope: a pure coverage contract that translates each C3 review-only
  observation into explicit C4 event/C5 projection/C6 handoff/C7 consumer
  surfaces and required source-bound fields. A derived 46-observation JSON
  matrix may be generated under this task's execution evidence path.
- Out of scope: source listing/protocol parsing, adapter invocation, mapping
  activation, registry/API/runtime writes, clinical adjudication, CTCAE/risk
  calculation, React/UI changes, browser checks, real-project data and service
  startup.

## Success Criteria

- Every C3 observation appears exactly once in the coverage plan, retains its
  project/adapter/trial/source sheet/field/evidence locator and remains
  `observed_requires_medical_review`.
- Domain policy explicitly covers Timeline and Profile; AE/LAB/VITALS/ECG may
  additionally expose a safety metric surface; risk remains
  `explicit_risk_instance_id_only`; unsupported domains or overclaims fail closed.
- Required event/observation fields include source identity, dates/visit,
  evidence, value/missingness, rules, completeness and uncertainty; the plan
  has deterministic hash and `activation_allowed=false`.
- The actual C3 inventory produces 46 coverage observations across RUX, MY009
  and MG-K10 with no source invocation or runtime mutation.

## Risk Boundaries

- Generated artifacts are limited to this task's execution evidence path; no
  production/runtime/registry writes are allowed.
- Codex is the implementation, review and acceptance authority; no delegated
  agent, Hermes route or conference is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 01:35:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 01:36: direct task contract filled; coverage will consume only the
  existing C3 JSON inventory and C3 typed observations, never real listings.
- 2026-08-02 01:44: added `services/api/app/monitoring_adapter_consumer_coverage.py`
  and focused tests. It normalizes observed source domains (including explicit
  `SOURCE`/`BACKGROUND_TREATMENT`→`OTHER` with the original label retained) and
  assigns only explicit Timeline/Profile/safety-metric/risk-link surfaces. The
  risk policy is fixed at `explicit_risk_instance_id_only`; `activation_allowed`
  is always false; required event/observation fields include identity, dates,
  visit, evidence, value/missingness, rules, completeness and uncertainty.
- 2026-08-02 01:44: generated
  `runs/execution/medical_monitoring_phase_c8_adapter_consumer_coverage_20260802/ADAPTER_CONSUMER_COVERAGE_MATRIX.json`
  from the existing C3 inventory. All **46 observations** (RUX 11, MY009 18,
  MG-K10 17) were reproduced with matching C3 plan hashes; matrix hash is
  `ce7dd80adc1806ef9ffaf22dd1a1f8a5f63e571125aa93e6d4c5c76e1714983d`, and
  activation remains false. Focused C8 **4 passed**; C1-C8 contract suite
  **65 passed**; pycompile/Ruff and matrix generation passed. No adapter,
  source listing, service, browser, runtime write or real-project run occurred.
