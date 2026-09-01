# 执行成员合同：预填候选的监管中文与证据确定性门

你是Hermes/aishuo/cms-model的有界执行成员。首先完整读取并遵守
`/Users/smkzw/.hermes/SOUL.md`，并在最终报告中如实说明是否读完。

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_prefill_language_evidence_01.md`

不得自行写上述runner报告；在final response中返回完整报告，由runner持久化。

## Hard boundaries

- 工作目录仅为当前workspace。
- 只允许修改：
  - `services/api/app/medical_writing_authoring_prefill_ai.py`
  - `tests/test_medical_writing_authoring_prefill_ai_quality.py`（可新建）
- 既有测试文件只读；不得修改合同模型、journey、repository、main、前端、数据库、配置、
  记录或其他源文件。
- 不进行工程安全、漏洞、后门或渗透工作。
- 不替代工作台产品AI；实现和测试必须继续通过既有独立DeepSeek provider边界。
- 不改变英文ClinicalTrials.gov疾病检索词的职责。
- 不把未确认设计或人群属性写成既定事实。

## Read these files only:

- `AGENTS.md`
- `context/plans/medical_writing_ai_first_candidate_packages_20260724.md`
- `context/mw_ai_first_candidate_packages_20260724_context.md`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_medical_writing_authoring_prefill_ai.py`
- `tests/test_medical_writing_authoring_prefill.py`
- `reviews/d017_competitor_triage_v2_medical_qc_20260724.md`

## 已复现问题

干净项目只输入`CMS-D017`、`阵发性睡眠性血红蛋白尿症（PNH）`、`II期`，采用英文疾病
检索词并完成67项ClinicalTrials.gov检索后，工作台独立AI把下列无直接证据内容置为推荐：

- `framing.document_title`: `Phase 2 Study of CMS-D017 in PNH`
- `framing.population_intent`: `Adult PNH patients meeting criteria`

中国临床试验方案写作中，除ClinicalTrials.gov疾病词、必要的药物代号/英文缩写外，候选
正文和用户可见理由/局限必须使用规范中文。仅凭药物、适应症、分期和注册库摘要，不得把
“成人”、随机、盲法、对照、给药方式、治疗线、严重程度、靶点/机制等写成已知事实。

## 实现目标

1. 更新bulk系统提示：
   - `clinicaltrials_condition_term_en`仍必须为英文；
   - 其他候选的value、preview、rationale必须为适合中国临床试验方案的中文；
   - 不得将未确认设计/人群/治疗事实写入候选；
   - 只有当前项目已确认事实或已登记且可引用的来源才能支持新增事实；
   - 注册库hints只用于提出设计方向或候选，不等于当前研究事实。
2. 在服务端增加失败关闭的候选质量门，不能只依赖提示词：
   - 非检索词候选明显为整句英文时拒绝；
   - 无注册来源的候选如新增成人/儿童、随机、盲法、安慰剂/阳性对照、给药途径、机制、
     精确治疗线等未确认事实时拒绝或不得升为推荐；
   - 不误伤药物代号、NCT号、PK/PD、SAD/MAD、PNH等必要英文缩写。
3. 修正合并/排序规则：
   - AI候选不是因为“来自AI”就无条件替换已有推荐；
   - 无新增可验证证据的纯措辞候选可作为备选，但不能把安全、证据绑定的确定性候选挤出
     推荐位；
   - 真正有已登记来源支持且质量门通过的AI候选仍可成为推荐。
4. 所有用户可见AI局限和默认理由使用中文，删除
   `AI proposed; not yet adopted by medical manager.`之类英文开发语句。
5. 不改变候选最多5个、去重、产品provider身份校验及精确数字事实门。

## 必须新增的反例测试

- 英文condition term保留并可推荐。
- 英文方案标题被拒绝，中文安全标题仍为推荐。
- 无来源`成人PNH患者`、`随机双盲安慰剂对照`、`口服给药`不得成为推荐。
- `CMS-D017`、`PNH`、`PK/PD`、`SAD/MAD`等缩写不触发整句英文误杀。
- 有当前项目已登记source id并满足既有证据ref合同的候选可按规则保留。
- 所有既有`test_medical_writing_authoring_prefill*.py`零失败。

## 验收命令

至少运行：

```bash
pytest -q \
  tests/test_medical_writing_authoring_prefill_ai_quality.py \
  tests/test_medical_writing_authoring_prefill_ai.py \
  tests/test_medical_writing_authoring_prefill.py
```

必须零失败；不得用通过率代替。

最终报告包含：修改文件、关键函数、测试命令与结果、未解决问题、紧凑loop trace。
完成标记必须为：
`HERMES_PREFILL_LANGUAGE_EVIDENCE_01_COMPLETE`
