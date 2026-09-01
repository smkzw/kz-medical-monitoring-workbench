# 同会话返修：直接竞品降级不能污染间接参照篮子

继续使用上一轮同一会话。再次核对并遵守
`/Users/smkzw/.hermes/SOUL.md`。

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v4_source_truth_02.md`

不得自行写上述 runner 报告；在 final response 中返回完整报告，由 runner 持久化。

## Hard boundaries

- 仅允许修改：
  - `services/api/app/medical_writing_competitor_triage.py`
  - `tests/test_medical_writing_competitor_triage_v4_source_truth.py`
- 不修改其他文件，不替代产品独立 AI，不启动真实 run，不做安全审计。

## Read these files only

- `/Users/smkzw/.hermes/SOUL.md`
- 本返修提示
- 上一轮 runner 报告
- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_medical_writing_competitor_triage_v4_source_truth.py`
- `tests/test_medical_writing_competitor_triage.py`

## Codex 已复现的失败

上一轮实现中：

1. `_enforce_direct_competitor_downgrade` 只看项目关键事实是否未知，完全不看候选适应症和
   干预类型。若模型把不同适应症、器械、手术、移植或其他非药物研究误标
   `direct_competitor`，服务端会错误降为 `indirect_reference`，污染保留篮子。
2. `_sanitize_reason` 只要保护维度 unknown，就无条件追加
   “仅作为同适应症药物研究参考”，即使前文已经判断适应症不同或候选不是药物研究。
3. docstring 声称只对同适应症药物研究降级，但代码未实现该条件。

## 必须修正

1. 直接竞品在项目 modality/route/target 未补齐时：
   - 候选适应症与项目明确一致，且至少存在明确药理学干预类型（例如
     `DRUG`、`BIOLOGICAL` 或可明确视为药品的组合产品）时，才降为
     `indirect_reference`；
   - 候选适应症明确不同，降为 `excluded`；
   - 仅为 `DEVICE`、`PROCEDURE`、`RADIATION`、移植/手术等非药理学干预，降为
     `excluded`；
   - 条件或干预类型缺失，失败关闭为 `excluded` 或保持原 `excluded`，不得凭空留在
     间接参照篮子。
2. `_sanitize_reason` 必须依据最终分类和显式输入生成结论：
   - 只有真正满足同适应症药物研究条件且最终为 `indirect_reference` 时，才写
     “可作为同适应症药物研究参考”；
   - 不同适应症或非药物研究应明确写不纳入；
   - 不得出现前后矛盾。
3. 可调整函数签名并在 `_validate_chunk_response` 内传入 candidate/project facts/final
   classification；旧两参数 validator 仍兼容。

## 新增反例

- 不同适应症 DRUG 被模型误标 direct -> excluded，理由不含“同适应症参考”。
- 同适应症 DEVICE/PROCEDURE/移植被模型误标 direct -> excluded。
- 同适应症 DRUG、项目关键直接竞争事实未知 -> indirect_reference。
- 条件缺失或干预缺失 -> 不得保留为 indirect_reference。
- 原本 excluded 不提升。
- 所有上一轮 v4 测试和既有 triage 测试零失败。

## 验收

```bash
pytest -q \
  tests/test_medical_writing_competitor_triage_v4_source_truth.py \
  tests/test_medical_writing_competitor_triage.py
python3 -m py_compile services/api/app/medical_writing_competitor_triage.py
```

完成标记：
`HERMES_COMPETITOR_TRIAGE_V4_SOURCE_TRUTH_02_COMPLETE`

