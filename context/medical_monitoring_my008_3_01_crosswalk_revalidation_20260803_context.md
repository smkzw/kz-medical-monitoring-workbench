# Task Context: medical_monitoring_my008_3_01_crosswalk_revalidation_20260803

Created: 2026-08-03 03:51:30
Objective: Read-only revalidate MY008-3-01 V1.1 protocol visit axis against current locked listing form-set identities; persist crosswalk evidence without activation or authority
Task type: `clinical_document_router`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Listing: `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-01（MM外包）/原始数据/【3-01经治锁库后原始数据】MY008211A-PNH-3-01_锁库后EXCEL数据集.xlsx`
  (3,565,691 bytes; SHA-256 `080facc4057d7e56052d40b4a5cdd37373e4c832b3a04da9ecadd123fff45220`).
- Protocol: `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-01（MM外包）/方案/V1.1方案/（缺含研究者签字页方案）MY008211A-PNH-3-01-V1.1-通用版-2024.11.24-clean/研究方案/MY008211A-PNH-3-01_研究方案_V1.1_2025.1.7clean.docx`
  (419,004 bytes; SHA-256 `265858e23249191d382775882c2d6be539e1e88f084fc0e8c4816cb715460aed`).
- Parser/contract: `listing_file_parser_v3_ooxml_metadata_recovery`,
  `services/api/app/protocol_text_extractor.py`, and pure
  `services/api/app/monitoring_visit_crosswalk.py`.

## Scope

- In scope: current locked listing record replay; `表单集OID`/`表单集名称` identity grouping;
  V1.1 table 15 (方案表1研究流程表) visit-axis extraction; explicit derived crosswalk;
  persisted diagnostic artifact and focused replay evidence.
- Out of scope: source registration, adapter/canonical admission, prompt or provider calls,
  database/CAS/runtime writes, browser/API login, medical conclusions, endpoint interpretation,
  or changes to the product frontend/medical-writing subsystem.

## Success Criteria

- Reopen current listing/protocol bytes and preserve exact source hashes.
- Record 57 sheets, 27,474 rows and zero parser warnings; group all observed form-set identities
  (`COM`, `UNS`, `V1`–`V14`) with raw date-labelled name variants and row counts.
- Extract 14 required protocol visits (V1–V14; V14 includes the protocol early-withdrawal axis)
  from `docx:table:15` without guessing.
- Persist a deterministic crosswalk report. Derived label normalization must remain explicit and
  result in review-required findings; no activation or authority may be inferred from a clean shape.
- Run focused contract/replay checks and preserve the result in `TASK_RECORD.md`, `TEST_EVIDENCE.md`,
  review and metrics files.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 03:51:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Source replay confirmed the listing has no canonical `VISIT`/`VISTOID` columns;
  the observed identity is explicitly `表单集OID` plus date-bearing `表单集名称`. The crosswalk
  therefore uses a derived, review-required normalization rather than pretending raw labels match.
- 2026-08-03: Completed artifact/replay/review gate. Crosswalk is `review_required` with 14
  derived-binding findings; normalization separately records three undated V2 rows named
  `筛选期 V2`. No admission or runtime authority was granted.
- 2026-08-03: Raw OOXML recheck found no D70/D98 labels in the V1.1 listing and confirmed
  the expected V10/D112 and V12/D140 form-set variants. `COM`/`UNS` and the three undated
  V2 rows remain bounded exactly as recorded in
  `records/active_slices/medical_monitoring_my008_3_01_crosswalk_revalidation_20260803/FORMSET_SOURCE_NOTE.md`.
