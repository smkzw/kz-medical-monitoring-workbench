# Framework Adapters Spike (R1)

Isolated synthetic R1 POC validating `GraphPort`/`CheckpointPort` adapters for
LangGraph and Microsoft Agent Framework behind the accepted slice1 contract.
**Spike-only.** Not product, not medical-writing, not a dependency adoption.

## Boundary

- Writable root: this directory only.
- Do NOT edit accepted slice1 (`poc/medical_monitoring_ai_native_r1/src/mm_r1/`,
  `poc/medical_monitoring_ai_native_r1/tests/`), product, medical-writing,
  shared `.venv`, lockfiles, or config.
- The two candidate frameworks are **never co-installed**. They live in separate
  disposable `/tmp` venvs. Cross-candidate tests invoke each exact interpreter
  as a subprocess and compare shared JSON-normalized results.
- No services, network, provider calls, credentials, or real/clinical data.

## Layout

```
src/mm_r1_spike/
  contract.py              # framework-neutral conformance + exact Graph-IR comparator
  work_events.py           # append-only work-event store (worker_01)
  restart_harness.py       # subprocess restart/replay harness (worker_01)
  langgraph_adapter.py     # LangGraph 1.2.10 + SQLite checkpointer (worker_02 + manager repair)
  agent_framework_adapter.py # Agent Framework Core 1.13.0 (worker_03 + manager repair)
scripts/restart_worker.py  # subprocess entrypoint (worker_01)
tests/
  conftest.py
  test_contract_work_events.py     # contract/event/restart + Graph-IR unit tests
  test_langgraph_adapter.py        # LangGraph focused + manager regressions
  test_agent_framework_adapter.py  # Agent Framework focused + manager regressions
  test_cross_framework_conformance.py  # cross-candidate + public-port challenge
  test_restart_failure_injection.py    # corrupt/missing/wrong-run fail-closed
docs/
  DEPENDENCY_DECISION.md
  SPIKE_EVIDENCE.md
dependency-pins.json
README.md
```

## Environments

| Env | Python | Purpose |
|---|---|---|
| `/tmp/mm_r1_slice2_langgraph.7esOy8/venv` | 3.12.13 | LangGraph adapter + selected suite |
| `/tmp/mm_r1_slice2_agentframework.r44ruW/venv` | 3.12.13 | Agent Framework adapter + selected suite |
| `.venv` | 3.9.6 | read-only validation of accepted slice1 (103 tests) |

## Running the tests

Candidate-specific focused tests import their framework at collection time, so
each venv runs only the suites that apply. Do **not** collect the unavailable
candidate in the wrong venv.

**LangGraph venv** (contract + langgraph + cross/failure):
```
PYTHONPATH=poc/medical_monitoring_ai_native_r1/src:poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/src \
LANGGRAPH_STRICT_MSGPACK=true \
  /tmp/mm_r1_slice2_langgraph.7esOy8/venv/bin/python -m pytest -q \
  poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/tests/test_contract_work_events.py \
  poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/tests/test_langgraph_adapter.py \
  poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/tests/test_cross_framework_conformance.py \
  poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/tests/test_restart_failure_injection.py
```
Expected after manager repair: **113 passed** (contract 42 + langgraph 42 + cross 20 + failure 9).

**Agent Framework venv** (contract + agent_framework + cross/failure):
```
PYTHONPATH=poc/medical_monitoring_ai_native_r1/src:poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/src \
  /tmp/mm_r1_slice2_agentframework.r44ruW/venv/bin/python -m pytest -q \
  poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/tests/test_contract_work_events.py \
  poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/tests/test_agent_framework_adapter.py \
  poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/tests/test_cross_framework_conformance.py \
  poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/tests/test_restart_failure_injection.py
```
Expected after manager repair: **113 passed** (contract 42 + agent_framework 42 + cross 20 + failure 9).

**Accepted slice1** (shared 3.9, manager/Codex only):
```
.venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests
```
Expected: **103 passed**.

## Findings summary (post manager repair 2026-08-09)

See `docs/SPIKE_EVIDENCE.md` for the full pass/fail matrix and historical
worker_04 findings. Current verified state:

| Challenge | State |
|---|---|
| C-GRAPH-BIND (both) | **pass** (`failed_before_manager_repair -> pass_after_manager_repair`) |
| C-AF-CTOR wrong_run_id / stale_fingerprint | **pass** (`failed_before_manager_repair -> pass_after_manager_repair`) |
| C-RUN-REUSE public GraphRun fresh=`False` | **pass** (both) |
| LG public `resume` missing checkpoint fail-closed | **pass** |
| C-LG-FINALIZE narrow `CompletionGateError` only | **pass** (+ unexpected-error propagation regression) |
| AF checkpoint-save-after-domain-commit | **accepted residual** (not no-mutation) |
| Temporal | **DEFERRED** (unstarted) |

Pre-manager focused counts (worker_04 baseline): worker_01 **39**, each
candidate focused **37**. Manager added Graph-IR unit tests and public-contract
regressions; current focused counts are contract **42**, langgraph **42**,
agent_framework **42**.
