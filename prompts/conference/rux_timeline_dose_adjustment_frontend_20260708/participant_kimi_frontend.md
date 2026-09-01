You are Hermes running inside a Codex-chaired conference workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, state honestly whether you read the full file.

Conference role:
- Role id: `participant_kimi_frontend`
- Provider/model assigned by Codex: `buddy` / `kimi-k2.7-code`
- Role description: frontend implementation reviewer for the RUX Subject Timeline dose-adjustment slice.

Hard boundaries:
- Work only inside the current workspace root.
- Do not edit files.
- Do not browse web, run tests, open browsers, inspect images, or perform final visual acceptance.
- Write exactly one output file: `runs/conference/rux_timeline_dose_adjustment_frontend_20260708/participant_kimi_frontend.md`.

Read these files only:
- `context/rux_timeline_dose_adjustment_frontend_20260708_conference_context.md`
- `context/rux_timeline_dose_adjustment_frontend_20260708_review_packet.md`
- `frontend/AGENTS.md`
- `frontend/src/App.jsx`
- `tests/test_rux_monitoring_service.py`

Objective:
Produce a minimal frontend patch/test recommendation for rendering `dose_adjustment` events correctly in the existing Subject Timeline without redesigning the app.

Task:
Review the current implementation and packet. Recommend exact minimal changes and tests. Do not produce a full patch; Codex will implement after TDD.

Output schema:
1. `# Kimi Frontend Review`
2. `## Boundary Check`
3. `## Current-Code Finding`
4. `## Minimal Patch Recommendation`
5. `## Test Recommendation`
6. `## Visual/QC Checks`
7. `## Risks To Defer`

Quality gates:
- Keep the solution compatible with existing `timelineLaneDefs`, `eventTone`, `laneForEvent`, and `shortTimelineEventLabel`.
- Do not add a new page or broad state model.
- Do not claim browser acceptance.
