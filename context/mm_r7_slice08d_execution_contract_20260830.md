# R7 Slice-08D Governed Execution Contract

Date: 2026-08-30  
Task ID: `mm_r7_slice08d_execution_20260830`  
Goal: implement and verify the frozen 08D synthetic/offline comprehensive regression contract without changing accepted 08C desktop UX or protected medical-writing.

## Source authority

1. `reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_1_20260830.md`
2. `reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_2_20260830.md` (takes precedence on conflict)
3. Frozen 08A/08B/08C acceptance records and current filesystem source/tests

## Shared boundaries

- Work only in the medical-monitoring R7 implementation, related synthetic/offline tests, and task-owned context/review/metrics/evidence files.
- Do not modify medical-writing. Do not run real studies or real models. Do not start 8911/5174 or any app service. Do not use ego(lite), Playwright, screenshots, or redo 08C visual acceptance.
- Do not design/test system security or add mobile/narrow-screen obligations.
- Prefer tests and existing stdlib seams. Add production code only for a demonstrated shared-contract defect, and keep it minimal.
- Preserve the frozen 08B real R5/R6/artifact closure. Never substitute 08A proxy digest authority.
- Workers do not declare final acceptance. The execution manager integrates; Codex independently verifies current files and evidence.

## Work item 01 — 20-cell matrix and independent oracle

Primary write scope:

- `poc/medical_monitoring_ai_native_r7/tests/test_slice08d_three_mode_matrix.py` (new preferred consolidated test)
- existing continuity/bridge tests only when reuse is clearly shorter
- production seams only if the new tests prove an actual contract defect

Required result:

- Parameterized DF-N/B/M/R/C, DI-N/B/M/R/C, PL-N/B/M/R/C, PC-N/B/M/R/C closure.
- Expected values rebuilt only from input-side frozen facts and actual member bytes; no product-output or database-result oracle, no direct verified booleans, no case-name decision branches.
- Reverse mode/basis and stable error-code assertions.

## Work item 02 — determinism and atomic recovery

Primary write scope:

- `poc/medical_monitoring_ai_native_r7/tests/test_determinism_adjacent.py`
- `poc/medical_monitoring_ai_native_r7/tests/test_continuity_registry.py`
- production registry/continuity seams only for demonstrated defects

Required result:

- Fixed 5 seeds `{0,1,17,42,31415926}` × `normal/-O/-OO` 15-grid in independent subprocesses.
- SQLite reopen assertion through `PRAGMA busy_timeout = 10000`.
- Enumerate and hit all current finalize/publication/continuity atomic failure hooks.
- CAS, replay, late callback, recoverable retry, real-drift block, and no-half-publication assertions.

## Work item 03 — adjacent/public boundary and evidence

Primary write scope:

- existing 08C frontend/DTO contract tests only if a missing assertion is demonstrated
- task-owned evidence under `artifacts/mm_r7_slice08d_regression_20260830/`
- no product UI edits

Required result:

- Run the fixed adjacent suite from v0.2 §16 without deselection hiding affected tests.
- Verify public schema/UI node terminology boundaries without blanket source-body scrubbing.
- Record compileall, project/path neutrality, medical-writing protection, and 8911/5174 stopped evidence.
- Produce a compact machine-readable manifest of commands, exit codes, counts, and boundaries.

## Integration and done

The manager must reconcile all worker changes against the frozen contract, run the decisive combined suite, report actual test counts and failures, and leave P0-P4 classification for independent conference and Codex. Done is not reached until all 20 scenario keys, 15 determinism cells, all enumerated fault hooks, reverse mode/basis, public Chinese boundary, adjacent regression, protected ports, and medical-writing boundary have current evidence.
