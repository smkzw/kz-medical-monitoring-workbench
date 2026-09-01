# Task Context: medical_monitoring_my008_identity_20260805

Created: 2026-08-05 21:50:40
Objective: Repair the reproducible MY008 persisted monitoring-rule identity failure caused by in-place field-lineage unit normalization, preserving fail-closed lineage semantics and enabling stable protocol-version rereview evidence; no runtime/provider activation.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rule_repository.py` (strict rule
  persistence and read-side identity revalidation)
- `services/api/app/monitoring_protocol_rules.py` (field-lineage normalization
  contract and rule revision identity)
- `tests/test_monitoring_protocol_rule_real_my008.py` (real MY008 V3/V4
  protocol-version rereview fixture)
- `tests/test_monitoring_protocol_rule_repository_hardening.py` (durable
  repository integrity regression coverage)
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
  (authoritative runtime gate; still read-only/blocked)

## Scope

- In scope: prevent repository-side field-lineage validation from mutating a
  revision-bearing `MonitoringRuleDefinition`; add a deterministic regression
  proving legacy `unit` lineage survives store/read with the same rule id;
  re-run real MY008 and monitoring regressions.
- Out of scope: changing lineage validation semantics, changing rule revision
  identity generation, provider/AI/runtime/API activation, browser or
  Playwright work, real project LOOP, medical-writing surfaces, or the B6/C14
  gate.

## Success Criteria

- The strict validator continues to reject invalid lineage while receiving a
  copy of the rule payload at repository validation boundaries.
- A rule containing legacy `unit` lineage stores and reloads with the original
  revision id and source payload; the validator may still normalize its local
  copy.
- The real MY008 V3/V4 selective rereview test passes.
- Focused protocol/lifecycle/real-listing tests and the full monitoring test
  sweep pass; warnings remain explicitly identified.
- Runtime gate remains unchanged and no service, provider, browser, API login,
  or real project is started.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- Do not weaken fail-closed source/lineage checks or silently rewrite persisted
  rule identities; this is an integrity repair only.
- Keep 8911, 5174, 8910 and 4173 stopped while the authoritative gate is
  `read_only / blocked`.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 21:50:40: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 21:51:10: Reproduced the MY008 failure. The stored
  `field_lineage_json` had `unit_literal` while the revision-bearing rule was
  hashed with legacy `unit`; only `rule_revision_id` differed on rebuild.
- 2026-08-05 21:51:10: Patched the three repository-side
  `validate_rule_field_lineage` calls to pass a top-level copy, preserving the
  rule payload after revision identity calculation; no validator acceptance
  rule was changed.
- 2026-08-05 21:52:31: Added a repository hardening regression covering legacy
  unit lineage, store/read identity continuity, and source payload retention.
- 2026-08-05 21:53–22:25: Verification passed: focused identity pair 2;
  protocol/lifecycle/real-listing suite 138; nine-module monitoring regression
  741; full `tests/test_monitoring_*.py` sweep 2536 passed with 25 warnings in
  1050.02 seconds; py_compile passed. `ruff` is not installed in this runtime.
- 2026-08-05 22:25: Runtime/real-loop gate rechecked conceptually from the
  authoritative read-only audit; no activation or external execution was
  attempted. Next safe action is to record evidence and continue the source
  contract/API wiring only while the gate remains blocked.
- 2026-08-05 22:26: Direct gate recheck confirmed `status=blocked`,
  `read_only=true`, all activation/provider/write permissions false, and ports
  8911/5174/8910/4173 empty. Review-gate returned `ok: true` with no warnings.
