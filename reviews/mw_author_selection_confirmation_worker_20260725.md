# 医学作者选择/确认状态机统一实施记录

日期：2026-07-25  
范围：医学写作主路径中的章节候选/工作副本、Evidence/PICOS、翻译语料准入及对应 UI/测试。

## 结论

当前医学经理即医学作者。当前路径不再生成第二层待医学批准状态：

| 业务面 | 当前迁移 | 兼容边界 |
|---|---|---|
| 章节候选 | `candidate_ready` -> 原子 `accept-and-apply` -> `author_selected`，同事务写入版本化工作副本 | 复用既有实现；`pending_medical_approval`、`accepted_pending_medical_approval` 只按历史候选读取并在 UI 标为历史状态 |
| PICOS | 选择候选 + 医学理由 -> `作者已确认`；全部域和质量门通过 -> 作者确认快照 -> 直接写作交接 | 保留 `/approval-submissions` 路径作为旧客户端兼容入口；新行为不进入审批中心。历史 `in_medical_review` 仍可读取并投影为 `legacy_pending_medical_approval`，作者再次确认时原子升级同一旧绑定 |
| 翻译 | 候选生成 -> `pending_author_confirmation`；忠实度通过 + 作者确认 -> 同事务写确认记录、Evidence Brief 和 `author_confirmed_admitted` | 保留 `/medical-review` 路径作为兼容入口；`/admissions` 仅供旧客户端幂等重放。旧 `pending_medical_approval` 可读、可按作者确认语义直接准入 |

章节候选路径未重复改造：现有 `accept_and_apply_candidate` 已将候选选择、同轮兄弟候选处置、`author_selected`、工作副本内容/版本、快照、审计和幂等记录放在一个 SQLite 事务内。旧分步写入只保留在演示兼容面，生产 UI 使用“选用并写入”。

## 后端实现

- PICOS 每域确认的新写入状态为 `作者已确认`；历史 `mark_writing_candidate` 动作不改写审计记录，但当前投影统一为作者已确认。
- PICOS 确认快照继续复用现有不可变快照与运行库约束。兼容 `ApprovalGate` 在同次作者确认中直接写为 `medically_approved`，ID 使用 `confirmation_picos_*`，因此不会形成审批中心待办。
- PICOS 快照绑定资料包哈希和 revision；来源变化或任一域动作会失效原确认。相同 revision 重复确认复用同一快照。
- 若同一 revision/hash 已存在固定 `picos_snapshot_*`，且绑定为历史
  `approval_picos_*` + `medical_review_submission` +
  `legacy_medical_approval` + `in_medical_review`，作者再次确认会原子更新同一
  gate 为 `medically_approved`。旧 snapshot、旧 `approval_id` 和原工作流审计
  均保留；新增迁移审计保存旧 gate 完整载荷，并明确
  `second_medical_approval_required=false`。
- 历史 gate 迁移复用 `commit_approval_action` 的单事务 gate/审计/决策提交，
  使用由 snapshot + approval + revision 派生的固定迁移幂等键。重复点击、并发
  重放和进程重启均返回同一持久化绑定，不新增第二条迁移记录。
- 翻译作者确认沿用原仓储 CAS、来源当前性、文档哈希、结构审核、内容核验/用户 override、抽取 lineage、忠实度和幂等检查。
- `approved` 兼容决策现在表示作者确认。确认记录与 Evidence Brief 在同一个 `BEGIN IMMEDIATE` 事务内完成；任一准入门失败时确认记录、审计和准入整体回滚。
- 确认后 Evidence Brief 保存 `medical_author_confirmation` 和确认 ID；历史复核记录缺少新字段时按 `legacy_medical_review` 解析，不删除旧审计。
- 退回/拒绝会恢复 `pending_author_confirmation` 投影；已准入译文被退回、来源替换或抽取版本变化时，既有 Brief 继续按原规则失效并保留历史。
- 批量翻译 API 墕量返回 `author_confirmation_status`、`pending_author_confirmation_count`、`author_confirmed_count`；旧 `medical_review_status` 和旧计数字段保留兼容。

## UI 实现

- PICOS 当前页显示“确认当前域”“作者确认与撰写交接”“确认并生成快照”，不再跳转审批中心。
- 翻译当前页显示“待作者确认”“确认译文并准入”；移除当前 UI 的第二次 `/admissions` 调用和“纳入写作参考库”按钮。
- 批量翻译表、筛选、进度旅程和深链动作改为作者确认语义；忠实度阻断仍不可确认准入。
- `pending_medical_approval` 显示为“历史状态：待迁移”。
- I 期共享语料的额外选择明确标为跨项目“共享适用性核对/显式纳入”，不再表述为第二次医学批准。
- 文档内容核验、结构审核、逐项 warning、`已确认沿用` override 和失效提示均保留。

## 验证

聚焦与相邻回归：

```text
python3 -m unittest \
  tests.test_evidence_picos_workflow \
  tests.test_evidence_picos_approval_api \
  tests.test_writing_reference_admission_repository \
  tests.test_writing_reference_translation_batch \
  tests.test_writing_reference_translation_service \
  tests.test_writing_reference_repository \
  tests.test_writing_reference_api \
  tests.test_medical_writing_revision_application \
  tests.test_medical_writing_author_freeze_backend \
  tests.test_frontend_evidence_design_contract \
  tests.test_frontend_medical_writing_translation_batch_contract \
  tests.test_frontend_medical_writing_contract
```

结果：`206 tests`，全部通过（原 `205` 项 + 新增历史 PICOS 迁移回归）。

新增聚焦回归真实写入旧版不可变 PICOS snapshot 与
`approval_picos_* / in_medical_review` gate，并验证：

- gate 写入后的故障注入会整体回滚，旧 gate、迁移审计和决策均不产生部分写入；
- 作者再次确认后 workflow 为 `author_confirmed`，可直接创建版本化 handoff；
- dashboard 待审批计数与 inbox/审批中心项目均为 0；
- 旧 snapshot 类型、旧 `approval_id`、原工作流审计保持不变，迁移审计链校验通过；
- 换用新幂等键重复确认及重新创建存储/服务后，迁移审计和决策仍各只有 1 条。

```text
cd frontend && npm run build
```

结果：Vite `6.4.2` 构建通过，`1888 modules transformed`。仅有既存的大 chunk 警告，未影响构建。

静态事务清理核对：

- 对 `writing_reference_repository.py` 逐行扫描相邻
  `connection.rollback()`，结果为空；当前工作树已无连续重复 rollback，因此
  未再改写正常的独立校验回滚分支。

现有运行面只读核查：

- `http://127.0.0.1:5174/` 返回 200。
- `http://127.0.0.1:8911/api/health` 返回 200。
- MG-K10-CRSwNP 的实际 PICOS 页面显示“确认当前域”“确认并生成快照”“作者确认与撰写交接”，页面不含“待医学批准”或“提交医学批准”。
- 医学写作实际页面被版本门禁阻断，原因是 8911 仍运行旧后端 build，与当前前端期望 build 不一致。遵守“不重启 5174/8911”，未重启、未绕过，因此翻译页的最终实时交互仍待允许同步运行版本后复核。

未修改 runtime SQLite；未重启 5174/8911；未触碰
`runs/codex_mw-author-selection-confirmation-20260725.md`。

## 改动文件

生产源码：

- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/evidence_picos_workflow.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `frontend/src/features/evidence-design/EvidenceDesignWorkspace.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- `frontend/src/features/writing-reference/SharedPhase1CorpusPanel.jsx`
- `frontend/src/features/writing-reference/progressJourneyLogic.mjs`

直接相关测试：

- `tests/test_evidence_picos_workflow.py`
- `tests/test_evidence_picos_approval_api.py`
- `tests/test_writing_reference_admission_repository.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_writing_reference_translation_service.py`
- `tests/test_frontend_evidence_design_contract.py`
- `tests/test_frontend_medical_writing_translation_batch_contract.py`
- `tests/test_frontend_medical_writing_contract.py`

交付记录：

- `reviews/mw_author_selection_confirmation_worker_20260725.md`

Vite 构建刷新了 `frontend/dist/` 生成物。`medical_writing_repository.py` 和
`frontend/src/App.jsx` 未修改：其当前生产章节路径已采用作者选用语义和原子
`accept-and-apply`，历史状态标签也已满足兼容要求。

## 本次历史迁移补丁文件

- `services/api/app/evidence_picos_workflow.py`
- `tests/test_evidence_picos_approval_api.py`
- `reviews/mw_author_selection_confirmation_worker_20260725.md`

`writing_reference_repository.py` 属于本次任务原改动范围，但在本次补丁开始时
已无审阅指出的连续重复 `connection.rollback()`；未为制造差异改写该文件。
