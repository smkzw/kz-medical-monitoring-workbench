# 阶段 E：风险域扩展与五项目验收

## Goal

扩展风险域、报告审阅、三模式，并完成五项目真实全量/增量验收。

## Requirements

- Activate remaining risk domains on real data in user-value order: CM/IP, protocol/visit/PD, efficacy, safety/labs, cross-table, and center/project aggregation.
- Connect the R6 report-review runtime to the product UI: report upload, claim extraction, issue matrix, and annotated copy.
- Run daily, pre-lock, and post-lock/pre-CFDI modes with their required outputs.
- Complete at least one real full run for each of the five projects and an incremental run where a compatible dual snapshot exists.

## Acceptance Criteria

- [ ] User confirms risk location, source drill-down, Profile/Timeline, under-reporting comparison, Query, report review, and mode outputs for all five projects.
- [ ] Independent review completes; tag `mm-five-projects` exists.

## Constraints

- Extend the generic model/prompt framework; do not encode one study's drug, disease, scale, or listing shape as product logic.
