# D04 L0/L1 consistency micro-recheck

Continue the same Pi/Qwen session `019ff1a4-dd21-7000-b0a4-6928049e4fb4`.
Do not open a new session.

Hard boundaries:
- Work only in `.`.
- Read only the contract below.
- Do not edit, test, run services, read reports, or access real projects.

Read these files only:
- `reviews/medical_monitoring_r4_d04_protocol_pd_slice_contract_v1_20260812.md`

Runner-managed report path: `runs/conference/medical_monitoring_r4_d04_contract_acceptance_20260812/general_pi_qwen38_l0_l1_recheck.md`.
The runner owns the report file.

Immutable target SHA-256:
`eba23bf6b0eabb71d9db465708ed28c2d2b40f7ae1ef1c86defab3fff7a66803`

Recompute SHA before and after. Drift means `REVISE snapshot_drift`.

Recheck only the post-ACCEPT consistency correction:

1. §5 permits one package unit to have a logically determinate L1 positive or
   negative while a non-decisive component remains missing.
2. §6.1/§6.2 now use proof across all feasible assignments rather than requiring
   every non-decisive component to be complete.
3. Such a gap forces L0 partial, a deterministic coverage notice, and domain
   incomplete; it never creates an extra component risk/Query.
4. If the gap can change the issue expression, L1 is not_evaluable (or boundary
   only when the uncertainty is boundary and no not_evaluable input participates).
5. Challenges 58, 72, 73 and §11 are consistent with these rules.
6. The Chinese label for D04 participant disposition is now “退出或终止参与标准待核实”,
   not an IP-dose pause label.

Return `# D04 L0/L1 Micro-Recheck`, a six-row table, residual blockers, and
`## Verdict` with exactly `ACCEPT` or `REVISE`.
