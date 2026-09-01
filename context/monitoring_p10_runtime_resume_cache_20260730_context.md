# Task Context: monitoring_p10_runtime_resume_cache_20260730

Created: 2026-07-30 08:09:29
Objective: 受控恢复医学监查独立AI运行态，验证过期租约恢复与不可变字段画像缓存，并形成证据包v2合同切换前的可审计基线
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/handoffs/CODEX_NO_LOSS_PAUSE_MEDICAL_MONITORING_P10_20260730_0645.md`
- `records/active_slices/medical_monitoring_goal_p10_20260730/TASK_CONTEXT.md`
- `context/monitoring_field_profile_cache_context.md`
- `context/monitoring_p10_protocol_evidence_packet_v2_20260730.md`
- `services/api/app/monitoring_ai_field_profile_cache.py`
- `services/api/app/monitoring_ai_field_profiler.py`
- `services/api/app/monitoring_ai_router.py`
- `services/api/app/monitoring_batch_repository.py`
- 运行态只读证据：
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/medical_monitoring_ai.sqlite3`

## Scope

- In scope:
  - 稳定 API 受控启动和独立 AI readiness；
  - 只通过正式启动恢复/租约机制回收暂停时作业；
  - RUX 不可变大批次首次字段画像与第二次缓存命中计时；
  - 验证 AI 作业调用前后 revision check 不完整读取 listing；
  - 记录 evidence packet v2 旧作业失效后的当前基线。
- Out of scope:
  - 直接修改运行数据库；
  - 采用、确认或发布任何真实医学候选；
  - 修改医学写作子系统；
  - 在本切片内实现规则发布链或启动 daily run。

## Success Criteria

- `/api/runtime-readiness` 为 ready，产品独立 AI 已配置且
  `codex_runtime_dependency=false`。
- 暂停时过期作业只由正式恢复机制处理；旧 v1 方案作业保持 stale，不进入 v2 状态。
- 同一 RUX 批次第一次画像可生成完整缓存，第二次正式 API 调用显著提速并返回同一
  `profile_sha256`、字段数及当前 input revision。
- 缓存命中期间不加载完整 normalized rows；缓存身份或完整性漂移仍失败关闭。
- 聚焦回归、运行态只读核验和任务记录完成。

## Risk Boundaries

- 业务状态只能通过正式 API、worker 和租约状态机改变；禁止直接写 SQLite。
- 产品独立 AI 执行业务任务，Codex/subAgent/会商模型只做工程与验收。
- CM 仅为非试验用药；试验药物给药、dose adjustment 和其他变更保持独立。
- 不修改或清理医学写作工作副本、语料库、来源、版本或数据库。
- 本切片通过不等于医学监查上线或 P10 完成。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-30 08:09:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-30 08:08:36: 暂停记录中的 12 个核心文件 SHA-256 全部一致；8911 与
  8920 均无监听，未发现并行漂移。
- 2026-07-30 08:10:00: 仅用 `scripts/start_stable_backend.zsh` 启动稳定 API。
  readiness 为 ready；独立 AI 为 `alibaba_token_plan/qwen3.8-max-preview`，
  `codex_runtime_dependency=false`。
- 2026-07-30 08:10:00: 启动恢复后所有三项目旧方案 v1 作业均转为
  `stale_input`；RUX/MY009 的暂停 mapping 租约由正式 worker 重新领取，未直接改库。
- 2026-07-30 08:11:31: 通过正式 RUX field-mapping start API 首次建立缓存。请求
  52.367741 秒，返回 202；完整字段数 1805、作业数 175，`profile_sha256` 为
  `bc23dca0f1b85107110d0c1bbb7264014813751e01b26e2ca1db889c472e02ab`。
  缓存 snapshot 为 1,196,355 bytes，manifest/snapshot 权限均为 0600。
- 2026-07-30 08:11:xx: 同一正式 API 第二次请求 1.025797 秒，较首次提速约 51 倍；
  project、batch、profile/input SHA、1805 个字段及 175 个作业身份全部一致。
- 2026-07-30 08:12: 首次正式启动同时暴露向后兼容回归：新代码把冗余的
  `source_binding_revision` 纳入合同后，将同一不可变批次的历史 V13 合同误判为新输入，
  创建 revision `65c9d5f6104ae7...` 的 175 个任务，并把历史 revision
  `97334db06d953123...` 标为 stale。后端立即停止；缓存验收有效，但“没有创建另一套
  合同”的早期观察作废。
- 缓存 manifest 绑定批次 identity
  `d6a5e8c167096ccd8b2a1a649814f59268ed831bfe369558d63640bec483f149`
  和 source binding identity
  `01dd18c7f5f90f86dd519445c849d697a581a3aab1723e4e5163294af4e31c5e`；
  profiler 合同为 `monitoring_ai_field_profiler_contract_v1`。
- 2026-07-30 08:19-08:24: 增加严格历史合同兼容选择器。只有项目、批次版本、来源条目与
  内容哈希、完整字段画像、完整输入、提示词合同和持久化 payload 哈希全部匹配时，才
  复用未携带 binding identity 的历史合同；任何批次/来源/画像漂移仍使用新合同并失败
  关闭。状态接口同步只展示首选合同，避免后来产生的 stale 副本遮蔽旧候选。
- 2026-07-30 08:24: 聚焦 API 13 项、字段画像/仓储/服务/恢复/映射相邻 327 项通过。
  后端重新启动后，正式状态接口只选中历史 revision `97334...` 的 175 个任务。
- 2026-07-30 08:25: 通过正式 `retry_failed=true` 启动接口恢复：150 个带候选任务直接
  恢复 completed，25 个无候选任务排队；误建 `65c9...` 的 175 个任务全部保持
  `stale_input`，其唯一候选保持 `superseded`。历史当前候选 150 条恢复为 proposed，
  未直接写运行数据库。后台随后仅处理真实缺口。
