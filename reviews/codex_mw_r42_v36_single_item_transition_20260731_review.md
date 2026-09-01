# Codex Review: mw_r42_v36_single_item_transition_20260731

Date: 2026-08-01 00:20 CST
Delegated-agent output: `runs/codex_mw_r42_v36_single_item_transition_20260731.md`

## Verdict

**PASS — READY_FOR_CLONE_AUTHORIZATION.**

The bounded offline implementation and acceptance are complete. Runtime
execution is intentionally not included and remains unauthorized.

## Boundary Check

- Product/test writes were limited to the four declared connected files.
- Additional writes were confined to this task's `context/`, `plans/`,
  `prompts/`, `runs/`, `reviews/`, `logs/`, and `metrics/` records.
- The guard-reserved
  `runs/codex_mw_r42_v36_single_item_transition_20260731.md` and its stdout
  were not edited.
- Neither original r42 nor clone runtime was executed or modified. No service,
  OCR, translation, download, old attempt, ready item, or excluded item was
  run.
- Independent participants and chair state that they did not inspect either
  prohibited runtime or edit source.

## Codex Verification

- Existing batch retry was traced to `failed_retryable` only. It is a no-op for
  the frozen source state and cannot safely transition the
  `fidelity_blocked` item.
- The new route pins source batch + item + attempts + immutable lineage and
  derives the current target contract server-side.
- Deterministic temporary-repository tests prove:
  - source batch and all 20 source item payloads are byte-identical;
  - 4 ready and 15 excluded rows are unchanged;
  - child batch has exactly one new item;
  - old plan/chunk/integration/run/translation rows remain byte-identical;
  - target plan/chunk/integration/translation IDs are new;
  - VISIT/SCHEDULE pass current v36 preflight while omitted ECG fails closed;
  - duplicate request, worker takeover, restart-before/after dispatch intent,
    and persisted-output recovery do not duplicate model calls or rows.
- `python3 -m py_compile` passed for all changed Python files.
- `python3 -m unittest -q tests.test_writing_reference_translation_batch
  tests.test_writing_reference_translation_durable_jobs
  tests.test_mw_v11_translation_alignment`:
  **258 tests in 12.287s, OK**.
- Final product/test hashes match the values frozen in the task context.
  Five connected preserved files and the r42 checkpoint still match intake.
- Ports 55342, 55343, and proposed 55344 had no listener at final inspection.

## Delegated-Agent Output Review

- Initial native review reproduced one P1 takeover race; it was repaired and
  the same native child returned READY on delta recheck.
- Pi/DeepSeek initial review identified one accepted fail-closed decision and
  four actionable P4 gaps; all actionable gaps were repaired, and the same Pi
  session returned READY.
- Pi/Alibaba chair independently traced the current code, reran 258 tests, and
  returned READY with no unresolved P0-P4.
- The native app dispatcher did not expose the child's actual model selector;
  records therefore retain the declared route and explicitly avoid claiming
  an unverified literal selector. Pi participant and chair runtime identities
  were verified by their runners; neither used fallback.

## Residual Risk

- A committed model-call intent with no provable persisted output terminates as
  `model_call_outcome_unknown_after_restart`. It cannot be auto-reopened
  without risking an unprovable duplicate provider call.
- Runtime facts remain frozen at the last read-only clone observation.
  Authorization-time preflight must revalidate them before any mutation.
- This review authorizes only preparation of the clone-only request, not
  execution.

## Runtime Addendum — 2026-08-01 00:58 CST

### Current verdict

**TARGET RESULT PASS; EXECUTION CONTRACT DECISION REQUIRED.**

After exact user authorization, Codex executed one clone-only request. The
single child reached `candidate_ready`; job attempt count was 1; all protected
old rows remained byte-equivalent; original r42 remained unchanged; integrity,
foreign keys, port closure, and gate release passed.

The real integration path produced two new upper-layer stage-run rows and one
new escalation row for the target child: Flash QC completed degraded after its
attempted body mutation was rejected, then Pro escalation failed terminal.
The deterministic gate preserved the Hy output and passed it. These are
auditable, target-bound, non-duplicated calls, but their table classes were not
listed in the clone authorization's allowed-row enumeration.

The full runtime file comparison also detected physical SQLite/SHM changes in
the clone's monitoring-batches and monitoring-daily-runs stores. Independent
logical table comparison against the APFS snapshot found identical schema and
rows, with integrity OK; this is a startup/WAL physical delta, not a monitoring
business-data delta. It is nevertheless retained as a strict file-boundary
exception because the user excluded concurrent medical-monitoring files.

Codex therefore stopped the API and recorded
`runs/MW_R42_V36_CLONE_TRANSITION_SCOPE_DELTA_PAUSE_20260801_0058.md`.
No rollback, repeat request, or further model call is authorized. Offline
READY remains valid; runtime acceptance awaits the user's scope decision.

### Read-only root-cause conclusion

The target-bound Pro escalation is the deterministic implementation of the
current upper-layer contract: `completed_degraded` is explicitly escalation
eligible, and a failed Pro child causes the service to select the usable
Flash-degraded/Hy-preserved parent output. It is not a duplicate-call race.

The monitoring physical delta is likewise deterministic for the authorized
full-app command: `main.py` constructs both monitoring repositories at import
time, and their constructors immediately initialize WAL-backed SQLite stores.
The current code has no medical-writing-only startup surface. Future
file-isolated runs require a separate app/executor or a fail-closed lazy
subsystem initialization contract; they must not reuse full `main:app`.

## User Acceptance Addendum — 2026-08-01 08:45 CST

**FINAL VERDICT: RUNTIME ACCEPTED — PROTOCOL PHASE 0A CLOSED.**

The user explicitly accepted the target-bound upper-layer lineage and the
clone-local monitoring SQLite/SHM physical-only delta with zero logical
schema/row difference. This acceptance does not weaken the preserved
invariants: the old r42/v35 rows remain immutable, the original r42 runtime
remains unchanged, and the completed POST/idempotency scope must never be
replayed.

The next Protocol P0 work must use the current filesystem as truth and must
not use full `main:app` for a claim of strict medical-writing file isolation.
