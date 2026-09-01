# PICOS 单次作者确认与 handoff 业务幂等修复报告

日期：2026-07-25  
范围：独立审阅报告 `mw_author_selection_confirmation_independent_review_20260725.md` 的 P1-1、P1-2、P1-3。  
边界：未修改翻译仓库或翻译 UI；未重启 5174/8911；未读取、修改或迁移运行态 SQLite。

## 结论

P1-1、P1-2、P1-3 已在源码与隔离测试中完成修复。

- 医学经理选择候选，或保存对已选候选的修订，即完成该 PICOS 域的作者确认。
- 不再要求点击“确认当前域”，也不再把生成快照表述为第二次医学确认。
- 全部域已采用且质量门通过后，前端以一个技术动作生成版本快照并创建撰写交接。
- 历史 `in_medical_review`、`returned_for_revision` 均可通过当前 UI 使用的接口迁移；迁移后原审批中心待办清除。
- handoff 以服务端业务身份实现幂等，覆盖刷新、重复点击、不同客户端幂等键、并发、进程重建和新 revision。

## 修复前复现

### P1-1

`select_option` 即使同时提交候选和医学理由，仍写入“待医学确认”；随后必须再调用 `mark_writing_candidate`。前端也同时提供“保存医学理由”“确认当前域”“确认并生成快照”三个连续动作。

### P1-2

- `in_medical_review` 后端已有迁移能力，但 UI 禁用入口。
- `returned_for_revision` 虽可从 UI 调用快照接口，但后端对既有快照原样返回，形成 2xx 假成功。
- 两种历史状态均会被审批中心计为待办，未完成迁移时无法从真实用户路径清除。

### P1-3

handoff ID 已由项目、资料包、snapshot 和目标文档确定，但 SQLite 仅按客户端 `idempotency_key` 重放。同一业务交接更换 key 会再次插入同一主键并报唯一键冲突。前端又使用包级本地布尔值，刷新后丢失，新 revision 后也不能可靠复位。

## 实现

### 1. 域级作者确认只有一次

- `select_option` 原子保存候选、理由（如有）、revision 和审计，并直接投影为“作者已确认”。
- `save_rationale` 表示对当前候选完成修订并采用，保持“作者已确认”。
- 旧 `select_option` / `save_rationale` 记录即使保存了旧的“待医学确认”状态，也在当前投影中归一为作者已确认，避免历史项目再次点击确认。
- 未填写医学理由时，域选择仍是作者确认；完整性质量门继续提示理由缺失并阻断最终技术快照。这里的阻断是内容完整性，不是第二次医学确认。
- 前端移除“确认当前域”，将理由动作改为“保存修订并采用”。

### 2. 快照与交接改为纯技术动作

- 前端只保留“生成版本快照与撰写交接”按钮。
- 一次点击先确保当前 revision 存在版本化快照，再创建 protocol handoff。
- UI 不再使用“确认并生成快照”“历史审批待处理”等二次医学确认语义。
- 内部 API 路径和兼容字段仍保留 `approval` 命名，避免破坏既有调用；这些名称不再作为用户动作展示。

### 3. 历史状态真实迁移

- 既有快照处于 `in_medical_review` 或 `returned_for_revision` 时，均进入同一兼容迁移事务。
- 迁移在一个 SQLite 事务中更新 gate、写迁移审计和决策记录。
- 决策的 `previous_state` 保留真实历史状态，不再固定写成 `in_medical_review`。
- 迁移完成后必须重新读取 workflow 并验证当前 snapshot 已成为 `author_confirmed`；无法识别或未持久化的状态返回冲突错误，不再 2xx 假成功。
- 历史 gate 变为 `medically_approved` 仅作为旧数据兼容绑定；产品语义是“已有作者选择迁移为版本化技术快照”，不要求同一医学经理再次批准。

### 4. handoff 服务端业务幂等

- 业务身份包含：project、package、working state、snapshot、approval binding、revision、target module、target document type。
- 请求指纹不再包含随机时间戳，重试保持稳定。
- `BEGIN IMMEDIATE` 事务在验证当前 gate、snapshot、revision、来源哈希后，先查询业务确定的 handoff ID。
- 既有 handoff 与业务身份一致时直接重放，并为新的客户端幂等键登记结果，不重复写 handoff 或审计。
- 若同一 handoff ID 对应不同业务身份，明确返回冲突。
- 服务层发生重放时返回数据库中的既有 handoff，而不是带新时间戳的临时对象。

### 5. UI 以服务端状态为事实来源

`EvidencePicosWorkflowResult` 新增当前 handoff 投影：

- `current_handoff_id`
- `current_handoff_snapshot_id`
- `current_handoff_revision`
- `current_handoff_target_document_type`

前端据此判断当前 revision 是否已完成交接。刷新后状态可恢复；PICOS 修订产生新 revision 后，旧 handoff 不会阻止新 snapshot/handoff。

## 改动文件

生产源码：

1. `packages/contracts/workbench_contracts/models.py`
2. `services/api/app/evidence_picos_workflow.py`
3. `services/api/app/sqlite_runtime_store.py`
4. `frontend/src/features/evidence-design/EvidenceDesignWorkspace.jsx`

测试：

5. `tests/test_evidence_picos_workflow.py`
6. `tests/test_evidence_picos_approval_api.py`
7. `tests/test_frontend_evidence_design_contract.py`

构建校验生成了 `frontend/dist/` 下的 Vite 派生文件；未部署、未重启当前服务。

翻译相关源码和 UI 未由本任务修改。

## 测试

执行：

```text
python3 -m unittest \
  tests.test_evidence_picos_workflow \
  tests.test_evidence_picos_approval_api \
  tests.test_frontend_evidence_design_contract \
  tests.test_sqlite_evidence_design_store \
  tests.test_medical_writing_protocol_assembly_plan \
  tests.test_medical_writing_working_copy_persistence
```

结果：`43 tests passed`。

覆盖点：

- 无理由选择即域作者确认，但完整性门仍阻断最终快照。
- 保存理由/修订即采用，不需要 `mark_writing_candidate`。
- 五个 PICOS 域从原 10 次动作降为 5 次选择动作。
- `in_medical_review` 事务迁移、故障回滚、重试、重启恢复、审批待办清除。
- `returned_for_revision` 经真实 FastAPI 路径迁移，响应状态与持久化状态一致，审批待办清除。
- handoff 使用四路并发和不同客户端幂等键，只生成一条记录且返回同一 `created_at`。
- 进程重建后重复创建返回同一 handoff。
- 同资料包新 revision 生成新的 snapshot 和新的 handoff，旧 handoff 保留但不投影为当前。
- 来源或 revision 变化后，旧 snapshot 不能创建当前 handoff。
- PICOS 相邻写作装配和工作副本持久化回归通过。

附加校验：

```text
python3 -m py_compile \
  services/api/app/evidence_picos_workflow.py \
  services/api/app/sqlite_runtime_store.py \
  packages/contracts/workbench_contracts/models.py
```

结果：通过。

```text
npm --prefix frontend run build
```

结果：Vite 构建通过，1888 modules transformed。仅保留既有的大 chunk 警告，无构建错误。

## 残余风险与后续验收

1. 按任务要求未重启 5174/8911，因此当前已运行端口仍不是本轮源码的运行态验收证据。
2. 前端状态迁移已由静态合同、真实 FastAPI 路径和后端事务测试共同覆盖；仍需在统一重启窗口完成浏览器点击、刷新、快速重复点击和新 revision 的真实 UI 验收。
3. 内部 `approval-submissions` 路径及 `ApprovalGate.MEDICALLY_APPROVED` 保留用于历史数据与接口兼容。UI 已不再把该技术绑定描述为新的医学批准。
4. 当前完整性门仍要求每个域填写医学理由。缺理由只阻断技术快照，不撤销作者对候选的选择；若未来决定理由完全可选，应作为独立产品规则调整，不应重新引入确认按钮。
