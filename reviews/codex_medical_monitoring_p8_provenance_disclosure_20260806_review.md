# Codex Review: medical_monitoring_p8_provenance_disclosure_20260806

Date: 2026-08-06 (Asia/Shanghai)
Delegated-agent output: not used; Codex executed the bounded patch directly.

## Verdict

PASS for the bounded offline UI contract; the P8 authority choice remains
pending and the real-loop gate remains blocked.

## Hermes Review Gate

The Hermes workflow guard was used for task initialization and review-gate
validation. No Hermes/provider execution was dispatched for this direct Codex
slice.

## Boundary Check

- The changes stayed inside the workbench monitoring assurance panel, its
  scoped stylesheet, the existing frontend contract test, and this task's
  context/record surfaces.
- No service, provider, browser/Playwright, API login, real-project, source
  token, CAS, B6/C14 or medical-writing action was run.

## Codex Verification

Source-level checks confirmed that the disclosure is rendered only when the
explicit status is `mixed_provenance`; the existing proof shape guard still
rejects mixed proof before proof state commit. The task identity is retained
only to explain the blocker, and the completion policy receives a blocking
reason. Python contracts passed 187, all 37 medical-monitoring Node test files
passed, and the Vite production build passed. Browser and live authority
checks were intentionally not run because the current gate is
`read_only / blocked`.

## Delegated-Agent Output Review

The copy is deliberately provenance-conservative: it says the response
contains service-derived and caller-carried material without claiming which
individual fields are authoritative. The disclosure is collapsed by default,
read-only, and has no submit/review/complete control. No adjacent API or
repository schema was changed. This slice does not select either the
evidence-run ledger or signed-manifest route.

## Residual Risk

Residual risk is unchanged: a mixed proof cannot support medical approval or
completion until the owner selects and implements a deterministic evidence
authority contract, then revalidates the source-token/CAS and formal B6
outcomes. No clinical/scientific or commercial-readiness claim follows from
this UI-only verification.
