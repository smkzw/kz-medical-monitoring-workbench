# Codex Review: medical_monitoring_phase_c4_clinical_event_contract_20260802

Date: 2026-08-02 00:49 CST
Execution: Codex direct; no Hermes route, conference, or sub-agent was used.

Changed source/test:
- `services/api/app/monitoring_clinical_event_contract.py`
- `tests/test_monitoring_clinical_event_contract.py`

## Verdict

Pass for the offline shared clinical event/observation contract slice. This is
not an adapter migration, real-project onboarding, risk disposition, or runtime
release decision.

## Boundary Check

- Codex direct work stayed inside the declared C4 source, test and task-record
  surfaces. No delegated-agent output was expected or written.
- `main.py`, existing adapters, frontend, runtime database, services and
  medical-writing files were not changed. The known `main.py` content hash remains
  `0dabf52df865023a3e9f66c880462c3ec66775b1345c2e4a7fe796cdd1d104fc`.
- Ports 8911/5174 remained stopped; unrelated 18911/PID 43191 was not touched.

## Codex Verification

- The contract is pure dataclasses/enums and does not read source files, infer
  clinical links, call adapters, persist data or make medical adjudications.
- It validates explicit project/trial/site/subject and source revision/row
  identity; day/month/year precision with real calendar checks; raw and
  normalized values, units and reference ranges; visit metadata; explicit
  AE/MH/CM/IP/finding/PD/risk links; evidence locators; rule/threshold bindings;
  completeness; uncertainty; deterministic canonical hash and round-trip.
- Local/absolute/path-traversal-like locators, CM/IP aliasing, unbound evidence or
  rule references, observation/event mismatches, normalized values on non-present
  observations, malformed nested payloads and tampered hashes fail closed.
- C4 focused tests: **18 passed**.
- C1-C4 contract tests plus mapping semantic-quality regressions: **131 passed**.
- `python3 -m py_compile` passed for the C4 source and test; `python3 -m ruff
  check` passed.
- No browser/PPT/PDF/live authority check was applicable; no service, database,
  adapter or real-project run occurred.

## Delegated-Agent Output Review

- No delegated output exists because the user explicitly required Codex direct
  execution. The source and tests were reviewed directly against the C4 context
  and the C1-C3 contracts.
- Treatment/clinical/risk links are explicit ID tuples; free text is retained
  only as a raw/normalized value and never creates a relation.
- Evidence and rule references are nested value objects with source binding and
  revision; an event's declared evidence/rules are the only legal references for
  its observations.
- Canonical JSON snapshots prevent later mutation of nested ranges from silently
  changing the event hash. Collection ordering is deterministic.
- No adapter, API, frontend or database surface was widened. Future Timeline,
  Patient Profile, AE/lab/vitals/ECG and risk consumers still require separate
  mapping, UI and runtime integration work.

## Residual Risk

- This is a contract boundary, not proof that existing RUX/MY009/MG-K10 rows can
  populate every field. C3 remains review-only and B6 authority review/B4
  residuals remain unresolved.
- Clinical semantics, complete source coverage, standards/unit mapping,
  treatment identity evidence, event de-duplication and UI projection are still
  open. No authority dual-read, migration, write path or real-project canary is
  permitted from this slice.
- Next safe action: continue offline Phase C contract work (C5 projection/read
  model or equivalent) only after preserving this hash/test evidence; authority
  dual-read/migration remains gated on an explicit B6 outcome and existing
  boundary checks.
