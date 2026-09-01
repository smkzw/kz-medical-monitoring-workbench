# Task Context: medical_monitoring_runtime_identity_evidence_contract_20260804

Created: 2026-08-04 14:43:42
Objective: Define and test a read-only runtime-identity evidence contract that remains fail-closed until a server-verified host attestation is available; do not start runtime or grant authority.
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_runtime_principal.py` and its tests: server-verified principal envelope and
  time/tenant/scope constraints.
- `services/api/app/monitoring_runtime_route_context.py` and `monitoring_principal_host_adapter.py`: route
  binding and host-provided principal seam.
- `services/api/app/monitoring_real_loop_readiness.py`, `monitoring_real_loop_upstream_assembly.py`,
  `monitoring_real_loop_current_manifest.py` and their tests: current five-project gate contract and the
  currently missing `runtime_identity_revalidation` evidence row.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
  and `records/active_slices/medical_monitoring_real_loop_current_manifest_20260804/`: current filesystem
  truth; runtime identity remains missing and all authority flags are false.
- Current workspace and the applicable `AGENTS.md` files are the authority for scope and execution boundaries.

## Scope

- In scope: audit the existing runtime-principal and real-loop gate contracts; add the smallest pure,
  provider-neutral evidence validator only if an actual gap is demonstrated; add focused tests and a
  read-only evidence record; preserve an explicit `missing`/`not_proven` result when no host attestation
  exists.
- Out of scope: starting 8911 or any service/runtime; authenticating or browser-login; creating a host
  principal; calling any provider; changing B6/C14, approved-input, source-token, aggregate/CAS or
  medical-review outcomes; changing real-project data; granting execution/write/medical authority.

## Success Criteria

- A supplied runtime identity evidence document is validated with strict shape, hash/ref pairing,
  principal/tenant/project-scope consistency, time validity and explicit host-verification status.
- Missing, stale, unverified or malformed evidence is fail-closed and cannot set runtime/provider/write/
  migration/medical authority flags to true.
- Existing runtime principal and real-loop tests remain green; a focused regression proves the new
  contract does not coerce absent evidence into `runtime_identity_verified=true`.
- A bounded task record, review and metrics file pass `review-gate`; no service or reserved port is used.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 14:43:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Audited the existing runtime principal, route-context and real-loop upstream contracts;
  added a provider-neutral persisted-evidence validator and 7 focused tests. The current filesystem has
  no host attestation, so the revalidation artifact remains blocked/missing and all authority false.
- 2026-08-04: Combined focused regression passed 54/54; compile check passed; review-gate passed. Ruff
  was not run because the current environment has no `ruff` executable. No service, runtime, provider,
  browser, real project or gate activation was used.
