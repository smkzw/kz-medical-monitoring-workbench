# 01_STATEMAP — 第3步状态机全量状态持有者地图 v3（状态机重构专项·考古底稿）

> 调查日期：2026-10-17。只读调查，未修改任何代码/数据（唯一写入=本文件；探针全部 GET / sqlite `-readonly` / `ps eww` / `wc -l`）。
> 版本沿革：v1（2026-10-14）=S系实施前基线；v2（2026-10-15）=S1-S7 实施后重验；**本 v3 = 独立第三次全量重验**：本会话对下述每一条代码引用与每一条轮次实证**逐条重读原文**，并对 8911 隔离环境重新探针（不复用 v2 测量值）。
> 调查范围：数据接入向导第3步（研究文件核对 / 字段识别 / 映射确认 / 事实物化）涉及的**每一个状态持有者**。
> 代码根：`implementation/workbench`（下述相对路径均以此为根）。git HEAD=`6a3d4c3d`（本会话 `git rev-parse`/`git log` 实读）。
> 隔离环境实测（本会话现场）：API `http://127.0.0.1:8911` 在线，`backend_build_id=api-4ca198219617fc39`（`/api/runtime-readiness` 实测；=HEAD `6a3d4c3d` 提交信息所载重启构建），runtime 根 `runs/tester_loop_iso_20260928/runtime/`。
> 依据链：HANDOFF_40ROUNDS_20261014.md 第四部分根因一（L55-56「第3步状态机没有单一权威源」）→ 三条已知线索全部在本会话重新定位到代码级证据（见下）。

---

## 〇、v2→v3 变化（2026-10-15 之后两天内发生的，本会话实读证据）

1. **S8/T6 verdict 物化缓存已从「延后」变为「已实施但默认关闭」**：A2 库新增第 23 张表 `monitoring_document_authority_verdicts`（sqlite_master 本会话实读 23 张用户表；DDL `monitoring_ai_repository.py:554-566`）；B4 核验链拆分（`monitoring_document_evidence.py:98-182`：receipt 完整性永不缓存→promoted 才进 verifier 重放，指纹命中跳过）；env `WORKBENCH_DOCUMENT_VERDICT_CACHE` 默认 off（`monitoring_ai_repository.py:753-758`）。实施提交=`2d411755`（git log 实读）。**本会话实测：该表 0 行 + 8911 进程环境无此变量（`ps eww` pid 24250）→缓存未启用，A8 逐请求重放成本仍然在链上。**
2. **S6 infra 失败自动重排已在本进程灰度开启**：`WORKBENCH_MONITORING_AI_INFRA_RETRY=1`（`ps eww -p 24250` 实读，唯一命中的状态机相关 env；`STAGE_VIEW_MODE`/`WORKBENCH_DOCUMENT_VERDICT_CACHE` 均未设置→materialized 默认 + 缓存关）。v2 记录的是「默认 off 生产行为零变化」；`557707df` 提交信息载明重启时已带 `INFRA_RETRY=1`。失败缓存复用（冲突3）的灰度状态由此从「off」变为「**本环境 on**」——判定逻辑 `monitoring_ai_repository.py:885-915`（仅「终态失败+infra失败码+无契约退役」可重排）。
3. **E2E 攻坚续有两笔修复提交**（git log 实读）：`bda88a45`（事实准备「一键准备全部主题」恒禁用=W04 引入的 `aiStatus` prop 全前端零生产者→面板自取 `/api/ai-gateway/status`）；`6a3d4c3d`（整域缺口部分采纳确认链死锁：confirm 恒 409 `mapping_verifier_job_failed`/降级恒 409 `mapping_draft_source_unavailable`；缺口计算前置+域级门豁免补齐）。该提交并自述：10-15 探测坏行 `monai_b0e1764e`（致 SM3 mapping-candidates GET payload-hash-mismatch 确定性失败）已 DELETE、事件流保留。**本会话未运行 E2E，无从独立判定 E2E 门现状。**
4. **本会话性能实测显著劣于 v2**（单次采样、非基准）：mapping-candidates GET 20.3s（冷）/9.4s（暖）【v2: 0.40s】；facts GET 9.3s；**stage-state 首探 120s 超时（HTTP 000）、重试 241.5s 完成**【v2: 19.9s】。响应本体全部正确（见第二节冲突1复核）。最可能成因=S8 缓存关（0 行）下 documents 阶段 `document_readiness`（`mapping_pipeline.py:729-744` 实读：直调 `_document_evidence_resolver`）走 B4 全量 A8 重放 × 台账增至 176 行（`wc -l` 实测，v2 为 168）——**归因是推断，未做剖析采样**；且 241.5s 样本期间存在我方并发探针（一次 9.4s mapping-candidates GET）轻度叠加。
5. **自 v2 起新增 3 个从零项目走通到 confirmed**（A2 只读实查）：`proj_user_e282a7e982b0`(MX循SM1) draft v1 仍 `draft`+recognition `needs_attention`；`proj_user_f5cbef8251cd`(MX循SM2-R2) 与 `proj_user_b6251f4adc51`(MX循SM3) draft confirmed v1+facts ready（2026-10-16）。stage_state 事件计数现值：state_changed 622 / failure_recorded 36 / recovery_action 31 / degradation 6（T2/T3 新增 degradation 类），`stage_view_divergence` 仍 **0 条**。

---

## 一、状态持有者全量清单（本会话逐条行号重验）

第3步四段流水线（文档核对→字段识别→映射确认→事实物化）的状态分散在 **9 个后端持久层 + 1 个纯函数单源投影层 + 8 个请求时推导者 + 6 组前端本地态 + 1 个URL路由层**。逐项如下（全部行号=本会话 `Read`/`rg`/`sed` 现读，非沿用旧稿）。

### A. 后端持久层（跨重启）

| # | 持有者 | 位置/结构 | 持有的状态 | 本会话证据（file:line） |
|---|---|---|---|---|
| A1 | **源注册表**（研究文件台账） | `runtime/source_registry.jsonl`（JSONL，RLock+临时文件+`os.replace` 原子替换） | 每个研究文件的注册条目：`parser_status`、`metadata.monitoring_authority_status`（promoted 与否）、内嵌 `document_authority_receipt`、spans | 存储类 `services/api/app/source_intake.py:468-470`（jsonl_path+RLock）、`:522-609`（锁文件+`os.replace`:609）；读取 `:623,638,660-669`；装配 `main.py:1094-1095`。**本会话 `wc -l`=176 行** |
| A2 | **AI作业台账+映射草稿库+阶段状态库+verdict缓存**（同一 sqlite `runtime/medical_monitoring_ai.sqlite3`，本会话实测 4.3GB、**23 张用户表**） | ①`monitoring_ai_jobs/attempts/candidates/evidence_reads/call_ledger/queue_control/payload_blobs/conversation_turns/deterministic_repairs`（识别+文档核对作业状态机：queued/running/completed/failed/blocked/stale_input/cancelled）；②`monitoring_mapping_drafts/field_sources/edit_operations/adjudication_receipts/revisions`（draft→confirmed 两态权威）；③`monitoring_mapping_project_state/activation_history/activation_operations/batch_bindings(+history)/binding_operations`；④【S1】`monitoring_admission_stage_state`（PK=project+attempt+stage）+`monitoring_admission_stage_events`（append-only，no_update/no_delete 触发器）；⑤【S8/T6 新】`monitoring_document_authority_verdicts`（**实测 0 行=缓存未启用**） | 表清单=本会话 `sqlite3 -readonly … "SELECT name FROM sqlite_master"` 实读 23 项；作业表 DDL `monitoring_ai_repository.py`（`create_or_get:914`）、stage 两表 DDL `monitoring_admission_stage_store.py:83-118`（触发器 `:102-104`）、verdict 表 `monitoring_ai_repository.py:554-566`；草稿五表 DDL `monitoring_mapping_draft_repository.py:966-1057`；stage_store 挂接 `monitoring_ai_repository.py:354` 与 `monitoring_mapping_draft_repository.py:917`（draft写点同事务埋事件 `:926-956`）。装配 `main.py:1125`（AI仓）、`main.py:1156-1158`（草稿仓，同文件）。**本会话实查：常驻项目 draft `monmapdraft_73abe5c6…` confirmed v80；jobs completed=44+failed=2；全库 jobs 9327 行；`monitoring_mapping_project_state` 0 行；stage_state 15+ 行（最高 revision 51，活跃至 2026-10-16）；stage_events 695 条（state_changed 622/failure_recorded 36/recovery_action 31/degradation 6）；`stage_view_divergence` 0 条；verdicts 0 行** |
| A3 | **内容校验记录库** | `runtime/source_content_validation_records/`（sqlite，三表） | 每个源文件 `use_status`、`technical_status`——文档绑定 current 的必要条件之一 | `services/api/app/source_content_validation.py:285-320`（records/state/idempotency 三表 DDL 本会话实读） |
| A4 | **事实物化域对象**（per-project） | `runtime/medical_monitoring_r7/<project>/runtime/monitoring_runtime.sqlite3` 域对象 kind=`canonical_fact_materialization`，按 attempt_id 键 | `state: ready/not_generated`、`facts_generated: bool`、行/值核验计数 | KIND 常量 `packages/medical_monitoring/admission/fact_materialization.py:36`；`status()` `:636-661`（未生成→`{"state":"not_generated","facts_generated":False}`:642；ready→`facts_generated`:675；摘要不匹配 fail-closed `facts_snapshot_digest_mismatch`:654）；`_public` `:663-685` |
| A5 | **文档权威工作流工作区文件**（per-project 文件态，**未入库**） | `runtime/medical_monitoring_r7/<project>/document_authority_candidates/`：`batches/`、`user_selections/`、`identity_overrides/`、`last_document_check_note.json`（CAS+flock） | 核对批次状态机 `analyzing→reviewing→adjudicating→cross_checking→(promoted/needs_user_input/failed)`；用户角色裁决版本链；身份确认覆写 | 状态迁移 `services/api/app/monitoring_document_authority_workflow.py`：analyzing `:261,274`、reviewing `:556-559`、adjudicating `:671-675`、cross_checking `:797,819`、needs_user_input `:477`、failed `:401-402,605-606,724-725`；文件态 `:879`（note）、`:919`（identity_overrides）、`:1031`（user_selections）、`:1410`（batches json） |
| A6 | **接入暂存 attempts**（per-project 文件态） | `…/admissions/`：`staging/<attempt_id>/`（内容寻址 manifest+文件）与事件流水 | attempt 存在性/完整性（第2步→第3步输入边界） | `packages/medical_monitoring/admission/staging.py:69`（STAGING_SCHEMA_NAME）、`:130-139`（manifest 内容寻址）、`:144-154`（StagingAttempt） |
| A7 | **字段画像快照缓存** | `runtime/` 内容寻址快照（manifest+snapshot 双文件，digest 校验） | 字段识别结果缓存命中/缺席 | `services/api/app/monitoring_ai_field_profile_cache.py:32-34`（类）、`:38-45`（cache_key） |
| A8 | **晋升回执可验证性**（绑定在 A1 条目 metadata；验证证据在 A2 不可变作业行） | promoted 状态写 A1；验证=对 A2 作业证据**逐次重放** receipt（S8 缓存在本环境 off） | `monitoring_authority_status="promoted"` + receipt | 验证入口 `source_intake.py:694-711`（`monitoring_authority_entry_is_verified`：receipt 完整→非 promoted 即真→promoted 走 verifier 重放）——**即任务书已知线索#1，本会话逐行重读确认**；B4 消费 `monitoring_document_evidence.py:98-182`（缓存开/关两路径逐字分支）；resolver 接线 `main.py:1149-1155`（verdict_store=AI仓） |
| A9 | **facts 阶段行（best-effort 镜像，非权威）**【S7】 | A2 库 `monitoring_admission_stage_state` 的 `stage="facts"` 行 | facts 跨库镜像（ready/failure）——A4 仍是唯一事实权威 | `main.py:4327-4360`（`_record_facts_stage_state` docstring 明示「A4提交是权威；此函数只维护stage_state.facts行」）；本会话实查该行存在（如 `proj_user_b6251f4adc51/stg-5d0eeea4…/facts/ready/revision=1`） |

### B. 后端请求时推导层（纯函数单源 + 各推导者）

| # | 推导者 | 推导逻辑 | 本会话证据 |
|---|---|---|---|
| B0 | **【单源投影】`admission_stage_view.apply_single_source` / `build_stage_view`** | 纯函数无I/O；冲突1四字段唯一写点：顶层 state（materialized 默认读物化行，缺行→backfill，仍缺→fail-closed 500）、confirmation_status（drafts 权威行）、facts_generated（A4 直查值注入）、`summary.pending_confirmation_count`（无draft→candidate_count；draft_active→未答疑问数；confirmed→0）、字段级 confirmation_status；`build_stage_view` 聚合四阶段→stages/current_stage/blocking[]/primary_action_key/revision，§5.3 fail-closed 不变量（自救形态无动作键→500） | `packages/medical_monitoring/admission/admission_stage_view.py:31-37`（stage_view_mode 默认 materialized）、`:81-94`（pending 唯一推导式）、`:97-136`（confirmation_scope 查找键披露）、`:139-215`（apply_single_source，docstring:149「冲突1四字段的唯一写点」）、`:222-239`（STAGE_ACTION_KEYS）、`:251-361`（build_stage_view，不变量 `:339-349`） |
| B1 | **识别状态推导** `AdmissionMappingPipeline._project` | 作业行集合→`aggregate_recognition_state`（唯一聚合函数，`monitoring_admission_stage_store.py:178-190`：not_started/candidates_ready/needs_attention/generating）；S2 影子比对（materialized 默认下死代码保留）；S5 `inflight_adoption_available`（state==generating 且有候选且末次完成>30min，`:2273-2279`）；R44-02 服务端 pace `:2268`+`_generation_pace` | `packages/medical_monitoring/admission/mapping_pipeline.py:2191-2300`（_project；state=:2260；pace=:2268；inflight=:2273）；阈值 `:64`（RECOGNITION_INFLIGHT_STALL_SECONDS=30*60）；R19-01 同源契约注释 `:2247-2259` |
| B2 | **候选语义富化** `enrich_candidates` | v1 无条件 `facts_generated=False` 已删（S3）：现仅加 summary 计数与 user_questions，facts 值改由 B0 按 A4 直查提供 | `packages/medical_monitoring/admission/mapping_confirmation.py:286-326`（删除注释 `:322-324`「值由apply_single_source按A4直查唯一写点提供」） |
| B3 | **复核视图装配** `list_for_review` | 装配候选→读 draft 权威行→调 B0 `apply_single_source`（注入 A4 `_facts_status :431-450`、物化识别行 `_recognition_state_row :452+`、latest_draft=S4 披露）；确认响应 facts 同改 `:2281-2288` | `mapping_confirmation.py:496-560`（apply_single_source 调用 `:538-543`，S3 注释 `:534-537`） |
| B4 | **文档权威解析器** `MonitoringDocumentEvidenceResolver` | 每次调用对 A1 每条目走 A8 链（list_entries→receipt 完整性→promoted 则 replay A2 证据）+A3 校验+locator 哈希比对→role status current/missing/incomplete/ambiguous。**本环境无缓存（S8 off），是 stage-state/study-documents 慢的所在** | `services/api/app/monitoring_document_evidence.py:50-58`（类+verdict_store）、`:60-67`（缓存开关）、`:98-182`（`_entry_is_verified` 双路径）、`:184-204`（`_verified_entries`）、`:206-252`（resolve） |
| B5 | **映射确认门（运行启动）** `_r7_mapping_confirmation_gate` | 读法不变（S4 决议：门语义不动）：直读 `latest_draft_for_project`（project 维度 updated_at 最新），confirmed→放行，否则 409 `mapping_confirmation_required` fail-closed | `main.py:1161-1192`（门全文本会话实读）；`latest_draft_for_project` `monitoring_mapping_draft_repository.py:1494`；向导用 `find_draft_for_batch` `:1458`（attempt×batch 键）——**两键并存，S4 以 `confirmation_scope` 披露而非合并**（B0 `:97-136`） |
| B6 | **事实就绪门（运行启动）** | `latest_fact_materialization_ready`：按 A6 最新 attempt（共享 `latest_attempt_id`，S4 收编）+A4 ready 判定 | `fact_materialization.py:687-703`（latest_attempt_id docstring 明示与 B6 门同一函数）、`:705+`（门本体） |
| B7 | **路由公开投影**（净出口） | `_public_mapping_projection`/`_public_draft` 白名单出口（含 confirmation_scope/inflight/dual_review_degraded/compensation、forbidden-key 防线）；`_assemble_stage_state` 装配 stage-state 四阶段（documents←document_readiness；recognition←物化行，缺行回填 `aggregate_recognition_state`；mapping←drafts 权威行；facts←A4 直查；facts_recent_failure←事件流 T1 时效窗），If-None-Match→304 | `packages/medical_monitoring/api/r7_product/mapping_candidate_routes.py:668-742`（_public_draft）、`:791-881`（_public_mapping_projection，白名单 `:794-817`）、`:745-788`（R32-04 按表失败聚合）、`:884-1048`（_assemble_stage_state：documents `:902-919`、recognition `:921-967`、mapping `:969-1000`、facts `:1002-1016`、T1 `:1018-1033`） |
| B8 | **全局写门**（单飞） | `acquire_product_write_gate`：识别/解析类长任务持全局写锁 | `mapping_candidate_routes.py` 写点 `:1799,2054,2117,2177` 等（POST 系全部包 write_permit，本会话实读 :1799/:2054/:2117/:2177） |

### C. 前端本地态（S 系后现状，全部本会话现读行号）

| # | 持有者 | 状态 | 本会话证据 |
|---|---|---|---|
| C1 | **向导壳状态机** `admissionWizardReducer` | `phase: input\|creating\|reading\|ready\|failed\|done` + `stepIndex: 0..2` + attemptId/profile/error/retryTarget——本地导航态；第3步=`ADMISSION_WIZARD_STEPS[2]`「研究文件与字段映射确认」 | `frontend/src/features/medical-monitoring/medicalMonitoringAdmissionWizardState.mjs:5-9`（三步定义）、`:240-253`（初始态）、`:313-331`（advance/back，R17-03 注释）、`:566-577`（readAdmissionProfile：先 status 后 profile 两段读） |
| C2 | ~~localStorage 步骤记忆~~ **已删除（S7）** | 改为挂载时一次 `GET .../stage-state` 权威查询：current_stage 越过 documents 即恢复第3步；映射面板静默禁用态补一次重读（非轮询） | `MedicalMonitoringAdmissionWizard.jsx:2284-2295`（删除注释原文+挂载 stage-state 读取）、`:2312-2330`（补读）；API 路径 `medicalMonitoringProductApi.mjs:234` |
| C3 | **映射确认状态机** `admissionMappingConfirmReducer` | `phase: idle\|loading\|ready\|adopting\|adjudicating\|drafting\|confirming\|confirmed\|failed`——保留；confirmed 二次推导读的 `confirmation_status` 已是 S3 单源字段（渲染映射） | `medicalMonitoringAdmissionMappingConfirmState.mjs:43-44`（phase 枚举）、`:636-645`（`confirmation_status==="confirmed" \|\| draft.status==="confirmed"`→phase confirmed） |
| C4 | **文档核对本地态** `documentState` | `phase: idle\|uploading\|analyzing\|reviewing\|adjudicating\|cross_checking\|failed…`（镜像 A5，粒度细于 stage-state 的 documents 四态）+payload | `MedicalMonitoringAdmissionWizard.jsx:1719-1723`（useState 初始） |
| C5 | **事实本地态** `factState` | `phase: idle\|…\|ready\|failed`+payload（A4 权威投影） | `MedicalMonitoringAdmissionWizard.jsx:1740` |
| C6 | **在途防重入 ref 群 + stageState 快照** | adopt/adjudicate/confirm/documentUpload/documentResolve 五 in-flight ref + 4 个请求代际计数；`CONFIRM_STALE_MS=5min`（R3-D 47分钟pending变体的UI侧自救）；T4 `stageState` 权威快照供死锁哨兵 | refs `:1724-1739`（confirmInFlight :1729、CONFIRM_STALE_MS :1731）；stageState `:1741-1748`（T4 注释）；哨兵 `medicalMonitoringAdmissionWizardState.mjs:584-651`（键表 `:584-616`、`stageSentinelAction :618-651`：busy/有控件/主按钮可用→null 不误伤） |
| C7 | **主按钮综合推导**（多本地态合成） | `phase==="done" && mappingState?.phase==="confirmed" && factState.phase…` 等；candidates_ready 自动采纳、facts 自动生成联动 | `MedicalMonitoringAdmissionWizard.jsx`（mappingState reducer :1717-1721；主按钮分支经 `admissionPrimaryAction` `medicalMonitoringAdmissionWizardState.mjs:357-386`） |

### D. URL 路由层与步骤3 API 面（状态读写出口）

- **URL 路由层**：`medicalMonitoringBrowserRoute.mjs:36-38`（`activePageFromMonitoringRoute` 由 URL `view=` 推导 activePage）+ `medicalMonitoringProductRouteState`（search 参数序列化）。**仅导航态，不持有第3步流水线状态**；向导 stepIndex 不入 URL（刷新恢复靠 C2 stage-state 权威查询，S7 后无本地持久化）。
- **API 面**（状态读写出口锚点，全部本会话现读行号）：

| 端点 | 语义 | 证据（mapping_candidate_routes.py 除注明外） |
|---|---|---|
| `GET .../study-documents` | 文档核对就绪投影（B4 无缓存重放） | `:1177-1180` |
| `POST .../study-documents/analyze`、`POST/GET .../study-documents/resolve` | 核对推进/裁决/晋升（A5 写点） | `:1250-1256`、`:1340-1354` |
| `POST/GET .../mapping-candidates` | 识别候选生成/轮询（B1→B0→B7；GET 对 verifier 轻量状态包 R34-08 `:1894-1900`） | POST `:1776-1833`、GET `:1835-1934` |
| `POST .../mapping-candidates/retry-failed` | 失败分片重试（复用库层 retry_terminal `monitoring_ai_repository.py:2666`） | `:2009-2087` |
| `POST .../mapping-draft(/adopt)`、`PATCH .../mapping-draft/field`、`POST .../mapping-draft/adjudicate`、`POST .../mapping-draft/confirm` | 采纳/编辑/裁决/确认（写 A2 drafts） | `:2089-2150`（adopt）、`:2152+`（edit）、`:2212`（adjudicate）、`:2277`（confirm） |
| `GET .../facts` | 事实物化状态（A4 权威直查） | `packages/medical_monitoring/api/r7_product/fact_routes.py:106` |
| **`GET .../stage-state`**【S7】 | 四阶段权威聚合（B0.build_stage_view），If-None-Match→304 | `:1936-2007` |
| `GET /api/projects/{id}/admission-events` | 事件流水读取 | `main.py:5133` |

---

## 二、已知冲突点与44轮实证（本会话逐条原文重验 + 现场探针复核）

### 冲突1：mapping-candidates 投影 vs 权威终态（同包自相矛盾）——投影面已消（本会话探针证实），44轮原文在档

- **44轮机器实证（本会话从 jsonl 原文重提取）**：`r22s_siege_evidence.jsonl` 同秒双响应——2026-10-07T05:33:30.011 `a_mapping_candidates` 返回 `state=candidates_ready, confirmation_status=confirmed, facts_generated=false`（response 前缀本会话实读），同秒 .49 `a_facts` 返回 `state=ready, facts_generated=true`——权威与投影在**同一秒**互相矛盾。
- **轮记录原文（本会话实读）**：ISO_ENV_LOG.md:368（R21D）「mapping-candidates 投影顶层 facts_generated=False 与 summary pending_confirmation_count=60/user_question_count=1 同权威终态（facts ready / draft confirmed / user_questions=0项）不一致，属投影怪癖非阻断」；:384（R22D）「投影怪癖沿 R21D 持续」；:399（R23D）沿轮持续。同源投影面：round_21/report_D.md:127-131（F11 low「方案版本显示未确认，与交接的准备完成状态出入」）；round_22/report_D.md:50（F1 high「准备状态门禁自相矛盾：无已确认方案版本，却放行全量监查」）；round_23/report_D.md:69（F07 medium「准备状态自相矛盾：可运行但处处说未就绪」，:18 步骤3行同述）。
- **修复机理（S3，代码遗迹本会话确认）**：三处硬编码删除（B2 `mapping_confirmation.py:322-324`；B3 确认响应 `:2281-2288`；B1 口径收编 `aggregate_recognition_state`），四字段收编 B0 唯一写点（`admission_stage_view.py:149` docstring）。
- **本会话现场复核（2026-10-17 只读探针，常驻项目 proj_user_6ef58ac151e1 / stg-cd69899943…）**：
  - `GET .../mapping-candidates?focus=all` → HTTP 200，`state=candidates_ready`、`confirmation_status=confirmed`、**`facts_generated=True`**、`summary.pending_confirmation_count=0`、`confirmation_scope={scope:"confirmed", latest_draft_id: monmapdraft_73abe5c6…, latest_draft_attempt_id: stg-cd698999…}`、draft `{v80, status=confirmed}`、60 候选字段级 `confirmation_status=confirmed`；
  - `GET .../facts` → HTTP 200，`state=ready, facts_generated=true, summary{10表/591行/3038值/3038核验}`；
  - `GET .../stage-state` → HTTP 200（241.5s，见〇.4），`stages={documents:ready, recognition:candidates_ready, mapping_confirmation:confirmed, facts:ready}`、`current_stage=complete`、`blocking=[]`、revision=1、`etag W/"1"`。
  - **四口径一致，冲突1在投影面已消；代价是同端点耗时 20.3s/9.4s（mapping-candidates）与 241.5s（stage-state），性能债仍在链上。**

### 冲突2：前后端互斥（状态碎片化家族，R9 拍板第一优先根因）——结构性收敛，渲染层本地态保留（如实偏差）

- **44轮实证（本会话逐字重读）**：
  - R9 双实证之一：round_09/REPORT.md:14「预置在开考前 8 分钟已通过 API 达到『映射已确认、文档就绪、事实就绪』全绿（15:00），而界面与运行门在 15:08 起仍读『未确认』」+ 同段「预置日志已裁定：后端确认状态在，产品界面与运行门读不到」；
  - round_09/REPORT.md:67-69 根因归类第1条原文：「**状态碎片化（双实证，当前第一优先根因）**……接入管线写入的状态与运行门读取的状态**不是同一份事实**。修不好它，开考位永远开不了考」；:80 升级请求第3项「状态归一修复排期（双实证支撑，最优先）」；
  - round_11/REPORT.md:13「种子确认态与界面态在暂停/重启之后再次分叉——状态碎片化证据链增至四起（R8/R9/R10/R11）」。
- **S 系处置（代码遗迹本会话确认）**：①投影字段单源化（S3，冲突1同款）；②查找键二义性显式披露（S4 `confirmation_scope`，`admission_stage_view.py:97-136`；B5 门仍读 project-latest、向导读 attempt×batch——**语义披露而非合并**）；③C2 localStorage 删除、F5 恢复改 stage-state 权威查询（`Wizard.jsx:2284-2295`）；④T4 死锁哨兵以权威 blocking[] 为兜底动作源（`wizardState.mjs:584-651`）。
- **残留（如实）**：C1/C3/C4/C5/C7 本地态保留——「前端任一本地 phase 与后端权威短暂失步」的结构可能性仍在，只是失步窗口从「持久」缩到「单次载荷间」。R9 验收三问（:80「确认状态存哪、重启后活不活、运行门读哪个库」）现答：存 A2 drafts 行（sqlite 持久）；重启存活（本会话实查常驻项目 draft confirmed v80 跨 10 天在库）；运行门读同库 `latest_draft_for_project`——与投影同库不同键（S4 披露）。

### 冲突3：失败态被缓存复用（infra 故障固化为内容终态）——分层修复；S6 判定逻辑在库且**本环境灰度已开启（=1）**；S8 缓存已实施但关

- **44轮实证（本会话重读）**：
  - R11-01（critical，已修 24b7bc5）：round_11/REPORT.md:6 一句话结论「产品把一个**可重试的临时故障**按文件指纹**缓存成了不可逆的内容性终态结论**（重传同版文件被告知『直接复用已有核对结论』拒绝重析）」；:40 立单原文「瞬时故障被固化为永久死锁」；
  - R5-ISO 复核不收敛：ISO_ENV_LOG.md:51「adopt成功后复核(adjudication)恒running、confirm恒409 mapping_verifier_incomplete，而全部20个mapping job已终态(19完成+1失败)——**复核状态机在job全终态下不收敛**」；
  - R32-04 265 识别分片 `queue_dwell_timeout` 终态失败且 attempt_count=0：代码侧同源记录 `mapping_candidate_routes.py:745-752`（`_public_table_failures` docstring「R32实测…LB域全部沦陷」）；
  - R44 链条（HANDOFF L107 实读）：R44-01 致命「研究文件核对独立性诊断失败」、R44-02 高危「识别吞吐8-9小时vs页面承诺」。
- **代码机理（本会话实读）**：`create_or_get` 稳定 job_id 确定性去重（同请求身份直接返回已存在行含失败行，`monitoring_ai_repository.py:914`）；S6 下沉=仅「终态失败+failure_code∈INFRA_FAILURE_CODES+无契约退役」可按显式重试语义重排（`monitoring_admission_stage_store.py:66-79` INFRA_FAILURE_CODES + `monitoring_ai_repository.py:885-915` 判定 + `:2666` retry_terminal），env `WORKBENCH_MONITORING_AI_INFRA_RETRY` 控制——**本会话 `ps eww` 实测 8911 进程=1（开启）**。文档链 infra 不缓存（24b7bc5 起）。A7 字段画像缓存按内容键命中（`monitoring_ai_field_profile_cache.py:38-45`），天然不缓存失败（键=身份非结果）。
- **专项期间同族新暴露（git log 实读，已修）**：verifier 死锁=零认领排队行被 dwell 收割+confirm 409 兑现重排（`1f60d357`）；confirm 确定性 500=`_cohort_candidates_with_progress` 裸调 staticmethod（`fdcf827f`，基线存量地雷）；整域缺口确认链死锁（`6a3d4c3d`，缺口豁免在装载与再校验两处生效）。

### 冲突4：死锁变体族（同一根因的历次投影，代码遗迹本会话核对）

| 变体 | 轮次出处 | 代码遗迹（本会话行号） | 现状 |
|---|---|---|---|
| 「采用已识别的X个字段并继续」诱导提交→422→死锁 | HANDOFF §1.1 族1；round_09/REPORT.md:6（B位复核停滞第三次复现同屏） | `mapping_pipeline.py:2247-2259` R19-01 注释（未终态一律 generating「前端按钮态与后端校验同源」） | 口径三处同源（B1 `:2260` / A2 写点物化行 / stage-state 回填同函数 `aggregate_recognition_state`） |
| 识别已完成但确认路径不存在 | HANDOFF §1.1 族1（「阻塞组无入口」） | R35-01 知情降级入口+S5 双标志门（`mapping_confirmation.py` adopt 门，B7 白名单 `inflight_adoption_available`） | 服务端化完成（S5） |
| 阻断组无处置载荷（确认按钮恒disabled） | HANDOFF §1.1（R41-01 提交频次族） | `mapping_candidate_routes.py:696-731`（R41-01 注释原文：blocked-group 恒在、零角色编辑控件、确认按钮恒 disabled 约60分钟；现投影携带 rule_id/affected_fields/role_catalog） | B0 blocking[] 不变量兜底（`admission_stage_view.py:339-349` fail-closed） |
| 复核在作业全终态下不收敛 | ISO_ENV_LOG.md:51（R5-ISO） | B1 generating 需非终态作业；verifier 变体另修（`1f60d357`） | 部分收敛（本会话 E2E 项目 SM1 仍见 recognition needs_attention+draft v1 停滞，如实记录） |
| 确认请求 47 分钟 pending 永久卡死 | HANDOFF §1.1 族1（R3循环报告D） | `Wizard.jsx:1729-1731` CONFIRM_STALE_MS 注释原文（「后端同步收尾任务47分钟不返回」） | C6 超时自救保留为 UI 防重入；S7 后状态以服务端为准 |
| 刷新/挂起后 ETA 归零跳变 | HANDOFF L107（R44-02 高危） | `mapping_pipeline.py:2283-2295` R44-02 注释原文（「ETA在439↔144分钟间反复跳变」）；服务端 `_generation_pace :2300+` | 已修（服务端窗口预估；前端仅在缺席时回退） |

### 冲突5【专项新增】：E2E 验收门（从零三连）——本会话未运行，无法独立判定

03_IMPL_attempt1.md §0 与 04_E2E_FAILURE_DIAGNOSIS.md 在档（本轮仅确认文件存在与 git log 提交信息）：SM1/SM2/SM3 三轮从零停于 `mapping_bridge_failed` → 两笔真栈修复（`1f60d357`/`fdcf827f`）→ v2 记录「桥直查 HTTP 200、E2E 门未过=上游 AI 流瞬断」。**v2 之后**：`e3820cc1`（轮中暂停）→ T1-T6 五步半实施（`9eee3331`→`557707df`）→ `bda88a45`/`6a3d4c3d`（E2E 第2轮拦截修复，提交信息含现场 409/409 链取证）。**本会话未执行 E2E，从零三连现状不明**——这是唯一无法由只读探针闭环的验收项。

---

## 三、单一权威源候选评估（v3 现势）

### 结论：格局为「**A2 一库（23 表）+ A4/A1 两域真值 + B0 唯一纯函数投影写点 + stage-state 单一聚合出口**」；剩余缺口=E2E 门未闭环、S8 缓存未开启（重放成本 9-241s）、A5 核对批次状态机仍在库外文件态

- **候选1（现势最优）：A2 = `medical_monitoring_ai.sqlite3`（23 表）**。识别+映射+激活+阶段状态+事件流+verdict 缓存的既成事实权威：CAS/版本（drafts UNIQUE `monitoring_mapping_draft_repository.py:982`、idempotency `:1056`）、审计链（edit_operations/adjudication_receipts/revisions）、append-only 事件流（触发器不可变改/删 `monitoring_admission_stage_store.py:102-104`）。B5 门直读它；B0 投影默认读它的物化行；S7 facts 镜像行也落这里。**本会话实测漂移事件 0 条**（`stage_view_divergence` 空集）。缺口：①`monitoring_mapping_project_state` 0 行（激活链未被常驻路径消费）；②facts 行是 best-effort 镜像（A9，真相在 A4）；③A5 批次状态机未入库。
- **候选2：A4 `canonical_fact_materialization` 域对象**——事实层唯一真值（保留）。全链 facts_generated 均直查 A4（B0/B3/B7 三处实读确认）；A9 镜像行明确从属（`main.py:4333-4337` docstring）。
- **候选3：A1 `source_registry.jsonl`**——文档权威（保留，重放成本未解）。唯一被 B4 与晋升链共同消费的登记处（promoted+receipt+replay 闭环，`source_intake.py:694-711`）。JSONL 全量重写+文件锁（`:522-609`）弱于 sqlite；verified 语义依赖对 A2 重放——S8 缓存已实施但本环境 off（0 行），**本会话实测重放成本：mapping-candidates 9.4-20.3s、stage-state 120s 超时/241.5s 完成**（单次采样）。
- **结构性收口清单（供下一阶段决策）**：
  1. **E2E 门三连从零**（冲突5）——专项完成定义，现状不明，需在通道稳定窗口重跑；
  2. **S8 开启决策**：表与代码全在（`2d411755`），开启=env `WORKBENCH_DOCUMENT_VERDICT_CACHE=1`，可消 9-241s 重放；开启前需确认等价性测试覆盖（提交信息称 9 测试在档，本会话未运行 pytest）；
  3. **A5 状态机入库**（若追求一库全收）：batches/user_selections/identity_overrides 仍 CAS+flock 文件态；T2 已为其埋事件（`49f9ad79`），状态行仍未建（§2.5 裁决：不建=避免第二份权威）；
  4. **B5 门与 `find_draft_for_batch` 键统一**：S4 选择披露而非合并（R18-03 回归保护）；多 attempt 并存常态化后需按 `confirmation_scope` 驱动门判定；
  5. **前端 C7 主按钮接 `primary_action_key`**：stage-state 已供数，消费未做（仅 T4 哨兵消费 blocking[]）；
  6. **性能回归**：mapping-candidates/stage-state 耗时较 v2 恶化一个量级（20s/241s vs 0.4s/19.9s），单次采样待基准化；若 stage-state 接前端轮询将放大（03_IMPL §4.3 因此未接轮询）。

---

## 四、本次探针命令与输出（诚实清单，全部只读，2026-10-17 执行）

| # | 命令 | 结果 |
|---|---|---|
| 1 | `curl -s http://127.0.0.1:8911/api/runtime-readiness` | 200 `{"status":"ready","ready":true,...,"backend_build_id":"api-4ca198219617fc39","runtime_schema_version":16}` |
| 2 | `curl -s http://127.0.0.1:8911/api/projects` | 5 项目：`b6251f4adc51`(MX循SM3-CSU)、`f5cbef8251cd`(MX循SM2-CSU-R2)、`e282a7e982b0`(MX循SM1-CSU)、`2b125f77bd3c`(MX循SM2-CSU)、`6ef58ac151e1`(MX循开考-CSU 常驻) |
| 3 | `curl -s .../data-admissions/latest`（常驻） | `stg-cd69899943ba42618f589ba07a134a59`, state=`profile_ready` |
| 4 | `curl -w` 计时 `GET .../mapping-candidates?focus=all` | HTTP 200 **20.28s**；state=candidates_ready、confirmation_status=confirmed、**facts_generated=True**、pending_confirmation_count=0、confirmation_scope=confirmed、draft v80 confirmed、60 候选字段级 confirmed（全文摘录见冲突1） |
| 5 | 同上 `focus=critical`（暖） | HTTP 200 **9.36s**；四字段同上一致 |
| 6 | `curl -w` `GET .../facts` | HTTP 200 **9.32s**；`state=ready, facts_generated=true, {10表/591行/3038值/3038核验}` |
| 7 | `curl -m 120 -w` `GET .../stage-state` | **HTTP 000（120s 超时，无响应体）** |
| 8 | 重试 `curl -m 300` 同端点 | HTTP 200 **241.5s**；`stages={documents:ready,recognition:candidates_ready,mapping_confirmation:confirmed,facts:ready}`、current_stage=complete、blocking=[]、revision=1、`etag: W/"1"` |
| 9 | `lsof -tiTCP:8911 -sTCP:LISTEN` + `ps eww -p 24250` | pid 24250；env 命中 `WORKBENCH_MONITORING_AI_INFRA_RETRY=1`；`WORKBENCH_DOCUMENT_VERDICT_CACHE`/`STAGE_VIEW_MODE` 未设置（默认 off/materialized） |
| 10 | `sqlite3 -readonly medical_monitoring_ai.sqlite3 "SELECT name FROM sqlite_master WHERE type='table'"` | **23 张用户表**（v2 为 22；新增 `monitoring_document_authority_verdicts`） |
| 11 | `sqlite3 -readonly` stage_state / events / verdicts | stage_state 15+ 行（活跃至 2026-10-16，最高 revision 51）；events：state_changed 622 / failure_recorded 36 / recovery_action 31 / degradation 6；**divergence 0**；verdicts **0 行** |
| 12 | `sqlite3 -readonly` drafts/jobs/project_state | 常驻 draft `monmapdraft_73abe5c6…` confirmed v80；常驻 jobs completed=44+failed=2；全库 jobs 9327；`monitoring_mapping_project_state` **0 行**；SM1 draft v1=draft+needs_attention（在途如实记录） |
| 13 | `wc -l runtime/source_registry.jsonl` | **176 行**（v2 时 168） |
| 14 | `python3` 解析 `r22s_siege_evidence.jsonl` | 2026-10-07T05:33:30.011 `a_mapping_candidates` `facts_generated:false, confirmation_status=confirmed`；同秒 .49 `a_facts` `facts_generated:true`（冲突1 同秒机器证据） |
| 15 | `git rev-parse --short HEAD` + `git log --oneline -15` | HEAD=`6a3d4c3d`；S1-S7/T1-T6/S8/E2E 修复提交链全读（`e61d2067`→`6a3d4c3d`） |

**未做/不可做（如实声明）**：
① **E2E 从零三连未运行**——只读纪律下不可能执行（需建项/上传/AI 作业），冲突5 现状仅能引用文档与 git 提交信息；
② **未运行任何 pytest / node --test**（S8 等价性 9 测试、前端 94 项等仅为提交信息在档，本会话未复跑）；
③ **性能数字全部单次采样**，且 241.5s 样本期间有我方一次并发 GET；「S8 关→重放慢」的归因是代码链推断（`document_readiness→resolver` 直调已实读），**未做剖析采样证实**；
④ **未探查 R44-01/R41-01 等现场复现**（无在途故障）；R19/R41/R44 轮 round 报告原文未逐字重读（引用经 HANDOFF §1.1/L107 与代码注释互证，来源已如实标注）；
⑤ STATE_V2.json 台账 159 条未读全文（仅按任务点名核对 round_09/11/21/22/23 报告与 ISO_ENV_LOG 原文）；
⑥ `STAGE_VIEW_MODE` 的 materialized 默认是代码默认+env 缺省推断（`ps eww` 未命中该键=未显式设置），非运行时行为实测。

---

## 五、一句话结论

44 轮定位的「第3步状态机没有单一权威源」经 S1-S7+T1-T6 收编后，现势为「**A2 一库（23 表，含阶段状态行+事件流+已建未启用的 verdict 缓存）+ A4/A1 两域真值 + B0 唯一纯函数投影写点 + stage-state 单一聚合出口**」：冲突1（投影 vs 权威）经本会话现场探针证实已消（confirmed/0/True 三口径一致，且 44 轮同秒矛盾机器证据在档）、冲突2（状态碎片化）从持久互斥收敛为渲染层单载荷窗口、冲突3（失败缓存复用）判定逻辑在库且本环境 S6 灰度已开（=1）；**剩余真缺口三个——E2E 三连从零门现状不明（本会话无法只读闭环）、S8 verdict 缓存建成未启（重放成本 9.4s-241.5s，较 v2 恶化一个量级）、A5 核对批次状态机仍是库外文件态**。
