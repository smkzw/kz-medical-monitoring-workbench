# 医学监查 P10：方案监查准备编排后端切片

日期：2026-07-30  
状态：实现及聚焦回归完成

## 1. 目标

在不修改字段映射、日常运行、规则执行、前端和医学写作文件的前提下，
新增产品级“方案监查准备”编排：

1. 仅接受当前项目中已登记、已解析并已确认的 protocol 版本。
2. 由产品按固定医学监查主题检索该版本的真实方案 spans。
3. 将检索所得的准确来源包提交给既有独立产品 AI，任务类型固定为
   `protocol_clause_structuring`。
4. AI 结果只作为待当前用户确认的候选，不自动接受、不自动生成正式事实，
   更不自动发布规则。
5. 来源不足时跳过该主题并明确返回 `skipped/data_gap`，不补造条款。
6. 不直接读写运行数据库；所有作业持久化均调用既有产品 Repository/Service。

## 2. 边界

### 本切片改动

- `services/api/app/monitoring_protocol_preparation_service.py`
- `services/api/app/monitoring_protocol_preparation_router.py`
- `services/api/app/main.py`：仅增加 import、服务实例和 router 注入
- `tests/test_monitoring_protocol_preparation.py`
- 本记录

### 明确未改

- `monitoring_ai_router.py`
- `monitoring_ai_repository.py`
- `monitoring_ai_service.py`
- `monitoring_ai_worker.py`
- 字段映射相关 repository/service
- daily run、batch、risk、rule runner
- 前端
- 医学写作文件
- 任何运行数据库

## 3. 复用的现有产品契约

### 方案版本与规则仓

使用 `MonitoringProtocolRuleRepository.protocol_version()` 取得 protocol
版本，校验：

- 版本属于当前项目；
- 版本状态为 `confirmed`；
- 对应 Source Registry entry 属于 `medical_monitoring`；
- 来源类型为 `protocol_docx`；
- entry 内容哈希与 protocol 版本哈希完全一致；
- `parser_status=parsed` 且至少存在一个 span。

### 真实 span 检索与来源包

使用 `MonitoringAiSourcePacketResolver.search()` 和 `.resolve()`：

- 搜索范围由服务端固定主题词控制，客户端不能自行注入 source IDs；
- 搜索继续沿用当前来源、模块边界、内容基本校验和 override 后可用状态；
- 对相同 source ID 以及相同“entry + locator + text”进行确定性去重；
- 来源包必须且只能绑定当前 protocol 版本的 entry 与内容哈希；
- AI 输入保留 exact source bindings、locator、quote 和 source ID。

### 独立产品 AI

使用 `MonitoringAiService.submit_task()`，任务类型固定为
`PROTOCOL_CLAUSE_STRUCTURING`。模型、provider、凭证、运行时探测、输出修复、
候选校验和 worker 均沿用医学监查现有独立 AI 配置，不由代理生成或替代。

本切片的单元测试使用受控 fake provider，仅验证产品 AI 的调用合同、输入来源、
输出候选及状态持久化，不把 fake 输出计为真实医学质量通过。

## 4. 默认医学监查主题

| 主题 ID | 覆盖范围 |
|---|---|
| `eligibility_continuity` | 入选、排除、随机前复核、持续符合性和资格变化 |
| `visit_window_and_order` | 访视计划、研究日、允许时间窗、顺序、漏访和补访 |
| `study_treatment` | 试验药物给药方案、剂量调整、暂停、停药、重启和依从性 |
| `concomitant_medication_policy` | 非试验用合并用药的允许、限制、禁用、救援和洗脱 |
| `safety_assessment` | AE、SAE、AESI、实验室安全性、临床意义和安全性随访 |
| `efficacy_assessment` | 疗效终点、量表、评价时间点、评估者及缺失评估 |
| `early_withdrawal_and_deviation` | 提前退出、终止、撤回同意、失访和 PD |
| `data_quality` | 数据完整性、一致性、源数据核对、缺失、重复和更正 |

试验药物与 CM 边界已写入主题目的：试验药物给药及其变更、依从性属于
`study_treatment`，CM 只表示非试验用合并用药或治疗。

## 5. API

### 一键启动

`POST /api/projects/{project_id}/modules/medical-monitoring/protocol-preparation/protocol-versions/{protocol_version_id}/start`

- 无请求体：启动全部默认主题。
- 可选 `topic_ids`：仅启动指定的标准主题。
- 重复调用不会重复创建同一任务。

### 状态聚合

`GET /api/projects/{project_id}/modules/medical-monitoring/protocol-preparation/protocol-versions/{protocol_version_id}/status`

只返回：

- protocol 版本及来源 entry；
- 紧凑进度计数；
- 每个主题的 span 数、来源修订、紧凑作业状态；
- 完成后的候选、结构化内容、必要 claims 和原文 locator/quote。

不返回 prompt、完整 worker log、provider 内部信息或运行数据库信息。

## 6. 幂等与版本身份

每个主题先生成 `source_revision`，其确定性种子包含：

- 编排合同版本；
- `protocol_version_id`；
- 来源 entry；
- 来源内容 SHA-256；
- 主题 ID 与服务端查询词；
- 去重后的真实 span ID、locator 和 text。

business key 的确定性种子包含：

- `protocol_version_id`；
- topic；
- `source_revision`。

同一版本、同一主题、同一来源修订和同一产品 AI 合同重复启动时，
`MonitoringAiRepository.create_or_get()` 返回同一作业；来源、提示词或产品 AI
配置变化时，既有 AI Service 的稳定 job identity 与 supersede 逻辑继续生效。

## 7. 候选与确认语义

- 新候选状态保持 `proposed`。
- 对外显示 `review_status=pending_user_confirmation`。
- 本编排不调用 candidate decision、不创建 protocol fact、不调用
  `adopt_ai_candidate()`、不确认事实、不编译或发布规则。
- 用户后续主动接受候选时，仍沿用现有候选决策与规则编制链路。
- 没有使用“待医学批准”；当前医学用户的主动选择即为用户确认。

## 8. 来源不足

某主题没有检索到可用真实 span 时：

- `status=data_gap`
- `execution_status=skipped`
- `reason_code=data_gap`
- `job=null`
- `candidates=[]`
- 不调用 source packet resolver；
- 不创建 AI 作业；
- 返回明确说明，不生成任何替代文本。

## 9. LOOP 记录

### LOOP 1：契约对齐

读取并核对了现有 AI contracts、source packet、source registry span search、
AI service/repository、protocol repository、rule authoring service、router 和测试。
结论是复用现有产品 AI 与来源包即可，无需新增持久化或外部依赖；因此没有进行
外部工具选型。

### LOOP 2：最小编排实现

初版完成主题检索、去重、作业提交、状态聚合和 main 注入。首次测试发现：

1. 测试夹具 locator 随调用轮次变化，破坏幂等身份；
2. 当前测试解释器对 FastAPI 路由参数中的 `X | None` 反射不兼容；
3. fake runtime 缺少产品 AI 的完整运行环境身份，作业未真正进入 fake provider。

修订：

- locator 改为由主题确定；
- 路由使用兼容的 `Optional[...]` 注解并保留局部 Ruff 说明；
- fake runtime 补齐 provider、transport、base URL、API key、model、
  expected response model 和部署 profile。

### LOOP 3：边界加强

增加 Source Registry entry 预检，明确阻断：

- 未登记来源；
- 非医学监查模块；
- 非 protocol 来源；
- protocol 版本与来源内容哈希不一致；
- 未解析或零 span 来源。

同时避免启动后再次执行整套检索：启动阶段复用已准备的主题快照生成响应。

### LOOP 4：证明与相邻回归

完成专属测试、相邻 source packet/AI API/rule authoring/protocol API 回归、
Ruff、py_compile 和变更边界审阅。

## 10. 验证

### 专属与相邻回归

```text
.venv/bin/python -m pytest \
  tests/test_monitoring_protocol_preparation.py \
  tests/test_monitoring_ai_source_packet.py \
  tests/test_monitoring_ai_api.py \
  tests/test_monitoring_rule_authoring_service.py \
  tests/test_monitoring_protocol_rule_api.py -q

34 passed
```

专属测试单独运行：`7 passed`。

### Ruff

```text
uvx ruff check \
  services/api/app/monitoring_protocol_preparation_service.py \
  services/api/app/monitoring_protocol_preparation_router.py \
  tests/test_monitoring_protocol_preparation.py

All checks passed
```

`main.py` 存在本切片之前即有的全文件 Ruff 基线问题，未进行无关重排或清理；
本次新增 import 均被实际使用。对新文件执行完整 Ruff，对 `main.py` 执行
py_compile 和相关 API 回归。

### 语法

```text
.venv/bin/python -m py_compile \
  services/api/app/monitoring_protocol_preparation_service.py \
  services/api/app/monitoring_protocol_preparation_router.py \
  tests/test_monitoring_protocol_preparation.py \
  services/api/app/main.py

通过
```

## 11. 残余风险

1. 本切片验证了真实产品 AI 接口和 worker 合同，但未在运行数据库上创建真实项目
   作业；这是为了遵守“不直接修改运行数据库”和与正在运行的队列解耦。后续可通过
   产品 API 对真实 protocol 版本执行验收。
2. 当前每主题提交一个作业，沿用现有 `protocol_clause_structuring` 单作业最多
   5 个候选的合同。若真实方案某主题包含大量相互独立条款，后续真实项目验收应评估
   是否需要按 span 分块；本切片未擅自扩大作业数量和 token 消耗。
3. 首次真实项目验收发现，8 个主题逐一重扫大型方案会使状态查询耗时约 35 秒。
   已修订为：作业创建后，状态接口直接从不可变作业输入读取
   `protocol_version_id/topic/source_revision/evidence_packet`，不重复扫描方案；
   只有尚未启动的主题或明确 data-gap 复核才执行 span 搜索。专属回归 7 项通过，
   新增断言证明启动后的状态查询不增加 search 调用次数。受控重启后，真实 RUX
   8 主题状态聚合耗时从约 35 秒降至约 0.58 秒。
4. 本切片不负责把用户接受的候选转为 protocol facts 或规则；该责任继续由现有
   rule authoring 链路承担。

## 12. 真实产品 API 验收

- RUX-03-002 V1.3：8/8 主题找到真实方案 spans 并创建独立产品 AI 作业；
  各主题命中 13 至 50 个去重 span。
- MG-K10-SAR V2.1：8/8 主题找到真实方案 spans 并创建独立产品 AI 作业；
  各主题命中 12 至 50 个去重 span。
- 两个项目合计 16 个作业均保持 queued/proposed 链路，没有自动确认、生成事实或发布
  规则。它们与字段映射共用持久队列，将由产品独立 AI 处理。
