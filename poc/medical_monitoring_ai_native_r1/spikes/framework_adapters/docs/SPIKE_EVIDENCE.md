# Spike Evidence: framework_adapters

Spike: `medical_monitoring_ai_native_r1_slice2_framework_spike` (worker_04 + manager repair)
Recorded: 2026-08-09. Evidence for Codex; not acceptance authority.

## 0. Boundary

Isolated synthetic R1 POC only. Writable root:
`poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/`. No edits to
accepted slice1 core/tests, product, medical-writing, shared `.venv`, lockfiles,
or config. Manager repairs stayed under the spike root. All claims below are
directly observed unless marked `[INFERENCE]`.

## 1. Candidate outcome matrix (pass / fail / not_validated)

| Probe (challenge id) | LangGraph | Agent Framework | Basis |
|---|---|---|---|
| STORE-NORMALIZED conformance equivalence | **pass** | **pass** | identical authoritative Store shape, progress, counts, events |
| exact progress (3/3, manifest-derived) | **pass** | **pass** | `_normalize_from_store` |
| work-event ordering + idempotency (6 events, unique keys) | **pass** | **pass** | physical SQLite inspection |
| Store node/artifact/audit counts (3 rows, 0 art, 0 facts, audit ok) | **pass** | **pass** | domain DB inspection |
| fresh-process recovery (distinct PIDs, no duplicate side effect) | **pass** | **pass** | subprocess boundary |
| absence of framework state in domain artifacts/audits | **pass** | **pass** | no `writes` table in domain DB; separate checkpoint file |
| C-RUN-REUSE public GraphRun reused=False on fresh exec | **pass** | **pass** | pre-invocation terminal snapshot (manager repair) |
| C-RESUME only pre-committed nodes reused | **pass** | **pass** | public GraphRun + private LG path |
| C-REPLAY every node reused | **pass** | **pass** | public replay asserts all reused |
| replay no duplicate events/side effects | **pass** | **pass** | before/after normalize |
| **C-GRAPH-BIND** altered-edge graph rejected before mutation | **pass** | **pass** | shared `assert_exact_graph_ir` (see §4) |
| **C-AF-CTOR** wrong constructor run_id rejected | n/a | **pass** | constructor identity gate (see §5) |
| **C-AF-CTOR** stale manifest fingerprint rejected | n/a | **pass** | constructor identity gate (see §5) |
| C-LG-FINALIZE narrow CompletionGateError catch | **pass** | n/a | static + unexpected-error propagation |
| corrupt checkpoint fail-closed (no domain mutation) | **pass** | **pass** | blob/file corruption |
| missing checkpoint public resume fail-closed | **pass** | **pass** | see §6 |
| wrong-run checkpoint not cross-selected | **pass** | **pass** | separate work dirs |
| LG checkpoint state-blob corruption fail-closed | **pass** | n/a | blob corruption |
| LG missing run_id metadata fail-closed | **pass** | n/a | metadata tamper |
| AF checkpoint-save-after-commit residual risk | n/a | **accepted residual** | see §7 |

## 2. Commands and exact counts

Both disposable venvs (Python 3.12.13). Per-environment selected suites only
(unavailable candidate not collected in the wrong venv).

**Pre-manager baseline (worker_04):** worker_01 contract **39**; each candidate
focused **37**; cross/failure **29** with **3 failed** (C-GRAPH-BIND ×1 +
C-AF-CTOR ×2) in each venv → `3 failed, 102 passed` per combined suite.
Accepted slice1: **103 passed**.

**Post-manager repair (2026-08-09):**

**LG venv** — contract(42) + langgraph(42) + cross(20) + failure(9) = **113**:
```
PYTHONPATH=...src:...spikes/.../src LANGGRAPH_STRICT_MSGPACK=true \
  /tmp/mm_r1_slice2_langgraph.7esOy8/venv/bin/python -m pytest -q \
  tests/test_contract_work_events.py tests/test_langgraph_adapter.py \
  tests/test_cross_framework_conformance.py tests/test_restart_failure_injection.py
→ 113 passed in 19.32s
```

**AF venv** — contract(42) + agent_framework(42) + cross(20) + failure(9) = **113**:
```
PYTHONPATH=...src:...spikes/.../src \
  /tmp/mm_r1_slice2_agentframework.r44ruW/venv/bin/python -m pytest -q \
  tests/test_contract_work_events.py tests/test_agent_framework_adapter.py \
  tests/test_cross_framework_conformance.py tests/test_restart_failure_injection.py
→ 113 passed in 21.42s
```

**Accepted slice1** (shared Python 3.9):
```
.venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests
→ 103 passed in 0.80s
```

## 3. C-RUN-REUSE public GraphRun

**Historical worker_04 finding:** both candidates' PUBLIC `GraphRun` marked
freshly-executed nodes `reused=True` (post-execution Store state).

**Manager repair:** both public materializers capture pre-invocation terminal
state. Fresh run → all `False`; resume → only earlier committed `True`; replay
→ all `True`. AF `conformance_result` mirrors the last public pre-terminal
snapshot.

**Disposition:** `failed_before_manager_repair -> pass_after_manager_repair`.

**New regressions:**
- `TestManagerRepairRegressions::test_public_run_marks_fresh_nodes_not_reused` (LG + AF)
- `TestManagerRepairRegressions::test_public_resume_marks_only_precommitted_reused` (LG)
- `TestPublicPortReuseSemanticsChallenge::test_run_public_reuse_flags_observed_and_labeled` now expects `{"lg":"match","af":"match"}`

## 4. C-GRAPH-BIND

**Historical worker_04 finding:** both adapters accepted same graph_id + node
set with edges reordered `B→A→C` and mutated the Store (**FAIL**).

**Manager repair:** shared `assert_exact_graph_ir` in `contract.py` compares
ordered node ids, every execution-relevant node field (`node_type`, `handler`,
`description`, `mandatory`, `max_attempts`, `artifact_required`), and
ordered/conditional edges. Both public `run` methods call it before any
checkpoint/event/Store mutation.

**Disposition:** `failed_before_manager_repair -> pass_after_manager_repair`.

**Tests (exact):**
- `TestGraphBindingChallenge::test_altered_edge_order_rejected_before_mutation`
- `TestExactGraphIRComparator::test_altered_edges_rejected` / `test_node_field_mismatch_rejected`
- `TestManagerRepairRegressions::test_altered_edge_graph_rejected_before_mutation` (LG + AF)

## 5. C-AF-CTOR

**Historical worker_04 finding:** AF constructor accepted `run_id !=
contract.run_id` and stale `manifest_fingerprint` (**FAIL** ×2).

**Manager repair:** constructor rejects mismatched `run_id` and any contract
that differs from the current frozen manifest fingerprint/revision/graph/node
order **before** creating checkpoint directories or storage. Public methods
revalidate the live frozen contract at entry and validate exact Graph IR before
workflow construction. Public replay asserts all nodes were reused.

**Disposition:** `failed_before_manager_repair -> pass_after_manager_repair`.

**Tests (exact):**
- `TestAgentFrameworkCtorIdentityChallenge::test_wrong_constructor_run_id_observed`
- `TestAgentFrameworkCtorIdentityChallenge::test_stale_manifest_fingerprint_observed`
- `TestManagerRepairRegressions::test_ctor_rejects_wrong_run_id_before_checkpoint_dir`
- `TestManagerRepairRegressions::test_ctor_rejects_stale_fingerprint_before_checkpoint_dir`
- `TestManagerRepairRegressions::test_public_replay_asserts_all_reused`

## 6. Missing checkpoint / public resume

**Historical worker_04 observation:** AF public `resume` raised (fail-closed);
LG private `_run_contract` re-ran from Store when the checkpoint was missing
(semantic difference, safe under idempotency but not fail-closed).

**Manager repair:** LangGraph public `resume(run_id)` requires a persisted
framework checkpoint and fails closed if missing (no silent Store restart).
Public `run` may still start or resume per its contract. Failure-injection
`_RESUME` probe now calls public `resume` for both candidates; both must raise
with no domain/event mutation.

**Disposition:** `failed_before_manager_repair -> pass_after_manager_repair`.

**Tests (exact):**
- `TestMissingCheckpointFailClosed::test_missing_checkpoint_resume_fails_closed`
- `TestManagerRepairRegressions::test_public_resume_missing_checkpoint_fails_closed_no_mutation` (LG)

## 7. AF checkpoint-save-after-commit residual risk (accepted)

**Recorded limitation:** the AF runner persists the superstep checkpoint after
the executor may already have committed a domain effect
(`complete_node_run` / work-event append before `send_message` / checkpoint
save).

**Determination:** under this controlled deterministic spike (no
model/provider, synthetic handlers, separate operational checkpoint dir), Store
idempotency contains re-execution after checkpoint loss (no duplicate events).
This remains an **ACCEPTED RESIDUAL RISK** for the spike. It is **not**
documented as no-mutation.

**Tests:** `TestAgentFrameworkCheckpointSaveResidualRisk::*` (static ordering +
behavioral residual; does not claim no domain mutation).

## 8. C-LG-FINALIZE

Finalization catches only `CompletionGateError` from the synthetic evidence
gate. Broad `except Exception` removed. Unexpected finalization errors
propagate.

**Tests (exact):**
- `TestLangGraphFinalizationNarrowCatch::test_finalize_catches_only_gate_exception`
- `TestLangGraphFinalizationNarrowCatch::test_only_finalize_block_has_gate_catch`
- `TestManagerRepairRegressions::test_unexpected_finalization_error_propagates`

## 9. Temporal disposition

DEFERRED (unstarted). See `DEPENDENCY_DECISION.md` §5. SDK import/wheel presence
is not acceptance; meaningful validation requires server/worker/control plane.

## 10. Physical evidence (manager inspection)

**LangGraph** (temp work dir after stop-after-A then resume):
- files: `authoritative.sqlite3`, `work_events.sqlite3`,
  `langgraph_checkpoints.sqlite3`, `operational_checkpoint.json`, `artifacts/`
- checkpoint DB tables `{checkpoints, writes}`; domain DB has no `writes`;
  domain `node_runs=3`, `artifacts=0`; resume reuse `{A:True,B:False,C:False}`

**Agent Framework** (max_iterations=1 then public resume):
- `af_checkpoints/<namespace>/*.json` with `schema_version=mm-r1-spike-json-v1`;
  no pickle markers in payload; resume completes 3/3 with 6 events, 0 artifacts;
  resume reuse `{A:True,B:False,C:False}`

## 11. Uncertainty and residual limits

- AF commit-before-checkpoint ordering remains an accepted residual under the
  controlled deterministic scope only; not production durability proof.
- Failure injection uses controlled SQLite/JSON corruption and file removal in
  pytest `tmp_path`; it does not simulate real power loss, OS kill, network
  partition, or multi-process lock contention.
- No UI, Word/PDF, real medical semantics, provider, or commercial acceptance.
- The disposable `/tmp` venvs are evidence, not deliverables.
- **Codex remains final acceptance authority for D-R1-02; this spike is not
  declared accepted by the manager.**
