# 医学监查旧风险旁路关闭切片

时间：2026-07-30 08:24 CST  
范围：Checklist 空态、正式 daily-run 启动前门控及其只读状态投影。  
状态：代码与离线回归完成；未重启 API、未启动或操作任何真实 run。

## 原问题

Checklist 在风险快照为空时可直接调用旧
`POST /api/projects/{project_id}/modules/medical-monitoring/runs`，绕过当前已激活
字段映射、冻结批次能力快照、已发布规则包和正式 daily-run 状态机。

## 本轮完成

1. 前端 API client 删除旧 run 命令和旧命令边界常量；Checklist 空态只提供
   “查看准备状态”，进入本批次医学监查工作区。
2. 正式 daily-run 新增只读
   `GET /api/projects/{project_id}/monitoring/daily-runs/readiness?batch_id=...`。
   投影仅返回是否可启动、阻断状态、简洁原因和下一动作，不创建 run。
3. `POST /monitoring/daily-runs` 在创建 ledger 前强制执行同一合同：
   - 批次属于当前项目且已冻结；
   - 批次绑定的 mapping 与当前项目已激活 mapping 一致；
   - 冻结 mapping contract 含一致的 capability manifest 与 capability states；
   - 当前项目存在适用的已发布规则包或已发布的逐记录适用规则包；
   - 产品独立 AI 可用且走正式产品 API 通道；
   - 当前批次尚未成为已确认比较基线。
4. 前端只有 readiness 明确返回 `ready + start_daily_run` 才展示“开始医学监查”。
   mapping 与规则包缺口分别进入已有字段校对、方案规则准备入口；其他配置缺口只显示
   简洁状态，不制造旧旁路或“待医学批准”。
5. 已存在的正式 run 可继续恢复。readiness 临时读取失败不会阻断在途 run；新 run
   继续失败关闭。
6. daily-run 状态读取加入项目级请求作用域和 AbortController，项目切换、快速刷新及
   AI 轮询的迟到响应不能写回当前界面；确认时间缺失时不再渲染无效日期。

## 修改文件

- `frontend/src/App.jsx`
- `frontend/src/features/medical-monitoring/MedicalMonitoringBatchPanel.jsx`
- `frontend/src/features/medical-monitoring/MedicalMonitoringDailyRunPanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyRunStartGate.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringApi.test.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringDailyRunStartGate.test.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringProjectSwitchIsolation.test.mjs`
- `services/api/app/main.py`
- `services/api/app/monitoring_daily_run_router.py`
- `services/api/app/monitoring_daily_run_service.py`
- `tests/test_monitoring_daily_run_router.py`
- `tests/test_monitoring_daily_run_service.py`
- `tests/test_monitoring_record_rule_resolver.py`

## 验证

- daily-run 后端及相邻规则解析回归：`74 passed`。
- 后端本轮文件 Ruff：通过。
- `main.py` 及本轮后端模块 Python 编译：通过。
- 医学监查前端：`11/11` 个测试文件通过。
- 重点合同：
  - API client：`105 passed`
  - 启动门：`7 passed`
  - 项目切换隔离：`13 passed`
- Vite 生产构建：通过，`1910` 个模块完成转换。
- 全 frontend 源码中旧 run 路径与旧 handler 均只存在于“必须不存在”的测试断言。
- 独立只读审阅确认旧旁路关闭及前后端双重门控；其提出的异步迟到响应和空确认时间
  两项低风险问题已修订并重新通过测试/构建。

## 未操作与残余依赖

- 未重启当前 8911 API，因此运行中的旧进程尚未加载本轮后端代码。
- 未调用 readiness 实际接口，未创建、推进或确认真实 daily run，未写运行数据库。
- 规则包草稿、影子验证、发布的完整产品前端链仍是独立 P0，不在本切片内。
- readiness 的“准备医学规则”入口复用现有方案监查准备面板；规则发布链完善后仍需
  将其继续落到发布抽屉。
- Vite 仅保留既有大包体积提示，本轮没有扩大处理该非阻断债。

## 下一安全动作

后续恢复时先受控重启 API，再仅以 GET readiness 对三个真实项目读取状态并核对：
mapping revision、capability manifest、rule pack/record applicability 与产品 AI。
在规则发布链未完成且 readiness 未明确 ready 前，不得启动真实 daily run。
