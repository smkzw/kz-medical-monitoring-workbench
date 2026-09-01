# Codex Review: medical_monitoring_p9_rule_source_hash_exact_20260805

Date: 2026-08-05 11:20:00 +0800
Delegated-agent output: `runs/pi_medical_monitoring_p9_rule_source_hash_exact_20260805.md`

## Verdict

Pass for the bounded source-only slice; external route intentionally not dispatched. This does not clear the independent real-loop gate.

## Boundary Check

- Codex must confirm the delegated agent stayed inside allowed paths.
- Codex must confirm only the requested output file was written.

## Codex Verification

- Persisted complete monitoring rules now compare a raw exact lowercase 64-hex `source_text_sha256` with the digest calculated from stored source text; no trim/lower/coercion occurs.
- Added SQLite read-back shape regressions for padded, uppercase and non-string source hashes.
- `pytest -q tests/test_monitoring_protocol_rule_repository_hardening.py tests/test_monitoring_protocol_rules.py`: 61 passed.
- Protocol API/lifecycle/review/cross-project adjacency: 57 passed, 1 warning; shadow/lifecycle plus sample service: 56 passed, 1 warning.
- Daily-run/record-resolver/repository adjacency: 96 passed, 41 subtests.
- `python3 -m py_compile` passed for changed source/tests.
- MY008 fixture collection remains blocked by missing `cryptography`; no dependency was installed. Runtime/provider/browser/real-project acceptance was not run under the read-only/blocked gate.

## Delegated-Agent Output Review

- No delegated-agent output was used; the runner path remains reserved and was not dispatched or written.
- Changes are limited to persisted rule source hash validation and its regression. Rule semantics and clinical content are unchanged.
- Codex retains final authority for runtime, browser, scientific, visual and commercial acceptance.

## Residual Risk

- Legacy partial-identity rules continue to take the established readiness diagnostic path before strict source-hash revalidation.
- Live source registry, authorization, source-token/CAS replay, provider/runtime, browser and real-project acceptance remain unverified; no commercial-readiness claim is made.

## Hermes Boundary

- Hermes route was recorded by the workflow guard but not dispatched; no external output or provider call is part of this slice.
