# 医学监查 P10：V13 双项目早期语义审阅与公平调度

## 1. 审阅范围

- 运行库：`runtime/medical_monitoring_ai.sqlite3`（只读审阅；未直接修改）
- 提示词合同：`monitoring-listing-field-mapping-v13`
- 真实项目：
  - RUX-03-002 当前全量 listing
  - MG-K10-SAR 当前全量 listing
- 独立 AI：产品运行配置，由医学监查 API 自主调用；测试者未代替产品 AI 生成候选
- 早停原则：先审首批跨域结果；若出现通用医学边界或角色合同错误，先修合同，不等待
  325 个字段块全部消耗完成。

## 2. 队列公平性问题与修复

原 `claim_next()` 严格按全局创建顺序领取。RUX 先创建 175 个作业，MG-K10 后创建
150 个作业，因此四个并发槽会长期被 RUX 占用。该行为虽符合 FIFO，却会造成多项目
饥饿，不适合真实医学团队并行开展多个项目。

领取顺序现调整为：

1. 计算每个候选项目当前未过期的 `running` 作业数；
2. 优先领取运行槽最少项目的最早作业；
3. 同一项目内仍按 `created_at + job_id` 保持稳定顺序；
4. 不改变 lease、CAS、重试、审计和候选生命周期。

聚焦仓储/worker/service 回归：143 项通过；Ruff 通过。受控 API 重启后，MG-K10
立即获得 4 个真实产品 AI 槽，证明公平调度生效。停止前的 4 个 RUX lease 保留到过期，
没有直接改库或伪造完成状态。

## 3. 首批医学语义观察

截至本轮审阅：

- RUX 已完成：AE 6/6、AH 2/2、BSA 2/3；
- MG-K10 已完成：AE 3/3、AH 2/2、ALR 2/2、ASH 2/2、CM 1/3；
- 关键 CM 临床字段、试验药物 DAA/DAB、RUX BSA 评分字段仍未形成充分样本，不能放行。

已验证的正向信号：

- `SITENM`、`SUBJINI`、`VISIT`、`FORMNM__n`、`Block顺序号` 等 V13 新增稳定字段
  均由确定性规则输出，未再跨域自由命名；
- RUX AE 的 MedDRA LLT/PT/HLT/HLGT/SOC 术语和代码均为
  `standardized_coded`，且明确 `coding_system=MedDRA`、
  `dictionary_version_field=MDRAVER`；
- `AETERM` 保持来源报告术语，不因存在 MedDRA 编码链而被错误覆盖；
- AE 严重性与严重程度保持不同角色，未将 `seriousness` 与 `severity` 混为一谈；
- 当前尚未观察到把 CM 当作试验药物给药、剂量调整或停药的越界。

## 4. 尚未收口的问题

同一来源字段 `SUBJSTA` 在不同域被输出为：

- `subject_status`
- `subject_study_status`
- `subject_status_text`

三者语义接近，现有闭合角色目录会归入同一受试者状态概念，因此不是 CM/IP 或编码
血缘级全局错误；但原始推荐角色仍不统一。正式映射前必须收敛为一个项目无关的规范
角色，并为未来项目增加可审计的跨作业一致性检查，避免要求医学经理逐域重复修订。

此外：

- MG-K10 的 `ASHDAT`、`ASHYN/ASHYN1` 目前仅形成通用日期/是非角色；必须结合完整
  表单字段及项目方案判断其医学含义，不能仅凭字段名提升为具体临床结论；
- RUX `AETOXGR` 仅能证明来源分级值，尚无充分证据声明 CTCAE 版本；
- BSA、DLQI/CDLQI 等量表的总分、条目和复算血缘仍需等待完整字段块。

## 5. 下一步验收门

1. 等待并审阅两项目的 CM 临床字段和 RUX DAA/DAB；
2. 审阅 BSA、DLQI/CDLQI 的量表总分/条目/复算血缘；
3. 运行跨作业、跨域、跨项目候选一致性报告；
4. 对 `SUBJSTA` 等同义漂移形成一次性归并机制；
5. 只有完整字段块全部完成、语义门可解释且医学边界通过后，才允许批量采纳并组装 draft。

