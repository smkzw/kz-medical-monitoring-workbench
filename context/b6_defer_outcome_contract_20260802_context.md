# Task Context: b6_defer_outcome_contract_20260802

Created: 2026-08-02 18:41:57
Objective: 在用户明确执行授权下，支持 B6 明确 defer/pending outcome 的 fail-closed C14 投影，重绑发布 coverage，保持写入迁移激活关闭
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current user execution authorization in this task.
- `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json` and its bound input `CODEX_AUTHORIZED_ENGINEERING_DEFER_INPUT_20260802.json`.
- `services/api/app/monitoring_b6_activation_gate.py`, `tests/test_monitoring_b6_activation_gate.py`.
- `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/B6_TO_C13_ACTIVATION_GATE_REPORT.json`.
- `records/active_slices/medical_monitoring_release_evidence_coverage_20260802/CURRENT_RELEASE_COVERAGE.json`.

## Scope

- In scope: explicitly hash-bound `pending_review`/defer outcomes, C14 fail-closed category/count contract, B6/C14 evidence regeneration, release coverage rebind and focused regression.
- Out of scope: approve/reject clinical conclusions, source-content inference, aggregate/CAS write, migration, runtime/API/provider/browser/real-project execution, protected App/styles and medical-writing changes.

## Success Criteria

- Persist five outcomes with exact B3/B4 hashes and candidate fingerprints, each explicitly `pending_review` with no resolved blocker that was not evidenced.
- Allow C14 to validate nonzero pending outcomes while rejecting category/count drift; retain all activation/event/projection/write/migration flags false.
- Rebuild C14 and coverage sources; coverage decision remains `blocked`, `release_ready=false`, and 16 gates unmet.
- Focused tests and report hash replays pass; no runtime or protected surface is modified.

## Risk Boundaries

- User authorization permits the bounded evidence/contract update, not invention of medical approval or external action.
- `pending_review` is a defer state, not an approval; no aggregate/CAS, event, projection, migration or runtime write may be inferred.
- No delegated agent or conference; Codex retains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 18:41:57: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Wrote five hash-bound engineering defer outcomes; B6 remains pending, non-writing.
- 2026-08-02: C14 contract rejected nonzero pending outcomes; patched category/count validation and added regression.
- 2026-08-02: C14 rebuilt with 46/46 blocked; release coverage rebound to current B6/C14 sources.
