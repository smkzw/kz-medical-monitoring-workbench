# R3 中文自然语言规则适配器：外部方案发现与技术决定

**日期**：2026-08-10  
**范围**：用户自然语言风险条件到结构化规则草案的交换与验证边界  
**结论**：采用 JSON Schema 2020-12 兼容合同、Python 标准库本地严格校验和既有 R1/R3 生命周期；本切片不新增第三方运行依赖。

## 1. 必须满足的结果

1. 适配用户自行配置的任意 API 或 harness，不让业务代码选择供应商或模型。
2. 模型输出只能是可追溯的候选解释，不能越过本地字段目录、模拟和用户确认直接激活规则。
3. 对中文长句、医学缩写、日期/剂量/范围、多条件逻辑和未解决歧义作显式表达；不能用“尽力解析”掩盖截断或字段发明。
4. 与冻结 R1 执行证据和 R3 `RuleDraft → Simulation → Activation` 合同直接衔接，改动可整体撤回。

## 2. 一手资料核验

| 候选 | 一手证据 | 适配判断 |
|---|---|---|
| JSON Schema 2020-12 | [官方规范页](https://json-schema.org/specification)将 2020-12 列为当前版本，并分为 Core 与 Validation | 适合作为供应商中立交换合同；但规范本身不提供医学语义或运行时校验实现 |
| Pydantic | [官方仓库](https://github.com/pydantic/pydantic)提供类型驱动验证并支持 JSON Schema；[许可证](https://github.com/pydantic/pydantic/blob/main/LICENSE)为 MIT | 成熟且可用，但 R3/R1 当前无依赖清单；为少量固定字段引入运行依赖和版本迁移成本暂不划算 |
| Outlines | [官方仓库](https://github.com/dottxt-ai/outlines)支持 JSON/Pydantic/grammar 约束生成，声明 Apache-2.0 | 对可控本地模型或受支持服务很有价值；用户 harness/API 范围更广，不能保证所有执行端采用 generation-time constraints，因此不能作为公共基座 |
| Guardrails AI | [官方仓库](https://github.com/guardrails-ai/guardrails)支持 Pydantic 结构化输出与校验，声明 Apache-2.0 | 能组合 validator，但引入额外框架、插件/服务形态与 provider 适配面；不能替代本地冻结字段目录和显式激活门 |

## 3. 路线比较

| 路线 | 优点 | 当前决定 |
|---|---|---|
| 直接依赖 Pydantic | 实现快、错误信息成熟、可生成 schema | 暂不采用；现有 dataclass/标准库足以覆盖隔离纵切，避免形成新的版本基座 |
| 直接依赖 Outlines 或 Guardrails AI | 可约束或修复部分模型输出 | 暂不采用；对用户任意 harness/API 的覆盖并不统一，依赖面和回滚面过大 |
| JSON Schema 合同 + 本地严格解析 + R1/R3 复用 | 供应商中立、最小改动、可确定性测试、可整体撤回 | 采用 |

## 4. 冻结设计决定

1. schema 使用 JSON Schema 2020-12 可表达子集，同时用标准库写同构的严格解析器；所有额外属性拒绝。
2. 输出必须是单个 JSON 对象；不自动剥除 Markdown 代码围栏，不从散文或多个对象中“抢救”一个看似正确的片段。
3. 条件字段必须命中调用时冻结的字段目录；字段的允许操作符和值类型由目录决定。未知项进入阻断问题，不自动别名化。
4. R1 `CapabilityAttemptResult` 提供执行身份、输入哈希、原始输出、coverage 和 terminal state；本适配器只消费其公开数据，不创建第二套 transport。
5. 只有完整覆盖、无阻断问题的候选才能构造 R3 `RuleDraft`。模拟完全在本地执行，三个范围建议按固定顺序生成；用户明确确认后才调用 R3 `activate_rule`。
6. 若后续出现复杂 union/递归 schema、跨语言客户端或高吞吐需求，再以代表性错误语料比较 Pydantic/jsonschema 等具体版本；届时单独核验许可证、依赖树、维护和迁移成本。

## 5. 回滚与验证

- 所有新代码位于独立命名空间，可删除该目录而不改动冻结 R1/R3。
- 使用合成中文规则、恶意宽松输出、截断/partial/failed 状态、字段类型与 scope 边界做反例验证。
- 本记录不是对任何真实模型、真实项目或临床规则准确性的认可。
