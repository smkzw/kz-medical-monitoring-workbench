# Luna Round-4 Final Delta Review: P10 protocol v9 durable cutover

MODE=CONFERENCE.

## Hard boundaries

- Read-only review. Do not edit files, run tests, start services/providers/
  browsers, access runtime databases or real projects, or make candidate
  decisions.
- Runner-managed output path:
  `runs/conference/monitoring_p10_protocol_v9_contradiction_review_20260801/general_codex_luna_round4.md`.
  Never write it through tools; return the complete report to the parent.

## Read these files only

- `services/api/app/monitoring_ai_repository.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_api.py` only around the verified pre-binding
  compatibility test
- your immediately preceding round-3 findings in session context

Final hashes:

- repository:
  `9141cf512e358bedec243d338a6fab3c0195e9ec5f24893a404eefdab0471443`
- repository tests:
  `a9787efb982e275d1812ce954a516506b91862f6be4a47719ab1d319aa365692`
- protocol tests:
  `9bd1daa3d6df252a05ca7e3d09ebba9e5621a68bf0f2894275f328e198ea8b17`
- API tests:
  `3704acd94839a6f7d0136c4e0d30cc1594a9ce5bf16e380e849cb3a9a71a44f0`

Parent-observed final checks (secondary evidence, do not rerun):

- compile passed;
- repository/protocol/API: 83 passed;
- shared four-file monitoring contract: 439 passed;
- full monitoring with the known unrelated collection blocker ignored:
  1410 passed, 4291 deselected, 27 warnings.

Review only the round-3 P1/P3 corrective:

1. transactional backfill for all three historical `superseded_*` codes;
2. preservation of status, failure evidence, attempts and candidates;
3. defensive retry rejection when marker is empty but old failure code exists;
4. business-key input-only exemption cannot exempt an old supersession code;
5. true pre-marker schema regression for all three codes;
6. prompt/profile/model stale-contract classification plus the verified
   input-only compatibility path.

Note a pre-existing provider-only identity/SQLite uniqueness inconsistency was
observed while attempting a fourth parameter case. It was not modified in this
slice. State whether that is a blocker to this offline v8→v9 acceptance or a
separate residual issue.

Return:

1. `# Luna Round-4 Final Delta Review`
2. `## Boundary Check`
3. `## Findings`
4. `## Evidence And No-Issue Scope`
5. `## Residual Risk`
6. `## Gate Decision And Next Safe Action`

Do not claim runtime, startup, provider, canary, release, or full-Goal acceptance.
