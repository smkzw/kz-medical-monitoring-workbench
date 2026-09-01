# Codex Execution Plan: medical_monitoring_r4_d05_postverify_corrective_20260812

Objective: 修复并验证R4-D05独立验收发现的三个合同缺口

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 修复Journey活动标记planned_visit_key稳定关联并添加版本修订反例 | `runs/execution/medical_monitoring_r4_d05_postverify_corrective_20260812/worker_01.md` |
| `worker_02` | 强化116行直接场景声明式期望验证并加入空check_fn负控 | `runs/execution/medical_monitoring_r4_d05_postverify_corrective_20260812/worker_02.md` |
| `worker_03` | 使Journey根payload_hash覆盖activity/pending/out-of-cutoff标记并验证篡改敏感性 | `runs/execution/medical_monitoring_r4_d05_postverify_corrective_20260812/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_r4_d05_postverify_corrective_20260812/manager.md` |

## Codex Acceptance

ACCEPTED after Codex D05/R4/R2/R3 verification, execution-manager review and
same-session Luna final acceptance. See the authoritative D05 implementation
acceptance record; no rendered surface exists in this R4 slice.
