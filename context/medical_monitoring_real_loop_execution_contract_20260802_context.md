# Context: medical_monitoring_real_loop_execution_contract_20260802

## Goal

Create the post-run evidence boundary for the three-project real LOOP so a
future provider run can be independently checked before senior-medical-monitor
review. The contract must preserve the user's desired AI-lead/user-confirm
workflow while preventing silent scenario omission, cross-project identity
drift, unsupported output claims or route-window violations.

## Source of truth

- `services/api/app/monitoring_real_loop_readiness.py`
- `records/active_slices/medical_monitoring_real_loop_readiness_contract_20260802/REAL_LOOP_READINESS.json`
- current B6 formal package, approved-input dry-run, source-token and CAS
  evidence;
- current global, workspace and product `AGENTS.md` files.

## Contract boundary

- one evidence record per planned scenario (3 projects × 2 roles × 4 tasks);
- exact scenario identity and prompt/model binding;
- opaque batch/output/evidence references; a passed output requires its hash,
  while a failed/blocked run may be hashless;
- explicit uncertainty state and source/evidence traceability;
- timezone-aware start/end timestamps and approved Asia/Shanghai route window;
- failed/blocked scenarios retain a failure detail and cannot be accepted;
- structural completion is named `accepted_for_medical_review`, never
  `medical_approved` or `release_ready`;
- provider, runtime-write and medical-confirmation flags remain false.

## Current state

The readiness manifest is still `blocked` with 10 preflight issues, so no real
execution evidence is present or accepted. The 24-row synthetic fixture is only
unit-test evidence used to prove deterministic validator behavior.

## Next action

Do not run providers or start 8911/5174 until the formal reviewer, source-token,
aggregate/CAS and runtime-identity gates are actually closed. When they are
closed, run each approved scenario once, preserve its evidence row, validate the
complete execution set, and only then proceed to browser/scientific and medical
acceptance.
