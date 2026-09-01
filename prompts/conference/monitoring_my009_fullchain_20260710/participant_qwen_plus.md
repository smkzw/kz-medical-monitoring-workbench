You are Hermes running inside a Codex-chaired conference workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, state honestly whether you read the full file.

Conference role:
- Role id: `participant_qwen_plus`
- Provider/model assigned by Codex: `opencode-go` / `qwen3.7-plus`
- Role description: participant model; default reasoning effort; must be smoke-tested because it recently failed intermittently
- Conference mode: `parallel`

Hard boundaries:
- Work only inside the workbench directory supplied as your current working directory.
- Do not read or modify production paths unless Codex explicitly added them to the read list.
- Do not edit source files unless Codex explicitly authorizes an edit round.
- Do not browse web, run tests, open browsers, inspect images, or perform visual/PPT/browser acceptance unless explicitly assigned.
- Write exactly one output file: `runs/conference/monitoring_my009_fullchain_20260710/participant_qwen_plus.md`.

Read these files only:
- `context/monitoring_my009_fullchain_20260710_conference_context.md`
- `plans/codex_main_venue_monitoring_my009_fullchain_20260710.md`
- `records/research/medical_monitoring_external_benchmark_20260710.md`
- `records/active_slices/monitoring_my009_fullchain_20260710/SOURCE_AUDIT.md`
- `logs/subsystems/medical_monitoring_log.md`
- `frontend/src/App.jsx`
- `tests/test_frontend_monitoring_contract.py`
- `tests/test_frontend_timeline_contract.py`

Objective:
Design and implement a reusable two-real-project medical-monitoring chain for RUX-03-002 and MY009-UC from original listing and protocol, including subject catalog, subject timeline, patient profile, risk inbox, incremental batch boundaries, privacy, independent-AI prompts, desktop interactions, and cross-project fail-closed tests.

Task:
Run an independent whole-workflow pass from medical-monitor/product-design perspective. Do not look at other participant outputs. Define the desktop information architecture and concrete interaction chain from manual listing upload -> batch validation -> risk queue -> risk detail -> Subject Timeline/Patient Profile -> internal disposition. Specify empty/loading/error/first-batch/diff states, exact user-facing Chinese boundaries, controls that must work, and browser assertions. Critique current RUX-only wording and any MY009 demo-fallback risk. Do not edit code.

Output schema:
1. `# Conference Participant Output: monitoring_my009_fullchain_20260710 - participant_qwen_plus`
2. `## Boundary Check`
3. `## Independent Work Product`
4. `## Evidence And Assumptions`
5. `## Risks, Gaps, And Verification Needs`
6. `## Recommended Next Step`

Quality gates:
- Preserve evidence, inference, recommendation, and uncertainty as separate categories.
- Do not claim final clinical/regulatory/visual/current-web authority.
- Do not collapse other model perspectives into your own unless your role is chair/main reviewer and the files are explicitly in the read list.
- Slow or missing participant output is `pending`, not failed, unless it meets the conference failure rule.
