# Task Context: medical_monitoring_ai_native_r1_slice2_framework_spike_20260809

Created: 2026-08-09 13:25:15
Objective: 在隔离R1 POC内验证GraphPort/CheckpointPort对LangGraph与Microsoft Agent Framework的适配可行性、结构化work-event播报和进程重启恢复；不触碰产品/医学写作/真实项目/8911/5174，不把候选框架直接加入产品依赖
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `cms-smk` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`（文内 v1.1）。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`（文内 v1.1，R1 steps 1, 5, 7, 8, 10, 11）。
- accepted slice1: `poc/medical_monitoring_ai_native_r1/`, `reviews/codex_medical_monitoring_ai_native_r1_poc_20260809_review.md`, `metrics/medical_monitoring_ai_native_r1_poc_20260809_metrics.md`。
- LangGraph official install/repository/security: `https://docs.langchain.com/oss/python/langgraph/install`, `https://github.com/langchain-ai/langgraph`, `https://github.com/langchain-ai/langgraph/security/advisories`。
- Microsoft Agent Framework official package/workflow/checkpoint sources: `https://github.com/microsoft/agent-framework/blob/main/python/pyproject.toml`, `https://learn.microsoft.com/en-us/agent-framework/workflows/`, `https://learn.microsoft.com/nb-no/agent-framework/user-guide/workflows/checkpoints`。
- Temporal Python SDK official repository: `https://github.com/temporalio/sdk-python`。
- 2026-08-09 PyPI wheel metadata and license inspection: LangGraph `1.2.10`, `langgraph-checkpoint-sqlite` `3.1.1`, Agent Framework Core `1.13.0`, Temporal `1.31.0`; all require Python >=3.10 and carry MIT license files. Wheel SHA-256 values are recorded below.
- Current filesystem is final truth. Do not add product or medical-writing paths to the read set.

## Scope

- In scope implementation root only: `poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/`.
- In scope task records: this context plus guard-owned plan/prompt/run/log/review/metrics/archive files.
- In scope: a framework-neutral conformance contract over the accepted slice1 `GraphPort/CheckpointPort`; deterministic work-event stream with manifest-derived exact progress; subprocess restart/replay harness; one LangGraph local-SQLite adapter; one Microsoft Agent Framework local-file/checkpoint adapter; candidate comparison and Temporal disposition.
- External packages may be executed only from the exact disposable Python 3.12 environments listed below. They remain spike-only and must not enter product/shared `.venv`, lockfiles or imports.
- Out of scope: editing accepted slice1 core except manager-approved compatibility fixes proven necessary; product integration; UI/browser; model/provider calls; credentials; real projects or clinical content; 8911/5174; medical-writing source/runtime/data; starting Temporal or any product service.

## Success Criteria

- Both framework adapters consume the same synthetic three-node manifest/Graph IR and produce the same authoritative slice1 Store state; framework checkpoint/session/message types never enter domain schema, artifacts or audit payload authority.
- Exact progress is derived from frozen manifest nodes and exposes a structured append-only event stream with node/work-unit/status/current-detail/timestamp; replay never duplicates a completed event or side effect.
- A first subprocess stops after an injected boundary; a fresh subprocess resumes from persisted framework checkpoint plus slice1 Store and completes without resetting manifest progress, duplicating domain objects, or promoting partial state.
- LangGraph uses `1.2.10` + checkpoint `4.2.0` + checkpoint-sqlite `3.1.1`, strict msgpack mode, allowlisted/static metadata keys and a separate checkpoint DB. Security regression probes must remain non-exploitative and prove configured boundaries only.
- Agent Framework uses `agent-framework-core==1.13.0`, deterministic executors only, local checkpoint storage, no model/provider/Foundry dependency, and proves whether its checkpoint can resume in a fresh process.
- Temporal is not started. The decision record must state whether its service/worker/determinism cost is justified after the two local candidates; SDK import alone is not acceptance.
- All tests run in disposable environments; full accepted slice1 `103`-test suite remains green under shared Python 3.9.
- Codex independently inspects checkpoint files, Store rows, work-event ordering, restart results and dependency/license/security evidence before acceptance.

## Risk Boundaries

- Writable implementation path is only `poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/`; task records use existing workflow surfaces.
- Do not write to production, medical-writing, accepted slice1 core, shared `.venv`, package locks, user config, credentials or real-project paths.
- Do not start/listen on services or use network/provider APIs during tests. Package installation is already completed only in disposable `/tmp` environments.
- Treat framework checkpoints as untrusted persistence. No pickle; only JSON-compatible synthetic state; checkpoint DB/file is separate from authoritative slice1 Store.
- Any framework event claiming analysis/evidence/output/baseline authority, any duplicate side effect after restart, or any cross-project state reuse is a P0 failure.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Isolated Environment And Pin Record

- Python: `/Users/smkzw/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3` = 3.12.13; `uv` = 0.11.7; macOS 26.5.1 arm64.
- LangGraph venv: `/tmp/mm_r1_slice2_langgraph.7esOy8/venv`; `pip check` passed; import passed.
- Agent Framework venv: `/tmp/mm_r1_slice2_agentframework.r44ruW/venv`; `pip check` passed; import/version 1.13.0 passed.
- Download-only wheel audit root: `/tmp/mm_r1_slice2_packages.gAtv2y`.
- Wheel hashes: LangGraph `52c48bd42fa31a1de0e1c0f0ebfe342e11ca2957b8b3563f83dbd60d8e30f921`; checkpoint-sqlite `8505c54c94a658080525d7e6780fdd4e0c078ff2566b30d399c02cc9f9af1c63`; Agent Framework Core `ba354e70a2749a0d5e9a5d4b7c40773011717b453c3a39bfa2dccd2bceb0f131`; Temporal `abbfb486ba00053ccfa57c9c38b38f80f5dbfd08c67beb7a621515a57a9b9e9b`.
- LangGraph security minimums: `langgraph>=1.0.10`, `langgraph-checkpoint>=3.0.0`, `langgraph-checkpoint-sqlite>=3.0.1`; pinned versions exceed all three. `LANGGRAPH_STRICT_MSGPACK=true` is mandatory for the spike.
- These temp environments are execution evidence, not deliverables. After acceptance, preserve freeze/hash records and move the disposable directories to Trash.

## Implementation Decision D-R1-02

- Validate LangGraph and Microsoft Agent Framework in parallel behind the existing ports; keep slice1 SQLite Store as sole domain authority.
- Defer Temporal runtime execution because meaningful validation requires a server/worker and adds a second durable authority/control plane. Reopen only if both local candidates fail cross-process recovery or later requirements prove multi-machine durability necessary.
- Do not adopt a framework from import success or popularity. Acceptance requires the same conformance/restart suite and a compact cost/security/reversibility comparison.
- 2026-08-09 Slice 2 disposition: both candidates passed the same Store-normalized conformance and fresh-process recovery contract after bounded manager repair. LangGraph is the lead candidate for the next isolated audience-facing vertical-slice validation because its checkpoint identity path is stricter and it has no observed commit-before-checkpoint residual; Agent Framework remains a comparison candidate. This is not the final framework ADR. Per R1 step 13, final selection waits for the synthetic AE/MH audience-facing slice and adapter/failure matrix.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-09 13:25:15: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-09: Latest official sources, PyPI metadata, MIT license files and LangGraph advisories rechecked. Pinned versions exceed published patched versions for msgpack deserialization, checkpoint JSON RCE and SQLite metadata-key injection.
- 2026-08-09: Disposable Python 3.12 LangGraph and Agent Framework environments created under `/tmp`; both `pip check` and import probes passed. Shared Python 3.9 `.venv` and all product/medical-writing paths remain unchanged.
- 2026-08-09: worker_01 established the framework-neutral contract/work-event/restart substrate; workers 02/03 implemented real LangGraph and Agent Framework adapters; worker_04 independently exposed C-GRAPH-BIND for both adapters and C-AF-CTOR for Agent Framework, plus public reused/resume/finalization gaps.
- 2026-08-09: finite-code manager repaired the mandatory public-contract gaps only under the spike root. Historical findings remain recorded as `failed_before_manager_repair -> pass_after_manager_repair`; Agent Framework checkpoint-save-after-domain-commit remains an accepted residual for this deterministic spike only.
- 2026-08-09: Codex independently inspected the shared Graph-IR comparator, both public entry paths, LangGraph missing-checkpoint and finalization behavior, Agent Framework constructor ordering, strict JSON/no-pickle controls, challenge tests and dependency decision record.
- 2026-08-09: Codex independent suites passed: LangGraph selected `113/113` in `18.93s`; Agent Framework selected `113/113` in `21.09s`; accepted slice1 `103/103` in `0.78s`. No product service, real project, provider, medical-writing path or accepted slice1 source was changed.
- 2026-08-09: Slice 2 accepted for isolated R1 evidence. It is not production, clinical, UI, power-loss, lock-contention or multi-machine acceptance. Next safe action is the next isolated R1 slice, beginning with the representative synthetic fixture/audience-facing AE/MH vertical-slice contract; do not install either candidate into product dependencies yet.
- 2026-08-09: Post-acceptance cleanup was recoverable: the two candidate venv roots, wheel audit root and four import/test cache directories were moved to `/Users/smkzw/.Trash/medical_monitoring_r1_slice2_cleanup_20260809_1511/`. No source or evidence file was permanently removed.
- 2026-08-09: Guard review gate passed with zero warnings/errors. Prompt, run and log trees were archived under `archives/execution/medical_monitoring_ai_native_r1_slice2_framework_spike_20260809/`; `cleanup_manifest.json` and physical file enumeration confirm the material is retained.
