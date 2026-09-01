# Execution Context: medical_monitoring_r5_s2_runtime_20260818

Created: 2026-08-18 14:51:53
Objective: 实现并验收 R5 S2 synthetic/offline renderer-neutral 第一条薄纵切 packet/runtime；不写前端、不启动8911
Task type: `finite_code_task`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `pi` / `cms-smk` / `deepseek-v4-flash`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `context/medical_monitoring_r5_s2_precondition_contract_acceptance_record_20260818.md`
- `reviews/medical_monitoring_r5_s2_precondition_contract_v0_1_20260818.md`
- `artifacts/medical_monitoring_r5_s2_authority_packet_contract_v0_1/{exact_overlay.json,authority_packet_schema.json,manifest.json}`
- `context/medical_monitoring_r5_s1_acceptance_record_20260818.md`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/{contracts.py,canonical.py,authority_adapter.py}`
- `poc/medical_monitoring_ai_native_r5/tests/**`
- R4 public typed contracts/projections/ensemble runtime and synthetic catalog under `poc/medical_monitoring_ai_native_r4/**`, read-only.

## Risk Boundaries

- Only write new S2 files under `poc/medical_monitoring_ai_native_r5/src/mm_r5/`, corresponding new tests/challenge tests/evidence under the R5 POC, and this task's named process records. Existing S0/S1 files and root `__init__.py` are Codex-owned integration surfaces and remain read-only to workers.
- W1 exclusive write set: `src/mm_r5/s2_contracts.py`, `tests/test_s2_contracts.py`.
- W2 exclusive write set: `src/mm_r5/s2_authority_builder.py`, `tests/test_s2_authority_builder.py`, `tests/challenges/test_s2_authority_packet.py`.
- W3 exclusive write set: `src/mm_r5/s2_thin_slice.py`, `tests/test_s2_thin_slice.py`, `tests/challenges/test_s2_thin_slice.py`, `evidence/r4_s2_readonly_sha256.json`.
- Do not modify frontend/services/packages, existing R1-R4, existing S0/S1 code/tests/artifacts, real project data, medical-writing paths, or the accepted S2 precondition artifacts.
- Do not start 8911, browser, model endpoint, or long-running service; no clinical/user-state writes.
- Missing tools or environments must be recorded; do not install packages or alter credentials.
- Worker outputs are evidence; Codex owns `__init__.py` integration, broad tests, review and acceptance.

## Runtime Acceptance Criteria

- W1 mirrors the frozen exact packet schema with immutable typed dataclasses, exact enums, NFC/sorted-unique/cardinality/nullability validation, nonrecursive packet hash/id and fail-closed error codes.
- W2 derives one packet through the real R4 typed pipeline from a synthetic D10 envelope; center, project risk, deep link, source, baseline, two worker attempts/outputs/verifications, visible conflict, independent adjudicator and packet-only ModelEvidence all close by identity. It must not copy verifier decisions or branch on fixture/case/test ids.
- W3 emits one renderer-neutral projection chain: project risk → center cell → Inspector → Workspace/deep link → visit/event/risk anchor → exact source, with canonical return context and no nearest fallback. Public Inspector worker/support/counter refs remain empty and S4-deferred.
- Focused/challenge tests cover identity mismatch, hidden member/site, source mismatch, baseline attempt substitution, worker non-isolation, hidden conflict, adjudicator collision, date fabrication, unknown domain/severity and packet tampering.
- Existing S0/S1 and R4 frozen SHA gates remain unchanged; normal/optimized R5 tests, Ruff F, compile and 8911 stopped checks pass.

## Work Items

1. W1: 实现冻结 S2 authority packet typed contracts、canonical identity 与 fail-closed validator
2. W2: 实现真实 R4 typed pipeline synthetic authority builder，绑定 center/deep-link/source/baseline/ensemble packet
3. W3: 实现项目风险到中心到Inspector到Workspace时间锚点到来源的离线 projection，并补 focused/challenge/adjacent/SHA tests

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.

## Lossless Pause Checkpoint — 2026-08-18 16:39 +0800

### Current stage and acceptance state

- R5 S2 precondition contract remains accepted. S2 runtime is **not accepted**.
- The first independent runtime review returned `REVISE_R5_S2`; it found four semantic blockers: caller-replaceable individual-member authority, incomplete `ModelEvidence` identity closure, source `locator_kind` drift, and W3 dependence on fixed synthetic dates rather than the packet/R4 analysis window.
- This pause occurs during the bounded repair of those four blockers. No follow-up independent acceptance review has been requested yet.
- Do not claim R5 S2, R5 UI, browser behavior, real-project behavior, real-model behavior, or production readiness.

### Completed before the independent revision verdict

- W1/W2/W3 implementation and root-package public API integration existed.
- Prior broad evidence (before the current repair edits): R5 normal/optimized `410 passed`; R4 `4396 passed`; precondition generator/verifier normal and optimized passed; 13 precondition tamper probes passed; Ruff F and compile passed; port 8911 was stopped.
- Those results are historical pre-repair evidence and must be rerun before acceptance.

### Repair edits already present on disk

- `src/mm_r5/s2_authority_builder.py`
  - external `individual_registry` input now fails closed;
  - descendants resolve only from immutable typed `FROZEN_INDIVIDUAL_MEMBERS` with exact descendant/site/source equality;
  - actual R4 analysis window is required to be a single closed window and must contain the supplemental visit/event dates;
  - `ModelEvidence` now derives the exact receipt evaluation identity, shared attempt input, exact source refs/pairs, worker-output identity/hash, adjudication state and canonical binding hash;
  - semantic first-item selections touched in this repair were replaced with exact-cardinality tuple unpacking.
- `src/mm_r5/s2_contracts.py`
  - source binding now checks `locator_kind` as well as locator/file/row/lineage;
  - temporal geometry is checked against the packet-bound baseline window;
  - model-output identity/hash and model-binding hash recipes were added;
  - `ModelEvidence` validation now closes evaluation/input/model/ensemble/source/output/adjudication/role/binding identities.
- `src/mm_r5/s2_thin_slice.py`
  - the projection window now comes from the packet baseline temporal window rather than fixed 2026 constants;
  - exact-source resolution checks `locator_kind` and exact singleton source revision pair.
- `tests/test_s2_contracts.py`
  - the coherent packet fixture was updated to the new canonical `ModelEvidence` recipes.

### Decisive check completed after the latest edits

- Focused W1/W2 contract/builder test command completed: `60 passed in 0.31s`.
- Port check at pause: `127.0.0.1:8911 connect_ex=61` (not listening).
- The workspace directory is not a Git repository; continuity therefore relies on the explicit paths, hashes and tests in this record rather than Git status.

### Current file hashes (pause identity only; not acceptance pins)

- `s2_contracts.py`: `49cdfab19f78cf9445628070b8d0009419edcc17be49882e36750d226d6e3635`
- `s2_authority_builder.py`: `43e964ed1df8cd993b85f7177f51ae441dbda093e3a923487d0b7eef1f2464f4`
- `s2_thin_slice.py`: `0721cef73792a9ccf7cfd4131798b3c4a11a6b6962aeb11ec42e0f0cf46fcbf9`
- `test_s2_contracts.py`: `78d253ba3398097eebb57ab47f61d7d17f4732708a9dbdd7cbd59b5ff7e4405f`
- `test_s2_authority_packet.py`: `9ffe9a976db19aafe908a4a92f577cb893e69b089bd1df5eeadc4bbcb938e9c8`
- `evidence/r4_s2_readonly_sha256.json`: `d886c1c2f6f05d29510eed244a6ed8913ec1c13e2281b1b250d6f5b304fbd08d`

### Deliberately unfinished at pause

- Add explicit challenge tests for: alternate-but-valid external individual registry; all newly bound `ModelEvidence` identities/hashes/state; source `locator_kind` mismatch; shifted/malformed R4 analysis window and packet baseline window.
- Finish remaining safe removal of semantic `[0]` selections only where exact cardinality is already part of the contract; do not perform unrelated refactoring.
- Export the new model hash helpers only if the public S2 surface requires them.
- Do **not** update `evidence/r4_s2_readonly_sha256.json` until implementation and new challenge tests are stable. It is intentionally stale relative to the current W1/W2/W3 source hashes and W3 SHA tests may therefore fail now.
- After stabilization: focused W1/W2/W3 plus challenge tests; update the R5 evidence SHA file; rerun R5 normal and optimized suites, Ruff F, compile, precondition generator/verifier normal and optimized, precondition tamper probes, full R4 adjacent regression, and the 8911-stopped check.
- Then send the stable SHA set and evidence to the **same** independent reviewer session `r5_s2_runtime_reviewer` for an `ACCEPT_R5_S2` / `REVISE_R5_S2` verdict. Do not edit reviewed files while that review is running.
- Only after independent acceptance: complete the runtime review/acceptance records and execution cleanup. S3 remains locked until then.

### Next safe action on resume

Re-read this checkpoint and the independent `REVISE_R5_S2` findings, confirm the hashes above or account for concurrent drift, keep 8911 stopped, add the four attack-test families, run the focused suite, and only then refresh the evidence SHA pin. Do not start browser/UI/S7 work and do not touch medical-writing or R1–R4 source files.

## Final Acceptance Update — 2026-08-18 22:54 +0800

- The pause checkpoint above is preserved as history. Its pending items are now
  closed for S2.
- All four independent-review blockers were repaired and covered by explicit
  attacks; the adjacent worker claimed-window drift was also closed.
- Final stable source SHA: `s2_contracts.py` `8f9cc2ad...a4ad20c`;
  `s2_authority_builder.py` `6c8a18bd...9793c7`;
  `s2_thin_slice.py` `0721cef7...46fcbf9`; root `__init__.py`
  `0a24c699...b4ebd`; evidence record `6cec5b39...21af`.
- Current gates: R5 normal/optimized `427 passed + 15 subtests`; R4
  `4396 passed + 11258 subtests`; precondition normal/optimized plus 13 tamper;
  Ruff F and compile passed; 8911 stopped.
- The same isolated runtime reviewer compared 10 SHAs before/after, replayed
  all four attack families and returned `ACCEPT_R5_S2`.
- Acceptance is limited to synthetic/offline renderer-neutral R5 S2. S3-S8,
  UI/browser, real project/model, clinical truth, product/production, safety
  specialty and medical-writing remain outside this acceptance.
- Next safe stage is S3 contract/planning; do not start 8911 before the later
  S7 browser slice.
