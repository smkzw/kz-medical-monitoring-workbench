# Codex Review: p3_monitoring_rule_lineage

Date: 2026-07-29
Delegated-agent output: not dispatched

## Verdict

Pass for the assigned P3 rule-contract scope. Core CM/IP bypasses fail closed,
field lineage is structurally auditable, all 11 template families retain their
real protocol sources, and compiled rules start as candidates.

## Boundary Check

- Codex directly modified only the four user-assigned implementation/test
  surfaces. Workflow-owned context, review, and metrics records were also
  updated.
- Repository, database, and service code were not modified by this task.
- `monitoring_protocol_rule_service.py` changed concurrently during execution;
  its new evidence/status behavior was treated as current source truth.

## Codex Verification

- Baseline directly reproduced both core bypasses before the change.
- `python3 -m py_compile` passed for all four assigned Python files.
- `pytest -q tests/test_monitoring_rule_templates.py
  tests/test_monitoring_rule_core_boundaries.py`: 39 passed.
- `pytest -q tests/test_monitoring_protocol_rule_api.py
  tests/test_monitoring_protocol_rule_repository_hardening.py`: 14 passed.
- `pytest -q tests/test_monitoring_rule_evaluation_fail_closed.py`: 17 passed,
  including candidate execution rejection.
- Final combined assigned/adjacent regression: 70 passed.
- `pytest -q tests/test_monitoring_protocol_rules.py`: 16 passed, 1 failed.
  The failure is an old evaluator fixture without a stable record locator and
  is caused by the concurrent service evidence gate, not this patch.
- The real-MY008 test module could not collect because the active Python 3.12
  environment lacks `cryptography`.

## Delegated-Agent Output Review

Hermes: not dispatched. Codex performed implementation and verification
directly. No external dependency, architecture, or executable adoption was
needed, so external solution discovery had no material expected value.

## Residual Risk

- Existing template v1 facts require migration to v2 with complete lineage.
- Candidate rules require the existing confirmation/enabling lifecycle before
  production evaluation.
- `field_lineage` is additive and optional in the core model but is not
  persisted by the unchanged repository schema. Bound fact
  `normalized_payload` remains the durable publication-audit source.
- The concurrently changed service and its unassigned legacy tests require
  reconciliation by their owning workstream.
