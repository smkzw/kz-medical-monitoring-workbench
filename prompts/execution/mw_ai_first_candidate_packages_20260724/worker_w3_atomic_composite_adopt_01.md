# W3：组合候选单事务采纳与逐路径回执

## Read these files only

执行前完整读取并遵守：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `reviews/codex_subagent_w3_composite_adopt_design_20260724.md`
- 已接受的W2b-1证据目录和W2b-2服务端证据回绑实现及报告

Runner-managed output file: `runs/execution/mw_ai_first_candidate_packages_20260724/worker_w3_atomic_composite_adopt_01.md`

不得自行写上述runner报告；在final response中返回完整报告，由runner持久化。

## 角色与目标

你是非视觉复杂执行成员。实现`module/design_package`候选的一次性采纳：医学经理点选一个
population/intervention/outcomes/statistics组合候选后，服务端在单个journey SQLite事务内
解析全部目标路径、用户覆盖值、证据门、派生值和失效项，只提交一次revision，并返回逐路径
回执。不得通过循环调用单字段adopt实现。

## 允许写集

- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/main.py`
- 可新建：
  - `tests/test_medical_writing_authoring_prefill_composite_adopt.py`
  - `tests/test_medical_writing_authoring_prefill_composite_adopt_api.py`
- 仅因权威行为替换时最小修改相关prefill/journey测试。

不得修改W2b证据目录/AI adapter、竞品分诊、repository、前端、DOCX、记录或其他功能。

## Hard boundaries

- 仅允许上述写集；保留所有无关用户修改。
- 不得调用或替代产品独立AI，不得修改产品AI模型身份或提示词。
- 不得通过循环单字段采纳模拟组合事务。
- 不得声明跨SQLite/正文/SoA/装配计划等独立存储已实现原子重建。
- 不得把医学经理本次明确选择继续标记为“待医学批准”。
- Codex保留最终代码、临床语义和生产验收权。

## 必须实现

### A. 结果合同

新增并导出组合采纳结果与回执合同，至少包含：

- `journey`
- `receipt`
- receipt：
  - operation/package/candidate/package field标识
  - journey与package revision before/after
  - `applied_paths`
  - `overridden_paths`
  - `derived_paths`
  - `skipped_paths[{path, reason}]`
  - `invalidated_dependents`
  - `search_plan_rebuilt`
  - `package_marked_stale`
  - `replayed`

所有列表稳定排序。幂等重放返回原提交回执，`replayed=true`，不根据后来状态重新推测。

### B. 纯规划器

在prefill service中新增无I/O规划器。输入服务器持久化candidate、path overrides、当前
framing/PICOS和W2b服务端证据验证结果，输出完整不可变计划。规划阶段完成：

1. candidate必须为`module`或`design_package`；
2. target_paths非空，structured_value键与target_paths完全一致；
3. override keys必须是target_paths子集；
4. `pending_decision`只应用明确override路径，其余保持原状态；
5. recommended/alternative可应用候选值，但所有非override路径须通过W2b服务器证据门；
6. False、0、空字符串、空列表等只要key存在即是有效用户显式决定；
7. 按固定业务路径顺序调用现有mapper并累计payload；
8. 两个根路径派生到同一最终路径且值冲突时整次拒绝；
9. 最终统一构造并验证framing/PICOS；
10. 无任何实际应用路径拒绝，不制造空revision。

### C. 单事务service

新增`adopt_prefill_composite`，只使用一次`BEGIN IMMEDIATE`：

1. 请求hash包含operation discriminator、双revision、package field、candidate、规范化
   overrides和actor；
2. 事务内完成幂等、journey revision CAS、package revision CAS；
3. package只允许`ready`或`partial`，拒绝queued/running/failed/stale；
4. 只从当前持久化package定位候选，请求不得携带候选内容；
5. 调用W2b服务器验证器重新验证catalog ID/hash、binding、target、quote hash和来源漂移；
6. `path_overrides`是医学经理本次确认，不经过AI证据门，但事件记
   `origin=user_override`；
7. 只有applied和真实derived路径更新为confirmed；skipped路径状态完全不变；
8. 只在全部target_paths实际应用且无部分跳过时把候选标为user_confirmed；
9. 含override的完整组合生成或记录user-edited composite；部分应用不能伪装整包已确认；
10. journey/package/StudyDefinition各最多revision +1；搜索计划可在同一journey事务重建；
11. 正文、SoA、ProtocolAssemblyPlan等其他存储只原子标记失效，不能宣称跨库同步完成；
12. 一条事件持久化完整receipt；任一异常整体回滚。

### D. API

新增：

`POST /api/projects/{project_id}/medical-writing/authoring-journey/prefill-package/adopt-composite`

- 409：双revision过期、幂等键冲突、来源/catalog漂移、候选已完整确认；
- 404：journey/package/group/candidate不存在；
- 422：非法scope/路径、额外override、pending无override、证据不足、结构损坏或最终模型
  校验失败。

采用成功后用户选择即已确认，不得返回或引入“待医学批准”状态。

## 必测反例

覆盖只读审阅报告中的49项矩阵，至少显式证明：

1. pending无override 422且零写入；
2. pending部分override只应用这些路径，其余值与字段状态不变；
3. False/0/空字符串/空列表override不会被当作未提供；
4. recommended/alternative非override路径缺失或漂移binding整次失败；
5. competitor_option不得当作current-project exact fact采纳；
6. package状态queued/running/failed/stale均拒绝；
7. 双revision任一过期均零写入；
8. 同幂等键同payload返回相同receipt且只写一次；不同payload冲突；
9. candidate、group、scope、target、override越界均失败关闭；
10. mapper派生冲突整次回滚；
11. 一次成功只增加一次journey/package/study definition revision；
12. 部分应用不把候选标为user_confirmed；
13. 搜索输入变化同事务重建plan并清空旧snapshot绑定；
14. 下游独立存储仅记录失效，API不谎报已同步重建；
15. 单字段adopt和旧JSON回归继续通过。

## 验收

运行新增测试及相关完整回归：

```bash
pytest -q \
  tests/test_medical_writing_authoring_prefill_composite_adopt.py \
  tests/test_medical_writing_authoring_prefill_composite_adopt_api.py \
  tests/test_medical_writing_authoring_prefill.py \
  tests/test_medical_writing_authoring_prefill_package_contract.py \
  tests/test_medical_writing_authoring_prefill_picos_packages.py \
  tests/test_medical_writing_authoring_prefill_evidence_catalog.py \
  tests/test_medical_writing_authoring_prefill_ai.py \
  tests/test_medical_writing_authoring_journey.py
python3 -m py_compile \
  packages/contracts/workbench_contracts/models.py \
  services/api/app/medical_writing_authoring_prefill.py \
  services/api/app/medical_writing_authoring_journey.py \
  services/api/app/main.py
```

报告列出实际修改文件、事务边界、证据门复用点、回执示例、真实测试计数、未同步重建的独立
存储边界和完整loop trace。不得声称W4前端或跨存储原子重建完成。

完成标记：
`HERMES_W3_ATOMIC_COMPOSITE_ADOPT_01_COMPLETE`
