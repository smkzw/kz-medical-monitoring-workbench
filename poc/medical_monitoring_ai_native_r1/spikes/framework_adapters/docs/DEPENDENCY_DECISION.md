# Dependency / License / Security / Temporal Disposition

Spike: `medical_monitoring_ai_native_r1_slice2_framework_spike`
Recorded: 2026-08-09. Authoritative pins/hashes: `dependency-pins.json`.

## 1. Boundary

This record concerns only the isolated synthetic R1 POC spike at
`poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/`. It is evidence
for Codex, not acceptance authority. It does not claim product, clinical,
regulatory, or commercial readiness. No adoption decision is made beyond
evidence-grounded `recommended_for_next_isolated_validation` or `deferred`.

## 2. Pinned dependencies (frozen in parent context)

| Package | Version | SHA-256 (wheel) | License | Python |
|---|---|---|---|---|
| langgraph | 1.2.10 | `52c48bd4…0f921` | MIT | >=3.10 |
| langgraph-checkpoint | 4.2.0 | transitive (in-venv probe) | MIT | >=3.10 |
| langgraph-checkpoint-sqlite | 3.1.1 | `8505c54c…f1c63` | MIT | >=3.10 |
| agent-framework-core | 1.13.0 | `ba354e70…0f131` | MIT | >=3.10 |
| temporalio | 1.31.0 | `abbfb486…b9e9b` | MIT | >=3.10 |

Wheel hashes verified against `/tmp/mm_r1_slice2_packages.gAtv2y/*.whl` by
`sha256sum`. License evidence: each wheel's `*.dist-info/METADATA` declares MIT
(`License-Expression: MIT` for LangGraph wheels; `Classifier: License :: OSI
Approved :: MIT License` for agent-framework-core; LICENSE file present for all).
MIT license text confirmed in each wheel's `licenses/LICENSE`.

The two candidate frameworks are **never co-installed**. They live in separate
disposable `/tmp` venvs (Python 3.12.13). Cross-candidate tests invoke each
exact interpreter as a subprocess and compare shared JSON-normalized results.
The shared `.venv` (Python 3.9.6) is read-only validation for accepted slice1
and never imports a candidate framework.

## 3. LangGraph security minimums (four controls)

Per parent context, four minimums are mandatory and all are satisfied by the
pinned versions:

1. `langgraph>=1.0.10` — pinned `1.2.10`. ✓
2. `langgraph-checkpoint>=3.0.0` — pinned `4.2.0`. ✓
3. `langgraph-checkpoint-sqlite>=3.0.1` — pinned `3.1.1`. ✓
4. `LANGGRAPH_STRICT_MSGPACK=true` is mandatory and asserted at import:
   `langgraph.checkpoint.serde._msgpack.STRICT_MSGPACK_ENABLED` is `True`, and
   the adapter raises at module load if the flag is not set before first import.

Advisories covered: msgpack deserialization, checkpoint JSON RCE, SQLite
metadata-key injection. Pinned versions exceed all published patched versions.

**Strict msgpack + static metadata controls (verified):**
- `LANGGRAPH_STRICT_MSGPACK=true` set before any langgraph import; flag asserted.
- Static allowlist of checkpoint metadata keys: `source`, `step`, `parents`,
  `run_id`, `counters_since_delta_snapshot`. `verify_checkpoint_identity`
  rejects any non-allowlisted key.
- `run_id` binding is **required present** and must equal `contract.run_id`;
  missing run_id is failure (not accepted).
- Checkpoint state blob must be present and non-empty; corruption fails closed.
- Corruption of state blob or metadata causes resume to raise before any Store
  mutation (verified in `test_restart_failure_injection.py`).

## 4. Agent Framework Core controls

- `agent-framework-core==1.13.0`, import name `agent_framework`, deterministic
  executors only; no model/provider/Foundry/client instantiation.
- Spike-owned `StrictJsonCheckpointStorage`: rejects unsupported values,
  non-string keys, NaN/Infinity, and recursive/cyclic structures before any
  file write. The adapter source adds **zero** pickle references.
- **Residual note (worker_03):** the framework's own `FileCheckpointStorage`
  serializes the internal `WorkflowMessage` envelope with a pickle-in-base64
  payload embedded in the otherwise-JSON checkpoint file. The spike avoids this
  by using its own `StrictJsonCheckpointStorage`; the authoritative slice1 Store
  holds no pickle and no framework types. The worker_04 cross/failure tests
  confirm no framework state enters domain artifacts/audits.

## 5. Temporal disposition: DEFERRED (unstarted)

Temporal `temporalio==1.31.0` is recorded (hash/license verified) but **not
started**. Per parent context Decision D-R1-02 and the task's explicit
requirement, SDK import or wheel presence is **not acceptance**.

**Why deferred:** meaningful Temporal validation requires a running Temporal
**server**, a registered **worker** process, and a **control plane** (namespace,
task queue, retry/determinism policy). Starting any of these adds a second
durable authority and a separate control plane beyond the accepted slice1 SQLite
Store — which the spike's single-domain-authority invariant forbids. Without a
server/worker/control plane, a Temporal adapter can only demonstrate SDK import,
which proves nothing about cross-process restart recovery, determinism, or
idempotency under the conformance contract.

**Future reopen condition (not a decision):** reopen isolated Temporal
validation only if (a) both local candidates fail cross-process recovery under
the shared conformance suite, AND (b) later requirements prove multi-machine
durability necessary. Reopening requires a disposable Temporal server/worker and
must preserve the slice1 Store as sole domain authority.

## 6. Operating cost / reversibility / privacy boundary

- **Operating cost:** both candidates are local-only; no service, network, or
  provider calls during tests. The disposable venvs are evidence, not
  deliverables.
- **Reversibility:** the disposable `/tmp` venvs move to Trash after acceptance.
  No changes to product, medical-writing, accepted slice1, shared `.venv`,
  lockfiles, or user config. Writable root is the spike directory only.
- **Privacy / data egress:** no network, no credentials, no real/clinical data.
  All runtime products land in pytest `tmp_path` dirs. Framework checkpoint
  DB/files are separate from the authoritative Store.

## 7. Recommendation (evidence-grounded, not adoption)

This record makes **no adoption decision**. On the evidence gathered after the
2026-08-09 manager repair:

- Both candidates satisfy the STORE-NORMALIZED conformance contract: identical
  authoritative Store shape, work-event ordering, idempotency, counts, and
  fresh-process recovery with distinct PIDs.
- Historical worker_04 FAIL findings **C-GRAPH-BIND** (both) and **C-AF-CTOR**
  (AF wrong_run_id / stale_fingerprint) were repaired under the spike root:
  shared exact Graph-IR comparator on both public `run` paths; AF constructor
  identity gate before checkpoint dirs/storage. Disposition:
  `failed_before_manager_repair -> pass_after_manager_repair` (see
  `SPIKE_EVIDENCE.md` §4–§5). Do not erase the historical finding.
- Public GraphRun reuse, LG public-resume missing-checkpoint fail-closed, and
  narrow `CompletionGateError` finalization were also repaired and verified.
- LangGraph provides the strongest checkpoint identity fail-closed story
  (strict msgpack + static allowlist + run_id binding + state-blob corruption
  checks, all verified).
- Agent Framework provides deterministic executors and a clean strict-JSON
  checkpoint codec, with a recorded **accepted residual risk**
  (commit-before-checkpoint ordering). This is **not** documented as
  no-mutation; Store idempotency contains duplicate side effects under the
  controlled deterministic scope only.

Evidence-grounded labels for Codex (not acceptance; Codex owns D-R1-02):
- `recommended_for_next_isolated_validation`: both candidates are conformance-
  equivalent on the store-normalized contract after manager repair; residual
  risk is AF checkpoint-save-after-commit under controlled scope.
- `deferred`: Temporal (server/worker/control-plane cost not justified after two
  local candidates passed store-normalized conformance + cross-process recovery).

Verified suite counts (manager): LG selected **113 passed**; AF selected
**113 passed**; accepted slice1 **103 passed**. Pre-manager focused baselines:
worker_01 **39**, each candidate focused **37**.
