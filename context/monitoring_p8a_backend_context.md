# P8-A 后端权威风险分类与 Checklist 查询合同

## 目标

为医学风险 Checklist 建立唯一后端权威分类和服务端查询合同，消除前端依据标题或自由文本
重新推断“AE 漏报、MH 漏报、禁用药 PD”等医学类别的行为。此切片只实现后端和 API，
不修改共享前端 `App.jsx`，避免与并行医学写作开发冲突。

## 核心合同

### 权威分类

- `RiskCase.primary_category` 作为稳定分类代码，不再允许前端根据标题、risk_type 或 rationale
  改写。
- 新增版本化、封闭、可机读的医学风险类别字典，至少覆盖：
  - AE 漏报；
  - MH 漏报；
  - AE/MH 时间关系或分类复核；
  - CS/NCS 判定不合理；
  - 禁用合并用药 PD；
  - 限制合并用药 PD；
  - 试验药物剂量增加/降低；
  - 试验药物暂停；
  - 试验药物永久停药；
  - 试验药物重启；
  - 试验药物依从性；
  - 访视窗口/顺序 PD；
  - 其他方案执行 PD；
  - 实验室异常；
  - CTCAE 分级升高/异常加重；
  - 疗效评估缺失或不一致；
  - 数据质量；
  - 其他医学复核。
- 字典返回 `code`、简短中文 `label`、`taxonomy_version`、`safety_pv_flag` 和领域边界。
- Safety/PV 只允许作为附加标记，不能成为第二风险实例或替代主分类。
- CM 仅为非试验用合并用药/治疗；试验药物给药、剂量调整、暂停、停药、重启和依从性只能
  来自 `EX/EC/DA/IP` 边界。
- 分类必须由规则键/规则家族/确定性分类参数或创建风险时的显式代码产生，不得依赖标题、
  rationale 或任意自然语言包含关系。
- 旧的粗分类代码需通过显式兼容映射读取，但不得被静默升级为更细的医学结论。无法精确映射
  时返回 `other_medical_review`，并保留原代码作为 lineage。

### Checklist 查询

服务端当前风险快照接口支持七列对应的稳定筛选与排序：

- `subject_id`
- `site_id`
- `severity`
- `risk_category_code`
- `risk_item`（仅用于明确字段的文本查询，不参与分类）
- `disposition_status`
- `updated_at`

要求：

- 排序字段为封闭枚举，方向仅 `asc/desc`；
- 使用稳定次排序键，分页不得出现重复/遗漏；
- 返回 `risk_category_code`、`risk_category_label`、`safety_pv_flag`、
  `taxonomy_version`；
- 标题变化不得改变分类；
- 未知筛选/排序字段关闭失败；
- 当前快照在分页中变化时继续沿用既有快照身份保护。

## 写范围

允许：

- 新增医学监查专用风险分类模块；
- `services/api/app/medical_monitoring_summary.py`
- `services/api/app/medical_monitoring_router.py`
- `services/api/app/medical_risk_repository.py`
- `services/api/app/monitoring_rule_risk_bridge.py`
- `services/api/app/monitoring_ai_risk_bridge.py`
- 必要的真实项目医学监查适配器；
- 医学监查专属测试和 handoff/review/metrics。

谨慎：

- `packages/contracts/workbench_contracts/models.py` 为共享合同，除非最小向后兼容字段确有必要，
  否则不要修改。

禁止：

- `frontend/src/App.jsx`、全局 CSS 和医学写作前端；
- P7B/P7C 规则生命周期文件；
- 共享 AI 配置；
- 当前运行 API 与真实运行库。

## 验收

- 修改风险标题、理由或展示文本不改变分类；
- Safety/PV 标志与主分类独立；
- CM 风险不能被映射为试验药物变化，EX/EC/DA/IP 不能被映射为 CM；
- 旧粗分类明确降级为兼容类别，不凭文本细化；
- 七列筛选/排序的 API 契约、稳定分页、非法字段关闭失败；
- RUX、MG-K10、MY009 的现有风险创建路径均返回稳定分类投影；
- 聚焦、风险仓库、医学监查 API 和全医学监查回归通过；
- 不声明浏览器通过，前端接入与视觉验收属于后续 P8 切片。
