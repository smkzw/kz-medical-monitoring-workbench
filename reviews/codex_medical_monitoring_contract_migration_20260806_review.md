# Codex Review: medical_monitoring_contract_migration_20260806

Date: 2026-08-06

## Verdict

`accepted_source_only_with_unrelated_full_suite_blocker`

## Scope review

- Changed only the declared shared App legacy/demo region and three named Python contract files.
- Kept feature-owned medical-monitoring source, styles, main/runtime and medical-writing/reference files unchanged.
- No external agent, Hermes dispatch, service, provider, browser, API login or real-project action.

## Verification

- Python named contracts: 169 passed.
- Medical-monitoring Node suite: 36/36 files passed.
- Vite build: 1,956 modules transformed and production build passed.
- App active route mounts remain feature-owned and project-bound; the App no longer imports demo fixtures or contains local legacy Subject/Profile definitions.
- Protected hashes and stopped-port checks passed.

## Contract quality

The migration replaces legacy function-body parsing with feature-owned model/view assertions and a
stable App `timelineLaneDefs` boundary. It preserves exact semantic checks for CM/IP separation,
sparse unloaded-profile warnings, risk-event/point focus, source evidence and active route ownership.
The prior failed deletion hypothesis was not accepted until the tests were relocated and the complete
named suite returned green.

## Residual risk

No runtime or clinical/scientific acceptance was performed. Full pytest collection remains blocked by
the unrelated medical-writing `_REQUIRED_CORE_BODY_SEMANTIC_IDS` import error. Real-loop activation is
still forbidden by B6/C14/read-only gate. This slice is not a commercial release.

Hermes route was not dispatched; Codex executed and accepted the bounded source work directly.
