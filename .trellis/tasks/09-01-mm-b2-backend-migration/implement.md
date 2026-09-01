# B2 backend migration plan

## Ordered slices

- [x] Domain foundation: R1 domain/schema shape and complete R2 domain set.
- [x] Graph foundation: R1 graph/store/controller.
  - [x] Graph engine and authoritative store.
  - [x] Capability work-unit controller (moved with runtime dependencies).
- [x] Runtime primitives: R1 adapters/capability/audience progress.
- [x] Intelligence: R3 normalization/primitives/schema registry.
- [ ] Risks and projections: R4 modules, with fixture data externalized separately.
- [ ] Projection authority: R5 modules and product adapter.
- [ ] Reports and harness: R6 modules.
- [ ] Product runtime: R7 modules.
- [ ] Thin API package and product import cutover.

## Per-slice checks

1. Compile moved modules and compatibility shims.
2. Run package-native compatibility tests.
3. Run the original focused behavior tests for the moved modules.
4. Search for unintended medical-writing or frozen legacy changes.
5. Commit only the slice and Trellis journal/task updates.

## First-slice validation

```bash
python3 -m py_compile packages/medical_monitoring/domain/*.py
.venv/bin/python -m pytest -q \
  tests/medical_monitoring/test_domain_compatibility.py \
  poc/medical_monitoring_ai_native_r1/tests/test_domain_store_graph.py \
  poc/medical_monitoring_ai_native_r2/tests/test_r2_a_schema_registry.py \
  poc/medical_monitoring_ai_native_r2/tests/test_r2_a_domain.py \
  poc/medical_monitoring_ai_native_r2/tests/test_r2_b_risk.py
```
