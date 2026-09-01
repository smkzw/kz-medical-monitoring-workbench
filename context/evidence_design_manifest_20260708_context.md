# Task Context: evidence_design_manifest_20260708

Created: 2026-07-08 01:20:12
Objective: Build evidence research and protocol design typed manifest for the AI medical manager workbench from real CRSwNP source files, preserving source boundaries and product AI independence
Task type: `clinical_document_router`
Risk: `high`
Selected Hermes route: `deepseek-v4-pro` / `xhigh`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User instruction thread: build AI Medical Manager Workbench; prioritize medical-related subsystems; do not build first/fourth/fifth clinical-development links; do not expose lifecycle numbers in user-facing names.
- Local source package: `/Users/smkzw/Documents/康哲项目资料/竞品调研/CRSwNP/00_Master_Database/`.
- Authoritative P0 inputs:
  - `Document_Index.csv`
  - `Trial_Design.csv`
  - `Efficacy_Result.csv`
  - `Safety_Result.csv`
- Existing workbench code: `packages/contracts/workbench_contracts/models.py`, `services/api/app/main.py`, `frontend/src/App.jsx`, `frontend/src/styles.css`.
- QA outputs:
  - `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/records/visual_qc_20260708/evidence_design_manifest_qc.json`
  - desktop/mobile screenshots in the same directory.

## Scope

- In scope: typed manifest/API/frontend P0 for `证据调研与方案设计`, deterministic parsing of CRSwNP master CSVs, PICOS design question queue, quality gates, browser QC, logs.
- Out of scope: building non-medical first/fourth/fifth lifecycle subsystems, using previous deep-dive reports/HTML as production input, full-text OCR/LLM extraction, live registry refresh, final protocol approval, cross-trial ranking.

## Success Criteria

- API `GET /api/projects/{project_id}/evidence-design/manifest` returns real CRSwNP counts and desensitized payload.
- UI shows business name only, with no lifecycle numbering.
- UI/API do not expose `/Users/` paths or overclaim terms.
- Evidence panel appears before Source Registry and separates evidence facts, PICOS questions, and quality gates.
- Unit tests, full test suite, frontend build, and browser QC pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Hermes is not final authority; Codex owns verification and acceptance.
- Product runtime AI must be independent from Codex; P0 uses deterministic parsing and prepares future independent AI tasks only.
- Existing deep-dive Markdown/HTML reports are QA references only, not production input.

## Timeout Policy

- Do not mark Hermes failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-08 01:20:12: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-08 01:38: Codex implemented deterministic P0 locally, used three Codex subagents for backend/data, frontend/product, and Chinese medical terminology review; no external Hermes model invocation was performed.
- 2026-07-08 01:40: Unit tests, full tests, frontend build, Evidence browser QC, Safety/PV browser QC, and TFL browser QC passed.
