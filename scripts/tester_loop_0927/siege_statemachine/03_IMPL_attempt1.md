# 03_IMPL_attempt1 — 第3步状态机重构实施记录（attempt 1）

> 实施日期：2026-10-14。设计底稿：同目录 `02_DESIGN.md`（分步迁移 §7 S1-S8）。
> 工作目录：`implementation/workbench`（git main，未push）。
> 本文件为唯一实施留痕；所有提交前缀「状态机专项:」。

---

## 0. E2E验收拦截修复（2026-10-15，提交 `1f60d357`）

**卡点**：E2E两轮（MX循SM1/SM2-CSU）均停于数据接入向导第3步字段映射确认，`mapping_bridge_failed`×13次，~50分钟无进展停手。

**取证（本次实际执行）**：
- 两项目的mapping verifier分片各10片**全部`queue_dwell_timeout`终态失败且attempt_count=0**（sqlite只读查询medical_monitoring_ai.sqlite3）——入队后97分钟从未被认领即被视界收割；
- 同库历史：同形态早于本次实施即反复存在（`f0cd315ab2bd` 10-14 00:24全灭、10-10~10-12多项目177分片大量失败）——**非S1-S7引入的回归**；根因=单一verifier worker被先到项目（baf07c70c25c，177分片，verifier持续更新至10-15 01:31）独占25+小时，后到项目的零认领分片在自身视界到期后被收割（R42B的跨项目变体：R42-01的「本项目视界内有完成即跳过」保护不了自身零完成、纯排队等待的项目）；
- 复现核实：确认（confirm）恒409 `mapping_verifier_job_failed`，其409文案承诺「系统已将其重新排队重跑」但**该路径实际无人重排**（R42-01补偿只挂在降级确认路径）——重试死循环无出路；
- 服务端500零痕迹：mapping桥路由的`except Exception`静默吞栈，E2E期间的500无法取证（已补栈日志，未来必留痕；重放adopt 201/confirm 409无500，历史500最可能是识别刚完成写高峰期的瞬时故障被fail-closed放大，如实标注未能历史复现）。

**修复（最小根因，提交 `1f60d357`）**：
1. `MonitoringAiRepository.fail_queued_jobs_exceeding_dwell`：**等待≠滞留**——同任务类型存在running行（worker池在推进；过期租约行由claim_next自动回收、终态僵尸由expire_exhausted_leases周期清理，信号有界自愈）时，对`attempt_count=0`的排队行重置dwell_since并跳过收割；worker空闲后整段视界仍无人认领照常收割（真饥饿检测保留）；attempt>0重排循环仍按原视界（R29-01语义不变）。
2. `AdmissionMappingConfirmationService.confirm_draft`：`mapping_verifier_job_failed`在raise前调`_retry_failed_mapping_jobs`（与二轮复核路径同款有界预算`_ADJUDICATION_AUTO_RECOVERY_LIMIT`）——409文案与行为一致，预算内下次确认进入`mapping_verifier_incomplete`等待（前端adjudication-start自动轮询收敛）。
3. `admission_stage_view.apply_single_source`：backfill返回值此前被丢弃（row重读入参None），回填成功仍可能误触fail-closed——取回填真值。
4. mapping桥路由（GET/POST投影、白名单违规）500兜底补`_logger.exception`真栈。

**验证**：新增`tests/test_confirm_verifier_deadlock_fix.py`（4测试：在途豁免+等待钟重置/空闲照常收割/confirm兑现重排/回填值流）；全套件258 passed；回归门151 passed；服务重启后SM2/SM1 confirm各触发重排→20片复活为queued→verifier worker恢复逐片消费（≈10分/片，串行池）。**修复①活体取证**（02:34）：两项目18片queued行的dwell_since全部被收割循环重置至02:06-02:11、修复部署后新增收割事件=0（此前同形态全灭）；修复②重排实测生效（409后10片failed→queued）。全量排空为AI执行时长问题（约3小时）在后台自续，不阻塞本修复闭环；E2E三连重跑的新项目将走修复后的完整链路。

---

## 0b. E2E验收拦截修复第二轮（2026-10-15，提交见git log「真栈修复」）

**卡点**：E2E三轮（0/3）从零项目全部确定性停于「生成字段对应建议」`mapping_bridge_failed`×15次（每次20-60秒即失败）。

**真因（上轮部署的栈日志直接抓到）**：`mapping_confirmation.py:2111` `_cohort_candidates_with_progress` 在 `mapping_verifier_incomplete` 分支**裸调** `_cohort_progress(jobs)`，而它是本类 `@staticmethod`（:2117）——方法内裸名只查模块级，**必然NameError**→confirm路由`except Exception`→500 `mapping_bridge_failed`。触发条件=confirm时verifier处于queued/running：从零项目确认时复核必然未完成→**确定性必炸**。该地雷基线（bb7d47ac:2012/2018）即存在；此前未暴露是因为verifier死锁（§0）让项目根本走不到incomplete分支——§0修复解锁链条后立即踩雷。上轮E2E报500而重放只见409的差异由此完全解释：上轮两项目verifier已全灭（job_failed分支不经过NameError行）。

**修复**：`:2111`改`self._cohort_progress(jobs)`（staticmethod经self调用）；ruff F821全量扫描admission包+相关services模块，另发现并修复`monitoring_ai_repository.py:3679`注解`Optional`未导入（lazy注解暂不炸的同族缺陷）——修复后F821全清。

**验证**：新增回归测试`test_verifier_incomplete_annotates_progress_without_name_error`（锁incomplete分支：raise mapping_verifier_incomplete+cohort_progress聚合注释正常）；全套件**259 passed**；回归门**151 passed**；服务重启（build api-2fec4e3fa887808f）后对SM3真实卡死项目（proj_user_4f262469d486，verifier 3完成/5排队/2执行=原NameError触发形态）重放：confirm返回**409 mapping_verifier_incomplete**（非500，文案引导自动等待）、adjudicate 200正常载荷、服务器日志零NameError——UI链（confirm→adjudication-start自动轮询→复核完成后自动继续确认）恢复设计行为。

---

## 1. 总结论

| 步 | 状态 | 提交 | 新增pytest |
|---|---|---|---|
| S1 地基（两表+StageStore+事件埋点） | ✅完成 | `e61d2067` | tests/test_admission_stage_events.py（12） |
| S2 识别态物化（影子期） | ✅完成 | `c2461e1a` | tests/test_stage_state_recognition.py（4） |
| S3 投影单源 | ✅完成 | `903ff09f` | tests/test_projection_single_source.py（6） |
| S4 查找键收口 | ✅完成 | `0dd80582` | tests/test_gate_lookup_key_consistency.py（6） |
| S5 降级入口服务端化 | ✅完成 | `8413043b` | tests/test_inflight_adoption_server_flag.py（3） |
| S6 失败不缓存下沉 | ✅完成 | `7cc6a419` | tests/test_infra_failure_not_cached.py（4） |
| S7 stage-state端点+前端恢复 | ✅完成 | `1b9a84fb` | tests/test_stage_state_endpoint.py（10） |
| S8 文档验证结论物化 | ⏸延后（见§5） | — | — |

**回归门（本次实际执行）**：`cd implementation/workbench && .venv/bin/python -m pytest tests/medical_monitoring -q -p no:cacheprovider` → **151 passed, 21 warnings**（与实施前基线151 passed逐字一致，0失败，只拦新增=0拦截）。

**专项与基线套件（每步合并前均跑）**：设计§7指定的基线三件套+`test_monitoring_ai_repository.py`+`test_monitoring_ai_mapping_gate.py`+`test_mm_c3_dual_mapping_cohort.py`+全部专项新测试 → 最终态 **254 passed**（`1b9a84fb`上实测）。

**界面冒烟（本次实际执行，经5178界面非API）**：重启隔离对（8911 ready:true build `api-ff8c39482543ef6b`，5178 /monitoring 200，runtime-build.json指纹配对一致；8910/5177未触碰、全程DOWN与实施前一致）后，浏览器经 http://localhost:5178 选择项目「MX循开考-CSU · MG-K10 · 慢性自发性荨麻疹」→ 医学监查首页 → 点「开始一次新的监查」→ 四步向导完整走通：第2步呈现「数据层事实快照已核验：10表/591行/3038值100%往返校验」（B6 facts门过）、第4步「确认并开始监查」按钮 **disabled:false**（前置链校验入口可用）。**未点击最终开始按钮**——常驻项目按预置停在「confirmed+facts ready未启动运行」，实际启动会变更停驻状态（留给E2E验收阶段）。佐证：`GET .../data-admissions/stg-cd69899943ba42618f589ba07a134a59/stage-state` 在线返回 `current_stage:"complete"`、四阶段 ready/candidates_ready/confirmed/ready（lazy回填在真实数据上生效，revision=1）。

---

## 2. 各步实施内容（改了什么）

### S1 地基（e61d2067）
- 新增 `services/api/app/monitoring_admission_stage_store.py`：`monitoring_admission_stage_events`（append-only，ULID主键，no_update/no_delete触发器）与`monitoring_admission_stage_state`（PK=project+attempt+stage，revision单调）DDL常量 + `AdmissionStageStore`（append_event/bump_stage/get_stage/list_events，必须传外层conn同事务）+ `INFRA_FAILURE_CODES`（自文档链`_INFRA_FAILURE_CODES`上收共享，S6前置）+ `recognition_attempt_id`（business_key前缀解析，识别链两前缀外一律不落事件）+ `failure_class_for`（infra/content二分）+ `aggregate_recognition_state`（B1派生契约唯一函数）。
- `MonitoringAiRepository._initialize` 执行两表DDL（同库medical_monitoring_ai.sqlite3，纯附加，DROP即回滚）；构造器挂`stage_store`。
- 事件埋点（同事务）：`create_or_get`(INSERT)/`complete`/`fail`/`mark_stale`/`fail_queued_jobs_exceeding_dwell`(收割前预SELECT命中行)/`retry_terminal`(recovery_action，explicit→actor=user)/`stale_claimed`。文档链workflow的`_INFRA_FAILURE_CODES`改为导入共享常量（行为零变化）。
- 测试覆盖：变迁→事件存在；触发器immutable；infra/content分类；同事务回滚事件不存；revision单调；非法枚举ValueError；前缀解析边界。

### S2 识别态物化（c2461e1a）
- 上述六写点接`_materialize_recognition_stage`（同事务内primary cohort聚合→bump_stage）；**额外补齐全部状态跨越writer**（设计只列5方法，但租约耗尽/退役等不改会制造影子期假漂移）：`expire_exhausted_leases`、`retire_unstarted_duplicate`、`retire_obsolete_generation`、`_apply_contract_supersession`、claim隔离路径（仅物化不落事件）。
- 投影影子比对：`AdmissionMappingPipeline._project`计算派生state后调`_shadow_compare_recognition_state`（仅primary cohort；物化行缺失不算漂移；不一致→`stage_view_divergence`事件，独立事务、自身故障不影响投影；`STAGE_VIEW_MODE`≠derive时跳过）。
- 测试覆盖：§3.2全变迁矩阵（not_started→generating→candidates_ready→needs_attention→generating）；漂移留痕/verifier不比对/缺行不比对/env跳过；并发retry竞态（ThreadPool×2，恰一成功+一StateConflict，物化行一致）；CAS拒绝回滚不留亡态。

### S3 投影单源（903ff09f）
- 新增 `packages/medical_monitoring/admission/admission_stage_view.py`：`apply_single_source`——冲突1四字段唯一写点：顶层state（`STAGE_VIEW_MODE=materialized`默认读物化行，行缺失且有cohort作业→经调用方backfill按权威回填，仍无行→`AdmissionStageViewError("mapping_bridge_failed")` fail-closed；=derive保留派生值）；顶层confirmation_status（drafts权威行status）；facts_generated（A4直查）；pending_confirmation_count（无draft→candidate_count；active→未答疑问字段数；confirmed→0）；字段级confirmation_status（命中draft已答字段→confirmed）。
- 删除硬编码：B1 `mapping_pipeline._project` 的`:2189`字段级/:2214顶层confirmation_status/:2219 pending计数；B2 `enrich_candidates` 的facts_generated=False；`_draft_payload`的facts_generated=False；B3 `list_for_review` confirmed覆盖逻辑收编进apply_single_source；`confirm_draft`响应facts_generated改`_facts_status`（A4直查，值不变来源变）；`_project`内联_TERMINAL/_FAILED集合收编为`aggregate_recognition_state`（与物化行/verification同口径）。
- `AdmissionMappingConfirmationService`新增`facts_status_resolver`注入（main.py晚绑定lambda接`_r7_admission_fact_materializer.status`）与`_recognition_state_row`（读行+权威回填）。
- 存量测试更新2处：`test_mm_c3_mapping_confirmation.py`两处对已删硬编码的断言改为断言键不存在。

### S4 查找键收口（0dd80582）
- `fact_materialization.latest_attempt_id(project, workspace)`共享函数提取；`latest_fact_materialization_ready`与`main._r7_real_setup_inputs`两处同逻辑重复收编（B6门与投影同源）。
- stage_view新增`confirmation_scope`：本attempt draft confirmed且latest同draft→"confirmed"；latest属别attempt→"superseded_by_newer_attempt"+note「项目存在更新导入」；**门语义不变**（B5仍直读latest_draft_for_project，任一未确认409）；GET投影透出（路由白名单加confirmation_scope）。
- 测试覆盖：新attempt未确认→门409；旧attempt confirmed不放行新attempt（R18-03回归）；门与投影同键；latest_attempt_id归属。

### S5 降级入口服务端化（8413043b）
- 阈值上收：`RECOGNITION_INFLIGHT_STALL_SECONDS=1800`（原前端MAPPING_STALL_THRESHOLD_MS）；`_project`复用R44 pace窗口计算`inflight_adoption_available`（generating+有候选+窗口末次完成>30min）。
- `adopt_draft`门改为双标志：`allow_inflight_adoption` AND 服务端`inflight_adoption_available is True`（判定单源化，未停滞带前端标志仍422 mapping_run_incomplete；门禁不放松）。
- 前端：确认态模块新增`inflightAdoptionAvailable`正规化；向导降级入口按钮渲染改读服务端标志（本地停滞计时仅留提示UI）。
- R35测试桩更新：generating态且期望降级采纳通过的桩携带停滞标志。
- 测试覆盖：停滞→available；未停滞→adopt 422；停滞→adopt通过且在途字段按缺口排除（R35契约回归）。

### S6 失败不缓存下沉（7cc6a419）
- `create_or_get`：env灰度`WORKBENCH_MONITORING_AI_INFRA_RETRY`（默认off）开启时，命中行为「终态失败+failure_code∈INFRA_FAILURE_CODES+无契约退役」→按显式重试语义调`retry_terminal`（无automatic_recovery_limit=不受自动预算约束；retry_terminal自带recovery_action留痕actor=user）；StateConflict竞态回落常规路径。同job_id隐含输入指纹全等，revision变化行天然不命中。
- **调用点核实（设计§9未验证项3）**：AI作业提交唯一漏斗=`monitoring_ai_service.MonitoringAiService._create_job`（monitoring_ai_service.py:1819），已注明于`_infra_failure_requeue_enabled`docstring。灰度默认off=生产行为零变化。
- 测试覆盖：R11-01场景（infra失败→重发→requeued+actor=user留痕）；content失败原样返回；契约退役原样返回；env默认off原样返回。

### S7 stage-state端点+前端恢复（1b9a84fb）
- stage_view新增`build_stage_view`：四阶段聚合→stages/current_stage/blocking[]/primary_action_key/revision；blocking不变量（§5.3）：**自救形态**（当前阶段∈{failed,needs_attention,needs_user_input}或映射阶段未确认）必须携带≥1个action_available键，违反→500 fail-closed；健康等待态（in_progress/generating/未轮到）如实action_available=false不误伤。
- **动作键枚举扩展（设计之外，如实记录）**：原§3.5枚举缺常规动作键——no_draft常态的采纳与draft_active无疑问常态的确认按§3.3变迁必须可执行，否则§5.3不变量在健康路径必然500。补`adopt_full`/`confirm_mapping`两键（代码内注明）。
- 新端点 `GET /r7/data-admissions/{attempt}/stage-state`（READ_SOURCE_EVIDENCE投影权限，无写门）：documents←document_readiness（A1/A3/A5）；recognition←物化行（缺失回填）；mapping←drafts权威行；facts←A4直查（经confirmation._facts_status）；If-None-Match→304。路由清单存量测试（additive registration契约）纳入新端点。
- facts跨库best-effort回写（§2.3/§3.4）：`FactMaterializationService`新增`stage_recorder`注入（成功→facts行ready+state_changed；失败→failure_recorded事件，不改状态行）；main.py接`_record_facts_stage_state`（独立事务，异常静默——门与投影永远直查A4）。
- 前端C2删除：Wizard.jsx两段localStorage步骤记忆useEffect删除，改为挂载时`getDataAdmissionStageState`一次权威查询，current_stage越过documents即advance到映射面板（F5根治；R9-02类本地态失步结构上消除）。C6：确认超时（5min）从纯本地放行改为先`loadMappingCandidates()`重读权威再放行。C1/C3/C4/C5/C7的改造范围见§4如实偏差。

---

## 3. 验证证据（本次实际跑过的命令与结果）

| 验证 | 命令 | 结果 |
|---|---|---|
| 回归门 | `.venv/bin/python -m pytest tests/medical_monitoring -q -p no:cacheprovider` | **151 passed**（基线151，0失败） |
| 每步基线+专项 | 15个测试文件全量（§1列表） | 最终 **254 passed**（1b9a84fb） |
| 前端门 | `cd frontend && node --test $(ls src/features/medical-monitoring/*.test.mjs)`（60文件） | **94 pass / 0 fail**（分两半复跑64+30交叉验证覆盖完整） |
| 前端构建 | `npx vite build --logLevel error` | 通过 |
| 服务自检 | `curl 8911/api/runtime-readiness`、`curl localhost:5178/monitoring`、`runtime-build.json` | ready:true；200；指纹配对 `api-ff8c39482543ef6b` |
| 在线端点佐证 | `curl .../stage-state`（真实attempt） | `current_stage:"complete"`，四阶段齐 |

## 4. 如实偏差与未尽事项（不夸大）

1. **S8延后**：设计§7明示「性能，可独立延后」；A8 verdict缓存未实施。study-documents 68s重放成本现状不变（stage-state端点documents阶段读document_readiness，与既有面板同源同成本）。
2. **§6.3前端C1/C3/C4/C5/C7未做逐字改造**：C7主按钮documents分支（Wizard.jsx:1311-1377）保留——该块是R1/R28/R33-07/R41-03四轮实测教训的细化渲染（从documentState单一载荷的显式字段推导），backend `build_stage_view`的documents五态粒度不足以无损承载这些子形态（裁决/身份/内容差异三分）；机械替换会回退已验收UX且冒烟风险高。C3的confirmed推导现读的`confirmation_status`已是S3单源字段，前端二次推导实为渲染映射；C4/C5的载荷来源同样已是权威投影。**前端消费的字段已全部单源化（S3/S4/S5），本地综合判定唯余C2（已删）与C6（已改）**。
3. **stage-state轮询未接**：端点已支持If-None-Match 304，前端目前挂载时调用一次（F5恢复语义已兑现）；持续轮询留待S8后一并评估（避免引入68s级轮询负载）。
4. **facts generate失败态无持久行**：按设计§3.4「失败不落持久失败态」，只有failure_recorded事件；`retry_generate_facts`动作键在端点已可达（facts_recent_failure参数），但build_stage_view调用侧当前恒传false（失败事件的时效窗读取未接）——retry键现阶段经generate_facts路径兜底。
5. **C7主按钮的primary_action_key消费**、blocking[]的前端渲染未做（同偏差2）；stage-state端点已供数。
6. **attempt1期间一次git状态纠缠**：S4前核实migration gate存量失败时stash/checkout交错，已完整恢复（工作树经grep指纹+全量重跑验证，无丢失）；教训已吸收，此后不再在测试存量失败时做时间点切换。
7. **存量失败（非本次引入）**：`tests/test_mm_c3_mapping_migration_gate.py::test_legacy_glm_cohort_can_never_enter_a_new_draft` 在pre-S1基线`bb7d47ac`上同样失败（`TypeError: 'AssertionError' object is not iterable`，mapping_confirmation.py `_draft_payload`），不在回归门范围（tests/medical_monitoring之外）与设计指定基线套件之外，未修（最小根因修复原则不适用于范围外存量的顺手改）。

## 5. 回滚

权威schema零变更；两张新表`DROP TABLE monitoring_admission_stage_events, monitoring_admission_stage_state`即完全归零。逐步回退：S2/S3的`STAGE_VIEW_MODE=derive`回派生；S6 `WORKBENCH_MONITORING_AI_INFRA_RETRY`默认off；S7端点保留无害；前端C2/C6按组件revert（1b9a84fb单提交）。
