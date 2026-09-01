# D04 clinical/protocol final-SHA recheck

Continue the same Pi/Qwen session `019ff1a4-dd21-7000-b0a4-6928049e4fb4`.
Do not restart or open a new model session.

## Hard boundaries

- Work only in the current workspace (`.`).
- Read only `reviews/medical_monitoring_r4_d04_protocol_pd_slice_contract_v1_20260812.md`.
- Do not read other participant outputs or prior report files.
- Do not edit files, run services, run tests, or access real projects.
- Codex remains final clinical/regulatory/engineering authority.

Read these files only:

- `reviews/medical_monitoring_r4_d04_protocol_pd_slice_contract_v1_20260812.md`

Runner-managed report path: `runs/conference/medical_monitoring_r4_d04_contract_acceptance_20260812/general_pi_qwen38_final_recheck.md`.

The runner owns this file. Return the report in the model response; do not write it with tools.

## Immutable review target

The review target is the current draft with SHA-256:
`cb8506fda6d6abcf26da6a840314985898601742b71f0912ec3e01a4e3ba818c`

Recompute the file SHA before review and again before returning. If either differs,
return `REVISE` with `snapshot_drift` and do not grade a mixed snapshot.

## Focused closure questions

Recheck your prior B1-B3 and H1-H4, plus the main-venue correction below:

1. Candidate flags are strict public candidate-detail booleans, consumed before
   establishment; either flag forces severity=high, post-establish severity is
   asserted, and frozen R2 receives no new field.
2. not_evaluable uses deterministic `ProtocolCoverageGapNotice`, never an L2
   QueryDraftRef without a candidate/risk.
3. China 2026 GCP citation is four departments, announcement No. 50, effective
   2026-09-01, with official NMPA link and Shanghai mirror.
4. Applicability gate has deterministic, order-independent sentinel lineage and
   temporal identity; no run/snapshot/revision contamination.
5. Unparseable package logic fails closed; CM-as-evidence for an eligibility
   claim remains D04 without creating a D02 prohibition risk; D05 is explicitly
   a future owner tested only through a synthetic producer stub.
6. Combination rules now create one EvaluationUnit per independently adjudicable
   official control point. Components are evidence assessments only. Verify this
   eliminates the false positive where one alternative eligibility condition is
   unmet but another satisfies an ANY package, while retaining L0/component gaps.
7. Query wording distinguishes never-enrolled, enrolled/post-enrollment, and
   unresolved enrollment states; retrospective waivers cannot rewrite an unmet
   requirement as compliant.
8. The continuous 1-83 challenge matrix makes these boundaries executable.

Return:

1. `# D04 Clinical Final-SHA Recheck`
2. a closure table for B1-B3, H1-H4, and the package-unit correction
3. any residual blocker with exact section and replacement/test
4. `## Verdict` containing exactly `ACCEPT` or `REVISE`

Do not block on non-material style. Slow work remains pending. The runner owns the
report file.
