# Task Context: monitoring_mapping_contract_v14_20260730

Created: 2026-07-30 08:31:41
Objective: Repair generalized medical monitoring field-mapping prompt and deterministic semantic gates for treatment identity, dose ambiguity, scale totals, and IP change capability claims without touching runtime databases
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `context/monitoring_p10_mgk10_v13_scientific_audit_20260730.md`
- `context/monitoring_p10_v13_ip_cm_coding_semantic_review_20260730.md`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_mapping_contract.py`
- `services/api/app/monitoring_mapping_semantic_quality.py`
- `services/api/app/monitoring_ai_field_profiler.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_mapping_semantic_quality.py`
- Adjacent field-mapping tests discovered through `rg`.

## Scope

- In scope:
  - Upgrade the listing field-mapping prompt contract so pre-upgrade candidates
    are superseded by the normal job-contract lifecycle.
  - Expose deterministic form/page-name metadata as read-only domain context to
    the product independent AI without allowing it to emit mappings for those
    system-owned fields.
  - Require source-bounded treatment-object identity and conservative neutral
    treatment mapping when identity cannot be established.
  - Keep planned, prescribed, administered, dispensed, returned and
    duplicate/derived dose semantics separate; unresolved dose meaning must be
    visible and actionable.
  - Prevent score/total fields in questionnaire or disease-scale context from
    being classified as procedure/record numbers merely because they are numeric.
  - Add a deterministic capability limitation when the listing cannot
    independently reconstruct dose adjustment, interruption, restart,
    discontinuation and other investigational-product changes.
  - Add project-neutral synthetic tests covering multiple non-oncology study
    styles: background treatment, investigational product, placebo/active
    comparator, topical/inhaled products, disease scales and ambiguous doses.
  - Produce compact `context/`, `runs/`, `reviews/`, and `metrics/` records.
- Out of scope:
  - `monitoring_ai_router.py` and `tests/test_monitoring_ai_api.py`.
  - Protocol preparation, rule publication, daily-run/risk execution, frontend,
    medical writing, runtime selectors, and any real runtime database.
  - Starting port 8911, accepting/rejecting real candidates, assembling or
    activating real mappings.
  - Project-specific field-name hard coding or silently inferring absence of an
    event from absence of a listing field.

## Success Criteria

- A domain named `EX` or similar cannot by itself establish an
  investigational-product identity.
- Background, concomitant or rescue-treatment evidence cannot be promoted to
  an IP role. If object identity remains unknown, the persisted candidate uses
  a neutral treatment role and auditable unresolved identity plus specific
  `uncertainty` and `user_action`.
- Ambiguous planned/actual/duplicate dose evidence cannot silently produce one
  specific dose role.
- Scale totals/scores remain source-collected scale semantics unless a separately
  validated deterministic derivation exists; numeric shape alone cannot make
  them procedure identifiers.
- The mapping quality report explicitly limits IP change-lifecycle capability
  unless distinct, source-backed action families are available. It must never
  interpret missing fields as evidence that no change occurred.
- Prompt, service, quality, and synthetic regression tests pass. Ruff
  `E4/E7/E9/F` and `py_compile` pass for touched Python files.
- No forbidden file or runtime database changes occur.

## Risk Boundaries

- Direct writes are authorized only for the in-scope source, dedicated tests,
  and task records listed above in this shared workbench.
- Never write to runtime SQLite databases or start the backend service.
- Preserve CM as non-investigational medication/treatment only.
- Keep administration, dose adjustment, interruption, restart, discontinuation,
  dispensing, return, compliance and other IP changes as separate action families.
- Do not introduce MG-K10, RUX, MY009, or any specific source-field identifier
  into production decision logic.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-30 08:31:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-30 08:42: Source audits and current contracts inspected. Current
  product-AI payload drops deterministic `FORMNM`/page-name fields entirely,
  removing decisive background-treatment context. Implementation must restore
  that context read-only and add deterministic conservative post-validation.
- 2026-07-30: Delegated aishuo runner was formally rejected because no usable
  accepted result was established. A Kimi fallback could not establish a child
  session because the shared process lock remained occupied; it was stopped
  without creating a new model session. Per user correction, Codex completed
  the same task directly. Runner acceptance remains `false`.
- 2026-07-30: Effective product prompt upgraded from v14 to
  `monitoring-listing-field-mapping-v15`; normal business-key supersession makes
  older candidates stale.
- 2026-07-30: Added bounded/redacted read-only form/page context with actual
  representative/top values and exact profile/domain/field identity. The
  context survives domain chunking but is removed from required output.
- 2026-07-30: Added machine-checkable object identity, same-domain evidence,
  explicit cross-domain binding, dose semantics and system quality-gate actions.
  The deterministic post gate neutralizes background/concomitant/rescue
  treatment and unresolved EX-like administration rather than trusting a domain
  name or a dose field that self-attests IP identity.
- 2026-07-30: G-CMIP-005 is domain-scoped. Cross-domain release requires a
  validated subject-level treatment binding. A separate true IP domain cannot
  release a background-treatment domain.
- 2026-07-30: G-SCALE-002 now requires at least two scale-item siblings plus a
  total/score-like source name or a strong shared item prefix, and is a global
  blocker. Strong matches are rejected before draft assembly and therefore
  cannot reach confirmation or activation. A distinct legitimate procedure
  number remains allowed.
- 2026-07-30: IP change lifecycle now requires separate dose adjustment,
  interruption, restart, discontinuation and other-change families. Missing
  fields mean unavailable capability, never evidence of no event.
- 2026-07-30: Verification passed: 213 focused tests, 75 adjacent mapping tests,
  Ruff E4/E7/E9/F and Python compilation. Frozen router/API-test hashes remain
  unchanged. No service or port 8911 was started and no runtime database was
  touched.
