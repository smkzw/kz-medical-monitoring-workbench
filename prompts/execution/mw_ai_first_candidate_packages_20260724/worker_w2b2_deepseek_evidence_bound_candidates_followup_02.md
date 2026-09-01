# W2b-2第02轮：删除旧旁路并真正逐主张失败关闭

继续同一session：`20260724_214054_feeb90`。

完整读取并遵守：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- W2b-2原合同、当前源码/测试和第01轮runner报告

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_w2b2_deepseek_evidence_bound_candidates_02.md`

不得自行写runner报告；final response返回完整报告。

## Codex源码验收结论

261项测试虽全绿，但以下生产语义违反原合同，当前实现不接受：

1. `enrich_package()`在W2b验证后继续执行`legacy_overrides`，无claim binding的普通AI候选
   仍可成为用户可选项；registered source ID又重新成为裸语义证据旁路。
2. `clinicaltrials_condition_term_en`只是未经绑定的字符串，随后被重新包装成legacy candidate，
   丢失catalog身份和claim binding。
3. `catalog_sha256`缺失时不拒绝。
4. 模型不返回binding时，AI候选仍以`insufficient`保留；模型返回多个binding时只要一条有效，
   其他伪造/跨target/未发送binding不会导致整项拒绝。
5. `_ctgov_compatible_targets()`对未映射field_key返回空tuple，而验证器只有`if compatible`
   才检查，因此未映射CT.gov字段可绑定任意target。
6. package target_paths缺失时回退，或模型提供任意子集/替代集合时仍可通过；必须与服务器
   确定性package target paths完全一致。
7. `value_pointer`没有校验，所谓逐主张实际只有路径级绑定。
8. 请求仍携带独立`snapshot_hints`和`registered_source_ids`，120000字符预算只约束catalog
   entries，不能约束真实证据输入，也诱导模型使用无法回绑的旁路。
9. AI package scope被标成`module`，应使用既有`design_package`语义。

## Hard boundaries

允许写集保持第01轮不变：

- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `services/api/app/main.py`
- `tests/test_medical_writing_authoring_prefill_ai_evidence_binding.py`
- `tests/test_medical_writing_authoring_prefill_api_snapshot_injection.py`
- 最小修改相关AI质量/回归测试

不得改contracts、W2b-1 builder、journey、repository、竞品分诊、前端或DOCX。

## 必须返修

1. 正式catalog-first路径中彻底删除legacy fallback：
   - 不把`registered_source_ids`或`snapshot_hints`送入正式W2b请求；
   - 不运行`_parse_field_suggestions()`或`_build_condition_candidate()`旁路；
   - 旧helper可为兼容测试暂存，但产品`enrich_package()`不得调用。
2. catalog ID和SHA必须同时存在且精确相等；任一缺失/错误拒绝全部AI输出。
3. 每个AI候选至少一条有效binding；零binding直接拒绝并保留确定性pending候选。
4. 任一模型返回binding验证失败，整条候选拒绝，不允许“部分错误但仍可选”。
5. 未映射CT.gov `field_key`直接拒绝；所有`intervention[i].name/type`按同一规则支持
   intervention/comparator路径，不得只支持索引0，也不得开放其他目标。
6. package必须显式返回target_paths，且集合与服务器该package的确定性target paths完全一致；
   不缺省、不允许子集/超集/替代集合。
7. `value_pointer`：
   - 单字段候选允许空字符串表示整个字段；
   - package binding必须提供RFC6901风格、相对于structured_value根对象的pointer；
   - pointer必须真实解析到对应`target_path`下的非空原子值，错误/越界/空值拒绝该binding并
     因第4条拒绝整项；
   - `supported`只在每个非空原子叶均有binding覆盖时成立；部分覆盖为
     `partially_supported`，但所有已返回binding仍必须有效；
   - `competitor_option`不得把enrollment绑定成alpha、power、效应量、估计目标或精确样本量
     假设；保留现有语言/精确事实质量门。
8. condition term必须成为真正的catalog-bound field candidate：
   - 可调整模型输出schema，使其带value和claim bindings，或由服务端把模型英文检索词以
     `normalized_enum`绑定到支持`framing.clinicaltrials_condition_term`的当前项目
     indication entry；
   - 候选必须带真实catalog ID/hash/binding/evidence ref，manual_only；
   - 不得把无绑定字符串包装成候选。
9. package candidate使用`candidate_scope=design_package`。
10. 请求有界统计覆盖整个实际证据输入；去掉旁路后，120000字符catalog预算即为唯一证据
    文本预算。确定性候选结构可另计但需记录总payload字符并设合理硬上限，超限失败关闭。

## 必测反例

- 无catalog_sha或无catalog ID拒绝全部AI输出。
- 零binding候选拒绝。
- 一条有效+一条未知/未发送/跨target binding整条候选拒绝。
- 未映射document/date/status/URL等CT.gov字段不能绑定任意PICOS。
- intervention[2].name可绑定intervention/comparator，但不能绑定statistics。
- package缺target_paths、子集、超集、替代集合均拒绝。
- package pointer不存在、指向空值、指向其他target、非法转义均拒绝。
- 部分叶有有效binding可为partially_supported；每个非空叶均覆盖才supported。
- condition term候选有服务器真实binding；无可支持项目事实entry时不生成AI候选。
- 正式payload无`registered_source_ids`和独立`snapshot_hints`。
- 产品provider仍一次bulk call，正式模型身份仍严格为`deepseek/deepseek-v4-pro`。
- 原261项中与旧旁路冲突的断言应更新为权威新行为，不能放宽生产逻辑迁就旧测试。

完成标记：
`HERMES_W2B2_DEEPSEEK_EVIDENCE_BOUND_CANDIDATES_02_COMPLETE`
