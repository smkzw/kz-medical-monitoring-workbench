# Codex Review: medical_monitoring_p9_shadow_run_hash_exact_20260805

Date: 2026-08-05 11:07:30 +0800
Delegated-agent output: `runs/pi_medical_monitoring_p9_shadow_run_hash_exact_20260805.md`

## Verdict

Pass for the bounded source-only slice; external route intentionally not dispatched. This does not clear the independent real-loop gate.

## Boundary Check

- Codex must confirm the delegated agent stayed inside allowed paths.
- Codex must confirm only the requested output file was written.

## Codex Verification

- `RuleShadowRun.create()` now requires raw exact lowercase 64-hex gold and diagnostic case-set digests; only omitted diagnostic digest values (`None`/`""`) receive the deterministic empty-set digest.
- Persisted shadow-run reads still rebuild complete modern rows and fail closed when any case-set, diagnostic-set, diagnostic-result or coverage digest is padded, uppercase or non-string.
- `pytest -q tests/test_monitoring_protocol_rules.py tests/test_monitoring_protocol_rule_repository_hardening.py`: 59 passed.
- `pytest -q tests/test_monitoring_gold_shadow_p7c.py tests/test_monitoring_rule_lifecycle.py`: 57 passed.
- Protocol API/review/cross-project adjacency: 16 passed, 1 warning; daily-run/record-resolver/repository adjacency: 96 passed, 41 subtests.
- `python3 -m py_compile` passed for changed modules/tests.
- `_optional_sha256` now preserves only `None`/empty-string omission and rejects non-canonical non-empty values; sample-set/confirmation factory regressions cover padded, uppercase and non-string inputs.
- Shadow-sample service plus protocol API adjacency: **49 passed, 1 warning**.
- MY008 fixture collection remains blocked by missing `cryptography`; no dependency was installed. Runtime/provider/browser/real-project acceptance was not run because the formal gate is read-only/blocked.

## Delegated-Agent Output Review

- No delegated-agent output was used; the runner path remains reserved and was not dispatched or written.
- Changes are limited to RuleShadowRun digest admission, the shared provisional sample/confirmation digest boundary and focused tamper regressions. Shadow evaluation semantics are unchanged.
- Codex retains final authority for runtime, browser, scientific, visual and commercial acceptance.

## Residual Risk

- Persisted sample-set/confirmation readers already enforce canonical digest bytes; no reader logic changed in this slice.
- The real-loop/provider/browser gate remains blocked pending five formal reviewer outcomes; no E2E or commercial-readiness claim is made.

## Hermes Boundary

- Hermes route was recorded by the workflow guard but not dispatched; no external output or provider call is part of this slice.
