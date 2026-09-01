# Execution Context: mw_release_p0_resume_20260720

Created: 2026-07-20 18:21:53
Objective: Close the remaining medical-writing P0 product gaps after soft-pause recovery and prepare independent-AI 12-lane release validation.
Task type: `complex_delivery_conference`
Risk: `critical`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `complex_executor_cms` -> `hermes` / `aishuo` / `cms-model`
- Execution manager: user-overridden `qoder_manager` -> existing visible
  `~/Downloads/QoderVIP` qodercli / `Qwen3.7-Max`
- Execution-manager fallback: `use the declared role fallbacks`

## Source Of Truth

- `records/active_slices/medical_writing_final_release_e2e_20260720/TASK_RECORD.md`
- `records/active_slices/medical_writing_final_release_e2e_20260720/SOFT_PAUSE_RESUME.md`
- `runs/execution/mw_synopsis_import_latency_p0_20260720/hy3_readonly_audit.md`
- `runs/execution/mw_cross_project_document_contamination_p0_20260720/qoder_qwen37max_readonly_audit.md`
- Current product source and focused tests in this workspace.
- Stable runtime and user originals are read-only evidence; implementation and
  destructive tests use isolated runtime only.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- Qoder manager is read-only for product source in its first pass and writes
  only `runs/execution/mw_release_p0_resume_20260720/manager_plan.md`.

## Work Items

1. Implement resumable asynchronous synopsis import with truthful progress, cancellation/retry, and DeepSeek v4-pro source-fidelity repair.
2. Implement StudyDefinition fingerprint binding and fail-closed quarantine/migration for legacy or stale working copies across editor, preview, and DOCX export.
3. Unify user-selection-is-confirmation semantics across backend contracts, API state, audit records, and frontend without a second medical approval.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
