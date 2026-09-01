# R4-D07 外部依据与模式取舍 — 2026-08-13

Status: `DRAFT_EVIDENCE_DECISION`

## 研究问题

为合成/离线 D07 合同确定：实验室/生命体征/心电/体检/影像等安全检查如何形成可追溯的个体风险，而不把任何异常自动等同 AE、不把 CTCAE 等级等同严重性、不把监察优先级伪装成医学等级，也不把项目特异阈值硬编码进通用内核。

## 一手来源

1. [ICH E2A / FDA PDF](https://www.fda.gov/media/71188/download)：AE 可包含不利且非预期的实验室异常；AE、ADR、严重性及严重程度必须分开。
2. [ICH E3](https://database.ich.org/sites/default/files/E3_Guideline.pdf)：安全性评价要求检查实验室随时间变化、个体变化和显著异常；可采用 shift table 与预设变化阈值，但阈值须说明。
3. [ICH E19](https://database.ich.org/sites/default/files/ICH_E19_Guideline_Step4_2022_0826_0.pdf)：安全资料收集范围必须在方案/监查计划/SAP 中预先说明；选择性收集仅适用于安全特征已充分认识且不损害受试者安全的情形。
4. [NCI CTCAE 官方资源](https://dctd.cancer.gov/research/ctep-trials/for-sites/adverse-events)：CTCAE 是版本化 AE 严重程度分级资源；当前网站已发布 v6.0，同时保留 v5.0 等历史版本，因此运行时必须绑定研究指定版本，不能默认使用“网站最新版本”。
5. [FDA DILI 指导原则](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/drug-induced-liver-injury-premarketing-clinical-evaluation)：实验室数据可用于识别严重肝损伤潜在线索，但需要临床与实验室证据组合及替代原因评估；D07 只能产生项目规则约束的待核实线索，不能自动诊断 DILI。
6. [ICH E14 / FDA](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/e14-clinical-evaluation-qtqtc-interval-prolongation-and-proarrhythmic-potential-non-antiarrhythmic-0)：QT/QTc 评估、监测和停药阈值应按药物、适应症和受试者风险个体化并在方案中规定；通用内核不内置一个适用于所有项目的停药阈值。
7. [国家药监局临床试验数据监查委员会指导原则](https://www.nmpa.gov.cn/directory/web/nmpa/images/1602831452803080313.pdf)：安全性监查和受试者保护是核心任务，且需结合研究内外安全信息；本系统 D07 仅做个体级证据整理，不替代 DMC/申办方正式裁决。
8. [CDE 临床试验安全信息管理页面](https://www.cde.org.cn/main/guide/contentpage/545cf855a50574699b46b26bcb165f32)：申办者承担临床试验期间安全风险管理主体责任；SUSAR/DSUR 等正式报告不属于 D07 看板的自动动作。

## 选定模式

- 采用“原始观察 → 单位/范围语境 → 基线/治疗后变化 → 版本化分级 → 临床意义与处置链 → 相邻域 typed handoff”的确定性主链。
- 同时保存 `reference_range_state`、`grade`、`clinical_significance`、`seriousness clue` 和 `monitoring_priority`，五者不可互相覆盖。
- 项目方案/IB/中心实验室手册优先定义项目特异阈值和处置；CTCAE、DILI、QT 等外部规则必须以版本化 `RuleSet` 绑定后才能参与确定性求值。
- D07 负责检查异常本身及复测/处置一致性；D01 负责 AE/MH 记录与漏报判断，D02/D03 负责 CM/IP，D08 负责真正的跨域关系裁决，D10 负责中心/项目聚合。
- 输出面向中文医学监察员，使用“肝酶持续升高且缺少复测记录”“心电变化与方案处置记录不一致”等具体表达，不显示内部对象名或笼统“安全信号”。

## 拒绝的模式

- 把 abnormal flag、超参考范围或高 CTCAE grade 自动变成 AE/SAE。
- 全项目通用硬编码 Hy's law、QTc、实验室停药或复测阈值。
- 用最新 CTCAE 版本覆盖项目指定版本。
- 仅凭 NCS 字符串消除风险，或用中文子串命中把 NCS 误读为 CS。
- 用文件行序代替时间、用单次异常代替趋势、用模型补单位/范围/基线。
- 在 D07 内形成中心/治疗组/项目发生率或正式监管报告。

## 剩余不确定性

不同适应症、药物机制和方案对检查项目、阈值、复测/处置要求差异很大。合同必须冻结通用形状和 fail-closed 语义，而不是冻结具体医学阈值；具体项目规则留给 Study Knowledge Pack 与用户激活规则。
