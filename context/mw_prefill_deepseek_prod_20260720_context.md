# Task Context: mw_prefill_deepseek_prod_20260720

Created: 2026-07-20 00:02:43
Objective: Integrate direct production deepseek-v4-pro into medical-writing AI-first prefill, including English ClinicalTrials.gov condition-term generation, evidence-bounded package ranking/phrasing, two-real-indication tests, and deterministic fallback
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: user-overridden first priority `qodercli PID 39908` /
`Qwen3.8-Max-Preview`; Codex remains final authority.

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_fact_intake.py`
- `services/api/app/ai_gateway.py`
- `services/api/app/main.py`
- `services/api/app/writing_reference.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_authoring_journey.py`
- `tests/test_ai_gateway.py`
- `frontend/tests/medical_writing_authoring_prefill_frontend_qc.mjs`
- `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/TASK_RECORD.md`
- Current direct production route: provider `deepseek`, model
  `deepseek-v4-pro`, OpenAI-compatible transport, with response model identity
  verification. This route must be called directly by the workbench, not via
  Codex or Hermes.
- Official external references:
  - `https://api-docs.deepseek.com/guides/json_mode`
  - `https://api-docs.deepseek.com/api/create-chat-completion/`
  - `https://clinicaltrials.gov/data-api/about-api/search-areas`
  - `https://clinicaltrials.gov/data-api/about-api/study-data-structure`
- Observed runtime evidence:
  - The current deterministic package is structurally working and passes
    adoption/revision tests.
  - RA and PNH frontend runs both returned zero ClinicalTrials.gov rows because
    the fallback copied the Chinese indication into `query.cond`.
  - Official `query.cond` searches Condition, titles, MeSH terms and keywords;
    an English registry term is required for reliable retrieval in this flow.

## Scope

- In scope:
  - Create a production DeepSeek prefill adapter/service with one bounded bulk
    model call per generation stage, not one call per field.
  - Generate and validate an English ClinicalTrials.gov condition term from the
    confirmed drug/indication/phase creation minimum before public search.
  - After a real search snapshot exists, rank and phrase 3-5 materially distinct
    candidates from the confirmed study facts plus snapshot evidence.
  - Preserve deterministic candidates as an observable fallback when the AI
    route is disabled, times out, returns invalid JSON, or fails validation.
  - Wire the adapter through the existing API route without putting network
    calls inside an open SQLite write transaction.
  - Record model name, prompt version, source fingerprints and partial failures.
  - Add focused unit/contract tests and isolated runtime evidence for at least
    rheumatoid arthritis Phase II and PNH Phase III.
- Out of scope:
  - Frontend files currently owned by the Kimi frontend worker.
  - Automatic adoption or a second medical-approval object.
  - Fabricating exact dose, regimen, washout, endpoint, AESI, sample-size or
    statistical facts without direct project/protocol evidence.
  - General redesign of ClinicalTrials.gov ingestion or document translation.
  - Stable runtime `5174/8911` data or destructive migration.

## Success Criteria

- A new project still needs only drug, indication and phase.
- For Chinese indications, the production route proposes an English registry
  condition term such as `Rheumatoid Arthritis` or
  `Paroxysmal Nocturnal Hemoglobinuria`; the value remains an AI candidate until
  the medical manager adopts it.
- Public search uses the adopted English term and returns a real snapshot when
  ClinicalTrials.gov is reachable.
- A post-search package contains 3-5 distinct, evidence-traceable options where
  evidence supports alternatives; otherwise it returns fewer rather than
  padding duplicates.
- AI output may reorder, select or add evidence-grounded candidates but cannot
  change field paths, cite nonexistent source IDs, or promote exact clinical
  facts without source text.
- Provider calls happen outside the `BEGIN IMMEDIATE` transaction; the final
  persistence step rechecks the expected journey revision and package
  fingerprint.
- Provider unavailable/invalid output yields deterministic partial output plus
  a clear `partial_source_failures` entry, not an HTTP 500 and not an empty UI.
- Existing adoption authority, idempotency, conflict handling, state hashes and
  stale-package behavior remain green.
- Focused tests, broader related regression, Ruff on changed files, and two
  real-indication isolated API runs pass.

## Risk Boundaries

- Allowed write paths:
  - `services/api/app/medical_writing_authoring_prefill_ai.py` (new, if useful)
  - `services/api/app/medical_writing_authoring_prefill.py`
  - `services/api/app/medical_writing_authoring_journey.py`
  - `services/api/app/main.py`
  - `packages/contracts/workbench_contracts/models.py` only when metadata
    contract changes are essential
  - directly related new or existing `tests/test_medical_writing_*prefill*.py`
  - `runs/qoder_mw_prefill_deepseek_prod_20260720.md`
- Do not edit frontend files, stable runtime databases, unrelated services,
  global config, credentials or the runner-reserved Codex report path.
- Never log API keys, authorization headers, private source contents or raw
  production request bodies.
- Existing user edits and unrelated dirty files must be preserved.
- Qoder output is evidence; Codex owns source review, actual model/runtime
  verification, medical/regulatory judgment and final acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-20 00:02:43: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-20 00:06:00: Codex reproduced the zero-result RA/PNH search and
  identified the Chinese `query.cond` fallback as a production blocker.
- 2026-07-20 00:06:00: Official DeepSeek JSON mode and ClinicalTrials.gov
  search-area documentation were checked. Selected architecture is a bounded
  direct-model structured-output adapter plus deterministic fallback.
