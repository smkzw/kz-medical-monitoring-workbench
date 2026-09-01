# W2b-2第04轮：空RFC6901段与组内全部候选scope失败关闭

继续同一session：`20260724_214054_feeb90`。

完整读取并遵守：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- 第03轮prompt、报告、当前源码和测试

Read these files only:

- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `tests/test_medical_writing_authoring_prefill_ai_evidence_binding.py`
- `prompts/execution/mw_ai_first_candidate_packages_20260724/worker_w2b2_deepseek_evidence_bound_candidates_followup_03.md`
- `runs/execution/mw_ai_first_candidate_packages_20260724/worker_w2b2_deepseek_evidence_bound_candidates_03.md`

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_w2b2_deepseek_evidence_bound_candidates_04.md`

不得自行写runner报告；final response返回完整报告。

## Codex第03轮验收结果

第03轮相关298项测试和48项subtest全绿，严格多级解析、原子叶覆盖和package无fallback主体
已成立。但Codex直接运行生产函数发现两个遗漏：

```text
/picos.x//0 ACCEPTED ['picos.x', '', '0']
/picos.x/   ACCEPTED ['picos.x', '']
/           ACCEPTED ['']
```

这与函数docstring及第03轮合同“空错误段拒绝”冲突。另
`_extract_package_target_paths()`只检查组内首候选的`candidate_scope`，后续候选只比较
target_paths；后续候选若scope为`field/table/chapter`但target_paths相同，仍可通过。

## Hard boundaries

允许写：

- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `tests/test_medical_writing_authoring_prefill_ai_evidence_binding.py`

不得改main、contracts、builder、deterministic prefill、journey、repository、竞品分诊、
前端、DOCX或记录。

## 必须修复

1. `_parse_rfc6901_pointer()`必须拒绝任一原始空segment，包括`/`、尾随`/`和`//`。
   本系统受控target/JSON结构不使用空字符串键，因此采用该严格子集不会丢失合法业务数据。
2. `_extract_package_target_paths()`必须逐一验证组内每个候选：
   - scope为`module`或`design_package`；
   - target_paths非空；
   - target_paths集合与组内基准一致。
   不得只检查首候选。
3. 新增直接反例：
   - `/`拒绝；
   - `/picos.x/`拒绝；
   - `/picos.x//0`拒绝；
   - 第二个候选target_paths相同但scope=`field`时失败关闭；
   - 合法深层指针、合法`~0/~1`及正常四包继续通过。
4. 复跑第03轮相同完整回归和py_compile，报告真实计数。

完成标记：
`HERMES_W2B2_DEEPSEEK_EVIDENCE_BOUND_CANDIDATES_04_COMPLETE`
