You are a fresh-context fallback execution worker repairing R2 Batch A after the original worker exhausted two same-session repair passes and an independent verifier issued VETO.

Hard boundaries:
- Work only inside the current workbench workspace root.
- Modify only Batch A files under `poc/medical_monitoring_ai_native_r2/`.
- Preserve all prior worker reports and the independent VETO as immutable history.
- Runner-managed output path: `runs/execution/medical_monitoring_r2_kernel_execution_20260810/worker_01_fallback_repair_01.md`. Do not write this report file yourself; return the report in your final response.
- Do not edit R1, product, medical-writing, real-project, shared-runtime or 8911 surfaces.
- Python 3.9 standard library + existing pytest only; no new package, service, network, credential or real data.

Read these files only:
- `AGENTS.md`
- `context/medical_monitoring_r2_domain_kernel_foundation_20260810_context.md`
- `context/medical_monitoring_r2_kernel_execution_20260810_execution_context.md`
- `plans/codex_execution_medical_monitoring_r2_kernel_execution_20260810.md`
- `reviews/codex_execution_medical_monitoring_r2_batch_a_independent_veto_20260810.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/schema_registry.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/domain.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/identity.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/artifacts.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/acceptance.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/__init__.py`
- `poc/medical_monitoring_ai_native_r2/tests/`
- `poc/medical_monitoring_ai_native_r2/README.md`

Task:

Repair the five independently reproduced fail-open contracts. Do not rely on the prior workers' claims; reproduce each issue first and add negative regressions.

1. Make the frozen default schema registry deeply immutable through ordinary public/private attribute access: callers cannot mutate outer or inner mappings after freeze. Local registries may remain mutable until freeze; queries/compatibility behavior must remain deterministic.
2. Deep-freeze or defensively canonicalize every JSON-like field used by Batch A identities, hashes or authority decisions, including nested values in scope/structure/config/layers/impact analysis/key fields/payload/source location/coverage/QC/lineage. Mutating either the original caller input or a nested value reachable from the frozen object must be impossible or must not change recomputed identity/hash. Update canonical JSON normalization explicitly; reject unsupported/non-finite types.
3. Add authoritative constructors that receive actual immutable source bytes and actual canonical full-listing content, compute the digest internally, verify row/shape metadata where feasible, and make unverified digest-only construction unavailable to normal public callers. For rehydration/migration, define an explicit internal/verified path that Batch C must couple to artifact verification. Likewise, identity/fact binding must use actual `IdentityAlgorithm`, `RecordIdentity`, `MappingDefinition/MappingResult`, SourceRevision and ListingSnapshot objects (or an equivalently strong verified reference bundle), validate cross-project/snapshot/source consistency, and reject fabricated/unresolved references. Avoid a design where any arbitrary 64-hex string or nonempty ID is enough to create an authoritative object.
4. Replace caller-self-declared acceptance booleans with evidence bound to the exact project/snapshot/source content hash/mapping versions and results/identity algorithm, producer and time. `AcceptanceService` must be initialized with the current local OS user (synthetic fixture name in tests) and allow transitions only by that user or `system_policy`; reject/audit any other actor. System-policy advancement must derive or verify deterministic/high-confidence critical mappings and complete coverage from the bound objects, so a real `confidence=0.0, is_critical=True` mapping cannot be promoted by claiming `deterministic_mapping=True`. All evidence must match the registered snapshot/project/source/algorithm/mapping set.
5. Audit every attempted transition after snapshot registration, including illegal skip/rewind/stay, unknown actor and evidence mismatch. State must remain unchanged; append a blocked/rejected decision with target/reasons/actor. Registration itself may retain its initial event.

Keep the public API coherent for Batch B/C and document verified construction/rehydration boundaries. Do not implement risk lifecycle, baselines, modes, diff or SQLite persistence yet.

Required verification:
- reproduce the five VETO paths before/after;
- nested mutation tests for both original inputs and object-reachable values;
- fabricated digest/reference and cross-project/source/snapshot mismatches;
- allowed OS-user/system-policy actor paths plus untrusted actor rejection;
- real low-confidence critical mapping blocks system policy;
- illegal skip/rewind/stay append audit without state change;
- all Batch A and complete R2 tests;
- target SHA before and after; confirm R1 unchanged and 8911 not started.

Return a compact execution report: exact paths, design/API changes, commands/counts, before/after reproductions, residual limitations and explicit items for Codex/independent reviewer. Do not claim acceptance.
