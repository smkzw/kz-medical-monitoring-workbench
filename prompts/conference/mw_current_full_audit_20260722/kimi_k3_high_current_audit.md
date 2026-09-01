# Independent Current Medical-Writing Audit — Kimi Code/k3(high)

You are the independent Kimi audit participant. Use the already-running interactive Kimi Code process with model `kimi-code/k3`, thinking effort `high`, and the configured 192-step loop budget. Do not switch models, start a substitute process, or use your own model output in place of the system-under-test's independently configured production AI.

Change working directory to `./medical-writing-current`, the task-scoped symlink supplied in the current Kimi terminal directory.

## Hard boundaries

- This is an independent read-only audit, intentionally not a summary of Qoder.
- Do not edit production source/tests, runtime databases, stable services, or user documents.
- Run read-only searches/tests with bytecode and pytest caches disabled. Existing ports 5180/8910 are stale qoderwork and must not be used as current acceptance evidence.
- Do not perform final clinical, regulatory, visual, Word, or production acceptance.
- Runner-managed report path: `runs/conference/mw_current_full_audit_20260722/kimi_k3_high_current_audit.md`. Output exactly this one file.

## Read these files only

Initial read set:

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `context/mw_current_full_audit_20260722_conference_context.md`
- `plans/codex_main_venue_mw_current_full_audit_20260722.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/CURRENT_GAP_MATRIX.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/END_TO_END_PROGRESS_AUDIT.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/PROTOCOL_ASSEMBLY_PLAN_DECISION.md`

The initial list is a starting packet. Read additional current source/tests only when needed to verify a finding and record the path and reason.

Act simultaneously as:
- a lazy but highly experienced Chinese medical writer who expects AI to research and prefill, then only reviews/modifies;
- a clinical-design reviewer covering Phase I and Phase III non-oncology designs;
- a frontend interaction/visual consistency reviewer;
- a backend/API/concurrency and DOCX-contract reviewer.

Independently traverse and challenge the full path: minimum project facts; greenfield and synopsis import; optional/no IB; conversational fact intake; modality/route and multi-part Phase I; competitor/IB/product-AI pipeline; corpus/provenance; StudyDefinition binding; author confirmation/freeze; dynamic section/applicability projection; synopsis/chapter/SoA/flowchart/table consistency; rich editor; AI candidate/revision intents; literature identity/reindex/citation; DOCX/TOC/styles/attachments; errors/restarts/concurrency/cross-project isolation.

Use current source/tests and decisive probes. Do not merely enumerate features. Locate each high-impact friction or defect, explain the human workflow consequence, provide an exact reproducer or failing-test design, and distinguish current evidence from hypotheses. Explicitly identify where the system still behaves like an editor with AI attached instead of an AI-first writer. Verify that product AI rather than Kimi performs AI business steps.

Write the complete report to the allowed report path and finish with:
`KIMI_CURRENT_AUDIT_COMPLETE`

Required sections:
1. model/session/boundary confirmation;
2. real medical-writer journey map and friction inventory;
3. technical current-source findings with locators/reproducers;
4. visual/interaction findings and desktop-first recommendations;
5. independent-product-AI boundary;
6. cross-module conflicts and edge cases;
7. prioritized repair/test plan;
8. disagreements or complementary angles relative to the stated rebaseline records;
9. loop trace and residual uncertainty.
