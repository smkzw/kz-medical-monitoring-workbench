# D04 engineering final-SHA recheck

Continue the same Cursor CLI session `32fea678-0077-442c-9696-bd68a863aa53`.
Do not restart or open a new session.

Hard boundaries:
- Work only in the current workspace (`.`).
- Read only the contract listed below.
- Do not read other participant outputs or report files.
- Do not edit files, run services/tests, or access real projects.
- Codex remains final authority.

Read these files only:
- `reviews/medical_monitoring_r4_d04_protocol_pd_slice_contract_v1_20260812.md`

Runner-managed report path: `runs/conference/medical_monitoring_r4_d04_contract_acceptance_20260812/general_cursor_final_recheck.md`.
Return the report in the model response; do not write the report path with tools.

Immutable target SHA-256:
`cb8506fda6d6abcf26da6a840314985898601742b71f0912ec3e01a4e3ba818c`

Recompute SHA before and after review. Any drift is `REVISE snapshot_drift`.

Focused engineering checks:

1. Exactly one EvaluationUnit per independently adjudicable official control
   point/window. Atomic/package components are evidence assessments only. Verify
   ANY/ALL/AT_LEAST_N semantics cannot emit an atomic false-positive or duplicate
   candidate/Query and still expose component gaps through L0.
2. Applicability and routing gates have complete, deterministic eight-dimension
   unit identity, sorted feasible-version fingerprints, stable content ids and no
   run/snapshot/revision contamination.
3. Risk identity includes evaluation window and stable evaluation-node identity;
   lineage changes supersede rather than data-close.
4. not_evaluable uses a deterministic coverage-gap notice and creates no invalid
   QueryDraftRef without candidate/risk.
5. Candidate flags are strict public readers; establishment forces/asserts high;
   R2 is unchanged and existing close logic remains the sole authority.
6. D02/D03/D05 ownership is exclusive, including CM-as-evidence for an eligibility
   claim and future D05 synthetic-stub boundary.
7. Projection joins use a closed enum and typed stable ids; producer results are
   not duplicated.
8. The continuous 1-83 challenge matrix and allowed implementation surfaces are
   sufficient and internally consistent.

Return:
- `# D04 Engineering Final-SHA Recheck`
- an eight-row closure table
- residual blockers with exact section/replacement/test
- `## Verdict` with exactly `ACCEPT` or `REVISE`

Do not block on non-material style.
