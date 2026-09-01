# Codex Review: mw-protocol-progress-batch

Date: 2026-07-30
Delegated-agent output: `runs/kimi_mw-protocol-progress-batch.md`

## Verdict

Revise, then focused checks passed. Browser acceptance remains pending.

## Boundary Check

- The worker changed only its six authorized source/test surfaces.
- No runtime database, corpus-scope implementation, or production artifact was
  changed by the worker.
- Codex separately changed the preparation-batch contract/service/frontend and
  OCR probe surfaces under the parent task; those are not attributed to Kimi.

## Codex Verification

- Retained the one-click action over the currently filtered eligible rows.
- Retained pinned `(translation_id, translation_revision)` targets and
  per-item approved/skipped/stale/failed outcomes.
- Rejected and removed the empty-target API shortcut because it could confirm a
  revision the writer had not reviewed.
- Confirmed the endpoint still rejects stale revisions and never conceals other
  row outcomes.
- Focused results after revision:
  - translation batch and frontend contract: 60 passed;
  - AI-role and preparation-batch suites: 40 passed;
  - visual probe subset: 4 passed;
  - Vite production build: passed, 1910 modules.

## Delegated-Agent Output Review

- Good: bounded API and frontend action, explicit revision pinning, optimistic
  concurrency reuse, idempotent per-item keys, and clear per-item outcomes.
- Corrected: the report explicitly called out empty targets as residual risk;
  Codex made that route invalid rather than accepting the risk.
- Accepted: one batch audit event can exist for an idempotent retry attempt;
  the underlying review/admission records are not duplicated.
- Still to inspect in the real browser: placement, disabled state, filtered
  count, success/partial-outcome notice, and post-action refresh.

## Residual Risk

The rendered UI and a live safe-fixture click have not yet been accepted.
