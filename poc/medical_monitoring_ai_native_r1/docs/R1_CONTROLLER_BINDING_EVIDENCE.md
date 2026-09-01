# R1 application-owned controller binding evidence

Date: 2026-08-10  
Scope: isolated synthetic/offline R1 POC only

## Outcome

The application-owned controller now closes the provider-neutral capability-attempt / manifest
work-unit loop without introducing another scheduler or giving AI output medical authority.
The slice was accepted by an independent Luna review after two bounded VETO/remediation rounds.
Final independent verdict: **ACCEPT; P0/P1/P2/P3/P4 = 0**.

## Implemented contract

- `controller.py` pre-registers one immutable `capability_work_assignment` before dispatch. The
  assignment freezes the full JSON-RPC request, request hash, profile fingerprint, run, manifest
  revision, node, work unit and Chinese audience text.
- `CapabilityRuntime` notifies the controller only after durable journal claim/replay and before
  transport. Cached/terminal replay follows the same observer contract and performs no duplicate
  transport.
- `Store.bind_capability_attempt_to_work_unit` independently revalidates the version-1 assignment,
  exact request/identity, audit evidence and target work unit. A declared-but-unclaimed attempt or
  a claimed attempt without assignment cannot create audience-visible `running` progress.
- Before a terminal work unit may become `passed` or `failed`, Store verifies the complete
  `persist_capability_attempt` footprint: immutable raw output, adapter binding/run/analysis,
  execution profile, frozen attempt request, every work event and the candidate artifact when one
  exists. Store recomputes the evidence count; callers cannot assert it.
- `complete` maps to `passed`; `failed/timeout/cancelled/partial/truncated` map to `failed`;
  `interrupted` maps to `blocked` with zero terminal evidence. Strict `continued_from` permits the
  same work unit to reopen for a new retry attempt without rewriting prior audit history.
- Raw transport failure, timeout, cancellation and no-response paths retain bounded immutable raw
  evidence. AI artifacts remain candidate-only; no canonical facts, review authority, publication
  or user confirmation are created.

## VETO corrections

First review challenged:

1. concurrent conflicting assignment could create version 2;
2. a declared attempt could bind without durable claim;
3. failed/blocked work-unit closure could break strict runtime continuation.

Those were corrected by transactional immutable-object re-read, claim gating and explicit
retry/reopen semantics. The next review challenged:

4. journal terminal state could close a work unit without persisted raw/candidate evidence;
5. a claimed attempt could bypass controller assignment and create `running`.

Those were corrected by Store-owned assignment revalidation and Store-derived persistence-footprint
verification. The same persistent reviewer session then reproduced both old bypasses as fail-closed
and returned ACCEPT.

## Decisive verification

```text
controller + authoritative progress: 51 passed
controller + authoritative progress + capability runtime + audience progress: 170 passed
R1 core: 273 passed
scoped Ruff: All checks passed!
compileall: pass
8911 listener: none
```

Independent reviewer replay:

```text
NO_ASSIGNMENT_BIND=REJECTED: StoreError
NO_ASSIGNMENT_STATUS=pending
NO_PERSISTENCE_COMPLETE=REJECTED: StoreError
NO_PERSISTENCE_STATUS=running
PERSISTED_FAILED_STATUS=failed
PERSISTED_FAILED_EVIDENCE=8
INTERRUPTED_STATUS=blocked
INTERRUPTED_EVIDENCE=0
cross-manifest continuation: rejected before a new assignment is written
independent focused regression: 51 passed
```

The last accepted adjacent UI suites remain AE/MH audience `18 passed` and Patient Journey
`16 passed`; they were not rerun in this controller-only no-browser slice.

## Independent review route

Native App Luna child creation was explicitly unavailable, so the global contract's CLI
compatibility route used `gpt-5.6-luna` at max effort. Persistent session
`019fe746-ded2-7b83-9636-ff75466cacd2` produced the final follow-up ACCEPT record at
`runs/codex_medical_monitoring_r1_controller_binding_20260809_followup.md`.

## Frozen accepted implementation hashes

- `controller.py`: `2c2258074148179be4e67861f59d98723335b3dd37c16e50cfae39e814626070`
- `capability_runtime.py`: `21efb387d75155738b3155d674be21ac0b62a1c35fbb253aa0fb711790247bef`
- `store.py`: `741dad9110711b3d6a59039c9ef41f3d578d9bd39ce201955a71ae280929c0bc`
- `test_controller.py`: `4c4532938edeb350d2e61403c8a5289f20ef49d0e20c79771f1895dd6bc2dbfb`
- `test_authoritative_progress.py`: `5ec88b919e4237c410cc47a914beafacc4002d1516a8c3cc5d7c1b9dc3bfc778`

## Boundaries and residual risk

This is not R1 overall acceptance and not product/service acceptance. UI/browser, background
service hosting, real provider/endpoint behavior, real projects and port 8911 were deliberately not
used. The macOS Seatbelt path remains a synthetic POC containment mechanism, not a production
sandbox. The next slice may consume only this accepted controller projection in an isolated
synthetic UI/background-shell integration; it must not bypass the Store ledger or expose internal
provider/attempt/backend identifiers to users.
