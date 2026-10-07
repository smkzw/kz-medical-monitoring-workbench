# 攻坚日志（SIEGE_LOG）——运行启动死锁

按轮分节。每轮记录：复现（请求/响应/状态/耗时）→ 两侧口径差钉代码行 → 修复 → 重验。

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
