You are Grok Build continuing the same execution-manager session. Follow workspace `AGENTS.md`.

Read these files only:
- `AGENTS.md`
- `context/mw_soa_frontend_execution_20260717_execution_context.md`
- `runs/execution/mw_soa_frontend_execution_20260717/worker_01.md`
- `runs/execution/mw_soa_frontend_execution_20260717/worker_02_round2.md`
- `runs/execution/mw_soa_frontend_execution_20260717/worker_03_round2.md`

Hard boundaries:
- Work only inside the current workspace `.`.
- Do not edit product code or tests.
- Do not perform new broad research unless one missing fact is essential; the prior same-session pass already gathered evidence.

Write exactly one output file: `runs/execution/mw_soa_frontend_execution_20260717/manager_completion.md`.

The previous pass established a valid session and gathered evidence but was cancelled while starting the report. Return the complete implementation-ready manager report now. Do not use a file-writing tool and do not return planning narration; put the full report in the final response for runner persistence.

The report must contain these headings exactly:
- `# Execution Output:`
- `## Boundary And Context Check`
- `## Work Performed`
- `## Artifacts And Evidence`
- `## Commands And Observations`
- `## Blockers Or Missing Environment`
- `## Rerun Requests Or Next Step`

It must consolidate the three workers, challenge unsupported assumptions, preserve the Codex architecture decisions in the earlier manager prompt, and provide:
- exact failing tests and behavioral contracts;
- exact zero/one/multiple candidate state machine;
- exact bounded read/write set;
- ordered implementation plan and rollback boundary;
- exact focused test commands;
- one precise same-session Kimi implementation prompt;
- one precise same-session Grok cross-QC prompt;
- evidence/source links actually verified in the prior pass and any uncertainty.

Do not claim implementation or final UX acceptance.
