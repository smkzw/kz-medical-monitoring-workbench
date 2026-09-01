# Codex Review: medical_monitoring_phase_c3_mapping_inventory_20260802

Date: 2026-08-02 00:36 CST
Execution: Codex direct; no Hermes route, conference, or sub-agent was used.

Changed source/test/evidence:
- `services/api/app/monitoring_adapter_mapping_plan.py`
- `tests/test_monitoring_adapter_mapping_plan.py`
- `services/api/app/monitoring_mapping_contract.py` (minimal CM/IP false-positive fix)
- `runs/execution/medical_monitoring_phase_c3_mapping_inventory_20260802/build_inventory.py`
- `runs/execution/medical_monitoring_phase_c3_mapping_inventory_20260802/OBSERVED_ADAPTER_MAPPING_INVENTORY.json`

## Verdict

**Pass for the review-only source-code mapping inventory; it is not an activated mapping
or real-project onboarding result.**

## Boundary Check

- RUX, MY009 and MG-K10 adapter source files were inspected for constants and method
  references only. The inventory script does not import or invoke those adapter classes,
  read any listing/protocol bytes, resolve paths, start a service, or write a registry.
- No `main.py`, adapter implementation, frontend, runtime database or medical-writing file
  was patched. The current `main.py` content hash remains the recorded
  `0dabf52df865023a3e9f66c880462c3ec66775b1345c2e4a7fe796cdd1d104fc`.
- The JSON evidence is explicitly marked
  `source_code_constants_and_method_references_only` and `review_only=true`; its
  observations are not eligible for activation.

## Contract Review

- `StudyAdapterMappingObservation` binds adapter/project, source sheet/field, capability,
  observation kind, code locator and recommended role. Local-path-like values, unknown
  capabilities and non-review-only status fail closed.
- `StudyAdapterMappingPlan` rejects cross-project observations, duplicate IDs and
  duplicate source surfaces, sorts observations deterministically and binds
  `plan_sha256`.
- The inventory contains **3 plans / 46 observations**: RUX 11, MY009 18 and MG-K10 17.
  It records representative fixed sheet/metric surfaces from the currently inspected
  constants, not a claim that every header or medical semantic is final.
- The existing mapping semantic validator is reused. During C3 it exposed that its
  literal `ip_` marker falsely rejected the canonical `cm.non_ip_medication` role; the
  minimal token-aware fix preserves that canonical CM role while continuing to reject
  actual `ip_*` roles in CM. The change is covered by the C3 tests and semantic-quality
  regression set.

## Codex Verification

- C3 focused tests: **6 passed**.
- C1/C2/C3 contract tests plus mapping semantic-quality regressions: **159 passed**.
- Inventory script produced 3 plans/46 observations with
  `inventory_sha256=f395dc787910648362c41475266bfab80de171ab7615e68cdce904ddbe01807c`
  and no absolute-like sheet/field/evidence references.
- `python3 -m py_compile` passed for C3 module, tests and inventory script.
- `python3 -m ruff check` passed for the C3 module, tests, validator and script.
- No browser/runtime check was run; 8911/5174 remain stopped and 18911/PID 43191 was
  not touched.

## Residual Risk

- The 46 entries are source-code observations and representative fields, not approved
  clinical mappings. Medical review, complete header/row identity, standards, units,
  date precision, treatment identity evidence and capability confirmation remain open.
- The inventory is not attached to a real C1 config hash, does not migrate fixed adapter
  logic, and does not prove a fourth unseen project can onboard without code.
- B6 reviewer outcomes are absent and B4 residual blockers remain; no activation,
  dual-read, migration, disposition write, real-project run or service start is allowed.
