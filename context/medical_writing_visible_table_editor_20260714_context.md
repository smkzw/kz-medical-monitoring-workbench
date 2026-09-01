# Task Context: medical_writing_visible_table_editor_20260714

Created: 2026-07-14 05:08:41
Objective: Ensure all medical-writing tables, including newly promoted reusable table domains, are visibly rendered and synchronously editable in the document editor and AI revision flow without Markdown-only fallbacks
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `reasonix-cli` / `deepseek-v4-pro` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `frontend/src/App.jsx` and `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`.
- `services/api/app/medical_writing_document.py`, `medical_writing_tables.py`, `medical_writing_repository.py`, `medical_writing_table_templates.py`, `ai_gateway.py`.
- RUX-03-002, CMS-D001 and MY008211A-PNH-3-01 original protocol-derived document sessions.
- User boundary: all writing-panel tables must be rendered and reviewable; omission text and raw Markdown tables are not acceptable.

## Scope

- In scope: inline TipTap table rendering, synchronized title/notes, table selection/scroll linkage, reusable table templates, table-cell AI revision boundary, Word/export invariants, real-project/API/DOM tests.
- Out of scope: inventing project-specific medical values, replacing the immutable source DOCX, mobile-driven feature reduction, visual acceptance without a browser run.

## Success Criteria

- Every table block remains a real editable TipTap table; no placeholder or Markdown-only fallback.
- Active table title, source-caption divergence, dimensions and every non-empty note are visible in the editor panel.
- RUX/D001/PNH real project data and the three new promoted templates pass persistence and export checks.
- Independent AI cannot return Markdown table syntax in `proposal_text`; table creation is routed to the structured designer.
- Focused tests, medical-writing regression, full repository regression, frontend build and compile pass.

## Risk Boundaries

- Only the authorized local workbench is writable; original protocol files remain read-only.
- Hidden cells are merge continuations and must remain non-editable; their parent cell carries visible content.
- Source-linked captions/notes retain immutable source identity; working-copy review status/title changes remain separate.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-14 05:08:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-14: Existing TipTap path confirmed real table rendering and stable-cell synchronization; title/notes were detached from inline review.
- 2026-07-14: Added synchronized table context, source-caption divergence, scroll linkage, exact AI snapshot labels and Markdown-table output rejection.
- 2026-07-14: RUX/D001/PNH deterministic source verification covered 68 tables, 3,748 visible cells and 146 notes with no failures.
