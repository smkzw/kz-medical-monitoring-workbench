You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the current workspace (`.`).
- Do not read or modify production paths.
- This is an explicitly authorized bounded edit round. Modify only the paths listed under `Risk Boundaries` in the task context; treat every existing accepted source/test/UI file as read-only.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_medical_monitoring_r1_integrated_closure_20260810.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_r1_integrated_closure_20260810_context.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `poc/medical_monitoring_ai_native_r1/README.md`
- `poc/medical_monitoring_ai_native_r1/scripts/run_demo.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1`
- `poc/medical_monitoring_ai_native_r1/tests`
- `poc/medical_monitoring_ai_native_r1/docs`
- `poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench`
- `poc/medical_monitoring_ai_native_r1/slices/patient_journey`
- `poc/medical_monitoring_ai_native_r1/slices/background_progress_shell`

Task:
Complete WI-1 through WI-4 in the task context. First audit R1 steps 1-13 and prove the current cross-slice breakpoints. Then implement the smallest framework-neutral integrated synthetic closure in the authorized new files only.

The integrated path must use one Store/run/accepted snapshot/manifest revision and existing application-owned contracts. Include one injected synthetic API capability work unit through `CapabilityWorkUnitController` without any real external call. AI output stays raw-first and candidate-only. Deterministic AE/MH/QC/projection outputs must share the same identity and evidence chain; Profile and Timeline must share one `SubjectTemporalSpine`; Query drafts must retain the established basis/finding/action structure. Audience progress must come only from `project_audience_progress`, with no second progress state.

Build explicit failure-closed and reopen/replay tests. Do not fake integration by copying identifiers from the existing static Patient Journey fixture. If an accepted API genuinely prevents the same-run chain, stop at a precise gap report rather than modifying accepted code. Do not install dependencies, call the network, start a service or read real data.

Run focused tests plus the R1 core suite you can safely run. Do not claim R1 overall acceptance or final browser/clinical acceptance.

Output schema:
1. `# Hermes Execution Handoff: medical_monitoring_r1_integrated_closure_20260810`
2. `## Boundary Check`
3. `## R1 Step 1-13 Audit`
4. `## Files Changed`
5. `## Integrated Contract Implemented`
6. `## Verification Performed`
7. `## Failed Paths And Residual Risk`
8. `## Codex-Owned Verification`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Do not edit runner-owned report files under `runs/`.
- Keep current accepted modules immutable; use composition.
- Completion claims require real command output and exact artifact paths.
