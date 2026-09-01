# 医学作者选择/确认独立审阅

日期：2026-07-25  
范围：仅审阅功能、科学语义和状态机一致性；未做安全或后门审计。  
结论：**不建议按本轮状态放行。未发现 P0；发现 6 项 P1、2 项 P2。**

本结论以“系统用户就是医学经理；其选择、采用、修订后采用或确认即项目确认，不得再要求第二次医学批准”为判定原则。审阅未修改生产源码或运行态 SQLite，未重启 5174/8911。

## P0

无。

## P1

### P1-1 PICOS 当前流程仍要求同一医学经理重复确认

**现象**

- 选择候选并填写理由后，后端仍把域状态置为“待医学确认”，只有另一次 `mark_writing_candidate` 才成为“作者已确认”：[evidence_picos_workflow.py](../services/api/app/evidence_picos_workflow.py#L249)。
- UI 先执行候选选择，再要求点击“确认当前域”；全部域完成后还要求点击“确认并生成快照”：[EvidenceDesignWorkspace.jsx](../frontend/src/features/evidence-design/EvidenceDesignWorkspace.jsx#L947)、[EvidenceDesignWorkspace.jsx](../frontend/src/features/evidence-design/EvidenceDesignWorkspace.jsx#L987)、[EvidenceDesignWorkspace.jsx](../frontend/src/features/evidence-design/EvidenceDesignWorkspace.jsx#L1218)。

**影响**

对一个懒惰但专业的医学写作用户，这是同一身份对同一选择的二次乃至三次确认。它违背本轮明确原则，也增加漏点、误以为已完成和无意义待办的概率。

**测试假阳性**

`test_sqlite_snapshot_approval_and_handoff_are_revision_bound` 明确要求每个域“选择一次 + 确认一次”，5 个域累计 10 个 revision；前端合同测试还明确断言“确认并生成快照”存在。因此现有测试是在固化冲突行为，而不是防止回归：[test_evidence_picos_workflow.py](../tests/test_evidence_picos_workflow.py#L175)、[test_frontend_evidence_design_contract.py](../tests/test_frontend_evidence_design_contract.py#L124)。

**建议**

将医学经理的选择/修订后采用作为该域的项目确认。快照和交接可以保留为技术动作，但不得再次表述或实现为医学审批/确认；后端应以一个原子动作保存选择、理由、来源、revision 和审计。

### P1-2 PICOS 历史状态迁移与 UI 可达性冲突

**现象**

- 后端能够把历史 `in_medical_review` 快照升级为作者确认：[evidence_picos_workflow.py](../services/api/app/evidence_picos_workflow.py#L388)。
- UI 却只允许 `ai_draft`、`returned_for_revision` 调用该接口；`in_medical_review` 显示“历史审批待处理”且按钮禁用：[EvidenceDesignWorkspace.jsx](../frontend/src/features/evidence-design/EvidenceDesignWorkspace.jsx#L613)。
- 审批中心继续把 `in_medical_review` 计为待办：[main.py](../services/api/app/main.py#L1495)。因此历史 PICOS 会永久留在待办中，除非绕过当前 UI 直接调用接口。
- 反向边缘案例也存在：UI 允许 `returned_for_revision` 提交，但后端已有快照分支只迁移 `in_medical_review`，否则原样返回；UI 对任意 2xx 都提示“作者确认快照已生成”，会产生假成功：[evidence_picos_workflow.py](../services/api/app/evidence_picos_workflow.py#L388)、[EvidenceDesignWorkspace.jsx](../frontend/src/features/evidence-design/EvidenceDesignWorkspace.jsx#L477)。

**影响**

历史状态虽可读，但不能通过真实用户路径完成迁移；审批中心会保留不应存在的二次医学待办。`returned_for_revision` 还会向用户报告并未发生的确认。

**测试假阳性**

后端测试直接调用 service，能证明迁移事务本身正确，却没有证明 UI 可达：[test_evidence_picos_approval_api.py](../tests/test_evidence_picos_approval_api.py#L187)。静态前端测试反而断言了排除 `in_medical_review` 的条件。

**建议**

为 `in_medical_review` 提供一次作者确认即迁移的 UI 路径，并在同一事务中清除审批中心待办；明确处理已有 `returned_for_revision` 快照，不能以无状态变化的 2xx 返回成功。

### P1-3 PICOS 写作交接不具备业务级幂等和刷新恢复能力

**现象**

- handoff ID 由项目、资料包、快照和目标文档确定：[evidence_picos_workflow.py](../services/api/app/evidence_picos_workflow.py#L612)。
- 存储层却仅按客户端 `idempotency_key` 重放；同一快照换一个 key 会再次插入相同 handoff 主键并冲突：[sqlite_runtime_store.py](../services/api/app/sqlite_runtime_store.py#L8081)。
- UI 只用本地布尔值 `handoffCreated` 控制按钮；刷新后丢失，且生成新 snapshot/revision 后也不会重置，只有切换项目/资料包才重置：[EvidenceDesignWorkspace.jsx](../frontend/src/features/evidence-design/EvidenceDesignWorkspace.jsx#L223)、[EvidenceDesignWorkspace.jsx](../frontend/src/features/evidence-design/EvidenceDesignWorkspace.jsx#L488)。

**复现**

在临时 SQLite 中，同一 snapshot 首次创建成功；第二次使用不同 idempotency key 返回 `UNIQUE constraint failed: evidence_picos_writing_handoffs...handoff_id`。

**影响**

刷新后重复点击会报错；同一资料包修订并形成新快照后，旧布尔值又会阻止创建新交接，直到用户刷新。真实状态取决于浏览器会话而不是后端快照。

**建议**

按业务唯一键查询并返回既有 handoff，或用冲突安全的原子 upsert；UI 从服务端 handoff 状态投影，并按 `snapshot_id/revision/target_document_type` 绑定，不使用包级本地布尔值作为事实来源。

### P1-4 历史“已批准但未准入”译文在当前 UI 中无迁移出口

**现象**

- 旧记录缺少新字段时会反序列化为 `decision_type="legacy_medical_review"`、`admission_status="not_admitted"`：[models.py](../packages/contracts/workbench_contracts/models.py#L8408)。
- UI 能找到当前 `approved` review，但只有同时存在 `approved_current` brief 时才显示撤回；只有完全没有 review 时才显示“确认译文并准入”：[WritingReferencePanel.jsx](../frontend/src/features/writing-reference/WritingReferencePanel.jsx#L118)、[WritingReferencePanel.jsx](../frontend/src/features/writing-reference/WritingReferencePanel.jsx#L433)、[WritingReferencePanel.jsx](../frontend/src/features/writing-reference/WritingReferencePanel.jsx#L1533)。
- 当前 UI 已移除独立 admission 动作。因此“旧 approved + 无 brief”既不能准入，也不能重新确认或退回。

**复现**

在临时 SQLite 中写入一个旧式 `approved` review 且不写 brief，读取结果为 `legacy_medical_review / confirmed / not_admitted / current_brief_count=0`，UI 条件没有任何可执行分支。

**影响**

历史状态可读但不可迁移，医学经理无法把已经批准的译文带入新的一次确认即准入流程。

**建议**

提供显式兼容迁移：把旧 `approved + not_admitted` 映射为可由当前医学经理一次确认并原子准入的状态，同时保留旧 review 和迁移审计。

### P1-5 来源变化后，翻译批次仍把失效确认计为“当前作者已确认”

**现象**

- 来源失效会正确把 translation 和 brief 标为失效，历史记录仍保留。
- 批次投影却只根据同 revision 的 review decision 计算 `author_confirmation_status`；旧 `approved` review 因而仍映射为 `confirmed`，并进入 `author_confirmed_count`：[writing_reference_translation_batch.py](../services/api/app/writing_reference_translation_batch.py#L3340)、[writing_reference_translation_batch.py](../services/api/app/writing_reference_translation_batch.py#L3400)。
- 单条 UI 标签优先显示 review decision，而不是 translation 的当前失效状态：[WritingReferencePanel.jsx](../frontend/src/features/writing-reference/WritingReferencePanel.jsx#L1533)。

**复现**

临时库中准入前为 `author=confirmed, admission=admitted`；使来源失效后变为 `author=confirmed, admission=invalidated`，批次仍报告 `author_confirmed_count=1`。

**影响**

历史确认被错误投影为当前有效确认。医学写作用户会看到“已确认”与“已失效”并存，汇总数也高估可用材料；这破坏来源变化必须使当前确认失效的语义。

**建议**

把“历史曾确认”和“当前确认有效”拆开。只在 translation、extraction、source/hash、review 和 brief 均为当前有效时计入 `author_confirmed_count`；旧确认保留在历史区并标注失效原因。

### P1-6 当前 5174/8911 构建不匹配，不能完成真实运行态验收

**只读观察**

- `http://127.0.0.1:5174/runtime-build.json` 期望后端 `api-fc03aa9bf2e3a4f9`。
- `http://127.0.0.1:8911/api/runtime-readiness` 返回当前后端 `api-9a66182ec0a076ae`，其自身 `ready=true`、schema 16。
- 5174 首页可访问，8911 健康检查通过；但前端按 [runtimeReadiness.js](../frontend/src/runtimeReadiness.js#L20) 会把构建号不一致判为未就绪。

**影响**

本轮不能把源码审阅或静态前端测试等同于真实 UI 可用性。按用户限制，本次未重启服务。

**建议**

修复上述状态机问题后，在获准的发布/重启窗口以同一源码状态启动前后端，再完成浏览器端验收。

## P2

### P2-1 对旧 translation revision 的退回/拒绝会假成功

`record_medical_review` 在事务外读取指定历史 revision，事务内只对该 revision 的 review-state 做 CAS；退回/拒绝更新当前 translation-state 时附带 revision 条件，却不检查 rowcount：[writing_reference_repository.py](../services/api/app/writing_reference_repository.py#L2135)、[writing_reference_repository.py](../services/api/app/writing_reference_repository.py#L2223)。

临时库复现：当前已是 revision 2 时，对 revision 1 提交 `rejected` 返回成功并写入历史 review，但当前 revision 2 仍是 `pending_author_confirmation`。当前有效译文未被破坏，但用户收到假成功，审计中出现对非当前版本的处置。

建议在同一事务中读取并锁定 current translation revision；所有 decision 都必须与 current revision 一致，非批准分支也必须检查状态更新 rowcount。

### P2-2 直接测试缺少跨项目同 ID 回归，前端测试主要是字符串存在性

本次临时库探针表明，跨项目读取 batch 和跨项目 review translation 都会返回 `KeyError`，相关 SQL 也包含 `project_id`，未观察到实际跨项目泄漏。但本轮直接测试未覆盖“两个项目具有相同 batch/translation ID”时的读写、确认、失效和汇总隔离。

同时，[test_frontend_evidence_design_contract.py](../tests/test_frontend_evidence_design_contract.py#L124) 只验证字符串存在/不存在，无法发现按钮禁用、2xx 无状态变化、刷新后 handoff 丢失等行为。建议增加组件或浏览器级状态迁移测试，并加入同 ID 双项目隔离夹具。

## 已确认正确的路径

- 新翻译 `approved` 会在 `BEGIN IMMEDIATE` 事务内写作者确认并调用准入，任一失败整体回滚：[writing_reference_repository.py](../services/api/app/writing_reference_repository.py#L2128)、[writing_reference_repository.py](../services/api/app/writing_reference_repository.py#L2207)。
- 准入会核对当前 translation revision、extraction lineage、结构审核、来源有效性与哈希、内容校验、当前 review、忠实度及允许状态；该核心门禁方向正确。
- 已准入译文被退回时，当前 brief 会失效，translation 回到待作者确认；历史仍可读。
- 新 PICOS 快照直接写为 `MEDICALLY_APPROVED`，不会为新路径创建审批中心待办；handoff 存储层也会校验当前 gate、snapshot、revision 和 evidence package hash。
- 跨项目临时探针未观察到读写穿透；共享 Phase 1 语料库是显式全局准入边界，不应与项目内作者确认合并。

## 验证记录

在隔离运行目录执行以下聚焦测试，共 **206 项通过**，耗时约 9.36 秒：

```text
tests.test_evidence_picos_workflow
tests.test_evidence_picos_approval_api
tests.test_writing_reference_admission_repository
tests.test_writing_reference_translation_batch
tests.test_writing_reference_translation_service
tests.test_writing_reference_repository
tests.test_writing_reference_api
tests.test_medical_writing_revision_application
tests.test_medical_writing_author_freeze_backend
tests.test_frontend_evidence_design_contract
tests.test_frontend_medical_writing_translation_batch_contract
tests.test_frontend_medical_writing_contract
```

测试通过只能证明现有断言成立；P1-1、P1-2 和 P2-2 说明其中部分断言本身固化了错误流程。

## 修复后必须完成的运行态验收

1. 5174 与 8911 构建号一致，运行时准备门通过。
2. 医学经理选择或修订后采用 PICOS 时一次完成项目确认；快照/交接不再要求第二次医学确认。
3. 历史 `in_medical_review` 可经当前 UI 一次迁移，并从审批中心待办消失；历史 `returned_for_revision` 不得假成功。
4. 旧 `approved + not_admitted` 译文可一次确认并原子准入。
5. 来源、提取或哈希变化后，旧确认仅作为历史可读，不再计入当前确认数；重新确认后才恢复。
6. handoff 在刷新、重复点击、并发请求和同包新 revision 下均以服务端状态正确恢复。
7. 用两个具有相同业务 ID 的项目验证查询、确认、失效、批次统计和审批待办完全隔离。
