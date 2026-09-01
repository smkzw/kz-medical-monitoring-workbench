# Live Tester Contract: release-r5 A1 engineer

Use the exact external tester route
`pi/alibaba/qwen3.8-max-preview`, OMP selector
`alibaba-token-plan-cn/qwen3.8-max-preview`, thinking `xhigh`,
`--no-prewalk`, single-model. Any observed normalization to `high` or lower
invalidates this run. You are a tester/browser operator, not the product
medical-writing AI.

Read and obey:

- `AGENTS.md`
- `prompts/final_4x3_e2e_20260727/COMMON_TESTER_CONTRACT.md`
- `prompts/final_4x3_e2e_20260727/ROUTE_TIME_GUARD.md`
- `prompts/final_4x3_e2e_20260727/TESTER_A_PI_ALIBABA_QWEN38.md`
- `prompts/final_4x3_e2e_20260727/PER_SLOT_COMPLETION_SCHEMA.json`
- `records/handoffs/codex_retake_20260726/FINAL_4X3_TEST_MATRIX_DRAFT.md`
- `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r5-20260727/slots/A1/SLOT_CONTRACT.json`
- every JSON receipt already present under
  `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r5-20260727/slots/A1/engineer/`

Runtime:

- visible product: `http://127.0.0.1:50011/`
- product API: `http://127.0.0.1:50010/`
- evidence/output:
  `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r5-20260727/slots/A1/engineer/`

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

Through real visual browser controls, run the full journey from clean project
creation to complete DOCX, rendered PDF and native Word acceptance. Do not
supply a completed design. Exercise each user-visible control and the
associated state transition, including refresh/reentry, duplicate action,
failure and recovery behavior, long-running progress, save/version identity,
source lineage, corpus admission without override, AI-first framework/PICOS,
dynamic chapters, chapter drafting/editing, SoA/notes/flowchart, references
and citations.

Use an engineer's acceptance perspective while preserving the real human
workflow. Correlate visible actions with network/API and durable product
receipts only as evidence; do not replace UI actions with direct API, database
or DOM injection. Identify contract mismatches, stuck/false progress,
idempotency defects, stale state, silent failures and export/OOXML/Word errors.
Also assess whether the busy medical writer can finish mainly by accepting or
minimally editing AI defaults.

All medical generation must occur through the product's independently
configured AI. Never generate competitor conclusions, corpus material,
design recommendations or protocol prose yourself and paste them into the
product. Record product-AI identities separately for every stage.

Do not modify product source, shared runtime or prompt contracts. Do not use
corpus override, skeleton content, placeholders or historical outputs. Do not
create `PASS.md`.

Preserve product-created screenshots/downloads and the required structured
evidence under the assigned directory. Maintain
`EXTERNAL_TESTER_REPORT.md`. End it with exactly:

- `A1_ENGINEER_EXTERNAL_TEST_COMPLETE`, or
- `A1_ENGINEER_EXTERNAL_TEST_BLOCKED:<short reason>`.
