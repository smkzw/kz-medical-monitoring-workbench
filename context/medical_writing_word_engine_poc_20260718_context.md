# Task Context: medical_writing_word_engine_poc_20260718

Created: 2026-07-18 10:23:21
Objective: Use the current medical-writing production Word fixtures to evaluate Aspose.Words, Syncfusion DocIO, and Open XML SDK validation, then recommend and implement only a bounded production integration that passes source-fidelity, field-update, CJK-font, Microsoft Word, 200-DPI visual, and private-deployment gates.
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current exporter:
  `services/api/app/medical_writing_document_exporter.py`.
- Current production candidate and deterministic rendering evidence:
  `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_final_qc/greenfield_ra/`.
- Imported-source fidelity fixtures:
  `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_final_qc/proj_rux_03_002/`
  and
  `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_final_qc/proj_d001/`.
- Highest-priority company formatting/corpus sources already registered in the
  medical-writing task record, including CMS-D017 PNH, D005, MY004 RA and the
  company protocol-template directory.
- Technical comparison and official-source bibliography:
  `research/medical_writing_word_engine_comparison_20260718.md`.
- Microsoft Word native application is the final page-layout authority.
  LibreOffice is only a cross-platform deterministic rendering layer.
- User explicitly authorized integrating the best tool into production only
  after sufficient testing and conference review.

## Scope

- In scope:
  - isolated local POCs for Aspose.Words, Syncfusion DocIO and Open XML SDK
    validation;
  - compare template-first filling against current from-scratch greenfield
    construction;
  - use identical real-project fixtures and Word-native gates;
  - implement only a bounded, reversible production integration after the
    candidate passes;
  - preserve full task and decision records.
- Out of scope:
  - replacing source-preserving imported-DOCX passthrough without proof;
  - using Microsoft Word as an unattended server component;
  - purchasing or accepting a commercial license without user action;
  - changing medical content, approval semantics, project data contracts or
    the current stable ports before release gates pass.

## Success Criteria

- Open XML SDK validation runs deterministically on every generated candidate
  and detects the previously observed invalid field hierarchy.
- Each commercial/open-source candidate is tested on at least D017, RUX, D001
  and the greenfield RA package, or explicitly marked blocked by license/runtime
  with evidence.
- POC captures: package-part and relationship diffs, styles/numbering/headers/
  footers/sections/fields/bookmarks/media, field-result population, Chinese
  font substitution, page count, 200-DPI render, runtime/memory and deployment
  dependencies.
- Microsoft Word opens the candidate with `OpenAndRepair=false`; TOC, table and
  figure directories are readable; longitudinal section layout and page
  numbering are correct.
- Production integration is feature-flagged or otherwise reversible, preserves
  the current source-fidelity path, and has focused plus full regression tests.
- Conference reviewers receive the full evidence bundle and identify no
  unresolved P0/P1 before Codex accepts integration.

## Risk Boundaries

- POC writes only under
  `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_engine_poc/`
  until a candidate passes.
- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Never round-trip-save the authoritative imported source files in place.
- Never treat vendor capability claims or successful LibreOffice rendering as
  Word-native fidelity proof.
- Commercial trial watermarks/paragraph limits invalidate visual acceptance;
  record them as licensing blockers rather than hiding them.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-18 10:23:21: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-18: Context completed from the current exporter, real Word evidence,
  user authorization and source-fidelity boundaries. First action is isolated
  runtime setup and a fail-first Open XML validation fixture.
