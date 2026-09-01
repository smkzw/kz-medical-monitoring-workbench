# 同会话返修：value/preview/rationale 必须分别通过监管中文门

继续使用上一轮同一会话。再次核对并遵守
`/Users/smkzw/.hermes/SOUL.md`。

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_prefill_language_evidence_03.md`

不得自行写 runner 报告；在 final response 中返回完整报告，由 runner 持久化。

## Hard boundaries

- 只允许修改：
  - `services/api/app/medical_writing_authoring_prefill_ai.py`
  - `tests/test_medical_writing_authoring_prefill_ai_quality.py`
- 不修改其他文件，不放宽任何上一轮质量门。

## Read these files only

- `/Users/smkzw/.hermes/SOUL.md`
- 本返修提示
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `tests/test_medical_writing_authoring_prefill_ai_quality.py`
- 上一轮 runner 报告

## Codex 已复现的失败

当前 `_passes_language_and_evidence_gate` 先拼接：

```python
combined = f"{value} {preview} {rationale}"
```

再调用 `_detect_whole_sentence_english(combined)`。只要 rationale 为中文，英文 value/preview
就会因为 combined 中存在中文而跳过语言拒绝。例如：

- value=`Phase 2 Study of CMS-D017 in PNH`
- preview 同上
- rationale=`根据项目信息生成的标题候选`

当前可错误通过。这与真实 D017 生产反例完全同型。

## 必须修正

1. 对非 ClinicalTrials.gov condition term 路径，分别检查：
   - `structured_value`（字符串；list/dict 可使用稳定序列化后检查其中用户可见文本）
   - `preview`
   - `rationale`
2. 任一字段是无中文的英文 prose 都失败关闭；中文 rationale 不能替英文 value/preview
   遮挡。
3. CMS-D017、PNH、PK/PD、SAD/MAD、NCT号等必要缩写仍不得误伤。
4. 无依据设计事实门可继续对组合文本执行，但语言门必须逐字段执行。
5. 增加反例：
   - 英文 value + 中文 rationale -> reject
   - 中文 value + 英文 preview -> reject
   - 中文 value/preview + 英文 rationale -> reject
   - 中文句中含必要缩写 -> pass
6. 重跑完整三文件回归并 py_compile，零失败。

完成标记：
`HERMES_PREFILL_LANGUAGE_EVIDENCE_03_COMPLETE`

