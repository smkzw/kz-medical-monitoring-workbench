# Codex Review: medical_monitoring_p9_rule_gold_diagnostic_hash_exact_20260805

Date: 2026-08-05 11:00:51 +0800
Delegated-agent output: `runs/pi_medical_monitoring_p9_rule_gold_diagnostic_hash_exact_20260805.md`

## Verdict

Pass for the bounded source-only slice; external route intentionally not dispatched because Codex performed the bounded implementation and verification directly. This does not clear the independent real-loop gate.

## Boundary Check

- Codex must confirm the delegated agent stayed inside allowed paths.
- Codex must confirm only the requested output file was written.

## Codex Verification

- `RuleGoldStandardCase.create` and `RuleDiagnosticCase.create` require an exact lowercase 64-hex `source_content_sha256`; no trim/lower/coercion is used.
- Gold and diagnostic release binding checks require the same exact digest shape and bind evidence locators to the digest without normalizing the digest.
- SQLite persisted gold/diagnostic case reads reconstruct through the strict factories and fail closed on padded, uppercase, and non-string digest tampering.
- `pytest -q tests/test_monitoring_protocol_rules.py tests/test_monitoring_protocol_rule_repository_hardening.py tests/test_monitoring_rule_lifecycle.py`: 98 passed.
- `python3 -m py_compile` passed for the two source modules and two changed test modules.
- Runtime/provider/browser/real-project acceptance was not run: the active real-loop gate is read-only/blocked and all monitored ports remain empty.
- The broader MY008 fixture collection remains unverified because the environment lacks `cryptography`; no dependency was installed.

## Delegated-Agent Output Review

- No delegated-agent output was used; the generated runner path remains reserved and was not written or dispatched.
- Changes are limited to the stated case-digest boundary and its persistence regressions. Shadow-run set hashes and clinical semantics are unchanged.
- Review is source/test based; Codex retains final authority for runtime, browser, scientific, visual, and commercial acceptance.

## Residual Risk

- Legacy gold rows without coverage labels intentionally retain migration compatibility and are not rebuilt by the modern strict factory.
- The real-loop/provider/browser gate is still blocked pending the five hash-bound formal reviewer outcomes; no claim of E2E or commercial readiness is made.

## Hermes Boundary

- Hermes route was recorded by the workflow guard but not dispatched; no external output or provider call is part of this slice.
