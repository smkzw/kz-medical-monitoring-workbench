# 医学写作翻译历史迁移、失效投影与跨项目隔离修复报告

日期：2026-07-25  
范围：独立审阅报告 `P1-4`、`P1-5`、`P2-1`，以及 `P2-2` 跨项目同 ID 后端回归测试。  
执行约束：未修改 `evidence_picos_workflow.py`、`EvidenceDesignWorkspace.jsx` 或 handoff；未重启 5174/8911；未读取或写入运行态 SQLite。

## 1. 修复结论

本轮已完成以下语义闭环：

1. 历史 `approved + not_admitted` 不再成为 UI 死状态。旧 review 保持只读历史记录；当前医学作者可执行一次“确认当前译文并准入”，后端在同一事务内新增作者确认、完成语料准入并写迁移审计。
2. 来源失效或结构解析版本替换后，旧 review 仍可追溯，但不再作为当前作者确认。批次 `author_confirmed_count` 和单条 UI 均以当前 translation、当前作者确认和当前有效 brief 的联合状态为准。
3. 对非当前 translation revision 的任何作者处置均在事务内明确拒绝。尤其 `returned`、`rejected` 不再返回假成功，也不会新增 review、审计或改变当前 translation 状态。
4. 两个项目即使强制拥有相同 `batch_id`、`item_id`、`artifact_id`、`span_id` 和 `translation_id`，读取、确认、来源失效、brief 准入和批次统计仍按 `project_id` 完全隔离。

## 2. 修复前复现

先新增最小回归用例并在实现前运行，观察到：

- 历史批准记录没有迁移审计，UI 条件无可执行出口。
- 当前 translation 已为 revision 2 时，对 revision 1 首次提交 `returned` 会成功写入历史 review；第二次才因 review revision 冲突失败。
- 来源失效后，批次仍返回 `author_confirmation_status=confirmed`，且 `author_confirmed_count=1`。

初始复现命令：

```bash
python3 -m unittest \
  tests.test_writing_reference_admission_repository.WritingReferenceAdmissionRepositoryTests.test_legacy_approved_without_admission_requires_current_author_confirmation_and_preserves_history \
  tests.test_writing_reference_admission_repository.WritingReferenceAdmissionRepositoryTests.test_return_or_reject_of_non_current_translation_revision_is_rejected_without_audit_write \
  tests.test_writing_reference_translation_batch.WritingReferenceTranslationBatchTests.test_invalidated_source_keeps_review_as_history_but_clears_current_author_confirmation
```

结果：3 个测试中出现 1 个 error、4 个 failure，成功复现审阅报告所述状态错误。

## 3. 后端实现

### 3.1 历史批准的一次作者确认迁移

`WritingReferenceRepository.record_medical_review` 现在会在 `BEGIN IMMEDIATE` 事务内：

- 先读取当前 translation state，确认请求 revision 就是当前 revision；
- 读取当前 review state 及其完整历史 payload；
- 识别 `approved` 但 `decision_type != author_confirmation` 或 `admission_status != admitted` 的旧记录；
- 保留旧 review record，不覆盖历史 payload；
- 新建 `author_confirmation` review，并调用同事务的 `admit_translation`；
- 写入 `legacy_translation_author_confirmation_migrated` 审计，绑定旧 review ID、新作者确认 ID 和 translation revision；
- 任一准入门禁失败时整体回滚。

### 3.2 非当前 translation revision 明确拒绝

作者处置在幂等重放和 review-state 更新前先校验当前 translation revision。请求 revision 不是当前 revision 时抛出 `WritingReferenceStaleStateError`。

`returned`、`rejected` 分支更新 translation state 后检查 `rowcount == 1`；状态未实际改变时不再提交 review 或返回成功。

### 3.3 当前有效作者确认投影

批次投影不再把 `review.decision == approved` 直接等同于当前确认。只有同时满足以下条件才投影为 `confirmed`：

- translation 是该项目、该 ID 的当前 revision；
- translation 与批次 item 的 source span 一致；
- translation 当前状态为 `author_confirmed_admitted`；
- review 为当前 revision 的 `author_confirmation`；
- review 为 `approved` 且 `admission_status=admitted`；
- 同 revision 存在 `approved_current` evidence brief。

来源或结构解析失效时：

- `medical_review_status=approved` 可继续作为历史事实展示；
- `author_confirmation_status=not_confirmed`；
- `admission_status=invalidated`；
- `author_confirmed_count=0`、`admitted_count=0`；
- 失效项不计入当前待作者确认数量。

## 4. 前端实现

`WritingReferencePanel` 现在区分三类状态：

1. **当前作者确认有效**：仅当 translation、author confirmation 和 current brief 同时有效时显示“作者已确认”。
2. **历史批准但未准入**：显示“历史审核已批准”，明确其不构成当前确认，并提供“确认当前译文并准入”一次性迁移入口；仍可退回或拒绝。
3. **来源/解析/确认已失效**：主状态优先显示 translation 的失效原因，历史 review 使用中性历史标签，不显示为当前已确认，并提示基于当前来源重新生成译文。

`ReferenceTranslationBatchPanel` 的每行补充 `data-admission-status`，使回归测试和后续浏览器验收能同时核对作者确认与准入状态。

## 5. 新增回归覆盖

新增或调整的状态回归包括：

- 历史 approved、无 brief 的读取、一次作者确认、原子准入、旧 review 保留、迁移审计和审计链完整性；
- revision 2 已成为当前版本后，对 revision 1 执行 `returned`、`rejected` 均报 stale，且 review/audit 数不变；
- 来源失效后旧批准仅为历史，当前确认数和准入数归零；
- extraction revision 替换后旧批准仅为历史，当前确认数和准入数归零；
- 两个项目强制使用完全相同的 batch/translation 业务 ID：
  - 项目 A 确认不改变项目 B；
  - 项目 A 来源失效不改变项目 B；
  - 项目 B 后续确认不恢复项目 A；
  - 两项目批次统计、brief、review、artifact state 和审计链相互隔离。

## 6. 验证结果

聚焦后端与前端合同测试：

```bash
python3 -m unittest \
  tests.test_writing_reference_admission_repository \
  tests.test_writing_reference_translation_batch \
  tests.test_writing_reference_repository \
  tests.test_writing_reference_api \
  tests.test_frontend_medical_writing_translation_batch_contract \
  tests.test_frontend_medical_writing_contract
```

结果：

```text
Ran 162 tests in 2.561s
OK
```

Python 语法编译：

```bash
python3 -m py_compile \
  services/api/app/writing_reference_repository.py \
  services/api/app/writing_reference_translation_batch.py
```

结果：通过。

前端生产构建：

```bash
cd frontend
npm run build
```

结果：Vite 6.4.2，1888 modules transformed，构建成功。存在既有的大 chunk 警告，不影响本轮状态机功能验收。

## 7. 修改文件

- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- `tests/test_writing_reference_admission_repository.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_frontend_medical_writing_contract.py`
- `tests/test_frontend_medical_writing_translation_batch_contract.py`
- `reviews/mw_translation_legacy_invalidation_isolation_worker_20260725.md`

## 8. 未执行事项

- 按任务约束未重启 5174/8911，因此未把本轮源码切换到当前常态端口。
- 未对运行态 SQLite 做迁移探针或写入；所有状态验证均使用测试临时 SQLite。
- 未修改 PICOS、Evidence Design 或 handoff 相关代码。

