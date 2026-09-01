# Task Context: medical_monitoring_real_loop_upstream_ref_binding_20260804

Created: 2026-08-04 10:04:03
Objective: 为五项 RealLoop upstream gate evidence 增加成对 artifact ref + SHA-256 身份绑定，缺失/复用/不匹配 fail-closed，仅离线验证
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- 最新 global/workspace/workbench `AGENTS.md` 与当前文件系统。
- `monitoring_real_loop_readiness.py`、其 tests、以及 LOOP 5.91 upstream hash-binding
  records/review.
- Existing B6/C14, approved-input, source-token and aggregate-CAS artifact identities are
  evidence data only; no current outcome may be inferred from them.

## Scope

- In scope: add five explicit opaque artifact refs paired with the five upstream gate hashes;
  require both fields for a true prerequisite, reject empty/unsafe/duplicate refs and ref/hash
  mismatch, and carry canonical `(gate, ref, sha256)` rows into readiness report hashing.
- Out of scope: reading or rewriting actual gate JSON, reviewer decisions, API/runtime/provider/
  queue/database/browser/Playwright, real projects, B6/C14 activation or medical conclusions.

## Success Criteria

- A true upstream prerequisite cannot be execution-ready with only a hash or only a ref.
- Valid ref/hash pairs are distinct and deterministic; malformed/duplicate/missing pairs block
  readiness while preserving false-gate positional compatibility and no authority flags.
- Focused/adjacent/full monitoring tests pass, reserved ports stay empty and review-gate is clean.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Refs are opaque evidence identities, not permission to read or promote an artifact; this slice
  does not validate artifact content or invent outcomes.
- Keep B6/C14 and 8911/5174/8910/4173 closed; no external agent/provider is dispatched.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 10:04:03: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 10:05:00: Static audit found upstream gate hashes had no paired artifact identity;
  a hash alone is insufficient for later audit/reopen of the exact evidence record.
- 2026-08-04: Implemented opaque ref + SHA-256 pair validation and deterministic report
  propagation. Invalid, missing, reused or half-paired evidence is fail-closed; blocked reports
  omit both halves of an invalid pair so the report remains structurally self-consistent.
- 2026-08-04: Focused readiness/execution tests 32 passed; adjacent real-loop tests 75 passed;
  full `tests/test_monitoring*.py` 1968 passed with 25 existing warnings (529.56s, rc 0).
  Final checks confirmed 8911/5174/8910/4173 empty and no runtime/provider/real-project/browser
  execution occurred. Records, review and metrics are ready for review-gate.
