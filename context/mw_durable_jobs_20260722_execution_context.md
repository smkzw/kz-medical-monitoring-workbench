# Execution Context: mw_durable_jobs_20260722

Created: 2026-07-22 17:00:50
Objective: 将竞品分诊、章节AI候选和参考资料翻译迁移到统一SQLite持久作业合同，保持独立生产AI、冷恢复、取消、租约和项目隔离，并完成前后端集成与回归
Task type: `complex_delivery_conference`
Risk: `high`
Execution module trigger: Codex identified 5 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `complex_executor_cms` -> `hermes` / `aishuo` / `cms-model`
- Execution manager: `complex_manager_grok` -> `grok` / `grok-build` / `grok-4.5`
- Execution-manager fallback: `use the declared role fallbacks`

## Source Of Truth

- Architecture decision: `records/active_slices/medical_writing_production_rebaseline_20260722/ASYNC_JOB_ARCHITECTURE_DECISION.md`.
- Recovery and current-state record: `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md` and `CURRENT_GAP_MATRIX.md`.
- Proven durable-job reference implementation: `services/api/app/medical_writing_synopsis_import.py` and its API wiring in `services/api/app/main.py`.
- Existing business implementations: `services/api/app/medical_writing_competitor_triage.py`, `services/api/app/medical_writing.py`, `services/api/app/medical_writing_repository.py`, `services/api/app/writing_reference_translation_batch.py`, `services/api/app/writing_reference_preparation_batch.py`, and their tests.
- Product contracts: `packages/contracts/workbench_contracts/models.py`.
- Frontend source of truth: `frontend/src/` and existing medical-writing contract/browser tests.
- The current workspace is the authorized local production candidate. Source and tests inside this workspace may be edited only within the file ownership declared in the refined execution plan.

## Risk Boundaries

- Production-candidate code writes inside this workspace are authorized after the execution manager has assigned non-overlapping file ownership. Do not deploy externally or mutate real study data.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- Product runtime must call its independently configured DeepSeek/GLM-OCR/Hy-MT2 routes. Codex, Hermes, Grok, Kimi, Qoder, and CodeBuddy must never substitute their own output for system-under-test AI results.
- One shared durable job contract only. Do not clone separate lease/cancel/retry state machines for each business type.
- Preserve source-DOCX pass-through behavior, current plan-consumption gates, author-selection semantics, and explicit `test_only` provider fixtures.
- User selection is the medical decision. Do not introduce a generic extra `待医学批准` state.
- Keep legacy synchronous endpoints only as read-compatible shims during migration; no new HTTP request may block on a long model/download/OCR/translation operation.

## Required Durable Contract

- Stable idempotent `job_id` scoped by project, job type, business key, and request hash.
- SQLite truth with queued/running/retry_wait/completed/failed/cancelled states; claim token, lease expiry, heartbeat, monotonic progress, attempt count, timestamps, error summary, input/output hashes, artifact locator, provider/model audit, and schema version.
- Compare-and-swap completion/failure/cancel so stale owners and late provider responses cannot overwrite a newer claim or cancellation.
- Cold recovery on service start for queued/retry_wait/expired-running jobs; graceful worker shutdown; bounded retry; duplicate-click deduplication; strict project isolation.
- `POST` starts and returns `202` plus job locator. Unified status/result/cancel/retry endpoints are authoritative. FastAPI background work may only wake the local worker.
- Future executor adapter boundary for Celery plus Redis/RabbitMQ without changing HTTP or persisted job/artifact contracts.

## Acceptance Checks

- Deterministic unit tests for create/deduplicate/claim/heartbeat/lease loss/CAS complete/fail/cancel/retry/cold recovery/shutdown/project isolation/monotonic progress.
- Competitor triage, chapter candidates, and translation each prove restart recovery and stale-owner isolation using the shared contract.
- Chapter candidate adoption atomically records author selection and updates the versioned working copy, or writes neither.
- Frontend proves progress refresh, page reload resume, cancel/retry, terminal result rendering, no duplicate job on double click, and clear independent-AI/provider failure messaging.
- Existing `tests/test_medical_writing*.py` and affected frontend/build checks remain green. Browser acceptance is Codex-owned after deterministic checks pass.

## Work Items

1. 统一DurableMedicalWritingJob合同、SQLite存储、worker生命周期与恢复语义
2. 竞品分诊适配统一持久任务并移除HTTP同步长调用
3. 章节AI候选适配统一持久任务并实现候选采纳原子写入
4. 翻译批次适配统一持久任务及重启恢复
5. 统一作业API、前端进度交互、取消重试和集成回归

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
