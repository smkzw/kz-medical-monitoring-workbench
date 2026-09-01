# R7 Slice-09A governed execution assignments

Date: 2026-08-30

## Worker 01 — core backup/restore engine

Own:
- new `mm_r7/maintenance_gate.py` if needed by the core;
- new `mm_r7/project_backup.py`;
- focused core tests in new `test_project_backup.py`.

Implement deterministic ZIP, operation ledger, consistent SQLite snapshots, artifact closure, preflight, staging, switch/rollback, replay/conflict and failure hooks. Keep the API small and stdlib-only. Do not edit product router or existing unrelated tests.

## Worker 02 — product write gate and routes

Own:
- minimal edits to `services/api/app/medical_monitoring_r7_product_router.py`;
- minimal maintenance-gate integration at actual R7 product/background write boundaries;
- focused product-router tests for five routes, Chinese DTOs, authorization, stable errors and re-entrant progress.

Reuse Worker 01 public API. Do not fork core semantics or add UI/frontend work.

## Worker 03 — independent verification matrix

Own only test/evidence code:
- independent stdlib oracle and adversarial tests for deterministic bytes, member closure, corruption, cross-project identity, same-key conflict, active-writer race, switch failures, rollback and reopened identity;
- adjacent R7/R1/product regression selection and path/port/boundary evidence.

Do not modify production source. If a test exposes a defect, report the exact contract breach for manager remediation.

## Execution manager

Read every worker report and current diff. Resolve overlaps without discarding user/parallel work. Remediate only within the execution contract, run focused then adjacent tests, produce manifest/evidence and identify remaining P0–P4. Do not claim final acceptance.
