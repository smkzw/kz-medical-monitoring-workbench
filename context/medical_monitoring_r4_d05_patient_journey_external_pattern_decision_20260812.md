# R4-D05 Patient Journey 外部模式核验与实现决定（2026-08-12）

状态：`DECISION_RECORDED_FOR_D05_PROJECTION`

## 问题与边界

D05 当前只实现 renderer-neutral `VisitJourneyProjection`；不实现 R5 前端、不引入可执行前端依赖，也不把外部医疗数据模型直接写成项目业务模型。本次核验只回答：共享访视轴的数据投影应保留哪些计划、实际、episode、时间和来源关系，才能支持后续高质量交互式 Patient Journey。

## 外部一手资料

1. HL7 FHIR R5 `Encounter`：Appointment/计划阶段与实际 Encounter 是不同对象；实际接触可按 setting/type 区分，Encounter 可通过 `partOf` 表达住院内更细的接触层级，并以实际 period 表达持续时间。来源：https://hl7.org/fhir/encounter.html（检索日 2026-08-12）。
2. OHDSI ATLAS：开放源码 Apache-2.0 项目，Patient Profile 用于查看特定受试者的医疗记录；其 Person Profile 数据接口同时返回记录集合和相对 index day，支持以稳定基准观察多域事件的相对位置。来源：https://github.com/OHDSI/Atlas 与 https://ohdsi.github.io/ROhdsiWebApi/reference/getPersonProfile.html（检索日 2026-08-12）。

## 方案比较与结论

- **把计划访视与实际接触压成一个节点**：拒绝。会隐藏 missed visit、窗口偏移、一个计划访视多次接触、一次住院承载多个计划访视和待定归属。
- **只输出扁平事件列表**：拒绝。无法支持共享时间刷选、计划—实际 edge、跨域轨道和后续 Profile/Timeline 同步。
- **采用本项目的最小 renderer-neutral 投影**：采用。分别输出计划访视、实际接触、活动、风险、待定时间、cutoff 后上下文与稳定 join；以后由 R5 选择具体渲染技术。
- **本阶段引入 OHDSI/其他前端组件**：不采用。OHDSI 证明了 index-relative profile 和多域记录可视化模式，但它服务于 OMOP 观察性数据，不满足本项目方案访视 expected-set、双 cutoff、PD Query 和临床试验来源权威合同；直接集成会扩大 D05 范围。

## 对 D05 投影的约束

1. 计划访视与实际 Encounter 独立建模，以稳定 assignment edge 连接。
2. 一个计划节点可以连接多个实际接触；一个 episode/bundle 可承载多个计划节点，但不得合并 obligation identity。
3. 顶层保留实际日期连续轴、名义访视窗口、clinical cutoff、阶段和相对研究日/锚点信息；任何相对位置都必须可回到冻结 anchor。
4. AE、MH、CM、IP、检查/检验、住院/操作、症状/疗效、方案符合性保持独立域轨道；不得退化为“已记录事项”或“通用风险点”。
5. 日期缺失、冲突、部分日期、待定归属和 cutoff 后事件进入独立集合；不得为了渲染伪造时间点。
6. 风险 marker 保留 unit/risk/query/source locator 的稳定 join；筛选、聚类、缩放只改变显示，不改变 L1/L3。
7. 本决定不采用新依赖，回滚方式为删除本记录并保持冻结 D05 合同；实现仍以合同和当前测试为唯一验收权威。

