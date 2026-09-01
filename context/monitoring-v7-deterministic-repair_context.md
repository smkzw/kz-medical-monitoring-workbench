# Task Context: monitoring-v7-deterministic-repair

Created: 2026-07-29 22:19:42
Objective: 实现旧 v7 listing_field_mapping 纯技术元数据 invalid_ai_output 失败作业的受控确定性产品侧修复，严格关闭失败并保持 v7 assemble/adopt 兼容
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/monitoring_v7_deterministic_repair_context.md`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_ai_router.py`
- `services/api/app/monitoring_deterministic_metadata_mapping.py`
- Existing monitoring AI and mapping-draft tests under `tests/`
- No external dependency or architecture choice is involved; external discovery was
  skipped because the repair is an exact migration over existing local contracts.

## Scope

- In scope: the four allowed monitoring AI implementation files, adjacent monitoring
  AI tests, and this task's handoff/metrics/review records.
- Out of scope: API restart, real database reads or writes, medical writing, shared AI
  configuration, frontend, and P7B/P7C rule implementation or tests.

## Success Criteria

- Only terminal `failed` + `invalid_ai_output` +
  `monitoring-listing-field-mapping-v7` + `listing_field_mapping` jobs whose complete
  chunk contains only closed-whitelist deterministic metadata may be repaired.
- Exact project, batch, full-profile and input-revision identity must still be current;
  malformed, mixed, semantic, ambiguous, stale, or already-candidate-bearing jobs fail
  closed before mutation.
- Original job/prompt/input/requested-model identity and attempts remain unchanged.
- One deterministic v7-compatible candidate, output hash, immutable provenance,
  actor/reason and idempotency identity are committed atomically.
- Same idempotency key and request returns the same completed job/candidate; changed
  meaning conflicts.
- Focused and full monitoring AI combined tests pass, including v7 draft assembly.

## Risk Boundaries

- Do not call the repair endpoint, restart the API, or access a real SQLite database.
- Do not modify frontend, medical-writing, shared-AI, or P7B/P7C rule files.
- No delegated execution is used; Codex implements and performs final acceptance.
- Baseline boundary hashes:
  `monitoring_record_rule_resolver.py=902552b...addd25`,
  `test_monitoring_record_rule_resolver.py=640eb90...bf44`,
  `frontend/AGENTS.md=85c8514...9bf13`.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 22:19:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29 22:24: Read both instruction layers, the exact repair contract,
  implementation, whitelist, tests, and v7 mapping-draft consumer. Chosen design:
  explicit repair endpoint -> service fail-closed gate -> repository atomic CAS and
  immutable audit row -> existing candidate/assemble contracts.
- 2026-07-29 22:31: Implemented the four allowed monitoring AI files and a dedicated
  temporary-SQLite test module. No live API, real database, worker wake, or AI provider
  call was made.
- 2026-07-29 22:42: Acceptance complete for the requested slice: dedicated matrix
  `21 passed`; all monitoring AI/mapping combinations `233 passed`; final Python
  compilation passed. A wider `test_monitoring_*.py` run produced `636 passed,
  4 failed`; all four failures are in out-of-scope P7C release-coverage tests, and a
  minimal protocol-rule API failure reproduced alone. P7B/P7C files were not edited.
