# Task Context: mw_gap_rebaseline_20260717

Created: 2026-07-17 14:29:49
Objective: 基于当前代码、稳定运行态、真实项目验收和完成切片重建医学写作子系统Gap Matrix，识别首个仍未闭环且不重复开发的生产能力，并形成可验证下一切片合同
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_writing_full_gap_review_20260714/GAP_MATRIX.md` as the historical baseline only.
- Completed/current medical-writing slice records under `records/active_slices/medical_writing_*`.
- Current implementation under `services/api/app`, `frontend/src`, `packages/contracts`, tests and stable localhost runtime.
- The just-completed front-matter/synopsis browser and runtime evidence, including the observed 5174 -> legacy 8910 drift.

## Scope

- In scope: reclassify each historical P0/P1 gap against current code and verification; identify the first still-open production gap; write a current matrix and a bounded next-slice contract.
- Out of scope: new product implementation, clinical content changes, stable database writes, external-agent dispatch and repeating completed real-AI runs.

## Success Criteria

- Every changed status cites current code/test/runtime or completed-slice evidence.
- Completed capabilities are not reopened solely because the July 14 matrix is stale.
- Remaining gaps separate runtime/deployment correctness from content-policy and future breadth.
- The selected next slice has explicit fail/pass conditions and at least two stable-runtime scenarios.

## Risk Boundaries

- No stable working-copy or clinical content writes.
- Do not mark a capability complete from a task-record label alone when current runtime/code cheaply disproves it.
- Do not treat HTTP 200 as version compatibility.
- Codex direct route; no delegated-agent output is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-17 14:29:49: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-17 14:33: Current evidence shows most July 14 P0/P1 product gaps have closed. Stable build/route readiness remains open and was reproduced by 5174 silently proxying legacy 8910 while both services returned HTTP responses.
