# Worker 01 Same-Session Corrective P0 Slice

Continue the accepted Worker 01 backend work in the same Kimi session. Preserve all accepted Worker 01 changes; do not restart broad exploration and do not roll anything back. Work directly in the shared workbench.

## Read First

- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `context/monitoring_p10_rule_release_chain_20260730_execution_context.md`
- `plans/codex_execution_monitoring_p10_rule_release_chain_20260730.md`
- `runs/execution/monitoring_p10_rule_release_chain_20260730/worker_01.md`
- Current implementations and tests for shadow samples, daily-run identity/readiness, and existing-run recovery.

## Hard Boundaries

- Do not modify medical-writing files.
- Do not modify `monitoring_ai_router.py` or `tests/test_monitoring_ai_api.py`.
- Do not start port 8911 and do not write any real runtime database.
- Use isolated temporary repositories/databases only.
- Preserve CM/IP semantic boundaries.
- User adoption of a recommendation is already the medical decision; do not add a second rule-approval step.
- Shadow confirmation and publication remain distinct explicit actions.
- Keep existing independent preregistered gold/diagnostic evidence paths at least as strict as today.

## Corrective Slice

Implement all three items before returning.

### P0-A: automatic shadow evidence must remain provisional

The current automatic sample implementation copies the rule's own first-pass `matched` and `diagnostic_code` into expected gold/diagnostic outcomes, registers them as trusted release evidence, and may surface `shadow_passed`. This is circular self-validation.

Required behavior:

1. `prepare_and_run` on a frozen real batch creates an immutable provisional inspection run/sample set. It records and returns only actual hit/no-hit/indeterminate outcome, diagnostic output, source row bindings, coverage bucket, rule/pack/mapping/capability identities, and frozen batch identity.
2. A provisional run/sample is not a `RuleGoldStandardCase`, not trusted for release, cannot satisfy diagnostic/gold release gates, cannot be represented as `shadow_passed`, and cannot be published.
3. `confirm-shadow` is the medical manager's explicit confirmation of the frozen sample and its actual interpretation. It must atomically create an immutable medical-confirmation/expected-regression record or equivalently promote the exact frozen sample/outcome into medically confirmed expectation, then revalidate that exact snapshot before entering `confirmed`.
4. The confirmed frozen sample can be reused as expected regression evidence for later runs. Any difference in sample set, source binding, batch identity, outcome, rule/pack identity, mapping identity, or capability identity fails closed.
5. Existing independent preregistered gold/diagnostic cases remain valid and are not weakened.
6. API states and labels must distinguish `provisional`/inspection outcome from medically confirmed validation. A pre-confirmation response must never say `shadow_passed`.
7. Add tests proving:
   - first automatic run cannot self-create trusted expected evidence;
   - provisional cannot confirm a pack by a generic replay or publish it;
   - exact explicit `confirm-shadow` creates immutable medical confirmation and permits the expected transition;
   - later exact regression can compare against the confirmed expectation;
   - any identity/outcome/sample drift fails closed;
   - independent preregistered gold/diagnostic paths are unchanged.

### P0-B: freeze aggregate identity for `record_applicability`

The current record-level/site-specific resolution can return an empty identity and bypass mapping identity checks.

Required behavior:

1. Resolve a deterministic aggregate assignment/published-pack identity for every `record_applicability` batch. It must cover resolution inputs, applicable assignment identifiers and versions, all selected published packs/rules/content identities, and every mapping revision/content hash/capability-manifest/effective-capabilities identity.
2. Every included published rule must have complete immutable identities and must match the current frozen mapping contract. Legacy, partial, mixed, ambiguous, cross-project, unpublished, or drifted identities fail closed.
3. `readiness` and `prepare` freeze this aggregate identity with the frozen batch/run contract.
4. `execute` re-resolves against the same frozen inputs and rejects any assignment, pack, rule membership/content, mapping, or capability change. It must not silently use a new assignment/pack that appeared after prepare.
5. Add tests for complete success, missing identity, mixed identities, mapping/capability drift, assignment/pack change between prepare and execute, project isolation, idempotent retry, and legacy fail-closed behavior.

### P0-C: `_existing_run` must never cross batch

Locate the current `_existing_run` implementation. If no exact run exists for the requested project + batch + applicable contract, return no run. Remove any fallback that reuses the most recent run from another batch, even when case sets appear equal.

Add regression tests proving:

- no same-batch run returns none/new preparation;
- another batch's most recent run is never reused;
- exact same-batch idempotent retry is reused only when all frozen identities match;
- project isolation and identity drift fail closed.

## Verification

Run focused tests for all three corrections first, then the smallest adjacent backend suites covering rule lifecycle, shadow samples, daily-run service/router, repository state transitions, and app assembly. Use the repository's working Python test interpreter; if `.venv/bin/python` lacks pytest, use `/usr/bin/python3 -m pytest`.

Do not claim the previous `1034 passed` as evidence for these new invariants. Return:

- exact files changed;
- exact tests and counts;
- explicit proof for each P0 item;
- any residual risk;
- no frontend work.
