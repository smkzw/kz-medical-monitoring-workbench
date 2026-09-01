# Codex Execution Plan: monitoring_p10_rule_release_chain_20260730

Objective: 完成医学监查 P0 规则发布最小完整产品链并通过聚焦与相邻回归

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 审计并补齐后端状态机、不可变来源身份、失败关闭、幂等和项目隔离 | `runs/execution/monitoring_p10_rule_release_chain_20260730/worker_01.md` |
| `worker_02` | 实现桌面优先低噪音前端规则确认、自动影子验证、影子确认、显式发布和 readiness 交互 | `runs/execution/monitoring_p10_rule_release_chain_20260730/worker_02.md` |
| `worker_03` | 补齐自动真实批次影子样本、身份漂移与旧 candidate 无二次批准测试，并执行构建回归和记录 | `runs/execution/monitoring_p10_rule_release_chain_20260730/worker_03.md` |

Cross-gap ordering:

1. Worker 01 must first close provisional-shadow circular proof and
   record-applicability aggregate identity using a same-session targeted rerun.
2. Worker 02 starts only after Codex reproduces those tests as passing.
3. Worker 03 removes cross-batch `_existing_run` fallback, adds integration
   regressions for all three gaps, and records exact evidence.

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/execution/monitoring_p10_rule_release_chain_20260730/manager.md` |

## Codex Acceptance

Codex will:

1. Inspect exact file deltas and reconcile them with concurrent accepted slices.
2. Re-run focused and adjacent backend/frontend tests plus the production frontend build.
3. Start `8911` only after all isolated checks pass, then use formal read/start APIs
   against the existing three projects without direct database writes.
4. Inspect the real browser workflow at desktop resolution and verify the UI requests
   no engineering fields and distinguishes adopt, shadow confirm, and publish.
5. Confirm daily-run readiness is closed before publication or under identity drift,
   and ready only for the current published immutable chain.
6. Record residual scientific/runtime risk and update the active P10 loop ledger.
