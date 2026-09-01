# R5-S5 Subject Workspace / Patient Journey Contract v0.1 Context

日期：2026-08-26

## 当前状态

本批次只冻结 renderer-neutral 的 R5-S5 Subject Workspace / Patient Journey
typed contract；不创建 S5 runtime、test、UI、browser、service 或产品文件。
当前文件是候选快照，worker-01 不发出 `ACCEPT_R5_S5_CONTRACT`，最终接受仍需
独立 verifier 和 fresh isolated review。

## 权威链

- R5 v0.3 exact contract：`artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json`，父合同 raw/content SHA
  由 manifest 固定。
- Subject temporal 公共包：`subject-temporal-public-v1`。
- AE/MH match-history 公共包：`aemh-match-history-public-v1`。
- 两个公共包只接受冻结 `AuthorityBundleV02` 输入；candidate packet、fixture
  文本/计数、case id、文件名、未绑定 hash、nearest record 和 UI state 均不是医学或
  身份权威。

## S5 contract closure

- canonical leaves：265；core authority leaves：216。
- deferred core：0；placeholder core：0；self-signed core：0。
- parent v0.3 leaves：195，其中 53 个
  S5 deferred/shallow leaves 被明确替换为完整 typed packet leaves；不能表达 cutoff absent、日期范围或
  append-only history 的浅对象不会被误当成 S5 authority。
- challenge rows：250（父合同 204 行、S5 专项 36 行、
  accepted public replay 10 行）。这些行仅是测试元数据。
- 每一行都冻结 executable `single_mutation(op/path/value)` 与 `oracle_contract(rule_id/expected_outcome/expected_error/expected_projection/required_non_llm_anchor/test_locator)`；
  structured mutation/oracle rows：250/250，S5 专项不使用 alias 或 placeholder mutation。
- presentation leaves：22；它们是 S5-owned non-core renderer vocabulary，均明确
  `acceptance_claim=false`。域标签/形状/线型、禁词和 subtype 列表绑定 accepted R5 stage review 的精确 Markdown 行/段落，
  同时冻结 stage raw SHA、parent raw SHA 和 parent content SHA；legacy treatment 只绑定 parent 的实际
  `/legacy_domain_policy/<kind>` 对象。不存在 `/contract_constants/*` pseudo-selector，也不把 schema descriptor/predicate 当标量权威。
- `S5SeverityEncoding.line_weight` 的数值及 `S5AudienceLexicon.content_hash` 未被已接受来源具体冻结，均保留为
  future-renderer parameter，值为 null 且不构成 acceptance claim；clinical/identity/date/domain-event/history leaves
  仍是 core 并只来自 accepted executable public packets。
- 已接受 public-authority producer/test/evidence 的显式 path+SHA pin：11；
  manifest input raw pin map：59。

## Frozen semantics

一个 shared temporal context 绑定 Journey、Profile 和 Timeline 的同一 spine、axis、window、selection
和 anchor。实际日期轴为默认；study day 是显式投影。exact/partial/conflicted/missing 日期保留完整
endpoint state、candidate values、range 和 projectability，不吸附到名义访视或伪造日期。

域闭集恰好八类：AE、MH、CM、IP 给药、检验与检查、住院与操作、症状与疗效、方案符合性；unknown
和 OTHER fail-closed。不依赖颜色区分 event/risk，risk overlay 与事件形状严格分离。AEMH 保留
原始 reminder、后续 fact、identity evidence、previous prefix 和 append-only sequence；不自动关闭风险，
不重写 identity。
- domain/subtype matrix 是 exact 八域闭集：`ae=ae`、`mh=mh`、`cm=concomitant_medication`、
  `ip=(ip_dose,ip_pause,ip_resume)`、`lab_exam=(lab,exam)`、`hospital_procedure=(hospitalization,procedure)`、
  `symptom_efficacy=(symptom,efficacy,scale,outcome,trend)`、`protocol_compliance=protocol_deviation`；
  `ae/ip_dose` 及所有未列 pair 均 fail-closed。
- legacy severity 只允许 `severe→high`、`moderate→medium`、`mild→low`；unknown value fail-closed。
- future S5 runtime 必须在 projection acceptance 前由 `s5_validator.py::validate_domain_subtype_pair` 拒绝
  `domain=ae, subtype=ip_dose`，错误为 `DOMAIN_SUBTYPE_MISMATCH`、projection 为 `not_emitted`；对应 validator/test/challenge
  仅作为 exact 11-path future allowlist contract 冻结，当前均 absent。

## Boundaries and unlock

8911 必须保持 stopped；medical-writing 的既有保护聚合为 542
文件及其冻结 inventory SHA。即便未来 fresh review 接受本合同，也只允许 manifest 中 exact
`future_runtime_allowlist` 的 synthetic/offline create-only 路径；不解锁 8911、UI/browser、真实项目/模型、
产品/生产、medical-writing、producer mutation 或 security work。
runtime surface scan 覆盖 `poc/medical_monitoring_ai_native_r5/src/mm_r5, poc/medical_monitoring_ai_native_r5/tests, poc/medical_monitoring_ai_native_r5/evidence` 的全部非 cache 文件（冻结
51 个，inventory SHA `d94c9e7203572519f9db92c219d4f18a9b76fdd3af0fd8a60b98b85120ecb915`）；
任意新增或改名文件在生成前 fail-closed，future allowlist 恰为 11 个路径且当前全部 absent。
unlock 还必须由 fresh isolated 外部 review/conference record 绑定 exact contract hash、manifest hash、generator raw SHA、
verifier raw SHA、全部 generated artifact raw SHA 及 exact acceptance token；worker 不自签，verifier 不在自身 source 内自哈希。
