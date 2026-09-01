# Codex Review: medical_monitoring_subject_link_shape_20260802

Date: 2026-08-02
Mode: direct Codex review; no delegated agent or provider dispatch
Source record: `context/medical_monitoring_subject_link_shape_20260802_context.md`

## Verdict

Pass for this bounded offline slice; not a release, clinical, or runtime acceptance.

## Boundary Check

- Only `medicalMonitoringSubjectModels.mjs`, its Node regression, and task-scoped evidence/release-coverage records changed; `App.jsx`, `styles.css`, API/backend and medical-writing surfaces were not modified.
- No service/provider/browser/API/adapter/real project/B6/C14 authority or migration was used; 8911/5174 remain stopped.

## Codex Verification

- Strict singular AE `event_id` and plural AE/lab relation list helpers now reject non-string or scalar-shape relationship payloads from automatic matching.
- Valid string AE/lab link remains rendered; malformed numeric AE/lab link is not merged and the AE card shows `关联实验室未自动合并` plus a source-review/no-risk warning.
- Subject model regression and all medical-monitoring Node tests: **22/22 files passed**; Subject model assertion count: **67**.
- Focused frontend contracts: **64 passed**; `npm run build` from `frontend/`: Vite **1925 modules transformed**, successful with existing large-chunk warning.
- `PYTHONPATH=. pytest -q tests/test_monitoring_release_gate.py`: **7 passed**; coverage replay is consistent after LOOP 4.19 rebind.
- Release audit SHA `9814bba5f973e0d98dc7e0b315a52324cef988563fd3ff914021667406242cd8`; coverage SHA `e2804caefba10376f8f84dcbd457f868b05be98e18c19c7365158cedd38f85f4`; decision SHA `319249ab0fc045d918e537f25365775de55d429da4087c223412d20b6fc18431`; status `blocked/release_ready=false`, counts `0/12/3/1`.
- Hermes workflow guard `review-gate --require-verification` is the task-record integrity check; no Hermes/provider dispatch occurred.

## Delegated-Agent Output Review

Not applicable. Direct Codex retained final authority; no delegated output exists to review.

## Residual Risk

This is a consumer-layer payload-shape guard, not proof of source bytes, clinical relationship correctness, scientific validity, browser/UAT, B6 reviewer outcome, aggregate/CAS, or commercial release. Numeric/object relationship fields are intentionally withheld from auto-matching; a human must return to the source record. This may reduce automatic enrichment until source payloads are corrected, which is the safe fail-closed behavior.

## Next Safe Action

Maintain B6/C14 fail-closed and 8911/5174 stopped. The authority-dependent path remains formal B6 outcomes → append-only aggregate/CAS replay → MY009 legacy source-token revalidation → approved-input dry-run → controlled runtime/three-project LOOP. Until then, continue only bounded offline review or explicitly authorized consumer-contract fixes.
