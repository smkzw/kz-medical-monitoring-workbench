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
2026-10-04 10:23 第三次无损暂停（用户确认卡死后指示直接结束）：R16B位测试者卡服务方限流（token冻结979,499,000、6h12m零进展超5h纪律上限）→TaskStop；R16A/C/D已交卷在档；恢复=ResumeWorkflowRun dwfrun-513b9893（B位将重派）

## 2026-10-04（R16轮次·修复员：R16-01修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R16轮次：R16-01）
- 修复：resolve路由补GET变体（batch_id查询参数，与POST同语义；缺参给可读422非404）；前端轮询catch显式route_not_found/404分支→failed态+如实提示，不再无限静默。
- 自检：8911 ready:true（build api-2ac4a3a5e6a1db40——packages/改动不入build指纹但进程已重启加载新代码）；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11起：8910/5177仍无HTTP应答（本轮kill仅针对8911/5178）；留痕提请舰队值班。

## 2026-10-04 晚（R17D 开考位预置·守护员）

- **探障（无障碍，R5D marker 缺陷未复发，未修任何产品代码、未重启 8911/5178）**：① 循环收尾已把旧项目全部软归档（`GET /api/projects` → `[]`），无存量项目可按原样探 → 按 R13D-R16D 先例建项后探：R17D 建项瞬间 `GET /r7/project/open` blocked（bootstrap 前 monitoring_runtime.sqlite3 不存在的设计内瞬态，R1 已知同款）；② 修复代码在位：main.py:4925-4927,4935-4936 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 = mm-r7-w01r26-launch-registry-v5）；③ 建项前存量 20 个 workspace 的 launch_registry marker 逐库 sqlite 直查全部 v5；④ R17D 建项后产品 `inspect_project_schema` 实证 6 成员全 current/current_shape（launch_registry marker=v5），终态硬断言 Step10 通过（project/open 必须 current）。主侧AI路由复核：直连绑定跨重启生效，/api/ai-gateway/probe 双档案真实往返 passed:true（主侧 cms-router/glm-5.3-flash 3577ms；verifier ollama-cloud/deepseek-v4.1-flash 1018ms），本轮无需换绑。环境侧：8911 ready:true（build api-2ac4a3a5e6a1db40）；5178 存活（node 67415，[::1]:5178）；8910/5177 无监听（连接拒绝）——非本轮所致（仅只读 lsof/curl 复核），按铁律未触碰，如实记录。
- **预置 MX循R17D-CSU**（proj_user_6d794c3dfd2f，幂等键 r17d-seed-20261004T132225Z-4d453cfc）：三件套上传（stg-ed22e6108aa04ace9423b87c542da86f，591行/10表，sha256 与 R15D/R16D 逐字节一致）→ 文档权威双VLM约10.5分钟 ready（mmbatch_7e9b2f05ba8cfcbcbb237f18，自动归属确认，无身份门/角色门）→ 映射双队列（10主+10盲核，60候选，约20分钟）→ 复核收敛：16次 adjudicate_drive 多轮双队列（终轮 blocked remaining=9/系统裁决37 → 9张裁决卡作答 → complete remaining=0；5个 mapping 分片终态 failed=provider_runtime_error retryable，经自动恢复与系统裁决收敛）→ **confirm 200（draft monmapdraft_053c44ea0607a6086bb7d1b27dda v58 confirmed，user_questions=0）→ facts 201（10表/591行/1896值全核验，state=ready）**，停住未启动监查（runs=[]）；project/open → current/complete/canView/canEdit=true；run-setup/options 200。起止 13:22:25Z→19:25:01Z（约6小时03分，其中复核收敛约5.5小时为本循环历轮最慢，提请循环所有者留意 provider 侧时延；facts values 计数1896较近轮偏低已如实记录差异）。AI 台账：102作业（97完成/5终态failed经收敛 remaining=0）；193次调用，2,947,513 tokens。全程未跳任何质量门。轮次分节详见 `R5_SEEDED_PROJECT.md` R17D。
- 驱动与留痕：`r17d_seed_csu.py`（由 r16d_seed_csu.py 机械适配，既有裁决卡决策表原样保留）、`r17d_seed_state.json`、`r17d_seed_evidence.jsonl`、`r17d_seed_console.log`。

## 2026-10-05（R17轮次·修复员：五项修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R17轮次：R17-01/02/03、R15-02/04）
- 修复：疑点作答陈旧会话守卫改提示+自动重拉（不再静默丢弃）；映射错误在向导第3步面板内醒目渲染（含event_ref）；第2步补「返回上一步，重新选择数据」（回第1步重选数据源，服务端staging支持重走）；未配置模块页新增各模块前置链激活指引；字段关卡术语统一为「字段映射确认/研究文件与字段映射确认」。
- 自检：8911 ready:true；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11起：8910/5177仍无HTTP应答（本轮kill仅针对8911/5178）；留痕提请舰队值班。

## 2026-10-05 上午（R18D 开考位预置·守护员：受阻于主侧AI服务方计划级限流，未修码未重启）

- **探障（R5D marker 缺陷未复发，未修任何产品代码、未重启 8911/5178）**：① 存量隔离项目直探：R17D（proj_user_6d794c3dfd2f）/R17P（proj_user_20c4a3880375）`GET /r7/project/open` 均 state=current/openMode=edit/dataCoverage=complete（两项目虽被循环收尾软归档，直接 API 访问仍可探）；② 隔离 runtime 全部 25 个 workspace 的 launch_registry marker 逐库 sqlite 直查全部 = mm-r7-w01r26-launch-registry-v5；③ 修复代码在位复核：main.py:4925-4927,4935-4936 种子 marker 取 `launch_registry_contracts.SCHEMA_VERSION`（contracts.py:53-54 = v5）；④ R18D 新建 workspace marker sqlite 直查 = v5（现行进程写入实证）；⑤ `proj_mgk10_sar_real` open=blocked 系该参考项目 workspace 不在本隔离 runtime（且已归档），非 marker 缺陷。⑥ 8911 /api/runtime-readiness 正常应答、5178 node 存活（[::1]）；8910/5177 无监听（连接拒绝）——非本轮所致（仅只读 lsof/curl 复核），按铁律未触碰，如实记录。
- **预置 MX循R18D-CSU（进行中，卡在文档权威门）**：建项 proj_user_74e02b4af07c（201，幂等键 r18d-seed-20260905T031600Z-dddcb662）→ 三件套上传 stg-87131078840646e1984b76b8fa1fb0fb（591行/10表，sha256 与 R15D/R16D/R17D 逐字节一致）→ 文档权威批次 mmbatch_1f38738598938b07f25dc852：verifier 侧（ollama-cloud/deepseek-v4.1-flash）03:21:17Z completed（1 次成功，25,568 tokens）；主侧（cms-router/glm-5.3-flash 直连 open.bigmodel.cn）持续 HTTP 429——截至 08:20Z 已 1,602 次尝试全部 429、产品 infra 失败自动恢复（R11-01 设计）反复 requeue 仍无法穿透。
- **卡点定性（服务方计划级配额冻结，非产品缺陷）**：/api/ai-gateway/probe 对两个 zhipu 计划档案（medical_monitoring_ai__cms_router_glm53flash 与 independent_ai__zhipu_coding_plan_glm_flash）均 429，verifier 档案 passed:true；台账显示主侧最后一次成功 = 01:16:12Z，此后连续 >7h 零成功（超循环 R16B 事件 5h 零进展纪律线）；本隔离环境主侧消耗 10-03=8.45M、10-04=42.27M、10-05（冻结前）=5.88M tokens。本轮不改绑主侧档案（R12D/R13D 起的直连绑定属循环所有者决策，换绑属越权+改变测试条件），不跳门不造假。
- **恢复路径（已就绪，无需人工干预）**：监督循环 r18d_supervise.sh（nohup 存活，独立于守护员会话）每 50 分钟重拉幂等驱动 r18d_seed_csu.py；产品 resolve 轮询自动 requeue failed 作业。配额窗口恢复后全链自动推进至 confirmed+facts 停住；验收口径与 R17D 相同（Step10 硬断言：confirmation_status=confirmed + facts state=ready + project/open 非 blocked）。
- 留痕：`r18d_seed_csu.py`（由 r17d_seed_csu.py 机械适配，diff 验证仅轮次命名差异）、`r18d_seed_state.json`、`r18d_seed_evidence.jsonl`（1633 条）、`r18d_seed_console.log`、`r18d_supervise.sh`。轮次分节详见 `R5_SEEDED_PROJECT.md` R18D。

## 2026-10-05 主侧路由纠错与换绑回 OmniRouter（任务所有者依据用户指正执行）

- **用户指正成立**：cms-router 走 OmniRouter（127.0.0.1:20128，独立配额），与 ZCode 绑定的 glm-5.3-flash 无关。实测 OmniRoute 此刻 HTTP 200/2.8s 正常服务 glm-5.3-flash。
- **429 真相**：R12D/R13D 因当时本机 Clash 代理(7897)死亡，预置员把两个主侧档案从 OmniRouter 换绑成智谱官方直连(open.bigmodel.cn)+凭据仓直连钥匙——**档案名保留 cms_router 但实际路由早已不是 OmniRouter**。10-03/04/05 三天循环烧掉 8.45M+42.27M+5.88M tokens 把该直连钥匙配额打满（台账 01:16Z 后 1,921 次尝试全 429）。R18 守护员报告措辞"cms-router/glm-5.3-flash 直连 open.bigmodel.cn 429"易误读为 cms-router 配额问题，特此更正。
- **处置**：从 r12d_provider_config_backup 逐档案对比恢复——仅恢复 base_url 从 20128→bigmodel 变更过的两个档案（medical_monitoring_ai__cms_router_glm53flash、document_authority_primary_ai__...）回 http://127.0.0.1:20128/v1 + 原 router 钥匙；改前快照 *.pre_omni_restore_*；产品探针即时验证 passed:true（provider=cms-router，5.4s）。
- **后续**：R18 守护员留下的 r18d_supervise.sh 监督循环（pid 73910，~50min/轮）下一轮将走通修好的路由自动完成预置；R18 预检同理。教训：换绑档案必须同步改档案名或加路由注记，防"名实不符"误导后续取证。

## 2026-10-05 下午（R18轮次·修复员：门禁判据统一后隔离环境 8911+5178 双重启）

- 操作者：修复员（R18轮次：R18-03；R18-01完成环境侧调查）
- 修复：binding门禁（prepare-and-start的来源就绪门输入）由facts-manifest.json文件存在性改为与checklist横幅/运行设置完全同一信号源latest_fact_materialization_ready——「横幅消失允许创建但运行被409永久拦截」的判据分叉在两个方向都不可能再发生。
- R18-01环境调查结论（本轮实测）：端口5186=另一workbench实例（protocol-v3-workbench-mw_protocol_v3_phase0的vite，pid 62193，ego浏览器进程7643与之有活跃连接）——非本产品路由重定向；测试会话漂移疑与ego共享TaskSpace的多实例使用有关，建议循环侧固定每个TaskSpace只挂5178或明确端口清单。本产品侧无可修代码路径。
- 自检：8911 ready:true（build api-a9bb87fb5ee7ab77）；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11起：8910/5177仍无HTTP应答（本轮kill仅针对8911/5178）；留痕提请舰队值班。

## 2026-10-05 晚（R19D 开考位预置·常驻项目 MX循开考-CSU 就位，未修码未重启）

- **探障全过（R5D marker 缺陷未复发）**：① 常驻名存量 sqlite 直查 count=0（首轮新建）；② main.py:4925-4936 种子 marker 修复在位（contracts.py:53-54=v5）；③ 隔离 runtime 30 个存量 workspace launch_registry marker 逐库直查全部 v5，R19D 新建 workspace marker=v5；④ 主侧AI沿任务所有者 10-05 11:13 换回的 OmniRouter LB（127.0.0.1:20128）现行配置，probe 三档案 passed:true（主侧 5853/753ms、verifier 661ms）——R18D 上午 429 冻结已随路由纠错解除，本轮未换绑；⑤ 8911 ready（api-a9bb87fb5ee7ab77）与 5178 runtime-build.json 配对一致；8910/5177 无监听（仅只读复核，未触碰）。
- **预置常驻项目 MX循开考-CSU（单段完成，全程 1h40m）**：proj_user_6ef58ac151e1（201，幂等键 r19d-seed-20260905T190452Z-5f59e580）→ stg-cd69899943ba42618f589ba07a134a59（591行/10表，三件套 sha256 与历轮一致）→ 文档权威 mmbatch_06432a73d31b1d87094f90fd 约8.6分钟 ready（无人工门）→ 映射双队列 10主+10盲核 约18.5分钟 candidates_ready → 收敛 46→32→0（系统裁决14）→ 33张裁决卡全部既有决策表覆盖（零新卡、零 fail-closed）→ confirmed（v80）→ facts ready（10表/591行/3038值全核验）→ project/open current/complete/canEdit，run-setup/options 200，GET runs 空（停在 facts 未启监查）。六项独立 curl 复验全过。AI 台账：46作业（44完成/2终态failed经bounded-gap收敛）、76调用、1,628,699 tokens，质量门全部自然通过。
- **常驻约定**：本项目跨轮持久，后续轮次预置先查存量（confirmed+facts ready+project/open current 即复用零重种）；复盘归档不得删除/重建；「MX循开考-」前缀不属任何轮次。轮次分节详见 `R5_SEEDED_PROJECT.md` R19D。
- 留痕：`r19d_seed_csu.py`、`r19d_seed_state.json`、`r19d_seed_evidence.jsonl`、`r19d_seed_console.log`。

## 2026-10-06（R19轮次·修复员：契约统一+attempt失效自愈后隔离环境 8911+5178 双重启）

- 操作者：修复员（R19轮次：R19-01、R19-02）
- 修复：①needs_attention仅在全部作业终态时报告（任何queued/running→generating）+adopt防御性快失败（跑动作业在cohort→立即mapping_run_incomplete，不再70秒强校验422）；②GET resolve缺batch_id改报诚实新码mapping_resolve_batch_id_required（原误报mapping_attempt_id_invalid）+前端对attempt失效族错误立即转failed并自动getLatestDataAdmission自愈重入。
- 自检：8911 ready:true（build api-a9bb87fb5ee7ab77——packages/改动不入指纹但进程已重启加载新代码）；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11起：8910/5177仍无HTTP应答（本轮kill仅针对8911/5178）；留痕提请舰队值班。

## 2026-10-06（R20D 开考位预置·守护员：复用常驻项目，零重复预置，未修码未重启）

- 存量检查（ask 步骤0）现场实测三条件全过：`GET /api/projects` 仅 1 项目=常驻 MX循开考-CSU（proj_user_6ef58ac151e1，R19 归档刻意保留）；mapping-candidates → draft v80 status=confirmed/user_questions=0/60候选；facts → state=ready（10表/591行/3038值全核验）；project/open → current/complete/canView/canEdit；study-documents ready；run-setup/options 200。直接复用，**零新建、零 AI 作业、零代码修复、零重启**。
- 未启动监查：GET runs 仅 1 条 run:0bf83a78… run_state=waiting_start/result_available=false（R19 开考测试者向导创建的运行设置遗留，从未启动，保留不删）。运行启动留给随后的攻坚验证。
- 只读探障：main.py:4925-4936 marker 修复在位（contracts v5）；本项目 workspace launch_registry.sqlite3 marker sqlite 直查=v5；8911 ready（api-a9bb87fb5ee7ab77）与 5178 [::1] runtime-build.json 配对一致；8910/5177 无监听（沿 R11 起，未触碰）。
- 留痕：`R5_SEEDED_PROJECT.md` R20D 节。本轮无新驱动脚本/状态文件（复用即结论）。

## 2026-10-06 下午（R19攻坚·攻坚工程师第1次：两段重启，仅8911/5178）

- 操作者：攻坚工程师-R19-第1次（运行启动死锁攻坚）。
- 第1段（复现前）：攻坚开始时 8911（pid 35808，02:45 起）103.5% CPU 自旋、/api/health TCP通60s零响应（sample：主线程+工作线程深陷纯Python循环，PySequence_Tuple 热点；AI台账3 running 停在12:43Z、134 queued——R7-01 事件循环独占画像，环境级缺陷未修仅重启）。按标准命令重启 8911+5178；自检 8911 ready:true（api-a9bb87fb5ee7ab77）、5178 /monitoring=200、runtime-build.json 指纹配对一致。
- 第2段（修复后加载）：global_default 自愈修复（run_routes.py prepare-and-start reserve 前 ensure + run_entry.py ensure_builtin_global_default）落地并过回归后重启 8911 加载新代码（packages 改动不入 build 指纹，进程重启实证）；5178 未动仍为该指纹配对态。
- 未触碰 8910/5177（医学写作舰队）。攻坚决战与证据详见 scripts/tester_loop_0927/SIEGE_LOG.md R19 第1次节。

## 2026-10-06（R19轮次·修复员：证据链+风险分级修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R19轮次：R19-01、R19-03；R19-02前端分支经核实已在树上——攻坚工程师cbb5f52e/52fd9697已含attempt失效自愈+batch_id_required诚实化分支）
- 修复：source_locator_ref多locator时取首个（原仅恰好1条才下发→29条发现全部断链）；卡片severity_source=unknown时如实「严重度未知」+分级依据字段（severityBasis）入卡片与旅程详情两处、drawer新增「分级依据」节。
- 自检：8911 ready:true（build api-a9bb87fb5ee7ab77——packages/改动不入指纹但进程已重启）；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11起：8910/5177仍无HTTP应答（本轮kill仅针对8911/5178）；留痕提请舰队值班。

## 2026-10-06 傍晚（R20D 开考位预置·守护员第2次复验：攻坚/修复轮后三条件仍全过，零重复预置）

- 操作者：开考预置守护员-R20（第2次，D位）。背景：R20D 首验后同日 R19 攻坚工程师第1次与 R19 修复员（R19-01/03）多次重启 8911/5178 并加载新代码、攻坚验证在常驻项目上启动跑完 3 条监查运行——本次为现态复验。
- 存量检查现场实测（ask 步骤0）三条件全过：mapping-candidates → draft v80 status=confirmed/user_questions=0/60候选（与首验同版未漂移）；facts → state=ready（10表/591行/3038值全核验）；project/open → current/complete/canView/canEdit；run-setup/options 200；study-documents ready。**再次零新建、零 AI 作业、零代码修复、零重启、零启动运行**（runs 的 3 条 completed 均为攻坚验证所启动，非本轮动作）。
- 只读探障：main.py:4925-4927,4935-4936 marker 修复在位（contracts v5）；本项目 workspace launch_registry marker sqlite 直查=v5；8911 ready（api-a9bb87fb5ee7ab77）与 5178 [::1] runtime-build.json 配对一致；8910/5177 无监听（沿 R11 起，未触碰）。观察：8911 偶发慢响应（readiness 一次 25.9s）与同日 R7-01 事件循环独占记录相符，属已知环境现象。
- 留痕：`R5_SEEDED_PROJECT.md` R20D 节「第二次复验」小节。本轮无新驱动脚本/状态文件（复用即结论）。
2026-10-06 18:46 写作Agent适配落地（5a009dc6：摘要导入modules透传）→API+vite双双重启配对api-1d25bf363b10c2a5；循环恢复续跑

## 2026-10-07（R20轮次·修复员：四项修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R20轮次：R20-01核实/02/03、R18-02）
- 修复：R20-02接入来源可追溯（sourceNamesText投影+第2步「数据来源：」行）；R20-03占位循环（变化原因待确认不再作为字段值二次渲染）；R18-02角色缺失声明跨attempt继承（用户治理决定随项目而非attempt生命周期）；R20-01三面验证（初治PNH在store/manifest/journey三层逐字一致——「改写」非本仓库行为，如实记录）。
- 自检：8911 ready:true（build api-1d25bf363b10c2a5）；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11起：8910/5177仍无HTTP应答（本轮kill仅针对8911/5178）；留痕提请舰队值班。

## 2026-10-06T18:33-18:47Z（R21D 开考位预置·守护员第3次复验：R20修复后新build下三条件仍全过，零重复预置）

- 操作者：开考预置守护员-R21（D位）。背景：R20D 第2次复验后，环境经 10-06 18:46 写作Agent适配落地与 10-07 R20 修复员双重启，build 变为 api-1d25bf363b10c2a5；runtime 根实测已移至 implementation/workbench/runs/tester_loop_iso_20260928/runtime（lsof 8911 pid 12958 实证，仓库根旧 runs/ 路径不存在）。
- 存量检查现场实测（ask 步骤0）三条件全过：mapping-candidates → confirmation_status=confirmed / draft monmapdraft_73abe5c6c9561a9e95eec2056991 v80 status=confirmed / user_questions=0 / 60候选；facts → state=ready（10表/591行/3038值全核验，manifest 在盘 attempt stg-cd69899943ba42618f589ba07a134a59）；project/open → current/complete/canView/canEdit；run-setup/options 200；study-documents ready。**零新建、零 AI 作业、零代码修复、零重启、零启动运行**（runs 6 条 completed 均为 R19/R20 他位角色所启动，非本轮）。
- 只读探障：main.py:4925-4936 marker 修复在位（contracts v5）；本项目 workspace launch_registry sqlite 直查=mm-r7-w01r26-launch-registry-v5；8911 readiness ready:true（0.46s）与 5178 [::1] runtime-build.json expectedBackendBuildId=api-1d25bf363b10c2a5 配对一致；8910/5177 lsof 均 0 监听（沿 R11 起，未触碰）。AI gateway status 只读探看 configured，未做付费 probe。
- 观察如实记录：mapping-candidates 投影顶层 facts_generated=False 与 summary pending_confirmation_count=60/user_question_count=1 同权威终态（facts ready / draft confirmed / user_questions=0项）不一致，属投影怪癖非阻断，提请修复员核投影字段语义（详见 R5_SEEDED_PROJECT.md R21D 节）。
- 留痕：`R5_SEEDED_PROJECT.md` R21D 节。本轮无新驱动脚本/状态文件（复用即结论）。

## 2026-10-07 下午（R21轮次·修复员：四项修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R21轮次：R21-01、R21-02、R19-08、R19-10）
- 修复：发现卡riskId改用risk_instance_id（riski-实例引用，来源定位不再死链）；工作条保留最近一次非loading状态（视图切换不再塌陷为空态文案）；历史卡片加运行token尾号；数据侧重复导入检测（duplicate_of）+第2步重复提示。
- 自检：8911 ready:true（build api-1d25bf363b10c2a5）；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11起：8910/5177仍无HTTP应答（本轮kill仅针对8911/5178）；留痕提请舰队值班。

## 2026-10-07T05:0x-05:27Z（R22D 开考位预置·守护员第4次复验：R21修复员重启后三条件仍全过，零重复预置）

- 操作者：开考预置守护员-R22（D位）。背景：R21D 复验后，R21 轮次修复员对隔离对 8911/5178 双重启加载四项修复（riskId引用/工作条保留/运行token尾号/重复导入检测），8911 现行进程 pid 54721（原 12958），build 仍 api-1d25bf363b10c2a5。
- 存量检查现场实测（ask 步骤0）三条件全过：mapping-candidates → confirmation_status=confirmed / draft monmapdraft_73abe5c6c9561a9e95eec2056991 v80 status=confirmed / user_questions=0 / 60候选；facts → state=ready（10表/591行/3038值全核验，manifest 在盘 mtime Oct 5 22:44 与 R21D 一致）；project/open → current/complete/canView/canEdit；run-setup/options 200；study-documents ready。**零新建、零 AI 作业、零代码修复、零重启、零启动运行**（runs 9 条全部 completed，R21D 后新增 3 条为 R21 开考/攻坚角色所启动，非本轮）。
- 探查笔误自纠（如实记录）：本员首轮误用台账简写路径 `…/r7/…`（漏 `/modules/medical-monitoring/` 段）得三连 404，一度疑似「项目打不开」复发；核对 r19d_seed_csu.py:516 与 /openapi.json（43 条 r7 路由在册）后确认属本员笔误非产品缺陷，修正后全 200——未修码未重启。
- 只读探障：main.py:4925-4936 marker 修复在位（本员直读实证 import SCHEMA_VERSION 常量）；本项目 workspace launch_registry sqlite 只读直查=mm-r7-w01r26-launch-registry-v5；8911 readiness ready:true 与 5178 [::1] runtime-build.json expectedBackendBuildId=api-1d25bf363b10c2a5 配对一致；8910/5177 lsof 均 0 监听（沿 R11 起，未触碰）。AI gateway status 只读探看 configured=true，未做付费 probe。
- 观察如实记录：candidates 投影怪癖沿 R21D 持续（顶层 facts_generated=False / summary pending_confirmation_count=60、user_question_count=1，与权威 confirmed/facts ready 终态不一致），提请修复员核投影字段语义。
- 留痕：`R5_SEEDED_PROJECT.md` R22D 节。本轮无新驱动脚本/状态文件（复用即结论）。

## 2026-10-08（R22轮次·修复员：三项修复后隔离环境 8911+5178 双重启）

- 操作者：修复员（R22轮次：R22-02、R22-03、R22-01）
- 修复：复核分畨预过滤（规范化不敏感比对，同串/同义噪音自动合并agreed）；AE医学逻辑文字（severity/relationship/outcome/SAE组合理由+SAE漏报模式提示）入risk payload与旅程详情「医学依据」节；protocol-versions GET自愈（三项前置满足但列表空时自动注册已确认方案版本）。
- 自检：8911 ready:true（build api-e041fb3ab9060114）；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11起：8910/5177仍无HTTP应答（本轮kill仅针对8911/5178）；留痕提请舰队值班。

## 2026-10-07T08:3x-08:4xZ（R23D 开考位预置·守护员第5次复验：R22修复员新build下三条件仍全过，零重复预置）

- 操作者：开考预置守护员-R23（D位）。背景：R22D 复验后，R22 轮次修复员对隔离对 8911/5178 双重启加载三项修复（复核分畨预过滤/AE医学逻辑文字/protocol-versions自愈），build 由 api-1d25bf363b10c2a5 变为 **api-e041fb3ab9060114**（本轮之前他位动作，本轮未重启）。
- 存量检查现场实测（ask 步骤0）三条件全过：mapping-candidates → confirmation_status=confirmed / draft v80 status=confirmed / user_questions=0 / 60候选；facts → state=ready（10表/591行/3038值全核验）；project/open → current/complete/canView/canEdit；run-setup/options 200；study-documents ready。**零新建、零 AI 作业、零代码修复、零重启、零启动运行**（runs 12 条全部 completed，R22D 后新增 3 条为 R22 开考/攻坚角色所启动，非本轮）。
- 只读探障：main.py:4920-4940 marker 修复在位（import SCHEMA_VERSION 常量直读实证）；本项目 workspace launch_registry Python sqlite3 只读直查=mm-r7-w01r26-launch-registry-v5；8911 readiness ready:true（runtime_schema_version=16）与 5178 [::1]（node pid 13827）runtime-build.json expectedBackendBuildId=api-e041fb3ab9060114 配对一致；8910/5177 lsof 均 0 监听（沿 R11 起，未触碰）。AI gateway status 只读探看 configured=true，未做付费 probe。
- 观察如实记录：candidates 投影怪癖沿 R21D/R22D 持续（顶层 facts_generated=False / summary pending_confirmation_count=60、user_question_count=1，与权威 facts ready / draft confirmed 终态不一致），提请修复员核投影字段语义。另本员复验 R22D 同款台账简写路径笔误一次（漏 modules 段/study-documents 漏 attempt 段），核对 r19d_seed_csu.py:516,554 与 openapi 后自纠，非产品缺陷。
- 留痕：`R5_SEEDED_PROJECT.md` R23D 节。本轮无新驱动脚本/状态文件（复用即结论）。

## 2026-10-08 下午（R23轮次·修复员：写锁饥饿缓解后隔离环境 8911+5178 双重启）

- 操作者：修复员（R23轮次：R23-01）
- 修复：①线程池扩容40→128 token（写锁等待者各占一个token至wait超时，叠加轮询曾耗尽默认池→整站假死8分50秒）；②写锁等待上限30s→3s（拿不到快速失败503，前端重试/提示兜底；长任务走异步队列不持锁）。
- 自检：8911 ready:true（build api-06744bbced9d86a2）；5178=200；指纹配对一致。
- ⚠️舰队状态沿R11起：8910/5177仍无HTTP应答（本轮kill仅针对8911/5178）；留痕提请舰队值班。
2026-10-07 17:18 循环收尾：隔离测试环境已停止（运行时目录保留取证）

## 2026-10-07 17:44-17:46（R24·隔离环境守护员：循环收尾后按ask恢复隔离对 8911+5178）

- 操作者：隔离环境守护员-R24。背景：ask 报 API/前端探针双 exit=1；本员 17:44:41 实测 lsof 8911/5178 均无监听，与 17:18「循环收尾：隔离测试环境已停止（运行时目录保留取证）」条目吻合。恢复前核验 `runs/tester_loop_iso_20260928/runtime` 目录在盘（71 项，非整目录丢失），`~/.config/cms-medical-workbench/ai-runtime.env` 在位，具备恢复条件。
- API 重启（严格按 ask 给定命令）：kill 仅限 `lsof -ti:8911`，uvicorn 以 WORKBENCH_RUNTIME_DIR=…/tester_loop_iso_20260928/runtime、WORKBENCH_LOCAL_SINGLE_USER=1、WORKBENCH_AI_RUNTIME=api、WORKBENCH_MONITORING_AI_PARALLELISM=2 启动 → pid 801，3 秒存活，/tmp/mm_api_8911.log 无告警输出。
- vite 重启（严格按 ask 给定命令）：kill 仅限 `lsof -ti:5178`，VITE_API_PROXY_TARGET=http://127.0.0.1:8911 启动 → npx pid 821 / vite node pid 852（[::1]:5178），VITE v6.4.2 ready in 188ms，/tmp/mm_vite_5178.log 仅 App.jsx 超 500KB 的 BABEL 样式降级提示（非错误）。
- 自检（重启后等满 15 秒，17:45:44 实测）三条件全过：① http://127.0.0.1:8911/api/runtime-readiness → http 200，ready:true，backend_build_id=api-06744bbced9d86a2，runtime_schema_version=16，runtime_store_ready:true，independent_ai ready/configured=true（zhipu-coding-plan / glm-5.3-flash）；② http://localhost:5178/monitoring → http 200；③ http://localhost:5178/runtime-build.json expectedBackendBuildId=api-06744bbced9d86a2 与 8911 backend_build_id 完全一致（frontendBuildId=web-61cf3eec89de9bcb），且与 R23 轮次留痕 build 一致。
- 纪律：本轮零业务管道推进、零项目数据触碰；8910/5177 全程仅只读 lsof 查看（沿 R11 起本就无监听），未 kill 未重启未触碰。一次恢复即成，未用第二次尝试。

## 2026-10-07（R24·开考预置守护员-D位：常驻项目 MX循开考-CSU 存量复验，零重复预置）

- 操作者：开考预置守护员-R24（D位）。动作：查存量 → 三条件全过 → 直接复用。**零新建、零 AI 作业、零代码修复、零重启、零启动运行**。
- 存量检查现场实测（ask 步骤0）：`GET /api/projects` → 仅 1 项目 proj_user_6ef58ac151e1 / MX循开考-CSU / active（modules 含 medical_monitoring）；mapping-candidates → confirmation_status=confirmed / draft monmapdraft_73abe5c6c9561a9e95eec2056991 v80 status=confirmed / user_questions=0 / 60候选；facts → state=ready（10表/591行/3038值全核验，message「可用于监查的数据已生成，可以开始监查。」）；project/open → current/complete/openMode=edit/canView/canEdit；study-documents ready=true；run-setup/options 200。
- 只读探障：main.py:4936+4946 marker 修复在位（import SCHEMA_VERSION 常量，种子 marker 取该值；contracts.py:54=V5）；本项目 workspace launch_registry Python sqlite3 只读直查 r7_launch_registry_meta → ('schema_version','mm-r7-w01r26-launch-registry-v5')；8911 readiness ready:true（backend_build_id=api-06744bbced9d86a2，runtime_schema_version=16）与 5178 [::1] runtime-build.json expectedBackendBuildId 配对一致；runs 15 条全部 completed（R23D 后新增 3 条为 R23 开考/攻坚角色所启动，非本轮）；8910/5177 lsof 均 0 监听（沿 R11 起，未触碰）。
- 环境背景（非本轮动作）：本轮前 build 已由 R23-01 修复员（线程池扩容+写锁上限修复）与 R24 隔离环境守护员（循环收尾停机后恢复 8911+5178）更替为 api-06744bbced9d86a2；常驻项目跨停机恢复周期存活，draft v80 / facts 3038 值零漂移。
- 观察如实记录：candidates 投影怪癖沿 R21D-R23D 持续（顶层 facts_generated=False / summary pending_confirmation_count=60、user_question_count=1，与权威终态不一致），提请修复员核投影字段语义。
- 留痕：`R5_SEEDED_PROJECT.md` R24D 节。本轮无新驱动脚本/状态文件（复用即结论）。

## 2026-10-07 23:30–23:55（测试循环R24·修复员：隔离环境 API+vite 双重启）

- 操作者：修复员（R24 待修清单 R24-03/04/05/06、R18-03、R22-06）。动作：API 8911 与 vite 5178 均重启（指纹配对要求）；8910/5177 未触碰（lsof 确认无监听）。
- 重启命令：API `WORKBENCH_RUNTIME_DIR=runs/tester_loop_iso_20260928/runtime WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api WORKBENCH_MONITORING_AI_PARALLELISM=2 .venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8911`；vite `VITE_API_PROXY_TARGET=http://127.0.0.1:8911 npx vite --port 5178 --strictPort`。
- 自检（重启后实测）：8911 `/api/runtime-readiness` ready:true（backend_build_id=api-157c89f897d07331，较此前 api-06744bbced9d86a2 更替，源为本轮代码修复）；5178 `/monitoring` HTTP 200；5178 `/runtime-build.json` expectedBackendBuildId=api-157c89f897d07331 与 8911 一致（配对通过）。
- 诊断性验证（隔离环境内，被测动作本身）：①R24-03：proj_user_e08934f9a5a7 mapping-draft/confirm 修复前 500 mapping_bridge_failed（复现2次）→ 修复后 409 mapping_reconciliation_required（业务状态），adjudicate 200 且 AI 裁决队列推进（completed 33→35，46问收敛中，固有耗时非缺陷）；②R18-03：proj_user_6ef58ac151e1（历史 CONFIRMED draft v80）prepare-and-start 放行（run:4d16d078 创建，语义正确）；proj_user_e08934f9a5a7（未确认）被来源就绪门+映射确认门双阻断（readiness unconfirmed 详案）。
- 副作用如实记录：验证 R18-03 放行分支时在常驻项目 proj_user_6ef58ac151e1 上创建了 1 条真实运行 run:4d16d078ea9ae0d29ae898ae（该项目的正常行为，18→19 条）；e08934f9a5a7 的裁决队列被诊断调用推进（继续收敛，非破坏）。

## 2026-10-08 00:29-00:31（R25·隔离环境守护员：API 假死恢复 8911 重启 + 5178 重启）

- 操作者：隔离环境守护员-R25。背景：ask 报 API 探针 exit=1、前端探针 exit=0。恢复前实测（00:29:03）：8911 有残留进程 pid 69228（uvicorn，elapsed 33:22）但 `/api/runtime-readiness` 8 秒超时零字节返回（curl exit=28）——进程假死非缺席；5178 有 pid 66348。前提核验：`runs/tester_loop_iso_20260928/runtime` 在盘（71 项）、`~/.config/cms-medical-workbench/ai-runtime.env` 与 `.venv/bin/python` 在位。
- API 重启（严格按 ask 给定命令，00:29:40）：kill 仅限 `lsof -ti:8911`（杀掉假死 69228），uvicorn 以 WORKBENCH_RUNTIME_DIR=…/tester_loop_iso_20260928/runtime、WORKBENCH_LOCAL_SINGLE_USER=1、WORKBENCH_AI_RUNTIME=api、WORKBENCH_MONITORING_AI_PARALLELISM=2 启动 → pid 74159，/tmp/mm_api_8911.log 无输出（--log-level warning 下 uvicorn 启动横幅属 INFO 级，正常）。
- vite 重启（严格按 ask 给定命令，00:29:47）：kill 仅限 `lsof -ti:5178`，VITE_API_PROXY_TARGET=http://127.0.0.1:8911 启动 → vite node pid 74210 监听 [::1]:5178。
- 自检三条件（等满 15 秒后，00:30:15 首测 + 00:30:55 终验）全过：① `http://127.0.0.1:8911/api/runtime-readiness` → http 200，ready:true，backend_build_id=api-157c89f897d07331，runtime_schema_version=16，runtime_store_ready:true，independent_ai ready/configured=true（zhipu-coding-plan / glm-5.3-flash）；② `http://localhost:5178/monitoring` → http 200；③ 5178 `/runtime-build.json` expectedBackendBuildId=api-157c89f897d07331 与 8911 backend_build_id 完全一致（BUILD_ID_MATCH=YES，frontendBuildId=web-61cf3eec89de9bcb）。
- 时序如实记录：00:30:15 首测时 readiness 曾连接被拒（curl exit=7）——pid 74159 已起但应用仍在初始化（约 60 秒完成 listen+ready），非重启失败；00:30:42 起 ready:true 持续。一次重启即成，未用第二次尝试。
- 纪律：本轮零业务管道推进、零项目数据触碰；8910/5177 全程仅只读 lsof（本轮均无监听），未 kill 未重启未触碰。

## 2026-10-08T00:5xZ（R25D 开考位预置·守护员第7次复验：R24修复+R25守护员假死恢复重启后三条件仍全过，零重复预置）

- 操作者：开考预置守护员-R25（D位）。动作：查存量 → 三条件现场实测全过 → 直接复用。**零新建、零 AI 作业、零代码修复、零重启、零启动运行**。
- 存量检查现场实测（ask 步骤0）：`GET /api/projects` → 仅 1 项目 proj_user_6ef58ac151e1 / MX循开考-CSU / active（modules 含 medical_monitoring）；mapping-candidates → confirmation_status=confirmed / draft monmapdraft_73abe5c6c9561a9e95eec2056991 v80 status=confirmed / user_questions=0 / 60候选；facts → state=ready（10表/591行/3038值全核验，message「可用于监查的数据已生成，可以开始监查。」，facts-manifest.json 在盘 mtime Oct 5 22:44 零漂移）；project/open → current/complete/openMode=edit/canView/canEdit；study-documents HTTP 200 ready=true；run-setup/options 200（recommended_mode=daily）。
- 只读探障：main.py:5020+5030 marker 修复在位（import SCHEMA_VERSION 常量、种子 marker 取该值；行号自 R24 轮的 4936/4946 平移，修复本身未动）；contracts.py:53-54=V5；本项目 workspace launch_registry Python sqlite3 只读直查（uri mode=ro）=mm-r7-w01r26-launch-registry-v5；8911 readiness ready:true（backend_build_id=api-157c89f897d07331，pid 74159——R25 隔离环境守护员 00:29 假死恢复重启后的现行进程）与 5178 [::1]（node pid 74210）runtime-build.json expectedBackendBuildId 配对一致；runs 19 条全部 completed（R24D 后 +4：R24 开考/攻坚 +3、R24 轮修复员诊断验证 run:4d16d078 +1，非本轮）；8910/5177 lsof 均 0 监听（沿 R11 起，未触碰）。
- 观察如实记录：candidates 投影怪癖沿 R21D-R24D 持续（顶层 facts_generated=False / summary pending_confirmation_count=60、user_question_count=1，与权威 confirmed/facts ready 终态不一致），提请修复员核投影字段语义。
- 留痕：`R5_SEEDED_PROJECT.md` R25D 节。本轮无新驱动脚本/状态文件（复用即结论）。

## 2026-10-08 03:01–03:03 UTC（测试循环R25·修复员：隔离环境 API+vite 双重启）

- 操作者：修复员（R25 待修清单 R25-01/R25-06/R25-02/R25-03）。动作：API 8911 与 vite 5178 均重启（指纹配对要求）；8910/5177 未触碰（无监听）。
- 重启命令：按 ask 给定（API：WORKBENCH_RUNTIME_DIR=runs/tester_loop_iso_20260928/runtime、WORKBENCH_LOCAL_SINGLE_USER=1、WORKBENCH_AI_RUNTIME=api、WORKBENCH_MONITORING_AI_PARALLELISM=2；vite：VITE_API_PROXY_TARGET=http://127.0.0.1:8911）。
- 自检（重启后实测）：① 8911 `/api/runtime-readiness` ready:true（backend_build_id=api-589520532fc5317d，runtime_schema_version=16）；② `http://localhost:5178/monitoring` HTTP 200；③ 5178 `/runtime-build.json` expectedBackendBuildId=api-589520532fc5317d 与 8911 一致（配对通过）。
- 修复生效验证（只读）：本次修复的启动序调整使僵尸租约收割不再可被跳过——重启后 monai_fad0322b3fa2aaf9b8fb9e2c7039 与 monai_cab4f66709ae3c400b7254ccb2f0（attempt 2/2、租约 2026-10-07T22:59 过期、status=running 滞留>4小时）即时转 failed/worker_lease_expired 终态（updated_at 2026-10-08T03:02:17）；队列其余任务正常推进（completed 3887→3920）。此前 00:29 假死重启后同类僵尸存活至次日（对照证据）。
- 纪律：零业务管道推进、零 runs/ 数据修改（仅 sqlite 只读查询）；8910/5177 仅只读 lsof。

## 2026-10-08 05:41–05:45 +0200（R26·隔离环境守护员：API 假死恢复 8911 重启 + 5178 重启）

- 操作者：隔离环境守护员-R26。背景：ask 报 API 探针 exit=1、前端探针 exit=0。
- 恢复前实测（05:41:58）：8911 有残留进程 pid 16261（uvicorn，elapsed 39:55）但 `/api/runtime-readiness` 8 秒超时零字节（curl exit=28）——进程假死非缺席（与 R25 00:29 同款故障）；5178 pid 16303 `/monitoring` 200 正常。前提核验：`runs/tester_loop_iso_20260928/runtime` 在盘（72 项）、`~/.config/cms-medical-workbench/ai-runtime.env` 与 `.venv/bin/python` 在位。
- API 重启（严格按 ask 给定命令，05:42:24）：kill 仅限 `lsof -ti:8911`（杀假死 16261），uvicorn 以 WORKBENCH_RUNTIME_DIR=…/tester_loop_iso_20260928/runtime、WORKBENCH_LOCAL_SINGLE_USER=1、WORKBENCH_AI_RUNTIME=api、WORKBENCH_MONITORING_AI_PARALLELISM=2 启动 → pid 20020；`/tmp/mm_api_8911.log` 全程 0 字节（--log-level warning 下无告警，正常）。
- vite 重启（严格按 ask 给定命令，05:42:52）：kill 仅限 `lsof -ti:5178`（杀 16303），VITE_API_PROXY_TARGET=http://127.0.0.1:8911 启动 → pid 20086 监听 5178。
- 自检三条件（等满 15 秒后，05:43:23 实测）全过：① `http://127.0.0.1:8911/api/runtime-readiness` → http 200，ready:true，backend_build_id=api-589520532fc5317d（与 R25 修复员 03:01 重启时一致，本轮无代码变更），runtime_schema_version=16，runtime_store_ready:true，independent_ai ready/configured=true（zhipu-coding-plan / glm-5.3-flash）；② `http://localhost:5178/monitoring` → http 200；③ 5178 `/runtime-build.json` expectedBackendBuildId=api-589520532fc5317d 与 8911 backend_build_id 一致（BUILD_ID_MATCH=YES，frontendBuildId=web-f8b8094c1a14837e）。
- 波动如实记录：05:43:47 终验复核曾超时一次（curl exit=28 零字节，进程 20020 存活）——疑为启动期后台工作（过期租约收割/AI 队列恢复）短暂持锁；随后 05:44:16–05:44:27 三连测 http 200（~0.73s/次），05:45:19 完整终验三条件再全过，未复发。**一次重启即成，未动用第二次尝试。**
- 纪律：零业务管道推进、零项目数据触碰、零代码修改；8910/5177 全程仅只读 lsof（本轮均无监听：8910_none / 5177_none），未 kill 未重启未触碰。

## 2026-10-08T03:4x-03:5xZ（R26D 开考位预置·守护员第8次复验：R25修复员+R26守护员重启后三条件仍全过，零重复预置）

- 操作者：开考预置守护员-R26（D位）。动作：查存量 → 三条件现场实测全过 → 直接复用。**零新建、零 AI 作业、零代码修复、零重启、零启动运行**。
- 存量检查现场实测（ask 步骤0）：`GET /api/projects` → 仅 1 项目 proj_user_6ef58ac151e1 / MX循开考-CSU / active（modules 含 medical_monitoring，real_source_slice）；mapping-candidates → confirmation_status=confirmed / draft monmapdraft_73abe5c6c9561a9e95eec2056991 v80 status=confirmed / user_questions=0 / 60候选；facts → state=ready（values=source_values_verified=3038，message「可用于监查的数据已生成，可以开始监查。」，facts-manifest.json 在盘 mtime Oct 5 22:44 零漂移）；project/open → current/complete/openMode=edit/canView/canEdit；study-documents HTTP 200 ready=true；run-setup/options 200（recommended_mode=daily）。
- 只读探障：main.py:5029+5039 marker 修复在位（import SCHEMA_VERSION 常量、种子 marker 取该值；行号自 R25D 的 5020/5030 平移，修复本身未动）；contracts.py:53-54=V5；本项目 workspace launch_registry Python sqlite3 只读直查（uri mode=ro）=mm-r7-w01r26-launch-registry-v5；8911 readiness ready:true（backend_build_id=api-589520532fc5317d，pid 20020——R26 隔离环境守护员 05:42+0200 假死恢复重启后的现行进程）与 5178 [::1]（node pid 20086）runtime-build.json expectedBackendBuildId 配对一致（frontendBuildId=web-f8b8094c1a14837e）；runs 22 条全部 completed 且 result_available=true（R25D 后 +3 为 R25 开考/攻坚角色所启动，非本轮）；8910/5177 lsof 均 0 监听（沿 R11 起，未触碰）。
- 现场波动如实记录：本员首测时（03:48-03:49Z）API 业务端点短暂挂起（/healthz 404 秒回但 /api/projects、readiness 10s 超时零字节），03:49:26Z 起未干预自愈（首测 200 耗时 10.8s，随后 0.76/0.81s 正常）——与 R26 守护员 05:43:47+0200 记录的启动期波动同款，非持续性假死，未动用恢复动作。
- 观察如实记录：candidates 投影怪癖沿 R21D-R25D 持续（顶层 facts_generated=False / summary pending_confirmation_count=60、user_question_count=1，与权威 confirmed/facts ready 终态不一致），提请修复员核投影字段语义。
- 留痕：`R5_SEEDED_PROJECT.md` R26D 节。本轮无新驱动脚本/状态文件（复用即结论）。
2026-10-08 09:29 无损暂停（用户指令）：run dwfrun-4ea04740停于R26测试者阶段（A/C/D已交卷、B在途）。8911/5178有意保持运行供恢复（轮中暂停，环境门探针恢复时为日志回放不重查）；B位浏览器TaskSpace保留不清。恢复=ResumeWorkflowRun同run_id，详见PAUSE_HANDOFF_20261008.md

## 2026-10-08 19:26 +0200（R26轮后·修复员：R26清单修复完毕，API 8911 与 vite 5178 双重启）

- 操作者：修复员（R26 待修清单 R26-01/02/03/04/05 + R24-01）。动作：API 8911 与 vite 5178 均按 ask 给定命令重启（指纹配对要求）；8910/5177 未触碰（无监听）。
- 修复内容（本轮代码变更）：R26-01 eCRF缺失声明按生效裁决补写（mapping_candidate_routes+document_authority_jobs）；R26-02 PDF原生文本覆盖≥90%降级parsed+限制码（document_candidates+document_authority契约）；R26-03 前端文件输入value重置+网络错误中文包装；R26-04 项目记忆localStorage→sessionStorage（会话隔离防跨用户串选）；R26-05 运行启动方案版本门（run_routes+main gate）；R24-01 处理中不同屏喊缺件+readiness标题点名缺失文件。
- 重启命令：按 ask 给定（API：WORKBENCH_RUNTIME_DIR=runs/tester_loop_iso_20260928/runtime、WORKBENCH_LOCAL_SINGLE_USER=1、WORKBENCH_AI_RUNTIME=api、WORKBENCH_MONITORING_AI_PARALLELISM=2 → pid 87131；vite：VITE_API_PROXY_TARGET=http://127.0.0.1:8911 → pid 87140）。
- 自检（19:26:52 实测）：① 8911 `/api/runtime-readiness` ready:true（backend_build_id=api-272b43c31e966e99，runtime_schema_version=16——代码变更后新指纹）；② `http://localhost:5178/monitoring` HTTP 200；③ 5178 `/runtime-build.json` expectedBackendBuildId=api-272b43c31e966e99 与 8911 一致（配对通过）。
- 波动如实记录：vite 启动窗口（19:26:19）有一次 /api/ai-gateway/status 代理 ECONNREFUSED（API 尚在启动），终验三条件全过后未复发；`/tmp/mm_api_8911.log` 全程 0 字节（--log-level warning 无告警）。
- 纪律：零业务管道推进、零 runs/ 数据修改（含 R26-02 诊断用的 sqlite/manifest 均只读 mode=ro）。

## 2026-10-08T17:41-17:47Z（R27D 开考位预置·守护员第9次复验：R26轮后修复员重启（api-272b43c3）后三条件仍全过，零重复预置）

- 操作者：开考预置守护员-R27（D位）。动作：查存量 → 三条件现场实测全过 → 直接复用。**零新建、零 AI 作业、零代码修复、零重启、零启动运行**。
- 环境漂移（本轮之前他位动作，非本轮）：R26轮后·修复员 17:26Z 按 R26-01…05+R24-01 修复并双重启 8911+5178 → build api-272b43c31e966e99、API pid 87131（本员 lsof 实测同值）；5178 本员 lsof 实测 node pid 87162。
- 存量检查现场实测（ask 步骤0）：`GET /api/projects` → 仅 1 项目 proj_user_6ef58ac151e1 / MX循开考-CSU / active（modules 含 medical_monitoring，real_source_slice）；mapping-candidates → confirmation_status=confirmed / draft monmapdraft_73abe5c6c9561a9e95eec2056991 v80 status=confirmed / draft.user_questions=0 项 / 60候选（候选数与 R19D-R26D 零漂移）；facts → state=ready（values=source_values_verified=3038，message「可用于监查的数据已生成，可以开始监查。」，facts-manifest.json 在盘 mtime Oct 5 22:44 零漂移）；project/open → current/complete/openMode=edit/canView/canEdit「项目格式正常，可以继续使用。」；study-documents HTTP 200 ready=true；run-setup/options 200。
- 只读探障：main.py:5111+5121 marker 修复在位（行号自 R26D 的 5029/5039 平移，修复本身未动）；contracts.py:53-54=V5；本项目 workspace launch_registry Python sqlite3 只读直查（uri mode=ro）=mm-r7-w01r26-launch-registry-v5（文件 mtime Oct 8 16:37 本轮窗口前被触碰，marker 复测仍 v5，非缺陷）；8911 readiness ready:true（backend_build_id=api-272b43c31e966e99，runtime_schema_version=16）与 5178 [::1]/monitoring=200、runtime-build.json expectedBackendBuildId 配对一致（frontendBuildId=web-5c52de3cbd52918c）；ai-gateway/status 只读探看 configured=true 无 route_validation_errors/missing_env，未做付费 probe；runs 26 条全部 completed 且 result_available=true（R26D 后 +4 为 R26/R27 开考/攻坚角色所启动，非本轮）；8910/5177 lsof 均 0 监听（沿 R11 起，未触碰）。
- 观察：candidates 投影怪癖沿 R21D-R26D 持续（顶层 facts_generated=False / summary pending_confirmation_count=60、user_question_count=1，与权威 confirmed/facts ready 终态不一致），提请修复员核投影字段语义；本轮 API 全程响应正常（0.8-1.7s），无 R25/R26 记录的启动期挂起波动复发。
- 留痕：`R5_SEEDED_PROJECT.md` R27D 节。本轮无新驱动脚本/状态文件（复用即结论）。
- 纪律：零业务管道推进、零项目数据触碰、零代码修改；8910/5177 全程仅只读 lsof（本轮均无监听），未 kill 未重启未触碰。

## 2026-10-08T18:0xZ（R27·攻坚工程师：R27-01修复 eae38b14 后 8911+5178 标准重启）

- 操作者：攻坚工程师-R27-第1次。背景：R26-05 方案版本门自愈死代码修复（eae38b14，services 改动）需重启加载并重建指纹配对。
- 重启命令：kill 仅限 `lsof -ti:8911`（87131）/`lsof -ti:5178`（87162）；uvicorn 以 WORKBENCH_RUNTIME_DIR=…/tester_loop_iso_20260928/runtime、WORKBENCH_LOCAL_SINGLE_USER=1、WORKBENCH_AI_RUNTIME=api、WORKBENCH_MONITORING_AI_PARALLELISM=2 启动 → pid 93624；vite 以 VITE_API_PROXY_TARGET=http://127.0.0.1:8911 启动 → pid 93671 监听 [::1]:5178。
- 三条件自检（18:07 实测）全过：① 8911 `/api/runtime-readiness` ready、backend_build_id=**api-8f8b335e0cdb6221**（services 指纹变更，实证修复加载）；② `http://localhost:5178/monitoring` 200；③ runtime-build.json expectedBackendBuildId=api-8f8b335e0cdb6221 配对一致（frontendBuildId=web-5c52de3cbd52918c 不变）。
- 修复后行为实证：GET /protocol-versions（先前 items=[]）自愈种入 protov_d952458e7f816a46e614f900（status=confirmed、applicability_status=project_effective_confirmed）；同项目两遍全新幂等键 prepare-and-start 200 → completed → available → overview 可读（1,241,039B/41发现/16受试者，与 R25/R26 逐字节一致）；registry 终态 28 条全部 completed+result_available=1、waiting_start=0。
- 纪律：kill/重启仅动 8911/5178；8910/5177 未触碰（lsof 0 监听）；sqlite 诊断均只读 mode=ro（register 写沙箱副本，live 写全部经 API 设计端点/服务路径）。

## 2026-10-08T23:2x+0200（R27待修清单修复员：R27-01/03 + R25-04/05/07/08 修复后 8911+5178 双重启）

- 操作者：修复员（R27分诊清单 R27-01/R27-03/R25-04/R25-05/R25-07/R25-08）。动作：API 8911 与 vite 5178 均按 ask 给定命令重启（API pid 26563，vite pid 26582）；8910/5177 未触碰。
- 修复内容：R27-01 研究文件核对自动恢复加预算（_recover_failed_once 传 automatic_recovery_limit=3，预算耗尽落 failed 终态→resolve 409 透出 failure_code/message；前端诊断文案渲染）+ 前端长等待进度行（R25-04）；R27-03 analyze 对同批终态失败作业显式重排（start()，不受自动预算限，重传即完整重核）+横幅措辞对齐；R25-07/R25-08 总览收件箱 openItem 先导航后后台记账（原实现 await mark_read 3-30s 无反馈=点击无响应）+按钮语义具体化+防连点；R25-05 apply_action 单次构建（原整库重建两次，动作等待减半；写锁根治未动）。
- 重启命令：按 ask 给定（WORKBENCH_RUNTIME_DIR=runs/tester_loop_iso_20260928/runtime、WORKBENCH_LOCAL_SINGLE_USER=1、WORKBENCH_AI_RUNTIME=api、WORKBENCH_MONITORING_AI_PARALLELISM=2；vite VITE_API_PROXY_TARGET=http://127.0.0.1:8911）。
- 三条件自检（23:26-23:29 实测）全过：① 8911 /api/runtime-readiness ready:true（backend_build_id=api-75f010c43fde3f82）；② http://localhost:5178/monitoring HTTP 200；③ 5178 runtime-build.json expectedBackendBuildId=api-75f010c43fde3f82 与 8911 配对一致。
- 修复后行为实证（UI 走查）：CSU 总览收件箱卡片点击→立即跳 /monitoring（无 3-5s 空窗），后台记账完成计数 -1/-1 一致；「处理最高优先级」tooltip 具体到事项标题、点击即跳、计数随后台更新；R27B 向导第3步显示新进度行「本轮核对已进行约 0 分钟；系统有 1 项核对作业在队列中…」，且 20:16 起滞留的 primary 失败作业被自动恢复重新入队（failed→running，attempt 33/34 租约心跳中）——原「入队后永久滞留」链路已被预算化自愈取代。
- 纪律：零业务管道推进；runs/ 与 sqlite 诊断均只读 mode=ro；8910/5177 全程未触碰。

## 2026-10-08T22:44-22:50Z（R28D 开考位预置·守护员第10次复验：R27待修清单修复员重启（api-75f010c4）后三条件仍全过，零重复预置）

- 操作者：开考预置守护员-R28（D位）。动作：查存量 → 三条件现场实测全过 → 直接复用。**零新建、零 AI 作业、零代码修复、零重启、零启动运行**。
- 环境漂移（本轮之前他位动作，非本轮）：R27待修清单修复员（R27-01/03+R25-04/05/07/08）23:2x+0200 双重启 8911+5178 加载修复 → build api-75f010c43fde3f82、API pid 26563（本员 lsof 实测同值）；5178 本员 lsof 实测 node pid 26604 监听 [::1]:5178。
- 存量检查现场实测（ask 步骤0）：`GET /api/projects` → 仅 1 项目 proj_user_6ef58ac151e1 / MX循开考-CSU / active（modules 含 medical_monitoring，real_source_slice）；mapping-candidates → confirmation_status=confirmed / draft monmapdraft_73abe5c6c9561a9e95eec2056991 v80 status=confirmed / draft.user_questions=0 项 / 60候选（与 R19D-R27D 零漂移）；facts → state=ready（10表/591行/values=source_values_verified=3038，message「可用于监查的数据已生成，可以开始监查。」，facts-manifest.json 在盘 mtime Oct 5 22:44 零漂移，10表 AE/CM/DM/EX/ICF_TRACK/LB_HEM/MH/SV/UAS/VS）；project/open → current/complete/openMode=edit/canView/canEdit「项目格式正常，可以继续使用。」；study-documents HTTP 200 ready=true；run-setup/options 200（recommended_mode=daily）。
- 只读探障：main.py:5120+5130 marker 修复在位（行号自 R27D 的 5111/5121 平移，修复本身未动）；contracts.py:53-54=V5；本项目 workspace launch_registry Python sqlite3 只读直查（uri mode=ro）=mm-r7-w01r26-launch-registry-v5（文件 mtime Oct 8 20:22 较 R27D 观察的 16:37 又被现行进程触碰，marker 复测仍 v5，非缺陷）；8911 readiness ready:true（backend_build_id=api-75f010c43fde3f82，runtime_schema_version=16）与 5178 /monitoring=200、runtime-build.json expectedBackendBuildId 配对一致（frontendBuildId=web-1f04fb05696a5e24）；ai-gateway/status 只读探看 configured=true（zhipu-coding-plan/glm-5.3-flash）无 route_validation_errors/missing_env、deployment_profile_approved=true，未做付费 probe；runs 29 条全部 completed 且 result_available=true（R27D 后 +3 为 R27 开考/攻坚角色所启动，非本轮）；8910/5177 lsof 均 0 监听（沿 R11 起，未触碰）。
- 观察：candidates 投影怪癖沿 R21D-R27D 持续（顶层 facts_generated=False / summary pending_confirmation_count=60、user_question_count=1，与权威 confirmed/facts ready 终态不一致），提请修复员核投影字段语义；本轮 API 全程响应正常（0.95-2.0s），无 R25/R26 记录的启动期挂起波动复发。
- 留痕：`R5_SEEDED_PROJECT.md` R28D 节。本轮无新驱动脚本/状态文件（复用即结论）。
- 纪律：零业务管道推进、零项目数据触碰、零代码修改；8910/5177 全程仅只读 lsof（本轮均无监听），未 kill 未重启未触碰。

## 2026-10-09T02:59+0200（R28分诊清单修复员：R28-01/02/03/04/07 修复后 8911+5178 双重启）

- 操作者：修复员（R28分诊清单 R28-01/R28-02/R28-03/R28-04/R28-07；R28-06 skip 另报）。动作：API 8911 与 vite 5178 均按 ask 给定命令重启（本轮 API 重启两次：第一次加载全部修复后现 R28-07 初版实现令旧冻结包 AUTHORITY_DIGEST_MISMATCH 全不可读，当场复现→改 property 派生方案后第二次重启收敛）；8910/5177 未触碰。
- 修复内容：R28-01 旅程死链根因=量表周分值 float(12.0) 进入冻结包后 Python json.dumps("12.0") 与前端 JSON.stringify("12") 序列化分叉，response_digest 前端验签必败→读取链 payload 构建整值浮点规范为 int（_event_payload/_value_indicator/public_result_envelope 信封兜底）+facts 解析整值保 int，旧发布读时即愈；R28-02 查询工作区跳证据页 URL 以被点卡片自身身份为准（monitoringSourceEvidenceRoutePatch，Finding 卡带自身窗）；R28-03/R28-04 「重新核对研究文件」explicit_retry 突破自动恢复预算真实重排+失败文案按 infra/内容类区分+failure_class 透出+下一步按钮失败态不再误报「请先添加所需文件」；R28-07 AESER=是→R5RiskRecord.serious 派生属性（从 medical_note 合同字段解析，不新增哈希字段）+payload serious 位+前端 SAE 徽章/查询工作区与概览置顶。
- 重启命令：按 ask 给定（WORKBENCH_RUNTIME_DIR=runs/tester_loop_iso_20260928/runtime、WORKBENCH_LOCAL_SINGLE_USER=1、WORKBENCH_AI_RUNTIME=api、WORKBENCH_MONITORING_AI_PARALLELISM=2；vite VITE_API_PROXY_TARGET=http://127.0.0.1:8911）。
- 三条件自检（第二次重启后实测）全过：① 8911 /api/runtime-readiness ready:true（backend_build_id=api-3cc7a71cf1e003d7）；② http://localhost:5178/monitoring HTTP 200；③ 5178 runtime-build.json expectedBackendBuildId=api-3cc7a71cf1e003d7 与 8911 配对一致。
- 修复后行为实证（只读 API 复核，未推进任何管道）：常驻项目 MX循开考-CSU 既有发布 result-context:8b5ca1e2… ① subjects/subject-21001 旅程载荷 200/173,850B、JS 序列化语义 SHA-256 复算==response_digest（修复前 false）；② subjects/subject-23003 200，current_risks 31 条中 riski-AE-000039 serious=true（AESER=是，与生成器植入行一致）；③ overview 200、JS digest 复算一致、477 风险恰 1 条 serious、41 发现不变；④ source-evidence 200。
- 测试：tests/test_public_result_journey_digest_r28.py 4/4（含种子→运行→发布→结果→旅程整链、旧冻结浮点读时修复、AESER 派生位；修复回退变异验证 3/3 必败）；相关套件 111 passed（freeze/facts×2/doc-authority/data-admission/batch-rule-runner）+ r7 router 96/97（1 失败 test_late_project_dispatchers… 为改动前 HEAD 已然失败的既有并发用例，与本轮修复无关，已留证）；frontend node --test $(find src -name '*.test.mjs') 84/84。
- 纪律：零业务管道推进、零 runs/ 写入（sqlite 诊断只读 mode=ro）；8910/5177 全程未触碰。
2026-10-09 08:41 zhipu-coding-plan彻底摘除（用户指令）：independent_ai改绑independent_ai__deepseek_v4_flash（deepseek直连，非编码计划）；两条zhipu档案enabled=false。台账实证zhipu历史0次调用（cms-router 4738+ollama-cloud 2808为主）；该绑定系循环前配置继承（R12D换绑前备份已证），非本轮成员所设。备份=*.pre_zhipu_purge_1009
2026-10-09 10:43 轮中无损暂停（用户指令：完成当前细节点即停）：run dwfrun-9077e4cd停于R29分诊在途（四测试位已交卷28条原始发现）。8911/5178有意保持运行供恢复；在途现场不清。恢复=ResumeWorkflowRun同run_id，详见PAUSE_HANDOFF_20261009.md
2026-10-09 16:03 恢复执行（用户指令）+通道核验：cms-router/glm-5.3-flash探针passed:true（3267ms真实往返）——R29期间B/C位的429系上游凭证冷却暂态，已自愈；角色绑定核对=考场与主运行时8/8完全一致（independent_ai=deepseek与用户现行配置相同）。run dwfrun-9077e4cd已Resume，R29分诊起续跑

## 2026-10-09T17:26+0200（R29分诊清单修复员：R29-06/01 + R27-02 + R28-10/15 修复后 8911+5178 双重启）

- 操作者：修复员（R29分诊清单 R29-06/R27-02/R29-01/R29-07/R28-10/R28-15；R29-07 skip 另见 result）。动作：API 8911 与 vite 5178 均按 ask 给定命令重启（本轮 API 重启三次：①按 ask 原命令重启后 readiness ready:false 排查 → ②发现独立Ai就绪缺钥 → ③`set -a; source ai-runtime.env; set +a` 后重启收敛）；8910/5177 未触碰。
- 修复内容：R29-06 带锚点进「事件明细」100%崩溃根因=R24V2-B02（3a91cdb3）把 riskSeverityLabel 重命名为 riskSeverityInfo 时漏改两处调用（MedicalMonitoringWorkspace.jsx EventRow 1783 行 + DomainTracks 待确认区 1051 行），锚点渲染即 ReferenceError 落错误边界；改用 riskSeverityInfo 诚实呈现并新增回归 medicalMonitoringEventDetailAnchorRender.test.{jsx,mjs}（带锚点 timeline/无锚点/带锚点 journey 三对照+pending带risk）。R29-01 队列滞留：R29实测单作业滞留≥5.7h无终态（attempt 28「失败→重排→再排队」循环，租约/预算管不住queued侧）→ monitoring_ai_repository 新增 dwell_since 列+fail_queued_jobs_exceeding_dwell（超2h落 queue_dwell_timeout 可重试终态；显式重试重置基线、自动恢复不重置；暂停项目不收割；存量行按created_at兜底）+worker 15s poller 接入；测试 tests/test_monitoring_ai_queue_dwell_timeout.py 5/5。R27-02 前端：列表读取失败不再永久禁用「新建项目」（顶栏+EmptyProjectOverview 失败态均保留建项入口；建项不依赖列表读取）。R28-15 建项：submit 重构为响应到达即停慢提示计时器+每分支显式复位 busy（成功必关弹窗+交接导航；2xx缺项目身份也退出）+120s硬超时（AbortController）+409 同名冲突/超时后查 /api/projects 按名匹配给「前往已有项目」出口（App.jsx onResolveExisting，措辞与建项成功区分）。R28-10 请核实事项卡：product_projection_helpers._risk_payload 注入规则名（「依据当前项目监查规则「{risk_type_zh}」」）+事件术语与真实起止日期（绑定不到事件回落「域记录+日期状态」不伪造）+按9域差异化核查指向（_DOMAIN_VERIFY_HINTS）；overview/subject_workspace 三处调用方传 event_by_ref；测试 tests/test_risk_evidence_template_r2810.py 5/5。
- 重启命令：按 ask 给定（WORKBENCH_RUNTIME_DIR=runs/tester_loop_iso_20260928/runtime、WORKBENCH_LOCAL_SINGLE_USER=1、WORKBENCH_AI_RUNTIME=api、WORKBENCH_MONITORING_AI_PARALLELISM=2；vite VITE_API_PROXY_TARGET=http://127.0.0.1:8911）。**环境修复要点**：ai-runtime.env 为裸赋值无 export，按 ask 原命令 `source` 后 uvicorn 子进程拿不到 DEEPSEEK_API_KEY；zhipu 摘除（10-09 08:41）后 active 改绑 deepseek 档案且 ai_provider_secrets.json 无该档案凭证 → independent_ai configured:false → readiness ready:false（16:03 恢复执行核对绑定时未暴露，因只核对绑定未探 readiness）。本轮以 `set -a; source ~/.config/cms-medical-workbench/ai-runtime.env; set +a` 启动（共享 env 文件本身未改），ready:true 收敛。**后续重启命令建议统一加 set -a/set +a**。
- 三条件自检（第三次重启后实测）全过：① 8911 /api/runtime-readiness ready:true missing:[]（backend_build_id=api-0feb76ce663ae085，independent_ai ready:true）；② http://localhost:5178/monitoring HTTP 200；③ 5178 runtime-build.json expectedBackendBuildId=api-0feb76ce663ae085 与 8911 配对一致（frontendBuildId=web-339d936c48a63787）。
- 附带实测（R27-02/R23-01 相关）：冷启动 /api/projects 本轮三次重启实测 1.82-1.85s（非 R29 复盘所述 50.4s 量级；R23-01 <1s 仍未达，但 20s 前端超时预算内充分）；manifest 构建器本地实测 0.00s/域，50.4s 根因未在本环境复现，留待预检断言按复盘口径覆盖。
- 测试：backend pytest——test_monitoring_ai_queue_dwell_timeout 5/5、test_risk_evidence_template_r2810 5/5、test_monitoring_ai_repository 84/84、test_monitoring_ai_worker+test_monitoring_document_authority_jobs 34/34、test_monitoring_ai_contracts+contract_hash_shape+dwell+doc_authority_jobs 64/64、test_medical_monitoring_r5_product_adapter+r5_product_router 20/20、test_public_result_journey_digest_r28+test_facts_mode_outputs_n1 20/20、r7 router 96/97（1 失败 test_late_project_dispatchers… 经 git stash 对照为 HEAD 既有失败，与本轮无关）；frontend node --test anchor回归+timelineSemantics+journeyDrawer+subjectFlow+findingCard 5/5 套全过、vite build 成功（web-339d936c48a63787）。
- 纪律：零业务管道推进；runs/ 零直写（sqlite 诊断只读 mode=ro；active_profile 改绑经 PUT/POST /api/ai-gateway 设计端点）；8910/5177 全程未触碰。

## 2026-10-09 21:33–21:35（R30修复轮重启留痕）
- 操作者：修复员（R30分诊清单 R30-01/R30-03/R28-05/R28-08/R28-09/R28-11）。动作：API 8911 与 vite 5178 均按 ask 给定命令重启（API 重启两次：①按 ask 原命令重启后 readiness ready:false——与R29留痕同根因，ai-runtime.env裸赋值无export致DEEPSEEK_API_KEY未达uvicorn子进程；②`set -a; source ai-runtime.env; set +a` 后重启收敛 ready:true）；8910/5177 未触碰。
- 自检：http://127.0.0.1:8911/api/runtime-readiness → ready:true（21:34:12重启后）；http://localhost:5178/monitoring → 200；指纹配对 backend_build_id=api-e1c432cb92f53fd9 与 5178/runtime-build.json expectedBackendBuildId 一致（本轮含R30修复代码的新build）。
- 修复后基线：/api/projects 空载 0.79s→0.013-0.017s（R30-01缓存生效；重启前同机实测2.09s）。
- 再次建议：后续重启命令统一加 `set -a` / `set +a`（连续两轮同坑）。

## 2026-10-10 01:52–02:59（R31修复轮重启留痕：R31-01/02/03/04/05/06 修复后 8911+5178 双重启，API 共重启两次）
- 操作者：修复员（R31分诊清单 R31-01/R31-02/R31-03/R31-04/R31-05/R31-06 全6条）。动作：API 8911 与 vite 5178 均按 ask 给定命令重启（API 重启两次：①01:52 全部修复加载；②02:5x 补充修复 confirm_draft 对 _terminal_failure_domain_gaps 三元组返回值的解包——该回归由全量套件 HEAD 对照发现、targeted复现-修复-复验后重启收敛；两次均按R29/R30连续同坑要点以 `set -a; source ~/.config/cms-medical-workbench/ai-runtime.env; set +a` 启动）；vite 5178 重启一次（后端二次重启时前端代码未再变更，配对自检复验一致）；8910/5177 未触碰。
- 修复内容：R31-05 SAE漏报误报=facts_publication 「肯定」子串匹配把「肯定无关」也判漏报（对研究中心的错误指控）→改「肯定有关」显式含+「肯定无关」排除，补5断言回归（肯定无关/肯定有关/可能有关/修饰变体/脏数据均各自正确）。R31-01 识别停滞（根因经 ISO sqlite 只读诊断坐实：双项目612分片在2worker下2小时仅消化~85次AI调用，204分片滞留队列2小时不被认领也不失败，唯一被尝试的分片两次provider_response_truncated后终态失败）→收割视界从7200s对齐2700s（45分钟纪律，R31策略坐实的错配）+WORKBENCH_MONITORING_QUEUE_DWELL_TIMEOUT_SECONDS环境变量可调；阈值到即落queue_dwell_timeout可重试终态，needs_attention旁路真实可达。R31-02 采纳422死循环=库层槽位完整性门对「同域部分分片completed+部分分片failed」混合态硬拒MonitoringMappingSourceStateError，且_repo_error_code把一切ValueError归因为「用户修订内容无效」→①确认层_terminal_failure_domain_gaps扩展计算终态失败分片的(domain,chunk_index)槽位豁免集、assemble/_validated_source按槽位级豁免放行部分覆盖域（未传豁免仍fail-closed；extra slot一律硬拒；domain_gaps物化缺失分片数）；②SourceStateError独立归因mapping_draft_source_unavailable(409)+诚实文案，422「字段修订内容无效」仅留给真实用户输入非法；③存量部分草稿edit/confirm再校验走revalidating_persisted_draft（source_set_sha256内容钉死身份不被装配后状态变化推翻）；测试 tests/test_mapping_partial_slot_adoption_r31.py 6/6。R31-03 第3步自救契约=2.5s轮询每次load-start翻转phase致「正在读取系统识别结果…」灰置按钮长期遮蔽停滞重读入口（R31B实测70+分钟零可点入口）→load-start在有payload且非failed时保持phase只清错误（初次/失败重载仍loading），重读入口与needs_attention旁路按钮持续可见；needs_attention提示文案从「请先刷新等待」改为「已完成的识别结果可采纳继续」。R31-04 UAS7日期锚定=周分值列事件start恒None全落「日期待确认」→周分值事件按列名周数锚定（优先SV同周访视记录日期；缺席按EX首次给药日期+周数×7天推定，锚定出处写入标签；两者皆缺保持missing不补造），指标趋势四柱恢复、共享时间轴入轴；测试 tests/test_facts_publication_scale_week_anchor_r31.py 4/4（R29-10泳道空态同根一并收敛）。R31-06 研究文件核对排队无进展=_pending_state区分pending_running_count/pending_queued_count并经resolve路由透传，前端「N项核对作业在途（执行中X项、排队中Y项）」不再把排队误读为卡死（滞留收割同R31-01视界）；wizard渲染测试断言同步加强（fixtures带双计数断言执行中/排队中文案）。
- 重启命令：按 ask 给定（set -a 包裹 source；WORKBENCH_RUNTIME_DIR=runs/tester_loop_iso_20260928/runtime、WORKBENCH_LOCAL_SINGLE_USER=1、WORKBENCH_AI_RUNTIME=api、WORKBENCH_MONITORING_AI_PARALLELISM=2；vite VITE_API_PROXY_TARGET=http://127.0.0.1:8911）。
- 三条件自检（两次重启后均实测）全过：① 8911 /api/runtime-readiness ready:true（backend_build_id=api-f240b1ef669d7a88，含R31全部修复的新build）；② http://localhost:5178/monitoring HTTP 200；③ 5178 runtime-build.json expectedBackendBuildId=api-f240b1ef669d7a88 与 8911 一致（frontendBuildId=web-550d10e0866d34f0，本轮 vite build 产物）。
- 测试：backend pytest——R31新增 test_facts_publication_sae_underreport_r31 5/5、test_facts_publication_scale_week_anchor_r31 4/4、test_mapping_partial_slot_adoption_r31 6/6；回归=repository+worker+doc_jobs+contracts 128/128、r5 adapter/router+event_time+risk_evidence_r2810+digest_r28+facts_mode_n1 53/53、dwell timeout 5/5、doc authority jobs全过、r7 router 96/97（1失败 test_late_project_dispatchers… 经两次 git stash 对照为 HEAD 既有失败，与本轮无关）；全量tests/后台长跑在途（test_medical_writing_dynamic_section_matrix 收集期 ImportError 与 test_monitoring_principal_host_adapter 均为 HEAD 既有失败，均经 stash 对照留证）；frontend node --test 88/88（含R31-03新增断言与R31-06加强断言）、vite build 成功。
- 诊断留证（只读）：ISO runs sqlite 以 mode=ro 查询 R31B/C 停滞现场——monitoring_ai_jobs 287/205 个 queue_dwell_timeout 行、call_ledger 2h窗口85次调用、deterministic分片秒级完成而AI分片attempt=0，坐实容量型滞留而非异常吞噬；零写入。
- 纪律：零业务管道推进、零 runs/ 写入（sqlite 诊断只读 mode=ro）、8910/5177 全程未触碰。
2026-10-10 07:13 轮中无损暂停（用户指令：完成当前节点即停）：run dwfrun-6d5ff1cf停于R32修复员在途（测试位1/4通过+分诊完成12新条）。8911/5178有意保持运行；在途现场不清。恢复=ResumeWorkflowRun同run_id，详见PAUSE_HANDOFF_20261010.md
2026-10-11 08:32 环境恢复+independent_ai终绑：暂停期间8911/5178掉线已按预案重启；zhipu摘除收尾——deepseek直连双钥匙401（历史死通道）、ollama qwen3.5下架404，终绑=medical_monitoring_verifier_ai__ollama_cloud_dsv41（活凭据1s探针过；与主分析cms-router不同通道，与盲核同通道同模型系当前最佳可得，钥匙分离待用户供新通道）；死档案independent_ai__deepseek_v4_flash已禁用

## 2026-10-11 09:17–09:19（R32分诊清单修复员：R32-01/02/03/04/05/06 全6条修复后 8911+5178 双重启）

- 操作者：修复员（R32分诊清单 R32-01～R32-06 全6条）。动作：API 8911 与 vite 5178 均按 ask 给定命令重启；按 R29/R30/R31 连续三轮同坑要点，API 启动以 `set -a; source ~/.config/cms-medical-workbench/ai-runtime.env; set +a` 包裹（env 文件本身未改）；8910/5177 未触碰。
- 修复内容概要（详见本轮 git 提交）：R32-01 后端根因=r7数据接入async路由在事件循环内直接执行阻塞调用（register/analyze/resolve-GET/readiness/candidates/draft 全族；advance单次可达30s由其409文案自证），全部下放 run_in_threadpool（新增回归 tests/test_r7_route_event_loop_offload_r32.py：阻塞窗口内并发探测修复前1.11s被拖住→修复后<0.75s，先红后绿）；前端 App.jsx 列表读取失败按5/10/20s退避自动重拉（≤3次，文案如实显示第N次）。R32-02 死锁=「还有N组字段关系需要处理」横幅下页面零控件：阻断组明细卡（标题/摘要/涉及字段当前角色）+逐字段角色修订入口（PATCH recommended_role→自动重复核）+blocked态不再显示自相矛盾「正在自动保存…无需逐项核对」。R32-03/04 根因坐实（ISO sqlite只读诊断：proj_user_9610ef8760c3 计265分片queue_dwell_timeout终态失败且attempt_count=0，LB域verifier分片全灭、仅确定性规则VISTREP存活）：_project作业行暴露表名/分片/尝试数/失败原因，公开投影新增按表聚合 table_failures（无作业身份），新路由 POST …/mapping-candidates/retry-failed（可按表过滤，复用库层retry_terminal显式重试语义+worker唤醒），第3步渲染失败清单与「重跑失败分片/重跑全部」入口。R32-05 配对文档未就绪改走独立代码 mapping_document_evidence_roles_unmet(422)，消息如实指认缺件并明示与文件是否损坏无关；旧 mapping_document_evidence_incomplete 不再由配对缺失触发且文案去指控化。R32-06 结果读取（overview/evidence/subject）失败按退避自动重试≤3次（AbortError保持静默替换），「当前内容暂不可用」面板如实说明自动重试；新增源码合同测试 medicalMonitoringResultReadRetry.test.mjs。
- 三条件自检（实测）全过：① 8911 /api/runtime-readiness ready:true（backend_build_id=api-f240b1ef669d7a88）；② http://localhost:5178/monitoring HTTP 200；③ 5178/runtime-build.json expectedBackendBuildId=api-f240b1ef669d7a88 与 8911 一致（frontendBuildId=web-a9999632d1a640c4，本轮vite产物）。**指纹说明**：backend_build_id 仅指纹 services/api/app（contracts/runtime_contract.json build_fingerprint=backend_source_root:services/api/app），本轮后端修复全部位于 packages/medical_monitoring/**，不改变该指纹——新代码已实际加载的实证=openapi.json 含新路由 …/mapping-candidates/retry-failed（curl实测在列）。指纹覆盖面未含 packages/ 属共享基础设施既有口径，本轮不擅改，留痕供所有者裁决是否扩面。
- 测试：backend pytest——新增 tests/test_r7_route_event_loop_offload_r32.py 1/1、tests/test_mapping_table_failures_retry_r32.py 5/5、tests/test_document_evidence_roles_unmet_r32.py 3/3；回归=test_mm_c3_document_evidence（2处断言随R32-05语义更新为新代码）+证据门/R7 router+admission（r7_data_admission 38/38，路由面pin随新增retry路由更新；r7_product_router 96/97，1失败 test_late_project_dispatchers… 经git stash对照为HEAD既有失败）+repository/worker/doc_jobs/dwell 123+draft repo 64+confirmation gate/audit 23+mapping_confirmation/semantic_quality 143 全过。frontend node --test 88/88、vite build 绿。
- 诊断留证（只读）：ISO runs medical_monitoring_ai.sqlite3 以 mode=ro 查询R32B项目作业账：265 failed(queue_dwell_timeout, attempt_count=0) / 91 completed / 2 provider_runtime_error；LB2-LB18全部verifier分片终态失败——坐实容量型滞留+按域沦陷，非识别缺陷。零写入。
- 纪律：零业务管道推进、零 runs/ 写入（sqlite诊断只读 mode=ro）、8910/5177 全程未触碰。

## 2026-10-11（R33分诊清单修复员：R33-02/01/03 + R30-02/04 + R29-07 共6条修复后 8911+5178 双重启）

- 操作者：修复员（R33分诊清单6条）。动作：API 8911 与 vite 5178 均按 ask 给定命令重启；8910/5177 全程未触碰。
- 修复内容概要（详见本轮 git 提交）：R33-02 根因（ISO sqlite只读诊断 proj_user_ebdde4632266）=确认被双盲复核前置拦截：verifier识别分片在测试窗内未收敛（03:41–04:14UTC才陆续completed）→confirm 409 mapping_verifier_incomplete；随后adjudication分片遇上游provider_error滞留队列（05:08UTC被queue_dwell_timeout收割）→adjudicating轮询恒running。前端此前把409当失败循环（5+次手动重试）且复核末态无超时无出口。修复=后端 mapping_verifier_incomplete 文案如实点名双盲复核环节+自动推进路径、补登记 mapping_cohort_input_mismatch(409，此前落兜底500零信息)；前端 verifier_incomplete→adjudication-start 自动等待、复核停滞计时（15分钟阈值）+「重新加载识别结果」自救入口、blocked载荷的failure_code/failure_message透出、draft-error带错误码渲染。R33-01 「全部对应关系清晰」定论改为派生自 global_blocker_count/阻断组数（>0时改「仍有N组待处理，处理前不能确认」）。R33-03 失败态互斥渲染：pending-note「正在自动保存…」不再与error同屏；「可启用，但以下分析将受限」改为陈述后果「确认后以下分析将受限」（不承诺不存在的启用入口）。R30-04 建项弹窗：超时/失败分支立即复位busy（此前 findExistingProject 裸fetch /api/projects 在高负载窗72-119s把finally拖住→DOM全禁用死局）；核实列表加10s上限。R30-02 结果视图一次性大渲染分批挂载：风险定位清单（首80+每次120）、受试者入口（60+100）、流向明细表（60+100，筛选变化重置批次）+ .monitoring-load-more 样式；骨架屏已有（R28-05）未动。R29-07 facts_publication 新增 CM-MH 一致性确定性交叉判定：①CMINDC明示疾病词（剔除通用短语）在受试者MH全文无对应→medium+可核实依据；②CMINDC空/通用时内置常见用药对照（21族）推定适应症词，MH无对应→medium+「常见适应症对照提示核实，非医学诊断」；一致/未收录药物/无药物名不制造发现。洗脱期时间窗判定未实现（需方案入排/洗脱窗结构化数据，本轮如实不做）。
- 三条件自检（实测）全过：① 8911 /api/runtime-readiness ready:true（backend_build_id=api-f240b1ef669d7a88）；② http://localhost:5178/monitoring HTTP 200；③ 5178/runtime-build.json expectedBackendBuildId=api-f240b1ef669d7a88 与 8911 一致。指纹口径同上轮留痕：build_fingerprint 只覆盖 services/api/app，本轮 mapping_candidate_routes.py 位于 packages/medical_monitoring/api/r7_product/**，不改指纹；新代码已加载的实证=8911 确认失败路径新文案（mapping_verifier_incomplete 新消息）经 openapi/错误消息表加载（代码 import 即生效），packages/ 指纹覆盖面问题继续留待所有者裁决。
- 测试：backend pytest 新增 tests/test_facts_publication_cm_mh_consistency_r29.py 7/7（植入矛盾检出/一致不触发/通用负例/用药对照触发与别名命中/未知药不触发）；全量 tests/ 实跑（除 test_medical_writing_dynamic_section_matrix.py 收集期 ImportError——HEAD 既有，与医学写作舰队相关）=9083 passed / 57 failed（3776s）。57项失败逐一归因：①1项为本轮引入——test_reconciliation_errors_do_not_ask_user_for_bulk_review 钉住旧文案「不需要您确认」（即R33-03认定的矛盾文案#1），断言随诚实化文案同步更新后转绿；②其余56项经 git stash 对照在 HEAD（无本轮改动）逐一复现：sqlite_runtime_integration×6、monitoring_risk_index×2、migration_gate×1（legacy_glm_cohort）、r5_subject_flow pinned_hash、r7_product_router late_project_dispatchers（与上轮留痕一致）、frontend contract 9项（button/empty_project/source_manifest/translation_batch）、medical_writing×24（本轮零改动该舰队，上轮留痕同cluster）、d08/d09/d10「8911_stopped」×3（环境性：ISO API在跑，断言端口须停止）、ai_execution_policy/ai_route_freeze/approval_center/contracts/runtime_directory_configuration/document_pipeline_round8/visual_tool_bridge/visual_transport/principal_host_adapter/sqlite_runtime_real_rux×10。非本轮回归。frontend node --test medical-monitoring 全部85/85（含新增3条：verifier_incomplete→adjudicating、复核停滞超阈值reload出口、阻断组headline不claim全部清晰）、fieldMappingState 1/1（restricted标题断言随R33-03诚实化文案同步更新）、vite build 成功。
- 诊断留证（只读）：ISO runs medical_monitoring_ai.sqlite3 以 mode=ro 查询R33B项目（proj_user_ebdde4632266）：draft=monmapdraft_b6ac9dba…（version=1，始终未确认）；listing-field-mapping primary/verifier 识别分片各10片全completed（revision一致88913d96…，排除cohort mismatch）；listing-field-mapping-adjudication primary 10片全failed(queue_dwell_timeout, attempt_count=0, 05:08UTC收割)、verifier 2/10 completed；call_ledger 03:37–05:21UTC 多次 AiProviderRuntimeError——坐实「确认必败」=复核未收敛+复核作业滞留队列，非用户操作问题。零写入。
- 纪律：零业务管道推进、零 runs/ 写入（sqlite诊断只读 mode=ro）、8910/5177 全程未触碰。

## 2026-10-11 18:24（R34攻坚第1次：8911 单独重启）

- 操作者：攻坚工程师-R34-第1次。动作：**仅重启 8911**（`lsof -ti:8911 | xargs kill` 后按标准命令 `set -a; source ~/.config/cms-medical-workbench/ai-runtime.env; set +a; WORKBENCH_RUNTIME_DIR="$PWD/runs/tester_loop_iso_20260928/runtime" WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api WORKBENCH_MONITORING_AI_PARALLELISM=2 nohup .venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8911 --log-level warning`，~14s 就绪，日志 /tmp/mm_api_8911.log）；**5178 全程未触碰**（vite dev 服务源码、无需重启）；8910/5177 未触碰。
- 重启动机：R34 轮次修复提交 047dfdcc 内全部 14 个文件 mtime 统一 18:06:11、晚于前轮重启 16:58:07（前轮进程 PID 31869），且无 stash reflog 可查——运行中进程是否已加载 R34 packages 代码面（facts_publication CM-MH + mapping_candidate_routes）无法从 forensics 消除疑义；重启前经只读 sqlite 核对 launch_registry 无在途运行（最新 sequence 47 已 completed），安全窗口。
- 三条件自检（实测）全过：① 8911 /api/runtime-readiness ready:true（backend_build_id=api-f240b1ef669d7a88）；② http://localhost:5178/monitoring HTTP 200；③ 5178/runtime-build.json expectedBackendBuildId=api-f240b1ef669d7a88 与 8911 一致（frontendBuildId=web-693e9d2ed763d7f6）。
- 加载实证（行为级）：重启后两遍全新幂等键全链绿（SIEGE_LOG R34 节），overview 原文含「合并用药与病史一致性待核实」×24（=发现数增量 41→65 逐字相等）、「常见适应症对照」×46——R29-07 代码在役确证。
- 纪律：零业务管道推进（两遍运行=攻坚任务书要求的复现/重验）、零 runs/ 写入（sqlite 仅只读 mode=ro）。

## 2026-10-11 14:29Z（R34分诊清单修复员：R34-07/01/09/10 + R28-06 + R32-07 共6条修复后 8911+5178 双重启）

- 操作者：修复员（第34轮分诊清单6条）。动作：API 8911 与 vite 5178 均按 ask 给定命令重启（`WORKBENCH_MONITORING_AI_PARALLELISM=2`）；8910/5177 全程未触碰。
- 修复内容概要（详见本轮 git 提交）：R34-07 monitoring_ai_repository `fail_queued_jobs_exceeding_dwell` 改为按项目分组、视界随队列深度动态放宽（基线+(在队数-1)×180s，新构造参数 queue_dwell_seconds_per_queued_job）——129分片单worker串行场景队尾不再被固定2700s误收割为 queue_dwell_timeout 终态；「失败→重试→再排队」循环（R29-01场景）队列深度≈1-3视界仍≈基线，兜底语义不变。R34-01 mapping_pipeline.document_readiness：必需角色被用户裁决「本次未提供」时 headline/guidance 收敛为「研究文件配对不完整：电子病例报告表已确认本次未提供」受限态（ready 保持 true 不回退 R7 收口的接入流程），不再宣称「已准备好/自动完成两次独立核对」。R34-09+R32-07 result_context_service 新增冻结结果包进程内会话缓存（指纹=发布行17项身份字段，含workspace root 键；TTL 600s、LRU 4条、线程安全）——门禁核对+工件完整性校验+packet恢复结果复用，结果视图往返不再每次全量重读（R32实测7~129s/次），前端自动重试与手动重读本就同一读取链（MedicalMonitoringProductLoop startRead），失败窗随缓存消除；「完整性校验进度数值」未做（首读仍是原体重校验，进度条为装饰性，不做假进度）。R34-10 facts_publication._cm_mh_consistency_note 常见用药对照改为**全部**适应症别名参与病史匹配（此前只对照 aliases[0]：阿托伐他汀只查「高血脂」、孟鲁司特只查「哮喘」，病史载「血脂异常/过敏性鼻炎」被误报「无对应记录」）；真缺失仍提示核实，明示适应症路径不变。R28-06 facts_publication 新增 AE-化验趋势矛盾交叉核对（_AE_LAB_TREND_TERMS 血常规6族、降低方向、AE≥3级而历次检测均未低于参考下限60%→AE风险行追加矛盾提示并引用实测值/访视）——「AE与化验趋势矛盾」监查重点方向有确定性产出；CM-MH 方向由 R29-07（上轮已在役）产出；特殊关注已确认规则的工作项→产出结构化关联未改（检测层已落地两方向，诚实记录）。
- 三条件自检（实测）全过：① 8911 /api/runtime-readiness ready:true（backend_build_id=api-4ee144cc0f399a1e）；② http://localhost:5178/monitoring HTTP 200；③ 5178/runtime-build.json expectedBackendBuildId=api-4ee144cc0f399a1e 与 8911 一致（frontendBuildId=web-693e9d2ed763d7f6，前端本轮零改动）。
- 测试：backend pytest 本轮新增/更新=tests/test_monitoring_ai_queue_dwell_timeout.py 7/7（含深度放宽×2新测试）、tests/test_public_result_freeze_0926.py 10/10（含缓存命中跳过重校验+指纹失效fail-closed×2新测试）、tests/test_mm_c3_document_evidence.py（含受限态1条新测试）、tests/test_facts_publication_cm_mh_consistency_r29.py 12/12（含别名全量匹配×2+AE-化验矛盾×3新测试）；回归=monitoring AI/mapping 全家 1141、result/publication/admission 118、daily_run/batch/rule 546、monitoring_ai_service 500、facts/event_time 8+21 全过。前端 node --test resultReadRetry+admissionWizardRender+mappingConfirmState 26/26（前端零改动）。既有失败（与本轮无关，git stash 对照确认）：test_medical_monitoring_r7_product_router.py::test_late_project_dispatchers…、test_medical_writing_chapter_projection.py×2。
- 纪律：零业务管道推进、零 runs/ 写入、8910/5177 全程未触碰。
2026-10-11T14:33:30Z
2026-10-11 22:43 轮次边界无损暂停（用户指令：当前节点完成后停）：R34自然收官（修复员全程做完、复盘落盘完成，用户守候期间零打断），8911/5178已停（边界暂停可安全停机，下轮环境门自动拉起）。恢复=项目根CreateWorkflow接R35

## 2026-10-11 22:48:20 CST R35 隔离环境恢复
- 探针失败现场：8911/5178 均无进程监听（lsof exit=1），运行时目录 runs/tester_loop_iso_20260928/runtime 存在，未丢失，无需重建
- API 重启：uvicorn services.api.app.main:app 127.0.0.1:8911，PID=26745，WORKBENCH_RUNTIME_DIR=tester_loop_iso_20260928/runtime
- vite 重启：npx vite --port 5178 --strictPort（VITE_API_PROXY_TARGET=http://127.0.0.1:8911），PID=26774
- 自检1 runtime-readiness：curl http://127.0.0.1:8911/api/runtime-readiness → HTTP 200，ready:true，backend_build_id=api-4ee144cc0f399a1e
- 自检2 monitoring：curl http://localhost:5178/monitoring → HTTP 200
- 自检3 build id 一致：runtime-build.json expectedBackendBuildId=api-4ee144cc0f399a1e == 8911 backend_build_id → 一致
- 结论：隔离环境已恢复可用（首次尝试即成功，未触 8910/5177）
2026-10-12 06:43 立刻无损暂停（用户指令）：run dwfrun-91c93297停于R35修复员在途（测试位1/4+分诊毕，修复员约50分钟被停、恢复重做）。8911/5178保持运行；STATE_V2保持round34。恢复=ResumeWorkflowRun同run_id，详见PAUSE_HANDOFF_20261012.md
2026-10-12 08:5x（R35修复员六条修复后双重启，标准命令，未触 8910/5177）
- 背景：R35修复员提交六条修复（R35-01降级采纳/R33-07 resolve 422-R35-06严重程度语义/R33-04重跑反馈/R33-10对账标注/R33-11按期访视不生成锚点；后端改动全在 packages/**+前端 medical-monitoring，services/api/app 无改动故 backend_build_id 指纹不变）
- API 重启：lsof -ti:8911 kill → 标准命令拉起（WORKBENCH_RUNTIME_DIR=tester_loop_iso_20260928/runtime, WORKBENCH_MONITORING_AI_PARALLELISM=2），重启后进程在位
- vite 重启：lsof -ti:5178 kill → 标准命令拉起（VITE_API_PROXY_TARGET=http://127.0.0.1:8911，--port 5178 --strictPort）
- 自检1 runtime-readiness：curl http://127.0.0.1:8911/api/runtime-readiness → HTTP 200，ready:true，backend_build_id=api-4ee144cc0f399a1e
- 自检2 monitoring：curl http://localhost:5178/monitoring → HTTP 200
- 自检3 build id 一致：runtime-build.json expectedBackendBuildId=api-4ee144cc0f399a1e == 8911 backend_build_id → 一致
- 口径留痕（沿R32/R35前例）：backend指纹仅覆盖 services/api/app；本轮后端改动在 packages/medical_monitoring/**（mapping_confirmation/mapping_candidate_routes/facts_mode_outputs/facts_publication），指纹数值不变但重启已从源码重新加载全部 packages 代码

## 2026-10-12 16:41 CST R36修复员六条修复后标准重启（R36-01/R36-02/R36-04/R34-02/R34-03/R34-04，未触 8910/5177）
- 背景：R36修复批次改动 packages/medical_monitoring/admission/{pipeline,mapping_confirmation}.py + packages/medical_monitoring/api/r7_product/mapping_candidate_routes.py + 前端 medical-monitoring（AdmissionWizard/ProductLoop/confirmState）——backend指纹仅覆盖 services/api/app，数值不变（api-4ee144cc0f399a1e）；前端指纹因源码改动更新 web-2f9ae4d76eefc842→web-95e6457ceeb785a3
- API 重启：lsof -ti:8911 kill → 标准命令拉起（WORKBENCH_RUNTIME_DIR=tester_loop_iso_20260928/runtime, WORKBENCH_MONITORING_AI_PARALLELISM=2），就绪耗时约1-2分钟（3.6GB sqlite冷启动导入），16:43 ready
- vite 重启：lsof -ti:5178 kill → 标准命令拉起（VITE_API_PROXY_TARGET=http://127.0.0.1:8911，--port 5178 --strictPort）
- 自检1 runtime-readiness：curl http://127.0.0.1:8911/api/runtime-readiness → HTTP 200，ready:true，backend_build_id=api-4ee144cc0f399a1e
- 自检2 monitoring：curl http://localhost:5178/monitoring → HTTP 200
- 自检3 build id 配对：runtime-build.json expectedBackendBuildId=api-4ee144cc0f399a1e == 8911 backend_build_id → 一致；frontendBuildId=web-95e6457ceeb785a3（R36前端改动面新指纹）
- 结论：隔离环境已恢复可用，R36六条修复代码已加载（packages/medical_monitoring/** 与前端源码均为重启后加载面）
- 更正（同日 16:5x）：提交前最后一次前端补丁（复核预算耗尽错误态补降级出口）晚于上一次 vite 启动，served 指纹滞后于磁盘——vite 再启一次；自检 monitoring 200、frontendBuildId=web-fbcf1a886af42cbf（最终指纹）、expectedBackendBuildId=api-4ee144cc0f399a1e == 8911 backend_build_id 一致、8911 ready:true 未动
2026-10-12 17:06 快速无损暂停（用户指令）：run dwfrun-005a6979停于R36复盘在途（测试1/4+分诊17新条+修复阶段已全部完成）。8911/5178保持运行。恢复=ResumeWorkflowRun同run_id，详见PAUSE_HANDOFF_20261012B.md

## 2026-10-13 02:29 CST R37修复员五条修复后标准重启（R37-01/R37-02/R37-06/R35-02/R35-03，未触 8910/5177）
- 背景：R37分诊清单修复（R35-04如实跳过）：R37-01 字段映射确认死锁根因=76bef91c引入的前端拼写错误（MedicalMonitoringAdmissionWizard.jsx:563 引用不存在的adjudicatingProgressText，adjudicating态渲染即ReferenceError→错误边界整页告警，渲染级回归测试红→绿实证）；R37-02 document authority多文档单候选契约新增确定性归并（monitoring_ai_service.py，归并条件不满足照旧fail-closed）；R37-06 target_incomplete假自动重试承诺改如实文案；R35-02 项目名管理代号不再作判不一致唯一基准（source_content_validation.py+main.py）；R35-03 内容确认落盘即回执+resolve在途409如实容忍。改动面：services/api/app/{main,monitoring_ai_service,source_content_validation}.py + 前端 medical-monitoring 三文件 + 测试3新2改
- API 重启：lsof -ti:8911 kill → 标准命令拉起（WORKBENCH_RUNTIME_DIR=tester_loop_iso_20260928/runtime, WORKBENCH_MONITORING_AI_PARALLELISM=2），冷启动约5分钟（3.6GB sqlite导入，100%CPU 6分钟内就绪）
- vite 重启：lsof -ti:5178 kill → 标准命令拉起（VITE_API_PROXY_TARGET=http://127.0.0.1:8911，--port 5178 --strictPort）
- 自检1 runtime-readiness：curl http://127.0.0.1:8911/api/runtime-readiness → HTTP 200，ready:true，backend_build_id=api-5b547c38911d4ad5（services/api/app 本轮改动新指纹，与前轮 api-4ee144cc0f399a1e 不同属预期）
- 自检2 monitoring：curl http://localhost:5178/monitoring → HTTP 200
- 自检3 build id 配对：runtime-build.json expectedBackendBuildId=api-5b547c38911d4ad5 == 8911 backend_build_id → 一致；frontendBuildId=web-7c41e90d1490184a（R37前端改动面新指纹）
- 浏览器抽查（camofox，用户视角）：5178/monitoring 载入正常；选择常驻项目 MX循开考-CSU → 项目总看板数据载入正常（收件箱77项/高开13）；进入医学监查产品页（ProductLoop，含本轮改动渲染面）正常渲染「项目风险概览/本次结果已可查看/数据接入」，无错误边界告警；未打开数据接入向导（避免触发常驻项目管道动作），R37-01崩溃面以渲染级回归测试（adjudicatingRunning fixture 红→绿）为验收证据

## 2026-10-13 06:26 CST R38修复员标准重启（R36-03/R36-05/R36-06/R36-08/R36-09 五条修复 + R36-07浏览器探测，未触 8910/5177）
- 背景：R38分诊清单修复：R36-03 复核闭环（workbench_inbox.py 同含义发现处置/已读跨运行结转+main.py 收件箱身份守卫单次重建重试+前端收件箱读取中/失败诚实态与重试入口，App.jsx 保留旧列表+角标降级=R36-06）；R36-05 treatment-emergent核对（facts_publication.py AE早于首次给药+肯定有关出矛盾提示）；R36-08 核对进度补阶段名/预期区间；R36-09 内容差异确认卡补理由文本域（对齐归属确认卡）。改动面：services/api/app/{workbench_inbox,main}.py + packages/medical_monitoring/projections/facts_publication.py + 前端 App.jsx/AdmissionWizard + 测试（新增2后端1前端改）
- API 重启：lsof -ti:8911 kill → 标准命令拉起（WORKBENCH_RUNTIME_DIR=tester_loop_iso_20260928/runtime, WORKBENCH_MONITORING_AI_PARALLELISM=2），06:26:06 拉起
- vite 重启：lsof -ti:5178 kill → 标准命令拉起（VITE_API_PROXY_TARGET=http://127.0.0.1:8911，--port 5178 --strictPort）；首次误从 workbench 根目录启动（npx vite 404）即纠正为 frontend/ 目录重启
- 自检1 runtime-readiness：curl http://127.0.0.1:8911/api/runtime-readiness → HTTP 200，ready:true，backend_build_id=api-34f525073da51f3e（services/api/app 本轮改动新指纹）
- 自检2 monitoring：curl http://localhost:5178/monitoring → HTTP 200
- 自检3 build id 配对：runtime-build.json expectedBackendBuildId=api-34f525073da51f3e == 8911 backend_build_id → 一致；frontendBuildId=web-fc1973818c3b7897（R38前端改动面新指纹）
- R36-07浏览器探测（camofox，用户视角，只读）：/monitoring 载入后 0-12s 时间片采样：可见可达焦点元素19个全期稳定、[inert]=0、[aria-modal]=0、[tabindex=0]=0；代码面全量keydown扫描仅两处条件性Tab陷阱（JourneyDrawer overlay / SOA弹窗），页级自定义Tab链不存在——R36-07报告的「16个tabIndex=0仅6可达」在当前代码面无法复现（载入窗口可达集小=内容未渲染，非隐藏排除），如实跳过不改
2026-10-13 06:43 轮中无损暂停（用户纠偏：修复员完成即停）：run dwfrun-4fce9e30停于R38复盘节点开头（修复阶段已完成过门；P0/P1 16→8腰斩、新P0/P1首次归零）。8911/5178保持运行。恢复=ResumeWorkflowRun同run_id，详见PAUSE_HANDOFF_20261013.md
2026-10-13 08:49 Ollama Cloud额度耗尽切换（用户指令）：实测ollama 429、cms-router/glm-5.3-flash探针3.6s通过；三角色（文档权威盲核/监查盲核/独立核对）改绑cms_router_glm53flash（glm-5.3-flash/high）。备份=ai_role_bindings.json.pre_ollama_exhaust_1013。注：盲核与主分析暂同通道同模型（额度所迫的临时架构，ollama额度恢复或新钥匙到位后建议切回独立盲核）

## 2026-10-13 10:38 CST R39修复员六条修复后标准重启（R39-01/R39-02/R39-03/R37-03/R37-04/R37-05，未触 8910/5177）
- 背景：R39分诊清单六条全修，零跳过。R39-01 文档权威输出身份字段（input_sha256/conflict_packet_sha256）改为服务端注入（monitoring_ai_service.py `_inject_document_authority_identity_fields`，模型分析内容照旧全量校验、注入留痕server_normalizations；R37-02归并链路注入先行）；R37-03 失败区重试文案与复用语义统一（mapping_candidate_routes.py :1144-1163 按 invalid_ai_output/内容类/infra类三分支如实指引+前端停滞警示文案同口径）；R39-02 结果读取投影失败分支与setup/history读取路径补真实退避自动重试（MedicalMonitoringProductLoop.jsx 共享scheduleRetryAfterFailure+setupRetryAttempt，面板文案如实显示重试进度）；R39-03 查询工作区「发现」区新增数据驱动的两列表覆盖差异说明（MedicalMonitoringWorkspace.jsx 按risk实例引用实际计算缺席项，含紧急/高风险计数）；R37-04 医学问响应答纳入定论计数源（medicalMonitoringAdmissionMappingConfirmState.mjs mappingRecordedDecisionKeys=draft.fields user_action决定前缀，与后端_decision_recorded同判据；定论派生含userAnsweredCount；保存回执回显内容）；R37-05 文档角色状态行显式声明不可点击+上传入口aria-label与角色自动认领说明（AdmissionWizard.jsx）。改动面：services/api/app/monitoring_ai_service.py + packages/medical_monitoring/api/r7_product/mapping_candidate_routes.py + 前端4文件 + 测试（新增tests/test_mm_r39_document_authority_identity_injection.py 6用例；更新test_monitoring_document_authority_jobs.py身份修复契约断言、medicalMonitoringResultReadRetry.test.mjs 25检查、medicalMonitoringAdmissionWizardRender.test.mjs上传入口文案断言）
- API 重启：lsof -ti:8911 kill → 标准命令拉起（WORKBENCH_RUNTIME_DIR=tester_loop_iso_20260928/runtime, WORKBENCH_MONITORING_AI_PARALLELISM=2），10:37 拉起
- vite 重启：lsof -ti:5178 kill → 标准命令拉起（frontend/ 目录，VITE_API_PROXY_TARGET=http://127.0.0.1:8911，--port 5178 --strictPort）
- 自检1 runtime-readiness：curl http://127.0.0.1:8911/api/runtime-readiness → ready:true，backend_build_id=api-71272c9b18ef5f5d（本轮改动新指纹）
- 自检2 monitoring：curl http://localhost:5178/monitoring → HTTP 200
- 自检3 build id 配对：runtime-build.json expectedBackendBuildId=api-71272c9b18ef5f5d == 8911 backend_build_id → 一致；frontendBuildId=web-02219adfb901b542（R39前端改动面新指纹）
- 测试留痕：后端相关族 761 passed（mapping_confirmation/admission/wizard/document_authority/monitoring_ai_service，--ignore=test_medical_writing_dynamic_section_matrix.py=HEAD既有收集期ImportError）+ 48 passed（r7_data_admission/R38 carryover/treatment_emergent）+ 100 passed/1 failed（r7_product_router，失败=test_late_project_dispatchers 409 result_context_unavailable，经git stash对照证实HEAD既有与R39改动无关）+ 文档权威族112 passed；前端 node --test 95/95 + vite build 绿
2026-10-13 14:04 R40修复员标准重启（R40-01/02/03+R37-03/04/05之外的R40清单六条修复面：services/api/app/{monitoring_ai_service,monitoring_document_authority_workflow,monitoring_document_authority_jobs,source_intake}.py + packages/medical_monitoring/admission/{document_authority,mapping_gate无关}.py + mapping_candidate_routes.py + 前端App.jsx收件箱深链/AdmissionWizard.jsx+mappingConfirmState.mjs字段识别进度/Workspace.jsx Query导出/两个css）：
- API 重启：lsof -ti:8911 kill → 标准命令拉起（pid 34096，14:03:50）
- vite 重启：lsof -ti:5178 kill → 标准命令拉起（pid 34136，14:03:58）
- 自检1 runtime-readiness：ready:true，backend_build_id=api-233b2b43102a315b（本轮改动新指纹）
- 自检2 monitoring：curl http://localhost:5178/monitoring → HTTP 200
- 自检3 build id 配对：runtime-build.json expectedBackendBuildId=api-233b2b43102a315b == 8911 backend_build_id → 一致；frontendBuildId=web-544f152559b59671（R40前端改动面新指纹）
- 端口纪律：仅触碰8911/5178；8910/5177未执行任何操作（自检时点未在监听，与本次重启无关）
- 测试留痕：文档权威族159 passed（含新增test_mm_r40_document_authority_shared_runtime.py 5项：同身份提交建作业/advance作业缺失就地重建/同绑定推进到review/reconcile默认fail-closed/start包装submit失败）；r7_data_admission+offload_r32+source_content_validation+R35 67 passed；source_registry+source_content_validation+document_evidence 90 passed（1处旧英文文案断言随R38-03本地化同步更新，拒绝语义不变）；inbox+mapping_confirmation+gate 80 passed；monitoring_ai_service 493 passed；document_candidates+evidence_roles 36 passed；前端 node --test 97/97（新增R38-01生成进度2项+R38-03/R40-01回归）+ vite build 绿
- 注意：R40-01根因=用户指令Ollama切换（d6013072）后运行身份与mapping_gate种子常量失配致作业创建前抛错（ISE→job_missing死局）；R39-01注入修法非根因（其契约环节因作业未建从未执行到）。常驻项目现走「同通道同模型知情降级」路径，盲核独立性弱于常态已在202响应与轮询载荷中披露，恢复独立绑定后自动回到fail-closed。
2026-10-13 14:19 轮中无损暂停（用户指令，按裁定边界规则）：run dwfrun-4fb5cddf守候目标修复员完成后立即停——R40测试1/4+分诊9新条+修复阶段全部完成过门，复盘节点截停于开头。8911/5178保持运行。恢复=ResumeWorkflowRun同run_id，详见PAUSE_HANDOFF_20261013B.md

## 2026-10-13 20:19 CST R41D 开考预置复验（只读复用常驻项目 MX循开考-CSU，零重复预置，未触 8910/5177）
- 常驻复用语义第 23 次复验：三条件现场实测全过——mapping confirmed（draft monmapdraft_73abe5c6c9561a9e95eec2056991 v80）+ facts ready（10表/591行/3038值全核验）+ project/open current（canView/canEdit=true）；run-setup/options 200（snapshot_token 同值）、runs 50 条全 completed 零新增零启动（全程 GET 零 POST）。
- 环境现态：build api-233b2b43102a315b（R40修复员 14:04 CST 标准重启后现行进程，Python pid 34096 / node pid 34159 监听 [::1]:5178），runtime-readiness ready:true，前后端 build 配对一致；8910/5177 lsof 复核 0 监听仅只读未触碰。
- R5D marker 未复发：main.py:5151/5161 + contracts v5 + 常驻项目 workspace launch_registry.sqlite3 只读直查 marker=v5、integrity ok。
- 遗留回归四次上报：study-documents 在第四个 build（api-233b2b43）上仍 analyzing/ready=false（protocol/ecrf=需要重新识别），AI 台账 46 条全终态 non-terminal=0 证实静态态；不阻断三条件复用就绪，R38D-R40D 判定沿用，未做修复未跳门。
- independent_ai 现报 cms-router/glm-5.3-flash（10-13 08:49 Ollama 额度耗尽切换后现行配置，同通道同模型知情降级在案）；本轮零 AI 作业零调用，详见 R5_SEEDED_PROJECT.md R41D 节。
2026-10-13 23:42 R41修复员标准重启（R41清单六条修复面：packages/medical_monitoring/api/r7_product/{mapping_candidate_routes,publication_routes}.py + packages/medical_monitoring/{admission/mapping_pipeline,projections/{facts_publication,product_adapter,product_projection_helpers}}.py + services/api/app/monitoring_mapping_semantic_quality.py + 前端 ProductLoop/AdmissionWizard/Workspace/ProtocolPreparationPanel.jsx + fieldMappingState/journeyDrawerModel/journeyTimeline/productApi/trendScale/workspaceApi mjs + workspace css）：
- API 重启：lsof -ti:8911 kill → 标准命令拉起（首次nohup在长导入期未应答曾误判，实际pid 8770于23:42:0x完成绑定并提供服务；二次拉起的重复进程pid 8975已kill，8911现单进程=8770）
- vite 重启：lsof -ti:5178 kill → 标准命令拉起（pid 8818）
- 自检1 runtime-readiness：curl http://127.0.0.1:8911/api/runtime-readiness → ready:true，backend_build_id=api-321647a3bee8499d（本轮改动新指纹，较R40的api-233b2b43102a315b已更新）
- 自检2 monitoring：curl http://localhost:5178/monitoring → HTTP 200
- 自检3 build id 配对：runtime-build.json expectedBackendBuildId=api-321647a3bee8499d == 8911 backend_build_id → 一致；frontendBuildId=web-1a17ccb8197fa9d9（R41前端改动面新指纹）
- 端口纪律：仅触碰8911/5178；8910/5177未执行任何操作
- 测试留痕：新增tests/test_mm_r41_fixes.py 4/4（AE化验矛盾绑定4条化验行定位/量表跨周趋势归并为一条序列按日期排序/public_draft投影携带rule_id+affected_fields+G-ROLE-002随组role_catalog非角色组不带/定位符直读来源证据+风险绑定语义不变+未知定位fail-closed）；回归=r5_product_adapter+semantic_quality+draft_repo 168 passed；mm_c3 confirmation/dual/gate+digest_r28 67 passed；mapping_pipeline五族 98 passed/1 failed（migration_gate legacy_glm，stash对照证实HEAD既有）；facts_publication五族 34 passed；r7+r5 router+adapter 116 passed/1 failed（late_project_dispatchers 409 result_context_unavailable@router.py:2844，与R39/R40留痕逐字同签名、stash对照HEAD既有）；protocol_preparation+subject_flow+risk_bridge 81 passed/1 failed（subject_flow legacy packet pinned hash，stash对照HEAD既有）；前端 node --test 97/97（ResultReadRetry新增R41-02五项契约：入口失败计数进退避/入口重试共用退避/手动重读重置预算/结果上下文建立后清场/同步构造失败除target_incomplete外进调度）+ vite build 绿

## 2026-10-14 00:20 CST R42D 开考预置复验（只读复用常驻项目 MX循开考-CSU，零重复预置，未触 8910/5177）
- 常驻复用语义第 24 次复验：三条件现场实测全过——mapping confirmed（draft monmapdraft_73abe5c6c9561a9e95eec2056991 v80）+ facts ready（10表/591行/3038值全核验）+ project/open current（canView/canEdit=true）；run-setup/options 200（snapshot_token 同值）、runs 50 条全 completed 零新增零启动（全程 GET 零 POST）。
- 环境现态：build api-321647a3bee8499d（R41修复员 23:42 CST 标准重启后现行进程，Python pid 8770 / node pid 8818 监听 [::1]:5178），runtime-readiness ready:true，前后端 build 配对一致（frontendBuildId=web-1a17ccb8197fa9d9）；8910/5177 lsof 复核 0 监听仅只读未触碰。本节即第 5 个 build 上三条件首验。
- R5D marker 未复发：main.py:5151 + contracts.py:54 v5 + 常驻项目 workspace launch_registry.sqlite3（真实路径 runs/tester_loop_iso_20260928/runtime/…，WORKBENCH_RUNTIME_DIR env 定位）只读直查 marker=v5、integrity ok（size 471040B/mtime 10-13 20:47 CST，本轮窗口前 R41 轮内写入，如实并录）。
- ✅ 遗留回归五报转正向：R38D 发现的 study-documents 读路径回归（跨 4 个 build analyzing/ready=false）在本 build 实测 ready=true、headline「研究文件已准备好」、protocol/ecrf 均 current/已识别——与 23:42 R41修复员六条修复面吻合；本员零修复零 POST 仅只读实测。
- 本轮 API 慢带（重启后约 32 分钟冷缓存疑因，全部请求正常返回零漂移）：project/open 5.84s / mapping-candidates 10.69s / runs 12.91s / run-setup 17.61s / study-documents 69.33s；runtime-readiness 0.82s、ai/jobs 1.10s 正常带。零 AI 作业零调用，详见 R5_SEEDED_PROJECT.md R42D 节。

## 2026-10-14 04:32 CST R42修复员标准重启（R42清单修复面：services/api/app/{monitoring_ai_repository,monitoring_protocol_preparation_service}.py + packages/medical_monitoring/admission/mapping_confirmation.py + packages/medical_monitoring/api/r7_product/mapping_candidate_routes.py + 前端 ProductLoop/AdmissionWizard/ProtocolPreparationPanel.jsx + admissionMappingConfirmState/integration pin/render fixture）：
- API 重启：lsof -ti:8911 kill → 标准命令拉起（pid 59573 于 04:32 启动，启动期约40秒长导入后绑定端口并提供服务）
- vite 重启：lsof -ti:5178 kill → 标准命令拉起（pid 59739/59764）
- 自检1 runtime-readiness：curl http://127.0.0.1:8911/api/runtime-readiness → ready:true，backend_build_id=api-616662809274f9f0（本轮改动新指纹，较R41的api-321647a3bee8499d已更新）
- 自检2 monitoring：curl http://localhost:5178/monitoring → HTTP 200
- 自检3 build id 配对：runtime-build.json expectedBackendBuildId=api-616662809274f9f0 == 8911 backend_build_id → 一致
- 端口纪律：仅触碰8911/5178；8910/5177 lsof复核0监听未执行任何操作
- 测试留痕：新增tests/test_mm_r42_mapping_bridge_convergence.py 3项（慢而真实排空的盲核队列不被收割/停滞队列带陈旧完成照旧收割/降级确认触发verifier事后补偿+补偿失败不回滚确认+非降级确认零补偿）；R42-02新增status零检索契约1项；r5 adapter新增概览投影确定性钉住1项；monitoring_ai_queue_dwell_timeout 5/5原契约不变；前端渲染/integration钉住断言随R42-04双通路与R40-02失败态单一权威口径同步更新（拒绝语义不变）。回归=repository+worker+doc_jobs+contracts 128 passed；mapping五族+R36+R42+dwell 154 passed/1 failed（migration_gate legacy_glm，本轮stash对照证实HEAD既有）；protocol_preparation 50 passed；r5 adapter+subject_flow+risk_bridge 95 passed/1 failed（subject_flow legacy packet pinned hash，本轮stash对照证实HEAD既有）；r7 router+data_admission 135 passed/1 failed（late_project_dispatchers 409 result_context_unavailable，与R39-R42留痕逐字同签名）；前端 node --test 97/97 + vite build 绿
- R42-06说明：冻结读取链稳定性本轮线上实证——token 78af1e05两次读取字节相等（835221B×2、content_hash=d6707ea1…、74 medium+high行/方案符合性26/23003×3/24004×3），与测试者第二次读取口径一致；首渲染76/28/×4口径未能由任何现役发布载荷复现，未发现可修缺陷路径，投影确定性已加钉住测试；若复发请测试者附每次读取的content_hash

## 2026-10-14 05:01 CST R43D 开考预置复验（只读复用常驻项目 MX循开考-CSU，零重复预置，未触 8910/5177）
- 常驻复用语义第 25 次复验（第 6 个 build api-616662809274f9f0 上三条件首验）：三条件现场实测全过——mapping confirmed（draft monmapdraft_73abe5c6c9561a9e95eec2056991 v80）+ facts ready（10表/591行/3038值全核验）+ project/open current（canView/canEdit=true）；run-setup/options 200（snapshot_token 同值 snapshot:ef8692acfbab4d2a9846916f）、runs 50 条全 completed 零新增零启动（全程 GET 零 POST）。
- 环境现态：build api-616662809274f9f0（R42修复员 04:32 CST 标准重启后现行进程，Python pid 59573 / node pid 59764 监听 [::1]:5178），runtime-readiness ready:true，前后端 build 配对一致（frontendBuildId=web-2dc16940535b5f3e）；8910/5177 lsof 复核 0 监听仅只读未触碰。
- R5D marker 未复发：常驻项目 workspace launch_registry.sqlite3 只读直查 marker=v5、integrity ok（size 487424B/mtime 10-14 00:45:51 CST，本轮窗口前 R42 轮内他位写入，如实并录）。
- ✅ R38D study-documents 回归的正向修复状态在第 6 个 build 保持：ready=true、protocol/ecrf 均 current/已识别；本员零修复零 POST 仅只读实测。
- independent_ai=cms-router/glm-5.3-flash（沿 10-13 08:49 降级配置，本轮零 AI 作业零调用）；AI 台账 46 条全终态零新增。详见 R5_SEEDED_PROJECT.md R43D 节。

## 2026-10-14 07:25 CST R43修复员标准重启（R43清单修复面：services/api/app/{monitoring_ai_repository,monitoring_document_authority_workflow}.py + packages/medical_monitoring/{api/r7_product/mapping_candidate_routes.py,projections/facts_publication.py} + 前端 App.jsx/AdmissionWizard/ProtocolPreparationPanel.jsx/styles.css + render fixture/pin + 新增tests/test_mm_r43_fixes.py）：
- API 重启：lsof -ti:8911 kill → 标准命令拉起（pid 90569 于 07:22 CST 启动）
- vite 重启：lsof -ti:5178 kill → 标准命令拉起（pid 90633/90628）
- 自检1 runtime-readiness：curl http://127.0.0.1:8911/api/runtime-readiness → ready:true，backend_build_id=api-31cbdf421a25007a（本轮改动新指纹，较R42的api-616662809274f9f0已更新）；independent_ai=cms-router/glm-5.3-flash ready:true
- 自检2 monitoring：curl http://localhost:5178/monitoring → HTTP 200
- 自检3 build id 配对：runtime-build.json expectedBackendBuildId=api-31cbdf421a25007a == 8911 backend_build_id → 一致；frontendBuildId=web-f601e8914442d487（R43前端改动面新指纹）
- 端口纪律：仅触碰8911/5178；8910/5177 lsof复核0监听未执行任何操作
- R43-01现场注记：B位滞留核对作业（monai_51f2a26c，22:25:13显式重试后重新排队）在本轮重启前的旧代码面（纯FIFO）于23:10:26 UTC被dwell收割为queue_dwell_timeout（retryable=1，attempt_count=0从未执行）——与零执行死锁叙事一致；新代码面下该作业等失效核对作业经「重新核对研究文件」显式重试后按任务类型优先认领（只读诊断，未以任何API推进）
- 测试留痕：新增tests/test_mm_r43_fixes.py 10/10（R43-01认领优先级×2/R43-02 dwell重置+受理回执×3/R40-05 MH空术语+MH→CM方向+品牌名负例+过宽触发词负例+逐受试者去重×5）；_recover_failed_once返回契约bool→重排列表同步更新4处断言（truthy语义不变）；回归=repository+worker+R42收敛+mm_c3 dual 103 passed；doc_jobs+r40共享运行时+facts_publication五族 52 passed；r7 data_admission 39 passed；r5 adapter+subject_flow+risk_bridge+facts五族 68 passed/1 failed（subject_flow legacy packet pinned hash，stash对照HEAD既有，与R41/R42留痕同签名）；mm_c3 bridge/cohort/confirmation/document_evidence/facts+digest 147 passed；protocol_preparation+R38-03+R42 54 passed；mapping执行策略族 58 passed；定向sweep（repository/worker/document_authority/facts_publication）267 passed；r7 router 101 passed/1 failed（late_project_dispatchers 409 result_context_unavailable，stash对照HEAD既有与R39-R43留痕逐字同签名）；前端 node --test 97/97（新增R43六项契约：差异确认挂起不宣称缺文件/主按钮指向差异确认卡/受理回执可见且不裸奔作业身份/重新计时口径/重新识别过渡说明）+ vite build 绿

## 2026-10-14 07:53 CST R44D 开考预置复验（只读复用常驻项目 MX循开考-CSU，零重复预置，未触 8910/5177）
- 常驻复用语义第 26 次复验（第 7 个 build api-31cbdf421a25007a 上三条件首验）：三条件现场实测全过——mapping confirmed（draft monmapdraft_73abe5c6c9561a9e95eec2056991 v80，candidate_count=60/field_count=60）+ facts ready（10表/591行/3038值全核验）+ project/open current（canView/canEdit=true）；run-setup/options 200（snapshot_token 同值 snapshot:ef8692acfbab4d2a9846916f）、runs 50 条全 completed 零新增零启动（全程 GET 零 POST）。
- 环境现态：build api-31cbdf421a25007a（R43修复员 07:25 CST 标准重启后现行进程，Python pid 90569 / node pid 90655 监听 [::1]:5178，以 lsof 现场实测为准），runtime-readiness ready:true，前后端 build 配对一致（frontendBuildId=web-f601e8914442d487）；8910/5177 lsof 复核 0 监听仅只读未触碰。
- R5D marker 未复发：常驻项目 workspace launch_registry.sqlite3 只读直查 marker=v5、integrity ok（size 499712B/mtime 10-14 05:21:50 CST，本轮窗口前 R43 轮内他位写入，如实并录）；静态 marker main.py:5151 + contracts.py:54 sed 实测在位。
- ✅ R38D study-documents 回归的正向修复状态在第 7 个 build 保持：ready=true、protocol/ecrf 均 current/已识别；本员零修复零 POST 仅只读实测。
- independent_ai=cms-router/glm-5.3-flash（沿 10-13 08:49 降级配置，本轮零 AI 作业零调用）；AI 台账 46 条全终态零新增，queue enabled/in_flight=0；monai_51f2a26c（R43修复员现场注记的滞留作业）实测不在本项目 ai/jobs 台账，如实记录不强行归类。详见 R5_SEEDED_PROJECT.md R44D 节。
2026-10-14 11:57 轮中无损暂停（用户指令：当前节点后停，最多20分钟）：run dwfrun-51ae15d6守候B位测试者20分钟未收卷，按时限停机（B位ask恢复重做，169步零损失；A/C/D报告在盘）。8911/5178保持运行。恢复=ResumeWorkflowRun同run_id，详见PAUSE_HANDOFF_20261014.md
2026-10-14 20:04 恢复执行（用户指令：跑完本轮+40轮深度复盘+handoff）：暂停期间环境掉线已按预案复活（ready:True）；Resume dwfrun-51ae15d6（R44的B位重派→分诊→修复→复盘→落盘）

## 2026-10-14 22:05 CST R44修复员标准重启（R44清单修复面：packages/medical_monitoring/admission/{document_authority,mapping_pipeline}.py + packages/medical_monitoring/api/r7_product/mapping_candidate_routes.py + packages/medical_monitoring/runtime/launch_registry_contracts.py + services/api/app/monitoring_document_authority_jobs.py + 前端 App.jsx/AdmissionWizard/ProductLoop/ProductProjection/MappingConfirmState + 新增tests/test_mm_r44_mapping_generation_pace.py、test_mm_r42_rule_pack_label.py）：
- API 重启：lsof -ti:8911 kill → 标准命令拉起（pid 99400 于 22:04 CST 启动）
- vite 重启：lsof -ti:5178 kill → 标准命令拉起（pid 99442）
- 自检1 runtime-readiness：curl http://127.0.0.1:8911/api/runtime-readiness → ready:true，backend_build_id=api-5f86f3eb6ec412e7（本轮改动新指纹，较R43的api-31cbdf421a25007a已更新）；independent_ai=cms-router/glm-5.3-flash ready:true
- 自检2 monitoring：curl http://localhost:5178/monitoring → HTTP 200
- 自检3 build id 配对：runtime-build.json expectedBackendBuildId=api-5f86f3eb6ec412e7 == 8911 backend_build_id → 一致；frontendBuildId=web-9d2645950d5cc182（R44前端改动面新指纹）
- 端口纪律：仅触碰8911/5178；8910/5177 lsof复核0监听未执行任何操作
- 测试留痕：R44-01共享运行时回归2项新增（advance同绑定直通adjudicating/submit_adjudication_pair显式放行，stash对照修复前红后绿）+test_mm_r44_mapping_generation_pace 5/5+test_mm_r42_rule_pack_label 3/3；回归=doc_jobs+R40共享运行时+pace+规则标注+R32重跑 47 passed；mapping五族102 passed；r7 router+freeze 106 passed/1 failed（late_project_dispatchers 409 result_context_unavailable，stash对照HEAD既有同签名）；data_admission+repository+worker 130 passed；protocol_preparation 54 passed；前端 .mjs 99/99+.jsx 11/11+vite build绿（medical-writing 3项vitest缺依赖失败为HEAD既有）
- runs/tester_loop_iso_20260928/runtime/{ai_provider_settings,ai_role_bindings}.json 的tracked差异为07:23 API进程自身startup migration的格式化重写（值零变化），本轮未触碰该等运行时数据
2026-10-15 17:08 用户手动无损暂停：状态机专项run dwfrun-55c94557停于E2E第2轮第2位在途（12/13步零损失）。已完成：考古21源/设计8决策/实施两轮（d2a19628+verifier死锁根治1f60d357）/E2E第1轮1过2停（mapping_bridge_failed）。SM1-3测试项目保留勿删。恢复=ResumeWorkflowRun同run_id，详见PAUSE_HANDOFF_20261015.md

## 2026-10-15 17:50 CST 状态机专项v2（T1-T6）实施后标准重启（改动面：services/api/app/{main,monitoring_admission_stage_store,monitoring_ai_repository,monitoring_document_authority_jobs,monitoring_document_authority_workflow,monitoring_mapping_draft_repository}.py + packages/medical_monitoring/{admission/admission_stage_view,admission/mapping_confirmation,api/r7_product/mapping_candidate_routes}.py + 前端 Wizard/WizardState/css + tests 6个新文件；提交9eee3331..2d411755）：
- API 重启：lsof -ti:8911 kill → 标准命令拉起，**新增灰度env WORKBENCH_MONITORING_AI_INFRA_RETRY=1（T5 S6灰度开启，回滚=env置空重启）**（pid 20462）
- vite 重启：lsof -ti:5178 kill → 标准命令拉起（vite启动时指纹按新后端源码重算）
- 自检1 runtime-readiness：ready:true，backend_build_id=api-2c80589e9f8dfb30（T1-T6新指纹）
- 自检2 monitoring：5178 /monitoring → HTTP 200；runtime-build.json expectedBackendBuildId=api-2c80589e9f8dfb30 == 8911 backend_build_id 配对一致；前端新代码经vite转换含stageSentinelAction
- 自检3 env在进程内生效：ps eww 20462 含 WORKBENCH_MONITORING_AI_INFRA_RETRY=1；WORKBENCH_DOCUMENT_VERDICT_CACHE未设（T6缓存默认off=零缓存路径）
- 界面冒烟（经5178非API）：项目MX循开考-CSU → 医学监查 → 开始一次新的监查 → 四步向导走通（第2步「10表/591行/3038值100%往返校验」、第4步「确认并开始监查」disabled:false）；**未点击最终开始按钮**（常驻项目预置状态保留给E2E验收）
- 端口纪律：仅触碰8911/5178；8910/5177 curl复核仍DOWN（与实施前一致），未执行任何操作
- 遗留留痕（如实）：T5 live-fire经服务层重建载荷重发SM3两条infra失败行的尝试被claim侧身份校验正确隔离（monai_b0e1764e108871cf3fb6956c0f4b → monitoring_ai_job_identity_invalid quarantine，终态无害保留作审计；retire_obsolete_generation按设计不触终态行返回0）——R11-01现场点燃未在本窗口完成，行为由env-on单测（7项）锁定

## 2026-10-16 E2E验收拦截修复（2/3卡点：事实准备一键准备恒禁用）——纯前端修复无需重启：
- 根因（代码考古）：MedicalMonitoringProtocolPreparationPanel.jsx的aiStatus prop（W04 051f8f86引入，默认{}）从未被任何父级传入——全前端0个aiStatus生产者（rg实测），independentAiReady=aiStatus?.semantic_ai_tasks_enabled===true恒false→canStart恒false→「一键准备全部主题」永久disabled且8主题恒显「独立AI当前不可运行，配置后再一键准备」，与角色配置「当前可用」（/api/ai-gateway/status同源semantic_ai_tasks_enabled=true）同屏矛盾。E2E实测43分钟15次刷新全部prepareDisabled。
- 修复（最小根因，前端only）：panel挂载时自取/api/ai-gateway/status（与角色配置「当前可用」同一权威面、role-aware激活档位）经新增纯函数protocolPreparationAiStatus归一；「刷新状态」与「重新读取」联动重读AI就绪面；fetch失败fail-closed维持不可运行文案。vite dev即时生效，**无需重启8911/5178**。
- 线上验证（浏览器经5178，MX循SM1-CSU→方案事实与规则发布）：一键准备全部主题 disabled=false（修复前恒true）；主题文案改「该主题尚未核对方案原文；点击「一键准备全部主题」后系统会检索原文并生成结构化监查候选。」（截图在案）。
- 测试：medicalMonitoringProtocolPreparation.test.mjs新增归一契约5断言（真实载荷形状/缺省fail-closed/null/非布尔/false）37 checks全过；前端全量94/94；vite build绿；回归门151 passed（0失败）。
- 8911/5178全程未重启未触碰；8910/5177未触碰。

## 2026-10-17 E2E验收拦截修复（第2轮2/3卡点：字段映射确认确认链死锁）+遗留探测行清理，8911+5178标准重启：
- 现场取证（sqlite只读，proj_user_e282a7e982b0=10-16新建MX循SM1-CSU）：主cohort 20分片=19完成+EX--试验用药1片invalid_ai_output内容级终态失败（attempt2预算耗尽）；盲核cohort 20/20全完成；02:42部分采纳成功（EX整域豁免、domain_gaps物化，T3事件留痕）；02:42:52确认路径有界重排→02:44:12同因再败（内容级确定性）。
- 根因#1（mapping_verifier_job_failed确认×5）：reconcile_with_verifier装载主cohort候选时_completed_candidates对「存在终态失败分片」无条件硬抛，缺口豁免（R10/R31）与对账exempt_domains（R11）都没有机会生效——缺口计算前置到候选装载之前，缺口域终态失败分片按缺口语义跳过（对齐盲核侧缺席域跳过），非缺口域失败分片照旧硬失败。
- 根因#2（mapping_draft_source_unavailable降级×2）：库层域完整性门在edit/confirm再校验路径把装配时已豁免的整域缺口重判missing→SourceStateError。槽位级门本有revalidating_persisted_draft放行（R31-02），域级门同源同权补齐；装配路径不传开关仍必须显式豁免（零放宽）。
- 修复验证：①离线复放（/tmp副本+新代码）E2E项目confirm_draft(降级)→**confirmed且非降级**（缺口跳过后双盲对账以全完成盲核侧收敛auto_pass）——E2E失败×7的同一操作实测通过；②新增tests/test_confirm_whole_domain_gap_partial_adoption.py 3测试（整域缺口confirm/edit不再SourceStateError/装配无豁免照旧硬拒/对账跳过缺口分片+domain_gaps透出）。
- UI#3：失败分片重跑按钮被状态段遮挡（ego-browser报<p role=status>/<div> intercepts pointer events）→纯文本aria-live状态段pointer-events:none+details scroll-margin-bottom 76px（吸底操作栏预留）。
- 遗留清理（本会话自惹自查自纠）：10-15 T5现场点燃探测产生的重建载荷行monai_b0e1764e（SM3）被_validated_job_inputs逐行校验判定payload hash mismatch→SM3 mapping-candidates GET确定性失败（/tmp/mm_api_8911.log在案）。已DELETE该行（审计事件流保留），SM3 GET实测200/0.1s恢复。
- 重启：8911标准命令（保留WORKBENCH_MONITORING_AI_INFRA_RETRY=1灰度）→build **api-4ca198219617fc39** ready:true；5178标准命令重启→指纹配对一致；8910/5177未触碰。
- 线上验证（浏览器经5178，SM1 E2E项目第3步）：面板加载后确认链推进过原死锁点（无409/无错误横幅），进入复核收尾「系统正在复核少量疑点…」正常流程；重跑分片按钮enabled可见（截图在案）。
- 回归门：tests/medical_monitoring **151 passed**（0失败）；映射族定向套件（gap/slot/inflight/deadlock/draft-events/confirmation/draft-repo）**139 passed**。
- 如实声明：①项目列表20s级超时（09:24/10:21/10:35）未定位修复——伴生于20+AI作业高峰期，疑FastAPI线程池被长同步请求占满（R7-01已知架构压力），本轮未改码；②「后台标签页自动刷新不生效（DOM冻结）」为浏览器后台节流行为，未改码；③面板复核收尾（adjudication收敛）需真实AI分钟级时长，确认落库未在本验证窗口等待完成（离线复放已证明同一操作确定性成功）。

## 2026-10-17 01:52 CST 状态机专项v3（M1-M3）实施后标准重启（改动面：packages/medical_monitoring/api/r7_product/mapping_candidate_routes.py + services/api/app/main.py + tests/{test_facts_recent_failure_window,test_gate_blocked_event}.py；提交 d00a5a49 M1 / 3fd773bd M2；M3=纯env启用零代码）：
- API 重启：kill $(lsof -ti:8911) → 标准命令拉起（cwd=workbench，env 按 `ps eww 24250` 实读逐字保留：WORKBENCH_RUNTIME_DIR=runs/tester_loop_iso_20260928/runtime、WORKBENCH_LOCAL_SINGLE_USER=1、WORKBENCH_AI_RUNTIME=api、WORKBENCH_MONITORING_AI_PARALLELISM=2、WORKBENCH_MONITORING_AI_INFRA_RETRY=1 灰度保留；**新增 M3 灰度 env WORKBENCH_DOCUMENT_VERDICT_CACHE=1**；`.venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8911 --log-level warning`，pid 36398 于 01:52:13 CST 启动）
- 自检1 runtime-readiness：ready:true，backend_build_id=**api-817b6b45dc710ed1**（M1/M2 后端改动新指纹，较 6a3d4c3d 的 api-4ca198219617fc39 已更新）
- 自检2 env 在进程内生效：`ps eww 36398` 含 WORKBENCH_DOCUMENT_VERDICT_CACHE=1 + WORKBENCH_MONITORING_AI_INFRA_RETRY=1（两灰度并存）
- 自检3 build id 配对：5178 vite 于 ~03:3x CST 同步重启（cwd=frontend，VITE_API_PROXY_TARGET=http://127.0.0.1:8911，`node ./node_modules/vite/bin/vite.js --port 5178 --strictPort`）→ dev server `/runtime-build.json` expectedBackendBuildId=api-817b6b45dc710ed1 == 8911 backend_build_id 一致；frontendBuildId=web-c0cff6198668e909（本轮零前端改动，指纹不变）；/monitoring → HTTP 200
- 端口纪律：仅触碰 8911/5178；8910/5177 lsof 复核 0 监听未执行任何操作
- 重启前在途作业（如实）：SM1(proj_user_e282a7e982b0) 遗留 4 queued + 1 running（10-16 16:54 UTC 创建、running 行末更新 17:51 UTC，上一会话中断遗留）；重启后 worker 按设计重新认领（running 3）继续推进，未人工干预
- M3 A/B 等价性（同项目 MX循开考-CSU attempt stg-cd69899943ba42618f589ba07a134a59，GET 三端点各采样 off×2 / on cold×1+warm×2）：**三端点响应体语义等价**（stage-state/study-documents md5 逐字节相同；mapping-candidates 仅跨进程 JSON 键序不同、序无关比较全等）。verdicts 表 0→4 行（两项目各 2 条目，registry_revision 按项目各异），热探后行数稳定=命中
- M3 延迟（如实，**未达「个位数秒级」预算**）：stage-state off 17.0/17.6s → on cold 14.5s / warm 14.5/14.5s；study-documents off 17.6/17.4s → on 14.6/14.4/14.2s；mapping-candidates 0.28→0.27s。剖析归因（独立进程 cProfile 同 env 导入 main 跑 document_readiness，/tmp/m4_ab/profile_docreadiness.py）：剩余成本不在 verifier 重放（已被缓存消掉），而在 S8 范围外——`source_intake._read_all` A1 JSONL 全量重读 10 次 22.1s cum / `project_source_manifest.build_manifest→latest_fact_materialization_ready→graph store_base.__init__` 27 次 13.9s cum / `_monitoring_entry_validation_is_usable` A3 复查 11.1s cum。按设计 R4：不达标不放松 fail-closed、不改超时，转剖析采样在档；缓存保留启用（回滚=env 置空）
- 界面冒烟（经5178非API，ego-browser）：项目 MX循开考-CSU → 医学监查 → 开始一次新的监查 → 四步向导走通（第2步「10表/591行/3038值100%往返校验」、第4步「确认并开始监查」disabled:false）；**未点击最终开始按钮**（常驻项目预置状态保留）；如实：项目列表首载一次「读取失败」（与 10-17 已知 AI 高峰期 /api/projects 20s 级超时同签名，重载后成功，本轮未改码）
