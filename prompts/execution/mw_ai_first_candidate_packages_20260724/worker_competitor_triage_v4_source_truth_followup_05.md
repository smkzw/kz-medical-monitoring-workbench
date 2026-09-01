# 同会话最终返修：删除候选药理学推断旁路并修正过时旧测试

继续使用上一轮同一会话。重新读取并遵守：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v4_source_truth_05.md`

不得自行写上述 runner 报告；在 final response 中返回完整报告，由 runner 持久化。

## 允许写集

- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_medical_writing_competitor_triage_v4_source_truth.py`
- 仅修正一条已被新失败关闭边界取代的断言：
  `tests/test_medical_writing_competitor_triage.py`

不修改其他文件，不启动真实run，不替代产品独立AI，不做安全审计。

## Codex独立验收结论

第04轮正确删除了：

```python
if tech_known or route_known or target_known:
    return classification, confidence
```

但为迁就旧测试又新增：

- `_DRUG_STUDY_SIGNALS`
- `_project_identifies_as_drug_study`
- `_candidate_is_interventional`
- 在候选缺少显式`intervention_type`时，根据当前项目药名/剂型信号和候选
  `study_type=INTERVENTIONAL`推断候选为药理学研究

这与已明确的来源真值边界冲突。当前项目是药物研究，不能证明候选研究的显式干预类型；
`INTERVENTIONAL`也不能推出`DRUG/BIOLOGICAL/COMBINATION_PRODUCT`。该旁路必须删除。

## 必须修正

1. 完整删除上述三个helper/常量及其在
   `_enforce_direct_competitor_downgrade`中的回退调用。
2. 保留：
   - 只有`tech_known and route_known and target_known`时可保留模型direct；
   - 字面`unknown`按缺失；
   - 候选只有显式`DRUG/BIOLOGICAL/COMBINATION_PRODUCT`才是药理学干预；
   - 三个部分已知反例。
3. 修改旧测试
   `TestTriageRunCreation.test_successful_run_classifies_all_candidates`：
   该fixture的项目三项关键事实缺失，候选也没有显式干预类型，因此模型返回的
   `direct_competitor`必须服务端降为`excluded`；更新
   `recommended_retain/recommended_exclude`及逐项classification的预期，不要给fixture
   偷补药物类型来绕开失败关闭边界。
4. 增加或保留一个明确反例：即使项目名称/剂型显示为药物，只要候选
   `intervention_type`缺失，且三项项目关键事实不全，仍不得把候选降为
   `indirect_reference`，必须`excluded`。
5. 报告必须如实说明旧测试为什么改变，不能声称项目自身信息能证明候选干预类型。

## 验收

```bash
pytest -q \
  tests/test_medical_writing_competitor_triage_v4_source_truth.py \
  tests/test_medical_writing_competitor_triage.py
python3 -m py_compile \
  services/api/app/medical_writing_competitor_triage.py \
  tests/test_medical_writing_competitor_triage_v4_source_truth.py \
  tests/test_medical_writing_competitor_triage.py
```

完成标记：
`HERMES_COMPETITOR_TRIAGE_V4_SOURCE_TRUTH_05_COMPLETE`
