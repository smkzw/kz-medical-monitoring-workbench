# Task Context: rux_monitoring_domestic_platform_benchmark_20260708

Created: 2026-07-08 13:08:30
Objective: Critically benchmark domestic clinical trial medical monitoring/RBQM platforms such as SpruceCloud iMRDP and Taimei iMAP/iRMS for the medical monitoring subsystem, without adding features unless justified.
Task type: `unknown`
Risk: `medium`
Selected Hermes route: `deepseek-v4-pro` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User request: “对于医学监查子系统，你也可以看看国内的几个成熟产品，比如杉云平台。不是一定让你改或者加功能，你可以做一个参考和批判性借鉴。”
- Local current benchmark note: `research/medical_monitoring_domestic_platform_benchmark_20260708.md`
- Existing commercial/open-source references:
  - `research/commercial_and_open_source_research_20260708.md`
  - `research/rux_inbox_external_research_20260708.md`
  - `research/rux_timeline_dose_adjustment_interaction_research_20260708.md`
- Current implementation facts:
  - RUX-03-002 医学监查 must start from original listing and protocol.
  - Current daily monitoring input is manually uploaded/exported data listing; direct EDC/CTMS integration is future scope.
  - CM means non-investigational concomitant medication/treatment.
  - `dose_adjustment` and other investigational-product changes must be separate from CM.
- Web sources Codex checked on 2026-07-08:
  - `https://sprucecloud.com.cn/znyxjcsjpt`
  - `https://www.sprucecloud.com.cn/`
  - `https://www.21jingji.com/article/20240801/herald/e49c9352a18953a71dc1d6e6177c1e10.html`
  - `https://www.eeo.com.cn/2024/0819/680191.shtml`
  - `https://www.bagevent.com/org/921109?pagingNumberPer=5&pagingPage=3&sortDirection=1`
  - `https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106.pdf`
  - `https://www.fda.gov/media/121479/download`

## Scope

- In scope: critique whether the domestic-product benchmark note uses sources conservatively, separates product facts from product design inference, and keeps the current RUX/P0 medical-monitoring priorities intact.
- Out of scope: adding new features, changing code, making market-size claims, final regulatory conclusions, or asserting vendor capabilities beyond the listed public sources.

## Success Criteria

- Output identifies any overclaims, missing caveats, or useful design corrections.
- Output states whether the note can be accepted as a reference log after Codex review.
- Output does not introduce unsourced vendor claims.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- Hermes is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark Hermes failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-08 13:08:30: Task initialized by `tools/hermes_workflow_guard.py init-task`.
