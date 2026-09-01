# Task Context: monitoring_p10_protocol_v9_cutover_direct_tests_20260801

Created: 2026-08-01 10:20:31
Objective: Close the offline P2 test gap for v8-to-v9 protocol prompt cutover: prove failed legacy visibility, same-revision queued v8 no-claim/no-reuse, RUNNING v8 retirement/CAS fail-closed, and distinct v9 creation without starting runtime services or real projects
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `deepseek` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem.
- `context/monitoring_p10_protocol_v9_visible_scope_postpositive_corrective_pause_20260801.md`
- `reviews/codex_monitoring_p10_protocol_v9_visible_scope_postpositive_corrective_20260801_review.md`
- `runs/conference/monitoring_p10_protocol_v9_contradiction_review_20260801/general_codex_luna.md`
- `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`
- Governed code/tests:
  - `services/api/app/monitoring_ai_contracts.py`
  - `services/api/app/monitoring_ai_repository.py`
  - `tests/test_monitoring_ai_repository.py`
  - `tests/test_monitoring_protocol_preparation.py`
- Frozen pre-edit SHA-256:
  - `monitoring_ai_contracts.py` before follow-up:
    `9ee43b88a2de3e8779d4622a43b077f61c3e747fe0c476bc847cfe43b285cf30`
  - `monitoring_ai_repository.py`:
    `f603965c07c3c468b34fdbb15bd86d7bbec597bc3bbc0f5e4fca4bc88dec122d`
  - `test_monitoring_ai_repository.py`:
    `f1521e6a161e9d2b2a2ab1badab9085780025181ddf4e36a4a12c84895213af4`
  - `test_monitoring_protocol_preparation.py`:
    `dd26a2ff10089d06f3053843fd135cb970160a26d19f69ef9a35b056877aa6f6`

External-discovery decision: no web/package scan. This is a bounded internal
state-machine test and retry-boundary correction with no dependency,
architecture, executable-component or tool-adoption choice. The authoritative
evidence is the current repository implementation and frozen v8→v9 contracts.

## Current Observation And Hypothesis

- Prompt supersession retires queued/running legacy jobs to `STALE_INPUT` with
  `superseded_prompt_contract`; terminal completed/failed v8 history is
  preserved when v8 is explicitly listed as terminal legacy.
- `retry_terminal()` explicitly blocks `superseded_workflow_contract`, but
  current source inspection does not show an equivalent block for
  `superseded_prompt_contract` or `superseded_job_contract`.
- Hypothesis: a same-revision prompt-superseded v8 job may be manually revived,
  contradicting the no-retry/no-reuse contract. Prove this with a focused test
  before changing implementation and make the smallest fix only if reproduced.

## Scope

- Writable paths are limited to the three governed files above.
- Required direct coverage:
  1. completed v8 remains visible/queryable with proposed candidate;
  2. failed v8 remains visible/queryable with original failure evidence;
  3. same-revision queued v8 is retired by v9 prompt cutover, cannot be claimed,
     retried or reused;
  4. a claimed `RUNNING` v8 is retired, loses lease/CAS, cannot complete or
     persist candidates, and cannot be retried;
  5. a distinct v9 job is created/selected/claimed while v8 IDs and attempt
     counts remain frozen;
  6. ordinary stale-input revision retry/restore behavior remains unchanged.
- Implementation change is allowed only if the new tests reproduce a real
  contract-retry escape. Keep it repository-generic and surgical.
- Out of scope: prompt/classifier changes, protocol preparation implementation,
  medical-writing, frontend, runtime DBs, services, providers, real projects,
  candidates or canary.

## Success Criteria

- Test-first evidence either disproves the retry escape or reproduces and closes
  it.
- Every contract-superseded state (`workflow`, `prompt`, `job`) is non-retryable;
  normal same-revision stale-input retries and completed-candidate restoration
  remain valid.
- The direct v8→v9 test uses the same protocol input revision for queued/running
  legacy and fresh v9 work, so revision drift cannot explain retirement.
- Late completion from a retired running v8 loses CAS and persists zero
  candidates.
- Focused repository/protocol-preparation tests pass; Codex owns broader
  monitoring and adjacent regression.

## Risk Boundaries

- Do not start 8911/5174, product/provider calls, runtime DBs, browsers, workers
  outside temporary pytest fixtures, or any real project.
- Do not modify/read parallel medical-writing implementation beyond the
  already-recorded read-only drift check.
- Do not retry/reuse any real v4-v8 job and do not make candidate decisions.
- Preserve unrelated filesystem changes and stop if any pre-edit hash differs.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Launch Pi/deepseek once and use a single runner hard wait up to 120 minutes.
- No fixed provider polling, duplicate dispatch or fallback for latency.
- One consolidated same-session follow-up is allowed only after terminal
  completion for a concrete acceptance gap.

## Loop Log

- 2026-08-01 10:20:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- Latest global/project AGENTS and `multi-agent-verification-loop` Skill were
  read in full. Hashes remain `28029e...cd79`, `31d8b1...b001`,
  `40feb6...43a4`.
- 8911/5174 have no listeners; five prior v9 governed hashes match the pause.
- Parallel medical-writing private-symbol drift remains present and read-only.
- No external discovery was run for the bounded reason above.
- Pi session completed one pass without fallback. New tests first reproduced a
  real same-revision retry escape for `superseded_prompt_contract` and
  `superseded_job_contract`; `superseded_workflow_contract` was already blocked.
- Repository-generic fix now treats workflow/prompt/job contract supersession
  codes as non-retryable. No v8/v9 special case was added.
- Post-edit SHA-256:
  - `monitoring_ai_repository.py`:
    `dd550fea87787466519103f9afdbe054847d8729e7dd3f7dba25e2db73034e1d`
  - `test_monitoring_ai_repository.py`:
    `5461d3d7363a71bab888b3e9a803f042f9c8f9d6464e09938c2f44f3b85d61fa`
  - `test_monitoring_protocol_preparation.py`:
    `03da5abd4c1a993ad0873c668dc2297fe4c9fc37f4ab87dc4330be61eb8a9c7b`
- Codex verification: implementation compile; focused shared repository/service
  `429 passed`; full monitoring with the known unrelated collection file
  ignored `1400 passed, 4285 deselected, 27 warnings`; adjacent medical-writing
  contract files `200 passed`.
- Pi read two related source locations beyond the explicit read list while
  preparing its report. No unlisted file was modified. This read-boundary
  deviation must be recorded in final review.
- Parallel `medical_writing_protocol_template.py` changed mtime again at 10:48
  CST with unchanged size; it remains read-only and outside this slice.
- Luna round-2 delta review found a P1 retry escape:
  - preserved failed legacy rows retain provider failure codes and therefore
    are still retryable;
  - already-`STALE_INPUT` obsolete rows are skipped by all three supersession
    selectors and can later be restored/requeued;
  - the initial suffix-based v8 test does not prove the exact production
    business-key path; service fail-loud behavior is not directly covered.
- Selected corrective route: add one-to-one durable contract-retirement
  metadata to `monitoring_ai_jobs`, exposed on `MonitoringAiJob`, rather than
  overwriting original provider failure evidence or adding a separate join
  table. This is the smallest auditable representation:
  `contract_retirement_code`, `contract_retirement_reason`,
  `contract_retired_at`. Supersession operations must mark every obsolete row,
  including preserved terminal and already-stale rows, while keeping existing
  status/failure/candidate transition and return-count semantics.
- Pi same-session follow-up implemented the durable marker, migration columns,
  exact production-key test and service fail-loud test. Focused tests passed.
- Codex broader API verification found that treating every already-stale
  business-key row as permanently retired broke the verified pre-binding field
  mapping compatibility path (409 instead of 202). The final classification
  preserves input-only stale rows only when prompt/profile/provider/model match,
  while contract-obsolete rows remain permanently retired.
- Luna round 3 then found a migration P1: old databases with historical
  `superseded_*` failure codes received empty marker defaults. Codex added
  transactional backfill for all three codes, defensive retry rejection and a
  business-key legacy-code override.
- True pre-marker schema tests cover job/prompt/workflow codes and preserve
  status, failure evidence, attempt count and superseded candidate state.
  Prompt/profile/model contract differences are parameterized; verified
  input-only compatibility remains green.
- Final verification: compile passed; repository/protocol/API `83 passed`;
  shared four-file monitoring contract `439 passed`; full monitoring with only
  the known unrelated collection blocker ignored `1410 passed, 4291 deselected,
  27 warnings`.
- Adjacent medical-writing sample is currently `98 passed, 2 failed` because
  parallel implementation returns empty drafting text while two older chapter
  projection tests still require `待补充`. No medical-writing file was changed.
- Luna round 4 found no P0-P4 blocker and accepted the offline v8→v9 durable
  cutover. A pre-existing provider-only stable-ID/SQLite-unique mismatch is
  recorded as a separate P2 and was not folded into this schema slice.
- Final governed hashes:
  - `monitoring_ai_contracts.py`:
    `ec63cc67067395cac1a436fbc7e65b9d260c4a0a8046ee46b8f3ed624f8c8196`
  - `monitoring_ai_repository.py`:
    `9141cf512e358bedec243d338a6fab3c0195e9ec5f24893a404eefdab0471443`
  - `test_monitoring_ai_repository.py`:
    `a9787efb982e275d1812ce954a516506b91862f6be4a47719ab1d319aa365692`
  - `test_monitoring_protocol_preparation.py`:
    `9bd1daa3d6df252a05ca7e3d09ebba9e5621a68bf0f2894275f328e198ea8b17`
- Final stop check: 8911/5174 have no listeners; no slice-owned
  runner/pytest/worker remains. Unrelated frontend dev server uses 15174.
