# P10 RUX Patient Profile 重复趋势点审阅与修复

## 任务合同

- 目标：解释并修复真实运行态 RUX Patient Profile 中 S23010 的 BSA/EASI 同日同值四个趋势点。
- 范围：RUX 源 listing 身份、Patient Profile 构建服务、前端趋势渲染、专属测试。
- 禁区：不得按日期/值粗暴去重；不得修改医学写作或其他子系统；不启动外部执行或会商。
- 完成标准：证明四行的业务身份及总值层级；若为同一源事件重复投影，则按稳定事件身份只投影一个总值点，同时保留所有组成源行；专属测试、既有相关测试和真实浏览器运行态通过。

## 来源定位与直接观察

### 真实源文件

- Listing：`/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/准备阶段/RUX-03-002_列表_数据集_Excel_20250612_处理后.xlsx`
- BSA sheet：`BSA--受累体表面积（BSA）`
- EASI sheet：`EASI--湿疹面积及严重程度指数评分（EASI）`

### S23010 BSA

解析后 row 6695-6698 共享：

- `SUBJID=S23010`
- `VISTOID=SCR`, `VISTREP=0`
- `FORMOID=bsa`, `FORMREP=0`
- `BSADAT=2024-09-06`
- `BSARESS=19`
- `PAGELMDT=2024-11-13 17:44:31`

四行的业务差异是 `RECREP=1/2/3/4` 及 `BSALOC=头/颈、上肢、躯干、下肢`，对应部位值 `BSARES=2/8/3/6`。因此四行是同一 BSA 表单事件的四个部位子记录；`BSARESS=19%` 是表单级总值，被导出到每个部位行。

### S23010 EASI

解析后 row 3801-3804 共享：

- `SUBJID=S23010`
- `VISTOID=SCR`, `VISTREP=0`
- `FORMOID=easi`, `FORMREP=0`
- `EASIDAT=2024-09-06`
- `EASISCOS=8.3`
- `PAGELMDT=2024-11-13 17:49:19`

四行的业务差异是 `RECREP=1/2/3/4`、`EASILOC` 及各部位面积/严重度组成字段。`EASISCOS=8.3` 是同一表单事件的总分，不是四次独立 EASI 测量。

### 全表交叉核查

- BSA：6806 行形成 1703 个稳定表单事件；1701 个事件各含 4 个部位行，2 个事件为单行；每个事件内日期和总值均一致，无冲突。
- EASI：3864 行形成 968 个稳定表单事件；964 个事件含 4 个部位行，2 个含 3 个部位行，2 个为单行；每个事件内日期和总值均一致，无冲突。
- 这不是 S23010 特例，也不是四条完全相同的重复导出行，而是有业务含义的部位子记录承载了重复的访视级总值。

稳定表单事件身份定义为：

`SUBJID + VISTOID + VISTREP + FORMOID + FORMREP`

`RECREP` 保留为该事件内的组成记录身份，不作为总值趋势事件身份。

## 构建与渲染链路

1. `services/api/app/listing_file_parser.py` 逐行保留 Excel 数据，未制造重复。
2. `services/api/app/rux_monitoring_service.py::_simple_efficacy_metric()` 将 BSA/EASI sheet 行送入 `_trend_points_from_rows()`。
3. 修复前 `_trend_points_from_rows()` 对每个 `RECREP` 行生成一个 `SubjectTrendPoint`，所以同一表单总值被投影四次。
4. `frontend/src/App.jsx::buildSubjectView()` 将 API 的 `efficacy_trends` 原样传入页面模型。
5. `frontend/src/features/medical-monitoring/MedicalMonitoringSubjectViews.jsx::TrendSparkline()` 对 `metric.points` 原样画圆点和明细，不做去重。

根因位于 Profile 构建层，不在 Excel 解析器或前端 SVG。前端按源模型渲染是正确行为，不应增加日期/值兜底去重。

## 修复决策

只对 RUX BSA/EASI 的访视级总值投影增加稳定表单事件合并：

- 同一稳定表单事件、日期一致、总值一致：投影一个趋势点。
- 不同 `VISTREP` 或 `FORMREP`：即使同日同值也保留为不同趋势点。
- 同一稳定表单事件内日期或总值冲突：不合并，原样保留，避免隐藏源数据冲突。
- 合并点保留一个可解析的主 `source_locator`，并通过 `source_component_locators` 保留全部组成行 locator。
- `source_record_id` 改为稳定表单事件身份，`point_id` 由该身份生成，不依赖日期/值。

没有修改前端去重逻辑、医学写作或其他子系统。

## 改动文件

- `services/api/app/rux_monitoring_service.py`
- `packages/contracts/workbench_contracts/models.py` 中仅 `SubjectTrendPoint.source_component_locators`
- `tests/test_rux_patient_profile_duplicate_trends.py`
- 本记录

## 验证记录

- `python -m unittest tests.test_rux_patient_profile_duplicate_trends -v`：2/2 通过。
- 修复后直接构建 S23010：
  - `bsa_total`：1 点，19%，2024-09-06，组成 locator 4 个。
  - `easi_total`：1 点，8.3 分，2024-09-06，组成 locator 4 个。
- 聚焦回归：既有 RUX Profile、API、风险关联、时间线及共享合同 locator 用例通过。
- `tests.test_monitoring_source_revision.RuxFullCatalogRevisionTests.test_all_241_catalog_subjects_have_revision_bound_public_drilldowns`：通过，覆盖全部 241 名 RUX 受试者。
- `node src/features/medical-monitoring/medicalMonitoringSubjectModels.test.mjs`：通过。
- `npm run build`：通过；仅保留既有 bundle size warning。
- Python `py_compile`：通过。当前环境没有可执行的 `ruff`，未运行 Ruff。
- 真实本地运行态 `http://127.0.0.1:5176/monitoring?project_id=proj_rux_03_002&scope=subject&subject_id=S23010&view=profile`：
  - BSA 图 1 个圆点、1 条明细：SCR，2024-09-06，19%。
  - EASI 图 1 个圆点、1 条明细：SCR，2024-09-06，8.3 分。
  - Patient Profile 页面无横向溢出，浏览器控制台无 error。
- 实际 API 返回 BSA/EASI 各 1 点，各点 `source_component_locators` 长度均为 4。
- 既有 `tests.test_rux_monitoring_service` 全类运行有 2 个与本修复无关的当前运行状态失败：dashboard `open_risk_count=0`、workbench inbox 无项目；Profile/趋势相关断言通过。未越界修改风险收件箱或 assurance 状态。

## 残余风险

- 当前 `source_locator` 仍指向组成行中的第一行；完整组成证据需读取新增的 `source_component_locators`。
- `_bsa_efficacy_events()` 的高 BSA 时间线事件存在既有的 `(VISTOID, date)` 合并逻辑。本 P10 只修复 Patient Profile 总值趋势，未扩大到 Subject Timeline；若后续审阅该链路，应另立任务改为稳定事件身份。
- 本次没有重新定义 BSA/EASI 医学含义，只纠正总值与部位子记录的投影层级。
