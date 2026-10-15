# 01_STATEMAP — 第3步状态机全量状态持有者地图（状态机重构专项·考古底稿）

> 调查日期：2026-10-14。只读调查，未修改任何代码/数据。
> 调查范围：数据接入向导第3步（研究文件核对 / 字段识别 / 映射确认）涉及的**每一个状态持有者**。
> 代码根：`implementation/workbench`（下述相对路径均以此为根）。
> 隔离环境：API `http://127.0.0.1:8911`（本次探针时 build=`api-5f86f3eb6ec412e7`），runtime 根 `runs/tester_loop_iso_20260928/runtime/`（`services/api/app/main.py:591-593` 以 `WORKBENCH_RUNTIME_DIR` 覆盖）。
> 依据链：HANDOFF_40ROUNDS_20261014.md 第四部分根因一（第55-56行）→ 三条已知线索全部在本调查中定位到代码级证据；R9/R21/R22/R23 等轮记录已核对原文。

---

## 一、状态持有者全量清单

第3步的三条流水线（文档核对→字段识别→映射确认→事实物化）的状态分散在 **6 个后端持久层 + 2 个后端推导层 + 5 组前端本地态**。逐项如下。

### A. 后端持久层（跨重启）

| # | 持有者 | 位置/结构 | 持有的状态 | 证据 |
|---|---|---|---|---|
| A1 | **源注册表**（研究文件台账） | `runtime/source_registry.jsonl`（JSONL，原子替换写，文件锁） | 每个研究文件的注册条目：`parser_status`、`metadata.monitoring_authority_status`（promoted 与否）、内嵌 `document_authority_receipt` | `services/api/app/source_intake.py:467-469`（`SourceRegistryStore.__init__`，jsonl_path）、`source_intake.py:522-609`（原子写+锁）、装配点 `main.py:1093-1094`。隔离runtime实测：156行、常驻项目2条（protocol_docx+ecrf_document）全部 promoted（本次只读python统计） |
| A2 | **AI作业台账 + 映射草稿库**（同一sqlite双仓） | `runtime/medical_monitoring_ai.sqlite3`（隔离环境实测 4.4 GB，20张表） | ①`monitoring_ai_jobs/attempt/candidates/evidence_reads/call_ledger/queue_control/payload_blobs`（识别+文档核对作业状态机：queued/running/completed/failed/blocked/stale_input/cancelled，租约+queue_dwell_timeout）；②`monitoring_mapping_drafts/revisions/field_sources/edit_operations/adjudication_receipts`（draft→confirmed 两态权威）；③`monitoring_mapping_project_state/activation_history/activation_operations/batch_bindings(+history)/binding_operations`（映射激活/绑定，`monitoring_mapping_activation.py:298-370`） | 建表：`services/api/app/monitoring_ai_repository.py:353,359,394,406,424,451,466,477,499`；`monitoring_mapping_draft_repository.py:920,939,955,969,991`；`monitoring_mapping_activation.py:298,317,327,336,351,361`。装配：`main.py:1124-1140`（AI仓）、`main.py:1151-1153`（草稿仓，**与AI仓同文件**）。sqlite_master 只读实测列出全部20表；常驻项目 draft `monmapdraft_73abe5c6c9561a9e95eec2056991` status=confirmed v80；jobs 44 completed + 2 failed |
| A3 | **内容校验记录库** | `runtime/source_content_validation_records/`（sqlite，`source_content_validation_records` 表） | 每个源文件的 `use_status`（allowed/confirmed_after_warning/…）、`technical_status`（ready 与否）——文档绑定 current 的必要条件之一 | `services/api/app/source_content_validation.py:291-328`（建表+触发器）、`source_intake.py:434-448`（`current_content_validation` 消费） |
| A4 | **事实物化域对象**（per-project store） | `runtime/medical_monitoring_r7/<project>/runtime/monitoring_runtime.sqlite3` + `artifacts/`，域对象 kind=`canonical_fact_materialization`，按 attempt_id 键 | `state: ready/not_generated`、`facts_generated: bool`、行/值核验计数 | `packages/medical_monitoring/admission/fact_materialization.py:37`（KIND 常量）、`:58-60`（`_store`→`RUNTIME_DIR_NAME/runtime/monitoring_runtime.sqlite3`）、`:616-617`（status 未生成→`{"state":"not_generated","facts_generated":False}`）、`:640`（`facts_generated: ready`）、写入 `:607`（`store.put_domain_object`）。runtime 常量名 `packages/medical_monitoring/runtime/background_recovery_support.py:64` |
| A5 | **文档权威工作流工作区文件**（per-project 文件态） | `runtime/medical_monitoring_r7/<project>/document_authority_candidates/`：`batches/`、`manifests/`、`files/`、`user_selections/<batch>.json`+`user_selection_revisions/<batch>/decision-N.json`（CAS+flock）、`identity_overrides/<batch>.json`、`last_document_check_note.json` | 核对批次状态机 `analyzing→reviewing→adjudicating→cross_checking→(promoted/needs_user_input/failed)`；用户角色裁决决策版本链；身份确认覆写 | 状态机：`services/api/app/monitoring_document_authority_workflow.py:207,279,306,378,447,464,533,553,628,643`；批次落盘目录 `:710-711`；决策CAS `:834-1000`；身份覆写 `:722-832`；核对留痕 `:678-693`。工作流推进产物落盘实测见 `runs/tester_loop_iso_20260928/runtime/medical_monitoring_r7/proj_user_1824d9610247/document_authority_candidates/` |
| A6 | **接入暂存 attempts**（per-project 文件态） | `runtime/medical_monitoring_r7/<project>/admissions/`：`staging/<attempt_id>/`（内容寻址清单+文件）与 `admission_events.jsonl` | attempt 存在性与完整性（第2步→第3步的输入边界），事件流水 | `packages/medical_monitoring/admission/staging.py:19-27,143-165,223-236`；`main.py:4148-4152`（按 created_at 取最新 attempt——**运行门用时间序而非用户指定序**） |
| A7 | **字段画像快照缓存** | `runtime/` 下内容寻址快照（manifest+snapshot 双文件，digest 校验） | 字段识别结果的缓存命中/缺席（`cache_entry_absent` 等 reason_code） | `services/api/app/monitoring_ai_field_profile_cache.py:14-17,33-95` |
| A8 | **晋升回执可验证性**（派生但持久绑定在A1） | A1 条目 metadata 内嵌 receipt + A2 作业行 | `monitoring_authority_status="promoted"` 写入 A1（`monitoring_document_authority_jobs.py:1245-1253`）；验证=用 A2 的不可变作业证据**逐次重放** receipt（`main.py:1141-1147` 接线 → `monitoring_document_authority_jobs.py:1278+` `verify_document_authority_promotion_receipt`） | `source_intake.py:694-711`（`monitoring_authority_entry_is_verified`：receipt完整→状态promoted→replay验证）、`source_intake.py:112-152`（`monitoring_authority_receipt_is_complete`） |

### B. 后端每次请求的推导层（不落盘，但决定 API 语义）

| # | 推导者 | 推导逻辑 | 证据 |
|---|---|---|---|
| B1 | **识别状态推导** `AdmissionMappingPipeline._project` | 由作业行集合推导 `state`：全 completed→`candidates_ready`；全终态且有失败→`needs_attention`；否则→`generating`。同时把每字段硬编码 `confirmation_status:"pending_confirmation"`、`summary.pending_confirmation_count=len(mappings)` | `packages/medical_monitoring/admission/mapping_pipeline.py:2191-2236`（state推导:2200-2208；pending硬编码:2189,2219） |
| B2 | **候选语义富化** `enrich_candidates` | 在B1之上无条件写顶层 `facts_generated: False`、`candidate_fact_boundary:"candidates_only"`，并补 field_count/user_question_count/system_adopted_count（**不改 pending_confirmation_count**） | `packages/medical_monitoring/admission/mapping_confirmation.py:286-324`（facts_generated=False 在 :322） |
| B3 | **复核视图装配** `list_for_review` | B2 + 查 `find_draft_for_batch(project_id, batch_id)`：draft confirmed→顶层 `confirmation_status="confirmed"`+`draft.status`（**仍不纠正 summary.pending_confirmation_count / facts_generated**） | `mapping_confirmation.py:425-465`（confirmed 覆盖 :456-463） |
| B4 | **文档权威解析器** `MonitoringDocumentEvidenceResolver` | 每次调用对每个 A1 条目走 A8 链（list_entries→receipt完整性→replay A2 证据）+ A3 校验 + span/locator 清单哈希比对，推导 role status: `current/missing/incomplete/ambiguous` | `packages/medical_monitoring/admission/../services/api/app/monitoring_document_evidence.py:50-77`（_verified_entries→A8）、`:216-322`（_role_evidence）、`:375-507`（_current_binding：locator清单哈希:400-433、校验消费:434-448） |
| B5 | **映射确认门（运行启动）** `_r7_mapping_confirmation_gate` | 查 `latest_draft_for_project`（**跨attempt取updated_at最新一条**），confirmed→放行，否则 409 `mapping_confirmation_required` | `main.py:1156-1190`；`latest_draft_for_project` `monitoring_mapping_draft_repository.py:1415-1442`（与向导用的 `find_draft_for_batch` :1379-1408 **是两个不同查找键**：project-latest vs attempt-batch） |
| B6 | **事实就绪门（运行启动）** | `latest_fact_materialization_ready`：按 A6 最新 attempt + A4 域对象 ready 判定 | `fact_materialization.py:647-660+`（`latest_fact_materialization_ready`）、`main.py:4118-4135`（run setup 消费） |
| B7 | **路由公开投影**（净出口） | `_public_mapping_projection`/`_public_draft`：从B1-B3载荷挑字段出口——`state/confirmation_status/facts_generated/summary/candidates/verification/draft` 同包下发 | `packages/medical_monitoring/api/r7_product/mapping_candidate_routes.py:604-678`（_public_draft）、`:727-806`（_public_mapping_projection） |
| B8 | **全局写门**（单飞） | `acquire_product_write_gate`：识别/解析类长任务持全局写锁（R23-01 曾被59表串行识别霸占致整站假死） | 路由上下文 `mapping_candidate_routes.py:496-509`（MappingCandidateRouteContext.acquire_product_write_gate）；单飞辅助 `:52-89`（_try_begin_resolve/_try_begin_adjudicate） |

### C. 前端本地态（页面内存 + localStorage）

| # | 持有者 | 状态 | 证据 |
|---|---|---|---|
| C1 | **向导壳状态机** `admissionWizardReducer` | `phase: input\|creating\|reading\|ready\|failed\|done` + `stepIndex: 0..2`——前端自行推导当前步 | `frontend/src/features/medical-monitoring/medicalMonitoringAdmissionWizardState.mjs:240-247`（初始态）、`:260-355`（reducer：步骤推进/回退/重试） |
| C2 | **localStorage 步骤持久** `admission-step:{projectId}:{attemptId}` | 刷新后按第2步/第3步写入"2"，用于恢复提示 | `MedicalMonitoringAdmissionWizard.jsx:2262-2271`（写/删）、`:2274-2287`（读恢复） |
| C3 | **映射确认状态机** `admissionMappingConfirmReducer` | `phase: idle\|loading\|ready\|adopting\|adjudicating\|drafting\|confirming\|confirmed\|failed` + progress/stall 计时——**对后端载荷的二次状态推导**（load-ready 时从 `confirmation_status`/`draft.status` 推 confirmed，从 `state` 推 generating/needs_attention 文案） | `frontend/src/features/medical-monitoring/medicalMonitoringAdmissionMappingConfirmState.mjs:41-43`（初始态）、`:587-700`（load-ready 二次推导：`action.payload?.confirmation_status === "confirmed" || draft?.status === "confirmed"` → phase confirmed）、`:17,24,31-34`（停滞/轮询阈值常量） |
| C4 | **文档核对本地态** `documentState` + 阶段计时 | `phase: idle\|uploading\|analyzing\|reviewing\|adjudicating\|cross_checking\|failed…`（镜像A5状态机）+ `documentState.payload.ready` | `MedicalMonitoringAdmissionWizard.jsx:1697-1700`（useState）、`:1276-1296`（阶段键+停滞计时）、`:1311-1340`（主按钮按 documentPhase/identityBlocked/failed 分支推导文案） |
| C5 | **事实本地态** `factState` | `phase: idle\|…\|ready\|failed` | `MedicalMonitoringAdmissionWizard.jsx:1717-1718` |
| C6 | **在途防重入 ref 群** | adopt/adjudicate/confirm/documentUpload/documentResolve 六个 in-flight ref + 请求代际计数（confirm 5分钟陈旧放行） | `MedicalMonitoringAdmissionWizard.jsx:1702-1717`（含 CONFIRM_STALE_MS 注释：R3循环报告D确认请求pending 47分钟） |
| C7 | **主按钮综合推导** | 由 `phase === "done" && mappingState?.phase === "confirmed" && factState.phase` 与 `documentState.payload.ready` 等多个本地态合成主按钮 | `MedicalMonitoringAdmissionWizard.jsx:1308-1340` |

### D. 步骤3 API 面（状态读写出口，锚点）

| 端点 | 语义 | 证据 |
|---|---|---|
| `GET /api/projects/{p}/modules/medical-monitoring/r7/data-admissions/{attempt}/study-documents` | 研究文件核对就绪投影（B4） | `mapping_candidate_routes.py:935-1006` |
| `POST .../resolve`（及轮询 GET resolve_mapping_documents_get） | 核对推进/显式重试（R28-03/R27-01 预算区分 explicit_retry） | `mapping_candidate_routes.py:1098-1116`；请求模型注释 `:489-493` |
| `POST/GET .../mapping-candidates` | 识别候选生成/轮询（B1-B3, B7） | `mapping_candidate_routes.py:1534-1535, 1588-1589` |
| `POST .../mapping-candidates/retry-failed` | 失败分片重试（R42-01 补偿同源） | `mapping_candidate_routes.py:1684-1688` |
| `POST .../mapping-draft/adopt \| adjudicate \| confirm`、`PATCH .../mapping-draft/field` | 采纳/复核裁决/确认/编辑（写 A2） | `mapping_candidate_routes.py:1764-1768, 1827-1828, 1887-1888, 1952-1953`；确认落库 `mapping_confirmation.py:2130-2143`（确认后 `facts_generated=False`、`next_action="generate_facts_later"`） |
| `GET .../facts` | 事实物化状态（A4 权威） | fact_routes.py（fact_materialization.status → `{"state":"ready","facts_generated":true,...}`） |

---

## 二、已知冲突点与44轮实证

### 冲突1：mapping-candidates 投影 vs 权威终态（同包自相矛盾）——**本次探针在常驻项目上现场复现**

一个 GET 响应内同时携带三个互相矛盾的状态声明（2026-10-14 实测，`proj_user_6ef58ac151e1`/`stg-cd69899943ba42618f589ba07a134a59`，命令 `curl -s "http://127.0.0.1:8911/...mapping-candidates?focus=all"` HTTP 200）：

| 字段 | 实测值 | 语义来源 |
|---|---|---|
| `confirmation_status` / `draft.status` | `confirmed`（draft v80） | A2 权威（B3 覆盖） |
| `summary.pending_confirmation_count` | **60**（=全部字段），`user_question_count=1`, `critical_count=1` | B1 硬编码（`mapping_pipeline.py:2189,2219`），不随确认更新 |
| 顶层 `facts_generated` | **False** | B2 无条件写（`mapping_confirmation.py:322`） |
| `verification.summary.pending_confirmation_count` | **0**（verifier 轻量包） | 同一响应内第三种口径 |

同刻 `GET .../facts` 返回 `state:"ready", facts_generated:true`（3038 值全核验）——**与 mapping-candidates 顶层 facts_generated=False 直接相反**。代码机理：`enrich_candidates` 无条件 False（`mapping_confirmation.py:322`）+ 确认后仍置 False（`:2141`"Canonical facts remain a later deterministic step"）+ B1/B3 不回填。

**44轮实证（轮轮记录）**：
- ISO_ENV_LOG.md:368（R21D，2026-10-06）首次记录：「mapping-candidates 投影顶层 facts_generated=False 与 summary pending_confirmation_count=60/user_question_count=1 同权威终态（facts ready / draft confirmed / user_questions=0项）不一致，属投影怪癖非阻断」；
- ISO_ENV_LOG.md:384（R22D）、:399（R23D）、:424（R24D）、:449（R25D）、:476（R26D）、:495（R27D）、:522（R28D）——**沿轮持续至R28+，每轮如实记录、每轮不修**（超出单轮射程）；
- 机器证据：`r22s_siege_evidence.jsonl:3-4`（R22攻坚实测同一对矛盾响应原文）；
- R22-01 家族同源实证：round_22/report_D.md:17,50-52（F1「准备状态门禁自相矛盾：无已确认方案版本，却放行全量监查」——就绪投影与权威终态不一致的另一投影面）；round_23/report_D.md:18,69（F07 同款复现）；round_21/report_D.md:32,129（F11 首记录）。

### 冲突2：前后端互斥（状态碎片化家族，R9 拍板为第一优先根因）

后端 A2 已 confirmed/全绿，但界面与运行门读「未确认」——**写入方与读取方不是同一份事实**。
- **R9 双实证（第二次独立实证）**：round_09/REPORT.md:14 —— 预置 15:00 后端 API 返回 `ok:true、confirmation_status:"confirmed"、documents_ready:true、facts_state:"ready"、adjudication_state:"complete"、user_questions:0`（proj_user_f650151b5a42），15:08 起 D 位界面与运行门仍读「未确认」，三次确认被拒；复盘官裁定：**后端确认状态在，产品界面与运行门读不到**。同轮 round_09/REPORT.md:69 定性「接入管线写入的状态与运行门读取的状态不是同一份事实」，并列修复验收三问（:80「确认状态存哪、重启后活不活、运行门读哪个库」）。
- **R5 首实证（更早）**：round_05/REPORT.md:35 —— 预置 17:36 后端事实已就绪（`FACTS OK: state ready, facts_generated true, 2400 values verified`），17:50 开考时「监查模块界面却始终不认账」——「后端就绪与界面就绪之间的状态断裂」。
- **结构机理（本次定位）**：①前端主按钮由 C4/C3/C5 三个本地态合成（Wizard.jsx:1308-1340），每个本地态独立镜像不同后端端点，任一镜像失步即整体失步；②运行门 B5 用 `latest_draft_for_project`（project 维度、updated_at 最新），向导用 `find_draft_for_batch`（attempt×batch 维度）——**同一权威库的两个查找键**（`monitoring_mapping_draft_repository.py:1379-1442`）；③R9-02 向导自身状态机脱节（步骤条第3步、主体第1步内容，round_09/REPORT.md:27,41）是 C1/C2 本地态与载荷失步的形态之一（R11 轮 24b7bc5 修复）。
- **缓解史（未根治）**：R24 轮 R18-03 收尾把运行门改为读 A2 草稿表 fail-closed（main.py:1156-1190 注释「R19实测facts旁路存在时未确认映射照常执行(fail-open)」）——把互斥从"运行门读别处"收敛为"运行门读A2、界面读投影"，仍是两套读法。

### 冲突3：失败态被缓存复用（infra 故障固化为内容终态）

- **R11-01（critical，已修 24b7bc5）**：round_11/REPORT.md:6,13,40 —— AI 代理 503/409（infra）被按**文件指纹缓存为不可逆内容性终态结论**：重传同版文件秒回「直接复用已有核对结论」、重新核对瞬间返回同一 409、无自愈途径——「瞬时故障被固化为永久死锁」。
- **代码机理（本次定位）**：`MonitoringAiRepository` 作业创建是 `stable_job_id(request)` 确定性主键去重（`monitoring_ai_repository.py:630-677`，同请求身份直接返回已存在行，**含失败行**）；A7 字段画像缓存同样按内容键命中（`monitoring_ai_field_profile_cache.py:36-95`）。失败是否复用完全取决于上层是否区分错误类别（R11 修复在文档核对工作流层加 infra 不缓存；字段识别链在 R42-01 才补「终态失败复核分片重排补偿」`mapping_confirmation.py:2162-2196`）。
- **伴生实证**：R32-04——265 个识别分片 `queue_dwell_timeout` 终态失败且 attempt_count=0（LB 域全部沦陷），界面只笼统显示「部分识别任务已终态失败」（`mapping_candidate_routes.py:681-724` 注释原文）；R5 REPORT.md:35 预置收敛循环中「blocked/running 反复振荡、confirm 422×5」——失败态在作业台账与投影间振荡。

### 冲突4：死锁变体族（同一根因的历次投影，代码内均有遗迹注释）

| 变体 | 轮次 | 代码遗迹 |
|---|---|---|
| 「采用已识别的X个字段并继续」诱导提交→后端422→死锁 | R19-01 | `mapping_pipeline.py:2192-2197` 注释（needs_attention 仅在全部终态且有失败时报告；未终态一律 generating「前端按钮态与后端校验同源」） |
| 识别已完成但确认路径不存在（needs_attention 拒绝采纳） | R3循环报告C | `mapping_confirmation.py:484-503` 注释（R35-01 知情降级采纳入口） |
| 阻断组无入口（blocked-group 恒在、零角色编辑控件、确认按钮恒disabled约60分钟） | R41-01 | `mapping_candidate_routes.py:577-587,632-667` 注释（公开投影曾剥掉 rule_id/affected_fields，「死锁文案」） |
| 复核在作业全终态下不收敛 | R5-ISO/3-01家族 | ISO_ENV_LOG.md:51（「全部20个mapping job已终态(19完成+1失败)——复核状态机在job全终态下不收敛」）；R36-01 复核聚合进度/降级确认 `mapping_confirmation.py:2087-2124`、`mapping_candidate_routes.py:764-783` |
| 确认请求 47 分钟 pending 永久卡死 | R3循环报告D | `MedicalMonitoringAdmissionWizard.jsx:1704-1707` CONFIRM_STALE_MS 注释 |
| 跨批次/刷新后 ETA 归零、439↔144分钟跳变 | R44-02 | `mapping_pipeline.py:2221-2236`（服务端 pace 窗口）注释原文 |

---

## 三、单一权威源候选评估

### 候选1（推荐）：`monitoring_mapping_drafts` + `monitoring_ai_jobs`（A2，同库 sqlite）作映射/识别状态权威
理由：唯一同时具备 **CAS/版本（UNIQUE(project_id,batch_id,profile_sha)、expected_version、idempotency_key）、审计链（edit_operations/adjudication_receipts/revisions）、事件史（activation_history/binding_history）** 的存储（`monitoring_mapping_draft_repository.py:920-1010`、`monitoring_mapping_activation.py:298-370`）；运行门 B5 已经读它（main.py:1156）。现场可查：20表齐全、draft v80 confirmed 可靠。
缺口：需要把 B1 的 `state` 推导（generating/candidates_ready/needs_attention）落为持久列或派生视图（现为由请求时作业行集合重算）；需要吸收 A5 的核对批次状态机（文件态、无 SQL 约束）。

### 候选2：`source_registry.jsonl`（A1）作文档权威
已具备：唯一被 `MonitoringDocumentEvidenceResolver` 与晋升链共同消费的登记处，promoted+receipt+replay 验证闭环（source_intake.py:694-711、monitoring_document_authority_jobs.py:1245-1253）。缺口：JSONL 全量重写+文件锁（source_intake.py:522-609）在并发与规模下弱于 sqlite；且其「verified」语义依赖每次对 A2 的重放（无缓存，68s 探针实证），作单一权威前需把验证结论物化（缓存失效绑 registry_revision）。

### 候选3：`canonical_fact_materialization` 域对象（A4）作事实权威
唯一事实终态持有者（本次探针 facts=true 与 candidates 投影 facts_generated=False 的矛盾中，**它是真值方**）；per-project sqlite + artifacts 快照摘要校验。缺点：作用域限于事实层，不覆盖核对/识别/映射三段。

### 结构性建议（供专项 run 决策，非本次改动）
- 单一权威 = **A2（识别+映射+激活）∪ A4（事实）∪ A1（文档登记，验证结论物化缓存）**，统一「project+attempt+阶段」键；
- 路由层（B1-B3, B7）全部改为该权威的只读投影——本次实证的四个矛盾字段（facts_generated 顶层/summary.pending_confirmation_count/confirmation_status/verification.summary）应从同一行推导；
- 删除 C1-C7 中的**状态推导**（保留纯 UI 态如 in-flight/计时），前端只渲染后端 state——R9 拍板与 HANDOFF 方案A（第75-78行）一致；
- 运行门与向导共用同一查找键（B5 的 project-latest vs `find_draft_for_batch` 的 attempt-batch 二义性必须消解，R9 家族的残留机理）。

---

## 四、本次探针命令与输出（诚实清单）

| # | 命令 | 结果 |
|---|---|---|
| 1 | `curl -s http://127.0.0.1:8911/api/runtime-readiness` | 200 `{"ready":true,...,"backend_build_id":"api-5f86f3eb6ec412e7"}` |
| 2 | `curl -s http://127.0.0.1:8911/api/projects` | 常驻项目 `proj_user_6ef58ac151e1`（MX循开考-CSU） |
| 3 | `curl -s .../data-admissions/latest` | `stg-cd69899943ba42618f589ba07a134a59`, state=`profile_ready` |
| 4 | `curl -s ".../mapping-candidates?focus=all"`（HTTP 200, 0.36s） | 见冲突1表：confirmed + pending_confirmation_count=60 + facts_generated=False + verification pending=0 |
| 5 | `curl -s ".../facts"` | `{"state":"ready","facts_generated":true,"summary":{tables:10,rows:591,values:3038,source_values_verified:3038}}` |
| 6 | `curl -s ".../study-documents"` | 第一次 90s 超时（HTTP 000）；重试 200 但耗时 **68.3s**；`ready:true`，protocol/ecrf=`current`，IB/SAP=`missing`——B4 无缓存的 receipt 重放成本实证 |
| 7 | `sqlite3 -readonly .../medical_monitoring_ai.sqlite3 "SELECT name FROM sqlite_master WHERE type='table'"` | 20 表（清单见 A2） |
| 8 | `sqlite3 -readonly ... "SELECT draft_id,batch_id,status,version,updated_at FROM monitoring_mapping_drafts WHERE project_id='proj_user_6ef58ac151e1'"` | `monmapdraft_73abe5c6c9561a9e95eec2056991\|stg-cd69...\|confirmed\|80\|2026-10-05` |
| 9 | `sqlite3 -readonly ... "SELECT status,COUNT(*) FROM monitoring_ai_jobs WHERE project_id='proj_user_6ef58ac151e1' GROUP BY status"` | completed=44, failed=2 |
| 10 | python 只读统计 `source_registry.jsonl` | 156 行；常驻项目 2 条（protocol_docx, ecrf_document）均 promoted |
| 11 | `monitoring_mapping_project_state` 只读查询 | **0 行**（激活表在常驻项目上为空——映射激活链尚未被该路径使用，如实记录） |

**未做/不可做（如实声明）**：①未探查 R44-01「研究文件核对独立性诊断失败」的现场（本轮无复现请求）；②未读 `STATE_V2.json` 158 条台账全文核对每条在册单（仅核对 REQUEST 中点名的 R9/R21/R22/R23/R5/R11 报告原文与 ISO_ENV_LOG 行）；③未运行任何写路径或重试端点（只读纪律）；④study-documents 68s 是单次采样，未做基准重复。

## 五、一句话结论

第3步的「权威」事实上有五个半（A1/A2/A4/A5/A6 + A3），每次请求由 B1-B7 现场重算三套互相不一致的投影，前端再用三组本地态各自镜像其中之一（C1-C7），运行门又用第四种读法（B5/B6）——R9 拍板的「状态碎片化」、R21-R28 轮轮记录的「投影怪癖」、R11 的「失败缓存复用」在代码级全部收敛到本图 A/B/C/D 四节的具名坐标；重构的最小充分动作是把 B1/B2/B3/B7 的推导统一到 A2+A4 的持久行上并让 C 组降级为纯渲染。
