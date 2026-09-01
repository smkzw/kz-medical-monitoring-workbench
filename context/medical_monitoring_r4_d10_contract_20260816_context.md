# Task Context: medical_monitoring_r4_d10_contract_20260816

Created: 2026-08-16 03:30:02
Objective: 冻结R4-D10项目/跨中心安全与疗效信号聚合的owner边界、typed合同、挑战矩阵与证据要求，保持8911停止且保护医学写作与真实项目
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_r4_d10_project_signal_slice_contract_v0_6_20260816.md`, SHA-256 `c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95`：第五轮 revise 后的当前固定复核对象；不是已冻结合同。历史固定 SHA：v0.1 `9be8d4b6...34d8d09`，v0.2 `92bc5a29...ca479b`，v0.3 `b798d5ac...f55e135`，v0.4 `2c1f8dbe...3612f9b`，v0.5 `041052a7...275add3`。
- `context/medical_monitoring_r4_d10_external_pattern_decision_20260816.md`, SHA-256 `93475984dcf14e3d24aefce5eec6709f78b86cd39240045e4d551b21a9dba511`：监管/开源模式核验与采用边界。
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`：第 10-11、14、17 节为产品/医学语义边界。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`：R4 顺序与 D10 解锁边界。
- `reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md`：D09 冻结 owner/typed/measure/coverage/lineage/Query 边界；D10 不得回写。
- `context/medical_monitoring_r4_d09_contract_acceptance_record_20260814.md` 与 `context/medical_monitoring_r4_d09_runtime_final_acceptance_20260816.md`：D09 接受范围与未解锁边界。
- 外部权威只作为方法证据：ICH E6(R3) Step 4 Final Guideline、ICH E2F、FDA 2013/2023 risk-based monitoring guidance；URL 与采用限制记录于 external pattern decision。
- 当前文件系统是真相；任何先前模型结论都不是接受证据。

## Scope

- In scope：对当前固定 v0.6 进行独立、反证优先的临床/数据/工程合同审阅；验证 owner、五类 signal、expected-set、成员/分母/分析集、跨中心可比性、盲态/visibility、安全/疗效方法门、五类 L1、lineage/change cause、Query/R5、312-case 互斥 primary 配额与 mandatory-attack 子配额、非 LLM 锚点；报告可复现矛盾和最小精确修订。
- Out of scope：修改合同或任何源码；artifact/catalog/oracle/registry/generator/runtime；R5 UI；启动 8911/服务；真实项目/患者数据/模型运行；医学写作；系统安全设计/测试；正式临床、监管、获益-风险或治疗效果结论。
- Allowed output：只返回审阅 handoff，由 runner 写入 `runs/codex-subagent_medical_monitoring_r4_d10_contract_20260816.md`；审阅者不得用工具写任何文件。

## Success Criteria

- 固定 v0.6 起止 SHA 一致，审阅期间无目标文件漂移。
- 明确给出 `ACCEPT_D10_DRAFT_FOR_REVISION_FREEZE` 或 `REVISE_D10_DRAFT`，不得把 draft/runtime/UI/真实项目混为接受。
- 每个 revise 项给出：优先级、可复现反例、被违反的不变量、精确合同修改位置/语义与建议挑战用例。
- 必须尝试证伪：owner 越权、D09/个体重复计数、initial full 假变化、方法/coverage 变化冒充临床变化、中心污名化、盲态泄露、疗效 estimand 越权、正式安全信号越权、分母/coverage 漏门、重哈希/Unicode/工程引用注入、模型多数票越权。
- 至少一个非 LLM 锚点：真实 SHA、结构/闭集交叉检查或可执行静态探针；不以审阅者自信替代证据。
- 8911 结束仍停止；无真实项目、产品、医学写作或源码修改。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- 不得把 FDA/ICH 指南的监查原则扩张为某一统计方法或阈值的监管强制要求。
- 不得把项目内描述性 safety/efficacy 监查结论写成正式安全性信号、确证治疗效果或最终获益-风险结论。
- 不得仅因低频、小样本或项目总体率低而隐藏高风险个例；也不得将单例或离群值自动升级为中心/项目系统性结论。
- 不得读取 `/Users/smkzw/Documents/康哲项目资料/MG-K10/SAR` 等五个真实项目目录。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, malformed output, or a stale/incomplete catalog must be recorded and followed by one real route attempt. Explicit user-selected routes are not blocked merely because the catalog does not list them; only a missing executable or native transport boundary may stop before that attempt.

## Loop Log

- 2026-08-16 03:30:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-16: D09 runtime final acceptance re-anchored; 8911 observed stopped. Bounded external verification selected traceable drill-down/data-batch comparison patterns from FDA/ICH and MIT-licensed SafetyGraphics/clinDataReview, without adopting their R/Shiny runtime.
- 2026-08-16: Codex produced fixed v0.1 contract SHA `9be8d4b6...34d8d09`; D10 runtime remains locked pending independent contradiction review and Codex freeze gate.
- 2026-08-16: Independent Luna/max verifier returned `REVISE_D10_DRAFT` with 15 executable gaps: legal matrix, exact gates/schemas, evaluation identity, Query/projection binding, safety/efficacy contexts, baseline/change state, R2 prior/action, D09 descendant double-counting, completeness precedence, per-site comparability, numeric invariants, visibility, expected-set gates, model-evidence binding and quota arithmetic.
- 2026-08-16: Codex produced v0.2 closing those 15 gaps and corrected the mutually exclusive primary quota floor from 240 to 312; same-session targeted review is required before freeze.
- 2026-08-16: Same-session v0.2 review returned `REVISE_D10_DRAFT` with 13 residual executable gaps. Codex produced fixed v0.3 SHA `b798d5ac...f55e135`, adding per-object project scope, mode/visibility identity, R2 lineage/change binding, source-recomputable time, treatment assignment identity, visibility algebra, full Query identity, typed audience templates, exact ModelEvidence and mandatory-attack quotas.
- 2026-08-16: Same-session v0.3 review returned `REVISE_D10_DRAFT` with six narrow residuals. Codex produced fixed v0.4 SHA `2c1f8dbe...3612f9b`, closing top-level paired source/scope/mode/cutoff binding, cutoff-advance first-positive create, origin partition algebra, site/subject deep-link eligibility, Query redundancy identity and ModeContract change-cause handling.
- 2026-08-16: Same-session v0.4 review returned `REVISE_D10_DRAFT` with five residuals. Codex produced fixed v0.5 SHA `041052a7...275add3`, adding measure-origin paired provenance and mixed-origin mapping, strict cutoff advance decision, closed deep-link target kinds and sorted-unique Query redundancy identity.
- 2026-08-16: Same-session v0.5 review returned `REVISE_D10_DRAFT` with two residual propagation gaps. Codex produced fixed v0.6 SHA `c613bb7c...7deff95`, making cutoff advance derived-only with non-data mixed-change exclusion and binding all deep-link eligible sets to projectable-set algebra.
- 2026-08-16: Same-session v0.6 accepting pass returned `ACCEPT_D10_DRAFT_FOR_REVISION_FREEZE`; fixed SHA and 8911 stopped state held. Codex freeze gate accepted `FROZEN_R4_D10_CONTRACT_V0_6`. Artifact/runtime remain locked; task paused without loss before catalog construction.
