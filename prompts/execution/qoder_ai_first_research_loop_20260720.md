# Qoder Execution Review: AI-first competitor research and re-prefill loop

You are the first-priority execution reviewer for the CMS medical-writing
workbench. Use the exact Qoder model already loaded for this session:
`qmodel_preview` / `Qwen3.8-Max-Preview`. Tools and internal turns are not
artificially limited.

## Workspace

`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`

Read the current global instructions first:

`/Users/smkzw/.codex/AGENTS.md`

Then read at least:

- `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/TASK_RECORD.md`
- `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/QODER_AND_CTGV_BASELINE_20260720.md`
- `reviews/codex_prefill_source_acceptance_20260720.md`
- `reviews/codex_prefill_test_review_20260720.md`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/main.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/writing-reference/WritingReferencePanel.jsx`
- related tests for authoring journey, prefill, discovery, frontend contract,
  and browser QC.

## Current concurrency boundary

Kimi Code currently owns edits to:

- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/styles.css`
- `tests/test_frontend_medical_writing_contract.py`
- `frontend/tests/medical_writing_authoring_prefill_frontend_qc.mjs`

Do not edit those files in this pass. A real DeepSeek/ClinicalTrials.gov QC
worker is also running and may write only under:

`records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/prefill_ai_prod_qc_20260720/`

Do not overwrite its outputs.

## Product question

The product must behave as an AI authoring system, not a blank editor:

1. The user initially supplies only investigational product, indication, and
   phase.
2. The production `deepseek-v4-pro` prefill proposes an English
   ClinicalTrials.gov condition term and other low-risk framing candidates.
3. Once the medical manager adopts that condition term, the versioned search
   plan must be rebuilt.
4. The product should then complete the real public competitor search, bind
   the immutable snapshot, and regenerate the prefill package using the new
   evidence with clear progress and recoverable partial-failure states.
5. The user should not need to discover and repeat hidden cross-module
   operations, and there must be no second “待医学批准” gate for a candidate
   the medical manager already chose.
6. Exact clinical facts such as dose, regimen, endpoint, AESI, sample size,
   thresholds, washout, and visit timing remain blocked unless backed by
   explicit registered source IDs.

Inspect the actual backend and frontend flow, then answer:

- Does the current product fully close this loop for both new-project creation
  and later adoption of a revised English condition term?
- Which operations are currently automatic, which are merely available as
  buttons, and where can stale Chinese-condition snapshots or stale prefill
  packages survive?
- What is the smallest robust implementation that preserves idempotency,
  versioning, immutable snapshots, concurrency safety, source traceability,
  error recovery, and desktop-first progress visibility?
- Which backend contract and frontend interaction tests are missing?
- Are there edge cases for no results, registry timeout, AI timeout, stale
  revision, user switching projects, repeated adoption, and mixed RA/PNH
  result sets?

## Execution expectation

This pass is an evidence-grounded audit because the active Kimi write set must
not be conflicted. You may run read-only tests, browser inspection, and real
local API calls that do not mutate stable production data. Do not modify the
locked files above. If a disjoint, clearly safe test-only artifact is essential,
you may create it under:

`records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/qoder_ai_first_research_loop_20260720/`

Return a compact execution report in your final response containing:

1. exact sources and runtime surfaces inspected;
2. observed current behavior;
3. prioritized defects with concrete file/function references;
4. proposed API/state-machine sequence;
5. exact test matrix;
6. implementation steps and disjoint write scopes;
7. residual uncertainty.

Do not claim final clinical, visual, or production acceptance. Codex is the
final authority.
