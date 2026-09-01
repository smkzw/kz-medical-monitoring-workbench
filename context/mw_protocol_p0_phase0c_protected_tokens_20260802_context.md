# Task Context: mw_protocol_p0_phase0c_protected_tokens_20260802

Created: 2026-08-02 01:43:52
Objective: 继续 Protocol P0 Phase 0C：为局部 AI 精改建立确定性 protected-token 检查，保护数字/单位/受控术语/文献引文/表图交叉引用，并在真实候选应用前 fail closed；不触碰冻结 r42/v36、上游研究/OCR/翻译、运行时服务或医学监查并发线
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Immutable no-loss boundary: `runs/MW_R42_NO_LOSS_PAUSE_20260731_1609.md`.
- Approved Protocol-first roadmap and Phase 0C gates:
  `plans/mw_commercial_writing_gap_and_roadmap_20260731.md`.
- Accepted prerequisite Phase 0C diff/impact slice:
  `runs/codex_mw_protocol_p0_phase0c_diff_impact_20260802.md` with its
  context/review/metrics records.
- Current contracts and implementation under `packages/contracts/`,
  `services/api/app/medical_writing.py`,
  `services/api/app/medical_writing_repository.py`,
  `services/api/app/ai_task_runner.py`, `frontend/src/`, and deterministic
  tests under `tests/`.
- Current filesystem is final truth. No runtime service, browser, real model,
  OCR/translation, download, upstream state, or medical-monitoring file is an
  authority or an allowed input for this bounded task.

## Scope

- In scope:
  - Audit the current AI candidate and accept/apply paths for deterministic
    preservation of numeric values, units, controlled clinical terms, numeric
    literature citations, and table/figure cross-reference marks.
  - Define one pure, Unicode-aware token manifest/checker that compares the
    immutable selected source with each proposal without normalizing away
    clinically meaningful differences.
  - Persist only additive, auditable protection status/details on new
    `RevisionSuggestion` records; preserve legacy cold-load compatibility.
  - Fail closed before medical-author acceptance/application when a protected
    source token is missing, changed, reordered, or an unsupported structured
    cross-reference is replaced by plain text. Keep approved citation-binding
    application semantics intact.
  - Add focused deterministic tests for numeric/unit changes, abbreviations,
    citations, table/figure references, Unicode punctuation and legacy rows.
- Out of scope:
  - r42/v36 transition/retry, candidate-ready/excluded items, downloads,
    preparation, OCR, translation or any immutable upstream row.
  - Synopsis, CSR, cross-product graph migration, full undo/revision history,
    DOCX pagination/Word runtime, provider/model calls, browser automation,
    production databases/services, or the medical-monitoring concurrent lane.
  - Heuristic medical interpretation or automatic approval of new facts.

## Success Criteria

- The checker is deterministic, pure, Unicode-aware and independently
  testable; identical source/proposal text yields identical token identities
  and diagnostics.
- A proposal cannot silently remove or alter a source numeric, unit,
  controlled abbreviation/term, citation marker, or structured table/figure
  cross-reference before acceptance/application. Any unsupported or ambiguous
  tokenization is `unresolved`/fail-closed rather than silently allowed.
- New candidate records expose protection status and auditable mismatch codes;
  legacy records remain loadable as `legacy_unavailable`.
- Citation-binding and rich-text cross-reference application paths remain
  compatible and are covered by regressions.
- Focused tests, compile checks, review-gate, and frozen r42/process checks
  pass; no service, browser, real model, OCR/translation, upstream or
  monitoring state is touched.
- This remains a bounded Phase 0C increment and does not imply Protocol
  release readiness.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 01:43:52: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02: Selected as the next safe P0 increment because the accepted
  diff/impact slice still listed protected-token editing as residual risk.
  Initial audit is read-only; implementation will use only additive contracts
  and the existing candidate-application boundary.
- 2026-08-02: Implemented the deterministic protected-token contract in the
  contracts layer and kept the service import as a compatibility re-export.
  New candidates carry additive `protected_token_status` and auditable issue
  codes; legacy rows remain `legacy_unavailable`. The thread cold-load
  boundary recomputes the checker from authoritative selected/proposal text,
  rejecting forged status or issue payloads.
- 2026-08-02: The checker now protects numeric/unit identity, comparator and
  approximation semantics, Chinese dosage/frequency forms (including a
  trailing half and 百分之), citations, table/figure/chapter references,
  clinical abbreviations and polarity, Greek-suffixed and alphanumeric terms,
  phase/arm/cohort/group/part labels, PK terms, metric comparator expressions
  including mixed-case clinical metrics, conservative HGVS/cytoband tokens,
  and structured cross-reference marks. Unicode/compatibility normalization
  preserves source locators and does not collapse clinically meaningful M/m,
  mM/mm or nM/nm differences.
- 2026-08-02: Repository and service accept/apply paths recompute the check
  immediately before mutation and fail closed on missing/changed/reordered
  source identity. Structured rich-text cross-reference marks are required to
  survive the transformation. Additive proposal tokens remain visibly
  `unresolved` for medical review rather than being silently treated as
  verified. The concurrent same-idempotency race now returns the persisted
  winner's immutable snapshot/audit instead of a phantom local result.
- 2026-08-02: Closed the remaining API boundary: real and greenfield projects
  receive HTTP 410 from the legacy two-step ACCEPT and working-copy APPLY
  routes; only the explicit demo project remains compatible. This prevents a
  client from persisting author selection without the atomic working-copy
  write. The old real-project positive test was migrated to the 410 contract.
- 2026-08-02: Codex verification passed the final affected suite (`128
  passed, 2 deselected, 17 existing deprecation warnings`), including token,
  contract, application, durable, citation, API, and working-copy boundary
  regressions. Protected-token tests were `14 passed`; independent final
  challenge reported `48 passed`, ten mutation probes, four normalization
  probes, and no P0-P4/fail-open findings. Python compileall and frontend Vite
  build passed (`1918 modules transformed`).
- 2026-08-02: Final boundary checks preserved the immutable r42 checkpoint at
  SHA-256 `d354eb0b4f8b98225c831d76f752b346315949e0e78983f24c6392c91d255130`,
  mtime `2026-07-31 16:11:13 +0800`, size `6516` bytes; ports 18905/18906
  had no listeners. No service process, browser, Word/LibreOffice, real
  provider/model, OCR, translation, download, upstream item, or medical-
  monitoring file was started or changed.
- 2026-08-02: This bounded increment is accepted for continuation only. It
  does not imply Protocol release readiness. The next safe action is a
  separately tracked Phase 0C increment after this record; do not enter
  Synopsis, CSR, or the final serial provider/two-role visual gate from this
  record alone.
- 2026-08-02: `hermes_workflow_guard.py review-gate --require-verification`
  passed with no warnings or errors for this context/run/review/metrics
  quartet. Goal remains active.
