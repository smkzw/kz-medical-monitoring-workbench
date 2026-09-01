# 医学监查 R4-D10 runtime Worker-02 验收记录

日期：2026-08-18  
结论：`ACCEPT_WORKER02`  
范围：D10 renderer-neutral 投影、中文受众面、分层计数、风险标记/
hotspot、Query 草稿、visibility/deep-link 与 D10→R2 handoff。不接受
Worker-03、D10 runtime 整体、R4 整体、R5/UI、服务/8911、真实项目/
模型、产品或医学写作。

## 实施与独立审阅过程

- Pi/OpenCode Go 初始实现后经两次同会话纠偏，关闭并行评价身份、局部
  Query 泄漏、非结构化句段与内部 reason code 暴露。
- 首次独立审阅拒绝：隐藏中心的成员仍进入计数/风险/受众面，且重签
  篡改测试仅因本地 hash 陈旧失败。
- CodeBuddy `deepseek-v4-pro:xhigh` 回退会话修复上述两项。第二次独立审阅
  再拒绝：“不在 hidden site”不等于严格可见 pair，CASE-085/086 wrong-scope
  成员仍会进入受众面。
- 同一 CodeBuddy 会话定向补修：可见成员必须同时属于
  `projectable_member_refs`、`projectable_site_refs` 且精确
  `(subject_stable_id, site_stable_id)` 存在于
  `projectable_subject_site_pairs`。第三次独立审阅返回
  `ACCEPT_WORKER02`。

## 已接受行为

- 所有投影、Query、版本与 R2 handoff 唯一使用
  `D10RunResult.evaluation_content_identity`，与唯一 trace leaf 一致；投影不
  重跑 evaluator。
- 隐藏 member/site 与 Query 边界相交时整份 Query 抑制；不存在局部
  Query 或隐藏引用。
- Query 使用封闭类型“依据＋发现＋行动项”句段，业务标识只进入
  `source_business_identifier`，PD 措辞固定为“请核实是否为 PD”。
- 受众主要理由为封闭映射的原生中文，不暴露原始内部码。
- CASE-085/086 保留在权威 raw ledger 中的 `7/7/9/3`，但受众成员、
  计数、marker、hotspot、Query、link、payload 全部为空/抑制，不可评价
  表述为“暂无法评价（附原因）”。
- CASE-262/265 不泄漏隐藏中心成员；只保留项目级 signal count 与非受众
  R2 lifecycle handoff。
- 重新计算 canonical Query id/content hash、R2 handoff id/idempotency key 及内部
  一致的 projection 篡改，仍被 authoritative rebuild 拒绝；不再仅依赖
  stale hash。

## 稳定 SHA-256

- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_projection.py`  
  `14af6237f2052ff323cc12cb9760aad8ab91c93b594d89d04e1b88fd5e43e017`
- `poc/medical_monitoring_ai_native_r4/tests/test_d10_projection.py`  
  `f79b71210ffc9c7c4250570b91c7d22dce4b01738cb455980f66c446505369a1`

## 决定性验证

- D10 Worker-02 + Worker-01 adjacent：`118 passed, 11225 subtests passed`。
- D09 全量相邻：`243 passed, 33 subtests passed`。
- Ruff 两文件 `All checks passed`；`py_compile` 通过。
- 独立 reviewer 对最终 SHA 首尾复核后返回 `ACCEPT_WORKER02`。
- 8911 无监听；未启动服务、未运行真实项目，未触及医学写作。

## 下一安全动作

只解锁 Worker-03：公共导出、anti-overfit/mutation/reorder/replay、static
closure、emitted-object tamper、focused/adjacent/full R4 回归与 D10 runtime 最终独立
验收。R5/UI、8911/服务、真实项目/模型、产品与医学写作继续冻结。
