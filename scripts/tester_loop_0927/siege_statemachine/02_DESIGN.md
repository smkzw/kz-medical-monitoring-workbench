# 02_DESIGN — 第3步单一权威状态模型设计 v3（状态机重构专项·as-built 规范与剩余收口）

> 设计日期：2026-10-17。前置底稿：同目录 `01_STATEMAP.md`（v3 考古报告，本设计沿用其 A/B/C/D 状态持有者编号）、本文件 v1（2026-10-14，S1-S7 原始设计）与 v2（2026-10-15，T1-T7 收口设计；已提交于 git `e3820cc1`，工作区版本被本 v3 覆写）。
> 版本沿革：v1 设计并实施 S1-S7（`e61d2067`→`1b9a84fb`）；v2 设计 T1-T7，其中 **T1-T6 已全部实施**（`9eee3331` T1 / `49f9ad79` T2 / `286e037a` T3 / `3e81e2f6` T4 / `454edef0` T5 前置测试 / `2d411755` T6=S8 缓存，git log 本次实读）；**T7（E2E 三连从零）如实未执行**（`557707df` 提交信息原文），其后四笔 E2E 拦截修复（`1f60d357`/`fdcf827f`/`bda88a45`/`6a3d4c3d`）继续在档。v1/v2 全部权威裁决（权威不动/物化补缺/投影单源/门不读物化行）**保留，v3 不推翻任何一条**。
> 依据：本 v3 实际读取的代码（全部引用带 `file:line`，出自本次 Read/grep/sed 输出，代码根 `implementation/workbench`，git HEAD=`6a3d4c3d` 本次 `git rev-parse` 实读）+ 本 v3 实际运行的检查（§6 诚实清单，含一条**红测试**发现）。

---

## 〇、v3 先读：主结构已建成，剩余收口收敛为四步

v2 设计的 T1-T6 已全部落地（本会话逐项代码实证，见 §1-§3 引用）；「单一权威状态模型」的**权威存储+物化行+事件流+单源投影+stage-state 出口+F5 权威恢复+失败不缓存+降级入口服务端化+阻塞组载荷+前端哨兵**在生产形态上全部成立。逐项复核后，剩余真缺口收敛为四件：

| # | 缺口 | 证据（本 v3 实测/实读） |
|---|---|---|
| N1 | **T1 装配侧测试是定时炸弹，当前基线红（81 passed / 1 failed）**：`test_assemble_stage_state_passes_window_flag` 用固定 `NOW=2026-10-15 12:00 UTC`（`tests/test_facts_recent_failure_window.py:31`），而 `_assemble_stage_state` 调 `facts_recent_failure_from_events` **未注入 now**（`mapping_candidate_routes.py:1027-1031` 无 `now=` 实参→真钟 2026-10-17），事件距 NOW 48h>24h 窗→`generate_facts`≠`retry_generate_facts` 断言失败。**生产逻辑正确，测试缺时钟注入口**——该测试在实施当日（10-15）绿、10-16 12:01 UTC 起必红，`9eee3331` 声称的 7 绿已不可复现 | 本会话实跑：`pytest tests/test_facts_recent_failure_window.py::test_assemble_stage_state_passes_window_flag` → `AssertionError: assert 'generate_facts' == 'retry_generate_facts'`（§6 检查#1） |
| N2 | **S8 verdict 缓存建成未启（0 行），逐请求重放成本在链上**：8911 进程 env 无 `WORKBENCH_DOCUMENT_VERDICT_CACHE`（本会话 `ps eww -p 24250` 实读仅命中 `WORKBENCH_MONITORING_AI_INFRA_RETRY=1`）；verdicts 表 0 行（本会话 sqlite 只读实查）；stage-state 首探 120s 超时/重试 241.5s、mapping-candidates 9.4-20.3s（01_STATEMAP v3 §四#4-#8，本会话未重采样）；前端因此**明确不做周期轮询**（`MedicalMonitoringAdmissionWizard.jsx:2322-2324` 注释原文「端点documents阶段回放成本未收口前不做周期轮询」） | `monitoring_ai_repository.py:749-757`（env 默认 off）、`:560`（DDL）、`monitoring_document_evidence.py:60-66`（缓存开关）；本会话 sqlite 实查 verdicts=0 行 |
| N3 | **E2E 三连从零门未闭环**：T7 未执行（`557707df`），两轮拦截修复后（末笔 `6a3d4c3d`：整域缺口确认链死锁）门现状不明。01_STATEMAP v3 §〇.5 如实声明「本会话未运行 E2E，无从独立判定」 | git log 本次实读 + 01_STATEMAP §冲突5 |
| N4 | **gate_blocked 事件类型零写点**：schema 预留六类事件（`monitoring_admission_stage_store.py:38-53`），但 `rg` 全仓 `gate_blocked` 无任何 `append_event` 写点——B5 门 409 `mapping_confirmation_required` 不落任何事件，运行启动被阻断在事件史里不可查（44 轮取证痛点：`1f60d357` 提交信息自述此前 confirm 链 409「50分钟零服务端痕迹」） | 本会话 rg 实测：仅 store 常量定义与无关的 result/publication 命中，无写点 |

另两项维持「明确不做」裁决（v2 已立，v3 重申）：**A5 批次状态机不入库**（T2 事件留痕已满足审计取证；A5 文件态是 44 轮验收过的权威）；**C7 主按钮不整体接管 `primary_action_key`**（T4 哨兵已补死锁最后一公里；整体接管会回退四轮实测验收的细分 UX）。

---

## 一、权威状态表/事件流定义（as-built 规范）

### 1.1 权威归属与状态枚举总表

一句话总纲：**权威原位四组不动（A2 jobs+drafts / A4 facts / A1+A3+A5 文档三件套），识别聚合态物化进 A2 同库附加两表（状态行+事件流），documents/mapping 两阶段只留事件不留行（行=第二份权威），B0 纯函数是冲突字段唯一写点，stage-state 是跨阶段聚合唯一出口，运行门 B5/B6 永不读物化行，前端本地态全部降为只读渲染投影+死锁哨兵。**

| 阶段 | 权威（判定只读它） | 权威状态枚举 | 物化状态行 | 事件留痕 |
|---|---|---|---|---|
| documents | A1 `source_registry.jsonl`（promoted+receipt）+ A5 批次文件态（CAS+flock）+ A3 校验库；投影经 `pipeline.document_readiness` | A5 批次：analyzing/reviewing/adjudicating/cross_checking/promoted/needs_user_input/failed | **不建行**（stage_state PK=project+attempt+stage，批次无 attempt 归属；建行=第二份权威） | ✅ T2：16 处埋点（`monitoring_document_authority_workflow.py:258,266,347,373,398,473,552,576,602,668,695,721,793,815,840`），经 `_record_stage_event:71`→`append_event_autonomous`（best-effort，attempt_id='' 项目级） |
| recognition | A2 `monitoring_ai_jobs` 行级七态：queued/running/completed/failed/blocked/stale_input/cancelled | 聚合四态：not_started/candidates_ready/needs_attention/generating（`aggregate_recognition_state`，`monitoring_admission_stage_store.py:178-190`——B1 派生、物化行、回填三处同一函数） | ✅ 建行（聚合态在 A2 原本不存在，物化=补唯一缺口），随作业写点**同事务** bump（S2 实施超集：create_or_get/complete/fail/mark_stale/dwell 收割/租约耗尽/退役族/retry_terminal） | ✅ state_changed / failure_recorded（failure_class 经 `failure_class_for:157-167` 三分 infra/content/contract）/ recovery_action |
| mapping_confirmation | A2 `monitoring_mapping_drafts`（draft→confirmed 两态；version CAS + confirmed 不可变触发器） | no_draft/draft_active/confirmed（权威 drafts 行 status 即状态行） | **不建行**（drafts 行本身即状态行） | ✅ T3：upsert（`monitoring_mapping_draft_repository.py:945`）、编辑/规范化、confirm（`:2132-2154`）四个 CAS 写点与 draft 写**同事务**埋事件（attempt 键=batch_id）；部分采纳（域/槽位豁免）与降级确认另记 degradation（`:1324`、`:2154`） |
| facts | A4 `canonical_fact_materialization` 域对象（not_generated/ready；失败不落持久失败态） | not_generated/ready（失败态只存在于事件流的时效窗里） | best-effort 镜像行（`main.py:4334-4372`，docstring 明示「A4提交是权威；此函数只维护stage_state.facts行」） | ✅ state_changed(ready) / failure_recorded（T1 修后 failure_class 经 `failure_class_for` 分类，`main.py:4365-4369`） |

**关键不变量（fail-closed，任何改造不得放松）**——`packages/medical_monitoring/admission/admission_stage_view.py`：
1. 顶层 state：materialized 读物化行→行缺失且有 cohort 作业→权威回填（回填真值 1f60d357 修复）→仍缺→`AdmissionStageViewError("mapping_bridge_failed")` 500（`:163-175`）；
2. 自救形态（current_stage 处 failed/needs_attention/needs_user_input 或映射未确认）的 blocking 条目无 action_available 键→500（`:339-346`）；动作键不在 `STAGE_ACTION_KEYS` 枚举→500（`:347-349`）；
3. 冲突1四字段（state/confirmation_status/facts_generated/pending_confirmation_count）唯一写点=`apply_single_source`（`:139-215`）；
4. 运行门永不读物化行：B5 直读 drafts（`main.py:1161-1192`，confirmed→放行否则 409 fail-closed）、B6 直读 A4——投影与门分离是 fail-closed 的根基。

### 1.2 变迁矩阵（谁写/条件/事件）

**recognition（同事务，权威行与事件原子）**

| 变迁 | 条件 | 写入方 | 事件 |
|---|---|---|---|
| not_started→generating | cohort 分片入队 | `create_or_get`（S6 开启时命中 infra 终态失败行则先重排，见 §3.1） | state_changed + bump_stage |
| generating→candidates_ready | 最后一片 completed | `complete` | 同上 |
| generating→needs_attention | 全部作业终态且存在失败 | `fail`/`mark_stale`/dwell 收割/租约耗尽/退役族 | failure_recorded（class 经 failure_class_for）+ 物化 |
| needs_attention→generating | retry_terminal 显式重试（含 S6 自动重排，actor=user） | `retry_terminal` | recovery_action + 物化 |

R19-01 契约不变：任何作业未终态→一律 generating（`mapping_pipeline.py:2255-2262` 注释原文），前端按钮态与后端校验同源。

**mapping_confirmation（同事务，事件随 drafts CAS 写）**

| 变迁 | 条件 | 写入方 | 事件 |
|---|---|---|---|
| no_draft→draft_active(v1) | adopt：candidates_ready 全量 / needs_attention 部分 / generating 且双标志降级（`mapping_confirmation.py:592-604`：`allow_inflight_adoption` AND 服务端 `inflight_adoption_available`） | `adopt_draft`→仓 upsert | state_changed；降级另记 degradation |
| draft_active vN→vN+1 | 逐字段编辑/裁决（CAS expected_version） | 仓 edit 族 | state_changed |
| draft_active→confirmed | 疑问全答+双盲复核收敛或知情降级 | 仓 confirm（status='confirmed'，幂等重放不重复落事件） | state_changed；降级另记 degradation |

**documents（best-effort 独立事务，A5 文件态权威写成功之后落）**

| 变迁 | 条件 | 写入方 | 事件 |
|---|---|---|---|
| →analyzing | 上传/重传创建批次 | `workflow.start` | state_changed（重传重排另记 recovery_action） |
| analyzing→reviewing→adjudicating→cross_checking | advance 推进 | `advance` 各分支 | state_changed / recovery（失败自动恢复） |
| →needs_user_input | 身份/角色/内容裁决挂起 | `advance` | state_changed（reason_code=identity/role/content） |
| →failed | 终态失败聚合 | `advance` | failure_recorded（class 经 failure_class_for） |
| →promoted | 晋升链写 A1 事务提交后 | promote 链 | state_changed |

**facts（跨库 best-effort，A4 提交之后）**

| 变迁 | 条件 | 写入方 | 事件 |
|---|---|---|---|
| not_generated→ready | A4 物化提交成功 | `_record_facts_stage_state`（`main.py:4344-4360`） | state_changed + bump(ready) |
| （无状态变化） | A4 生成失败 | 同上（`:4361-4369`） | failure_recorded（reason_code + failure_class） |

facts 失败的**用户出口**=`facts_recent_failure` 时效窗（`mapping_candidate_routes.py:79-113` 纯函数：最近 failure_recorded 晚于最近 ready 且 24h 内→True）→ blocking 条目动作键 `generate_facts` 升级为 `retry_generate_facts`（`admission_stage_view.py:318-322`）——失败不是终态，是 24h 内可重试的入口。

### 1.3 事件流 schema 与写入纪律（as-built）

- 两表 DDL：`monitoring_admission_stage_store.py:83-118`（同文件 `medical_monitoring_ai.sqlite3`，`MonitoringAiRepository._initialize` 幂等建表）；事件表 append-only，no_update/no_delete 触发器（`:102-105`）；状态行 PK=(project, attempt, stage)，revision 行级单调自增（`bump_stage:299-343`）。
- 六类事件：state_changed/failure_recorded/recovery_action/degradation/gate_blocked/stage_view_divergence（`:38-53`）。**现状写点覆盖**：前五类中 gate_blocked 无写点（N4）；stage_view_divergence 写点=S2 影子比对（`mapping_pipeline.py:2161`，STAGE_VIEW_MODE=materialized 默认下恒跳过，保留为 derive 回退路径）。
- 写入纪律：A2 内写点传外层 conn 同事务；跨库点（A4/A5）用 `append_event_autonomous`（`:259-297`，独立事务+吞异常）——**留痕完整性 < 权威正确性，事件故障绝不外泄**；detail 禁作业身份/载荷。
- 本会话只读实测（8911 runtime 库）：stage_state 行=recognition 14 + facts 6（documents/mapping=0，与「只留事件不留行」裁决一致）；事件分布=state_changed 622 / failure_recorded 36 / recovery_action 31 / degradation 6 / gate_blocked 0 / divergence 0（**漂移 0 条=影子期零漂移**）。T2/T3 实施后事件总量从 v2 的 411 涨到 695，documents/mapping 取证缺口已实闭。

---

## 二、现有各投影的改造清单（从哪读权威 / 本地推导删除点现状）

| 投影 | 从哪读权威（as-built，本会话实读） | 本地推导删除点（已删/剩余） |
|---|---|---|
| **B0** `admission_stage_view.apply_single_source`/`build_stage_view` | 纯函数无 I/O；入参即权威值（物化识别行/drafts 权威行/A4 直查值/facts_recent_failure） | **唯一写点已成立**（S3）。剩余：无（`facts_recent_failure` 参数已由 T1 接线实传，`mapping_candidate_routes.py:1047`） |
| **B1** `mapping_pipeline._project` | 派生 state=`aggregate_recognition_state` 单源（`mapping_pipeline.py:2260`）；pace=服务端 `_generation_pace`（R44-02）；`inflight_adoption_available` 服务端停滞窗（`:2273-2279`，`RECOGNITION_INFLIGHT_STALL_SECONDS` 于 `:64`） | 已删：字段级/顶层 confirmation_status、pending 计数硬编码（S3）。**保留**：影子比对 `_shadow_compare_recognition_state` 在 materialized 下恒跳过——作为 derive 回退路径保留至 E2E 门通过（M4）后再评估删除 |
| **B2/B3** `enrich_candidates`/`list_for_review` | facts_status=A4 直查（resolver 注入）；draft 权威行；识别行经 `_recognition_state_row`（缺失回填） | 已删：无条件 facts_generated=False 与 confirmed 覆盖（S3）。剩余：无 |
| **B4** `MonitoringDocumentEvidenceResolver` | A1 逐条目 receipt 完整性（廉价、**永不缓存**）→promoted 才进 verifier 重放（指纹命中跳过，S8 拆分链）+A3 校验+locator 比对 | 结构已到位（T6：`monitoring_document_evidence.py:98-182` 双路径）。剩余：**仅启用决策**（M3，env `WORKBENCH_DOCUMENT_VERDICT_CACHE=1`） |
| **B5** 运行确认门 `main.py:1161-1192` | 直读 `latest_draft_for_project`（project 维度），confirmed→放行，否则 409 fail-closed | **零改动**（R18-03 保护）。与向导 `find_draft_for_batch` 双键并存由 `confirmation_scope` 显式披露（`admission_stage_view.py:97-136`，superseded_by_newer_attempt 形态在案）。剩余（可选，M2）：409 时补 gate_blocked 事件留痕 |
| **B6** 事实就绪门 | 直读 A4 + `latest_attempt_id` 与投影共享（S4 收编） | 零改动。剩余：无 |
| **B7** stage-state 端点 `mapping_candidate_routes.py:1936-2007` | 四阶段装配 `_assemble_stage_state:884-1048`：documents←document_readiness；recognition←物化行（缺失回填）；mapping←drafts 权威行；facts←A4 直查；facts_recent_failure←事件流时效窗（T1）；If-None-Match→304（`:2000-2006`） | 剩余（M1）：装配函数加可选 `now` 注入口修红测试（生产行为零变化） |
| **C1/C3** 向导壳/确认态机（前端） | 挂载 stage-state 一次权威查询恢复（S7：`MedicalMonitoringAdmissionWizard.jsx:2284-2310`）；确认态读 S3 单源字段 | C2 localStorage 已删（S7）。剩余：无（advance/back 为 UI 导航态） |
| **C4/C5** 文档/事实本地态 | 载荷已来自权威投影（document_readiness/A4）；子形态细分保留 | 无替换；死锁兜底由哨兵承担 |
| **C6** 在途防重入+哨兵快照 | `stageState` 权威快照（`:2312-2336` 挂载+映射面板静默禁用态一次重读，**非轮询**——注释明示回放成本未收口前不做周期轮询） | 剩余：M3 落地后可评估轻量轮询（届时另行设计，本设计不承诺） |
| **C7** 主按钮+哨兵 | 主按钮仍本地合成（保留，四轮验收 UX）；死锁哨兵 `stageSentinelAction`（`medicalMonitoringAdmissionWizardState.mjs:618-651`）消费权威 blocking[]：仅「本地无任何可用控件且非 busy」而权威携带 action_available=true 时产出，映射到既有 handler | 剩余：无（整体接管 primary_action_key 维持不做裁决） |

---

## 三、死锁家族根治点（as-built 判定 + 残余处置）

### 3.1 失败态永不缓存复用 —— 判定逻辑在库，本环境灰度已开；残余=观察窗+场景复验

- as-built：R11 判据下沉为库层不变量 `_is_requeueable_infra_failure`（`monitoring_ai_repository.py:896-915`：终态失败 failed/blocked/stale_input + failure_code∈INFRA_FAILURE_CODES + 无契约退役）；`create_or_get` 命中时按显式重试语义 `retry_terminal`（actor=user、不受自动预算约束、StateConflict 竞态回落 fail-safe，`:917-945`）。调用点唯一漏斗=`MonitoringAiService._create_job`（docstring 在案 `:880-893`）。content/contract/退役/输入指纹变化**一律不重排=按设计保持 fail-closed**（内容性失败复用旧结论才是 R11-01 死锁本体）。
- 灰度现状：8911 进程 env `WORKBENCH_MONITORING_AI_INFRA_RETRY=1`（本会话 `ps eww -p 24250` 实读）；叠加交互已测（`454edef0`：重排行 dwell 基线重置不被二次收割、在途豁免等待钟重置）。
- 残余处置：并入 M4——E2E 三连期间 R11-01 场景实测（infra 失败→同请求重发→requeued）+ 一个完整识别周期观察无收割异常。回滚=env 置空，生产行为逐字还原（T5 已验证 env off 复跑零行为差）。

### 3.2 降级入口（「采用已识别字段继续」）何时出现 —— 服务端单源判定，门禁零放松

- 出现条件（唯一权威判定，`mapping_pipeline.py:2273-2279`）：state==generating **且已有候选** 且服务端 pace 窗口末次完成距今 > `RECOGNITION_INFLIGHT_STALL_SECONDS`（30min）→ 投影顶层 `inflight_adoption_available=true` → blocking 出 `adopt_inflight_degraded` 可用键（`admission_stage_view.py:398-403`）。
- adopt 门双标志（`mapping_confirmation.py:592-604`）：前端显式标志 AND 服务端标志，缺一仍 422 `mapping_run_incomplete`——R19-01「未终态一律 generating→拒绝」默认契约不变；降级采纳把未完成分片按部分采纳同规约排除出草稿并物化缺口记录。
- needs_attention 形态的 `adopt_partial` 恒可用（`admission_stage_view.py:392-397` action_available=True）。
- 残余：无结构残余。前端 30min 本地计时仅提示 UI，不再决定可用性。

### 3.3 阻塞组（「还有N组待处理」）必有处理入口 —— 数据面+不变量面+前端哨兵三层

- 数据面：R41-01 载荷随投影下发 rule_id/affected_fields/role_catalog（`mapping_candidate_routes.py:696-731` 注释原文「处置入口才真实存在」）。
- 不变量面：blocked_group_count>0→`resolve_blocked_groups` action_available=true（`admission_stage_view.py:424-429`）；自救形态无可用键→500 fail-closed（`:339-346`）——**死锁形态宁可 500 暴露缺陷也不渲染死锁文案**。
- 前端哨兵（T4）：本地失步仍可能渲染无控件页面——`stageSentinelAction` 以权威 blocking[] 为兜底动作源（`medicalMonitoringAdmissionWizardState.mjs:618-651`），busy/有控件/主按钮可用/complete 恒 null 不误伤。
- 残余：无。回归在档：`tests/test_stage_state_endpoint.py::test_deadlock_shapes_always_yield_actionable_key`（本会话随 13 文件套件实跑通过）。

### 3.4 F5 后状态恢复 —— 已根治（S7+T4 快照）

- as-built：C2 localStorage 删除；挂载时 `getDataAdmissionStageState` 一次权威查询，current_stage 越过 documents 即 advance（`MedicalMonitoringAdmissionWizard.jsx:2284-2310`）；恢复失败静默从文档面板开始、权威可再查（`:2309`）；304 支持在档（`mapping_candidate_routes.py:2000-2006`）。
- 残余：恢复质量受 N2 性能缺口制约（首探 120s 超时期间用户白屏等待）——M3 落地即解，无需改恢复逻辑本身。

---

## 四、分步迁移路径（每步可独立验证 + pytest，顺序即依赖序）

**基线（本 v3 实际运行，§6 检查#1-#4）**：
- 专项 13 文件套件：`.venv/bin/python -m pytest tests/test_admission_stage_events.py tests/test_stage_state_recognition.py tests/test_projection_single_source.py tests/test_gate_lookup_key_consistency.py tests/test_inflight_adoption_server_flag.py tests/test_infra_failure_not_cached.py tests/test_stage_state_endpoint.py tests/test_confirm_verifier_deadlock_fix.py tests/test_admission_stage_documents_events.py tests/test_admission_stage_draft_events.py tests/test_facts_recent_failure_window.py tests/test_document_authority_verdict_cache.py tests/test_infra_requeue_dwell_interaction.py -q -p no:cacheprovider` → **81 passed / 1 failed（N1 红测试）**
- 回归门：`.venv/bin/python -m pytest tests/medical_monitoring -q -p no:cacheprovider` → **151 passed**
- 前端：`node --test src/features/medical-monitoring/medicalMonitoringAdmissionMappingConfirmState.test.mjs src/features/medical-monitoring/medicalMonitoringAdmissionWizardState.test.mjs` → **34 pass / 0 fail**（wizardState 文件为单 runner 内含 ~110 checks，其中哨兵 11 checks 全绿）

| 步 | 内容 | 验证（命令级） | 回滚 |
|---|---|---|---|
| **M1 修 N1 红测试（时钟注入）** | `_assemble_stage_state` 增可选 kwarg `now: Optional[datetime] = None`，透传 `facts_recent_failure_from_events(..., now=now)`（`mapping_candidate_routes.py:1027-1031`）；测试改经 `mcr._assemble_stage_state(..., now=NOW)` 传入固定钟。**生产行为零变化**（缺省=None→真钟=现状）；纯函数与写入侧测试不动 | 同上三条基线命令 → 13 文件套件 **82 passed / 0 failed**；其余两门数字不变 | revert 单提交；参数缺省=现状 |
| **M2 gate_blocked 留痕（N4，可选但建议）** | `_r7_mapping_confirmation_gate`（`main.py:1161-1192`）返回 409 dict 前，经 `monitoring_ai_repository.stage_store.append_event_autonomous(project_id, attempt_id='', stage='mapping_confirmation', event_type='gate_blocked', reason_code='mapping_confirmation_required', detail={'draft_status': …})`——best-effort 吞异常，门判定路径零变化、永不读物化行 | 新增 `tests/test_gate_blocked_event.py`：未确认 draft 调门→事件存在且六字段正确；事件写故障→门仍正常 409（吞异常）；幂等（同请求重复触发允许多条，门是求值不是变迁——如实记录每次阻断）。跑 13 文件套件+151 回归门 | revert 单提交；事件表留存无害 |
| **M3 S8 verdict 缓存启用（N2）** | 前置①：S8 等价性 9 测试实跑全绿（`tests/test_document_authority_verdict_cache.py`，本会话已在 81 passed 内）。前置②：隔离 runtime 同项目 A/B——`WORKBENCH_DOCUMENT_VERDICT_CACHE` off/on 各采样 GET study-documents + stage-state + mapping-candidates，断言响应体 JSON 等价（缓存只加速不改判定）+ 记录延迟。前置③：失效链实测——注册新文件（registry_revision 变）与重放被引作业行（digest 变）后缓存必 miss。然后置 env=1 重启 8911，复测三端点延迟并记录 ISO_ENV_LOG | 等价性断言脚本输出在案；延迟对比表在档；**验收预算：stage-state P95 回到个位数秒级（v2 实测 19.9s 为参照上限）**——若 M3 后仍不达标，如实记录并转剖析采样（不达标不许把超时改成 fail-open） | env 置空即回直连重放（读写均不发生，T6 验证零缓存路径）；必要时 `DROP TABLE monitoring_document_authority_verdicts` 归零 |
| **M4 E2E 三连从零门 + S6 观察窗关闭（N3，专项完成定义）** | 以 `scripts/fullchain_sar_rerun_20260926/` 幂等脚本为底座，从零路径（真实上传三件套）连续 3 次「建项→上传→核对→识别→映射确认→事实→运行→发布→结果」全通；期间覆盖：R11-01 场景（infra 失败→重发→requeued）、facts 失败→retry_generate_facts 可达（T1/M1 修复链）、F5 恢复、哨兵不误伤 | 每轮 run 日志+stage-state 事件流导出（T2/T3/M2 事件史可直接回答「卡在哪一步」）；**此门通过前不删 B1 影子比对死代码**；通过后才评估 derive 回退路径与 C6 轮询 | 非代码步；失败按 04_E2E_FAILURE_DIAGNOSIS 三分归因（桥/上游/状态机） |
| **不做（维持裁决）** | A5 批次状态机入库（文件态是验收过的权威，T2 事件已满足取证）；C7 整体接管 primary_action_key（哨兵已补最后一公里）；B5 门与 find_draft_for_batch 键合并（S4 披露替代，多 attempt 并存常态化时按 confirmation_scope 驱动门判定再重访） | — | — |

---

## 五、风险与回滚

| # | 风险 | 缓解 | 回滚 |
|---|---|---|---|
| R1 | M1 注入口被未来调用方误用（传错 now 导致窗口判定漂移） | kwarg 仅测试消费；缺省 None=真钟=现状；纯函数 `facts_recent_failure_from_events` 已有 4 个直接单测锁语义（本会话实跑通过） | revert 单提交 |
| R2 | M2 事件写放大（每次运行启动被阻断都落一条） | gate 求值是低频人工动作（运行启动），非轮询路径；append_event_autonomous 吞异常不外泄；90 天归档纪律沿用（>90 天导出 JSONL 后清理，导出即留痕） | revert；DROP 事件行可选 |
| R3 | M3 缓存脏读（失效键遗漏→陈旧 verdict 放行文档） | 失效键绑两个可变源（registry_revision=A1 全条目指纹 / cited_job_digest=被引作业行+候选行摘要，`monitoring_ai_repository.py:560-566` DDL）；receipt 完整性**永不缓存**（廉价先判，S8 拆分链 `monitoring_document_evidence.py:98-182`）；等价性 A/B 是启用前置门；灰度 env 起步 | env 置空=零缓存路径逐字还原；DROP TABLE 归零 |
| R4 | M3 后延迟仍不达标（瓶颈另有其处，如 A7 画像缓存或 A1 JSONL 全量重读） | 验收预算显式写明；不达标**不许**用 fail-open 超时或跳过 documents 阶段装配放松 fail-closed；转剖析采样（01_STATEMAP v3 §〇.4 如实声明归因未证实） | env off 回滚无损 |
| R5 | M4 期间 S6 重排与收割叠加外溢（重排队列放大/饿死真失败） | 判据四类边界（content/contract/退役/指纹变化）库层不变量不放松；`454edef0` 交互测试在档；观察窗异常即 env 置空 | env 置空，逐字还原 |
| R6 | 红测试长期滞留掩盖真回归（N1 不修，后续任何红都先怀疑定时炸弹） | M1 是第一步且最小；修后 13 文件套件恢复全绿基线，后续红=真信号 | — |
| **总原则** | 权威 schema（A1/A2 jobs+drafts/A4/A5 文件态）**任何一步都不改不迁**；M1-M2 纯附加；M3 新表已建纯启用；全部事件写入维持「留痕完整性 < 权威正确性」 | — | 已落地部分回滚面：`STAGE_VIEW_MODE=derive`（投影回派生）、`WORKBENCH_MONITORING_AI_INFRA_RETRY` 空（失败不重排）、`WORKBENCH_DOCUMENT_VERDICT_CACHE` 空（零缓存）+M1/M2 组件级 revert，即全部归零 |

---

## 六、诚实清单（本 v3 实际做了什么、没做什么）

**实际执行（本次会话，2026-10-17）**：
- 读：`01_STATEMAP.md` v3 全文、`02_DESIGN.md` v2 全文、`03_IMPL_attempt1.md`/`04_E2E_FAILURE_DIAGNOSIS.md` 仅确认存在与 git 提交信息、`HANDOFF_40ROUNDS_20261014.md` 全文；代码：`monitoring_admission_stage_store.py` 全文、`admission_stage_view.py` 全文、`mapping_candidate_routes.py:79-124,692-732,884-1048,1930-2008`、`main.py:1155-1200,4320-4400`、`mapping_pipeline.py:725-750,2185-2300`、`mapping_confirmation.py:586-614`、`monitoring_ai_repository.py:876-945`、`monitoring_document_evidence.py`/`monitoring_document_authority_workflow.py`/`monitoring_mapping_draft_repository.py`（grep 锚点行）、前端 `medicalMonitoringAdmissionWizardState.mjs:580-660`、`medicalMonitoringAdmissionWizardState.test.mjs:1-40,340-448`、`MedicalMonitoringAdmissionWizard.jsx:2278-2340`。
- 检查（命令与结果）：
  1. 专项 13 文件 pytest → **81 passed / 1 failed**（红=tests/test_facts_recent_failure_window.py::test_assemble_stage_state_passes_window_flag，断言输出原文在案）；
  2. 失败细节复跑 + 读测试/纯函数源定位根因（固定 NOW vs 真钟）；
  3. `pytest tests/medical_monitoring -q` → **151 passed**；
  4. `node --test`（confirm 33 + wizardState 1，共 **34 pass / 0 fail**）；
  5. `curl /api/runtime-readiness` → 200，`backend_build_id=api-4ca198219617fc39`（=HEAD 重启构建）；
  6. `sqlite3 -readonly` stage_state/事件/verdicts 分布（§1.3 数字）；
  7. `lsof`+`ps eww -p 24250` → env 仅 `WORKBENCH_MONITORING_AI_INFRA_RETRY=1`，`WORKBENCH_DOCUMENT_VERDICT_CACHE`/`STAGE_VIEW_MODE` 未设置；
  8. `git log -30`/`git rev-parse`（T1-T6 提交链与 HEAD）。
- M1-M4 为设计，改造代码未运行——M1 的 82-passed 预期、M2 的新测试、M3 的 A/B 等价性均为实施时验证项。

**没做/引用他源（不填猜值）**：
1. 未重采样 8911 三端点延迟（20.3s/9.4s/241.5s 引 01_STATEMAP v3 §四，标注「考古报告」；本会话只做了 runtime-readiness 轻探针）——M3 预算数字以实施时实测为准；
2. E2E 三连从零未运行（M4 执行项；`6a3d4c3d` 后门现状不明，如实继承 01_STATEMAP §冲突5 声明）；
3. `monitoring_document_authority_workflow.py` 16 处埋点与 `monitoring_mapping_draft_repository.py` 4 写点经 grep 行号证实存在，未逐行读全文（T2/T3 各自 6 测试在本会话 81 passed 内实跑通过，作为行为证据）；
4. `STAGE_VIEW_MODE` materialized 默认=代码默认+env 缺省推断（`ps eww` 未命中），非运行时行为实测；
5. 性能劣化归因（S8 关→B4 全量重放）沿用代码链推断（`document_readiness→_document_evidence_resolver` 直调已实读 `mapping_pipeline.py:728-744`），未做剖析采样。

---

## 七、一句话结论

第3步单一权威状态模型**主结构与四族死锁根治点已全部建成并经本会话逐项代码+数据实证**（四组权威原位不动、识别物化行+四阶段事件流 695 条、B0 唯一写点+stage-state 唯一出口+四条 fail-closed 不变量、失败不缓存灰度已开、降级入口服务端单源、阻塞组三层入口、F5 权威恢复+哨兵兜底）；v3 剩余收口只有四件事——**修红测试（M1）、gate_blocked 留痕（M2）、S8 缓存启用解性能债（M3）、E2E 三连从零门收官（M4）**——每步独立可验证、可单独回滚，权威 schema 依旧零迁移。
