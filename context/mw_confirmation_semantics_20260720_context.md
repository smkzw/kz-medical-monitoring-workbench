# Task Context: mw_confirmation_semantics_20260720

Created: 2026-07-20 13:58:59
Objective: Remove redundant second medical-approval stages from the medical-writing workflow: an authenticated medical manager's explicit selection, adoption, confirmation, or manual save is the approval event; preserve audit snapshots and quality/source gates without a duplicate approval center action.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: guard defaulted to `codex` / `codex-main` / `high`.
User-level project routing overrides the implementation manager to the existing
visible QoderVIP `qodercli` / `Qwen3.8-Max-Preview` session. Because this is
unrelated to the currently running autonomy probe, the manager must begin with
`/new` before receiving the complete task packet. Codex remains final authority.

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User decision: the signed-in user is the medical manager. When that user
  explicitly selects, adopts, confirms, or saves content, that action is the
  medical decision. The product must not show another "待医学批准" step.
- `tests/test_medical_writing_authoring_prefill.py`, especially
  `test_no_second_approval_object_created`, is the already-landed narrow
  contract: adoption produces `user_confirmed` and no second approval object.
- Current contradictory surfaces include:
  - `frontend/src/features/evidence-design/EvidenceDesignWorkspace.jsx`
  - `frontend/src/App.jsx`
  - `services/api/app/evidence_picos_workflow.py`
  - `services/api/app/medical_writing_manifest.py`
  - `services/api/app/medical_writing_repository.py`
  - `services/api/app/writing_reference_translation_batch.py`
  - `frontend/src/features/writing-reference/*.jsx`
  - `packages/contracts/workbench_contracts/models.py`
- The current filesystem and live API/browser behavior are authoritative.

## Scope

- In scope:
  - Medical-writing creation, PICOS/evidence design, competitor-reference
    translation/admission, AI candidate adoption, chapter/table editing,
    handoff, and DOCX export semantics.
  - A single semantic state matrix shared by frontend labels, backend state
    transitions, persistence, audit events, quality gates, and tests.
  - Backward-compatible handling of existing records whose stored enum is
    `pending_medical_approval` or `accepted_pending_medical_approval`.
  - An atomic confirmation snapshot/audit event created by the user's explicit
    action. Existing persistence structures may be retained internally when
    migration risk makes deletion unsafe, but they must not impose a second
    user action or visible approval state.
- Out of scope:
  - Removing the system-wide Approval Center for unrelated modules or future
    multi-role governance.
  - Electronic signature, regulatory submission, final document archival, or
    future medical-director role separation.
  - Weakening source traceability, factual completeness, quality, consistency,
    or export-validation gates.
  - Rewriting unrelated medical-monitoring approval semantics.

## Success Criteria

1. Unselected AI/system text is labelled `建议` or `待确认`, never
   `待医学批准`.
2. A medical manager's explicit select/adopt/confirm action atomically records
   the current revision, actor, source/candidate identity, timestamp, and audit
   hash, and immediately moves the item to `已采纳`/`已确认`.
3. Manual editing and save create the current versioned working copy without a
   separate approval step.
4. Automatic translation remains `待审核`; the user's accept action immediately
   becomes `已审核` and, when explicitly admitted, `已纳入语料`, with no later
   approval action.
5. Source or design changes invalidate only affected confirmations and display
   `需重新确认`; they do not route through a duplicate approval center.
6. Once all required PICOS decisions are confirmed and non-approval quality
   gates pass, writing handoff is available directly.
7. Formal DOCX export depends on required content/source/quality/consistency and
   export checks, not a count of separate "医学批准快照" actions.
8. Legacy stored states load without data loss, are presented as
   `历史候选，待迁移` or an equivalent non-blocking compatibility state, and do
   not leak obsolete wording into the UI.
9. Targeted backend/frontend tests, build, isolated API tests, and real browser
   interaction pass. Stable runtime and existing project data remain unchanged
   until Codex accepts the patch.
10. Repository scan confirms no user-facing `待医学批准`, `提交医学批准`, or
    duplicate approval instruction remains in the scoped writing surfaces.

## Risk Boundaries

- Work only in this repository and an isolated runtime. Do not modify stable
  runtime data, user originals, credentials, or real project records.
- Do not bulk replace strings. First map each state transition and distinguish
  `待确认`, source/quality blockers, audit snapshots, electronic signatures,
  and actual future multi-role approval.
- Preserve persistent schema compatibility unless a tested migration and
  rollback path is included.
- Do not bypass evidence, content, consistency, reference, or DOCX quality
  checks by renaming them.
- Execution models may implement and test; they must not generate clinical
  content or make final release claims. Codex owns final browser/API/Word
  acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-20 13:58:59: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-20: Codex reproduced 175 scoped hits and confirmed a direct
  contradiction: the new authoring-prefill contract already uses
  `user_confirmed` with no second approval object, while the PICOS workflow and
  several writing/reference UIs still require a separate approval submission.
- 2026-07-20: User clarified session hygiene. Same-defect follow-ups retain the
  prior model session. This semantics refactor is independent of the active
  Qoder autonomy probe and therefore must start with `/new`.
