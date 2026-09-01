# r42 A1 Medical-Writing Release Retest

## Goal

Re-run A1 `lazy_medical_writer` from a clean immutable runtime after repairing
the r41 drawer-to-authoring triage-status propagation defect, then continue the
full greenfield protocol and native Word acceptance contract.

## Source And Runtime

- Round: `release-r42-20260730`
- Slot/perspective: `A1 / lazy_medical_writer`
- Input fingerprint:
  `292a9c82f8ec0462190b556684332ee1ec62d85920bd58cc38093d110fa2c9d8`
- Runtime identity:
  `d14a3eb101a5d89d35c184394059bd86a14c28aa30283ba88480dde062219fca`
- Frontend: `http://127.0.0.1:55223/`
- Backend: `http://127.0.0.1:55222`
- API PID: `88514`
- Frontend PID: `88552`
- Contract: `medical-writing-api-2026-07-17.1`
- Backend build: `api-d72782983d1410ac`
- Frontend build: `web-7cf2a34312de0473`

## AI Role Freeze

- Comprehensive AI:
  `deepseek / deepseek-v4-pro` (day route selected at 09:03 CST)
- OCR AI: `GLM-OCR-bf16`
- Body translation AI:
  `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`
- Translation-support LLM:
  DeepSeek official `deepseek-v4-flash`
- OCR/translation admission:
  OCR <= 8, translation <= 8, combined <= 16.

## Pre-Freeze Verification

- r41 synchronization repair:
  - 26 focused tests passed;
  - 175 broader medical-writing frontend contract tests passed;
  - production frontend build passed.
- Exact concurrent workspace:
  - 5142 passed;
  - 9 failed;
  - 29 warnings;
  - 1317.47 seconds.
- The nine failures are outside the medical-writing synchronization slice:
  monitoring catalog/risk-seed assumptions and two monitoring disabled-button
  explanation contracts. They remain recorded and were not changed from this
  writing release task.
- The matrix fail-closed receipts now include the new triage-status regression.
- Post-freeze harness/runtime/baseline/route/status regression:
  `97 passed in 0.76s`.

## A1 Scenario

- COPD, phase III, fixed-dose inhaled combination, greenfield route.
- Tester enters only product, indication, and phase.
- Product independent AI must perform research and triage.
- No API/database/DOM injection, corpus override, skeleton prefill, or manual
  per-item classification.

## First Acceptance Point

After triage reaches terminal state:

1. drawer and outer authoring progress show the same completed/total count;
2. no stale pre-retry count remains;
3. bulk locking is enabled through the visible product UI;
4. no duplicate search, project, or triage run is created.

## Full Acceptance Boundary

Continue through source acquisition, preparation, validation, OCR/translation,
corpus construction, framework/PICOS, complete protocol drafting, rich editing,
tables, SoA, flowchart, scale-image attachment, references, persistence,
versioning, DOCX export, and native Word verification. `PASS.md` is forbidden
until the complete contract passes.

## Dispatch

- Tester: existing Codex subAgent
  `019fafee-99ee-7530-9478-e1b3cc4cbf80`
- Model contract: `gpt-5.6-luna-high`
- Dispatch submission: `019fb08d-44e7-79e1-ba6e-0cc8c52d1077`
- Polling policy: sparse; do not interrupt healthy long-running product AI.

## Live Loop Log

- 09:17 CST: Created `MW-III-1A3A1248` through the visible new-project
  workflow using only drug, COPD indication, and phase III.
- 09:36 CST: The outer authoring page reached triage `19/19 / 100%`; the stale
  r41 `17/19` state did not recur.
- 09:38 CST: The visible competitor drawer reached `665/665`, with independent
  AI recommending retain 49 and exclude 616. Bulk locking was enabled.
- 09:39 CST: The tester clicked one visible bulk-confirm action for all 665
  candidates. No manual per-item classification was performed. The pipeline
  advanced to original-document download.
- 10:13 CST read-only diagnostic: the durable product pipeline was healthy at
  original-document preparation `38/91`, overall 53%. It was processing
  `NCT03888131 / Prot_000.pdf`, with 55/65 OCR-required pages complete and a
  current substep percentage of 64%. This is real weighted progress, not a
  stalled black box.
- Evidence:
  - `screenshots/original_resolution/003_triage_outer_terminal_19_of_19.png`
  - `screenshots/original_resolution/004_drawer_ai_triage_665_locked.png`
  - `BROWSER_ACTION_TRACE.jsonl`
