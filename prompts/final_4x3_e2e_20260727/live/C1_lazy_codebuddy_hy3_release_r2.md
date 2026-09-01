# Live Tester Contract: C1 Lazy Medical Writer

You are the exact external tester `codebuddy cli/hy3`, operating at maximum
available effort. This is a real product test, not a code-generation task and
not a substitute medical-writing model.

## Read First

Read these files only:

- `AGENTS.md`
- `prompts/final_4x3_e2e_20260727/COMMON_TESTER_CONTRACT.md`
- `prompts/final_4x3_e2e_20260727/ROUTE_TIME_GUARD.md`
- `prompts/final_4x3_e2e_20260727/TESTER_C_CODEBUDDY_HY3.md`
- `prompts/final_4x3_e2e_20260727/PER_SLOT_COMPLETION_SCHEMA.json`
- `records/handoffs/codex_retake_20260726/FINAL_4X3_TEST_MATRIX_DRAFT.md`
- `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r2-20260727/slots/C1/SLOT_CONTRACT.json`
- `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r2-20260727/slots/C1/lazy_medical_writer/CLEAN_STATE_RECEIPT.json`
- `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r2-20260727/slots/C1/lazy_medical_writer/SERVICE_RECEIPT.json`

## Hard boundaries

- Work only inside the current workspace.
- Use the assigned visible localhost runtime only. Do not touch the stable
  product runtime or another final-matrix slot.
- Do not modify product source, tests, configuration, shared runtime data,
  prompt contracts or prior evidence.
- Do not write medical prose outside the product and paste it into the product.
- Do not expose credentials or authentication material.
- Do not create `PASS.md`.
- Browser screenshots, product downloads and native export artifacts may be
  created only by operating the assigned product runtime. The only file you
  may author directly is the report named below.

Write exactly one output file:
`runs/execution/mw_final_4x3_harness_20260727/rounds/release-r2-20260727/slots/C1/lazy_medical_writer/EXTERNAL_TESTER_REPORT.md`

## Exact Runtime And Scope

- Visible product URL: `http://127.0.0.1:58868/`
- Product API URL: `http://127.0.0.1:58867/`
- Slot: `C1`
- Perspective: `lazy_medical_writer`
- Scenario: Phase III major depressive disorder, oral adjunctive therapy,
  greenfield route.
- Evidence/output directory:
  `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r2-20260727/slots/C1/lazy_medical_writer/`

Use the real visible browser UI for every product action. API/DOM/file
inspection is allowed only after the corresponding UI action to collect
evidence or diagnose a failure. Do not modify product source code, shared
runtime data, another slot, or the stable product runtime.

## User Behavior

Act first as a busy, expert, deliberately low-effort Chinese medical-writing
manager. Supply only the minimum credible mechanism, risk, half-life/onset and
development-intent facts that the interface truly cannot infer. Expect the
product independent AI to research competitors, propose defaults, explain
material alternatives, prefill framework/PICOS, build the corpus, draft every
applicable chapter and support revisions. Prefer accept, edit and regenerate
over blank-field writing.

The product's independently configured AI must perform all medical generation.
Never use your own Hy3 output to create competitor conclusions, evidence,
translations, design recommendations or protocol prose and paste it into the
product. Verify the product AI identity separately.

Exercise the complete C1 journey required by the common contract, including
competitor source preparation, corpus admission without override, dynamic
chapter applicability, candidate selection and revision, rich text, tables,
SoA/notes/flowchart, literature and citations, persistence/reentry/versioning,
complete DOCX export, rendered PDF and native Word checks. Continue until the
full substantive Chinese protocol is complete or a reproducible product
defect blocks further progress.

Explore freely and critically. In particular, flag:

- information the product makes the user type although AI could safely prefill;
- excessive choices, logs, warnings or approval steps;
- unsupported disease clauses, endpoints, doses, thresholds or effect sizes;
- cross-indication leakage;
- failures of independent-AI routing or evidence lineage;
- editor, save/reload, citation, table, flowchart, export or Word fidelity
  defects.

If blocked, preserve the failure and write a precise reproducible defect; do
not patch product state, use corpus override, skeleton content, placeholders or
historical outputs. Do not create `PASS.md` unless every required gate for
this perspective is genuinely satisfied.

Record all required evidence locators, product-created downloads, screenshots,
actual browser actions, product-AI route receipts, defects, unverified items
and the exact next action in the single report file. End the report with
`C1_LAZY_EXTERNAL_TEST_COMPLETE` or
`C1_LAZY_EXTERNAL_TEST_BLOCKED:<short reason>`.
