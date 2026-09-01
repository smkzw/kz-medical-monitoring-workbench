# Task Context: medical_writing_content_quality_20260714

Created: 2026-07-14 08:34:12
Objective: 在不修改原始方案的前提下，构建跨项目医学写作源内容异常检测、精确来源展示、医学分类处置、审计和正式输出门禁闭环；以RUX真实<0}异常以及D001/PNH阴性对照验证，系统独立运行并保留override边界
Task type: `complex_delivery_conference`
Risk: `high`
Selected agent route: `mixed` / `conference:buddy-glm-5.2-chair+aishuo-minimax+buddy-deepseek-pro+opencode-go-mimo` / `mixed:Hermes default reasoning for participants; mimo is the default non-visual replacement; no Reasonix second review`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- RUX immutable original protocol: `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/RUX-03-002-自查文件包-20260107/10-临床试验重要文件/1-临床试验方案/V1.3版-2024.8.14/磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx`.
- D001 immutable original protocol: `/Users/smkzw/Documents/康哲项目资料/AI/入排/test-D001项目/CMS-D001 银屑病2、3期临床方案 v1.0-2025.12.21.docx`.
- PNH immutable original protocol: the MY008211A-PNH-3-01 source currently registered in `services/api/app/medical_writing_manifest.py`.
- Existing medical-writing fact and workflow layers: `services/api/app/medical_writing_document.py`, `medical_writing_repository.py`, `sqlite_runtime_store.py`, contract models, API routes, frontend editor, and focused tests.
- Proven positive: RUX exact source string `对于研究中具有生育能力的女性受试者：<0}` in Appendix 1, source table 11 row 3 cell 1.

## Scope

- In scope: conservative deterministic source/working-copy text findings; exact source text before locator; context, section, table/cell identity; medical dispositions with reason; fingerprint invalidation; audit; working-copy approval blockers; approved-final backstop; compact editor-side workflow; three-project validation.
- Out of scope: modifying original DOCX files, malware/security scans, generic prose style checking, autonomous medical correction, electronic signature, regulatory submission, mobile feature cuts, unrelated writing document types.

## Success Criteria

- RUX real `<0}` is detected from the original protocol without project-specific code and returns the exact source text plus secondary locator.
- D001 and PNH act as real cross-project controls; legitimate medical comparison operators are not reported by the same rule.
- Medical users can mark `confirmed_source_text` or `correction_required` only with a substantive reason; the warning remains visible and every action is audited.
- Dispositions are bound to source/document/section/location/rule/content fingerprint and become inapplicable after content or source-version changes.
- Draft editing and draft preview remain available; unresolved blocking findings prevent medical approval and approved-final export.
- API, persistence, frontend interactions, focused and full tests, desktop browser QC, conference review and task/system/subsystem records pass.

## Risk Boundaries

- Original protocols are immutable read-only evidence; no silent source rewrite.
- Initial rules must be explainable and conservative. Valid values such as `<10`, `>1.5`, `≤5%` must not be treated as malformed placeholders.
- Source text is the primary user-facing evidence; locator is secondary traceability metadata.
- Override requires warning retention, reason, actor and audit. Source/content change invalidates prior confirmation.
- Frontend remains editor/AI-first and desktop-first; no high-visibility global banner for a local content finding.
- Conference participants are read-only and advisory. Codex owns code, browser acceptance and final clinical/product judgment.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-14 08:34:12: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-14: Re-anchored after resume. Existing stable source locators, versioned working copies, immutable approval snapshots and approval blockers will be reused rather than duplicated. Slice task record: `records/active_slices/medical_writing_content_quality_20260714/TASK_RECORD.md`.
