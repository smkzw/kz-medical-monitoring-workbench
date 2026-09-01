# RUX P0 Backend Review Packet - 2026-07-08

## Purpose

This packet asks Hermes to review Codex's most recent RUX-03-002 medical-monitoring backend work before Codex continues into unified inbox integration or frontend rewiring.

This is advisory only. Hermes must not edit files. Codex remains final authority for product writes, browser/visual QC, source-boundary acceptance, and any clinical/regulatory judgment.

## User Requirements Still Binding This Review

- The workbench must eventually run independently from Codex. Runtime AI work must call independent provider routes, not Codex's reasoning.
- Medical monitoring must start from original project-level data listing and original protocol, not from prior skill-generated HTML or deconstructed intermediate outputs.
- Original project folders are read-only. Workbench code, generated records, logs, and tests may be edited only by Codex after review and TDD.
- Every visible medical-monitoring risk/event/trend must preserve source locators to listing rows and protocol table/paragraph anchors.
- Do not build or expose non-medical lifecycle modules. Visible subsystem names must not show `第几环节`, `阶段`, or `Stage`.
- If code changes are later accepted, Codex must use test-first implementation: watch a failing test before production-code edits.

## Current Implemented Slice

Implemented after the prior Hermes RUX preflight:

- `packages/contracts/workbench_contracts/models.py`
  - added `source_locator` to `SubjectTimelineEvent`;
  - added `source_locator` to `SubjectTrendPoint`;
  - added compatibility validators that fill `source_locator` from existing `source_domain:source_record_id` when legacy payloads omit it.
- `services/api/app/rux_monitoring_service.py`
  - new additive RUX service;
  - reads the original RUX listing workbook through `parse_listing_file()`;
  - reads the original RUX protocol through `parse_protocol_docx()`;
  - extracts Table 4 and Table 7 protocol rules;
  - emits selected deterministic `RiskCase` anchors for S01017, S01003, and S03040;
  - emits a S01003 subject-monitoring drilldown with visit, ANC, AE, and dose-adjustment timeline events plus an ANC trend.
- `services/api/app/main.py`
  - added RUX listing/protocol path constants;
  - instantiated `RuxMonitoringService`;
  - dispatched `GET /api/projects/proj_rux_03_002/subjects/S01003/monitoring` to the real-source RUX service.
- `tests/test_rux_monitoring_service.py`
  - covers protocol rule extraction, real ALT/ANC/BSA anchors, S01003 timeline/trend locators, and FastAPI endpoint dispatch.

No unified inbox integration for RUX has been landed yet.

## Current Verification Evidence

RUX source verification gate:

- file: `records/rux_monitoring_profile_20260708/rux_p0_verification_gates_20260708.md`
- original listing parse baseline: 53 sheets, 180,793 rows, about 12.96s, peak RSS about 365 MB;
- original protocol parse baseline: 2,005 paragraphs, 20 tables;
- verified protocol anchors:
  - Table 4 rows for ALT/AST >3xULN interruption, ANC <1.5 interruption, other grade >=3 lab abnormality, AST/ALT >5xULN discontinuation, serious infection;
  - Table 7 rows for allowed conmed, prohibited conmed, poor-efficacy discontinuation, non-efficacy discontinuation;
  - BSA >20% stop/review paragraphs;
- verified listing anchors:
  - S01017 LBCHEM rows 1849 and 1863 for ALT >3xULN and >5xULN;
  - S01003 LBHEMA row 231 for ANC 1.24 *10^9/L, with AE and ECB dose pause/restart chain;
  - S03040 BSA rows 2185-2188 for D15 BSA 33%.

Latest recorded tests before this review:

- RUX focused service tests: 5 OK.
- Full backend unit suite: 122 OK.
- Frontend production build: passed, known Vite chunk-size warning only.

## Current Known Boundaries

- `RuxMonitoringService` is a P0 slice, not a complete RUX monitoring engine.
- It currently covers selected verified anchors only, not all 192 subjects.
- Prohibited concomitant medication classification is intentionally not implemented; keyword-only matching is not acceptable. It requires independent runtime AI plus protocol-sourced deterministic overrides.
- Patient Profile rich chart generation from RUX real events/trends is pending.
- RUX risks are not yet projected into the unified workbench inbox.
- The RUX project is not yet represented in project list/dashboard metadata.
- Frontend RUX project switching, Subject Timeline rendering, and Patient Profile rendering have not been visually QC'd on real RUX data.

## Current Unified Inbox Context

Relevant implementation files:

- `services/api/app/workbench_inbox.py`
  - builds unified items from demo repo risks, approvals, AI runs, PICOS decisions, TFL handoffs, Safety/PV handoffs, writing gates, Source Registry, and eligibility items;
  - currently calls `self.repo.project(project_id)` at inbox entry, so a project not present in demo repository will fail unless a RUX-specific dispatch/adapter is added;
  - `_risk_items()` expects `RiskCase` objects and projects source refs from `risk.rule_id` and `risk.evidence_span_ids`.
- `tests/test_workbench_inbox.py`
  - currently tests demo project inbox, read-state, dedupe, source-boundary behavior, eligibility aggregation, and module summaries.

Planned next TDD slice if Hermes and Codex agree:

1. Add a failing test that `GET /api/projects/proj_rux_03_002/workbench-inbox?limit=20` returns RUX monitoring risk items with S-prefix subject ids and no local path/hash leakage.
2. Add the smallest RUX inbox adapter/projection, likely separate from demo `WorkbenchInboxService` to avoid mutating the demo repository contract.
3. Preserve current demo inbox behavior and read-state semantics.
4. Run focused and full backend regressions.
5. Log accepted decisions and unresolved issues.

## Review Questions For Hermes

1. Is the additive `RuxMonitoringService` architecture acceptable as a P0 real-source service, or is there a concrete defect that must be fixed before inbox integration?
2. Are the current risk anchors and source locators sufficient for a safe first inbox projection, or would projecting them create misleading product semantics?
3. Should RUX inbox integration be implemented as a separate adapter/service rather than modifying `WorkbenchInboxService._risk_items()` or demo repository data?
4. What failing tests should Codex write before implementation?
5. What source-boundary/public API fields need explicit negative assertions?
6. Are there conflicts with existing eligibility, TFL, writing, Safety/PV, approval, source-registry, or module-scope contracts?
7. Are there Chinese clinical product terminology or information-architecture issues in the planned labels such as `医学监查`, `风险项`, `进入复核`, `受试者 S01003`, `实验室安全 / 肝功能中断规则`, and `待医学确认`?
8. What should be deferred until after full RUX event-layer and Patient Profile generation?

## Expected Output

Each participant should return:

- evidence-based findings tied to files or packet sections;
- severity-ranked risks or defects;
- recommended TDD next step;
- changes that should not be made yet;
- verification obligations for Codex;
- questions that truly require user decision.

Do not propose a broad rewrite unless a specific current defect requires it.
