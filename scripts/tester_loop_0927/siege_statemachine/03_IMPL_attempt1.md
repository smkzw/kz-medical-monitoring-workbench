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

---

# 03_IMPL_attempt1（v2续篇）— 02_DESIGN v2剩余收口T1-T6实施记录（2026-10-15）

> 设计底稿：同目录 `02_DESIGN.md` v2（§5分步迁移T1-T8）。本节为v2收口的实施留痕，
> 追加于v1记录（§0-§5）之后；提交前缀仍为「状态机专项:」。基线（v2设计§5实测）：
> 专项8文件51 passed / 回归151 passed / 前端confirm-state 33 pass-0 fail（本次实施前复跑逐字一致）。

## 6. 总结论

| 步 | 状态 | 提交 | 新增测试 |
|---|---|---|---|
| T1 facts失败时效窗（D5） | ✅完成 | `9eee3331` | tests/test_facts_recent_failure_window.py（7） |
| T2 documents事件留痕（D1） | ✅完成 | `49f9ad79` | tests/test_admission_stage_documents_events.py（6） |
| T3 mapping事件留痕（D2） | ✅完成 | `286e037a` | tests/test_admission_stage_draft_events.py（6） |
| T4 前端死锁哨兵（D6/C7） | ✅完成 | `3e81e2f6` | WizardState.test.mjs新增8断言（模块84 checks） |
| T5 S6灰度开启（D3） | ✅代码+灰度env已开/⚠️现场点燃未完成 | `454edef0` | tests/test_infra_requeue_dwell_interaction.py（3） |
| T6 S8 verdict物化缓存（D4） | ✅完成（缓存默认off灰度） | `2d411755` | tests/test_document_authority_verdict_cache.py（9） |
| T7 E2E三连从零门 | ❌本窗口未执行（见§12如实声明） | — | — |
| T8 A5入库 | 按v2设计建议不做 | — | — |

**回归门（本次实际执行，ask指定命令）**：`cd implementation/workbench && .venv/bin/python -m pytest tests/medical_monitoring -q -p no:cacheprovider` → **151 passed, 21 warnings**（与实施前基线151逐字一致，0失败，只拦新增=0拦截）。

**专项+邻域套件（最终态实测）**：15个测试文件 → **173 passed**；前端门 `node --test src/features/medical-monitoring/*.test.mjs` → **94 pass / 0 fail**；`npx vite build --logLevel error` 通过。

## 7. 各步实施内容

### T1（9eee3331）
- `mapping_candidate_routes.py`：新增纯函数 `facts_recent_failure_from_events`（时效窗唯一推导：最近failure_recorded晚于最近ready且24h内→True）；`_assemble_stage_state` 装配侧经 `stage_store.list_events(stage="facts")` 读取并以 `facts_recent_failure` 实参传入 `build_stage_view`——`retry_generate_facts` 动作键真实可达；读取故障best-effort回退False=现状。
- `main.py _record_facts_stage_state`：`failure_class="content"` 字面量改 `failure_class_for(failure_code)`（infra/content正确分类）。
- `monitoring_admission_stage_store.list_events` 加可选 `stage=""` 过滤（缺省=原契约；防同attempt的recognition事件挤占limit截断最新facts事件）。

### T2（49f9ad79）
- workflow增 `_record_stage_event`（best-effort独立事务，attempt_id=''项目级，双保险吞异常）；§2.2 documents表全部变迁埋点：start→analyzing（batch_started；重传重排另记recovery_action actor=user）、advance的分析作业重建/四阶段推进（analyzing→reviewing→adjudicating→cross_checking）/各阶段显式与自动重排（recovery_action）/failed（failure_recorded，failure_class经failure_class_for）/identity门挂起（state_changed→needs_user_input reason=identity）。
- `monitoring_document_authority_jobs`：promote链A1注册事务提交后→promoted；内容确认挂起→needs_user_input（reason=content）。签名加可选 `stage_event_from_state`（调用方线性阶段提示，缺省''）。
- store增 `append_event_autonomous`（独立事务+内部吞异常）。不建状态行（§2.5裁决）。
- 实施事故与修复（如实）：promote函数的annotate循环曾被缩进错改移出A1事务（原测试`test_product_workflow_starts_both_models_and_promotes_direct_agreement`当场红：source registry annotation requires a transaction），已修复为纯附加diff后该测试绿。

### T3（286e037a）
- `MonitoringMappingDraftRepository` 挂同文件 `AdmissionStageStore`（`_initialize` 幂等补建STAGE_TABLES_DDL——独立文件场景如测试直连也需要事件表落点）；`_record_draft_event` 接draft写的外层conn（**同一sqlite事务**，§2.3纪律）。
- 四个CAS写点埋事件（attempt键=batch_id）：assemble→no_draft→draft_active(v1)；edit_field/reapply_known_export_context→vN→vN+1；confirm→draft_active→confirmed。部分采纳（域/槽位豁免非空）与降级确认（服务层confirm加可选 `degraded` 实参传入）另记degradation。幂等重放路径提前返回不重复落事件。不建状态行。

### T4（3e81e2f6）
- `medicalMonitoringAdmissionWizardState.mjs` 新增纯函数 `stageSentinelAction(stageState, localPhases)`：窄契约——仅当「面板无任何可用控件且非busy」而权威blocking[]携带action_available键时产出哨兵；busy（导入/识别轮询/复核/监查数据生成中）与complete态恒null；键→既有onPrimaryAction分支映射（reload-documents/reload/adopt/confirm/generate-facts）。
- Wizard：stage-state权威快照入state（挂载S7同源一次+映射面板静默禁用态一次1.5s去抖重读，**非周期轮询**——T6缓存灰度off前documents回放成本未收口）；footer哨兵次按钮（琥珀描边，不替换既有主按钮文案与逻辑）；onPrimaryAction加reload-documents分支。

### T5（454edef0+运行时）
- 前置交互测试3项：重排显式重置dwell基线→视界内不被二次收割；在途豁免=**整轮跳过**（attempt=0等待钟重置，worker空闲下一轮按原视界补收——测试如实记录该语义，与实施注释逐字对齐）；env off复跑零行为差。
- 隔离runtime灰度开启：8911重启带 `WORKBENCH_MONITORING_AI_INFRA_RETRY=1`（ps eww实测在进程env内）；回滚=env置空重启（代码路径不变）。

### T6（2d411755）
- A2同库新表 `monitoring_document_authority_verdicts`（key=project+entry+registry_revision+cited_job_digest，verdict 0/1，CHECK约束；`MonitoringAiRepository._initialize` 幂等建表）。
- `MonitoringDocumentEvidenceResolver` 加 `verdict_store` 注入（main.py接monitoring_ai_repository）：核验链拆分——receipt完整性（廉价哈希/形状检查）永不缓存先判，promoted条目才进verifier重放（指纹命中跳过）；**缓存关闭路径与现状逐字一致**（钩子直调/回退，含测试自定义钩子语义不受影响）；cited_job_digest=被引作业行+候选行内容摘要；读写均env `WORKBENCH_DOCUMENT_VERDICT_CACHE` 门控（默认off=零缓存路径）。

## 8. 验证证据（本次实际执行的命令与结果）

| 验证 | 命令 | 结果 |
|---|---|---|
| 回归门（ask指定） | `.venv/bin/python -m pytest tests/medical_monitoring -q -p no:cacheprovider` | **151 passed**（基线151，0失败） |
| 每步合并门 | 新测试+专项8文件+邻域（draft仓/确认/文档jobs） | 每步全绿（T1 58/T2 91/T3 179/最终态173 passed） |
| 前端门 | `node --test src/features/medical-monitoring/*.test.mjs` | **94 pass / 0 fail** |
| 前端构建 | `npx vite build --logLevel error` | 通过 |
| 服务自检 | 8911 runtime-readiness / 5178 /monitoring / runtime-build.json | ready:true build `api-2c80589e9f8dfb30`；200；指纹配对一致 |
| 灰度env生效 | `ps eww <8911 pid> \| grep WORKBENCH_MONITORING_AI_INFRA_RETRY` | `WORKBENCH_MONITORING_AI_INFRA_RETRY=1` 在进程env内 |
| 界面冒烟（经5178非API） | 浏览器驱动 | 见§9 |

## 9. 界面冒烟（本次实际执行，经5178界面非API）

8911/5178按ISO_ENV_LOG标准命令双重启（8910/5177 curl复核仍DOWN与实施前一致，未触碰）后，浏览器经 http://localhost:5178 选择项目「MX循开考-CSU · MG-K10 · 慢性自发性荨麻疹」→ 医学监查 → 点「开始一次新的监查」→ 四步向导完整走通：第1步日常监查（系统推荐）、第2步「数据层事实快照已核验：10表/591行/3038值100%往返校验」（B6 facts门过）、第3步特殊关注规则勾选、第4步「确认并开始监查」按钮 **disabled:false**（前置链校验入口可用）。**未点击最终开始按钮**——常驻项目按预置停在「confirmed+facts ready未启动运行」，实际启动会变更停驻状态（留给E2E验收阶段）。

## 10. 如实偏差与未尽事项（不夸大）

1. **T7未执行**：三连从零E2E门需要上游AI通道稳定窗口（每轮真实建项→上传→核对→识别→确认→事实→运行→发布数分钟到小时级壁钟；04诊断记录的失败形态=上游glm-5.3-flash 429瞬断；fullchain底座为SAR重跑1000+作业量级）。本窗口上游仅经冒烟路径被使用，三连全通无法在诚实前提下完成——**未跑即未跑，不以单轮或回放冒充**。gatePassed按ask定义=回归门+冒烟（均过）。
2. **T5现场点燃未完成**：经服务层以重建载荷重发SM3两条infra失败行的尝试被claim侧身份校验正确隔离（`monitoring_ai_job_identity_invalid` quarantine，72ms内，终态无害保留作审计行 `monai_b0e1764e108871cf3fb6956c0f4b`；`retire_obsolete_generation`按设计不触终态行返回0）——重建载荷≠管线原始funnel输入本就是预期差异。R11-01行为由env-on单测锁定（`test_infra_failed_hit_requeues_on_resubmit`：infra失败→同请求重发→requeued+actor=user）；现场点燃留待E2E自然触发。「观察一个完整识别周期无收割异常」本窗口无识别运行可观察，未跑。
3. **T4不做周期轮询**：哨兵权威快照=挂载一次+映射面板静默禁用态一次重读（1.5s去抖、按键变化触发）。原因：T6缓存env off时stage-state的documents回放成本（考古报告19.9s级）不宜引入周期负载；缓存灰度开启后可再评估。
4. **T4哨兵不覆盖文档面板**：文档面板保留四轮验收的自身控件集（上传/重试/裁决/差异确认），哨兵hasEnabledControl恒真不与其打架（R3）；哨兵实际作用域=映射/事实面板（D6的C7缺口主体）。
5. **T2的needs_user_input reason族**：两模型工作流无「角色裁决挂起」独立返回点（身份门/内容差异确认是仅有的两个挂起出口）——design表的reason=role在本工作流无对应变迁返回，实际落点为identity与content两类，role类未伪造。
6. **T6缓存路径语义假设**：缓存开启时按生产registry（SourceRegistryService）标准钩子语义拆分；无钩子registry的回退契约（receipt完整即verified）逐字保留。
7. **T2/T3事件写入纪律差异（按设计）**：T2跨文件点=独立事务best-effort（权威写后，异常双保险吞）；T3=与draft写同一事务（设计明示同事务，CAS回滚连事件一起回滚，测试锁定）。
8. **工作树遗留（非本次产生）**：`01_STATEMAP.md`/`02_DESIGN.md` 的未提交修改与 `runs/*/ai_provider_settings.json`、`ai_role_bindings.json` 的tracked差异在本会话开始前已存在（后者为API进程startup migration格式化重写，R44留痕同款），本次未触碰不纳入提交。
9. **8911灰度env为进程级**：服务若被无该env的命令重启，灰度静默回退off（=设计回滚路径）；ISO_ENV_LOG已留痕标准重启命令含该env。

## 11. 回滚

T1/T2/T3：单提交revert（事件表留存无害，投影/门不读documents与mapping事件）。T4：组件revert（3e81e2f6），哨兵默认不渲染=现状。T5：env置空重启即回滚（代码路径不变）。T6：env off回直连重放；`DROP TABLE monitoring_document_authority_verdicts` 归零。权威schema（drafts/jobs/registry/facts/A5文件态）全程零迁移。

## 12. 一句话结论

v2剩余六缺口中**五个半已收口**——T1/T2/T3/T4/T6完成并各自带锁行为测试，T5代码+交互测试+灰度env已部署（现场点燃留待E2E），T7三连从零门因上游壁钟依赖本窗口未执行（非代码验收步，按04诊断流程另约窗口）；回归门151 passed与基线逐字一致，常驻项目界面冒烟走通四步向导至开始按钮可用。

---

# 03_IMPL_attempt1（v3续篇）— 02_DESIGN v3剩余收口M1-M4实施记录（2026-10-17）

> 设计底稿：同目录 `02_DESIGN.md` v3（§四-M1~M4，git工作区版本，本会话实读）。
> 提交前缀仍为「状态机专项:」。实施前基线（本会话实跑，与v3设计§四基线逐字一致）：
> 专项13文件套件 **81 passed / 1 failed**（红=N1定时炸弹）· 回归门 **151 passed** · 前端node --test **34 pass / 0 fail**。

## 13. 总结论

| 步 | 内容 | 状态 | 提交/产物 | 验证 |
|---|---|---|---|---|
| M1 | 修N1红测试（`_assemble_stage_state`时钟注入口） | ✅完成 | `d00a5a49` | 13文件套件 **82 passed / 0 failed**（生产调用零变化，缺省None=真钟） |
| M2 | gate_blocked留痕（N4） | ✅完成 | `3fd773bd` | 新增tests/test_gate_blocked_event.py 5测试；14文件 **87 passed**；回归 **151 passed** |
| M3 | S8 verdict缓存启用（N2） | ✅启用，⚠️延迟预算未达标（如实） | 纯env，无代码提交；ISO_ENV_LOG已记 | 前置① 9/9；前置② 三端点语义等价；前置③ 活体失效链在案；剖析归因在档 |
| M4 | E2E三连从零门（N3） | ⏳部分完成（详见§16，如实） | 驱动脚本+证据入库 | Round2全链从零✅；Round1确认✅但事实门产品断点；Round3/Round1b对账中 |
| 不做 | A5入库/C7整体接管/B5门键合并 | 维持v3裁决 | — | — |

**回归门（本次实际执行，ask指定命令）**：`.venv/bin/python -m pytest tests/medical_monitoring -q -p no:cacheprovider` → **151 passed**（M2后终态，与基线逐字一致，0失败）。

## 14. M1/M2 实施内容（改了什么）

### M1（d00a5a49）
- `packages/medical_monitoring/api/r7_product/mapping_candidate_routes.py:884`：`_assemble_stage_state` 增可选kwarg `now: Optional[datetime] = None`，docstring注明「仅测试消费——缺省None=真钟=现状」；
- `:1027-1031`：`facts_recent_failure_from_events(..., now=now)` 实参透传（生产调用点:1981 不传=零变化）；
- `tests/test_facts_recent_failure_window.py:106`：`test_assemble_stage_state_passes_window_flag` 改传 `now=NOW`（固定钟2026-10-15T12:00Z）。

### M2（3fd773bd）
- `services/api/app/main.py:1161` `_r7_mapping_confirmation_gate`：两个阻断return改为先组装 `blocked` dict→**落gate_blocked事件**→再return。事件经 `monitoring_ai_repository.stage_store.append_event_autonomous`（attempt_id=''项目级、stage=mapping_confirmation、reason_code=mapping_confirmation_required、detail.draft_status=草稿状态或no_draft）；外层try+append_event_autonomous内层吞异常双保险；门判定路径零变化、永不读物化行（R18-03保护不变）；门是求值不是变迁，每次阻断如实留痕（同请求多条允许）。
- `tests/test_gate_blocked_event.py`（新增5测试）：未确认draft调门→事件六字段正确；no_draft→draft_status=no_draft；事件写故障（BrokenStore）→门仍返回409详情不外泄；重复触发→多条事件；confirmed放行→零事件。
- 端点唯一消费点核实：`run_routes.py:131`（POST /runs/prepare-and-start，用户动作非轮询路径），无写放大风险。

## 15. M3 实施与验证（env=1，零代码改动）

### 前置① 等价性单测
`tests/test_document_authority_verdict_cache.py` 独立实跑 **9 passed**。

### 前置② 隔离runtime A/B（同项目 MX循开考-CSU attempt stg-cd69899943…）
采样 off×2（env off现进程）→ env=1重启 → cold×1 + warm×2，三端点响应体全部留档（`scripts/fullchain_statemachine_20261017/m3_ab_samples/`）：
- **语义等价**：三端点off/on序无关JSON比较全等（stage-state/study-documents md5逐字节相同；mapping-candidates仅跨进程JSON键序不同，语义等价）。
- **缓存写/命中**：verdicts表0行→重启采样后4行（两项目各2条目）→多次热控行数稳定=命中。
- **延迟（如实：预算未达标）**：stage-state off 17.0/17.6s → on cold/warm 14.5s±0.1；study-documents off 17.6/17.4s → on 14.2-14.6s；mapping-candidates 0.28s（不动）。预算「P95个位数秒级」**未达成**。

### 前置③ 失效链
- 单测在档：registry失效/digest失效（9测试内）。
- **活体实证**（M4期间自然发生）：round1项目（2edc1e9be2cd）文档角色裁决/重晋升使A1指纹变化，verdicts表该两条目累积**12个registry_revision**、round3项目（57fe3b136c9a）2个——每次指纹变化=旧键失配miss重算+新键落行，失效语义在生产负载下逐字生效；34行/5项目在案。

### 延迟未达标的剖析归因（按设计R4：不放松fail-closed、不改超时，转剖析）
独立进程cProfile（同env导入main跑document_readiness，脚本+结果在档 `m3_profile_docreadiness.py`）：verifier重放已被缓存消掉（profile不可见）；剩余成本在S8范围外——`source_intake._read_all`×10 **22.1s cum**（A1 JSONL全量重读）、`build_manifest→latest_fact_materialization_ready→graph store_base.__init__`×27 **13.9s cum**（反复开图库）、`_monitoring_entry_validation_is_usable` **11.1s cum**（A3复查）、pydantic校验7.4s。回滚=env置空即回直连重放（A/B实测零缓存路径行为不变）。

### 重启与配对
8911标准重启（pid 36398，01:52:13 CST，env按ps eww实读逐字保留+新增缓存env）→ build `api-817b6b45dc710ed1` ready:true；5178 vite同步重启→指纹配对一致；8910/5177 lsof复核0监听未触碰。详见ISO_ENV_LOG 2026-10-17 01:52节。

## 16. M4 E2E从零门（部分完成，如实分项）

驱动：`scripts/fullchain_statemachine_20261017/e2e_round.py`（幂等stage断点续跑+journal+事件流导出；底座模式沿fullchain_sar_rerun_20260926；链路=向导同源r7端点：建项→上传→核对→识别→采纳/答题/对账/确认→事实→run-setup/prepare-and-start→progress→publish→results）。证据：`rounds/<round>/{journal.jsonl,state.json,stage_events_export.jsonl}`。

| 轮 | 项目/attempt | 结果 |
|---|---|---|
| Round1 | 2edc1e9be2cd / stg-f729c319… | ⚠️**走至确认✅、事实门产品断点**：EX主分片invalid_ai_output内容级失败→部分采纳（EX整域豁免，T3 degradation事件在档）→23个双盲分歧题作答→对账收敛42/0→**确认成功且非降级**（6a3d4c3d修复链实证）→事实POST 409 `facts_mapping_incomplete`×3（T1时效窗机制现场生效：stage-state出`retry_generate_facts`可用键）→R32-04重跑EX（第2次尝试）成功→事实仍409：**事实门按已确认修订字段判全表列覆盖，整域缺口不被容忍；已确认草稿不可变；重新采纳409 mapping_draft_conflict（源集已变须新批次）**。SM1(10-16)同点停滞，系同因。驱动已改按正确用户流：确认前先重跑失败分片 |
| Round2 | 4403e7ad1d7a / stg-c961dea0… | ✅**全链从零走通**：建项19:35→上传→身份门(用户确认归属)→文档链ready 20:08→识别20:09-20:53（candidates_ready，0失败，60字段）→采纳→对账（46分歧题逐个AI复核作业）→16题作答→对账收敛46/0→**确认非降级02:52**→事实201 ready 02:53→运行(daily/full)02:56→发布200→结果entry/overview 200→stage-state `current_stage=complete, blocking=[]`。事件流125条导出 |
| Round3 | 57fe3b136c9a / stg-d46c7798… | ⏳进行中：身份门+**角色裁决needs_user_input**（ecrf角色用户选文件，§1.2变迁现场首次出现）→文档ready→识别candidates_ready（0失败）→采纳→2题作答→对账46疑点推进中（记录时点02:31启动） |
| Round1b | 2edc1e9be2cd / stg-ce0d34e1…（round1项目新批次，产品出口路径） | ⏳进行中：文档复用已晋升→识别candidates_ready（0失败，retry-before-adopt生效）→采纳→2题作答→对账中 |

### M4覆盖项实测
- R11-01（infra失败→同请求重发→requeued）：**现场未自然发生**（三轮全部失败均为内容级invalid_ai_output，按设计不自动重排）——该行为由env-on单测锁定，本窗口无活体点燃，如实记录。
- facts失败→retry_generate_facts可达（T1/M1修复链）：✅round1现场观测（stage-state blocking出可用键）。
- F5恢复+哨兵不误伤：✅（见§17）。
- M2 gate_blocked活体写入：未触发（本窗口无「映射未确认即点开始运行」动作），5/5单测在档，如实记录。

### M4过程发现（只记录，不在本专项修）
1. **身份门确定性命中**：三件套在新项目上无论项目名是否与方案一致，首次resolve恒`project_mismatch`→「确认属于当前项目并继续」是真实用户路径（三轮同此）。
2. **部分采纳死链**（round1，产品级断点）：见上表。
3. **对账重算CPU饱和**：并发两轮adjudicate时8911进程CPU 97-102%（GIL单核），单次confirm/adjudicate POST可达15分钟+（客户端超时两次）——R7-01线程池压力的CPU级佐证；缓解=轮次串行化，未改码。
4. **分歧题文本写入user_action**：双盲分歧卡的问题文本存于字段`user_action`（前缀`系统两轮独立复核对本字段结论仍不一致…`），未决判定必须用「用户已确认：/用户已核对：」前缀规则（与confirm侧`_decision_recorded`同源）——API消费方不能把「有文本」当「已作答」（驱动初期bug，修正后round1/2/3全通）。
5. 项目列表「读取失败」一次（AI高峰期已知现象，重载恢复）。

## 17. 界面冒烟（经5178界面非API，ego-browser实测）
- 常驻项目 MX循开考-CSU → 医学监查 → 开始一次新的监查 → 四步向导走通：第2步「10表/591行/3038值100%往返校验」、第4步「确认并开始监查」**disabled:false**（可点）；**未点击最终开始按钮**（常驻项目预置态保留，与既往冒烟纪律一致）。
- F5恢复+哨兵（round1项目界面）：向导挂载→stage-state权威恢复直落第3步「研究文件与字段映射确认」、忙态「正在确认字段对应关系…」无哨兵按钮；页面reload后重开向导仍恢复第3步，哨兵零误伤。
- 如实：项目列表首载一次「读取失败」（重载成功）；截图CDP超时未取得，DOM断言为证。

## 18. 回滚

M1/M2：单提交revert。M3：env置空重启=零缓存路径逐字还原（A/B实测）；可选`DROP TABLE monitoring_document_authority_verdicts`归零。M4：非代码步；驱动/证据为增量文件可整体移除。权威schema依旧零迁移。已落地回滚面与v2§11一致。

## 19. 如实偏差与未尽事项
1. M3延迟预算未达标（14.5s vs 个位数秒级）：归因在案（A1全量重读+manifest/图库churn+A3复查），按设计R4如实记录不放松，缓存保留启用。
2. M4三连未在本窗口完成3/3：round2全通✅，round1确认后卡事实门（产品断点，非状态机回归），round3/1b对账进行中（journal留痕可续证）。专项完成定义（M4三连全通）未达成，不得宣称「专项完成」。
3. R11-01与gate_blocked无活体点燃（见§16覆盖项）。
4. 本会话未改M3归因指向的S8范围外热点（A1重读等）——超出状态机专项最小根因边界，另行立项。
5. `01_STATEMAP.md`/`02_DESIGN.md`工作区v3覆写与runs/*运行时json差异均为会话前已存在，本次未触碰不纳入提交（沿v2留痕惯例）。

## 20. 一句话结论

v3四步中M1（红测试修复）/M2（gate_blocked留痕）/M3（缓存启用+等价性+活体失效链+延迟不达标如实归因）三步完成并各自可回滚，M4以幂等驱动跑通**首个全链从零E2E（round2：确认非降级→事实→运行→发布→结果视图）**并暴露两个真实产品断点（部分采纳死链/身份门必经用户确认）；回归门151 passed与基线逐字一致，常驻项目冒烟+F5+哨兵全过——「单一权威状态模型」在真实从零负载上的行为与设计一致，E2E三连收官仍差round3/1b对账收敛（留痕可续）。
