# Task Context: monitoring_protocol_contract_v2

Created: 2026-07-30 08:12:10
Objective: Version medical monitoring protocol preparation jobs for evidence packet v2 while preserving v1 audit records and disabling v1 candidates in aggregation, decisions, and recovery
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `context/monitoring_p10_protocol_evidence_packet_v2_20260730.md`
- `context/monitoring_p10_input_revision_compatibility_recovery_20260730.md`
- Current medical-monitoring protocol-preparation repository/service/router and tests.

## Scope

- In scope: protocol-preparation job contract identity, legacy-contract retirement
  through the repository state machine, status aggregation, candidate decisions,
  startup recovery, and focused compatibility/recovery tests.
- Out of scope: frontend, medical writing, field mapping, daily run, protocol-rule
  lifecycle, API startup, and any real runtime database mutation.

## Success Criteria

- Current jobs explicitly bind `monitoring_protocol_preparation_v2` and evidence
  packet v2 in their frozen payload.
- Legacy v1 jobs and candidates remain queryable for audit but cannot be aggregated,
  decided, retried, claimed, or recovered.
- Restarting the same confirmed protocol version creates/selects only the v2
  contract and never migrates a v1 candidate.
- Focused and adjacent tests plus static checks pass without starting the API.

## Risk Boundaries

- Edit the authorized main workspace directly with `apply_patch`.
- Use only formal repository/service state transitions; never write runtime SQLite
  state directly.
- Do not start the API or modify the real runtime database.
- Preserve legacy rows, attempts, candidate evidence, and recorded user decisions.
- Do not touch frontend, medical-writing, field-mapping, or daily-run code.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-30 08:12:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-30: Confirmed v2 payload/status/decision guards already exist; the
  missing boundary is atomic legacy workflow retirement before explicit start
  and startup worker wake.
- 2026-07-30: Added one shared contract module and repository state transition.
  Explicit start retires incompatible contracts project-wide before creating or
  selecting v2 jobs. The official startup recovery repository entrypoint retires
  legacy workflow jobs before any worker wake can reclaim them.
- 2026-07-30: Legacy proposed candidates become `superseded`; accepted/rejected
  decisions and all job/payload/evidence rows remain intact. Jobs become
  `stale_input` with `superseded_workflow_contract`, and generic retry rejects
  that terminal reason.
- 2026-07-30: Dedicated test proves status aggregation hides v1, decision API
  returns lineage mismatch, same-version restart creates a distinct empty v2
  job, v1 payload/evidence remains queryable, v1 cannot retry, and startup
  recovery claims the v2 job rather than v1.
- 2026-07-30: Verification passed: 183 adjacent tests, Ruff, and `py_compile`.
  Existing FastAPI `on_event` deprecation warnings remain unchanged. API port
  8911 was not started and the real runtime database was not accessed.
