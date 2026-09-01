# Codex Execution Plan: medical_monitoring_ai_native_r1_slice2_framework_spike_20260809

Objective: 在隔离R1 POC中以同一conformance contract验证LangGraph与Microsoft Agent Framework适配、结构化work-event和跨进程restart恢复；保持slice1 SQLite/domain唯一权威并保护医学写作/产品/真实项目

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 定义框架中立conformance contract、结构化work-event store与subprocess restart/replay harness | `runs/execution/medical_monitoring_ai_native_r1_slice2_framework_spike_20260809/worker_01.md` |
| `worker_02` | 实现并测试LangGraph 1.2.10 + SQLite checkpointer适配，使用严格序列化与独立checkpoint DB | `runs/execution/medical_monitoring_ai_native_r1_slice2_framework_spike_20260809/worker_02.md` |
| `worker_03` | 实现并测试Microsoft Agent Framework Core 1.13.0 deterministic workflow + local checkpoint适配 | `runs/execution/medical_monitoring_ai_native_r1_slice2_framework_spike_20260809/worker_03.md` |
| `worker_04` | 完成依赖/许可证/安全/Temporal处置记录与跨候选一致性/失败注入测试 | `runs/execution/medical_monitoring_ai_native_r1_slice2_framework_spike_20260809/worker_04.md` |

## Sequence And Ownership

1. Worker 01 establishes the immutable conformance/restart/event substrate and passes `tests/test_contract_work_events.py`.
2. Workers 02 and 03 then implement the two adapters in disjoint files and each pass its focused test file.
3. Worker 04 runs only after both adapter reports exist; it adds cross-framework normalization, failure injection, dependency/security/Temporal disposition, and spike evidence.
4. The manager reviews all worker reports and the live files, runs the complete spike suite plus the accepted slice1 suite, and applies only evidence-backed bounded repairs under the spike root.

Exact file ownership, environments, shared contract fields, failure boundaries, and stop conditions are authoritative in `context/medical_monitoring_ai_native_r1_slice2_framework_spike_20260809_execution_context.md`.

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `finite_code_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_ai_native_r1_slice2_framework_spike_20260809/manager.md` |

## Codex Acceptance

Codex independently verifies: source diff boundaries; package pins/hashes/license/security record; framework primitive use; physical checkpoint/work-event persistence; subprocess PID/restart evidence; Store/node/artifact/audit counts; replay idempotency; cross-candidate normalized output; all spike tests in both disposable environments as applicable; and the unchanged 103-test accepted slice1 suite under shared Python 3.9. Only Codex may accept D-R1-02 or select/defer a framework.
