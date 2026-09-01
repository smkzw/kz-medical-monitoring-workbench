# R4 D04 Implementation Acceptance Snapshot v2 — 2026-08-12

Status: `FROZEN_FOR_RECHECK`

This is the Codex-observed corrective implementation snapshot after the first implementation conference rejected v1. Reviewers must verify these exact hashes before and after their read-only recheck. Any drift invalidates acceptance and requires a new snapshot. The rejected v1 snapshot remains immutable historical evidence.

Frozen contract:

- `reviews/medical_monitoring_r4_d04_protocol_pd_slice_contract_v1_20260812.md` — `6d0a7ee2fe507555f68f7a719c60dfa2cc92f995fcaf2c4a3825bbcb3bc6d6b5`

Implementation and focused tests:

- `poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py` — `993d6bea9b10842aa13f8226847961ff3881689a34797c8fdb9d68ac1aa6e5c4`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/lifecycle.py` — `99fec3e3b363f9a85a0a2f24db66a07d02f9dd852096fcf4185fa1e82a45d795`
- `poc/medical_monitoring_ai_native_r4/tests/test_shared_domain_protocol.py` — `5ed4e0843068ecec11e76bedb2eab9c695cdeb36be159b82b8cdacab91f56e5a`
- `poc/medical_monitoring_ai_native_r4/tests/test_lifecycle_projection.py` — `777988eca21c3b7cba5bb1c3efd36e477875805b2393969ce6acfcbac0202a0c`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/protocol.py` — `4665c5113c3f9d9ada10d3c3b2837f181c661d879ae3844f26504685b1127f47`
- `poc/medical_monitoring_ai_native_r4/tests/test_protocol_slice.py` — `b4a607f430b8476cbda90b0afc8d183a8d523bb68ca18ba197da62379fcd88d4`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/protocol_projection.py` — `c4cf09ce3af8fa38aac21087e8aedda43e2d76ebe4f5215e256dfaacd0dc38b0`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/protocol_fixtures.py` — `ea51204401423f3547903993ae2d5b5bc0a7af771a609adf22f3b2cf37e8b30f`
- `poc/medical_monitoring_ai_native_r4/tests/test_protocol_projection.py` — `51fff1dd8b5ee3d06d1dac179da18e8d8214f1ed280ba47cd852b7553ee3e851`
- `poc/medical_monitoring_ai_native_r4/tests/test_protocol_challenge_matrix.py` — `88de9d169a04a97cdbb4ea7ca9c647b231e18e4579c49eb21b74321e35a9d478`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py` — `d5e0050c91fd6c0f2cc36ab7ebbf4991117a697d8cbec084c80f263d98cca5ad`
- `poc/medical_monitoring_ai_native_r4/README.md` — `9858bb4ecb03868975e571dd5f322e62747cedc20dd8f344e415b38399b7ab12`

Corrective delta from rejected v1:

- Protocol transition scope is resolved before the one-feasible-version shortcut. `all_switch`, `new_enrollment_only`, `existing_continue_old`, `next_visit_or_reconsent`, and `undetermined` now have explicit fail-closed semantics.
- Codex independently reproduced the formerly blocking scenarios: a supported existing subject remains on V1.0; missing old-version support, missing enrollment date, or an unresolved next-visit/re-consent trigger returns one `not_evaluable` applicability gate and never V2.0.
- High, ever-user-confirmed, and identity-ambiguous risks have a combined machine-close prohibition test; the user-confirmed case supplies exact linked-negative and closed-ledger prerequisites.
- Audience uncertainty payloads use native Chinese and do not leak raw `not_evaluable` or `AND/OR` tokens.
- Challenge mappings 50, 52, 62, 66, and 78 now target producer-side transition tests, with exact mapping regression locks. The matrix remains 83 continuous rows and 12 adjacent named references.
- Golden projection payload hashes for cases 74 and 82 were updated only after deterministic recomputation following the Chinese wording correction.

Codex-observed deterministic checks immediately before freeze:

- Corrective transition/lifecycle/audience subset: `10 passed`.
- Full R4: `985 passed`.
- Frozen R2: `598 passed`.
- Frozen R3: `339 passed`.
- Ruff: corrected implementation and test files passed.
- compileall: R4 source/tests passed.
- Frozen contract hash unchanged.
- TCP 8911 has no listener.

Session continuity:

- Worker-02 corrective 03 continued provider session `019ff241-42ca-7000-8ece-fb1053207bb3`.
- Worker-03 corrective 02 continued provider session `019ff223-87e3-7000-b551-2e0fc8cf44fb`; no fallback or new worker session was used.

