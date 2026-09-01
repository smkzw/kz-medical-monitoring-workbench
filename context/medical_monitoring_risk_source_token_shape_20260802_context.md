# Task Context: medical_monitoring_risk_source_token_shape_20260802

Created: 2026-08-02 18:18:24
Objective: 阻止风险清单入口与索引将非字符串 source version batch revision 静默当作绑定或触发窗口，并避免 malformed token 导致消费层崩溃
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

这是医学监查总 Goal 下的离线风险清单消费层审查：在 B6/C14、运行时和真实项目仍关闭时，阻止来源 token 形状异常导致列表崩溃或被误显示为批次/触发窗口。Codex 直接完成，没有 delegated agent 或 provider dispatch。

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统说明书.md` V1.1；`docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md`；`docs/medical_monitoring_manual/医学监查子系统_分阶段实施与LOOP计划.md`。
- 当前源：`frontend/src/features/medical-monitoring/medicalMonitoringModels.mjs` 与同名 Node 测试；P10 release audit/coverage；B6/C14 gate JSON。
- 当前阻断证据：B6 `pending_review`、C14 `blocked_pending_b6_review`、8911/5174 停止。

## Scope

- In scope: Inbox/API risk-row source version/batch/revision strict text projection, explicit `sourceTokenShape`, trigger-window safe degradation, lineage malformed count, regression and evidence records.
- Out of scope: risk facts/severity/disposition, `App.jsx`/`styles.css`, backend/API/SQLite, source registry/token migration, B6 reviewer outcome, aggregate/CAS, provider/runtime/browser, real projects and medical-writing surfaces.

## Success Criteria

1. Numeric/object source tokens cannot crash `monitoringRiskRowsFromInbox` or `riskIndexRowsFromApi`.
2. Malformed tokens cannot become batch labels, source revisions or trigger windows; rows carry `sourceTokenShape=malformed` and lineage summary counts them.
3. Valid string source token behavior remains unchanged.
4. Subject-adjacent Node suite, focused frontend contracts, Vite, release-gate/hash replay and review-gate are reproducible.

## Risk Boundaries

- 只修改 `medicalMonitoringModels.mjs`、同名测试和任务/发布证据记录；不修改产品 shell、后端、权威 gate 或运行库。
- 不生成/代填 B6 outcome，不启动服务/provider/API/SQLite/browser/真实项目，不触碰医学写作。
- Codex 保留最终验证权；本轮没有 delegated agent。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 18:18:24: Task initialized by `tools/hermes_workflow_guard.py init-task --task-type finite_code_task`; no route was dispatched。
- 2026-08-02: Pre-change model/test hashes: `321e99531b857a64782677e7b1c0f0c6f6e8a08edf76ddc68dd6be15471dce54` / `c9a7e7cbd83b8d5f1a5df3920acd6734c1bac557c7766a09b8b2c737232bb286`；protected App/styles unchanged。
- 2026-08-02: Added `explicitTextState`/`sourceTokenShape`; Inbox/API projections now sanitize source tokens, avoid unsafe string methods, set malformed shape, and use a visible safe trigger-window label. Added numeric/object regression cases。
- 2026-08-02: Risk model **69 passed**, all Node **22/22**, focused contracts **64**, current-shell Vite **1926 modules**. LOOP 4.20 release audit appended and coverage re-bound read-only; release remains blocked。
- 2026-08-02: Final model/test hashes `a95847605a489e4cc806d67e8363e34ceade80e42223f8ad894c259c7a5b6e4b` / `14c6509c7bf7dddf02f79e7614467f8409cce44794cb90602c22f720d871d2c6`; final audit/coverage/decision hashes `8c68c5fee9f138a9239657cdd54231275cd235071ec3555702c683c4a2039d97` / `dce41ba682623e429b327a5ef585848ab184be2a6534cea2c4b3284995d49251` / `b855b25f1071a04fbc190829d9606036755d3a7f60c6956836d4ad4135957892`。
- 2026-08-02: Protected-surface recheck found `frontend/src/App.jsx` had drifted from baseline `3346d9457805eb69bbeb8897fc9112ae809feecc1e45a6d7c50ce3b9190c9f61` to `307cb7961790bcab39fb697ece22b7cef3e2fe1afef3283173bc8910b34a1b8c` (765020 bytes, mtime 18:22:11), and `frontend/src/styles.css` was observed at `35f2e0119a0175d58d81775ca8140aa057a4ab6b01a8007ae9e2ec62764d3a43` (421631 bytes, mtime 18:22:39), while this task only edited `medicalMonitoringModels.mjs`, its test and evidence records. A concurrent QoderWork process was present, but the writer/source is not attributed. Neither protected file was overwritten or reverted; shared-shell acceptance remains unresolved.
