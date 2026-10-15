# 02_DESIGN — 第3步单一权威状态模型设计（状态机重构专项·实施设计）

> 设计日期：2026-10-14。前置底稿：同目录 `01_STATEMAP.md`（本设计的 A/B/C/D 编号沿用其状态持有者地图）。
> 设计依据：本次逐段读取的代码（引用均带 `file:line`，均为本次实际读到）+ 01_STATEMAP 探针记录（引用处标注"考古报告"）+ HANDOFF_40ROUNDS_20261014.md 方案A（第74-78行）。
> 设计性质：**实施设计**（DDL、函数契约、逐文件改造点、逐步迁移与验证命令），非概念图。未运行任何改造代码——第9节如实声明验证边界。

---

## 0. 设计总纲（一句话 + 一张图）

**权威不动、物化补缺、投影单源、前端降级为渲染。**

四个既有权威存储原位复用（零数据迁移）：A2（`medical_monitoring_ai.sqlite3`：jobs+drafts）、A4（`canonical_fact_materialization` 域对象）、A1（`source_registry.jsonl`）+A3（校验库）、A5（文档批次文件态）。只新增两张小表（与 A2 同库、同事务可达）：**阶段状态行表**（补"识别聚合态无持久行"这一唯一权威缺口 + F5 恢复锚点）与**阶段事件流表**（补"变迁无留痕"）。所有投影（B1/B2/B3/B7）收敛到单一视图函数；前端 C1-C7 删除状态推导、只渲染后端 state/action_key。运行门（B5/B6）**保持直接读权威 fail-closed，永不读物化行**。

```
权威层（不动）                物化层（新增，同库同事务）           投影层（单源化）              前端（只渲染）
A1 source_registry  ─┐
A3 校验库            ├─ documents ─┐
A5 批次文件态        ┘             │
A2 monitoring_ai_jobs ─ recognition ├─ stage_state 表 ──→ admission_stage_view ──→ GET stage-state ──→ C1/C2/C4/C5/C7 只渲染
A2 drafts(+revisions)─ mapping   ─┘        + events 表（变迁留痕）      （每字段唯一推导式）      mapping-candidates 等既有端点 ──→ C3 只渲染
A4 facts 域对象      ── facts（不需要状态行，A4 即权威行）
```

---

## 1. 权威归属决策（含"为什么不能更省"）

| 阶段 | 权威（复用，零迁移） | 已具备 | 缺口（本设计补） |
|---|---|---|---|
| 文档核对 | A1 `source_registry.jsonl`（promoted+receipt）+ A5 批次状态机 + A3 校验库 | 持久、有晋升验证闭环（`source_intake.py:694-711`，考古报告A8） | ①批次状态变迁无事件流；②A8 每请求重放 68s（考古报告探针#6）→ Step 8 物化缓存 |
| 字段识别 | A2 `monitoring_ai_jobs`（行级状态机 queued/running/completed/failed/blocked/stale_input/cancelled，`monitoring_ai_repository.py:359-392`） | 持久、UNIQUE 去重、retry_terminal 显式重试（`:2195-2294`） | **聚合态（generating/candidates_ready/needs_attention）每次请求由 B1 现场重算（`mapping_pipeline.py:2200-2208`），无持久行、无变迁留痕** → stage_state.recognition 行 |
| 映射确认 | A2 `monitoring_mapping_drafts`（draft→confirmed 两态 + version CAS + confirmed 不可变触发器 `monitoring_mapping_draft_repository.py:920-1033`） | 权威完备（考古报告候选1判定，本次核实表结构属实） | 无权威缺口；仅投影/查找键问题（见 §4） |
| 事实 | A4 `canonical_fact_materialization`（state: not_generated/ready，`fact_materialization.py:616-617,:640`） | 唯一真值方（冲突1中它是真值，考古报告候选3） | 无权威缺口；仅投影反填问题 |

**为什么不建"一张大总表"**：第3步四阶段各有天然权威行，且映射确认已有 CAS+审计链（edit_operations/adjudication_receipts/revisions，`:955-1011`）——重造一张总表等于把最成熟的权威降级。缺的只是①识别聚合态的持久行；②跨权威的事件流；③单一投影函数。新增两张**附加**表即可，权威 schema 零变更、零数据迁移，任何一步可 DROP 回滚。

**为什么 stage_state 必须建（不能只加事件表+纯派生）**：
1. **F5 后状态恢复**需要后端一句话回答"这个 attempt 到哪了"——现状无此物（C2 用 localStorage 记"2"，`MedicalMonitoringAdmissionWizard.jsx:2260-2287`）；
2. **降级入口服务端化**（死锁根治点2）需要服务端持久的 stalled 判定，不能靠前端 30 分钟计时器（`medicalMonitoringAdmissionMappingConfirmState.mjs:17`）；
3. **"每个状态变迁必须落事件留痕"**要求变迁点存在——纯派生态的"变迁点"=每次投影请求，无留痕可言。

---

## 2. 新增表 DDL（与 A2 同文件 `runtime/medical_monitoring_ai.sqlite3`，随 `MonitoringAiRepository._initialize` 建表）

装配点：`main.py:1124-1140`（AI仓）与 `main.py:1151-1153`（drafts 仓同文件）已证实同库；`MonitoringAiRepository._connect` 用 WAL（`:346`），同库内跨仓同事务可行。

### 2.1 `monitoring_admission_stage_events`（事件流，append-only）

```sql
CREATE TABLE IF NOT EXISTS monitoring_admission_stage_events (
    event_id      TEXT PRIMARY KEY,           -- ULID（时序可排序）
    project_id    TEXT NOT NULL,
    attempt_id    TEXT NOT NULL DEFAULT '',
    stage         TEXT NOT NULL
                  CHECK(stage IN ('documents','recognition','mapping_confirmation','facts')),
    event_type    TEXT NOT NULL,              -- state_changed | failure_recorded |
                                              -- recovery_action | degradation | gate_blocked | stage_view_divergence
    from_state    TEXT NOT NULL DEFAULT '',
    to_state      TEXT NOT NULL DEFAULT '',
    reason_code   TEXT NOT NULL DEFAULT '',   -- 既有 failure_code / 门 code 原样
    failure_class TEXT NOT NULL DEFAULT ''
                  CHECK(failure_class IN ('','infra','content','contract')),
    actor         TEXT NOT NULL DEFAULT '',   -- principal_id / 'system' / 'workbench-system'
    detail_json   TEXT NOT NULL DEFAULT '{}', -- 摘要级：计数/表名/draft版本/requeued_count。
                                              -- 禁止：作业身份(job_id/provider/model)、原文载荷（与公开投影同规约）
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_stage_events_attempt
    ON monitoring_admission_stage_events(project_id, attempt_id, created_at);
CREATE TRIGGER trg_stage_events_no_update BEFORE UPDATE ON monitoring_admission_stage_events
BEGIN SELECT RAISE(ABORT,'admission stage event is immutable'); END;
CREATE TRIGGER trg_stage_events_no_delete BEFORE DELETE ON monitoring_admission_stage_events
BEGIN SELECT RAISE(ABORT,'admission stage event deletion is forbidden'); END;
```
不可变触发器沿用库内既有风格（`monitoring_mapping_activation.py:370-388`、`monitoring_mapping_draft_repository.py:1022-1033`）。

### 2.2 `monitoring_admission_stage_state`（阶段状态行）

```sql
CREATE TABLE IF NOT EXISTS monitoring_admission_stage_state (
    project_id  TEXT NOT NULL,
    attempt_id  TEXT NOT NULL,                -- documents 阶段允许多批次：attempt_id 存批次所属 attempt；
                                              -- 批次级状态仍以 A5 文件态为权威，此行是跨阶段索引投影
    stage       TEXT NOT NULL
                CHECK(stage IN ('documents','recognition','mapping_confirmation','facts')),
    state       TEXT NOT NULL,                -- 枚举见 §3
    detail_json TEXT NOT NULL DEFAULT '{}',  -- 阶段参数：stalled_since/inflight_adoption_available/
                                              -- draft_id/version/retryable_failure_count/registry_revision
    revision    INTEGER NOT NULL,             -- 行级单调版本，供轮询 If-None-Match 与 F5 对账
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (project_id, attempt_id, stage)
);
```
**facts 不建状态行的裁决**：A4 域对象本身就是 per-attempt 持久行级权威（`fact_materialization.py:600` 写入、`:609-627` 直查），再建一行只是复制品；facts 的 stage_state 行由物化服务在 A4 提交后 best-effort 维护（仅为 stage-state 端点聚齐四行用），**门与投影的 facts 判定永远直查 A4**（`main.py:4133` 现状保持）。

### 2.3 写入纪律（fail-closed 不放松的具体含义）

| 权威 | stage_state/events 写法 | 一致性保证 |
|---|---|---|
| A2 jobs（识别） | 与作业状态写**同一 sqlite 事务**（同文件） | 原子，无漂移窗口 |
| A2 drafts（映射） | 与 draft 写**同一事务**（同文件） | 原子 |
| A5 批次文件（文档） | 文件态先行（权威），随后事件+状态行；进程崩溃丢事件不丢权威 | 事件是留痕不是权威；补偿扫描器（启动时按 A5 重放补行）在 Step 7 落地 |
| A4 facts（跨库 sqlite） | A4 提交后 best-effort 维护 stage_state.facts 行 | 门/投影直查 A4，best-effort 行只影响端点聚合展示，不影响任何判定 |

---

## 3. 权威状态表：状态枚举、变迁条件、谁写谁读

### 3.1 stage=documents（研究文件核对）

状态枚举（stage_state.documents.state）：`not_started | in_progress | needs_user_input | failed | ready`

| 变迁 | 条件 | 写入函数（谁写） | 事件 |
|---|---|---|---|
| not_started→in_progress | 用户上传研究文件，批次创建+分析作业提交 | `MonitoringDocumentAuthorityWorkflow.start`（`monitoring_document_authority_workflow.py:207` 返回 analyzing） | state_changed, actor=user |
| in_progress→in_progress | advance 轮询，作业仍在跑（无状态跨越时**不落事件**，只 lease/心跳） | `advance`（`:306-313`） | 无 |
| in_progress→needs_user_input | 身份门不一致待人工裁决 / 角色裁决挂起 / 内容差异确认挂起 | `advance`（`:335-359` 起的身份裁决分支） | state_changed, reason_code=identity/role/content |
| in_progress→failed | 作业终态失败且预算耗尽/契约退役 | `advance`（`:1310-1317` failed_jobs 聚合） | failure_recorded, failure_class=infra\|content\|contract |
| needs_user_input→in_progress | 用户提交角色裁决/身份确认/差异确认 | `advance`（user_role_selections/identity_confirmation 参数，`:224-232`） | recovery_action |
| failed→in_progress | 显式重试（「重新核对研究文件」按钮）/ 重传同组文件触发重排 | `advance` explicit_retry（`:232,:283-305`）、`start` 对终态失败作业 retry_terminal（`:187-205`） | recovery_action |
| 任意→ready | 全部必需角色 A1 promoted + A8 replay 通过 + A3 校验 ready（B4 resolver 判 current） | promote 链（`monitoring_document_authority_jobs.py:1245-1253`，考古报告）后由 resolver 首次核验通过时写行 | state_changed |

谁读：GET `study-documents` 投影（`mapping_candidate_routes.py:935-1006`，考古报告D节）、前端 C4、主按钮 documents 分支（`Wizard.jsx:1313-1372`）。

### 3.2 stage=recognition（字段识别）

状态枚举（stage_state.recognition.state）：`not_started | generating | candidates_ready | needs_attention`
——**三态语义与 B1 现契约逐字保持**（`mapping_pipeline.py:2192-2208`：needs_attention=全终态且有失败；未终态一律 generating），不在状态枚举里加第四态。"知情降级可采纳"是 generating 上的**标志位**而非状态：`detail_json.inflight_adoption_available`（见 §5.3）。

| 变迁 | 条件 | 写入函数（谁写） | 事件 |
|---|---|---|---|
| not_started→generating | cohort 首个作业入队 | `MonitoringAiRepository.create_or_get`（`:629-677`，INSERT 分支） | state_changed |
| generating→candidates_ready | 最后一片 complete | `complete`（`:2014`） | state_changed |
| generating→needs_attention | 最后一片进入终态失败 | `fail`（`:2097`）/ `mark_stale`（`:2371`）/ `fail_queued_jobs_exceeding_dwell`（`:1036`） | failure_recorded，failure_class 按 `_INFRA_FAILURE_CODES`（§5.1）分类 |
| needs_attention→generating | retry_terminal 重排任一分片 | `retry_terminal`（`:2195-2294`） | recovery_action（explicit 与自动预算分别记 actor/detail） |
| candidates_ready→generating | 新提交合同再识别（input revision 变化，新作业组） | `create_or_get` 新组 INSERT | state_changed |

写入实现：上述五个写方法各加一行 `self._stage_events.append(...)` + `self._stage_state.bump_recognition(project_id, attempt_id)`，与作业状态写同一事务（同文件 sqlite）。attempt_id 从 business_key 前缀解析（`contract.job_business_key_prefix(attempt_id)`，`mapping_pipeline.py:1578-1582` 已证实该前缀含 attempt）。
谁读：stage_view（→GET mapping-candidates 投影）、`adopt_draft` 的状态校验（`mapping_confirmation.py:498-506`）、前端 C3。

### 3.3 stage=mapping_confirmation（映射确认）

状态枚举（stage_state.mapping_confirmation.state）：`no_draft | draft_active | confirmed`（detail_json 带 draft_id/version；confirmed 对应权威行 status='confirmed'，不可变触发器 `:1022-1027` 兜底）。

| 变迁 | 条件 | 写入函数（谁写） | 事件 |
|---|---|---|---|
| no_draft→draft_active(v1) | 采纳：state=candidates_ready；或 needs_attention 部分采纳；或 generating 且服务端 inflight_adoption_available（§5.3） | `AdmissionMappingConfirmationService.adopt_draft`（`mapping_confirmation.py:467-506`）→ 仓 upsert | state_changed；降级采纳另记 degradation |
| draft_active(vN)→draft_active(vN+1) | 逐字段编辑 / 裁决（CAS expected_version） | `edit_field` / adjudicate（仓 `:1444+`、`:1801` confirm 相邻方法族） | state_changed |
| draft_active→confirmed | 疑点全部已答（`:2081-2084`）+ 双盲复核收敛或显式知情降级（`:2087-2124`，_DEGRADABLE_DUAL_REVIEW_CODES `:2056-2062`） | `confirm_draft`（`:2064-2160`）→ 仓 confirm（`:1801`） | state_changed；降级另记 degradation（degraded_note 已落 confirmation_reason `:2125-2129`） |

谁读：B3 投影（`:425-465`）、B5 运行门（`main.py:1156-1190`，读权威 drafts）、stage_view、前端 C3。

### 3.4 stage=facts（事实物化）

状态枚举：`not_generated | ready`（A4 唯一两态，`fact_materialization.py:616-617,:640`）。**失败不落持久失败态**：generate 抛错只落 `failure_recorded` 事件（failure_class 分类），A4 保持无行/not_generated，重试路径天然开放——这是"失败态永不缓存复用"在事实层的表达。

| 变迁 | 条件 | 写入函数 | 事件 |
|---|---|---|---|
| not_generated→ready | 物化成功（全部 fact_set 校验通过，`:577-600`） | `FactMaterializationService.generate`（put_domain_object `:600`）后 best-effort 维护 stage_state.facts 行 | state_changed |
| ready→not_generated | 不存在（ready 是终态；重导入走新 attempt 新键） | — | — |
| （无状态变化） | generate 失败 | 同上 service | failure_recorded（reason_code=facts_generation_failed `:605`） |

谁读：GET facts（A4 直查）、B6 运行门（`latest_fact_materialization_ready` `:649-675`，`main.py:4133` 消费）、投影反填 facts_generated、前端 C5。

### 3.5 跨阶段聚合：`current_stage` 与 `blocking[]`（stage-view 出口）

```
current_stage = 第一个 state ∉ {ready/confirmed/candidates_ready 视阶段而定} 的阶段；
全部就绪 = "complete"。
blocking[] 不变量（投影层强制，违反→500 fail-closed）：
  任何非完成阶段必须在 blocking[] 携带 ≥1 个 action_available=true 的动作键。
```
动作键枚举（前端文案表只认 key）：`upload_documents / retry_document_check / resolve_role_adjudication / confirm_identity / retry_recognition_failed(→retry-failed 端点 `mapping_candidate_routes.py:1684-1688`) / adopt_partial / adopt_inflight_degraded / answer_questions / resolve_blocked_groups / confirm_mapping_degraded / generate_facts / retry_generate_facts`。

---

## 4. 事件流定义

**事件即留痕，不是权威**：判定永远读权威行；事件用于 ①审计（44轮"每轮如实记录"的服务端化）②F5 恢复对账 ③影子校验记录（Step 2）④死锁取证（R3/R19/R41 类"卡在哪一步"直接可查）。

统一写入 API（新模块 `services/api/app/monitoring_admission_stage_store.py`）：

```python
class AdmissionStageStore:            # 持有 ai.sqlite3 连接工厂；与各仓共用 _connect 语义
    def append_event(self, conn, *, project_id, attempt_id, stage, event_type,
                     from_state="", to_state="", reason_code="", failure_class="",
                     actor="system", detail=None) -> None          # 必须传入外层 conn（同事务）
    def bump_stage(self, conn, *, project_id, attempt_id, stage,
                   state, detail=None) -> None                      # revision 自增
    def get_stage(self, project_id, attempt_id, stage) -> Row
    def list_events(self, project_id, attempt_id, *, after="", limit=200) -> list
```
写入点清单（§3 各表"事件"列的全部行）：`MonitoringAiRepository` 5 个写方法、`MonitoringMappingDraftRepository` upsert/edit/confirm、`MonitoringDocumentAuthorityWorkflow` start/advance 各返回分支、`FactMaterializationService.generate` 成功/失败分支、两个运行门阻断时（gate_blocked，采样记录：仅阻断时写，放行不写，避免启动路径写放大）。

---

## 5. 死锁家族根治点（四条逐一）

### 5.1 失败态永不缓存复用

机理（考古报告冲突3 + 本次代码核实）：`create_or_get`（`monitoring_ai_repository.py:629-677`）按确定性 job_id 命中**任何**既有行——含 failed——原样返回；A7 画像缓存按内容键命中（`monitoring_ai_field_profile_cache.py:53-95`）。是否复用失败全看上层是否区分错误类别（R11 只在文档链修了 `_recover_failed_once`，`monitoring_document_authority_workflow.py:1350-1399`）。

**根治：把 R11 的判据下沉为库层不变量 + 显式动作语义。**
1. 把 `_INFRA_FAILURE_CODES`（`:1323-1334`）提取为 `monitoring_ai_contracts.py` 共享常量 `INFRA_FAILURE_CODES`（文档链原引用改为导入，行为零变化）；
2. `create_or_get` 命中既有行为终态失败（failed/blocked/stale_input）且 `failure_code ∈ INFRA_FAILURE_CODES` 且无 `contract_retirement_code` 时，**不原样返回**——按**显式重试**语义调 `retry_terminal`（不传 automatic_recovery_limit，与 R28-03「用户显式动作不受自动预算约束」同权，`monitoring_document_authority_workflow.py:1381-1386` 先例）后返回重排后的行，并落 `recovery_action` 事件（actor=提交请求的 principal）。理由：同请求身份再次提交=用户刚刚点了生成/重传按钮，就是显式动作。
3. **边界保持 fail-closed**：content/contract 类失败、契约退役行、input revision 已变化的行，维持现状（原样返回或 MonitoringAiStateConflictError），绝不重排；
4. A7 画像缓存无需改（它只缓存字段画像不缓存失败结论，`cache_entry_absent`/digest 校验语义已安全）。
5. 识别链 create_or_get 调用点在实施前逐一核实（见 §9 未验证项3），Step 6 以 env 开关灰度。

### 5.2 降级入口（「采用已识别字段继续」）何时出现

现状：入口出现与否由**前端本地计时**决定（`MAPPING_STALL_THRESHOLD_MS=30min`，`medicalMonitoringAdmissionMappingConfirmState.mjs:17`；`adjudicationStalledMs` 超阈值放行 reload，`:788-800`），后端只认 `allow_inflight_adoption` 标志（`mapping_confirmation.py:498-506`）。前后端各自判定→可能出现"前端有按钮后端必拒"或反之。

**根治：停滞判定服务端化，前端只渲染标志。**
- 服务端：`detail_json.stalled_since` 复用 R44-02 的服务端 pace 窗口（`mapping_pipeline.py:2221-2236` `_generation_pace`：最近完成时刻窗口已在服务端计算）；窗口末次完成距今 >30min（阈值常量从前端常量上收为服务端常量）且已有候选 → `inflight_adoption_available=true`；
- 投影：GET mapping-candidates 顶层带 `inflight_adoption_available`；
- 前端：删除本地计时驱动按钮的逻辑，按钮渲染读标志；点击仍走 `include_incomplete`（`mapping_candidate_routes.py:1805`），后端校验（`:498-506`）原样保留=**入口出现的判定单源化，但后端门禁不放松**（标志计算有竞态时后端 422 仍兜底，前端保留现有 422→错误提示路径）。

### 5.3 阻塞组（「还有N组待处理」）必有处理入口

现状：R41-01 已修数据面（finding_groups 随组下发 rule_id/affected_fields/role_catalog，`mapping_candidate_routes.py:632-667`）；但"入口必在"仍是逐案修复，无结构保证。

**根治：把"必有入口"上升为投影层不变量。** `admission_stage_view.build_stage_view` 产出 `blocking[]` 时执行 §3.5 不变量校验：非完成阶段无 actionable 动作键 → 直接 500 `mapping_bridge_failed`（fail-closed 暴露缺陷而非渲染死锁文案）。blocked-groups 场景动作键=`resolve_blocked_groups`（R41-01 的组内处置控件即其执行体）；质量门阻断场景动作键由 `semantic_quality` 各 rule 映射。回归门：`tests/test_stage_state_endpoint.py` 用 R41/R3 各实测形态做参数化断言（blocked-group 恒在/零编辑控件/确认恒禁用三种历史形态在投影层都必须产出 action_available 键）。

### 5.4 F5 后状态恢复

现状：C2 localStorage 记步骤号（`Wizard.jsx:2260-2287`），刷新后 C1/C3/C4/C5 全部从 idle 重推，R9-02 类"步骤条第3步、主体第1步"即本地态与载荷失步形态（考古报告冲突2③）。

**根治：恢复=一次权威查询。**
- 新端点 `GET /api/projects/{p}/modules/medical-monitoring/r7/data-admissions/{attempt}/stage-state`（projection 权限，无写门）：返回 `{attempt_id, stages:{documents,recognition,mapping_confirmation,facts}, current_stage, blocking[], inflight_adoption_available, primary_action_key, revision}`；
- 前端：向导挂载时以 stage-state 替代 localStorage 恢复（C2 两段 useEffect `:2260-2287` 删除；stepIndex 由 `current_stage` 单向映射：documents未就绪→第3步文档面板激活，就绪→映射面板，以此类推）；C3/C4/C5 的 load-ready 派生保留但**源字段切换**（§6）；
- 轮询：携带 `revision`，未变化返回 304 语义（减少 R31-03 类轮询打翻本地态的诱因）。

---

## 6. 投影改造清单（每个投影：从哪读权威、本地推导删除点）

### 6.1 后端 B1/B2/B3/B7 → `admission_stage_view`（新模块 `packages/medical_monitoring/admission/admission_stage_view.py`）

**每字段唯一推导式表**（本表是投影单源化的规范，四个矛盾字段的现状出处=冲突1四行）：

| wire 字段 | 唯一推导式（改造后） | 现状多头出处（删除/收编点） |
|---|---|---|
| 顶层 `state` | `stage_state.recognition.state`（物化） | B1 每请求重算 `mapping_pipeline.py:2200-2208` → Step 2 影子期保留重算作比对，Step 3 起只读物化+失败即 500 |
| 顶层 `confirmation_status` | drafts 权威行 status（attempt 键 `find_draft_for_batch`，仓 `:1379-1413`） | B1 硬编码 `"pending_confirmation"`（`:2214`）与字段级硬编码（`:2189`）→ 删除；B3 覆盖逻辑（`:456-463`）收编进 stage_view 成为唯一写点 |
| 顶层 `facts_generated` | A4 直查（attempt 键，`fact_materialization.py:609-627`） | B2 无条件 False（`mapping_confirmation.py:322`）→ 删除；confirm 响应硬编码 False（`:2141`）→ 改调 A4 直查函数（值不变来源变） |
| `summary.pending_confirmation_count` | 无 draft→candidate_count；draft_active→draft 内未确认字段数；confirmed→0 | B1 硬编码 `len(mappings)`（`:2219`，确认后永不更新=冲突1实测60）→ 删除；`verification.summary` 同包第三口径（考古报告冲突1第4行）→ 同函数推导 |
| 字段级 `confirmation_status` | draft.fields 匹配（domain,source_field）→ confirmed/else pending | B1 硬编码（`:2189`）→ 删除 |
| `user_question_count` / `critical_count` / `system_adopted_count` | `enrich_candidates` 保留（纯计数聚合 `:308-316`） | 无变化 |
| `verification.summary` | verifier cohort 的 stage_state 轻量行 | GET 双装配（`mapping_candidate_routes.py:1639-1670`）保留装配来源，聚合数改读物化 |

`_public_mapping_projection`/`_public_draft`（B7，`:727-806`/`:604-678`）**白名单机制保留**（它是防作业身份外泄的闸，`:784-805` 禁词校验不动），仅数据来源换成 stage_view 输出；R41-01 组下发（`:632-667`）与 R32-04 table_failures（`:681-724`）原样保留并纳入 blocking[] 动作键。

### 6.2 运行门（不改读法，只收口查找键二义性）

- B5 `_r7_mapping_confirmation_gate`（`main.py:1156-1190`）**保持读 `latest_draft_for_project` 权威 fail-closed**——它读的就是权威，R18-03 修复不回退；
- B6 facts 门（`main.py:4118-4135` + `:4148-4156`）保持 A4 直查 + created_at 最新 attempt——**Step 4 起门与投影共享同一 attempt 归属函数**（`_latest_attempt_id(project)` 提取公用，消除 `main.py:4148-4156` 与 `fact_materialization.py:652-659` 两处同逻辑重复）；
- 二义性消解在**投影侧**：stage_view 的 mapping_confirmation 输出 `confirmation_scope`：`find_draft_for_batch(project, attempt)` confirmed 且 `latest_draft_for_project` 同为该 draft → "confirmed"；latest 是**别的 attempt** 的 confirmed/未确认草稿 → 本 attempt 如实显示未确认 + blocking 注明"项目存在更新导入"。门语义不变（任一未确认即 409），两键不再暗中打架而是显式披露。

### 6.3 前端 C1-C7（删除推导、保留纯 UI 态）

| 持有者 | 改造 | 删除点 | 保留（纯 UI 态，不参与语义判定） |
|---|---|---|---|
| C1 向导壳 | stepIndex/phase 由 stage-state 单向映射 | `medicalMonitoringAdmissionWizardState.mjs:260-354` 中 advance/back/retry 的**步骤推导**保留导航语义但初值来自端点 | 输入框/文件选择本地态 |
| C2 localStorage | **整段删除** | `Wizard.jsx:2260-2287` | — |
| C3 映射确认 | phase 收敛为渲染态：`stages.recognition.state`/`stages.mapping_confirmation.state` 直接映射；load-ready 不再从 `confirmation_status`/`draft.status` 推 confirmed | `medicalMonitoringAdmissionMappingConfirmState.mjs:634-644` 的二次推导布尔 → 改读 `stages` 字段；`:627-631` 三态文案改渲染 state | answeredKeys、in-flight、停滞计时（仅作提示UI，不再决定按钮可用性） |
| C4 文档核对 | documentPhase 直接镜像 `stages.documents.state` | `Wizard.jsx:1276-1296` 阶段键合成保留计时展示；`:1313-1372` 主按钮 documents 分支的 6 层 if 推导 → 后端 action_key | 上传中 in-flight ref |
| C5 事实 | 镜像 `stages.facts.state` | `Wizard.jsx:1717-1718` 初始态保留、推导删除 | 生成中 in-flight |
| C6 防重入 refs | 保留防重入；**删除"超时本地翻转语义"**：CONFIRM_STALE_MS（`:1704-1708`）改为超时触发"重读 stage-state"而非本地放行 | — | 请求代际计数（竞态防护是纯 UI 职责） |
| C7 主按钮 | 消费后端 `primary_action_key`（枚举见 §3.5），前端只留 key→label 文案表 | `Wizard.jsx:1306-1374` 的跨三本地态合成 | 文案表（纯渲染） |

---

## 7. 分步迁移路径（每步独立可验证 + pytest）

基线（本次实测）：`python3 -m pytest tests/test_mm_c3_mapping_confirmation.py tests/test_mapping_inflight_adoption_r35.py tests/test_monitoring_ai_queue_dwell_timeout.py -q` → **62 passed**；`node --test frontend/src/features/medical-monitoring/medicalMonitoringAdmissionMappingConfirmState.test.mjs` → **33 pass / 0 fail**（该 feature 下另有 60 个 .test.mjs）。每步合并前跑该步新测试 + 基线三件套 + `tests/test_monitoring_ai_repository.py tests/test_monitoring_ai_mapping_gate.py tests/test_mm_c3_dual_mapping_cohort.py`。

| 步 | 内容 | 新增验证（pytest） | 回滚 |
|---|---|---|---|
| **S1 地基** | 建两张表+AdmissionStageStore+五个仓写方法埋事件（双写，读路径零变化） | `tests/test_admission_stage_events.py`：变迁→事件存在；no_update/no_delete 触发器生效；failure_class 分类正确；同事务性（作业失败回滚则事件不存） | revert 代码；表留存无害 |
| **S2 识别态物化（影子期）** | stage_state.recognition 随作业写点维护；投影仍用派生值，每次派生与物化比对，不一致记 `stage_view_divergence` 事件 | `tests/test_stage_state_recognition.py`：§3.2 全变迁矩阵+并发 retry 竞态 | env `STAGE_VIEW_MODE=derive` 一键回派生 |
| **S3 投影单源** | 上 stage_view；删 B2 `:322`、B1 `:2189/:2214/:2219`；B3 覆盖收编；confirm `:2141` 改 A4 直查 | `tests/test_projection_single_source.py`：**冲突1场景参数化断言**——confirmed draft + facts ready 时，同投影内 pending_confirmation_count=0、facts_generated=true、verification 口径一致 | 单 PR revert |
| **S4 查找键收口** | stage_view 加 `confirmation_scope`（attempt 键 × project-latest 键显式披露）；门不动；`_latest_attempt_id` 提取公用 | `tests/test_gate_lookup_key_consistency.py`：新 attempt 未确认→门 409+投影如实；旧 attempt confirmed 不放行新 attempt（R18-03 语义回归） | revert |
| **S5 降级入口服务端化** | stalled_since 服务端计算（pace 窗口）+ `inflight_adoption_available` 投影 + adopt 门校验不变 + 前端按钮改读标志 | `tests/test_inflight_adoption_server_flag.py`：停滞→available→adopt 过；未停滞→adopt 422 mapping_run_incomplete | 前端回退本地计时（后端标志向前兼容） |
| **S6 失败不缓存下沉** | `INFRA_FAILURE_CODES` 提取共享；create_or_get 命中 infra 终态失败→显式重试重排（env 灰度） | `tests/test_infra_failure_not_cached.py`：R11-01 场景——503 失败行→同请求重发→requeued；content/contract 失败仍原样返回 | env 关闭新行为 |
| **S7 stage-state 端点+前端只读化** | GET stage-state + blocking[] 不变量 + §6.3 前端改造（C1/C2→C3→C4/C5→C7 四个独立 PR） | 后端 `tests/test_stage_state_endpoint.py`（含 §5.3 死锁形态参数化）；前端 `node --test` 全量 60 文件绿 + 更新 `medicalMonitoringAdmissionMappingConfirmState.test.mjs` | 按组件回退；端点保留无害 |
| **S8 文档验证结论物化（性能，可独立延后）** | verdict 缓存表绑 `registry_revision`+被引作业行 sha，失效即重放；B4 读缓存 | `tests/test_document_authority_verdict_cache.py`：注册表更新/作业行变化→缓存失效重放；判定结果与直连重放逐 case 一致；探针复测 study-documents 延迟（对照考古报告 68.3s 单次采样） | 读开关回直连重放（缓存只加速不改判定） |

**S3/S7 后的专项验收**（超出本设计执行范围，按 HANDOFF 方案A 第2条）：从零路径 E2E 连续 3 次走通全链，底座 `scripts/fullchain_sar_rerun_20260926/`。

---

## 8. 风险与回滚

| # | 风险 | 缓解 | 回滚 |
|---|---|---|---|
| R1 | stage_state 与权威行漂移（跨库/跨文件写点） | A2 内同事务原子；A5/A4 权威先行+事件留痕+启动补偿扫描；**门永不读物化行**（B5 读 drafts、B6 读 A4）；facts 判定永远直查 A4 | S2 影子模式常驻可回；derive/materialized 开关 |
| R2 | 写放大（4.4GB 库） | 事件=每分片状态跨越一行（265 分片量级单次事件量可忽略）；lease/heartbeat/轮询无跨越不落事件；WAL 已开（`:346`）；门放行不落事件 | 事件表可归档不影响权威 |
| R3 | 事件表无界增长 | >90 天导出 JSONL（含 event_id 哈希链）后清理；导出即留痕满足审计 | 归档脚本独立可停 |
| R4 | S6 重排语义外溢（识别链 submit 意外重排） | env 灰度默认 off；调用点逐一核实后才开；content/contract/revision 变化三类一律不重排 | env 关闭 |
| R5 | 前端改造面大引入回归 | S7 拆四个独立 PR；node --test 60 文件全量作门（该门本次实测可跑：33 pass 样本） | 按组件 revert |
| R6 | 降级入口服务端化后前后端判定竞态（服务端未标 available 但用户停滞更久） | 后端 422 契约+前端现有错误路径保留；stalled 阈值可配（env） | 前端回退计时 |
| R7 | 双写期间崩溃半提交 | 同库同事务=原子；跨库点语义上允许事件缺失（留痕完整性 < 权威正确性，如实取舍） | 补偿扫描器重放 |
| **回滚总原则** | 权威 schema（drafts/jobs/registry/facts/A5 文件态）**任何一步都不改不迁**；两张新表是纯附加物 | — | `DROP TABLE` 即完全回滚，无数据丢失路径 |

---

## 9. 诚实清单（本次做了什么、没做什么）

**本次实际执行**：
- 读 01_STATEMAP.md 全文 + HANDOFF_40ROUNDS_20261014.md 第1-114行（方案A=第74-78行）；
- 读代码（全部引用均在本次 Read/grep 输出中核实）：`mapping_pipeline.py:1554-1637,2130-2236,290-320`；`mapping_confirmation.py:270-509,2050-2229`；`monitoring_mapping_draft_repository.py:915-1033,1370-1470`；`monitoring_ai_repository.py:340-534,600-719,2195-2294`；`monitoring_mapping_activation.py:280-389`；`fact_materialization.py:560-676`；`monitoring_document_authority_workflow.py:180-313,1310-1407`；`mapping_candidate_routes.py:490-806,1440-1825`；`main.py:1085-1190,4100-4168`；`monitoring_ai_field_profile_cache.py:14-113`；前端 `MedicalMonitoringAdmissionWizard.jsx:1265-1374,1690-1724,2230-2299`；`medicalMonitoringAdmissionMappingConfirmState.mjs:1-130,560-720,779-839`；`medicalMonitoringAdmissionWizardState.mjs:235-354`；
- 测试基线实测：pytest 三件套 62 passed（0.48s）；node --test 映射确认态测试 33 pass/0 fail；pytest 配置 `testpaths=tests`。

**没做/不可做（不填猜值）**：
1. 未运行任何改造代码——本设计可执行性以 DDL/契约/文件行号表达，未经运行验证；
2. 未重跑考古报告探针（冲突1 的 curl、study-documents 68.3s）——引用 01_STATEMAP 第四节原始记录，标注为"考古报告"；
3. `mapping_pipeline` 识别分片 submit 路径的 create_or_get 调用点未逐一读过（S6 的 env 默认 off 与"调用点核实前置"即由此而来）；
4. `fact_routes.py`、`source_intake.py`、`monitoring_document_evidence.py`、`monitoring_document_authority_jobs.py` 未直接读过（相关行为引 01_STATEMAP A3/A4/A6/A8/B4/D 节，标注为考古报告）；
5. 事件写入点的崩溃恢复补偿扫描器未给出实现细节（S7 项，留实施）；E2E 从零路径验收不在本设计范围（§7 末）。

---

## 10. 一句话结论

第3步的单一权威 = **既有 A2 drafts+jobs、A4 facts、A1+A3+A5 文档三组权威原位不动**，新增同库两张附加表（阶段状态行 + append-only 事件流）补上"识别聚合态无持久行"与"变迁无留痕"两个唯一缺口；B1/B2/B3/B7 与前端 C1-C7 全部收编为单源投影与纯渲染；四个矛盾字段每字段一个推导式；失败分类、降级入口、阻塞组入口、F5 恢复四个死锁家族根因各有一个结构性根治点（§5.1-5.4）；八步迁移每步带具名 pytest 与独立回滚，权威 schema 零迁移、`DROP TABLE` 即归零。
