# Conference Context: monitoring_my009_fullchain_20260710

Created: 2026-07-10 14:52:53
Objective: Design and implement a reusable two-real-project medical-monitoring chain for RUX-03-002 and MY009-UC from original listing and protocol, including subject catalog, subject timeline, patient profile, risk inbox, incremental batch boundaries, privacy, independent-AI prompts, desktop interactions, and cross-project fail-closed tests.
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

- User requirements and current project decisions in `logs/subsystems/medical_monitoring_log.md` and `logs/system_build_log.md`.
- Sanitized real-source audit: `records/active_slices/monitoring_my009_fullchain_20260710/SOURCE_AUDIT.md`.
- External benchmark brief: `records/research/medical_monitoring_external_benchmark_20260710.md`.
- Current implementation: `services/api/app/main.py`, `services/api/app/monitoring_raw_intake.py`, `services/api/app/rux_monitoring_service.py`, `packages/contracts/workbench_contracts/models.py`, `frontend/src/App.jsx`.
- Current verification: `tests/test_monitoring_raw_project_intake.py`, `tests/test_rux_monitoring_service.py`, `tests/test_frontend_monitoring_contract.py`, `tests/test_frontend_timeline_contract.py`.
- The user explicitly authorized read-only use of original RUX and MY009 project files, but participant prompts use the sanitized audit rather than reopening participant-level files.

## Scope

- In scope: reusable project adapter/registry boundary; canonical subject catalog; visit-axis timeline; separate AE, MH, CM, non-drug treatment, study-drug change/dose-adjustment, lab and efficacy domains; Patient Profile trends; project-scoped risk inbox; first-batch and later-batch/diff semantics; source locators; independent-AI prompt/output boundary; desktop interaction and two-project tests.
- Out of scope for this decision: EDC direct integration, automatic scheduled triggers, mobile-first redesign, unblinded treatment-arm exposure, formal external Query transmission, e-signature, broad RUX service rewrite, and using prior timeline/Profile/risk outputs as input.

## Success Criteria

- MY009 canonical and alias monitoring routes return the same real project service and never fall back to demo or RUX data.
- Real MY009 subject catalog is derived from the 61-sheet listing and includes 26 subjects / 12 sites.
- At least five high-information MY009 subjects are exercised; at minimum `S01003`, `S01008`, `S01009`, `S08001`, and `S05003`.
- Subject Timeline is visit-axis based; every event has a project/source locator; CM contains non-investigational medication only; DA/EX/EX2/EX3 remain study-drug change/dose-adjustment.
- Patient Profile exposes source-grounded UC efficacy candidates and safety trends without claiming medical interpretation before validation.
- Risk outputs distinguish deterministic data checks from AI/medical interpretation and remain `待医学复核`; no rule result is silently converted into a formal conclusion.
- A first uploaded batch has an explicit no-baseline state; later snapshots support idempotency and diff semantics without mutating original files.
- API, static contracts, browser QC and a full cross-module regression pass; no local path, PHI, hash, demo subject or cross-project leakage.

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
- The current RUX adapter is a verified project-specific implementation; reuse its public contract, not its disease-specific constants.
- Do not make SDTM/ADaM a prerequisite for ongoing medical monitoring. Current source is manual EDC data listing plus protocol.
- Do not use existing Subject Timeline HTML, Patient Profile HTML, manual risk summaries or prior derived comparison conclusions as production input.
- Do not merge CM with investigational-product exposure or dose adjustment.
- Do not infer unblinded treatment allocation.

## Loop Log

- 2026-07-10 14:52:53: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-10 14:55 CST: Codex confirmed the production defect: MY009 raw intake is real, while subject catalog and inbox remain empty/demo-backed. External benchmark and real-source schema audit were added before participant dispatch.
