# 医学监查 P10：字段映射候选跨作业/跨项目只读审计

## 1. 任务目标

为独立 AI 生成的医学监查字段映射候选增加一个可复用的只读观察层，在候选汇总为完整
mapping draft 之前，识别：

- 分块字段覆盖缺口；
- 稳定技术字段的跨作业、跨域和跨项目角色漂移；
- CM 与试验药物给药/变更语义越界；
- MedDRA、WHO Drug、CTCAE 编码血缘缺口或链内漂移；
- 确定性派生值的来源字段、公式和确认血缘缺口；
- 部分日期被误作精确日期的风险；
- 量表来源总分、条目/分项和工作台复算结果的角色混淆；
- 同名临床字段的跨项目差异，以便识别供应商差异、项目特异语义或提示词过拟合。

该工具只观察候选作业之间的一致性，不替代
`monitoring_mapping_semantic_quality.py` 对一份完整 mapping draft 的正式语义质量门。
它不确认、不拒绝、不激活映射，也不改变任何业务状态。

## 2. 产物

- `scripts/monitoring_mapping_candidate_audit.py`
- `tests/test_monitoring_mapping_candidate_audit.py`
- 本记录

未修改服务代码、前端或运行库。初始化工作流时自动生成但超出本侧任务写入边界的临时
context/prompt/review/metrics 文件已删除。

## 3. 数据输入与只读边界

### 3.1 SQLite

支持直接读取 `monitoring_ai.sqlite3`：

```bash
.venv/bin/python scripts/monitoring_mapping_candidate_audit.py \
  --sqlite /path/to/monitoring_ai.sqlite3 \
  --prompt-version monitoring-listing-field-mapping-v13 \
  --output-json /path/to/audit.json \
  --output-markdown /path/to/audit.md
```

只读保障：

1. 使用 SQLite URI `mode=ro` 打开；
2. 连接后设置 `PRAGMA query_only = ON`；
3. 仅查询 `monitoring_ai_jobs` 与 `monitoring_ai_candidates`；
4. 每个作业只采用符合筛选条件的最新候选；
5. 默认只纳入 `completed` 作业及 `proposed/accepted` 候选；
6. 测试对读取前后的数据库文件 SHA-256 进行比较，并确认未生成 journal。

可重复使用 `--prompt-version`、`--project-id`、`--job-status` 和
`--candidate-status` 缩小范围。工具不会执行 UPDATE、INSERT、DELETE、DDL 或 PRAGMA
写操作。

### 3.2 导出的 candidate JSON

支持以下输入形态：

- 单个候选对象；
- 候选对象数组；
- 产品 AI 输出 envelope 中的 `candidates`；
- SQLite JSON 导出行，其中 `candidate_json` 为 JSON 字符串；
- 以 `records/jobs/items/results` 包裹的候选集合。

候选必须包含 `structured_payload.field_mappings`。字段覆盖的期望集合直接取自候选已绑定
的冻结 field-profile evidence，因此不需要回查业务数据表。

## 4. 报告合同

JSON schema 版本：

`monitoring_mapping_candidate_cross_job_audit_v1`

主要节点：

- `summary`：项目、作业、项目-数据域、字段出现次数及发现计数；
- `domain_summaries`：按 project/domain 汇总作业数、唯一字段数和字段性质；
- `job_summaries`：按 project/domain/chunk 汇总字段数、期望字段数、遗漏、越界和重复；
- `inventories.technical_roles`：稳定技术字段签名；
- `inventories.coding_lineage`：编码体系、完整/不完整血缘、版本和支撑字段；
- `inventories.derived_lineage`：来源字段、公式、确认状态及缺失来源；
- `inventories.date_precision`：声明精度、精确日期支持和部分日期证据；
- `inventories.scale_roles`：量表总分、条目/分项、其他字段和来源总分；
- `findings`：错误、警告和观察项，附跨作业定位；
- `report_sha256`：对规范化报告正文计算的确定性 SHA-256。

Markdown 报告默认仅展示摘要、项目-数据域覆盖、归并后的发现、编码血缘概览和使用边界。
单项定位超过 8 处时截断显示，但 JSON 保留全量定位。

可选 `--fail-on error` 或 `--fail-on warning` 用于后续 CI；默认只生成报告，不以观察结果
改变进程退出状态。

## 5. 医学审计规则

### 5.1 字段覆盖

候选映射与同一候选已绑定的冻结字段画像逐一比较。遗漏、越界或重复属于错误。该规则
只判断每个 chunk 的候选完整性，不替代完整 draft 的全项目覆盖门。

### 5.2 稳定技术角色

仅对以下任一条件成立的字段执行强一致性检查：

- `field_kind=source_metadata`；
- 角色目录判定为 metadata；
- mapping provenance 标记为 deterministic rule。

同名稳定技术字段若在候选间出现不同角色概念或不同字段性质，报告错误。临床来源字段
不会因为同名就被强迫跨项目同义。

### 5.3 CM 与试验药物

- CM 只表示非试验用药或治疗；
- CM 数据域映射为试验药物角色时报告错误；
- 同一角色合并实际给药、剂量调整、暂时停药、永久停药、恢复给药、发放、回收或
  依从性中的多个动作时报告错误；
- 同名字段跨项目分别映射为 CM 与试验药物时仅报告警告，要求结合项目数据字典复核。

剂量调整和其他试验药物变更始终单列，不归入 CM。

### 5.4 编码血缘

编码结果字段和编码血缘支撑字段分开处理：

- MedDRA/WHO Drug 标准编码结果需具备来源字段、明确编码体系、字典版本或版本字段；
- CTCAE 分级至少需明确 CTCAE 版本或分级定义版本；
- `standardized_coded` 缺少必要血缘属于错误；
- 来源编码角色血缘不足属于警告，允许保留原始值但不能启用依赖标准编码的能力；
- 同一编码链的体系、版本或字段性质漂移属于错误；
- 字典版本和编码语言等 `source_metadata` 作为支撑字段统计，不与标准编码结果比较
  字段性质。

最后一条来自真实 V13 校准：`MDRAVER`、`MDRALANG` 是血缘支撑字段，不应因其为
`source_metadata` 而与 PT/HLT 等 `standardized_coded` 字段形成伪冲突。

### 5.5 确定性派生

`deterministic_derived` 必须同时具备：

- 非空 `source_fields`；
- 明确 `formula`；
- `user_confirmed=true`；
- 来源字段真实存在于同一项目、批次和数据域。

同名派生字段跨项目公式不一致时报告警告而非直接判错，因为可能存在项目特异计算规则。

### 5.6 日期精度

对临床日期字段检查冻结 evidence 中的代表值、top values 和异常样例。当前识别：

- `UK/UNK/UNKNOWN/XX/00` 等未知组件；
- 仅年份；
- 仅年月。

存在部分日期证据但未声明 `date_precision` 或 `supports_exact_date=false` 时报告警告；
若同时声明支持精确日期则报告错误。技术审计 datetime 不纳入临床日期精度检查。

### 5.7 量表总分与条目

- 总分和条目/分项必须使用独立角色；
- `source_collected` 总分作为观察项保留，可以展示但不得声称为工作台复算值；
- 只有满足确定性派生血缘后，工作台复算总分才可作为派生事实；
- 量表版本、语言、条目集合、条件分支、缺失计分规则仍由完整 draft 质量门和量表规则
  绑定负责。

真实数据校准中，`questionnaire_total_score` 最初因简单子串匹配被误认为同时包含
`question` 条目语义；现已改为分词级识别，只有独立 `question/item/qN` 标记才归条目。

## 6. 测试

执行：

```bash
.venv/bin/python -m pytest \
  tests/test_monitoring_mapping_candidate_audit.py \
  tests/test_monitoring_mapping_semantic_quality.py -q
```

结果：`56 passed`。

其中本工具新增 `7 passed`，覆盖：

1. 两个项目的稳定技术角色和完整 MedDRA 血缘；
2. 技术角色漂移、CM/IP 越界、多个试验药物动作合并；
3. 虚假标准编码、派生血缘不足、部分日期、量表角色冲突和 chunk 覆盖缺口；
4. 来源总分只作为观察项；
5. 两类导出 JSON 形态；
6. SQLite 文件只读及 CLI JSON/Markdown 生成；
7. 报告对输入作业顺序稳定；
8. CTCAE 分级版本与版本支撑字段的边界；
9. Markdown 长定位压缩。

附加检查：

- `py_compile`：通过；
- Ruff：通过。

## 7. 真实 V13 只读证据

冻结报告：

- 临时 JSON：`/private/tmp/monitoring_v13_cross_job_audit_final.json`
- 临时 Markdown：`/private/tmp/monitoring_v13_cross_job_audit_final.md`
- 报告 SHA-256：
  `ac723a48c682cc5b61874ad090979aa197d8689af69cf1b9eef5fd5be3726368`
- 观察截止：
  `2026-07-29T19:10:45.094292+00:00`

该时点只纳入已完成作业：

- 2 个真实项目；
- 35 个 V13 候选作业；
- 13 个项目-数据域；
- 368 个字段出现。

结果：

- 错误 0；
- 警告 3；
- 观察 8。

### 7.1 已通过的观察层不变量

本快照未发现：

- chunk 字段遗漏、越界或重复；
- 稳定技术角色漂移；
- CM 与试验药物语义越界；
- 多个试验药物动作被压成同一角色；
- 虚假标准编码或编码链漂移；
- 虚假确定性派生。

MedDRA 血缘：

- 10 个标准编码结果字段具有完整血缘；
- 2 个支撑字段：`MDRAVER`、`MDRALANG`；
- 版本通过独立字段 `MDRAVER` 绑定；
- 未发现链内体系、版本或字段性质漂移。

### 7.2 保留的真实警告

3 个日期字段存在部分日期，但候选尚未形成日期精度声明：

- `ASH.ASHDAT`：可见 `2023-UK-UK`、`2015-UK-UK` 等；
- `CM.CMENDAT`：可见 `2024-10-UK`、`2024-UK-UK` 等；
- `CM.CMSTDAT`：可见 `2023-08-UK`、`2024-08-UK` 等。

这些字段可保留原始值并用于保守顺序判断；在精度模型或上下界未建立前，不得直接驱动
精确洗脱期、访视窗、持续时间或固定天数 PD 结论。

### 7.3 保留的观察项

- `CDLQIRES` 识别为来源总分；CDLQI 条目字段单列。该来源总分可以展示，但尚不能声称
  是工作台复算结果。
- 7 个同名临床字段存在跨项目角色文字差异，例如 code/flag、code/assessment 或
  status/status text。工具仅将其列为观察，不自动判错；后续需判断它们是供应商字段
  口径差异、真实项目语义差异，还是提示词可进一步收敛的同义表达。

## 8. 未解决风险与下一使用点

1. 真实 V13 队列仍在运行，本快照不是全量验收；全量候选完成后必须重新执行。
2. 本快照尚未出现可核验的 WHO Drug、CTCAE 标准化候选，也没有
   `deterministic_derived` 候选；对应路径已有临时数据测试，但缺少本轮真实项目证据。
3. 日期精度识别是保守启发式；新供应商若使用其他未知组件标记，应以真实样本扩展，
   但必须始终保留原值。
4. 跨项目临床角色差异只提供观察层信号，不能脱离项目数据字典、CRF 和方案判定优劣。
5. 全量完成后建议依次执行：
   - 本工具审计全部 V13 候选；
   - 汇总完整 mapping draft；
   - 调用正式 draft 语义质量门；
   - 仅在无全局阻断且能力状态符合要求时确认/激活。
