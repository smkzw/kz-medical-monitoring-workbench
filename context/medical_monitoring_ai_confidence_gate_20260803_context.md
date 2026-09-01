# Task Context: medical_monitoring_ai_confidence_gate_20260803

Created: 2026-08-03 18:03:06
Objective: 统一医学监查 AI 候选低置信度展示、人工确认与自动化禁用边界，并完成前后端回归
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes tracked-task entrypoint because the change crosses backend contracts, browser-facing confirmation UI, and regression evidence. Per the active task instruction and the local execution boundary, Codex performed the bounded implementation and verification directly; no delegated worker, service, browser login, or real project run was started.

## Source Of Truth

- Backend contracts: `services/api/app/monitoring_ai_contracts.py`, `monitoring_ai_router.py`, `monitoring_protocol_preparation_service.py`, and `monitoring_rule_template_recommendation_service.py`.
- Browser contract: `frontend/src/features/medical-monitoring/medicalMonitoringProtocolPreparation.mjs`, `medicalMonitoringRuleTemplateRecommendation.mjs`, `MedicalMonitoringProtocolPreparationPanel.jsx`, and the loaded CSS files.
- Existing regression suites under `tests/` and the monitoring feature `*.test.mjs` files.
- External design principle consulted: FDA transparency and uncertainty-quantification pages; these are rationale only, not runtime authority.

## Scope

- In scope: expose one fail-closed confidence summary for AI candidates; keep all candidates user-confirmation gated; require a non-empty explanation before accepting below-threshold or malformed candidates; show the state and reason field in protocol/rule-template review UI; add focused regression checks.
- Out of scope: provider configuration, real AI transport, source batch admission, B6/C14 activation, automatic medical decisions, production deployment, real project imports, service startup, browser login, and external-agent dispatch.

## Success Criteria

- Confidence summary is present on public candidate payloads and explicitly reports `automation_permitted=false`.
- Low, malformed, or missing confidence is visible and cannot be accepted without an explanation where an acceptance route exists.
- Threshold-passing candidates still require medical-manager confirmation.
- Focused backend/frontend tests and the frontend production build pass.
- Existing safety boundaries remain unchanged: no service or real project run, and B6/C14/release authority remain false.

## Risk Boundaries

- Only the workbench source and its task records may be changed; no production paths, real project data, or runtime state may be touched.
- The 0.70 value is a presentation/governance threshold, not a calibrated clinical probability and not a medical conclusion.
- A candidate may remain visible for review, but no candidate may authorize automatic risk disposition or a no-risk conclusion.
- No delegated agent was dispatched; Codex is the sole implementation and acceptance authority for this bounded slice.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 18:03:06: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Read-only source and official FDA transparency/uncertainty guidance re-anchored the need to show limitations, confidence, evidence gaps, and human review at the point of use.
- 2026-08-03: Added backend `candidate_confidence_summary`, public payload propagation, and low-confidence explanation gates for generic AI, protocol preparation, and rule-template recommendation decisions.
- 2026-08-03: Added frontend confidence summaries and required explanation fields for protocol and rule-template acceptance; all automation flags remain false.
- 2026-08-03: Verification passed: `py_compile`; backend focused suite 502 passed; confidence/protocol/rule-template focused subset 71 passed; all 23 medical-monitoring frontend test modules passed; Vite production build passed with only the existing chunk-size warning.
- 2026-08-03: Added an integration-level protocol-preparation regression that mutates only a temporary candidate fixture to 0.40 and proves blank-reason acceptance is rejected; accepted/proposed status gating preserves idempotent replay semantics.
- 2026-08-03: Hermes preflight was run but not dispatched; it reported the generated prompt's absolute workspace path as a production-like-path warning. No external session was started. B6/C14/release gates remain blocked and all monitored ports remain stopped.
