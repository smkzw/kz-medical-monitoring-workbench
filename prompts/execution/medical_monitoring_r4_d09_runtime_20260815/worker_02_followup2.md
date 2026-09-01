# Worker02 same-session corrective follow-up 2

Hard boundaries:
- Work only inside the current workspace root (`.`).
- Initial read set (read these files only): `AGENTS.md`,
  `reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md`,
  `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_contracts.py`,
  `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_evaluator.py`,
  `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_projection.py`,
  `poc/medical_monitoring_ai_native_r4/tests/test_d09_projection.py`, and
  `poc/medical_monitoring_ai_native_r4/tests/test_d09_adapter.py`.
- Edit only the current `d09_projection.py` and `test_d09_projection.py`.
- Runner-managed report path:
  `runs/execution/medical_monitoring_r4_d09_runtime_20260815/worker_02.md`;
  do not write it through tools. Return the complete report schema.
- Do not start services/8911, use real projects/models, or touch UI/product/
  medical-writing/frozen artifacts/Worker01 files.

The first correction closed PD/visibility/trend/prior/algorithm items, but the
independent Luna verifier still returned `REVISE_D09_WORKER02_PROJECTION` on the
prior snapshot. Re-read your new snapshot and close every remaining item below.

1. **No engineering IDs in the three user-facing Query sentences.** Current
   basis/finding still prints `pattern_definition_id`, `positive_rule_ref`,
   `analysis_window_stable_id`, `mode_contract_version`, raw member refs and
   source revision refs (for example `SYN-D09-DEF-*`, `SYN-D09-RULE-*`,
   `SYN-D09-MODE-*`). Replace them with native Chinese content:
   - basis: clinical pattern label + current effective project/protocol rule +
     human-readable computed window dates/kind, without internal ids;
   - finding: `本中心`, visible affected/event/gap counts, denominator and
     coverage, followed by a finite natural record list derived from exact typed
     member facts (subject id plus event date/risk category, gap category plus
     visit/time anchor, or trend current/prior window); never raw member refs;
   - action: specific fields/records to verify, preserving exact PD gate.
   Keep all ids/revisions/rule/window/member refs in structured trace fields,
   not prose. Add structured `basis_refs`/`source_revision_refs` if needed for
   traceability and include them in hashes/validation. Add tests that all 65
   catalog Query sentences exclude synthetic definition/rule/mode/window/member
   engineering ids while retaining a non-empty finite natural record list.

2. **Evidence completeness is mandatory.** Every projectable uncovered member
   in a Query must contribute a locatable source locator and the draft evidence
   set must equal that full deterministic set and be non-empty. Missing locator
   must fail closed before producing a draft (raise `D09ProjectionError`), not
   silently return a draft with empty/partial evidence. Validator must reject
   removing any locator and recomputing the content hash. Add direct tests.

3. **All deep-link member kinds require a typed anchor.** A subject-risk member
   with empty `event_time_ref`, a gap member with no anchor even if its state says
   resolved, and a trend member missing either current/prior window ref must all
   produce `unavailable` + `来源暂无法定位` with neither exposed locator nor anchor.
   Only locatable+anchored members may produce a locatable link. Add all three
   direct probes.

4. **Hidden refs must not enter the renderer-neutral audience bundle.** R2
   internal lifecycle handoff may retain the complete unit member set, but the
   bundle's `risk_marker` is an audience projection and must reference only the
   resolved projectable member/locator set. Include risk-marker refs in the
   audience leak check. With one hidden member, Query natural counts/list,
   hotspot/deep links/count forms and risk marker must all exclude it. With all
   uncovered members hidden, the built draft is absent and
   `audience.query_present` must be false even if the internal evaluator ledger
   records `query_count=1`.

5. **Audience presence reflects built payloads.** An admitted `not_evaluable`
   unit must have `audience_payload_present=False`; its independent count/status
   surface may still explain `暂无法评价`. Compute query/risk/hotspot/Journey
   presence from actual built audience-safe objects, not raw internal counts.
   Add global-gate and admitted-not-evaluable assertions.

6. **R2 action boundary.** Keep the builder fail-closed and do not invent
   `update/propose_close/reopen` without typed lifecycle facts. Document and test
   that the contract's full R2 action vocabulary is a downstream R2 lifecycle
   surface while this D09 projection may initiate only create/continue/supersede
   from current typed facts. Validator must reject all tampered identity-bearing
   fields including member refs, measure/completeness refs and no-auto-close
   reasons, not merely the prior/public/lineage fields. Add tamper probes.

Re-run focused 179-case invariants, D09 runtime/adapter, D08 adjacency, Ruff,
in-memory compile, immutable SHAs and 8911 STOPPED. Return new exact SHAs and do
not claim acceptance or unlock Worker03.
