# Conference Context: source_registry_frontend_boundary_review_20260708

Created: 2026-07-08 09:26:46
Objective: Review current AI medical manager workbench prior work and the proposed Source Registry frontend boundary fix; decide whether Codex should finish the server-side candidate-id refactor, remove local absolute paths from the frontend bundle, and add tests/QC before landing, without editing production code during review
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

- `context/source_registry_frontend_boundary_review_20260708_review_packet.md`: current user instruction, current code facts, proposed Codex fix, and review questions.
- `logs/system_build_log.md`: chronological implementation, Hermes review, verification, and remaining-risk log.
- `logs/SOFT_PAUSE_20260708_0905_CST.md`: last soft-pause handoff state.
- `reviews/codex_conference_prior_work_rux_preflight_review_20260708_review.md`: previous Codex/Hermes review of prior work and RUX preflight.
- `services/api/app/main.py`: current Source Registry public API and partially added `local-candidate` endpoint.
- `services/api/app/source_intake.py`: Source Registry service contracts and public/internal source handling.
- `packages/contracts/workbench_contracts/models.py`: public contract model exclusions and source registry model fields.
- `frontend/src/App.jsx`: current frontend Source Registry candidates and review-action loading text.
- `frontend/AGENTS.md`: durable frontend/product constraints.
- Relevant tests/QC: `tests/test_source_registry.py`, `tests/test_contracts.py`, `frontend/tests/source_registry_qc.mjs`, `frontend/tests/overview_ai_gateway_qc.mjs`, `frontend/tests/safety_pv_manifest_qc.mjs`.
- Do not add original clinical production paths to Hermes read lists for this review. The issue is boundary design and code, not clinical data interpretation.

## Scope

- In scope:
  - Review whether the proposed Source Registry frontend boundary refactor is correct.
  - Review whether frontend local absolute paths must be removed before productized distribution.
  - Review whether backend allowlisted local path mapping is acceptable for current local-single-machine deployment.
  - Review required tests/QC before Codex lands any patch.
  - Review the Safety/PV `提交中` wording/QC interaction as part of frontend clinical-boundary hygiene.
- Out of scope:
  - Editing source code inside Hermes.
  - Browser/visual acceptance by Hermes.
  - RUX medical monitoring engine implementation.
  - D001 from-scratch enrollment workflow implementation.
  - External web research.
  - Any clinical/regulatory final conclusion.

## Success Criteria

- All selected Hermes roles complete or are explicitly recorded as pending/failed with evidence.
- Hermes output answers the six review questions in the review packet.
- Codex reviews the Hermes outputs and either accepts or rejects each proposed modification with rationale.
- No code patch is landed until Codex records consensus or a justified Codex override.
- If a patch is landed later, required verification includes backend tests, frontend build, `/Users/` source/dist scan, and Source Registry browser QC.

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

- 2026-07-08 09:26:46: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-08 09:30 CST: Codex added review packet and filled conference context. Current known P0 issue: frontend bundle still contains local absolute paths under `sourceRegistryCandidates`; backend has already gained an internal `local-candidate` endpoint.
