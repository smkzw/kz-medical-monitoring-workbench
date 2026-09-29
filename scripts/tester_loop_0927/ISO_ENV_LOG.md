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
