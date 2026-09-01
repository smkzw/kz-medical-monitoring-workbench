# W1执行合同：AI-first组合候选与原子采纳请求模型

你是Hermes/aishuo/cms-model的有界执行成员。首先完整读取并遵守
`/Users/smkzw/.hermes/SOUL.md`，并在最终报告中如实说明是否读完。

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_w1_candidate_contract_01.md`

不得自行写上述runner报告；在final response中返回完整报告，由runner持久化。

## Hard boundaries

- 工作目录仅为当前workspace。
- 只允许修改：
  - `packages/contracts/workbench_contracts/models.py`
  - `packages/contracts/workbench_contracts/__init__.py`
  - `tests/test_medical_writing_authoring_prefill_package_contract.py`（可新建）
- 不得修改service、API、前端、数据库、配置、记录或其他测试。
- 不进行工程安全、漏洞、后门或渗透工作。
- 保持旧候选JSON可反序列化；不新增平行事实状态机。
- 本轮只建立合同，不实现服务或HTTP，不宣称原子采纳已完成。

## Read these files only:

- `AGENTS.md`
- `context/plans/medical_writing_ai_first_candidate_packages_20260724.md`
- `context/mw_ai_first_candidate_packages_20260724_context.md`
- `runs/execution/mw_ai_first_candidate_packages_20260724/manager_plan_grok_02.md`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `tests/test_medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_authoring_journey.py`

## 目标合同

在现有`AuthoringPrefillPackage`和`AuthoringPrefillCandidate`上做向后兼容最小扩展：

1. `candidate_scope`：
   `field | module | design_package | table | chapter`，旧数据默认`field`。本轮只消费前三类，
   table/chapter仅为后续稳定枚举，不在本轮实现业务。
2. `target_paths: list[str]`：
   - field旧候选可为空，等价于`[field_path]`；
   - module/design_package必须非空、去重、为合法非空路径；
   - 组合候选`structured_value`必须是以target path为键的对象，键集合与target_paths一致。
3. `recommendation_role`：
   `recommended | alternative | pending_decision`，旧数据默认`recommended`。
4. `clinical_tradeoffs: list[str]`、`evidence_gaps: list[str]`、`ai_run_id: str`，均有向后兼容
   默认。
5. `adoption_mode`：
   `manual_only | batch_allowed`，旧数据默认`manual_only`。它由服务端构造，未来前端据此
   判断批量采用，不再使用静态字段名白名单。`pending_decision`必须强制`manual_only`。
6. 保留原state枚举`ai_proposed | user_confirmed | superseded`；用户选择即确认，不新增
   “待医学批准”状态。
7. 新请求模型`AuthoringPrefillCompositeAdoptRequest`：
   - `expected_revision`
   - `expected_package_revision`
   - `package_field_path`
   - `candidate_id`
   - `path_overrides: dict[str, Any] = {}`
   - `actor`
   - `idempotency_key`
   严格校验key、路径和值；只定义合同，不实现事务。
8. 从包`__init__.py`导出全部新增公开类型。

## 反例测试

- 旧单字段JSON无新增字段时可加载，默认值准确。
- module/design_package target_paths为空拒绝。
- target_paths重复、空字符串拒绝。
- 组合structured_value不是对象、键缺失或多余拒绝。
- pending_decision + batch_allowed拒绝。
- composite request空候选/空actor/空idempotency、override未知路径拒绝。
- 正常field、module、design_package及table/chapter枚举通过。
- 包入口import smoke通过。

## 验收

运行：

```bash
pytest -q tests/test_medical_writing_authoring_prefill_package_contract.py
python3 -m py_compile \
  packages/contracts/workbench_contracts/models.py \
  packages/contracts/workbench_contracts/__init__.py
```

必须零失败。最终报告包含修改、测试、兼容性、不确定性和紧凑loop trace。
完成标记：
`HERMES_W1_CANDIDATE_CONTRACT_01_COMPLETE`
