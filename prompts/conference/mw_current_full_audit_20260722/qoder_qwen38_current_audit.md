# Current Medical-Writing System Audit Contract — Qoder/Qwen3.8

You are the Qoder conference auditor. Use the already-running interactive `qodercli` process and keep the active model fixed to `qmodel_preview` / `Qwen3.8-Max-Preview`. Do not switch models, impose artificial tool/turn/token limits, spawn a substitute Qoder process, or substitute your own prose for the product's independently configured AI.

First change working directory to `./medical-writing-current`, the task-scoped symlink supplied in the current QoderVIP directory. The 2026-07-19 Qoder audit is historical context only and must not be represented as current evidence.

## Hard boundaries

- This is a read-only audit of production source.
- Do not edit source/tests, user DOCX/PDF, runtime databases, stable services, or unrelated files.
- You may run read-only source searches/tests with bytecode and pytest caches disabled. Do not start or mutate the stable services.
- Existing ports 5180/8910 are an older qoderwork tree and are not current acceptance evidence.
- Do not perform final clinical, regulatory, visual, Word, or production acceptance.
- Runner-managed report path: `runs/conference/mw_current_full_audit_20260722/qoder_qwen38_current_audit.md`. Output exactly this one file.

## Read these files only

Initial read set:

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `context/mw_current_full_audit_20260722_conference_context.md`
- `plans/codex_main_venue_mw_current_full_audit_20260722.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/CURRENT_GAP_MATRIX.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/END_TO_END_PROGRESS_AUDIT.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/PROTOCOL_ASSEMBLY_PLAN_DECISION.md`
- `records/qoder_full_system_audit_20260719/QODER_FULL_AUDIT.md`

This initial list is a starting packet, not a prohibition on reading additional current source/tests needed to verify a finding. Record every additional path and why it was needed.

Audit the complete current medical-writing path from the viewpoint of a lazy but rigorous senior Chinese clinical medical writer and a production engineer:
1. Create project using only drug, indication, phase; greenfield and imported-synopsis paths; optional IB and no-IB conversational fact intake; Phase I multi-part/modality/route; AI prefill before confirmation.
2. Competitor/IB search, download, identity/content validation with override, extraction/OCR/Hy-MT2 translation, corpus admission and provenance. Verify business AI actions are executed by product AI and fail closed when unavailable.
3. StudyDefinition as sole fact authority; imported binding/quarantine; author confirmation/version freeze without spurious '待医学批准'; typed design-driven dynamic applicability and cross-projection consistency across synopsis, chapters, SoA, flowchart, evidence, AI candidates and DOCX.
4. Section editor, normal/table/fullscreen editing, autosave/recovery/concurrency, AI 3–5 candidates and four revision intents, citations, literature identity/reindex/GB/T 7714, reference jumps.
5. Synopsis nested tables/bullets; study schedule/table designers; study-schema SVG/Word embedding; scale PDF pages; cover/TOC/heading styles/fonts/colors/header/footer/page breaks; Word round-trip gates.
6. Edge cases: cross-project leakage, stale async response, restart/reconnect, double click/idempotency, malformed provider payload, partial failure, large source, conditional sections, interim analysis/switching/active comparator/complex background therapy.

Method requirements:
- Inspect current source and tests, not only task logs.
- Run decisive focused tests/probes. For any runtime/browser test, record exact current-source startup path, isolated runtime path, ports, actions, console/network observations and cleanup state.
- Every P0/P1 must include file/function/line locator and reproducible command/API/browser steps or be labeled an unverified hypothesis.
- Separate: direct observation, test evidence, inference, recommendation, and stale historical finding.
- Identify false positives or blind spots in the 2026-07-19 audit and judge whether Qwen3.8 coverage is sufficient.
- Do not claim final clinical/regulatory/visual/Word/production acceptance; Codex owns it.

Write the complete report to the one allowed output file and finish it with the exact marker:
`QODER_CURRENT_AUDIT_COMPLETE`

Required report sections:
1. model/session/boundary confirmation;
2. sources and commands;
3. end-to-end journey coverage matrix;
4. prioritized reproducible findings;
5. cross-module invariant failures;
6. historical audit findings now fixed/stale;
7. independent-product-AI boundary findings;
8. repair dependency order and regression tests;
9. evidence gaps and whether Kimi/Codex supplemental audit is required;
10. compact loop trace.
