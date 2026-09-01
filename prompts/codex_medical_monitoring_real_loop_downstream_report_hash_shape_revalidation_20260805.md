You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside the configured workspace.
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_real_loop_downstream_report_hash_shape_revalidation_20260805.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only before editing:
- `context/medical_monitoring_real_loop_downstream_report_hash_shape_revalidation_20260805_context.md`
- `services/api/app/monitoring_real_loop_acceptance.py`
- `services/api/app/monitoring_real_loop_execution.py`
- `services/api/app/monitoring_real_loop_acceptance_revalidation.py`
- Their focused real-loop regression modules.

Task:
Review the task context and complete one bounded source-only integrity slice
directly. Ensure downstream acceptance/execution report-chain and persisted
revalidation digests fail closed on padded, uppercase, non-hex, short and
non-string values instead of lower/strip rewriting them, while preserving
canonical report construction, assessment and blocked diagnostics. Use the
smallest coherent patch and do not alter upstream readiness or route policy.

Allowed product files:
- `services/api/app/monitoring_real_loop_acceptance.py`
- `services/api/app/monitoring_real_loop_execution.py`
- `services/api/app/monitoring_real_loop_acceptance_revalidation.py`
- Their focused regression modules.

Do not start services, ports 8911/5174/8910/4173, providers, browser/
Playwright/API login, real projects, medical-writing data, or formal B6/C14 /
release activation. Compile and run focused/adjacent source tests only.

Output schema:
1. `# Codex Direct Task: medical_monitoring_real_loop_downstream_report_hash_shape_revalidation_20260805`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
