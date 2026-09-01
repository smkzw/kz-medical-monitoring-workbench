# Conference Context: project_source_manifest_20260709

Created: 2026-07-09 12:00:55
Objective: Build ProjectSourceManifest as the unified real-project source and identity layer for the medical manager workbench, covering dashboard, eligibility, monitoring, TFL, writing, safety/PV, and source-boundary governance.
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes And Reasonix Delegation

- Lead/chair: OpenCode Go `minimax-m3`.
- Hermes participant models: OpenCode Go `qwen3.7-plus` and OpenCode Go `mimo-v2.5`, all default reasoning effort unless Codex overrides.
- Reasonix CLI participant model: `deepseek-flash` alias for `deepseek-v4-flash`.
- All `deepseek-v4-flash` and `deepseek-v4-pro` routes must leave Hermes and run through Reasonix CLI. OpenCode Go, Hermes custom providers, and the direct DeepSeek provider are not allowed for these models in this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro` only. Hermes/OpenCode Go/direct DeepSeek routes are not allowed for this role.

## Source Of Truth

- User requirements in this thread: do not self-pause; use subAgents/Hermes in background; log continuously; keep medical-only subsystem naming; desktop-first frontend; CM is non-investigational concomitant medication only; dose adjustment and other investigational-product changes must be separate.
- Implemented code:
  - `services/api/app/project_source_manifest.py`
  - `services/api/app/main.py`
  - `frontend/src/App.jsx`
  - `frontend/src/styles.css`
  - `tests/test_project_source_manifest.py`
  - `tests/test_frontend_source_manifest_contract.py`
  - `tests/test_frontend_monitoring_contract.py`
  - `tests/test_frontend_timeline_contract.py`
  - `frontend/tests/project_source_manifest_qc.mjs`
- Implementation records:
  - `records/active_slices/project_source_manifest_20260709/README.md`
  - `records/active_slices/project_source_manifest_20260709/LOOP_LEDGER.md`
  - `records/active_slices/project_source_manifest_20260709/CROSS_MODULE_TEST_MATRIX.md`
  - `records/active_slices/project_source_manifest_20260709/SUBAGENT_REVIEW.md`
  - `logs/subsystems/module_scope_log.md`
  - `logs/subsystems/medical_monitoring_log.md`
- Browser QC outputs:
  - `records/active_slices/project_source_manifest_20260709/visual_qc/project_source_manifest_qc_metrics.json`
  - `records/active_slices/project_source_manifest_20260709/visual_qc/overview_source_manifest.png`
  - `records/active_slices/project_source_manifest_20260709/visual_qc/monitoring_source_manifest.png`
  - `records/active_slices/project_source_manifest_20260709/visual_qc/timeline_source_manifest.png`
  - `records/active_slices/project_source_manifest_20260709/visual_qc/eligibility_source_manifest.png`
  - `records/active_slices/project_source_manifest_20260709/visual_qc/safety_source_manifest.png`
- Verification already run by Codex:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover tests -v` -> 183 tests OK.
  - `npm run build` -> OK with existing Vite chunk-size warning.
  - `APP_URL=http://127.0.0.1:5173/ API_BASE=http://127.0.0.1:8910 node tests/project_source_manifest_qc.mjs` -> OK.

## Scope

- In scope: review the implemented ProjectSourceManifest slice, focusing on source identity, route binding, public redaction, cross-project UI disclosure, medical-only module naming, monitoring write-route correction, CM vs investigational-product-change boundary, and future package-role integration risks.
- Out of scope: editing source files; browsing web; rerunning tests; claiming visual/browser final acceptance; changing real source locations; adding non-medical lifecycle modules; final clinical/regulatory conclusions.

## Success Criteria

- Confirm whether the implementation and tests address the P0 mismatch: MG-K10 top project vs D001/RUX/MY009 module source identity.
- Identify gaps that Codex should fix next, especially hidden project-id coupling in medical writing, TFL, Safety/PV, approval center, source registry candidates, and future multi-project deployment.
- Verify that the logs are sufficient for future handoff/resume.
- Preserve boundaries: advisory only; Codex keeps final authority.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes and Reasonix are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-09 12:00:55: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-09: Codex implemented ProjectSourceManifest slice and completed regression/browser QC before dispatching Hermes review. Hermes should critique the completed slice and next risks, not redo implementation.
