# 同会话返修：I期 Part 可选目录必须结构化完整

继续使用上一轮同一会话。再次核对并遵守
`/Users/smkzw/.hermes/SOUL.md`。

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_w2a_deterministic_picos_packages_02.md`

不得自行写上述 runner 报告；在 final response 中返回完整报告，由 runner 持久化。

## Hard boundaries

- 仅允许修改：
  - `services/api/app/medical_writing_authoring_prefill.py`
  - `tests/test_medical_writing_authoring_prefill_picos_packages.py`
- 不修改合同、AI adapter、journey、main、repository、frontend、数据库或记录。
- 不实现W2b/W3/W4，不替代产品独立AI，不做安全审计。

## Codex 已复现的剩余缺口

上一轮把I期主要Part类型写入了`phase1_part_types`和中文说明，但最终调用：

```python
add("design.phase1_parts", part_candidates[:5])
```

因候选合同最多只允许1个推荐加4个备选，实际结构化候选只保留待决定卡、SAD+MAD、SAD、
MAD和首次患者；食物影响、物质平衡、肝损伤、肾损伤、DDI均被截断。它们只存在于说明文字，
前端无法可靠读取为完整多选目录。

## 必须修正

1. 保持候选数量上限和“不默认SAD+MAD”的行为不变。
2. 在`design.phase1_parts`的首个`pending_decision`候选结构化值内加入稳定、机器可读的
   完整可选目录，例如`available_part_types`，至少逐项包含：
   - SAD
   - MAD
   - 首次患者
   - 食物影响
   - 物质平衡
   - 肝损伤
   - 肾损伤
   - DDI
3. `parts`仍为空，不能把目录误当成已选择Part；`sequence`仍未决定。
4. 增加测试，断言上述8项全部存在于结构化目录、无重复，且`parts == []`、
   `recommendation_role == pending_decision`、`adoption_mode == manual_only`。
5. 既有全部测试零失败。

## 验收

```bash
pytest -q \
  tests/test_medical_writing_authoring_prefill_picos_packages.py \
  tests/test_medical_writing_authoring_prefill.py \
  tests/test_medical_writing_authoring_prefill_package_contract.py \
  tests/test_medical_writing_authoring_prefill_ai_quality.py \
  tests/test_medical_writing_authoring_prefill_ai.py
python3 -m py_compile \
  services/api/app/medical_writing_authoring_prefill.py \
  services/api/app/medical_writing_authoring_prefill_ai.py
```

完成标记：
`HERMES_W2A_DETERMINISTIC_PICOS_PACKAGES_02_COMPLETE`
