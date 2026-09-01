# 医学写作三事实竞品检索门禁修复记录

日期：2026-07-25  
结论：限定范围内通过。

## 产品合同

- 从零项目只需“研究药物、适应症、研究分期”即可形成并执行 ClinicalTrials.gov 竞品检索计划。
- `clinicaltrials_condition_term` 为系统建议、用户可修改的检索优化词；留空时使用适应症，不阻断检索。
- 内在研究目的、靶点/机制、总体设计、目标人群等是检索后的医学分诊和 AI/证据预填字段，不是初始检索硬门。
- 完整研究框架、PICOS、语料准入和方案候选生成仍维持原有严格门禁。
- 摘要导入仍先解析和预填，再由用户确认；研究分期及其他选择保留自然语言输入。
- 未为测试或运行态填充任何虚构项目值。

## 根因

1. `MedicalWritingStudyFraming.missing_required_fields()` 将
   `clinicaltrials_condition_term` 纳入完整框架必填，前端又把完整框架就绪
   与竞品检索入口绑定，导致最小三事实无法直接检索。
2. 草稿保存只记录草稿，不基于草稿中的三事实形成检索计划；而搜索执行只读取
   已正式提交的 framing，迫使用户先确认本应由检索结果预填的扩展字段。
3. 前端存在英文检索词门禁和虚构占位值，且研究分期为封闭下拉框。

## 修改文件

- `packages/contracts/workbench_contracts/models.py`
  - 从完整 framing 必填集合移除 `clinicaltrials_condition_term`。
  - 保持 `creation_minimum_missing_fields()` 仅包含研究药物、适应症、研究分期。
- `services/api/app/medical_writing_authoring_journey.py`
  - framing 草稿具备三事实时创建或重建检索计划；缺任一事实时明确不生成。
  - 相同注册库过滤条件时保留既有计划和快照。
  - 搜索执行使用当前有效草稿值，同时不把草稿扩展字段提交为已确认事实。
  - 扩展字段只进入检索后分诊条件，不进入 ClinicalTrials.gov 注册库请求。
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
  - 新增独立 `framingSearchReady`，只校验三事实；完整 `framingReady` 继续用于第一阶段正式提交。
  - 新增“保存三项信息并检索”，先保存三事实草稿，再按返回的计划执行检索。
  - 移除英文检索词硬门和方案号、标题、药物、适应症虚构占位值。
  - 疾病检索词改为可留空的系统建议字段，实际请求回退到适应症。
  - 研究分期在从零和摘要导入路径均改为“推荐列表 + 自由输入”。
  - 内在研究目的保留固定推荐项，同时允许逐行填写其他自然语言目的。
- `tests/test_medical_writing_authoring_journey.py`
  - 覆盖三事实创建计划并形成可执行请求。
  - 覆盖缺少任一三事实时阻断。
  - 覆盖草稿扩展字段不被默认确认、旧正式 framing 不被覆盖。
  - 覆盖快照可进入后续 prefill 证据包。
  - 保留旧 payload 兼容性验证。
- `tests/test_frontend_medical_writing_contract.py`
  - 覆盖三事实按钮、适应症回退、无英文词门禁、无虚构占位值、自由分期和自然语言目的入口。
  - 主会场复核后，将一条仍要求旧“低风险逐字段假批量”和英文检索词硬门的
    过期测试改写为现行原子 composite-adopt 合同；未删除安全边界。

本执行未修改 `services/api/app/main.py`、translation 或 upper-layer 文件；
任务期间观察到另一并行执行者更新了 `main.py`、upper-layer adapter 等文件，
本执行未覆盖、回退或吸收其变更。未启动或重启任何服务，未调用真实模型。

## 行为矩阵

| 输入/状态 | 检索计划 | 可执行检索请求 | 完整方案候选 |
|---|---:|---:|---:|
| 药物 + 适应症 + 分期 | 是 | 是 | 否，仍需完整 framing/PICOS/语料门 |
| 缺药物 | 否 | 否 | 否 |
| 缺适应症 | 否 | 否 | 否 |
| 缺分期 | 否 | 否 | 否 |
| 疾病英文规范词为空 | 使用适应症 | 是 | 不影响后续严格门禁 |
| 扩展字段仅在草稿中 | 可作为医学分诊线索 | 不进入注册库过滤 | 保持未确认 |
| 已有相同过滤条件的计划/快照 | 保留 | 可重放既有合同 | 保持原状态 |

## 验证

1. 后端相邻回归：
   - 命令：`python3 -m pytest -q tests/test_medical_writing_authoring_journey.py tests/test_medical_writing_authoring_prefill.py tests/test_medical_writing_authoring_prefill_ai.py tests/test_medical_writing_synopsis_import.py tests/test_medical_writing_greenfield_runtime.py`
   - 结果：`154 passed`，仅既有 FastAPI `on_event` 弃用警告。
2. 聚焦前端契约：
   - 命令：`python3 -m pytest -q tests/test_frontend_medical_writing_contract.py -k 'authoring_journey_auto_searches or authoring_search_plan or supports_synopsis_import'`
   - 结果：`3 passed, 96 deselected`。
3. Python 语法：
   - `python3 -m py_compile packages/contracts/workbench_contracts/models.py services/api/app/medical_writing_authoring_journey.py`
   - 结果：通过。
4. 前端生产构建：
   - `npm run build`
   - 结果：通过，1888 modules；保留既有大 chunk 警告。
5. 全量前端静态契约：
   - 首轮结果：`98 passed, 1 failed`。
   - 复核结论：失败测试过期，不是业务回归。逐行证据见下节。
   - 测试合同更新后：`99 passed`。
6. W4 原子复合采用专项 QC：
   - `node frontend/tests/medical_writing_composite_adopt_frontend_qc.mjs`
   - 结果：通过；覆盖一次请求、pending 门禁、override/skip、回执分类、
     幂等回放/陈旧包、单字段采用保留和 409 只重载不重提。

## 主会场复核：`LOW_RISK_BATCH_PREFILL_FIELDS`

结论：这是过期测试合同。本次三事实业务修改没有删除或破坏该常量；该常量及
逐字段循环已在 2026-07-24 通过 W4-A 正式替换为更强的原子复合采用合同。

逐行证据：

1. `context/mw-w4a-recommendation-ui_context.md:32-36` 明确要求删除假的顺序
   低风险单字段采用循环，改为一次公开 `prefill-package/adopt-composite` 请求。
2. 同文件 `:50-61` 将“一次POST、稳定幂等、409只重载不自动重提、
   pending逐路径override/skip、保留真实单字段采用”列为验收标准。
3. `runs/execution/mw_w4_recommendation_frontend_20260724/kimi_manager_plan_01.md:17-18`
   将 `adoptLowRiskPrefills` 定义为待删除的“假批量”；`:28-35` 再次把删除
   `LOW_RISK_BATCH_PREFILL_FIELDS` 和循环列为W4-A写集；`:73-81` 要求测试
   反向断言该循环不存在。
4. 当前 `MedicalWritingAuthoringJourneySetup.jsx:829-897` 实际采用
   `adoptPrefillComposite`：一次fetch、双revision、稳定幂等键、path overrides、
   receipt写回、409重载一次且不自动重提。恢复旧常量会重新引入非原子多请求。
5. 当前专项测试
   `frontend/tests/medical_writing_composite_adopt_frontend_qc.mjs:100-135`
   明确要求旧常量、旧函数和逐字段循环不存在，并验证一次请求和409行为。
6. 原失败测试修改前 `tests/test_frontend_medical_writing_contract.py:409-425`
   同时要求旧常量和逐字段循环存在；`:444-445` 还要求英文疾病词硬门。
   后一要求又与本任务批准的适应症自动回退合同冲突。
7. 因此没有把 `LOW_RISK_BATCH_PREFILL_FIELDS` 重新塞回源码。测试改为断言：
   旧路径不存在；composite endpoint仅调用一次；pending逐路径门禁、稳定幂等、
   receipt、409不自动重提、真实单字段采用和适应症回退全部保留。

## 残余真实运行门

- 按任务约束未启动或重启稳定服务，因此没有在真实 HTTP runtime 中验证
  “保存三项信息并检索”按钮到 API 的完整交互。
- 未调用 ClinicalTrials.gov 真实 API；当前已验证的是搜索计划、请求合同、
  快照挂接和 prefill 消费的确定性链路。
- 未进行真实浏览器点击和网络面板验收。合并到稳定运行态后，应在允许统一
  重载时执行一次隔离浏览器用例：空项目只填三事实、检索词留空、保存并检索、
  检查请求 condition 回退、挂接快照、刷新恢复、扩展字段仍为未确认。
- 未调用真实独立 AI；AI 对竞品结果形成扩展字段建议的质量不属于本次门禁修复。
