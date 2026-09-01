# Task Context: medical_monitoring_signal_lifecycle_contract_20260803

Created: 2026-08-03 00:26:56
Objective: 实现纯离线、fail-closed 的医学监查 signal-review-decision-action-recheck 生命周期契约，不接入运行时或授权
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_signal_lifecycle_contract.py` and its focused tests.
- Existing `monitoring_audit_contract.py`, `monitoring_identity_authorization.py`,
  `monitoring_ai_risk_bridge.py`, real-loop readiness/execution/acceptance contracts.
- The external landscape decision record from the immediately preceding research slice.
- Current workbench AGENTS.md and global Codex operating instructions.

## Scope

- In scope: a pure typed domain contract for signal → review → human decision →
  action → recheck; evidence/source/project identity checks; diagnostic report;
  focused unit tests and adjacent contract regression.
- Out of scope: SQLite/repository persistence, source registration, CAS writes,
  router/activation integration, provider dispatch, browser/server startup,
  medical approval, query transmission, frontend changes and real project data.

## Success Criteria

- Complete valid chain is accepted and marked closed only after a human decision,
  resolved action and resolved recheck.
- Pending/mismatched/duplicate/broad-target/automatic-action inputs fail closed.
- All reports remain diagnostic-only with provider/runtime-write/medical authority
  flags false.
- Focused, adjacent and static checks pass; protected frontend and ports remain unchanged.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 00:26:56: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Compared the desired risk-to-action pattern with existing audit,
  identity and AI evidence contracts; chose a separate pure lifecycle read model
  rather than modifying persistence or authorization.
- 2026-08-03: Added the typed signal/review/decision/action/recheck module and
  eight focused fail-closed tests.
- 2026-08-03: Focused tests passed 8; adjacent audit/admission/readiness/
  execution/acceptance/AI tests passed 86; Ruff format/check and compileall passed.
- 2026-08-03: No service/provider/browser/runtime/SQLite/CAS/source registration
  ran; 8911/5174 remained stopped and protected frontend hashes were unchanged.
- 2026-08-03: Read-only interrupted-change scan found only the current admission
  contract/test plus pre-existing frontend npm-cache logs after the checkpoint;
  no unreported Kimi production change was found. B6/C14 JSON still show five
  pending outcomes, zero accepted IDs, both blockers, and all activation/event/
  projection/write flags false.
- 2026-08-03: Next safe action is an independently reviewed, controlled integration
  only after B6 → approved-input → source-token/CAS → runtime gates close.
