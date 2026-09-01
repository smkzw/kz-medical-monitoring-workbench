# Task Context: medical_monitoring_p9_upstream_evidence_hash_exact_20260805

Created: 2026-08-05 18:47:41
Objective: 在真实LOOP正式门保持阻断的前提下，使五项真实LOOP upstream assembly 的 evidence_sha256 严格接受原始小写64位SHA-256，并以聚焦/相邻回归证明空白填充、大写和非字符串证据哈希失败关闭。
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_real_loop_upstream_assembly.py`
- `tests/test_monitoring_real_loop_upstream_assembly.py`
- current-manifest builder/replay and selected readiness/acceptance tests
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
- P9 checkpoint and P10 LOOP ledger.

## Scope

- In scope: exact raw lowercase 64-hex admission for upstream evidence
  `evidence_sha256`, malformed-hash regressions, and selected assembly/
  manifest/readiness adjacency.
- Out of scope: upstream gate meaning, authority flags, provider/runtime
  activation, services, browser/API login, source-token/CAS replay, real
  projects, dependency installation and medical-writing paths.

## Success Criteria

- Uppercase, whitespace-padded and non-string evidence hashes fail closed with
  the existing invalid/field diagnostics.
- Canonical lowercase values and missing-row behavior remain unchanged.
- Focused and selected assembly/manifest/readiness tests pass; compile and
  review-gate pass.
- Formal gate remains `read_only / blocked`; ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- No provider, runtime, browser, API login or real-project action is allowed
  while the authoritative gate remains blocked.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 18:47:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Re-anchored from latest AGENTS.md, P9 checkpoint/ledger and the
  current formal gate. Selected this bounded source-only seam because upstream
  assembly read evidence hashes through `_text()` and stripped whitespace.
- 2026-08-05: Preserved raw string evidence hashes in assembly and added
  padded/non-string regressions while retaining existing invalid/field issue
  semantics. Focused upstream suite passed 13 tests; selected assembly/
  manifest/replay/readiness/acceptance adjacency passed 85 tests; compile and
  review-gate passed. Final gate recheck remained `read_only / blocked` and all
  reserved ports were empty.
