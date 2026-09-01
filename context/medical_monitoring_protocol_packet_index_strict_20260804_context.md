# Task Context: medical_monitoring_protocol_packet_index_strict_20260804

Created: 2026-08-04 23:13:13
Objective: Require non-boolean table and row indices in protocol evidence structural repair
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_source_packet.py`: project-neutral protocol evidence context and structural repair.
- `tests/test_monitoring_ai_source_packet.py`: table/list structural repair contracts.
- Existing independent-AI evidence and P10/B6/C14 boundary records.

## Scope

- In scope: reject boolean table/row indices at all protocol structural-repair consumers; add table-index and row-index regressions; record offline evidence.
- Out of scope: provider/runtime startup, browser or Playwright login, API login, real projects, medical review, database state, and production writes.

## Success Criteria

- Boolean table coordinates cannot be interpreted as numeric evidence structure.
- Canonical integer table/list evidence behavior remains covered.
- Protocol packet plus monitoring-AI and real-loop/assurance tests pass, changed Python compiles, and reserved ports remain empty.

## Risk Boundaries

- Only the protocol source-packet module, focused test, and task-scoped evidence/review/metrics/ledger records may change.
- No delegated agent, Hermes dispatch, service/provider startup, browser/Playwright/API login, database mutation, real-project import, medical-writing artifact, or production artifact mutation.
- Codex remains final authority; review-gate does not grant provider, medical, or release authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 23:13:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 23:14:00: Source inspection found three protocol structural-repair sites accepting bool as int table coordinates; no runtime/provider/browser action was permitted.
- 2026-08-04 23:16:00: Added a shared non-boolean index predicate and table/row regressions; packet, AI, and real-loop offline suites passed.
