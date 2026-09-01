# Task Context: medical_monitoring_r1_authoritative_progress_20260809

Created: 2026-08-09 20:52:29
Objective: 在隔离R1中实现framework-neutral的权威manifest work-unit ledger与结构化进度feed，使精确数字进度和当前工作播报来自可审计状态；仅synthetic/offline，不触碰产品、医学写作、8911、真实provider或真实项目
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/medical_monitoring_ai_native_system_design_v1_20260809.md`: ExecutionManifest、真实进度、后台运行与用户可理解播报的设计约束。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`: R1 当前门禁、证据和下一安全动作。
- `context/medical_monitoring_ai_native_rearchitecture_audit_20260809_context.md`: D17 决策；分母必须预先展开并随 manifest revision 版本化，播报必须来自结构化状态事件。
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`、`store.py`、`graph.py`: 当前 framework-neutral 领域、SQLite 权威状态和图端口实现。
- `poc/medical_monitoring_ai_native_r1/tests/`: 现有回归合同；旧 manifest 不声明 work unit 时必须保持节点级进度语义。
- 外部一手证据：Microsoft Durable Functions custom orchestration status 文档与 Kubernetes Pod Conditions `observedGeneration` 文档，仅用于验证“框架可投影状态，业务分母和版本真相仍应由应用自有台账掌握”。

## Scope

- In scope: 为 R1 POC 增加 manifest-bound work-unit 声明、SQLite 运行台账、追加式结构化事件、精确 numerator/denominator/status 统计、当前工作与有界播报投影、manifest revision 隔离、依赖/终态/幂等门禁及对应 synthetic/offline 测试。
- In scope: 显式 work unit 的节点只有在所属单元全部终态后才可完成；旧 manifest 保持当前节点级行为。
- Out of scope: UI 页面、真实 provider/harness 调用、真实项目数据、生产调度框架接入、长运行服务、8911、医学写作子系统及产品源码。

## Success Criteria

- 显式 work-unit manifest 设定时原子初始化当前 revision 的权威分母和 `pending` 状态；变更 manifest 产生新 revision，保留旧历史并拒绝 stale callback。
- begin/complete 仅接受当前 revision、合法依赖、合法状态迁移；重放不重复记录，冲突终态不改写历史。
- `manifest_progress()` 对新 manifest 从 work-unit 台账计数，对旧 manifest 继续返回现有精确三键形状。
- 新结构化快照返回 revision、denominator hash、分子/分母/百分比、分状态数量、当前工作、有界事件播报；内容仅来自结构化迁移，不暴露模型思维过程、原始日志、token 或密钥。
- 新聚焦测试、相邻台账/图回归、完整 R1 核心套件、compileall 及相关 lint 通过；独立新鲜上下文复核通过后才接受。

## Risk Boundaries

- 只写入隔离 R1 POC 和本任务的 `context/`、`reviews/`、`metrics/`、`prompts/` 记录；不改产品、医学写作、共享运行库或 runner 所有的 `runs/` 产物。
- 8911 必须保持停止；不启动服务、不安装包、不运行真实项目、不调用真实外部模型/provider/endpoint。
- 对旧 manifest 必须向后兼容；任何新门禁只在显式声明 work units 时启用。
- 外部调度框架的 custom status 仅可作投影，SQLite manifest revision 与 work-unit ledger 始终是 R1 权威来源。
- 独立复核者仅可依据冻结文件、验收准则和可重现检查作出 ACCEPT/VETO；Codex 保持最终验收权。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-09 20:52:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-09 21:34 CST: Bounded primary-source discovery confirmed that external workflow
  runtimes expose application-authored status projections but do not define the medical-monitoring
  denominator. Selected the existing application-owned `ExecutionManifest` + SQLite store instead
  of adding a framework/dependency. Work-unit observations are bound to manifest revision, analogous
  to an observed-spec generation boundary.
- 2026-08-09 21:34 CST: Implemented manifest-frozen `ManifestWorkUnit`, revision-keyed
  `work_unit_runs`, atomic pending initialization, dependency and terminal gates, immutable
  idempotent begin/complete transitions, denominator hash, exact progress counts, current-work
  projection and bounded audit-chain feed. Legacy manifests without work units preserve their
  existing node-level three-key progress shape.
- 2026-08-09 21:34 CST: Focused progress tests 9/9, domain/store/failure adjacent 82/82, capability
  runtime 51/51, R1 core 163/163, audience slice 18/18 and Patient Journey 16/16 passed; grouped
  runnable evidence is 197. Compileall and scoped Ruff pass. 8911 has no listener.
- 2026-08-09 21:34 CST: Full adjacent rerun under the documented `.venv/bin/python` exposed an
  earlier isolation-test fixture omission: its frozen read roots did not declare the active venv,
  so Seatbelt correctly denied `.venv/pyvenv.cfg`. The synthetic helper now includes `sys.prefix`
  only when the interpreter is actually a virtualenv. Product policy and capability runtime remain
  unchanged; focused `.venv` isolation 3/3, capability 51/51 and core 163/163 now pass. This
  correction is recorded rather than preserving the older misleading test-environment assumption.
- 2026-08-09 21:34 CST: Evidence recorded in
  `poc/medical_monitoring_ai_native_r1/docs/R1_AUTHORITATIVE_PROGRESS_EVIDENCE.md`; independent
  artifact-only review is pending. No UI/background worker/real provider/harness/project or product
  acceptance is claimed.
- 2026-08-09 21:58 CST: Native Luna probe was rejected by the current App tool surface, so the
  required fresh reviewer ran through the labeled `codex exec -m gpt-5.6-luna` compatibility path
  in session `019fe6a4-b42f-7403-8279-4940a6ae073c`. First pass returned VETO: P1 ledger mismatch
  did not stop `structured_progress`; terminal same-key conflicting begin was accepted; replaying a
  retrieved manifest created a revision; public audit append could forge feed fields. It also found
  a P2 cross-connection race around the global idempotency pre-check. The review sandbox itself was
  read-only and could not allocate pytest temp files, but reproduced all four P1 paths in memory.
- 2026-08-09 21:58 CST: Remediation normalized manifest definitions before hashing, stored an
  immutable begin-request hash, made structured progress verify exact ledger membership and the
  audit hash chain, reserved work-unit event types to internal transitions, validated exact feed
  payloads without allowing payload metadata overwrite, and moved global idempotency check/replay
  inside `BEGIN IMMEDIATE`. Added direct corruption, forged feed, retrieved-manifest replay,
  conflicting terminal begin and two-connection concurrency tests.
- 2026-08-09 21:58 CST: Post-remediation local anchors pass: focused 11/11, adjacent 84/84,
  capability 51/51, core 165/165, Ruff and compileall. Grouped runnable evidence is now 199 with
  the unchanged 18 audience and 16 Patient Journey tests. Same-session Luna re-review pending.
- 2026-08-09 21:56 CST: Fresh reviewer continuation session
  `019fe6b0-30da-7343-beca-9f0c41624942` completed three adversarial VETO/remediation rounds.
  It reproduced same-count unit substitution, audit-tail truncation, historical legacy cross-revision
  projection, forged node binding, row-only valid terminal status, stale legacy callback, and finally
  a real v4-to-v5 migration that rebound rev1 terminal state to current rev2.
- 2026-08-09 21:56 CST: Remediation now requires exact manifest/ledger/audit-transition agreement,
  persists an audit tail anchor, stores revisioned legacy node denominators, binds node runs and each
  immutable attempt to its opening manifest revision, filters completion gates to the current revision,
  and migrates pre-v5 node state by attempt timestamp against manifest freeze time instead of assigning
  the current revision. Migration tests remove the actual old columns and prove rev2 can reopen without
  inheriting rev1 output.
- 2026-08-09 21:56 CST: Current anchors pass: focused 16/16, adjacent 89/89, capability
  51/51, core 170/170, Ruff and compileall; grouped runnable evidence is 204 with unchanged audience
  18 and Patient Journey 16. Port 8911 has no listener. Same-session final Luna review remains pending;
  no acceptance or R1 completion is claimed before its terminal verdict.
- 2026-08-09 22:01 CST: Same-session final Luna review
  `019fe6b0-30da-7343-beca-9f0c41624942` returned ACCEPT with P0/P1/P2/P3/P4 all zero.
  It reran focused 16/16, adjacent 89/89, the real v4-to-v5 missing-column migration probe,
  all prior adversarial probes, Ruff, compileall and frozen SHA checks. Its nested sandbox could not
  nest Seatbelt (`sandbox_apply: Operation not permitted`), so those 3 checks remain separately
  grounded by the parent-environment capability result 51/51 rather than being claimed from Luna.
  This accepts only the authoritative progress slice; no R1-wide or product acceptance is claimed.
- 2026-08-09 22:01 CST: Accepted frozen hashes are `domain.py`
  `0c3d7e7133d86f4f57826c9452a0d2ec272b3cd82d36f5c3c87f3db024ab3bbd`, `store.py`
  `9a6e344840c90e67c584e95a5a44d41f91015ee09dba7ea0b35f84aef2c41c16`, `__init__.py`
  `955be008d640247cb6076a6312489569ea2840fc6b97c8a81876a4352e77d5e5`, and
  `test_authoritative_progress.py`
  `fbe1457d3c2fc0d19bee3768a71c6289426dab3e6ec26566e1a9f867421beffe`.
  Next safe action is a new isolated slice that binds work-unit execution identity to the durable
  capability attempt journal; it must remain synthetic/offline and may not start UI/service/8911.
