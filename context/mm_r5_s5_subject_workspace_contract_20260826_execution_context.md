# Execution Context: mm_r5_s5_subject_workspace_contract_20260826

Created: 2026-08-26 01:46:11
Objective: Freeze and independently verify the renderer-neutral R5-S5 Subject Workspace and Patient Journey implementation contract now that both public-authority producers are accepted, while keeping 8911 stopped and medical-writing untouched.
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_opencode_flash` -> `codex-subagent` / `codex` / `gpt-5.6-luna`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `AGENTS.md`.
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`, R5/S5.
- `reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md` and
  `artifacts/medical_monitoring_r5_contract_v0_3/{exact_contract,challenge_registry,quota_ledger,manifest}.json`.
- `context/medical_monitoring_r5_s4_acceptance_record_20260819.md`.
- `context/medical_monitoring_r5_s5_public_authority_producers_v0_1_acceptance_record_20260826.md`.
- Accepted producer modules and focused tests under
  `poc/medical_monitoring_ai_native_r5/{src/mm_r5,tests}`; their bytes are frozen by the acceptance record.
- Accepted S1-S4 source/tests/evidence under `poc/medical_monitoring_ai_native_r5` are read-only authority inputs.
- Current filesystem is final truth; this workspace is not Git.

Starting anchors:

- R5 v0.3 exact contract: `3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949`.
- Producer acceptance record: `76ec09525bc37a3efc4112bae5b5d1e11b9b9fc46a0b9c04c5a19ba0902364c2`.
- `public_authority_common.py`: `4767e28ab7e54a4fbc89e3e30a12448467597cdadfc06833f11158bc2aa54b4c`.
- `subject_temporal_public.py`: `0a519d6b93dee9bc06930707eed7f6b7f2be180fe2b35dc25d23ccf8ce918be7`.
- `aemh_match_history_public.py`: `3463eedf0bad35596f9b1f28c9479c76fb0cffaf5977766e812839e342bd3243`.

## Risk Boundaries

- No product/frontend/service/package/runtime or medical-writing writes.
- Do not modify any accepted R1-R5 source, test, evidence, context, review, artifact or tool.
- Do not create S5 runtime or test modules. This task freezes contract-only artifacts.
- Do not start any service or port; 8911 must have no listener throughout.
- Do not read real project data or invoke real models for medical analysis.
- Do not design or test system security.
- Do not create bytecode or cache files; use `PYTHONDONTWRITEBYTECODE=1` and no-cache checks.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

### Exact create-only output allowlist

- `context/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_20260826_context.md`
- `reviews/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_20260826.md`
- `artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/exact_contract.json`
- `artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/source_leaf_matrix.json`
- `artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/challenge_registry.json`
- `artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/manifest.json`
- `tools/generate_medical_monitoring_r5_s5_subject_workspace_contract_v0_1.py`
- `tools/verify_medical_monitoring_r5_s5_subject_workspace_contract_v0_1.py`

Worker 01 may create the first seven paths except the verifier. Worker 02 may
create only the verifier after Worker 01 is terminal. Worker 03 is read-only.
Runner-owned reports are persisted by the runner and are not worker write paths.

## Contract Requirements

- Freeze the renderer-neutral S5 Subject Workspace/Journey contract, not UI.
- Consume the accepted public packets; never use fixture text, counts, case ids,
  filenames, hashes, nearest records or UI state as medical/identity authority.
- Close one shared temporal spine/window/selection/anchor across Journey, Profile
  and Timeline; dates must preserve exact/partial/conflict/missing state.
- Cover exactly eight audience domains, unknown-domain fail-closed, non-color
  event/risk encoding, and the accepted native Chinese lexicon/forbidden terms.
- Preserve AEMH original-reminder and later-recorded append-only history without
  automatic closure or identity rewrite.
- Pin exact source-to-leaf authority mappings, validators, canonical identities,
  challenge rows, all source hashes and the future runtime create-only allowlist.
- `ACCEPT_R5_S5_CONTRACT` is eligible only if every core S5 leaf has executable
  accepted authority and zero deferred/placeholder/self-signed mappings.
- Acceptance may unlock only an exact later synthetic/offline S5 runtime allowlist;
  it never accepts runtime, UI, browser, real projects/models or product state.

## Work Items

1. Design and generate the exact S5 typed contract and source-to-leaf authority mapping from the accepted R5 v0.3 stage contract plus accepted S1-S4 and public-authority producers.
2. Build the deterministic verifier, challenge registry, negative/replay gates, and frozen source/path hashes for the exact S5 contract without creating S5 runtime.
3. Independently audit the frozen S5 contract for deferred authority, fail-open mappings, temporal/domain/history identity gaps, protected boundaries, and exact unlock conditions.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
