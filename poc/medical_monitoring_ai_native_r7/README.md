# R7 — ExecutionProfile persistence, Run binding, product API / run setup / background recovery

Isolated POC for R7 product-integration seams. Synthetic/offline only — no
8911/5174 listeners, no real model calls, no real projects, no frontend or
medical-writing edits. Slice-03 adds a minimal product `main.py` mount of the
project-scoped adapter; Slice-04 adds explicit preparation and read-only
SQLite-backed progress; Slice-05 adds synthetic/offline background execution
and interruption recovery. No slice invokes models or starts live listeners.

## Slices

| Slice | Status | Surface |
|---|---|---|
| Slice-01 | accepted (limited) | `profile_store` + `run_binding` |
| Slice-02 | accepted (limited) | `run_entry` + isolated FastAPI `api` |
| Slice-03 | accepted (limited) | product adapter + `main.py` mount |
| Slice-04 | worker evidence draft | synthetic runtime prepare + progress tests/receipt |
| Slice-05 | worker evidence draft | SQLite control lease + synthetic background recovery |
| Slice-06 | worker evidence draft | synthetic harness bridge, bounded attempt retry and recovery |
| Slice-07C-1 | worker evidence draft | synthetic three-mode run setup, keyed diff and versioned risk rules |
| Slice-07C-2 | accepted (synthetic limited) | atomic prepare/start registry, live public history, idempotency and recovery |

Authority:

- Slice-01 contract: `context/medical_monitoring_r7_slice_01_execution_profile_run_binding_contract_20260828.md`
- Slice-01 acceptance: `context/medical_monitoring_r7_slice_01_execution_profile_run_binding_acceptance_record_20260828.md`
- Slice-02 contract: `context/medical_monitoring_r7_slice_02_product_api_run_entry_contract_20260828.md`
- Slice-02 acceptance: `context/medical_monitoring_r7_slice_02_product_api_run_entry_acceptance_record_20260828.md`
- Slice-03 contract: `context/medical_monitoring_r7_slice_03_product_mount_contract_20260828.md` (SHA-256 `23a01f905fa1d19566873b0f04bd8a55f38f37e9ce28529a09a39a1f75f89b9b`)
- Slice-03 acceptance: `context/medical_monitoring_r7_slice_03_product_mount_acceptance_record_20260828.md`
- Slice-05 contract: `context/medical_monitoring_r7_slice_05_background_recovery_contract_20260828.md` (SHA-256 `590285e545a0d61ac9049b278e4b61cfaef8e1a22f56131a842ff7677978d65d`)
- Slice-06 contract: `context/medical_monitoring_r7_slice_06_harness_attempt_recovery_contract_20260828.md` (SHA-256 `3c879889e30541b2556bc8c2643758029b52e7cc9876f9b27d7e0e5b73bbbc21`)
- Slice-07C-1 contract: `reviews/medical_monitoring_r7_slice07c_three_mode_product_loop_contract_v0_2_20260829.md`
- Slice-07C-2 contract: `reviews/medical_monitoring_r7_slice07c2_prepare_start_contract_v0_1_20260829.md`
- Slice-06 stage record: `context/medical_monitoring_r7_slice_06_harness_runtime_implementation_stage_record_20260828.md`
- Design: `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §§6, 9, 15
- Plan: `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R7
- Accepted R6 adapter: `poc/medical_monitoring_ai_native_r6/src/mm_r6/agent_harness.py`

This README is verification/documentation evidence only. Codex remains the
final authority for acceptance. Slice-02/03 acceptance is **limited**: not
model-invoked, not three-mode end-to-end complete, and not R7 overall
complete. Slice-03 acceptance covers offline product-mount wiring only.
Slice-04 is a worker evidence draft: it covers synthetic/offline preparation,
R1-backed progress reconstruction, scope revision rules and fail-closed tests;
it does not claim background execution, real-project execution or Codex final
acceptance. Slice-05 is also a worker evidence draft: it covers only
synthetic/offline control, lease, dependency scheduling, stop/continue,
recovery and product-overlay tests; it does not claim real-model continuation,
real-project execution or Codex final acceptance. Slice-06 is a worker evidence
draft: it covers only injected catalog/transport faults, the R6-to-R1 bridge,
bounded synthetic attempts, run/attempt lease checks, retry identity, public
leakage and product regressions; it does not claim real-model smoke, real-project
execution or Codex final acceptance.
Slice-07C-1 is a worker evidence draft for the pure synthetic run-setup data
contract: three mode options, same-mode published baseline eligibility,
complete-listing keyed diff, project-scoped versioned risk rules, and
deterministic template-to-work-unit manifests. It does not claim
prepare-and-start, result publication, frontend behavior, real-project
execution, or Codex final acceptance.
Slice-07C-2 is accepted within the synthetic/offline launch boundary:
multi-candidate lock-before-CFDI baseline selection, three-mode launch records,
project-scoped idempotency, fail-closed option tokens, bounded runtime-backed
public history, and same-run recovery after reservation or start interruption.
It does not claim result publication, frontend behavior, real-project execution,
medical correctness, R7 overall, or R8 acceptance.


## Create-only path map

### Slice-01

| Path | Owner |
|---|---|
| `src/mm_r7/profile_store.py` | worker_01 |
| `src/mm_r7/__init__.py` | worker_01 |
| `src/mm_r7/run_binding.py` | worker_02 |
| `tests/test_profile_store.py` / `test_run_binding.py` / `test_determinism_adjacent.py` / `conftest.py` | worker_03 |
| `evidence/r7_execution_profile_run_binding_receipt.json` | worker_03 |

### Slice-02

| Path | Owner |
|---|---|
| `src/mm_r7/run_entry.py` (+ `__init__.py` export) | worker_01 |
| `src/mm_r7/api.py` | worker_02 |
| `tests/test_run_entry.py` / `tests/test_api.py` | worker_03 |
| `evidence/r7_product_api_run_entry_receipt.json` | worker_03 |
| `README.md` | worker_03 |

### Slice-03

| Path | Owner |
|---|---|
| `services/api/app/medical_monitoring_r7_product_router.py` | worker_01 |
| `tests/test_medical_monitoring_r7_product_router.py` | worker_02 |
| `services/api/app/main.py` (import + include only) | worker_03 |
| `evidence/r7_product_mount_receipt.json` | worker_03 |
| `README.md` (progress update) | worker_03 |

### Slice-04

Status: `codex_synthetic_offline_limited_acceptance` (2026-08-28). This accepts
durable synthetic preparation and read-only Chinese progress reconstruction
only. Background execution, recovery, real models/projects, frontend and visual
acceptance remain outside this slice.

| Path | Owner |
|---|---|
| `src/mm_r7/runtime_progress.py` | worker_01 |
| `services/api/app/medical_monitoring_r7_product_router.py` (prepare/progress mount) | worker_02 |
| `tests/test_runtime_progress.py` | worker_03 |
| `tests/test_medical_monitoring_r7_product_router.py` (prepare/progress additions) | worker_03 |
| `evidence/r7_durable_progress_receipt.json` | worker_03 |
| `README.md` (progress update) | worker_03 |

### Slice-05

Status: `synthetic_offline_worker_evidence_draft` (2026-08-28). This slice
adds one run-level SQLite control row, an expiring owner lease, dependency-aware
synthetic work-unit scheduling, stop/continue, interruption recovery and a
Chinese product overlay. R1's manifest and work-unit ledger remain the only
progress fact source.

| Path | Owner |
|---|---|
| `src/mm_r7/background_recovery.py` | worker_01 |
| `src/mm_r7/runtime_progress.py` (minimal action/overlay integration) | worker_01 |
| `services/api/app/medical_monitoring_r7_product_router.py` (action routes) | worker_02 |
| `tests/test_background_recovery.py` | worker_03 |
| `tests/test_medical_monitoring_r7_product_router.py` (action/overlay regressions) | worker_03 |
| `tests/test_determinism_adjacent.py` (allowlist/boundary update) | worker_03 |
| `evidence/r7_background_recovery_receipt.json` | worker_03 |
| `README.md` (progress update) | worker_03 |

### Slice-06

Status: `synthetic_offline_worker_evidence_draft` (2026-08-28). This slice
connects the frozen R6 profile/receipt surface to R1's capability controller
through an R7-only harness runtime. The test seam injects fake catalog and
transport outcomes; no provider discovery, process start or model call is
performed. `FakeCatalog` and `FakeHarnessAdapter` inject catalog validity or
exception, transport exception, blocking timeout, receipt-state, identity,
fallback and unsupported-operation outcomes without leaving the offline test
workspace.

| Path | Owner |
|---|---|
| `src/mm_r7/harness_runtime.py` | worker_01 |
| `src/mm_r7/background_recovery.py` (retry ownership guard) | worker_01 |
| `src/mm_r7/runtime_progress.py` (harness seam) | worker_01 |
| `services/api/app/medical_monitoring_r7_product_router.py` (injection seam) | worker_02 |
| `tests/fake_harness.py` | worker_03 |
| `tests/test_harness_runtime.py` | worker_03 |
| `tests/test_medical_monitoring_r7_product_router.py` (harness regressions) | worker_03 |
| `tests/test_determinism_adjacent.py` (allowlist/boundary update) | worker_03 |
| `evidence/r7_harness_attempt_recovery_receipt.json` | worker_03 |
| `README.md` (progress update) | worker_03 |
| `context/medical_monitoring_r7_slice_06_harness_runtime_implementation_stage_record_20260828.md` | worker_03 |

The bridge keeps separate R6 execution-profile and R1 profile identities,
requires one frozen preflight result before assignment/attempt/transport, maps
R6 complete/partial/truncated/timed_out/failed/not-evaluable receipts through
the existing R1 classifier, and strips paths/secrets from retained receipt
evidence. Each work unit allows at most one linked retry; retry input/profile
identity and `continued_from` are preserved without claiming a model session.
Run-level lease renewal covers a blocked current transport, while a cancelling
or stale owner cannot claim or append a new attempt. Product tests exercise the
injected fake through the project-scoped HTTP router and scan the public Chinese
projection for internal execution fields. The current worker evidence is 27
focused harness tests and 33 product-router tests, including simultaneous
claim serialization, cached preflight handoff, timeout/truncated linked retry,
attempt-lease rejection, both frozen profile identities, transport-failure
projection and cancellation wording.

### Slice-07C-1

Status: `ACCEPT_R7_SLICE_07C2_SYNTHETIC_LIMITED` (2026-08-29). This slice
adds only deterministic synthetic fixtures and tests for the frozen run-setup
contract. The complete current listing remains the source carrier for daily
incremental comparison; a canonical keyed diff marks added, revised,
unchanged, deleted, or cannot-compare rows. Baselines are selectable only
when published, same-project, same-mode, and not fixed-total. Versioned
project rules are opt-in, and later revisions do not rewrite historical
manifests.

| Path | Owner |
|---|---|
| `tests/fixtures_run_setup.py` | worker_03 |
| `tests/test_run_setup.py` | worker_03 |
| `evidence/r7_slice07c1_run_setup_receipt.json` | worker_03 |
| `README.md` (progress update) | worker_03 |

The focused suite covers all three modes, full-listing incremental semantics,
cross-hash-seed digest stability, mixed/unpublished/cross-project baseline
filtering, no-stable-key fail-closed behavior, ambiguous/confirmed/versioned
rules, historical manifest immutability, and template denominator parity.

### Slice-07C-2

Status: `synthetic_offline_worker_evidence_draft` (2026-08-29). This slice
adds the test and evidence boundary for atomic prepare-and-start dependencies.
The synthetic fixture exposes two selectable, same-project, published
lock-before-CFDI baselines; the latest is only a recommendation, while the
request must preserve an explicit selection. The launch registry tests cover
all three modes, canonical rule-token ordering, same-key replay and conflict,
project isolation, fail-closed expired option tokens, bounded public history,
and recovery to `waiting_start` after a start failure.

| Path | Owner |
|---|---|
| `src/mm_r7/launch_registry.py` | worker_01 |
| `services/api/app/medical_monitoring_r7_product_router.py` (prepare-and-start/history integration) | worker_02 |
| `tests/fixtures_run_setup.py` | worker_03 |
| `tests/test_run_setup.py` / `tests/test_launch_registry.py` | worker_03 |
| `tests/test_determinism_adjacent.py` (allowlist/boundary update) | worker_03 |
| `evidence/r7_slice07c2_prepare_start_receipt.json` | worker_03 |
| `README.md` (progress update) | worker_03 |

The launch registry remains synthetic/offline: it uses a project-scoped
SQLite file with a configured busy timeout and explicit close/reopen lifecycle.
The public history projection contains only public run token, Chinese mode,
data cutoff, comparison range, run state, result availability, and the main
action. A start failure keeps the reserved run and public token. A retry after
only reservation finishes the same run; a replay after manifest freeze never
starts a duplicate worker. History reconciles each frozen run with runtime
state, while one inconsistent record cannot break the whole project list.

Do not modify R1–R6 source/tests/receipts, frontend, medical-writing trees,
runtime databases, ports, or processes. Do not edit frozen Slice-01/02
receipts without an explicit Codex revision. Slice-03 must not register
`mm_r7.api.install_exception_handlers` on the product `app`, and must not
expose isolated `/api/medical-monitoring/r7`.

Codex integration note: `tests/test_determinism_adjacent.py::test_r7_create_only_allowlist`
enumerates the accepted create-only paths and includes
`evidence/r7_product_mount_receipt.json`,
`evidence/r7_background_recovery_receipt.json`,
`evidence/r7_harness_attempt_recovery_receipt.json`,
`evidence/r7_slice07c1_run_setup_receipt.json`, and
`evidence/r7_slice07c2_prepare_start_receipt.json`.

## Public API

### Slice-01 — `mm_r7.profile_store` / `mm_r7.run_binding`

- Four-layer precedence: `global_default < capability_agent < project < run_override`.
- `ProfileStore` constructor performs **no** business writes.
- `RunBindingStore.bind` is idempotent on same input; conflicts fail closed.
- Modes: `daily | pre_lock | post_lock_pre_cfdi`. Bases: `full | incremental`.

### Slice-02 — `mm_r7.run_entry` / `mm_r7.api`

Landed symbols (contract tests pin these names):

- `run_entry.API_PREFIX` = `/api/medical-monitoring/r7`
- `run_entry.RunEntryError` with stable `.code` + Chinese `.message`
- `run_entry.ProductRunEntry(workspace_dir)` — no constructor seed; the path is
  a directory containing the two SQLite stores, never a SQLite filename
  (`MonitoringRunEntry` / `RunEntry` are aliases)
- Methods: `bootstrap_workspace`, `append_execution_profile`,
  `get_execution_profile`, `resolve_scope_layers`,
  `freeze_effective_profile_for_scopes`, `bind_run` /
  `bind_monitoring_run`, `get_run` / `get_monitoring_run`,
  `reopen_and_validate_run`, `close`, `reopen`
- Public dict returns embed `replayed` on bootstrap/bind
- `api.create_router(entry)` / `api.create_isolated_app(entry)` /
  `api.create_isolated_app_from_run_entry(workspace_dir)`
- `api.create_router_from_run_entry(workspace_dir)` is low-level wiring only;
  a host app that mounts it must also call `install_exception_handlers(app)`
- Routes:
  - `POST /workspace/bootstrap`
  - `POST|GET /execution-profiles/{layer_kind}/{scope_key}`
  - `POST /runs` / `GET /runs/{run_id}`
- Errors: JSON `{code, message}` (Chinese message); no credential values or
  medical-object leakage in public responses.
- Builtin default: MTPLX
  `mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality` + `reasoning_effort=medium`.
  DeepSeek `deepseek/DeepSeek V4 flash` + `max` only via explicit layer — never
  auto-fallback.

### Slice-03 — product mount (`services/api/app`)

- Product prefix:
  `/api/projects/{project_id}/modules/medical-monitoring/r7`
- Factory: `create_medical_monitoring_r7_product_router(runtime_dir=...,
  project_resolver=..., principal_resolver=..., require_server_principal=True)`
- `main.py` wires `runtime_dir=RUNTIME_DIR`,
  `project_resolver=_canonical_module_project_id(..., "medical_monitoring")`,
  `principal_resolver=resolve_monitoring_principal_from_request` (not the R5
  synthetic fixture principal).
- Workspace path:
  `RUNTIME_DIR / "medical_monitoring_r7" / <canonical_project_id>`
- Per-request `MonitoringRunEntry` open/close; bootstrap alone seeds MTPLX
  medium; product DTO omits client `project_id` / scope override dual-write.
- Project aliases resolve to one canonical workspace/scope; unknown R7 paths
  and wrong methods retain the local Chinese `{code, message}` envelope.
- Focused offline host: `tests/test_medical_monitoring_r7_product_router.py`
  (Slice-03 baseline 15 passed; current file suite includes 8 Slice-04 tests;
  throwaway FastAPI + tmp runtime; does not import product `main.py`).

### Slice-04 — durable preparation and progress

- Product routes: `POST /runs/{run_id}/execution/prepare` and
  `GET /runs/{run_id}/progress` under the project-scoped R7 prefix.
- The R1 SQLite manifest/work-unit ledger remains the only progress fact source;
  the R7 adapter stores no second progress state.
- Daily and pre-lock scope changes append a revision; historical A→B→A reuse is
  rejected. Post-lock scope is frozen after first preparation.
- Product run creation rejects internal/hash-like `data_cutoff` values before
  binding so every accepted cutoff can be shown to a Chinese medical monitor.
- Acceptance evidence: 38 focused tests, R7 108, R1 327 and R6 763; protected
  ports remained stopped and the 542-file medical-writing boundary hash matched.

### Slice-04 — durable progress (synthetic/offline)

The product surface remains project-scoped:
`/api/projects/{project_id}/modules/medical-monitoring/r7`.

- `POST /runs/{run_id}/execution/prepare` requires an explicit non-empty
  `work_units` list. Each item is limited to the frozen audience fields
  `work_unit_id`, `stage`, `label`, `scope`, `target_ref`, `ordinal`,
  `mandatory`, and `depends_on`.
- `GET /runs/{run_id}/progress` reconstructs counts and Chinese audience
  status from the R1 SQLite ledger and `project_audience_progress`.
- The runtime layout is one store per canonical project and can contain
  multiple Runs: `medical_monitoring_r7/<canonical_project_id>/runtime/`.
- Prepare responses expose only `replayed`, scope version, total, cutoff,
  mode and basis text. Progress responses add the bounded Chinese projection;
  internal run/node/work-item identities, model/provider details, hashes,
  paths and database details are not public fields.
- Slice-04 preparation/read paths do not start workers, advance work
  automatically, call models, run real projects, or expose execution actions.

### Slice-05 — background recovery (synthetic/offline)

- `r7_execution_control` is the single run-level control record in the same
  SQLite database as the R1 manifest and work-unit ledger. It contains only
  revision, generation, state, owner lease, cancellation flag and timestamps;
  counts remain in R1.
- Stable work keys are
  `r7-background:{run_id}:{revision}:{work_unit_id}`. A worker claims work
  only after dependency statuses are `passed`, `reused`, `skipped` or
  `not_applicable`.
- Product actions are project-scoped `POST .../execution/start`,
  `POST .../execution/resume` and `POST .../execution/cancel`; public action
  responses expose only `replayed`, `run_status_text` and Chinese
  `available_actions`. Product reads add the same overlay to the R1 audience
  snapshot.
- An expired lease is marked `interrupted` and is never auto-resumed. An
  explicit continue claims a new generation and replays the same stable key;
  R1 absorbs same-key callbacks and rejects conflicting fingerprints.
- Failed dependencies leave downstream work pending, close the worker without
  a retry spin, and report that no work can continue. Stop lets the current
  synthetic unit finish and then prevents new claims.
- Tests inject blocked actions, store failure, lease expiry and two SQLite
  connections entirely in temporary workspaces. They do not start services,
  models, harnesses or real projects.
- A progress read may first persist an expired active lease as `interrupted`,
  then read a later consistent audience snapshot. It never starts/resumes a
  worker or changes R1 counts; the exact boundary is recorded in the Slice-05
  contract erratum.
- Limited acceptance evidence: focused runtime/determinism 47, product router
  28, full R7 125, adjacent R1 core 327, and R6 functional 758 with five
  obsolete cache-inclusive boundary assertions explicitly excluded. The
  medical-writing boundary is now a stable 443 non-cache-file aggregate.

### Slice-06 — harness attempts and bounded recovery (synthetic/offline)

- `HarnessCapabilityRuntime` is an R7-only thin wrapper over the frozen R6
  adapter and R1 `CapabilityRuntime`; it does not discover a provider or start
  a process. `FakeCatalog` and `FakeHarnessAdapter` inject catalog, transport,
  blocking, receipt, and transport-exception outcomes in temporary tests.
- The default frozen profile remains MTPLX with `medium`; an explicitly bound
  DeepSeek profile uses the effective selector
  `deepseek/deepseek-v4-flash` with `max`. The bridge retains distinct R6 and
  R1 identity digests and rejects fallback or mapping drift.
- Preflight runs before assignment and attempt declaration. A catalog failure
  records only a de-sensitive diagnosis, leaves the work unit pending, and
  produces no transport call. R6 receipts are mapped through the existing R1
  JSON-RPC classifier; only complete, parsed, identity-consistent, complete
  coverage can pass a work unit.
- A work unit receives at most two claimed/bound attempts. A partial,
  truncated, timeout or interrupted first attempt may create one linked retry;
  the retry preserves input/profile/version identity and `continued_from`, but
  does not claim a same-session model continuation. Failed or unsupported
  transport outcomes do not self-retry.
- A blocked fake transport renews the current R7 run lease. Cancelling permits
  only that current unit to finish; an owner/revision/lease drift rejects late
  terminal persistence and prevents a linked retry. Public product progress and
  action responses remain Chinese-only projections without execution identity,
  path, hash, receipt or secret material.
- Worker evidence: `test_harness_runtime.py` and two product-router tests cover
  the above behavior. Real-model smoke, real-project execution, service
  listeners, frontend/visual acceptance and Codex final acceptance remain
  unclaimed.
### Slice-07C-2 — atomic prepare-and-start dependencies

- `LaunchRegistry` is the append-only project-scoped reservation/history seam.
  `project_id + idempotency_key` is unique; the canonical request fingerprint
  covers mode, basis, current snapshot, optional baseline, and sorted unique
  confirmed rule tokens.
- Same key and same normalized content replays the existing public run. Same
  key and changed normalized content fails with `idempotency_conflict`; a
  different project may reuse the key without sharing the run.
- The reserved state is `waiting_start`. A start failure transitions an
  already-running synthetic record back to `waiting_start`; recovery replays
  the same public token. A successful replay never creates a second registry
  row or starts a second run.
- Public history is bounded and excludes internal run, source, digest,
  profile, provider, model, database, and rule-token fields. Slice-07C-2 keeps
  `result_available` false; publication belongs to Slice-07C-3.


## Offline verification

Focused R7 suite (includes Slice-01 + Slice-02 tests when peers landed):

```bash
cd poc/medical_monitoring_ai_native_r7
PYTHONHASHSEED=0 python3 -m pytest tests/ -q
```

Slice-02 nine-cell digests: `tests/test_run_entry.py::test_slice02_bootstrap_bind_digest_matrix`
(`PYTHONHASHSEED` ∈ {0,1,42} × normal/`-O`/`-OO`).

Adjacent R6 regression (read-only):

```bash
cd poc/medical_monitoring_ai_native_r6
PYTHONHASHSEED=0 python3 -m pytest tests/ -q
```

Protected ports `8911` / `5174` must remain stopped. Medical-writing aggregate
must remain `542` files /
`feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`.

Product-focused Slice-03 offline suite (workbench root):

```bash
PYTHONHASHSEED=0 python3 -m pytest tests/test_medical_monitoring_r7_product_router.py -q
```

Slice-04 focused offline suites:

```bash
PYTHONHASHSEED=0 python3 -m pytest poc/medical_monitoring_ai_native_r7/tests/test_runtime_progress.py -q
PYTHONHASHSEED=0 python3 -m pytest tests/test_medical_monitoring_r7_product_router.py -q
```

Slice-05 focused offline suite:

```bash
PYTHONHASHSEED=0 python3 -m pytest poc/medical_monitoring_ai_native_r7/tests/test_background_recovery.py -q
PYTHONHASHSEED=0 python3 -m pytest tests/test_medical_monitoring_r7_product_router.py -q
```

Slice-06 focused offline suites:

```bash
PYTHONHASHSEED=0 python3 -m pytest poc/medical_monitoring_ai_native_r7/tests/test_harness_runtime.py -q
PYTHONHASHSEED=0 python3 -m pytest tests/test_medical_monitoring_r7_product_router.py -q
```

Slice-07C-1 focused offline suite:

```bash
PYTHONHASHSEED=0 python3 -m pytest poc/medical_monitoring_ai_native_r7/tests/test_run_setup.py -q
```
Slice-07C-2 focused offline suites:

```bash
PYTHONHASHSEED=0 python3 -m pytest poc/medical_monitoring_ai_native_r7/tests/test_run_setup.py -q
PYTHONHASHSEED=0 python3 -m pytest poc/medical_monitoring_ai_native_r7/tests/test_launch_registry.py -q
```


The focused tests cover the frozen Slice-04 matrix: zero runtime I/O before
binding/preparation and after read-only progress, strict work-unit and
audience validation, first prepare/replay, daily and pre-lock revision
evolution, post-lock freezing, R1 status-to-Chinese projection, alias and
project isolation, identity mismatch without `set_manifest`, stale callbacks,
and ledger/audit tamper fail-closed behavior. Slice-05 adds no-thread prepare
and GET, no-polling completion, dual-connection claim serialization, injected
action/lease recovery, old-generation CAS, dependency blocking, stop/continue,
scope-change rejection, stale revision callbacks, control/audit tamper blocking,
product action permission and public leakage regressions. Slice-06 adds fake
catalog/transport failure injection, frozen preflight reuse, R6-to-R1 status
mapping, dispatch ordering, simultaneous claim serialization, blocked lease
renewal, cancelling behavior, bounded timeout/truncated linked retry,
run/attempt identity drift rejection, receipt sanitization, exact default and
explicit profile preservation, product harness execution and
preflight/transport-failure projections. Slice-07C-1 adds deterministic
synthetic coverage for the three mode option projections, same-mode published
baseline filtering, complete-listing added/revised/unchanged/deleted diff
carriers, missing-key disablement, cross-hash-seed output stability, project
rule ambiguity and revisions, and template denominator/source parity.
Slice-07C-2 adds deterministic synthetic coverage for explicit multi-candidate
lock-before-CFDI selection, three-mode registry reservations, normalized
idempotent replay, same-key conflict, project isolation, expired snapshot and
baseline option tokens, bounded public history, close/reopen persistence,
waiting-start start-failure recovery, reservation-only retry healing, admin
restart through completed public history, product-level cross-project token
rejection, medical-monitor launch authorization, no duplicate successful replay,
and a nine-cell hash-seed/optimizer request-fingerprint matrix. Slice-07C-2's
receipt records Codex synthetic-limited acceptance; other receipts retain their
own stated authority.

Receipts:

- Slice-01: `evidence/r7_execution_profile_run_binding_receipt.json`
- Slice-02: `evidence/r7_product_api_run_entry_receipt.json`
- Slice-03: `evidence/r7_product_mount_receipt.json`
- Slice-04: `evidence/r7_durable_progress_receipt.json`
- Slice-05: `evidence/r7_background_recovery_receipt.json`
- Slice-06: `evidence/r7_harness_attempt_recovery_receipt.json`
- Slice-07C-1: `evidence/r7_slice07c1_run_setup_receipt.json`
- Slice-07C-2: `evidence/r7_slice07c2_prepare_start_receipt.json`

## Out of scope

UI, real model calls, provider retries, exactly-once delivery, long-task
real-project recovery, real project data, medical conclusions, Query dispatch,
medical-writing changes, and R1–R6 source edits. Slice-05's stop/continue and
Slice-06's harness attempts are synthetic/offline only; real-model smoke and
production execution remain outside this worker evidence. Slice-02/03 exclude
credential-value editing endpoints and Run *execution* endpoints. Slice-03
additionally excludes app-wide exception-handler installation and isolated
`/api/medical-monitoring/r7` product exposure.
