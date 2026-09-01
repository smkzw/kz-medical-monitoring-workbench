# Codex Review: medical_monitoring_p9_batch_source_binding_hash_exact_20260805

Date: 2026-08-05 (Asia/Shanghai)
Delegated-agent output: `runs/codex_medical_monitoring_p9_batch_source_binding_hash_exact_20260805.md`

## Verdict

**Pass — bounded source-only slice.**

This review is submitted to the Hermes review gate as the required deterministic
verification record; Hermes dispatch was not used because direct Codex is the
selected route.

## Boundary Check

- Codex performed the work directly; no delegated agent or external provider
  was used. All source/test/evidence paths are inside the workbench.
- The reserved runner output path was not edited. Only the declared batch
  repository, test, context, record, review, metrics and LOOP-ledger surfaces
  changed.
- The formal real-loop gate remains `read_only / blocked`; no runtime or
  production path was activated.

## Codex Verification

- Reviewed `load_profile_ready_batch`; source bindings now pass raw persisted
  content hashes through `_require_exact_sha256`.
- Boundary selection: 1 test passed with four malformed subcases; full batch
  repository: 54 passed; adjacent field-profiler/daily-AI/analysis/batch-runner:
  64 passed.
- `python3 -m ruff check` and `python3 -m compileall -q` passed.
- Browser/Playwright, runtime, provider, real-project and medical acceptance
  were intentionally not run because the authoritative gate is blocked.

## Delegated-Agent Output Review

No delegated-agent output exists; Codex is the source reviewer and final
authority. The change is traceable to the profile-ready source-binding boundary
and its repository tests. No clinical or live-runtime claim is made.

## Residual Risk

This proves a narrow profile-ready source hash boundary only. It does not prove
source-token/CAS authenticity, formal B6/C14 authority, clinical correctness,
browser visual quality, provider behavior, or commercial release readiness.
