You are a Codex native subAgent running under a parent Codex task.

The parent Codex owns the project contract, source authority, final verification, production boundary, and user delivery. Use the requested model `gpt-5.6-sol` with reasoning effort `high`. Read and comply with the workspace `AGENTS.md`; do not route through Hermes or another external Agent.

Hard boundaries:
- Work only inside the current workbench workspace.
- Create only the nine implementation-contract paths listed in the task context.
- Do not create producer/runtime/test/evidence files or modify any existing R1-R5, root init, frontend, services, packages, runtime, deploy, medical-writing, or real-project file.
- Do not start 8911, services, browsers, real projects, or models.
- Do not issue an acceptance verdict.
- Runner-managed output path: `runs/codex-subagent_medical_monitoring_r5_s5_public_authority_implementation_contract_20260819.md`. Do not write that report path with tools; return the complete handoff and let the runner persist it.

Read these files only:
- `context/medical_monitoring_r5_s5_authority_contracts_20260819_context.md`
- `.hermes/plans/2026-08-19_1945-medical-monitoring-r5-s5-contract.md`
- `context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md`
- `reviews/medical_monitoring_r5_s5_public_authority_contract_v0_1_20260819.md`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/exact_overlay.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/source_matrix.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/challenge_registry.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/base_inputs.json`
- `artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json`
- `tools/generate_medical_monitoring_r5_s5_public_authority_contract_v0_1.py`
- `tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py`
- `artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json`
- `context/medical_monitoring_r5_s4_acceptance_record_20260819.md`
- `context/medical_monitoring_r5_s4_runtime_contract_erratum_acceptance_record_20260819.md`
- `poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s4_readonly_sha256.json`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py`
- `poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_journey.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/contracts.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/authority_adapter.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_authority_builder.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_authority_builder.py`

Task:
Create and freeze one exact machine-verifiable implementation contract for
`subject-temporal-public-v1` and `aemh-match-history-public-v1`. Implement the accepted planning
requirements in the task context: exact Python >=3.9 public APIs; typed source bundles; accepted
17/13 output objects without extra leaves; per-leaf real source joins; canonical hash, identity,
visibility, source, date, study-day, visit, eight-domain and AE/MH append-only invariants; exact
schema/authority version `2026-08-19.1`; audience contract `contract.s4.1`; accepted 81-error-code
union with deterministic priority; no file I/O/artifact imports/assert/case-id/sentinel branches in
future runtime; exact producer allowlist and shared-common SHA invalidation.

Freeze 236 real runtime cases: subject 48 inherited + 95 producer-specific, AE/MH 16 inherited +
77 producer-specific. Keep the remaining 22 artifact-governance cases in the contract verifier.
Every runtime row must name typed fixture, one mutation, expected code, forbidden audience output,
and non-LLM oracle. The contract verifier must pin the accepted 10-file snapshot, all parent/source/
protected pins, deterministic 542-file medical-writing aggregate, exact contract and producer path
sets, absence of all producer files/bytecode before acceptance, and stopped 8911.

Run generator `--check` and verifier in normal and `PYTHONOPTIMIZE=2`, Ruff with no cache, SHA and
boundary checks. Only `ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT` may later unlock
producer creation; this work is not either producer acceptance and does not unlock S5.

Output schema:
1. `# Codex SubAgent Task: medical_monitoring_r5_s5_public_authority_implementation_contract_20260819`
2. `## Boundary Check`
3. `## Work Performed`
4. `## Evidence And Observations`
5. `## Verification And Gaps`
6. `## Next Action For Parent Codex`
