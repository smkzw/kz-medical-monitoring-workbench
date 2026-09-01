# P10 字段映射受控切换与导出上下文归一

时间：2026-07-30

## 目的

在不直接修改运行数据库、不绕过语义质量门的前提下，为真实 V13 字段映射提供可重复的
正式 API 检查、采纳、确认和激活路径；同时处理真实候选暴露的导出上下文字段角色漂移，
避免医学经理逐域修订同一类技术字段。

## 实现

1. 新增 `scripts/qc/monitoring_mapping_api_cutover.py`。
   - 默认 `--action check`，只读取 `field-mapping-status`。
   - `adopt` 和 `confirm` 必须显式指定并提供不少于 10 个字符的理由。
   - 全量作业未完成、完成作业候选不是恰好 1 个、profile SHA-256 缺失时停止。
   - `confirm` 只调用正式 draft confirm API，使用 draft version、project version CAS
     和确定性幂等键；不编辑 blocker，不写 SQLite。
   - `activation_disposition=reject` 时在确认前停止。
   - 可将请求路径、状态摘要、draft 质量报告和激活结果写为 JSON 证据。
2. draft 组装边界新增保守导出上下文归一。
   - `FORM` → `form_name/source_metadata`
   - `PAGE` → `page_name/source_metadata`
   - `LINE` → `record_line_number/source_metadata`
   - `LB*` 域的 `LBNAM` → `laboratory_configuration_name/source_metadata`
   - 原独立 AI 候选保持不可变，draft 中注明归一依据和修订提示。
   - `unmapped`、标准编码、确定性派生、CM/IP 字段不进入该归一。
3. 闭合角色目录补入上述角色及真实候选中已观察到的同义名称。
4. 只读跨作业审计器修订：
   - 全空 `unmapped` 技术字段不与有值技术字段构成角色漂移。
   - 已知导出上下文字段按正式 draft 的归一结果比较。
   - `source_collected` 与 `unmapped` 的未标准化编码候选不再误报编码链错误；
     只有涉及 `standardized_coded` 或版本/编码体系冲突才是编码链错误。
   - 域尚未完成全部 chunk、且候选已声明真实来源字段和版本字段时，跨 chunk
     版本支持暂缺为 warning；全量后仍缺失会恢复正式错误。

## 真实运行观察

- RUX 只读检查曾发现 `LBTUBE:0002-of-0004` 因产品 AI 返回外层 schema 而失败。
  已通过正式 `field-mapping-jobs` 的 `retry_failed=true` 路径重排队；未直接改库。
- 重试后 RUX 状态为 87 completed、3 running、85 queued、0 failed。
- 三项目候选审计在本切片最终观察点：
  - RUX：97 jobs、1008 field occurrences、0 error、39 warning。
  - MG-K10-SAR：104 jobs、1036 field occurrences、0 error、7 warning。
  - MY009：36 jobs、349 field occurrences、0 error、46 warning。
- warning 主要为未完成域的跨 chunk 编码支持、来源编码候选缺少完整血缘及能力限制，
  不等于正式映射已通过。

## 验证

- 受控切换工具与 AI API：`12 passed`。
- mapping draft、语义质量、候选审计：`119 passed`。
- mapping、activation、batch lifecycle、daily run、record resolver 联合：
  `211 passed`。
- 相关文件 Ruff 与 Python compile：通过。
- 真实只读证据：
  `runs/execution/medical_monitoring_p10_20260730/loop_2_mapping_cutover/`。

## 未完成

- 三项目 V13 尚未全量完成，不得执行 adopt/confirm。
- 全量完成后必须重新运行候选审计，再通过正式 API 组装 draft；此时任何未补齐的
  MedDRA/药品编码、日期精度、量表或试验药物语义应由正式语义质量门阻断或限制能力。
