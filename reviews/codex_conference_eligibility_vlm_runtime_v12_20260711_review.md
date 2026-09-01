# Codex Conference Review: eligibility_vlm_runtime_v12_20260711

Date: 2026-07-11

## Verdict

Accepted for its bounded, fail-closed purpose. No bounded-slice P0/P1 defect was reproduced. This is not production VLM authorization; all seven canonical release gates remain closed.

## Boundary Compliance

- Prompts passed preflight after removing the generated absolute workspace line.
- Participants wrote only their assigned outputs and did not edit product code.
- Antigravity was excluded because this was not a visual conference.
- The required Hermes chair ran on the `aishuo` custom endpoint with exact `MiniMax-M3` runtime markers. No chair fallback occurred.

## Participant Outputs Reviewed

- Qwen, Mimo and Reasonix DeepSeek Flash produced substantive independent outputs.
- Qwen classified durable circuit, in-flight revocation and production profile registration as P0. Codex treats these as production release gates, not defects introduced by the bounded v12 slice.
- Mimo and DeepSeek Flash found no bounded-slice P0; both recommended the durable multi-process circuit as the next slice.

## Hermes Sub-Venue Review

The 335-line `aishuo/MiniMax-M3` package compared all participants and inspected the current implementation. Codex accepts its convergence on durable circuit state as the next slice and its rejection of Qwen's audit-UNIQUE concern. Codex does not accept two chair statements as evidence: VLM audit rows currently do not contain actor/identity columns, and the mutable test dictionary is not proof that a production governance resolver is stateless. These remain explicit identity/governance design obligations.

## Main-Venue DeepSeek Pro Review

Reasonix `deepseek-pro` completed a 328-line independent review. It agreed that durable circuit state, in-flight authorization semantics and production profile registration are forward release gates rather than defects introduced by v12. It identified one factual error in the Hermes package: `eligibility_vlm_audit_events` has no `actor` or `authenticated_actor` column, so any bounded identity work requires an additive migration.

Codex accepts the main review's wall-clock persistence requirement for a restart-safe breaker and its call for a single canonical gate list. Codex does not accept the suggested literal `authenticated_actor="operator_console"` as an identity implementation; a hardcoded actor would not establish authentication. Identity remains a separate closed gate.

## Codex Independent Verification

- Three pre-implementation and two post-implementation Codex SubAgent audits were reviewed and reproduced where material.
- Added and verified attempt/lease fencing, source binding, generic-worker exclusion, server-owned policy resolver, profile collision guard, profile attempt limit, size-before-read guard and privacy-bounded projections.
- Ruff passed on all changed Python files.
- Focused VLM/evidence/QC/migration suite passed 96/96.
- Whole repository regression passed 532/532 in 205.951 seconds.
- Frontend production build passed; existing >500 kB chunk warning remains.
- No runtime database exists under `runtime/`; no active database was migrated.
- No real clinical image was processed and no real VLM profile was enabled.
- A fresh v12 database passed `PRAGMA integrity_check` and `PRAGMA foreign_key_check`; direct `PRAGMA table_info` confirmed the audit table's 13 columns and the absence of actor/identity fields.
- The production API and worker instantiate `SqliteRuntimeStore` without a controlled-artifact policy resolver. VLM registration therefore fails closed. There is no production resolver whose statelessness can currently be claimed or tested.

## Final Decision

Accept v12 as a durable, nonclinical, fail-closed runtime foundation. Do not describe it as production-auditable or production-enabled. The canonical seven release gates are recorded in `VLM_DURABLE_RUNTIME_V12.md`.

The next bounded implementation slice is durable multi-process circuit state with restart-safe single half-open admission, wall-clock persistence and explicit concurrency tests. Identity, clinical authorization and visual QC remain separate gates. The prior chair assertion about an existing actor column is superseded by direct schema evidence.
