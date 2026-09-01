# Task Context: medical_monitoring_ai_contract_hash_shape_revalidation_20260805

Created: 2026-08-05 07:52:42
Objective: Harden independent-AI source/evidence/revision hash validators to reject noncanonical present digests without normalization
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_contracts.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_ai_api.py`
- Current P10/B6/C14 gate records; the real-loop gate remains read-only and
  blocked.

## Scope

- In scope: exact lowercase SHA-256 shape validation for source bindings,
  evidence and candidate input-revision hashes in the independent-AI contract;
  focused and adjacent source-only regressions.
- Out of scope: provider invocation, prompt/model routing, clinical inference,
  persistence migration, API/browser activation, real projects,
  medical-writing data, B6/C14 and release claims.

## Success Criteria

- Present digest values that are uppercase, padded, malformed or otherwise
  noncanonical fail closed; valid lowercase values remain unchanged.
- No source hash is silently case-folded or whitespace-normalized.
- Existing valid AI job/candidate/repository behavior remains green; compile
  and focused/adjacent tests pass without any runtime/provider/browser action.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Keep 8911, 5174, 8910 and 4173 stopped; do not use Playwright or real data.
- Do not change canonical digest generation, user-confirmation gating or source
  identity semantics.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 07:52:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Reconnaissance found source/evidence/candidate validators using
  `.strip().lower()` before SHA-256 checks; this is a concrete source-boundary
  normalization gap adjacent to the completed clinical/identity repairs.
- 2026-08-05: Replaced those normalizers with exact lowercase SHA-256 checks,
  tightened the regex end boundary to `\Z`, and added negative/positive
  regressions. Focused **22 passed**; all discovered AI-contract test modules
  with `real_` excluded **759 passed, 4 deselected, 17 warnings**; compileall
  passed; preflight passed; reserved ports remained empty; Ruff unavailable.
