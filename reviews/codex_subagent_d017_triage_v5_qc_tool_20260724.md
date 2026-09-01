# D017 竞品分诊 v5 新 Run 医学 QC 工具审阅报告

## 1. 任务边界

- 工作区：`implementation/workbench`
- 只新增：
  - `scripts/qc/d017_competitor_triage_v5_acceptance.py`
  - `tests/test_d017_competitor_triage_v5_acceptance.py`
  - 本报告
- 未修改旧 v4 证据目录、产品 service、contracts、API、前端或任务记录。
- 未启动或重启后端，未调用产品 AI，未创建、确认或修改任何真实竞品分诊 run。

## 2. 命令行接口

```bash
python3 scripts/qc/d017_competitor_triage_v5_acceptance.py \
  <snapshot.json> \
  <run.json>
```

标准输出始终为 JSON。通过时退出码为 `0`，医学 QC 不通过时为 `1`，输入 JSON 无法解析或结构致命错误时为 `2`。

D017 默认项目适应症为`阵发性睡眠性血红蛋白尿症（PNH）`，英文 ClinicalTrials.gov 条件词默认读取
`snapshot.request.indication`。只有项目三项关键事实已被确认时，才应使用以下可选参数：

```text
--project-indication
--clinicaltrials-condition-term
--project-technology-type
--project-route                  # 可重复
--project-target-mechanism
```

报告主要字段：

- `accepted`：所有失败关闭检查是否通过。
- `checks`：每项不变量的期望值、观察值、通过状态及问题数。
- `issues`：带 `check_id`、错误码、NCT、chunk 和证据的可定位问题。
- `snapshot_source`：快照 ID、ClinicalTrials.gov 查询 URL、API 版本和数据时间。
- `source_inventory`：67 项候选的 study record URL，以及每份公开文件的 locator、类型和下载 URL。
- `residual_boundaries`：确定性工具不能替代人工医学语义审阅的剩余边界。

## 3. 判定不变量

### 3.1 身份、快照和完整性

- run 和每个成功 chunk 的 provider 必须为 `deepseek`。
- response model 必须为 `deepseek-v4-pro`。
- prompt version 必须为 `competitor_triage_deepseek_v4_source_truth`。
- schema version 必须为 `competitor_triage_v1`。
- run 必须为 `review_ready`。
- 使用已接受产品 service 的同一 canonical material 重算 snapshot SHA-256；run 的 snapshot ID/hash 必须一致。
- 必须为 5/5 succeeded chunks。
- snapshot 和 run 必须均为 67/67 唯一 NCT；每个 chunk 的结果必须是其 NCT 集合的完整无重复排列。

### 3.2 适应症和干预类型

- 每个 condition 独立规范化后，只允许与项目中文适应症或英文 ClinicalTrials.gov 条件词做完整 token 集合相等比较。
- 词序和标点差异可匹配；禁止 subset、百分比重叠、编辑距离或其他模糊匹配。
- 缩写仅在项目术语提供括号缩写且候选为同一括号缩写或独立大写缩写时成立。
- `Paroxysmal Nocturnal Dyspnea`、`Severe Asthma`不匹配 PNH。
- `Paroxysmal Hemoglobinuria, Nocturnal`和独立`PNH`匹配。
- 只有显式 `DRUG`、`BIOLOGICAL`、`COMBINATION_PRODUCT`属于允许的药理学干预。
- 混合干预中至少一项允许类型即可；仅 DEVICE/PROCEDURE/BEHAVIORAL 等不成立。

### 3.3 分类、未知维度和理由

- 每一项 `indirect_reference`无条件复验“同适应症 + 至少一项显式允许干预类型”。
- `direct_competitor`还要求项目 technology/route/target 三项均已知，候选三项有显式快照字段、非 unknown 匹配结果和可定位 study record URL。
- D017 默认三项项目事实未知，因此每个结果的 modality/route/target_mechanism 必须为 `unknown`，任何 direct 均失败。
- `indirect_reference`理由必须明确“适应症一致”和“可作为同适应症药物研究参考”，不得出现排除结论。
- `excluded`理由必须明确“不纳入竞品篮子”，且适应症表述必须与确定性匹配结果一致。

### 3.4 文档、来源和不受支持事实

- Protocol/SAP flags 和中文 document role 只由 snapshot `public_documents.document_type`确定性生成。
- `other`类公开文件（例如 ICF）保留为合法来源，但不计为 Protocol/SAP。
- snapshot query URL、每个 study record URL、每份公开文件的 document ID 和下载 URL 均须完整并指向 ClinicalTrials.gov HTTPS 来源。
- 对给药途径、补体/C3/C5/B 因子、抑制剂、抗体、剂量递增等高风险事实执行显式快照词锚检查；无来源时失败。

## 4. 测试与现场验证

执行：

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider \
  tests/test_d017_competitor_triage_v5_acceptance.py \
  tests/test_medical_writing_competitor_triage_v4_source_truth.py
```

结果：`100 passed in 0.36s`。

- 新 v5 QC 工具测试：33 项。
- 已接受产品来源真值回归：67 项。
- 覆盖 PNH/近似呼吸困难反例、词序变体、独立 PNH、Severe Asthma、三种允许药理学类型、混合非药理学干预、direct 三维门、文档角色、provider/model/prompt、snapshot hash、5/5 chunks、67/67 NCT、未知维度、理由、来源 URL/locator 和不受支持事实。

语法检查：

```bash
python3 -m py_compile \
  scripts/qc/d017_competitor_triage_v5_acceptance.py \
  tests/test_d017_competitor_triage_v5_acceptance.py
```

结果：通过。

只读套跑旧 v4 snapshot/run：

- `accepted=false`
- 快照候选、结果和唯一 NCT 均为 67；chunk 为 5。
- 来源 URL/locator 检查通过。
- 正确检出 67 项旧 document role 不一致、48 项间接参照理由不一致、12 项理由中的适应症误判、3 项不满足严格同适应症规则的间接参照及 3 项无显式来源的高风险事实主张。
- 该结果仅用于证明新门能拒绝已知旧 run；旧证据和真实 run 未被写入。

## 5. 剩余边界

1. 该工具可证明结构化字段、失败关闭分类语义、来源定位和一组高风险事实锚定，但不能证明任意自然语言句子的完整医学蕴含；通过后仍需医学经理审阅最终篮子。
2. 工具按要求不联网，仅核对 URL 的 HTTPS、ClinicalTrials.gov 主机、NCT归属和 locator 完整性，不证明链接在验收时仍可下载。
3. 严格规则会排除`PNH - Paroxysmal Nocturnal Hemoglobinuria`这类既非完整 token 集合相等、也非括号/独立缩写的写法；这是当前已批准的失败关闭边界，不应在 QC 工具内自行放宽。
4. 若未来 D017 的 technology/route/target 三项事实被确认，调用方必须显式传参；否则工具继续按三项未知保护。
