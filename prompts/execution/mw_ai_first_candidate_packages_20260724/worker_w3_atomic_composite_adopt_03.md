# W3 第03轮：删除弱化证据验证器，复用W2b完整门并重建实时目录

继续同一session `20260724_223328_589e30`。不要重开任务。第02轮事务修复大部分可保留，
但Codex拒绝证据重验实现。只修以下源码级缺陷，不得开始W4。

## Read these files only

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- 第01、02轮W3 prompt和runner报告
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill_evidence.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/main.py`
- W3/W2b相关测试

Write exactly one output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_w3_atomic_composite_adopt_03.md`.
该文件由runner持久化；不得自行写。final response返回完整报告。

## Hard boundaries

- 保留第02轮已正确的事务、回放、状态、path origin和API路由修复。
- 允许写集与第02轮相同，另允许修改必要的W3/W2b聚焦测试；不得改前端、竞品分诊、
  DOCX、流程图、任务记录或产品AI提示词/provider/model。
- 不得复制一套弱化证据规则。必须调用
  `medical_writing_authoring_prefill_evidence_binding.py`现有RFC6901、CT.gov映射、
  support kind和逐原子叶覆盖实现，必要时把小函数提升为稳定公共服务器接口。
- Codex保留最终源码和生产验收。

## Codex可复现拒绝依据

1. `ServerEvidenceVerifier.verify_candidate_path()`只比较catalog/entry的字符串，不调用
   W2b `_validate_and_rebind_single_binding()`、`_validate_value_pointer()`或
   `_all_atomic_values_bound()`。它完全忽略`value_pointer`和`proposed_value`。
2. W3测试helper为`candidate_scope=module`的组合候选生成
   `value_pointer=""`。这在W2b正式合同中必须拒绝，但第02轮验证器却接受，证明测试绕开了
   真正证据门。
3. 验证器不检查CT.gov `field_key -> target_path`兼容性。一个
   `competitor_observation`即使来自`lead_sponsor`等明确不可支持的字段，只要
   `support_kind=competitor_option`且目标不是少数framing身份字段就会通过。
4. 验证器只对package内自带catalog重算自洽hash，没有按prompt要求从当前
   `MedicalWritingAuthoringJourney`和`writing_reference_repository.search_snapshot()`
   重建实时服务器catalog，因此删除/替换snapshot、当前项目事实漂移、package catalog与
   当前来源不一致都不会被发现。第02轮报告也明确把此项列为“未验证边界”。
5. `catalog.project_id/journey_revision/snapshot_id`未与当前project、双CAS后的journey及
   search plan绑定。
6. user-edited composite的`evidence_refs`按每个非override路径重复复制整个原候选refs，
   没有按claim binding筛选，可能重复或错误关联；需生成去重且只属于非override路径的来源。

## 必须实现

### A. 实时服务器目录

1. API在调用事务前构造只读、惰性的catalog resolver。它必须：
   - 以当前canonical project读取journey；
   - 若package/catalog绑定snapshot，则只能按该精确snapshot_id从
     `writing_reference_repository.search_snapshot(canonical_id, snapshot_id)`读取；
   - snapshot缺失、项目不符或search plan不再指向该snapshot时失败关闭；
   - 调用`build_evidence_catalog(current_journey, snapshot)`重建目录。
2. service事务内完成journey/package双CAS后才调用verifier；verifier必须比较实时重建
   catalog与package catalog的ID、SHA、project_id、journey_revision、snapshot_id和完整
   entries。因为writing-reference snapshot由数据库触发器保持不可变，允许API在事务前读取，
   但必须用双CAS和精确snapshot identity证明来源未漂移。
3. 纯用户override且没有任何AI路径时不得因旧package无catalog/snapshot而失败；resolver
   只能在首个非override AI路径验证时实际调用。

### B. 直接复用W2b绑定门

1. 对每个非override路径，使用W2b现有服务器重绑逻辑验证全部bindings：
   catalog entry存在且在实际发送目录中；target path；source/locator/quote hash；
   support scope/kind；CT.gov field_key映射；严格RFC6901 pointer；pointer解析到非空原子叶。
2. 对整个candidate一次验证全部非空原子叶都有绑定；不能只验证“每个path有一个binding”。
3. 组合候选的合法pointer必须形如
   `/design.randomization/mode`，不是空字符串；list/dict每个非空原子叶分别绑定。
4. competitor observation只能作为映射允许的设计/PICOS选择依据，不能写当前项目核心身份，
   不能伪装成`exact_fact/normalized_enum`。

### C. 回执来源

为含override的完整user-edited composite保留非override路径的claim bindings和相应来源，
按稳定键去重；manual ref只描述override路径。不得把整个候选evidence refs对每个路径重复。

## 必须新增的行为反例

- 当前第02轮空`value_pointer`组合候选必须422。
- pointer指向容器、越界list、首segment不等于target、漏一个嵌套原子叶均422且零写入。
- CT.gov `lead_sponsor`或document字段支持PICOS设计必须422。
- package catalog虽自洽但与实时重建snapshot/catalog不同必须422。
- snapshot删除/缺失、search plan换snapshot、catalog project/revision漂移必须失败关闭。
- 合法多叶组合候选真实API成功；纯override旧package仍成功。
- user-edited refs无重复，只来自非override binding对应entries，加一条清楚的manual override ref。

运行W3全部相关测试、W2b证据/AI回归和py_compile。报告真实计数、API resolver链、复用的
W2b公共接口、上述每个反例和剩余边界。不得以mock验证器或source-string断言作为API接线证明。

完成标记：
`HERMES_W3_ATOMIC_COMPOSITE_ADOPT_03_COMPLETE`
