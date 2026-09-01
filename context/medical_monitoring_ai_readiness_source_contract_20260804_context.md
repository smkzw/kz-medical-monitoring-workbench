# Task Context: medical_monitoring_ai_readiness_source_contract_20260804

Created: 2026-08-04 22:25:21
Objective: Prevent medical-monitoring field mapping and protocol preparation panels from treating a generic role-ready flag as semantic independent-AI readiness
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Medical-monitoring frontend readiness model and panels under
  `frontend/src/features/medical-monitoring/`.
- Backend vocabulary is the strict `semantic_ai_tasks_enabled` field emitted
  by monitoring raw intake and the independent-AI status contract.
- Current gate artifacts remain authoritative for runtime boundaries:
  B6 freshness/revalidation, release coverage, and real-loop gate audit under
  `records/active_slices/`.

## Scope

- In scope: normalize the monitoring readiness object and make field-mapping /
  protocol-preparation panels consume only the semantic-AI flag; add positive
  and negative source/unit contracts.
- Out of scope: provider configuration, API schemas, credentials, runtime,
  browser/Playwright, real projects, SQLite, medical-writing data, and release
  authority.

## Success Criteria

- Generic role `{ready: true}` cannot enable monitoring semantic-AI actions.
- The normalized monitoring object preserves the backend vocabulary so the
  current callers remain compatible.
- Field mapping and protocol preparation both use the strict semantic flag.
- Focused frontend, all monitoring Node, related backend contracts, build,
  compile, and reserved-port checks pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Finding And Decision

- `monitoringFieldMappingCopy` and
  `MedicalMonitoringProtocolPreparationPanel` accepted `aiStatus.ready` in
  addition to the semantic flag. A generic role-status payload uses `ready`
  for connection/role availability, which is weaker than the monitoring
  semantic-task permission. That could show “AI识别/生成” actions while the
  product AI gate was still blocked.
- Chosen repair: `monitoringAiReadiness()` now carries the normalized
  `semantic_ai_tasks_enabled` field; downstream monitoring panels require that
  field to be strictly `true`. No API or task transition changed.

## Loop Log

- 2026-08-04 22:25:21: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 22:25-22:27: Audited all monitoring panel consumers; patched the
  model, protocol panel, and positive/negative contracts; no Hermes/external
  dispatch was made.
- 2026-08-04 22:27: Focused and related verification completed; runtime gates
  remain closed.
