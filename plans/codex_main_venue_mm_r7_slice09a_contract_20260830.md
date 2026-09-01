# Codex Main-Venue Plan: mm_r7_slice09a_contract_20260830

Date: 2026-08-30
Objective: 独立挑战并冻结 R7 Slice-09A 项目备份、恢复、导出与导入合同；核查最小范围、包闭包、一致快照、原子恢复、故障矩阵、中文用户语义与相邻回归，不实施产品代码。

## Task Decomposition

1. Independently inspect the draft contract against current R7/R1 storage and Slice-09 boundaries.
2. Challenge package membership, deterministic ZIP design, live SQLite/artifact consistency, restore state machine and rollback.
3. Challenge user-visible Chinese semantics, active-run and old-package decisions, replay/conflict and failure coverage.
4. Return exact required corrections and severity; no implementation.
5. Codex validates findings against source, applies bounded same-session corrections, then freezes only after independent acceptance.

## Source Packet

- `reviews/medical_monitoring_r7_slice09a_project_backup_restore_contract_v0_1_20260830.md`
- `context/medical_monitoring_r7_slice08_overall_review_and_slice09_plan_20260830.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `services/api/app/medical_monitoring_r7_product_router.py`
- R7 `run_entry.py`, `runtime_progress.py`, `launch_registry.py`, `run_setup.py`
- R1 `store.py`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `cms-router` | `minimax-m3` | `runs/conference/mm_r7_slice09a_contract_20260830/general_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Use the runner-owned 120-minute hard wait; no fixed-interval controller polling.
- Preserve the session for any required correction round; do not replace a resumable session.
- Record actual provider/model, duration, fallback status and whether follow-up was incorporated.

## Codex Verification Checklist

- [ ] Every claimed current member/path/schema is confirmed in source.
- [ ] Contract does not imply copying a live WAL main file.
- [ ] Restore never yields a mixed workspace and preserves rollback evidence.
- [ ] Manifest is not treated as its own independent oracle.
- [ ] Public DTO contains no path/table/hash/internal execution identity.
- [ ] Active-run, old-package and same-value replay decisions are explicit.
- [ ] Failure hooks and adjacent regression are executable and finite.
- [ ] No product source, service, model, real project or medical-writing mutation occurred.
