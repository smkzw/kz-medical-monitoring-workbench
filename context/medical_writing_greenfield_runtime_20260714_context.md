# Task Context: medical_writing_greenfield_runtime_20260714

Created: 2026-07-14 15:38:03
Objective: 将通用绿地研究方案文档基线接入医学写作工作台，复用现有编辑、审批与Word导出链路并保持真实DOCX项目不变
Task type: `visual_delivery_conference` after implementation and browser proof
Risk: `high`
Selected agent route: Codex-led no-chair visual panel: Hermes aishuo / MiniMax-M3, Hermes buddy / kimi-k2.7-code, OpenCode Go / qwen3.7-plus

## Trigger Reason

The original guard generated a legacy Reasonix route. That route was not dispatched because the workspace conference rules supersede it. Implementation and deterministic proof are complete enough for a bounded visual/design conference; Codex remains final authority.

## Source Of Truth

- Existing DOCX editor reference at the same 1600 x 1000 viewport: `records/visual_qc_20260714/medical_writing_greenfield_runtime/reference_existing_docx_editor_1600x1000.png`.
- Greenfield setup implementation: `records/visual_qc_20260714/medical_writing_greenfield_runtime/greenfield_setup_1600x1000.png`.
- Greenfield editor implementation: `records/visual_qc_20260714/medical_writing_greenfield_runtime/greenfield_editor_1600x1000.png`.
- Browser metrics and API proof: `records/visual_qc_20260714/medical_writing_greenfield_runtime/medical_writing_greenfield_qc.json`.
- UI source: `frontend/src/App.jsx`, `frontend/src/styles.css`.
- Backend source: `services/api/app/medical_writing_greenfield.py`, `services/api/app/medical_writing_document.py`, `services/api/app/medical_writing_repository.py`, `services/api/app/medical_writing_manifest.py`, `services/api/app/main.py`.
- Contract and tests: `packages/contracts/workbench_contracts/models.py`, `tests/test_medical_writing_greenfield_runtime.py`, `tests/test_frontend_medical_writing_contract.py`, `frontend/tests/medical_writing_greenfield_qc.mjs`.

## Scope

- In scope: compare the new greenfield setup and resulting editor state against the existing product's desktop visual language; identify overflow, hierarchy, alignment, terminology, misleading states, missing controls, or workflow breaks; assess whether the editor and AI interaction remain primary.
- Out of scope: redesigning the medical writing system, changing the Kangzhe visual system, adding a separate project-creation route, approving medical content, changing the production AI route, or editing production files.

## Success Criteria

- The setup stays inside the existing medical-writing editor workspace; it is not a wizard, landing page, or new route.
- Project fields, 14-section scaffold, unresolved decision controls, candidate boundary, AI rail, and document map are visible and usable at 1600 x 1000.
- After creation, the same editor, AI rail, document map, working-copy, approval, table, and Word paths remain in place.
- No local path leak, lifecycle numbering, horizontal page overflow, source-project fallback, or error noise appears.
- Visual recommendations must be grounded in the three screenshots and report; distinguish pixel observations from inference.
- Each participant completes three rounds in the same session: independent review, skeptical challenge, corrected final pass.

## Risk Boundaries

- Review is read-only. Participants may only read the listed files and screenshots and write their own conference outputs under the current task `runs/` or `logs/` directories.
- Do not treat synthetic or greenfield text as medically approved facts.
- Do not recommend removing desktop capabilities for mobile responsiveness.
- Do not invent a new design system or judge final acceptance; Codex owns the final browser and visual decision.
- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-14 15:38:03: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-14: Legacy Reasonix prompt marked superseded and not dispatched.
- 2026-07-14: Backend and frontend implementation completed; targeted 54-test pass, full 180-test medical-writing pass, and Vite production build pass recorded.
- 2026-07-14: Native Chrome CDP visual QC passed with no failed metrics; draft Word export returned 38,064 bytes in an isolated runtime.
