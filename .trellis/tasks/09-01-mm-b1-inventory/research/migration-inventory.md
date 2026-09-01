# Phase B migration inventory

Date: 2026-09-01  
Method: static AST import traversal from the live R7/R5 product routers and adapter, supplemented by route/frontend searches. No source was changed during this inventory.

## Product entry surfaces

- `services/api/app/main.py` mounts the current root medical-monitoring router, R5 product router, R7 product router, and frozen legacy `monitoring_*` routes independently.
- `services/api/app/medical_monitoring_r7_product_router.py` is 7,684 lines. It exposes project open/verify/upgrade, backup/restore, workspace bootstrap, run setup/risk rules/profiles, run binding/execution/progress/publication, result overview/subject/source/continuity, and result-entry routes.
- The R7 router has direct POC imports for 14 R7 modules, direct `mm_r1` imports, dynamic `sys.path` insertion for R2–R7, and lazy imports for continuity, harness runtime, and continuity bridge.
- `services/api/app/medical_monitoring_r5_product_router.py` exposes overview, subject workspace, and source evidence through the 2,276-line `medical_monitoring_r5_product_adapter.py`.
- Product-route owning tests: `tests/test_medical_monitoring_r7_product_router.py`, `tests/test_medical_monitoring_r5_product_router.py`, `tests/test_medical_monitoring_r5_product_adapter.py`, `tests/test_medical_monitoring_r5_product_allowlist.py`, and `tests/test_medical_monitoring_r5_subject_flow.py`.

## Reachable backend modules

The live product import graph reaches 95 POC modules: R1 9, R2 5, R3 3, R4 39, R5 12, R6 5, and R7 22. The target below is the module's migration disposition. Test ownership is the matching `poc/medical_monitoring_ai_native_rN/tests/` tree plus the product-route tests above; the noted counts are files with a static import of that module.

### `domain/`

| Source module | Static test files |
|---|---:|
| `mm_r1`, `mm_r1.domain`, `mm_r1.schema_shape` | 4, 21, 1 |
| `mm_r2.acceptance`, `mm_r2.domain`, `mm_r2.identity`, `mm_r2.risk`, `mm_r2.schema_registry` | 7, 14, 12, 8, 2 |

### `graph/`

| Source module | Static test files |
|---|---:|
| `mm_r1.controller`, `mm_r1.graph`, `mm_r1.store` | 2, 2, 19 |

### `intelligence/`

| Source module | Static test files |
|---|---:|
| `mm_r3.normalization`, `mm_r3.primitives`, `mm_r3.schema_registry` | 2, 1, 0 |

`mm_r3.schema_registry` has no direct static test import and must be covered through its consumers before the old tree is removed.

### `risks/`

| Source modules | Static test-file counts in module order |
|---|---|
| `mm_r4`, `aemh`, `cm`, `contracts`, `coverage`, `d07_safety`, `d07_safety_evaluator` | 25, 4, 4, 20, 8, 1, 5 |
| `d08_contracts`, `d08_evaluator`, `d09_contracts`, `d09_evaluator` | 4, 5, 6, 7 |
| `d10_adapter`, `d10_contracts`, `d10_evaluator` | 11, 13, 11 |
| `efficacy`, `efficacy_evaluator`, `ensemble`, `ensemble_contracts` | 4, 2, 6, 6 |
| `ip`, `lifecycle`, `protocol`, `visit_schedule`, `visit_schedule_evaluator` | 4, 8, 3, 4, 3 |

### `projections/`

| Source modules | Static test-file counts in module order |
|---|---|
| `mm_r4.cm_projection`, `d07_journey`, `d07_query`, `d08_projection`, `d09_projection`, `d10_projection` | 3, 1, 1, 5, 6, 12 |
| `mm_r4.efficacy_projection`, `ip_projection`, `projection`, `protocol_projection`, `visit_schedule_projection` | 3, 4, 2, 3, 3 |
| `mm_r5`, `authority_adapter`, `canonical`, `contracts`, `r5_publication_authority` | 22, 3, 1, 9, 3 |
| `mm_r5.s2_authority_builder`, `s2_contracts`, `s2_thin_slice` | 4, 4, 3 |
| `mm_r5.s4_authority_builder`, `s4_contracts`, `s4_projection`, `s4_validator` | 2, 7, 6, 4 |

### `reports/`

| Source module | Static test files |
|---|---:|
| `mm_r6`, `mm_r6.contracts`, `mm_r6.mode_output`, `mm_r6.report_review` | 12, 8, 6, 4 |

### `runtime/`

| Source modules | Static test-file counts in module order |
|---|---|
| `mm_r1.adapters`, `audience_progress`, `capability_runtime` | 8, 2, 6 |
| `mm_r6.agent_harness` | 5 |
| `mm_r7`, `background_recovery`, `continuity`, `continuity_bridge`, `harness_runtime` | 7, 3, 5, 3, 1 |
| `mm_r7.launch_registry`, `launch_schema`, `maintenance_gate`, `migration` | 7, 1, 4, 5 |
| `mm_r7.profile_store`, `project_audit`, `project_backup`, `project_lifecycle`, `project_verifier` | 8, 2, 7, 1, 1 |
| `mm_r7.root_ledger_schema`, `run_binding`, `run_entry`, `run_setup`, `runtime_progress`, `schema_manifest`, `technical_log` | 0, 7, 7, 6, 4, 4, 1 |

`mm_r7.root_ledger_schema` has no direct static test import; its DDL is covered through project-audit/backup/verifier consumers.

### `api/`

| Source module | Static test files |
|---|---:|
| `mm_r7.api` | 1 |

### `tests/fixtures/medical_monitoring/`

The following R4 modules contain fixture data and must become external data assets rather than product Python literals: `mm_r4.fixtures`, `efficacy_fixtures`, `ip_fixtures`, `protocol_fixtures`, and `visit_schedule_fixtures` (8, 4, 3, 2, and 2 static test files respectively).

## Critical cross-layer dependencies

- R7 runtime depends on R1 domain/graph/runtime, R5 publication projections, and R6 reports/harness.
- R5 projections depend on R4 D10/ensemble risk and projection contracts.
- R4 risk domains depend on R2 identity/risk and R3 normalization.
- Therefore deletion must occur only after the full chain is repointed: R1/R2 domain → R1 graph → R3 intelligence → R4 risks/projections → R5 projections → R6 reports/runtime → R7 runtime/API → product routers.

## Frontend inventory

- 165 files exist under `frontend/src/features/medical-monitoring/` across root legacy, `r5`, `r7`, and `g6` generations.
- `App.jsx` imports the R5 page/route state and owns the active R5 browser state around lines 15,078–16,068.
- `MedicalMonitoringR5Page.jsx` embeds R7 Journey, product-loop, and progress components. R7 product-loop and tests import R5 route state/components, so R5/R7 are one coupled current generation and must be flattened together.
- G6 is a separate synthetic-only generation and is not a migration source except for reusable visual/fixture behavior.
- Root `medicalMonitoring*` files are the frozen legacy chain; they remain untouched during Phase B unless route isolation is required.

## Dependency-safe migration order

1. Domain primitives: R1 domain/schema shape and the complete R2 domain set.
2. Graph/runtime primitives: R1 graph/store/controller followed by R1 adapters/capability/progress.
3. Intelligence: R3 normalization/primitives/schema registry.
4. R4 risk domains and their projections; externalize five fixture modules.
5. R5 publication/authority projections and the product adapter.
6. R6 reports/mode output and harness adapter.
7. R7 runtime, lifecycle, persistence, backup/recovery, and continuity.
8. Thin package API and split product routers; then frontend flattening, product synthetic profile, duplicate deletion, and test cleanup.

## Next implementation slice

Start B2 with a move-only domain foundation: create the package skeleton and migrate R1 `domain.py`/`schema_shape.py` plus the five R2 domain modules. Add package-native imports and focused compatibility tests; do not change medical behavior or product routing in this first slice.

