# Execution Context: medical_monitoring_ai_native_r1_slice2_framework_spike_20260809

Created: 2026-08-09 13:31:03
Objective: 在隔离R1 POC中以同一conformance contract验证LangGraph与Microsoft Agent Framework适配、结构化work-event和跨进程restart恢复；保持slice1 SQLite/domain唯一权威并保护医学写作/产品/真实项目
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 4 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_k3_256k` -> `pi` / `cms-smk` / `cms-model`
- Execution manager: `finite_code_manager_cursor` -> `cursor` / `cursor-cli` / `auto`
- Execution-manager fallback: `Codex takes over finite-code execution management directly`

## Source Of Truth

- Parent contract and pinned evidence: `context/medical_monitoring_ai_native_r1_slice2_framework_spike_20260809_context.md`.
- System contract: `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` (document version v1.1).
- Implementation contract: `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` (document version v1.1, R1 only).
- Accepted immutable reference implementation: `poc/medical_monitoring_ai_native_r1/src/mm_r1/` and its tests. Workers may read and import it; they must not edit it.
- Accepted slice1 evidence: `poc/medical_monitoring_ai_native_r1/docs/R1_EVIDENCE.md`, `reviews/codex_medical_monitoring_ai_native_r1_poc_20260809_review.md`, and `metrics/medical_monitoring_ai_native_r1_poc_20260809_metrics.md`.
- Writable implementation root: `poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/` only.
- Official framework/license/security URLs and exact package versions/hashes are frozen in the parent task context. No additional package installation or dependency upgrade is authorized.
- Current filesystem is final truth. Do not read or write the medical-writing subsystem, product runtime, real-project paths, shared `.venv`, ports 8911/5174, credentials, or user configuration.

## Risk Boundaries

- No production or accepted-slice1 writes. All implementation changes are confined to the writable spike root above.
- Do not install packages, start services, listen on ports, call model/provider APIs, use real clinical data, or perform network access during implementation/tests.
- Use only `/tmp/mm_r1_slice2_langgraph.7esOy8/venv` for LangGraph and `/tmp/mm_r1_slice2_agentframework.r44ruW/venv` for Agent Framework. Shared Python 3.9 is read-only validation for accepted slice1.
- Framework checkpoints and work events are separate operational persistence. The accepted slice1 SQLite `Store`, manifest, node runs, artifacts, facts, snapshots, and audits remain the sole domain authority.
- No pickle or opaque executable state. Persist only JSON-compatible synthetic state. LangGraph requires `LANGGRAPH_STRICT_MSGPACK=true` and static allowlisted metadata keys.
- Missing framework capability is a candidate failure to record, not permission to fake conformance or build a framework-shaped wrapper.
- Worker and manager outputs are evidence for Codex, not acceptance authority.

## Work Items

1. 定义框架中立conformance contract、结构化work-event store与subprocess restart/replay harness
2. 实现并测试LangGraph 1.2.10 + SQLite checkpointer适配，使用严格序列化与独立checkpoint DB
3. 实现并测试Microsoft Agent Framework Core 1.13.0 deterministic workflow + local checkpoint适配
4. 完成依赖/许可证/安全/Temporal处置记录与跨候选一致性/失败注入测试

## File Ownership And Dependency Order

1. `worker_01` runs first and exclusively owns `src/mm_r1_spike/__init__.py`, `src/mm_r1_spike/contract.py`, `src/mm_r1_spike/work_events.py`, `src/mm_r1_spike/restart_harness.py`, `scripts/restart_worker.py`, `tests/conftest.py`, and `tests/test_contract_work_events.py` under the writable spike root.
2. After worker 01 passes its focused tests, `worker_02` and `worker_03` may run independently. Worker 02 exclusively owns `src/mm_r1_spike/langgraph_adapter.py` and `tests/test_langgraph_adapter.py`. Worker 03 exclusively owns `src/mm_r1_spike/agent_framework_adapter.py` and `tests/test_agent_framework_adapter.py`. They may read but must not edit worker 01 files or each other's files.
3. After both adapters terminate, `worker_04` exclusively owns `tests/test_cross_framework_conformance.py`, `tests/test_restart_failure_injection.py`, `docs/DEPENDENCY_DECISION.md`, `docs/SPIKE_EVIDENCE.md`, `dependency-pins.json`, and `README.md`. It may read all earlier outputs but must not rewrite them.
4. The manager runs last. It may apply the smallest bounded fix anywhere under the writable spike root only when the defect is evidenced and the fix preserves file ownership intent. It must not edit accepted slice1 or task records.

## Shared Contract And Required Evidence

- All candidates consume one deterministic three-node `Graph`/frozen `ExecutionManifest` using accepted `mm_r1.graph` and `mm_r1.store` types. The normalized result is framework-neutral and compares node status, reuse, manifest progress, artifact counts/hashes, work-event projection, and audit integrity.
- Work events are append-only operational evidence with at least: `event_id`, `run_id`, `manifest_revision`, `sequence`, `node_id`, `work_unit_id`, `phase`, `status`, `completed`, `total`, `current_detail`, `created_at`, and `idempotency_key`. Exact progress is derived from frozen manifest nodes. Retry/replay cannot duplicate an idempotency key or side effect.
- Restart evidence is a real subprocess boundary: process A completes one node and exits at an injected boundary; process B is freshly launched against persisted authoritative Store plus separate framework checkpoint/event persistence and finishes. Tests use only temporary directories.
- Framework checkpoint persistence must be demonstrably used. A plain call to the accepted `LocalGraphPort` with a decorative framework object does not pass.
- Focused tests must inspect physical checkpoint/event files, ordering, deduplication, fresh-process PID separation or invocation records, and authoritative Store row/artifact counts.
- The shared accepted slice1 test command remains green: `.venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests` (expected 103 tests). Workers do not run it unless assigned; manager and Codex do.

## Acceptance And Stop Conditions

- A worker stops after its owned files and focused tests are complete, or on a precise framework/API/environment blocker. It does not broaden scope or install alternatives.
- Candidate pass requires actual framework primitives plus subprocess recovery under the shared contract. Import success alone is insufficient.
- Any duplicate domain artifact, work-event idempotency collision with divergent payload, checkpoint content entering a domain artifact/audit authority field, accepted-slice1 modification, medical-writing/product read/write, service start, provider call, or real-project data use is an immediate failure.
- The manager cannot declare acceptance; it returns an evidence-grounded report and precise rerun request for any unresolved gap.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
