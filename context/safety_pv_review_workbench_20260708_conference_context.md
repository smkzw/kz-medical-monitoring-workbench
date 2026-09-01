# Conference Context: safety_pv_review_workbench_20260708

Created: 2026-07-08 05:00:53
Objective: Build the Safety/PV Collaboration P0 review workbench: real MY009/RUX safety sources, candidate signal review actions, durable audit records, PV handoff candidates, frontend workflow, tests and browser QC, without replacing formal PV systems
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes Sub-Venue

- Lead/chair: OpenCode Go `minimax-m3`.
- Participant models: OpenCode Go `qwen3.7-plus`, OpenCode Go `mimo-v2.5`, and DeepSeek supplier `deepseek-v4-flash`, all default reasoning effort unless Codex overrides.
- All `deepseek-v4-flash` routes must use the DeepSeek supplier. OpenCode Go `deepseek-v4-flash` is not allowed for this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: DeepSeek supplier `deepseek-v4-pro` only. OpenCode Go `deepseek-v4-pro` is not allowed for this role.

## Source Of Truth

- Current workbench root: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Current product scope log: `logs/subsystems/module_scope_log.md`.
- Current system build log: `logs/system_build_log.md`.
- Existing safety/PV backend:
  - `services/api/app/safety_pv_manifest.py`
  - `services/api/app/main.py`
  - `packages/contracts/workbench_contracts/models.py`
  - `packages/contracts/workbench_contracts/__init__.py`
- Existing safety/PV frontend and QC:
  - `frontend/src/App.jsx`
  - `frontend/src/styles.css`
  - `frontend/tests/safety_pv_manifest_qc.mjs`
  - `records/visual_qc_20260707/safety_pv_manifest_qc.json`
- Existing tests:
  - `tests/test_safety_pv_manifest.py`
  - `tests/test_contracts.py`
  - `tests/test_ai_gateway.py`
- Real safety source inputs are read-only:
  - `/Users/smkzw/Documents/朗来项目资料/MY009治疗UC/S1安全性评价-202604/MY009-UC-2-01-MM Listing_20260410_Comparison.xlsx`
  - `/Users/smkzw/Documents/朗来项目资料/MY009治疗UC/S1安全性评价-202604/MY009-UC-2-01-MM Listing_20260408(已自动还原).xlsx`
  - `/Users/smkzw/Documents/朗来项目资料/MY009治疗UC/S1安全性评价-202604`
  - `/Users/smkzw/Documents/朗来项目资料/MY009治疗UC/DSUR/附件1：MY009_DSUR#4_资料收集 to CPM、RA、医学-MM.docx`
  - `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/2-RUX-03-002-现场核查项目层面文件目录-20260424/22.PV计划`
  - `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/RA/2.7.4/2-7-4临床安全性总结`
- External research inputs already captured in `research/commercial_and_open_source_research_20260708.md`; treat them as design context, not final clinical/regulatory authority.

## Scope

- In scope:
  - Design and critique a P0 `安全信号与PV协同` review workbench.
  - Use current MY009 and RUX safety source manifests as real-source input.
  - Add or review candidate-signal disposition actions, durable audit records, quality gates, and PV handoff candidate boundaries.
  - Preserve the workbench's unified contract pattern and local-single-machine now / private deployment later direction.
  - Verify the product-language boundary: `待医学/PV确认`, `不替代PV系统`, no formal PV claim.
- Out of scope:
  - Formal PV database/case-processing system replacement.
  - E2B generation/submission, regulatory clock tracking, SAE reportability workflow, or official PV database writes.
  - Final seriousness, expectedness, causality, listedness, or regulatory reporting decisions.
  - Moving, deleting, or modifying original files under `/Users/smkzw/Documents/康哲项目资料` or `/Users/smkzw/Documents/朗来项目资料`.
  - Building standalone non-medical lifecycle subsystems.

## Success Criteria

- Participant outputs propose concrete contracts/API/UI/QC gaps and do not violate PV boundaries.
- Codex can implement a bounded P0 slice:
  - backend safety review workbench endpoint;
  - review action endpoint with append-only JSONL store;
  - `医学已复核`, `转PV确认候选`, `退回补充资料`, `关闭为暂无需处理`, `重置状态` action semantics;
  - frontend safety review panel;
  - backend tests and browser QC.
- Public API and UI do not expose local absolute paths, lifecycle numbering, or forbidden PV-system overclaim terms.
- All outputs remain `待医学/PV确认`; no formal PV conclusion is generated.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-08 05:00:53: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-08 05:06 CST: Codex narrowed the slice to P0 safety signal review and PV handoff candidates. Formal PV system features remain forbidden.
- 2026-07-08 05:07-05:08 CST: Hermes participants `qwen3.7-plus`, `mimo-v2.5`, and DeepSeek supplier `deepseek-v4-flash` completed independent passes and converged on the same implementation gap: Safety/PV had real-source manifesting but no review actions, durable audit, or handoff candidates.
- 2026-07-08 05:28-05:40 CST: Codex implemented and verified the P0 workbench: backend contracts/API/store, frontend action panel, backend tests, production build, and desktop/mobile browser QC. Lead/main conference outputs remain placeholders and are recorded as excluded for this bounded slice.
