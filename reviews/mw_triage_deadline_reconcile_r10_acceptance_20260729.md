# Triage Deadline Reconciliation Acceptance

Date: 2026-07-29

## Verdict

Accepted for a new clean `release-r11` runtime. The frozen `release-r10`
remains `BLOCKED / FAIL` and is not reclassified.

## Reproduced Cause

The durable competitor-triage child reached `completed` and its bound triage
run reached `review_ready` inside the parent's final 2.5-second sleep window.
The parent checked its 900-second deadline before re-reading the child and
therefore persisted `分诊超时` approximately 1.1 seconds after the child was
ready.

## Accepted Behavior

- After the polling deadline, the parent performs exactly one final
  authoritative read of the same durable child and bound run/snapshot.
- A completed child whose same run/snapshot is `review_ready` or `confirmed`
  follows the normal post-triage path.
- Deadline-edge completion and in-window completion share the same return
  contract; the helper does not own the human-confirm pause and cannot bypass
  `auto_confirm_triage`.
- A queued/running child, an unready run, or a failed/cancelled child remains a
  truthful failure.
- The repair neither extends the deadline nor starts/retries AI triage work.

## Evidence

- Production source:
  `services/api/app/medical_writing_research_pipeline.py`
  SHA-256
  `5276cb545e5288a1efdfd71b5bb16f403ec8f910d0919c99122aa95b54d4f628`
- Deterministic regression:
  `tests/test_mw_triage_deadline_reconcile_r10.py`
  SHA-256
  `dd007523a1d4881274ccc8e2c55dbde2784a74f6c22a2b93b247d24a16d9bf2a`
- Worker report:
  `runs/hermes_mw_triage_deadline_reconcile_r10.md`
- Manager review:
  `runs/cursor_mw_triage_deadline_reconcile_r10_manager.md`

## Verification

- Dedicated deadline suite: `9 passed`.
- Directly affected pipeline, durable-triage, recovery, and minimum-start
  suites: `86 passed`.
- Python compilation of production source and regression test: passed.
- The dedicated orchestration test invokes
  `execute_stages(auto_confirm_triage=True)` and proves the deadline-edge path
  calls `continue_after_triage` exactly once with
  `awaiting_triage_confirm` state.

## Remaining Runtime Gate

Run A1 lazy medical-writer E2E in a new isolated `release-r11` runtime with a
new database, ports, browser profile and project. Acceptance requires the
parent to expose one bulk basket confirmation and then create real preparation
and translation work without source edits or gate overrides.
