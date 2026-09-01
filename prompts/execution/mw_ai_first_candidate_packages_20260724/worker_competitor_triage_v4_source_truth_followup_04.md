# 同会话返修：直接竞品要求三个关键维度均有明确事实

继续使用上一轮同一会话。再次核对并遵守
`/Users/smkzw/.hermes/SOUL.md`。

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v4_source_truth_04.md`

不得自行写上述 runner 报告；在 final response 中返回完整报告，由 runner 持久化。

## Hard boundaries

- 仅允许修改：
  - `services/api/app/medical_writing_competitor_triage.py`
  - `tests/test_medical_writing_competitor_triage_v4_source_truth.py`
- 不修改其他文件，不替代产品独立AI，不启动真实run，不做安全审计。

## Codex 已复现的新回归

第三轮在修复“缺失干预类型必须失败关闭”时，额外加入：

```python
if tech_known or route_known or target_known:
    return classification, confidence
```

这会在三个直接竞争关键维度只有任意一个已知时，无条件信任模型的
`direct_competitor`。该变化未在返修合同中授权，也违背既有设计：直接竞争至少要求当前
项目的技术类型、给药途径、靶点/机制三个关键维度均有明确事实，才能允许模型进一步比较；
任何一个缺失，都不得保留direct。

## 必须修正

1. 保留第三轮的两个正确修复：
   - 字符串`unknown`按缺失处理；
   - 候选药理学属性只由显式DRUG/BIOLOGICAL/COMBINATION_PRODUCT判断。
2. 删除“任一关键维度已知就信任模型”的逻辑。
3. 只有`tech_known and route_known and target_known`时，才可保留模型的
   `direct_competitor`；否则必须按显式候选事实降级：
   - 同适应症 + 显式药理学干预 -> `indirect_reference`
   - 其他 -> `excluded`
4. 新增至少三个部分已知反例：
   - 仅技术类型已知、途径和机制未知 -> 不得direct；
   - 仅途径已知、技术类型和机制未知 -> 不得direct；
   - 仅机制已知、技术类型和途径未知 -> 不得direct。
   同适应症显式DRUG均应降为indirect；不同适应症/非药理学仍excluded。
5. 三项均明确时保留direct的既有测试继续通过。

## 验收

```bash
pytest -q \
  tests/test_medical_writing_competitor_triage_v4_source_truth.py \
  tests/test_medical_writing_competitor_triage.py
python3 -m py_compile services/api/app/medical_writing_competitor_triage.py
```

完成标记：
`HERMES_COMPETITOR_TRIAGE_V4_SOURCE_TRUTH_04_COMPLETE`
