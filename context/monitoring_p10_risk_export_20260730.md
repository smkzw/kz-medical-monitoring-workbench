# 医学监查 P10 当前风险与证据导出

**日期：** 2026-07-30  
**状态：** 源码与隔离 API/前端验收通过；当前 `8911` 后端未为本切片重启  
**合同：** `medical-monitoring-risk-export-2026-07-30.1`

## 1. 目标

在项目级医学风险 Checklist 上，按用户当前范围、筛选和排序导出当前持久化风险快照，
同时提供逐风险、可直接审阅的证据。导出不得重新生成风险、改变风险或处置状态，也不得
暴露本地路径、内部任务编号或内部风险实例编号。

## 2. 边界

- 仅修改医学监查风险快照查询、导出 API、Checklist 下载入口及其聚焦测试。
- 未修改医学写作、daily run、mapping、protocol preparation 或 `main.py`。
- 未重启当前 `8911` 后端，避免干扰正在运行的独立 mapping 工作。
- 导出沿用项目 canonical ID、当前持久化 snapshot、已有筛选/排序校验及 work-item
  处置投影；没有新增风险评估或写入路径。
- 前端不新增默认表格列，仍保持七列 Checklist。

## 3. 产品与接口实现

### 3.1 导出入口

- Checklist 状态工具栏右侧新增下载图标按钮。
- 按钮使用当前项目、范围、筛选、排序及已固定的 snapshot ID 发起导出。
- 当前页码和每页条数不会进入请求，导出的是所有符合当前条件的风险，而非当前页。
- 下载期间按钮禁用；失败沿用医学监查页面现有错误反馈。

### 3.2 API

`GET /api/projects/{project_id}/modules/medical-monitoring/risk-snapshots/current/export`

支持当前风险快照已有的：

- snapshot、中心、受试者、风险键/实例、风险类别、具体风险项；
- 风险级别、当前处置、更新时间、风险状态、批次变化；
- 是否包含终态风险；
- 排序字段和升降序。

不接受分页或未声明参数。服务先调用现有 `current_risk_snapshot` 获取、校验并固定当前
snapshot，再以同一 snapshot 和相同条件取得完整结果。因此导出期间即使产生新快照，
同一个导出包也不会跨快照混合。

### 3.3 导出包

响应为 ZIP，包含两个带 UTF-8 BOM 的 CSV：

1. `risk-checklist.csv`
   - 受试者编号
   - 中心编号
   - 风险级别
   - 风险类别
   - 具体风险项
   - 当前处置
   - 更新时间
2. `risk-evidence.csv`
   - 通过“风险清单行号”与 Checklist 行关联；
   - 先列原始 listing 事实，再列方案依据、计算过程、其他来源，最后列系统规则与判断；
   - “原始事实或依据”为主字段，“次级定位”为溯源辅助字段；
   - 同时保留证据状态、判断理由和建议动作。

证据文字优先使用已经冻结在风险快照中的可读摘要或原文，其次才从公开字段组合事实。
不得回到源文件重新解析，也不得通过独立 AI 重新生成证据。不存在冻结来源片段时明确
标记，不伪造证据。

## 4. 隐私与只读保证

- 输出前移除 macOS/Linux/Windows 本地绝对路径。
- 不导出 `job_id`、candidate/batch ID、内部 hash、mapping/prompt/rule revision、
  source revision、内部文件路径或 `risk_instance_id`。
- 内部 locator 前缀不进入公开定位；公开 display locator 可作为次级定位保留。
- API 只执行 GET；聚焦测试在导出前后比较风险 snapshot/instance 数据库行数，确认无写入。
- 过滤、排序、风险类别与处置状态均来自当前服务端权威投影，不复制第二套业务规则。

## 5. 改动文件

- `services/api/app/medical_monitoring_summary.py`
  - 导出合同、完整 snapshot 投影、ZIP/CSV 组装、证据排序和公开字段清理。
- `services/api/app/medical_monitoring_router.py`
  - 项目级只读导出路由、参数白名单及响应头。
- `frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs`
  - 二进制下载客户端与文件名读取。
- `frontend/src/features/medical-monitoring/medicalMonitoringApi.test.mjs`
  - 当前筛选/排序透传、无分页、GET/ZIP 合同测试。
- `frontend/src/features/medical-monitoring/MedicalMonitoringRiskChecklist.jsx`
  - Checklist 工具栏下载图标及加载状态。
- `frontend/src/App.jsx`
  - 当前查询导出、浏览器下载和错误处理；延迟释放 object URL。
- `frontend/src/styles.css`
  - 下载按钮稳定尺寸和工具栏对齐。
- `tests/test_medical_monitoring_risk_export.py`
  - 新增 API、CSV、证据优先级、脱敏、只读和非法参数测试。
- `tests/test_frontend_unified_risk_workbench_contract.py`
  - Checklist 下载入口及无新增列合同。

## 6. 验收证据

### 6.1 自动化

- `pytest`：
  `tests/test_medical_monitoring_risk_export.py`、
  `tests/test_medical_monitoring_module_contract.py`、
  `tests/test_frontend_unified_risk_workbench_contract.py`
  - 结果：`32 passed`
- 前端医学监查 API 测试：
  - 结果：`86 passed`
- Ruff：
  - 结果：`All checks passed`
- Python `py_compile` 与 Node `--check`：
  - 结果：通过
- Vite 生产构建：
  - 结果：1903 modules，构建成功
  - 保留既有约 1.71 MB 主 chunk 警告，本切片未新增架构级依赖。

### 6.2 真实桌面前端

在 `1280×720` 真实运行页面验证：

- 下载按钮唯一、可见、可用；
- 按钮为 34×34 px，位于 Checklist 状态工具栏右侧；
- 七列 Checklist 未变化，无文字溢出或工具栏错位；
- 浏览器控制台无 error/warn。

未在当前页面实际点击下载：运行中的 `8911` 服务启动于本次后端路由落盘之前，且承载
并行 mapping 工作。为遵守任务边界，本轮没有重启该服务；下载字节、文件名、ZIP 内容和
只读行为均已通过隔离 FastAPI `TestClient` 验证。

## 7. 残余风险与下一步

1. **运行态激活：** 下一次受控后端重启后，新路由才会进入 `8911`。应执行一次真实页面
   下载，使用 Excel/Numbers 打开两个 CSV 并核对中文、排序和当前筛选。
2. **大批量内存：** 当前导出在内存中组装完整 CSV/ZIP，适合现有项目级快照规模。若单项目
   风险量未来达到数十万级，应改为同一 snapshot 上的流式生成，不改变导出合同。
3. **历史证据完整性：** 旧风险可能没有冻结来源片段；导出会明确标记“未包含冻结来源片段”，
   仅保留已有判断理由和建议动作，不回填或虚构原始事实。
4. **格式范围：** 本切片交付 CSV/ZIP，未提供 XLSX；CSV 已满足当前要求并避免引入新的
   文档生成依赖。
5. **构建体积：** Vite 主 chunk 警告是全前端现有问题，不属于 P10 导出功能阻断。

下一安全动作：在不影响 mapping 的受控窗口重启 API，完成一次真实 ZIP 下载与人工内容
核对；若通过即可关闭 P10 导出切片。
