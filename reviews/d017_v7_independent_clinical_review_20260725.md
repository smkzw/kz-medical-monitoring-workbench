# D017 v7 竞品分诊独立临床科学性复核

- 复核日期：2026-07-25
- 复核性质：只读、独立临床科学性复核
- 冻结快照：`wref_search_35f39994abfb89587948`
- v7 运行：`ct_run_351829d15f3e6c352d83`
- 运行状态：`review_ready`
- v7 分布：50 个 `indirect_reference`，17 个 `excluded`，0 个 `direct_competitor`
- 确认状态：`confirmation_id=""`，未发生医学经理确认
- 网络边界：未联网；未用实时 ClinicalTrials.gov 内容替代冻结快照

## 1. 独立结论

**v7 不能按当前 50/17 分割直接确认。**

1. `NCT05731050`、`NCT06978699`、`NCT07212426` 已合理归入
   `indirect_reference`。三项均为明确 PNH、II 期、药物或生物制品研究；
   在 D017 技术类型、给药途径和靶点/机制缺失时，降级为间接参考而非
   `direct_competitor` 是审慎且合理的。
2. 17 个 `excluded` 中，15 个排除合理，**2 个仍属明确临床误排**：
   - `NCT02591862`：PNH 使用英式拼写 `Haemoglobinuria`，PHASE2，
     Coversin 药物研究，并有公开 Protocol/SAP 元数据。
   - `NCT03439839`：PNH 患者限定为“伴活动性溶血”，PHASE2，
     iptacopan 加标准治疗的药物研究，并有公开 Protocol/SAP 元数据。
3. 50 个 `indirect_reference` 均可从冻结登记确认 PNH 条件及至少一个
   `DRUG`、`BIOLOGICAL` 或 `COMBINATION_PRODUCT` 干预；未发现
   非药物-only或错误适应症项。其临床用途并不等质：
   - 25 个核心 PNH 药物/生物制品候选；
   - 10 个长期/延展参考；
   - 12 个早期、特殊人群或小样本参考；
   - 3 个历史/支持性治疗背景项，需医学经理逐项决定是否有可迁移价值。
4. 将两项误排纠正后，供医学经理审阅的候选篮子为 **52 项候选、15 项
   排除**。其中 3 个历史/支持性治疗项仍不是自动保留结论；若医学经理
   无法指定可迁移章节或设计要素，可将其排除。
5. `acceptance_report.json` 的 `accepted: true` 证明的是身份、哈希、
   完整性、枚举、来源定位和规则一致性，不证明每项临床分类正确。

## 2. 证据与方法

### 2.1 冻结来源

| 文件 | SHA-256 |
|---|---|
| `runs/evidence/d017_competitor_triage_v7_20260725/run_response_final.json` | `d61f1db7bf26bbed57776dce53ba2ef7fce803e2b452fcb4fca3d04b98f7650d` |
| `runs/evidence/d017_competitor_triage_v7_20260725/acceptance_report.json` | `4463121f5e94739a153247a3732ae2087a5ce681224a1edd6604e3bb0140fa8d` |
| `runs/evidence/d017_competitor_triage_v4_20260724/search_snapshot.json` | `cc80e476d8443b6c087a59d7390290b7b7de317b7a5055cb5f954dd801413b61` |
| `reviews/d017_v6_independent_clinical_review.md` | `4d90b4fedb29f89e49711f5172312ee209b797fe1afad97f30661e0d767c49c2` |
| `services/api/app/medical_writing_competitor_triage.py` | `54ba170fd300748baf1a7f8b6cd0d3399eed7174e07baba40993681bc22601d4` |

### 2.2 判定标准

- `excluded`：其他适应症，或研究主轴为移植、预处理、放疗、器械等不能
  支持 D017 药物方案设计的策略。
- `indirect_reference`：同一 PNH 适应症且存在明确药物/生物制品干预，
  可支持人群、终点、安全性、剂量、访视、统计或长期随访中的至少一类参考。
- `direct_competitor`：还需 D017 与候选的技术类型、给药途径、靶点/机制
  等直接可比证据。当前项目三项事实均缺失，不能自动产生直接竞品。
- “存在药物字段”不覆盖研究主轴判断。移植研究中的预处理药、免疫抑制药
  或支持药物不能使移植研究成为 D017 药物方案竞品。
- 公开 Protocol/SAP 在本轮仅核查登记元数据是否存在，不读取正文，不据此
  推断具体章节可迁移性。

## 3. P0/P1/P2 问题

### P0

**未发现已发生的 P0。** 冻结运行仍为 `review_ready`，`confirmation_id`
为空；没有证据显示系统已把 AI 推荐自动写成医学经理最终确认。

若下游将 `accepted: true` 或 `review_ready` 直接解释为已确认并自动投射到
权威语料库，则会升级为 P0，但该后果不在本轮冻结证据中。

### P1

1. **两项明确假阴性：`NCT02591862`、`NCT03439839`。** 两项均是同一
   PNH 适应症的 II 期药物研究，却被写成“适应症不同”并排除。
2. **技术验收通过但临床结论仍错误。** `classification_eligibility` 和
   `reason_consistency` 通过，仅证明输出遵守当前规则且理由与最终枚举一致；
   不能证明当前规则的疾病同义词/限定语判断具有临床正确性。
3. **项目关键产品事实缺失。** `technology_type=""`、
   `administration_routes=[]`、`target_mechanism=""`，因此 0 个直接竞品是
   证据不足的结果，不能将 50 个或纠正后的 52 个候选统称为已确认竞品。

### P2

1. `NCT00004464`、`NCT01642979`、`NCT01760096` 是历史/支持性治疗或
   骨髓衰竭背景研究。机械门槛允许保留，但冻结登记未证明其对 D017 的
   具体可迁移设计价值，且无公开 Protocol/SAP 正文可在本轮核查。
2. `indirect_reference` 同时容纳核心 II 期研究、长期延展、健康人/患者
   早期研究、儿童研究和样本量 1 的研究。若不加用途分层，不能直接驱动
   文献优先级、章节推荐或竞品排序。
3. 多个正确排除项的 v7 理由仅以“候选干预 + 不纳入竞品篮子”收束，
   未突出决定性临床主轴为移植/预处理。分类可接受，但人工复核效率不足。

## 4. 机制性根因

服务端适应症匹配采用精确标准化词集、严格别名对和已证明缩写，明确拒绝
模糊、子集或百分比重叠匹配（`medical_writing_competitor_triage.py` 第
805-827 行）。这修复了 `PNH - Paroxysmal Nocturnal Hemoglobinuria`
别名形式，但仍会把以下临床等价表达判为不匹配：

- 英式拼写：`Haemoglobinuria` vs `Hemoglobinuria`；
- 同病种后附人群限定：`... (PNH) With Signs of Active Hemolysis`。

分类协调又规定模型给出的 `excluded` 永不反向提升（第 1222-1241 行）。
因此，匹配器产生的假阴性会稳定保留，并由服务端重新生成一条内部一致但
临床错误的“适应症不同”理由。

## 5. 67 项逐项判定表

| # | NCT | v7分类 | 独立临床判定 | 冻结登记依据/用途 |
|---:|---|---|---|---|
| 1 | `NCT00004143` | `excluded` | 维持 `excluded` | 研究主轴为造血干细胞移植、预处理、放疗或相关非药物策略；PNH并非D017药物方案可迁移主轴 |
| 2 | `NCT00004464` | `indirect_reference` | 低优先级背景候选，医学经理人工确认 | 高剂量环磷酰胺/非格司亭；再障合并PNH历史治疗；无公开方案文本可核查迁移性 |
| 3 | `NCT00143559` | `excluded` | 维持 `excluded` | 研究主轴为造血干细胞移植、预处理、放疗或相关非药物策略；PNH并非D017药物方案可迁移主轴 |
| 4 | `NCT00145613` | `excluded` | 维持 `excluded` | 研究主轴为造血干细胞移植、预处理、放疗或相关非药物策略；PNH并非D017药物方案可迁移主轴 |
| 5 | `NCT00397813` | `excluded` | 维持 `excluded` | 研究主轴为造血干细胞移植、预处理、放疗或相关非药物策略；PNH并非D017药物方案可迁移主轴 |
| 6 | `NCT00544115` | `excluded` | 维持 `excluded` | 登记条件不支持D017 PNH匹配，且研究主轴为移植/其他血液病 |
| 7 | `NCT00566696` | `excluded` | 维持 `excluded` | 研究主轴为造血干细胞移植、预处理、放疗或相关非药物策略；PNH并非D017药物方案可迁移主轴 |
| 8 | `NCT00587054` | `excluded` | 维持 `excluded` | 研究主轴为造血干细胞移植、预处理、放疗或相关非药物策略；PNH并非D017药物方案可迁移主轴 |
| 9 | `NCT00731328` | `excluded` | 维持 `excluded` | 研究主轴为造血干细胞移植、预处理、放疗或相关非药物策略；PNH并非D017药物方案可迁移主轴 |
| 10 | `NCT00975975` | `excluded` | 维持 `excluded` | 登记条件不支持D017 PNH匹配，且研究主轴为移植/其他血液病 |
| 11 | `NCT01174108` | `excluded` | 维持 `excluded` | 登记条件不支持D017 PNH匹配，且研究主轴为移植/其他血液病 |
| 12 | `NCT01192399` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | PNH核心药物/生物制品研究：Eculizumab；PHASE2，n=29；无公开 Protocol/SAP |
| 13 | `NCT01194804` | `indirect_reference` | 维持 `indirect_reference`，长期/延展参考 | PNH药物长期治疗、延展或继续用药研究：Eculizumab；无公开 Protocol/SAP |
| 14 | `NCT01529827` | `excluded` | 维持 `excluded` | 研究主轴为造血干细胞移植、预处理、放疗或相关非药物策略；PNH并非D017药物方案可迁移主轴 |
| 15 | `NCT01642979` | `indirect_reference` | 低优先级背景候选，医学经理人工确认 | 左旋咪唑+环孢素+糖皮质激素；经典PNH；状态UNKNOWN；无公开方案文本 |
| 16 | `NCT01760096` | `indirect_reference` | 低优先级背景候选，医学经理人工确认 | 左旋咪唑+环孢素+糖皮质激素；亚临床PNH/骨髓衰竭背景；状态UNKNOWN；无公开方案文本 |
| 17 | `NCT02352493` | `indirect_reference` | 维持 `indirect_reference`，早期/特殊参考 | ALN-CC5；PHASE1/2，n=62，含健康受试者和PNH患者；有公开 Protocol/SAP 元数据 |
| 18 | `NCT02534909` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | PNH药物/生物制品研究：LFG316 + LNP023；PHASE2，n=10；有公开 Protocol/SAP 元数据 |
| 19 | `NCT02591862` | `excluded` | **误排，应改为 `indirect_reference` 候选** | PNH（英式拼写 Haemoglobinuria），PHASE2，Coversin；n=1；有公开 Protocol/SAP 元数据 |
| 20 | `NCT02598583` | `indirect_reference` | 维持 `indirect_reference`，早期/特殊参考 | ALXN1210 剂量递增；PHASE1/2，n=13；无公开 Protocol/SAP |
| 21 | `NCT02605993` | `indirect_reference` | 维持 `indirect_reference`，早期/特殊参考 | Ravulizumab 多次递增给药；PHASE2，n=26；有公开 Protocol/SAP 元数据 |
| 22 | `NCT03030183` | `indirect_reference` | 维持 `indirect_reference`，小样本参考 | Zilucoplan；PHASE2，n=3；有公开 Protocol/SAP 元数据 |
| 23 | `NCT03053102` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | Danicopan；PHASE2，n=10；有公开 Protocol/SAP 元数据 |
| 24 | `NCT03078582` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | Zilucoplan；PHASE2，n=26；有公开 Protocol/SAP 元数据 |
| 25 | `NCT03157635` | `indirect_reference` | 维持 `indirect_reference`，早期/特殊参考 | Crovalimab；PHASE1/2，n=59，含健康受试者和PNH患者；无公开 Protocol/SAP |
| 26 | `NCT03181633` | `indirect_reference` | 维持 `indirect_reference`，长期/延展参考 | ACH-0144471 长期治疗；有公开 Protocol/SAP 元数据 |
| 27 | `NCT03225287` | `indirect_reference` | 维持 `indirect_reference`，长期/延展参考 | Zilucoplan 继续用药/延展；有公开 Protocol/SAP 元数据 |
| 28 | `NCT03333486` | `excluded` | 维持 `excluded` | 研究主轴为造血干细胞移植、预处理、放疗或相关非药物策略；PNH并非D017药物方案可迁移主轴 |
| 29 | `NCT03427060` | `indirect_reference` | 维持 `indirect_reference`，小样本参考 | Coversin；PHASE2，n=1；有公开 Protocol/SAP 元数据 |
| 30 | `NCT03439839` | `excluded` | **误排，应改为 `indirect_reference` 候选** | PNH伴活动性溶血是同一适应症人群限定；PHASE2，iptacopan + SoC，n=16；有公开 Protocol/SAP 元数据 |
| 31 | `NCT03472885` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | Danicopan + Eculizumab；PHASE2，n=12；有公开 Protocol/SAP 元数据 |
| 32 | `NCT03520647` | `excluded` | 维持 `excluded` | 研究主轴为造血干细胞移植、预处理、放疗或相关非药物策略；PNH并非D017药物方案可迁移主轴 |
| 33 | `NCT03593200` | `indirect_reference` | 维持 `indirect_reference`，小样本参考 | Pegcetacoplan；PHASE2a，n=4；有公开 Protocol/SAP 元数据 |
| 34 | `NCT03896152` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | LNP023；PHASE2，n=13；有公开 Protocol/SAP 元数据 |
| 35 | `NCT03946748` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | REGN3918；PHASE2，n=24；有公开 Protocol/SAP 元数据 |
| 36 | `NCT04170023` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | ALXN2050；PHASE2，n=29；有公开 Protocol/SAP 元数据 |
| 37 | `NCT04330534` | `indirect_reference` | 维持 `indirect_reference`，早期/特殊参考 | BCX9930；PHASE1/2，含健康受试者和PNH患者；无公开 Protocol/SAP |
| 38 | `NCT04702568` | `indirect_reference` | 维持 `indirect_reference`，长期/延展参考 | BCX9930 长期治疗/继续用药；有公开 Protocol/SAP 元数据 |
| 39 | `NCT04811716` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | Pozelimab + Cemdisiran；PHASE2，n=24；有公开 Protocol/SAP 元数据 |
| 40 | `NCT04888507` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | Pozelimab + Cemdisiran；PHASE2，n=6；有公开 Protocol/SAP 元数据 |
| 41 | `NCT04901936` | `indirect_reference` | 维持 `indirect_reference`，儿童参考 | Pegcetacoplan；PHASE2，n=12，12-17岁；无公开 Protocol/SAP |
| 42 | `NCT04965597` | `excluded` | 维持 `excluded` | 研究主轴为移植预处理和骨髓/外周血干细胞移植；PNH只是骨髓衰竭条件之一 |
| 43 | `NCT05116774` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | BCX9930，对C5抑制剂反应不足PNH；PHASE2，n=12；有公开 Protocol/SAP 元数据 |
| 44 | `NCT05116787` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | BCX9930 单药；PHASE2，n=12；有公开 Protocol/SAP 元数据 |
| 45 | `NCT05476887` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | KP104 剂量选择/概念验证；PHASE2，n=35；无公开 Protocol/SAP |
| 46 | `NCT05646524` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | NM8074；PHASE2，n=12；无公开 Protocol/SAP |
| 47 | `NCT05646563` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | NM8074，Soliris反应不足PNH；PHASE2，n=12；无公开 Protocol/SAP |
| 48 | `NCT05731050` | `indirect_reference` | **维持，v7 修正合理** | `PNH - Paroxysmal Nocturnal Hemoglobinuria`；NM8074；PHASE2，n=6 |
| 49 | `NCT05741346` | `indirect_reference` | 维持 `indirect_reference`，长期/延展参考 | BCX9930 继续用药和长期安全性；有公开 Protocol/SAP 元数据 |
| 50 | `NCT05876312` | `indirect_reference` | 维持 `indirect_reference`，早期/特殊参考 | ADX-038；PHASE1/2a，n=50，含健康受试者和PNH患者；无公开 Protocol/SAP |
| 51 | `NCT05972967` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | OMS906，Ravulizumab反应不足PNH；PHASE2，n=12；无公开 Protocol/SAP |
| 52 | `NCT06050226` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | MY008211A；PHASE2，n=34；无公开 Protocol/SAP |
| 53 | `NCT06051357` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | HRS-5965；PHASE2，n=26；无公开 Protocol/SAP |
| 54 | `NCT06134414` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | MY008211A；PHASE2，n=40；无公开 Protocol/SAP |
| 55 | `NCT06238544` | `indirect_reference` | 维持 `indirect_reference`，长期/延展参考 | HRS-5965 长期治疗；无公开 Protocol/SAP |
| 56 | `NCT06298955` | `indirect_reference` | 维持 `indirect_reference`，长期/延展参考 | OMS906 长期重复给药；无公开 Protocol/SAP |
| 57 | `NCT06412497` | `excluded` | 维持 `excluded` | 研究主轴为减低强度预处理、异基因造血细胞移植和移植后环磷酰胺 |
| 58 | `NCT06561841` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | HSK39297；PHASE2，n=47；无公开 Protocol/SAP |
| 59 | `NCT06745622` | `indirect_reference` | 维持 `indirect_reference`，长期/延展参考 | HSK39297 长期治疗；无公开 Protocol/SAP |
| 60 | `NCT06764303` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | NTQ5082；PHASE2，n=24；无公开 Protocol/SAP |
| 61 | `NCT06933914` | `indirect_reference` | 维持 `indirect_reference`，长期/延展参考 | MY008211A 长期治疗/继续用药；无公开 Protocol/SAP |
| 62 | `NCT06978699` | `indirect_reference` | **维持，v7 修正合理** | `PNH - Paroxysmal Nocturnal Hemoglobinuria`；XH-S003；PHASE2，n=24 |
| 63 | `NCT07187401` | `indirect_reference` | 维持 `indirect_reference`，早期/特殊参考 | ALN-CFB 首次人体；PHASE1/2，持续贫血PNH，n=24；无公开 Protocol/SAP |
| 64 | `NCT07212426` | `indirect_reference` | **维持，v7 修正合理** | `PNH - Paroxysmal Nocturnal Hemoglobinuria`；LP-005；PHASE2，n=30 |
| 65 | `NCT07266155` | `indirect_reference` | 维持 `indirect_reference`，长期/延展参考 | LP-005 延展研究；无公开 Protocol/SAP |
| 66 | `NCT07387302` | `indirect_reference` | 维持 `indirect_reference`，核心候选 | SLN12140；PHASE2，n=10；无公开 Protocol/SAP |
| 67 | `NCT07470762` | `indirect_reference` | 维持 `indirect_reference`，早期/特殊参考 | HS-10542；PHASE1b/2，n=50；无公开 Protocol/SAP |

## 6. 候选篮子与系统确认的边界

### 6.1 本报告给出的是什么

本报告给出的是**供医学经理确认的候选篮子**：

- 明确排除：15 项；
- 明确应作为候选：49 项（含两项 v7 误排纠正后的核心/特殊参考）；
- 低优先级、待医学经理用途确认：3 项；
- 最大候选篮子：52 项；
- 0 项可在当前证据下自动标为 `direct_competitor`。

### 6.2 本报告没有做什么

本报告没有执行系统确认，也没有修改运行、快照、代码、数据库或语料库。
服务端代码明确要求调用独立的 `confirm_basket` 用户决策动作；“医学经理的
确认即医学决定”（第 2689-2707 行）。最终分类可由医学经理相对 AI 建议
调整，并作为权威决定写入，同时保留不可变 AI 运行用于比较（第
3019-3021、3058-3067 行）。

因此：

- `review_ready` = 全部候选已产生可审阅结果；
- `accepted: true` = 冻结产物通过技术验收；
- 二者均不等于医学经理已确认；
- 只有明确的确认请求及完整最终分类才构成系统权威确认。

## 7. 建议的医学经理确认动作

1. 将 `NCT02591862`、`NCT03439839` 从 `excluded` 调整为
   `indirect_reference` 候选。
2. 维持其余 15 个 `excluded`。
3. 对 `NCT00004464`、`NCT01642979`、`NCT01760096` 逐项指定用途：
   疾病历史、既往治疗背景、特殊骨髓衰竭人群，或排除。不能仅因含 `DRUG`
   字段自动进入核心语料。
4. 在技术类型、给药途径和靶点/机制未补齐前，不确认任何
   `direct_competitor`。
5. 对保留项在下游至少保留“核心方案设计、早期/特殊、小样本、长期/延展、
   历史/背景”用途层，不用单一 `indirect_reference` 直接决定优先级。

## 8. 残余边界

- 本轮只使用冻结登记摘要、结构化条件、干预、设计、状态和公开文档元数据；
  未核查 ClinicalTrials.gov 当前页面或更新状态。
- 未下载或读取公开 Protocol/SAP 正文；“有公开 Protocol/SAP”只表示快照
  存在文档元数据，不能证明全文适用于 D017 写作。
- 未获得 D017 技术类型、给药途径和靶点/机制，因此不能评价直接竞争性、
  同靶点相似性或给药方案可比性。
- 冻结快照未提供完整结果数据、终点定义、入排标准和安全性细节，本报告不
  评价疗效优劣，也不把开发代号推断为未登记的机制或药物类别。
- 对 3 个历史/支持性治疗项的最终保留与否属于医学经理用途判断，不应由
  当前服务器最低门槛替代。

## 9. 最终判定

**结论：v7 是比 v6 更好的待审阅候选集，但仍未达到按 50/17 原样确认的
临床条件。**

三项指定 NCT 的修正有效；同时仍存在两项明确同适应症药物研究误排。
完成两项纠正后，可形成 52/15 的医学经理候选篮子，再由医学经理决定 3 个
历史/支持性治疗项的最终用途。当前无任何系统自动确认，亦不应把技术验收
通过解释为临床篮子已确认。
