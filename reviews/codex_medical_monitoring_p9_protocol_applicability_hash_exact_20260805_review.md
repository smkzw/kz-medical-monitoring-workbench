# Codex Review: medical_monitoring_p9_protocol_applicability_hash_exact_20260805

Date: 2026-08-05 11:16:00 +0800
Delegated-agent output: `runs/pi_medical_monitoring_p9_protocol_applicability_hash_exact_20260805.md`

## Verdict

Pass for the bounded source-only slice; external route intentionally not dispatched. This does not clear the independent real-loop gate.

## Boundary Check

- Codex must confirm the delegated agent stayed inside allowed paths.
- Codex must confirm only the requested output file was written.

## Codex Verification

- `ProtocolApplicabilityAssignment.create()` now requires raw exact lowercase 64-hex `evidence_source_content_sha256` bytes; no trim/lower/coercion is used.
- Persisted applicability assignment reads reconstruct through the strict factory and fail closed for padded, uppercase and non-string digest tampering.
- `pytest -q tests/test_monitoring_protocol_rules.py tests/test_monitoring_protocol_rule_repository_hardening.py`: 60 passed.
- Protocol API/lifecycle/review/cross-project adjacency: 57 passed, 1 warning.
- Daily-run/record-resolver/repository adjacency: 96 passed, 41 subtests.
- `python3 -m py_compile` passed for changed source/tests.
- MY008 fixture collection remains blocked by missing `cryptography`; no dependency was installed. Runtime/provider/browser/real-project acceptance was not run under the read-only/blocked gate.

## Delegated-Agent Output Review

- No delegated-agent output was used; the runner path remains reserved and was not dispatched or written.
- Changes are limited to applicability evidence digest admission and its persistence regressions; applicability overlap/CAS and clinical semantics are unchanged.
- Codex retains final authority for runtime, browser, scientific, visual and commercial acceptance.

## Residual Risk

- Protocol applicability semantics, live source-token/CAS replay, authorization, provider/runtime, browser and real-project acceptance remain unverified.
- The formal gate remains blocked pending five hash-bound reviewer outcomes; no commercial-readiness claim is made.

## Hermes Boundary

- Hermes route was recorded by the workflow guard but not dispatched; no external output or provider call is part of this slice.
