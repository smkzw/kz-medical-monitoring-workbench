# Worker02 same-session corrective follow-up 1

Codex does not accept the first projection snapshot. Continue in the same
session and edit only the two already-authorized files:

Hard boundaries:
- Work only inside the current workspace root (`.`).
- Read these files only as the corrective source set:
  - `AGENTS.md`
  - `reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md`
  - `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_contracts.py`
  - `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_evaluator.py`
  - `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_projection.py`
  - `poc/medical_monitoring_ai_native_r4/tests/test_d09_projection.py`
  - `poc/medical_monitoring_ai_native_r4/tests/test_d09_adapter.py`
- Runner-managed report path:
  `runs/execution/medical_monitoring_r4_d09_runtime_20260815/worker_02.md`.
  Never write this report through tools; return the complete report and let the
  runner persist it.

- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_projection.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d09_projection.py`

Do not edit any other file. Re-read the current files before patching and keep
the frozen Worker01 input SHAs unchanged.

## Required corrections

1. **PD wording is medically wrong in the first pass.** The frozen policy's
   `allowed_action_kinds` is an allowlist, not proof that the current finding
   concerns PD. Codex replayed all 179 cases: 65 Query drafts were emitted;
   only 2 contained exact structured `gap_kind == "pd_unreported"`, yet all 65
   said `请核实是否为 PD` (63 false positives, e.g. CASE-010 repeated SAE risk
   and CASE-035 missing_required_field). Make PD wording necessary only when:
   (a) policy allows `verify_pd`, and (b) at least one **projectable uncovered
   member** carries an exact structured, closed PD fact. For the frozen v0.5
   schema this is exact `GapMember.gap_kind == "pd_unreported"`; do not use
   substring/prose/display-label/producer-domain guesses and do not invent a
   future risk-kind vocabulary. Validator must independently enforce the same
   two-part gate. Add a full-catalog assertion: all non-PD drafts exclude the
   phrase and exact PD drafts include it; expected current distribution is 63
   non-PD drafts and 2 PD drafts, but do not branch production code on counts or
   case ids.

2. **Typed visibility sets must be authoritative.** The first pass derives
   evaluation/projectable solely as all-members minus hidden and ignores
   `VisibilityDecision.evaluation_member_refs` and `projectable_member_refs`.
   Implement one closed helper used by every audience surface. If an explicit
   set is non-empty it is authoritative; empty retains the current schema's
   backward-compatible implicit set. Fail closed on unknown refs, overlap,
   projectable outside evaluation, hidden outside evaluation, or an explicit
   partition that does not reconcile. Query, hotspots, links, visible counts,
   ordering and leak checks must all consume this same resolved set. Add direct
   negative tests and one positive explicit-partition test; preserve the five
   frozen hidden-member cases.

3. **Trend deep-link anchors.** Contract section 11 forbids gap/trend members
   from having only a center summary without a locatable anchor. A
   `ChangeLedgerMember` has typed `current_window_instance_ref` and
   `prior_window_instance_ref`; use the current window ref as its target anchor
   (and include both refs in deterministic return-state identity if needed).
   Missing required current/prior refs must yield `unavailable` +
   `来源暂无法定位`, not a locatable link with no anchor. Add positive and
   negative tests. Gap and subject-risk behavior must remain unchanged.

4. **R2 prior binding minimum.** Any non-create handoff must require both
   `prior_risk_instance_ref` and `prior_public_risk_identity_ref`; missing either
   fails closed. Carry the prior public identity ref in the immutable handoff or
   otherwise include it in validation/idempotency so it cannot be silently
   ignored. This does not claim local resolution of the R2 object; explicitly
   label downstream same-public-identity resolution as an R2 application gate.
   Add missing-ref/tamper tests. Do not invent propose-close/reopen/update from
   absent typed facts.

5. **Frozen algorithm identity.** Contract §5.1 and the independent artifact
   generator fix `algorithm_version="d09_v1"`; the first pass used the unrelated
   runtime constant value `d09_unit_v1`. The projection's evaluation-content
   identity must use the frozen contract literal `d09_v1`, with a focused test
   independently re-deriving the identity. Do not modify `d09_contracts.py`.

6. Re-run all prior focused/adjacent checks plus the new negative probes, Ruff,
   in-memory compile, frozen SHA checks and TCP 8911 STOPPED. Return the full
   execution report schema and new exact SHAs. Do not claim acceptance or unlock
   Worker03.
