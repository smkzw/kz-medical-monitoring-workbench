# R4-D07 validation artifacts fresh independent acceptance review

You are a fresh-context independent clinical/engineering verifier. Review the final synthetic/offline R4-D07 contract and validation artifacts. The producing workers and manager cannot accept their own work.

## Hard boundaries

- Work read-only inside the current workbench (`.`).
- Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d07_artifacts_acceptance_20260813.md`. It is runner-managed; return it, do not write it through tools.
- Do not edit files, implement D07 runtime, run real projects/providers/browser/R5/product/services/medical-writing, or start port 8911.
- You may run only the deterministic artifact generator/tests/static audits and read the exact files below.

Read these files only:

- `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`
- `runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813_followup3.md`
- `reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json`
- `reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json`
- `tools/generate_d07_challenge_registry.py`
- `tests/test_d07_artifact_generator.py`
- `runs/execution/medical_monitoring_r4_d07_artifacts_20260813/worker_03_followup1_emitted_artifacts.json`
- `runs/execution/medical_monitoring_r4_d07_artifacts_20260813/worker_03_followup1_evidence.json`
- `runs/execution/medical_monitoring_r4_d07_artifacts_20260813/manager.md`

## Frozen snapshot

- contract file `0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84`, semantic `6facbaed37a97f7963a3010072687d0a2509a0f0e768058bd71067b36ec3b02a`;
- semantic acceptance report `467aa75c2714a010eeab825b73d463726590a9fe6c2632e10b5cafb65acbcd63`;
- catalog file `47bc39c13270f841ac93bd28b1b9d68f60a7ba0b651aecdbd6465aac1f2882e4`, content `bc9190ef7204550c114afd0c553741e68274350e8602e675505f056942e963ed`;
- oracle file `80041644e94d64771e5010aae4b758bda069b4627bded6d704ae14774d6b1c52`, content `82b1f5b8845063ed1bccb623d228bc5a52c028b6aeceef814f80cb679954d367`;
- registry file `5fad6b7c8ff9ef91103e2c4d6c98f7ab616bef2b7b61df9f5a214d6307519b3f`, content `0072e8448f666ce581123ad19ea939de9f89fbf01c53455d024d49f545bec705`;
- generator `30d82164eb15e8231e9832af566f00f31f932e7a1e431d369b64d619673505da`;
- tests `5693fa748efdb4d8f584ec021bc60a208f30c9b511abae232ecd47fe83a733d5`;
- manager report `20f88cbea80a87a51822ef1b57000d582b974eda2ddffe2f3e7be330c5ad5da2`.

## Required verification

1. Recompute all hashes and run generator `--check-inputs`, registry `--check`, focused pytest, compile/static import audit and port 8911 listener check.
2. Verify exactly 144 cases, contiguous IDs, category distribution `12/16/16/16/14/18/14/12/10/8/8`, five-way case/fixture/oracle/manifest/test bijection, exact leaf/program mapping, closed DSL and deterministic byte rendering.
3. Verify catalog contains no expected outcome and oracle contains no typed input/runtime path; generator assembles/validates only and cannot derive medical expected values from fixtures/runtime.
4. Clinically spot-check matrix coverage, especially cases 004/005/006/007/009; all five L1 dispositions; unit/range/baseline/trend/grade/CS-NCS/follow-up/organ/examination; owner/query/priority/lifecycle/Journey; and integrity cases 028/119–128.
5. Verify authority-backed L1 not_applicable is distinct from grade not_applicable, empty table is neither negative nor not_applicable, and an open D05 gate yields no D07 unit/risk/query/priority/lifecycle.
6. Verify mutation vocabulary covers the §14.2 classes and distinguish artifact-layer evidence from future runtime execution. Do not reject merely because runtime is intentionally absent.
7. Identify any P0-P4 defect that makes the artifact freeze circular, under-covered, overfit, non-deterministic, or inconsistent with v0.4. Findings must cite exact case/schema/path and observed evidence.

Return boundary/sources/hashes, checks run, findings P0-P4, accepted invariants, residual boundaries and final disposition. If no actionable P0-P4 remains, end `VERDICT: ACCEPT_D07_ARTIFACT_FREEZE`. Otherwise end `VERDICT: REVISE`.
