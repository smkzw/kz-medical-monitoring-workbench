You are continuing the same `worker_01` session for the R2 Batch A acceptance repair.

Hard boundaries:
- Work only inside the current workbench workspace root.
- Modify only Batch A files under `poc/medical_monitoring_ai_native_r2/`.
- Preserve the initial report as immutable history.
- Runner-managed output path: `runs/execution/medical_monitoring_r2_kernel_execution_20260810/worker_01_followup_01.md`. Do not write this report file yourself; return the report in your final response.
- Do not edit R1, product, medical-writing, real-project, shared-runtime or 8911 surfaces.

Read these files only:
- `context/medical_monitoring_r2_kernel_execution_20260810_execution_context.md`
- `plans/codex_execution_medical_monitoring_r2_kernel_execution_20260810.md`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/schema_registry.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/domain.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/identity.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/artifacts.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/acceptance.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/__init__.py`
- `poc/medical_monitoring_ai_native_r2/tests/`
- `poc/medical_monitoring_ai_native_r2/README.md`

Codex independently reproduced the following contract failures against the current files; Batch A is not accepted:

```text
fresh_identical_artifact_hash_equal False
cross_project_record_digest_equal True
external_mutation_bypassed_chain True
no_evidence_system_policy_eligible True
candidate_materialized_as_canonical_fact candidate
default_registry_runtime_mutable True
```

Inspection also found that `SourceRevision.content_hash` and `ListingSnapshot.content_hash` are derived only from metadata/IDs and do not bind the actual immutable source/listing content. A different full listing with the same ID/version/row count/shape cannot be distinguished. Treat this as a seventh blocker.

Repair Batch A only, using the smallest coherent changes to its owned R2 modules/tests:

1. A fresh envelope with identical logical metadata/payload must have the same content hash regardless of random artifact instance ID or timestamp. Preserve an operational `artifact_id` if useful, but exclude it from the content address. Add a regression for fresh-envelope idempotency and concurrent fresh-envelope writes.
2. Record identity must be project-scoped and stable. Include `project_id` in the digest and make the public stable ID deterministic rather than a fresh UUID. Risk identity must likewise use a deterministic public ID; merge/split-derived identity must include lineage so it cannot collapse onto an existing identity with the same dimensions. Add cross-project and repeated-factory regressions.
3. External callers must not mutate the authoritative snapshot acceptance record or bypass transitions. Use frozen values/copy-on-write or an equivalent enforced boundary; `get` and registration/advance returns must not expose mutable authoritative lists/state.
4. Baseline eligibility must require affirmative current evidence rather than treating omitted evidence as complete. Introduce an explicit frozen evidence contract binding source coverage, critical mapping review, identity review, approved scope/deterministic checks and an evidence hash. Missing evidence fails closed. When actor is `system_policy`, approved scope and deterministic/high-confidence mapping evidence are mandatory at the applicable acceptance steps. Keep rejected/blocked attempts auditable.
5. `CanonicalFact` may only represent the facts role. Candidate/inference/suggestion remain ArtifactEnvelope payload roles or future separate objects and cannot be materialized as CanonicalFact. Add negative regressions.
6. The process-wide default schema registry must be truly frozen after construction. Callers cannot append a rogue schema/version. Local registry construction may remain mutable until explicitly frozen. Batch B/C add declarations only by editing the single source declaration table and restarting the process.
7. Bind `SourceRevision` and `ListingSnapshot` to actual immutable content. Do not manufacture a “content hash” from random IDs and metadata. Require/validate a real SHA-256 content digest produced from synthetic source bytes/full listing canonical content, and if needed expose a separate deterministic metadata/revision fingerprint. Ensure full snapshot tests prove different row content yields different content identity even when version/shape/count match. Keep all fixtures synthetic/offline.

Also correct any tests or report wording that currently encode the opposite behavior (for example, the comment saying fresh envelopes intentionally hash differently). Do not implement Batch B/C, edit R1, install packages, start services, or read real projects.

Run:

- focused regressions for all seven blockers;
- all Batch A tests;
- the complete current R2 suite;
- compileall with no persistent cache left behind if practical.

Return a compact execution report with: boundary check; exact changed paths; before/after reproduction evidence for all seven blockers; exact test commands/counts; public interface changes worker_02 must consume; remaining limitations. Do not claim acceptance—Codex owns the gate.
