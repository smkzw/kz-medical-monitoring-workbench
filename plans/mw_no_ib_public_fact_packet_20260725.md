# 无IB项目最小产品事实包：受控实施计划

日期：2026-07-25  
状态：已完成方案边界；尚未实现，不得在前端宣称已自动完成

## 目标

用户只提供“研究药物、适应症、研究分期”，且暂时没有IB时，系统自动检索目标药物的公开
来源，生成可逐项采用、修订或拒绝的产品事实候选。用户采用即构成项目层医学确认，不再增加
第二层“待医学批准”。

## 第一性原理边界

1. 适应症宽检索得到的是竞品研究，不能据此把竞品的技术类型、给药途径、靶点或安全性写成
   目标药物事实。
2. 目标药物事实必须来自目标药物名称、别名、代码或明确同义词命中的公开记录；身份不能
   确认时先要求用户确认别名，不能继续自动归并。
3. ClinicalTrials.gov结构化登记可提供干预名称、其他名称、干预类型和干预描述，但不能保证
   机制、剂型、给药途径或关键安全事实完整。
4. PubMed可补充目标药物的论文题录、摘要和可获得全文；论文中的事实仍须保留PMID/DOI及
   原文证据段落。
5. 独立AI只负责来源内结构化提取、冲突归并和追问建议，不负责浏览器检索，也不得把推断
   直接写入已确认项目事实。

## 权威接口

- ClinicalTrials.gov API v2 Search Areas：
  <https://clinicaltrials.gov/data-api/about-api/search-areas>
  - 目标药物检索使用`query.intr`，不复用适应症宽检索篮子。
- ClinicalTrials.gov Study Data Structure：
  <https://clinicaltrials.gov/data-api/about-api/study-data-structure>
  - 读取`InterventionName`、`InterventionOtherName`、`InterventionType`、
    `InterventionDescription`及对应研究、分期和申办方定位。
- NCBI E-utilities：
  <https://www.ncbi.nlm.nih.gov/sites/books/NBK25501/>
  - 使用ESearch获得PMID，再用ESummary/EFetch取得题录、摘要和可用全文定位。

## 产品流程

1. **目标药物身份候选**
   - 输入：研究药物原始名称。
   - 输出：规范名、登记别名、申办方、命中研究数、冲突提示。
   - 用户只在多身份冲突时选择；唯一高置信命中可预选但仍可修改。
2. **公开来源快照**
   - 独立创建目标药物ClinicalTrials.gov快照和PubMed快照。
   - 每个来源记录查询式、接口版本、抓取时间、原始记录ID、内容SHA-256。
3. **独立AI结构化提取**
   - 候选字段：技术类型、给药途径、剂型、暴露范围、靶点/作用机制、既往临床研究、
     已公开剂量方案、PK/PD、安全性关注项、免疫原性/装置依赖。
   - 精确剂量、阈值、间隔、暴露裕度、停止规则必须附直接原文；无直接证据时保持未知。
4. **冲突归并**
   - 同一字段多来源一致：形成一个候选并列出全部来源。
   - 不一致：并列展示差异和版本日期，不自动裁决。
   - 竞品类推：只能作为“AI推断/设计参考”，不能进入目标产品事实包。
5. **用户确认**
   - 采用、修订、拒绝三种动作。
   - 采用后写入`product_profile.evidence_facts`，同步更新
     `minimum_product_fact_packet.supporting_source_ids`和未解决高影响缺口。
6. **下游门**
   - 公开调研始终可启动。
   - 只有相关高影响事实有直接来源或用户明确输入时，才允许生成依赖这些事实的方案条款；
     其余章节局部阻断，不阻断整个项目。

## 前后端实现切片

1. 新增目标药物身份和来源快照合同，不复用适应症竞品快照。
2. 扩展现有`medical_writing_literature.py`的NCBI客户端，增加PubMed ESearch/批量摘要获取；
   保持现有PMID/DOI导入行为不变。
3. 复用ClinicalTrials.gov v2客户端，增加`query.intr`目标药物检索和不可变快照。
4. 新增耐久任务：`public_product_fact_discovery`，阶段为身份检索、登记检索、文献检索、
   AI提取、冲突归并、待用户确认；每阶段写入可见进度。
5. 复用事实对话的proposal/decision合同；来源候选必须为`source_extracted`并带真实
   `source_id`和locator。
6. 前端在最小产品事实包区域展示进度、候选和缺口；移除当前“已经自动汇总”的提前承诺，
   在功能完成前改为“可补充公开来源检索”。

## 代表性验收

- 至少三个不同药物类型：口服小分子、注射单抗、局部/外用制剂。
- 每个项目覆盖：唯一名称、多个别名、无公开记录、同名冲突、来源不一致。
- 断言：
  - 竞品事实不会写入目标药物事实；
  - 采用前项目事实不变化；
  - 采用后来源ID和原文locator完整；
  - 精确临床事实无直接证据时保持未知；
  - 刷新、重启、重试和幂等重放不重复创建来源或确认；
  - 产品独立AI为DeepSeek `deepseek-v4-pro`，Codex/会商模型不参与生产结果。

