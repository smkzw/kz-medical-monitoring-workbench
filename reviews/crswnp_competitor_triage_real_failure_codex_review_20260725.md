# CRSwNP 竞品分诊真实失败样本 Codex 评审

## 结论

真实独立 AI 运行 `ct_run_7d9db4c3d935b989b0b4` 不通过医学验收，不得确认、投影
或进入语料库。运行使用产品配置的 `deepseek/deepseek-v4-pro`，但其 12/12 全排除
结论与输入事实矛盾。

## 直接证据

- 项目：`proj_user_4ef4aa3da246`
- 原快照：`wref_search_f695ab9e5565293eb9e7`
- 原运行证据：
  `runs/evidence/crswnp_competitor_triage_real_20260725/run_snapshot_01.json`
- 项目状态：
  `runs/evidence/crswnp_competitor_triage_real_20260725/journey_snapshot_pre_fix.json`
- 旧快照：
  `runs/evidence/crswnp_competitor_triage_real_20260725/search_snapshot.json`
- 2026-07-25 ClinicalTrials.gov 官方 v2 原始记录：
  `runs/evidence/crswnp_competitor_triage_real_20260725/ctgov_live_20260725/`
- 官方记录结构化摘要：
  `runs/evidence/crswnp_competitor_triage_real_20260725/ctgov_live_summary.json`

## 失败点

1. 适应症等价识别错误。
   `Chronic Rhinosinusitis With Nasal Polyps`、
   `Chronic Rhinosinusitis Phenotype With Nasal Polyps (CRSwNP)`及受控的
   `Sinusitis`+`Nasal Polyps`组合被判为与“慢性鼻窦炎伴鼻息肉”不同。
2. 信息缺失被错误转化为排除证据。
   项目技术类型、给药途径或靶点/机制未知时，只能阻断“直接竞品”并降低置信度，
   不能排除同适应症药理性研究的设计参考价值。
3. 旧快照结构化字段不完整。
   旧快照中的干预、摘要、设计和入组数为空；官方实时记录和当前
   `candidate_from_study`均能读取这些字段，因此旧不可变快照不得继续复用。
4. 项目状态存在测试污染。
   CRSwNP PICOS中残留UC的IBDQ量表；`target_mechanism="全部"`不构成可用医学事实。

## 修复后医学验收基线

在项目靶点/技术类型尚未可靠确认的前提下，本批 12 项不能自动标为直接竞品；但均为
同适应症或明确CRSwNP表型的药理性研究，原则上至少应保留为
`indirect_reference`，再由医学经理审阅：

| NCT | 关键事实 | 预期最低分类 |
|---|---|---|
| NCT02898454 | III期，Dupilumab+安慰剂+MFNS，随机平行四盲，Protocol+SAP | indirect_reference |
| NCT02912468 | III期，Dupilumab+安慰剂+MFNS，随机平行双盲，Protocol+SAP | indirect_reference |
| NCT04607005 | III期，Mepolizumab+安慰剂+标准治疗，随机平行三盲，Protocol+SAP | indirect_reference |
| NCT05274750 | III期，Depemokimab+安慰剂，随机平行三盲，Protocol+SAP | indirect_reference |
| NCT05281523 | III期，Depemokimab+安慰剂，随机平行三盲，Protocol+SAP | indirect_reference |
| NCT05878093 | 中国III期，Dupilumab+安慰剂+Budesonide，随机平行四盲，Protocol+SAP | indirect_reference |
| NCT05931744 | II/III期，息肉内Budesonide/Prednisone/Saline，随机平行四盲 | indirect_reference |
| NCT06338995 | III期，Lebrikizumab+安慰剂+INCS，随机平行四盲 | indirect_reference |
| NCT06639295 | III期，611+安慰剂，随机平行四盲 | indirect_reference |
| NCT07107256 | III期，TQC2731+安慰剂，随机平行四盲 | indirect_reference |
| NCT07424144 | III期长期延展，Itepekimab+安慰剂，随机平行三盲 | indirect_reference |
| NCT07520162 | IIIb期，Tezepelumab，开放单臂 | indirect_reference |

其中无公开Protocol/SAP者仍可作为注册状态或设计发现候选，但不得伪装成可直接进入
方案语料库的全文证据；长期延展、开放单臂及不同给药策略应在理由中说明其可迁移范围。

## 必须重新执行的门

1. 修复受控适应症等价和“缺失不等于排除”的服务器判定。
2. 清理CRSwNP项目中的IBDQ污染和无效靶点值，并通过正式影响预览/提交链路留痕。
3. 生成新的检索计划和新的不可变富化快照，确认干预、摘要、设计、入组数及文档元数据
   均存在。
4. 使用产品独立 `deepseek-v4-pro` 对新快照重新分诊。
5. Codex逐条核对分类、理由、证据缺口、文档用途和来源，不自动确认。
6. 医学经理最终选择即为批准，不再额外显示“待医学批准”。

