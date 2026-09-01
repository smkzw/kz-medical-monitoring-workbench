# Task Context: medical_monitoring_r3_nl_rule_adapter_20260810

Created: 2026-08-10 16:19:41
Objective: 在隔离 POC 中实现中文自然语言新增风险规则到结构化 RuleDraft、确定性模拟、影响范围建议及用户明确版本激活的模型无关纵切，不修改冻结 R1/R2/R3、产品源码、医学写作子系统或真实项目源文件，8911 保持停止。
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `cms-smk` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`，重点为 §§5-8、15、19-20：用户配置 API/Harness、ExecutionProfile 冻结、自然语言规则先拆解/模拟/确认、激活时冻结版本与 evaluation scope。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`，重点为 R3 第 8 步与 §16 当前恢复点。
- 冻结且只读的 `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`、`adapters.py`：复用模型无关执行、覆盖、截断/失败分类、原始输出封存与候选结果边界。
- 冻结且只读的 `poc/medical_monitoring_ai_native_r3/src/mm_r3/rules.py`：复用 `RuleDraft`、`simulate_rule`、`activate_rule`、三类 `EvaluationScope`。
- `reviews/medical_monitoring_r3_nl_rule_adapter_external_discovery_20260810.md`：JSON Schema 2020-12、Pydantic、Outlines、Guardrails AI 的一手资料比较与本切片不新增运行依赖的决定。
- 当前冻结锚点：R1 full tree `ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`；R2 Python `69033e28616ca497579d7b3b9bbbd87ab8fc3031eb7d0259ba3954db1a338003`；R3 root-relative Python `418b5aacef1e0be50f6d8992aa01c19a1eaaeb2008dc42da77e122e898f4120d`。
- 用户当前边界：中文原生、面向不熟悉 AI 的资深医学监察员；新增规则可发生在后续任一次阶段监查；系统需区分全历史、当前快照、仅未来；用户决定范围和激活；当前不做系统安全设计/测试。

## Scope

- In scope：新建独立 `poc/medical_monitoring_ai_native_r3_rule_ai/`；通过公开 import 复用冻结 R1/R3，不修改其文件。
- In scope：定义模型无关、JSON Schema 2020-12 兼容的中文规则解析请求/响应；模型只获得用户原文、当前项目的可用字段目录与必要业务上下文，不获得模拟记录。
- In scope：解析并严格校验 `rule_name`、`conditions`、`logical_combination`、`severity_hint`、`domain_hint`、逐条件原文依据、假设与未解决项；未知字段、未知操作符、额外属性、缺字段、截断和非 JSON 必须显式分类，不能静默猜测。
- In scope：只有 `complete` 且无阻断问题的候选可转换为冻结 R3 `RuleDraft`；随后仅在本地对合成记录运行确定性 `simulate_rule`。
- In scope：根据模拟结果与三个固定范围生成中文范围建议及影响摘要；默认可推荐当前快照，但不得自动激活。激活必须由用户明确确认、显式版本号和 EvaluationScope 完成。
- In scope：正例、阴性、歧义、未知字段、类型不符、额外键、Markdown 包裹、多个 JSON、部分 JSON、transport truncated/partial/failed、陈旧模拟、范围和版本边界测试；决定性聚焦回归、冻结 R3 回归、内存编译、缓存清理和独立新鲜上下文 QC。
- Out of scope：真实项目资料/真实患者数据、真实模型端点调用、模型选择或 API 配置 UI、R4 风险域实现、R5 前端、Query 生成、产品源码、医学写作子系统、8911 服务、系统安全设计或安全测试。

## Success Criteria

- 新包只依赖 Python 标准库及冻结 R1/R3 的公开合同，不把供应商/模型名写入公共业务逻辑，不新增第三方运行依赖。
- 结构化输出 schema 是单一权威，并能确定性导出；`additionalProperties: false`、枚举和值类型均有本地同构校验。
- 原始中文规则、逐条件 `extracted_from`、模型执行身份、输入哈希、原始输出引用、解析状态、覆盖与未解决项均可追溯。
- 模型输出不能直接创建 `RuleActivation`；`partial/truncated/failed` 或任何阻断问题均不能创建 `RuleDraft`。
- 字段只能来自调用时冻结的字段目录；禁止凭常识发明 `AEDECOD`、`ALT` 等字段。候选字段值类型与操作符兼容性可验证。
- 模拟不调用模型且不把模拟记录写回模型原始输出；空集合、缺字段和重复 record identity 保持冻结 R3 行为。
- 同一输入与同一模型候选输出产生稳定内容哈希、稳定解析结论与稳定范围建议顺序。
- 至少覆盖 AE/MH/CM/IP/PD/入排/实验室等领域词汇的结构化候选，但不得加入项目名、项目路径或具体 listing 表名特例。
- 任务内聚焦/全量测试与冻结 R3 `339 passed` 回归通过；R1/R2/R3 冻结摘要不变；8911 未监听；生成缓存清零。
- 独立 verifier 使用新鲜上下文、源码、测试与反例证据作出 ACCEPT；当前结果只称 R3 自然语言规则 AI adapter 隔离纵切，不称产品或真实项目完成。

## Risk Boundaries

- Allowed implementation writes：`poc/medical_monitoring_ai_native_r3_rule_ai/**` only。
- Allowed record writes：本任务对应的 `context/`、`prompts/`、`runs/`、`reviews/`、`metrics/`、必要的 `archives/execution/`。
- Immutable/read-only：`poc/medical_monitoring_ai_native_r1/**`、`poc/medical_monitoring_ai_native_r2/**`、`poc/medical_monitoring_ai_native_r3/**`、产品/应用源码、医学写作子系统、五个真实项目及其隔离输入。
- 不启动任何服务、监听器或 8911；不读取或运行五个真实项目；测试只用合成数据。
- 不设计或测试访问控制、密钥、攻击防护、渗透等系统安全能力；本任务中的类型、身份、版本和状态约束属于医学功能正确性边界。
- 不清理用户文件或旧项目记录；仅在验收后精确清理由本任务生成且可重建的 cache/process artifacts。
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Launch the guard-declared worker/manager route once and leave it pending for the 120-minute hard wait; do not fixed-interval poll, redispatch, or intervene because output is unchanged.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, or malformed probe output must be recorded and followed by one real route attempt. Only a missing executable or explicit invalid/retired/unlisted model may stop before that attempt.

## Loop Log

- 2026-08-10 16:19:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-10: Codex re-anchored frozen R1 capability runtime and frozen R3 rule lifecycle. Bounded external discovery selected a standards-first JSON contract plus local deterministic validation; Pydantic, Outlines and Guardrails AI remain eligible future candidates but are not adopted in this isolated slice.
- 2026-08-10: Implementation, adversarial remediation and independent conference completed. Final 13-file snapshot `8130880453d935fdd9490c19519a564a6257c8ebb51d2f53a18fd4382e20426c`; rule-AI `247 passed`, frozen R3 `339 passed`, Ruff/12-file compile green, R1/R2/R3 anchors unchanged, no cache, 8911 stopped. Pi/CMS and Minimax fallback independently ACCEPT; Grok's two cancelled outputs and Cursor's venue-level evidence veto are retained as route history, not product defects. This closes only the isolated R3 NL-rule adapter; next safe action is R4 coverage matrix plus AE/MH first risk vertical slice.
- 2026-08-10: Task, execution and conference review/metrics gates all passed. Execution prompts/runs/logs were moved by `cleanup-execution --apply` into `archives/execution/medical_monitoring_r3_nl_rule_adapter_exec_20260810/`; source, accepted reviews/metrics and live conference evidence remain. No obsolete package cache or temporary `.git` remains.
