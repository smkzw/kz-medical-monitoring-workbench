# Execution Context: mm_r5_s7_product_integration_runtime_v0_1_20260826

Created: 2026-08-26 14:02:48
Objective: 按已接受的R5-S7合同与闭合allowlist实现产品最小接入：新增GET-only R5后端router/adapter与前端R5页面/adapter/route/CSS/fixtures，做最小App/main/read-action接线，完成聚焦和相邻离线回归及production build；本execution不启动8911/5174/浏览器，不运行真实项目/模型，不修改医学写作。
Task type: `long_horizon_code`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_opencode_flash` -> `codex-subagent` / `codex` / `gpt-5.6-luna`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `AGENTS.md`
- `reviews/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1_20260826.md` SHA-256 `767aa5ab127f383e504178dc71bd02684b931e1afc67a8e82aa8d6af57a5aba8`
- `artifacts/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1/browser_acceptance_matrix.json` SHA-256 `6a5f8db3146ab170d1c186bd3478a3c98955070883a5e81b18383800c721ab7e`
- `context/medical_monitoring_r5_s7_product_integration_browser_contract_v0_1_acceptance_record_20260826.md`
- Accepted S5/S6 runtime under `poc/medical_monitoring_ai_native_r5/**` is read-only authority input.
- Existing medical-monitoring product entry points may be read; only exact allowlist files below may be changed.
- Current filesystem is authoritative; this workspace is not Git.

## Risk Boundaries

- Worker 01 write allowlist only:
  - `services/api/app/medical_monitoring_r5_product_router.py`
  - `services/api/app/medical_monitoring_r5_product_adapter.py`
  - `services/api/app/main.py`
  - `services/api/app/monitoring_read_action_contract.py`
  - `tests/test_medical_monitoring_r5_product_adapter.py`
  - `tests/test_medical_monitoring_r5_product_router.py`
  - `tests/test_medical_monitoring_r5_product_allowlist.py`
- Worker 02 write allowlist only:
  - `frontend/src/App.jsx`
  - `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`
  - `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Adapter.mjs`
  - `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5RouteState.mjs`
  - `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5.css`
  - `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Fixtures.mjs`
  - `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Adapter.test.mjs`
  - `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5RouteState.test.mjs`
  - `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5ProductContract.test.mjs`
- Worker 03 is read-only and runs only after Codex has reviewed the merged product implementation.
- No path containing `medical-writing` or `medical_writing` may change. Protected inventory before/after: 542 files, aggregate `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`.
- Do not modify R1-R4, accepted R5 POC, runtime/SQLite, package locks, Vite config, legacy medical-monitoring feature files, safety/PV or real project files.
- Do not start 8911/5174, FastAPI, Vite, browser, Playwright, provider or model. No real project run. No security design/testing.
- Synthetic data may be exposed only behind an explicit isolated S7 fixture mode and must carry unmistakable synthetic project/run/snapshot identity; there is no fallback from a missing real authority packet to synthetic data.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 后端实现：仅写合同4.2/4.3精确allowlist，提供三条GET-only R5 API、synthetic隔离projection、完整identity/digest/read-only envelope、fail-closed参数与测试；最小修改main.py/read-action contract。
2. 前端实现：仅写合同4.1精确allowlist，新增中文R5项目/中心/风险/受试者医学旅程页面、八域+风险编码、独立route state与GET-only adapter，并对App.jsx做最小R5 closed-view接线；完成Node合同测试和build。
3. 独立验证：后端/前端合并后机械检查exact allowlist、医学写作inventory、8911/5174停止、GET-only/no-fallback、中文禁词、S5/S6 identity、聚焦/相邻测试与production build，输出ACCEPT或REVISE；不得改源码。

## Implementation Requirements

- Keep code short, stdlib/native React first, no new dependency.
- R5 closed views on `/monitoring`: `overview|site_overview|journey|profile|timeline|evidence`; legacy `checklist|ae-mh` remains untouched. Invalid/absent R5 identity fails closed.
- In `App.jsx`, identify the R5 branch before legacy hydration and suppress legacy monitoring inbox/summary/AI/subject/raw-intake effects while R5 is active. Preserve the medical-writing unsaved navigation guard byte-for-byte except unavoidable context lines.
- Frontend imports only the new GET-only adapter. No POST/PUT/PATCH/DELETE/FormData/download/provider/model/AI gateway or legacy API fallback.
- The page is a read/search/locate dashboard, not a todo system. Use concise native Chinese. Do not show `正式事实`, `候选信号`, `只读xx`, `Checklist`, `待行动`, `未读`, internal ids/hashes/provider/model/backend on ordinary pages.
- Show all current high/medium risk entries, project identity/cutoff/coverage/change, center pattern numerator/denominator/coverage, one-hop subject Journey/risk anchor, and one further operation to exact source.
- Subject workspace defaults to `受试者医学旅程`; share one visit/time axis across `旅程总览`, `指标趋势`, `事件明细`; eight domains must have distinct shape/line/short-label encoding plus separate severity/risk overlay; include date-pending and AE/MH later-recorded history.
- Backend exposes only the three contract GET endpoints, rejects unknown query/body/identity mismatch, returns the exact read-only envelope and full identity trace fields, does not write or use an old endpoint fallback.
- Worker 01 tests must run focused backend tests and closely shared read-action/main import tests without starting a server. Worker 02 runs all three R5 Node tests plus the existing medical-monitoring pure contract tests that share route/subject APIs, and `npm run build`.
- Workers report exact changed paths, hashes, test commands/results, remaining issues and no-service evidence. Worker self-report is not acceptance.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
