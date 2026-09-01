# R4-D05 实施无损暂停记录（2026-08-12）

状态：`PAUSED_AFTER_WORKER_02_ACCEPTANCE`

## 1. 目标与边界

- 目标：按 `FROZEN_R4_D05_CONTRACT_V1_2` 在 R4 合成/离线包实现“访视、评估、样本与时序符合性”纵切。
- 冻结合同：`reviews/medical_monitoring_r4_d05_visit_schedule_slice_contract_v1_20260812.md`，SHA-256 `23172cac905b3b152937976a7ee5d7eb895bac274ced7fc40a49b5f7a205921c`。
- 本次只完成执行序列中的 worker_01 与 worker_02；按用户指令，在当前细分步骤验收后暂停。
- 始终保持：合成/离线；不启动 8911；不运行真实项目或真实 provider；不改产品/R5 UI、R1-R3、医学写作子系统；不做系统安全设计/测试。

## 2. 已完成并由 Codex 接受的工作

### 2.1 worker_01：领域对象、双 cutoff、gate、bundle 与 typed anchor

- 会话：`019ff2db-e533-7000-b2b0-75e83dd07efd`。
- 当前接受文件：
  - `poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule.py`
    - SHA-256 `00ecf4b5c777715417c63d3f84102a90784fa8c0d2877fdaec68696f46e4daff`
  - `poc/medical_monitoring_ai_native_r4/tests/test_visit_schedule_contract.py`
    - SHA-256 `8e4fc830d380a88fa479c56a193bc6f185368cf290eb61a3e72d518285a8942e`
- 关键纠偏：
  1. `ActualEncounterBundle` 增加可验证/自动计算的 `stable_actual_object_key`；输入顺序和 Run 变化不改变稳定身份，错误声明 fail closed。
  2. producer typed anchor 改为全维显式匹配；缺失、错误或冲突的 producer domain/unit/stable event key/content hash/subject/site/phase/episode/interval/precision/timezone/relation type 均 fail closed，不允许同日或 locator 替代。
  3. producer 期望维度省略不再视为通配符；producer context 缺任一规定维度也 fail closed。
- Codex 独立门禁：contract tests `163 passed`；当时完整 R4 `1148 passed`；Ruff、compile/import、保护哈希和 8911 停止均通过。

### 2.2 worker_02：expected-set、双向 assignment、五类 L1、Query 与 lifecycle

- 会话：`019ff304-37bb-7000-87a5-9bd0312aea0f`。
- 初轮由北京时间 07:00 前的有效路由 `Pi/opencode-go/deepseek-v4-flash:max` 执行；07:00 后的纠偏在同一 session 切换为 `Pi/cms-smk/deepseek-v4-flash:max`，未废弃或新开 session。
- 当前接受文件：
  - `poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule_evaluator.py`
    - SHA-256 `bf6fdc047a40da4a199a1fb5aae765b239eaa5c4751eb4f70c6f934edc647c1f`
  - `poc/medical_monitoring_ai_native_r4/tests/test_visit_schedule_slice.py`
    - SHA-256 `fcaa4489e512d5a413e89b9ae0ee0ca0c8082e803359efea9f3c16f0766c2569`
- 已落地：合同顺序的 gate/expected-set、双 cutoff scope、访视与活动双向 assignment、consumption ledger、固定/producer/链式 anchor、五类 L1、确定性优先级、三段式中文 Query、公共 R4 lifecycle adapter 接线。
- Codex 定向纠偏：
  1. 修复“open gate 但 `domain_complete == (True, [])`”；现在医学完整性为 coverage 完整性与 gate 关闭状态的 AND，applicability/routing/anchor/cutoff 任一 open gate 均返回不完整和确定性理由。
  2. 修复“任意处置记录被当作已入组”；现在只有明确随机/入组或接受研究干预且覆盖完整才允许 `enrolled_or_post_enrollment` 与 PD 措辞。处置记录单独存在保持未决；明确未随机且未干预可判为尚未入组。
- Codex 独立反例复现：
  - open applicability gate：`gates_block_domain=True`，`domain_complete=(False, ['open ScheduleGate(s) block domain completeness: applicability'])`。
  - disposition-only：`enrollment_state_unresolved`；随机/入组=False 且研究干预=False：`enrollment_not_occurred`；明确随机/入组=True：`enrolled_or_post_enrollment`。
- 最终门禁：D05 contract+slice `247 passed`；完整 R4 `1232 passed`；Ruff、compileall/import、保护哈希与 8911 停止均通过。

## 3. 保护面与最终哈希

- `src/mm_r4/contracts.py` `993d6bea9b10842aa13f8226847961ff3881689a34797c8fdb9d68ac1aa6e5c4`
- `src/mm_r4/lifecycle.py` `99fec3e3b363f9a85a0a2f24db66a07d02f9dd852096fcf4185fa1e82a45d795`
- `src/mm_r4/protocol.py` `4665c5113c3f9d9ada10d3c3b2837f181c661d879ae3844f26504685b1127f47`
- `src/mm_r4/protocol_projection.py` `c4cf09ce3af8fa38aac21087e8aedda43e2d76ebe4f5215e256dfaacd0dc38b0`
- `src/mm_r4/protocol_fixtures.py` `ea51204401423f3547903993ae2d5b5bc0a7af771a609adf22f3b2cf37e8b30f`
- `src/mm_r4/__init__.py` `d5e0050c91fd6c0f2cc36ab7ebbf4991117a697d8cbec084c80f263d98cca5ad`
- `README.md` `9858bb4ecb03868975e571dd5f322e62747cedc20dd8f344e415b38399b7ab12`
- 8911：无监听。

## 4. 执行证据注意事项

- `runs/execution/.../worker_01.md` 与 `worker_02.md` 仍是 runner 首轮报告文本，未反映同 session 后续纠偏的最终哈希/计数；不得将其单独当作恢复真相。
- 最终纠偏证据保存在：
  - `logs/execution/medical_monitoring_r4_d05_implementation_20260812/worker_01_followup1.stdout.log`
  - `logs/execution/medical_monitoring_r4_d05_implementation_20260812/worker_01_followup2.stdout.log`
  - `logs/execution/medical_monitoring_r4_d05_implementation_20260812/worker_02_followup1.stdout.log`
- 当前文件系统、本文哈希和 Codex 独立测试结果优先于旧首轮报告。
- 过程日志较大但仍是未完成执行链的纠偏证据，本次暂停不清理；仅在 D05 总体验收和归档后按执行清理流程处理。

## 5. 明确未完成

1. worker_03 未启动：`visit_schedule_projection.py`、`visit_schedule_fixtures.py`、Patient Journey renderer-neutral 投影、116 行挑战矩阵与确定性金样均未实现/验收。
2. worker_04 未启动：根包导出、README、D01-D04/R2/R3 相邻回归尚未完成。
3. Cursor execution manager 未启动；Codex 尚未做 D05 总体接受或冻结实现快照。
4. 独立接受审阅、R0-R8/LOOP 最终收口、review-gate 与 execution cleanup 均未进行。
5. 这不是 R4 总体、R5 UI、Patient Journey 前端、真实项目、产品或商业使用接受。

## 6. 下一次恢复的安全动作

1. 完整读取最新全局与 workbench `AGENTS.md`、冻结合同、本文、执行 context、R0-R8 计划和 LOOP ledger。
2. 只读复核本文四个接受文件 SHA、七个保护文件 SHA、`247` 聚焦测试、`1232` 完整 R4 和 8911 停止状态；不要从旧 worker 报告恢复代码。
3. 更新并预检 worker_03 prompt，显式写入当前四个接受 SHA、open-gate completeness 和 enrollment Query 纠偏；然后按当时有效路由启动 worker_03。
4. worker_03 经 Codex 验收后，依次执行 worker_04、manager、Codex 全量决定性回归与独立接受；继续保持串行，不提前启动后续角色。
5. 继续不运行真实项目、不启动 8911、不触碰产品/R5 UI/医学写作、不扩展系统安全设计/测试。

