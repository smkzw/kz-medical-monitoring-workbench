# 同会话返修：监管中文候选必须真正失败关闭

继续使用上一轮同一会话。首先再次核对并遵守
`/Users/smkzw/.hermes/SOUL.md`。

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_prefill_language_evidence_02.md`

不得自行写上述 runner 报告；在 final response 中返回完整报告，由 runner 持久化。

## Hard boundaries

这是对上一轮实现的 Codex 验收返修。保持原任务的 workspace、模型、独立 AI 边界和写集，
但本轮额外允许仅为修正已证实的过时断言而修改：

- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `tests/test_medical_writing_authoring_prefill_ai_quality.py`
- `tests/test_medical_writing_authoring_prefill_ai.py`

不得修改其他文件。

## Read these files only

- `/Users/smkzw/.hermes/SOUL.md`
- 本返修提示
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `tests/test_medical_writing_authoring_prefill_ai_quality.py`
- `tests/test_medical_writing_authoring_prefill_ai.py`
- `tests/test_medical_writing_authoring_prefill.py`
- 上一轮 runner 报告

## Codex 已复现的失败

上一轮 126 项测试虽全绿，但产品验收不通过：

1. `_merge_ai_candidates` 把整句英文或无依据设计事实放入 `demoted_ai`，最终仍暴露为可手动
   选择的候选。错误建议不能因为“不在首位”就继续提供给医学经理。
2. 用户可见 limitation 仍含英文开发标签 `AI proposed`。
3. `_detect_whole_sentence_english` 允许 `Phase II Study` 等短英文方案正文，违背“除
   ClinicalTrials.gov 检索词和必要缩写外使用监管中文”。
4. `_passes_language_and_evidence_gate` 仅以 `len(evidence_refs)>0` 放行随机、盲法、途径、
   机制等主张，任意不相关来源都可能绕过。
5. `_merge_ai_candidates` docstring 声称失败候选 dropped，代码实际保留，合同与实现矛盾。

## 必须修正

1. 对非 `framing.clinicaltrials_condition_term`：
   - 整句英文候选必须从结果中删除，不能作为备选；
   - 对方案标题、目标人群、总体设计及 PICOS prose 字段，除仅由药物代号/NCT号/通用缩写
     构成的机器字段外，用户可见 value/preview/rationale 应包含中文；
   - `Phase II Study`、`Adult PNH patients`、`randomized trial` 等均不能保留。
2. 无依据新增成人/儿童、随机、盲法、对照、途径、治疗线、严重度、靶点/机制的候选必须
   从结果中删除。
3. 本轮不要用“任意 evidence ref”放行上述主张：
   - 当前 bulk 请求只提供 registered source IDs，未提供可核对的原文片段，无法证明
     source 与主张语义一致；
   - 因此生产 AI 解析得到的上述新主张本轮一律失败关闭；
   - 单元测试可直接验证：即使给一个与主张不对应的普通 evidence ref，也不能放行。
   - 真正的主张-引文语义绑定在后续 W2 扩展 source excerpt 合同时实现。
4. 删除用户可见的 `AI proposed` 英文标签，统一为自然中文，如
   “AI预填候选，需由医学经理核对后采用。”
5. 修订 `tests/test_medical_writing_authoring_prefill_ai.py` 中仅用于保留错误行为的两个
   过时断言：
   - 不再要求英文标题仍出现在候选列表；
   - 不再要求 limitation 含 `AI proposed`。
   不得放宽其他测试。
6. 更新/增加反例：
   - 英文标题和无依据设计事实在 merge 后完全不存在；
   - `Phase II Study` 在正文路径失败；
   - 必要缩写和药物代号不误伤；
   - 不相关 evidence ref 不能放行；
   - 所有用户可见 limitation/rationale 无旧英文开发标签。

## 验收

```bash
pytest -q \
  tests/test_medical_writing_authoring_prefill_ai_quality.py \
  tests/test_medical_writing_authoring_prefill_ai.py \
  tests/test_medical_writing_authoring_prefill.py
python3 -m py_compile services/api/app/medical_writing_authoring_prefill_ai.py
```

必须零失败。报告需明确说明上一轮为何绿测仍不符合产品语义，以及本轮如何修复。完成标记：

`HERMES_PREFILL_LANGUAGE_EVIDENCE_02_COMPLETE`
