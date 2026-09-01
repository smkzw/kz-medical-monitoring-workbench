# Task Context: monitoring_p10_v9_retirement_timestamp_corrective_20260801

Created: 2026-08-01 12:28:10
Objective: Preserve updated_at on marker-only contract retirement for terminal/already-stale monitoring AI history while retaining updated_at transitions for active retirement; add direct regressions and revalidate before v9 canary attempt 2
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `deepseek` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem.
- `runs/execution/monitoring_p10_v9_isolated_canary_20260801/ATTEMPT1_ZERO_SUBMIT_GATE.md`
- `context/monitoring_p10_v9_isolated_canary_20260801_context.md`
- `services/api/app/monitoring_ai_repository.py`
- `tests/test_monitoring_ai_repository.py`
- `tests/test_monitoring_protocol_preparation.py`
- Frozen pre-edit SHA-256:
  - repository:
    `9141cf512e358bedec243d338a6fab3c0195e9ec5f24893a404eefdab0471443`
  - repository test:
    `a9787efb982e275d1812ce954a516506b91862f6be4a47719ab1d319aa365692`
  - protocol test:
    `9bd1daa3d6df252a05ca7e3d09ebba9e5621a68bf0f2894275f328e198ea8b17`

## Scope

- In scope:
  - change marker-only contract supersession so adding the immutable
    `contract_retirement_*` fields does not overwrite `updated_at`;
  - retain `updated_at=now` when a queued/running/blocked/non-preserved row
    actually transitions to `stale_input`;
  - add direct regressions proving updated-at preservation for already-stale
    rows and preserved completed/failed legacy prompt rows;
  - run only focused repository/protocol tests in the worker pass.
- Out of scope:
  - provider-only identity/SQLite unique migration;
  - any other repository behavior, prompt, service, runtime, provider, project,
    candidate or medical-writing change;
  - canary attempt 2, broad/full test acceptance or release decisions.

## Success Criteria

- Marker-only SQL updates only the three retirement fields.
- Active retirement SQL still transitions status/failure/lease/retry fields and
  updates `updated_at`.
- Tests fail under the pre-edit behavior and pass after the edit for:
  - an already-stale row receiving a first retirement marker;
  - preserved completed and failed v8 rows receiving prompt-retirement markers;
  - active queued/running retirement continuing to advance `updated_at`.
- Existing retry fail-closed, candidates, provider evidence, first-marker
  immutability and input-only compatibility remain covered.
- Worker returns exact changed paths, test commands/results, hashes and
  residual risk. Codex independently reviews and broadens verification.

## Risk Boundaries

- Writable product paths are exactly:
  - `services/api/app/monitoring_ai_repository.py`
  - `tests/test_monitoring_ai_repository.py`
  - `tests/test_monitoring_protocol_preparation.py`
- Writable task record is runner-owned
  `runs/pi_monitoring_p10_v9_retirement_timestamp_corrective_20260801.md`;
  the worker returns the report and does not write it directly.
- Preserve unrelated user/parallel-agent changes. Stop if any frozen hash does
  not match before editing.
- Do not modify runtime, backups, canary evidence, medical-writing files or any
  other product path.
- Do not start services, providers, browsers, real projects, ports, workers or
  candidates.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Dispatch Pi/deepseek-v4-flash once at max effort and wait on the runner hard
  wait up to 120 minutes. No fixed-interval polling or duplicate dispatch.
- Same-session follow-up is allowed only after terminal output and one
  actionable gap. Fallback only on terminal failure or failed acceptance after
  the allowed recovery pass.

## Loop Log

- 2026-08-01 12:28:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- Trigger evidence: isolated startup produced all 12 correct retirement markers
  but changed every preserved terminal/already-stale `updated_at`; attempts,
  candidates and all other inspected historical fields remained unchanged.
- Pi/deepseek-v4-flash session completed once with no fallback. It removed
  `updated_at` only from the marker-only UPDATE, retained it in the active
  transition UPDATE, added three direct repository regressions, and left the
  protocol test file unchanged.
- Codex verification:
  - compilation passed;
  - project `.venv` three-file repository/protocol/API gate:
    `86 passed`;
  - standard `tests -k monitoring` remained collection-blocked only by the
    pre-existing parallel medical-writing import of
    `_REQUIRED_CORE_BODY_SEMANTIC_IDS`;
  - excluding exactly that one unrelated collection file:
    `1413 passed, 4301 deselected, 27 warnings`;
  - adjacent AI-role and medical-writing seven-file sample:
    `142 passed, 17 warnings`.
  A first Codex run through the default Homebrew Python 3.12 failed collection
  only because that interpreter lacks `cryptography`; rerunning through the
  project `.venv` resolved the environment mismatch without installing
  anything.
- Current-code replay on a fresh copy of the real pre-marker monitoring backup
  returned integrity `ok`, all 12 markers (`3 job + 9 prompt`), zero unmarked,
  zero queued/running/v9, and exact before/after fingerprints for all historical
  pre-marker fields:
  - jobs `85eb5fbc...15e97`;
  - attempts `e5530e5e...30f63`;
  - candidates `ddb85eca...d8ee2`.
- The existing Luna reviewer completed one same-session read-only review after
  one hard wait. Decision: **PASS for attempt-2 zero-submit preparation only**.
  It found no P0-P3; only a non-blocking P4 opportunity for dedicated
  workflow/job marker-only timestamp tests. No POST/runtime/provider/canary or
  release acceptance is implied.
