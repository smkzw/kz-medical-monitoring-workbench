# Review Packet: Prior Work Audit And RUX Monitoring Preflight - 2026-07-08

## Purpose

The user asked Codex to let Hermes review prior work in the background, provide enough information for a real judgment, discuss the recommendations, and only land changes that Codex and Hermes both accept.

This packet is for an advisory-only Hermes conference. Do not edit source files. Do not browse the web. Do not run tests or open browsers. Read only the listed workspace files and write only the assigned output file.

## Current Product Scope

- Product: AI Medical Manager Workbench for clinical-trial medical users.
- Allowed visible modules: `项目总看板`, `证据调研与方案设计`, `入排审核`, `医学监查`, `数据分析与TFL`, `医学写作`, `安全信号与PV协同`, `审批中心`.
- Do not build or expose standalone first/fourth/fifth non-medical clinical-development links.
- User-facing subsystem names must not include `第几环节`, `阶段`, or `Stage`.
- Original real-project folders are read-only unless copied/backup-first.
- The system must ultimately run independently from Codex. Runtime AI work must be routed through independent AI services, not Codex reasoning.
- For future AI routing: OCR uses local oMLX GLM-OCR-bf16 or PaddleOCR-vl-1.6; LLM uses Hermes buddy DeepSeek supplier `deepseek-v4-pro`; VLM uses Hermes buddy `minimax-m3`.

## Prior Review Already Completed

The previous Codex-chaired Hermes conference `workbench_resume_review_20260708` completed and passed the review gate. Key records:

- `context/workbench_resume_review_20260708_review_packet.md`
- `runs/conference/workbench_resume_review_20260708/participant_qwen_plus.md`
- `runs/conference/workbench_resume_review_20260708/participant_mimo.md`
- `runs/conference/workbench_resume_review_20260708/participant_ds_flash.md`
- `runs/conference/workbench_resume_review_20260708/hermes_lead.md`
- `runs/conference/workbench_resume_review_20260708/main_deepseek_pro.md`
- `reviews/codex_conference_workbench_resume_review_20260708_review.md`
- `metrics/workbench_resume_review_20260708_conference_metrics.md`
- `logs/SOFT_PAUSE_20260708_0833_CST.md`

Accepted changes from that conference included model-level exclusion of `SourceRegistrySpan.preview_hash`, harmonized visible/default wording from `EDC listing` to `原始数据 listing`, deterministic preservation of duplicate inbox item ids, and browser QC guard against visible `EDC` wording.

## Verified State From Prior Closure

Per `logs/SOFT_PAUSE_20260708_0833_CST.md`:

- Focused backend regression: 39 tests OK.
- Full backend regression: 114 tests OK.
- Frontend production build: passed, with known Vite chunk-size warning only.
- Live API V1: `/api/projects/proj_mgk10_sar_demo/workbench-inbox?limit=80` returned 99 total open items and 80 visible items, including cross-module item types.
- Live API V2: `/sources`, `/eligibility`, `/workbench-inbox`, and `/api/health` did not expose `/Users/`, `content_hash`, `preview_hash`, `storage_key`, `server_path`, `source_record_id`, or `data_path`.
- Browser QC: `frontend/tests/overview_ai_gateway_qc.mjs` passed desktop/mobile; 8 module rows; no lifecycle/non-medical/path/Source Registry/医学监督/EDC visible wording; unread count changed from 99 to 98 after click while total open count stayed 99.

## Current Known Risks To Re-Audit

1. `frontend/src/App.jsx` still contains static local absolute paths in source rows for CRSwNP, RUX, MY009, PV, and safety packages. Even if default overview QC does not show them, this is a product-boundary and path-leak risk for source/data-health surfaces.
2. `services/api/app/monitoring_intake.py` is still generic/demo-driven. Its aliases and rules are mostly SAR-style examples such as loratadine washout, eye AE/MH, lab abnormal, and rTNSS. It is not a protocol-driven RUX AD monitoring engine.
3. Subject Timeline and Patient Profile pages have contracts in `frontend/AGENTS.md`, but the next build must derive RUX visit axis, event lanes, efficacy/safety trends, and risk prompts from original RUX listing/protocol files. Prior skill outputs or generated HTML must not be used as the data source.
4. `_select_visible_items()` remains a short-term recovery patch for overview visibility. It should not be treated as final product-grade work prioritization.
5. Some tests still use `EDC listing` strings as fixture values. This may be acceptable inside tests only if visible UI/API guardrails prevent user-facing `EDC` wording and the tests are not asserting product copy.
6. The workspace is not a git repository. Review should rely on source files, logs, tests, and records rather than `git diff`.

## RUX Original Source Precheck

Use `context/rux_monitoring_source_precheck_20260708.md`.

Highlights:

- RUX project listing XLSX exists and parses: 53 sheets, 180,793 rows.
- RUX subject report XLS exists and parses: 192 rows, fields include `SUBJID`, `RANDNO`, `SITENM`, `SEX`, `SUBJSTA`, `ARM`, `RANDDTC`.
- RUX protocol DOCX exists and parses: 2,005 paragraphs, 20 tables, 2,005 spans.
- Key listing sheets include `SV`, `RAND`, `CM`, `PR`, `MH`, `AE`, `IGA`, `EASI`, `BSA`, `NRS`, `LBHEMA`, `LBCHEM`, `LBURIN`, `UNS`.
- Protocol-derived candidates include visit schedule table, IGA/EASI/NRS endpoints, lab interruption/repeat-confirmation table, concomitant medication recording requirements, prohibited medication impact on Week 8 IGA-TS, and unscheduled visit logic.

This precheck proves the raw files are parseable. It does not prove medical monitoring has been implemented.

## Files To Review

Core records:

- `logs/SOFT_PAUSE_20260708_0833_CST.md`
- `logs/system_build_log.md`
- `reviews/codex_conference_workbench_resume_review_20260708_review.md`
- `runs/conference/workbench_resume_review_20260708/main_deepseek_pro.md`
- `context/rux_monitoring_source_precheck_20260708.md`

Scope and product contracts:

- `README.md`
- `frontend/AGENTS.md`
- `logs/subsystems/module_scope_log.md`
- `logs/subsystems/project_dashboard_log.md`

Backend/API:

- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/main.py`
- `services/api/app/monitoring_intake.py`
- `services/api/app/listing_file_parser.py`
- `services/api/app/protocol_text_extractor.py`
- `services/api/app/source_intake.py`
- `services/api/app/demo_repository.py`
- `services/api/app/workbench_inbox.py`
- `services/api/app/enrollment_adapter.py`

Frontend/QC/tests:

- `frontend/src/App.jsx`
- `frontend/tests/overview_ai_gateway_qc.mjs`
- `frontend/tests/patient_profile_qc.mjs`
- `frontend/tests/monitoring_upload_qc.mjs`
- `tests/test_contracts.py`
- `tests/test_workbench_inbox.py`
- `tests/test_listing_file_parser.py`
- `tests/test_protocol_text_extractor.py`
- `tests/test_source_registry.py`

Do not read `frontend/node_modules`, `frontend/dist`, runtime JSONL stores, or original real-project folders in this advisory review.

## Review Questions

1. Does the previous Hermes/Codex closure still look valid after reading the current files and logs? Identify any regression or unaddressed issue.
2. Are there remaining path/hash/internal-id leakage risks, especially from `frontend/src/App.jsx` static source rows and public API serializers?
3. Is current `monitoring_intake.py` acceptable as a prototype placeholder only, or does it risk misleading the RUX real-data build? What must be replaced before using RUX data?
4. What is the minimum correct RUX medical monitoring P0 architecture from original listing + protocol: parser, protocol rule extraction, field mapping, risk engine, subject timeline, Patient Profile, review actions, audit/source trace?
5. How should the system prevent Codex-runtime dependence for AI-assisted protocol/listing decomposition while preserving medical approval boundaries?
6. Which changes, if any, are safe to land now before the RUX implementation loop? Which must be deferred until after Codex external research and real-data testing?
7. What verification gates should Codex run before accepting any next edit round?

## Required Output

Return:

- Findings ordered by severity with file references.
- Consensus on whether previous work remains accepted, conditionally accepted, or reopened.
- Concrete change recommendations divided into `land now`, `defer until RUX build`, and `do not do`.
- RUX P0 design risks and required verification.
- Any disagreements or uncertainties.

Keep evidence, inference, recommendation, and uncertainty separate.
