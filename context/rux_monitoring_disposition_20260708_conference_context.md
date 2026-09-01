# Conference Context: rux_monitoring_disposition_20260708

Created: 2026-07-08 17:48:57
Objective: Implement and verify a minimal RUX medical monitoring risk disposition loop: reviewed -> query_draft -> submitted_for_approval, preserving mark_read as notification state and using real RUX project risks.
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes Sub-Venue

- Lead/chair: OpenCode Go `minimax-m3`.
- Participant models: OpenCode Go `qwen3.7-plus`, OpenCode Go `mimo-v2.5`, and DeepSeek supplier `deepseek-v4-flash`, all default reasoning effort unless Codex overrides.
- All `deepseek-v4-flash` routes must use the DeepSeek supplier. OpenCode Go `deepseek-v4-flash` is not allowed for this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: DeepSeek supplier `deepseek-v4-pro` only. OpenCode Go `deepseek-v4-pro` is not allowed for this role.

## Source Of Truth

- User requirement: RUX 医学监查 must move beyond “已读” to a real medical disposition loop. `mark_read` is notification state only and must not be treated as medical review.
- Local authoritative code/tests:
  - `services/api/app/workbench_inbox.py`
  - `packages/contracts/workbench_contracts/models.py`
  - `services/api/app/rux_monitoring_service.py`
  - `services/api/app/main.py`
  - `frontend/src/App.jsx`
  - `frontend/src/styles.css`
  - `tests/test_workbench_inbox.py`
  - `tests/test_frontend_monitoring_contract.py`
  - `frontend/tests/rux_monitoring_inbox_qc.mjs`
  - `frontend/AGENTS.md`
  - `logs/subsystems/medical_monitoring_log.md`
  - `logs/system_build_log.md`
- Current RUX risk anchors:
  - project id `proj_rux_03_002`
  - subjects `S01017`, `S01003`, `S03040`
  - current risk rows are generated from real RUX listing/protocol anchors through `RuxMonitoringService.evaluate_subject_risks()`.
- Existing accepted boundary:
  - RUX P0 inbox is a risk-anchor workflow, not a full 192-subject RUX commercialization claim.
  - `dose_adjustment`, study drug pause/restart, and other investigational-product changes are separate from CM; CM means non-investigational concomitant medication/treatment only.
  - UI and API must not expose `/Users/`, hash/storage internals, lifecycle numbering, or overclaim formal/clinical/regulatory completion.

## Scope

- In scope:
  - Extend the workbench inbox action contract for RUX medical monitoring risk disposition.
  - Preserve `mark_read` as a separate notification/read-state action.
  - Add a persisted, auditable disposition overlay using the existing inbox action store or a clearly bounded adjacent store.
  - Support the minimum ordered state machine:
    - initial: `待医学复核`
    - action `mark_reviewed`: display `已医学复核`
    - action `create_query_draft`: display `Query草稿`
    - action `submit_for_approval`: display `已提交审批`
  - Enforce invalid transition failures, including submit-before-query and query-before-review.
  - Require user comments/query draft text where medically necessary.
  - Keep item visible after disposition; status changes should be visible in inbox/risk detail.
  - Add desktop-first UI controls in `RiskDetail`.
  - Extend unit/static/browser QC.
- Out of scope:
  - Full 192-subject RUX monitoring scale-out.
  - EDC or CTMS live query writeback.
  - Formal e-signature, eTMF filing, or regulatory submission.
  - AI-generated query text if external AI is not configured. Manual/query-template drafting must still work without AI.
  - Reclassifying investigational product changes as CM.

## Success Criteria

- Backend:
  - `mark_read` only affects unread state.
  - disposition actions persist audit records with action, actor, comment, source_version, and timestamp.
  - state labels and `needs_action` reflect the latest valid disposition action.
  - invalid transition attempts raise a clear API error and do not mutate state.
  - public payloads contain no local paths, lifecycle labels, hash/storage fields, or formal approval overclaims.
- Frontend:
  - risk detail shows state-aware controls for `标记已复核`, `记录Query草稿`, and `提交审批`.
  - controls are disabled or messaged when transition preconditions are not met.
  - status updates after action without deleting the risk item.
  - Subject Timeline and Patient Profile handoff buttons remain visible.
  - desktop layout has no horizontal overflow.
- Verification:
  - TDD red tests are observed before implementation.
  - focused unit/static tests pass.
  - frontend build passes.
  - browser QC runs the risk through review -> query draft -> submit approval on a real RUX risk item.
  - full regression is run before any completion claim.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-08 17:48:57: Conference initialized by `hermes_workflow_guard.py init-conference`.
