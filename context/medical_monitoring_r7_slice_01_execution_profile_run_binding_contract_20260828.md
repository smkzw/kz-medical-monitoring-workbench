# R7 slice-01 ExecutionProfile persistence and Run binding contract

Date: 2026-08-28
Status: frozen implementation input

## Goal

Build the first isolated R7 product-integration seam: persist user-owned ExecutionProfile layers and freeze one effective R6 Agent Harness profile into one Monitoring Run entry. Prove deterministic reopen and fail-closed identity without modifying product services, frontend, medical-writing, real projects, or medical business objects.

## Authority

- System design: `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`, especially sections 6, 9 and 15.
- Implementation plan: `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`, R7 steps 1, 2 and 4.
- Accepted adapter: `poc/medical_monitoring_ai_native_r6/src/mm_r6/agent_harness.py` pinned by `context/medical_monitoring_r6_runtime_slice_07_agent_harness_acceptance_record_20260828.md`.
- Existing R1 persistence/attempt model is design evidence only; this slice must not modify R1 bytes.

## In scope

1. A stdlib-only isolated package under `poc/medical_monitoring_ai_native_r7/`.
2. Append/version semantics for four profile layers: global default, capability/Agent, project, and Run override.
3. Public serialization that stores credential references only and never accepts a credential value field.
4. Deterministic effective-profile freeze by delegating to the accepted R6 profile registry/freeze contract.
5. Immutable Run binding containing project, mode, execution basis, cutoff/source revision identity, effective profile id/digest, adapter id/version, and binding digest.
6. Idempotent same-input bind; reject same Run identity with a different effective profile or data identity.
7. SQLite close/reopen parity and deterministic JSON/API-ready projections.
8. Exact default MTPLX medium behavior and explicit DeepSeek V4 Flash max behavior; no automatic fallback.
9. Synthetic/offline tests, optimizer/hash matrix, adjacent R6 regression and a durable receipt.

## Out of scope

- Product API routes, UI, background workers, services, ports, browser or Patient Journey.
- Real model calls; R6 slice-07 already proves the two adapter connectivity paths.
- Continue/resume/cancel, provider retries, fallback execution, long-task recovery or notifications.
- Real project data, medical conclusions, risk generation, Query dispatch or medical-quality acceptance.
- Medical-writing files, shared runtime databases and existing R1-R6 source modifications.
- System safety/security feature design or testing.

## Required invariants

- Profile/provider/model/selector/effort remain harness-layer fields and never enter ModeOutput, risk, Profile, Timeline, Query or report payloads.
- Layer precedence is global < capability/Agent < project < Run override; omitted fields inherit, invalid/empty required values fail closed.
- Profile records are immutable versions. A new revision creates a new row; prior versions remain readable.
- A Run binding is immutable. Exact idempotent replay returns the existing binding; any conflicting replay fails closed.
- Run binding must validate its R6 frozen profile identity/digest before persistence and after reopen.
- Only known monitoring modes (`daily`, `pre_lock`, `post_lock_pre_cfdi`) and execution bases (`full`, `incremental`) are accepted.
- `incremental` requires an explicit prior accepted snapshot reference; `full` forbids pretending a prior snapshot is its basis.
- Cutoff and source revision identifiers are non-empty and content-addressed by the binding digest.
- Fallback profile ids may be configured as metadata but are never executed or silently selected in this slice.
- Public projections use user-facing configuration names, while audit projections may include effective selector and exact digests. Neither projection contains credential values.

## Create-only ownership

- Worker 01: `poc/medical_monitoring_ai_native_r7/src/mm_r7/profile_store.py` and package initialization.
- Worker 02: `poc/medical_monitoring_ai_native_r7/src/mm_r7/run_binding.py`.
- Worker 03: `poc/medical_monitoring_ai_native_r7/tests/`, `README.md`, and `evidence/r7_execution_profile_run_binding_receipt.json`.
- All workers may read R1/R6 and this contract. They must not edit existing R1-R6 source, tests or receipts.

## Acceptance

- Focused tests prove default/explicit profile selection, all four precedence layers, revision history, reopen parity, idempotent bind, conflicting replay rejection, forged profile rejection, mode/basis rules, deterministic projections and no medical-object leakage.
- Normal/`-O`/`-OO` × `PYTHONHASHSEED=0/1/42` yields identical effective and binding digests.
- Full R6 POC remains green and its frozen source/test/receipt hashes remain unchanged.
- Medical-writing protected aggregate remains unchanged; 8911/5174 stay stopped.
- Governed execution audit and independent acceptance review pass before Codex acceptance.
