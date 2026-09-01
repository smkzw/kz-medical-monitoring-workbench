# Task Context: mw_a1_triage_finalize_r8

Created: 2026-07-28 19:24:36
Objective: 修复医学写作竞品篮子确认后下游仍判定分诊未完成的状态合同，并从全新clean round复测A1
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/handoffs/CODEX_NO_LOSS_PAUSE_A1_R8_20260728.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r8-20260728/slots/A1/lazy_medical_writer/DEFECTS.md`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/writing_reference_preparation_batch.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/main.py`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- Existing focused tests adjacent to those modules.
- Frozen r8 runtime evidence is read-only and must not be reused as a passing run.

## Scope

- In scope:
  - remove the pre-PICOS circular dependency where preparation accepts an
    authoritative confirmed discovery basket but translation requires
    post-PICOS finalized corpus triage;
  - derive one authoritative retained-candidate scope from finalized corpus
    triage when present, otherwise from the current confirmed discovery basket;
  - require exact locked snapshot and authoritative confirmation lineage;
  - make the user's one bulk `确认并锁定全部` action advance the research
    pipeline without a second “确认分诊后继续” click;
  - preserve idempotency, durable retry/re-entry and fail-closed stale lineage;
  - add deterministic service/API/frontend tests.
- Writable product scope:
  - `services/api/app/writing_reference_translation_batch.py`
  - `services/api/app/medical_writing_research_pipeline.py`
  - `services/api/app/main.py`
  - `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
  - focused adjacent tests only.
- Read-only reference:
  - competitor-triage, authoring-journey and preparation-batch implementation;
  - all r8 evidence and databases.
- Out of scope:
  - changing clinical classifications, corpus content or prompts;
  - weakening content validation or corpus admission;
  - manual/corpus-gate override;
  - production/shared runtime writes;
  - starting the next E2E round or claiming PASS;
  - unrelated UI redesign.

## Success Criteria

- A confirmed discovery basket for the current locked snapshot may drive
  preparation and translation before PICOS completion.
- Finalized corpus triage remains preferred after PICOS completion.
- Missing, stale, wrong-snapshot or non-authoritative discovery projection
  remains blocked.
- Translation scope and frozen-lineage validation use the same effective
  retained-candidate authority.
- One bulk confirmation action advances the parent from
  `awaiting_triage_confirm`; repeat/reload is idempotent and does not duplicate
  download/extraction.
- No per-candidate confirmation is introduced.
- Existing post-PICOS and corpus-finalized paths remain passing.
- Focused unit/API/frontend tests and adjacent regressions pass.
- Codex will create a new immutable clean round and perform browser acceptance;
  delegated output cannot establish release acceptance.

## Risk Boundaries

- Do not write to shared product runtime or frozen r8 evidence.
- Do not mutate the authoritative confirmed basket merely to satisfy
  translation.
- Do not equate `discovery_projected` with final corpus admission; it is only
  authority for document preparation/translation needed to inform PICOS.
- Do not make a second user approval mandatory.
- Do not edit files outside the explicit writable scope.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-28 19:24:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-28 19:24-19:30: Codex re-anchored from the no-loss pause and
  identified the preparation/translation authority mismatch and stale parent
  pipeline as the shared cause of `MW-A1-002`.
- 2026-07-28 19:27-19:30: Codex reread the current global AGENTS contract
  (`1d54ff677fb83d271492b32cecaa15b329f033d11e1759cb1fcb55c6bf0cab6a`),
  verified the Aishuo route was inside its allowed start window, expanded the
  task prompt into an explicit fail-closed read set, and passed workflow
  preflight with no warnings or errors.
- 2026-07-28 19:30: The finite-code execution worker started on
  `Hermes/aishuo/cms-model` at `high`, with a 128-turn budget and 7200-second
  hard wait. Frozen r8 evidence remains read-only; no new E2E round has been
  created.
- 2026-07-28 19:53-20:17: Hermes completed the first repair; Cursor CLI/auto
  execution management found and remediated a stale-finalized-snapshot scope
  bug plus a durable business-key collision. Codex conflict review then found
  that the resumed pipeline still re-confirmed/recomputed the medical
  manager's basket. The same Hermes session completed a targeted follow-up:
  the exact confirmed retained IDs now flow through the durable payload and
  synchronous path, and the confirmed resume never calls the triage confirm
  or legacy finalize helpers.
- 2026-07-28 20:18: Codex reran the focused backend/API/frontend suites:
  `66 passed`; frontend triage projection: `14 passed`. Harness/runtime/baseline
  regressions: `69 passed`.
- 2026-07-28 20:19: Frozen source receipts were expanded from 53 to 57 so the
  critical translation implementation and its focused tests are covered.
  Harness validation returned `VALID` with all 57 hashes matching.
- 2026-07-28 20:20: New immutable round `release-r9-20260728` created with
  input fingerprint
  `5d787256352646b2608d8ccced2a930b7e925452babbcca5454db6e0f0a8fd5f`.
  A1 lazy runtime started at backend `51564`, frontend `51565`, runtime identity
  `7ea35114464a8e92a627844b5cd6a1365a1769b8b4d8aa80b58eeac2746bb856`.
  Product source is now frozen until this run reaches a terminal result.
