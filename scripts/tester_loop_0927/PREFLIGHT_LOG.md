# 全链预检日志（PREFLIGHT_LOG）

按轮次分节。预检工程师在隔离环境 8911（严禁 8910/5177）以一次性预检项目把
整条链真跑一遍：建项→上传→文档权威→映射确认→facts→运行监查→发布→结果。
只证明通或不通，不修复、不绕过、不伪造状态。

---

## R10 第1次（20261001，run=r10p_preflight）

- 驱动脚本：`scripts/tester_loop_0927/r10p_preflight_csu.py`（幂等，状态
  `r10p_preflight_state.json`，逐步留痕 `r10p_preflight_evidence.jsonl`，
  运行日志 `logs/r10p_preflight_run1.log`、`logs/r10p_preflight_run2.log`）
- 数据：`tester_staging_0927/synth_csu` 三件套（方案V1.3 docx + eCRF指南
  V1.0 docx + 合成listing V1.0 xlsx）
- 项目：**MX循R10P-CSU**（proj_user_cae1decd4224，慢性自发性荨麻疹 /
  MG-K10 / modules=[medical_monitoring]，幂等键 r10p-preflight-20260930
  T181225Z-ee3db712 唯一，status=active，**留在原地待复盘归档**）
- 环境：8911 ready，backend_build_id=api-439b9e81187f0da4，AI 网关
  zhipu-coding-plan/glm-5.3-flash，runtime=runs/tester_loop_iso_20260928
  （进程 env WORKBENCH_RUNTIME_DIR 实测确认）

### 结论：chainOk = false

**blockedAt = 运行启动**：六阶段后（建项→上传→文档权威→映射确认→facts 全绿），
`POST /r7/runs/prepare-and-start` 被 409 `medical_monitoring_source_readiness_
unconfirmed` 硬拒（readiness.implementation_status=intake_pending）。发布/结果
两阶段未到达。与 R8/R9 台账「状态碎片化（接入管线 confirmed vs 监查侧
unconfirmed）」家族同源，本轮把根因定位到文件级（见下）。

### 八阶段计时

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.0 | project_id=proj_user_cae1decd4224；名称/适应症/产品/modules 合同核对无误 |
| 2 | 上传 | ✅ | 0.2 | attempt=stg-5ed938de954d48a0aa5def87bf7cef4b，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 857.4 | analyze→resolve（身份确认+文件角色裁决两个设计内人工门）→ready=true「研究文件已准备好」；8个AI作业全completed |
| 4 | 映射确认 | ✅ | 12670（首跑12644+复跑26） | 首跑双队列20作业→adopt→4轮复核收敛（remaining 46→34→29→15→0）时浮出2张未知裁决卡 fail-closed 停住；openpyxl 实测 CM 表（开始日期32行合法/结束日期33行合法/start≤end 32/33）后作答复跑，26.2s 收敛：draft.status=confirmed（monmapdraft_b3952e2e210556ca055e209069cd）、60候选、adj=complete |
| 5 | facts | ✅ | 0.2 | state=ready：10表/591行/2548值 source_values_verified=2548（100%） |
| 6 | 运行 | ❌ | 0.3 | run-setup/options 200（快照 token snapshot:40cc7316…「10表/591行/2548值100%往返校验」），但 prepare-and-start 409 medical_monitoring_source_readiness_unconfirmed——运行从未创建，谈不上完成 |
| 7 | 发布 | ❌ | — | 未到达（无运行可发布） |
| 8 | 结果 | ❌ | — | 未到达 |

注：阶段4的2张未知卡为 CM/CMSTDAT、CM/CMENDAT，卡片原文「主分析判断=X，
独立复核判断=X」两侧逐字相同（R3-01 家族矛盾卡表现，两轮目击后第三次）。

### 状态碎片化拦截证据（console/API 双侧，20260930T22:03:26Z）

**API 侧A（r7 接入管线，backend 状态）**：
- GET `{att}/mapping-candidates?focus=all` → mapping_state=candidates_ready，
  draft.status=**confirmed**（monmapdraft_b3952e2e210556ca055e209069cd）
- GET `{att}/facts` → state=**ready**（10表/591行/2548值100%核验）

**API 侧B（监查侧/run 引擎读到的状态）**：
- POST `/r7/runs/prepare-and-start` → **409**
  `{code: medical_monitoring_source_readiness_unconfirmed, readiness:
   {kind: unconfirmed, implementation_status: intake_pending,
    can_read: false, can_start: false, reason_code: readiness_unconfirmed}}`
- GET `/api/projects` 模块绑定同步显示 medical_monitoring → **intake_pending**
  （从建项起到 facts ready 后始终未变）

**console 侧**：`/tmp/mm_api_8911.log` 全程 0 字节（uvicorn --log-level
warning）——门禁拒绝在后端控制台零留痕，只在 HTTP 层可见。证据以
`fragmentation_evidence` 事件存于 r10p_preflight_evidence.jsonl。

**根因（文件级，本轮新增定位）**：`services/api/app/project_source_manifest.py:171-190`
`_monitoring_facts_materialized()` 用**硬编码舰队 runtime 路径**
`runs/phase_c_mgk10_authority_v2_20260905/runtime/medical_monitoring_r7/{pid}
/runtime/artifacts/facts-manifest.json` 判断 facts 是否物化，不读
WORKBENCH_RUNTIME_DIR。实测：facts-manifest.json **存在**于隔离 runtime
（runs/tester_loop_iso_20260928/runtime/medical_monitoring_r7/
proj_user_cae1decd4224/runtime/artifacts/），硬编码路径下**不存在**
（No such file or directory）→ 绑定永留 intake_pending（该文件 :377-386 的
三目：real_source_slice if _monitoring_facts_materialized else intake_pending）
→ `monitoring_source_readiness.py:20-28` 的 ACTIVE 集合不含 intake_pending
→ `resolve_monitoring_source_readiness` 返回 unconfirmed（:51-58）→
`run_routes.py:115-116` prepare-and-start 前置 `ensure_source_ready` 抛 409。
**该缺陷只在非默认 runtime（隔离实例 8911）复现**；8910 舰队 runtime 与硬编码
路径重合，SAR 链因此能通。R5D/R8D/R9D 预置项目「API全绿 vs 引擎unconfirmed」
的 6 分钟对照由此完全解释。修复属修复员职责，本轮未绕过、未改库、未在舰队
runtime 下放任何文件。

### AI 节点路由核验（台账：module `/ai/jobs`，读自 medical_monitoring_ai.sqlite3）

`/api/ai/queue` 在本 build 404（Not Found），台账以项目级 `/api/projects/{pid}/
modules/medical-monitoring/ai/jobs?limit=500` 为准。总量 78 作业，终态
74 completed + 4 failed，**0 queued/running（无滞留）**；4 个 failed 均有
显式 failure_code + attempt_count（无静默失败），经自动恢复预算/bounded-gap
收敛，链路继续走到 confirmed。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（document-authority-analysis primary-v9、review-v7、adjudication-v8、critique-v2 各1） | 4 | 4 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（同上四族 verifier） | 4 | 4 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（listing-field-mapping-v19） | 10 | 10 completed | ✅ |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（mapping-verifier-v8-tools-v6） | 10 | 10 completed | ✅ |
| 裁决（映射收敛） | 主 cms-router/glm-5.3-flash（adjudication-v19-tools-v7.2）25；盲核 ollama-cloud/deepseek-v4.1-flash（adjudication-verifier-v17-tools-v7.2）25 | 50 | 46 completed + 4 failed（1×invalid_ai_output 主侧；3×provider_runtime_error=provider_reasoning_only 盲核侧）；adjudication 收敛 complete/remaining=0 | ✅（4失败可见且已按设计恢复为可见缺口） |
| 监查分析 | 未派发（运行未启动，无作业无路由可报） | 0 | — | ❌ 被①的409拦截 |

### 过程事件（如实）
- 20260930T18:12Z run1 启动；18:26:43 文档权威 ready；18:47:33 adopt；
- 20260930T21:57 run1 在第4轮收敛浮出 CM/CMSTDAT+CMENDAT 未知卡 fail-closed
  退出（exit 2），历时 12644s；
- 20261001T06:02Z（本地）以实测作答复跑 run2（exit 3=碎片化拦截）：
  26s 收敛+confirm+facts 全绿，运行启动被拒；
- 全程未触碰 8910/5177；未改任何产品代码/数据库；项目与全部留痕原地保留。

---

## R10 第2次（20261001，run=r10p_preflight2）

- 前提：R10第1次拦截根因（project_source_manifest 硬编码舰队runtime路径）已由
  修复员修复并重启（build **api-ce1c512e7a64adf5**，project_source_manifest.py:
  172-192 `_monitoring_runtime_root` WORKBENCH_RUNTIME_DIR 感知；8911 进程 env
  实测确认 WORKBENCH_RUNTIME_DIR=runs/tester_loop_iso_20260928/runtime）。
- 驱动脚本：`scripts/tester_loop_0927/r10p_preflight2_csu.py`（第1次驱动的复本，
  状态 `r10p_preflight2_state.json`、留痕 `r10p_preflight2_evidence.jsonl` 独立）
- 数据：同 `tester_staging_0927/synth_csu` 三件套
- 项目：**MX循R10P-CSU-2**（proj_user_525e635e5fb1，幂等键
  r10p-preflight-20260930T221704Z-3c903847 唯一）。**名称偏离说明**：按任务要求
  先以精确名「MX循R10P-CSU」建项被 409 拒（`已存在同名项目：MX循R10P-CSU`——
  第1次项目按指令留在原地待复盘，不可改名/删除；API 报错自指引「如加序号或
  管理代号后缀」），故按 API 指引加后缀 -2，P=预检语义不变。
- 环境：8911 ready（build api-ce1c512e7a64adf5），AI 网关
  zhipu-coding-plan/glm-5.3-flash，隔离 runtime 同第1次。

### 结论：chainOk = false

**blockedAt = 映射确认（阶段4，adopt）**——非预期的碎片化家族（本轮未到达
运行启动，该门未被测试）。现象：映射双队列 EX 域主分片两次终态失败
（invalid_ai_output），自动重排预算耗尽（retryable=0），adopt 被 422
mapping_draft_invalid 硬拒——根因是**库层域完整性门**：`monitoring_mapping_
draft_repository.py:2762-2767` `_validated_source` 要求全部期望域在场
（EX 域主命名空间零候选 → "expected field mapping domains are missing"），
与确认层声明允许部分采纳的设计（`mapping_confirmation.py:482-490`，R3报告C：
needs_attention 允许对已完成子集知情采纳）**直接矛盾**。首遍映射lane无
adjudication 阶段的 bounded-gap 逃生通道（run1/R10D 的同类 EX 主分片
invalid_ai_output 失败发生在裁决阶段，被 bounded-gap 吸收后链路继续），
故**单域分片终态失败 = 映射lane死锁，无恢复路径**。

### 八阶段计时

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.0 | proj_user_525e635e5fb1（精确名首次尝试 409 同名拒绝→按API指引加-2后缀；合同 indication/product/modules 核对无误） |
| 2 | 上传 | ✅ | 0.2 | attempt=stg-c41043d09c3646a78b16dd3e15aa8647，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 560.7 | analyze→（身份归属确认1次，自动）→ready=true「研究文件已准备好」；本轮无文件角色人工裁决；8个AI作业全completed |
| 4 | 映射确认 | ❌ | 1828（驱动808+恢复窗口1020） | 双队列20作业：盲核10/10（EX经1次重排恢复completed），主9/10——EX主分片 invalid_ai_output×2 终态（详见下）；候选55/60（缺EX域5字段）；adopt 422 mapping_draft_invalid |
| 5 | facts | ❌ | — | 未到达（无draft可confirm） |
| 6 | 运行 | ❌ | — | 未到达（碎片化门本轮未被测试） |
| 7 | 发布 | ❌ | — | 未到达 |
| 8 | 结果 | ❌ | — | 未到达 |

### 阶段4拦截证据（台账+代码级）

- **EX主分片终态失败**（medical_monitoring_ai.sqlite3 直读）：
  `listing-field-mapping:stg-c41043d09c3646a78b16dd3e15aa8647:EX:0001-of-0001`
  provider=cms-router/glm-5.3-flash，prompt=monitoring-listing-field-mapping-v19，
  failure_code=**invalid_ai_output**，failure_message=「provider output remained
  invalid after one controlled repair: ...Value error, **provider output contains
  definitive approval language**, path=candidates.0」，attempt=2/3、**retryable=0**、
  automatic_recovery_count=1/1。
- **恢复路径逐条 exhausted**（全部产品自身路径，无绕过）：
  ① 技术重排（`mapping_pipeline.py:1416 _recover_failed_submission_jobs`，
  requeue-once）：22:47Z 重入候选生成，EX主第2次同样 invalid_ai_output，EX盲核
  恢复 completed；22:56Z 第3次重入不再重排（预算尽）；
  ② 路由fallback（`mapping_pipeline.py:940-1000`）：仅覆盖 _REMOTE_UNAVAILABLE_
  FAILURES={ai_not_configured, ai_transport_rejected, ai_configuration_error,
  provider_runtime_error}，不含 invalid_ai_output；
  ③ 部分采纳（mapping_confirmation.py:482-490 设计允许）：被库层
  `monitoring_mapping_draft_repository.py:2762-2767` 域完整性门否决（EX 域
  主命名空间零候选 → MonitoringMappingSourceStateError(ValueError) → 422
  mapping_draft_invalid，`mapping_candidate_routes.py:522` 的映射）。
- **非确定性实证**：同三份合成文件、同路由、同 prompt 代际，第1次预检（run1）
  首遍20作业全完成（60候选）——本轮 EX 主分片模型输出两次触发
  「definitive approval language」校验拒绝属模型输出质量波动；run1 的 EX 主
  invalid_ai_output 失败发生在**裁决阶段**（bounded-gap 吸收），本轮发生在
  **首遍阶段**（无逃生通道）——同一底层波动在不同阶段的天壤后果。
- console `/tmp/mm_api_8911.log` 全程 0 字节（uvicorn --log-level warning），
  422 拒绝只在 HTTP 层可见（与第1次同现象）。

### AI 节点路由核验（台账：module `/ai/jobs`，读自 medical_monitoring_ai.sqlite3）

`/api/ai/queue` 本 build 仍 404。本项目总量 28 作业，终态 26 completed +
2 failed→恢复后 27 completed + 1 terminal failed，**0 queued/running（无滞留）**；
失败作业有显式 failure_code/failure_message/attempt_count（无静默失败）。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis primary-v9、review-v7、adjudication-v8、critique-v2 各1） | 4 | 4 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（同上四族 verifier） | 4 | 4 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（listing-field-mapping-v19） | 10 | 9 completed + 1 terminal failed（EX分片 invalid_ai_output，恢复预算尽） | ❌（该失败即链路拦截点） |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（mapping-verifier-v8-tools-v6） | 10 | 10 completed（EX经1次重排恢复） | ✅ |
| 裁决（映射收敛） | 未派发（adopt 422 → 无 adjudication 作业产生） | 0 | — | ❌ 被阶段4拦截 |
| 监查分析 | 未派发（运行未启动） | 0 | — | ❌ 被阶段4拦截 |

### 过程事件（如实）
- 20260930T22:12Z（本地06:12）第2次启动：精确名建项 409（同名）→ 按API指引
  加后缀-2 重建成功；
- 22:26:25Z 文档权威 ready（560.7s）；映射双队列启动，22:39:53Z state=
  needs_attention（主9/10）→ adopt 422，驱动 fail-closed（exit 2）；
- 22:41-22:56Z 按产品恢复路径人工重放：重入候选生成×2（EX主分片两次终态
  invalid_ai_output、EX盲核恢复completed）、adopt 探针×1（422 复现），
  4条 manual_recovery_* 证据已补写 r10p_preflight2_evidence.jsonl；
- 全程未触碰 8910/5177；未改任何产品代码/数据库；项目与全部留痕原地保留
  （归档交复盘官）；第1次项目（proj_user_cae1decd4224，含修复员复验运行
  run:09d074a46e284a870b4d8e36 waiting_start）同样原地保留。
- 备注：第1次的碎片化根因修复本轮**未被端到端复测**（未到达运行启动），
  其有效性仅由修复员在 run1 项目上的原地复验背书。

---

## R10 第3次（20261001，run=r10p_preflight3）——**chainOk = true，全链首次端到端跑通**

- 前提：前两轮拦截根因均已修复——①runtime路径（api-ce1c512e7a64adf5）；
  ②映射draft域完整性门 allowed_missing_domains（api-9b827e5405b94cea，
  monitoring_mapping_draft_repository.py:2767 本轮核实在位）。
- 驱动脚本：`scripts/tester_loop_0927/r10p_preflight3_csu.py`（幂等，状态
  `r10p_preflight3_state.json`，留痕 `r10p_preflight3_evidence.jsonl`，
  运行日志 logs/r10p_preflight3_run1..run5.log，五遍：run1 首跑到矛盾卡
  fail-closed、run2 补答后 confirm+facts、run3 撞孤儿预约、run4 同键重放
  启动运行走完全链、run5 修正计数启发式后八阶段全绿复验）
- 数据：同 `tester_staging_0927/synth_csu` 三件套
- 项目：**MX循R10P-CSU-3**（proj_user_5f1fd3ae8c92，幂等键
  r10p-preflight-20260930T230705Z-b595a4e0 唯一）。**名称偏离说明**：按任务
  要求先以精确名「MX循R10P-CSU」建项被 409 拒（前两轮项目按指令留在原地
  占名），按 API 报错自指引加后缀 -3，P=预检语义不变。
- 运行：run:b2b473b8f9816c635917e6db（r7-run-32e41b473866403ba22c54b19233178f，
  daily/full，快照 snapshot:db77204c8f9d24ffda929a06）
- 结果：result-context:89cd1e6d0d1340bf9e4216e56dd690de（overview 597KB）
- 项目按指令留在原地待复盘归档。

### 结论：chainOk = true（八阶段全ok；运行真完成、发布available、结果可读）

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.0 | 精确名409（同名占名）→按API指引-3后缀；indication=慢性自发性荨麻疹/product=MG-K10/modules=[medical_monitoring] 合同核对无误 |
| 2 | 上传 | ✅ | 0.2 | attempt=stg-74f74846ee584c138180012a60d795a2，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 253 | analyze→resolve（身份确认1次，自动）→ready=true「研究文件已准备好」；4个AI作业全completed（本轮无角色人工裁决） |
| 4 | 映射确认 | ✅ | 10056（首跑10012含fail-closed+复跑44） | 双队列首遍20/20全completed（60候选）→adopt 200（**第2次卡点未复发**）→4波裁决收敛46→38→24→0（系统裁决22+4张DM矛盾卡实测作答）→draft.status=confirmed（monmapdraft_3d7d42902b7243a737df80b6e29a，v68）；3个裁决阶段终态failed被bounded-gap吸收，链路继续 |
| 5 | facts | ✅ | 0.2 | state=ready：10表/591行/2974值 source_values_verified=2974（100%） |
| 6 | 运行 | ✅ | 30.4 | 两次驱动侧修正后真正完成：①workspace/bootstrap 200（新项目首次启动运行前种全局档，产品既定步骤，0923交接有载，驱动初版漏调）；②run2的prepare在reserve后422（global_default_missing）留孤儿waiting_start预约→run4以**同一幂等键**重放，run_routes replay分支补完同一运行；run_state=completed（10/10项100%，通用检查7/7+日常监查3/3），result_available=true |
| 7 | 发布 | ✅ | 0.4 | publication POST 200→publication_state=available（结果已整理完成） |
| 8 | 结果 | ✅ | 0.4 | result-entry 200；overview 597,305字节非空；**finding_count=15**（query_findings，meta.state=completed_with_findings/gaps=0）+current_risks=477（高14/中15/低448）；subject_count=16 |

注：run5 复验一遍八阶段全绿（总耗时28s，幂等复用），stage计时取各阶段
**首次真实完成**的数值（run1-4）。

### 过程中的三个真实发现（非产品缺陷即产品既定行为，如实记录）

1. **新项目 API-only 启动运行需先 workspace/bootstrap**：prepare-and-start
   的 profile 解析要求 global_default 层（run_entry.py:445），新项目首次
   启动前须 POST r7/workspace/bootstrap 种全局档（前端向导内含此步；
   HANDOFF_FULLCHAIN_20260923「关键工程事实」有载）。漏调→422
   global_default_missing「请先完成工作区初始化」。
2. **422-after-reserve 留孤儿 waiting_start 预约**：reserve 成功后 profile
   解析失败返回422，但预约已在册（manifest_digest=None）——后续换新幂等键
   的 prepare 被 409 in_flight_conflict 拒；产品恢复路径=**同幂等键重放**
   （run_routes「must finish the same run」分支），重放补完同一运行。与
   0923交接「孤儿waiting_start（挡新运行、无法cancel）」记载一致。
3. **监查运行发现不经AI台账**：本build日常监查运行（16受试者，30s完成）
   的发现由 FactsModeOutputProvider 从已核验事实确定性聚合产出
   （facts_mode_outputs.py 模块docstring「severity/type aggregation for
   the full-risk output and adverse-event (medium-or-higher) query
   findings …No invented findings」），AI双队列价值实现在映射/裁决阶段。
   全隔离实例台账历史仅3种task_type（mapping/authority），无监查分析
   task_type——15条query_findings+477 risks 为事实回执产出，非AI产出。

### 映射阶段4张DM矛盾卡（R3-01家族第4次目击，本轮实测作答）

DM·AGE/COMPSTATUS/RANDDT/SEX 四卡「主分析判断=X，独立复核判断=X」两侧
逐字相同；openpyxl 直读 DM 表实测：16名受试者，性别=男8/女8、年龄=16行
全数值23~61、随机日期=16行全合法日期（2026-03-02~2026-04-01）、研究状态
=全列唯一值'完成'。按 recommended_role+实测依据作答，44s 内收敛 complete。

### AI 节点路由核验（台账：medical_monitoring_ai.sqlite3 直读；/api/ai/queue 本build仍404）

本项目总量 60 作业，终态 57 completed + 3 terminal failed，**0 queued/
running（无滞留）**；3 个 failed 均裁决阶段、有显式 failure_code+attempt
计数（无静默失败），经 bounded-gap 吸收后收敛 remaining=0。调用108次，
prompt 1,310,988 + completion 808,450 tokens。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis primary-v9、review primary-v7 各1） | 2 | 2 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（analysis verifier-v9、review verifier-v7 各1） | 2 | 2 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（listing-field-mapping-v19） | 10 | 10 completed | ✅ |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（mapping-verifier-v8-tools-v6） | 10 | 10 completed | ✅ |
| 裁决（映射收敛） | 主 cms-router/glm-5.3-flash（adjudication-v19-tools-v7.2）18：16 completed+2 failed（UAS/EX invalid_ai_output att=2 rec=1）；盲核 ollama-cloud/deepseek-v4.1-flash（adjudication-verifier-v17-tools-v7.2）18：17 completed+1 failed（EX provider_reasoning_only att=4 rec=1） | 36 | 33 completed + 3 terminal failed（bounded-gap吸收，收敛complete/remaining=0/系统裁决22） | ✅（失败可见且按设计恢复） |
| 监查分析 | 本build运行lane不经AI台账（FactsModeOutputProvider事实回执确定性产出，见发现3） | 0 | —（无作业=无滞留/无静默失败；15发现+477风险已产出） | ✅（机制核实，如实报0作业） |

### 过程事件（如实）
- 07:07:05 run1 启动：建项（精确名409→-3）/上传/文档权威253s全绿；映射双
  队列 07:11-07:40 20/20 completed→adopt 200→裁决4波收敛；
- 09:58 run1 在第4波浮出4张DM矛盾卡 fail-closed 退出（exit 2，收敛期
  10012s）；10:00 openpyxl 实测作答后续跑 run2：44s 收敛+confirm+facts
  全绿；run2 首次 prepare 422 global_default_missing（reserve后失败留
  waiting_start 孤儿）；
- 10:08 run3 补 workspace/bootstrap 200 后撞孤儿 409 in_flight_conflict
  （驱动幂等键保存缺陷：422响应不回显键→存了None→run3生成了新键）；
  修驱动（键先持久化）+注入在册键后 run4 10:09:46 同键重放启动运行，
  30.4s run_state=completed→发布 available→结果可读（驱动计数启发式
  漏 query_findings 键名误报 finding_count=0）；
- 10:16 run5 修正计数后复验：八阶段全绿（ok=true）；
- 全程未触碰 8910/5177；未改任何产品代码/数据库（驱动脚本与一次性预检
  项目自身数据除外）；项目与全部留痕原地保留（归档交复盘官）。
