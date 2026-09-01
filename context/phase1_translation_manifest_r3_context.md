# Task Context: phase1_translation_manifest_r3

Created: 2026-07-16 17:37:48
Objective: Complete current-contract Phase I competitor protocol translation manifests, regenerate stale small-molecule/RNA candidates, and verify the medical-writing runtime without admitting unreviewed text
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User-approved recovery boundary: `records/active_slices/medical_writing_phase1_autoimmune_mnc_corpus_20260716/SOFT_PAUSE_RESUME.md`.
- Current source selections: `translations/biologic_translation_selection.json` and `translations/translation_selection.json` under the same active slice.
- Current biologic candidates: `flash_biologic_current_glossary_batch_v4.json`, `flash_biologic_targeted_corrections_v1.json`, and `flash_biologic_nct04668066_correction_v2.json`, with matching audit JSONL files.
- Production translation contract is defined by `services/api/app/writing_reference.py`, `services/api/app/ai_gateway.py`, and `services/api/assets/medical_writing_glossary/regulatory_translation_glossary_v1.json`.
- Runtime evidence is the live workbench services on 5174/8911 and direct DeepSeek helpers on 8934/8935. Secrets must never be printed or persisted.

## Scope

- In scope: deterministic manifest builder, current-contract biologic manifest, current-contract regeneration and review manifest for the ten eligible small-molecule/RNA segments, focused/broad tests, compile checks, stable runtime restart and status verification, and durable task records.
- Out of scope: medical approval, corpus admission, held Phase 1/2 PNH RNA boundary segments, changes to original Protocol files, and unrelated medical-writing UI changes.

## Success Criteria

- Manifest builder rejects duplicate IDs, stale source hashes, wrong provider/model/prompt/contract, failed automatic gates, and non-pending medical/corpus statuses.
- Biologic manifest has exactly eight unique selected current-contract records, automatic pass 8/8, medical approval 0, corpus admission 0.
- Small-molecule/RNA manifest has exactly ten eligible current-contract records under v0_5/r3, automatic pass 10/10, medical approval 0, corpus admission 0.
- Relevant tests and compile checks pass after the final code state.
- Stable 8911 loads the final code and reports general Pro plus translation Flash; SQLite integrity/schema and frontend 5174 pass.
- Task record and subsystem log preserve commands, observations, failed paths, decisions, and exact resume state.

## Risk Boundaries

- Allowed writes are limited to the active slice, its translation manifests/audit outputs, scoped tests, the translation/glossary implementation when a verified defect requires it, and task/run/review/metrics records.
- `medical_qa_pending` is not medical approval; no candidate may be admitted to the production corpus in this task.
- Do not weaken correct fidelity gates to obtain a passing batch.
- Direct `deepseek-v4-flash` is the independent production translation route; Codex reviews evidence but does not substitute its own translation as runtime output.
- Preserve all failed and stale batch files as audit history; do not overwrite them as if current.
- Codex remains final authority for source fidelity, runtime verification, and production writes.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-16 17:37:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-16 17:39: Recovery record, global/project instructions, selections, manifests, and runtime contract reread. Decision: create a deterministic manifest builder before running new translation batches.
- 2026-07-16 17:39: Builder and focused test file added, then user explicitly requested no-loss pause before any execution. No translation/test/manifest process remains. On resume, review import setup and run the focused test first.
- 2026-07-16 resumed: builder verified and extended to re-run current fidelity gates. Biologic manifest rebuilt at 8/8 automatic pass; small-molecule/formulation translations completed a four-round language-quality loop and final manifest rebuilt at 10/10. Medical approvals and corpus admissions remain zero.
- 2026-07-16 verification: 101 related tests passed; compileall passed; all runtime SQLite integrity checks passed; stable 5174/8911 returned HTTP 200. General AI reports direct DeepSeek Pro and translation AI reports direct DeepSeek Flash, both without Codex runtime dependency.
- 2026-07-16 infrastructure observation: local proxy caused false 502 results; nohup child was reaped by the exec environment; launchctl could not safely run the Unicode Documents path. Decision: use detached screen for the stable API and macOS Keychain for the credential, without granting broader filesystem permissions.
