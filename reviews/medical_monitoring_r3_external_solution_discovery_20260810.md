# 医学监查 R3 外部方案发现与技术选型记录

**日期**：2026-08-10  
**范围**：Study Intelligence、异构 data listing 结构画像、语义 mapping 与来源追溯  
**边界**：仅形成 R3 技术决策；未下载、安装或运行外部组件，未读取真实项目资料。

## 1. 问题拆解

R3 需要同时满足：

1. 方案、修订、IB/RSI、项目计划与外部证据可版本化、可定位、可表达有效时间和适用范围；
2. 任意 workbook/table/field 先保留原始含义，再形成可解释的领域映射候选；
3. 非标准 listing、项目自定义表和不完整元数据不能因“不符合标准”而被拒绝或误改；
4. 映射、日期、单位、编码、记录身份和 snapshot diff 必须可确定性测试；
5. 本地单用户内核保持轻量，不把大型外部平台或供应商 session 变成业务状态权威。

## 2. 一手资料核查

| 来源 | 可复用要点 | 对 R3 的限制 |
|---|---|---|
| [CDISC ODM v2.0](https://www.cdisc.org/standards/data-exchange/odm-xml/odm-v2-0) | 以供应商中立方式同时表达临床数据、元数据、管理/参考信息和审计信息；支持 XML/JSON 等序列化 | ODM v2.0 与旧版存在不兼容；R3 不声明 ODM conformance，也不要求所有 listing 转成 ODM |
| [CDISC Define-XML v2.1.7](https://www.cdisc.org/standards/data-exchange/define-xml/define-xml-v2-1-7) | 数据集、变量、受控术语、标准版本和 origin 元数据可作为 table/field profile 与来源合同的参考 | 主要面向规范化表格元数据，不能替代原始 Excel/listing 的结构发现与语义确认 |
| [CDISC Dataset-JSON v1.1](https://www.cdisc.org/standards/data-exchange/dataset-json) | 简单、稳定、可扩展的表格数据交换形状，可选关联 Define-XML 元数据 | 只作为未来 adapter 目标；当前不增加序列化运行时依赖 |
| [CDISC SDTM](https://www.cdisc.org/standards/foundational/sdtm) | 先判断 Events/Interventions/Findings 等观察类，再判断具体域；标准化表示不得改变原始含义 | R3 只把 SDTM 类/域作为候选语义提示，不能把非标准 listing 的推断映射冒充正式 SDTM 映射 |
| [CDISC DDF-RA / USDM](https://github.com/cdisc-org/DDF-RA) | Study definition、API、Implementation Guide 与受控术语共同构成可交换研究设计；代码 MIT、内容 CC-BY-4.0 | 采用概念和字段边界时保留出处/许可；不复制整个模型，也不声称本项目实现 USDM conformance |
| [OpenStudyBuilder](https://github.com/NovoNordisk-OpenSource/openstudybuilder-solution) | 标准库、研究定义、访视、入排、干预、活动和协议元素共享元数据；可作为 Study Knowledge Pack 的架构参考 | 完整方案含 Neo4j、FastAPI、Vue、Docker 等多服务；官方 README 要求至少 6GB Docker 环境，整体分发 GPLv3 且组件许可证混合；当前 R3 不采用其运行时或复制其代码 |
| [CDISC Rules Engine](https://github.com/cdisc-org/cdisc-rules-engine) | MIT 许可、持续维护，用于依据数据标准验证临床试验数据 | 用途是标准符合性验证，不解决原始异构 listing 的发现、语义映射和人工确认；保留为 R7/R8 可选 adapter 候选 |

2026-08-10 GitHub API 复核：`cdisc-org/DDF-RA`、`cdisc-org/cdisc-rules-engine`、`cdisc-org/cdisc-open-rules` 均未归档且声明 MIT；OpenStudyBuilder 仓库未归档，但顶层许可证明确为整体 GPLv3、组件按 GPLv3/MIT/CC-BY-4.0 分列。许可证与运行复杂度均不支持在当前 R3 直接嵌入完整平台。

## 3. 候选路线比较

| 路线 | 适配度 | 决定 |
|---|---|---|
| 强制转成 SDTM/ODM 后再监查 | 对规范提交数据有价值，但会丢失项目原始 listing 的自定义语义并制造虚假确定性 | 拒绝 |
| 直接部署 OpenStudyBuilder 作为研究知识底座 | 功能成熟、元数据思路强，但运行栈和迁移边界过重，且混合/强 copyleft 许可增加当前集成负担 | 拒绝直接采用；仅作参考 |
| 在 R3 内复制 CDISC CORE/开放规则 | 可校验标准化数据，但不是异构结构推断器 | 当前拒绝；保留后续 adapter |
| 小型框架中立 R3 合同 + 标准参考 + adapter 边界 | 能保留原始值/来源、不确定性和用户少量确认；与已冻结 R2 兼容且可用合成数据穷举测试 | 采用 |

## 4. 冻结决策

1. R3 新建独立纯 Python 包，首个切片只使用标准库和现有测试工具，不新增外部可执行依赖。
2. 以 USDM/DDF 的研究定义分层、ODM/Define-XML 的来源/元数据/键、SDTM 的通用观察类作为**参考合同**，不宣称标准符合性。
3. 所有输入先保存 source locator、raw label、raw value、display format 和缺失/不确定语义；规范化值和领域映射只作为版本化派生结果。
4. mapping 输出必须包含候选概念、证据特征、置信度、依赖字段、冲突和确认状态；低置信度或冲突进入少量确认，不自动接受。
5. 项目专属词典、表名和路径只能进入 adapter/fixture/配置，不得进入公共内核规则。
6. 未来支持 ODM/Define-XML/Dataset-JSON/USDM 时通过 adapter 导入导出，不反向污染内部权威对象。

## 5. 验证与回滚

- 当前选择用合成三结构 fixture、隐藏命名/列顺序挑战和稳定 identity 属性测试验证。
- 若 R3 后段发现标准 adapter 可以显著减少定制代码，再对具体版本、许可证、维护状态和本地集成成本单独建 ADR；未通过门禁前不安装。
- R3 是新命名空间，可整体停用而不修改 R1/R2、产品源码、医学写作子系统或真实项目。

