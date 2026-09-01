# Codex Conference Review: medical_writing_additional_table_domains_20260714

Date: 2026-07-14

## Verdict

Pass after Codex revision. The conference supported adding three profiles, but Codex rejected the proposed 13-column PK starter and the proposal to leave generated-template semantic roles empty.

## Boundary Compliance

- Original protocol roots remained read-only.
- Participants read only the preflight-approved workbench packet and implementation/test files; no participant performed production writes, web research or visual acceptance.
- Each participant and the GLM chair completed three rounds in one session with no fallback or terminal failure.
- CLI shutdown emitted non-fatal unknown-toolset/event-loop warnings after valid output persistence; runner JSON confirms return code 0 for all 12 rounds.

## Participant Outputs Reviewed

- MiniMax-M3: promote sample size and PK; guard analysis sets; preserve compact PK layout.
- DeepSeek-V4-Pro: promote all three but widen PK to 13 columns.
- MiMo-V2.5: promote analysis sets; guard sample size and PK because of layout variation.
- All agreed on project-value isolation, shared working-copy/approval/Word paths and localized registry-driven implementation.

## Hermes Sub-Venue Review

GLM-5.2 resolved the grade disagreement in favor of A-grade semantic profiles for all three candidates, with `parameter + assumption` required for sample size, `set name + definition` required for analysis sets, and no required roles for PK/PD/immunogenicity. It rejected the 13-column PK proposal and recommended a compact starter.

## Main-Venue Codex Review

- Accepted: three A-grade profiles, no global project values, source-faithful two-column analysis-set core, flexible PK semantic vocabulary and compact starter.
- Revised: generated PK templates retain semantic roles for their seven visible starter columns. Leaving those roles empty would make a newly inserted table unnecessarily incomplete; imported source matrices can still clear/map roles and use `semantic_only` without structural coercion.
- Rejected: 13-column PK starter, universal statistical calculation engine, mandatory project-specific thresholds/formulas, automatic decomposition of a two-column analysis-set source, and promotion of AE management/stopping/biomarker candidates without enough direct evidence.
- Dose modification remains guarded B and trial-drug-only; CM remains a separate concept.

## Codex Independent Verification

- Recomputed SHA-256 and re-read the cited PDF pages for 9 A-grade source protocols across sample size, analysis sets and PK/PD/immunogenicity sampling.
- Deterministic inventory scanned 373 files, deduplicated to 340 unique hashes and retained 127 OCR boundaries. v1 page-level propagation was rejected; v2 requires table or bounded adjacent-context hits and is explicitly a retrieval index, not medical evidence.
- TDD: the pre-change catalog failed exactly because the three profiles were absent; post-change focused tests passed.
- Source-faithful two-column analysis-set mapping and an uncoerced PK source matrix with no semantic roles both validate and can be medically confirmed without structural errors.
- Three real protocol projects (RUX-03-002, CMS-D001 and MY008211A-PNH-3-01) passed all-11-table persistence, cold restart, table-scoped blockers and Word export with the three new profiles included.
- Medical-writing suite: 157 passed. Full repository: 874 passed, 12 existing warnings. Frontend production build and backend compile passed; existing >500 kB chunk warning remains.
- API cold restart on `127.0.0.1:8911` reports status ok, SQLite schema 14/integrity ok, 8 profiles and the expected three template names/starter counts.
- Browser and rendered Word visual acceptance were not performed in this execution context and remain explicitly unclaimed.

## Final Decision

Adopt `sample_size_assumptions`, `analysis_sets` and `pk_immunogenicity_schedule` as schema-driven profiles. Preserve every table in the same visible structured-table, rich-text, AI, approval, audit and Word chain. Keep AE management, stopping rules, biomarker matrices and related candidates generic/guarded until their own evidence gates pass. Overall Goal remains active.
