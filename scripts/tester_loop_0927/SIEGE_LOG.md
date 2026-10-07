# 攻坚日志（SIEGE_LOG）——运行启动死锁

按轮分节。每轮记录：复现（请求/响应/状态/耗时）→ 两侧口径差钉代码行 → 修复 → 重验。

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
