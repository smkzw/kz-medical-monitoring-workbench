# W3 原子组合候选采纳只读技术审阅

## 1. 审阅结论

W3 不应通过循环调用现有 `adopt_prefill_candidate()` 实现。正确的最小实现是：

1. 新增一个组合采纳服务方法，在内存中一次性解析候选、覆盖值、证据门和所有派生变更。
2. 使用现有 journey SQLite 的单个 `BEGIN IMMEDIATE` 事务，只提交一次 journey、一次 prefill package、至多一次 StudyDefinition 和一条审计事件。
3. `pending_decision` 候选的未覆盖路径一律跳过，不写值、不改字段状态。
4. 用户显式提供的 `path_overrides` 即医学经理确认的项目事实，提交后直接为 `confirmed`，不得再增加“待医学批准”。
5. AI 候选原值中的 `exact_fact` / `normalized_enum` 必须通过服务端证据验证器；不能仅相信客户端、候选自报的 `evidence_status` 或裸 `claim_bindings`。
6. 只有实际解析并应用的路径可以更新字段状态。部分覆盖时不得把整个组合候选标为 `user_confirmed`。
7. 检索计划属于 journey 同一状态对象，可以在同一事务内重建；ProtocolAssemblyPlan、正文、SoA 等位于其他存储，不能宣称跨库原子重建，只能以新的 StudyDefinition revision/hash 和 `invalidated_dependents` 原子失效，事务后再刷新。

当前合同已经具备组合请求和多路径候选的基本形状，但服务方法、API 路由、逐路径采纳回执和组合反例测试尚不存在，不能声称 W3 已实现。

## 2. 实际读取范围

- `/Users/smkzw/.codex/AGENTS.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_prefill_evidence.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/main.py`
- `services/api/app/medical_writing_protocol_assembly_plan.py`
- `tests/test_medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_authoring_prefill_package_contract.py`
- `tests/test_medical_writing_authoring_prefill_picos_packages.py`
- `tests/test_medical_writing_authoring_prefill_evidence_catalog.py`
- `tests/test_medical_writing_authoring_journey.py`
- `tests/test_medical_writing_protocol_assembly_plan.py`

本审阅未修改源码或测试，未调用外部模型，未进行安全审计。

## 3. 当前实现的关键事实

### 3.1 已有能力

- `AuthoringPrefillCompositeAdoptRequest` 已包含：
  - `expected_revision`
  - `expected_package_revision`
  - `package_field_path`
  - `candidate_id`
  - `path_overrides`
  - `actor`
  - `idempotency_key`
- `AuthoringPrefillCandidate` 的 `module` / `design_package` 候选要求：
  - `target_paths` 非空且去重；
  - `structured_value` 必须是对象；
  - 对象键必须与 `target_paths` 完全一致。
- 单字段采纳已有可复用的事务骨架：
  - 事务前幂等重放；
  - `BEGIN IMMEDIATE` 后再次检查幂等；
  - journey revision CAS；
  - package revision CAS；
  - 单次 `_persist_update()` 同时更新状态和插入事件；
  - commit 前异常可整体回滚。
- `_build_study_definition()` 会在事实哈希变化时将既有研究流程图标记为 `stale`。
- ProtocolAssemblyPlan 使用独立 SQLite，并通过 StudyDefinition id/revision/hash 判断是否过期。

### 3.2 当前缺口

- `main.py` 只导入和暴露单字段 `AuthoringPrefillAdoptRequest`，不存在
  `POST .../prefill-package/adopt-composite`。
- `AuthoringPrefillCompositeAdoptRequest` 的文档明确说明当前只有合同，没有事务实现。
- 单字段方法只阻止 `package.status == "stale"`，会放过 `queued`、`running` 和
  `failed`；组合方法不能复制该宽松条件。
- 单字段方法一次只处理一个根路径，不能保证多路径组合的全有或全无。
- `_merge_prefill_adoption_field_states()` 接收一个扁平 `changed_paths`，并把这些路径全部
  标为 `confirmed`，尚不能表达：
  - 候选值采纳；
  - 用户 override；
  - pending 未解析而跳过；
  - 确定性派生路径；
  - 部分组合采纳。
- 当前 StudyFact evidence 类型只直接表达摘要抽取证据；W2b 的通用 catalog binding 还没有
  统一投影进 StudyDefinition field state。
- 现有 `_idempotent_replay()` 返回当前 journey，而不是原提交时的逐路径回执。对于组合部分
  采纳，API 需要可重复返回明确的 applied/skipped 结果。

## 4. W3 必须保持的业务不变量

1. **服务器权威候选**：只从当前持久化 package 中按
   `package_field_path + candidate_id` 找候选；请求体不得携带或替换候选内容。
2. **双 revision CAS**：journey 和 package revision 必须在同一个写事务内验证。
3. **单次提交**：一次组合采纳最多使 journey revision `+1`、package revision `+1`、
   StudyDefinition revision `+1`，不得按路径累计增加。
4. **pending 优先**：`recommendation_role == "pending_decision"` 时，只有
   `path_overrides` 中明确出现的路径可应用；其余候选结构值即使非空也不得写入。
5. **override 即确认**：按键是否存在决定来源。只要路径出现在 `path_overrides` 中，即视为
   医学经理明确确认，包括 `False`、`0`、空字符串或空列表等显式选择；不得按“是否与候选值
   相同”重新归类为 AI 值。
6. **AI 证据门**：非 override 的 AI `exact_fact` / `normalized_enum` 必须有服务器验证过的
   逐路径 binding；缺失或失配应整次拒绝，不能静默写入。
7. **逐路径状态**：只有 `applied_paths` 及其确定性派生路径可变为 `confirmed`；任何
   `skipped_paths` 保持原状态。
8. **部分不等于整包确认**：只要有一个 target path 未应用，原组合候选不得标为
   `user_confirmed`。
9. **不增加二次批准**：成功应用的用户决定直接进入 `confirmed`，不存在新的医学审批门。
10. **派生与来源一致**：所有 invalidation、search plan、StudyDefinition、package
    fingerprint 和事件回执都必须由同一份最终内存状态计算。

## 5. 推荐的最小服务/API写集

### 5.1 合同层

建议新增一个很小的结果合同，而不是只返回 journey：

`AuthoringPrefillCompositeAdoptResult`

- `journey`
- `receipt`

`receipt` 最少包含：

- `operation_id`
- `package_id`
- `candidate_id`
- `package_field_path`
- `journey_revision_before` / `journey_revision_after`
- `package_revision_before` / `package_revision_after`
- `applied_paths`
- `overridden_paths`
- `derived_paths`
- `skipped_paths: [{path, reason}]`
- `invalidated_dependents`
- `search_plan_rebuilt`
- `package_marked_stale`
- `replayed`

原因：部分 override 后，前端必须直接知道哪些路径已生效，不能从整个 journey 猜测。

### 5.2 纯规划函数

建议在 `medical_writing_authoring_prefill.py` 增加一个无 IO 的规划器：

`plan_composite_adoption(current, package, candidate, path_overrides, evidence_verdicts)`

输出一个不可变 plan：

- 最终 framing/picos payload；
- `applied_candidate_paths`；
- `applied_override_paths`；
- `derived_paths`；
- `skipped_paths`；
- `value_changed_paths`；
- `resolution_changed_paths`；
- 每条路径的来源和证据回执；
- 候选组的新状态；
- 下游影响集合。

规划器必须先完成全部路径模拟和 Pydantic 校验，任何冲突均在持久化前失败。

### 5.3 journey service

新增：

`MedicalWritingAuthoringJourneyService.adopt_prefill_composite(project_id, request, *, evidence_verifier)`

它应复用现有 `_connect()`、`_idempotent_replay()`、`_persist_update()` 和
`_build_study_definition()`，但不能循环调用 `adopt_prefill_candidate()`。

### 5.4 API

新增：

`POST /api/projects/{project_id}/medical-writing/authoring-journey/prefill-package/adopt-composite`

错误映射沿用现有边界：

- 409：revision/package stale、幂等键冲突、候选已完整确认、来源漂移；
- 404：journey/package/group/candidate 不存在；
- 422：额外 override 路径、非法 scope、候选结构损坏、pending 无任何 override、
  证据 binding 不满足、最终 framing/PICOS 校验失败。

无需新增数据库表或迁移。组合回执可以作为 journey event 的 `payload_json` 持久化。

## 6. 单事务验证与提交顺序

### 6.1 请求身份

请求哈希建议包含：

```text
operation = "authoring_prefill_composite_adopt_v1"
expected_revision
expected_package_revision
package_field_path
candidate_id
canonical(path_overrides)
actor
```

`idempotency_key` 本身不进入内容哈希。加入 operation discriminator 可避免项目级唯一幂等键
在不同 endpoint 间发生同内容误重放；加入 actor 可避免另一个操作者复用同一键却继承原审计
身份。

### 6.2 事务外

只允许做可重复、只读、无副作用的准备：

- 解析必要的不可变 evidence catalog；
- 形成逐路径证据验证结果；
- 不调用网络模型；
- 不写任何其他 repository。

若 W2b 最终把服务器验证回执完整固化在 package candidate 中，可省略外部 catalog 读取。

### 6.3 事务内

1. `BEGIN IMMEDIATE`。
2. 按 project + idempotency key 查事件：
   - 同 hash：返回原回执，`replayed=true`，不再检查旧 expected revision；
   - 不同 hash：409。
3. 加载当前 journey 行。
4. 校验 `expected_revision == current.revision`。
5. 校验 package 存在。
6. 校验 `expected_package_revision == package.package_revision`。
7. package 状态只允许 `ready` 或 `partial`；拒绝
   `queued/running/failed/stale`。`partial` 只表示可选择的单个候选仍需独立通过本次门。
8. 校验 package 与当前 journey 的 package/source 指纹关系；不得仅依赖客户端 revision。
9. 在 `package.field_candidates[package_field_path]` 中唯一定位 candidate。
10. 校验：
    - candidate state 不是 `user_confirmed` / `superseded`；
    - scope 仅为 `module` 或 `design_package`；
    - candidate.field_path 等于 package_field_path；
    - target_paths 非空；
    - structured_value 键与 target_paths 完全一致；
    - 每个 target path 属于组合采纳白名单；
    - override keys 是 target_paths 的子集。
11. 按第 7 节生成逐路径 plan。
12. plan 没有任何实际解析路径时返回 422；不得制造 no-op revision。
13. 对所有 candidate-origin 的 exact/normalized 路径执行证据验证。
14. 在内存中按确定顺序应用全部根路径及派生路径，检测冲突，并一次性验证最终
    framing/PICOS。
15. 重建 StudyDefinition；只合并本次 `applied_paths + derived_paths` 的状态。
16. 计算精确的 invalidated dependents。
17. 若影响 `competitor_search_plan`，在内存中调用 `_search_plan()` 重建；任何异常均终止事务。
18. 若影响 `study_schema`，清空 `study_schema_presentation`；StudyDefinition 内的 schema 由
    `_build_study_definition()` 标为 stale。
19. 更新组合候选组和 package revision。
20. 统一计算 package/journey/source/search/corpus fingerprints；若搜索来源发生改变，应将
    package 标为 stale，不能用新 fingerprint 掩盖旧竞品来源。
21. `_persist_update()` 更新 journey 行并插入唯一事件。
22. commit。

## 7. 路径解析规则

| 情形 | 行为 | 字段状态 | 候选整体状态 |
|---|---|---|---|
| pending，无 override | 拒绝 422 | 不变 | 不变 |
| pending，部分 override | 只应用 override，其他跳过 | 仅 override 为 confirmed | 不得 user_confirmed |
| pending，覆盖全部 target paths | 应用全部用户值 | 全部 confirmed | 创建完整的 user-edited composite candidate |
| recommended/alternative，无 override，值已解析且证据门通过 | 应用候选值 | applied 路径 confirmed | 全部 target paths 生效时可 user_confirmed |
| recommended/alternative，部分 override，其余候选值可用 | override 优先，其余采用候选值 | 全部实际生效路径 confirmed | 全路径生效时创建完整 user-edited candidate |
| AI exact/normalized 无 binding | 整次拒绝 422 | 不变 | 不变 |
| 候选值为空且未 override | 跳过并写明原因 | 不变 | 不得整包 confirmed |
| False/0 来自候选且合法 | 可应用 | confirmed | 按完整性决定 |
| 空字符串/空列表来自 override | 视为用户显式决定 | confirmed | 按完整性决定 |

### 7.1 确定性应用顺序

不要依赖合同将 `target_paths` 排序后的字典序表达业务优先级。建议：

1. 先按服务端固定的路径优先级排序；
2. 每次调用 `map_design_adoption_to_study_updates()` 时传入前一步累计后的 payload；
3. 记录 mapper 产生的 secondary/derived paths；
4. 同一最终路径若由两个根路径产生不同值，拒绝整个候选；
5. 最后统一构造和验证 framing/PICOS 模型。

这可避免 comparator、intervention rules、structured design 等互相覆盖时出现“最后一个路径
偶然胜出”。

### 7.2 候选状态

- 完整采用原候选且无 override：原候选改为 `user_confirmed`，同组旧确认项改为
  `superseded`。
- 完整采用但含 override：创建一个以最终完整 target map 为值的 user-edited composite
  candidate；原候选保持来源或标为 `superseded`。
- 部分采用：不得创建伪完整候选，也不得把原候选标为 `user_confirmed`。逐路径事实和事件
  回执才是权威结果。

## 8. 证据门的 W3 边界

W3 不应硬编码 W2b 尚未冻结的 catalog 存储字段，但必须依赖一个服务器端接口：

```text
verify_candidate_path(
    project_id,
    package,
    candidate,
    target_path,
    proposed_value,
) -> VerifiedBindingReceipt
```

验证器至少必须确认：

- 证据要求由服务器路径策略判定，不能由 candidate 自报 `support_kind` 决定；
- candidate 是 AI 候选时，exact_fact / normalized_enum 存在对应 target path 的 binding；
- catalog id/hash 与生成时固化值一致；
- catalog entry 存在；
- entry 的 source id、locator、quote hash 与 binding 一致；
- target path 位于 entry 允许范围；
- `exact_fact` / `normalized_enum` 只能使用适当的 current-project evidence；
- competitor observation 只能支持“候选设计选项”，不能伪装成当前项目事实；
- binding 对 proposed value 的原子 pointer 有效；
- 来源 revision/hash 未漂移。

`path_overrides` 不经过 AI binding 门，因为它是用户当次明确确认的值；但事件必须记录
`origin=user_override`。这不是降低证据要求，而是区分“AI声称的事实”和“医学经理作出的项目
决定”。

当前 W2b 候选字段是向后兼容的可选字段，旧候选默认 `insufficient`。因此旧 AI 候选不能因
Pydantic 可加载就获得 exact/normalized 采纳资格。

## 9. StudyDefinition 与字段状态

现有 `_merge_prefill_adoption_field_states()` 应泛化为接收逐路径 disposition，而不是只接收
`changed_paths`：

```text
path_dispositions[path] = {
  status: applied | derived | skipped,
  origin: candidate | user_override | deterministic_projection,
  evidence_receipts: [...],
}
```

规则：

- `applied` / `derived` -> `confirmed`；
- `skipped` -> 完整保留 previous state；
- unrelated path -> 完整保留 previous state；
- override -> `value_origin=medical_manager_edit`，reviewed/confirmed 均为当前 actor/time；
- candidate 经用户点击采纳后同样是已确认的项目决定，不再设审批状态；
- catalog binding 至少固化在 package candidate 和 event receipt；待 StudyFact evidence 合同
  泛化后，再投影到 field state，不能丢失来源。

需要同时区分：

- `value_changed_paths`：值发生变化；
- `resolution_changed_paths`：值相同但从未决变为确认；
- `derived_paths`：由 mapper 确定性生成；
- `skipped_paths`：完全不改变。

下游失效应使用 `value_changed_paths ∪ resolution_changed_paths ∪ derived_paths`，而不是候选
声明的全部 target paths。

## 10. 共享派生的原子边界

### 10.1 可在同一事务内处理

- journey revision；
- framing/picos 或相应 draft；
- StudyDefinition revision/hash/field states；
- StudyDefinition 内嵌 study schema 的 stale 标志；
- `study_schema_presentation=None`；
- search plan 重建及旧 snapshot 解绑；
- prefill package revision/candidate states/fingerprints/status；
- corpus triage/gate/alignment/discovery projection 的必要失效；
- `invalidated_dependents`；
- journey event 和组合回执。

### 10.2 不能在当前架构中跨库原子重建

- ProtocolAssemblyPlan；
- 已生成正文、章节候选和动态目录；
- SoA；
- 文档 repository 中的流程图/表格；
- DOCX。

这些对象位于独立服务或独立 SQLite。正确策略是：

1. journey 事务原子提交新的 StudyDefinition revision/hash；
2. 同一事件写出精确 invalidation/outbox 信息；
3. ProtocolAssemblyPlan 读取时因 definition binding 不匹配而 stale/fail closed；
4. 事务后由专用 refresh 重新生成并让用户确认适用性；
5. 失败时保留新项目事实和明确的 `invalidated_dependents`，不得回滚已确认的用户事实，也不得
   继续消费旧派生。

若未来要求“用户事实 + AssemblyPlan 重建”跨服务全有或全无，必须先把两者迁到同一事务存储，
或引入事务 outbox/saga；当前最小 W3 不应伪造这种保证。

## 11. 检索计划与 corpus 状态

当应用路径命中 `competitor_search_plan` 或 `corpus_coverage`：

- 重建 search plan；
- 解除旧 `latest_snapshot_id`；
- 重置 corpus triage、PICOS-corpus alignment 和依赖旧 snapshot 的 discovery projection；
- corpus gate 回到未就绪；
- 当前 prefill package 若使用旧 snapshot/catalog，提交选中结果后必须标为 `stale`，要求重新
  检索/生成；不能把 package 的 search fingerprint 改成新值后继续伪装为当前来源。

只改变与检索无关的路径时，可以保留其他候选，但下一次采纳仍应按路径重新验证证据 binding，
不能把一次组合采纳当成对整个 package 的永久批准。

## 12. 幂等、重复和异常语义

### 12.1 同 key 重试

- 同 project、同 key、同 canonical payload：不再写入，返回原 adoption receipt，
  `replayed=true`。
- 即使请求中的 expected revision 已因第一次提交而变旧，也应先命中重放。

### 12.2 同 key 不同内容

- 409；
- 包括 candidate、override 值、expected revision/package revision 或 actor 任一变化。

### 12.3 不同 key 的重复动作

- 已完整确认的同一 candidate：409。
- 部分采纳后再次提交相同 override，若没有任何值或状态变化：409 no-op。
- 部分采纳后以新值覆盖：视为新的用户决定，可提交一次新 revision。

### 12.4 异常

在下列任一点异常，journey 行、package、StudyDefinition、search plan、事件均必须保持提交前
状态：

- 证据验证；
- 第 N 个路径映射；
- 最终 Pydantic 校验；
- search plan 重建；
- StudyDefinition 重建；
- journey UPDATE 后；
- event INSERT 前/后；
- commit 前。

## 13. 推荐测试矩阵

### A. 合同/API

1. composite 路由出现在 OpenAPI，schema 为
   `AuthoringPrefillCompositeAdoptRequest`。
2. package/group/candidate 不存在分别返回 404。
3. field scope、table scope、chapter scope 候选被 422 拒绝。
4. override 包含 target_paths 外路径被 422 拒绝。
5. queued/running/failed/stale package 被拒绝；ready 和有完整候选的 partial 可进入逐候选门。

### B. revision 与幂等

6. stale journey revision -> 409，数据库无变化。
7. stale package revision -> 409，数据库无变化。
8. 同 key 同 body 重放，不增加任何 revision/event。
9. 同 key 不同 override -> 409。
10. 同 key 不同 actor -> 409。
11. 同 key 碰撞其他 endpoint 的 operation discriminator -> 409，不误重放。
12. 不同 key 重复完整候选 -> 409。

### C. pending 与部分 override

13. pending + 无 override -> 422，任何 target path 均不写。
14. pending + 1/4 override -> 只确认一个路径，另三条状态和值不变，候选仍非
    user_confirmed。
15. pending + 覆盖全部路径 -> 一次提交全部确认并创建完整 user-edited candidate。
16. override 的 False/0/空字符串/空列表均按键存在视为显式用户决定。
17. override 值恰好等于 AI 候选值时仍记录为 user_override。

### D. 推荐/备选候选

18. 无 override、全部路径可解析 -> 所有路径一次应用，候选 user_confirmed。
19. 部分 override + 其余候选值 -> override 优先，完整最终值创建 user-edited candidate。
20. 候选含空未决值 -> 空路径不确认，候选不得整包 user_confirmed。
21. 两个根路径产生同一 derived path 且值冲突 -> 422，整次回滚。
22. 结果模型校验失败 -> 422，整次回滚。

### E. 证据门

23. AI exact_fact 无 binding -> 422。
24. AI normalized_enum 无 binding -> 422。
25. catalog id/hash 不匹配 -> 409/422，按是否来源漂移区分。
26. entry 不存在、locator/source/hash 任一失配 -> 422。
27. competitor observation 冒充 current project exact fact -> 422。
28. binding 的 target path 或 value pointer 不匹配 -> 422。
29. user override exact fact 无 AI binding -> 成功，并记录 user_override。
30. 旧候选仅有 `evidence_refs`、没有已验证 W2b receipt -> 不得通过 exact/normalized 门。

### F. 字段状态与候选状态

31. 只更新 applied/derived field states；unrelated 和 skipped 状态逐字节等价保留。
32. StudyDefinition unresolved_paths 只移除实际确认路径。
33. 部分采纳不把整包或整组误标 confirmed。
34. 完整编辑候选保留原 AI 候选来源，并新增用户版本。
35. 确定性 secondary path（如 intervention rules）与根路径同 revision 确认。

### G. 派生与检索

36. 修改 CT.gov condition term：同一事务产生新 search plan，旧 snapshot 清空。
37. `_search_plan()` 注入异常：journey/package/event 均不变化。
38. 命中 corpus 依赖：triage/gate/alignment/projection 同步失效。
39. StudyDefinition 事实变化：既有 study schema 变 stale，presentation 清空。
40. ProtocolAssemblyPlan 在提交后读取为 stale/不可消费，刷新前不能生成旧章节/SoA。
41. 不影响检索的组合采纳不会无故清除 snapshot。

### H. 事务故障

42. 第 2/N 个路径映射异常，验证无部分路径写入。
43. `_persist_update()` journey UPDATE 后注入异常，无 journey/event 残留。
44. event INSERT 后、commit 前注入异常，无 journey/event 残留。
45. 连接重开后状态与提交前完全一致。
46. 正常成功仅一条 event，journey/package/StudyDefinition 各至多增加一次 revision。

### I. API 返回

47. 成功响应回执准确区分 applied/overridden/derived/skipped。
48. 幂等重放返回同一 operation/receipt，`replayed=true`。
49. 部分 override 前端可直接显示未解析路径，不出现“待医学批准”。

## 14. 未决依赖

W3 可以先完成事务与 API 框架，但在正式接线前必须由 W2b 冻结以下语义：

1. 哪个服务器函数判定路径属于 `exact_fact`、`normalized_enum` 或
   `competitor_option`；不能信任模型自报。
2. 服务器已验证 binding receipt 的最小不可变形状。
3. catalog 如何按 id/hash 解析，以及来源漂移的判断。
4. 一次采纳使 journey revision 变化后，未选中候选的旧 catalog binding 如何逐路径继续验证。
5. 通用 catalog binding 如何持久投影到 StudyDefinition field evidence；在此之前至少必须同时
   保留在 package candidate 与不可变 event receipt。

这些依赖不改变 W3 的事务结构。实现时应通过 `evidence_verifier` 接口注入，而不是把 W2b
具体字段散落到 journey service。

## 15. 推荐实施顺序

1. 先补结果/回执合同和组合 target path 白名单。
2. 实现纯 `plan_composite_adoption()` 及全部单元反例。
3. 将 W2b verifier 作为接口接入纯规划器。
4. 实现单事务 service 和故障注入测试。
5. 新增 API 路由、OpenAPI 和 HTTP 错误映射测试。
6. 补 search/corpus/StudyDefinition/AssemblyPlan 跨服务失效测试。
7. 最后接前端；前端一次点击即视为用户确认，不再添加审批动作。

