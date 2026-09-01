# Kimi Compact Frontend Review Packet - 2026-07-08

## Purpose

This compact packet is for a retry of buddy `kimi-k2.7-code` after the first full frontend review prompt failed with supplier HTTP 400. A separate smoke test succeeded with `KIMI_ROUTE_OK`, so the route is available; the likely issue is the large context or request parameter combination in the first full prompt.

Kimi should review previous frontend and interaction work only. It should not edit code, run browser QC, or claim rendered acceptance. Codex remains final authority for browser/visual QC and production writes.

## Current Product Boundary

Visible modules must remain:

- 项目总看板
- 证据调研与方案设计
- 入排审核
- 医学监查
- 数据分析与TFL
- 医学写作
- 安全信号与PV协同
- 审批中心

Do not expose `第几环节`, `阶段`, `Stage`, project startup, site operation, recruitment, or EDC/data-collection construction as user-facing subsystems.

## User Corrections Relevant To Frontend

- The three visual concepts correspond to three actual scenarios, not alternatives:
  1. 项目总看板 after selecting a project.
  2. 医学监查子系统首页, with clear entry into each subject's Subject Timeline and Patient Profile.
  3. 医学写作 process page.
- 康哲 logo must match the provided CMS asset.
- 医学监查 must not use old skill-generated HTML as source truth. For RUX-03-002 it must rebuild from original data listing and protocol.
- Subject Timeline should be visit-axis based, with events distributed under the axis by time. It must be dense enough for clinical review and avoid low-information empty lanes.
- Patient Profile must follow the previous successful profile concept: longitudinal efficacy and safety metrics, graphical trends, subject/site-level views, and risk hints integrated with the data.
- Risk cards and Chinese labels must use clinical-trial medical language. Vague terms such as bare `AE`, bare `Lab`, or odd wording like `危急` should be replaced by precise labels such as `AE/MH漏报`, `实验室异常未解释`, `禁限用药/洗脱`, `疗效偏离`, `数据质量/字段漂移`, with notes when a compact card cannot carry the full definition.
- `自上次查看以来的医学关注项` should be treated as unread items/read state, not disappearing automatically on re-entry.
- Frontend must not be judged complete merely because it renders. Every button, workflow, data edge, and backend interaction must be tested with realistic project data.

## Current Frontend Findings From Existing Subagent Audit

The frontend audit report at `runs/subagents/monitoring_frontend_interaction_audit_20260708.md` concluded:

- 医学监查首页 has module entry, batch panel, mapping prompt, risk ledger, right-side risk detail, and two drilldown entrances, but batch summary and default risk rows still contain hardcoded demo content.
- Upload batch flow can parse XLS/XLSX/XLSM through backend and CSV through frontend; however session/audit/source row traceability and detailed mapping confirmation are not yet production-grade.
- Risk detail visually suggests actions such as query, close, and review submission, but several controls do not yet persist to backend. The UI should avoid implying a completed action until backend state exists.
- Subject Timeline source code is directionally closer to the user's requirement: visit axis, SVG events, hover title, detail rows. It lacks 20260708 rendered visual QC and still depends on demo/static subject profiles.
- Patient Profile has center filter, subject switch, subject tree, base info, efficacy/safety trends, PD/query, risk prompts, and event index. It lacks RUX-derived data coverage and recent rendered visual QC.

## Backend-First Constraint

Multiple Hermes and subagent reviewers agree that RUX medical monitoring should start with a backend data dictionary / protocol rule / normalized event layer before large frontend replacement.

Reason: current monitoring frontend still reads demo subject profiles. If React components are renamed to RUX metrics before the RUX event layer exists, the UI would remain disconnected from real listing/protocol evidence.

However, frontend can still make non-data-contract-breaking safety fixes now:

- remove or label hardcoded demo summaries;
- disable or mark non-persistent action buttons until backend actions exist;
- ensure precise Chinese labels and tooltip/explanatory notes;
- add QC assertions for no overflow, no text overlap, stable timeline dimensions, and drilldown route state.

## Review Questions For Kimi

1. Which frontend fixes can be safely done before the RUX backend event/rule layer exists?
2. Which visible widgets should be deferred until the RUX backend contracts are available?
3. What should the revised 医学监查 homepage interaction hierarchy be, especially risk list/detail versus Subject Timeline/Patient Profile entrances?
4. What QC assertions are required for Subject Timeline and Patient Profile on desktop and mobile?
5. What should Codex avoid changing now to prevent demo-debt or conflicting work across modules?

## Required Output

Write only:

`runs/conference/lower_half_commercialization_rux_monitoring_20260708/participant_kimi_frontend_retry.md`

Separate:

- evidence from files/packet;
- inference;
- recommended frontend changes;
- changes that must wait for backend;
- QC assertions;
- unresolved questions for Codex.

