# B2 backend migration design

## Boundaries

- The new authority is `packages.medical_monitoring`; old POC module paths become temporary re-export shims until B6 deletes them.
- Every slice is a mechanical move plus import repair. Behavioral redesign, API redesign, and large-file splitting are separate work.
- Product imports change only after all dependencies needed by that product surface are present in the new package.
- Medical-writing routes/assets and frozen legacy `monitoring_*` modules are outside the write scope.

## Package map

- `domain/`: orthogonal states, accepted snapshots, canonical entities, identity, risk lifecycle, schema registry.
- `graph/`: graph IR execution, authoritative store, controller, checkpoints.
- `intelligence/`: normalization, schema profiling, mapping, knowledge/rules.
- `risks/`: domain evaluators and candidate generation.
- `projections/`: dashboard, center, subject/Journey, Query and publication views.
- `reports/`: report review and three-mode outputs.
- `runtime/`: harness, run binding, progress, lifecycle, persistence, backup/recovery.
- `api/`: thin routers only.

## Compatibility strategy

1. Move one cohesive dependency layer into the new package.
2. Repair relative imports inside the new authority.
3. Replace the old module with a small re-export shim so untouched consumers keep working during migration.
   Each POC source root exposes the consolidated `packages` namespace through a temporary relative symlink so isolated legacy subprocesses resolve the same authority without `sys.path` mutation.
4. Add a package-native compatibility test and run the original focused behavior tests through the shim.
5. Commit the slice. Remove all shims only in B6 after the product and tests use the new authority.

## First slice

- Move R1 `domain.py` to `domain/execution.py` and `schema_shape.py` to `domain/schema_shape.py`.
- Move R2 `schema_registry.py`, `domain.py`, `identity.py`, `acceptance.py`, and `risk.py` to `domain/schema_registry.py`, `entities.py`, `identity.py`, `acceptance.py`, and `risk.py`.
- Keep R1 and R2 compatibility shims at their old paths.
- No changes to product routers, main.py, frontend, model bindings, or fixtures.

## Graph slice

- Move R1 `graph.py` and `store.py` to `graph/engine.py` and `graph/store.py`.
- Defer `controller.py` until `capability_runtime.py` moves in the next slice; this avoids making the new graph authority depend on an old POC runtime module.
- Keep isolated legacy subprocesses working through the temporary source-root package links described above.

## Rollback

Each slice is one git commit. Revert that commit to restore the prior source layout; no data migration occurs in B2.
