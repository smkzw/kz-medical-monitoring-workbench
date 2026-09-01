# RUX 医学监查 Inbox 外部产品/开源调研 - 2026-07-08

Purpose: 作为 RUX-03-002 医学监查统一 inbox 投影前的外部参照。仅用于产品/架构原则，不作为商业宣称或我们当前功能已完成的证据。

## Sources Checked

- Medidata Clinical Data Studio, official product page, accessed 2026-07-08.
- Veeva CDB / DQS, official product page/search result excerpt, accessed 2026-07-08.
- eClinical Solutions elluminate Data Central / Clinical Data Cloud, official product pages/search result excerpts, accessed 2026-07-08.
- Oracle Life Sciences Clinical One, official product/help excerpts, accessed 2026-07-08.
- GitHub topic/repository scan for clinical-trial adverse-event dashboards, clinical Shiny templates, teal/TFL dashboards, and patient-safety monitoring examples, accessed 2026-07-08.

## Direct Product Principles Extracted

1. Unified data review is a core pattern.
   - Medidata CDS describes a single review/monitoring environment for Medidata and external sources, covering clinical data management, central monitoring, RBQM, medical monitoring, patient profiles, and audit trail review.
   - Veeva DQS/CDB and elluminate Data Central both emphasize aggregation of multi-source trial data into one workbench/platform rather than spreadsheet trackers.
   - Implication for this project: RUX inbox projection must fit the existing cross-module `WorkbenchInboxService` contract instead of creating an isolated RUX-only page that cannot participate in unread/read-state, handoff, and audit workflows.

2. Source traceability and audit trail are not optional.
   - Commercial systems explicitly position audit trail review, issue workflow, query resolution, and data quality management as core clinical data review capabilities.
   - Implication: RUX inbox items must expose public stable locators through `WorkbenchItemSourceRef.locator` and must not expose local paths, hashes, server storage keys, or raw file-system details.

3. Patient profile and signal drill-down are expected user flows.
   - Medidata CDS highlights patient profiles and automated signal detection as context for medical monitoring; elluminate medical-monitoring materials similarly emphasize centralized real-time access and review capability.
   - Implication: inbox items should not be terminal summaries. They should route to `target_page="monitoring"` / subject-level review and carry subject ids like `S01003`, enabling later Subject Timeline / Patient Profile drill-down.

4. Changed/new review state matters.
   - Veeva DQS highlights change detection and automation to remove redundant effort. This matches the user's requirement that "自上次查看" should be implemented as unread/read-state rather than disappearing on page entry.
   - Implication: RUX inbox projection must preserve existing `source_version` + store-backed `unread` hydration and must not build a separate nonpersistent notification list.

5. Open-source examples are useful for visualization patterns, not production clinical workflow completeness.
   - GitHub examples include Shiny adverse-event visualization, clinical dashboards, safetyCharts/teal-style interactive data exploration, and TFL dashboards.
   - These are useful references for timeline/profile/TFL visual components, but they do not replace commercial-grade source traceability, audit, role-based review, or protocol-derived rule provenance.

## Decisions For Current TDD Slice

- Keep the implementation backend-first and additive.
- Use the unified `WorkbenchInboxService` item contract.
- Do not mutate demo repository data to register RUX as if it were a demo project.
- Preserve read-state, visible selection, source-version semantics, and existing demo project behavior.
- Project only verified deterministic RUX anchors in P0 and visibly label them as `待医学确认` / `基于已验证规则锚点`.
- Defer frontend visual work until backend RUX inbox semantics and tests pass.

## Non-Goals For This Slice

- Full 192-subject RUX monitoring coverage.
- Prohibited concomitant-medication semantic classification.
- Commercial claims about reducing review cycle time.
- Frontend Patient Profile/Subject Timeline redesign.
- Replacing current project catalog/dashboard data model.
