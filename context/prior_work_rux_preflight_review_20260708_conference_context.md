# Conference Context: prior_work_rux_preflight_review_20260708

Created: 2026-07-08 08:45:41
Objective: Audit current AI Medical Manager Workbench implementation and preflight the next RUX medical monitoring real-data build; Hermes advisory only, no source edits
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

- User's current request: let Hermes review previous Codex work in the background, give Hermes enough information to judge, discuss recommendations, and only land changes accepted by both Hermes and Codex.
- Primary review packet: `context/prior_work_rux_preflight_review_20260708_review_packet.md`.
- RUX source precheck: `context/rux_monitoring_source_precheck_20260708.md`.
- Prior accepted conference: `workbench_resume_review_20260708` records under `context/`, `runs/conference/`, `reviews/`, `metrics/`, `logs/`.
- Current source files and tests listed in the review packet.
- Original RUX files are summarized in the precheck file. Hermes should not open original real-project paths during this advisory review.

## Scope

- In scope:
  - Audit whether the previous Hermes/Codex closure remains valid.
  - Re-check path/hash/internal-id leakage boundaries.
  - Review the current medical monitoring placeholder against the user's requirement to rebuild RUX monitoring from original listing + protocol.
  - Preflight the minimum correct RUX medical monitoring P0 architecture and verification gates.
  - Produce advisory recommendations only.
- Out of scope:
  - Source edits, test runs, browser/PPT/PDF/image acceptance, web research, or reading original real-project folders.
  - Final clinical/regulatory conclusions.
  - Treating prior skill-generated SAR outputs or RUX summaries as RUX medical monitoring source data.

## Success Criteria

- Each participant writes exactly one output file under `runs/conference/prior_work_rux_preflight_review_20260708/`.
- Review findings cite files/lines or named records where possible.
- Recommendations are separated into `land now`, `defer until RUX build`, and `do not do`.
- The Hermes lead compares participants, identifies conflicts, and gives Codex a bounded recommendation.
- DeepSeek Pro main-venue review identifies any remaining required Codex verification before code is changed.
- Codex does not land code changes from this conference unless Codex and Hermes both accept them after review.

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

- 2026-07-08 08:45:41: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-08: Codex filled source of truth, scope, success criteria, and review packet before participant dispatch to avoid the previous TODO-context process gap.
