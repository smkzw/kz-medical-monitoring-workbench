# Task Context: medical_monitoring_consumer_rollup_conservation_20260802

Created: 2026-08-02 17:08:48
Objective: 加固 C7 前端 consumer handoff 的项目/中心 rollup 集合守恒与缺失状态，保持 source-preserving、只读、不接运行库
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/features/medical-monitoring/medicalMonitoringConsumerContract.mjs` and its focused Node test define the serialized C6 handoff consumed by Timeline/Profile/risk fixtures.
- `services/api/app/monitoring_clinical_consumer_handoff.py` and `monitoring_clinical_projection_contract.py` define the upstream rollup fields: project/site level, event/observation/risk ID sets and domain/count fields.
- Current product release records, B6/C14 gates and protected App/styles hashes remain read-only boundaries.

## Scope

- In scope: validate project/site rollup object shape and identity level; verify project event/observation/risk sets against normalized handoff records; verify supplied site rollups against site-partitioned event/observation/risk sets; expose explicit `rollupConservation` statuses (`conserved`, `partial`, `missing`, `not_conserved`, `empty`) without inventing data.
- Out of scope: React/App/CSS wiring, API/backend changes, source parsing, severity/clinical interpretation, canonical risk authority, persistence, migration, B6/C13/C14, services, browser/real-project execution.

## Success Criteria

- A valid project rollup cannot silently omit normalized observations or risk links; malformed or mismatched sets fail closed.
- Empty site rollups remain usable only with an explicit `missing`/`partial` conservation status, never as proof that no center data exists.
- Existing C7 fixture behavior remains source-preserving; focused and full Node suites, frontend contracts, build, release-gate, hash replay and review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 17:08:48: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Direct Codex route; no external dispatch. Inspection found project rollup only compared `event_ids` with timeline and `site_rollups` were cloned without validating level/identity or event/observation/risk set conservation.
