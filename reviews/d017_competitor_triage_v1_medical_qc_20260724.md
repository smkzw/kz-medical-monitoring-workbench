# CMS-D017 PNH 竞品分诊 v1 医学质量复核

## 范围

- 项目：`proj_user_0c2edf8d099d`
- ClinicalTrials.gov快照：`wref_search_42d02b8b17a6f5bfafe6`
- 检索：PNH、PHASE2、INTERVENTIONAL
- 候选：67项；公开Protocol/SAP：48份
- 产品AI：`deepseek/deepseek-v4-pro`
- 分诊run：`ct_run_63882297ef5cac61eb09`
- 提示版本：`competitor_triage_deepseek_v4_v1`
- 结果：5/5分块成功；direct 13、indirect 38、excluded 16

## 可接受表现

- 同适应症、口服、小分子、II期、随机开放标签剂量探索的研究多数被识别为直接竞品。
- 多数非PNH恶性血液病/移植研究被排除。
- 每个NCT均有分类、置信度、理由和文档适用性，集合完整且无漏项。

## 阻断性医学问题

1. **未知事实被推断。**
   - 对HRS-5965、LNP023等使用“likely oral”“likely same pathway”等理由。
   - 当前项目靶点/机制未确认；候选输入也未提供完整干预类型、途径和机制，不能据代码名推断。

2. **非药物治疗边界不一致。**
   - NCT00004143、NCT00731328等造血干细胞移植被标为间接参照。
   - 同类移植研究又被排除。对于当前口服胶囊药物方案，移植、手术、器械等不同治疗模态默认不应进入方案写作语料篮子。

3. **同适应症药物研究的排除逻辑不一致。**
   - 部分注射用抗体/联合方案仅因途径或设计不同被排除。
   - 另一些同样途径/设计差异的研究被列为间接参照。途径、盲法或人群不同通常降低直接竞争性，但仍可能提供终点、安全性、访视和入排参考。

4. **延展研究被高估为直接竞品。**
   - 长期延展研究更适合作为长期安全性/持久性间接证据，不应与核心剂量探索研究使用同一“直接竞品”语义。

5. **保留篮子过宽。**
   - 51/67被推荐保留，包含历史化疗、免疫抑制和非药物治疗；若直接进入下载、解析、翻译，会显著增加无效处理并稀释章节候选。

## 已实施修订

- 提示升级为`competitor_triage_deepseek_v4_v2_medical_relevance`。
- 项目事实新增：
  - 内在研究目的；
  - 靶点/机制与竞品靶点范围；
  - 产品技术类型、给药途径、剂型和暴露范围；
  - 研究人群、干预、对照和主要终点。
- 明确分类规则：
  - 不得从开发代码推断机制、途径、剂型或药物类别；
  - 非药物治疗模态默认排除，除非当前项目同属该模态；
  - 同适应症药物但途径/设计不同通常为间接参照；
  - 长期延展研究通常为间接参照；
  - 临床相关性与是否存在公开Protocol/SAP分开判断；
  - 理由、匹配维度和证据缺口使用监管中文。

## 下一轮验收

在加载v2源码后，使用同一67项不可变快照重跑，并比较：

- 不得出现`likely oral`、`likely same pathway`等无来源推断；
- 造血干细胞移植/手术/器械不进入保留篮子；
- 延展研究从direct降为indirect；
- 同适应症药物研究仅因途径不同不得随意排除；
- direct/indirect/excluded的边界在不同分块中一致；
- 仍保持67/67完整输出、5/5分块成功和中文理由。

若v2仍跨分块不一致，再增加基于当前项目治疗模态和候选显式元数据的确定性后置质量门；不能用人工静态名单替代通用规则。

## 外部字段依据

- ClinicalTrials.gov Study Data Structure:
  https://clinicaltrials.gov/data-api/about-api/study-data-structure
- ClinicalTrials.gov API:
  https://clinicaltrials.gov/data-api/about-api

官方API已验证可按字段返回`InterventionName`、`InterventionType`、
`DesignAllocation`、`DesignInterventionModel`、`DesignMasking`、
`EnrollmentCount`和`BriefSummary`。下一结构切片应将这些显式字段纳入候选快照，
减少仅凭标题分诊。
