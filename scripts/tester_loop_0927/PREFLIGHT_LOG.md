# 全链预检日志（PREFLIGHT_LOG）

按轮次分节。预检工程师在隔离环境 8911（严禁 8910/5177）以一次性预检项目把
整条链真跑一遍：建项→上传→文档权威→映射确认→facts→运行监查→发布→结果。
只证明通或不通，不修复、不绕过、不伪造状态。

---

## R20 第1次（20261006，run=r20p_preflight）——**chainOk = true，第十一次全链端到端跑通（run1 映射收敛4h预算被并行外源lane争抢耗尽exit10→run2 幂等续跑全绿 exit 0；21张问题卡全被R5D-R15D既有决策表覆盖、零未知卡；碎片化家族未命中；3个盲核裁决分片终态失败经bounded-gap吸收，facts 2804值；总壁钟约6h46m——首个与外源SAR-scale lane（362作业）同实例并行的全绿轮）**

- 驱动脚本：`scripts/tester_loop_0927/r20p_preflight_csu.py`（由 R19P 全绿驱动
  r19p_preflight_csu.py 机械适配 R20 命名/幂等键/留痕文件——diff 实测 44 行，
  其中 41 行为轮次标识替换（r19p→r20p/R19P→R20P/幂等键前缀）、3 行为头部
  血缘注释更新；R5D-R15D 裁决卡决策表与数据内容行原样保留；幂等，状态
  `r20p_preflight_state.json`，留痕 `r20p_preflight_evidence.jsonl`
  （645事件，**仅 1 条 ok=false=run1映射收敛预算耗尽**），运行日志
  logs/r20p_preflight_run1.log / r20p_preflight_run2.log，**run1 exit 10 →
  run2 exit 0**）
- 数据：同 `tester_staging_0927/synth_csu` 三件套（方案V1.3 docx + eCRF指南V1.0 docx + 合成listing V1.0 xlsx）
- 项目：**MX循R20P-CSU**（proj_user_ce177c32b799 / MW-PHASE-2194C7EB，
  慢性自发性荨麻疹 / MG-K10 / modules 含 medical_monitoring【projects API：
  medical_monitoring→real_source_slice + source-manifest API 双核对】，
  幂等键 r20p-preflight-20261006T010407Z-4190fec1 唯一，精确名一次建项 201
  成功（开赛前在册仅 R19D 常驻开考位 MX循开考-CSU，无同名冲突），
  status=active，**留在原地待复盘归档**）
- 运行：run:3272e6b47bf84a11da8965b6（run_start_idem=
  r20p-run-20261006T074959Z-2d6b6530；run-setup/options 200 456ms（snapshot:
  df2e8cee890d89b3463b7341）→workspace/bootstrap 200 343ms→prepare-and-start
  一次 200 387ms，项目 runs 列表仅此1条无孤儿）
- 结果：result-context:eae1cb71e64e46d19fcbf37ba4421a57（overview 驱动侧
  序列化 597,305 字节；独立HTTP读取原始载荷 **778,126 字节——与R14P-R19P
  字节数完全一致**）

### 结论：chainOk = true（八阶段全ok；运行真完成10/10项100%、发布available、结果可读）

已知状态碎片化家族（后端confirmed vs 监查侧unconfirmed，readiness 409）
**未命中**——run-setup/options 200、workspace/bootstrap 200 后
prepare-and-start 一次 200（387ms），无 409 窗口，evidence 中
fragmentation_evidence 事件 0 条。

### 与前轮的关键差异：并行外源lane资源争抢（如实记录）

开赛前发现隔离实例上存在**另一活跃工作负载**（proj_user_cee0d996f1a5 /
attempt stg-f6167e8fe37f428abc51120b6d243dd8，362 个 listing_field_mapping
作业=SAR-scale 规模，疑为 SAR 续跑工作流，22:53Z(10-05) 启动，lease 实时
续期中）。本预检 48→80 作业与其共享同一工人工池（实测 cms-router 同时仅
2 slot、ollama-cloud 1-2 slot）：主侧映射吞吐被摊薄至 ~2作业/9分钟
（R19 无争抢时 20作业/19分钟），直接后果是 **run1 映射收敛 14400s 预算
耗尽 exit 10**（17474s，队列尚余5作业）→ run2 幂等续跑（状态复用，前三
阶段 0s/6.5s/18.4s 重放）后收敛完成。外源 lane 至 07:30Z 前后自行排干
（终态 355 completed + 7 failed），全程无跨项目作业抢占失败、无429风暴，
本预检项目无任何作业被外源 lane 污染（台账 business_key 双核对）。

### 八阶段计时（秒数=首次真实完成；跨 run1+run2 总壁钟 01:04Z→07:50Z 约6h46m）

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 7.7 | proj_user_ce177c32b799，精确名一次成功201；indication/product/modules 合同双核对无误 |
| 2 | 上传 | ✅ | 10.1 | attempt=stg-a7bdd6720a834b70a14a5ce052735fd3，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 830.0 | analyze 202（mmbatch_f272575dcdc9cdc15e7f7a90）→ready=true「研究文件已准备好」；**零人工门**（零身份确认、零角色选择——R19尚有1次ecrf角色选择）；8个AI作业全completed（本阶段耗时为R19的469s×1.8倍，主因共享工池排队） |
| 4 | 映射确认 | ✅ | 17474(run1预算耗尽exit10)+5804(run2续)=23278 | 首遍双队列20/20（主10/10+盲核10/10）→60候选→adopt 201（monmapdraft_06955eff5efeafa6716e20e99a8a）→**21张用户问题卡浮现**（CM×5/DM×5/LB_HEM×6/SV×1/VS×4，全部命中R5D-R15D既有决策表按数据实测作答，零未知卡零fail-closed）→裁决波g01+系统裁决多轮（adjudicate 10连发：remaining 46→41→33→**0**，sys=25）→confirm 200（draft status=confirmed）；3个盲核裁决分片终态失败（见AI节点表）经bounded-gap吸收，收敛仍 complete remaining=0 |
| 5 | facts | ✅ | 0.8 | state=ready：10表/591行/**2804值** source_values_verified=2804（物化100%口径内；低于R19的3422——3个终态失败盲核分片bounded-gap扣减，与R18P 1752同机制但幅度小） |
| 6 | 运行 | ✅ | 2.0 | run-setup/options 200→workspace/bootstrap 200→prepare-and-start 一次200 387ms（**碎片化家族未命中**）→run_state=completed，**10/10项100%「已完成」**（progress复核API独立确认 percent=100.0+status_overview=[{已完成,count:10}]+result_available=true） |
| 7 | 发布 | ✅ | 0.6 | publication POST 200（619ms）→publication_state=available「结果已整理完成」（publication端点+progress端点双一致，replayed=false） |
| 8 | 结果 | ✅ | 1.0 | result-entry 200（指针载荷338B）；overview 独立读取778,126字节非空；**finding_count=15**（query_findings列表长度与query_findings_meta.total双一致）+current_risks=477；subject_count=16；identity.project_ref=proj_user_ce177c32b799 归属核对无误；data_cutoff=2026-08-19 |

### AI 节点路由核验（台账：隔离实例 runs/tester_loop_iso_20260928/runtime/medical_monitoring_ai.sqlite3 直读；/api/ai/queue 本轮404，模块级 ai/jobs 200）

本项目总量 **80 作业**（权威8[analysis/critique/review/裁决 各1对] + 映射pipeline 20 +
映射裁决g01波52；task_type 视图 document_authority_analysis 2 + document_authority_review 6
+ listing_field_mapping 72 与之一致），终态 **77 completed + 3 failed，
0 queued/running（无滞留）**；主侧 cms-router/glm-5.3-flash 40作业全completed，
盲核侧 ollama-cloud/deepseek-v4.1-flash 40作业（37 completed+3 终态失败）。
调用135次，prompt 1,599,962 + completion 880,534 = **2,480,496 tokens**
（高于R19的1.32M——争抢期重试/自愈/裁决多轮重发所致）。14个作业经历>1次
attempt（7个2次常规重试、7个经 automatic_recovery 复活，其中4个升到
attempt 4/4：3个终态失败+1个自愈完成）。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis/critique/review/裁决 :primary 各1） | 4 | 4 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（analysis/critique/review/裁决 :verifier 各1） | 4 | 4 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（pipeline ×10 + 裁决g01波 ×26） | 36 | 36 completed（含CM/UAS主分片 invalid_ai_output 后 automatic_recovery 复活） | ✅ |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（pipeline ×10 + 裁决g01波 ×26） | 36 | 33 completed + **3终态失败**（MH/EX/UAS 各4/4次耗尽 provider_runtime_error「reasoning-only」瞬态家族，本轮未自愈——R18P同族bounded-gap吸收先例） | ✅（链路通；覆盖下降如实记录） |
| 裁决（权威内+映射收敛） | 主 cms-router/glm-5.3-flash 27（权威1+g01×26）+ 盲核 ollama-cloud/deepseek-v4.1-flash 27（权威1+g01×26），tools车道 | 54 | 51 completed + 3终态失败（映射裁决 adj_state=complete/remaining=0/sys=25；权威裁决双队列一致） | ✅ |
| 监查分析 | 本build运行lane不经AI台账（本项目 task_type 仅 document_authority_* 与 listing_field_mapping 双核对；FactsModeOutputProvider 事实回执确定性产出，同R10P3-R19P；monitoring_daily_runs 表本build在AI台账sqlite中不存在——sqlite_master 查证） | 0 | —（无作业=无滞留/无静默失败；15发现+477风险已产出） | ✅（机制核实，如实报0作业） |

注：**裁决行为横切视图非加法行**——其中权威内裁决2作业已计入权威主/盲核行，
g01裁决52作业已计入映射主/盲核行；加法合计 4+4+36+36=**80** 与总量一致。

### 过程事件（如实）
- 开赛前健康断言：8911 /api/health ok（runtime_store integrity ok，schema v16）、
  /api/runtime-readiness ready:true（**build api-a9bb87fb5ee7ab77，与R19P同build**）、
  AI网关 /api/ai-gateway/status configured=true（zhipu-coding-plan/glm-5.3-flash，
  route_validation_errors=[]）；在册项目仅 R19D 常驻开考位 MX循开考-CSU，
  精确名 MX循R20P-CSU 无冲突；synth_csu 三件套在位；8910/5177 连接拒绝
  （000，未触碰）；台账非干净起点（外源lane 222 in-flight，见上节）；
- 01:04:07Z run1 启动：建项/上传即绿；文档权威 830s 过门（零人工门）；
  01:18 映射首遍启动，盲核10/10先行完成、主侧在共享工池下 ~2作业/9分钟，
  02:10 双队列20/20→adopt 201→21张问题卡按既有决策表作答→g01裁决波
  （多轮系统裁决+复活重试）→06:09 收敛预算14400s耗尽 exit 10（队列余5）；
- 06:12:48Z run2 幂等续跑：前三阶段状态复用重放，收敛继续排干
  （07:22 队列空）→adjudicate remaining 41→33→**0（sys=25，complete）**
  →confirm 200（07:49）→facts 201（2804值）→run-setup/bootstrap/
  prepare-and-start 三连200（07:49:59Z）→运行2.0s completed→发布
  available→结果可读（07:50:0xZ），八阶段全绿 exit 0；
- **3个g01盲核分片终态失败（全程可见）**：MH/EX/UAS 均为
  ollama-cloud/deepseek-v4.1-flash 的 listing-field-mapping-adjudication:verifier
  分片，4/4 次耗尽 provider_runtime_error（「AI provider returned only
  reasoning tokens with no final answer channel」），其中历经
  automatic_recovery 复活仍失败——与 R18P 6分片同族；本轮 bounded-gap
  吸收后 facts 覆盖 3422→2804（-618），链路仍 complete/confirmed/全绿；
  对照 R19P 同build 3分片同族失败全部自愈——瞬态家族在争抢负载下的自愈
  成功率下降，如实记录；
- 后续为复盘归档做了API独立复核（非驱动日志自证）：progress端点
  run_state=completed/percent=100.0/status_overview=[{已完成,count:10}]/
  publication_state=available/result_available=true、publication端点available
  （replayed=false）、runs列表仅1条（无孤儿）、result-entry 200 指针载荷+
  overview 独立读取 778,126字节·15发现（列表与meta.total双一致）/16受试者/
  477风险/identity归属、source-manifest medical_monitoring→real_source_slice
  ——全部一致（注：overview 正确路径为 /r7/results/…，无 /r7 前缀返回404）；
- console /tmp/mm_api_8911.log 全程 0 字节（uvicorn --log-level warning；
  本轮链路无门禁拒绝、无碎片化拦截，无需 console 取证）；
- 全程未触碰 8910/5177（开始/结束只读复核连接拒绝状态，000）；未改任何
  产品代码/数据库（驱动脚本与一次性预检项目自身数据除外）；项目
  MX循R20P-CSU 与全部留痕原地保留（归档交复盘官；在册另有 R19D 常驻
  开考位 MX循开考-CSU 仍active）。

---

## R19 第1次（20261005-06，run=r19p_preflight）——**chainOk = true，第十次全链端到端跑通（新build api-a9bb87fb5ee7ab77 首跑即单run全绿 exit 0：零未知卡、零用户裁决卡、零终态失败；碎片化家族未命中；3个盲核分片 transient reasoning-only 后经 attempt 自愈；facts 3422 值历史最高覆盖；总壁钟约1h38m 历史最快）**

- 驱动脚本：`scripts/tester_loop_0927/r19p_preflight_csu.py`（由 R18P 全绿驱动
  r18p_preflight_csu.py 机械适配 R19 命名/幂等键/留痕文件——diff 实测 24 行，
  全部为轮次标识替换与来源注释更新，R5D-R15D 裁决卡决策表与数据内容行原样
  保留（「是17/否17」等实测依据未误伤）；幂等，状态 `r19p_preflight_state.json`，
  留痕 `r19p_preflight_evidence.jsonl`（277事件，**0 条 ok=false**），
  运行日志 logs/r19p_preflight_run1.log，**单run exit 0，无 run2**）
- 数据：同 `tester_staging_0927/synth_csu` 三件套（方案V1.3 docx + eCRF指南V1.0 docx + 合成listing V1.0 xlsx）
- 项目：**MX循R19P-CSU**（proj_user_a526cc59cbab / MW-PHASE-C5A336DC，
  慢性自发性荨麻疹 / MG-K10 / modules 含 medical_monitoring【projects API：
  medical_monitoring:real_source_slice + source-manifest API 双核对】，
  幂等键 r19p-preflight-20261005T205013Z-10765291 唯一，精确名一次建项 201
  成功（在册仅 R19D 常驻开考位 MX循开考-CSU，无同名冲突），status=active，
  **留在原地待复盘归档**）
- 运行：run:783eed325e3f31b6ccf07930（run_start_idem=
  r19p-run-20261005T222751Z-a48f422e，run-setup/options 200（snapshot:
  7a5e6c1bfec8cf43ad78c994）→workspace/bootstrap 200→prepare-and-start
  一次 200（397ms），项目 runs 列表仅此1条无孤儿）
- 结果：result-context:76fa8fefb8044790bb00668f771b7527（overview 驱动侧
  序列化 597,305 字节；独立HTTP读取原始载荷 **778,126 字节——与R14P-R18P
  字节数完全一致**）

### 结论：chainOk = true（八阶段全ok；运行真完成10/10项100%、发布available、结果可读）

已知状态碎片化家族（后端confirmed vs 监查侧unconfirmed，readiness 409）
**未命中**——链尾 run-setup/options 200、workspace/bootstrap 200 后
prepare-and-start 一次 200（397ms），无 409 窗口，evidence 中
fragmentation_evidence 事件 0 条。

**本build首次预检**：runtime-readiness build **api-a9bb87fb5ee7ab77**
（R13-R18 均为 api-2ac4a3a5e6a1db40，两轮之间 build 已更换；赛前 R19D
开考位在同build同数据已验证至 facts 物化、0未知卡）。R18P 的主侧429风暴
窗口未复现——本轮主侧 cms-router 全程健康。

### 八阶段计时（秒数=首次真实完成；单run，总壁钟 20:50:13Z→22:28:24Z 约1h38m）

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.3 | proj_user_a526cc59cbab，精确名一次成功201；indication/product/modules 合同双核对无误 |
| 2 | 上传 | ✅ | 0.8 | attempt=stg-8f545a43aacc4302aa33ecbe821f0ba5，1文件/10表/591行 profile_ready |
| 3 | 文档权威 | ✅ | 469.0 | analyze 202（mmbatch_8ad6a257997104b439cbc78d）→analyzing→reviewing→adjudicating→cross_checking→needs_user_input（ecrf文件角色选择1次，19.8s）→ready=true「研究文件已准备好」；**零身份确认门**（R18有1次）；8个AI作业全completed |
| 4 | 映射确认 | ✅ | 5386.8（壁钟20:58Z→22:27Z约1h30m） | 首遍双队列20/20（主10/10+盲核10/10，无 invalid_ai_output）→60候选→adopt 201（monmapdraft_7e84fd0d28d3ee29050ab388d2db）→裁决波g01双队列20作业→adjudicate 4连发：running 46/0→running 46/0→blocked 26（sys 20）→**complete remaining=0（sys 20）**；**零用户裁决卡**（question_card_answer 0条、unknown_questions_fail_closed 0条）→confirm 200（draft status=confirmed） |
| 5 | facts | ✅ | 0.9 | state=ready：10表/591行/**3422值** source_values_verified=3422（物化100%；历史最高——R16P/R17P为3038、R18P为1752，本build口径+零终态失败无bounded-gap扣减） |
| 6 | 运行 | ✅ | 32.5 | run-setup/options 200→workspace/bootstrap 200→prepare-and-start 一次200（**碎片化家族未命中**）→run_state=completed，**10/10项100%「已完成」**（progress复核API独立确认 percent=100.0+status_overview=[{已完成,count:10}]+result_available=true） |
| 7 | 发布 | ✅ | 0.7 | publication POST 200→publication_state=available「结果已整理完成」（publication端点+progress端点双一致，replayed=false） |
| 8 | 结果 | ✅ | 1.0 | result-entry 200（指针载荷338B）；overview 独立读取778,126字节非空；**finding_count=15**（query_findings列表长度与query_findings_meta.total双一致）+current_risks=477；subject_count=16；identity.project_ref=proj_user_a526cc59cbab 归属核对无误；data_cutoff=2026-08-19 |

### AI 节点路由核验（台账：隔离实例 runs/tester_loop_iso_20260928/runtime/medical_monitoring_ai.sqlite3 直读；/api/ai/queue 本build仍404，模块级 ai/jobs 200）

本项目总量 **48 作业**（权威8[analysis 2+critique 2+review 2+裁决2] + 映射pipeline 20 +
映射裁决g01 20；task_type 视图 document_authority_analysis 2 + document_authority_review 6
+ listing_field_mapping 40 与之一致），终态 **48/48 全 completed，0 failed，
0 queued/running（无滞留、无静默失败）**；主侧 cms-router 24作业与盲核侧
ollama-cloud 24作业（各半，双队列对称）全completed。调用72次，
prompt 905,553 + completion 413,539 = **1,319,092 tokens**。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis/critique/review/裁决 :primary 各1） | 4 | 4 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（analysis/critique/review/裁决 :verifier 各1） | 4 | 4 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（pipeline listing-field-mapping ×10 + 裁决g01 :primary ×10） | 20 | 20 completed（首遍无 invalid_ai_output） | ✅ |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（pipeline mapping-verifier ×10 + 裁决g01 :verifier ×10） | 20 | 20 completed（**3个g01盲核分片 att1-3 reasoning-only 后自愈**，见下） | ✅ |
| 裁决（权威内+映射收敛） | 主 cms-router/glm-5.3-flash 11（权威1+g01×10）+ 盲核 ollama-cloud/deepseek-v4.1-flash 11（权威1+g01×10），tools车道 | 22 | 22 completed（映射裁决 adj_state=complete/remaining=0/sys=20；权威裁决双队列一致） | ✅ |
| 监查分析 | 本build运行lane不经AI台账（本项目 task_type 仅 document_authority_* 与 listing_field_mapping 双核对；FactsModeOutputProvider 事实回执确定性产出，同R10P3-R18P） | 0 | —（无作业=无滞留/无静默失败；15发现+477风险已产出） | ✅（机制核实，如实报0作业） |

注：**裁决行为横切视图非加法行**——其中权威内裁决2作业已计入权威主/盲核行，
g01裁决20作业已计入映射主/盲核行（与R18P表注同口径）；加法合计
4+4+20+20=**48** 与总量一致。权威8作业内部为 analysis/critique/review/裁决
各1对（task_type 视图 analysis 2 + review 6）。monitoring_daily_runs 存表
本build为空（0行，运行lane不落该表），运行真完成的权威证据为
progress/publication/result 三端点（已独立复核一致）。

### 过程事件（如实）
- 开赛前健康断言：8911 /api/health ok（runtime_store integrity ok，schema v16）、
  /api/runtime-readiness ready:true（**build api-a9bb87fb5ee7ab77，新build**）、
  AI网关 /api/ai-gateway/status configured=true（zhipu-coding-plan/glm-5.3-flash，
  route_validation_errors=[]）；在册项目仅 R19D 常驻开考位 MX循开考-CSU
  （proj_user_6ef58ac151e1，已至 facts 物化），精确名 MX循R19P-CSU 无冲突；
  synth_csu 三件套在位；实例级 AI 台账 0 queued/running（干净起点）；
  8910/5177 连接拒绝（000，未触碰）；
- 20:50:13Z run1 启动：建项/上传即绿；文档权威 469s 过门（本轮零身份确认门，
  仅 ecrf 文件角色选择1次设计内人工门）；20:58 映射首遍启动，21:17 双队列
  20/20 全completed→adopt 201（21:17:14Z）→裁决g01波（10主+10盲核）至
  22:21 排干→adjudicate blocked 26（sys 20）→22:27 complete remaining=0
  （sys 20，**零用户裁决卡零fail-closed**）→confirm 200→facts 201
  （3422值100%）→run-setup/bootstrap/prepare-and-start 三连200（22:27:51Z）
  →运行32.5s completed（22:28:22Z）→发布available（22:28:23Z）→结果
  可读（22:28:24Z），八阶段全绿 exit 0，**单run无续跑**；
- **3个g01盲核分片 transient 失败自愈（全程可见，无终态失败）**：均为
  ollama-cloud/deepseek-v4.1-flash 的 listing-field-mapping-adjudication:verifier
  分片，attempt 1-3 显式 failure_code=provider_runtime_error/
  provider_reasoning_only（「AI provider returned only reasoning tokens…」），
  经 resolve 复活路径 attempt 3/4 转 success（automatic_recovery_count=1），
  终态 completed——R18P 同家族6分片终态失败需 bounded-gap 吸收，本build
  该自愈路径首次全程把同类失败拉回成功，facts 覆盖 3422 值无扣减（如实对比）；
- 台账时间过滤勘误（工作留痕）：sqlite created_at 为 ISO'T'格式，与
  datetime('now') 空格格式字符串比较会误放大时间窗（首查误报全天2476次
  provider_error）；改用 julianday 过滤后近15分钟仅本项目7次尝试
  （2错5成），无跨项目争抢、无429风暴；
- 后续为复盘归档做了API独立复核（非驱动日志自证）：progress端点
  run_state=completed/percent=100.0/status_overview=[{已完成,count:10}]/
  publication_state=available/result_available=true、publication端点available、
  runs列表仅1条（无孤儿）、result-entry 200 指针载荷+overview 独立读取
  778,126字节·15发现（列表与meta.total双一致）/16受试者/477风险/
  identity归属、source-manifest medical_monitoring→real_source_slice——
  全部一致（注：overview 正确路径为 /r7/results/…，无 /r7 前缀返回404）；
- console /tmp/mm_api_8911.log 全程 0 字节（uvicorn --log-level warning，
  与前几轮同现象；本轮链路无门禁拒绝、无碎片化拦截，无需 console 取证）；
- 全程未触碰 8910/5177（开始/结束只读复核连接拒绝状态，000）；未改任何
  产品代码/数据库（驱动脚本与一次性预检项目自身数据除外）；项目
  MX循R19P-CSU 与全部留痕原地保留（归档交复盘官；在册另有 R19D 常驻
  开考位 MX循开考-CSU 仍active）。

---

## R18 第1次（20261005，run=r18p_preflight）——**chainOk = true，第九次全链端到端跑通（run1撞主侧AI路由429窗口+收敛预算耗尽exit10→run2幂等续跑全绿；碎片化家族未命中；6个裁决盲核分片终态失败经bounded-gap吸收，如实记录facts覆盖率下降3038→1752）**

- 驱动脚本：`scripts/tester_loop_0927/r18p_preflight_csu.py`（由 R17P 全绿驱动
  r17p_preflight_csu.py 机械适配 R18 命名/幂等键/留痕文件——diff 实测 38 行，
  全部为轮次标识替换（与R16P→R17P适配同规模），R5D-R15D 裁决卡决策表原样
  保留，数据内容行「是17/否17」未误伤；幂等，状态 `r18p_preflight_state.json`，
  留痕 `r18p_preflight_evidence.jsonl`（853驱动事件，唯一 ok=false 为 run1
  收敛预算耗尽的 stage_result 留痕），运行日志 logs/r18p_preflight_run1.log、
  run2.log，run1 退出码10（预算耗尽可重跑续）、run2 退出码0）
- 数据：同 `tester_staging_0927/synth_csu` 三件套（方案V1.3 docx + eCRF指南V1.0 docx + 合成listing V1.0 xlsx）
- 项目：**MX循R18P-CSU**（proj_user_429cae9629e8，慢性自发性荨麻疹 / MG-K10 /
  modules 含 medical_monitoring【projects+source-manifest API 双核对：发布后
  medical_monitoring → real_source_slice】，幂等键 r18p-preflight-20261005T082942Z-8efd4505
  唯一，精确名一次建项成功无需后缀（在册仅 MX循R18D-CSU 开考位），status=active，
  **留在原地待复盘归档**）
- 运行：run:bac6aaad1781e1b92a9402c4（run_start_idem=r18p-run-20261005T152031Z-e3392c01，
  run-setup/options 200→workspace/bootstrap 200→prepare-and-start 一次 200（1555ms），
  项目 runs 列表仅此1条无孤儿）
- 结果：result-context:6fada1d73eb64b8588213ed675cd05d0（overview 驱动侧序列化
  597,305 字节；独立HTTP读取原始载荷 778,126 字节——与R14P/R15P/R16P/R17P字节数完全一致）

### 结论：chainOk = true（八阶段全ok；运行真完成10/10项100%、发布available、结果可读）

已知状态碎片化家族（后端confirmed vs 监查侧unconfirmed，readiness 409）**未命中**
——run2 链尾 run-setup/options 200、workspace/bootstrap 200 后 prepare-and-start
一次 200，无 409 窗口，evidence 中 fragmentation_evidence 事件 0 条。

**本轮真实事件（如实，全程未改产品代码/数据库；驱动脚本与一次性预检项目自身数据除外）**：
1. **主侧AI路由429风暴（环境级，非链路缺陷，未修复只记录）**：cms-router/
   glm-5.3-flash 自 2026-10-05T01:18:18Z 起全部调用 HTTP 429（起始时 R17D
   映射主道正以正常节奏 1-2 次/分成功——01:16:12Z 最后一次成功，属配额墙
   非突发风暴），零成功持续约 8 小时，至 09:16-09:19Z 恢复（本轮权威主作业
   255 次尝试后 09:16:24Z completed 为恢复首证）。期间 R18D 开考位（proj_user_74e02b4af07c）
   的文档权威主作业陷入「终态failed→resolve轮询复活→重试429」循环（attempt
   1600+，08:26-08:28Z 台账直读实证）；r18d_supervise.sh 连续 6 轮 exit=10
   卡 documents 步（r18d_seed_console.log）。本轮未触碰该循环（非本岗职责），
   恢复后该lane自行重新推进（15:27Z 台账见其作业 attempt 重置为1并开始完成）；
2. **run1 在 429 窗口内启动**：建项/上传即绿；文档权威盲核 14s 完成（ollama
   健康），主作业在 429 窗口内循环重试，恰好等到 09:19Z 窗口开启后一口气完成
   （analysis+critique/review链×主盲核全 completed），3180s 过门；映射首遍
   双队列 20/20 全 completed（无 invalid_ai_output 首遍失败）→adopt 201→裁决
   多波收敛（remaining 46→31→22→16，system_adjudicated 0→24→30）至 4h 收敛
   预算耗尽 exit 10（15691s，仍在推进非阻断）；
3. **run2 幂等续跑全绿**：前三阶段秒级复用；收敛续推 remaining 16→9→0
   （sys=37）→confirm 200（24.3s，facts_generated=true）→facts→运行5.8s→
   发布available→结果可读，八阶段全绿 exit 0。**10张用户裁决卡**（EX·EXTRT
   run1内 + AE×8 + SV·VISDAT run2内）全部命中既有决策表按数据实测作答，
   unknown_questions_fail_closed 事件 0 条；
4. **6个裁决盲核分片终态失败，可见且被吸收**：全部为 ollama-cloud/deepseek-v4.1-flash
   的 listing-field-mapping-adjudication:verifier 分片，显式 failure_code=
   provider_runtime_error / failure_message=「AI provider returned only
   reasoning tokens with no final answer channel…(provider_reasoning_only)」、
   各 att=2/2、无静默失败；经 bounded-gap 吸收后 adjudicate complete
   （remaining=0）。**如实记录代价：facts 物化 10表/591行/1752值
   source_values_verified=1752（物化值100%核验，但绝对值低于 R16P/R17P 的
   3038——与 R15P 记载的盲核终态失败→覆盖下降同现象，3038→1752）**。

### 八阶段计时（秒数=首次真实完成；映射确认为 run1+run2 两段活跃驱动窗口合计 21402.5s，中间58s重启间隙不计入；总壁钟 08:29:42Z→15:20:38Z 约6h51m，其中429窗口等待约2h54m包含在文档权威3180s内）

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.0 | proj_user_429cae9629e8，精确名一次成功（在册仅 MX循R18D-CSU 开考位，无同名冲突）；indication/product/modules 合同双核对无误 |
| 2 | 上传 | ✅ | 0.2 | attempt=stg-460555f9071d42a299bd9b9edd465ce3，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 3180.0 | analyze→主作业429窗口内255次尝试→09:19Z窗口开启后完成→（ecrf文件角色选择1次）→ready=true「研究文件已准备好」；8个AI作业全completed（analysis 1+1、review链 3+3，主/盲核） |
| 4 | 映射确认 | ✅ | 21402.5（run1 15691 + run2 5711.5；壁钟09:22:42Z→15:20:27Z约5h58m） | 首遍双队列20/20→60候选→adopt 201（monmapdraft_944a63003bb4bcef500c4061583f）→裁决多波收敛（remaining 46→31→22→16→9→0；system_adjudicated 0→15→24→30→37）→10张用户卡按实测决策表作答→confirm 200（24.3s confirmed，facts_generated=true） |
| 5 | facts | ✅ | 1.2 | state=ready：10表/591行/**1752值** source_values_verified=1752（物化100%；绝对值低于R16P/R17P的3038，6盲核终态失败bounded-gap吸收的代价，如实） |
| 6 | 运行 | ✅ | 5.8 | run-setup/options 200→workspace/bootstrap 200→prepare-and-start 一次200（**碎片化家族未命中**）→run_state=completed，**10/10项100%「已完成」**（progress复核API独立确认 percent=100.0+status_overview=[{已完成,count:10}]+result_available=true） |
| 7 | 发布 | ✅ | 1.5 | publication POST 200→publication_state=available「结果已整理完成」（publication端点+progress端点双一致） |
| 8 | 结果 | ✅ | 1.2 | result-entry 200（指针载荷338B：snapshot_token+result_context_token）；overview 独立读取778,126字节非空；**finding_count=15**（query_findings列表长度与query_findings_meta.total双一致）+current_risks=477；subject_count=16；identity.project_ref=proj_user_429cae9629e8 归属核对无误；data_cutoff=2026-08-19 |

### AI 节点路由核验（台账：隔离实例 runs/tester_loop_iso_20260928/runtime/medical_monitoring_ai.sqlite3 直读；/api/ai/queue 本build仍404，模块级 ai/jobs 200）

本项目总量 **80 作业**（权威8 + 映射pipeline 20 + 裁决52[主26+盲核26]），终态
**74 completed + 6 terminal failed**，**0 queued/running（项目级无滞留）**；
6个 failed 全部为裁决盲核分片、全部有显式 failure_code/failure_message
（provider_reasoning_only，att=2/2），无静默失败；主侧（cms-router）40作业
**全completed零失败**。调用404次，prompt 1,589,019 + completion 873,163 =
**2,462,182 tokens**。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis primary-v9 ×1[**att=255，429窗口内等待**] + review primary ×3） | 4 | 4 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（analysis verifier ×1 + review verifier ×3） | 4 | 4 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（pipeline listing-field-mapping ×10 + 裁决 primary ×26） | 36 | 36 completed（首遍无 invalid_ai_output） | ✅ |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（pipeline mapping-verifier ×10 + 裁决 verifier ×26） | 36 | 30 completed + 6 failed（全部 reasoning-only 显式失败码，bounded-gap吸收） | ✅（失败可见且按设计恢复为可见缺口） |
| 裁决（映射收敛） | 主 cms-router/glm-5.3-flash 26（26 completed）+ 盲核 ollama-cloud/deepseek-v4.1-flash 26（20 completed+6 failed），tools车道 | 52 | 46 completed + 6 failed（46分歧=系统37+用户卡10消化，adj_state=complete/remaining=0/sys=37） | ✅ |
| 监查分析 | 本build运行lane不经AI台账（本项目 task_type 仅 document_authority_* 与 listing_field_mapping 双核对；FactsModeOutputProvider 事实回执确定性产出，同R10P3-R17P） | 0 | —（无作业=无滞留/无静默失败；15发现+477风险已产出） | ✅（机制核实，如实报0作业） |

注：映射主/映射盲核行含首遍pipeline双队列（10+10）与裁决车道（26+26）；
裁决行单列的是其中裁决车道52作业。四行合计 4+4+36+36=80 与总量一致。

### 过程事件（如实）
- 开赛前健康断言：8911 /api/health ok（runtime_store integrity ok，schema v16）、
  /api/runtime-readiness ready:true（build api-2ac4a3a5e6a1db40，与 R13-R17 同build）、
  AI网关 /api/ai-gateway/status configured=true（zhipu-coding-plan/glm-5.3-flash，
  route_validation_errors=[]）；在册项目仅 MX循R18D-CSU（开考位，429循环卡
  documents），精确名 MX循R18P-CSU 无冲突；synth_csu 三件套在位；8910/5177
  连接拒绝（000，未触碰）；
- **赛前基线观察（环境级，非本轮所致、未处理）**：主侧路由 cms-router 429
  连续 7h10m（01:18Z 起零成功，实例台账 1600+ 失败调用，每小时约 250-320 次
  探测全 429）；R18D 权威主作业 revive-retry 循环 att=1608→1616 实时目击；
  r18d_supervise.sh 6 轮 exit=10（r18d_seed_console.log 04:09Z-08:20Z）；
  盲核侧 ollama-cloud 同窗健康（03:00-05:00Z 81次成功/14次失败）；
- 08:29:42Z run1 启动：建项/上传即绿；权威盲核 14s 完成，主作业 08:34:40Z
  首次终态failed（30次bounded重试429）后被resolve轮询复活续试（与R18D同机理，
  08:35Z att=30→34 实时目击）——**这是驱动面设计内的自愈路径，非绕过**；
  09:19:07Z 主侧窗口开启（本项目首证），09:16:24Z 权威主作业 completed、
  review链快速过，09:22:32Z ecrf角色选择→09:22:42Z ready；映射首遍 09:43Z
  前后 20/20→adopt 201（09:43:53Z）→裁决波 46→31（sys 15）→22（sys 24），
  13:44:13Z 4h收敛预算耗尽 exit 10（唯一 ok=false 事件即此 stage_result）；
- 13:45:11Z run2 幂等续跑：前三阶段秒级复用；收敛 22→16（sys 30）→9→0
  （sys 37，adjudicate complete）；15:18:34-15:18:55Z 9张用户卡（AE×8+SV·VISDAT）
  按实测决策表作答（EX·EXTRT 已在 run1 09:43:53Z 作答）；15:20:27Z confirm
  200（24.3s）→facts 201→run-setup/bootstrap/prepare-and-start 三连200→
  运行5.8s completed→发布available→结果可读（15:20:38Z），八阶段全绿 exit 0；
- 后续为复盘归档做了API独立复核（非驱动日志自证）：progress端点 run_state=
  completed/percent=100.0/status_overview=[{已完成,count:10}]/publication_state=
  available/result_available=true、publication端点 available+「结果已整理完成」、
  runs列表仅1条（无孤儿）、result-entry 200 指针载荷+overview 独立读取
  778,126字节·15发现（列表与meta.total双一致）/16受试者/477风险/identity归属、
  source-manifest medical_monitoring→real_source_slice——全部一致；
- console /tmp/mm_api_8911.log 全程与赛前基线一致（0字节，uvicorn
  --log-level warning；本轮链路无门禁拒绝、无碎片化拦截，无需 console 取证）；
- 全程未触碰 8910/5177（开始/结束只读复核连接拒绝状态，000）；未改任何产品
  代码/数据库（驱动脚本与一次性预检项目自身数据除外）；项目 MX循R18P-CSU 与
  全部留痕原地保留（归档交复盘官；在册另有 R18D 开考位项目 MX循R18D-CSU
  仍active，429恢复后其种子lane已自行恢复推进）。

---

## R17 第1次（20261004，run=r17p_preflight）——**chainOk = true，第八次全链端到端跑通（单run零fail-closed零未知卡；碎片化家族未命中；facts 满覆盖3038值；1个裁决主分片终态失败经bounded-gap吸收）**

- 驱动脚本：`scripts/tester_loop_0927/r17p_preflight_csu.py`（由 R16P 全绿驱动
  r16p_preflight_csu.py 机械适配 R17 命名/幂等键/留痕文件——diff 实测 38 行，
  全部为轮次标识替换，R5D-R15D 裁决卡决策表原样保留；幂等，状态
  `r17p_preflight_state.json`，留痕 `r17p_preflight_evidence.jsonl`
  （474驱动事件，0条ok=false），运行日志 logs/r17p_preflight_run1.log，退出码 0）
- 数据：同 `tester_staging_0927/synth_csu` 三件套（方案V1.3 docx + eCRF指南V1.0 docx + 合成listing V1.0 xlsx）
- 项目：**MX循R17P-CSU**（proj_user_20c4a3880375，慢性自发性荨麻疹 / MG-K10 /
  modules 含 medical_monitoring【projects+source-manifest API 双核对：发布后
  medical_monitoring → real_source_slice】，幂等键 r17p-preflight-20261004T193426Z-3b0bf5c7
  唯一，精确名一次建项成功无需后缀，status=active，**留在原地待复盘归档**）
- 运行：run:91d42cd0b0b9de85ca2ba9d4（run_start_idem=r17p-run-20261004T231504Z-7d01c90d，
  prepare-and-start 一次 200，项目 runs 列表仅此1条无孤儿）
- 结果：result-context:f02aaa35e2324ec494c86fce1ba91ad8（overview 驱动侧序列化
  597,305 字节；独立HTTP读取原始载荷 778,126 字节——与R14P/R15P/R16P字节数完全一致）

### 结论：chainOk = true（八阶段全ok；运行真完成10/10项100%、发布available、结果可读）

已知状态碎片化家族（后端confirmed vs 监查侧unconfirmed，readiness 409）**未命中**
——本轮 run-setup/options 200、workspace/bootstrap 200 后 prepare-and-start 一次 200，
无 409 窗口，无需碎片化取证（evidence 中 fragmentation_evidence 事件 0 条）。

**本轮真实事件（如实，全程未改产品代码/数据库）**：
1. **单 run 全绿，零 fail-closed、零未知卡**：收敛期浮现 **29 张用户裁决卡**
  （AE 8 + CM 6 + DM 5 + EX 2 + LB_HEM 1 + MH 3 + UAS 4，evidence
  question_card_answer 事件逐卡留痕），全部命中 R5D-R15D 既有决策表按数据实测
  作答（unknown_questions_fail_closed 事件 0 条）；draft v1→76，confirm 200，
  mapping state=candidates_ready / draft.status=confirmed / user_questions=0；
2. **裁决收敛三波，盲核道串行主导壁钟**：remaining 46→42→27→0、
  system_adjudicated 0→4→19→19（46分歧 = 系统19 + 用户27后收敛，29卡含波间重复浮出面），
  收敛 12612.1s（约3h30m，慢于R16P的6942s——盲核裁决道本轮19分片逐个串行，
  中途 DM 分片一次 controlled repair 重试后通过）；裁决AI作业 38 个（主19+盲核19）；
3. **1个裁决主分片终态失败，可见且被吸收**：主侧 EX/裁决分片
  invalid_ai_output（"provider output remained invalid after one controlled repair"，
  att=2/3，automatic_recovery_count=1，显式failure_code+failure_message），经
  bounded-gap 吸收后 adjudication complete（remaining=0）——**facts 满覆盖：
  10表/591行/3038值，source_values_verified=3038（100%），与R14P/R15D/R16P持平**；
4. **文档权威本轮8作业（长内部复核链，同R15P形态）**：analysis+critique+review+
  adjudication 四环节 × 主/盲核各1，全completed；docs resolve 状态链
  analyzing→reviewing→adjudicating→cross_checking→needs_user_input（身份归属确认
  1次，自动）→ready，625.3s。

### 八阶段计时（秒数=首次真实完成；总活跃驱动 13269.0s，壁钟 19:34:26Z→23:15:35Z 约3h41m，映射收敛3h30m占绝对主导）

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.0 | proj_user_20c4a3880375，精确名一次成功（在册仅 MX循R17D-CSU 开考位，无同名冲突）；indication/product/modules 合同双核对无误；status=active |
| 2 | 上传 | ✅ | 0.2 | attempt=stg-975a0e04a8a5416cb0e0fd9f498804fb，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 625.3 | analyze→长内部复核链（analysis/critique/review/adjudication × 主/盲核）→（身份归属确认1次，自动）→ready=true「研究文件已准备好」；8个AI作业全completed |
| 4 | 映射确认 | ✅ | 12612.1 | 双队列10+10→candidates_ready（60候选）→裁决三波收敛（remaining 46→42→27→0；system_adjudicated 0→4→19）→29张用户卡全按数据实测决策表作答→adjudicate complete（remaining=0）→confirm 200（draft v76 confirmed，user_questions=0） |
| 5 | facts | ✅ | 0.2 | state=ready：10表/591行/**3038值** source_values_verified=3038（100%物化值核验） |
| 6 | 运行 | ✅ | 30.3 | workspace/bootstrap 200→run-setup/options 200→prepare-and-start 一次200（**碎片化家族未命中**）→run_state=completed，**10/10项100%「已完成」**（progress复核API独立确认percent=100.0+status_overview=[{已完成,count:10}]+result_available=true） |
| 7 | 发布 | ✅ | 0.4 | publication POST 200→publication_state=available（progress侧publication_state=available+result_available=true双端点一致） |
| 8 | 结果 | ✅ | 0.5 | result-entry 200；overview 非空（序列化597,305字节/原始载荷778,126字节）；**finding_count=15**（query_findings列表长度与query_findings_meta.total双一致）+current_risks=477；subject_count=16；identity.project_ref=proj_user_20c4a3880375 归属核对无误 |

### AI 节点路由核验（台账：隔离实例 runs/tester_loop_iso_20260928/runtime/medical_monitoring_ai.sqlite3 直读；/api/ai/queue 本build仍404，模块级 ai/jobs 200）

本项目总量 **66 作业**（权威8 + 映射pipeline 20 + 裁决38），终态 **65 completed +
1 terminal failed**，**0 queued/running（项目级无滞留）**；唯一 failed 为裁决主侧
EX分片 invalid_ai_output，有显式 failure_code/failure_message（provider输出缺
schema_version/task_id/candidates等必填字段，一次受控修复后仍无效）、att=2/3、
automatic_recovery_count=1，无静默失败；经 bounded-gap 吸收后 adjudication
complete/remaining=0，facts 满覆盖3038值。调用95次（observed 与 requested
response_model 全一致，0 mismatch），prompt 1,293,434 + completion 690,857 =
**1,984,291 tokens**。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis/critique/review/adjudication primary 各1） | 4 | 4 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（analysis/critique/review/adjudication verifier 各1） | 4 | 4 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（pipeline listing-field-mapping-v19 ×10 + adjudication primary ×19） | 29 | 28 completed + 1 failed（EX裁决分片 invalid_ai_output att=2/3，bounded-gap吸收） | ✅（失败可见且按设计恢复为可见缺口） |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（pipeline mapping-verifier/verifier 分片 ×10 + adjudication verifier ×19） | 29 | 29 completed | ✅ |
| 裁决（映射收敛） | 主 cms-router/glm-5.3-flash 19（18 completed+1 failed）+ 盲核 ollama-cloud/deepseek-v4.1-flash 19（19 completed），tools车道 | 38 | 37 completed + 1 failed（终态失败为可见缺口；46分歧=系统19+用户卡全消化，adj_state=complete/remaining=0） | ✅ |
| 监查分析 | 本build运行lane不经AI台账（本项目 business_key 仅 document-authority-* 与 listing-field-mapping* 两族；FactsModeOutputProvider 事实回执确定性产出，同R10P3-R16P） | 0 | —（无作业=无滞留/无静默失败；15发现+477风险已产出） | ✅（机制核实，如实报0作业） |

注：映射主/映射盲核行含首遍pipeline双队列（10+10）与裁决车道（19+19）；
裁决行单列的是其中裁决车道38作业。四行合计 4+4+29+29=66 与总量一致。

### 过程事件（如实）
- 开赛前健康断言：8911 /api/health ok（runtime_store integrity ok，schema v16）、
  /api/runtime-readiness ready:true（build api-2ac4a3a5e6a1db40，与 R13-R16 轮
  同build）、AI网关 /api/ai-gateway/status configured=true（zhipu-coding-plan/
  glm-5.3-flash，route_validation_errors=[]）；在册项目仅 MX循R17D-CSU（开考位，
  已推至 facts ready），精确名 MX循R17P-CSU 无冲突；synth_csu 三件套在位；
  8910/5177 连接拒绝（000，未触碰）；
- **赛前基线观察（如实记录，非本轮所致、未处理）**：实例台账存在 1 个僵尸
  running 作业 monai_a7a4be4f864671b0d180ce4a3088（listing_field_mapping PE2
  分片，属 proj_user_912dfa63e8cd——该项目不在当前实例项目注册表中，为历轮
  遗留），created 2026-10-04T04:40:02Z、attempt 2、lease 已于 13:41:36Z 过期、
  全程 updated_at 停在 13:11:36Z 未再变化；本轮全链（含映射双队列与裁决三波）
  在其存在期间完整跑通，证明其不阻塞新作业；R17D（13:22Z→19:24Z 完整推至
  facts ready）亦在其之后完成——按预检职责只记录不修复；
- 19:34:26Z run1（唯一run）启动：精确名建项一次成功；上传 0.2s；文档权威
  625.3s 全绿（长内部复核链+自动身份归属确认1次，无文件角色人工裁决）；
  映射双队列 19:44:52Z 启动，首遍10主+10盲核全completed→60候选→adopt 201
  （monmapdraft_330742f5cd6b3cd659f366857fa7）→裁决三波约3h30m收敛
  （盲核道串行19分片逐个跑，DM分片一次controlled repair后通过）→29张用户
  裁决卡全按 R5D-R15D 数据实测决策表作答→confirm 200（draft v76）；
  23:15:04Z facts → 运行30.3s → 发布available → 结果可读（23:15:35Z）；
- 后续为复盘归档做了API独立复核（非驱动日志自证）：progress端点 run_state=
  completed/percent=100.0/status_overview=[{已完成,count:10}]/publication_state=
  available/result_available=true、publication端点available、result-entry 200/
  overview 独立读取778,126字节·15发现（列表与meta.total双一致）/16受试者/
  477风险/identity归属、mapping-candidates终读 draft v76 confirmed/
  user_questions=0/candidates=60、source-manifest real_source_slice、runs列表
  仅1条（无孤儿，run_state=completed）——全部一致；
- console /tmp/mm_api_8911.log 全程与赛前基线一致（0字节，uvicorn --log-level
  warning；本轮链路无门禁拒绝、无碎片化拦截，无需 console 取证）；
- 全程未触碰 8910/5177（开始/结束只读复核连接拒绝状态）；未改任何产品代码/
  数据库（驱动脚本与一次性预检项目自身数据除外）；项目 MX循R17P-CSU 与全部
  留痕原地保留（归档交复盘官；在册另有 R17D 开考位项目 MX循R17D-CSU 仍active）。

---

## R16 第1次（20261004，run=r16p_preflight）——**chainOk = true，第七次全链端到端跑通（单run零fail-closed零未知卡；碎片化家族未命中；facts 恢复满覆盖3038值；2个EX裁决分片终态失败经bounded-gap吸收）**

- 驱动脚本：`scripts/tester_loop_0927/r16p_preflight_csu.py`（由 R15P 全绿驱动
  r15p_preflight_csu.py 机械适配 R16 命名/幂等键/留痕文件——diff 仅轮次标识行，
  R5D-R15D 裁决卡决策表原样保留；幂等，状态 `r16p_preflight_state.json`，
  留痕 `r16p_preflight_evidence.jsonl`（311驱动事件），运行日志
  logs/r16p_preflight_run1.log，退出码 0）
- 数据：同 `tester_staging_0927/synth_csu` 三件套（方案V1.3 docx + eCRF指南V1.0
  docx + 合成listing V1.0 xlsx）
- 项目：**MX循R16P-CSU**（proj_user_40af822c4021，慢性自发性荨麻疹 / MG-K10 /
  modules 含 medical_monitoring【projects+source-manifest API 双核对；发布后
  medical_monitoring → real_source_slice】，幂等键 r16p-preflight-20261004T021422Z-937b996e
  唯一，精确名一次建项成功无需后缀，status=active，**留在原地待复盘归档**）
- 运行：run:cfbfa81c373158b61081e498（run_start_idem=r16p-run-20261004T041433Z-07f76e7e，
  prepare-and-start 一次 200，项目 runs 列表仅此1条无孤儿）
- 结果：result-context:bd10d2d86b204f70b7f6d8e2f7b52133（overview 驱动侧序列化
  597,305 字节；独立HTTP读取原始载荷 778,126 字节——与R14P/R15P字节数完全一致）

### 结论：chainOk = true（八阶段全ok；运行真完成10/10项100%、发布available、结果可读）

已知状态碎片化家族（后端confirmed vs 监查侧unconfirmed，readiness 409）**未命中**
——本轮 run-setup/options 200、workspace/bootstrap 200 后 prepare-and-start
一次 200，无 409 窗口，无需碎片化取证；source-manifest medical_monitoring →
**real_source_slice**。

**本轮真实事件（如实，全程未改产品代码/数据库）**：
1. **单 run 全绿，零 fail-closed、零未知卡**：收敛期浮现 **28 张用户裁决卡**
  （AE 7 + CM 2 + DM 4 + ICF 2 + LB_HEM 3 + MH 5 + UAS 4 + MHNUM），全部命中
  R5D-R15D 既有决策表按数据实测作答（比R15P的13张多，分歧面逐轮不同属正常
  波动）；draft v1→47→75，confirm 200，mapping state=candidates_ready /
  draft.status=confirmed / user_questions=0；
2. **裁决收敛更快且分歧消化结构不同**：remaining 46→46→28→0、
  system_adjudicated 0→0→18→18（46分歧 = 系统18 + 用户28），收敛6942s（约1h56m，
  快于R15P的3h）；裁决AI作业本轮20个（主10+盲核10，R15P为60个）；
3. **2个EX域裁决分片终态失败，可见且被吸收**：主侧1个
  invalid_ai_output（"provider output remained invalid after one controlled
  repair"，att=2/3，显式failure_code）+ 盲核侧1个 provider_runtime_error
  （reasoning-only，att=4/4，R12-R15已知家族），均bounded-gap吸收后
  adjudication complete（remaining=0）——**facts 恢复满覆盖：10表/591行/3038值，
  source_values_verified=3038（100%），回到R14P/R15D水平（R15P曾降至2204）**；
4. **文档权威本轮4作业（短链）**：analysis + review 各主/盲核1个（R15P为8作业
  长内部复核链），268.3s全completed。

### 八阶段计时（秒数=首次真实完成；总活跃驱动 7242.1s，壁钟 02:14:22Z→04:15:04Z 约2h1min，映射收敛1h56m占绝对主导）

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.0 | proj_user_40af822c4021，精确名一次成功（在册 MX循R16D-CSU 无同名冲突）；indication/product/modules 合同双核对无误；status=active |
| 2 | 上传 | ✅ | 0.2 | attempt=stg-1555e0e482b248b3b66623bff2639e1e，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 268.3 | analyze→（身份归属确认1次，自动）→ready=true「研究文件已准备好」；4个AI作业全completed（analysis/review × 主/盲核各1） |
| 4 | 映射确认 | ✅ | 6942.3 | 双队列10+10→candidates_ready（60候选）→裁决收敛（remaining 46→46→28→0；system_adjudicated 0→18）→28张用户卡全按数据实测决策表作答→adjudicate complete（remaining=0）→confirm 200（draft v75 confirmed） |
| 5 | facts | ✅ | 0.2 | state=ready：10表/591行/**3038值** source_values_verified=3038（100%物化值核验，恢复R14P/R15D满覆盖水平） |
| 6 | 运行 | ✅ | 30.3 | workspace/bootstrap 200→run-setup/options 200→prepare-and-start 一次200（**碎片化家族未命中**）→run_state=completed，**10/10项100%「已完成」**（progress复核API独立确认percent=100.0+status_overview[{已完成,count:10}]） |
| 7 | 发布 | ✅ | 0.4 | publication POST 200→publication_state=available（progress侧publication_state=available+result_available=true双端点一致） |
| 8 | 结果 | ✅ | 0.4 | result-entry 200；overview 非空（序列化597,305字节/原始载荷778,126字节）；**finding_count=15**（query_findings列表长度与query_findings_meta.total双一致）+current_risks=477；subject_count=16；identity.project_ref=proj_user_40af822c4021 归属核对无误 |

### AI 节点路由核验（台账：隔离实例 runs/tester_loop_iso_20260928/runtime/medical_monitoring_ai.sqlite3 直读；/api/ai/queue 本build仍404）

本项目总量 **44 作业**（权威4 + 映射pipeline 20 + 裁决20），终态 **42 completed +
2 terminal failed**，**0 queued/running（无滞留；全台账亦0滞留）**；2 个 failed
均为EX域裁决分片，均有显式 failure_code（主侧invalid_ai_output / 盲核侧
provider_runtime_error reasoning-only）+ failure_message，无静默失败。调用66次
（observed_model 与 requested 全一致，0 mismatch），prompt 1,004,822 +
completion 524,643 = **1,529,465 tokens**。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis primary-v9 ×1 + review primary-v7 ×1） | 2 | 2 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（analysis verifier-v9 ×1 + review verifier-v7 ×1） | 2 | 2 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（pipeline listing-field-mapping-v19 ×10 + adjudication-v19-tools-v7.2 ×10） | 20 | 19 completed + 1 failed（EX分片 invalid_ai_output att=2/3，bounded-gap吸收） | ✅（失败可见且按设计恢复为可见缺口） |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（pipeline mapping-verifier-v8-tools-v6 ×10 + adjudication-verifier-v17-tools-v7.2 ×10） | 20 | 19 completed + 1 failed（EX分片 reasoning-only att=4/4 已知家族，bounded-gap吸收） | ✅（同上） |
| 裁决（映射收敛） | 同上两车道（主 cms-router/glm-5.3-flash 10 + 盲核 ollama-cloud/deepseek-v4.1-flash 10，tools-v7.2） | 20 | 18 completed + 2 failed（终态失败为可见缺口；46分歧=系统18+用户28全消化，adj_state=complete） | ✅ |
| 监查分析 | 本build运行lane不经AI台账（本项目 task_type 仅 document_authority_analysis/review + listing_field_mapping；FactsModeOutputProvider 事实回执确定性产出，同R10P3-R15P） | 0 | —（无作业=无滞留/无静默失败；15发现+477风险已产出） | ✅（机制核实，如实报0作业） |

注：映射主/映射盲核行含 pipeline 双队列与裁决车道（business_key 前缀区分），
裁决行单列的是其中裁决车道部分；三行作业数合计 20+20+20 与总量44的关系为
pipeline 20 与裁决 20 分属映射两行、裁决行重复计其中20。

### 过程事件（如实）
- 开赛前健康断言：8911 /api/health ok（runtime_store integrity ok，schema v16）、
  /api/runtime-readiness ready:true（build api-2ac4a3a5e6a1db40，与 R13-R15 轮
  同build）、AI网关 /api/ai-gateway/status configured=true（zhipu-coding-plan/
  glm-5.3-flash，route_validation_errors=[]）、实例台账基线 412 completed +
  12 failed 且 **0 queued/running**（R15D/R15P及更早轮遗产）；8910/5177 连接
  拒绝（000，未触碰）；synth_csu 三件套在位；在册项目仅 MX循R16D-CSU（开考位，
  已推至 facts ready），精确名 MX循R16P-CSU 无冲突；
- 02:14:22Z run1（唯一run）启动：精确名建项一次成功；上传 0.2s；文档权威
  268.3s 全绿（自动身份归属确认1次，无文件角色人工裁决）；映射双队列 02:18:54Z
  启动，约17分钟 candidates_ready（10主+10盲核全completed，60候选）；收敛波约
  1h56m：remaining 46→46→28→0，system_adjudicated 0→0→18→18，28张用户裁决卡
  全按 R5D-R15D 数据实测决策表作答，无未知卡、无fail-closed；confirm 200 后
  facts/运行/发布/结果 全部秒级~30s级完成（04:14:33Z facts → 04:15:04Z 结果可读）；
- 后续为复盘归档做了API独立复核（非驱动日志自证）：progress端点 run_state=
  completed/percent=100.0/status_overview=[{已完成,count:10}]/publication_state=
  available/result_available=true、publication端点available、result-entry 200/
  overview 独立读取15发现（列表与meta.total双一致）/16受试者/477风险/
  identity归属、source-manifest real_source_slice、runs列表仅1条（无孤儿，
  run_state=completed）——全部一致；
- console /tmp/mm_api_8911.log 全程与赛前基线一致（0字节，uvicorn --log-level
  warning；本轮链路无门禁拒绝、无碎片化拦截，无需 console 取证）；
- 全程未触碰 8910/5177（开始/结束只读复核连接拒绝状态）；未改任何产品代码/
  数据库（驱动脚本、一次性预检项目自身数据、产品恢复路径内的裁决重试除外）；
  项目 MX循R16P-CSU 与全部留痕原地保留（归档交复盘官；在册另有 R16D 开考位
  项目 MX循R16D-CSU 仍active）。

---

## R15 第1次（20261003，run=r15p_preflight）——**chainOk = true，第六次全链端到端跑通（单run零fail-closed；R15D卡表全覆盖；5个盲核终态失败经bounded-gap吸收——如实记录facts覆盖率下降3038→2204）**

- 驱动脚本：`scripts/tester_loop_0927/r15p_preflight_csu.py`（由 R14P 全绿驱动
  r14p_preflight_csu.py 的8阶段流程面 + R15D 轮已在本build同数据完整验证至
  facts 的裁决卡表 R5D-R15D（含 R13/R14 dict 卡与 R15_ROUND1_CARDS VS 四列）
  机械组装适配 R15P 命名/幂等键/留痕文件；幂等，状态
  `r15p_preflight_state.json`，留痕 `r15p_preflight_evidence.jsonl`（385驱动
  事件），运行日志 logs/r15p_preflight_run1.log）
- 数据：同 `tester_staging_0927/synth_csu` 三件套（方案V1.3 docx + eCRF指南V1.0 docx + 合成listing V1.0 xlsx）
- 项目：**MX循R15P-CSU**（proj_user_655f6a5bbac5，慢性自发性荨麻疹 / MG-K10 /
  modules 含 medical_monitoring【projects+source-manifest API 双核对；发布后
  medical_monitoring → real_source_slice】，幂等键 r15p-preflight-20261003T193608Z-533bdb6e
  唯一，精确名一次建项成功无需后缀，status=active，**留在原地待复盘归档**）
- 运行：run:348d287368d0c54caf511f9a（run_start_idem=r15p-run-20261003T224407Z-29a1bfca，
  prepare-and-start 一次 200，项目 runs 列表仅此1条无孤儿）
- 结果：result-context:1ebd50f120fa418390f6b6c20b6380af（overview 驱动侧序列化
  597,305 字节；独立HTTP读取原始载荷 778,126 字节）

### 结论：chainOk = true（八阶段全ok；运行真完成10/10项100%、发布available、结果可读）

已知状态碎片化家族（readiness 409）**未命中**——本轮 run-setup/options 200、
workspace/bootstrap 200 后 prepare-and-start 一次 200，无 409 窗口；
source-manifest medical_monitoring → **real_source_slice**。

**本轮真实事件（如实，全程未改产品代码/数据库）**：
1. **单 run 全绿，零 fail-closed**：R15D 卡表（27卡决策面）本轮全部覆盖收敛期
   实际浮现的 13 张用户裁决卡（EX.EXFRQ/EX.EXTRT + ICF/LB_HEM/MH/UAS 既有卡），
   无新未知卡（VS 四列卡 R15D 已收编，本轮未再浮现需作答的 VS 卡）；
2. **收敛期失败家族多次复发并被产品恢复路径消化**：盲核裁决分片
   provider_runtime_error（reasoning-only）反复出现（failed 计数 6→3→5→6→5
   波动，多次被后续裁决波自动重排恢复），最终 **5 个分片 att=4/4 终态失败**
   （AE/EX/CM/DM/SV 各1，均为显式 failure_code/failure_message，无静默失败），
   经 bounded-gap 吸收后 adjudication complete（remaining=0，system_adjudicated=35，
   confirm 200，monmapdraft_35139cb0f69090b7292715d5bc61 v60 confirmed）；
3. **facts 覆盖率下降（如实记录，交复盘官）**：本轮 facts 物化 10表/591行/
   **2204值**（source_values_verified=2204=100%），显著低于 R14P/R15D 同数据的
   **3038值**——与盲核终态失败数 5（R14P/R15D 各2）相关，bounded-gap 吸收使
   更多字段不进入事实物化。发布结果层结构仍与 R14P 完全一致（15发现/16受试者/
   477风险，overview 序列化字节数相同 597,305），链路门本身按产品规则全绿
   （facts state=ready、物化值100%核验），但**数据覆盖度差异是本轮值得复盘的
   真实事件**；
4. **文档权威本轮走了更长内部复核链**（产品内波次变化）：analysis 双VLM外，
   review 阶段含 adjudication-v8 + critique-v2 + review-v7 双车道各3作业
   （R14P 为 1+1），4+4 全 completed，452s（与R15D约4.8分钟一致）。

### 八阶段计时（秒数=首次真实完成；总活跃驱动 11309.6s，壁钟 19:36:08Z→22:44:07Z 约3h8min，其中映射收敛 3h 占绝对主导）

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.0 | proj_user_655f6a5bbac5，精确名一次成功（在册 MX循R15D-CSU 无同名冲突）；indication/product/modules 合同双核对无误；status=active |
| 2 | 上传 | ✅ | 0.2 | attempt=stg-4f6889391e0a4a37953b7456fc1654bc，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 451.9 | analyze→（身份归属确认1次，自动）→ready=true「研究文件已准备好」；8个AI作业全completed（analysis/review × 主/盲核，review含3波内部复核链） |
| 4 | 映射确认 | ✅ | 10826.4 | 双队列10+10→candidates_ready（60候选）→裁决收敛波（remaining 46→34→28→21→11→0；system_adjudicated 0→12→18→25→35）→13张用户卡全按数据实测决策表作答→adjudicate complete（remaining=0）→confirm 200；收敛3h远慢于R14（92min，盲核串行+失败/恢复循环多轮），仍在4h预算内 |
| 5 | facts | ✅ | 0.1 | state=ready：10表/591行/**2204值** source_values_verified=2204（100%物化值核验；对比R14P/R15D 3038值，见上第3条） |
| 6 | 运行 | ✅ | 30.3 | workspace/bootstrap 200→run-setup/options 200→prepare-and-start 一次200（**碎片化家族未命中**）→run_state=completed，**10/10项100%「已完成」**（progress复核API独立确认percent=100.0+status_overview[{已完成,count:10}]） |
| 7 | 发布 | ✅ | 0.3 | publication POST 200→publication_state=available（progress侧publication_state=available+result_available=true双端点一致） |
| 8 | 结果 | ✅ | 0.4 | result-entry 200；overview 非空（序列化597,305字节/原始载荷778,126字节）；**finding_count=15**（query_findings列表长度与query_findings_meta.total双一致）+current_risks=477；subject_count=16；identity.project_ref=proj_user_655f6a5bbac5 归属核对无误 |

### AI 节点路由核验（台账：隔离实例 runs/tester_loop_iso_20260928/runtime/medical_monitoring_ai.sqlite3 直读；/api/ai/queue 本build仍404）

本项目总量 88 作业（权威8+映射pipeline 20+裁决60），终态 83 completed +
5 terminal failed，**0 queued/running（无滞留）**；5 个 failed（均为盲核裁决
分片）均有显式 failure_code=provider_runtime_error（reasoning-only，R12-R15D
同款已知家族）+ failure_message，无静默失败。调用139次（observed_model 与
requested 全一致，0 mismatch），prompt 1,369,628 + completion 782,501 =
2,152,129 tokens。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis primary-v9 ×1；review：adjudication-primary-v8 + critique-primary-v2 + review-primary-v7 ×3） | 4 | 4 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（analysis verifier-v9 ×1；review：adjudication-verifier-v8 + critique-verifier-v2 + review-verifier-v7 ×3） | 4 | 4 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（pipeline listing-field-mapping-v19 ×10 + adjudication-v19-tools-v7.2 ×30） | 40 | 40 completed | ✅ |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（pipeline mapping-verifier-v8-tools-v6 ×10 + adjudication-verifier-v17-tools-v7.2 ×30） | 40 | 35 completed + 5 failed（AE/EX/CM/DM/SV 各1，att=4/4，reasoning-only 已知家族，bounded-gap吸收） | ✅（失败可见且按设计恢复为可见缺口） |
| 裁决（映射收敛） | 同上两车道（主 cms-router/glm-5.3-flash 30 + 盲核 ollama-cloud/deepseek-v4.1-flash 25c+5f，tools-v7.2） | 60 | 55 completed + 5 failed（终态失败为可见缺口；收敛期另有多轮失败被产品后续裁决波重排恢复） | ✅（adj_state=complete，remaining=0，system_adjudicated=35，confirm 200） |
| 监查分析 | 本build运行lane不经AI台账（本项目 task_type 仅 document_authority_*/listing_field_mapping；FactsModeOutputProvider 事实回执确定性产出，同R10P3-R14P） | 0 | —（无作业=无滞留/无静默失败；15发现+477风险已产出） | ✅（机制核实，如实报0作业） |

### 过程事件（如实）
- 开赛前健康断言：8911 /api/health ok（runtime_store integrity ok，schema v16）、
  /api/runtime-readiness ready:true（build api-2ac4a3a5e6a1db40，与 R13/R14 轮
  同build）、AI网关 /api/ai-gateway/status configured=true（zhipu-coding-plan/
  glm-5.3-flash，route_validation_errors=[]）、实例台账 0 queued/running
  （285c+7f 均为 R15D 及更早轮遗产）；8910/5177/5178 连接拒绝（000，未触碰）；
  synth_csu 三件套在位；在册项目仅 MX循R15D-CSU（R14D/R14P 已被归档），
  精确名 MX循R15P-CSU 无冲突；
- 21:36:08 本地（19:36:08Z）run1（唯一run）启动：精确名建项一次成功；上传
  0.2s；文档权威 451.9s 全绿（自动身份归属确认1次，无文件角色人工裁决）；
  映射双队列 21:43:40 启动，约16分钟 candidates_ready（10主+10盲核全completed，
  60候选）；收敛波 20:00Z→22:44Z 约3h：remaining 46→34→28→21→11→0，
  system_adjudicated 0→12→18→25→35，盲核reasoning-only失败家族反复
  （6→3→5→6→5 多轮恢复/复发循环），13张用户裁决卡（EX.EXFRQ/EX.EXTRT+
  ICF/LB_HEM/MH/UAS 11张既有卡）全按 R5D-R15D 数据实测决策表作答，
  无未知卡、无fail-closed；confirm 200 后 facts/运行/发布/结果 全部秒级~30s级
  完成（22:44:07Z run_start → 22:44:37Z 结果可读）；
- 后续为复盘归档做了API独立复核（非驱动日志自证）：progress端点 run_state=
  completed/percent=100.0/status_overview=[{已完成,count:10}]/publication_state=
  available/result_available=true、publication端点available、result-entry 200/
  overview 独立读取15发现（列表与meta.total双一致）/16受试者/477风险/
  identity归属、source-manifest real_source_slice、runs列表仅1条（无孤儿）
  ——全部一致；
- console /tmp/mm_api_8911.log 全程与赛前基线一致（0字节，uvicorn --log-level
  warning；本轮链路无门禁拒绝、无碎片化拦截，无需 console 取证）；
- 全程未触碰 8910/5177（开始/结束只读复核连接拒绝状态）；未改任何产品代码/
  数据库（驱动脚本、一次性预检项目自身数据、产品恢复路径内的裁决波重排除外）；
  项目 MX循R15P-CSU 与全部留痕原地保留（归档交复盘官；在册另有 R15D 预置项目
  MX循R15D-CSU 仍active）。

---

## R14 第1次（20261003，run=r14p_preflight）——**chainOk = true，第五次全链端到端跑通（run1 新裁决卡 VS·DBP fail-closed→数据实测补答→run2 全绿）**

- 驱动脚本：`scripts/tester_loop_0927/r14p_preflight_csu.py`（由 R13P 全绿驱动
  r13p_preflight_csu.py 机械适配 R14P 命名/幂等键/留痕文件，R5D-R13D 全部既有
  裁决卡决策表原样保留 + 本轮新增 R14P_ROUND1_CARDS（VS·DBP）；幂等，状态
  `r14p_preflight_state.json`，留痕 `r14p_preflight_evidence.jsonl`（292驱动事件），
  运行日志 logs/r14p_preflight_run1.log、run2.log）
- 数据：同 `tester_staging_0927/synth_csu` 三件套（方案V1.3 docx + eCRF指南V1.0 docx + 合成listing V1.0 xlsx）
- 项目：**MX循R14P-CSU**（proj_user_1dcc60966d7f，慢性自发性荨麻疹 / MG-K10 /
  modules 含 medical_monitoring【projects+source-manifest API 双核对；发布后
  medical_monitoring → real_source_slice】，幂等键 r14p-preflight-20261003T145230Z-dc3d9547
  唯一，精确名一次建项成功无需后缀，status=active，**留在原地待复盘归档**）
- 运行：run:3d008a4411571e821b3f675d（run_start_idem=r14p-run-20261003T162924Z-36f1b106，
  prepare-and-start 一次 200，项目 runs 列表仅此1条无孤儿）
- 结果：result-context:3fc045e90b08407588ad337b1674c41b（overview 原始 597,305 字节）

### 结论：chainOk = true（八阶段全ok；运行真完成10/10项100%、发布available、结果可读）

已知状态碎片化家族（readiness 409）**未命中**——本轮 run-setup/options 200、
workspace/bootstrap 200 后 prepare-and-start 一次 200，无 409 窗口；
source-manifest medical_monitoring → **real_source_slice**。

**本轮真实事件（如实，全程未改产品代码/数据库）**：
1. run1 收敛期首波裁决浮现 **1张新未知裁决卡 VS·DBP**（主分析
   diastolic_blood_pressure vs 独立复核 vital_signs_diastolic_blood_pressure，
   不在 R5D-R13D 决策表）→ 驱动按设计 fail-closed 退出（exit 2，5501.4s）。
   工程师 openpyxl 直读 VS 表实测：双行表头（中文列标题'舒张压mmHg' + CDISC
   次行 DBP），64行数据全为60-88 mmHg连续数值，与 SBP/HRRATE/RESP 同表同行
   配对（64条生命体征记录=16受试者×4访视）——两轮结论语义同为舒张压，域已为
   VS（生命体征），角色名无需重复域前缀，按主分析侧采纳 diastolic_blood_pressure
   补入 R14P_ROUND1_CARDS 后 run2 幂等续跑全绿。同 R11D/R12P「首次遇到新卡
   fail-closed→数据实测补答」先例，属设计内人工医学确认门，非缺陷；
2. 收敛期已知失败家族多次复发并全部由产品自身路径消化：CM 主分片 att1
   invalid_ai_output（信封字段族缺失）与 EX/LB_HEM 盲核 reasoning-only 在后续
   裁决波被产品重排恢复（failed→0）；终态仅剩 2 个 EX 裁决分片终态失败（见
   AI节点表），均显式 failure_code 且经 bounded-gap 吸收后 adjudication complete。

### 八阶段计时（秒数=首次真实完成；映射确认为 run1 5501.4s（fail-closed拦截）+run2 12.2s，活跃驱动合计 5513.6s，壁钟 14:56-16:29Z 约93min）

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.0 | proj_user_1dcc60966d7f，精确名一次成功（在册仅 MX循R14D-CSU 无同名冲突）；indication/product/modules 合同双核对无误；status=active |
| 2 | 上传 | ✅ | 0.4 | attempt=stg-c2ae25a5ba4348b38be64d7a38c34523，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 213.6 | analyze→（身份归属确认1次，自动）→ready=true「研究文件已准备好」；4个AI作业全completed（analysis/review × 主/盲核），无文件角色人工裁决 |
| 4 | 映射确认 | ✅ | 5513.6（run1 5501.4+run2 12.2） | 首波46→run1 未知卡VS·DBP fail-closed（exit 2）→openpyxl直读实测补答→run2 adjudicate complete（remaining=0，system_adjudicated=16）→confirm 200（monmapdraft_34bafa5976a8ad45f8153f609d1a，draft v1 confirmed）；共31张卡全按数据实测决策表作答（30既有+1本轮新增） |
| 5 | facts | ✅ | 0.2 | state=ready：10表/591行/3038值 source_values_verified=3038（100%） |
| 6 | 运行 | ✅ | 30.3 | workspace/bootstrap 200→run-setup/options 200→prepare-and-start 一次200（**碎片化家族未命中**）→run_state=completed，**10/10项100%「已完成」**（progress复核API独立确认percent=100.0+status_overview[{已完成,count:10}]） |
| 7 | 发布 | ✅ | 0.3 | publication POST 200→publication_state=available「结果已整理完成」（progress侧publication_state=available双端点一致，result_available=true） |
| 8 | 结果 | ✅ | 0.4 | result-entry 200；overview 原始597,305字节非空；**finding_count=15**（query_findings列表长度与query_findings_meta.total双一致）+current_risks=477；subject_count=16；identity.project_ref=proj_user_1dcc60966d7f 归属核对无误 |

### AI 节点路由核验（台账：隔离实例 runs/tester_loop_iso_20260928/runtime/medical_monitoring_ai.sqlite3 直读；/api/ai/queue 本build仍404）

本项目总量 44 作业（权威4+映射pipeline 20+裁决20），终态 42 completed +
2 terminal failed，**0 queued/running（无滞留）**；2 个 failed（均为 EX 域
裁决分片）均有显式 failure_code/failure_message（无静默失败）：主分片
invalid_ai_output att=2/3（att1 信封字段族缺失→att2 内容级拒绝「treatment/dose
semantics source support unresolved; the system will not substitute another
role」，R10-2 内容级家族表现）；盲核分片 provider_reasoning_only att=4/4
（R12/R13 同款已知家族）。两者经 bounded-gap 吸收后 adjudication complete
（remaining=0）。调用84次（observed_model 与 requested 全一致），prompt
1,165,854 + completion 598,210 = 1,764,064 tokens。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis primary-v9、review primary-v7 各1） | 2 | 2 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（analysis verifier-v9、review verifier-v7 各1） | 2 | 2 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（pipeline listing-field-mapping-v19 ×10 + adjudication-v19-tools-v7.2） | 19 | 18 completed + 1 failed（EX裁决主分片 att=2/3，内容级语义拒绝，bounded-gap吸收） | ✅（失败可见且按设计恢复为可见缺口） |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（pipeline mapping-verifier-v8-tools-v6 ×10 + adjudication-verifier-v17-tools-v7.2） | 19 | 18 completed + 1 failed（EX裁决盲核 reasoning-only att=4/4，同R13已知家族，bounded-gap吸收） | ✅（同上） |
| 裁决（映射收敛） | 同上两车道（主 cms-router/glm-5.3-flash + 盲核 ollama-cloud/deepseek-v4.1-flash，tools-v7.2） | 20 | 18 completed + 2 failed（EX域双侧分片终态失败为可见缺口；收敛期另3次已知家族失败被产品后续裁决波重排恢复） | ✅（adj_state=complete，remaining=0，system_adjudicated=16，confirm 200） |
| 监查分析 | 本build运行lane不经AI台账（本项目 task_type 仅 document_authority_*/listing_field_mapping；FactsModeOutputProvider 事实回执确定性产出，同R10P3/R11P2/R12P/R13P） | 0 | —（无作业=无滞留/无静默失败；15发现+477风险已产出） | ✅（机制核实，如实报0作业） |

### 过程事件（如实）
- 开赛前健康断言：8911 /api/health ok（runtime_store integrity ok，schema v16）、
  /api/runtime-readiness ready:true（build api-2ac4a3a5e6a1db40，与 R13 轮同build）、
  AI网关 /api/ai-gateway/status configured=true（zhipu-coding-plan/glm-5.3-flash，
  route_validation_errors=[]）、实例台账 0 queued/running（48 completed 均为 R14D
  种子轮遗产）；8910/5177/5178 连接拒绝（000，未触碰）；synth_csu 三件套在位；
  在册项目仅 MX循R14D-CSU（R13D/R13P 已被归档），精确名无冲突；
- 14:52:30Z run1 启动：精确名建项一次成功；上传/文档权威 213.6s 全绿；映射双队列
  14:56Z 启动（主侧并发2+盲核），候选生成约28分钟后进入裁决收敛波；收敛期先后
  观察 CM主 att1 invalid_ai_output（信封缺失）、EX/LB_HEM盲核 reasoning-only 等
  已知家族失败，随后续裁决波产品重排全部恢复（failed 计数归零）；16:27Z 首波
  裁决 remaining=30 时浮现新卡 VS·DBP → 驱动 fail-closed（exit 2，5501.4s），
  unknown_questions_fail_closed 证据留痕；
- openpyxl 直读 VS 表实测（列值60-88 mmHg×64、双行表头 CDISC 缩写 DBP、与
  SBP/HRRATE/RESP 同行配对）后补 R14P_ROUND1_CARDS 入驱动；16:29:24Z run2 幂等
  续跑：建项/上传/文档权威秒级复用→VS·DBP按实测作答→adjudicate complete
  （remaining=0，system_adjudicated=16）→confirm 200（4.6s量级）→facts 201→
  bootstrap/prepare 200→运行30.3s 10/10 completed→发布available→结果可读，
  八阶段全绿（exit 0，16:29:55Z）；
- 后续为复盘归档做了API独立复核（非驱动日志自证）：progress端点 run_state=
  completed/percent=100.0/status_overview=[{已完成,count:10}]/publication_state=
  available/result_available=true、publication端点available、result-entry 200/
  overview 597,305字节/15发现（列表与meta.total双一致）/16受试者/477风险/
  identity归属、source-manifest real_source_slice、runs列表仅1条（无孤儿）
  ——全部一致；
- console /tmp/mm_api_8911.log 全程与赛前基线一致（523字节fastapi警告，无新增；
  uvicorn --log-level warning，同前几轮现象；本轮链路无门禁拒绝，无需 console 取证）；
- 全程未触碰 8910/5177（开始/结束只读复核连接拒绝状态）；未改任何产品代码/
  数据库（驱动脚本、一次性预检项目自身数据、产品恢复路径内的裁决波重排除外——
  本轮连API级人工恢复重放都无需，仅新卡补答属医学确认门作答）；项目与全部留痕
  原地保留（归档交复盘官）。

---

## R13 第1次（20261003，run=r13p_preflight）——**chainOk = true，第四次全链端到端跑通（含一次首遍EX主分片失败→产品自恢复路径重放后通过）**

- 驱动脚本：`scripts/tester_loop_0927/r13p_preflight_csu.py`（由 R12P 全绿驱动
  r12p_preflight_csu.py 机械适配 R13P 命名/幂等键/留痕文件，R5D-R12D 全部既有
  裁决卡决策表原样保留；幂等，状态 `r13p_preflight_state.json`，留痕
  `r13p_preflight_evidence.jsonl`（292驱动事件+2条人工恢复补录），运行日志
  logs/r13p_preflight_run1.log、run2.log）
- 数据：同 `tester_staging_0927/synth_csu` 三件套（方案V1.3 docx + eCRF指南V1.0 docx + 合成listing V1.0 xlsx）
- 项目：**MX循R13P-CSU**（proj_user_f26b043b3337，慢性自发性荨麻疹 / MG-K10 /
  modules 含 medical_monitoring【projects+source-manifest API 双核对；发布后
  medical_monitoring → real_source_slice】，幂等键 r13p-preflight-20261003T083512Z-c3990522
  唯一，精确名一次建项成功无需后缀，status=active，**留在原地待复盘归档**）
- 运行：run:32c4bd34ee2277473f30d2b4（run_start_idem=r13p-run-20261003T101637Z-5c4c9945，
  prepare-and-start 一次 200（55ms）无孤儿预约，项目 runs 列表仅此1条）
- 结果：result-context:93fba13007ce4d36947e6436ff7d75b0（overview 原始 778,126 字节）

### 结论：chainOk = true（八阶段全ok；运行真完成10/10项100%、发布available、结果可读）

已知状态碎片化家族（readiness 409）**未命中**——本轮 prepare-and-start 一次 200
（55ms），workspace/bootstrap 200 后首发即成功；source-manifest medical_monitoring →
**real_source_slice**。R13D 界内换绑的主侧AI直连路由（cms-router 身份串不变，
base_url 智谱官方直连）本轮承载全链无 503 窗口。

**本轮真实事件（如实，非缺陷修复——全程未改产品代码/数据库）**：run1 映射首遍
EX 主分片 attempt 1/2 终态 invalid_ai_output（provider 输出缺 schema_version/
task_id/task_type 等整个信封字段族，经一次受控修复仍无效）→ 主侧 9/10 →
state=needs_attention → adopt 422 mapping_draft_invalid（EX 域主命名空间零候选，
域完整性门拒绝，R10-2 同家族不同表现：彼时为「definitive approval language」）。
预检工程师按产品自身恢复路径（R10-2 先例：`mapping_pipeline.py`
_recover_failed_submission_jobs requeue-once）人工重放**重入候选生成**：EX 主分片
attempt 2/2 completed → 10/10 → candidates_ready → run2 adopt 201 通过。
与 R10-2 的差异：彼时恢复预算尽（att=2/3 + requeue 已用）链路拦截，本轮
requeue-once 成功——同一模型输出质量波动家族，恢复路径本轮有效。两轮结论合并看：
该家族是否拦截取决于失败发生在首遍（有重排预算则可自愈）还是恢复预算耗尽后。

### 八阶段计时（秒数=首次真实完成；映射确认为 run1 702s（拦截）+恢复窗口+run2 4174.6s，活跃驱动合计 4876.6s，壁钟 08:40-10:16Z 含恢复间隙）

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.0 | proj_user_f26b043b3337，精确名一次成功（R13D 在册名为 MX循R13D-CSU，无同名冲突）；indication/product/modules 合同双核对无误；status=active |
| 2 | 上传 | ✅ | 0.2 | attempt=stg-7fc7a549a1ec415fac8958cbbbfc85ef，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 304.1 | analyze→（身份归属确认1次，自动）→ready=true「研究文件已准备好」；4个AI作业全completed（analysis/review × 主/盲核），无文件角色人工裁决 |
| 4 | 映射确认 | ✅ | 4876.6（run1 702+run2 4174.6；壁钟约96min） | 首遍主侧EX attempt1 invalid_ai_output→adopt 422拦截（run1 exit 2）→重入候选生成（requeue-once）EX attempt2 completed→10/10主+10/10盲核→60候选→adopt 201（monmapdraft_d2cdd15e8b49be28ee4215ba269c）→裁决波46→28(sys 17)→1→0（既有决策表作答，本轮**零未知卡**，无fail-closed退出）→confirm 200（draft v76 confirmed，user_questions=0） |
| 5 | facts | ✅ | 0.2 | state=ready：10表/591行/3422值 source_values_verified=3422（100%） |
| 6 | 运行 | ✅ | 30.3 | workspace/bootstrap 200→run-setup/options 200（snapshot:edb…）→prepare-and-start 200（55ms一次成功，**碎片化家族未命中**）→run_state=completed，**10/10项100%「已完成」×10**（progress复核API独立确认percent=100.0） |
| 7 | 发布 | ✅ | 0.3 | publication POST 200→publication_state=available「结果已整理完成」（progress侧publication_state=available双端点一致，result_available=true） |
| 8 | 结果 | ✅ | 0.4 | result-entry 200；overview 原始778,126字节非空；**finding_count=15**（query_findings列表长度与query_findings_meta.total双一致）+current_risks=477；subject_count=16；identity.project_ref=proj_user_f26b043b3337 归属核对无误 |

### AI 节点路由核验（台账：medical_monitoring_ai.sqlite3 直读；/api/ai/queue 本build仍404）

本项目总量 46 作业（权威4+映射首遍20+裁决主11+裁决盲核11），终态 45 completed +
1 terminal failed，**0 queued/running（无滞留）**；唯一 failed（裁决盲核分片）有显式
failure_code=provider_runtime_error/failure_message=「AI provider returned only
reasoning tokens with no final answer channel; reasoning is not accepted as medical
content (failure_code=provider_reasoning_only)」、attempt=4/4（无静默失败），经
bounded-gap 吸收后 adjudication complete。调用71次，prompt 960,998 +
completion 504,586 tokens。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis primary-v9、review primary-v7 各1） | 2 | 2 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（analysis verifier-v9、review verifier-v7 各1） | 2 | 2 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（listing-field-mapping-v19） | 10 | 10 completed（EX attempt1 invalid_ai_output→requeue-once→attempt2 completed；输出缺信封字段族，与R10-2同家族首遍失败，本轮恢复预算内自愈） | ✅ |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（mapping-verifier-v8-tools-v6） | 10 | 10 completed | ✅ |
| 裁决（映射收敛） | 主 cms-router/glm-5.3-flash（adjudication-v19-tools-v7.2）11：11 completed；盲核 ollama-cloud/deepseek-v4.1-flash（adjudication-verifier-v17-tools-v7.2）11：10 completed+1 failed | 22 | 21 completed + 1 terminal failed（reasoning-only att=4/4，bounded-gap吸收，adjudication complete；同R12已知家族复发一次） | ✅（失败可见且按设计恢复为可见缺口） |
| 监查分析 | 本build运行lane不经AI台账（实例全库 task_type 仅 document_authority_*/listing_field_mapping 双核对；FactsModeOutputProvider 事实回执确定性产出，同R10P3/R11P2/R12P） | 0 | —（无作业=无滞留/无静默失败；15发现+477风险已产出） | ✅（机制核实，如实报0作业） |

### 过程事件（如实）
- 开赛前健康断言：8911 runtime-readiness ready:true（build api-2ac4a3a5e6a1db40，
  R13 重建隔离运行时后的新build）、AI网关 status configured+
  route_validation_errors=[]、实例台账 0 queued/running（47 completed+1 failed
  均为 R13D 种子轮遗产，唯一 failed 为其裁决盲核 EX reasoning-only 已知家族）；
  8910/5177/5178 连接拒绝（000，未触碰）；
- 20261003T08:35:12Z（本地16:35）run1 启动：精确名建项一次成功；上传/文档权威
  304.1s全绿；映射双队列08:40启动，08:51 needs_attention（主5/10，UAS/VS仍在跑）
  → adopt 422 mapping_draft_invalid，驱动 fail-closed（exit 2，702s）；
- 08:52-09:05Z 队列独立排干（UAS/VS completed→主9/10）；台账取证：EX主分片
  attempt 1/2 invalid_ai_output（输出缺 schema_version/task_id/task_type 等
  信封字段族，att=1/2 未触顶）；工程师按产品恢复路径人工重放重入候选生成
  （POST mapping-candidates，R10-2 同款 manual_recovery 先例）→ EX requeue-once
  attempt 2/2 completed → 09:05Z candidates_ready（主10/10+盲核10/10，60候选）；
  2条 manual_recovery_* 证据已补写 r13p_preflight_evidence.jsonl；
- 09:07:00Z run2 幂等续跑：建项/上传/文档权威秒级复用，adopt 201→裁决波收敛
  46→28(sys 17)→1→0（既有决策表作答，**本轮零未知卡**，与 R12P 的3张EX卡
  fail-closed 不同——R12P_ROUND1_CARDS 已入表）→confirm 200（draft v76，
  4.6s）→facts 201→bootstrap/prepare 200（55ms）→运行30.3s 10/10 completed
  →发布available→结果可读，八阶段全绿（exit 0，10:17:08Z）；
- 后续为复盘归档做了API独立复核（非驱动日志自证）：progress端点10/10项
  percent=100.0+已完成×10、publication端点available、result-entry 200/
  overview 778,126字节/15发现（列表与meta.total双一致）/16受试者/477风险/
  identity归属、source-manifest real_source_slice、runs列表仅1条（无孤儿）
  ——全部一致；
- console /tmp/mm_api_8911.log 全程 0 字节（uvicorn --log-level warning，与前几轮
  同现象；本轮链路无门禁拒绝，无需 console 取证）；
- 全程未触碰 8910/5177（开始/结束只读复核连接拒绝状态）；未改任何产品代码/
  数据库（驱动脚本、一次性预检项目自身数据、产品恢复路径API重放与证据补录除外）；
  项目与全部留痕原地保留（归档交复盘官）。

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

## R11 第2次（20261001-02，run=r11p2_preflight）——**chainOk = true，第二次全链端到端跑通**

- 前提：R11第1次拦截根因（对账门把 domain_gaps 豁免域的对侧映射判 unexpected 硬
  violation）已由修复员修复——`packages/medical_monitoring/admission/mapping_reconciliation.py`
  :346-353 域缺席豁免（「R11预检：域缺席豁免（allowed_missing_domains）」注释在位），
  `mapping_confirmation.py:1604-1632` 把 gap_domains 传入对账；文件 mtime 20261001
  18:14、8911 进程 18:18 重启（pid 60895）实测确认。**注意：build id 仍为
  api-807dff49e5ad28ec**（与R11第1次相同）——build 指纹只覆盖 services/api/app
  （runtime_contract.json build_fingerprint.backend_source_root），packages/ 树不在
  指纹内，同 id 不代表同码。
- 驱动脚本：`scripts/tester_loop_0927/r11p2_preflight_csu.py`（R11第1次驱动的复本，
  运行标签/幂等键前缀 r11p2-/状态 `r11p2_preflight_state.json`/留痕
  `r11p2_preflight_evidence.jsonl`/日志 logs/r11p2_preflight_run1..run3.log 独立）
- 数据：同 `tester_staging_0927/synth_csu` 三件套
- 项目：**MX循R11P-CSU-2**（proj_user_ff6b552f8eef，慢性自发性荨麻疹 / MG-K10 /
  modules 含 medical_monitoring，幂等键 r11p2-preflight-20261001T104209Z-5fe4c2d2
  唯一）。**名称偏离说明**：精确名「MX循R11P-CSU」被R11第1次项目（proj_user_
  d029b0208f85，按指令留在原地）409 占用，按 API 报错自指引加 -2 后缀，P=预检
  语义不变。**留在原地待复盘归档**。
- 运行：run:80d35162c4c39abbe6549016（daily/full，snapshot:d1feca1f066258c1e21ab699）
- 结果：result-context:c9c8881a5d6545009a265d804b247a6e（overview 原始 778,126 字节）

### 结论：chainOk = true（八阶段全ok；运行真完成10/10、发布available、结果可读）

已知状态碎片化家族（readiness 409）**未命中**——本轮 prepare-and-start 一次 200，
R10第1次的 runtime 路径修复持续有效；R11第1次的修复（对账域缺席豁免）在库但
**未被行使**：本轮首遍映射双队列 20/20 全 completed（R11第1次的 AE 主分片
invalid_ai_output 未复发，印证该失败属模型输出质量波动而非确定性缺陷）、60/60
候选无 domain_gaps，走的是干净路径。

### 八阶段计时（秒数=首次真实完成；映射确认为三段活跃驱动窗口合计）

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.2 | 精确名409（R11第1次占名）→按API指引-2后缀；indication/product/modules 合同核对无误 |
| 2 | 上传 | ✅ | 0.4 | attempt=stg-88d7d5c3501f41afb1abfbcab5c1be15，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 434.5 | analyze→（身份归属确认1次，自动）→ready=true「研究文件已准备好」；8个AI作业全completed，无人工角色裁决 |
| 4 | 映射确认 | ✅ | 16342（run1 1952+run2 11304+run3 3085.9；壁钟28.6h含两次驱动被杀的24h空窗） | 首遍双队列20/20（主10/10无AE失败）→60候选→adopt 201（monmapdraft_e65f6ca44633c50e56169462dd82）→裁决多波收敛 remaining 46→41→31→26→0、system_adjudicated=46、**零用户问题卡**（本轮全系统裁决，R3-01 家族卡未浮现）→confirm 200（draft v47 confirmed）；11个裁决代际作业 provider_runtime_error（reasoning-only，att=4终态）被 bounded-gap 吸收，链路继续 |
| 5 | facts | ✅ | 0.1 | state=ready：10表/591行/914值 source_values_verified=914（100%）。注：values 计数与 R10第3次的 2974 不同（计数口径/物化差异，state=ready 契约满足，未深究） |
| 6 | 运行 | ✅ | 30.3 | workspace/bootstrap 200（既定步骤）→prepare-and-start 200（幂等键 r11p2-run-20261002T152442Z-9d915375，一次成功无孤儿）→run_state=completed，10/10项100%「本次医学监查已完成」，result_available=true（完成后复核） |
| 7 | 发布 | ✅ | 0.3 | publication POST 200→publication_state=available「结果已整理完成」 |
| 8 | 结果 | ✅ | 0.3 | result-entry 200；overview 原始778,126字节非空（驱动侧重序列化597,305）；finding_count=15（query_findings，meta.state=completed_with_findings）+current_risks=477；subject_count=16；identity.project_ref=proj_user_ff6b552f8eef 归属核对无误 |

### AI 节点路由核验（台账：module `/ai/jobs` + sqlite 直读双核对；`/api/ai/queue` 本build仍404）

本项目 92 作业（190 次调用，prompt 1,682,936 + completion 907,612 tokens），
终态 81 completed + 11 failed，**0 queued/running（无滞留）**；11 个 failed 全部
裁决代际、显式 failure_code=provider_runtime_error（reasoning-only，att=4 终态），
无静默失败，经 bounded-gap 吸收后 adjudication remaining=0。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis primary-v9、review primary-v7、adjudication primary-v8、critique primary-v2 各1） | 4 | 4 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（同上四族 verifier） | 4 | 4 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（listing-field-mapping-v19） | 10 | 10 completed（R11第1次 AE invalid_ai_output 未复发） | ✅ |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（mapping-verifier-v8-tools-v6） | 10 | 10 completed | ✅ |
| 裁决（映射收敛） | 主 cms-router/glm-5.3-flash（adjudication-v19-tools-v7.2）32：26 completed+6 failed；盲核 ollama-cloud/deepseek-v4.1-flash（adjudication-verifier-v17-tools-v7.2）32：27 completed+5 failed | 64 | 53 completed + 11 terminal failed（全部 reasoning-only att=4，bounded-gap吸收，收敛 remaining=0/sys=46） | ✅（失败可见且按设计恢复为可见缺口） |
| 监查分析 | 本build运行lane不经AI台账（实例全库 task_type 仅 document_authority_*/listing_field_mapping；FactsModeOutputProvider 事实回执确定性产出，同R10第3次发现3） | 0 | —（无作业=无滞留/无静默失败；15发现+477风险已产出） | ✅（机制核实，如实报0作业） |

### 过程事件（如实）

- 20261001 18:42 run1 启动：建项（-2后缀）/上传/文档权威434.5s全绿；18:49-19:42
  映射首遍+adopt 201+裁决前两波；**19:42 驱动进程被宿主会话清理误杀**（轮询命令
  取消时连带进程组，留痕 run1.conv 2160s 截止）；
- 21:23 run2 幂等续跑（建项/上传/文档权威秒级复用）：裁决波 46→41→31；
  **00:32（20261002）驱动再次被同样方式误杀**（run2.conv 11334s 截止）；两次误杀
  均为宿主侧进程管理问题，非产品缺陷；后端 AI 队列独立于驱动轮询继续排干
  （76C/4F 定格）；
- 20261002 22:33 run3 续跑（改用宿主持有的后台任务方式防误杀）：15:23:27Z 一次
  adjudicate 500（mapping_bridge_failed「生成字段对应建议时出现问题」，一次即恢复，
  下一 tick 即 complete/remaining=0）→15:24:41 confirm 200→facts 201→
  bootstrap/prepare 200→运行30.3s completed→发布available→结果可读，八阶段全绿；
- console `/tmp/mm_api_8911.log` 全程 0 字节（uvicorn --log-level warning，与前几轮
  同现象；本轮无门禁拒绝，无需 console 取证）；
- 全程未触碰 8910/5177；未改任何产品代码/数据库（驱动脚本与一次性预检项目自身
  数据除外）；项目与全部留痕原地保留（归档交复盘官）。

---

## R11 第1次（20261001，run=r11p_preflight）

- 驱动脚本：`scripts/tester_loop_0927/r11p_preflight_csu.py`（继承 R10P 第3次全绿驱动
  r10p_preflight3_csu.py 并补 R11D 轮新裁决卡；幂等，状态
  `r11p_preflight_state.json`，留痕 `r11p_preflight_evidence.jsonl`，
  运行日志 logs/r11p_preflight_run1.log、run2.log）
- 数据：`tester_staging_0927/synth_csu` 三件套（方案V1.3 docx + eCRF指南V1.0 docx +
  合成listing V1.0 xlsx）
- 项目：**MX循R11P-CSU**（proj_user_d029b0208f85，慢性自发性荨麻疹 / MG-K10 /
  modules 含 medical_monitoring【source-manifest API 核对无误】，幂等键
  r11p-preflight-20261001T091433Z-9af7eeec 唯一，精确名一次建项成功无需后缀，
  status=active，**留在原地待复盘归档**）
- 环境：8911 ready（build api-807dff49e5ad28ec），AI 网关
  zhipu-coding-plan/glm-5.3-flash，隔离 runtime=runs/tester_loop_iso_20260928
  （进程 env WORKBENCH_RUNTIME_DIR 实测确认，pid 27561）

### 结论：chainOk = false

**blockedAt = 映射确认（阶段4，裁决/确认永久 blocked）**——本轮**未到达运行启动**，
已知状态碎片化家族（readiness 409）未被测试。拦截机理（代码级+数据级定位）：

1. **AE 主分片终态失败**：`listing-field-mapping:stg-0d8b…:AE:0001-of-0001`
   （cms-router/glm-5.3-flash）invalid_ai_output（「provider output contains
   definitive approval language」）**连续 14 次**（首跑1次+重排恢复+adjudicate轮询
   期间R5冲刺重排循环）。对照：台账历史同三份文件的 AE 主分片 22 个全部 attempt-1
   完成——本 Attempt 冻结输入在当前模型态下确定性产出非法输出；
2. **R10P第2次修复（allowed_missing_domains）在 adopt 门首次端到端生效**：
   adopt 201（run1 的 422 是轮询提前触发——needs_attention 在队列仍在跑时即出现，
   队列排干+重排恢复耗尽后 run2 adopt 成功），draft monmapdraft_0d3bed9fecaa34b4
   98ac2e708c8e v1，51/60 字段，domain_gaps=[AE]，链路如修复注释所言「继续」了
   **一步**；
3. **但下一道门（双队列确定性对账）把修复意图反噬**：修复注释明言「盲核侧若有
   该域结果仍参与复核」，而 `mapping_reconciliation.py:353-356 _index_cohort` 把
   不在 draft profile 里的映射判为硬 violation——盲核侧 AE 分片恰好 completed
   （10/10），其 9 个 AE 字段全部落在 51 字段 draft profile 之外 →
   hard_violations>0 → reconciliation state=**blocked**（:598-600）→
   `mapping_confirmation.py:732-738` adjudication 恒 blocked（无 failure_code、
   remaining=0、无问题卡可答）；bounded-gap 通道不可达——它只覆盖 adjudication
   代际作业的失败分片（:927-945），本 block 发生在其上游的确定性对账，无任何
   可重试对象；
4. **confirm 不可达**：`confirm_draft`（mapping_confirmation.py:1806-1814）要求
   reconciliation auto_pass 或 diverged 态的 durable resolutions；blocked 两者
   皆非 → mapping_reconciliation_required；
5. **无自愈路径**：即使 AE 主分片最终成功（14次未成），既有 draft 的 51 字段
   profile 与双侧 cohort 的 60 字段映射不对称依旧 → 换成 primary 侧 9 个域外
   字段 → 仍 blocked；重采纳被 source-set 冲突拒绝
   （monitoring_mapping_draft_repository.py:1150-1163「mapping draft source set
   changed; create a new batch/profile」）→ 本 Attempt 死锁，无恢复路径。

**缺陷定性**：R10P第2次修复只打通了 adopt 门，与紧随其后的确定性对账门直接矛盾
（同一修复的注释承诺与对账门的硬 violation 判定不相容）——该修复此前从未被
端到端验证过（R10P3 全 20 作业 completed 未走到此分支；修复员当时只原地验证了
adopt 通过）。**单主命名空间分片终态失败 = 映射 lane 死锁**这一 R10P2 结论在
修复后依然成立，只是死点从 adopt 422 后移到了对账 blocked。

console 侧：`/tmp/mm_api_8911.log` 全程 0 字节（uvicorn --log-level warning）——
block 只在 HTTP/台账层可见（与前几轮同现象）。

### 八阶段计时

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.1 | proj_user_d029b0208f85，精确名一次成功；indication/product/modules 合同经 source-manifest 核对无误 |
| 2 | 上传 | ✅ | 0.4 | attempt=stg-0d8b4989793b4ebd811ba37b7f7962d2，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 724 | analyze→（身份归属确认1次，自动）→ready=true「研究文件已准备好」；8个AI作业全completed，无人工角色裁决 |
| 4 | 映射确认 | ❌ | 2447（含恢复窗口） | run1 381s：needs_attention 出现时队列仍在跑（primary 1/10），adopt 422 mapping_draft_invalid 属轮询提前；队列排干后按产品 requeue-once 重入候选生成，AE 第2次同样终态失败（attempt=2、预算尽）；run2：adopt 201（51/60字段+domain_gaps=[AE]，allowed_missing_domains 首次端到端生效）→ adjudicate 恒 blocked（remaining=0、无 failure_code、无问题卡）→ 对账门硬 violation 死锁（见结论5条），498s 时以确定性证明停止驱动。adjudication/confirm 无恢复路径 |
| 5 | facts | ❌ | — | 未到达（无 confirmed draft） |
| 6 | 运行 | ❌ | — | 未到达（碎片化门本轮未被测试） |
| 7 | 发布 | ❌ | — | 未到达 |
| 8 | 结果 | ❌ | — | 未到达 |

### AI 节点路由核验（台账：medical_monitoring_ai.sqlite3 直读；/api/ai/queue 仍404）

本项目总量 28 作业（57 次调用，prompt 1,268,732 + completion 444,141 tokens），
终态 23 completed + 4 completed(经1次重排) + 1 terminal failed；**0 queued/
running（驱动停止后 ≥5 分钟无新重排——重排由 adjudicate/reconcile 轮询路径触发，
无人轮询即停）**；唯一 failed（AE主分片）有显式 failure_code/failure_message/
attempt=14（无静默失败），是本轮拦截点本身。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis primary-v9、review primary-v7、adjudication primary-v8、critique primary-v2 各1） | 4 | 4 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（同上四族 verifier） | 4 | 4 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（listing-field-mapping-v19） | 10 | 9 completed + 1 terminal failed（AE 分片 invalid_ai_output×14） | ❌（该失败即拦截点） |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（mapping-verifier-v8-tools-v6） | 10 | 10 completed（CM 经1次重排） | ✅（其 AE 结果正是对账门硬 violation 的来源） |
| 裁决（映射收敛） | 未派发（reconciliation 在 adjudication 代际创建之前即 blocked，无作业无路由可报） | 0 | — | ❌ 被阶段4拦截 |
| 监查分析 | 未派发（运行未启动） | 0 | — | ❌ 被阶段4拦截 |

### 过程事件（如实）
- 17:14:33（本地）run1 启动：建项/上传全绿；文档权威 724s ready；映射双队列启动；
  17:32:54 state=needs_attention（primary 1/10 时 AE 首败）→ adopt 422（轮询提前，
  队列仍在跑）→ 驱动 fail-closed 退出（exit 2，381s）；
- 17:41-17:53 被动等待队列排干（primary 9/10、verifier 10/10、候选 51）；期间读码
  确认产品恢复路径（mapping_pipeline.py:1416 requeue-once）；
- 17:54 按产品路径重入候选生成一次（POST mapping-candidates 201，留痕
  manual_recovery_reenter_candidates）：AE 重排后第2次同样终态失败（attempt=2、
  预算尽）→ needs_attention 定格；
- 17:58 run2 幂等续跑：adopt 201（allowed_missing_domains 首次端到端生效，
  domain_gaps=[AE] 物化）→ 收敛循环 11 轮 adjudicate 恒 blocked；18:0x 直读台账
  （AE attempt 爬升至 12）+ 代码级定位对账门死锁（5条证据链）后，18:06 主动停止
  驱动（继续循环只会重排 AE 燃烧预算，判定已确定性）；驱动停止后 AE 又执行 2 次
  （12→14）后无新重排；
- 全程未触碰 8910/5177；未改任何产品代码/数据库（驱动脚本与一次性预检项目自身
  数据除外）；项目与全部留痕原地保留（归档交复盘官）。

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

---

## R12 第1次（20261002-03，run=r12p_preflight）——**chainOk = true，第三次全链端到端跑通（R12轮主侧AI直连路由下首跑）**

- 驱动脚本：`scripts/tester_loop_0927/r12p_preflight_csu.py`（由 R11P2 全绿驱动
  r11p2_preflight_csu.py 机械适配 R12P 命名/幂等键/留痕文件，并并入 R12D 轮实测的
  R12_ROUND4_CARDS；本轮收敛期新浮现3张EX卡 fail-closed 后按 openpyxl 直读实测
  补答 R12P_ROUND1_CARDS——依据注释在位；幂等，状态 `r12p_preflight_state.json`，
  留痕 `r12p_preflight_evidence.jsonl`（329事件），运行日志 logs/r12p_preflight_run1.log、
  run2.log）
- 数据：同 `tester_staging_0927/synth_csu` 三件套（方案V1.3 docx + eCRF指南V1.0 docx + 合成listing V1.0 xlsx）
- 项目：**MX循R12P-CSU**（proj_user_21672090ff4a，慢性自发性荨麻疹 / MG-K10 /
  modules 含 medical_monitoring【source-manifest API 核对：medical_monitoring →
  real_source_slice】，幂等键 r12p-preflight-20261002T201545Z-916f5d4c 唯一，
  精确名一次建项成功无需后缀，status=active，**留在原地待复盘归档**）
- 运行：run:469f4c6dd1f628134fcca021（run_start_idem=r12p-run-20261002T223035Z-4718a3ff，
  一次 prepare-and-start 200 首跑即完成，无孤儿预约，项目 runs 列表仅此1条）
- 结果：result-context:803bfa537de54de（overview 原始 597,305 字节）

### 结论：chainOk = true（八阶段全ok；运行真完成10/10项100%、发布available、结果可读）

已知状态碎片化家族（readiness 409）**未命中**——本轮 prepare-and-start 一次 200（60ms），
workspace/bootstrap 200 后首发即成功；source-manifest medical_monitoring →
**real_source_slice**（建项起即非 intake_pending，R10第1次的 runtime 路径修复持续有效）。
R11P2 的对账域缺席豁免本轮**未被行使**（首遍映射双队列 20/20 全 completed、60候选无
domain_gaps，走干净路径）。R12D 界内修复的主侧AI直连路由（cms-router 身份串不变，
base_url 由坏 LB 改智谱官方直连）首次承载全链：**主侧31作业（权威2+映射首遍10+
裁决19）全completed零失败**；本轮全链仅1个AI终态失败（裁决盲核CM分片 reasoning-only，
att=4，经bounded-gap按设计吸收，见下表），无503窗口——R11-01（infra错误按文件
指纹缓存为终态结论）家族未复发：文档权威一次通过，无任何「复用已有结论」拒绝，
该修复路径本轮未被触发（如实：修复在build内但未被行使）。

### 八阶段计时（秒数=首次真实完成；映射确认为两段活跃驱动窗口合计，中间 fail-closed 间隙约4.5分钟不计入）

| # | 阶段 | ok | 秒 | 备注 |
|---|---|---|---|---|
| 1 | 建项 | ✅ | 0.0 | proj_user_21672090ff4a，精确名一次成功（R12D 在册名为 MX循R12D-CSU，无同名冲突）；indication/product/modules 合同经 source-manifest+projects API 双核对无误 |
| 2 | 上传 | ✅ | 0.3 | attempt=stg-f372f54041ac41398af7bdfecf461917，1文件/10表/591行 |
| 3 | 文档权威 | ✅ | 325.1 | analyze→（身份归属确认1次，自动）→ready=true「研究文件已准备好」；4个AI作业全completed（analysis/review × 主/盲核），无文件角色人工裁决 |
| 4 | 映射确认 | ✅ | 7477.9（run1 7440+run2 37.9；壁钟2h09m） | 首遍双队列20/20（主10/10+盲核10/10，无R10P2/R11P1的invalid_ai_output首遍失败）→60候选→adopt 201（monmapdraft_db98ebd2d0886dff4f368ba76d22）→裁决波收敛46→40(6sys)→27(19sys)→浮出3张未知EX卡 fail-closed（run1，第25+3张卡：25张既有决策表按实测作答+3张未知）→实测补答后续跑run2：3卡作答→adjudicate一次即complete/remaining=0/sys=19→confirm 200（draft v74 confirmed，user_questions=0） |
| 5 | facts | ✅ | 0.2 | state=ready：10表/591行/3346值 source_values_verified=3346（100%） |
| 6 | 运行 | ✅ | 30.3 | workspace/bootstrap 200→run-setup/options 200（snapshot:76af01be1ced01d276270a7c「10表/591行/3346值100%往返校验」）→prepare-and-start 200（幂等键 r12p-run-20261002T223035Z-4718a3ff，一次成功无孤儿）→run_state=completed，**10/10项100%「本次医学监查已完成」**（status_overview=已完成×10，percent=100.0，progress复核API独立确认） |
| 7 | 发布 | ✅ | 0.3 | publication POST 200→publication_state=available「结果已整理完成」（progress侧publication_state=available双端点一致） |
| 8 | 结果 | ✅ | 0.4 | result-entry 200；overview 原始597,305字节非空；**finding_count=15**（query_findings，projection.query_findings_meta.total）+current_risks=477；subject_count=16；identity.project_ref=proj_user_21672090ff4a 归属核对无误；data_cutoff=2026-08-19 |

### 本轮新浮现的3张EX裁决卡（R12P_ROUND1_CARDS，fail-closed→实测作答→续跑）

收敛期（run1，7440s）第4波浮出3张未知卡 fail-closed 退出（unknown_questions_fail_closed
留痕）。openpyxl 直读 EX 表实测（128行=16名受试者×8次给药）后作答复跑：

| 卡 | 表现 | 实测依据 | 作答 |
|---|---|---|---|
| EX·EXDAT | 主分析=独立复核=administration_date（两侧逐字相同，R3-01家族第5+次目击） | 给药日期列128行全为合法日期（2026-03-02~2026-07-08），同受试者相邻给药间隔实测全部恰为**14天** | 采纳两侧一致角色 administration_date |
| EX·EXFRQ | 列标题'给药频次'但全列128行唯一值'300mg'（剂量值非频次）：列内容实为单次给药剂量 | 全列唯一值'300mg'（剂量+单位格式，与'给药药物'列'300mg'一致）；频次语义不在本列——实际给药间隔每14天一次 | 按单次给药剂量口径采纳 treatment_administration_dose（系统推荐一致），频次以给药日期列实测间隔为准 |
| EX·EXSTATE | 主分析=独立复核=administration_status（两侧逐字相同） | 给药状态列完成×86/延迟给药×42二值分布 | 采纳两侧一致角色 administration_status |

**如实留痕的合成数据观察（供复盘官，非链路阻断）**：EX域存在标签-内容双不一致——
① EXFRQ列标题'给药频次'但内容是剂量'300mg'；② EXTRT列方案标签'300mg Q4W'（每4周）
但实测给药间隔全部为每14天（Q2W）。系统浮出了①的标签-内容问题（EXFRQ卡），但
未自行提出②的间隔-标签矛盾——与R10-02（PSO剂量/途径实质矛盾未被系统提出）同型：
事实层可推导的实质性矛盾未转化为监查发现。作答文本已如实载明②的实测依据。

### AI 节点路由核验（台账：medical_monitoring_ai.sqlite3 直读；/api/ai/queue 本build仍404）

本项目总量 62 作业（权威4+映射首遍20+裁决主19+裁决盲核19），终态 61 completed +
1 terminal failed，**0 queued/running（无滞留，项目级与实例级双查均0）**；唯一
failed（裁决盲核CM分片）有显式 failure_code=provider_runtime_error/
failure_message=「AI provider returned only reasoning tokens with no final answer
channel; reasoning is not accepted as medical content (failure_code=
provider_reasoning_only)」、attempt=4/4、automatic_recovery_count=1（无静默失败），
经 bounded-gap 吸收后 adjudication complete/remaining=0/sys=19。调用89次，
prompt 1,055,922 + completion 623,284 tokens。

| 节点 | provider/model（台账实测） | 作业数 | 终态 | ok |
|---|---|---|---|---|
| 文档权威主 | cms-router/glm-5.3-flash（analysis primary-v9、review primary-v7 各1） | 2 | 2 completed | ✅ |
| 文档权威盲核 | ollama-cloud/deepseek-v4.1-flash（analysis verifier-v9、review verifier-v7 各1） | 2 | 2 completed | ✅ |
| 映射主 | cms-router/glm-5.3-flash（listing-field-mapping-v19） | 10 | 10 completed（R10P2/R11P1 的 EX/AE 分片 invalid_ai_output 首遍失败未复发） | ✅ |
| 映射盲核 | ollama-cloud/deepseek-v4.1-flash（mapping-verifier-v8-tools-v6） | 10 | 10 completed | ✅ |
| 裁决（映射收敛） | 主 cms-router/glm-5.3-flash（adjudication-v19-tools-v7.2）19：19 completed；盲核 ollama-cloud/deepseek-v4.1-flash（adjudication-verifier-v17-tools-v7.2）19：18 completed+1 failed | 38 | 37 completed + 1 terminal failed（reasoning-only att=4，bounded-gap吸收，收敛complete/remaining=0/sys=19） | ✅（失败可见且按设计恢复为可见缺口） |
| 监查分析 | 本build运行lane不经AI台账（实例全库 task_type 仅 document_authority_*/listing_field_mapping 双核对；FactsModeOutputProvider 事实回执确定性产出，同R10P3发现3/R11P2） | 0 | —（无作业=无滞留/无静默失败；15发现+477风险已产出） | ✅（机制核实，如实报0作业） |

### 过程事件（如实）
- 20261002T20:15:45Z（本地04:15）run1 启动：精确名建项一次成功；上传/文档权威
  325.1s全绿；映射双队列04:21启动，04:39首遍20/20全completed（无分片失败）；
  adopt 201 后裁决波 46→40→27（sys 0→6→19），收敛期既有决策表25卡按实测作答
  （06:25），第4波浮出3张未知EX卡 fail-closed 退出（exit 2，7440s）；
- 06:26-06:29 openpyxl 实测 EX 表（上表依据），驱动补 R12P_ROUND1_CARDS（注释含
  实测依据+fail-closed防护说明）；
- 06:29:48 run2 幂等续跑：建项/上传/文档权威秒级复用，3卡作答06:29:57→adjudicate
  一次即 complete/remaining=0/sys=19（run1 收敛期+fail-closed间隙约4.5分钟内后端
  AI队列独立排干——与R11P2记载的驱动侧停止后队列继续排干同现象）→confirm 200
  （draft v74，18.1s）→facts 201→bootstrap/prepare 200（60ms）→运行30.3s
  10/10 completed→发布available→结果可读，八阶段全绿（exit 0）；
- 后续为复盘归档做了API独立复核（非驱动日志自证）：progress端点10/10项100%+
  已完成×10、publication端点available、result-entry/overview 597,305字节/
  15发现/16受试者/477风险、identity归属、source-manifest real_source_slice、
  runs列表仅1条（无孤儿）——全部一致；
- console /tmp/mm_api_8911.log 全程 0 字节（uvicorn --log-level warning，与前几轮
  同现象；本轮链路干净无门禁拒绝，无需 console 取证）；
- 开赛前健康断言（按R11轮升级请求⑦落实于本轮预检）：8911 runtime-readiness
  ready:true（build api-21b0d9e61406a8e）、5178 配对一致、AI网关 status
  configured+route_validation_errors=[]、实例台账 0 queued/running、最近一次
  provider_runtime_error 为 R12D 路由修复前（16:11Z，proj_user_d02f5371b45d）
  ——503限流窗口未复发，R12D 主侧直连配置持续生效；
- 全程未触碰 8910/5177（本轮开始/结束仅只读复核连接拒绝状态，二者无监听为
  R12D 已记载的既有状态，非本轮所致）；未改任何产品代码/数据库（驱动脚本与
  一次性预检项目自身数据除外）；项目与全部留痕原地保留（归档交复盘官）。
