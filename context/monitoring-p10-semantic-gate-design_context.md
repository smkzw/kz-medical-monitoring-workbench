# Task Context: monitoring-p10-semantic-gate-design

Created: 2026-07-30 01:31:24
Objective: 设计医学监查字段映射独立AI候选之后、人工激活之前的跨项目语义质量门，仅写设计文档
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: no delegated run; Codex local source review

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/monitoring_p10_v10_partial_mapping_qc_20260730.md`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_mapping_draft_repository.py`
- `services/api/app/monitoring_mapping_activation.py`
- `services/api/app/monitoring_mapping_contract.py`
- `services/api/app/monitoring_ai_field_profiler.py`
- Corresponding repository, mapping-draft, activation and AI-service tests.

## Scope

- In scope: post-candidate, pre-confirmation/pre-activation semantic gate design.
- Out of scope: code, database, frontend, runtime state and source-file changes.

## Success Criteria

- Define cross-project rules for the V10 semantic failures.
- Separate global blockers, capability blockers, warnings and hidden auto-resolution.
- Preserve CM as non-investigational medication and separate all IP lifecycle roles.
- Define minimum data contracts, lifecycle binding, UI compression and implementation slices.
- Write the requested design to
  `context/monitoring_p10_mapping_semantic_quality_gate_design_20260730.md`.

## Risk Boundaries

- Do not modify code, databases, frontend, runtime state or source files.
- Do not treat AI confidence or candidate acceptance as a semantic pass.
- Do not record subject-level source values.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-30 01:31:24: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-30: Reviewed V10 fixed-cut QC and the current candidate, draft,
  confirmation and activation contracts.
- 2026-07-30: Located the missing whole-draft semantic gate between accepted
  candidates and formal activation.
- 2026-07-30: Wrote and self-reviewed the requested design; no delegated model
  was called, so the prohibited nighttime aishuo route was not used.
