# 同会话返修：候选干预类型缺失必须失败关闭

继续使用上一轮同一会话。再次核对并遵守
`/Users/smkzw/.hermes/SOUL.md`。

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v4_source_truth_03.md`

不得自行写上述 runner 报告；在 final response 中返回完整报告，由 runner 持久化。

## Hard boundaries

- 仅允许修改：
  - `services/api/app/medical_writing_competitor_triage.py`
  - `tests/test_medical_writing_competitor_triage_v4_source_truth.py`
- 不修改其他文件，不替代产品独立 AI，不启动真实 run，不做安全审计。

## Codex 已复现的唯一剩余失败

上一轮虽然补充了候选适应症和干预类型判断，但
`_candidate_has_pharmacologic_intervention()` 在完全没有明确
`intervention_type` 时，仅凭 `study_type == "INTERVENTIONAL"` 就返回
`True`。对应测试还把这一错误行为固化为“defaults to
pharmacologic”。

这违反上一轮合同“条件或干预类型缺失必须失败关闭为 excluded”，也会把未说明药物、
生物制品或组合药品类型的器械/行为/其他干预研究错误保留到间接参照篮子。

## 必须修正

1. 只有候选显式含至少一个 `DRUG`、`BIOLOGICAL` 或
   `COMBINATION_PRODUCT` 干预类型时，才可判定为药理学干预。
2. 没有 `interventions`、数组为空、元素不是对象、所有
   `intervention_type` 为空或未知时，均返回 False；不得使用
   `study_type=INTERVENTIONAL` 补推药理学属性。
3. 同适应症但干预类型缺失且模型误标 direct，最终必须为 `excluded`，理由必须说明显式
   干预类型不足，不能写“可作为同适应症药物研究参考”。
4. 修订上一轮固化错误行为的两条测试：
   - 直接函数级缺失干预反例；
   - 完整 validator 缺失干预反例。
5. 保持同适应症显式 DRUG/BIOLOGICAL/COMBINATION_PRODUCT 降为
   `indirect_reference`；不同适应症、DEVICE/PROCEDURE/RADIATION、条件缺失及原
   `excluded` 逻辑不变。

## 验收

```bash
pytest -q \
  tests/test_medical_writing_competitor_triage_v4_source_truth.py \
  tests/test_medical_writing_competitor_triage.py
python3 -m py_compile services/api/app/medical_writing_competitor_triage.py
```

完成标记：
`HERMES_COMPETITOR_TRIAGE_V4_SOURCE_TRUTH_03_COMPLETE`
