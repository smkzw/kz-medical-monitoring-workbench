# R1 Integrated Closure Gap Audit (v3 — final narrow corrections)

> Codex final correction: QC acceptance now depends on Store-verified raw output and the actual persisted `ai_candidate` artifact, not merely on non-empty references. A corruption injected after the AI work unit and before QC continuation fails the QC work unit, blocks dashboard/Journey/Query, leaves evidence partial and prevents publication. The synthetic AI-skip path now uses the public runtime lifecycle plus controller reconcile rather than mutating a private attempt journal.

Created: 2026-08-10 (v1), corrected (v2), final narrow corrections (v3)
Audience: Codex (final authority)
Scope: R1 steps 1-13 integration completeness for the isolated synthetic POC.

## 1. Purpose

This audit distinguishes "single module proven" from "one same-run evidence
chain" for R1 steps 1-13. It documents the v1 failures, v2 corrections, and
v3 narrow corrections. It does not claim R1 overall acceptance.

## 2. R1 Step 1-13 Evidence Matrix

| Step | Same-run chain? | Locator |
|---|---|---|
| 1 (Graph IR) | **YES** | 7 work units with real begin/complete |
| 2 (Schema + states) | **YES** | AnalysisState/EvidenceState/OutputState truthful |
| 3 (Fixture) | **YES** | Same accepted snapshots |
| 4 (Vertical) | **YES** | 7-unit manifest: accept→facts→AI→QC→dashboard→journey→query |
| 5 (Engine) | partial | `graph.py` separately |
| 6 (Adapter) | **YES** | Controller + synthetic transport in same run |
| 7 (Progress) | **YES** | `project_audience_progress` from same ledger |
| 8 (Fault) | **YES** | AI fail/skip → BLOCKED; corruption blocks export; idempotent re-entry |
| 9-11 | partial | Module-proven |
| 12-13 (ADR) | N/A | Decision artifacts |

## 3. v3 Corrections (Codex findings on v2)

### 3.1 Evidence state not persisted to Store (CORRECTED)

**v2 failure**: `ClosureResult.evidence_state` said `partial` but
`store.get_run(run_id).evidence_state.value` was `not_evaluable`.

**v3 fix**: Added `store.update_run_state(run_id, evidence=EvidenceState.PARTIAL)`
in the failure path before returning.

**Proof**: `test_failure_evidence_state_matches_store`,
`test_skip_ai_evidence_state_matches_store`.

### 3.2 skip_ai left AI work unit PENDING (CORRECTED)

**v2 failure**: `skip_ai=True` left the AI work unit PENDING, audience progress
was 6/7, headline was "医学监查准备继续".

**v3 fix**: Uses the controller interrupt/reconcile contract to create a real
declared interrupted capability attempt and close the AI work unit as BLOCKED
with zero evidence. All 7 units are terminal; headline is
"本次监查已结束，部分工作未完成".

**Proof**: `test_skip_ai_downstream_blocked` (AI is now BLOCKED, not PENDING).

### 3.3 QC did not verify AI raw/candidate evidence (CORRECTED)

**v2 failure**: QC treated `ai_raw_ref is not None` as verified consumption.

**v3 fix**: QC explicitly calls `store.verify_adapter_raw_output` and
`store.verify_artifact` on the persisted candidate artifact from
`persist_capability_attempt` (found via `adapter_run` domain object's
`candidate_artifact_id`). Exposes `raw_verified` and `candidate_verified`
booleans in payload and node output.

**Proof**: `test_qc_fails_when_ai_raw_corrupted`,
`test_qc_consumes_ai_evidence` (identity chain).

### 3.4 Dashboard artifact projection_count=0 (CORRECTED)

**v2 failure**: `_build_dashboard_artifact` used `proj_dict.get("projections")`
which doesn't exist in `ProjectionBundle.as_dict()`.

**v3 fix**: Now counts `versions` (the actual persisted projection count,
matching `persist_projections` return value). Artifact count matches node
output.

**Proof**: `test_dashboard_artifact_count_matches_persisted`.

### 3.5 INTERRUPT_AFTER_AI continuation test added

**v2 gap**: The public `INTERRUPT_AFTER_AI` hook had no test.

**v3 fix**: Added `test_interrupt_after_ai_then_continue` verifying
Store close/reopen continuation with zero transport calls on resumption.

## 4. Cross-Slice Breakpoints (Still Present, Accepted)

- `background_progress.py` uses its own `SHELL_RUN_ID`.
- UI slices are static fixtures, not Store-derived.

## 5. What This Closure Does NOT Prove

- R1 overall acceptance.
- UI slice runtime connection.
- Real project/provider/clinical data.
- Cross-process concurrency.
