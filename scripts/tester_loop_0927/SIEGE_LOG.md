# 攻坚日志（SIEGE_LOG）——运行启动死锁

按轮分节。每轮记录：复现（请求/响应/状态/耗时）→ 两侧口径差钉代码行 → 修复 → 重验。

---

## R39 攻坚·第 1 次（2026-10-13，攻坚工程师-R39-第1次）

### 0. 结论先行

**墙未复发：R38 修复员五条修复（7c9d8f03：R36-03/05/06/08/09）与 R38 轮次
归档（9c63bd6d）之后，8911 于 2026-10-13 06:26:06 重启、5178 于 06:26:50
重启（ISO_ENV_LOG 06:43 标准条目），本轮两遍全新幂等键全链全绿，零阻断、
零代码修复、零重启、零跳门。** 常驻项目「MX循开考-CSU」（proj_user_6ef58ac151e1）
以两个全新幂等键（r39s-fresh-60e279f8ee0d=registry seq 63 /
r39s-fresh-def9f57d2361=seq 64）各走完 run-setup/options →
workspace/bootstrap（留证）→ prepare-and-start → progress completed
（15s/2 轮询）→ publication available → result-entry → overview 可读
（两遍均为 1,243,923B/60 发现/16 受试者/389 现行风险）。主投影
query_findings 与 R38 基线 60 条逐条**零漂移**；current_risks 389 条中
**恰 2 条**新增 R36-05 治疗 emergent 时间矛盾提示（risk-AE-000011
2026-03-13 早于首次给药 2026-03-16——即 7c9d8f03 提交说明点名的命中场景；
risk-AE-000014 2026-03-18 早于 2026-03-30），字节数 1,242,681→1,243,923
（+1,242B）逐字段归因为 R36-05 设计内输出，content_hash/
replay_content_identity 变化系其下游哈希，非内容损坏。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（pid 38899，2026-10-13 06:26:06 拉起，127.0.0.1 IPv4 监听）
  `/api/runtime-readiness` 200 status=ready、
  backend_build_id=**api-34f525073da51f3e**（7c9d8f03 提交说明
  ISO_ENV_LOG 条目同指纹）；`/api/health` 200（integrity ok, schema v16）。
- 5178（vite node pid 39039，06:26:50 拉起）**仅监听 [::1]:5178（IPv6）**
  ——`curl 127.0.0.1:5178` 连接拒绝（000）而
  `http://localhost:5178/monitoring` 200，与 R24/R25 记录的监听布局同型；
  runtime-build.json expectedBackendBuildId=api-34f525073da51f3e 与后端
  **配对一致**（frontendBuildId=web-fc1973818c3b7897，与 R38 归档留痕同）。
- 加载面实证：`git rev-parse --show-toplevel`=implementation/workbench、
  `git diff HEAD --stat -- packages services frontend/src` 为空——
  磁盘==HEAD==进程加载面（HEAD=9c63bd6d，含 7c9d8f03 五条修复；工作区仅
  R5_SEEDED_PROJECT.md/STATE_V2.json 留痕文件改动，源码零改动）。
- 复现前磁盘基线：launch_registry 62 条全部 completed+result_available=1、
  **waiting_start=0**（尾 4 条：seq 59 monitoring_fb491a46 e49f95084811、
  seq 60/61 r38s 攻坚两键 f58ccf16c4f3、seq 62 monitoring_dc93df88
  e49f95084811=UI 键家族）；execution_profiles `global_default|*|1` 在位；
  admission_events 6 行。

### 2. 复现（任务①）——两遍全链（驱动 `r39s_siege_repro.py`，证据
`r39s_siege_evidence.jsonl` 54 行、0 阻断）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测）。

**第一遍（00:23:35Z 起，key=r39s-fresh-60e279f8ee0d，链路壁钟 39s
含两遍）**：

| 步骤 | 实测 |
| --- | --- |
| 基线双侧 | mapping-candidates 200（236ms，confirmation_status=confirmed/draft v80 confirmed/60 候选）、facts 200（91ms，state=ready）、project/open 200（102ms，current/edit/canEdit）、protocol-versions 200（47ms）——预置台与运行门无口径差 |
| run-setup/options | 200，225ms，snapshot:ef8692acfbab4d2a9846916f（与 R34–R38 同快照） |
| workspace/bootstrap（留证） | 200，100ms，replayed=true revision=1 |
| prepare-and-start | **200，433ms**，run:c04ef12cfe44e8a211b439e9（registry seq 63） |
| progress | completed，percent=100.0，polls=2，run_seconds=15（result_available 投影时序沿 R20 §4：发布后才置 1） |
| publication | POST 200 → **available**（753ms） |
| result-entry | 200，371ms，rct=result-context:77f44baa10d14815992c3aea0fe8cf14 |
| results/{rct}/overview | 200，403ms，**1,243,923B、60 发现/16 受试者**；缓存探针二读 218ms 字节相等 |

**第二遍=重验（任务③，key=r39s-fresh-def9f57d2361）**：全绿同型——
options 200（228ms，同快照）→ bootstrap 200 replayed → prepare-and-start
**200**（427ms，run:b9cbf9b3776fa5e287fe806d，seq 64）→ progress completed
（polls=2，15s）→ publication **available**（695ms）→ entry 200
（rct=result-context:97290e3eb76343508dca4ec5aa5df7d4）→ overview 200
（404ms，1,243,923B/60/16，chain_ok=True；缓存探针 184ms 字节相等）。

终态磁盘：sequence 1-64 全部 completed+result_available=1（新增 63/64 两行
mdig 均为 f58ccf16c4f3 主指纹家族；seq 59/62 的 e49f95084811 为 UI 键
rule_tokens_json 输入差，R38 攻坚已归因非缺陷）、**waiting_start=0**、
admission_events 6 行=6 行（零新增接入事件）、global_default|*|1 三次
采样稳定。

### 3. 修复（任务②）与交接回归项核验

**无需新修复，本轮零代码改动、零重启。** 两侧口径在本轮无分叉：预置台
（mapping confirmed / facts ready / project current）与运行启动门
（run-setup/options 200 + prepare-and-start 200×2）读数一致；任务书装备的
`backend_truth()` 同刻对照在两遍 b3 前均实测（0 阻断未触发归因路径）。

**交接回归警报核验（PAUSE_HANDOFF_20261013：新 build 使 study-documents
ready 退化、新生成字段映射会被 422 拒——恢复后 R39 验证）**：

- 复现前实测：GET study-documents → 200（11,950ms，首读慢调用家族），
  **ready=false、state=analyzing**、headline「已上传研究文件的核对尚未得出
  结论」、analysis_token=mmbatch_06432a73d31b1d87094f90fd——该批次文件
  mtime=2026-10-06 03:04、authority_status=not_adjudicated（两候选
  not_promoted/not_assessed），是**陈旧未晋级批次**经
  `mapping_candidate_routes.py:917-938`（_latest_unpromoted_batch_brief
  附带，R25-02 语义）附着于未就绪投影，并非在途 AI 作业。
- **该状态不拦运行链**：本轮两遍 prepare-and-start 均 200 + 全链绿为直接
  证明；映射生成 422 门
  （`document_evidence.py:491-509` validate_document_evidence_packet →
  `mapping_document_evidence_roles_unmet`，经 `mapping_bridge.py:425`
  消费）只作用于**新生成字段映射**输入，对已确认映射（draft v80/60 候选）
  的运行启动不生效。与 R38-03 台账项（「方案事实与规则发布」准备核对面板
  `registered document authority is incomplete`，status=待修复）同子系统、
  相互印证：**该回归在当前 build（api-34f525073da51f3e）仍在场，属 R38-03
  修复员排期项，非本轮运行链墙**。
- 「新生成字段映射会被 422 拒」本轮**未实测**：触发映射再生成会改写常驻
  项目已确认映射夹具（破坏性、超出运行链验证边界），留待测试者轮按
  strategyNote 以独立脚本核验。

### 4. 在役回归（本轮亲测）

- `pytest tests/test_medical_monitoring_r7_product_router.py -k r19_siege -q`
  → **2 passed**（1.03s，R19 global_default 补种两用例）。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py -q` →
  **97 passed**（41.77s；与 R27 全绿同数，R38 修复员记录的
  late_project_dispatchers 409 未复现）。

### 5. 遗留与边界（转台账，不属本轮墙判据）

- study-documents ready=false/R38-03 准备核对面板失联：见 §3，待修复员
  沿 authority 注册记录（src_proj_user_6ef58ac151e1_protocol_docx_b6e1bceb269c）
  定位；本轮证据（陈旧批次附着路径+422 门代码行）可直接复用。
- study-documents 首读 11,950ms：沿 R25 §7 偶发慢调用家族观察，未拦链路。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径，沿 R25-R38 历轮边界）。

留痕文件：`r39s_siege_repro.py`、`r39s_siege_evidence.jsonl`、
`r39s_overview_p1.json`、`r39s_overview_p2.json`、本日志节。

---

## R38 攻坚·第 1 次（2026-10-13，攻坚工程师-R38-第1次）

### 0. 结论先行

**墙未复发：R37 测试者修复（9e6f97a0：R37-01/02/06+R35-02/03 五条——后端面
services/api/app/{main,source_content_validation,monitoring_ai_service}.py
+packages document authority 归并+前端向导面）与轮次归档（43aa3376）之后，
8911 于 2026-10-13 02:29:10 重启（全部源码 mtime 02:28:11 均早于进程启动；
`git diff HEAD -- packages services frontend/src` 为空——
磁盘==HEAD==进程加载面），本轮两遍全新幂等键全链全绿，零阻断、零代码修复、
零重启、零跳门。** 常驻项目「MX循开考-CSU」（proj_user_6ef58ac151e1）以两个
全新幂等键（r38s-fresh-df73854baef2 / r38s-fresh-efdac43c3ab6）各走完
run-setup/options → workspace/bootstrap（留证）→ prepare-and-start →
progress completed（15s/2 轮询）→ publication available → result-entry →
overview 可读，主投影（query_findings+current_risks）与 R37 基线**逐位相等**
（1,242,681B/60 发现/16 受试者/389 现行风险）。

### 1. 复现（两遍全链，r38s_siege_repro.py，证据 r38s_siege_evidence.jsonl）

前置三条件自检全过：① /api/runtime-readiness ready:true
（backend_build_id=**api-5b547c38911d4ad5**，即 9e6f97a0 提交内留痕的新指纹）；
② http://localhost:5178/monitoring HTTP 200；③ 5178/runtime-build.json
expectedBackendBuildId=api-5b547c38911d4ad5 配对一致
（frontendBuildId=web-7c41e90d1490184a 与提交留痕同）。
**加载实证（forensics）**：9e6f97a0（02:39 提交）全部源码 mtime 02:28:11 早于
8911 进程启动 02:29:10；提交后 diff 空——进程加载面==HEAD（含 R37 五条修复）。

| 侧 | 信号 | 实测（两遍一致） |
| --- | --- | --- |
| 预置台/API | mapping-candidates | state=candidates_ready，confirmation_status=**confirmed** |
| 预置台/API | facts | state=**ready** |
| 预置台/API | r7/project/open | state=**current** |
| 预置台/API | run-setup/options | 200，222/224ms，snapshot_token=snapshot:ef8692acfbab4d2a9846916f（与 R34–R37 同快照） |
| 磁盘 | launch_registry（基线） | 59 条全 completed、waiting_start=0；seq 59=monitoring_fb491a46…（10-12T12:23Z，R37 测试者轮 UI 回归运行） |
| 磁盘 | execution_profiles | `global_default\|*\|1`（R19 修复在盘） |
| 磁盘 | admission_events.jsonl | 6 行，本轮时间窗**零新增** |

全链逐步（2026-10-12T19:09:46Z 起两遍共 36s）：

| 步 | 端点 | 第一遍 | 第二遍 |
| --- | --- | --- | --- |
| 1 | GET run-setup/options | 200，222ms，同快照 | 200，224ms，同快照 |
| 2 | POST workspace/bootstrap（留证：前端零组件调用） | 200，97ms，replayed=true revision=1 | 200，102ms，replayed=true revision=1 |
| 3 | POST runs/prepare-and-start（全新幂等键） | **200，423ms**，run:da06f204577ee2dd4… | **200，416ms**，run:0e173979eb815986… |
| 4 | GET runs/{token}/progress | **completed**，percent=100，2 次轮询，15s | **completed**，percent=100，2 次轮询，15s |
| 5 | POST runs/{token}/publication | 200，712ms，publication_state=**available** | 200，678ms，**available** |
| 6 | GET runs/{token}/result-entry | 200，335ms，rct=result-context:c74b910a…611b | 200，322ms，rct=result-context:d44c1391…2f17 |
| 7 | GET results/{rct}/overview | 200，408ms，**1,242,681B/60 发现/16 受试者/389 现行风险** | 200，403ms，主投影逐位一致 |
| 8 | GET results/{rct}/overview（缓存探针） | 200，181ms（首读 408ms） | 200，182ms（首读 403ms） |

终态磁盘：sequence 60/61 两条新 run 全 completed、result_available=1、
request_fingerprint=68ba60ad…（与 R34–R37 各轮 siege 运行逐位同指纹）、
registry 共 61 条全 completed、waiting_start=0；admission_events 仍 6 行。

### 2. 两处口径差异的归因（均非缺陷，留证防误判）

1. **seq 59（R37 测试者轮 UI 运行）manifest_digest=e49f95084811 ≠
   f58ccf16c4f3（R34–R38 siege 运行）**：launch_registry 行级对照（本轮
   实测）——seq 59 的 `rule_tokens_json=["rule-revision:5d00d4ce2f2622ce…"]`
   非空（UI 向导携带风险规则修订），seq 57/58/60/61 的 rule_tokens_json 为空；
   输入不同 → request_fingerprint/manifest_digest 不同，**输入差非代码漂移**。
   本轮两遍指纹与 R34–R37 同输入运行逐位一致。
2. **两遍 overview 除主投影外 `query_findings_meta.query_drafts` 顺序不同**：
   结构化 diff（本轮实测）——60 个 finding_id 集合两遍相等、逐 finding
   内容（除每轮派生的 query_draft_id）逐字段相等、主投影
   query_findings+current_risks 三方（p1/p2/R37）逐位相等；差异仅
   query_drafts 列表顺序 + 由其派生的 artifact/content_sha256 哈希。属
   列表顺序非确定性，结果内容**零漂移**；R37 节「两遍逐项一致」结论按
   字节/计数口径成立，本轮将「顺序非确定」细目补记在案。

### 3. 修复

**无（零阻断零代码改动）。** 运行链上无任何一道门拒绝：接入管线侧
confirmed/ready/current 与运行门无口径差；prepare-and-start 首击即 200
（423/416ms），无 waiting_start 残留、无 in_flight_conflict、无
global_default_missing（R19 ensure_builtin_global_default 持续在役，
profile_layer_versions 稳定 `global_default|*|1`）；publication 首击即
available；result-entry/overview 冻结包会话缓存（R34-09/R32-07）持续在役
（二读 181/182ms vs 首读 408/403ms）。8911/5178 本轮全程未重启（02:29 拉起
后持续在役，重启系 R37 测试者轮标准操作，非本轮所为）。

### 4. 回归（本轮实跑，.venv/bin/pytest）

- `pytest tests/test_medical_monitoring_r7_product_router.py -k
  "r19_siege or prepare_and_start or global_default" -q`：**7/7 绿**
  （运行启动 siege 语义：缺失补种/失败 fail-closed 无僵尸/幂等重放）；
- `pytest tests/test_mm_r37_document_authority_multi_candidate.py
  tests/test_mm_r35_project_code_not_study_number.py -q`：**10/10 绿**
  （9e6f97a0 新代码面：document authority 多候选归并 ×6 + R35 项目代号
  提示 ×4）；
- `pytest tests/test_source_content_validation.py -q`：**23/23 绿**
  （R35-02/R35-03 触达面 registered 基准与确认回执分离）。

### 5. 遗留与边界

- backend_build_id 指纹仅覆盖 services/api/app、不含 packages/** 的口径
  未变（R32 起在案，留待所有者裁决扩面）；本轮 9e6f97a0 的 packages 改动面
  由 mtime forensics + git diff 空 + §4 该面 10 项单测三重确证在役。
- R37-01（向导复核进度段拼写修正）属界面交互面，本轮 API 驱动全链未触达
  （mapping 已 confirmed、无在途复核）；其渲染级回归 3 fixture 已在
  9e6f97a0 提交内留痕，界面呈现归测试者轮。
- 结果内容基线与 R36/R37 相同：**1,242,681B/60 发现/16 受试者/389 现行
  风险/病史一致性×19/常见适应症×36（提示核实×18）/化验趋势×1**，后续轮次
  继续按此口径比对（注意 §2-2 顺序非确定细目）。
- 常驻项目 registry 现 61 条全 completed；后续轮次开考直接走「开始运行
  监查」即可。

留痕文件：`r38s_siege_repro.py`、`r38s_siege_evidence.jsonl`、
`r38s_overview_p1.json`、`r38s_overview_p2.json`、本日志；本轮零重启，
ISO_ENV_LOG 无新条目（02:29 拉起条目已在 9e6f97a0 提交内留痕）。

---

## R37 攻坚·第 1 次（2026-10-12，攻坚工程师-R37-第1次）

### 0. 结论先行

**墙未复发：R36 测试者修复（76bef91c：R36-01/02/04+R34-02/03/04 六条——
后端改动全在 packages/admission/mapping_confirmation.py+pipeline.py+
api/r7_product/mapping_candidate_routes.py，前端四文件；services/api/app
零改动故 build 指纹不变 api-4ee144cc0f399a1e；8911 进程 16:41:13 拉起、
3 个 packages 文件 mtime 16:40:45 均早于进程启动、16:44:49 提交后
`git diff 76bef91c..HEAD -- packages services frontend/src` 为空——
磁盘==HEAD==进程加载面）下，本轮两遍全新幂等键全链全绿，零阻断、零代码
修复、零重启。本轮 = 76bef91c 新代码面（双盲复核收敛/文件夹混选收口/
结果读取重试承诺）在役下的首次运行链证明；该提交不触 facts_publication，
结果内容与 R36 基线逐项零漂移（1,242,681B/60 发现/16 受试者/389 现行
风险、病史一致性×19/常见适应症×36（提示核实×18）/化验趋势×1/严重程度
中度 15 卡全 AE recorded/系统按中重度标记 45/SV 残留 26 全失约行）。**
常驻项目「MX循开考-CSU」（proj_user_6ef58ac151e1）以两个全新幂等键
（r37s-fresh-10dc32f36488 / r37s-fresh-c7244c48489d）各走完
run-setup/options → workspace/bootstrap（留证）→ prepare-and-start →
progress completed（15s/2 轮询）→ publication available → result-entry →
overview 可读，两遍逐项一致（合计 40s）。

### 1. 复现（两遍全链，r37s_siege_repro.py，证据 r37s_siege_evidence.jsonl）

前置（本轮开始时 8911 PID 92639=16:41:13 拉起、5178 PID 93548=16:45 拉起，
本轮零重启），三条件自检全过：① /api/runtime-readiness ready:true
（backend_build_id=api-4ee144cc0f399a1e）；② http://localhost:5178/monitoring
HTTP 200；③ 5178/runtime-build.json expectedBackendBuildId 配对一致——
该文件由 vite 插件 workbench-runtime-build-manifest 在 dev server 每次启动
时按源码现算（frontend/vite.config.mjs:58-77 sourceFingerprint），16:45
启动晚于末次源码 mtime 16:44:43，故 frontendBuildId=web-fbcf1a886af42cbf
即当前源码指纹（与 R36 修复提交内留痕 web-95e6457ceeb785a3 的差异为指纹
时点差异，非源码漂移——提交后源码零改动为 git diff 空所证）。
**加载实证（forensics）**：76bef91c 的 3 个 packages 文件 mtime 16:40:45
早于进程启动 16:41:13；提交后 diff 空——进程加载面==HEAD。

| 侧 | 信号 | 实测（两遍一致） |
| --- | --- | --- |
| 预置台/API | mapping-candidates | 200，state=candidates_ready，confirmation_status=confirmed |
| 预置台/API | facts | 200，state=ready |
| 预置台/API | r7/project/open | 200，state=current |
| 预置台/API | run-setup/options | 200，295/298ms，snapshot_token=snapshot:ef8692acfbab4d2a9846916f（与 R34–R36 同快照） |
| 磁盘 | launch_registry（基线） | 56 条全 completed、waiting_start=0（sequence 56=monitoring_a71dd3c5…，10-12T02:14Z，R36 测试者轮回归运行，mdig f58ccf16c4f3） |
| 磁盘 | execution_profiles | `global_default\|*\|1`（R19 修复在盘） |
| 磁盘 | admission_events.jsonl | 6 行，本轮时间窗**零新增** |

全链逐步（2026-10-12T12:12:24Z 起两遍共 40s）：

| 步 | 端点 | 第一遍 | 第二遍 |
| --- | --- | --- | --- |
| 1 | GET run-setup/options | 200，298ms，同快照 | 200，295ms，同快照 |
| 2 | POST workspace/bootstrap（留证：前端零组件调用） | 200，144ms，replayed=true revision=1 | 200，140ms，replayed=true revision=1 |
| 3 | POST runs/prepare-and-start（全新幂等键） | **200，562ms**，run:08ed0ccade19445b… | **200，572ms**，run:ce99f8c0d3906088… |
| 4 | GET runs/{token}/progress | **completed**，percent=100，2 次轮询，15s | **completed**，percent=100，2 次轮询，15s |
| 5 | POST runs/{token}/publication | 200，921ms，publication_state=**available** | 200，885ms，**available** |
| 6 | GET runs/{token}/result-entry | 200，423ms，rct=result-context:3f53bea4…caf42 | 200，435ms，rct=result-context:59eba9bf…bd646 |
| 7 | GET results/{rct}/overview | 200，469ms，**1,242,681B/60 发现/16 受试者/389 现行风险** | 200，513ms，**逐项一致** |
| 8 | GET results/{rct}/overview（缓存探针） | 200，245ms（首读 469ms），字节相等 | 200，275ms（首读 513ms），字节相等 |

终态磁盘：sequence 57/58 两条新 run 全 completed、result_available=1、
manifest_digest=f58ccf16c4f3（与 R34/R35/R36 同快照同摘要）、registry 共
58 条全 completed、waiting_start=0；admission_events 仍 6 行（零新增拒绝）。

### 2. 结果内容基线比对（R36→R37 零漂移，逐项实测）

R36 基线 1,242,681B/60 发现/16 受试者/389 现行风险 → 本轮**逐项相同**
（overview_bytes=1,242,681 两遍；current_risks=389 两遍；两遍 overview
除 identity.public_run_token 外内容一致）。家族计数逐项核对（p1 全文）：
「合并用药与病史一致性待核实」×19、「常见适应症」×36（「提示核实」×18）、
「化验趋势」×1（AE-化验矛盾）、发现卡「严重程度中度」15/15 全为 AE
recorded 域（「记录一条不良事件」）、inferred 域 45 张卡「系统按中度/
重度关注标记」、protocol_compliance:SV 残留 26 条 **26/26 全失约行**。
与 R36 节记录逐字一致——76bef91c 六条修复全部不触结果内容面
（mapping_confirmation/pipeline/mapping_candidate_routes 为识别与确认面，
前端四文件为呈现面），本轮实测证实。

### 3. 修复

**无（零阻断零代码改动）。** 运行链上无任何一道门拒绝：接入管线侧
confirmed/ready/current 与运行门无口径差；prepare-and-start 首击即 200
（562/572ms），无 waiting_start 残留、无 in_flight_conflict、无
global_default_missing（R19 ensure_builtin_global_default 持续在役，
profile_layer_versions 稳定 `global_default|*|1`）；publication 首击即
available；result-entry/overview 冻结包会话缓存（R34-09/R32-07）持续在役
（二读 245/275ms vs 首读 469/513ms，字节逐位相等）。8911/5178 本轮全程
未重启（16:41/16:45 拉起后持续在役；本轮开始前的该次重启非本轮所为，
属 R36 测试者轮标准重启，加载疑义由 mtime forensics + git diff 空 +
§2 行为零漂移三重关闭）。

### 4. 回归（本轮实跑，.venv/bin/pytest）

- `pytest tests/test_medical_monitoring_r7_product_router.py -k
  "r19_siege or prepare_and_start or global_default" -q`：**7/7 绿**
  （运行启动 siege 语义：缺失补种/失败 fail-closed 无僵尸/幂等重放）；
- `pytest tests/test_mm_r36_dual_review_convergence.py
  tests/test_mapping_inflight_adoption_r35.py
  tests/test_facts_mode_outputs_severity_semantics_r35.py
  "tests/test_medical_monitoring_r7_data_admission.py::test_resolve_get_rejects_missing_and_malformed_batch_id_structured" -q`：
  **13/13 绿**（76bef91c 最新改动面双盲复核收敛 ×7 + R35 分诊面
  降级采纳 ×4 + 严重程度语义 ×1 + resolve 422 结构化门 ×1）。

### 5. 遗留与边界

- backend_build_id 指纹仅覆盖 services/api/app、不含 packages/** 的口径
  未变（R32 起在案，留待所有者裁决扩面）；76bef91c 的 packages 改动面由
  §1 mtime forensics + git diff 空 + §2 行为零漂移三重确证在役。
- R36-01（双盲复核收敛）四条后端语义中，常驻项目本轮仅触及
  prepare-and-start→progress→publication 链（mapping 已 confirmed、无
  在途复核），复核收敛/文件夹混选/降级通道属**不触发面**，其单测 13 项
  中 7 项已覆盖，界面呈现归测试者轮。
- 结果内容基线与 R36 相同：**1,242,681B/60 发现/16 受试者/389 现行
  风险/残留 SV 锚点 26 条全失约行/病史一致性×19/常见适应症×36
  （提示核实×18）/AE-化验矛盾×1**，后续轮次继续按此口径比对。
- 常驻项目 registry 现 58 条全 completed；后续轮次开考直接走「开始运行
  监查」即可。

留痕文件：`r37s_siege_repro.py`、`r37s_siege_evidence.jsonl`、
`r37s_overview_p1.json`、`r37s_overview_p2.json`、本日志；本轮零重启，
ISO_ENV_LOG 无新条目（16:41/16:45 拉起条目已在 76bef91c 提交内留痕）。

---

## R36 攻坚·第 1 次（2026-10-12，攻坚工程师-R36-第1次）

### 0. 结论先行

**墙未复发：R35 分诊修复（850e39aa：R35-01/06+R33-07/04/10/11 六条，后端
改动全在 packages/**——mapping_confirmation/mapping_candidate_routes/
facts_mode_outputs/facts_publication，前端 medical-monitoring 四文件；
8911 进程 09:34:19 拉起、4 个后端文件 mtime 09:33:44 均早于进程启动、
09:35:55 提交后源码零改动——磁盘==HEAD==进程加载面）下，本轮两遍全新
幂等键全链全绿，零阻断、零代码修复、零重启。本轮 = 850e39aa 新代码面的
首次全链运行证明。** 常驻项目「MX循开考-CSU」（proj_user_6ef58ac151e1）
以两个全新幂等键（r36s-fresh-075ff6a5840d / r36s-fresh-3b322bd24342）各
走完 run-setup/options → workspace/bootstrap（留证）→ prepare-and-start →
progress completed（15s/2 轮询）→ publication available → result-entry →
overview 可读，两遍逐项一致（各 38s 总耗时）。**结果内容基线合法变化并
逐项归因（§2）：current_risks 477→389（-88=R33-11 按期访视不再生成风险
锚点，残留 26 条 SV 全为失约行）、1,469,932→1,242,681 字节、发现 60/
受试者 16/CM-MH ×19/常见适应症对照 ×36/AE-化验矛盾 ×1 恒定**；
R35-06 严重程度语义在役行为级实证（「严重程度中度」15 张卡全为 AE
recorded 域，inferred 域 45 张卡以「系统按中度/重度关注标记」归因）。

### 1. 复现（两遍全链，r36s_siege_repro.py，证据 r36s_siege_evidence.jsonl）

前置（本轮开始时 8911 PID 88436=09:34:19 拉起、5178 PID 88663 在役，本轮
零重启），三条件自检全过：① /api/runtime-readiness ready:true
（backend_build_id=api-4ee144cc0f399a1e）；② http://localhost:5178/monitoring
HTTP 200；③ 5178/runtime-build.json expectedBackendBuildId 配对一致
（frontendBuildId=web-2f9ae4d76eefc842，随 850e39aa 前端改动更新）。
**加载实证（forensics）**：850e39aa 的 4 个后端文件 mtime 09:33:44 均早于
进程启动 09:34:19，提交（09:35:55）后 git status 对源码零改动——进程加载
面==HEAD；行为级双证见 §2（R33-11/R35-06 语义均为该提交才可能的行为）。

| 侧 | 信号 | 实测（两遍一致） |
| --- | --- | --- |
| 预置台/API | mapping-candidates | 200，state=candidates_ready，confirmation_status=confirmed |
| 预置台/API | facts | 200，state=ready |
| 预置台/API | r7/project/open | 200，state=current |
| 预置台/API | run-setup/options | 200，204/207ms，snapshot_token=snapshot:ef8692acfbab4d2a9846916f（与 R34/R35 同快照） |
| 磁盘 | launch_registry（基线） | 53 条全 completed、waiting_start=0（sequence 53=monitoring_602fd305…，10-11T15:10Z，R35 测试者轮回归运行） |
| 磁盘 | execution_profiles | `global_default\|*\|1`（R19 修复在盘） |
| 磁盘 | admission_events.jsonl | 6 行，本轮时间窗**零新增** |

全链逐步（2026-10-12T02:01:58Z 起两遍共 38s）：

| 步 | 端点 | 第一遍 | 第二遍 |
| --- | --- | --- | --- |
| 1 | GET run-setup/options | 200，204ms，同快照 | 200，207ms，同快照 |
| 2 | POST workspace/bootstrap（留证：前端零组件调用） | 200，94ms，replayed=true revision=1 | 200，95ms，replayed=true revision=1 |
| 3 | POST runs/prepare-and-start（全新幂等键） | **200，387ms**，run:5403743943c10557… | **200，399ms**，run:f7a37ad5ce66d7e8… |
| 4 | GET runs/{token}/progress | **completed**，percent=100，2 次轮询，15s | **completed**，percent=100，2 次轮询，15s |
| 5 | POST runs/{token}/publication | 200，702ms，publication_state=**available** | 200，681ms，**available** |
| 6 | GET runs/{token}/result-entry | 200，358ms，rct=result-context:d1eb66af…972ce | 200，380ms，rct=result-context:93227d5d…b8895 |
| 7 | GET results/{rct}/overview | 200，361ms，**1,242,681B/60 发现/16 受试者/389 现行风险** | 200，364ms，**逐项一致** |
| 8 | GET results/{rct}/overview（缓存探针） | 200，181ms（首读 361ms），字节相等 | 200，184ms（首读 364ms），字节相等 |

终态磁盘：sequence 54/55 两条新 run 全 completed、result_available=1、
manifest_digest=f58ccf16c4f3（与 R34/R35 两遍同快照同摘要）、registry 共
55 条全 completed、waiting_start=0；admission_events 仍 6 行（零新增拒绝）。

### 2. 结果内容基线变化逐项归因（R35→R36 合法变化，非回归）

R35 基线 1,469,932B/60 发现/477 现行风险 → 本轮 1,242,681B/60 发现/389
现行风险（-227,251B/风险 -88），发现数/受试者数恒定。逐项钉到 850e39aa
代码面：

1. **-88 现行风险 = R33-11 按期完成的正常访视不再生成风险锚点**：
   `packages/medical_monitoring/projections/facts_publication.py`（R33-11
   改动面，SV 非失约行 with_risk=False，事件保留时间轴）。行为级实测：
   477-389=88 条按期访视锚点清除；残留 26 条 protocol_compliance:SV 风险
   的 evidence_summary **26/26 全为失约行**（样本原文「访视失约·W8
   （2026-05-15）」「访视失约·FU（2026-08-07）」）——仅失约访视继续生成
   锚点与 Query，与该修复的目标行为逐字一致。「把记录存在当风险信号」
   冤枉面消失。
2. **字节差自洽**：-88 条风险行（每条约 2.5KB 文案）全部落在
   current_risks 内容面；projection 结构、发现数（60）、受试者数（16）、
   identity/指纹字段不变，manifest_digest 与 R35 恒定（f58ccf16c4f3）。
3. **R35-06 严重程度语义在役行为级实证**：overview 原文含「严重程度中度」
   的发现卡 15/15 全为 AE 域 recorded 来源（basis「已核验事实：…记录一条
   不良事件（头痛），严重程度中度」——源记录载明）；inferred 域（合并
   用药等）45 张卡 finding 行以「系统按中度关注标记」归因（实测样张：
   basis 只陈述已核验的用药记录事实、不陈述不存在的属性）——
   `packages/medical_monitoring/api/r7_product/facts_mode_outputs.py`
   语义在产出面生效。
4. **R34→R35 既有基线项全部恒定**：「合并用药与病史一致性待核实」×19、
   「常见适应症对照」×36（其中「提示核实」×18）、「与同期化验趋势存在
   矛盾待核实」×1——R34-10 别名全量匹配与 R28-06 AE-化验矛盾交叉核对
   产出无漂移。

### 3. 修复

**无（零阻断零代码改动）。** 运行链上无任何一道门拒绝：接入管线侧
confirmed/ready/current 与运行门无口径差；prepare-and-start 首击即 200
（387/399ms），无 waiting_start 残留、无 in_flight_conflict、无
global_default_missing（R19 ensure_builtin_global_default 持续在役，
profile_layer_versions 稳定 `global_default|*|1`）；publication 首击即
available；result-entry/overview 冻结包会话缓存（R34-09/R32-07）持续在役
（二读 181/184ms vs 首读 361/364ms，字节逐位相等）。8911/5178 本轮全程
未重启（09:34:19 拉起后持续在役，加载疑义由 mtime forensics + §2 行为级
双证共同关闭）。

### 4. 回归（本轮实跑）

- `pytest tests/test_mapping_inflight_adoption_r35.py
  tests/test_facts_mode_outputs_severity_semantics_r35.py
  "tests/test_medical_monitoring_r7_data_admission.py::test_resolve_get_rejects_missing_and_malformed_batch_id_structured" -q`：
  **6/6 绿**（850e39aa 三改动面：R35-01 降级采纳 ×4、R35-06 严重程度
  语义 ×1、R33-07 resolve 422 结构化 ×1）；
- `pytest tests/test_facts_publication_event_time.py
  tests/test_facts_publication_scale_week_anchor_r31.py -q`：**12/12 绿**
  （R33-11 按期访视无锚点断言 + scale_week 夹具）；
- `pytest tests/test_medical_monitoring_r7_product_router.py -k
  "r19_siege or prepare_and_start or global_default" -q`：**7/7 绿**
  （运行启动 siege 语义：缺失补种/失败 fail-closed 无僵尸/幂等重放）。

### 5. 遗留与边界

- backend_build_id 指纹仅覆盖 services/api/app、不含 packages/** 的口径
  未变（R32 起在案，留待所有者裁决扩面）；850e39aa 的 packages 改动面由
  §1 mtime forensics + §2 行为级证据双重确证在役。
- R35-01（字段识别停滞降级采纳）与 R33-04/10（分片重跑反馈/阶段对账
  标注）在本轮常驻项目上属**不触发面**（mapping 已 confirmed、无在途
  失败分片），其单测 6/6 已覆盖，界面呈现归测试者轮。
- 结果内容基线自本轮起更新为 **1,242,681B/60 发现/16 受试者/389 现行
  风险/残留 SV 锚点 26 条全失约行/「合并用药与病史一致性待核实」×19/
  AE-化验矛盾 ×1**（R33-11 清按期访视锚点的合法净变化），后续轮次勿再
  按 477 现行风险口径比对。
- 常驻项目 registry 现 55 条全 completed；后续轮次开考直接走「开始运行
  监查」即可。

留痕文件：`r36s_siege_repro.py`、`r36s_siege_evidence.jsonl`、
`r36s_overview_p1.json`、`r36s_overview_p2.json`、本日志；本轮零重启，
ISO_ENV_LOG 无新条目（09:34 拉起条目已在其上，见 850e39aa 提交内 08:5x/
09:34 双重启留痕）。

---

## R35 攻坚·第 1 次（2026-10-11，攻坚工程师-R35-第1次）

### 0. 结论先行

**墙未复发：R34 分诊修复（d4dbd691：R34-07/01/09/10+R28-06+R32-07 六条，
backend_build_id 升为 api-4ee144cc0f399a1e，2026-10-11 14:29Z 双重启加载、
22:48 R35 环境门按标准命令拉起）下，本轮两遍全新幂等键全链全绿，零阻断、
零代码修复、零重启。** 本轮 = 该新代码面的**首次**全链运行证明（R34 攻坚
两遍绿跑在其前一版 build api-f240b1ef669d7a88 上）。常驻项目「MX循开考-CSU」
（proj_user_6ef58ac151e1）以两个全新幂等键（r35s-fresh-fd5bf2c69389 /
r35s-fresh-2d38de5566fb）各走完 run-setup/options → workspace/bootstrap
（留证）→ prepare-and-start → progress completed（15s/2 轮询）→
publication available → result-entry → overview 可读，两遍逐项一致。
**R34-09/R32-07 结果包会话缓存在役行为级实证**：同一 rct 第二次读取
386→193ms / 405→214ms、字节逐位相等（首读为冷读全量校验，二读命中缓存）。
**结果内容基线合法变化并逐项归因**（§2）：65→60 发现、1,489,541→1,469,932
字节（R34-10 别名全量匹配清除 5 条 CM-MH 误报）、current_risks 477 恒定、
R28-06 AE-化验趋势矛盾交叉核对在役首产 1 条。

### 1. 复现（两遍全链，r35s_siege_repro.py，证据 r35s_siege_evidence.jsonl）

前置（本轮开始时，22:48 环境门已拉起 8911/5178，PID 26745/26774；本轮零重启），
三条件自检全过：① /api/runtime-readiness ready:true
（backend_build_id=api-4ee144cc0f399a1e）；② http://localhost:5178/monitoring
HTTP 200；③ 5178/runtime-build.json expectedBackendBuildId 配对一致
（frontendBuildId=web-693e9d2ed763d7f6）。

| 侧 | 信号 | 实测（两遍一致） |
| --- | --- | --- |
| 预置台/API | mapping-candidates | state=candidates_ready，confirmation_status=**confirmed** |
| 预置台/API | facts | state=**ready** |
| 预置台/API | r7/project/open | state=**current** |
| 预置台/API | run-setup/options | 200，208/217ms，snapshot_token=snapshot:ef8692acfbab4d2a9846916f（与 R34 同快照） |
| 磁盘 | launch_registry（基线） | 50 条全 completed、waiting_start=0（sequence 50=monitoring_b62c39e7…，10:40Z，R34 测试者轮回归运行） |
| 磁盘 | execution_profiles | `global_default\|*\|1`（R19 修复在盘） |
| 磁盘 | admission_events.jsonl | 6 行，本轮时间窗**零新增** |

全链逐步（2026-10-11T14:55Z 起两遍共 37s）：

| 步 | 端点 | 第一遍 | 第二遍 |
| --- | --- | --- | --- |
| 1 | GET run-setup/options | 200，208ms，同快照 | 200，217ms，同快照 |
| 2 | POST workspace/bootstrap（留证：前端零组件调用） | 200，120ms，replayed=true revision=1 | 200，98ms，replayed=true revision=1 |
| 3 | POST runs/prepare-and-start（全新幂等键） | **200，404ms**，run:c13f332e44e0dcee4dd22c31… | **200，403ms**，run:29fb5290c6b4bd5fe5d13074… |
| 4 | GET runs/{token}/progress | **completed**，percent=100，2 次轮询，15s | **completed**，percent=100，2 次轮询，15s |
| 5 | POST runs/{token}/publication | 200，741ms，publication_state=**available** | 200，683ms，**available** |
| 6 | GET runs/{token}/result-entry | 200，350ms，rct=result-context:b8a1fa8d…79b05 | 200，388ms，rct=result-context:57afe01f…e478c3 |
| 7 | GET results/{rct}/overview | 200，386ms，**1,469,932B/60 发现/16 受试者/477 现行风险** | 200，405ms，**逐项一致** |
| 8 | GET results/{rct}/overview（缓存探针，本轮新增） | 200，193ms（首读 386ms），字节相等 | 200，214ms（首读 405ms），字节相等 |

终态磁盘：sequence 51/52 两条新 run 全 completed、result_available=1、
manifest_digest=f58ccf16c4f3（与 R34 两遍同快照同摘要）、registry 共 52 条
全 completed、waiting_start=0；admission_events 仍 6 行（零新增拒绝）。

### 2. 结果内容基线变化逐项归因（R34→R35 合法变化，非回归）

R34 基线 1,489,541B/65 发现 → 本轮 1,469,932B/60 发现（-20,609B/-5 发现），
current_risks 477 恒定。逐项钉到 d4dbd691 代码面：

1. **-5 发现 = R34-10 别名全量匹配清除误报**：
   `packages/medical_monitoring/projections/facts_publication.py:232-290`
   `_cm_mh_consistency_note`——此前只对照 `aliases[0]`，现在
   `acceptable_terms` 全组别名参与病史匹配（:268-271
   `any(term and term in history for term in acceptable_terms)`）。行为级
   实测：「合并用药与病史一致性待核实」24→**19**（CM 发现 24→19，精确
   -5）；「常见适应症对照」46→**36**（第二分支同步收敛，其中
   「常见适应症对照提示核实」新口径 18 条）。病史载「血脂异常/过敏性鼻炎」
   的同药记录不再输出「无对应记录」绝对化误报——正是该修复的目标行为。
2. **+1 条 AE-化验趋势矛盾 = R28-06 首产**：
   `facts_publication.py:336-448` `_ae_lab_trend_contradiction_note`
   （AESEV≥3 级 + 血常规 6 族术语匹配 + 同指标 LB 历次检测均未低于参考
   下限 60% 才触发）。overview 原文实测「该AE声明的严重程度与同期化验
   趋势存在矛盾待核实」×**1**（含实测值/访视引用与「请核查严重程度分级
   依据」出口文案）——此前该监查重点方向确定性零产出，本轮首次有产出。
   注意：该发现的 note 文本是「…与同期化验趋势存在矛盾待核实」，
   不含「AE与化验趋势矛盾」字面（后者仅见于代码注释/监查方向名）。
3. **字节差与发现数差自洽**：-5 条误报发现（每条约 4KB 文案）−1 条新
   矛盾提示，净变化全部落在 query_findings 内容面；projection 结构、
   受试者数（16）、现行风险数（477）、identity/指纹字段均不变。

### 3. 修复

**无（零阻断零代码改动）。** 运行链上无任何一道门拒绝：接入管线侧
confirmed/ready/current 与运行门无口径差；prepare-and-start 首击即 200
（404/403ms），无 waiting_start 残留、无 in_flight_conflict、无
global_default_missing（R19 ensure_builtin_global_default 持续在役，
profile_layer_versions 稳定 `global_default|*|1`）；publication 首击即
available；result-entry/overview 新缓存路径首次实战即绿（fail-open 面未
触发：两次冷读均正常全量校验后返回）。8911/5178 本轮全程未重启（22:48
环境门拉起后持续在役，加载疑义由 22:48 自检三条件 + 本轮行为级证据共同
关闭：缓存探针与 AE-化验矛盾文案均为 d4dbd691 新代码面才可能的行为）。

### 4. 回归（本轮实跑）

- `pytest tests/test_facts_publication_cm_mh_consistency_r29.py
  tests/test_public_result_freeze_0926.py
  tests/test_monitoring_ai_queue_dwell_timeout.py -q`：**29/29 绿**
  （d4dbd691 三个后端改动面：CM-MH 别名全量匹配+AE-化验矛盾 ×12、
  结果包冻结缓存 ×10、动态收割视界 ×7）；
- `pytest tests/test_medical_monitoring_r7_product_router.py -k
  "r19_siege or prepare_and_start or global_default" -q`：**7/7 绿**
  （运行启动 siege 语义：缺失补种/失败 fail-closed 无僵尸/幂等重放）。

### 5. 遗留与边界

- backend_build_id 指纹仅覆盖 services/api/app、不含 packages/** 的口径
  未变（R32 起在案，留待所有者裁决扩面）；d4dbd691 的 packages 改动面
  （facts_publication）由 §1/§2 行为级证据确证在役，services/api 改动面
  （result_context_service 缓存）由 build_id 升级+缓存探针双证。
- R34-01 document_readiness 受限态与 R34-07 动态收割视界在本轮常驻项目
  上属**不触发面**（该项目研究文件配对完整、运行 15s 远短于收割视界），
  其单测 29/29 已覆盖，界面呈现归测试者轮。
- 结果内容基线自本轮起更新为 **1,469,932B/60 发现/16 受试者/477 现行
  风险/「合并用药与病史一致性待核实」×19/AE-化验矛盾 ×1**（R34-10 清误报
  +R28-06 新产出的合法净变化），后续轮次勿再按 65 发现口径比对。

留痕文件：`r35s_siege_repro.py`、`r35s_siege_evidence.jsonl`、本日志；
本轮零重启，ISO_ENV_LOG 无新条目（22:48 环境门条目已在其上）。

---

## R34 攻坚·第 1 次（2026-10-11，攻坚工程师-R34-第1次）

### 0. 结论先行

**墙未复发：R34 轮次修复（047dfdcc：R33-02/01/03+R30-02/04+R29-07 六条，
改动面=facts_publication CM-MH 交叉判定+mapping_candidate_routes 409 登记
+前端 wizard/workspace/confirm-state）下，本轮两遍全新幂等键全链全绿，
零阻断、零代码修复。** 与前两轮（R32/R33 攻坚零重启）不同，本轮执行了
一次 8911 重启：提交内全部 14 个文件 mtime 统一为 18:06:11，晚于前轮重启
16:58:07，且无 stash reflog 可查——进程加载版本无法从 forensics 消除疑义，
按纪律以标准命令重启 8911（只动 8911；registry 无在途运行，安全窗口），
重启后三条件自检全过。常驻项目「MX循开考-CSU」（proj_user_6ef58ac151e1）
以两个全新幂等键（r34s-fresh-e78fda541d63 / r34s-fresh-1d96f3c9daf7）各走完
run-setup/options → workspace/bootstrap（留证）→ prepare-and-start →
progress completed（15s/2 轮询）→ publication available → result-entry →
overview 可读，两遍逐项一致。**R29-07 代码在役获行为级实证**：overview
发现 41→65（+24 =「合并用药与病史一致性待核实」出现次数逐字相等），
CM 发现 24 条全部升 medium（此前 41 发现中 CM=0），「常见适应症对照」
46 次（第二分支同在役）——结果内容合法变化，与 R31–R33 恒定的
1,392,075 字节/41 发现口径不再可比。

### 1. 复现（两遍全链，r34s_siege_repro.py，证据 r34s_siege_evidence.jsonl）

前置（本轮开始时，18:24）：8911 标准命令重启（见 ISO_ENV_LOG 同日条目），
三条件自检：① /api/runtime-readiness ready:true（backend_build_id=
api-f240b1ef669d7a88）；② http://localhost:5178/monitoring HTTP 200；
③ 5178/runtime-build.json expectedBackendBuildId=api-f240b1ef669d7a88
配对一致（frontendBuildId=web-693e9d2ed763d7f6）。

| 侧 | 信号 | 实测（两遍一致） |
| --- | --- | --- |
| 预置台/API | mapping-candidates | state=candidates_ready，confirmation_status=**confirmed** |
| 预置台/API | facts | state=**ready** |
| 预置台/API | r7/project/open | state=**current** |
| 磁盘 | launch_registry（基线） | 47 条全 completed、waiting_start=0 |
| 磁盘 | execution_profiles | `global_default\|*\|1`（R19 修复在盘） |
| 磁盘 | admission_events.jsonl | 6 行，本轮时间窗**零新增** |

全链逐步（2026-10-11T10:28Z 起两遍共 37s）：

| 步 | 端点 | 第一遍 | 第二遍 |
| --- | --- | --- | --- |
| 1 | GET run-setup/options | 200，282ms，snapshot_token=snapshot:ef8692acfbab4d2a9846916f | 200，206ms，同快照 |
| 2 | POST workspace/bootstrap（留证：前端零组件调用） | 200，97ms，replayed | 200，94ms，replayed |
| 3 | POST runs/prepare-and-start（全新幂等键） | **200，377ms**，run:5862c51a0a3681789f3d83cd… | **200，380ms**，run:af1225779260a2a157eab850… |
| 4 | GET runs/{token}/progress | **completed**，percent=100，2 次轮询，15s | **completed**，percent=100，2 次轮询，15s |
| 5 | POST runs/{token}/publication | 200，783ms，publication_state=**available** | 200，715ms，**available** |
| 6 | GET runs/{token}/result-entry | 200，314ms，rct=result-context:f057e64d…de13de | 200，304ms，rct=result-context:8859336f…7b36a |
| 7 | GET results/{rct}/overview | 200，397ms，**1,489,541B/65 发现/16 受试者/477 现行风险** | 200，365ms，**逐项一致** |

终态磁盘：sequence 48/49 两条新 run 全 completed、result_available=1、
registry 共 49 条全 completed、waiting_start=0；admission_events 仍 6 行
（零新增拒绝）。

### 2. R29-07 代码在役实证（行为级，消除 18:06:11 mtime 疑义）

对第二遍 overview（rct=8859336f…）原文检索：

- `合并用药与病史一致性待核实` **24 次** —— 与发现数增量 41→65 的 +24
  逐字相等（facts_publication.py:276/282 的 note 文本）；
- `常见适应症对照` **46 次** —— CMINDC 空/通用分支（facts_publication.py
  内置 21 族对照表）同在役；
- issue 分布：facts-issue-cm=**24**（R33 时 0）、facts-issue-ae=15、
  facts-issue-protocol_compliance=26；CM 发现 basis/finding 文案示
  「中度合并用药信号」= cm_mh_severity_hint="medium" 升级生效
  （facts_publication.py:1211-1226 调用点）。

即：运行中的 8911 进程（本轮 18:24 重启）加载的 facts_publication 与
HEAD（047dfdcc+归档，运行时代码零差异）行为一致，加载疑义关闭。

### 3. 修复

**无（零阻断零代码改动）。** 运行链上无任何一道门拒绝：接入管线侧
confirmed/ready/current 与运行门无口径差；prepare-and-start 首击即 200
（377/380ms），无 waiting_start 残留、无 in_flight_conflict、无
global_default_missing（R19 ensure_builtin_global_default 修复持续在役，
profile_layer_versions 稳定 `global_default|*|1`）。

### 4. 回归（本轮实跑）

- `pytest tests/test_facts_publication_cm_mh_consistency_r29.py`：**7/7 绿**
  （R34 本轮新增 CM-MH 代码面）；
- `pytest tests/test_medical_monitoring_r7_product_router.py -k
  "r19_siege or prepare_and_start or global_default"`：**7/7 绿**
  （运行启动 siege 语义：缺失补种/失败 fail-closed 无僵尸/幂等重放）。

### 5. 遗留与边界

- backend_build_id 指纹仅覆盖 services/api/app、不含 packages/** 的口径
  未变（R32 起在案，留待所有者裁决扩面）；本轮以行为级实证（§2）替代
  指纹证明 packages 代码在役。
- 前端 R34 修复（verifier_incomplete→adjudication-start 自动等待、阻断组
  headline、结果分批挂载、建项弹窗 busy 复位）属向导/结果视图交互面，
  本轮 API 驱动全链未触达；其界面回归归测试者轮。
- 结果内容基线自本轮起更新为 1,489,541B/65 发现/16 受试者/477 现行风险
  （R29-07 CM-MH 合法增量），后续轮次勿再按 41 发现口径比对。

留痕文件：`r34s_siege_repro.py`、`r34s_siege_evidence.jsonl`、本日志；
ISO_ENV_LOG.md 补 8911 重启条目。

---

## R33 攻坚·第 1 次（2026-10-11，攻坚工程师-R33-第1次）

### 0. 结论先行

**墙未复发：R32 轮次修复（c0dc2f0a）+ R32 轮次归档（b3740d86，HEAD）、
2026-10-11 09:17 重启后的新代码面（R7 数据接入族 run_in_threadpool 下放、
retry-failed 新路由、evidence roles 422 门语义变更）下，本轮独立复现两遍
全新幂等键全链全绿，零阻断、零代码改动、零重启。** R32 轮改动触及运行链
上游数据接入族与映射确认门（R32-05 配对未就绪改独立 422 代码），该代码面
下运行链是否仍通未经验证——本轮按任务①独立复现。常驻项目
「MX循开考-CSU」（proj_user_6ef58ac151e1）以两个全新幂等键各走完
run-setup/options → workspace/bootstrap（留证）→ prepare-and-start →
progress completed → publication available → result-entry →
results/{rct}/overview 可读（两遍投影均 **1,392,075 字节/41 发现/16 受试者
/477 现行风险**，逐项一致，与 R32 恒定）。终态磁盘 46 条全部
completed+result_available=1、**waiting_start=0**，admission_events 本轮
时间窗（02:08–02:09Z）零新增（基线 6 行=终态 6 行，末条仍为
2026-10-07T22:36:55Z 历史拒绝）。**本轮 r7 router 全量 97/97 全绿**——
R19 起在案的存量失败
test_late_project_dispatchers_keep_two_actual_api_results_isolated 本轮
通过（该失败为 HEAD 既有偶发，本轮零源码改动、工作树仅台账/驱动文件，
HEAD 等价 trivially 成立；见 §4）。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（Python pid 22140，2026-10-11 09:17:18 起）`/api/health` 200
  （runtime_store integrity ok, schema v16）；`/api/runtime-readiness`
  ready:true、backend_build_id=**api-f240b1ef669d7a88**。5178（vite node
  pid 22182，09:17:23 起）`/runtime-build.json`
  expectedBackendBuildId=api-f240b1ef669d7a88 配对一致
  （frontendBuildId=**web-a9999632d1a640c4**）。本轮全程未重启。
- 新代码实际加载实证（指纹口径差异沿 R32 轮留痕：backend_build_id 仅指纹
  services/api/app，本轮 R32 轮修复全部在 packages/**——ISO_ENV_LOG
  2026-10-11 09:17–09:19 条目已实证 openapi.json 含新路由
  …/mapping-candidates/retry-failed；本轮 §3 回归实测 R32 轮新增三测试
  29 项断言在役）。
- HEAD=b3740d86（R32 轮次归档）；`git status` 仅台账/状态文件
  （PREFLIGHT_LAST_GREEN.json、R5_SEEDED_PROJECT.md、STATE_V2.json）+
  本轮新增驱动/证据，**零源码改动**。
- 复现前磁盘基线：launch_registry **44 条全部 completed+result_available=1**
  （seq 44=R32 轮界面键 monitoring_affef98e…，manifest e49f95084811）、
  **waiting_start=0**；execution_profiles `global_default|*|1` 在位；
  admission_events.jsonl 6 行（末条 2026-10-07T22:36:55Z 历史拒绝）。

### 2. 复现（任务①）——两遍全链（驱动 `r33s_siege_repro.py`，证据
`r33s_siege_evidence.jsonl` 50 行、全 ok、0 阻断）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测，
两遍均 200 replayed=true revision=1 幂等零改动）。

**第一遍（02:08:15Z 起，key=r33s-fresh-449b0c75a688，链路壁钟 ~19s）**：

| 步骤 | 实测 |
| --- | --- |
| 基线同刻双侧 | mapping-candidates 200（533ms，**candidates_ready**、draft confirmed v80）、facts 200（458ms，**ready**）、project/open 200（109ms，**current**）、protocol-versions 200（62ms，confirmed）——预置台与运行门无口径差 |
| run-setup/options | 200，408ms，snapshot:ef8692acfbab4d2a9846916f（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，124ms，replayed=true revision=1 |
| prepare-and-start | **200，434ms**，run:290beaf04bbd07ab…（registry sequence 45，manifest_digest f58ccf16c4f3 同源） |
| progress | 首询 running（332ms），二询 **completed**（percent=100.0，polls=2、15s 间隔；result_available 首询 false，发布后 registry 终态 1，R20 §4/R32 §4 同型投影时序） |
| publication | POST 200→**available**（877ms） |
| result-entry | 200，357ms，rct=result-context:edc702f2147447f9af1a50faadad01c6 |
| results/{rct}/overview | 200，432ms，**1,392,075 字节、41 发现/16 受试者/477 现行风险**，identity.project_ref=proj_user_6ef58ac151e1 |

**第二遍=重验（任务③，02:08:37Z 起，key=r33s-fresh-8bc4ab66cac2，壁钟
~17s）**：同链全绿：options 200（245ms，snapshot 同源）→ bootstrap 200
replayed → prepare-and-start **200**（448ms，run:56cf8c7418adc2e1…，
sequence 46，manifest f58ccf16c4f3）→ progress completed（polls=2）→
publication **available**（960ms）→ entry 200（465ms，
rct=result-context:b661156d7176452ba0a8055e1d574d34）→ overview 200
（547ms，**1,392,075 字节、41/16/477**）。两遍序列化字节数逐项一致，
总耗时 45s。

### 3. 修复（任务②）与口径差对照

**无需新修复，本轮零代码改动、零重启。** 两侧口径在本轮无分叉：预置台
（mapping candidates_ready / facts ready / project current / 方案版本
confirmed 在位）与运行启动门（run-setup/options 200 + prepare-and-start
200×2）读数一致；backend_truth() 对照本轮两遍均未触发差异；
admission_events.jsonl 在本轮时间窗（02:08–02:09Z）**零新增**（基线 6 行
=终态 6 行）。

既有修复在役证明（本轮全部亲测）：

- R19/R27：`pytest tests/test_medical_monitoring_r7_product_router.py
  tests/test_medical_monitoring_r27_protocol_gate_selfheal.py -k "r19_siege
  or protocol or selfheal" -q` → **6 passed**（3.60s）。
- R32 轮改动面（本 build 新代码）+ R31 改动面 + dwell：
  `pytest tests/test_r7_route_event_loop_offload_r32.py
  tests/test_mapping_table_failures_retry_r32.py
  tests/test_document_evidence_roles_unmet_r32.py
  tests/test_facts_publication_sae_underreport_r31.py
  tests/test_facts_publication_scale_week_anchor_r31.py
  tests/test_mapping_partial_slot_adoption_r31.py
  tests/test_monitoring_ai_queue_dwell_timeout.py -q` → **29 passed**
  （2.27s）。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py -q` →
  **97 passed / 0 failed**（55.14s；R19 起在案的存量偶发失败
  test_late_project_dispatchers_keep_two_actual_api_results_isolated 本轮
  通过，见 §4）。
- 投影连续性（R32 轮语义复测）：本轮 pass1 新 rct overview 实测
  **「日期待确认」0 次**（R31-04 周锚定在役）、「肯定无关」10 次/
  「肯定有关」10 次（R31-05 排除语义在役）；发现/受试者/现行风险计数
  41/16/477 与 R32 恒定——R32 轮改动面未扰动运行投影。

### 4. 观察与边界（不拦链路）

- **存量失败转绿**：test_late_project_dispatchers…（409
  `result_context_unavailable`，tests/
  test_medical_monitoring_r7_product_router.py:2844）在 R19/R31/R32 各轮
  记录为 HEAD 既有失败（stash 对照在案），本轮 97/97 全量绿——该测试为
  HEAD 既有偶发（flake），本轮零源码改动无从归因于任何修复；后续轮次
  如再红按存量偶发口径记录，不再作为新墙证据。
- progress 本轮两遍均 polls=2（首询 running、15s 间隔后二询 completed），
  result_available 首询 false→发布后 registry 终态 1，与 R20/R32 同型
  投影时序（completed 即刻发布尚未完成时的正常投影），非缺陷。
- `/api/projects` 本轮基线实测 4.9s、runs 列表 1.7s（冷启动后首调；
  R32-01 threadpool 下放在役——调用期间后续请求未被阻塞，全链各步
  62–547ms 正常返回）。远低于 R32-01 修复前 43–50s 量级，属 R32-01
  修复后正常波动，非缺陷证据。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径；界面回归归墙破后的测试轮）。

留痕文件：`r33s_siege_repro.py`、`r33s_siege_evidence.jsonl`（两遍全链）、
本日志节。

---

## R32 攻坚·第 1 次（2026-10-10，攻坚工程师-R32-第1次）

### 0. 结论先行

**墙未复发：R31 轮次修复（dc4939ec）+ R31 轮次归档（b3fa0a0c，HEAD）重建
后的新 build（api-f240b1ef669d7a88）下，本轮独立复现两遍全新幂等键全链
全绿，零阻断、零代码改动、零重启。** R31 轮修复触及运行链上游（facts
公布层 R31-04 周锚定/R31-05 SAE 匹配、映射槽位豁免、队列收割视界），新
build 下运行链是否仍通未经验证——本轮按任务①独立复现。常驻项目
「MX循开考-CSU」（proj_user_6ef58ac151e1）以两个全新幂等键各走完
run-setup/options → workspace/bootstrap（留证）→ prepare-and-start →
progress completed → publication available → result-entry →
results/{rct}/overview 可读（两遍投影均 **1,392,075 字节（重序列化口径）
/41 发现/16 受试者/477 现行风险**，逐项一致；较 R31 的 1,392,406 的
-331 字节已核为 dc4939ec facts_publication 合法文本变化，见 §4）。终态
磁盘 43 条全部 completed+result_available=1、**waiting_start=0**，
admission_events 本轮时间窗（02:19–02:21Z）零新增（基线 6 行=终态 6 行，
末条仍为 2026-10-07T22:36:55Z 历史拒绝）。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（Python pid 30554）`/api/health` 200（runtime_store integrity ok,
  schema v16）；`/api/runtime-readiness` ready:true、backend_build_id=
  **api-f240b1ef669d7a88**（R31 攻坚收尾时 api-e1c432cb92f53fd9，其间经
  R31 轮次修复 dc4939ec + 归档 b3fa0a0c 重建重启，ISO_ENV_LOG 2026-10-10
  01:52–02:59 R31修复轮重启留痕（两次 API 重启，dc4939ec 提交内））。5178（vite node pid 21074）**仅绑
  IPv6 [::1]**，`http://[::1]:5178/monitoring` 200；`/runtime-build.json`
  expectedBackendBuildId=api-f240b1ef669d7a88 配对一致
  （frontendBuildId=web-550d10e0866d34f0）。本轮全程未重启。
- 既有修复在新 build 在位（本轮亲读源码提交面 + 实测）：R19
  `ensure_builtin_global_default`（runtime/run_entry.py，调用点
  api/r7_product/run_routes.py prepare_and_start 内）经本轮 prepare-and-
  start 200×2 实证在役；R31 轮 facts_publication 改动画经定向测试
  20/20 在役（§3）。
- 复现前磁盘基线：launch_registry **41 条全部 completed+result_available=1**
  （seq 41=R31 轮次界面键 monitoring_dd862418…，manifest e49f95084811）、
  **waiting_start=0**；execution_profiles `global_default|*|1` 在位；
  admission_events.jsonl 6 行（末条 2026-10-07T22:36:55Z in_flight_conflict
  历史拒绝）。

### 2. 复现（任务①）——两遍全链（驱动 `r32s_siege_repro.py`，证据
`r32s_siege_evidence.jsonl` 50 行、全 ok、0 阻断）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测，
两遍均 200 replayed=true revision=1 幂等零改动）。

**第一遍（02:19:18Z 起，key=r32s-fresh-07db416b8178，链路壁钟 ~17s）**：

| 步骤 | 实测 |
| --- | --- |
| 基线同刻双侧 | mapping-candidates 200（178ms，**candidates_ready**、draft confirmed）、facts 200（65ms，**ready**）、project/open 200（74ms，**current**）、protocol-versions 200（36ms，confirmed）——预置台与运行门无口径差 |
| run-setup/options | 200，164ms，snapshot:ef8692acfbab4d2a9846916f（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，75ms，replayed=true revision=1 |
| prepare-and-start | **200，320ms**，run:651f762178f959fb…（registry sequence 42，manifest_digest f58ccf16c4f3 同源） |
| progress | 首询 running/30%（218ms），二询 **completed**（percent=100.0，polls=2、15s 间隔；result_available 首询 false，发布后终态 1，R20 §4 同型投影时序） |
| publication | POST 200→**available**（618ms） |
| result-entry | 200，275ms，rct=result-context:e044ce805196474ab3ab451b339cdb01 |
| results/{rct}/overview | 200，335ms，**1,392,075 字节（重序列化）、41 发现/16 受试者/477 现行风险**，identity.project_ref=proj_user_6ef58ac151e1 |

**第二遍=重验（任务③，02:19:53Z 起，key=r32s-fresh-4b14e5931e42，壁钟
~17s）**：同链全绿：options 200（175ms，snapshot 同源）→ bootstrap 200
replayed → prepare-and-start **200**（323ms，run:4ddc95b4d53cab17…，
sequence 43，manifest f58ccf16c4f3）→ progress completed（polls=2）→
publication **available**（583ms）→ entry 200（276ms，
rct=result-context:1282b6129d0d482ab283d26dc9ae7dba）→ overview 200
（332ms，**1,392,075 字节、41/16/477**）。两遍序列化字节数逐项一致，
总耗时 35s。

### 3. 修复（任务②）与口径差对照

**无需新修复，本轮零代码改动、零重启。** 两侧口径在本轮无分叉：预置台
（mapping candidates_ready / facts ready / project current / 方案版本
confirmed 在位）与运行启动门（run-setup/options 200 + prepare-and-start
200×2）读数一致；backend_truth() 对照本轮两遍均未触发差异；
admission_events.jsonl 在本轮时间窗（02:19–02:21Z）**零新增**（基线 6 行
=终态 6 行）。

既有修复在役证明（本轮全部亲测）：

- R19/R27：`pytest tests/test_medical_monitoring_r7_product_router.py
  tests/test_medical_monitoring_r27_protocol_gate_selfheal.py -k "r19_siege
  or protocol or selfheal" -q` → **6 passed**（3.73s）。
- R31 轮改动面（本 build 新代码）+ R29 dwell：
  `pytest tests/test_facts_publication_sae_underreport_r31.py
  tests/test_facts_publication_scale_week_anchor_r31.py
  tests/test_mapping_partial_slot_adoption_r31.py
  tests/test_monitoring_ai_queue_dwell_timeout.py -q` → **20 passed**
  （0.70s）。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py
  tests/test_medical_monitoring_r27_protocol_gate_selfheal.py -q` →
  **98 passed / 1 failed**（50.73s；唯一失败
  test_late_project_dispatchers_keep_two_actual_api_results_isolated 为
  R19 起在案存量失败，见 §4）。

### 4. 观察与边界（不拦链路，转台账观察）

- **overview 字节数 1,392,406 → 1,392,075（-331）已核为 R31 轮次修复
  dc4939ec 的合法投影变化**：该提交改 `packages/medical_monitoring/
  projections/facts_publication.py`（+71 行，R31-04 周锚定 + R31-05 SAE
  匹配）。本轮亲测当前 overview 中 **「日期待确认」出现 0 次**（R31-04
  的投诉正是周分值事件 start 恒 None 全落「日期待确认」——现已被周数
  锚定取代），「肯定无关」10 次（R31-05 排除语义的语料在卡文本中正常
  呈现）；发现/受试者/现行风险计数不变（41/16/477），两遍逐项一致——
  非回归信号。
- r7 router 全量唯一失败
  `test_late_project_dispatchers_keep_two_actual_api_results_isolated`
  （409 `result_context_unavailable`，tests/
  test_medical_monitoring_r7_product_router.py:2844）：R19 攻坚已 stash
  对照证实 HEAD 既有、R31 轮次提交记录同口径（96/97「1失败HEAD既有经
  stash对照」）；本轮零源码改动（工作树仅台账/运行时文件 + 本轮新增
  驱动/证据），HEAD 等价，非本轮墙（常驻项目链路两遍全绿）。
- progress 本轮两遍均 polls=2（首询 running/30%，15s 轮询间隔后二询
  completed），与 R30 的 polls=1 差异为轮询时序抖动（run 内部秒级完成 vs
  15s 间隔），非缺陷；result_available 首询 false→发布后 registry 终态
  1，R20 §4 同型投影时序沿台账。
- 5178 本轮实测仅绑 IPv6（[::1]），IPv4 127.0.0.1 连接拒绝；前端页面
  经 [::1]/localhost 均可达（/monitoring 200、指纹配对一致）。浏览器
  本身走 localhost 不受影响，属环境观察非缺陷。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径；界面回归归墙破后的测试轮）。

留痕文件：`r32s_siege_repro.py`、`r32s_siege_evidence.jsonl`（两遍全链）、
本日志节。

---

## R31 攻坚·第 1 次（2026-10-09，攻坚工程师-R31-第1次）

### 0. 结论先行

**墙未复发：R30 攻坚之后的新 build（api-e1c432cb92f53fd9）下，本轮独立
复现两遍全新幂等键全链全绿，零阻断、零代码改动、零重启。** R30 轮次修复
（ac98a4ee：R30-01 身份中间件免清单+移出事件循环+清单物化单次化+60s TTL/
R30-03 来源清单中间态诚实化/R28-05 公开结果四端点移入线程池/R28-08/09/11
前端）+ R30 轮次归档（606fd958）+ 任务所有者解除搁置（4f235507，仅新增
scripts/tester_loop_0927/STATE_V2.json 台账文件，零源码改动，HEAD）重建
重启后，backend_build_id 变为 **api-e1c432cb92f53fd9**（R30 攻坚收尾时
api-0feb76ce663ae085），前端 runtime-build.json expectedBackendBuildId
配对一致（frontendBuildId=web-f829378ee806b096）。常驻项目
「MX循开考-CSU」（proj_user_6ef58ac151e1）以两个全新幂等键各走完
run-setup/options → workspace/bootstrap（留证）→ prepare-and-start →
progress completed → publication available → result-entry →
results/{rct}/overview 可读（两遍投影均 **1,392,406 字节/41 发现/16 受试者
/477 现行风险**，逐字节一致，与 R30 读数完全相同——R30 轮次修复改执行
模型不改投影文本）。终态磁盘 40 条全部 completed+result_available=1、
**waiting_start=0**，admission_events 本轮时间窗（19:58–19:59Z）零新增
（基线 6 行=终态 6 行，末条仍为 2026-10-07T22:36:55Z 历史拒绝）。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（Python pid 64610，今日 21:34 由 R30 修复轮重启，ISO_ENV_LOG
  21:33–21:35 留痕）`/api/health` 200（runtime_store integrity ok,
  schema v16）；`/api/runtime-readiness` ready:true、backend_build_id=
  **api-e1c432cb92f53fd9**。5178（vite node pid 64327，今日 21:33 起）
  `/runtime-build.json` expectedBackendBuildId 配对一致；
  `/monitoring` 200。本轮全程未重启。
- 既有修复在新 build 在位（本轮亲读源码）：R19
  `packages/medical_monitoring/runtime/run_entry.py:377`
  `ensure_builtin_global_default()`，调用点
  `packages/medical_monitoring/api/r7_product/run_routes.py:199`；R27
  `services/api/app/main.py:1205` 与
  `services/api/app/medical_monitoring_router.py:1087`
  `applicability_status="project_effective_confirmed"`。
- 复现前磁盘基线：launch_registry **38 条全部 completed+result_available=1**
  （seq 38=R30 轮次界面键 monitoring_258ac9de…，manifest e49f95084811）、
  **waiting_start=0**；execution_profiles `global_default|*|1` 在位；
  admission_events.jsonl 6 行（末条 2026-10-07T22:36:55Z in_flight_conflict
  历史拒绝）。

### 2. 复现（任务①）——两遍全链（驱动 `r31s_siege_repro.py`，证据
`r31s_siege_evidence.jsonl` 50 行、全 ok、0 阻断）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测，
两遍均 200 replayed=true revision=1 幂等零改动）。

**第一遍（19:58:23Z 起，key=r31s-fresh-de1482ab78e7，链路壁钟 ~17s）**：

| 步骤 | 实测 |
| --- | --- |
| 基线同刻双侧 | mapping-candidates 200（171ms，**state=candidates_ready**）、facts 200（60ms，**state=ready**，summary source_values_verified=3038）、project/open 200（71ms，**state=current**）、protocol-versions 200（35ms，1 条 status=confirmed）——预置台与运行门无口径差 |
| run-setup/options | 200，157ms，snapshot:ef8692acfbab4d2a9846916f（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，73ms，replayed=true revision=1 |
| prepare-and-start | **200，303ms**，run:c005550a8410c4ba5d41c747…（registry sequence 39，manifest_digest f58ccf16c4f3 同源） |
| progress | 首询 running/30%（206ms），二询 **completed**（percent=100.0，polls=2；result_available 首询 false，发布后终态 1，R20 §4/R29 §2/R30 §2 同型投影时序） |
| publication | POST 200→**available**（598ms） |
| result-entry | 200，269ms，rct=result-context:77e85171c0214af3a3b427e1d04e4f29 |
| results/{rct}/overview | 200，327ms，**1,392,406 字节、41 发现/16 受试者/477 现行风险**，identity.project_ref=proj_user_6ef58ac151e1 |

**第二遍=重验（任务③，19:58:41Z 起，key=r31s-fresh-dd1ccea2ccfc，壁钟
~17s）**：同链全绿：options 200（161ms，snapshot 同源）→ bootstrap 200
replayed → prepare-and-start **200**（297ms，run:7b13204bc9d4a2bd16e0bf35…，
sequence 40，manifest f58ccf16c4f3）→ progress completed（polls=2）→
publication **available**（576ms）→ entry 200（308ms，
rct=result-context:bfb286d84a1748698986cf8a96b1584a）→ overview 200
（325ms，**1,392,406 字节、41/16/477**）。两遍序列化字节数逐字节一致，
总耗时 35s。

### 3. 修复（任务②）与口径差对照

**无需新修复，本轮零代码改动、零重启。** 两侧口径在本轮无分叉：预置台
（mapping candidates_ready / facts ready / project current / 方案版本
confirmed 在位）与运行启动门（run-setup/options 200 + prepare-and-start
200）读数一致，R19/R27 修复在役（§1 代码行亲读 + 定向测试）。backend_truth()
对照（同刻快照）两遍装备均未触发；admission_events.jsonl 在本轮时间窗
（19:58–19:59Z）**零新增**（基线 6 行=终态 6 行）。

本 build 相对 R30 攻坚收尾的改动面（ac98a4ee）恰好被本轮实测覆盖：
publication/result-entry/overview 三请求（200×3）走的正是该提交线程池化后的
`packages/medical_monitoring/api/r7_product/publication_routes.py` 路径；
prepare-and-start 走过 `services/api/app/main.py` 身份中间件免清单+TTL 路径
（options/prepare 单请求 157–303ms，无 70–120s 阻塞复现）。

既有修复在役证明（本轮全部亲测）：

- R19/R27：`pytest tests/test_medical_monitoring_r7_product_router.py
  tests/test_medical_monitoring_r27_protocol_gate_selfheal.py -k "r19_siege
  or protocol or selfheal" -q` → **6 passed**（2.68s）。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py
  tests/test_medical_monitoring_r27_protocol_gate_selfheal.py -q` →
  **99 passed**（46.92s；97 路由 + 2 门自愈）。
- R30 轮改动面新增/改动 + R28 读取链集成 + R29 轮次新增：
  `pytest tests/test_project_source_manifest.py
  tests/test_public_result_journey_digest_r28.py
  tests/test_risk_evidence_template_r2810.py
  tests/test_monitoring_ai_queue_dwell_timeout.py -q` → **31 passed**
  （2.39s）。

### 4. 观察与边界（不拦链路，转台账观察）

- overview 字节数与 R30 完全一致（1,392,406），发现/受试者/现行风险计数
  不变（41/16/477）——ac98a4ee 改的是公开结果端点执行模型（async 内同步
  校验+投影移入线程池）、身份/清单路径与前端渲染，未触及投影文本，与读数
  恒定自洽，非回归信号。
- progress 本轮两遍均 polls=2（首询 running/30%，15s 轮询间隔后二询
  completed），与 R30 的 polls=1 差异为轮询时序抖动（run 内部秒级完成 vs
  15s 间隔），非缺陷；result_available 首询 false→发布后 registry 终态 1，
  R20 §4 同型投影时序沿台账。
- seq 38（R30 轮次界面键）manifest e49f95084811 与空规则令牌键
  f58ccf16c4f3 分叉=R28 §4 既有观察（界面规则令牌有效输入不同），本轮未
  触碰，沿台账。
- 证据 JSONL 响应体截断 2500 字符（终态 progress/overview 大响应仅留
  头部；驱动内存中完整解析，终态判定不受影响）。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径；界面回归归墙破后的测试轮）。

留痕文件：`r31s_siege_repro.py`、`r31s_siege_evidence.jsonl`（两遍全链）、
本日志节。

---

## R30 攻坚·第 1 次（2026-10-09，攻坚工程师-R30-第1次）

### 0. 结论先行

**墙未复发：本轮独立复现两遍全新幂等键全链全绿，零阻断、零代码改动、
零重启。** R29 轮次修复（6e8412ce：事件明细锚点 riskSeverityLabel 悬空引用
/队列滞留 dwell 收割/首页建项/请核实事项卡域差异化等）+ R29 轮次归档
（c71bce82，HEAD）重建后，backend_build_id 变为 **api-0feb76ce663ae085**
（R29 攻坚收尾时 api-3cc7a71cf1e003d7），前端 runtime-build.json
expectedBackendBuildId 配对一致（frontendBuildId=web-339d936c48a63787）。
常驻项目「MX循开考-CSU」（proj_user_6ef58ac151e1）以两个全新幂等键各走完
run-setup/options → workspace/bootstrap（留证）→ prepare-and-start →
progress completed → publication available → result-entry →
results/{rct}/overview 可读（两遍投影均 **1,392,406 字节/41 发现/16 受试者
/477 现行风险**，逐字节一致）。读取链字节数较 R29 的 1,249,624 增加
142,782 字节，**已核为 6e8412ce「请核实事项卡注入规则名+事件术语+真实日期
区间+9域差异化核查指向」对每张风险卡 evidence_summary/query_draft 文本的
合法扩写**（packages/medical_monitoring/projections/
product_projection_helpers.py 新增 _DOMAIN_VERIFY_HINTS/_DATE_STATE_TEXT/
_risk_record_clause 并改写 _risk_payload 三段文本；477 卡×~300 字节量级
吻合），发现/受试者/风险计数不变（41/16/477），非回归。终态磁盘 37 条全部
completed+result_available=1、**waiting_start=0**，admission_events 本轮
时间窗零新增（基线 6 行=终态 6 行，末条仍为 2026-10-07T22:36:55Z 历史拒绝）。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（Python pid 20186）`/api/health` 200（runtime_store integrity ok,
  schema v16）；`/api/runtime-readiness` ready:true、backend_build_id=
  **api-0feb76ce663ae085**。5178（vite node pid 19315）`/runtime-build.json`
  expectedBackendBuildId 配对一致；`/monitoring` 200。该 build 晚于 R29
  攻坚收尾的 api-3cc7a71cf1e003d7（期间经 R29 轮次修复 6e8412ce + 归档
  c71bce82 重建，HEAD=c71bce82，工作树仅台账/运行时文件未提交改动）。
  本轮全程未重启。
- 既有修复在新 build 在位（本轮亲读源码）：R19
  `packages/medical_monitoring/runtime/run_entry.py:377`
  `ensure_builtin_global_default()`，调用点
  `packages/medical_monitoring/api/r7_product/run_routes.py:199`；R27
  `services/api/app/main.py:1205` 与
  `services/api/app/medical_monitoring_router.py:1087`
  `applicability_status="project_effective_confirmed"`。
- 复现前磁盘基线：launch_registry **35 条全部 completed+result_available=1**
  （R29 攻坚两条 seq33/34 + R29 轮次界面键 seq35，monitoring_b1fc9150…，
  manifest e49f95084811 与空规则令牌键 f58ccf16c4f3 的分叉=R28 §4 既有
  观察：界面规则令牌有效输入不同）、**waiting_start=0**；execution_profiles
  `global_default|*|1` 在位；admission_events.jsonl 6 行（末条
  2026-10-07T22:36:55Z in_flight_conflict 历史拒绝）。

### 2. 复现（任务①）——两遍全链（驱动 `r30s_siege_repro.py`，证据
`r30s_siege_evidence.jsonl` 48 行、全 ok、0 阻断）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测，
两遍均 200 replayed=true revision=1 幂等零改动）。

**第一遍（03:09:33Z 起，key=r30s-fresh-e8c45113e389，链路壁钟 ~9s）**：

| 步骤 | 实测 |
| --- | --- |
| 基线同刻双侧 | mapping-candidates 200（1139ms，**candidates_ready**）、facts 200（1040ms，**ready**）、project/open 200（1037ms，**current**）、protocol-versions 200（1027ms，status=confirmed）——预置台与运行门无口径差 |
| run-setup/options | 200，1166ms，snapshot:ef8692acfbab4d2a9846916f（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，replayed=true revision=1 |
| prepare-and-start | **200，1315ms**，run:50722ae3e1b3c5e0…（registry sequence 36，manifest_digest f58ccf16c4f3 同源） |
| progress | 首轮询即 completed（percent=100.0，polls=1，run 内部 ~1s；result_available 首轮询 false，发布后终态 1，R20 §4/R29 §2 同型投影时序） |
| publication | POST 200→**available**（1581ms） |
| result-entry | 200，1232ms，rct=result-context:913cf1ca7296446d8c969c4277688bfa |
| results/{rct}/overview | 200，1297ms，**1,392,406 字节、41 发现/16 受试者/477 现行风险** |

**第二遍=重验（任务③，03:09:47Z 起，key=r30s-fresh-f51b05587ba0，壁钟
~9s）**：同链全绿：options 200（1238ms，snapshot 同源）→ bootstrap 200
replayed → prepare-and-start **200**（1296ms，run:7ef6a652830e90fd…，
sequence 37，manifest f58ccf16c4f3）→ progress completed（polls=1）→
publication **available**（1575ms）→ entry 200（1244ms，
rct=result-context:9f3e3229cd354c63a9046b1a5037de14）→ overview 200
（1332ms，**1,392,406 字节、41/16/477**）。两遍序列化字节数逐字节一致，
总耗时 31s。

### 3. 修复（任务②）与口径差对照

**无需新修复，本轮零代码改动、零重启。** 两侧口径在本轮无分叉：预置台
（mapping candidates_ready / facts ready / project current / 方案版本
confirmed 在位）与运行启动门（run-setup/options 200 + prepare-and-start
200）读数一致，R19/R27 修复在役（§1 代码行亲读 + 定向测试）。本驱动
backend_truth() 对照（同刻快照）两遍装备均未触发；admission_events.jsonl
在本轮时间窗（03:09–03:10Z）**零新增**（基线 6 行=终态 6 行）。

既有修复在役证明（本轮全部亲测）：

- R19/R27：`pytest tests/test_medical_monitoring_r7_product_router.py
  tests/test_medical_monitoring_r27_protocol_gate_selfheal.py -k "r19_siege
  or protocol or selfheal" -q` → **6 passed**（2.80s）。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py
  tests/test_medical_monitoring_r27_protocol_gate_selfheal.py -q` →
  **99 passed**（62.43s；97 路由 + 2 门自愈）。
- R28 读取链集成 + R29 轮次新增（本 build 改动面）：
  `pytest tests/test_public_result_journey_digest_r28.py
  tests/test_risk_evidence_template_r2810.py
  tests/test_monitoring_ai_queue_dwell_timeout.py -q` → **14 passed**
  （1.48s）。

### 4. 观察与边界（不拦链路，转台账观察）

- **overview 字节数 1,249,624 → 1,392,406（+142,782）已核为 R29 轮次修复
  6e8412ce 的合法投影变化**：该提交新增 _DOMAIN_VERIFY_HINTS（9 域差异化
  核查指向）、_DATE_STATE_TEXT、_risk_record_clause（事件术语+真实日期
  区间）并改写 evidence_summary 的 basis/finding/action_item 与 query_draft
  四段文本（packages/medical_monitoring/projections/
  product_projection_helpers.py:84-180 区域），且有
  tests/test_risk_evidence_template_r2810.py 5 测试在役（本轮 14 passed
  覆盖）；发现/受试者/现行风险计数不变（41/16/477），两遍逐字节一致——
  非回归信号。
- seq 35（R29 轮次界面键）manifest e49f95084811 与空规则令牌键
  f58ccf16c4f3 分叉=R28 §4 既有观察（界面规则令牌有效输入不同），本轮未
  触碰，沿台账。
- progress 首轮询 `result_available=false` 与 registry 终态 1 的瞬差：
  R20 §4 同型投影时序，发布 available 后一致，两遍均复现，非缺陷。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径；界面回归归墙破后的测试轮）。

留痕文件：`r30s_siege_repro.py`、`r30s_siege_evidence.jsonl`（两遍全链）、
本日志节。

---

## R29 攻坚·第 1 次（2026-10-09，攻坚工程师-R29-第1次）

### 0. 结论先行

**墙未复发：本轮独立复现两遍全新幂等键全链全绿，零阻断、零代码改动、零重启。**
R28 轮次修复（4b9338ca，首次触及结果读取链：读取链整值浮点规范 int + facts
解析保 int + 信封兜底 + failure_class 透出 + AESER=是派生 serious 位）+
R28 轮次归档（a9fa52c2，HEAD）重建后，backend_build_id 变为
**api-3cc7a71cf1e003d7**（R28 攻坚收尾时 api-75f010c43fde3f82），前端
runtime-build.json expectedBackendBuildId 配对一致（frontendBuildId=
web-c15c8dcc41ac30fe）。常驻项目「MX循开考-CSU」（proj_user_6ef58ac151e1）
以两个全新幂等键各走完 run-setup/options → workspace/bootstrap（留证）→
prepare-and-start → progress completed → publication available →
result-entry → results/{rct}/overview 可读（两遍投影均 **1,249,624 字节/
41 发现/16 受试者**，逐字节一致）。读取链字节数较 R25–R28 的 1,241,039
增加 8,585 字节（发现/受试者数不变）——R28 轮次修复对投影/读取链的
合法改动所致（见 §4），两遍自洽。终态磁盘 34 条全部
completed+result_available=1、**waiting_start=0**，admission_events 零新增。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（Python pid 62965，今日 04:57 起，127.0.0.1 IPv4 监听）`/api/health`
  200（runtime_store integrity ok, schema v16）；`/api/runtime-readiness`
  status=ready、backend_build_id=**api-3cc7a71cf1e003d7**。5178（vite node
  pid 62430，今日 04:53 起，**仅 [::1] IPv6 监听**）`/runtime-build.json`
  expectedBackendBuildId **配对一致**；`/monitoring` 200。该 build 晚于
  R28 攻坚收尾时的 api-75f010c43fde3f82（期间经 R28 轮次修复 4b9338ca +
  归档 a9fa52c2 重建，HEAD=a9fa52c2，源码树仅 tester_loop 台账文件有改动）。
  本轮全程未重启。
- 既有修复在新 build 在位（本轮亲读源码）：R19
  `packages/medical_monitoring/runtime/run_entry.py:377`
  `ensure_builtin_global_default()`，调用点
  `packages/medical_monitoring/api/r7_product/run_routes.py:199`；R27
  `services/api/app/main.py:1205` 与
  `services/api/app/medical_monitoring_router.py:1087`
  `applicability_status="project_effective_confirmed"`。
- 复现前磁盘基线：launch_registry **32 条全部 completed+result_available=1**
  （R28 后新增 2 条：R28 轮次界面键 seq 32 + 攻坚两键已含）、waiting_start=0；
  execution_profiles `global_default|*|1` 在位；`GET /protocol-versions` →
  1 条 project_effective_confirmed（protov R27 自愈种入）。种子 attempt
  stg-cd69899943ba42618f589ba07a134a59 仍在（200）。

### 2. 复现（任务①）——两遍全链（驱动 `r29s_siege_repro.py`，证据
`r29s_siege_evidence.jsonl` 52 行、0 阻断）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测，
两遍均 200 replayed=true revision=1 幂等零改动）。

**第一遍（03:29:28Z 起，key=r29s-fresh-d607661a264f，链路壁钟 16s）**：

| 步骤 | 实测 |
| --- | --- |
| 基线双侧 | readiness 200（917ms）；mapping-candidates 200（1100ms，**candidates_ready，draft.status=confirmed**，60 候选）、facts 200（984ms，**ready**，summary 10 表/591 行/3038 值 source_values_verified=3038）、project/open 200（994ms，**current**）、protocol-versions 200（959ms，1 条 confirmed）——预置台与运行门无口径差 |
| run-setup/options | 200，1077ms，snapshot:ef8692acfbab4d2a9846916f（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，1024ms，replayed=true revision=1 |
| prepare-and-start | **200，1232ms**，run:c0da2448a95aca68134448d2…（registry sequence 33，manifest_digest f58ccf16c4f3 同源） |
| progress | 首轮询即 completed（percent=100.0，polls=1；result_available 首轮询 false，发布后终态 1，R20 §4 同型投影时序） |
| publication | POST 200→**available**（1486ms） |
| result-entry | 200，rct=result-context:8e55915d13374890879a2d08e5d1a401 |
| results/{rct}/overview | 200，1242ms，**1,249,624 字节、41 发现/16 受试者**，identity.project_ref=proj_user_6ef58ac151e1 |

**第二遍=重验（任务③，03:30:04Z 起，key=r29s-fresh-7e0c59c1793d，壁钟 16s）**：
同链全绿：options 200（1109ms，snapshot 同源）→ bootstrap 200 replayed →
prepare-and-start **200**（1321ms，run:140af38f16f6b4d1c5c0b49f…，sequence 34）
→ progress completed（polls=1）→ publication **available**（1565ms）→
entry 200（rct=result-context:f488955069154ce695ea4c7e6ad4fdf8）→ overview 200
（1273ms，**1,249,624 字节、41 发现/16 受试者**，chain_ok=True）。两遍序列化
字节数逐字节一致。

### 3. 修复（任务②）与口径差对照

**无需新修复，本轮零代码改动、零重启。** 两侧口径在本轮无分叉：预置台
（mapping confirmed / facts ready / project current / 方案版本
project_effective_confirmed 在位）与运行启动门（run-setup/options 200 +
prepare-and-start 200）读数一致。backend_truth() 对照（mapping/facts/project/
open/protocol-versions 同刻快照）装备未触发（0 阻断）；
admission_events.jsonl 在本轮时间窗（03:29–03:30Z）**零新增**（末条仍为
R27 期 2026-10-07T22:36:55Z 的历史拒绝）。

既有修复在役证明（本轮全部亲测）：

- R19：代码在位（见 §1）；`pytest tests/test_medical_monitoring_r27_protocol_gate_selfheal.py tests/test_medical_monitoring_r7_product_router.py -k "r19_siege or protocol or selfheal" -q` → **6 passed**（2.67s）。
- R27：同上 6 passed 含 selfheal 2/2。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py tests/test_medical_monitoring_r27_protocol_gate_selfheal.py -q` → **99 passed**（43.95s；97 路由 + 2 门自愈）。
- R28 轮次新增读取链集成测试（本 build 改动面）：`pytest tests/test_public_result_journey_digest_r28.py -q` → **4 passed**（1.01s，种子→运行→发布→结果→旅程）。

### 4. 观察与边界（不拦链路，转台账观察）

- **overview 字节数 1,241,039 → 1,249,624（+8,585）已核为 R28 轮次修复的
  合法投影变化**：4b9338ca 触及读取链
  `packages/medical_monitoring/api/r7_product/publication_view_helpers.py`、
  `projections/facts_publication.py`、`projections/product_projection_helpers.py`、
  `projections/product_types.py`（failure_class 透出、AESER=是派生 serious
  位经 medical_note、信封兜底）；发现/受试者计数不变（41/16），两遍逐字节
  一致，R28 集成测试 4/4 绿——非回归信号。
- 5178 本轮观测为**仅 IPv6 [::1] 监听**（R28 期记录为 node 26604，未注明
  栈族）；127.0.0.1:5178 拒连属栈监听族差异，非服务缺陷，`/monitoring`
  经 [::1] 200。
- progress 首轮询 `result_available=false` 与 registry 终态 1 的瞬差：
  R20 §4 同型投影时序，发布 available 后一致，两遍均复现，非缺陷。
- 本轮结论仅覆盖「运行启动→完成→发布→可读」墙；R28 §4 所列（seq 29 指纹
  分叉=界面规则令牌有效输入不同）、R27 §7 / R25 §7 沿台账，本轮未触碰。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径；界面路径的自动收口行为已有 Loop.jsx 代码佐证，R25 §3）。

留痕文件：`r29s_siege_repro.py`、`r29s_siege_evidence.jsonl`（两遍全链）、
本日志节。

---

## R28 攻坚·第 1 次（2026-10-09，攻坚工程师-R28-第1次）

### 0. 结论先行

**墙未复发：本轮独立复现两遍全新幂等键全链全绿，零阻断、零代码改动、零重启。**
R27 攻坚修复（eae38b14）与 R27 轮次修复（9f5f8101）之后的新 build
（backend_build_id=**api-75f010c43fde3f82**，前端 expectedBackendBuildId 配对一致）下，
常驻项目「MX循开考-CSU」（proj_user_6ef58ac151e1）以两个全新幂等键各走完
run-setup/options → workspace/bootstrap（留证）→ prepare-and-start →
progress completed → publication available → result-entry →
results/{rct}/overview 可读（两遍投影均 **1,241,039 字节/41 发现/16 受试者**，
逐字节一致，与 R25/R26/R27 绿路径同源）。R19/R27 修复在新 build 在役：
代码亲读在位、回归亲测绿。终态磁盘 31 条全部 completed+result_available=1、
**waiting_start=0**。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（pid 26563，127.0.0.1 IPv4 监听）`/api/health` 200（runtime_store
  integrity ok, schema v16）；`/api/runtime-readiness` status=ready、
  backend_build_id=**api-75f010c43fde3f82**，与 5178（node pid 26604）
  `runtime-build.json` expectedBackendBuildId **配对一致**
  （frontendBuildId=web-1f04fb05696a5e24）。该 build 晚于 R27 攻坚收尾时的
  api-8f8b335e0cdb6221（期间经 R27 轮次修复 9f5f8101 + 归档 4e7fbade 重建，
  HEAD=4e7fbade，源码树 clean，仅 tester_loop 台账文件有未提交改动）。
  本轮全程未重启。
- 既有修复在新 build 在位（本轮亲读源码）：
  `packages/medical_monitoring/runtime/run_entry.py:378`
  `ensure_builtin_global_default()`（R19），调用点
  `packages/medical_monitoring/api/r7_product/run_routes.py:199`
  （`registry.reserve()`（:222）之前）；`services/api/app/main.py:1205` 与
  `services/api/app/medical_monitoring_router.py:1087`
  `applicability_status="project_effective_confirmed"`（R27）。
- 复现前磁盘基线：launch_registry **29 条全部 completed+result_available=1**、
  waiting_start=0、completed 未发布=0；execution_profiles
  `global_default|*|1` 在位；`GET /protocol-versions` → 1 条 confirmed
  （protov_d952458e…，applicability_status=project_effective_confirmed，
  R27 自愈种入那条，非手工）。种子 attempt
  stg-cd69899943ba42618f589ba07a134a59 仍在（200，profile_ready）。

### 2. 复现（任务①）——两遍全链（驱动 `r28s_siege_repro.py`，证据
`r28s_siege_evidence.jsonl` 50 行、0 阻断）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测，
两遍均 200 replayed=true revision=1 幂等零改动）。

**第一遍（22:54:55Z 起，key=r28s-fresh-b899f11e021c，链路壁钟 14s）**：

| 步骤 | 实测 |
| --- | --- |
| 基线双侧 | mapping-candidates 200（1063ms，**candidates_ready，confirmation_status=confirmed**，顶层 facts_generated=false 为 R25 §7 已录投影怪癖）、facts 200（945ms，**ready**，10 表/591 行/3038 值 100% 往返核验）、project/open 200（951ms，**current**）、protocol-versions 200（921ms，1 confirmed）、runs 200——预置台与运行门无口径差 |
| run-setup/options | 200，1016ms，snapshot:ef8692acfbab4d2a9846916f（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，968ms，replayed=true revision=1 |
| prepare-and-start | **200，1159ms**，run:ffbc38bcc47ddfe063aeccca…（registry sequence 30，manifest_digest 回到 f58ccf16c4f3 同源） |
| progress | 首轮询即 completed（percent=100.0，polls=1；result_available 首轮询 false，发布后终态 1，R20 §4 记录的同型投影时序） |
| publication | POST 200→**available**（1418ms） |
| result-entry | 200，rct=result-context:f20e389cda3f4ca5a3b6c2a9bdcff3e4 |
| results/{rct}/overview | 200，1184ms，**1,241,039 字节、41 发现/16 受试者**，identity.project_ref=proj_user_6ef58ac151e1 |

**第二遍=重验（任务③，22:55:25Z 起，key=r28s-fresh-c28a51ab12c1，壁钟 15s）**：
同链全绿：options 200（1161ms，snapshot 同源）→ bootstrap 200 replayed →
prepare-and-start **200**（1217ms，run:794b65200ce0385d585714c4…，sequence 31）
→ progress completed（polls=1）→ publication **available**（1457ms）→
entry 200（rct=result-context:f7a1e4bb9fdc4ea595dc7111612e4894）→ overview 200
（1221ms，**1,241,039 字节、41 发现/16 受试者**，chain_ok=True）。两遍序列化
字节数与 R25/R26/R27 五读（1,241,039）**逐字节一致**。

### 3. 修复（任务②）与口径差对照

**无需新修复，本轮零代码改动、零重启。** 两侧口径在本轮无分叉：预置台
（mapping confirmed / facts ready / project current / 方案版本 confirmed 在位）
与运行启动门（run-setup/options 200 + prepare-and-start 200）读数一致。
本轮若复现 422/409/卡「等待开始」，对照方案为驱动内 `backend_truth()`
（mapping/facts/project/open/protocol-versions 同刻快照，较 R26 驱动新增
protocol-versions——上一道墙 R27 正是该门）——已装备但未触发（0 阻断）。

既有修复在役证明（本轮全部亲测）：

- R19：代码在位（见 §1）；`pytest tests/test_medical_monitoring_r27_protocol_gate_selfheal.py tests/test_medical_monitoring_r7_product_router.py -k "r19_siege or protocol or selfheal" -q` → **6 passed**（2.33s）。
- R27：同上 6 passed 含 selfheal 2/2（门经自愈种入合法枚举并放行 / 无方案docx 时保持 fail-closed）。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py tests/test_medical_monitoring_r27_protocol_gate_selfheal.py -q` → **99 passed**（43.41s；97 路由 + 2 门自愈）。

### 4. 观察与边界（不拦链路，转台账观察）

- **sequence 29 的 manifest_digest 分叉已核非缺陷**：该条为 R27 归档后界面键
  监查（monitoring_ad43781e…，2026-10-08T18:22Z，mode=daily/full 与我两遍
  相同），digest e49f95084811 与历史 f58ccf16c4f3 不同——亲读 registry 行：
  其 `rule_tokens_json=["rule-revision:5d00d4ce2f2622ce11b3d029"]`（界面勾选
  规则修订令牌），而我两遍 `risk_rule_tokens: []`（默认规则集）——**有效输入
  不同故 manifest 不同**，属正常语义；该运行自身 completed+available 收口。
- progress 首轮询 `result_available=false` 与 registry 终态 1 的瞬差：R20 §4
  同型投影时序，发布 available 后一致，两遍均复现，非缺陷。
- 本轮结论仅覆盖「运行启动→完成→发布→可读」墙；R27 §7 所列（自愈种入的
  version_date/operational_effective_from 兜底 1970-01-01、双副本自愈待收敛、
  version_label 截断上限 200 vs 80）、R25 §7 所列（409 文案语义偏差、
  candidates 投影怪癖、偶发 10-22s 慢调用家族）沿台账，本轮未触碰。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径；界面路径的自动收口行为已有 Loop.jsx 代码佐证，R25 §3）。

留痕文件：`r28s_siege_repro.py`、`r28s_siege_evidence.jsonl`（两遍全链）、
本日志节。

---

## R27 攻坚·第 1 次（2026-10-08，攻坚工程师-R27-第1次）

### 0. 结论先行

**墙以第三种形态复发：R26-05 新方案版本门（409 `protocol_version_required`）
拦死常驻项目，其内建自愈因非法枚举值是死代码——已核验方案docx的项目不存在
任何用户可达的方案版本确认路径，被永久拦在启动门外。** 最小根因修复（2 行：
两处自愈的 `applicability_status="active"` → `"project_effective_confirmed"`，
commit eae38b14）+回归测试（修复前红/修复后绿）+8911/5178 标准重启
（新指纹 api-8f8b335e0cdb6221 配对一致）后，同项目两遍全新幂等键全链绿
（completed→available→可读，投影 1,241,039 字节/41 发现/16 受试者，与
R25/R26 三读逐字节一致）。未跳门：项目状态由修复后的设计自愈路径
（R22-01 语义）真实补齐。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（pid 87131，127.0.0.1 IPv4 监听）`/api/health` 200（schema v16）；
  `/api/runtime-readiness` ready、backend_build_id=**api-272b43c31e966e99**
  （R26 攻坚时 api-589520532fc5317d；期间经 R26 轮次修复 e2772c4a——R26-01..05
  +R24-01——重建并已由 R27D 守护员 17:41Z 复验三条件配对一致），
  与 5178（vite node pid 87162，仅监听 [::1]:5178）`runtime-build.json`
  expectedBackendBuildId 配对一致（frontendBuildId=web-5c52de3cbd52918c）。
- R19 修复在新 build 在位（本轮亲读源码）：`packages/medical_monitoring/
  runtime/run_entry.py:377` `ensure_builtin_global_default()`、调用点
  `api/r7_product/run_routes.py:199`（reserve 之前）。
- 复现前磁盘基线：launch_registry 26 条全部 completed+result_available=1、
  manifest_digest 统一 f58ccf16c4f3、waiting_start=0（seq 25/26 为界面键
  monitoring_*，R26 轮次后角色所启动，已收口）；execution_profiles
  `global_default|*|1` 在位。

### 2. 复现（任务①）——第一遍即 BLOCKED（驱动 `r27s_siege_repro.py`，
证据 `r27s_siege_evidence.jsonl` 前段）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测，
200 replayed=true revision=1 幂等零改动）。17:50:50Z
（key=r27s-fresh-e6f117fbef09）：

| 步骤 | 实测 |
| --- | --- |
| 基线双侧 | mapping-candidates 200（1004ms，candidates_ready，confirmed）、facts 200（899ms，**ready**）、project/open 200（903ms，**current**）、runs 200——预置台全绿 |
| run-setup/options | 200，979ms，snapshot:ef8692acfbab4d2a9846916f（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，902ms，replayed=true revision=1 |
| prepare-and-start | **409 `{"code":"protocol_version_required","message":"先完成方案版本确认：当前项目尚无已确认且可解析的方案版本……"}`，2566ms** |
| 被拒同刻后端真实状态 | mapping 200（1023ms，candidates_ready）/ facts 200（916ms，ready）/ project/open 200（919ms，current）——**预置台口径与运行门口径当场分叉** |
| 磁盘 launch_registry | 26 条全部 completed（复现前基线），无 waiting_start；`GET /protocol-versions` → **items=[]** |

### 3. 根因（两侧口径差钉到代码行）

口径差本质：**接入管线侧 candidates_ready/ready/current 全部为真，运行启动门
拒的是「方案版本列表为空」；而补齐它的唯一自动路径（自愈）因传了非法枚举值
必然抛错、被静默吞掉——自愈是死代码，前端又没有手动确认路径**：

1. `packages/medical_monitoring/api/r7_product/run_routes.py:142-149`
   （R26-05 门，e2772c4a 引入）：`context.protocol_version_gate(canonical)`
   命中即 409 `protocol_version_required`。门本身语义正确（fail-closed，
   无方案依据的运行不得产出医学结论），本轮**不动门**。
2. `services/api/app/main.py:1204-1245`（修复前行号）`_r7_protocol_version_gate`：
   `_has_confirmed_version()`（:1218-1223，查 protocol-versions 列表
   status=confirmed）为假 → 调自愈（:1236）→ `except Exception: pass`
   （**:1237-1239**，静默吞）→ 再判仍假 → 409（:1242+）。
3. 自愈本体 `services/api/app/main.py:1164-1201`
   `_auto_register_confirmed_protocol_version`：调用
   `authoring.register_protocol_version(...)` 时传
   **`applicability_status="active"`（修复前 :1196）**——非法值。合法枚举仅
   `version_date_only / project_effective_confirmed / site_specific`
   （`monitoring_protocol_rules.py:13-17`），`ProtocolSourceVersion.create`
   于 `monitoring_protocol_rules.py:1182` 经 `_validate_enum`
   （**:410-415**）必抛 `MonitoringProtocolRuleError` → 被第 2 条的
   except 吞掉。**自愈自引入起一次都不能成功。**
4. 同一缺陷的第二副本：`services/api/app/medical_monitoring_router.py:1077-1094`
   GET `/protocol-versions` 的 R22-01 抽屉自愈，同样传 `"active"`
   （修复前 :1084）+ 同样的 `except Exception: pass`（修复后 :1095）——抽屉恒空。
5. **用户可达路径缺失**：前端对 `/protocol-versions` 只有 GET
   （`frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs:50`），
   `frontend/src` 零处调用 POST `/protocol-versions`
   （medical_monitoring_router.py:1141 注册端点无前端调用方）——门文案
   「请前往『方案事实与规则发布』确认方案版本」对用户实际不可达。
6. 缺陷引入点：git blame 两处 `"active"` 均为 e2772c4a（R26 轮修复提交，
   2026-10-08）；门也是该提交新增——**门上线即带死自愈**，R27D 守护员
   17:41Z 预检未探运行门故未发现。
7. R19/R25 修复与本案正交且仍在役：本轮 global_default 在位（422 未复现）、
   复现前无 in-flight 遗留（409 in_flight_conflict 未复现）。

### 4. 修复（任务②，最小根因修复，2 行 + 注释，不跳门）

`"active"` 的语义意图是「项目级生效中」，对应合法枚举
`project_effective_confirmed`（且 `create()` 要求的
`operational_effective_from` 两处调用本就传入——该参数仅在
project_effective_confirmed 下生效；`current_published_pack`
（`monitoring_protocol_rule_repository.py:2368+`）解析规则包也只认
project_effective_confirmed 版本）：

- `services/api/app/main.py`：`_auto_register_confirmed_protocol_version`
  的 `applicability_status="active"` → `"project_effective_confirmed"`
  （附 R27 攻坚注释：非法枚举→必抛→被吞→409 死锁成因与取值论证）。
- `services/api/app/medical_monitoring_router.py`：R22-01 抽屉自愈同步修正
  （同因同修，抽屉自愈恢复工作——修复后实证：GET protocol-versions 即种入
  `protov_d952458e7f816a46e614f900`，status=confirmed、
  applicability_status=project_effective_confirmed、源
  src_proj_user_6ef58ac151e1_protocol_docx_b6e1bceb269c）。

回归测试（`tests/test_medical_monitoring_r27_protocol_gate_selfheal.py`，
沙箱驱动真实 `_r7_protocol_version_gate`）：

- `test_r27_gate_self_heal_registers_confirmed_version_and_passes`：
  已登记+内容校验通过（parsed/ready/allowed）的方案docx 上，门必须经自愈
  种入 confirmed 版本并放行（返回 None），版本注册值须为合法枚举且
  幂等（二次过门不重复注册）。**git stash 修复后该测试红**（门吞异常后
  返回 409 dict），恢复修复后绿——红/绿均本轮亲测。
- `test_r27_gate_still_fails_closed_without_parsed_protocol_docx`：
  无方案docx 来源时门保持 fail-closed 409——修复不得放宽门禁。

套件：新文件 2/2 绿（1.51s）；`tests/test_medical_monitoring_r7_product_router.py`
**97 passed**（44.32s，含 R19 siege 2/2、R26-05 门禁正反用例）；
`tests/test_monitoring_protocol_rule_api.py` +
`tests/test_medical_monitoring_module_contract.py` **99 passed**（3.73s）；
`-k "r19_siege or protocol"` 4 passed；`test_monitoring_protocol_rule_real_my008.py`
1 passed。

提交：eae38b14『测试循环R27攻坚: 修复R27-01方案版本门自愈死代码……』
（修复+测试+本轮驱动/诊断/证据脚本），提交在重启之前。

### 5. 重启（标准命令，只动 8911/5178）

- 8911：kill `lsof -ti:8911`（87131）→ uvicorn
  （WORKBENCH_RUNTIME_DIR=runs/tester_loop_iso_20260928/runtime、
  WORKBENCH_LOCAL_SINGLE_USER=1、WORKBENCH_AI_RUNTIME=api、
  WORKBENCH_MONITORING_AI_PARALLELISM=2）→ **pid 93624**。
- 5178：kill `lsof -ti:5178`（87162）→ vite
  （VITE_API_PROXY_TARGET=http://127.0.0.1:8911）→ **pid 93671**。
- 三条件自检全过：① `/api/runtime-readiness` ready、
  backend_build_id=**api-8f8b335e0cdb6221**（services 改动后新指纹，
  实证修复已加载）；② `http://localhost:5178/monitoring` 200；
  ③ runtime-build.json expectedBackendBuildId=api-8f8b335e0cdb6221
  配对一致（frontendBuildId=web-5c52de3cbd52918c 不变，前端源未动）。

### 6. 重验（任务③，同项目 MX循开考-CSU，两遍全新幂等键全链）

**第一遍（18:08:07Z，key=r27s-fresh-3f7925e9aff4，链路壁钟 12s）**：

| 步骤 | 实测 |
| --- | --- |
| 基线双侧 | mapping 200（964ms，candidates_ready，confirmed）、facts 200（876ms，ready）、project/open 200（894ms，current）、runs 200 |
| run-setup/options | 200，1030ms，snapshot:ef8692acfbab4d2a9846916f |
| workspace/bootstrap（留证） | 200，883ms，replayed=true revision=1 |
| prepare-and-start | **200，1067ms**，run:fb08220896efc848a13b125a…（registry sequence 27）——修复前同刻 409 的同端点 |
| progress | 首轮询即 completed（percent=100.0，polls=1；result_available 首轮询 false，发布后终态 1，R20 §4 同型投影时序） |
| publication | POST 200 → **available**（1362ms） |
| result-entry | 200，rct=result-context:1e25d1a6081b4d24aa4aeb41f3481bf1 |
| results/{rct}/overview | 200，1101ms，**1,241,039 字节、41 发现/16 受试者**，与 R25/R26 三读逐字节一致 |

**第二遍=复验（key=r27s-fresh-e9d0d0e3af54，壁钟 13s）**：全绿——options 200
（935ms，snapshot 同源）→ bootstrap 200 replayed → prepare-and-start **200**
（1106ms，run:cf20c1f07413153e509a1733…，sequence 28）→ progress completed
（polls=1）→ publication **available**（1359ms）→ entry 200
（rct=result-context:e702a7caed3e4c48905b1adcba36663c）→ overview 200
（1303ms，1,241,039 字节、41 发现/16 受试者，chain_ok=True）。

终态磁盘：sequence 1-28 全部 completed+result_available=1、manifest_digest
统一 f58ccf16c4f3、**waiting_start=0**（本轮新增 27/28 两行）；方案版本列表
1 条 confirmed（自愈种入，非手工/非脚本直写）。

### 7. 遗留与边界（转台账，不属本轮墙判据）

- 自愈种入的 `version_date/operational_effective_from` 均为兜底
  1970-01-01（`getattr(latest, "registered_at", "")` 取不到值——
  SourceRegistryEntry 无该属性名，实为 created_at）：不拦门、语义可用，
  但日期失真，转台账提请修复员核字段名。
- 两处自愈逻辑（main.py 与 medical_monitoring_router.py）仍是复制粘贴
  双副本（历史上已三次同向修），转台账建议收敛为单一共享实现。
- `version_label` 截断上限不一致：调用方 `[:200]` vs 契约
  `max_length=80`（ProtocolVersionAuthoringRequest 是路由层的约束，
  create() 同为 80）——超长文件名标题会在自愈处必抛，同属「自愈静默死」
  家族的潜在复发点，转台账。
- R25 §7 所列 409 文案语义偏差（completed+未发布场景）、candidates 投影
  怪癖、偶发 10-22s 慢调用家族：沿台账，本轮未触碰。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径；界面路径的自动收口行为已有 Loop.jsx:1060-1065 代码佐证，R25 §3）。

留痕文件：`r27s_siege_repro.py`、`r27s_gate_diagnose.py`（沙箱钉根因）、
`r27s_siege_evidence.jsonl`（409 复现+两遍全链）、本日志节。

---

## R26 攻坚·第 1 次（2026-10-08，攻坚工程师-R26-第1次）

### 0. 结论先行

**墙未复发：本轮独立复现两遍全链全绿，零阻断、零代码改动、零重启。**
R19 根因修复（cbb5f52e）在当前新 build（backend_build_id=**api-589520532fc5317d**；
R25 攻坚时为 api-157c89f897d07331，期间经 R25 四项修复 f74c3946、单轮制v2加固
5a22b00d 重建）下亲测仍在役：代码两处都在位（`run_entry.py:377`
ensure_builtin_global_default、`run_routes.py:183` reserve 前接入点）、R19 回归
2/2 绿、全量路由套件 95/95 绿。常驻项目「MX循开考-CSU」（proj_user_6ef58ac151e1）
以两个全新幂等键各走完 run-setup/options → workspace/bootstrap（留证）→
prepare-and-start → progress completed → publication available →
result-entry → results/{rct}/overview 可读。R25 §5 的收口终态（22 条全部
completed+result_available=1）在本轮复现前完整保持，单运行窗口无遗留占用。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（pid 20020，127.0.0.1 IPv4 监听）`/api/health` 200
  （runtime_store integrity ok, schema v16）；`/api/runtime-readiness`
  status=ready、backend_build_id=**api-589520532fc5317d**，与 5178
  （vite node pid 20086，仅监听 [::1]:5178）`runtime-build.json`
  expectedBackendBuildId **配对一致**（frontendBuildId=web-f8b8094c1a14837e）。
  本轮全程未重启。
- R19 修复在新 build 在位（本轮亲读源码）：
  `packages/medical_monitoring/runtime/run_entry.py:377`
  `ensure_builtin_global_default()`；调用点 `packages/medical_monitoring/api/r7_product/run_routes.py:183`，
  仍在 `registry.reserve()` 之前、补种失败 fail-closed 无预约落库。
- 复现前磁盘基线：launch_registry 22 条全部 completed+result_available=1、
  manifest_digest 统一 f58ccf16c4f3、**waiting_start=0**（R25 收口 seq 19 之后
  新增 sequence 22 `monitoring_a42de239`（2026-10-07T22:56Z 界面键，R25 攻坚后
  轮次角色所启动，亦已收口））；execution_profiles `global_default|*|1` 在位。

### 2. 复现（任务①）——两遍全链（驱动 `r26s_siege_repro.py`，证据
`r26s_siege_evidence.jsonl` 44 行、0 阻断）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测，
200 replayed=true revision=1 幂等零改动）。

**第一遍（03:57:14Z，key=r26s-fresh-d5e6381277cc，链路壁钟 11s）**：

| 步骤 | 实测 |
| --- | --- |
| 基线双侧 | mapping-candidates 200（861ms，candidates_ready，confirmed）、facts 200（758ms，**ready**，10 表/591 行/3038 值）、project/open 200（778ms，**current**/edit/canEdit）、runs 200——预置台与运行门无口径差 |
| run-setup/options | 200，820ms，snapshot:ef8692acfbab4d2a9846916f（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，778ms，replayed=true revision=1 |
| prepare-and-start | **200，938ms**，run:5dc9dd46939d7abd1a3eaf53（registry sequence 23） |
| progress | 首轮询即 completed（percent=100.0，polls=1；result_available 首轮询 false，发布后终态 1，R20 §4 记录的同型投影时序） |
| publication | POST 200→**available**（1,217ms） |
| result-entry | 200，rct=result-context:4a20b647000f4d86a8c5c98eb0074f3d |
| results/{rct}/overview | 200，1,012ms，序列化 1,241,039 字节，**41 发现/16 受试者**，identity.project_ref=proj_user_6ef58ac151e1 |

**第二遍=重验（任务③，03:58Z 起，key=r26s-fresh-738d13bc7207，壁钟 39s）**：
同链全绿：options 200（840ms，snapshot 同源）→ bootstrap 200 replayed →
prepare-and-start **200**（953ms，run:cad11f1b081c4fa59c6dee2c，registry
sequence 24）→ progress completed（polls=1）→ publication **available**
（1,279ms）→ entry 200（rct=result-context:a86900ddbf1f4a08b669950d94bdc1b6）
→ overview 200（991ms，**1,241,039 字节、41 发现/16 受试者**，chain_ok=True）。
两遍序列化字节数与 R25 两遍+seq 19 收口三读（1,241,039）**逐字节一致**。

### 3. 修复（任务②）与口径差对照

**无需新修复，本轮零代码改动、零重启。** 两侧口径在本轮无分叉：预置台
（mapping confirmed / facts ready / project current）与运行启动门
（run-setup/options 200 + prepare-and-start 200）读数一致。本轮若复现
422/409/卡「等待开始」，对照方案为驱动内 `backend_truth()`（mapping/facts/
project/open 同刻快照）——已装备但未触发（0 阻断）。R25 攻坚确认的
单运行窗口语义（completed+未发布也算 in-flight，launch_registry_core_mixin.py
既有产品语义）本轮无遗留命中：复现前 22 条全部已收口，两个新键均直接通过。

R19 修复在新 build 在役证明（本轮亲测）：

- 代码在位：`packages/medical_monitoring/runtime/run_entry.py:377`
  `ensure_builtin_global_default()`（仅缺失时幂等种入）；
  `packages/medical_monitoring/api/r7_product/run_routes.py:183`
  prepare-and-start 在 reserve 之前调用（补种失败 fail-closed 且无预约落库）。
- `pytest tests/test_medical_monitoring_r7_product_router.py -k r19_siege
  -q` → **2 passed**（1.00s）。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py -q` →
  **95 passed**（42.45s）。

### 4. 终态与边界

- 终态磁盘：sequence 1-24 全部 completed+result_available=1、manifest_digest
  统一 f58ccf16c4f3、**waiting_start=0**（本轮新增 23/24 两行，registry
  created→updated 各约 1s）。
- 第二遍基线出现两笔慢调用（mapping-candidates 13,976ms / facts 9,814ms，
  首读后同端点恢复 ~0.8s）——与 R25 §7 记录的偶发 10-22s 慢调用家族同型，
  未拦链路，继续台账观察。
- 本轮结论仅覆盖「运行启动→完成→发布→可读」墙；R25 §7 所列 409 文案语义
  偏差、candidates 投影怪癖（facts_generated=False 顶层键与权威终态不一致）
  等属测试循环排期项，不属本攻坚墙判据。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径；界面路径的自动收口行为已有 Loop.jsx 代码佐证，见 R25 §3）。

留痕文件：`r26s_siege_repro.py`、`r26s_siege_evidence.jsonl`、本日志节。

---

## R25 攻坚·第 1 次（2026-10-08，攻坚工程师-R25-第1次）

### 0. 结论先行

**墙以新形态复发一次：遗留「completed+未发布」诊断运行占用单运行窗口，
全新幂等键 prepare-and-start 被 409 in_flight_conflict 拒（969ms）。**
根因不在 R19 修复失效（其两处代码在新 build 仍在役、回归 2/2 绿），而是
R24 轮次角色留下的 API 驱动诊断运行（registry seq 19
`diag-r18-03-gate-check-002`）止步于发布收口之前，命中
`launch_registry_core_mixin.py:326-340` 既有单运行窗口语义
（`run_state='completed' AND result_available=0` 也算 in-flight，blame
5f1a071a）。**最小根因处置=用与界面完全相同的设计端点把该遗留运行收口
（POST publication → available、result_available=1、其结果自身可读），
零代码改动、零重启、不跳门**；随后两遍全新幂等键全链皆绿
（completed→available→可读，投影逐字节一致 1,241,039B/41 发现/16 受试者）。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（pid 74159，127.0.0.1 IPv4 监听）`/api/health` 200
  （runtime_store integrity ok, schema v16）；`/api/runtime-readiness`
  status=ready、backend_build_id=**api-157c89f897d07331**（R24 攻坚时为
  api-06744bbced9d86a2；期间经 R24 六项修复 commit 117657f6 重建），
  与 5178（vite node pid 74210，仅监听 [::1]:5178，属 R24 记录的监听
  布局）`runtime-build.json` expectedBackendBuildId **配对一致**
  （frontendBuildId=web-61cf3eec89de9bcb）。本轮全程未重启。
- R19 修复在新 build 在位（本轮亲读源码）：
  `packages/medical_monitoring/runtime/run_entry.py:377`
  `ensure_builtin_global_default()`；调用点因 117657f6 增补代码自 :166
  移至 `api/r7_product/run_routes.py:183`，仍在 `registry.reserve()`
  （run_routes.py:207）之前、补种失败 fail-closed 无预约落库。
- 复现前磁盘基线：launch_registry 19 条（18 条 completed+result_available=1；
  **sequence 19 `diag-r18-03-gate-check-002` completed+result_available=0**，
  created 2026-10-07T21:52:13Z、updated 22:32:54Z，R24 轮次角色的 R18-03
  门禁核查诊断运行）、waiting_start=0；execution_profiles
  `global_default|*|1` 在位。

### 2. 复现（任务①）——第一遍即 BLOCKED（驱动 `r25s_siege_repro.py`，
证据 `r25s_siege_evidence.jsonl` 前段）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测，
200 replayed=true revision=1 幂等零改动）。第一遍 22:36:48Z
（key=r25s-fresh-778f7877dc91）：

| 步骤 | 实测 |
| --- | --- |
| 基线双侧 | mapping-candidates 200（869ms，candidates_ready）、facts 200（779ms，**ready**）、project/open 200（796ms，**current**）、runs 200——预置台全绿 |
| run-setup/options | 200，839ms，snapshot:ef8692acfbab4d2a9846916f（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，897ms，replayed=true revision=1 |
| prepare-and-start | **409 `{"code":"in_flight_conflict","message":"当前已有监查正在进行，请先查看本次进度"}`，969ms** |
| 被拒同刻后端真实状态 | mapping 200（1045ms，candidates_ready）/ facts 200（825ms，ready）/ project/open 200（828ms，current）——**预置台口径与运行门口径当场分叉** |
| 磁盘 launch_registry | 19 条全部 completed（含 seq 19 result_available=0），无 waiting_start |

### 3. 根因（两侧口径差钉到代码行）

口径差本质：**接入管线侧 candidates_ready/ready/current 全部为真，运行
启动门拒的是注册表里一条「已完成但从未发布」的遗留运行**：

1. `packages/medical_monitoring/runtime/launch_registry_core_mixin.py:326-340`
   `_find_in_flight_locked` 的 SQL 含
   `OR (launch.run_state = 'completed' AND launch.result_available = 0)`
   ——completed+未发布也算 in-flight（git blame 5f1a071a，2026-09-02
   既有产品语义：单运行窗口**包含结果发布收口**，不是本轮新代码）。
2. `launch_registry_core_mixin.py:601-604` `reserve()` 前的
   `enforce_in_flight` 命中即抛 `in_flight_conflict` →
   prepare-and-start 409（run_routes.py reserve 调用点）。
3. 遗留成因：界面路径本会自动收口——
   `frontend/src/features/medical-monitoring/MedicalMonitoringProductLoop.jsx:1060-1065`
   轮询到 `runState=completed && publicationState=not_started` 即调
   `api.publishResult`（幂等键 `result-publication:{token}`）；而 seq 19
   是 R24 轮次角色的 **API 驱动**诊断运行（diag-r18-03-gate-check-002，
   复核其 publication_state=not_started、"分析已结束，结果整理未完成"），
   止步于发布前，无人再走收口 → 常驻项目单运行窗口被永久占用，拦住
   后续**所有**新幂等键（与 R19 僵尸同型的「自我强化」，只是形态从
   waiting_start 换成 completed+未发布）。
4. R19 修复与本案正交且仍在役：本轮 global_default 在位、422 未复现。

### 4. 处置（任务②，最小根因收口，非代码改动）

单运行窗口语义（5f1a071a）是设计门禁而非缺陷，**不跳门、不改注册表
状态位**；遗留运行的**设计收口路径**存在且对监查用户可达
（`api/r7_product/publication_routes.py:122` POST
`/runs/{public_run_token}/publication`，READ_AI_RUN 权限、按运行指纹
幂等——与界面 publishResult 同端点同语义）。执行
`r25s_close_leftover.py`（证据 c* 系列事件）：

- 收口前双侧：GET publication 200 publication_state=**not_started**；
  磁盘 seq 19 completed+result_available=0。
- POST publication（幂等键 r25s-closure-diag-r18-03-002）→ 200，
  **21,130ms → publication_state=available**。
- 磁盘复核：seq 19 **result_available=1**（22:46:37Z）。
- 该遗留运行自身结果可读留证：result-entry 200 →
  rct=result-context:b04ed8f0a5af4e24855f7f1eaac26e91 →
  overview 200，1,241,039 字节。

### 5. 重验（任务③，同项目 MX循开考-CSU，两遍全新幂等键全链）

**第一遍（22:47:31Z，key=r25s-fresh-641f06e0e9b9）**：options 200（822ms，
snapshot 同源）→ bootstrap 200 replayed → prepare-and-start **200**
（1,002ms，run:282cccabd8db2cb10ccb2bc2，registry seq 20）→ progress
**completed**（percent=100.0，polls=1；result_available 首轮询 false，
发布后终态 1，R20 §4 已记录的同型投影时序）→ publication **available**
（1,205ms）→ result-entry 200（rct=result-context:979e834ff18a4589…
）→ overview 200（16,386ms 首读，**1,241,039 字节、41 发现/16 受试者**，
identity.project_ref=proj_user_6ef58ac151e1），链路壁钟 47s。

**第二遍=重验（22:48:07Z 起，key=r25s-fresh-e55c16ceabe8）**：全绿壁钟
16s：prepare-and-start 200（1,019ms，run:13b8e67b5487ecfefd927bd9，
registry seq 21）→ progress completed → publication **available**
（1,264ms）→ entry 200（rct=result-context:7fdef2e0b3374dfabf456…）→
overview 200（1,016ms，1,241,039 字节、41 发现/16 受试者，
chain_ok=True）。两遍与 seq 19 收口 overview 投影**逐字节一致**
（1,241,039B，较 R24 的 1,148,653B 增加系 R24 六项修复 117657f6 改变
投影输出，本轮三读一致佐证确定性）。

终态磁盘：sequence 19/20/21 全部 completed+result_available=1、
manifest_digest 统一 f58ccf16c4f3、**waiting_start=0**。

### 6. 回归

- `pytest tests/test_medical_monitoring_r7_product_router.py -k r19_siege
  -q` → **2 passed**（1.10s）。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py -q` →
  **95 passed**（45.78s）。
- 本轮零代码改动，故无新增 pytest；上述两档证明在役代码未被本轮触碰。

### 7. 遗留与边界（转台账，不属本轮墙判据）

- 409 文案语义偏差：completed+未发布场景下报「当前已有监查正在进行，
  请先查看本次进度」——实为「上一运行已完成待发布收口」，且响应不带
  指向该运行 token 的字段，客户端无从引导用户收口（本轮靠 registry
  磁盘行定位）。产品语义层发现，与 R20 §4 同类，转测试循环台账。
- 观察到偶发 ~16-22s 慢调用（收口首发 publication POST 21.1s、两次
  链路首读 overview 16.4s/冷 projects_list 22.0s；其后同端点 ~1s）——
  疑与 R23-01 写锁/线程池家族相关的首次重计算或锁等待，未拦链路，
  转台账观察。
- 常驻项目现有 3 条 completed+已发布运行（seq 19 补收口的 R24 诊断、
  seq 20/21 本轮两键）；后续轮次开考直接走「开始运行监查」即可。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码
  核验为口径；界面路径的自动收口行为已有 Loop.jsx:1060-1065 代码
  佐证）。

留痕文件：`r25s_siege_repro.py`、`r25s_close_leftover.py`、
`r25s_siege_evidence.jsonl`（含 409 复现、c* 收口、两遍全链）、本日志节。

---

## R24 攻坚·第 1 次（2026-10-07，攻坚工程师-R24-第1次）

### 0. 结论先行

**墙未复发：本轮独立复现两遍全链全绿，零阻断、零新修复、零重启。**
R19 根因修复（cbb5f52e）在**当前新 build**（backend_build_id=
api-06744bbced9d86a2；R23 攻坚时为 api-e041fb3ab9060114，期间经 R23-01
写锁饥饿缓解 19d4359e（线程池 128 token+写锁等待 3s 快速失败）重建，且
循环收尾停机后由 R24 隔离环境守护员 17:44-17:46 恢复 8911（pid 801）/
5178（vite node pid 852））下亲测仍在役：代码两处都在位
（`run_entry.py:377` ensure_builtin_global_default、`run_routes.py:166`
reserve 前接入点，两文件最后修改 commit 即 cbb5f52e、工作树无未提交改动）、
R19 回归 2/2 绿、全量路由套件 95/95 绿。常驻项目「MX循开考-CSU」
（proj_user_6ef58ac151e1）以两个全新幂等键各走完 run-setup/options →
prepare-and-start → progress completed → publication available →
result-entry → results/{rct}/overview 可读。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（pid 801，127.0.0.1 IPv4 监听）`/api/health` 200
  （runtime_store integrity ok, schema v16）；`/api/runtime-readiness`
  status=ready、backend_build_id=**api-06744bbced9d86a2**，与 5178
  （vite node pid 852，**仅监听 [::1]:5178**——127.0.0.1 直连 exit 7
  属该监听布局的预期，`http://[::1]:5178/` 与 `/monitoring` 均 200）
  `runtime-build.json` expectedBackendBuildId **配对一致**
  （frontendBuildId=web-61cf3eec89de9bcb）。本轮全程未重启。
- 复现前磁盘基线：launch_registry 15 条全部 completed+
  result_available=1、manifest_digest 统一 f58ccf16c4f3、
  waiting_start=0；execution_profiles `global_default|*|1` 在位。

### 2. 复现（任务①）——两遍全链（驱动 `r24s_siege_repro.py`，证据
`r24s_siege_evidence.jsonl` 48 行、0 阻断）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测
——两遍均 replayed=true revision=1，幂等零改动）。

**第一遍（15:51:24Z，key=r24s-fresh-3aee4195b12f）**：

| 步骤 | 实测 |
| --- | --- |
| 基线双侧 | mapping-candidates 200（736ms，candidates_ready，draft monmapdraft_73abe5c6c9561a9e95eec2056991 **v80 confirmed**，user_questions=0，60 候选）、facts 200（651ms，**ready**）、project/open 200（656ms，**current**/edit/canEdit）、runs 200——预置台与运行门无口径差 |
| run-setup/options | 200，708ms，snapshot:ef8692acfbab4d2a9846916f（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，658ms，replayed=true revision=1 |
| prepare-and-start | **200，794ms**，run:79277d8fbc4b53b6425f9acf（registry sequence 16 落库即 running，created→updated 1.86s） |
| progress | 首轮询即 completed（percent=100.0，polls=1；result_available 首轮询 false→发布后终态 1，R20 §4 记录的同型投影时序，不拦链路） |
| publication | POST 200→**available**（1003ms） |
| result-entry | 200，rct=result-context:fc2dbb76b11c410ba69b6a1108c8cb19 |
| results/{rct}/overview | 200，1001ms，序列化 1,148,653 字节，**15 发现/477 现行风险/去重受试者 11**，identity.project_ref=proj_user_6ef58ac151e1 |

**第二遍=重验（任务③，15:51:50Z，key=r24s-fresh-ea3eaa54ff26）**：同链
全绿 9s 壁钟：options 200（702ms）→ bootstrap 200 replayed → prepare 200
（798ms，run:bef92bd76de41a6d66596213，registry sequence 17，
created→updated 1.94s）→ progress completed → publication **available**
（1013ms）→ entry 200（rct=result-context:d0d9112f268a444aaab1e24d81ddb357）
→ overview 200（883ms，1,148,653 字节、15 发现/477 现行风险/11 受试者，
chain_ok=True）。两遍序列化字节数逐字节一致，与 R23 新 build 绿路径口径
（1,148,653）一致（较 R19-R22 的 1,136,740 增加系 R22 三项产品修复
3042c74b 改变投影输出，R23 §2 已记录）。

### 3. 修复（任务②）与口径差对照

**无需新修复，本轮零代码改动、零重启。** 两侧口径在本轮无分叉：预置台
（mapping confirmed v80 / facts ready / project current）与运行启动门
（run-setup/options 200 + prepare-and-start 200）读数一致。本轮若复现
422/卡「等待开始」，对照方案为驱动内 `backend_truth()`（mapping/facts/
project/open 同刻快照）——已装备但未触发（0 阻断）。

R19 修复在新 build 在役证明（本轮亲测）：

- 代码在位：`packages/medical_monitoring/runtime/run_entry.py:377`
  `ensure_builtin_global_default()`（仅缺失时幂等种入）；
  `packages/medical_monitoring/api/r7_product/run_routes.py:166`
  prepare-and-start 在 reserve 之前调用（补种失败 fail-closed 且无预约
  落库）；两文件工作树无未提交改动、最后一次修改 commit cbb5f52e。
- `pytest tests/test_medical_monitoring_r7_product_router.py -k r19_siege
  -q` → **2 passed**（1.03s）。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py -q` →
  **95 passed**（42.96s）。

### 4. 终态与边界

- 终态磁盘：sequence 1-17 全部 completed+result_available=1、
  manifest_digest 统一 f58ccf16c4f3、**waiting_start=0**（本轮新增 16/17
  两行，壁钟 created→updated 各约 1.9s）。基线 15 条与 R24-D 只读复验
  读数一致；R23 攻坚（seq 13/14）后、本轮之前的 sequence 15
  （monitoring_c83192f9…，2026-10-07T08:51Z 界面键）为 R23 轮次角色
  所启动，非本轮。
- 本轮结论仅覆盖「运行启动→完成→发布→可读」墙；测试循环台账升级区所列
  fail-open 语义修正、R7-01 异步隔离、确认映射重跑公平评估，及 R21D-R24D
  持续记录的 candidates 投影怪癖（顶层 facts_generated=False /
  summary pending_confirmation_count=60 与权威终态不一致）均属测试循环
  排期项，不属本攻坚墙判据。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径；R19-D/R20-D 已两轮覆盖界面路径到结果视图）。

留痕文件：`r24s_siege_repro.py`、`r24s_siege_evidence.jsonl`、本日志节。

---

## R23 攻坚·第 1 次（2026-10-07，攻坚工程师-R23-第1次）

### 0. 结论先行

**墙未复发：本轮独立复现两遍全链全绿，零阻断、零新修复、零重启。**
R19 根因修复（cbb5f52e）在**当前新 build**（expectedBackendBuildId=
api-e041fb3ab9060114 / frontend web-1e1b51b10b4de15c；R22 时为
api-1d25bf363b10c2a5，R22 归档后后端经重建+重启，当前 pid 13760）下
亲测仍在役：代码两处都在位（`run_entry.py:377`
ensure_builtin_global_default、`run_routes.py:166` reserve 前接入点）、
R19 回归对 2/2 绿、全量路由套件 95/95 绿（R19 时的存量失败
test_late_project_dispatchers_keep_two_actual_api_results_isolated 亦绿）。
常驻项目「MX循开考-CSU」（proj_user_6ef58ac151e1）以两个全新幂等键各走完
run-setup/options → prepare-and-start → progress completed → publication
available → result-entry → results/{rct}/overview 可读。任务书背景
「此墙自 R8 起 10 轮未破」仍系 R19/R20 攻坚前的历史口径，本轮实测不成立。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（pid 13760，2026-10-07 10:29:52 启动）`/api/health` 200
  （runtime_store integrity ok, schema v16）；`/api/runtime-readiness`
  status=ready、backend_build_id=**api-e041fb3ab9060114**，与 5178
  （pid 13827，仅监听 [::1]）`frontend/public/runtime-build.json` 的
  expectedBackendBuildId **配对一致**。build 指纹自 R22 后变化系 R22 归档
  后三笔 commit（3042c74b 三项产品修复、dfccdf49/ed4cbeb9 轮次归档）重建
  所致；packages/medical_monitoring 与 services/api 全部源码 mtime 最晚
  10:26:12，早于进程启动 10:29:52——运行进程加载的即含 R19 修复的当前
  源码。本轮全程未重启（无修复即无重启需要）。
- 复现前磁盘基线：launch_registry 12 条全部 completed+
  result_available=1、manifest_digest 统一 f58ccf16c4f3、
  waiting_start=0（sequence 12=monitoring_30ab326a，2026-10-07T05:42Z
  界面键，亦 completed）；execution_profiles `global_default|*|1` 在位。

### 2. 复现（任务①）——两遍全链（驱动 `r23s_siege_repro.py`，证据
`r23s_siege_evidence.jsonl` 48 行、0 阻断）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测
——两遍均 replayed=true revision=1，幂等零改动）。

**第一遍（08:43Z，key=r23s-fresh-f7b10a93062d）**：

| 步骤 | 实测 |
| --- | --- |
| 基线双侧 | mapping-candidates 200（candidates_ready，draft **confirmed**，user_questions=0）、facts 200（**ready**）、project/open 200（**current**）、runs 200——预置台与运行门无口径差 |
| run-setup/options | 200，636ms，snapshot:ef8692ac…（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，655ms，replayed=true revision=1 |
| prepare-and-start | **200，721ms**，run:f1230e28aa5ebd65891f468d（registry sequence 13 落库即 running，created→updated 约 1.7s） |
| progress | 首轮询即 completed（percent=100.0，polls=1；result_available 首轮询 false→发布后终态 1，R20 §4 记录的同型投影时序，不拦链路） |
| publication | POST 200→**available**（947ms） |
| result-entry | 200，rct=result-context:3c5fcb8fa5514dfaaabc05d8f419a32e |
| results/{rct}/overview | 200，805ms，序列化 1,148,653 字节，**15 发现/477 现行风险/去重受试者 11**，identity.project_ref=proj_user_6ef58ac151e1 |

**第二遍=重验（任务③，08:44Z，key=r23s-fresh-ac35b9caf8b9）**：同链
全绿 8s 壁钟：options 200 → bootstrap 200 replayed → prepare 200
（727ms，run:9b07ae19f3983d2501c0ca38，registry sequence 14）→ progress
completed → publication **available**（915ms）→ entry 200
（rct=result-context:873634ced7c74b95913a8b22f8346a24）→ overview 200
（850ms，1,148,653 字节、15 发现/477 现行风险，chain_ok=True）。

**序列化字节数口径更新**：两遍均 1,148,653 字节且逐字节互相一致；较
R19-R22 绿路径口径（1,136,740）增加，系 R22 三项产品修复（3042c74b：
AE 医学逻辑入发现等）改变投影输出所致——发现数 15/现行风险 477/去重
受试者 11 与 R21/R22 读数一致，本轮两遍互证为新 build 下的稳定绿路径
口径。

### 3. 修复（任务②）与口径差对照

**无需新修复，本轮零代码改动、零重启。** 两侧口径在本轮无分叉：预置台
（mapping confirmed / facts ready / project current）与运行启动门
（run-setup/options 200 + prepare-and-start 200）读数一致。本轮若复现
422/卡「等待开始」，对照方案为驱动内 `backend_truth()`（mapping/facts/
project/open 同刻快照）——已装备但未触发（0 阻断）。

R19 修复在新 build 在役证明（本轮亲测）：

- 代码在位：`packages/medical_monitoring/runtime/run_entry.py:377`
  `ensure_builtin_global_default()`（仅缺失时幂等种入）；
  `packages/medical_monitoring/api/r7_product/run_routes.py:166`
  prepare-and-start 在 reserve 之前调用（补种失败 fail-closed 且无预约
  落库，接入点注释块在位）；两文件工作树无未提交改动、最后一次修改
  commit cbb5f52e。
- `pytest tests/test_medical_monitoring_r7_product_router.py -k r19_siege
  -q` → **2 passed**（1.07s）。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py -q` →
  **95 passed**（42.39s，无存量失败残留）。

### 4. 终态与边界

- 终态磁盘：sequence 1-14 全部 completed+result_available=1、
  manifest_digest 统一 f58ccf16c4f3、**waiting_start=0**（本轮新增 13/14
  两行，壁钟 created→updated 各约 1.7s）。
- 本轮结论仅覆盖「运行启动→完成→发布→可读」墙；测试循环台账升级区所列
  fail-open 语义修正、R7-01 异步隔离、确认映射重跑公平评估等属测试循环
  排期项，不属本攻坚墙判据。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径；R19-D/R20-D 已两轮覆盖界面路径到结果视图）。

留痕文件：`r23s_siege_repro.py`、`r23s_siege_evidence.jsonl`、本日志节。

---

## R22 攻坚·第 1 次（2026-10-07，攻坚工程师-R22-第1次）

### 0. 结论先行

**墙未复发：本轮独立复现两遍全链全绿，零阻断、零新修复、零重启。**
R19 根因修复（cbb5f52e）在当前 build（expectedBackendBuildId=
api-1d25bf363b10c2a5 / frontend web-2fb29a9f1da6fb9c，与 R21 同一后端
build）下亲测仍在役：代码两处都在位（`run_entry.py:377`
ensure_builtin_global_default、`run_routes.py:161-181` reserve 前接入点）、
R19 回归对 2/2 绿、全量路由套件 95/95 绿（R19 时的存量失败
test_late_project_dispatchers_keep_two_actual_api_results_isolated 本轮
亦绿）。常驻项目「MX循开考-CSU」（proj_user_6ef58ac151e1）以两个全新
幂等键各走完 run-setup/options → prepare-and-start → progress completed
→ publication available → result-entry → results/{rct}/overview 可读。
任务书背景「此墙自 R8 起 10 轮未破」系 R19/R20 攻坚前的历史口径，
与 R21 结论一致，本轮实测再次不成立。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（pid 54721）`/api/health` 200（runtime_store integrity ok,
  schema v16）；5178（pid 54768，仅监听 [::1]）200，
  runtime-build.json expectedBackendBuildId=api-1d25bf363b10c2a5 与
  前端配对。本轮全程未重启（无修复即无重启需要）。
- 复现前磁盘基线：launch_registry 9 条全部 completed+
  result_available=1、manifest_digest 统一 f58ccf16c4f3、
  waiting_start=0（R21 后新增 sequence 9=monitoring_46c726d1，
  2026-10-06T19:02Z 界面键，亦 completed）；execution_profiles
  `global_default|*|1` 在位。

### 2. 复现（任务①）——两遍全链（驱动 `r22s_siege_repro.py`，证据
`r22s_siege_evidence.jsonl` 48 行、0 阻断）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测
——两遍均 replayed=true revision=1，幂等零改动）。

**第一遍（05:33Z，key=r22s-fresh-44e88869012b）**：

| 步骤 | 实测 |
| --- | --- |
| 基线双侧 | mapping-candidates 200（candidates_ready，draft **confirmed**，60 候选，user_questions=0）、facts 200（**ready**）、project/open 200（**current**）、runs 200——预置台与运行门无口径差 |
| run-setup/options | 200，542ms，snapshot:ef8692ac…（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，495ms，replayed=true revision=1 |
| prepare-and-start | **200，601ms**，run:98389c6e1b554500f4496b8b（registry sequence 10 落库即 running） |
| progress | 首轮询即 completed（percent=100.0，polls=1；result_available 首轮询 false→发布后终态 1，R20 §4 记录的同型投影时序，不拦链路） |
| publication | POST 200→**available**（808ms） |
| result-entry | 200，rct=result-context:4efc3bd28a1f48a0b00eb80fda3e173a |
| results/{rct}/overview | 200，719ms，序列化 1,136,740 字节，**15 发现/477 现行风险**（受试者去重 11 人口径与 R21 §2 相同），identity.project_ref=proj_user_6ef58ac151e1 |

**第二遍=重验（任务③，05:33:54Z，key=r22s-fresh-45c2a1e80fee）**：同链
全绿 7s 壁钟：options 200（528ms）→ bootstrap 200 replayed → prepare 200
（665ms，run 落 registry sequence 11）→ progress completed → publication
**available**（954ms）→ entry 200（rct=result-context:1846c9ddb63c40a9a…）
→ overview 200（1,136,740 字节、15 发现/477 现行风险，chain_ok=True）。
两遍序列化字节数与 R19/R20/R21 绿路径口径（1,136,740/15/477）逐项一致。

### 3. 修复（任务②）与口径差对照

**无需新修复，本轮零代码改动、零重启。** 两侧口径在本轮无分叉：预置台
（mapping confirmed / facts ready / project current）与运行启动门
（run-setup/options 200 + prepare-and-start 200）读数一致——R19 修复使
运行启动侧不再依赖「用户不可达的 bootstrap」预置 global_default，本轮
基线即见 execution_profiles `global_default|*|1` 在位（R19 修复后历轮
自愈种入的持久态）。本轮若复现 422，对照方案为驱动内 `backend_truth()`
（mapping/facts/project/open 同刻快照）——已装备但未触发（0 阻断）。

R19 修复在役证明（本轮亲测）：

- 代码在位：`packages/medical_monitoring/runtime/run_entry.py:377`
  `ensure_builtin_global_default()`（仅缺失时幂等种入）；
  `packages/medical_monitoring/api/r7_product/run_routes.py:161-181`
  prepare-and-start 在 reserve 之前调用（补种失败 fail-closed 且无预约落库）。
- `pytest tests/test_medical_monitoring_r7_product_router.py -k r19_siege
  -q` → **2 passed**（0.90s）。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py -q` →
  **95 passed**（42.09s，无存量失败残留）。

### 4. 终态与边界

- 终态磁盘：sequence 1-11 全部 completed+result_available=1、
  manifest_digest 统一 f58ccf16c4f3、**waiting_start=0**（本轮新增 10/11
  两行，壁钟 created→updated 各约 1.5-2s）。
- 本轮结论仅覆盖「运行启动→完成→发布→可读」墙；R21 台账升级区所列
  fail-open 语义修正、R7-01 异步隔离、确认映射重跑公平评估等属测试循环
  排期项，不属本攻坚墙判据。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径；R19-D/R20-D 已两轮覆盖界面路径到结果视图）。

留痕文件：`r22s_siege_repro.py`、`r22s_siege_evidence.jsonl`、本日志节。

---

## R21 攻坚·第 1 次（2026-10-06，攻坚工程师-R21-第1次）

### 0. 结论先行

**墙未复发：本轮独立复现两遍全链全绿，零阻断、零新修复。** R19 根因修复
（cbb5f52e）在当前 build（api-1d25bf363b10c2a5，R19 时为 api-a9bb87fb5ee7ab77，
期间经 62bb84a1/e46ca795/c9199d2c 多次重建）下核验仍在役：代码两处都在位
（`run_entry.py:377` ensure_builtin_global_default、
`run_routes.py:166` reserve 前接入点）、R19 回归测试对 2/2 绿、
常驻项目「MX循开考-CSU」（proj_user_6ef58ac151e1）以两个全新幂等键各走完
run-setup/options → prepare-and-start → progress completed → publication
available → result-entry → results/{rct}/overview 可读。任务书背景
「此墙自 R8 起 10 轮未破」系 R19/R20 攻坚前的历史口径，本轮实测不成立。

### 1. 环境前置（复现前，未重启任何服务）

- 8911（pid 12958）`/api/health` 200（runtime_store integrity ok, schema v16）；
  5178（pid 13033）200，runtime-build.json expectedBackendBuildId=
  api-1d25bf363b10c2a5 与前端配对。服务自 20:35 起在监听，本轮全程未重启
  （无修复即无重启需要，与 R20 口径一致）。
- 复现前磁盘基线：launch_registry 6 条全部 completed+result_available=1、
  manifest_digest 统一 f58ccf16c4f3、waiting_start=0；execution_profiles
  `global_default|*|1` 在位。R19 修复核验：`ensure_builtin_global_default`
  于 `packages/medical_monitoring/runtime/run_entry.py:377`、
  `packages/medical_monitoring/api/r7_product/run_routes.py:166`。

### 2. 复现（任务①）——两遍全链（驱动 `r21s_siege_repro.py`，证据
`r21s_siege_evidence.jsonl` 48 行、0 阻断）

忠实界面路径（不先 workspace/bootstrap；bootstrap 仅按任务书列名留证实测
——第一遍 replayed=true revision=1，幂等零改动，界面链路从不调用它）。

**第一遍（18:52:42Z，key=r21s-fresh-68721906a5e5）**：

| 步骤 | 实测 |
| --- | --- |
| 基线双侧 | mapping-candidates 200（576ms）、facts 200（489ms）、project/open 200（498ms）、runs 200 |
| run-setup/options | 200，514ms，snapshot:ef8692ac…（与历史 registry 指纹同源） |
| workspace/bootstrap（留证） | 200，532ms，replayed=true revision=1 |
| prepare-and-start | **200，587ms**，run:64254e31021f1b14fcc0f91d（registry sequence 7） |
| progress | 首轮询即 completed（percent=100.0，polls=1；result_available 首轮询 false→发布后复测 true，R20 §4 记录的同型投影时序，不拦链路） |
| publication | POST 200→**available**（796ms） |
| result-entry | 200，rct=result-context:4dc65be18d9b45778f3707fffa37e145 |
| results/{rct}/overview | 200，722ms，序列化 1,136,740 字节，**15 发现/477 现行风险**；受试者双口径实测：projection.subjects 主脊 **16 人**（subject-21001…24016），15 条发现覆盖去重 subject 11 人（current_risks 项不含 subject_id 键，风险侧计 0）——与 R19/R20「16 受试者」口径（projection.subjects）一致，identity.project_ref=proj_user_6ef58ac151e1 |

**第二遍=重验（任务③，18:53Z，key=r21s-fresh-e5ec5cbc6dcb）**：同链全绿
7s 壁钟：options 200 → bootstrap 200 replayed → prepare 200（run:
2ad95d98599ea6bddd7c723c，sequence 8）→ progress completed → publication
**available**（819ms）→ entry 200（rct=result-context:c130d456…）→ overview
200（1,136,740 字节、15 发现/477 现行风险/主脊 16 受试者，chain_ok=True）。
两遍序列化字节数与 R19/R20 绿路径口径（1,136,740/15/477/16）逐项一致。

### 3. 修复（任务②）与口径差对照

**无需新修复，本轮零代码改动、零重启。** 两侧口径在本轮无分叉：预置台
（mapping confirmed / facts ready / project current）与运行启动门
（run-setup/options 200 + prepare-and-start 200）读数一致——R19 修复使
运行启动侧不再依赖「用户不可达的 bootstrap」预置 global_default，即 R19
SIEGE_LOG §2 钉出的口径差（`project_source_manifest.py:179/208` 注释记录的
「预置管线不 bootstrap → prepare-and-start 必死 global_default_missing」）
已消除。本轮若复现 422，对照方案为驱动内 `backend_truth()`（mapping/facts/
project/open 同刻快照）——已装备但未触发（0 阻断）。

R19 修复在役证明（本轮亲测）：`pytest
tests/test_medical_monitoring_r7_product_router.py::test_r19_siege_prepare_and_start_seeds_missing_global_default
::test_r19_siege_seed_failure_fails_closed_without_reservation -q` →
**2 passed**（1.14s）。

### 4. 终态与边界

- 终态磁盘：sequence 1-8 全部 completed+result_available=1、manifest_digest
  统一 f58ccf16c4f3、**waiting_start=0**（本轮新增 7/8 两行）。
- 本轮结论仅覆盖「运行启动→完成→发布→可读」墙；R21 台账升级区所列
  fail-open 语义修正、R7-01 异步隔离、确认映射重跑公平评估等属测试循环
  排期项，不属本攻坚墙判据。
- 浏览器像素级全链回归未执行（工程验证身份以 API 驱动+状态机代码核验为
  口径；R19-D/R20-D 已两轮覆盖界面路径到结果视图）。

留痕文件：`r21s_siege_repro.py`、`r21s_siege_evidence.jsonl`、本日志节。

---

## R20 攻坚·第 1 次（2026-10-06，攻坚工程师-R20-第1次）

### 0. 结论先行

**墙已破且未复发：本轮全链两遍实测全绿，无需新修复。** R19 落地的根因修复
（cbb5f52e）在役：代码在位、回归测试 2/2 绿、全量路由套件 95/95 绿、
常驻项目「MX循开考-CSU」以全新幂等键两遍走完 run-setup/options →
prepare-and-start → progress completed → publication available →
result-entry/overview 可读。R20-D 触发本轮攻坚的「等待开始」报告发生在
R19 修复**之前**（时间线见 §2），非新墙。

### 1. 环境前置（复现前）

- 8911（pid 57073）/5178（pid 57134）在监听，`/api/health` 200
  （runtime_store integrity ok，schema v16）。未重启任何服务（无需要）。
- 复现前磁盘基线：launch_registry 3 条全部 completed+result_available=1
  （sequence 1= R19-D 僵尸补完、2= R19 攻坚路径B、3= R19-D 修复后界面重测），
  **waiting_start 计数 0**；execution_profiles 有 `global_default|*|1`。

### 2. 复现（任务①）——驱动与双侧口径

驱动：`r20s_siege_repro.py`；证据：`r20s_siege_evidence.jsonl`（每请求
ts/http_status/elapsed_ms/响应体）。忠实界面路径（不先 workspace/bootstrap
——前端 `medicalMonitoringProductApi.mjs:390` 定义 bootstrapWorkspace 但零
组件调用；任务书列名该步骤，故按列名实测留证其行为）。全新幂等键=用户
下一次日常监查的常规路径。

**第一遍（15:31Z，key=r20s-fresh-c50dfe352ffa）**：

| 步骤 | 实测 |
| --- | --- |
| 基线双侧 | mapping-candidates 200（candidates_ready）、facts 200（ready）、project/open 200（current）、runs 200 |
| run-setup/options | 200，1037ms，snapshot:ef8692ac…（与 registry 指纹一致） |
| workspace/bootstrap（留证） | 200，992ms，replayed=true revision=1（已有内置档，幂等零改动） |
| prepare-and-start | **200，1195ms**，run:b8f424d9c3a84a2f92467044（registry sequence 4 落库即 running） |
| progress | 首轮询即 completed（percent=100.0；registry created→updated 2.7s） |
| publication | POST 200→**available**（1376ms） |
| result-entry | 200，rct=result-context:7dd7780b… |
| results/{rct}/overview | 200，原始 778,126 字节（序列化 1,136,740），**15 发现/477 现行风险/16 受试者**（投影含 query_findings 15 条、current_risks 477 条、identity.project_ref 归属正确）——与 r19p/r20p 绿路径口径逐项一致 |

第一遍证据行 b7 的 findings=0 系驱动初版提取键错误（读了不存在的顶层
`findings/subjects` 键；正确路径 `projection.query_findings/current_risks`），
随后独立复核与第二遍（修正后）均为 15/477/16——证据文件如实保留初版记录。

**第二遍=重验（15:35Z，key=r20s-fresh-01f0b714b089，任务③）**：
同链全绿：options 200（12.5s）→ bootstrap 200 replayed → prepare 200
（20.3s，run:273d3736cda3d1a383d7f2d）→ progress completed → publication
**available** → entry 200（rct=result-context:7052e30e…）→ overview 200
（15 发现/477 现行风险，chain_ok=True，总壁钟 97s）。本遍各步耗时升高
（1s→12-20s）系隔离实例上外源项目（proj_user_b4e6e62616c9）在途负载
所致（r20p 预检补记已载），非本项目链路劣化——运行本体 registry
created→updated 仍约 2.7s。

终态磁盘：sequence 1-5 全部 completed+result_available=1，
**waiting_start=0**。

**R20-D「等待开始」报告的时间线归因（口径差钉行）**：R20-D 测试窗口为
2026-10-06 01:56–02:23Z（报告载 09:56–10:23 本机时间），早于 R19 攻坚
修复（复现 12:47Z、验证 12:54–13:05Z，r19s_siege_evidence.jsonl 时间戳）。
其所见「等待开始+无发起控件」是修复前僵尸在途的界面投影：workbar 在
选中运行 in-flight 时不渲染新监查入口
（`frontend/src/features/medical-monitoring/medicalMonitoringProductState.mjs:249-275`：
仅 published 或 completed-未整理才给出 secondaryTarget="wizard"）；
僵尸补完后（12:54Z 起）该控件即回归——R19-D 修复后界面重测
（round_19/report_D.md 旅程表）即从向导四步走到结果视图（registry
sequence 3，13:05:41Z 界面键 monitoring_3948aab1…）。R20-D 报告的
「数据接入向导第 3 步未点亮」为会话级步骤进度（挂载即重置 stepIndex，
`medicalMonitoringAdmissionWizardState.mjs:240-253`），不是对持久确认态
的读数——修复前后该显示一致，非缺陷、不拦链路。

### 3. 修复（任务②）

**无需新修复。** R19 根因修复核验（本轮全部亲测）：

- 代码在位：`packages/medical_monitoring/runtime/run_entry.py:377-396`
  `ensure_builtin_global_default()`（仅缺失时幂等种入）；
  `packages/medical_monitoring/api/r7_product/run_routes.py:161-181`
  prepare-and-start 在 `registry.reserve()` 之前调用（补种失败 fail-closed
  且无预约落库）。
- 回归测试：`pytest tests/test_medical_monitoring_r7_product_router.py -k
  r19_siege` → **2 passed**（缺档自愈真启动 / 补种失败无僵尸）。
- 全量：`pytest tests/test_medical_monitoring_r7_product_router.py` →
  **95 passed**（R19 记录的存量失败
  test_late_project_dispatchers_keep_two_actual_api_results_isolated 本轮
  亦绿）。
- 实链：本日志 §2 两遍（含 422→200 的对照历史证据 r19s_siege_evidence.jsonl）。

### 4. 遗留与边界

- progress 首轮询时 `result_available=false` 与 registry 终态 1 的瞬差：
  completed 即刻发布尚未完成时的正常投影时序，发布 available 后一致，
  不拦链路（两遍均复现同型时序，非缺陷证据）。
- R19-D 修复后报告的「准备门禁语义未定义」（向导警告前置未完成但不拦
  运行、「方案事实与规则发布」抽屉文案与运行结果并存）属产品语义层发现，
  在测试循环台账流转，不属运行启动死锁墙（该墙以「运行能否真正完成+
  发布+可读」为判据，本轮两遍皆绿）。
- 浏览器像素级全链回归未在本攻坚内执行（工程验证身份以 API 驱动+状态机
  代码核验为口径；界面全量回归归墙破后的测试轮，R19-D 修复后重测已覆盖
  向导→结果视图一段）。

留痕文件：`r20s_siege_repro.py`、`r20s_siege_evidence.jsonl`、本日志节。

---

## R19 攻坚·第 1 次（2026-10-06，攻坚工程师-R19-第1次）


### 0. 环境前置（复现前）

- 攻坚开始时 8911 进程在（pid 35808，02:45 起）但 `/api/health` TCP 通、
  60s 零响应；`ps` 示 103.5% CPU、状态 RN；`sample` 采样：主线程与一个
  工作线程（Thread_17221470）均深陷纯 Python 循环（热点 `PySequence_Tuple`）；
  AI 台账 `monitoring_ai_jobs` 3 个 running 停在 12:43:43Z、134 queued——
  与 R7-01「事件循环独占」家族画像一致（R20-B 测试者 11:50 停笔时间吻合）。
  该自旋属既有环境级缺陷（R7-01，台账在案），非本次攻坚墙本身；按规程
  只重启 8911/5178（标准命令，ISO_ENV_LOG.md:20-21 口径），未触碰 8910/5177。
- 重启后自检：8911 `ready:true`（build api-a9bb87fb5ee7ab77）；5178
  /monitoring=200、runtime-build.json expectedBackendBuildId=api-a9bb87fb5ee7ab77
  指纹配对一致。

### 1. 复现（常驻项目「MX循开考-CSU」proj_user_6ef58ac151e1）

驱动：`r19s_siege_repro.py`；证据：`r19s_siege_evidence.jsonl`（逐请求
http_status/elapsed_ms/响应体）。忠实界面路径——**不先 workspace/bootstrap**
（前端 `medicalMonitoringProductApi.mjs:390` 定义了 bootstrapWorkspace 但无任何
组件调用；且 `/workspace/bootstrap` 需 ADMINISTER_RUNTIME 权限，监查用户无从
调用）。同一幂等键重放 R19-D 向导 2026-10-05T22:35:48Z 创建的预约
（monitoring_46a9e2b3-ad66-4790-8efe-b05a12309b34，指纹入参与 registry 行一致）。

同一时刻（2026-10-06T12:47Z）双侧状态：

| 侧 | 信号 | 实测 |
| --- | --- | --- |
| 预置台/API | mapping-candidates | state=candidates_ready，draft.status=**confirmed**（v80，user_questions=[]，60 候选） |
| 预置台/API | facts | state=**ready**（10 表/591 行/3038 值 100% 往返核验） |
| 预置台/API | r7/project/open | state=**current** |
| 预置台/API | run-setup/options | 200，snapshot_token=snapshot:ef8692ac…（与僵尸预约指纹一致） |
| 磁盘 | execution_profiles.sqlite3 | `profile_layer_versions` **空**（无 global_default 修订）；对照组绿路径项目 proj_user_ce177c32b799 有 `global_default|*|1` |
| 磁盘 | launch_registry.sqlite3 | 僵尸预约：sequence 1、run_state=waiting_start、result_available=0、**manifest_digest=NULL**、created 22:35:48.728Z |
| 运行门 | POST runs/prepare-and-start | **422 `{"code":"global_default_missing","message":"请先完成工作区初始化。"}`，768ms**；rejection 事件第 4 条落盘 admission_events.jsonl（12:47:40Z，与 R19-D 当晚 3 条同因：22:35:48/22:36:00/22:36:15Z 均 global_default_missing） |

### 2. 根因（两侧口径差钉到代码行）

口径差的本质：**接入管线侧的 confirmed/ready/current 全部为真，运行启动侧
要求的是另一个从未被任何用户可达路径种入的东西——工作区 `global_default`
执行档（内置基础设施配置）**，且失败发生在预约落库之后：

1. `packages/medical_monitoring/api/r7_product/run_routes.py:92-252`
   `prepare_and_start`：`registry.reserve()`（:157，先写 waiting_start 行）→
   `entry.bind_run()`（:193）失败于 global_default_missing → 通用 except
   （:236）返回 422——预约已持久化，成为**永不可启动的 waiting_start 僵尸**。
2. `packages/medical_monitoring/runtime/run_entry.py:444-445`
   `resolve_scope_layers(require_global_default=True)`：`global_default/*`
   修订缺失即 raise——真正的 raise 点。
3. `packages/medical_monitoring/api/r7_product/route_utils.py:28-33`
   `_workspace_is_ready` 只查两个库**文件存在**（预置管线建了文件），不查
   global_default 修订——早门放行、晚门必死。
4. `packages/medical_monitoring/api/r7_product/project_routes.py:550-559`
   `/workspace/bootstrap` 要求 `ADMINISTER_RUNTIME`——用户侧启动链路无权
   调用；前端 `frontend/src/features/medical-monitoring/medicalMonitoringProductApi.mjs:390`
   的 bootstrapWorkspace **零组件调用**。
5. 预置侧：`r19d_seed_csu.py` 按设计停在 facts（不启动监查，故不 bootstrap）——
   常驻/预置项目**必然**落入该状态；预检脚本（r19p/r20p）显式调
   workspace/bootstrap（HANDOFF_FULLCHAIN_20260923 工程事实），故一次性新项目
   8 连绿。
6. 僵尸的自我强化：`launch_registry_core_mixin.py:_find_in_flight_locked`
   的 in-flight 判定**含 waiting_start**——僵尸预约拦住该项目后续所有新幂等键
   （409 in_flight_conflict），同键重放又死在同一 raise 点。R8 起 10 轮 8 次
   「创建运行即卡等待开始」全部由此而来。

### 3. 修复（最小根因修复，未跳任何门）

内置 global_default 是基础设施默认（bootstrap_workspace 幂等种入的内置配置，
非用户决策）——运行启动路径在 **reserve 之前**幂等补种它，缺失才种、已有
修订零改动、补种失败 fail-closed 且此时尚未创建任何预约（无僵尸）：

- `packages/medical_monitoring/runtime/run_entry.py`：新增
  `ensure_builtin_global_default()`（仅缺失时调 bootstrap_workspace，已有修订
  不动、不断言 builtin——后续配置覆盖层属正常状态）。
- `packages/medical_monitoring/api/r7_product/run_routes.py`：
  `prepare_and_start` 在 `resolve_launch_inputs` 之后、`open_launch_registry`
  之前接入 ensure（附 R19 攻坚注释：僵尸成因 + 管理员权限不可达 + in_flight
  自我强化）。

回归测试（`tests/test_medical_monitoring_r7_product_router.py`）：

- `test_r19_siege_prepare_and_start_seeds_missing_global_default`：
  未 bootstrap 工作区（库文件在、global_default 修订缺——常驻项目终态）上
  prepare-and-start 必须 200+真正 running→completed，内置档补种 revision 1，
  同键重放幂等语义不回归。**stash 修复后该测试红**（422 复现），恢复修复后绿。
- `test_r19_siege_seed_failure_fails_closed_without_reservation`：
  补种失败（monkeypatch raise）→ 422 如实返回且 launch_registry 库文件不存在
  （fail-closed 无僵尸——顺序保证）。

套件：`tests/test_medical_monitoring_r7_product_router.py` 94/95 绿
（1 失败 `test_late_project_dispatchers_keep_two_actual_api_results_isolated`
为**存量失败**——stash 我的全部改动后同样红，与本修复无关）；
`tests/medical_monitoring/test_synthetic_startup.py` 绿。

修复后 8911 重启加载（标准命令，只动 8911/5178；packages 改动不入 build
指纹 api-a9bb87fb5ee7ab77，进程重启实证加载）。

### 4. 重验（同项目 MX循开考-CSU，两条路径）

**路径 A——同键重放补完历史僵尸（恢复语义）**：
prepare-and-start 200（512ms）→ 同一 run:0bf83a78… waiting_start→running
（manifest_digest=f58ccf16…落库、global_default revision 1 种入）→
progress **completed** → publication 200 **available** → result-entry 200
（rct=result-context:b926211a…）→ overview 200、597,305 字节、
**15 发现/16 受试者/477 现行风险**（与 r19p/r20p 绿路径口径逐项一致）。
终态磁盘：sequence 1 run_state=completed result_available=1。

**路径 B——全新幂等键（用户下一次日常监查的常规路径）**：
run-setup/options 200 → prepare-and-start 200（14.8s，新 run:3ee655a0…）→
progress **completed** → publication **available** → result-entry 200 →
overview 200（597,305 字节、15 发现/16 受试者）。终态 registry：两条 run
全部 completed+result_available=1，无 waiting_start 残留。

### 5. 遗留与边界

- R7-01 事件循环独占（本轮重启前的自旋）：环境级缺陷，台账在案
  （R19 报告已列「异步隔离排期与门禁并列」），本轮仅按规程重启未修。
- R19-D 的 F2（向导确认按钮循环弹 alert）：后端修复后 prepare-and-start
  首击即成，该交互路径不再触发；向导自身的反馈呈现属 R19-01/02 家族
  （52fd9697 已修，待复测），未在本攻坚范围内另改前端。
- 常驻项目现已有 2 条 completed 运行（1 条为补完的 R19-D 僵尸、1 条为
  攻坚重验新键）；后续轮次开考直接走「开始运行监查」即可。

留痕文件：`r19s_siege_repro.py`、`r19s_siege_evidence.jsonl`、
本日志；ISO_ENV_LOG.md 补 8911/5178 重启条目。
