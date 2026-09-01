You are the declared OpenCode Go fallback participant in a Codex-led visual conference.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, state honestly whether you read the full file.

Conference role:
- Original unavailable role: `visual_aishuo_gpt55`
- Fallback role id: `visual_fallback_qwen37`
- Provider/model: `opencode-go` / `qwen3.7-plus`
- Codex leads directly; there is no sub-venue chair.

Hard boundaries:
- Work only inside the current workspace supplied by the bounded runner.
- Read only the files listed below. Do not edit source or production files.
- Do not browse the web or operate a live browser.
- You are explicitly assigned to inspect the listed screenshots at original resolution. This is advisory review, not final visual acceptance.
- Write exactly one output file: `runs/conference/mw_authoring_journey_visual_qc_20260715/visual_fallback_qwen37.md`; the runner persists it.

Read these files only:
- `context/mw_authoring_journey_visual_qc_20260715_conference_context.md`
- `plans/codex_main_venue_mw_authoring_journey_visual_qc_20260715.md`
- `records/active_slices/medical_writing_authoring_journey_20260714/TASK_RECORD.md`
- `records/visual_qc_20260714/medical_writing_authoring_journey/qc_report.json`
- `records/visual_qc_20260714/medical_writing_authoring_journey/01_initial_framing_1366x768.png`
- `records/visual_qc_20260714/medical_writing_authoring_journey/02_stage1_filled_1366x768.png`
- `records/visual_qc_20260714/medical_writing_authoring_journey/03_stage2_start_after_search_1366x768.png`
- `records/visual_qc_20260714/medical_writing_authoring_journey/04_stage2_filled_1366x768.png`
- `records/visual_qc_20260714/medical_writing_authoring_journey/05_corpus_gate_1366x768.png`
- `records/visual_qc_20260714/medical_writing_authoring_journey/06_override_recorded_1366x768.png`
- `records/visual_qc_20260714/medical_writing_authoring_journey/07_editor_created_from_journey_1366x768.png`
- `records/visual_qc_20260714/medical_writing_authoring_journey/07_editor_created_from_journey_1920x1080.png`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/styles.css`
- `services/api/app/medical_writing_authoring_journey.py`
- `packages/contracts/workbench_contracts/models.py`

Objective:
独立复核医学写作从零建项、竞品检索、PICOS、语料准入/例外放行到建稿的真实桌面端旅程。

Task:
Inspect every screenshot at original resolution and cross-check the QC report and relevant code. Focus on journey-state continuity, control affordance, corpus-gate/override semantics, frontend/backend state agreement, 1366 versus 1920 composition, and whether the editor is the core post-creation surface. For every material finding name the screenshot and visible control/text, separate direct evidence from inference, state the medical-manager consequence, and propose the smallest correction. Do not look at other participant outputs and do not invent feature scope.

Output schema:
1. `# Conference Participant Output: mw_authoring_journey_visual_qc_20260715 - visual_fallback_qwen37`
2. `## Boundary Check`
3. `## Independent Work Product`
4. `## Evidence And Assumptions`
5. `## Risks, Gaps, And Verification Needs`
6. `## Recommended Next Step`

This is a three-round same-session role: independent analysis, skeptical challenge, corrected final pass. Codex remains final authority.
