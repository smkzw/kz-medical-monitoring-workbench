# 攻坚日志（SIEGE_LOG）——运行启动死锁

按轮分节。每轮记录：复现（请求/响应/状态/耗时）→ 两侧口径差钉代码行 → 修复 → 重验。

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
