# Codex Review: medical_monitoring_my008_3_01_crosswalk_revalidation_20260803

Date: 2026-08-03 CST
Delegated-agent output: `runs/codex_medical_monitoring_my008_3_01_crosswalk_revalidation_20260803.md`

## Verdict

**PASS for the bounded read-only crosswalk evidence; controlled onboarding remains
blocked/review-required.**

## Boundary Check

- This was a direct Codex route under Hermes, not a delegated external run.
- Only the task-scoped context, review, metrics, task record, test evidence and
  persisted diagnostic JSON were added. No product runtime, provider, service,
  browser, database, source registry or medical-writing path was changed.
- The source files were read-only and their current bytes/SHA-256 were recorded.

## Codex Verification

- Current listing replay: 57 sheets, 27,474 rows, zero parser warnings; 16 form-set
  OID groups with all raw date-labelled names retained in the artifact.
- Current V1.1 protocol replay: `docx:table:15`, 14 required visits V1–V14.
- Focused crosswalk/precheck tests: **13 passed in 0.06s**.
- Artifact reconstruction and `validate_visit_crosswalk()` replay were exact:
  `review_required`, 14 `derived_binding_review` findings; report SHA
  `feda574f808e72a809518128adba5fd020391e48c528ecdfe4db7db77d0a4949`; artifact SHA
  `b324b822512a4240b215a05fc619310e3dc878a6dd1d9d353fd288a33f02f8df`.
- A second deterministic normalization pass found one real anomaly outside the
  crosswalk contract: three V2 rows have raw name `筛选期 V2` without a date. It is
  persisted as `scheduled_form_set_date_missing`, not silently normalized.
- No browser, provider, runtime, API login or clinical/UAT check was appropriate:
  this slice intentionally stops before those authority-dependent gates.

## Delegated-Agent Output Review

Not applicable. The direct work preserved evidence versus inference: raw names are
not claimed to equal protocol labels; normalization is explicitly `derived` and
review-required. COM and UNS remain non-scheduled/special rows. No OID or endpoint
semantics were inferred.

## Residual Risk

Human/source-backed review is still required for date-bearing form-set label
normalization, the three undated V2 rows, and V14/early-withdrawal semantics before
any candidate admission.
This artifact does not prove adapter completeness, source approval, medical
correctness, real AI behavior, browser usability, or commercial readiness; B6/C14
and the canonical three-project real-loop gates remain unchanged and blocked.

## Source-level clarification (2026-08-03)

Raw OOXML recheck found no D70/D98 labels in the V1.1 listing and confirmed the
V10/D112 and V12/D140 variants. This candidate therefore has no additional
MY008-3-02-style missing V10/D70 or V12/D98 scheduled-visit issue; the existing
14 derived bindings remain review-required and no authority changed.
