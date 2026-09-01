# Task Context: mw_triage_throughput_20260727

Created: 2026-07-27 09:14:52
Objective: Diagnose and minimally repair ClinicalTrials.gov large-indication competitor triage throughput without reducing medical recall or source completeness; changes limited to triage/pipeline adjacent code and tests
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Product implementation:
  - `services/api/app/medical_writing_competitor_triage.py`
  - `services/api/app/writing_reference_repository.py`
  - `services/api/app/medical_writing_authoring_journey.py`
- Focused regression:
  - `tests/test_medical_writing_competitor_triage.py`
- Read-only historical product evidence authorized by the user:
  - `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/writing_reference.sqlite3`
  - immutable snapshot `wref_search_3998701372f95ba40d90`
  - project `proj_ra_greenfield_sandbox`
  - 652 ClinicalTrials.gov candidate records
  - `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/medical_writing_authoring_journey.sqlite3`
  - matching authoring journey revision 31
- Recovery authority:
  - `records/handoffs/codex_retake_20260726/NO_LOSS_PAUSE_20260727_0952.md`
  - `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`
- Global execution contract:
  - `/Users/smkzw/.codex/AGENTS.md`
  - SHA-256 at resume: `1d54ff677fb83d271492b32cecaa15b329f033d11e1759cb1fcb55c6bf0cab6a`

## Scope

- In scope:
  - Reproduce the current reduction plan against the exact 652-record snapshot.
  - Prove exact partition with no omission, duplication, or overlap.
  - Measure deterministic dispositions, AI candidate count, AI batch count,
    serialized batch sizes, and estimated provider-call reduction.
  - Re-run focused retry, partial-failure, progress, cancellation, and durable
    ownership tests.
  - If the current plan fails an acceptance criterion, make the smallest
    triage-adjacent code/test change that preserves medical recall and source
    completeness.
- Out of scope:
  - No writes to shared product databases or existing corpus.
  - No live 652-record provider execution before the bounded plan is accepted.
  - No deterministic indication mismatch exclusion, no corpus override, no
    skeleton fallback, and no model substitution.
  - No broad independent-AI routing, frontend, authoring, or DOCX refactor.

## Success Criteria

- The 652 immutable NCT identifiers form an exact deterministic-or-AI
  partition; duplicate, omitted, and overlapping counts are all zero.
- Deterministic exclusion is limited to explicit non-pharmacologic
  interventions or absence of a public Protocol/SAP.
- Every AI batch contains at most five candidates and at most 25,000
  serialized input characters, except a documented single-candidate outlier.
- The evidence report records old and current provider-call counts and the
  complete reason-code distribution.
- Focused tests for deterministic reduction, retry-only-failed chunks,
  partial failure, cancellation, progress, route identity, and durable
  ownership pass.
- Any product change has a file-level SHA-256 before/after record and is
  independently reviewed before source freeze.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-27 09:14:52: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-27 09:52 CST: Delegated sidecar ended before analysis because the
  selected subagent model reported capacity exhaustion. No product source,
  corpus, database, test fixture, or runtime was changed. The user then
  requested a no-loss pause, so the task was not redispatched. This file
  remains failed-task scaffolding, not a completed task contract or result.
- 2026-07-27 21:50 CST: Resumed from the current no-loss boundary, reread the
  latest global routing contract, and replaced the TODO scaffold with this
  bounded read-only acceptance contract. Existing product code already
  contains deterministic registry reduction and size-bounded AI batches, so
  current behavior will be measured before any implementation change.
- 2026-07-27 21:54 CST: Real replay passed exact partition and bounds:
  562 deterministic records, 90 AI candidates, 18 AI batches, largest input
  7,208 characters, zero overlap/omission/duplicates, and 59.1% fewer estimated
  provider calls than the historical 44-call path.
- 2026-07-27 21:55 CST: Complete focused triage regression passed
  `395` tests. A read-only aishuo/cms-model decision pass was dispatched to
  challenge only the remaining serial-versus-bounded-concurrency release
  judgment.
- 2026-07-27 22:02 CST: The exact `Hermes/aishuo/cms-model` decision pass
  returned `ACCEPT_CURRENT_SERIAL_FOR_RELEASE_ROUND`. Codex checked the
  decision against the replay evidence and focused suite and accepted it:
  current 18-batch serial execution remains the release path. Bounded
  concurrency is deferred unless a real run observes batch P95 above 30
  seconds with total duration above 10 minutes, three or more consecutive
  provider-limit failures that also fail retry, or more than 200 AI candidates
  and total duration above 15 minutes. This preserves the current claim lease,
  cancellation, ordered persistence and retry-only-failed-batch semantics.
  The worker report is
  `runs/execution/mw_triage_throughput_20260727/worker_aishuo_throughput_decision_01.md`.
