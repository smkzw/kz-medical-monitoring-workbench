You are Codex executing this task directly. Ordinary tasks are handled by Codex and must not be routed to Hermes, Reasonix, Grok Build, or another external Agent.

Hard boundaries:
- Work only inside `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Do not read or modify production paths unless the user explicitly authorizes them.
- Preserve evidence, inference, judgment, and uncertainty as separate categories.
- Runner-managed output path: `runs/codex_medical_monitoring_assurance_all_read_route_authorization_20260803.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_assurance_all_read_route_authorization_20260803_context.md`

Task:
Implement the bounded backend read-authorization slice described by the task
context.

Required:

1. Use the existing provider-neutral `server_authorization` seam with
   `MonitoringAction.READ_RISK_AUDIT` for assurance task list/detail,
   readiness, full-recompute-proof read and rollup read routes. Add the
   `Request` parameter without parsing headers/cookies/tokens.
2. Preserve 503 for absent host principal and 403 for an authenticated role
   without medical audit scope in the production router. Preserve 404 and
   409 semantics after authorization. Keep read routes mutation-free.
3. Keep `require_server_principal=False` an explicit offline test-harness
   bypass only; production `main.py` must remain true. Do not add a default or
   demo principal.
4. Add focused production-boundary tests for each read route (at least one
   absent-principal and one unauthorized-role case), plus regression coverage
   for the existing assurance test suite. Do not alter clinical data or
   frontend code.

Out of scope: authentication provider/middleware, new ACL actions, denied
attempt persistence, schema/write changes, service/browser/provider/API login,
runtime DB, real projects, B6/C14 and approved-input gates.

Verification: run focused route/identity/assurance tests, relevant full
monitoring regression if the shared router contract warrants it, Ruff and
py_compile for changed Python, check ports 8911/5174/8910/4173 remain empty,
write task records/review/metrics and pass the Hermes review-gate before
continuing.

Output schema:
1. `# Codex Direct Task: medical_monitoring_assurance_all_read_route_authorization_20260803`
2. `## Boundary Check`
3. `## Direct Work`
4. `## Evidence And Assumptions`
5. `## Verification`
6. `## Residual Risk`
