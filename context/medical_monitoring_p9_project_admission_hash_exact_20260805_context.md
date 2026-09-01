# Task Context: medical_monitoring_p9_project_admission_hash_exact_20260805

Created: 2026-08-05 18:33:57
Objective: 在正式真实LOOP门保持阻断的前提下，使项目准入批次与提示词哈希在只读契约边界严格接受原始小写64位SHA-256，并以聚焦/相邻回归证明非法值失败关闭。
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_project_admission_contract.py`
- `tests/test_monitoring_project_admission_contract.py`
- `tests/test_monitoring_real_loop_readiness.py`
- `tests/test_monitoring_real_loop_upstream_assembly.py`
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
- P9 checkpoint and P10 LOOP ledger.

## Scope

- In scope: exact raw lowercase 64-hex validation for `listing_sha256` and
  `prompt_sha256`, focused regressions, and read-only readiness adjacency.
- Out of scope: audit-chain hashes, identity authorization, source-token/CAS
  replay, provider/runtime activation, services, browser/API login, real
  projects, dependency installation, and medical-writing paths.

## Success Criteria

- Uppercase, padded, and non-string batch/prompt hashes fail closed.
- Existing canonical lowercase hashes and diagnostic-only admission behavior
  remain valid.
- Focused and selected readiness/upstream adjacency tests pass; compile and
  review-gate checks pass.
- Formal gate remains `read_only / blocked`; ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- No provider, runtime, browser, API login, or real-project action is allowed
  while the authoritative gate remains blocked.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 18:33:57: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Re-anchored from latest AGENTS.md, P9 checkpoint/ledger and the
  current formal gate. Selected this bounded source-only identity audit because
  `_sha256()` normalized raw values with `str(...).strip().lower()`.
- 2026-08-05: Changed only project-admission hash admission and added focused
  regressions for uppercase, whitespace-padded and non-string batch/prompt
  digests. Focused suite passed 7 tests; readiness/upstream adjacency passed
  41 tests; compile and review-gate passed.
