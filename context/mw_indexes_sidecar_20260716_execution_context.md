# Execution Context: mw_indexes_sidecar_20260716

Created: 2026-07-16 23:52:03
Objective: 为医学写作Word目录与交叉引用闭环提供三个独立、可落地的实现侧车，由Codex保留主线合成与最终验收
Task type: `complex_delivery_conference`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. First-line workers execute bounded work items. The execution manager checks progress, diagnoses environment/tool blockers, requests same-session reruns when needed, and consolidates outputs for Codex. Codex owns task contract, source authority, final verification, acceptance, production writes, and user delivery.

## Assigned Roles

- First-line executor: `complex_executor_minimax` -> `hermes` / `aishuo` / `MiniMax-M3`
- Execution manager: `complex_manager_grok` -> `grok` / `grok-build` / `grok-4.5`

## Source Of Truth

- Global operating and routing rules: `/Users/smkzw/.codex/AGENTS.md`.
- Active slice record: `records/active_slices/medical_writing_word_indexes_crossrefs_20260716/TASK_RECORD.md`.
- Current importer and exporter: `services/api/app/medical_writing_document.py`, `services/api/app/protocol_text_extractor.py`, `services/api/app/medical_writing_document_exporter.py`, and `services/api/app/medical_writing_repository.py`.
- Current frontend: `frontend/src/features/medical-writing/` and the related medical-writing API client/routes.
- Current tests: `tests/test_medical_writing_document_exporter.py` and related medical-writing repository/API/frontend tests.
- Authoritative RUX source DOCX, read-only: `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/RUX-03-002-自查文件包-20260107/10-临床试验重要文件/1-临床试验方案/V1.3版-2024.8.14/磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx`.
- Verified source fact: Word body paragraph containing `表 8 SCORAD-主观症状评分` is immediately followed by a drawing that embeds `word/media/image12.png`; the current `ProtocolDocument` contains the caption paragraph but no corresponding content object.
- Company implementation boundary: main TOC uses `TOC \\o "1-3" \\h \\z \\u`; table/figure indexes use `TOC \\h \\z \\c "表/图"`; numbered objects use `SEQ` and internal references use `REF` with bookmarks.

## Risk Boundaries

- No production writes.
- Source DOCX and stable runtime data are strictly read-only. Do not modify `5174/8911`, runtime stores, imported work copies, or external project files.
- Workers may inspect workspace source and tests and may include an exact patch in their single report, but must not edit the shared workspace source tree. Codex will apply and verify accepted changes.
- Do not solve the RUX mismatch by changing the expected count from 8 to 7 or by classifying arbitrary unnumbered layout tables as catalog tables.
- Cross-reference targets must use stable object IDs; client-provided bookmark names are untrusted and export must fail closed when a target no longer exists.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Work Items

1. 审计并实现源DOCX题注后嵌入图片对象的确定性保真导入方案，重点覆盖RUX表8 PNG丢失；限定写入隔离补丁/测试报告，不改稳定运行时数据。
2. 审计文档索引目录、SEQ书签与REF交叉引用的后端契约、失败关闭边界和API端点，提交可应用补丁或精确变更清单。
3. 审计医学写作编辑器交叉引用选择器的桌面端交互、TipTap/ProseMirror mark持久化与浏览器验收路径，提交可应用补丁或精确变更清单。

## Success Criteria

- Worker 01 identifies a deterministic OOXML/media extraction and serialization path for captioned source drawings, including hash, MIME type, dimensions, relationship/source locator, and lossless DOCX re-export behavior; it must explain how an image semantically captioned as `表` enters the table index without pretending it is an editable native table.
- Worker 02 defines one authoritative index catalog, stable bookmark derivation, `SEQ`/`REF` export, stale-target failure behavior, and a minimal read-only API response contract.
- Worker 03 defines a compact desktop insertion interaction, a persisted mark schema containing only stable target identity, save/reload behavior, and concrete browser tests without adding log-like cards to the writing workbench.
- Every report lists files read, commands/observations, exact recommended edits or patch, uncertainty, and rerun needs.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
