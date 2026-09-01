# Independent acceptance review: R1 authoritative progress

You are an independent verifier in a fresh context. You did not implement this
work. Return ACCEPT or VETO; do not repair.

Hard boundaries:

- Work only inside the current workbench.
- Remain read-only and do not modify any file.
- Do not start services, touch port 8911, install dependencies, or run real
  providers, harnesses or projects.
- Runner-managed output path:
  `runs/codex_luna_authoritative_progress_reviewer_20260809.md`. Never write
  this path; return the review in your final response for parent consolidation.

Goal: verify that the isolated R1 POC now has a truthful, manifest-revision
authoritative work-unit ledger and structured progress feed, with idempotent
and fail-closed state transitions and exact legacy compatibility. Also verify
that an adjacent `.venv` Seatbelt test-fixture correction declares read-only
runtime material without relaxing the product runtime/default policy.

Read these files only:

1. `context/medical_monitoring_r1_authoritative_progress_20260809_context.md`
2. `poc/medical_monitoring_ai_native_r1/docs/R1_AUTHORITATIVE_PROGRESS_EVIDENCE.md`
3. `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`
4. `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
5. `poc/medical_monitoring_ai_native_r1/tests/test_authoritative_progress.py`
6. `poc/medical_monitoring_ai_native_r1/tests/test_capability_runtime.py`, limited
   to `_python_runtime_read_roots`, `_isolated_harness_profile` and Seatbelt tests
7. `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py`, only as
   needed to prove the production/default policy did not change

Frozen SHA-256 before dispatch:

- domain.py: `42d3119397ac477ccaa2339bd8212ac9629e7b2084838b3d75cf267c8e3de3c6`
- store.py: `fbbb444d8910ae01105dd7823fa47a1b8edba498211bbef413e6e3e4a8b6fa10`
- __init__.py: `955be008d640247cb6076a6312489569ea2840fc6b97c8a81876a4352e77d5e5`
- test_authoritative_progress.py: `0012a29ea4b73ecc0d8dfa353ac5f6f89f59260121a6173a826a0b863c07f81d`
- test_capability_runtime.py: `ab1dd16ccf2f14a84b1726aa866f74d66906cd9e249771028e109209cdf83828`
- capability_runtime.py: `906c48fe1eefc8a9aeb34aafedbbd0c0d74d7b3529c9f5280dd32bf11a2bee9f`

Independently run at least:

```sh
cd poc/medical_monitoring_ai_native_r1
../../.venv/bin/python -m pytest tests/test_authoritative_progress.py -q
../../.venv/bin/python -m pytest tests/test_domain_store_graph.py tests/test_failure_injection.py tests/test_authoritative_progress.py -q
../../.venv/bin/python -m pytest tests/test_capability_runtime.py -q
../../.venv/bin/python -m pytest tests -q
../../.venv/bin/python -m ruff check src/mm_r1/domain.py src/mm_r1/store.py src/mm_r1/capability_runtime.py tests/test_authoritative_progress.py tests/test_capability_runtime.py
../../.venv/bin/python -m compileall -q src/mm_r1 tests/test_authoritative_progress.py tests/test_capability_runtime.py
```

Audit specifically:

- manifest uniqueness, all-node coverage, dependency existence/cycle validation;
- atomic denominator initialization and denominator/ledger mismatch behavior;
- stale revision callbacks, dependency gates and terminal node gates;
- same-request idempotency, conflicting replay rejection and event duplication;
- audit-chain feed consistency, bounded ordering, accurate failure/blocked status;
- exact three-key legacy progress compatibility and historical revision queries;
- execution-identity field restriction and absence of arbitrary raw log/token fields;
- any path that silently changes denominator, overwrites another revision,
  double-counts events or presents failed work as passed;
- `.venv` helper correction only expands the explicit synthetic profile read root
  when actually running in a venv; confirm `capability_runtime.py` SHA is unchanged.

Return only a compact report with:

1. Verdict: ACCEPT or VETO
2. Decisive evidence
3. Findings by P0-P4 (say none if none)
4. Uncovered/residual risk
5. Final SHA-256 stability

Any material correctness, authority, cross-revision, idempotency, information
leakage or evidence-overclaim issue is a VETO.
