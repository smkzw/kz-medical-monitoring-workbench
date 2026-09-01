# r42 v36 单项 downstream-contract transition 实施计划

时间：2026-07-31 CST  
状态：离线实施与独立验收 READY；等待 clone-only runtime 专门授权  
范围：仅 Phase 0A，不授权 clone runtime

## 已证事实

- 原 `/translation-batches/{batch_id}/retry` 只选择
  `generation_status='failed_retryable'`。
- clone 当前为 `completed_with_blocked / attempt 3`，且
  `0 failed_retryable`，所以原 retry 是 no-op：
  - 不会触及 4 个 `candidate_ready`；
  - 不会触及 15 个 `excluded`；
  - 也不能处理唯一 `fidelity_blocked`。
- 不得把目标旧项改写成 `failed_retryable` 再复用 batch retry。该路径会
  重新查询整批失败项，而且 durable executor 不消费 payload 中的
  `failed_item_ids`，不能形成可证明的单项边界。
- 目标 clone 身份（只读）：
  - batch `wref_translation_batch_ad27f97d2f06c106b0c2a158`
  - item `wref_translation_item_4dae08490b884310d35a6198`
  - batch/item attempt `3 / 5`
  - translation `wref_translation_ch_59e4ce2858f2ad9cf515c718 / r1`
  - plan `docplan_af5970d5095a4fb17590aac8`
  - integration `integration_ee761fed488f365841284463`
  - source downstream fingerprint
    `a88015cd42ee152f9942cc24c93b54579661f2d2be0809c6b3b016bc054c9f01`
  - source composite contract
    `5cf798bac7c3912a674540bb233a4866150e8026a3efff6a67b66d06cc07c65e`
  - source Hy prompt
    `hy_mt2_chapter_translation_v0_29_reference_metadata_fidelity`
  - stable code `unit_1:source_abbreviation_missing`
- 当前目标：
  - downstream fingerprint
    `c61a5e2d775c14302f3b0853ac09cc5785a230d3108e0b2f2d42cdf8aa6be79d`
  - Hy prompt
    `hy_mt2_chapter_translation_v0_30_protocol_heading_abbreviation_stopwords`
  - alignment contract
    `cms_seg_aligned_units_v36_protocol_heading_abbreviation_stopwords`

## 选定设计

不修改旧 batch/item，也不复用旧 plan/chunk/integration/candidate。新增一条
独立、显式、单项 API：

1. 请求路径同时固定 `source_batch_id + source_item_id`，并携带 expected：
   batch/item attempt、translation ID/revision、plan、integration、source
   composite/downstream contract、source Hy prompt、stable failure code，以及
   服务端当前 target downstream/Hy/alignment identity。
2. 事务内验证 source batch=`completed_with_blocked`、source
   item=`fidelity_blocked`，并核对 source item→translation→plan→integration
   的不可变链。
3. 用旧 blocked raw output 与当前确定性 fidelity gate 做无模型 preflight：
   只有当前 v36 已消除全部 failure 才允许转换；仍缺真实临床缩写时 fail
   closed。
4. 以 source plan 为 parent，确定性复制章节结构到全新的 v36 plan
   namespace/plan ID；旧 plan 原样保留。
5. 建立一个确定性、仅含一个新派生 item 的 child batch。child item 清空旧
   candidate/progress 指针，显式保存 source/target transition lineage。
6. semantic transition identity 不含客户端 idempotency key；同一 source
   revision→target contract 只能有一个 transition/child batch/item。
7. durable payload 明确携带 transition ID 和唯一 target item；executor
   只能 claim/process 该 item，不调用源 batch 的 batch-wide retry。

## restart / 精确一次边界

普通 CAS 和 immutable rows 只能防重复提交，不能证明“模型返回后、结果落库
前崩溃”不会重复调用。因此本补丁增加 transition-scoped external-call
record + state：

- 调用前先写 deterministic call intent/state=`dispatched`；
- 调用完成后写 state=`completed` 和结果 hash；
- restart 时：
  - `dispatched` 且无确定性已落库结果：终止为
    `model_call_outcome_unknown_after_restart`，禁止重调；
  - `completed` 且对应 v36 chunk/integration 已落库：只从新 v36
    immutable rows 恢复，不重调；
  - 尚未 dispatch：允许安全续作。

这选择 fail-closed，而不是在无法证明上一次调用结果时制造重复调用。

## 离线验收

- 临时 SQLite repository + deterministic planner/Hy/QC fakes。
- 模拟旧 v35 中 `VISIT/SCHEDULE` 假阳性的 blocked source。
- 证明 source batch、source items、旧 immutable rows byte-equivalent。
- 证明 child 只有一个 target item，且 plan/chunk/integration/candidate 全为
  新 v36 identity。
- 证明普通 `VISIT/SCHEDULE` 通过，真实 `ECG` 缺失仍 fail closed。
- 证明 duplicate request、duplicate executor、restart-safe reuse 不增加模型
  调用或业务记录。
- 证明 restart unknown-outcome 分支终止且不重调。

通过 Codex 聚焦回归后，再按 workflow guard 发起一次独立反证审阅。只有
READY 才形成 clone-only runtime 申请；本计划不授权运行 clone。

## 最终离线结果

- 产品/测试改动仅限：
  - `packages/contracts/workbench_contracts/models.py`
  - `services/api/app/writing_reference_translation_batch.py`
  - `services/api/app/main.py`
  - `tests/test_writing_reference_translation_batch.py`
- 独立 transition 建立 immutable intent、mutable state、单项 child
  batch、全新 v36 plan/chunk/integration/candidate identity，以及
  transition-scoped external-call ledger。
- 首轮反证发现 P1 lease takeover 竞态：旧 owner 的 stage CAS 静默失败后
  仍可调用模型。已修复为显式 `_OwnershipLostError`，并在 call-intent
  事务提交后、provider 调用前再次核对 durable ownership。
- 补齐两种 takeover 交错、persisted chunk settle、pre-dispatch restart、
  child retry rejection 和 OpenAPI response contract 用例。
- Codex 全量相关回归：`258 passed`；两位参与者同会话复审及
  Pi/Alibaba 会商主席均为 `READY`，无遗留 P0-P4。
- `model_call_outcome_unknown_after_restart` 保持 terminal/non-retryable：
  在没有 provider-side idempotency/result lookup 时，这是防重复调用的
  有意 fail-closed 停止条件，不自动重开。

## 当前停止点

离线阶段完成。不得自行启动服务或 POST。下一安全动作仅是在用户专门授权后，
按 `runs/MW_R42_V36_SINGLE_ITEM_READY_AND_CLONE_AUTH_REQUEST_20260801_0020.md`
执行一次 clone-only、单项 transition。
