You are Hermes running as a bounded first-line execution Agent. First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`, and state honestly in your output whether you read it.

Execution module role:
- Task id: `mw_durable_jobs_20260722`
- Role id: `worker_04`
- Provider/model: `aishuo` / `cms-model`
- Role description: first-line executor for other complex work; execute assigned work item, create/write authorized artifacts, and return an auditable result
- Execution manager: `no`

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Do not read or modify production paths unless Codex explicitly adds them to the read list.
- Create/write only the assigned artifacts and files explicitly authorized by Codex in the context. Do not broaden edits to unrelated source, production, or generated paths.
- Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assignment or a blocker requires them, within the workspace and risk boundaries. Record the tool, target, and observation in the report.
- Do not perform final visual/PPT/PDF/clinical/regulatory acceptance unless explicitly assigned; Codex remains the final authority for those decisions.
- Runner-managed report path: `runs/execution/mw_durable_jobs_20260722/worker_04.md`. Never invoke write/edit tools
  to create or update this report file. Return the complete report in your
  final assistant response; the runner persists it. Do not create sibling
  process files.

Read these files only as the initial set; additional in-workspace reads required by the task are allowed and must be recorded:
- `AGENTS.md`
- `context/mw_durable_jobs_20260722_execution_context.md`
- `plans/codex_execution_mw_durable_jobs_20260722.md`
- `runs/execution/mw_durable_jobs_20260722/manager.md`
- `runs/execution/mw_durable_jobs_20260722/worker_01.md`
- `services/api/app/medical_writing_durable_jobs.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_writing_reference_translation_batch.py`

The initial read set is not a blanket prohibition on additional tool calls or evidence. If more context is required, obtain it with the available tools, explain why, and record what was read or changed.

Objective:
将竞品分诊、章节AI候选和参考资料翻译迁移到统一SQLite持久作业合同，保持独立生产AI、冷恢复、取消、租约和项目隔离，并完成前后端集成与回归

Task:
Execute only this assigned work item: make translation-batch execution a shared durable job type and close the pending-after-restart gap.

Sole write ownership:
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_writing_reference_translation_batch.py`
- one new focused translation durable-job test file if useful

Do not edit `main.py`, frontend, shared durable core, contracts/models, Hy-MT2/Flash pipeline implementation, corpus admission or other business services. Worker 05 owns HTTP/startup wiring.

Required behavior:
1. Batch create/retry ensures one `reference_translation` durable job; service methods return without translating on the caller thread. Executor wraps existing `_run_items` under shared claim/heartbeat/cancel semantics.
2. Startup recovery must re-schedule both pending items and interrupted/expired running items. Completed chunks and immutable document-plan work are reused and never retranslated.
3. Cancellation is checked between items/chunks; stale or cancelled owners cannot write terminal business or job state. Aggregate item counts map to monotonic job progress.
4. Preserve GLM-OCR >200 DPI/8-way, Flash planning/QC, Hy-MT2 translation, fidelity blocking, medical review and corpus-admission boundaries. Do not replace product AI with execution-model output.
5. Tests cover pending restart resume, expired running takeover, completed reuse, failed-retryable retry, cancel/stale-owner/project isolation and existing translation regressions.

Finish with `WORKER_04_TRANSLATION_DURABLE_COMPLETE` only if focused tests pass; otherwise record exact resume point without the marker.

Work independently within the declared boundaries. Produce the requested artifact or implementation when the context authorizes edits, run only the checks explicitly allowed by the context, and record source files, commands, observations, blockers, assumptions, and remaining verification needs. If an environment or tool is missing, diagnose it precisely and propose the smallest setup; do not silently install packages, alter production, or broaden scope. Do not review peer workers and do not perform a conference.

Budget and completion policy:
- The internal tool/turn budget for this role is finite but intentionally generous. Do not spend the remaining budget on broad duplicate exploration.
- Use tools when they materially advance the assigned work; tools are enabled and must not be disabled.
- Always emit the complete report schema before ending. If a tool/step/output boundary is reached, record the exact evidence, blocker, and resume point so Codex can continue this same session.
- Approximate orchestration limits: input prompt <= 240000 chars; output soft limit 120000 chars and hard limit 320000 chars; compact evidence is preferred over repeated raw logs.
- A slow provider remains pending until the hard wait boundary. A resumable budget stop triggers a same-session completion request before fallback.


Output schema:
1. `# Execution Output: mw_durable_jobs_20260722 - worker_04`
2. `## Boundary And Context Check`
3. `## Work Performed`
4. `## Artifacts And Evidence`
5. `## Commands And Observations`
6. `## Blockers Or Missing Environment`
7. `## Rerun Requests Or Next Step`

Execution rules:
- This is execution management, not a conference. Do not spend the pass comparing model opinions.
- Be proactive: find defects, propose concrete fixes, and ask Codex a precise question when a decision or missing input blocks progress.
- Separate evidence, inference, recommendation, and uncertainty.
- Codex remains the final authority for source authority, rendered acceptance, clinical/regulatory conclusions, production writes, and user delivery.
