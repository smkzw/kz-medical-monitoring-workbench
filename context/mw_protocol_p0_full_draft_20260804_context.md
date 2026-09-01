# Task Context: mw_protocol_p0_full_draft_20260804

Updated: 2026-08-04 11:35 Asia/Shanghai  
Objective: 修复研究方案全文初稿为空白的问题，建立独立 AI 全文候选、源绑定、幂等持久化、整体采纳和 Word 实质内容闸门，并在隔离运行时用可见浏览器验证完整正文。
Task type: `long_horizon_code`; risk: `high`.

## Source of truth

- `/Users/smkzw/.codex/AGENTS.md`（全局方法学、执行/会商/路由、OCR/翻译闸门、token saving）。
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`。
- `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/AGENTS.md` 及 `frontend/AGENTS.md`。
- r12 无损检查点：`/Users/smkzw/Documents/AI Cache/Codex x Hermes/runs/MW_PROTOCOL_P0_NO_LOSS_PAUSE_20260804_R12.md`；恢复上下文：`context/mw_protocol_p0_resume_20260803_context.md`。
- 当前产品源码、测试、实际 DOCX 与工作树；不以已删除父 Session 的逐条对话为证据。
- 已核对的空白 Word：`records/active_slices/medical_writing_authoring_journey_20260715/browser_qc/pi_deepseek_engineer_role_20260803/r1/engineer_r1/asthma_p1/asthma_p1_draft_preview.docx`。

## Scope and non-negotiables

In scope: Protocol P0 全文初稿生成链、证据绑定/AI 输出契约、持久化 executor、候选文件完整性、明确整体采纳、CAS/幂等/重启复用、可见候选审阅、Word 导出实质正文闸门、独立 LLM/OCR/翻译/翻译辅助 AI 配置及聚焦验证。  
Out of scope: Synopsis、CSR、最终多模型/多角色上线矩阵；不得重跑冻结的分诊、下载、preparation、OCR、全量翻译、attempt 2/3、4 candidate-ready、15 excluded 或既有 immutable fidelity-blocked row；不得触碰并发医学监查任务或稳定 PID 28472/8900。

## Acceptance criteria

1. AI 只能返回严格 `protocol_full_draft` 结构：请求章节 ID 按序且唯一、每章实质中文正文、逐章 evidence span 绑定、`needs_medical_confirmation=true`；标题/Markdown/占位符/泛化“不适用” fail closed。
2. 生成不改工作副本；候选保存为校验过的 JSON，durable job 只存 locator/digest；用户明确整体采纳后逐章 CAS 写入，重复请求/重启/重复 worker 复用确定性分批 artifact，不重复模型调用或写入。
3. 文档身份、版本、StudyDefinition 绑定、来源和路由身份变化会阻断采纳；旧正文、旧审计与不相关项目保持不变。
4. 适用的 greenfield/template 正文章节未达到 80 字符实质正文时，`draft_preview` 和 `approved_final` Word 导出均阻断；原始 source-backed DOCX 章节保留无损导出路径。
5. 前端展示完整候选章节内容、证据数量和 rationale，用户先审核再采纳；不把标题骨架或旧空白 Word 计为通过。

## Completed evidence

- 已定位旧链：`medical_writing_protocol_template.py::_project_chapter_body_draft` 在无确认事实时返回空，`medical_writing_greenfield.py::_build_greenfield_document` 把空 `initial_text` 写入正文；UI/harness 只有单章节候选，因此旧“全文”Word 实际约 165 段、156 个标题、约 2.3k 字符，不能称完整正文。
- 已新增 `AiTaskType.PROTOCOL_FULL_DRAFT`、PromptRegistry/执行策略/runner 严格契约及一次修复重试；新增 `medical_writing_full_draft.py` durable service/executor、分批确定性 chunk artifact、candidate JSON、显式 adopt/CAS/审计边界；main 注册三条 API；前端生成/恢复/候选审阅/采纳状态；repository export gate。
- 原始 DOCX source-backed sections 在 gate 中保留无损导出，greenfield/template 空白正文仍被阻断。
- 聚焦通过：`python3 -m unittest tests.test_medical_writing_full_draft -v`（4/4）；`tests.test_ai_gateway tests.test_ai_execution_policy tests.test_ai_task_runner`（102/102）；`tests.test_medical_writing_greenfield_runtime`（18/18）；受影响真实项目/内容质量/绑定/冻结/表格测试（16/16）；`npm run build` 成功（Vite 1951 modules，只有既有 chunk-size warning）；全量 py_compile 通过。
- 新增测试确保标题骨架 Word 导出被阻断、source-backed raw DOCX 仍可导出、worker restart/reclaim 复用分批 artifact（fake runner calls 不增加）、重复采纳只 replay。
- 已重新核对独立 AI 角色底座：`independent_ai`、`ocr`、`translation_body`、`translation_support` 已有独立 profile/binding、凭据隔离、PaddleOCR 专用模型白名单及 oMLX 角色路由；当前仍需补齐并验证 LLM/翻译辅助的 thinking 开关与 reasoning 强度的持久化及实际 envelope 传递。
- 首次隔离可见浏览器探索：临时 API `8913` + Vite `5187`，稳定监查运行时 `8900`/PID `28472` 未触碰；创建了 `CMS-PNH-209 · 阵发性睡眠性血红蛋白尿 · III期`（临时 project `proj_user_2323be9d21e4`）。自动 ClinicalTrials 公开检索进入失败终态；随后用户可见导航及点击完成 framing commit（`impact-preview`、`stages/framing/commit` 均 200），journey revision 进入 6。
- 该探索发现真实 workflow race：研究/预填充仍在运行时直接提交第一步收到 `409 expected revision 3, current 4`；刷新并返回“医学写作”后可见提交成功。此项暂按 P1/P2 候选记录，尚未修复或计入通过。

## Known residuals / next safe actions

- 尚未完成真实独立 AI 全文及 Word 证明。下一安全动作是先补独立角色 thinking 配置契约，然后沿同一隔离运行时可见点击继续 PICOS→语料准入→全文生成→候选审核→整体采纳→Word 解压/读取/渲染；若自动检索失败，仅允许在可见界面记录项目特异性例外放行并保留审计。
- 本轮目标配置要求记录为：LLM 与翻译辅助 AI = DeepSeek `deepseek-v4-flash(max)`；OCR = 官方 PaddleOCR-VL-1.6；正文翻译 = oMLX `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`。隔离探索当前复用的临时 Qwen 配置仅用于流程定位，不是目标配置证明；未启动 OCR/翻译或下载任务。
- 真实 provider/AI 输出、Word 全文完整性、引用/目录/交叉跳转和用户角色矩阵未验收；不能报告任何 P0–P4 连续清零或上线 accepted。
- `tests.test_medical_writing_template_upgrade` 当前存在独立的既有 ProtocolSection completion_status fixture 验证错误（与本次全文契约/导出 gate 无因果证据），不修改其范围。

## 2026-08-04 continuation evidence (11:35)

- Role settings are now wired end-to-end: the visible UI persisted DeepSeek `deepseek-v4-flash` for `independent_ai` and `translation_support` with thinking enabled and selectable reasoning intensity; OCR remains the official PaddleOCR-VL-1.6 profile and body translation remains the oMLX Hy-MT2 profile. The provider envelope accepts the role defaults and the task runner freezes them into the durable profile.
- A bounded stale-preparation repair was added. An unexpected downstream exception in `resume_waiting()` now persists a truthful retryable failure instead of leaving the journey indefinitely in `preparing`; a read-only `status()` reconciliation converts a terminal preparation batch left in `preparing` to an auditable failed state without downloading, OCR, or retrying work. Focused pipeline/OCR/gateway regression: 119 passed; full-draft/greenfield/role/frontend contracts: 53 passed; `py_compile` and frontend build pass.
- In isolated visible Playwright runtime API `8913` + Vite `5187`, project `proj_user_414af710ad8e` reached a preparation failure caused by the intentionally strict OCR/provider identity and Paddle remote-outcome gates. Expanding the visible failure details exposed `从已完成原文继续`; clicking that button reused the completed preparation and created exactly one translation batch, now durably processing via the configured oMLX route. No API/backend click was used for this recovery action.
- Read-only runtime evidence at 11:35: translation batch `wref_translation_batch_151ffa90b610e62a45f8e186` is `running`, durable job `mwjob_ad8345a3d10f1ed2cd44e0b7` is leased with progress `2/20 items processed`; no stable port 8900/PID 28472 or frozen r42/v36/ready/excluded data was touched.
- This is still exploratory runtime evidence. No substantive full Word has yet been downloaded, inspected, or rendered; no tester round or consecutive P0-P4 clean claim has started. The earlier duplicate fact-turn 409 remains an open race candidate and is not silently counted as fixed.
- At 11:48 the visible runtime had completed the first 15/20 translation items and was processing the next document-planning item. The two NCT03907878 items then failed closed with `document_plan_failed` and the persisted root code `flash_planner_structural_failure` / `response_model_mismatch`; the worker advanced to NCT03580356 without duplicate retry. The adapter now preserves the observed response model (or an explicit missing value) in the immutable stage record instead of replacing it with the requested model; the focused upper-layer wiring suite is 28/28 after this change. The running isolated process still uses the prior code until its terminal state and controlled restart.
- At 12:00–12:03 the same visible batch remained `running` at 17/20 projected items; the durable lease continued renewing and no second worker or retry was created. Read-only process sampling showed the active API thread waiting in TLS/proxy I/O for the NCT03580356 DeepSeek planner call, so the job was left pending under its lease. The durable progress projection was confirmed to count only successful/excluded states (`2/20`) while the user-visible projection counted processed states (`17/20`). A source-only fix now counts every non-pending/non-running item, including `failed_retryable`, as processed; its new deterministic regression passed 1/1. This fix is not hot-loaded into the current worker and will be verified only after a natural terminal state and controlled restart.

## Immutable boundaries

- 不重放或改写 r42/v36/ready/excluded/历史 immutable row；不启动或干扰医学监查运行时；不运行 OCR/下载/翻译/分诊/失败项。
- 允许写入：本产品源码、其聚焦测试、当前任务 `context/`、`runs/`、`reviews/`、`metrics/`；临时运行时必须在隔离目录且可删除/回滚。

## 2026-08-04 continuation evidence (12:40+)

- The visible authoring page exposed a lineage mismatch: the active journey had advanced to snapshot `wref_search_9e730dd999fdc1d63b81`, while the earlier failed pipeline/translation batch remained immutably bound to `wref_search_3bbd439b662cf26d8b1c`. The current snapshot had no preparation artifacts; read-only SQLite confirmed the old preparation/translation rows were unchanged.
- Before Protocol preparation existed for the new locked snapshot, opening `结构与译文确认` leaked the raw `KeyError` `'proj_user_414af710ad8e/wref_search_9e730dd999fdc1d63b81'`. The backend now converts only the missing-preparation lookup into an actionable fail-closed `ValueError` telling the user to start Protocol preparation in `文档与解析`; the focused translation tests pass 2/2. Missing snapshot and non-terminal preparation errors retain their original semantics.
- The user-visible `文档与解析` path was used once to start a new preparation batch for the current snapshot (batch `wref_prep_dd4cc0d007d58c9c9c94b4b7`). This is a new snapshot lineage, not a retry of the old failed batch: the old batch `wref_prep_405155ce662391a6cdd8789a` and old translation batch remain immutable and untouched. The new batch is bounded at 8 active public Protocol items plus 4 deferred items; read-only status later showed 7 prepared, 1 running and 4 deferred.
- The running current batch pins `PaddleOCR-VL-1.6` from the OCR role at extraction start. No direct API click or database mutation was used; the only transition was the visible Playwright click on `开始批量准备`.
- A missing user-facing stage boundary was fixed in `ReferencePreparationBatchPanel.jsx`: when a batch reaches `awaiting_stage_admission`, a visible idempotent `准入下一阶段（n）` button calls the existing `/advance-stage` route; the label/status and focused frontend contract now cover this path. This prevents a manually started bounded batch from becoming stranded when the parent legacy pipeline snapshot differs.
- `npm run build` remains green after the disclosure/advance-stage UI changes; focused frontend preparation contract tests pass 3/3. The isolated API is intentionally not restarted while the current OCR preparation call is running, so the actionable missing-preparation source fix is pending controlled post-terminal verification.

## Current safe next action

Leave the current visible preparation batch pending until its natural terminal state. Then, without restarting or duplicating the worker, use the visible stage-admission button for each deferred stage, review any OCR/content blockers, and only after a terminal preparation state verify the new actionable preview error and continue through structure/translation/corpus/full-draft. The old 3bb snapshot lineage and its failed translation items remain excluded from retry unless a later explicit, source-bound recovery proves it is the only safe path.

## 2026-08-04 lossless pause checkpoint (current bounded step)

- Scope remained isolated to Protocol P0 and the current visible project `proj_user_414af710ad8e`; no stable service, frozen r42/v36/ready/excluded rows, medical-monitoring runtime, or historical lineage was changed.
- Current-snapshot evidence: locked snapshot `wref_search_9e730dd999fdc1d63b81`; translation batch `wref_translation_batch_8488879d054d781b86ae1916` is terminal `completed_with_blocked` (attempt 3, 242/242), with 49 `candidate_ready`, 28 `excluded`, 165 `fidelity_blocked`, and 0 failed items. Prior failed/repaired rows remain immutable and untouched.
- The bounded product repair adds a visible structured-design confirmation editor to the PICOS step: one-click suggestion from current study facts, explicit confirmation controls for randomization/blinding/comparator/assignment/center, explicit `待确认/不计划/计划` flags for adaptive, crossover, OLE, treatment switch, sample-size re-estimation, interim, SRC, and DMC, and a visible dosage-form field. Backend remains fail-closed.
- Real headful Playwright evidence: the visible suggestion was applied; product exposure `systemic`, dosage form `注射剂`, and center model `多中心` were selected and saved through the UI; structured design values were persisted and impact confirmation completed. Read-only journey ended at revision 33 with `framing_complete=true`, `picos_complete=false`, stage `picos` (`PICOS设计进行中`); no full draft or Word was produced.
- The latest visible prefill call returned an unsupported composite top-level shape (`claim_bindings, clinical_tradeoffs, evidence_gaps, preview, rationale, recommendation_role, structured_value`). It remained `partial`, with no durable AI run or design-package recommendation; the response was rejected rather than coerced.
- Verification: `npm run build` passed (Vite 1,951 modules; only the existing large-chunk warning). Focused frontend contract focus passed 3/3. A transient HMR 500 during reload cleared after full rebuild/reload. No OCR/download/triage/retranslation/attempt-2-or-3 rerun was initiated in this bounded step.
- Remaining blocker: after visible structured-fact confirmation and stage flow, the completion response did not expose why the journey computed `picos_complete=false`. Full-draft/content-quality/Word/rendering and the serial two-role multi-model matrix remain unstarted and must not be reported as accepted.
- Next safe action on resume: read-only inspect the saved PICOS draft, `missing_required_fields()`/completion response, and exact stage-completion API error; repair only that bounded state contract, then re-open the current-snapshot assembly plan. Treat `systemic`/`注射剂`/`多中心` as explicit test inputs, not sourced clinical evidence.
- Pause boundary: close isolated browser session 47098, Vite session 5490, and API session 87734 after recording; stable API port 8900/PID 33143 remains running and untouched.
