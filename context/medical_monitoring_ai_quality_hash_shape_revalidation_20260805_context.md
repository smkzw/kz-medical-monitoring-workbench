# Task Context: medical_monitoring_ai_quality_hash_shape_revalidation_20260805

Created: 2026-08-05 08:05:29
Objective: Harden independent-AI quality observation hash reads to reject noncanonical attempt digests without normalization
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_quality.py`
- `tests/test_monitoring_ai_quality.py`
- `services/api/app/monitoring_ai_contracts.py` (canonical digest helper)
- Current P10/B6/C14 gate records; the real-loop gate remains read-only and
  blocked.

## Scope

- In scope: exact lowercase SHA-256 validation for quality observation input,
  request and optional response attempt digests, including the persisted-attempt
  factory path; focused and adjacent source-only regressions.
- Out of scope: provider dispatch, quality scoring semantics, clinical/release
  decisions, runtime/browser activation, real projects, medical-writing data,
  B6/C14 and commercial-release claims.

## Success Criteria

- Present malformed, padded, uppercase, short, non-hex or non-string attempt
  digests fail closed without normalization; absent optional response digest
  remains compatible.
- Existing quality observation identity/outcome behavior remains green; compile
  and focused/adjacent tests pass without runtime/provider/browser action.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep 8911, 5174, 8910 and 4173 stopped; do not use Playwright or real data.
- Do not alter quality outcome mapping, review semantics or canonical hash
  generation beyond rejecting noncanonical persisted digest text.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 08:05:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Reconnaissance found quality model/factory paths using
  `.strip().lower()` for request/response attempt hashes; this is a concrete
  persisted quality-evidence normalization gap.
