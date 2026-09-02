# 阶段 B：医学监查整合归一

## Goal

收敛单一 packages/medical_monitoring package、单代前端与产品本体 synthetic profile；删除已迁移的平行应用和 POC 工作副本。

## Requirements

- Create `packages/medical_monitoring/` as the sole authoritative backend package with domain, graph, intelligence, risks, projections, reports, runtime, and thin API layers.
- Migrate behavior and tests before redesign; keep legacy `monitoring_*` code frozen and protect all medical-writing routes/assets.
- Consolidate the frontend into one `medical-monitoring` feature and move only medical-monitoring routing/state out of `App.jsx`.
- Replace the parallel G6 app with product-native `--synthetic` loading from external fixture files.
- Delete migrated `deploy/medical_monitoring_local` and `poc/medical_monitoring_ai_native_r1..r7` working copies only after imports are detached and migrated tests pass.
- Remove frozen hash-pinning and obsolete parallel-app tests while retaining behavioral digest checks.

## Acceptance Criteria

- [ ] Migrated medical-monitoring tests pass from their new locations.
- [ ] The workbench starts with the product-native synthetic profile.
- [ ] Dashboard, center graph, Subject Workspace/Journey, and progress page have no P0/P1 visual issue at the primary wide-screen resolution.
- [ ] A fresh-context reviewer confirms behavior and medical-semantic preservation.
- [ ] User confirms the stage; tag `mm-consolidated` exists.

## Constraints

- Follow `.trellis/spec/medical-monitoring-engineering.md`.
- Use git commits per migrated layer; never add new process records under `context/` or `reviews/`.
