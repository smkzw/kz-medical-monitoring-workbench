# Review Packet: AI Medical Manager Workbench Resume Review - 2026-07-08

## Role And Boundary

This is a Codex-chaired Hermes review. Hermes is advisory only. Do not edit files. Do not browse web. Do not run tests unless explicitly requested in a later prompt. Read the listed local files and return concrete review findings with file/line references when possible.

The user asked Codex to resume the full AI Medical Manager Workbench build toward a commercializable product, then asked Hermes to review previous work in the background. Codex must discuss Hermes findings and only land changes that Codex and Hermes both accept. Some local fixes may already be in progress because Codex was closing a QC failure discovered before this review request.

## Hard Product Scope

- Do not build first/fourth/fifth clinical-development links.
- Do not expose standalone non-medical subsystems such as project startup/activation, EDC construction, site operations, visit execution, or recruitment operations.
- User-facing subsystem names must be business names only, without `第几环节`, `阶段`, or `Stage`.
- Allowed visible modules are: 项目总看板, 证据调研与方案设计, 入排审核, 医学监查, 数据分析与TFL, 医学写作, 安全信号与PV协同, 审批中心.
- Original real-project folders are read-only unless copied/backup-first.
- Public API/UI must not expose local absolute paths, server paths, raw hash fields, raw AI replies, or internal file fingerprints.

## Current State Summary

The implementation workspace is:

`/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`

Runtime at resume:

- API: `http://127.0.0.1:8910/`
- Frontend: `http://127.0.0.1:5174/`

The latest soft-pause closure completed:

- Source Registry public API excludes `content_hash`, `preview_hash`, `storage_key`, `server_path`.
- Source Registry entry ids use namespace-derived opaque tokens instead of raw hash prefixes.
- `/api/health` no longer exposes `data_path`.
- 入排 evidence `source_record_id` is excluded from public model dumps.
- 入排 audit summary strips path/run-log fields and redacts `/Users/`.
- 入排 inbox aggregation scans all review phases rather than only the active phase.
- 医学监查 UI copy was reduced from `EDC` wording to `原始数据 listing` wording.

Focused verification before resume:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_source_registry tests.test_workbench_inbox tests.test_eligibility_adapter tests.test_contracts -v`: 37 OK.
- `npm run build`: passed with known Vite chunk-size warning only.
- Live API spot checks found no `/Users/`, `content_hash`, `preview_hash`, `source_record_id`, or `data_path` in `/sources`, `/eligibility`, and `/workbench-inbox`.

On resume, overview browser QC failed because the default 80-item inbox was dominated by all-phase 入排 actions:

`Workbench inbox API missing required item type source_ready: ["eligibility_action","ai_review","approval","risk","handoff"]`

Codex then observed:

- `limit=80`: 68 `eligibility_action`, 6 `ai_review`, 3 `risk`, 2 `approval`, 1 `handoff`; no `source_ready`, `data_health`, `picos_decision`, or `quality_gate`.
- `limit=200`: 99 total items, including 71 `eligibility_action`, 3 `source_ready`, 2 `data_health`, 5 `picos_decision`, 2 `quality_gate`, 2 `handoff`.

Codex started implementing `_select_visible_items()` in `services/api/app/workbench_inbox.py` so limited inbox responses still include minimum cross-module item types while `total_open_count`, `unread_count`, `handoff_count`, and module summaries are calculated on all open items.

## Files To Review

Read these project files:

- `logs/SOFT_PAUSE_20260708_0640_CST.md`
- `logs/system_build_log.md`
- `logs/subsystems/project_dashboard_log.md`
- `logs/subsystems/module_scope_log.md`
- `frontend/AGENTS.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/main.py`
- `services/api/app/source_intake.py`
- `services/api/app/workbench_inbox.py`
- `services/api/app/enrollment_adapter.py`
- `tests/test_source_registry.py`
- `tests/test_workbench_inbox.py`
- `tests/test_eligibility_adapter.py`
- `tests/test_contracts.py`
- `frontend/src/App.jsx`
- `frontend/tests/overview_ai_gateway_qc.mjs`

Do not read real production project data folders for this review. Do not read `frontend/dist` or `node_modules`.

## Review Questions

1. Does the Source Registry / 入排 / health public API boundary now look adequate for a local commercial prototype? Identify any remaining path/hash/internal-id leakage risks.
2. Is the `_select_visible_items()` approach the right product/engineering fix for limited overview inbox responses, or should this be done with separate endpoint fields, grouping, filters, or frontend fetch limit changes? Discuss benefits/risks.
3. Does all-phase 入排 scanning create too many work items? If yes, what production-grade prioritization/grouping should be introduced next without losing safety-critical findings?
4. Does the visible module scope still respect the user’s rule that first/fourth/fifth clinical-development links are not built and subsystem names do not include lifecycle numbering?
5. Which next build loop should Codex prioritize after this recovery QC: 医学监查 RUX real listing/protocol workflow, 入排 D001 from-scratch workflow, or 医学写作 protocol-first rich-text workflow? Give evidence-based reasoning.
6. What tests/browser checks/log updates must pass before Codex can consider the current overview recovery accepted?

## Required Output

Return:

- Findings ordered by severity with file references.
- Recommended acceptance/rejection of Codex’s current `_select_visible_items()` direction.
- Concrete changes you would make now versus defer.
- Verification checklist.
- Any disagreements or uncertainty.

Do not produce generic encouragement. Keep it specific and actionable.
