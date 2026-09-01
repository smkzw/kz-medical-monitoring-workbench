# Lower-Half Commercialization And RUX Monitoring Review Packet - 2026-07-08

## Purpose

This packet resumes the AI medical manager workbench build after the Source Registry frontend boundary patch. The product goal is not a demo slice: it is a commercial-ready medical manager workbench covering every medical-related clinical-development workflow that the user approved.

The immediate decision is whether the next implementation loop should start with the RUX-03-002 real-data medical monitoring event/rule layer, and how to build it without reusing previous skill-generated HTML or already-derived outputs as source truth.

## Current Scope Boundary

Visible product surfaces stay limited to:

- 项目总看板
- 证据调研与方案设计
- 入排审核
- 医学监查
- 数据分析与TFL
- 医学写作
- 安全信号与PV协同
- 审批中心

Do not build or expose standalone modules for non-medical lifecycle steps such as project startup, EDC/data-collection system build, site operations, visit execution, or recruitment operations. User-facing subsystem names must not show lifecycle numbering such as `第几环节`, `阶段`, or `Stage`.

## User Requirements That Still Govern The Work

- Every subsystem must eventually be tested from original project files/data, not from prior skill outputs or already-deconstructed artifacts.
- Original project folders are read-only for this build. If write/delete/edit is needed, copy into the workbench first.
- The system must run independently of Codex. AI tasks in the runtime must call independent AI providers through the workbench/Hermes/AI Gateway path, with output validation and medical approval gates.
- OCR, when needed, should use local oMLX GLM-OCR-bf16 or PaddleOCR-VL-1.6.
- LLM work should use Hermes-configured independent providers. DeepSeek supplier `deepseek-v4-pro` is required for high-risk Chinese clinical/regulatory wording. For frontend/aesthetic design, use buddy `glm-5.2` and `kimi-k2.7-code` in consultation with Codex.
- Codex remains final authority for source boundaries, production writes, browser/visual QC, and final clinical/regulatory conclusions.

## Current Workbench Evidence

Relevant local files:

- `README.md`
- `frontend/AGENTS.md`
- `logs/SOFT_PAUSE_20260708_0958_CST.md`
- `logs/system_build_log.md`
- `context/rux_monitoring_source_precheck_20260708.md`
- `services/api/app/main.py`
- `services/api/app/monitoring_intake.py`
- `services/api/app/listing_file_parser.py`
- `services/api/app/protocol_text_extractor.py`
- `services/api/app/ai_task_runner.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_contracts.py`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `frontend/tests/monitoring_upload_qc.mjs`
- `frontend/tests/patient_profile_qc.mjs`

The previous accepted Source Registry patch is current evidence:

- Frontend source and bundle no longer contain `/Users/` path strings.
- Frontend source candidates use opaque candidate ids and business titles.
- `/sources/local-candidate` is the local prototype route for backend-owned source mapping.
- Backend candidate mapping and allowed roots still must be externalized before distribution, multi-machine deployment, or public push.

## Current Module Maturity Snapshot

Project overview:

- Backend has `WorkbenchInboxService`, read-state JSONL, and module summaries.
- Frontend displays unified inbox, module status, handoff ledger, and source/data health.
- Known P0/P1 gap: `_select_visible_items()` remains a short-term visibility patch. Commercial version needs grouping, filtering, pagination, and clear read-vs-resolved semantics.

Evidence design:

- Real CRSwNP master databases are used for manifest/PICOS workflow.
- PICOS remains a design coach and must not be represented as an approved protocol.
- Gap: evidence refresh, source de-duplication, and handoff into medical writing need stronger end-to-end proof.

Eligibility review:

- Existing MG-K10 enrollment-review system is adapted and tested.
- D001 raw enrollment bundle remains a required from-scratch workflow.
- Gap: D001 original protocol + raw subject folder build path needs to produce rule extraction, subject evidence, decisions, and inbox actions without relying on prebuilt review outputs.

Medical monitoring:

- Current upload/intake path can parse xlsx/csv/xls and run simplified demo/SAR-style rules.
- Current Subject Timeline and Patient Profile frontends read demo repository subject profiles.
- RUX precheck already showed original RUX listing workbook has 53 sheets / 180,793 rows; subject report has 192 rows; protocol extraction has 2,005 paragraphs / 20 tables.
- Gap: no RUX-ready protocol-parameterized event layer, data dictionary, rule engine, or RUX-derived Timeline/Profile generation yet.

Data analysis and TFL:

- RUX and MY008 file inventories/manifests exist; TFL review and writing-candidate handoff exists.
- Gap: row drilldown, SAP/shell/program traceability, ADaM/SDTM calculation assurance, and approval gate coupling need stronger production-grade coverage.

Medical writing:

- Real DOCX protocol manifest, revision thread, TFL citation candidate integration, and approval states exist.
- Gap: review DOCX export, IB/ICF/CSR/CTD 2.5/2.7.3/2.7.4 manifests, and real provider-based drafting validation are not complete.

Safety signal and PV collaboration:

- MY009/RUX safety source manifests, review workbench, and PV handoff candidate flow exist.
- Boundary is correct: this is not a PV case-processing or regulatory clock system.
- Gap: exportable medical review packet, stronger PV handoff gates, and safety-writing integration remain.

Approval center:

- Approval action API, blockers, decisions, and tests exist.
- Gap: gates must cover TFL writing candidates, PICOS writing candidates, Safety/PV handoff candidates, and source/data-health quality gates rather than only demo monitoring/protocol blockers.

## RUX-03-002 Original Source Packet

These original source paths are authorized for Codex read-only inspection, but Hermes participants should rely on the precheck and local workbench files unless Codex explicitly assigns direct reads:

- Listing workbook: `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/准备阶段/RUX-03-002_列表_数据集_Excel_20250612_处理后.xlsx`
- Subject report: `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/准备阶段/RUX-03-002_受试者报表_20250613.xls`
- Protocol DOCX: `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/CFDI Inspection/RUX-03-002-自查文件包-20260107/10-临床试验重要文件/1-临床试验方案/V1.3版-2024.8.14/磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx`

The first RUX build loop must start from those files, not from previous Subject Timeline HTML, Patient Profile HTML, AE/MH leakage reports, or skill-generated intermediate datasets.

## External Research Targets And Principles

Codex performed a live web scan on 2026-07-08 and will continue source-specific verification. These public targets should inform architecture, not be treated as copied product requirements:

- Regulatory/standards grounding: ICH E6(R3), ICH E8(R1), FDA risk-based monitoring guidance, CDISC SDTM/ADaM.
- Commercial UX/logic references: Veeva clinical data review/data studio surfaces, Medidata clinical data review/data studio surfaces, CluePoints RBQM, Saama clinical data analytics/monitoring.
- Open-source implementation references: pharmaverse/teal, safetyGraphics, safetyExploreR, admiral, Tplyr and related clinical-trial R packages.
- Product principle inferred from research: commercial systems converge on a unified clinical data layer, risk/task orchestration, source-traced review actions, patient-level profiles, data quality signals, and audit trails. Open-source tools are strongest for safety/lab/AE visual idioms and reproducible clinical table/profile logic.

## First-Principles Architecture Hypothesis

For RUX medical monitoring, the core product abstraction should not be a page-specific parser or a single risk rule. It should be:

1. Original source ingestion and data dictionary layer.
2. Protocol-derived rule set and visit schedule layer.
3. Unified subject event layer with source locators.
4. Deterministic derivations for timelines/trends where possible.
5. Independent AI interpretation only for semantic judgment that cannot be safely hard-coded.
6. Review actions, query recommendations, approval gates, and audit trail.
7. Frontend surfaces generated from the same event/rule layer: risk workbench, Subject Timeline, Patient Profile, and project inbox.

## Decision Questions For Hermes

1. Should Codex start implementation with the RUX data dictionary/event layer before changing medical-monitoring frontend, or is there a smaller safe slice that still advances commercial readiness?
2. What is the minimum schema for `DataDictionaryProfile`, `ProtocolRuleSet`, and normalized subject events that supports RUX P0 without overbuilding?
3. Which RUX domains and fields are P0 versus P1?
4. Which rules must be deterministic from protocol/listing, and which require independent AI?
5. What tests should be written first and watched fail before implementation?
6. What frontend changes should be deferred until the RUX-derived backend layer exists?
7. Are there conflicts between RUX medical monitoring, D001 eligibility, TFL, writing, Safety/PV, and approval contracts that must be handled before code changes?

## Required Output From Participants

Provide a decision-ready recommendation with:

- evidence versus inference separated;
- recommended build slice;
- schema proposal;
- test-first plan;
- risks and rollback/fallback;
- implications for frontend, AI Gateway, and approval/workbench inbox;
- issues requiring Codex-only verification or user decision.
