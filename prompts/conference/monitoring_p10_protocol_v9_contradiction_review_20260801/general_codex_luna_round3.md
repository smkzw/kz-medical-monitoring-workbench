# Luna Round-3 Delta Review: P10 protocol v9 durable cutover

MODE=CONFERENCE. This is a read-only contradiction and acceptance review.

## Hard boundaries

- Do not edit files, run tests, start services/providers/browsers, access runtime
  databases or real projects, or make candidate decisions.
- Runner-managed output path:
  `runs/conference/monitoring_p10_protocol_v9_contradiction_review_20260801/general_codex_luna_round3.md`.
  Never write this file through tools; return the report to the parent, which
  owns persistence.

## Read these files only

- `context/monitoring_p10_protocol_v9_cutover_direct_tests_20260801_context.md`
- `runs/pi_monitoring_p10_protocol_v9_cutover_direct_tests_20260801_followup1.md`
- `services/api/app/monitoring_ai_contracts.py`
- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_ai_service.py` only around `_create_job`
- `services/api/app/monitoring_ai_router.py` only around
  `_compatible_legacy_field_mapping_revision`,
  `_preferred_field_mapping_revision`, and `start_field_mapping`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_api.py` only around
  `test_formal_start_reuses_compatible_pre_binding_contract_and_candidates`

Frozen final hashes:

- `monitoring_ai_contracts.py`
  `ec63cc67067395cac1a436fbc7e65b9d260c4a0a8046ee46b8f3ed624f8c8196`
- `monitoring_ai_repository.py`
  `aab9f8a6e69703b33e40058e76aae6ba930fec4d560e53b11990a16c51639df6`
- `test_monitoring_ai_repository.py`
  `3a742c0420c51b7b7402ebbd1ad478125a2f0b838a790587f3480f6ddb2a3879`
- `test_monitoring_protocol_preparation.py`
  `9bd1daa3d6df252a05ca7e3d09ebba9e5621a68bf0f2894275f328e198ea8b17`
- `test_monitoring_ai_api.py`
  `3704acd94839a6f7d0136c4e0d30cc1594a9ce5bf16e380e849cb3a9a71a44f0`

Parent-observed checks (secondary evidence; do not rerun):

- compile passed;
- repository/protocol/API: 78 passed;
- shared four-file monitoring contract: 434 passed;
- full monitoring selector with one known unrelated collection blocker ignored:
  1405 passed, 4288 deselected, 27 warnings;
- a deliberately chosen five-file medical-writing adjacent sample had 98 pass,
  2 unrelated failures because current parallel implementation returns empty
  drafting text while old chapter-projection tests still expect `待补充`.
- ports 8911/5174 have no listeners.

Review the final state against your round-2 P1/P3 findings. In particular:

1. Is the durable marker independent of provider failure evidence, backward
   compatible for existing SQLite databases, exposed on the model, first-write
   retained, and checked by `retry_terminal()`?
2. Do prompt/workflow/job supersession mark preserved failed legacy and
   genuinely contract-obsolete already-stale rows without changing their audit
   evidence or return-count semantics?
3. Does the Codex correction after the API regression correctly distinguish an
   already-stale row caused only by input-revision change with the same
   execution contract from a genuinely obsolete prompt/profile/provider/model
   contract? Look for a retry escape or over-retirement.
4. Do tests cover failed v8, completed-to-stale-to-prompt cutover, stale-claimed
   across all three supersession paths, protocol and non-protocol tasks, exact
   production business key, service fail-loud, and verified pre-binding
   compatibility?
5. Identify any P0-P4 blocker to offline acceptance. Runtime/startup/canary are
   explicitly unproven and must remain separate.

Return:

1. `# Luna Round-3 Delta Review`
2. `## Boundary Check`
3. `## Findings` with severity and exact locators
4. `## Evidence And No-Issue Scope`
5. `## Residual Risk`
6. `## Gate Decision And Next Safe Action`

Do not claim runtime, provider, canary, release, or full Goal acceptance.
