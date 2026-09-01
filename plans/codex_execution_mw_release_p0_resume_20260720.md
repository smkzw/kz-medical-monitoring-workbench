# Codex Execution Plan: mw_release_p0_resume_20260720

Objective: Close the remaining medical-writing P0 product gaps after soft-pause recovery and prepare independent-AI 12-lane release validation.

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Implement resumable asynchronous synopsis import with truthful progress, cancellation/retry, and DeepSeek v4-pro source-fidelity repair. | `runs/execution/mw_release_p0_resume_20260720/worker_01.md` |
| `worker_02` | Implement StudyDefinition fingerprint binding and fail-closed quarantine/migration for legacy or stale working copies across editor, preview, and DOCX export. | `runs/execution/mw_release_p0_resume_20260720/worker_02.md` |
| `worker_03` | Unify user-selection-is-confirmation semantics across backend contracts, API state, audit records, and frontend without a second medical approval. | `runs/execution/mw_release_p0_resume_20260720/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `qoder_manager` | existing visible QoderVIP/qodercli | `Qwen3.7-Max` | `runs/execution/mw_release_p0_resume_20260720/manager_plan.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
