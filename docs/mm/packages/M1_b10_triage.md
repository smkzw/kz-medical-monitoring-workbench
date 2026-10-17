# M1/B10 三用例判定（2026-10-18）

## 用例1: test_legacy_glm_cohort_can_never_enter_a_new_draft
- **判定：代码行为变化（非断言陈旧）**
- 根因：状态机专项T系列修复改变了`_completed_candidates`对legacy cohort的处理路径——mock返回AssertionError对象进入`_draft_payload`而非被门禁拦截。
- 处置：M2将删除该门禁流程（简化为确定性识别+单模型分类），此用例将随M2代码一起删除。M1只记录。

## 用例2: test_degraded_confirm_requeues_failed_verifier_shards
- **判定：测试fixture不完整（非代码回归）**
- 根因：mock的ai_repository是SimpleNamespace，缺少`list_jobs`方法——R42修复（degraded confirm重排）新增了对`list_jobs`的调用，测试mock未同步。
- 处置：修复测试mock补`list_jobs`方法。M1内修。

## 用例3: test_pipeline_submits_existing_harness_jobs_with_glm_identity
- **判定：断言陈旧**
- 根因：单源投影改造后`generate_candidates`返回的dict不再含`confirmation_status`键（由`mapping_candidate_routes`层添加）。
- 处置：更新断言为检查实际返回的键（`state`等），或在route层测试。M1内修。
