# Codex Review: medical_monitoring_r1_gap_audit_20260809

Date: 2026-08-09
Independent verifier: native fresh-context `/root/capability_runtime_review`

## Verdict

PASS for the isolated provider-neutral capability-runtime slice only. R1 overall remains
incomplete and no real API/provider/harness, product surface or clinical project is accepted.

## Boundary Check

- Writes remained inside `poc/medical_monitoring_ai_native_r1/` and this task's existing
  `context/`, `reviews/` and `metrics/` records.
- No product source, medical-writing subsystem, shared runtime/package, 8911/service,
  credentials or real project was read for execution or modified.
- API transport was injected and offline; harness execution was an explicit local synthetic
  argv with `shell=False`.

## Hermes

The tracked task was initialized with `hermes_workflow_guard.py init-task`. Implementation
was performed directly by Codex because the route was `codex/codex-main/high`; an independent
fresh-context native verifier owned acceptance. No Hermes provider execution, real provider
call or undeclared fallback occurred.

## Codex Verification

- Inspected the existing ModeContract, ClaimCoverageLedger, adapter, Store and failure-matrix
  surfaces before selecting the gap; modes and ledger were not rebuilt.
- Reproduced focused capability tests and the full R1 core suite after repairs.
- Checked candidate-only authority, mandatory manifest revision checks, response execution
  identity, raw-before-candidate persistence and exact coverage denominator constraints.
- Browser/PPT/PDF checks are not applicable to this non-UI runtime slice. Slice 4 visual
  evidence remains separately accepted and protected.

## Delegated-Agent Output Review

The verifier issued two evidence-backed VETOs before acceptance. The first exposed coverage,
manifest/resume, timeout/cancel, deadlock, raw preservation/order, identity and sensitive-input
gaps. The second reproduced status/reason/`expected=false` pollution of the expected coverage
denominator. Codex repaired each issue and added deterministic regressions. The third pass
accepted frozen implementation/test hashes with `25 passed` focused and `128 passed` core.
After that freeze, only the inaccurate persistence-order docstring in `adapters.py` changed;
behavior is revalidated during closeout.

## Residual Risk

- allowed-tools and context isolation are still declarations, not an enforced sandbox;
- cross-process interruption/restart/checkpoint/duplicate/late-callback recovery is open;
- raw corruption-on-read and whole persistence crash atomicity are open;
- real API/provider/harness compatibility, explicit fallback and keychain integration are open;
- ensemble/adjudication and unavailable token/cost semantics are open;
- non-cooperative API transport may continue below the domain-side timeout/cancel boundary;
- executable identity does not yet cover every transitive dependency;
- credential/environment/argv derived-hash policy still needs explicit later governance.
