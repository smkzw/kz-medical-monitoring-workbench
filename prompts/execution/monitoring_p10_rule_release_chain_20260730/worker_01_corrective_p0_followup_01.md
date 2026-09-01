# Worker 01 Corrective P0 Follow-up 01

Resume the same session and preserve all accepted Worker 01 and corrective changes. Do not restart broad review. Codex independently reproduced two remaining contract gaps. Fix only these gaps and their focused tests.

Re-read the current files before every edit because a medical-writing session is concurrently changing shared files. Do not edit `main.py`, `frontend/src/App.jsx`, any medical-writing file, `monitoring_ai_router.py`, or `tests/test_monitoring_ai_api.py`. Do not start 8911 or write a real runtime database.

## P0-A atomic promotion failure

Current `MonitoringShadowSampleService.confirm_samples` persists promoted trusted gold/diagnostic cases before `run_shadow_validation`. If evaluation or run persistence fails, trusted cases remain even though no medical confirmation exists. This violates the required atomic promotion and can contaminate later release evidence.

Implement a transactionally safe or equivalently failure-atomic confirmation path:

- failure at any point before the immutable medical confirmation is committed must leave no newly promoted gold cases, diagnostic cases, trusted shadow run, or confirmation;
- existing independent preregistered gold/diagnostic cases must never be deleted or weakened;
- the exact successful confirmation remains idempotent;
- do not mask failures by cleaning with broad project/rule deletes;
- prefer an explicit repository transaction/atomic persistence contract or an in-memory prevalidation followed by one atomic evidence commit; avoid compensating deletion that can race or remove unrelated evidence.

Add a deterministic test that injects failure after candidate cases are prepared but before confirmation commit and proves counts remain unchanged for newly promoted evidence. Also test that pre-existing independent trusted cases survive the failed attempt unchanged.

## P0-B complete capability identity

`MonitoringRecordRuleResolver.aggregate_identity` currently allows an included published rule with empty `effective_capabilities_sha256`, even though the aggregate identity contract claims all mapping/capability identities are complete.

- Require non-empty, valid `effective_capabilities_sha256` for every included published rule in record-applicability mode.
- Mixed or missing effective-capability identities fail closed as `monitoring_rule_pack_identity_unverifiable`.
- Add focused tests for missing and mixed effective-capability identities.

## Verification

Run the focused shadow-service, record-resolver, daily-run service/repository/router tests and the relevant rule lifecycle/authoring tests. Return exact files changed, counts, and proof of zero residual trusted evidence on injected confirmation failure. No frontend work.
