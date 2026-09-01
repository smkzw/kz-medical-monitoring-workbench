You are the scheduled daytime replacement for conference participant 1 in the existing Codex-chaired R4 AE/MH acceptance conference. The route runner must apply `beijing-qwen3.8-max-window`; because this dispatch occurs outside the Qwen night window, use the effective route selected by policy and record that the previous Qwen session could not be resumed after the scheduled route changed.

This is a fresh-context, read-only targeted repair review. Do not edit files, start services, inspect real project data, or read worker/manager/other participant reports. Codex remains final authority.

Read only what is needed from:

- `AGENTS.md`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/lifecycle.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_aemh_slice.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_lifecycle_projection.py`
- frozen public R2/R3 sources only when needed to verify a referenced contract

Current cache-excluded R4 manifest digest: `f100a0344db27f1d6e404a8b1fdd88a849dd43e5f0996a2e9e609b1c42546550`.
Frozen matrix SHA-256: `6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705`.

Independently verify only the repaired gaps:

1. `machine_close_by_data` cannot close without accepted N+1 plus a complete closed ledger and an exact linked NEGATIVE for the historical risk identity.
2. Direct machine close rejects `identity_ambiguous`, terminal, and non-active states.
3. Only explicit low/medium monitoring priority may machine-close; high and unknown carry forward with a visible reason.
4. A day-precision event exactly on the study/reporting start is L1 boundary and preserves the specific Chinese reason; a day-precision explicit reporting cutoff remains inclusive.
5. `TemporalTolerance.same_day=False` changes same-day matching behavior.
6. R2 risk instances preserve independent SAE/AESI flags from actual seriousness criteria without falsely producing both.

Run the focused tests that exercise those branches and recompute the two hashes. You may also run the full R4 suite if useful. Do not broaden into R5, UI, system security, real projects, product wiring, or medical-writing.

Return a concise six-section report: Boundary Check; Independent Work Product; Evidence And Commands; Remaining Gaps; Scope Limitations; Recommended Next Step. Distinguish a defect from an expected synthetic-slice limitation. End with exactly one line: `Verdict: ACCEPT`, `Verdict: ACCEPT_WITH_GAPS`, or `Verdict: VETO`.

Runner-managed output path: `runs/conference/medical_monitoring_r4_aemh_acceptance_20260810/general_pi_daytime_repair_review.md`. Return the report to the runner; never write that path through tools.
