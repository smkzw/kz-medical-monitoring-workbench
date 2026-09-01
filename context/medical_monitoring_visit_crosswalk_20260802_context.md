# Task Context: medical_monitoring_visit_crosswalk_20260802

Created: 2026-08-02 09:26:06
Objective: Add a pure fail-closed protocol-to-listing visit crosswalk contract and tests for treatment-specific, ordinal-conflict, unplanned, withdrawal, and non-visit handling without runtime activation
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_listing_precheck.py` and its tests: the
  existing pure mapping precheck and activation=false invariant.
- Canonical MY008 3-02 listing:
  `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-02（MM外包）/原始数据/【3-02初治锁库后数据集】MY008211A-PNH-3-02-锁库后EXCEL数据集.xlsx`
  (SHA `152b8c2eb4d398ca2cfd861ee7932942eb753d6494ae7c93a5806734d5ced106`).
- MY008 3-02 protocol:
  `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-02（MM外包）/方案/2.1版方案/MY008211A-PNH-3-02_研究方案_V2.1_2024.11.08-clean.docx`
  (SHA `562af73b1a7dda045a42540947e810a1c6026cfee53c6205fc4c304037345e90`).
- `records/active_slices/medical_monitoring_my008_mapping_review_20260802/`
  and the current P10 release-gate audit: record-level `VISIT`/`VISTOID`
  exists, but protocol D70/D98 and V17/withdrawal do not align with listing
  ordinal IDs; the canonical/alternate source copies must not be merged.
- `subject-timeline-builder`, `clinical-patient-profile-html`, and
  `ae-risk-assessment` skill contracts already read in the parent task: source
  locators and uncertainty are preserved; no profile or AE risk output is built
  from an unresolved crosswalk.

## Scope

- In scope: a new offline module and focused tests for observed listing visit
  identity pairs and explicit protocol crosswalk bindings; deterministic
  validation of duplicate/missing/ambiguous/conflicting bindings, treatment-arm
  applicability, non-visit/common rows, unplanned rows, withdrawal rows, source
  hashes, and stable report/input hashes; a task record/review/metrics update.
- Out of scope: source registry, onboarding, SQLite/API/runtime writes, risk or
  clinical events, provider calls, browser work, activation/B6/C13 changes,
  changing App.jsx, or reading the alternate listing into the canonical baseline.

## Success Criteria

- A mapping report is immutable/hashable, order-independent, and always
  `activation_allowed=false`.
- Any required protocol visit without an evidence-backed observed binding,
  arm mismatch, duplicate/conflicting binding, or unclassified observed visit
  fails closed; non-visit/common and explicitly unplanned/withdrawal records are
  represented without being silently treated as scheduled visits.
- Listing OID ordinal mismatch is surfaced as a review/blocking finding rather
  than silently normalized.
- Focused tests and relevant mapping/precheck regression pass; py_compile and
  Ruff pass; no runtime or parallel medical-writing files are changed.

## Risk Boundaries

- This is offline contract work only. Do not create or modify sources, registry,
  SQLite, B6/C13/C14, API routes, provider state, runtime processes, frontend
  App.jsx, or medical-writing files.
- Preserve raw source locators and exact source hashes; do not include subject
  identifiers or cell values in durable artifacts.
- The module must never grant activation, migration, write, medical approval, or
  source acceptance permission.
- No subagent or Hermes dispatch; Codex owns implementation, verification, and
  acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 09:26:06: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 09:27:00: Source of truth and boundaries filled; implementation will
  be isolated to the new crosswalk module, focused tests, and task-owned records.
- 2026-08-02 09:34:00: Added the pure `monitoring_visit_crosswalk` contract and
  focused regressions. The first test run exposed only a test-helper object-vs-
  mapping mistake (`4 failed, 4 passed`); the helper was corrected without
  changing production logic. Focused rerun is `8 passed`; pycompile, Ruff
  format/check, and adjacent precheck/B6/C13/source-token regression are all
  clean (`44 passed`). No runtime, API, SQLite, provider, frontend, B6/C13,
  service, browser, real-project, or medical-writing surface was touched.
- 2026-08-02 09:36:00: Codex review accepted the slice as offline-only. The
  report always carries `activation_allowed=false`; the current B6
  `pending_review` gate and C13/C14 blocked state remain unchanged. Durable
  evidence is in
  `records/active_slices/medical_monitoring_visit_crosswalk_20260802/`.
