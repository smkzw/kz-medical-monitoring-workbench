# Governed execution contract: R7 Slice-09A

Date: 2026-08-30  
Frozen contract: `FROZEN_ACCEPTED_R7_SLICE_09A_CONTRACT_V0_3`

## Goal

Implement the smallest synthetic/offline project backup, export, preflight, restore and status slice that satisfies the frozen v0.1+v0.2+v0.3 contract. A senior Chinese medical monitor must be able to request a project backup, inspect a Chinese restore impact summary, and recover the same project without handling SQLite or filesystem details.

## Source authority

- `reviews/medical_monitoring_r7_slice09a_project_backup_restore_contract_v0_1_20260830.md`
- `reviews/medical_monitoring_r7_slice09a_project_backup_restore_contract_v0_2_20260830.md`
- `reviews/medical_monitoring_r7_slice09a_project_backup_restore_contract_v0_3_20260830.md`
- `context/medical_monitoring_r7_slice09a_contract_acceptance_record_20260830.md`
- Current R7/R1/product source and tests on disk.

## Allowed changes

- New R7 stdlib modules under `poc/medical_monitoring_ai_native_r7/src/mm_r7/` for maintenance gate and project backup/restore.
- Minimal R7 product router DTO/routes and product-safe error mapping.
- Focused R7/product tests and test-only synthetic fixtures/oracles.
- Existing R7 write-entry wrapping only where necessary to prove the maintenance gate closes the actual product write surface.
- Execution artifacts, context, reviews, metrics and plans for this task.

## Hard boundaries

- Do not start 8911/5174, real services, browsers or models.
- Do not read or run the five real projects.
- Do not modify medical-writing, R1–R6 business semantics, frontend/UI, mobile/narrow layouts or system-security features.
- Do not hand-edit runner-owned reports.
- Do not add third-party dependencies, custom crypto, cancel/delete APIs, arbitrary hook-count floors or new authorization rules.
- Do not clean unrelated files or rollback directories. Synthetic temp workspaces only.

## Required implementation surfaces

1. Deterministic `.mmbackup` ZIP with manifest, six-member project closure, SQLite online backup, R1 artifact closure, atomic package publication and package/workspace identities.
2. Root-level `backup_operations.sqlite3` and POSIX shared/exclusive project maintenance gate, with bounded wait and stable operation progress.
3. Import/restore preflight, project identity/schema/member checks, staging, atomic live/rollback switch, reopen verification, auto-rollback and idempotent replay.
4. Five frozen product routes with Chinese DTOs and existing project authorization.
5. Source-enumerated failure hooks and synthetic/offline tests for determinism, corruption, orphan, cross-project, replay/conflict, writer race, switch/rollback and post-restore identity.

## Done evidence

- Focused 09A tests and affected R7/product adjacent suites pass.
- Independent stdlib oracle does not call product helpers.
- Compileall and project/path-neutrality pass.
- 8911/5174 remain stopped; medical-writing protection evidence is unchanged during the task.
- Execution manager returns an auditable report; Codex reopens source and evidence.
- Independent implementation conference returns P0–P4 all zero before 09A acceptance.

Implementation acceptance remains synthetic/offline and only unlocks 09B.
