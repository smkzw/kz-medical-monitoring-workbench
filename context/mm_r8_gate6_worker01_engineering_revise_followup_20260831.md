# G6 Worker 01 Same-Session Engineering Revision — Actual App Runtime And Independent Observers

Continue the same admitted `worker_01` session. Do not start a new session, browser, model, external network call, or subprocess Agent. Do not start the actual listener in this implementation pass.

## Hard boundaries

- Work only inside the current workbench and only on the allowed files below.
- Do not access real projects, medical-writing source, credentials, external accounts, or paths outside this workbench.
- All file mutations exercised by tests must use pytest/system temporary roots; do not change user application data.
- This is synthetic/offline implementation only. Do not claim G6 acceptance.

## Read these files only

- `reviews/medical_monitoring_r8_gate6_synthetic_ego_audience_acceptance_contract_v0_1_20260831.md`
- `runs/execution/mm_r8_gate6_synthetic_ego_implementation_20260831/worker_01_manifest_followup.md`
- `runs/execution/mm_r8_gate6_synthetic_ego_implementation_20260831/worker_02_engineering_revise.md`
- current files under `deploy/medical_monitoring_local/`
- current focused G6 tests under `tests/`

## Independent review findings to close

1. P0: no independently executable filesystem/process/network/adapter observer and reconciliation evidence path.
2. P1: actual app opens `/`, not the synthetic route.
3. P1: runs are frontend-memory-only and disappear on refresh/restart.
4. P1: application notification records, precise navigation, and §15.4 user task disk state are not actual-app executable.

## Assigned repair

### A. Actual synthetic entry and persistent run identity

1. Freeze the actual window URL to a static-server-safe synthetic route, preferably `/?g6=synthetic`; the `.app` cold-start URL must mount the G6 page. Add no-listener entry URL→route identity tests.
2. Add the smallest stdlib actual-app API/runtime store under the already-authorized runtime root. Persist state atomically and key every run by the exact canonical `project_ref + admission_id + run_ref + analysis_mode + binding_digest` selected from the bundle `run_bindings` matrix.
3. Implement deterministic synthetic endpoints/seams for prepare/start/read/restore. Refresh, page return, and app restart must recover the same run without creating or continuing another binding. Reject old/stale/mixed-binding callbacks fail closed.
4. Persist application notification facts for all nine terminal states and four capability states. Each record must keep the same fact/revision/binding and precise navigation target; replay is idempotent. Actual macOS `presented` remains for the later visual packet, but the actual-app durable record/navigation path must be executable now.

### B. §15.4 actual-app task engine

5. Implement all 13 required synthetic application tasks as a deterministic state machine backed by actual files only inside a task-specific runtime sandbox. Each task begins from its canonical initial state and exposes preview/action/cancel/confirm/status seams needed by the frontend. Evidence is generated only after the requested user actions, never pre-passed.
6. The state machine must cover the contract-visible/disk outcomes: export/import identity+lineage, backup ownership, corrupt-import block, clean restore, pre-upgrade protection, migration success, boundary failure without half-switch, original-version use, actual rollback after restart, ordinary export credential canary zero scan, default uninstall data retention, cancel/confirm clear-data, and late callback rejection. Keep implementation synthetic and generic; no real disease/drug/listing format.

### C. Independent observation and reconciliation

7. Add a separate release module/CLI (not an app self-report method) that can observe an actual running synthetic app with OS/filesystem evidence: process tree, listening/network endpoints, open/referenced files and runtime tree changes, and adapter-call ledger. It must emit canonical observer ledgers, compare them to the frozen execution boundary and app write/call ledger, and fail closed when `ps`/`lsof`/filesystem observation is unavailable, unknown, incomplete, outside allowed roots, on a foreign process/port, or on a non-synthetic/fallback adapter.
8. Keep observation code independent of actual-app state mutation. Tests may use frozen synthetic OS command outputs and temporary trees; actual `presented`/live observer evidence is later.

### D. Manifests and tests

9. Update boundary schema/manifest, release sources, entry manifest and all hashes after the runtime/observer closure is complete. Consume worker_02's new fixture/profile/run/bundle/task-spec identities; never confuse profile and run bindings.
10. Add focused no-listener tests for persistence/restart, six run bindings, stale callback rejection, notification idempotency/navigation, all 13 disk tasks, independent observer positive and fail-closed cases, actual entry URL, and release closure.

## Allowed files

- current files under `deploy/medical_monitoring_local/`
- focused G6 actual-app/runtime/observer tests under `tests/`
- runner-managed worker report only

## Verification

Run focused Python tests and app self-check without binding any port. Report exact tests, API/state contracts for worker_03, observer evidence schema, all refreshed digests, and remaining browser/macOS notification gaps. Do not claim G6 acceptance.

## Output

Return one compact handoff to the runner-managed output file `runs/execution/mm_r8_gate6_synthetic_ego_implementation_20260831/worker_01_engineering_revise.md`. Do not write that report path directly through file tools.
