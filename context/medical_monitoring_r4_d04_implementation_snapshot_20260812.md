# R4 D04 Implementation Acceptance Snapshot — 2026-08-12

Status: `REJECTED_BY_IMPLEMENTATION_CONFERENCE_REVISE`

This is the Codex-observed implementation snapshot after all first-line corrections. Reviewers must verify these exact hashes before and after their read-only pass. Any drift invalidates acceptance and requires a new snapshot. No implementation/test edits are permitted while the manager or conference reviewers are evaluating this snapshot.

Conference outcome: the medical/protocol reviewer and the engineering fallback reviewer both returned `REVISE`. Codex reproduced the blocking amendment-transition false-certainty scenarios. This snapshot is retained as immutable rejected evidence; subsequent corrections must produce a new acceptance snapshot rather than overwriting these hashes.

Frozen contract:

- `reviews/medical_monitoring_r4_d04_protocol_pd_slice_contract_v1_20260812.md` — `6d0a7ee2fe507555f68f7a719c60dfa2cc92f995fcaf2c4a3825bbcb3bc6d6b5`

Implementation and focused tests:

- `poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py` — `993d6bea9b10842aa13f8226847961ff3881689a34797c8fdb9d68ac1aa6e5c4`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/lifecycle.py` — `99fec3e3b363f9a85a0a2f24db66a07d02f9dd852096fcf4185fa1e82a45d795`
- `poc/medical_monitoring_ai_native_r4/tests/test_shared_domain_protocol.py` — `5ed4e0843068ecec11e76bedb2eab9c695cdeb36be159b82b8cdacab91f56e5a`
- `poc/medical_monitoring_ai_native_r4/tests/test_lifecycle_projection.py` — `777988eca21c3b7cba5bb1c3efd36e477875805b2393969ce6acfcbac0202a0c`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/protocol.py` — `64e1797abfe4e2a5d55d31e9475b948513914d844b522079ebc3db7365bdb968`
- `poc/medical_monitoring_ai_native_r4/tests/test_protocol_slice.py` — `85203b91bd170d1388f07717fbc39aea6698578b13006e1169340a560a7c7f6d`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/protocol_projection.py` — `c4cf09ce3af8fa38aac21087e8aedda43e2d76ebe4f5215e256dfaacd0dc38b0`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/protocol_fixtures.py` — `6fb5f979816a416e6d167786d37b245034bd07d9e9c14472f597c706e6e52590`
- `poc/medical_monitoring_ai_native_r4/tests/test_protocol_projection.py` — `51fff1dd8b5ee3d06d1dac179da18e8d8214f1ed280ba47cd852b7553ee3e851`
- `poc/medical_monitoring_ai_native_r4/tests/test_protocol_challenge_matrix.py` — `88e437945d64203e61209ab4952fd3d0fbc5130bb040d1565ed86cfba26b0fb1`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py` — `d5e0050c91fd6c0f2cc36ab7ebbf4991117a697d8cbec084c80f263d98cca5ad`
- `poc/medical_monitoring_ai_native_r4/README.md` — `9858bb4ecb03868975e571dd5f322e62747cedc20dd8f344e415b38399b7ab12`

Codex-observed deterministic checks immediately before freeze:

- D04/shared focused set: `395 passed`.
- Full R4: `971 passed`.
- Frozen R2: `598 passed`.
- Frozen R3: `339 passed`.
- Ruff: all R4 source/tests passed.
- compileall: all R4 source/tests passed.
- Challenge matrix: 83 rows, continuous numbering 1–83; direct D04 assertions plus 12 named adjacent-test references, all resolved by the passing matrix suite.
- Forbidden audience terms occur only in negative assertions/guard lists, not in generated audience payloads.
- TCP 8911 has no listener.

Runner evidence note:

- Worker-02 follow-up 02 could not directly resume the prior provider handle after the executable night route reset; the runner established provider session `019ff241-42ca-7000-8ece-fb1053207bb3` and used that same session for its automatic incomplete-output completion pass. No different model was substituted. The runner record, rather than the worker narrative, is authoritative for session continuity.
