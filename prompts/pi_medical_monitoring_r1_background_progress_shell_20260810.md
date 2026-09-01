You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the current workspace (`.`).
- Do not read or modify production paths.
- This is an explicitly authorized bounded edit round. Modify only paths allowed by the task context. Existing accepted runtime/controller/store/audience-progress and existing UI slice sources are read-only references.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_medical_monitoring_r1_background_progress_shell_20260810.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_r1_background_progress_shell_20260810_context.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/audience_progress.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/controller.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`
- `poc/medical_monitoring_ai_native_r1/docs/R1_AUDIENCE_PROGRESS_EVIDENCE.md`
- `poc/medical_monitoring_ai_native_r1/docs/R1_CONTROLLER_BINDING_EVIDENCE.md`
- `poc/medical_monitoring_ai_native_r1/tests/conftest.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_controller.py`
- `poc/medical_monitoring_ai_native_r1/tests/test_audience_progress.py`
- `poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench`
- `poc/medical_monitoring_ai_native_r1/slices/patient_journey`

Task:
Implement the bounded synthetic background-progress shell described in the task context. Build the smallest coherent, dependency-neutral integration that:

1. runs application-owned synthetic work asynchronously without needing an open progress page or active polling;
2. derives every audience progress response only from `project_audience_progress(store, run_id)` and never maintains a second completed/total/percent state;
3. exposes a strict audience-only schema to a calm, Chinese-native single-page progress shell;
4. supports leaving the progress view, returning, browser refresh and facade reconstruction against the same SQLite state without duplicate dispatch;
5. uses only fictional synthetic data and, for browser tests, loopback ephemeral port `127.0.0.1:0` that is closed after each test;
6. adds focused Python/contract/browser tests but does not touch product code, existing accepted slices, real projects, providers or 8911.

Keep engineering internals out of rendered text. The user-facing page should show a precise progress bar, `已处理 x/y 项`, stage rows, current work and a restrained rolling update list. It should make clear that the user may leave and return while work continues. Handle failed/blocked states truthfully. Prefer standard library mechanisms; do not introduce a framework decision or external package.

Run focused deterministic tests you can run safely. Do not claim final visual acceptance. Return a compact handoff with files changed, architecture, commands/results, known gaps and exact Codex verification targets.

Output schema:
1. `# Hermes Execution Handoff: medical_monitoring_r1_background_progress_shell_20260810`
2. `## Boundary Check`
3. `## Files Changed`
4. `## Implementation`
5. `## Verification Performed`
6. `## Codex-Owned Verification`
7. `## Residual Risk And Next Safe Action`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Do not edit runner-owned report files under `runs/`.
- No completion claim without real command output; keep the handoff compact.
