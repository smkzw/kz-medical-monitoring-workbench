# R1 Evidence：worker_04 failure-injection slice

## 1. 结论边界

本文件只记录隔离 `SYNTHETIC` R1 POC 的 worker_04 证据。它不宣称 UI、产品、
真实项目、provider、临床、监管或商业化就绪；`draft_exportable` 只表示 demo
内部的 synthetic Run 状态。

## 2. 直接观察（命令与文件）

以下是本轮实际观察到的结果：

| 检查 | 直接观察 |
|---|---|
| worker_01-03 基线 | `.venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests` → `85 passed`（编辑前） |
| worker_04 focused | `.venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests/test_failure_injection.py`；修正测试自身错误后为 `10 passed, 3 failed` |
| demo | `.venv/bin/python poc/medical_monitoring_ai_native_r1/scripts/run_demo.py --output-dir <caller-temp-dir>` → `SYNTHETIC_R1_DEMO_OK` |
| demo SQLite/JSON | caller 目录实际生成 `r1.sqlite3`、`artifacts/*.json`、acceptance/audit/progress/projections/recovery/run/report_ledger/summary JSON |
| demo progress/audit | `progress.json` 观察到 `completed=3,total=3,by_status.passed=3`；恢复后 audit verify 为 `true`，first bad seq 为 `null` |
| demo domain separation | `summary.json` 观察到 reported AE/MH 与 candidate 分开、`candidates_counted_as_reported=false`；报告 ledger `full_report_reviewed=true` |
| demo boundary | `summary.json` 观察到 `service_started=false`、`provider_called=false`、`real_project_data=false` |

demo 的 caller 临时输出目录不是本仓库交付物；`run_demo.py` 会拒绝覆盖已有
`r1.sqlite3` 或已知 JSON 输出。

## 3. 故障注入覆盖

新增文件：

- `tests/test_failure_injection.py`
- `scripts/run_demo.py`
- `README.md`
- `docs/ADR-001-framework-neutral-sqlite.md`
- `docs/R1_EVIDENCE.md`

直接测试观察如下：

| 场景 | 观察 | 状态 |
|---|---|---|
| artifact 写入后、DB 提交边界注入异常 | 无 authoritative artifact row；文件只作为 orphan 被 `recover()` 列出；Run 未发布 | PASS |
| artifact 篡改后走 `publish` | `verify_artifact` 为 `False`；`publish` 重新执行 `_gate_reasons` 并抛 `CompletionGateError`；output 保持 `dashboard_visible` | PASS (manager repair 2026-08-09) |
| artifact 篡改后走 `update_run_state(output=...)` | 同上，output advancement 路径统一复检 integrity/provenance/coverage/publishability | PASS (manager repair 2026-08-09) |
| 未接受 snapshot 使用 Store 派生 eligibility | `IMPORTED` → `False`，生命周期不产生 `resolved_by_data` | PASS |
| 未接受 snapshot 被 caller `True` 覆盖 | 裸 `True` 不再授权；仅 live `store`+`snapshot_id` 可授权 | PASS (manager repair 2026-08-09) |
| 伪造 `SnapshotBaselineProof`（含 `from_acceptance`）无 Store | 不产生 `resolved_by_data` / merge | PASS (manager correction_01) |
| 伪造 proof + Store `imported` | proof 不能覆盖 Store；仍 fail closed | PASS (manager correction_01) |
| 跨项目复用 eligible snapshot | snapshot project 与当前分析 project 不一致，不能授权关闭/merge/split | PASS (Codex final review) |
| 同项目但 snapshot version 不匹配 | Store snapshot 与当前分析版本不一致，不能授权风险关闭 | PASS (Codex final review) |
| `update_run_state(output=EXPORTED)` | 任意/合法 actor 均 `StoreError`，指引 `publish()`；状态不变 | PASS (manager correction_01) |
| `publish(..., actor=getpass.getuser())` | 原子写出 `output_state=EXPORTED` 与 `user_disposition=EXPORTED` | PASS |
| adapter persistence 重放 | artifact 可追溯但 facts 为空，四条 Run 正交状态不变，domain object version 不重复 | PASS |
| incomplete merge / non-accepted split | 不产生 merge/split transition，lineage 保持 not-evaluable 并可持久化审计 | PASS |
| invalid report ledger | ledger envelope 不可发布，`complete_analysis` 被阻断，Run 保持 running/not_published | PASS |
| manifest idempotent replay | manifest revision 保持 1，进度分母保持 `2/2`，artifact 和 node-complete 数量不增加 | PASS |
| duplicate / stale callback | 一个 attempt、一个 artifact；late callback 被拒绝并审计 | PASS |
| partial / truncated artifact | `complete_analysis` 被 coverage gate 阻断，未产生假完成 | PASS |
| audit payload tamper | recovery 返回 `audit_ok=false, first_bad_seq=1`，不追加 recovery event | PASS |

## 4. Manager remediation status

### 2026-08-09 initial manager pass

Worker_04 exposed three authority-boundary failures. Manager closed them without
weakening tests: output-advance re-gates via `_gate_reasons()`, and bare caller
`True` no longer authorized AE/MH resolution.

### 2026-08-09 manager_correction_01 (Codex independent findings)

Codex found two remaining authority gaps after the first manager report:

1. `SnapshotBaselineProof.from_acceptance()` could mint `store_verified=True`
   from any caller-built `SnapshotAcceptance`, and
   `resolve_baseline_eligibility()` previously accepted that proof without a
   Store lookup. **Repair:** public
   `run_ae_mh_vertical_slice` / `merge_risk_identities` / `split_risk_identity`
   authorize only via live `store.get_acceptance(snapshot_id)`. Bool and proof
   arguments are projection-only, never override Store, and fail closed without
   Store. Pure `reconcile_risk_lifecycle` keeps an internal verified bool.
2. `update_run_state(output=EXPORTED)` was a competing export path (actor only
   nonempty; no OS-user check; no atomic `user_disposition=EXPORTED`).
   **Repair:** that call fails closed with `StoreError` directing callers to
   `publish()`, which remains the sole EXPORTED route.

Post-correction manager suite: `101 passed`; Codex added cross-project and
snapshot-version binding cases and independently obtained `103 passed`. Demo temp-dir run remains
`SYNTHETIC_R1_DEMO_OK` with `draft_exportable`, verified audit chain, and
Store-projected acceptance evidence hashes (authority remains store+snapshot_id).

## 5. 不确定性与残余限制

- 失败注入使用临时 SQLite、monkeypatch 的提交异常和受控 SQL 审计篡改；没有模拟
  真实断电、进程被操作系统杀死、网络分区或多进程锁争用。
- demo 使用人工 synthetic rows；没有读取、复制或运行真实项目，也没有启动服务、
  浏览器或 provider。JSON/SQLite 文件存在不等于产品运行证据。
- 本轮没有安装或运行 LangGraph、Microsoft Agent Framework、Temporal；ADR 中的
  官方 URL/license 是从冻结本地材料转录，没有新的 web 验证。
- `SnapshotBaselineProof` 明确降级为 acceptance 投影；伪造 proof 不能再授权
  公共 AE/MH 入口。权威只来自当前 Store 行（`store` + `snapshot_id`）。
- live Store 行还必须绑定当前项目；纵向分析同时绑定当前 snapshot version，防止
  跨研究或旧版本的 eligible snapshot 被误用为本次风险关闭依据。
- 未进行 UI、Word/PDF、真实医学语义或商业发布验收。

## 6. 下一步

1. Codex 独立重跑完整测试目录与 `scripts/run_demo.py`。
2. 仅把本 slice 记为 isolated synthetic R1 POC 通过候选；不得宣称产品、真实项目、
   临床或商业就绪。
3. 接受后执行 `cleanup-execution` 归档 runs；不要删除证据。
