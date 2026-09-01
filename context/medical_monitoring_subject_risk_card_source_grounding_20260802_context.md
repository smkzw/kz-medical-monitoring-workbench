# Task Context: medical_monitoring_subject_risk_card_source_grounding_20260802

Created: 2026-08-02 09:48:46
Objective: Remove unsupported hardcoded safety assertions from subject risk cards while preserving source-grounded AE, laboratory, prompt, locator, and uncertainty evidence
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.mjs`:
  `referenceRiskCards()` is the presentation model for the subject-level risk
  cards and currently contains a hardcoded `说明书/IB：感染/实验室风险`
  assertion.
- `frontend/src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`:
  source-derived AE/laboratory/prompt fixture and regression coverage.
- The read-only requirements baseline from the named
  `subject-timeline-builder`, `clinical-patient-profile-html`, and
  `ae-risk-assessment` skills: no inferred project-specific safety topic;
  retain source event fields, explicit evidence, uncertainty, and locators.
- Existing frontend consumer/model contracts and the P10/B6/C13 evidence
  records define the boundary: this slice is presentation-only and cannot
  grant monitoring authority or runtime activation.

## Scope

- In scope: remove the unsupported hardcoded safety topic from
  `referenceRiskCards`; build the AE card from fields explicitly present in
  the AE event, linked laboratory event, and AE/lab prompt; preserve event
  relationship/status/date, source identifiers/locators, supplied safety
  references, and a neutral review-needed fallback; add focused source-
  grounding regressions and task evidence.
- Out of scope: API/backend/SQLite/source registry, risk-rule semantics, CTCAE
  thresholds, protocol/IB interpretation, App.jsx, styles.css, runtime/browser,
  providers, 8911/5174, B6/C13/C14, real projects, and the parallel
  medical-writing lane.

## Success Criteria

- With the existing fixture, the AE card contains the supplied AE/prompt
  content and no `说明书/IB` or `感染/实验室风险` text.
- An explicit supplied safety reference is rendered only when present; no
  safety topic is inferred from an AE title or laboratory domain.
- Missing or malformed optional fields remain safe and concise.
- Focused Node tests and the existing medical-monitoring contract suite pass;
  no protected runtime/source boundary changes.

## Risk Boundaries

- Do not edit `frontend/src/App.jsx` or `frontend/src/styles.css`, both of
  which remain parallel/Kimi candidate surfaces.
- Do not start 8911/5174 or any service/provider/browser; do not touch SQLite,
  B6/C13/C14, real-project data, or medical-writing files.
- Do not introduce a new clinical rule, label, CTCAE interpretation, or
  implicit source mapping. Use only explicit event/prompt fields and neutral
  fallback language.
- The delegated route is not final authority; Codex owns verification and
  acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 09:48:46: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 09:53 CST: Replaced the unsupported hardcoded AE safety phrase
  with source-derived AE/prompt/locator/evidence assembly. Explicit AE-to-lab
  linkage is required; same-visit coincidence is not enough. Focused model,
  all 22 medical-monitoring Node files, Python frontend contracts (61), and
  Vite build (1925 modules) passed. Review-gate remains to be recorded. No
  runtime/API/provider/browser/SQLite/B6/C13/medical-writing surface changed.
- 2026-08-02 09:56 CST: Tightened the same source-grounding slice so empty
  CM/PD branches say evidence is unavailable rather than implying a current
  rule hit. Re-ran Node 22 files, Python 61 contracts, and Vite build; all
  passed. Review-gate evidence remains PASS.
