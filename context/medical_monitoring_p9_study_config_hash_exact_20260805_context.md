# Task Context: medical_monitoring_p9_study_config_hash_exact_20260805

Created: 2026-08-05 19:30:51
Objective: Preserve exact lowercase study configuration source and declared configuration SHA-256 bytes at deserialization boundaries
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_study_config.py`: source-binding and declared configuration digest validation.
- `tests/test_monitoring_study_config.py`: project-neutral config round-trip and tamper regressions.
- `services/api/app/monitoring_mapping_contract.py`: field-mapping semantic dependency used by the config fixtures.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`, the P9 checkpoint and LOOP ledger.
- Current filesystem plus the latest global/workspace/workbench `AGENTS.md` files.

## Scope

- In scope: exact lowercase 64-hex enforcement for source-binding `content_sha256` and optional declared `config_sha256`; focused malformed-hash regressions and task evidence.
- Out of scope: study-config semantics, source registry resolution, project adapters, provider/runtime/browser activation, API login, real projects, clinical/scientific/visual/commercial acceptance and unrelated hash fields.

## Success Criteria

- Padded, uppercase and non-string source/config digests fail closed; canonical project-neutral config round-trip and deterministic config identity continue to pass.
- Focused and selected adjacent tests pass; targeted compilation passes; review-gate is green.
- The formal real-loop gate remains `read_only / blocked` with all activation/provider/runtime/write flags false and ports 8911/5174/8910/4173 empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 19:30:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 19:31:00: Codex direct source-only route selected; no external provider dispatch is permitted by the formal gate.
- 2026-08-05 19:36:00: Exact source-binding and declared-config digest validation plus regressions passed; selected adjacency and compilation passed. Review-gate is green, the nine-row manifest verifies exactly, the formal gate remains blocked/read-only, and all reserved ports are empty.
