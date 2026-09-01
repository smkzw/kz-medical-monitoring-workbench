# W2b-2第03轮：真正RFC6901原子叶绑定与服务器组合路径失败关闭

继续同一session：`20260724_214054_feeb90`。

完整读取并遵守：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- 第02轮prompt、当前源码/测试和runner报告

Read these files only:

- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `services/api/app/main.py`
- `tests/test_medical_writing_authoring_prefill_ai_evidence_binding.py`
- `tests/test_medical_writing_authoring_prefill_api_snapshot_injection.py`
- `tests/test_medical_writing_authoring_prefill_ai.py`
- `prompts/execution/mw_ai_first_candidate_packages_20260724/worker_w2b2_deepseek_evidence_bound_candidates_followup_02.md`
- `runs/execution/mw_ai_first_candidate_packages_20260724/worker_w2b2_deepseek_evidence_bound_candidates_02.md`

Runner-managed output file: `runs/execution/mw_ai_first_candidate_packages_20260724/worker_w2b2_deepseek_evidence_bound_candidates_03.md`

不得自行写runner报告；final response返回完整报告。

## Codex第02轮源码验收结论

第02轮已正确删除正式legacy merge、裸source ID和snapshot hint，并补齐catalog身份、整候选
binding失败关闭、未映射CT.gov字段、任意intervention索引及design_package scope。但仍有
三个生产语义缺口：

1. `_validate_value_pointer()`只把整个pointer去掉首个`/`后当成一个dict key，不支持真正
   RFC6901多级路径。它还允许非空list/dict作为“原子值”。因此
   `picos.inclusion_modules`、终点列表、量表对象等只做到根路径级绑定，没有做到逐原子主张。
2. `_all_atomic_values_bound()`只比较`target_path`集合。一个binding指向列表/对象根就可把
   整个复杂内容标成supported，未核对每个非空原子叶的pointer。
3. `_extract_package_target_paths()`仍在组合包缺失时使用硬编码fallback，并只信任组内第一个
   候选的target_paths；这会掩盖确定性package缺失或组内目标集合漂移。

另有提示词一致性缺口：模块说明与`_BULK_SYSTEM_PROMPT`仍写
`registered_source_ids`、`registry hint`旧语义，虽然payload已删除，会误导真实产品AI。

## Hard boundaries

允许写集保持：

- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `services/api/app/main.py`
- `tests/test_medical_writing_authoring_prefill_ai_evidence_binding.py`
- `tests/test_medical_writing_authoring_prefill_api_snapshot_injection.py`
- 最小修改相关AI质量/回归测试

不得改contracts、W2b-1 builder、deterministic prefill、journey、repository、竞品分诊、
前端或DOCX。

## 必须返修

### A. 真正RFC6901

1. package pointer必须以`/`开头；逐segment解析，严格只接受`~0`和`~1`转义，非法`~`、
   空错误段、越界、`-`、非规范数组索引均拒绝。
2. `structured_value`根仍是以完整target path为键的对象；pointer首segment解码后必须等于
   binding.target_path，后续segment可进入dict/list。
3. 最终解析值必须是非空原子叶：允许非空str、bool、int、float等标量；拒绝None、空字符串、
   list、dict。容器自身不算原子主张。
4. 稳定枚举每个target path下全部非空原子叶的规范RFC6901 pointer：
   - 根标量示例：`/picos.population_summary`
   - 字符串列表：`/picos.inclusion_modules/0`
   - 对象列表：`/picos.assessment_instruments/0/instrument_id`
   - 所有segment必须按RFC6901重新转义。
5. `supported`仅在每个非空原子叶pointer都有至少一条有效binding覆盖时成立；
   缺少任何叶为`partially_supported`。模型返回的每条binding仍必须全部有效，否则整候选拒绝。

### B. 服务器目标路径

1. `_extract_package_target_paths()`不得fallback。四个package group任一缺失、无候选、候选
   非`module/design_package`、空target_paths或组内候选target_paths集合不一致，均失败关闭。
2. `enrich_package()`必须捕获该失败并返回可见partial_source_failure，不调用产品AI、不抛500。
3. 正常W2a确定性四包继续产生相同服务器路径集合。

### C. 提示词/说明一致性

1. 删除生产`_BULK_SYSTEM_PROMPT`与模块说明中`registered_source_ids`、独立registry hint等
   已废弃指令，改成只允许引用`evidence_catalog.sent_entry_ids`，所有binding由服务端回绑。
2. 不要求删除仍被旧测试直接调用的兼容helper，但正式路径和提示词不得再暗示旧旁路。

## 必测

- package pointer缺少首`/`、非法`~2`、list越界、`-`、`01`索引、指向容器均拒绝。
- `/picos.inclusion_modules/0`解析字符串叶成功；对象列表深层pointer成功。
- 一个两元素列表只有第0项binding => `partially_supported`；两项均逐pointer覆盖 =>
  `supported`。
- 任一深层binding无效仍整候选拒绝。
- 缺少任一确定性package group时不调用provider并记录partial failure。
- 同一package组两个候选target_paths不同，失败关闭且不调用provider。
- 正常四包、单次bulk、DeepSeek模型身份、catalog/condition/CT.gov映射及原有全部回归全绿。
- 断言实际system prompt/payload不再出现`registered_source_ids`或
  `relevance_screened_registry_hints`。

完成标记：
`HERMES_W2B2_DEEPSEEK_EVIDENCE_BOUND_CANDIDATES_03_COMPLETE`
