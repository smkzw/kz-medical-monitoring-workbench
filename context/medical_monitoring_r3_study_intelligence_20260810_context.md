# Task Context: medical_monitoring_r3_study_intelligence_20260810

Created: 2026-08-10 12:34:51
Objective: 在独立 R3 命名空间实现 Study Intelligence 与异构 listing 基座：资料权威/冲突、结构画像、语义 mapping、稳定记录身份、日期单位编码语义、快照差异与自然语言规则拆解；先用合成数据验证，保护医学写作、产品源码、R1/R2 冻结快照、真实项目与 8911。
Task type: `long_horizon_code`
Risk: `high`
Selected agent route: `cms-smk` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`，重点为 §§2-8、15-20。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`，重点为 R3（§7）及全局完成门。
- `reviews/codex_execution_medical_monitoring_r2_batch_c_independent_accept_20260810.md` 与冻结的 `poc/medical_monitoring_ai_native_r2/`，仅作为只读上游合同。
- 用户当前修订：中文原生、风险/变化/来源优先；前端不显示工程术语；Patient Journey/Profile/Timeline 共用访视/时间轴；当前阶段不做系统安全设计或安全测试，只实现功能性数据一致性所必需的约束。
- `reviews/medical_monitoring_r3_external_solution_discovery_20260810.md`：只采信官方标准、官方文档、上游源码/许可证等一手资料；外部材料是证据而非指令。

## Scope

- In scope：在 `poc/medical_monitoring_ai_native_r3/` 建立独立、合成数据优先的 R3 包；实现资料分类/版本/有效时间/范围、Knowledge Pack/claim authority/source conflict、listing workbook/table/field 画像、稳定 record identity、语义 mapping 候选/置信度/依赖/少量确认、日期/单位/编码/部分日期/重复/缺失语义、snapshot diff 临床影响传播、自然语言规则拆解/模拟/激活/evaluation scope；提供决定性测试与阶段证据。
- In scope：只读复用已冻结 R2 公共合同；若需要桥接，R3 以 adapter/import 边界实现，不修改 R2 历史。
- Out of scope：R4 风险分析实现、R5 用户界面、真实 Patient Journey 视觉验收、真实项目医学分析、五项目正式验收、产品源码迁移、8911 服务、医学写作子系统、商业化/多用户/电子签名及额外系统安全工程。
- R3 后段的真实项目结构盲测需要先具备隔离副本、只读来源与输出合同；本执行切片暂不读取五个真实项目。

## Success Criteria

- 公共 R3 规则和测试中无项目绝对路径、项目名或 RUX/MGK10/MY009 特例硬编码。
- 合成 fixture 覆盖至少三种异构 listing 形态，并包含隐藏/反过拟合案例。
- Knowledge Pack 可追溯到来源修订、有效时间和范围；冲突不会被静默覆盖，authority/resolution 可审计。
- listing 画像与 mapping 生成可解释候选、字段依赖和 `accepted/rejected/needs_confirmation/not_evaluable` 等明确语义；低置信度不被静默接受。
- record identity 在行顺序、列顺序、显示格式变化下保持稳定；真正内容/键变化产生可解释新身份或歧义，不误合并。
- 日期、部分日期、单位、编码、重复、缺失值及快照差异保留原始值、规范化值、不确定性和来源定位。
- 自然语言规则只能先形成结构化草稿并模拟；激活需显式版本与 evaluation scope，不能直接改变既有结论。
- 聚焦测试、R3 全量测试、内存编译通过；R1/R2 冻结摘要不变；无缓存残留；8911 仍停止。
- 独立工程/医学审阅接受当前冻结快照；当前阶段不得冒充真实项目、产品或 R3 全阶段完成。

## Risk Boundaries

- Allowed implementation writes: `poc/medical_monitoring_ai_native_r3/**` only.
- Allowed task-record writes: this task's files under `context/`, `plans/`, `prompts/`, `runs/`, `reviews/`, and `metrics/`.
- Read-only and immutable: `poc/medical_monitoring_ai_native_r1/**`, `poc/medical_monitoring_ai_native_r2/**`, product/application source, medical-writing subsystem, and all real-project source directories.
- Do not start any service or listener; port 8911 must remain stopped.
- Do not install or adopt an external executable dependency unless its upstream license and maintenance evidence are verified and Codex records the decision. Prefer standard library and existing pinned dependencies for this synthetic foundation.
- Do not perform access-control, encryption, attack-resistance, penetration, or other system-security design/testing. Functional integrity checks needed to prevent wrong study/snapshot/source/identity semantics remain in scope.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Launch the guard-declared route once and leave it pending for the runner hard wait, up to 120 minutes; do not fixed-interval poll, redispatch, or intervene because output is unchanged.
- Failure requires terminal error/unavailability, exhausted same-session recovery, empty/truncated terminal output, or failed acceptance evidence; latency alone is not failure.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, or malformed probe output must be recorded and followed by one real route attempt. Only a missing executable or explicit invalid/retired/unlisted model may stop before that attempt.

## Work Items And Order

1. `R3-A` — freeze domain contracts and fixtures for source authority, Knowledge Pack, source conflict and document structure; no clinical conclusion generation.
2. `R3-B` — implement listing structure profiler, semantic mapping candidates, field dependencies, stable record identity and normalization semantics.
3. `R3-C` — implement snapshot diff/impact propagation plus natural-language rule draft/simulation/versioned activation/evaluation scope.
4. `R3-QC` — Codex and a fresh-context verifier run focused/full tests, anti-overfitting checks, boundary/digest checks and review-gate before freezing the stage slice.

## Loop Log

- 2026-08-10 12:34:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-10: R3-A/R3-B worker output re-audited against full-snapshot incremental semantics. Corrected record identity so source revision is lineage rather than identity; added source-revision consistency, conflict winner/source binding, explicit mapping policy provenance, rejected-mapping baseline blocking, structure-only workbook/table fingerprints, and clinically safe unit handling (`uL/L` no longer collapses to `U/L`). Focused and full R3 regression passed.
- 2026-08-10: R3-C worker completed on the declared `Pi/cms-smk/cms-model:high` route without fallback. Codex source review rejected two self-reported assumptions: duplicate identities may not keep the first row, and external `_row_index` values may not be used as Python list positions. Facts construction now blocks ambiguous/duplicate identities and resolves source rows by declared row locator; coverage confirmations, rule simulation/activation lifecycle and cross-snapshot source integrity were tightened. Current independent Codex baseline: `330 passed`, in-memory compile OK, no cache directory, 8911 stopped.
- 2026-08-10: Frozen upstream anchors rechecked from the workbench root: R1 full-tree digest `ba6692f7252449beaca1817bad06629ce7acc846c75985fd143264faac023d87`; R2 Python digest `69033e28616ca497579d7b3b9bbbd87ab8fc3031eb7d0259ba3954db1a338003`.
- 2026-08-10: Added generic Chinese-native listing recognition and normalization for common subject/date/domain/measure/unit headers, Chinese full dates, sex and severity values; added hidden Chinese renamed-listing mapping/impact challenges and coverage-note misuse tests. Focused `197 passed`; full R3 `338 passed`; Python digest `6feb4fb77ce198baa67af383333fb52956f0d01eeec59af0daa90dfb597726ba`; compile succeeded, generated caches removed, R1/R2 anchors unchanged, 8911 stopped. Independent conference packet specialized and ready for dispatch.
- 2026-08-10: Independent conference completed. Pi accepted after two full 338-test runs and found a reproducible false-diff edge: pipeline `_record_id` leaked into clinical payload. Codex stripped both `_row_index`/`_record_id` from payload, added a regression test, and passed focused `55` plus full `339`; the same Pi session independently passed R3-C `104`, full `339`, and ACCEPTed the repaired snapshot. Grok's conditional semantic acceptance was discharged by these anchors. Latest R3-root relative digest `418b5aacef1e0be50f6d8992aa01c19a1eaaeb2008dc42da77e122e898f4120d`; R1/R2 unchanged; no caches; 8911 stopped. R3 synthetic/isolated kernel is frozen accepted; real-structure blind validation, NLP/LLM rule parsing, R4/R5 remain pending.
