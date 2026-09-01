# W3 第02轮：补齐真实W2b证据门、派生冲突和精确回放

继续同一session `20260724_223328_589e30`。不要重开任务。完整复核首轮实现与报告后，
只修复以下Codex拒绝项；不得开始W4。

## Read these files only

执行前完整读取：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `runs/execution/mw_ai_first_candidate_packages_20260724/worker_w3_atomic_composite_adopt_01.md`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill_evidence.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/main.py`
- 首轮W3测试及相关W2b evidence/AI测试

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_w3_atomic_composite_adopt_02.md`

不得自行写runner报告；在final response中返回完整报告，由runner持久化。

## Hard boundaries

- 只允许下述写集；保留所有无关用户修改。
- 不得修改或调用独立产品AI模型、provider或提示词。
- 不得修改竞品分诊、前端、DOCX、任务记录或其他子系统。
- 不得用测试mock替代真实API证据验证调用链。
- Codex保留最终代码、医学语义和生产验收权。

## Codex拒绝依据

首轮虽然报告250项测试通过，但当前源码不满足冻结合同：

1. `main.py`调用`adopt_prefill_composite()`时未注入任何`evidence_verifier`；planner又只在
   `tp in EXACT_FACT_PATHS`时调用可选验证器。恰好`EXACT_FACT_PATHS`全部不在
   `COMPOSITE_ADOPTABLE_PATHS`，所以当前真实API的W2b证据重验路径实际上永远不运行。
2. `test_competitor_option_binding_on_target_path_rejected`反而断言把
   `competitor_option`支持的`framing.indication`直接采用成功；这与“竞品观察不能写成当前
   项目精确事实”相反。报告把该反例误报为已覆盖。
3. 报告称“W2b验证器尚未冻结”不成立。W2b r04已经被Codex接受；现有
   `medical_writing_authoring_prefill_evidence.py`和
   `medical_writing_authoring_prefill_evidence_binding.py`就是冻结来源。W3必须复用或最小
   扩展这些服务器验证器，不能再把接口留成未接线的可选参数。
4. planner删除了真实派生冲突检测，只用注释声称mapper不会冲突；冻结合同明确要求两个根路径
   导出同一最终叶路径且值不同时整次拒绝，并须用patched mapper反例证明。
5. 幂等回放找不到或无法解析原receipt时会构造空
   `AuthoringPrefillCompositeAdoptReceipt(replayed=True)`；这不是“返回原提交回执”，必须
   失败关闭，绝不推测或伪造。
6. 部分采用时，当前循环仍会把同组其他`user_confirmed`候选标为`superseded`；部分路径采用
   不得推翻原整组已确认状态。
7. package门采用已知拒绝集合，而非明确只允许`ready/partial`；改为正向allowlist。
8. 事件只记录`overridden_paths`，没有逐路径`origin=user_override`；需在一条持久化事件中
   保存稳定排序的path origin。

## 允许扩展写集

保留首轮写集，另允许最小修改：

- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill_evidence.py`
- `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
- 对应的W2b evidence/AI测试文件

不得修改竞品分诊、前端、DOCX、记录或其他子系统。

## 必须实现

### A. 持久化并重验服务器证据目录

1. 在prefill package生成/AI enrichment时，把该次模型实际使用的服务器
   `AuthoringPrefillEvidenceCatalog`以类型化、hash稳定、向后兼容的形式持久化到package；
   不得只保存模型回显的ID/hash。旧package没有目录时，AI非override路径必须失败关闭，纯用户
   override仍可按合同采用。
2. 每个非override路径都必须调用服务器证据重验，不限于`EXACT_FACT_PATHS`：
   - package持久化catalog的ID/hash与candidate必须完全一致；
   - catalog hash须由服务器重算；
   - 每条binding的catalog entry、target、source_id、locator、quote_sha256、
     support_scope/support_kind、value pointer和原子叶覆盖重新验证；
   - 任一binding缺失、漂移、越界或未覆盖，整次422/409且零写入。
3. 使用package的`search_snapshot_id`从既有writing-reference repository读取不可变snapshot；
   API可在事务前构造只读验证上下文，但service事务内双CAS后必须实际调用验证器。不得依赖请求体
   提供目录、candidate或binding。
4. 对当前项目事实和竞品观察进行来源漂移检查。核心framing事实（至少protocol_id、version、
   title、indication、phase、investigational product、target/mechanism）不得由
   `competitor_option`写回；设计/PICOS可选方案只有在CT.gov映射允许且用户本次明确选择时，
   才能把竞品观察作为“设计选择依据”，不得标成来源精确事实。
5. 加入真实API反例：篡改catalog SHA、entry quote、binding locator、target/value pointer、
   删除原子叶binding、缺失snapshot、旧package无catalog、competitor indication覆盖，均应
   失败且revision/event不变；完整真实绑定候选必须成功。

### B. 修复事务语义

1. 实现叶级派生贡献冲突检测：不同根路径对同一最终叶路径贡献不同值时整次失败；两个根路径向
   `structured_design`不同子键做加法合并仍允许。使用patched mapper分别证明冲突和合法合并。
2. 幂等回放只能返回事件中持久化的完整原receipt并设置`replayed=true`。receipt缺失、损坏或
   与操作不符时失败关闭，不能返回空receipt。
3. 部分采用不得supersede同组既有user-confirmed候选；只有新组合完整采用时才能替代整组确认。
4. package status必须显式`in {"ready","partial"}`。
5. event detail加入稳定排序的`path_origins`，override路径为`user_override`，经服务器验证的
   candidate路径为`ai_candidate_evidence_bound`，真实derived路径为`derived`。
6. 完整含override的user-edited composite保留非override路径的服务器证据引用，并只把override
   路径标成manual；不能用一个manual ref覆盖整个组合的来源。

## 验收

除首轮全部回归外，新增测试必须直接证明上述每一项，特别是：

- endpoint确实构造并注入真实验证器，不是mock可选接口；
- 非exact、但AI生成的每个非override路径也执行目录/binding重验；
- 首轮错误的competitor-option成功测试被删除或改为拒绝；
- patched mapper冲突零写入；
- 缺失receipt回放失败；
- 部分采用保留旧user-confirmed；
- event path origins和混合来源user-edited composite正确。

运行完整相关测试和py_compile，报告真实计数、实际修改文件、证据目录持久化形态、API到事务内
重验调用链、所有失败关闭反例。不得声称W4或生产验收完成。

完成标记：
`HERMES_W3_ATOMIC_COMPOSITE_ADOPT_02_COMPLETE`
