# Live Tester Contract: release-r5 A2 lazy medical writer

Use exact external tester `pi/alibaba/qwen3.8-max-preview`, OMP selector
`alibaba-token-plan-cn/qwen3.8-max-preview`, thinking `xhigh`,
`--no-prewalk`, single-model. You are a visual tester, not the product AI.

Read the common tester, route/time, Tester A, completion-schema, matrix and
`release-r5-20260727/slots/A2/SLOT_CONTRACT.json` contracts before acting.
Use a fresh session and only the isolated runtime/evidence paths below:

- product: `http://127.0.0.1:50011/`
- API: `http://127.0.0.1:50010/`
- evidence:
  `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r5-20260727/slots/A2/lazy_medical_writer/`
- synopsis to upload through the visible UI:
  `runs/execution/mw_final_4x3_harness_20260727/input_fixtures/A2_AATD_Phase_I_Oral/A2_AAT-201-FIH_方案摘要_V0.1.docx`
- minimum no-IB facts, if the UI requests them:
  `runs/execution/mw_final_4x3_harness_20260727/input_fixtures/A2_AATD_Phase_I_Oral/fact_pack.json`

Scenario: α1-抗胰蛋白酶缺乏症, Phase I, oral small molecule, synopsis
import. The intended study is healthy-volunteer SAD+MAD with sentinel dosing,
SRC review, stopping/escalation rules, food effect and dense PK/PD sampling.
Do not invent or paste a patient-efficacy cohort. The synopsis intentionally
leaves cohort count, observation window and PD sampling density open so the
product AI must recommend them.

Act as a busy expert medical writer who wants extraction, research and
AI-prefill before minimal corrections. Run the full visible journey:
project creation, DOCX import and extracted-fact confirmation, product-AI
competitor search/triage, at least three original Protocol reviews, content
validation, OCR/translation/resume where relevant, corpus admission without
override, framework/PICOS, dynamic chapters, all chapter candidates and
editing, SoA/notes/flowchart, citations, save/reload/versioning, full DOCX,
PDF and native Word navigation/edit/save/reopen.

The product must exclude RNA editing, gene transfer, cell/gene therapy and
device studies from the usable test corpus. It may use an oral small-molecule
Protocol only with healthy/PiXZ population boundaries made explicit. Check
phase, modality and indication specificity without writing the medical
content yourself.

Use only real visual browser controls. Do not substitute direct API/database/
DOM injection, do not modify source, do not use historical outputs, skeleton
content, placeholders or corpus override, and do not create `PASS.md`.
Product independent AI must perform every medical generation task.

Create all required structured evidence and `EXTERNAL_TESTER_REPORT.md`.
End it exactly with:

- `A2_LAZY_EXTERNAL_TEST_COMPLETE`, or
- `A2_LAZY_EXTERNAL_TEST_BLOCKED:<short reason>`.
