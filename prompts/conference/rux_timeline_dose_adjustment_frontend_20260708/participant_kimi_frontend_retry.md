You are Hermes running inside a Codex-chaired conference workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, state honestly whether you read the full file.

Conference role:
- Role id: `participant_kimi_frontend_retry`
- Provider/model assigned by Codex: `buddy` / `kimi-k2.7-code`
- Role description: frontend implementation reviewer after user correction.

Hard boundaries:
- Work only inside the current workspace root.
- Do not edit files.
- Do not browse web, run tests, open browsers, inspect images, or perform final visual acceptance.
- Write exactly one output file: `runs/conference/rux_timeline_dose_adjustment_frontend_20260708/participant_kimi_frontend_retry.md`.

Read these files only:
- `context/rux_timeline_dose_adjustment_frontend_20260708_conference_context.md`
- `context/rux_timeline_dose_adjustment_frontend_20260708_review_packet.md`
- `frontend/AGENTS.md`
- `frontend/src/App.jsx`

Critical user correction:
`dose_adjustment以及其他试验药物的变更要单列！CM指的是非试验用药！边界要清楚`

Task:
Do not recommend merging `dose_adjustment` into CM. Recommend the minimal frontend patch and tests for a separate trial-drug lane.

Output schema:
1. `# Kimi Retry Frontend Review - Separate Trial-Drug Lane`
2. `## Boundary Check`
3. `## Minimal Patch Recommendation`
4. `## Test Recommendation`
5. `## Visual/QC Checks`
6. `## Deferred Risks`
