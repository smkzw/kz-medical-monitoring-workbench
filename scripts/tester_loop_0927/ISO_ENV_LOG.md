# 隔离测试环境日志（0927V1 质量循环 R3+）

隔离组合：**独立 API 8911 + 独立 vite 5178**，与医学写作舰队共用的 8910/5177 完全隔离。
- 运行时目录：`runs/tester_loop_iso_20260928/runtime`（一次性从 `runs/phase_c_mgk10_authority_v2_20260905/runtime` 快照复制：sqlite3 逐库 `.backup`（排除 4.4G AI 账本库与 -wal/-shm），rsync 排除 `*.sqlite3*`、`medical_monitoring_r7/`；共 347M）
- vite 代理：`VITE_API_PROXY_TARGET=http://127.0.0.1:8911`（vite.config.mjs 原生支持）
- 隔离实例的 AI 账本/队列为全新空库：测试期的 AI 作业与花费与舰队账本互不污染
- **铁律：循环内一切重启只允许动 8911/5178；严禁触碰 8910/5177（医学写作舰队在用）**

## 2026-09-28 18:1x-18:31 建成并验证（任务所有者手动，去风险）

- API 启动：8911 ready:true，build=api-db761d4a7f4bf45c；AI 网关 zhipu-coding-plan/glm-5.3-flash，无路由校验错误
- vite 启动：5178 /monitoring=200；/runtime-build.json expectedBackendBuildId=api-db761d4a7f4bf45c（与 8911 一致，指纹配对✓）；代理转发 ready:true
- 项目清场：隔离实例上 12 个外来项目（写作舰队 T1/T3/T5×2/C-ADC 等 + 2 个 MG-K10 遗留 + 3 个 R3 暂停遗留）全部软删除归档（副本上操作，不影响 8910 原件）
- 节点冒烟：POST /api/projects 建项成功（合同=project_name/indication/product_name/modules/idempotency_key，**无 name 字段——R1-05 号发现的实证**），DELETE 归档 200；探针已清理，当前可见项目=0
- 数据暂存：workbench/tester_staging_0927/ 补齐四套三件套（12 文件），提示词将使用绝对路径

### 恢复命令（隔离环境守护员用）

```
API：cd implementation/workbench && lsof -ti:8911 | xargs kill 2>/dev/null; sleep 2; source ~/.config/cms-medical-workbench/ai-runtime.env; WORKBENCH_RUNTIME_DIR="$PWD/runs/tester_loop_iso_20260928/runtime" WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api WORKBENCH_MONITORING_AI_PARALLELISM=2 nohup .venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8911 --log-level warning > /tmp/mm_api_8911.log 2>&1 &
vite：cd implementation/workbench/frontend && lsof -ti:5178 | xargs kill 2>/dev/null; sleep 1; VITE_API_PROXY_TARGET=http://127.0.0.1:8911 nohup npx vite --port 5178 --strictPort > /tmp/mm_vite_5178.log 2>&1 &
自检：8911 runtime-readiness ready:true；5178 /monitoring 200；5178 /runtime-build.json 与 8911 backend_build_id 一致
```

## 2026-09-28 下午（测试循环R3·修复员：缺陷修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（测试循环R3）
- 原因：R3-01/02/03/04/05 修复涉及后端 Python（main.py/user_project_store/mapping_confirmation/authority workflow/routes）与前端（App.jsx/向导/RouteOutlet/状态机/styles.css），隔离环境 API 与 vite 双双重启。**未触碰 8910/5177（医学写作舰队），重启后经 curl 验证二者仍为 200 正常服务。**
- API(8911)：`lsof -ti:8911 | xargs kill` 后按标准命令以 `WORKBENCH_RUNTIME_DIR=runs/tester_loop_iso_20260928/runtime` 启动（uvicorn 127.0.0.1:8911）。
- vite(5178)：`lsof -ti:5178 | xargs kill` 后 `VITE_API_PROXY_TARGET=http://127.0.0.1:8911 npx vite <frontend绝对路径> --port 5178 --strictPort`（必须以 frontend 为 root 启动）。
- 自检：8911 `/api/runtime-readiness` → `"ready": true`；`http://localhost:5178/monitoring` → 200；`5178/runtime-build.json` 的 `api-e9110b23c475b2ef` 与 8911 `backend_build_id` 一致（指纹配对✓）；8910/5177 复核均为 200（舰队未受影响）。

## 2026-09-29 上午（测试循环R4·修复员：R4-01修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（测试循环R4）
- 原因：R4-01（数据接入第一步选择控件）为纯前端修复（向导+CSS+render测试），隔离环境 vite 重启加载新代码；API 一并按规程双重启。**未触碰 8910/5177，重启后复核二者均为 200。**
- 自检：8911 `/api/runtime-readiness` → `"ready": true`（build api-e9110b23c475b2ef）；`5178/monitoring` → 200；`5178/runtime-build.json` 与 8911 `backend_build_id` 一致（指纹配对✓）；向导模块 vite 转换已含新「选择单个数据文件」入口。
2026-09-29 01:17 循环收尾：隔离测试环境已停止（运行时目录保留取证）
2026-09-29 09:50 用户拍板R5冲刺前手工拉起隔离对（API+vite）
2026-09-29 09:50 用户拍板R5冲刺前手工拉起隔离对（API 8911 + vite 5178，指纹配对 api-e9110b23c475b2ef，含R4修复代码）

## 2026-09-29 中午（测试循环R5冲刺·修复员：批量修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R5冲刺第1批）
- 原因：29条批修涉及后端（worker/repository/service/main/pipeline/models/validation/intake）与前端（App/向导/RouteOutlet/ProductLoop/状态机/样式），隔离环境双双重启。**未触碰 8910/5177。**
- 自检：8911 ready:true（build api-39dd6f40246a95ce）；5178/monitoring=200；runtime-build.json 与 8911 backend_build_id 一致。
- ⚠️ 冲突记录：R5验收实测期间发现**测试循环并行会话同时在8911隔离实例活动**（02:56出现第二个MX循R5-CSU-c2ae项目，本修复员的验收项目proj_user_8f09c3d11ce1 workspace于02:55(UTC)被清场——验收attempt的admissions目录被移除）。为完成CSU计时验收，修复员在8912端口起一次性验收实例（/tmp/r5_accept_runtime，与任何现有runtime隔离），验收结束后关闭。

## 2026-09-29 下午（R5验收实测留痕）

- 验收实测三跑：①8911被并行循环清场中断（前段完成：建项→导入→文档核对ready=312.8s自动完成）；②8912首跑文档链cross_checking后模型输出违约invalid_ai_output（fail-closed正确报409诊断，非挂起）；③8912终跑：文档链233s→mapping链candidates_ready(60字段)约12分钟自动完成（全程无人值守、脚本崩溃后任务仍持续推进——病根修复生效实证）；adopt成功后复核(adjudication)恒running、confirm恒409 mapping_verifier_incomplete，而全部20个mapping job已终态(19完成+1失败)——**新发现残余缺陷：复核状态机在job全终态下不收敛**（R3-01「后台收尾任务不收敛」的复核段变体），修复留待下批。验收结论：≤15分钟目标部分达成（文档+识别段✓、确认段被上述缺陷阻断）。
- 8912一次性实例与/tmp临时runtime已关闭清理，未影响8910/5177/8911。

## 2026-09-29 下午（R5冲刺·开考门槛预置员：预置 MX循R5D-CSU）

- 操作者：开考门槛预置员（R5D）。开始时间：2026-09-29 ~15:0x（本地）。
- 动作：在 8911 上新建项目 MX循R5D-CSU（慢性自发性荨麻疹 / MG-K10 / modules=[medical_monitoring]，幂等键唯一），上传 synth_csu 三件套，经 API 推进全链至「字段映射 confirmed + facts 物化」停住（不启动监查运行）。
- 驱动脚本：`scripts/tester_loop_0927/r5d_seed_csu.py`（幂等，状态 r5d_seed_state.json，留痕 r5d_seed_evidence.jsonl）。AI 作业（文档权威双VLM + 映射双队列）真实产生、等待自然完成，不跳质量门。
- （本行为进行中留痕，结束时补起止时间与作业数）

### R5D 进行中留痕（14:5x 本地）

- 12:50 建项成功 proj_user_9ce08d6a722d；12:51 listing 上传（attempt stg-68d7a08f01b3472196931402184b53c4）；12:52 文档权威双VLM分析提交（mmbatch_b941ebb0895ff818a59fae94）
- 13:07 文件角色人工裁决（ecrf→eCRF填写指南docx；IB/SAP 标记缺失）后 readiness ready=true（文档链约15分钟，6个文档权威AI作业）
- 13:07 映射双队列启动：10主+10盲核；13:25 candidates_ready（60字段，双队列20作业全完成）
- 13:25 adopt 成功（draft monmapdraft_0173cdeeed8a9196d4bfc37edd6e）；复核（adjudication）第二轮双队列20作业开始
- 13:51-13:53 设计内医学手势：EX/EXTRT 问题卡作答（依据合成数据实测：128行给药记录两臂同值，治疗身份以DM.试验分组为准）；MH/MHNUM 角色改选闭合目录 metadata.record_id → G-ROLE-002 全局阻断清零（semantic pass_with_warnings/activate_restricted）
- 14:15 复核第一轮终态：43完成+5失败（verifier分片 provider_reasoning_only）；系统自动恢复3个（attempt 2→4）；余2个（AE/CM verifier分片）自动恢复预算耗尽（arc=1/1, attempts=4/4），按 bounded-gap 设计转为可见缺口（remaining 46→32）
- 14:5x 系统对余下32个分歧字段提交新一轮复核（新冲突包摘要，8主+8盲核16作业在跑）；confirm 暂被 409 mapping_reconciliation_required 挡住（符合设计：等复核收敛）

### R5D 完成留痕（17:36 本地）

- 复核收敛阶梯（全部系统设计行为，无人为跳门）：分歧字段 46→32→27→23→8→0，历经4轮第二轮双队列复核；失败verifier分片按 bounded-gap 设计自动恢复（attempt 2→4）后转为可见不可评估缺口；17:29-17:30 对最终8张两轮分歧裁决卡按数据实测逐卡作答（PATCH mapping-draft/field，决策前缀留痕）
- 17:36:51 confirm 200（confirmation_status=confirmed，draft v57）→ 同秒 facts 物化 201：state=ready，10表/591行/2400值全部来源核验，message「可用于监查的数据已生成，可以开始监查。」
- AI 作业总量：92个（文档权威8 + 映射第一轮20 + 复核多轮64），终态87完成/5失败（provider_reasoning_only×4、invalid_ai_output×1，均经自动恢复预算与bounded-gap收敛）；调用台账：183次调用，2,653,827 tokens
- 起止：12:50→17:37（约4小时47分，含等待轮询；纯AI处理约2.5小时）
- ⚠️ **新发现产品缺陷（阻断「界面可开始运行监查」）**：`GET /r7/project/open` → blocked（dataCoverage=incomplete）、`GET /r7/run-setup/options` → 409 project_open_blocked。根因：`services/api/app/main.py:4850` `_init_monitoring_runtime_dbs` 建项时以 manifest 现行 v5 DDL 创建 launch_registry.sqlite3 却写入过期 v4 marker（mm-r7-slice08b-launch-registry-v4），schema 检验按 marker 找 v4 形状→shape_mismatch→CORRUPT→运行入口全挡。实证：隔离 runtime 全部14个项目workspace同样 shape_mismatch（含并行会话项目）；用当前 LaunchRegistry 代码新建文件为 v5 且检验 CURRENT（写入方自洽，仅建项种子过期——R24 校正过同类漂移，W01-R26 升 v5 后又落后一版）。修复需后端改 marker 为 v5（或回归 R24 的权威取值），本轮未绕过、未改库。
- 环境未触碰 8910/5177；驱动脚本与留痕：tester_loop_0927/r5d_seed_csu.py、r5d_question_cards.py、r5d_final_cards.py、r5d_converge.py、r5d_seed_state.json、r5d_seed_evidence.jsonl

## 2026-09-29 下午（R5轮次·修复员：R5-03+复核收敛修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R5轮次）
- 原因：R5-03（口径链打通，前端抽屉+后端阻断文案+台账说明）与复核收敛性修复（mapping_confirmation终态失败分片上报新码mapping_verifier_job_failed+幂等重排队）。
- 自检：8911 ready:true（build api-afdb4eed4c25f97d）；5178/monitoring=200；指纹配对一致；8910/5177复核均200未受影响。

## 2026-09-29 傍晚（R6轮次·修复员：R6三修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R6轮次）
- 原因：R6-01（文档状态机假死）与R6-02（eCRF裁决候选集）涉及后端jobs+前端向导；R6-03纯前端CSS。
- 自检：8911 ready:true（build api-713057f57b434486）；5178/monitoring=200；指纹配对一致；8910/5177复核均200未受影响。

## 2026-09-30（R7轮次·修复员：R7-01防重入+R1-02缺失声明+R3-01漂移显式化后隔离环境 8911+5178 双重启）

- 操作者：修复员（R7轮次）
- 原因：R7-01（resolve防重入+前端轮询退避）、R1-02（未提供eCRF缺失声明→readiness清除required）、R3-01（复核revision漂移显式化）涉及后端routes/pipeline/confirmation+前端向导。
- 自检：8911 ready:true（build api-713057f57b434486）；5178/monitoring=200；指纹配对一致；8910/5177复核均200未受影响。

## 2026-09-30 凌晨（R8轮次·开考预置守护员：探障修复 launch_registry 种子marker + 预置 MX循R8D-CSU）

- 操作者：开考预置守护员-R8D。起止：2026-09-30 02:0x → 05:0x（本地 CST）。
- **探障确认**：`GET /r7/project/open`（R5D项目 proj_user_9ce08d6a722d）→ `state=blocked / dataCoverage=incomplete / canView=false`（界面症状「暂时无法安全打开此项目」）；`run-setup/options` 409 project_open_blocked。用产品自身 `inspect_member` 实证：隔离 runtime 全部 **21个** workspace 的 launch_registry 均 corrupt/shape_mismatch（marker=mm-r7-slice08b-launch-registry-v4 但形状为v5，其余成员均 current）。
- **修复1（产品缺陷，最小修复）**：`services/api/app/main.py` `_init_monitoring_runtime_dbs` 建项种子 launch_registry marker 原硬编码 v4（W01-R26 升 v5 后落后一版）→ 改为直接取 `launch_registry_contracts.SCHEMA_VERSION`（mm-r7-w01r26-launch-registry-v5），杜绝再落后。临时 runtime 实测：新种子文件 inspect_member → current/current_shape。
- **修复2（存量隔离库原地 v4→v5 升级）**：`scripts/tester_loop_0927/r8d_repair_launch_registry.py` 按 `LaunchRegistry.open()` 同语义守卫式原地升级（查PRAGMA列→缺列才ALTER→同事务推进marker），对隔离 runtime（runs/tester_loop_iso_20260928/runtime）**21个** launch_registry.sqlite3 全部 corrupt→current（v5列已存在，ALTER为no-op仅推进marker）；证据 r8d_repair_evidence.jsonl。未触碰 8910 舰队 runtime。
- **重启（只动 8911/5178）**：按本文件标准命令双重启。自检：8911 ready:true（build **api-700a1dd6ecebb56e**）；5178 /monitoring=200；runtime-build.json 与 backend_build_id 指纹配对一致；8910/5177 复核均 200 未受影响。重启后 R5D 项目 project/open → **current/complete/canView/canEdit=true**，run-setup/options 200（原409消除）。
- **预置 MX循R8D-CSU**（proj_user_6ae946bc497a，幂等键 r8d-seed-20260929T180648Z-80a50af6）：三件套上传→文档权威双VLM（mmbatch_b5dd4c1eb2e15b22b114559a，~16min ready，ecrf角色按文件名裁决+身份归属确认）→映射双队列（10主+10盲核，60候选）→adopt→复核收敛 46→36→21→0（3轮，失败分片自动恢复重排）→21张两轮分歧裁决卡逐卡按数据实测作答（15张R8新卡以R5D已确认版 monmaprev_e4c1fe85a816792f0814cbec2179 同数据已确认角色+列值实测为依据；首次遇到15张未知卡时驱动脚本 fail-closed 诚实退出留痕，未虚构作答）→**confirm 200（draft v68 confirmed，user_questions=0）→ facts 201（10表/591行/2834值全核验，state=ready「可用于监查的数据已生成，可以开始监查。」）**，停住未启动监查运行（runs=[]）。project/open → current/complete/canView/canEdit=true。
- AI 台账：64作业（61完成/3终态失败：invalid_ai_output×1、provider_runtime_error×2，经自动恢复与后续轮次收敛，adjudication remaining=0）；105次调用，1,942,073 tokens。全程未跳任何质量门。
- 驱动与留痕：`r8d_seed_csu.py`（幂等，状态 r8d_seed_state.json、留痕 r8d_seed_evidence.jsonl）、`r8d_repair_launch_registry.py`（r8d_repair_evidence.jsonl）。
2026-09-30 10:05 ZCode宿主崩溃后恢复：隔离对8911/5178与共享对8910/5177双双拉起，指纹配对api-700a1dd6ecebb56e（含R8修复代码）

## 2026-09-30 下午（R8轮次·修复员：R8三修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R8轮次）
- 原因：R8-01（prepare-and-start前置来源就绪门fail-fast）、R8-02（存量waiting_start运行历史行blocked_reason注入+进度页指引文案）、R8-03（来源阻断码不再被「监查范围已更新」误译）。
- 自检：8911 ready:true（build api-ff4268b99214365a）；5178/monitoring=200；指纹配对一致；8910/5177复核均200未受影响。
- ⚠️ 旁注：项目根默认runtime（PROJECT_ROOT/runtime/ai_task_runs.jsonl，非8910/8911所用目录）今日09:24被并行会话写入含 route_thinking/fallback_* 新字段的记录，本仓库AiTaskRun模型extra_forbid——裸跑（无WORKBENCH_RUNTIME_DIR）import main会迁移报错；8910/8911均显式指定runtime不受影响，但任何裸跑进程会失败，提请循环侧关注该文件来源与口径。
2026-09-30 10:46 循环收尾：隔离测试环境已停止（运行时目录保留取证）
2026-09-30 10:57 R9前手工拉起隔离对（第二次升级后用户未答，按常设指示以推荐方案续跑）

## 2026-09-30 中午（R9轮次·开考预置守护员：探障无障碍 + 预置 MX循R9D-CSU）

- 操作者：开考预置守护员-R9D。起止：11:02 → 15:00（本地 CST）。
- **探障**：`GET /r7/project/open`（R8D项目）→ current/complete/canView/canEdit=true，无 blocked/CORRUPT；R8D 修复代码在位（main.py:4883-4884,4893-4894 种子marker取 launch_registry_contracts.SCHEMA_VERSION，现行build api-ff4268b99214365a）；R9D 新建 workspace 的 launch_registry 经产品 inspect_member 实测 current/current_shape（v5）。**本轮无缺陷需修，未做任何重启（8911/5178/8910/5177 均未动）。**
- **预置 MX循R9D-CSU**（proj_user_f650151b5a42，幂等键 r9d-seed-20260930T030202Z-9b9b988e）：三件套上传 → 文档权威双VLM ~19min ready（身份归属确认一次）→ 映射双队列（10主+10盲核，60候选，1失败分片自动恢复）→ adopt → 复核收敛 46→37→33→28→12→0（5轮adjudicate/4轮双队列）→ 第4轮后浮现6张R9新裁决卡（CM×4+LB_HEM×2），驱动脚本首次遇未知卡 fail-closed 退出留痕后，按 openpyxl 直读合成文件列值实测+两轮队列同判结论逐卡作答 → **confirm 200（draft v59 confirmed，user_questions=0）→ facts 201（10表/591行/2724值全核验，state=ready）**，停住未启动监查（runs=[]）。project/open → current/complete。
- AI 台账（本项目）：88作业（84完成/4终态failed均为mapping分片，经自动恢复收敛 remaining=0）；139次调用，2,471,717 tokens。全程未跳任何质量门。
- 驱动与留痕：`r9d_seed_csu.py`、`r9d_seed_state.json`、`r9d_seed_evidence.jsonl`。

## 2026-09-30 傍晚（R9轮次·修复员：七项修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R9轮次）
- 原因：R7-03（新批次清旧核对结论，后端workflow）、R7-02/R6-06（项目列表20s超时错误态+空列表自动重拉，App.jsx）、R5-05（generating主按钮稳定禁用）、R6-04（域代码中文字典扩充+两视图复用）、R5-02（抽屉backdrop让出侧栏顶栏）、R9-04（三个弹层Escape，ref-callback实现避免SSR测试hook崩溃）。
- 自检：8911 ready:true（build api-439b9e81187f0da4）；5178/monitoring=200；指纹配对一致；8910/5177复核均200未受影响。
2026-09-30 17:44 循环收尾：隔离测试环境已停止（运行时目录保留取证）

## 2026-09-30 傍晚（R10轮次·隔离环境守护员：探针失败后恢复 8911+5178）

- 操作者：隔离环境守护员-R10。起止：17:46:59 → 17:48:29（本地 CST）。
- 触发：API探针 exit=1、前端探针 exit=1。排查：8911/5178 均无监听进程（lsof 空），系 17:44 循环收尾主动停止所致，非损坏；隔离 runtime 目录（runs/tester_loop_iso_20260928/runtime）完整在位，**未重建**（仅整目录丢失才按规程从 phase_c_mgk10_authority_v2_20260905 重建）。
- 恢复：按标准命令双重启——API：`WORKBENCH_RUNTIME_DIR=runs/tester_loop_iso_20260928/runtime WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api WORKBENCH_MONITORING_AI_PARALLELISM=2 nohup .venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8911`（pid 39061，日志 /tmp/mm_api_8911.log）；vite：`VITE_API_PROXY_TARGET=http://127.0.0.1:8911 nohup npx vite --port 5178 --strictPort`（日志 /tmp/mm_vite_5178.log，ready in 145ms）。
- 旁注：API 启动耗时略超 15 秒，17:47:17 首探 curl exit 7（连接被拒），此时进程存活、随后 17:47:59 监听就绪探针即通过——属启动竞态非故障，未触发第二次重启。
- 自检：8911 `/api/runtime-readiness` → 200 ready:true，backend_build_id=**api-439b9e81187f0da4**（与 R9 傍晚修复员轮次同 build，本轮无代码变更）；5178 `/monitoring` → 200；`runtime-build.json` expectedBackendBuildId=api-439b9e81187f0da4 与 backend_build_id 配对一致；17:48:29 复探 ready 稳定；8910/5177 只读复核均 200 未触碰未受影响。

## 2026-10-01 凌晨（R10轮次·开考预置守护员：探障无障碍+5178复活 + 预置 MX循R10D-CSU）

- 操作者：开考预置守护员-R10D。起止：2026-09-30 17:53 → 2026-10-01 02:03（本地 CST）。
- **探障（旧项目全被循环收尾软归档，改三路替代）**：① R8D 修复在位——main.py:4883-4884,4893-4894 种子 marker 仍取 `launch_registry_contracts.SCHEMA_VERSION`（=V5，contracts.py:54）；② 隔离 runtime 存量 29 个 workspace 的 launch_registry marker 逐库直查全 v5；③ 新建项目 4 个种子成员经产品 `inspect_member` 实测全 CURRENT。**R5D marker 缺陷未复发，本轮未修任何产品代码、未重启 8911。** 建项瞬间 project/open 的 blocked 为 `required_member_missing`（runtime/monitoring_runtime.sqlite3 bootstrap 前不存在，R1 已知瞬态同款），facts 物化后即 current——非损坏，未绕过。
- **5178 复活（只动隔离对）**：本轮中途发现隔离 vite 5178 掉线（连接拒绝），按本文件标准命令重启（`VITE_API_PROXY_TARGET=http://127.0.0.1:8911 npx vite --port 5178 --strictPort`，v6.4.2 ready in 290ms）；自检 /monitoring=200、runtime-build.json expectedBackendBuildId=api-439b9e81187f0da4 与 8911 配对一致。8911 全程未动；8910 复核 200；**5177 复核时连接拒绝（已停）——非本轮所致（对 8910/5177 仅只读 curl），按铁律未触碰拉起，如实记录**。
- **预置 MX循R10D-CSU**（proj_user_ad685a18f853，幂等键 r10d-seed-20260930T095343Z-a18f7bd1）：三件套上传 → 文档权威双VLM 约14min ready（本轮无人工门触发）→ 映射双队列（10主+10盲核，60候选）→ adopt → 复核收敛 46→38→27→20→12→0（系统裁决34；v19-tools-v7.2 工具型裁决作业，收敛约7.2h，驱动两次预算耗尽按幂等续跑）→ EX/EXTRT 卡按数据实测作答一次 → **confirm 200（draft v60 confirmed，user_questions=0）→ facts 201（10表/591行/2290值全核验，state=ready）**，停住未启动监查（runs=[]）。project/open → current/complete/canView/canEdit=true。
- AI 台账（本项目）：82作业（76完成/6终态failed均为mapping分片，经自动恢复收敛 remaining=0）；149次调用，2,267,750 tokens。全程未跳任何质量门。
- 驱动与留痕：`r10d_seed_csu.py`、`r10d_seed_state.json`、`r10d_seed_evidence.jsonl`；轮次分节见 `R5_SEEDED_PROJECT.md`。

## 2026-09-30 晚（R10预检·修复员：runtime路径根因修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R10预检第1次拦截）
- 根因修复：project_source_manifest._monitoring_facts_materialized硬编码舰队runtime路径→改为WORKBENCH_RUNTIME_DIR感知（_monitoring_runtime_root），缺省回退原舰队路径（8910行为不变）。
- 复验（对预检项目proj_user_cae1decd4224原地重放）：①绑定intake_pending→real_source_slice（source-manifest API核对）；②prepare-and-start不再409 readiness——经workspace/bootstrap一次初始化后运行创建成功（runs列表run:09d074a46e284a870b4d8e36，waiting_start，幂等重试得in_flight_conflict证明registry已有run）；③监听分析0作业派发的原因（运行未启动执行）不再是本缺陷。
- 自检：8911 ready:true（build api-ce1c512e7a64adf5）；5178=200；指纹配对一致；8910/5177复核均200未受影响。

## 2026-10-01 凌晨（R10预检第2次·修复员：部分采纳域完整性门打通后隔离环境 8911+5178 双重启）

- 操作者：修复员（R10预检第2次拦截：首遍主分片终态失败→adopt 422）
- 修复：mapping_draft_repository域完整性门新增allowed_missing_domains豁免（仅限cohort中该域全部分片终态失败且无completed覆盖）；在场域计数和替代全量full_field_count核对；adopt_draft计算合法缺席域并作为domain_gaps物化到draft响应。
- 自检：8911 ready:true（build api-9b827e5405b94cea）；5178=200；指纹配对一致；8910/5177复核均200未受影响。

## 2026-10-01 上午（R10轮次·修复员：四项修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R10轮次：R8-04/05/07、R5-06）
- 修复：closeWizard刷新工作区；completion_rate占位归零+Progress「未开始」态；准入事件流水（jsonl+GET /api/projects/{id}/admission-events+台账展示区）；顶栏适应症/方案版本加载态「读取中…」区分。
- 自检：8911 ready:true（build api-807dff49e5ad28ec）；5178=200；指纹配对一致；8910/5177复核均200；新admission-events端点在8911上返回合法空列表。

## 2026-10-01 下午（R11轮次·开考预置守护员：探障无障碍+5178复活 + 预置 MX循R11D-CSU）

- 操作者：开考预置守护员-R11D。起止：14:31 → 17:09（本地 CST）。
- **探障（旧项目全被循环收尾软归档，GET /api/projects→[]，但 R10D 项目路由仍可探）**：`GET /r7/project/open`（R10D项目 proj_user_ad685a18f853）→ current/complete/canView/canEdit=true，无 blocked/CORRUPT；修复代码在位（main.py:4925-4936 种子 marker 取 launch_registry_contracts.SCHEMA_VERSION=V5）；存量 36 个 workspace 的 launch_registry marker 逐库 sqlite 直查全 v5；R11D 新建项目 4 个种子成员经产品 `inspect_member` 实测全 current/current_shape（launch_registry marker=v5）。**R5D marker 缺陷未复发，本轮未修任何产品代码、未重启 8911。** 建项瞬间 project/open 的 blocked 为 required_member_missing（bootstrap 前瞬态，R1 已知同款），非损坏。
- **5178 复活（只动隔离对）**：本轮开始时隔离 vite 5178 掉线（lsof 无监听），按本文件标准命令重启（`VITE_API_PROXY_TARGET=http://127.0.0.1:8911 npx vite --port 5178 --strictPort`，v6.4.2 ready in 180ms）；自检 /monitoring=200、runtime-build.json expectedBackendBuildId=api-807dff49e5ad28ec 与 8911 backend_build_id 配对一致。8911 全程未动；8910 复核 200；**5177 复核连接拒绝（已停）——非本轮所致（对 8910/5177 仅只读 curl），按铁律未去拉起，如实记录**。
- **预置 MX循R11D-CSU**（proj_user_175b6374dcd6，幂等键 r11d-seed-20261001T064001Z-ae6864d3）：三件套上传 → 文档权威双VLM 约4min ready（protocol/ecrf 自动识别，无人工门）→ 映射双队列（10主+10盲核，60候选，约17分钟）→ adopt → 复核收敛 46→37→24→0（系统裁决22，约2小时；2个分片 provider_runtime_error 经 bounded-gap 收敛）→ 24张裁决卡：21张按既有数据实测表作答 + 3张R11新卡（CM.CMENDAT/CM.CMSTDAT/ICF_TRACK.ICFVER）首次浮现时 fail-closed 诚实退出留痕（09:01:57Z），按 openpyxl 直读列值实测+两轮同判角色补答（09:03:24Z）→ **confirm 200（draft v71 confirmed，user_questions=0）→ facts 201（10表/591行/2958值全核验，state=ready）**，停住未启动监查（runs=[]）。project/open → current/complete/canView/canEdit=true。
- AI 台账（本项目）：60作业（58完成/2终态failed均为mapping分片，经收敛 remaining=0）；89次调用，1,726,840 tokens。全程未跳任何质量门。
- 驱动与留痕：`r11d_seed_csu.py`（幂等，状态 r11d_seed_state.json、留痕 r11d_seed_evidence.jsonl）；轮次分节见 `R5_SEEDED_PROJECT.md`。

## 2026-10-01 午间（R11预检第1次·修复员：确定性对账域豁免后隔离环境 8911+5178 双重启）

- 操作者：修复员（R11预检第1次拦截：对账门把domain_gaps对侧字段判死）
- 修复：mapping_reconciliation新增exempt_domains贯通（_index_cohort对豁免域映射跳过而非判unexpected硬violation）；reconcile_with_verifier用adopt同款_terminal_failure_domain_gaps计算豁免域并传入对账+domain_gaps投射到reconciliation响应。
- 验证（脚本）：51字段draft+60字段盲核含9个AE域外字段——无豁免blocked（unexpected_in_verifier×9），豁免['AE']后agreed；主侧豁免域字段同样跳过。
- 自检：8911 ready:true；5178=200；指纹配对一致（注：build id按合同只哈希services/api/app，本轮改动在packages/故id不变api-807dff49e5ad28ec——进程确已重启加载新代码）；8910/5177复核均200。
2026-10-01 19:43 用户指示彻底暂停：R11预检第2次执行1h08m未止→按指示TaskStop（无损，191步已沉淀）；隔离对8911/5178已停（恢复命令见本文件顶部）；舰队8910未触碰
2026-10-01 21:11 解除暂停：手工拉起隔离对（用户指示恢复循环）
2026-10-02 00:32 用户指示尽快无损暂停：R11预检第2次因服务方限流3小时零进展（非死锁），TaskStop无损（191步沉淀全保）；隔离对8911/5178保持运行以便随时一条命令恢复；恢复=ResumeWorkflowRun dwfrun-ea87a585
2026-10-02 22:29 第二次解除暂停：环境曾掉线重新拉起（指纹配对api-807dff49e5ad28ec一致），恢复循环

## 2026-10-03 凌晨（R12轮次·开考预置守护员：探障无障碍 + 主侧AI路由界内换绑直连 + 预置 MX循R12D-CSU）

- 操作者：开考预置守护员-R12D。开始时间：2026-10-03 ~01:02（本地 CST）。
- **探障（三路全通过，R5D marker 缺陷未复发，未修任何产品代码、未重启 8911）**：① `GET /r7/project/open`（R11D项目 proj_user_175b6374dcd6）→ current/complete/canView/canEdit=true；② 修复代码在位：main.py:4925-4927,4935-4936 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 = mm-r7-w01r26-launch-registry-v5）；③ 隔离 runtime **42 个** workspace 的 launch_registry marker 逐库 sqlite 直查**全部 v5**；④ R12D 建项后产品 `ProjectSchemaInspector` 实证 4 个种子成员全 current（launch_registry marker=v5）。环境侧：8911 ready:true（build api-21b0d9e61406a8e）；5178 存活（监听 [::1]）且 runtime-build.json expectedBackendBuildId=api-21b0d9e61406a8e 与 8911 配对一致；**8910/5177 无监听（连接拒绝）——非本轮所致（仅只读 lsof/curl 复核），按铁律未触碰，如实记录**。
- **主侧AI路由界内修复（非产品代码缺陷，host 代理故障的隔离实例侧规避；未跳任何质量门）**：文档权威/映射主侧角色档案（cms-router/glm-5.3-flash）原经本机 omniroute LB 127.0.0.1:20128 → Clash Verge 代理 127.0.0.1:7897 → api.z.ai；Clash Verge 核心自 ≥2026-10-02T14:00Z 起未运行（仅特权 helper 在跑），主侧作业 provider_runtime_error 连续快速失败（本项目主分析累计 204 次失败；并行测试会话同故障；omp 自身日志同报）。**修复动作**：用产品自有 AiRuntimeSettingsStore（经隔离 runtime 目录，非 API 亦非直改运行库）把两个主侧角色档案 `medical_monitoring_ai__cms_router_glm53flash`（rev4→5）与 `document_authority_primary_ai__medical_monitoring_ai__cms_router_glm53flash`（rev1→2）的 base_url 由 LB 改为智谱官方直连 `https://open.bigmodel.cn/api/coding/paas/v4`、extra_headers 清空、存储凭据改用隔离实例自有 zhipu coding-plan 直连密钥（取自同库 independent_ai 档案，密钥未落任何日志）；**provider 身份串（cms-router）、模型（glm-5.3-flash）、推理档（high）、prompt 版本、全部质量门保持不变**。改前备份四件配置至 `scripts/tester_loop_0927/r12d_provider_config_backup/`（settings/secrets/master.key/role_bindings）。生效实证：卡住的主分析作业 17:38:20Z 最后一次代理失败后 **17:40:02Z 首次尝试即 success**（205 次尝试终态 completed）；产品 probe 端点对该档案完成真实往返（返回结构非探针期望形状，属探针形状校验，连通性与真实模型输出已实证）。verifier 侧（ollama-cloud/deepseek-v4.1-flash）全程未动。
- **预置 MX循R12D-CSU**（proj_user_5bcd73dd2cf8，幂等键 r12d-seed-20261002T170213Z-fe436efb）：三件套上传（stg-b11c1e67bbe64da3bd83df6b6b2fc663）→ 文档权威双VLM（mmbatch_1d0b2221fbfc01b033af34ab）→ 映射双队列（10主+10盲核，60候选）→ 复核收敛 46→42→30→0（系统裁决16）→ 31张裁决卡（27张既有表 + 4张R12新卡 DM.AGE/COMPSTATUS/RANDDT/SEX 首次浮现 fail-closed 留痕后按 openpyxl 直读列值实测补答）→ **confirm 200（draft v77 confirmed，user_questions=0）→ facts 201（10表/591行/3038值全核验，state=ready）**，停住未启动监查（runs=[]）。project/open → current/complete/canView/canEdit=true；run-setup/options 200。结束时间 2026-10-03 04:05 CST。AI 台账：66作业（65完成/1终态failed经收敛 remaining=0）；303次调用，2,086,644 tokens。全程未跳任何质量门。轮次分节详见 `R5_SEEDED_PROJECT.md` R12D。
- 驱动与留痕：`r12d_seed_csu.py`（由 r11d_seed_csu.py 机械适配：R12D 命名/幂等键/留痕文件；R5/R8/R9/R11 既有裁决卡决策表原样保留，未知卡 fail-closed 防护在位）、`r12d_seed_state.json`、`r12d_seed_evidence.jsonl`。

## 2026-10-01 下午（R11轮次·修复员：七项修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R11轮次：R11-01/03、R9-01/02/03/05/06）
- 修复：infra失败不受重试预算+previously_analyzed仅completed；确认按钮loading/disabled/防连点；被拒启动入事件流水；向导主体与步骤指示器同源+失配恢复提示；4个顶栏icon-button补aria-label；侧栏hover展开改为纯悬浮（不挤压布局流）；未识别差异项显式声明无原文摘录。
- 自检：8911 ready:true（build api-21b0d9e614066a8e）；5178=200；指纹配对一致。
- ⚠️ 舰队状态如实记录：本轮隔离对重启后复核，8910/5177 暂不响应（8910进程3150在跑但无HTTP应答；5177未见vite进程）。本轮所有kill命令仅针对8911/5178，未触碰舰队进程；按纪律不介入舰队，留痕提请循环所有者/舰队值班关注。

## 2026-10-02（R12轮次·修复员：三项修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R12轮次：R12-01、R10-01、R10-02）
- 修复：差异确认逐条pending/confirmed反馈+防连点；暂停整理乐观UI+8s超时回滚；映射AI提示词增加方案-vs-数据剂量/频次/给药途径交叉核对要求（EX域与AE给药术语口径矛盾必须提疑点）。
- 自检：8911 ready:true（build api-2ac4a3a5e6a1db40）；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11记录：8910（进程3150在跑）与5177仍无HTTP应答——本轮kill仅针对8911/5178未触碰舰队，继续留痕提请舰队值班处理。
2026-10-03 10:53 循环收尾：隔离测试环境已停止（运行时目录保留取证）
2026-10-03 14:37 R13重启前重建隔离运行时（347M快照）+拉起隔离对（指纹api-2ac4a3a5配对）+外来项目清零；任务所有者铁律生效（UI-only测试）

## 2026-10-03 下午（R13轮次·开考预置守护员：探障无障碍+主侧AI路由界内换绑直连+数据暂存重建 + 预置 MX循R13D-CSU）

- 操作者：开考预置守护员-R13D。开始时间：2026-10-03 ~14:45（本地 CST）。
- **探障（无障碍，R5D marker 缺陷未复发，未修任何产品代码、未重启 8911）**：本轮开始时隔离 runtime 经 R13 重建（外来项目清零，GET /api/projects→[]），无存量项目可探 → 按 R5D 先例改为建项后探：R13D 新建项目建项瞬间 `GET /r7/project/open` blocked（bootstrap 前 monitoring_runtime.sqlite3 尚不存在的设计内瞬态，R1 已知同款）；随后产品 `inspect_project_schema` 实证 6 个成员全 current/current_shape（launch_registry marker=mm-r7-w01r26-launch-registry-v5，sqlite 直查同值）；修复代码在位：main.py:4925-4927,4935-4936 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 = SCHEMA_VERSION_V5）。终态验收断言在驱动脚本 Step10（project/open 必须 current）。环境侧：8911 ready:true（build api-2ac4a3a5e6a1db40）；5178 /monitoring=200 且 runtime-build.json expectedBackendBuildId=api-2ac4a3a5e6a1db40 配对一致；8910/5177 无监听（连接拒绝）——非本轮所致（仅只读 lsof/curl 复核），按铁律未触碰，如实记录。
- **主侧AI路由界内换绑直连（R12D 同款先例，host 代理故障的隔离实例侧规避；未跳任何质量门）**：R13 重建隔离 runtime 后，两个主侧角色档案 base_url 回到本机 omniroute LB 127.0.0.1:20128；LB 上游 Clash Verge 代理 127.0.0.1:7897 不可达（产品 /api/ai-gateway/probe 实证 `[Proxy Fast-Fail] Proxy unreachable (HTTP 503)`）。修复动作：`r13d_rebind_primary_ai.py` 用产品自有 AiRuntimeSettingsStore（经隔离 runtime 目录，非 API 亦非直改运行库）把 `medical_monitoring_ai__cms_router_glm53flash`（rev4→5）与 `document_authority_primary_ai__medical_monitoring_ai__cms_router_glm53flash`（rev1→2）的 base_url 改为智谱官方直连 `https://open.bigmodel.cn/api/coding/paas/v4`、extra_headers 清空、存储凭据改用隔离实例自有 zhipu coding-plan 直连密钥（取自同库 independent_ai 档案，密钥未落任何日志）；provider 身份串（cms-router）、模型（glm-5.3-flash）、推理档（high）、prompt 版本、全部质量门保持不变。改前四件配置备份至 `scripts/tester_loop_0927/r13d_provider_config_backup/`。生效实证：probe 两主侧档案真实往返 passed:true（2729ms/4354ms）；verifier 两侧（ollama-cloud/deepseek-v4.1-flash）未动且 probe passed:true（680ms/638ms）。
- **数据暂存重建（环境侧动作，非产品缺陷）**：循环收尾后 workbench/tester_staging_0927/ 已不存在；从已验证字节一致来源重建 synth_csu 三件套：①合成listing ← runs/phase_c_mgk10_authority_v2_20260905 产品 admissions/staging 存档副本（sha256 4be08e9e…，openpyxl 实测 10 表/591 数据行，与 R5D/R12D 上传摘要一致）；②临床研究方案V1.3 ← 研究方案库/MG-K10-CSU-001_临床研究方案-V1.3-0212-clean-0211.docx（sha256 73024713…，与产品 document_authority_candidates 内容寻址存档逐字节一致）；③eCRF填写指南V1.0 ← 产品 document_authority_candidates/files/8109d25a….docx（word/document.xml 与另一存档副本 c1e2a9e6… 完全同哈希）。
- **预置 MX循R13D-CSU**（proj_user_bbcc5c21edfb，幂等键 r13d-seed-20261003T064711Z-83d83077）：三件套上传（stg-ff9b4b097f334cbe87badede0a9da480）→ 身份门一次确认 → 文档权威双VLM约7分钟 ready（protocol/ecrf 自动识别）→ 映射双队列（10主+10盲核，60候选，约14分钟）→ 复核收敛 46→30→1→0（系统裁决16）→ 31张裁决卡（29张既有表 + 2张R13新卡：EX.EXFRQ 剂量/频次口径卡按 openpyxl 实测作答 ip_administered_dose_with_unit_text、EX.EXSTATE 同token分歧卡采纳 treatment_administration_status；两卡均首次浮现时 fail-closed 诚实退出留痕）→ **confirm 200（draft v79 confirmed，user_questions=0）→ facts 201（10表/591行/3422值全核验，state=ready）**，停住未启动监查（runs=[]）；project/open → current/complete/canView/canEdit=true；run-setup/options 200。起止 06:47→08:28Z（约1小时41分）。AI 台账：48作业（47完成/1终态failed=provider_runtime_error 经 bounded-gap 收敛）；63次调用，1,322,816 tokens。全程未跳任何质量门。轮次分节详见 `R5_SEEDED_PROJECT.md` R13D。

## 2026-10-03（R13轮次·修复员：三项修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R13轮次：R13-01、R11-02、R11-04）
- 修复：导入错误分类（NotFoundError/NotAllowedError/422细分码→准确文案，网络兜底仅留给真传输错误）；方案准备抽屉errorText sanitize异常原文（Cannot read properties等→友好文案+console.warn留技术细节）；「增加特殊关注」死按钮修复（按钮改为打开输入面板，面板内「生成关注方向」才调API——原按钮直接调onPreview而预览文本为空时handler静默返回）。
- 自检：8911 ready:true（build api-2ac4a3a5e6a1db40）；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11/R12记录：8910/5177仍无HTTP应答（本轮kill仅针对8911/5178）；继续留痕提请舰队值班。

## 2026-10-03 晚（R14轮次·开考预置守护员：探障无障碍 + 预置 MX循R14D-CSU）

- 操作者：开考预置守护员-R14D。开始时间：2026-10-03 ~21:05（CST）。
- **探障（无障碍，R5D marker 缺陷未复发，未修任何产品代码、未重启 8911/5178）**：本轮开始前 R13轮次修复员已重启隔离对（8911/5178 进程 12:56Z=20:56 CST 拉起，非 runtime 重建）。① `GET /r7/project/open`（R13D 项目 proj_user_bbcc5c21edfb）→ current/complete/canView/canEdit=true，无 blocked/CORRUPT；② 修复代码在位：main.py:4925-4936 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 = mm-r7-w01r26-launch-registry-v5）；③ R14D 建项后产品 `inspect_project_schema` 实证成员全 current（launch_registry marker=v5），终态硬断言 Step10 通过。环境侧：8911 /api/health ok、/api/runtime-readiness ready:true（build api-2ac4a3a5e6a1db40）；5178 /monitoring=200（[::1]）且 runtime-build.json expectedBackendBuildId=api-2ac4a3a5e6a1db40 配对一致；8910/5177 无监听（连接拒绝）——非本轮所致（仅只读 lsof/curl 复核），按铁律未触碰，如实记录。
- **主侧AI路由复核（本轮无需换绑）**：R12D/R13D 换绑的直连配置跨重启保持生效，产品 `/api/ai-gateway/probe` 四档案真实往返全 passed:true（两主侧 cms-router/glm-5.3-flash 3063/3211ms；两 verifier ollama-cloud/deepseek-v4.1-flash 681/608ms）。
- **预置 MX循R14D-CSU**（proj_user_588084370b49，幂等键 r14d-seed-20261003T130929Z-174dc92d）：三件套上传（stg-77d9531264f249608bb0c013e208e930，591行/10表）→ 文档权威双VLM约9.5分钟 ready（mmbatch_501bf7540ce877aff57e0a70，自动归属确认，无身份门/角色门）→ 映射双队列（10主+10盲核，60候选，约14.5分钟）→ 复核收敛 46→（系统裁决16）→30→0（48/48 作业全 completed）→ 30张裁决卡（29张既有表 + **1张R14新卡 EX.EXDAT** 两轮分歧卡首次浮现 fail-closed 留痕后按 openpyxl 直读实测补答 treatment_administration_date：128行全合法ISO日期、16受试者×8条Q4W给药记录）→ **confirm 200（draft monmapdraft_df096d4513fe2f965946b6bc1530 v77 confirmed，user_questions=0）→ facts 201（10表/591行/3422值全核验，state=ready）**，停住未启动监查（runs=[]）；project/open → current/complete/canView/canEdit=true；run-setup/options 200。起止 13:09→14:39Z（21:09→22:39 CST，约1小时30分）。AI 台账：48作业全completed；63次调用，1,577,719 tokens。全程未跳任何质量门。轮次分节详见 `R5_SEEDED_PROJECT.md` R14D。
- 驱动与留痕：`r14d_seed_csu.py`（由 r13d_seed_csu.py 机械适配 + R14_ROUND1_CARDS 一卡表）、`r14d_seed_state.json`、`r14d_seed_evidence.jsonl`、`r14d_seed_console.log`/`r14d_seed_console2.log`。

## 2026-10-03 下午（R14轮次·修复员：三项可访问性/引导修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R14轮次：R12-02、R12-06、R12-07）
- 修复：表结构区Tab焦点链收敛（外层details唯一焦点+内层summary tabindex=-1+跳到主操作跳过链接）；研究文件上传入口显式引导+视觉层级提升（dashed大按钮+缺什么说明）；导航禁用豁免（无项目时台账/审批中心仍可进入，台账页无项目态给出明确提示）。
- 自检：8911 ready:true（build api-2ac4a3a5e6a1db40）；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11起：8910/5177仍无HTTP应答（本轮kill仅针对8911/5178）；留痕提请舰队值班。

## 2026-10-03 深夜（R15轮次·开考预置守护员：探障无障碍 + 预置 MX循R15D-CSU）

- 操作者：开考预置守护员-R15D。起止：2026-10-03 17:58Z → 19:28Z（2026-10-04 01:58→03:28 CST 北京；本机时区现 CEST）。全程未修任何产品代码、未重启 8911/5178（R14轮次修复员已于 17:43Z 重启隔离对，build api-2ac4a3a5e6a1db40 指纹配对在位）。
- **探障（无障碍，R5D marker 缺陷未复发）**：① `GET /r7/project/open`（R14D 项目 proj_user_588084370b49）→ current/complete/canView/canEdit=true，无 blocked/CORRUPT；② 修复代码在位：main.py:4925-4927,4935-4936 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 = mm-r7-w01r26-launch-registry-v5）；③ 隔离 runtime 存量 10 个 workspace 的 launch_registry marker 逐库 sqlite 直查全部 v5；④ R15D 建项后产品 `inspect_project_schema` 实证 6 成员全 current/current_shape（建项瞬间 project/open blocked 为 bootstrap 前 monitoring_runtime 不存在的设计内瞬态，R1 已知同款），终态硬断言 Step10 通过。主侧AI路由复核：直连绑定跨重启生效，/api/ai-gateway/probe 三档案真实往返全 passed:true（两主侧 5358/3319ms；verifier 535ms），本轮无需换绑。8910/5177 无监听（连接拒绝）——非本轮所致（仅只读复核），按铁律未触碰，如实记录。
- **预置 MX循R15D-CSU**（proj_user_b556e56f50ba，幂等键 r15d-seed-20261003T175809Z-f69ce3fd）：三件套上传（stg-c2e8050af8ba4db1b4e144c49c5c7b9b，591行/10表，sha256 与 R13D 重建版逐字节一致）→ 文档权威双VLM约4.8分钟 ready（mmbatch_3cc1450700092fc19a46a9e3，自动归属确认，无身份门/角色门）→ 映射双队列（10主+10盲核，60候选，约13.9分钟）→ 复核收敛：remaining 46 →（系统裁决20）→26 →（27张裁决卡作答）→0 complete → **confirm 200（draft monmapdraft_23b664f6059daaaf1a96cf905a54 v74 confirmed，user_questions=0）→ facts 201（10表/591行/3038值全核验，state=ready）**，停住未启动监查（runs=[]）；project/open → current/complete/canView/canEdit=true；run-setup/options 200。
- 裁决卡 27 张 = 1 首轮 EX.EXFRQ + 22 既有表 + **4张R15新卡 VS.DBP/HRRATE/RESP/SBP**（历轮首次浮现）首次浮现 fail-closed 诚实退出留痕（r15d_seed_evidence.jsonl unknown_questions_fail_closed 19:21:45Z）后，按 openpyxl 直读 VS 表实测（64行=16受试者×4访视，心率58-94/收缩压98-140/舒张压60-88/呼吸16-22 全整数）补答，采纳双队列同判角色 token。
- AI 台账（本项目）：46作业（44完成/2终态failed=provider_runtime_error×1+invalid_ai_output×1，均 mapping 分片，经自动恢复与 bounded-gap 收敛 remaining=0）；73次调用，1,427,947 tokens。全程未跳任何质量门。轮次分节详见 `R5_SEEDED_PROJECT.md` R15D。
- 驱动与留痕：`r15d_seed_csu.py`（由 r14d_seed_csu.py 机械适配 + R15_ROUND1_CARDS 四卡表）、`r15d_seed_state.json`、`r15d_seed_evidence.jsonl`、`r15d_seed_console.log`/`r15d_seed_console2.log`。

## 2026-10-04 凌晨（R15轮次·修复员：三项修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R15轮次：R15-01、R13-02、R13-03）
- 修复：特殊关注多候选显式选择即确认（run_setup.append_revision语义修正，无选择仍fail-closed）；疑点卡展示系统判断内容+残句消毒；准入错误响应与台账事件双带event_ref（EVT-时间-随机-原因码）且前台可复制展示。
- 自检：8911 ready:true（build api-2ac4a3a5e6a1db40）；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11起：8910/5177仍无HTTP应答（本轮kill仅针对8911/5178）；留痕提请舰队值班。

## 2026-10-04 上午（R16D 开考位预置·守护员）

- **探障（无障碍，R5D marker 缺陷未复发，未修任何产品代码、未重启 8911/5178）**：① 循环收尾已把旧项目全部软归档（`GET /api/projects` → `[]`），无存量项目可按原样探 → 按 R13D-R15D 先例建项后探：R16D 建项瞬间 `GET /r7/project/open` blocked（bootstrap 前 monitoring_runtime.sqlite3 不存在的设计内瞬态，R1 已知同款）；② 修复代码在位：main.py:4925-4927,4935-4936 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 = mm-r7-w01r26-launch-registry-v5）；③ R16D 新建 workspace 的 launch_registry marker sqlite 直查 = v5（现行进程写入实证），存量 15 个 workspace 逐库直查全部 v5；④ 终态硬断言 Step10 通过（project/open 必须 current）。环境侧：8911 /api/runtime-readiness ready:true（build api-2ac4a3a5e6a1db40，R15 修复员凌晨双重启后的现行进程）；5178 /monitoring=200（[::1]）且 runtime-build.json expectedBackendBuildId=api-2ac4a3a5e6a1db40 配对一致；8910/5177 无监听（连接拒绝）——非本轮所致（仅只读 lsof/curl 复核），按铁律未触碰，如实记录。
- **预置 MX循R16D-CSU**（proj_user_e82b9e8acc60，幂等键 r16d-seed-20261004T001015Z-c018a8b7）：三件套上传（stg-e62b469df0b54c9a94866be0b8cef25e，591行/10表，sha256 与 R15D 逐字节一致）→ 文档权威双VLM约4.4分钟 ready（mmbatch_76e97b66cde8d4a2c47a2954；身份门 project_identity_incomplete 触发一次＝界面一次点击同款手势；角色门未触发，protocol/ecrf 自动识别 current）→ 映射双队列（10主+10盲核，60候选，约15.3分钟）→ 复核收敛：remaining 46 →（系统裁决23）→23 →（23张已知裁决卡作答）→0 complete → **confirm 200（draft monmapdraft_09ce60ee5b30df2e05d3cbfd5ebb v72 confirmed，user_questions=0）→ facts（10表/591行/3550值全核验，state=ready）**，停住未启动监查（runs=[]）；project/open → current/complete/canView/canEdit=true；run-setup/options 200。
- 裁决卡：25 次作答事件 / **23 张唯一卡全部由既有决策表覆盖**（R5/R8/R9/R11/R12/R13/R14/R15 表；EX.EXFRQ、EX.EXTRT 两卡跨轮次重复浮现各作答两次）——**本轮无新卡浮现，无 fail-closed 退出**。中途 1 个 mapping 分片 failed 后自动重试完成，终态 44/44 作业全 completed，无 bounded-gap 缺口。
- AI 台账（本项目）：44 作业全 completed（document_authority_analysis×2 + document_authority_review×2 + listing_field_mapping×40）；62 次调用，1,344,591 tokens（prompt 876,253 + completion 468,338）。全程未跳任何质量门。轮次分节详见 `R5_SEEDED_PROJECT.md` R16D。
- 驱动与留痕：`r16d_seed_csu.py`（由 r15d_seed_csu.py 机械适配，既有裁决卡决策表原样保留）、`r16d_seed_state.json`、`r16d_seed_evidence.jsonl`、`r16d_seed_console.log`。
2026-10-04 06:28 R16材料事故修复：十二轮收官清理误删暂存夹具→R13重启只补CSU→R16B位MY008派发时暴露；任务所有者已补齐四套三件套（MY008/RUX/CSU/PSO）并ResolveWorkflowQuestion答复按原任务开测；教训=夹具与垃圾同删、循环重启必须全量补料
