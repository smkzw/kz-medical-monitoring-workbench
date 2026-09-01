# Codex Conference Review: mm_r7_slice_03_product_mount_contract_20260828

Date: 2026-08-28

## Verdict

Pass after contract revision; frozen for implementation only.

## Boundary Compliance

Both participants were read-only and did not modify source, start services, call models, run projects, or touch medical-writing. The governed workflow packet was used; no ad-hoc Hermes substitution occurred.

Route-policy note: the live packet declares the Grok fallback as provider `cursor` / model `cursor-grok-4.6`; `cursor-cli` / `auto` remains a cataloged finite-code route, not a third conference participant. This note records the validator vocabulary mismatch and does not claim an unrun role.

## Participant Outputs Reviewed

- Pi / google-antigravity / gemini-3.7-flash high: complete, primary route.
- Grok Build / grok-4.6 medium: complete, primary route.

## Conference Panel Review

Both reviewers rejected direct mounting of the isolated router. Pi identified project/profile scope existence, pre-open project validation, and app-wide handler regressions. Grok independently identified unscoped identity, global handler pollution, import-time SQLite DDL, per-request lifecycle, project isolation and package-import decisions. No finding supported direct `create_isolated_app` reuse in product `main.py`.

## Main-Venue Codex Review

Codex inspected the actual `main.py`, R5 router, monitoring router, project canonicalization, runtime directory, Slice-02 factories and SQLite constructors. The frozen contract now uses a project-scoped thin adapter, local top-level Chinese responses, per-project workspace, project validation before store open, automatic project/run layer existence resolution, per-request close, existing action seams, and namespace import of the frozen R7 core. It explicitly forbids app-wide R7 exception handlers.

## Codex Independent Verification

This is a contract-only gate: no implementation tests or browser checks are claimed. Read-only import proved the frozen R7 package is reachable through `poc.medical_monitoring_ai_native_r7.src.mm_r7` without a `sys.path` rewrite. Slice-02 gates remain 93 R7 / 763 R6; ports remained stopped at the preceding accepted checkpoint.

## Final Decision

Freeze contract SHA-256 `23a01f905fa1d19566873b0f04bd8a55f38f37e9ce28529a09a39a1f75f89b9b` as `FROZEN_R7_SLICE_03_PRODUCT_MOUNT_CONTRACT_V1`. This authorizes only the bounded implementation slice; it does not accept a product mount or R7 overall.
