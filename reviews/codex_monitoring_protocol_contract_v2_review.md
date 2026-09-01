# Codex Review: monitoring_protocol_contract_v2

Date: 2026-07-30
Execution: Codex direct in the user-authorized main workspace; no delegated
write pass was used.

## Verdict

Pass for the bounded backend slice.

## Boundary Check

- Product code changes are limited to the protocol-preparation contract,
  protocol-preparation service, and the monitoring AI repository state machine.
- Test changes are limited to `tests/test_monitoring_protocol_preparation.py`.
- `monitoring_ai_router.py` and `tests/test_monitoring_ai_api.py` were not edited.
- Frontend, medical writing, field mapping, daily run, and real runtime state
  were not modified.

## Codex Verification

- `tests/test_monitoring_protocol_preparation.py`: 21 passed.
- Adjacent repository/startup/service/source-packet/protocol suite: 183 passed.
- Ruff: passed.
- Python compile check: passed.
- No listener was started on API port 8911.
- Existing unrelated local API process on port 55222 was observed but not
  started, stopped, or used by this slice.

## Delegated-Agent Output Review

Hermes dispatch was not started, so no delegated output was accepted as
evidence. Codex inspected the state-machine paths directly and verified the
highest-risk legacy-to-v2 transitions with temporary test repositories only.

## Residual Risk

- Startup retirement is intentionally attached to the existing repository
  recovery entrypoint (`expire_exhausted_leases`) to avoid modifying the main
  application startup surface during concurrent work. The official startup path
  invokes this entrypoint before worker wake.
- Historical accepted/rejected candidate decisions are preserved; this slice
  does not reinterpret or migrate them into v2.
- No real runtime cutover or three-project regeneration was performed.
