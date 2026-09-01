# Same-session completion: AI apply and persistence gate

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md` and the latest
`/Users/smkzw/.codex/AGENTS.md`. Continue Hermes session
`20260717_235733_a624c5`; do not repeat the four expensive DeepSeek candidate
generation calls, D017 import confirmation, or competitor plan/execute checks
that already passed.

## Hard boundaries

- Work only inside the current workspace.
- Use disposable runtimes and non-stable ports only.
- Do not touch stable databases, stable ports, credentials, original clinical
  documents, frontend source, or unrelated backend code.
- The product must use its configured direct DeepSeek supplier/model
  `deepseek-v4-pro`; Hermes output may not substitute for product output.
- Authorized product writes are limited to directly implicated medical-writing
  AI/apply/persistence modules and related tests, plus durable evidence under
  `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ai_final_qc/`.
- Write exactly one output file:
  `runs/execution/medical_writing_prelaunch_release_20260717_v2/ai_quality_remediation.md`.

Read these files only for initial context:

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ai_final_qc/ai_quality_remediation_results.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ai_final_qc/intent_medical_writing_revision_candidates.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ai_final_qc/intent_regulatory_tone_candidates.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ai_final_qc/intent_consistency_check_candidates.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ai_final_qc/intent_evidence_gap_candidates.json`
- `services/api/app/main.py`
- `services/api/app/medical_writing_repository.py`
- `tests/test_medical_writing_revision_application.py`

The initial list is not a blanket prohibition on later tools or evidence.
Record every additional target and why it was needed.

## Current evidence and exact remaining work

The timed-out pass has already proven:

- four substantive protocol intents through direct `deepseek-v4-pro`;
- 3-4 non-punctuation-only candidates per intent;
- CMS-D017 synopsis upload, review/confirm, framing/PICOS prefill;
- competitor search plan then execute.

Do not spend tokens regenerating these results. The only failed stage was the
test harness manually replacing block `text` without updating `rich_text`, so
the backend correctly returned `409 working copy rich text must match block
text`. This is evidence of a bad harness operation, not permission to weaken
the invariant.

## Required completion checks

1. Use the public revision-thread approval/application route
   `/medical-writing/working-copies/{section_id}/revision-threads/{thread_id}/apply`
   or the same production workflow exercised by the frontend. Do not manually
   mutate only `text`.
2. Use the already-created substantive candidate/thread if the disposable
   runtime remains available; otherwise recreate only the minimum thread
   needed from the already-saved candidate evidence, without repeating all
   four intent calls.
3. Approve/apply one candidate, verify synchronized `text` and `rich_text`,
   revision increment, exact audit snapshot, browser/API reload, and owned
   backend stop/start persistence.
4. Exercise undo/restore where the production contract supports it. Prove a
   stale revision is rejected and that no newer revision is overwritten.
5. Confirm the persisted thread/application is associated with the direct
   provider/model evidence and does not silently fall back to Hermes.
6. Update the durable results JSON so prior PASS stages remain visible and the
   new apply/reload/restart/stale checks are independently recorded.
7. Run focused revision-application, persistence, routing, and prompt-contract
   tests. Record exact commands/results.
8. Produce an exact PASS/FAIL/UNVERIFIED report with candidate usefulness
   assessment, D017/competitor evidence, apply/persistence evidence, residual
   uncertainty, and no hidden credentials or real full protocol text.

Only change product code if a real production-route defect is reproduced
after correcting the harness. Do not weaken rich-text/source/audit/concurrency
validation.

Use the required execution-report headings and finish the report before
ending the pass.
