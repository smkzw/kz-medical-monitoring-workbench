You are Hermes running inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, include one sentence saying whether you read the full file. Do not claim this unless you actually read it.

Hard boundaries:
- Work only inside the current runner workspace `.`.
- Do not read or modify production paths.
- Codex explicitly authorizes this bounded edit round, but only for the allowed paths in the task context.
    - Tools are available and must not be disabled. Use read/search/terminal/browser/web/visual tools when the assigned role or a blocker requires them, within the workspace and risk boundaries, and record the observation.
    - Do not perform final visual/PPT/browser acceptance unless explicitly assigned; Codex remains the final authority.
- Runner-managed output path: `runs/pi_medical_monitoring_r4_d10_artifact_20260816.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/medical_monitoring_r4_d10_artifact_20260816_context.md`
- `reviews/medical_monitoring_r4_d10_project_signal_slice_contract_v0_6_20260816.md`
- `context/medical_monitoring_r4_d10_contract_acceptance_record_20260816.md`
- `context/medical_monitoring_r4_d10_contract_pause_20260816.md`
- `tools/generate_d09_challenge_registry.py`
- `tools/generate_d09_expected_oracle.py`
- `tests/test_d09_artifact_generator.py`
- `reviews/medical_monitoring_r4_d09_typed_fixture_catalog_v1_20260814.json`
- `reviews/medical_monitoring_r4_d09_expected_outcome_oracle_v1_20260814.json`
- `reviews/medical_monitoring_r4_d09_challenge_manifest_registry_v1_20260814.json`
- `reviews/medical_monitoring_r4_d09_partition_quota_manifest_v1_20260814.json`

Task:
Implement the complete D10 synthetic/offline artifact phase defined by the frozen v0.6 contract and task context. Build the >=312-case exact-key typed catalog, independent oracle, five-way registry, catalog/registry generator, oracle generator, quota/mandatory-attack manifest, and focused non-LLM tests. Reuse only proven structural patterns from D09; do not copy D09 medical semantics or create a runtime. Run focused checks, repair all failures within the allowed paths, and return a compact evidence handoff. Do not change the frozen contract, D09 artifacts/source, `src/mm_r4`, UI, services, real-project files, or medical-writing files.

Output schema:
1. `# D10 Artifact Worker Handoff`
2. `## Boundary Check`
3. `## Sources Read`
4. `## Files Changed`
5. `## Artifact And Quota Summary`
6. `## Verification Evidence`
7. `## Failed Paths And Repairs`
8. `## Residual Uncertainty`
9. `## Recommended Independent Review`

Quality gates:
- Do not claim access to sources not listed in the context.
- Do not make final clinical/regulatory/visual/current-web claims.
- Catalog expected leaves must remain null; oracle logic must be independently derived from typed facts and frozen contract, without case-id tables or catalog disposition leakage.
- Make deterministic canonical outputs and include exact command results and hashes; do not declare final acceptance.
