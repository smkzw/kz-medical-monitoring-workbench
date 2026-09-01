# Task Record: monitoring_mapping_contract_v14_20260730

Created: 2026-07-30
Status: implemented, pending Codex acceptance

## Goal

Repair the generalized medical monitoring field-mapping prompt and deterministic
semantic gates for treatment identity, dose ambiguity, scale totals, and IP change
capability claims without touching runtime databases.

## Files Changed

- `services/api/app/monitoring_mapping_semantic_quality.py`
- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_mapping_semantic_quality.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_mapping_activation.py`

## Contract Versions

- ROLE_CATALOG_VERSION: v1 → v2
- RULE_CATALOG_VERSION: v2 → v3
- PROMPT_VERSION: v13 → v14
- Backward-compatible alias ROLE_CATALOG_V1 = ROLE_CATALOG_V2 retained for scripts

## New Rules

- G-CMIP-005: treatment-object identity not established (capability blocker)
- G-CMIP-006: dose semantics indistinguishable (capability blocker)
- G-CMIP-007: IP change lifecycle families not available (capability blocker)
- G-SCALE-002: scale score misclassified as procedure/record number (review warning)

## New Capability

- ip_change_lifecycle: blocked when dose_adjustment/interruption/discontinuation/restart
  action families are absent from the listing

## Verification

- 311 focused + adjacent tests pass
- Ruff E4/E7/E9/F: all clear
- py_compile: all clear
