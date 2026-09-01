# Task Context: medical_writing_word_table_fidelity_20260714

Created: 2026-07-14 06:32:23
Objective: 验证并修复医学写作工作副本导出Word中研究流程表及其他复杂方案表格的跨页、宽表、合并单元格、重复表头、表题和附注视觉保真，使用RUX、D001、PNH真实项目并完成渲染检查与多模型会商
Task type: `visual_report_structure`
Risk: `high`
Selected agent route: `mixed` / `conference:visual-no-chair-aishuo-minimax+buddy-kimi+opencode-go-qwen` / `mixed:Codex-led visual panel; participant defaults; qwen is the default visual replacement`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current API export endpoint: `http://127.0.0.1:8911/api/projects/{project_id}/medical-writing/document.docx?mode=draft_preview`.
- Real current working-copy projects: `proj_rux_03_002`, `proj_d001`, `proj_my008_pnh_3_01`.
- Export implementation: `services/api/app/medical_writing_document_exporter.py` and `services/api/app/medical_writing_table_exporter.py`.
- Structured source/session authority: current API repository and original registered protocol blocks; original DOCX files remain immutable.
- Canonical render tool: `/Users/smkzw/.codex/plugins/cache/openai-primary-runtime/documents/26.709.11516/skills/documents/render_docx.py` using the bundled workspace Python/LibreOffice runtime.
- Prior structural evidence: `output/medical-writing-table-sync-qc/medical_writing_table_sync_qc.json` and `records/active_slices/medical_writing_visible_table_editor_20260714/TASK_RECORD.md`.

## Scope

- In scope: export a current draft-preview DOCX for all three real projects; inspect OOXML geometry; render all pages; identify pages containing each table; verify table title, cells, merges, repeated headers, orientation changes, page breaks and notes; fix exporter defects only; rerender and regress.
- In scope: compare at least the densest SoA and representative non-SoA/generic/domain tables in each project, not only a toy fixture.
- Out of scope: changing original protocol content, medical approval, approved-final export, electronic signatures, tracked changes/comments, source DOCX round-trip identity or general visual redesign of the protocol.

## Success Criteria

- Three real current draft exports complete without Markdown fallback or source mutation.
- Every exported structured table is located in the DOCX/PDF; table count and visible content agree with the assembled snapshot.
- Wide tables use the intended orientation and fit the printable area without text clipping; merged cells remain coherent.
- Long tables repeat configured header rows after page breaks and do not truncate fixed-height rows.
- Table title and all structured notes stay readable and associated with the table; no duplicated caption/note rendering.
- Rendered pages pass Codex original-resolution inspection and the required three-model visual conference; focused and full regressions pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Writable paths are limited to `records/active_slices/medical_writing_word_table_fidelity_20260714/`, task conference/review/metrics files, production source/tests only after a reproduced exporter defect, and append-only system/subsystem logs.
- Draft watermark/header is expected and must not be mistaken for final approval.
- LibreOffice rendering is a verification runtime and may differ from Word; OOXML structure remains a parallel authority for repeat headers, merges, section geometry and row-split flags.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-14 06:32:23: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-14 06:34 CST: Adjacent-surface review selected rendered Word table fidelity as the next active Goal slice; no pause entered.
- 2026-07-14 06:44 CST: Three current API exports rendered to 154 pages / 68 tables / 17 landscape pages. Automated OOXML/PDF checks returned no failures; D001's empty table 2 is an original decorative 1x1 table.
- 2026-07-14 06:44 CST: Visual inspection found CJK glyph loss in the bundled LibreOffice PDF despite intact Chinese text extraction. A nine-font probe reproduced the issue for every CJK family while system fontconfig could enumerate the fonts; no production exporter defect is established.
- 2026-07-14 06:44 CST: User explicitly requested a lossless manual pause. No production code was changed and no conference was started. Resume from `records/manual_pause_20260714_word_table_fidelity/RESUME_CONTEXT.md`.
- 2026-07-14: User explicitly resumed work. A controlled three-case probe proved that explicit `FONTCONFIG_FILE`/`FONTCONFIG_PATH` restores CJK glyph embedding without changing the DOCX. The production exporter remains unchanged; the canonical renderer will be invoked with the task-local verified fontconfig for the three-project visual gate.
- 2026-07-14 08:15 CST: Verified-fontconfig rerender completed for unchanged RUX/D001/PNH DOCX exports: 259 pages, 68 tables and 26 landscape pages. Automated CJK-aware report has zero failures and confirms embedded Chinese fonts plus repeat-header rows for every schedule table.
- 2026-07-14 08:15 CST: Codex reviewed all 17 full-document contact sheets and 24 original-resolution pages spanning schedules, dense tables, merged cells, notes, questionnaires and document tails. No clipping, overlap, missing glyphs or missing tables were observed. Black page-exterior areas in some PNG tool views are transparency-display artifacts, not PDF defects.
- 2026-07-14 08:15 CST: Visual conference preflight initially rejected overbroad/missing-file prompt inputs. Prompts were narrowed to the evidence packet, structured report and enumerated images; all three participants passed preflight and were launched in parallel for three same-session rounds.
- 2026-07-14 08:29 CST: All three participants completed three same-session rounds without fallback. MiniMax and Kimi disclosed incomplete original-page coverage; Qwen completed the assigned packet but overgeneralized several sampled observations. Codex bounded those claims and retained final authority.
- 2026-07-14 08:29 CST: Conference-flagged RUX p70 `<0}` text was reproduced in the immutable original protocol DOCX, exported DOCX and PDF text. It is a source-content anomaly, not an exporter/rendering defect. Codex re-opened the challenged RUX/D001/PNH pages; current table visual fidelity passed with no production change.
