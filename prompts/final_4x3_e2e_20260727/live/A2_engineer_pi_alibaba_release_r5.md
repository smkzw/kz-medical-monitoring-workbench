# Live Tester Contract: release-r5 A2 engineer

Use exact external tester `pi/alibaba/qwen3.8-max-preview`, OMP selector
`alibaba-token-plan-cn/qwen3.8-max-preview`, thinking `xhigh`,
`--no-prewalk`, single-model. You are a visual tester, not the product AI.

Read the common tester, route/time, Tester A, completion-schema, matrix and
`release-r5-20260727/slots/A2/SLOT_CONTRACT.json` contracts. Use:

- product: `http://127.0.0.1:50011/`
- API: `http://127.0.0.1:50010/`
- evidence:
  `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r5-20260727/slots/A2/engineer/`
- synopsis uploaded through the visible UI:
  `runs/execution/mw_final_4x3_harness_20260727/input_fixtures/A2_AATD_Phase_I_Oral/A2_AAT-201-FIH_方案摘要_V0.1.docx`
- minimum no-IB facts when requested:
  `runs/execution/mw_final_4x3_harness_20260727/input_fixtures/A2_AATD_Phase_I_Oral/fact_pack.json`

Scenario: α1-抗胰蛋白酶缺乏症 Phase I oral small molecule, synopsis import,
healthy-volunteer SAD+MAD with sentinel dosing, SRC, stopping/escalation,
food effect and dense PK/PD. The product AI must fill intentional synopsis
gaps and must not invent a patient-efficacy cohort.

Run the complete journey through real visual browser actions to DOCX/PDF/
native Word acceptance. Exercise all visible controls and correlate only for
evidence with network/API/durable state: upload/extraction, retry/cancel/
resume, refresh/reentry, duplicate action/idempotency, research/triage,
three original Protocol reviews, validation, OCR/translation, corpus without
override, AI-prefilled framework/PICOS, dynamic chapters, chapter candidates
and editing, SoA/notes/flowchart, citations, versioning and export.

Test exclusion of RNA editing, gene transfer, cell/gene therapy and device
studies, and correct healthy/PiXZ boundaries for oral small-molecule evidence.
Distinguish scientific/product defects from tester runtime limits. Do not use
direct API/database/DOM injection as a substitute for UI actions.

All medical generation must occur through product independent AI. Do not
modify product source, paste tester-written medical content, use historical
outputs, skeletons, placeholders or corpus override, or create `PASS.md`.

Complete all supported evidence even when blocked. Maintain
`EXTERNAL_TESTER_REPORT.md` ending exactly with:

- `A2_ENGINEER_EXTERNAL_TEST_COMPLETE`, or
- `A2_ENGINEER_EXTERNAL_TEST_BLOCKED:<short reason>`.
