# 医学监查 R8-0 联合准入合同接受记录

日期：2026-08-31  
状态：`CONTRACT_FROZEN_AND_INDEPENDENTLY_ACCEPTED`  
范围：R8-0 合同文本；不等于 R8-0 readiness 或任何真实验证

## 接受对象

- 合同：`reviews/medical_monitoring_r8_gate0_source_admission_anti_overfit_contract_v0_1_20260831.md`
- 首轮会商前摘要：`a19fd612c758f38107c937c93f44f1d693e3a68f6bea3f4200ee212d8a95158b`
- 第三轮独立接受的实质条款摘要：`f25f53b035b0f880b62dfec73051746b00f5249b5e20b954fdec2658e659b1b0`
- 最终文件摘要：`19a855bf51e2ed5cecd3f294cdeed823bc972a01ce84aaa9095a29089e344e74`

最终摘要与第三轮实质条款摘要之间仅更新合同顶部和 §15 的处置标签/下一步说明；门禁、状态、职责、测试和禁止声明条款未再改变。Codex 对该处置性变更承担最终接受责任。

## 执行与会商

1. governed execution `mm_r8_gate0_contract_draft_20260831`
   - 三个独立工作项分别起草 source-admission、anti-overfit/harness responsibility、real-app/notification/§15.4/acceptance matrix；
   - `Pi/openai-codex/gpt-5.6-luna:max`，三项均终态成功，无 fallback；
   - execution audit `ok=true`。
2. fresh-context conference `mm_r8_gate0_contract_review_20260831`
   - `Pi/cms-router/minimax-m3:xhigh`；
   - 同一 session `01a055d7-e931-7000-90f2-720edde28db7` 连续三轮，无 fallback；
   - Round 1：`REVISE`；
   - Round 2：所有原 P0/P1 关闭或按用户范围降级，提出六项窄修订；
   - Round 3：N1/N2/N4/N5/N6 关闭，N3 按 UI 偏好与模型 binding 无关而拒绝，最终无 P0/P1/P2/P3 合同阻断，支持 `CONTRACT_FROZEN_AND_INDEPENDENTLY_ACCEPTED`。

ChatGPT Web advisory 只完成 dry-run；`codex-with-chatgpt` skill 入口缺失，且当前阶段禁止浏览器，因此未启动浏览器。按 route fallback contract 继续 declared executable panel，不影响正式会商证据。

## 关键纠偏

- 项目 identity 增加不可复用 id、binding digest、撤销/重新准入引用边界；未引入 HMAC 或密钥系统。
- 目标 macOS `source_access_profile` 必须在 synthetic shadow root 证明只读、写事件可观察及监测失效可识别；不得对真实来源做写探针。
- 所有命名 digest 必须冻结字段集合、缺省值、排序、规范化、序列化器和 replay；output manifest 使用 revision chain。
- raw→envelope→parsed→validation→adjudication→disposition 以 artifact id + SHA-256 绑定；未引入 BLAKE3/CAS/SQLite 强制方案。
- Codex/开发者不得补项目医学答案；unknown/null/not_applicable 分离；validator 不能以字符串相似度修正医学候选。
- 隐藏挑战冻结 capability × mutation × anchor × unit coverage matrix；waiver 留在 expected 且不计通过。
- 医学风险分级候选与 QA P0-P4 完全分离。
- G6 ego(lite) 仅用 mock/recorded adapter；真实模型仍禁止。
- full/incremental 必须冻结并验证 `source_scope_spec` 兼容性。
- 写事件、terminal status、通知路由、§15.4 声明、缺陷传播和 clean-streak 均有 fail-closed 语义。

## 明确未接受

- 未读取、列举、`stat`、哈希、搜索或打开 P1..P5 真实项目根；
- 未调用医学监查内置真实 VLM/LLM 或任何真实项目模型；
- 未启动产品服务、8911/5174/8984 或产品浏览器；
- 未运行真实备份、迁移、回滚、卸载或 §15.4；
- 未验证真实项目医学质量、泛化、Patient Journey、中心/试验看板或视觉；
- 未修改医学写作子系统；
- 未接受 R8-0、R8、商业化、生产或监管声明。

## 下一安全动作

只进入 G2 `RUNTIME_LAUNCH_READY_SYNTHETIC`：

1. 冻结并实现 canonical digest 表、source/output manifest schema 与 replay；
2. 冻结并实现目标 macOS `source_access_profile` 的 synthetic shadow-root 证据；
3. 使用 synthetic/offline fixture 验证依赖闭包、start/stop/restart、一键入口和无手工端口；
4. 形成 G2 独立接受后再进入 G3 通知路径决定与 G4 synthetic §15.4；
5. G7 前继续禁止任何真实项目访问；G8 前禁止真实项目语义进入模型；G6 前禁止产品浏览器。
