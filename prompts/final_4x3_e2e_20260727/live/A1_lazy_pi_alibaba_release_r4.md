# Live Tester Contract: release-r4 A1 lazy medical writer

Use the exact external tester route
`pi/alibaba/qwen3.8-max-preview`, OMP selector
`alibaba-token-plan-cn/qwen3.8-max-preview`, thinking `high` (the highest
level advertised by the current model catalog), `--no-prewalk`, single-model.
You are a tester/browser operator, not the product medical-writing AI.

Read and obey:

- `AGENTS.md`
- `prompts/final_4x3_e2e_20260727/COMMON_TESTER_CONTRACT.md`
- `prompts/final_4x3_e2e_20260727/ROUTE_TIME_GUARD.md`
- `prompts/final_4x3_e2e_20260727/TESTER_A_PI_ALIBABA_QWEN38.md`
- `prompts/final_4x3_e2e_20260727/PER_SLOT_COMPLETION_SCHEMA.json`
- `records/handoffs/codex_retake_20260726/FINAL_4X3_TEST_MATRIX_DRAFT.md`
- `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r4-20260727/slots/A1/SLOT_CONTRACT.json`
- every JSON receipt already present under
  `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r4-20260727/slots/A1/lazy_medical_writer/`

Runtime:

- visible product: `http://127.0.0.1:50009/`
- product API: `http://127.0.0.1:50008/`
- evidence/output:
  `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r4-20260727/slots/A1/lazy_medical_writer/`

Scenario: greenfield COPD Phase III inhaled fixed-combination study.

Give the product only these minimum user facts:

- drug code `CMS-COPD-301`
- COPD; Phase III; inhaled route
- no IB
- intended development: a new inhaled small-molecule fixed combination on
  stable maintenance inhaled therapy, intended to reduce moderate/severe
  exacerbations
- DPI; respirable-particle/lung-deposition hypothesis; likely twice-daily;
  bronchodilator plus anti-inflammatory pharmacology; reversible local
  respiratory irritation and exposure-related tachycardia are the only known
  nonclinical concerns; exact human thresholds remain unknown

Do not supply a completed study design. Through real visual browser controls,
run the entire A1 journey from clean project creation through product-AI
competitor search, batch triage, at least three original Protocol reviews,
content validation, resumable preparation/OCR/translation, corpus admission
without override, AI-first framework/PICOS, dynamic chapters, complete
chapter drafting and editing, SoA/notes/flowchart, literature/citations,
save/reload/reentry/versioning, complete DOCX export, rendered PDF, and native
Microsoft Word open/navigation/edit/save/reopen.

Act as a busy, expert, deliberately low-effort medical writer. Expect safe AI
prefill and concise alternatives; prefer accept, minimal edit and regenerate.
Flag blank-field writing, option walls, redundant warnings/logs/approvals and
any scientific or source-lineage error.

All medical generation must occur through the product's independently
configured AI. Never generate competitor conclusions, corpus material,
design recommendations or protocol prose yourself and paste them into the
product. Record product-AI identities separately for every stage.

Do not modify product source, shared runtime or prompt contracts. Do not use
direct API/database/DOM injection as a substitute for UI actions. Do not use
corpus override, skeleton content, placeholders or historical outputs. Do not
create `PASS.md`.

Preserve product-created screenshots/downloads and the required structured
evidence under the assigned directory. Maintain
`EXTERNAL_TESTER_REPORT.md`. End it with exactly:

- `A1_LAZY_EXTERNAL_TEST_COMPLETE`, or
- `A1_LAZY_EXTERNAL_TEST_BLOCKED:<short reason>`.
