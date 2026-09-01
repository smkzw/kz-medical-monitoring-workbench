# Live Tester Contract: release-r5 A3 lazy medical writer

Use exact external tester `pi/alibaba/qwen3.8-max-preview`, OMP selector
`alibaba-token-plan-cn/qwen3.8-max-preview`, thinking `xhigh`,
`--no-prewalk`, single-model. You are a visual tester, not the product AI.

Read the common tester, route/time, Tester A, completion-schema, matrix and
`release-r5-20260727/slots/A3/SLOT_CONTRACT.json` contracts. Use:

- product: `http://127.0.0.1:50011/`
- API: `http://127.0.0.1:50010/`
- evidence:
  `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r5-20260727/slots/A3/lazy_medical_writer/`

Scenario: greenfield Phase II intranasal local therapy for chronic
rhinosinusitis without nasal polyps (CRSsNP).

Give the product only these minimum facts:

- drug code `CMS-CRS-201`
- CRSsNP, Phase II, intranasal spray, no IB
- a novel locally acting small-molecule anti-inflammatory intended as add-on
  to stable intranasal corticosteroid
- intended twice-daily administration; local nasal irritation and taste
  disturbance are plausible reversible concerns; systemic exposure is
  expected to be low but has not been established

Do not provide a completed design. Act as a busy expert writer who expects the
product AI to research, rank and prefill, then performs only necessary
approval and minimal correction. Run the full visible journey through
project creation, independent-AI research/triage, three original Protocol
reviews, validation, OCR/translation/resume, corpus without override,
framework/PICOS, dynamic chapters, all chapter candidates/editing,
SoA/notes/flowchart, citations, versioning, DOCX/PDF and native Word.

Check that CRSsNP is not silently replaced by CRSwNP; intranasal study drug,
background intranasal corticosteroid, rescue treatment and prohibited
medication remain separate; local tolerance, device training,
endoscopy/imaging and relevant endpoints are appropriately handled. An oral
competitor or nasal-polyp endpoint may be borrowed only with explicit,
scientifically justified boundaries. The product AI, not you, must make and
write these decisions.

Use real visual browser click/type controls. Do not replace UI actions with
direct API/database/DOM injection, modify source, paste tester-written medical
content, use historical outputs/skeletons/placeholders/corpus override, or
create `PASS.md`.

Complete all structured evidence and `EXTERNAL_TESTER_REPORT.md`, ending:

- `A3_LAZY_EXTERNAL_TEST_COMPLETE`, or
- `A3_LAZY_EXTERNAL_TEST_BLOCKED:<short reason>`.
