# Worker03 same-session completion follow-up 1

Resume the same session from the exact budget boundary in your prior report.
Do not repeat mapping, artifact exploration, mutation probing or export design.

Hard boundaries:

- Work only inside the current workspace root (`.`); do not traverse to sibling
  projects.
- Initial read set — read these files only at resume start:
  - `AGENTS.md`
  - `prompts/execution/medical_monitoring_r4_d09_runtime_20260815/worker_03.md`
  - `runs/execution/medical_monitoring_r4_d09_runtime_20260815/worker_03.md`
  - `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py`
  - `poc/medical_monitoring_ai_native_r4/tests/test_d09_mutation_suite.py`
  - `poc/medical_monitoring_ai_native_r4/tests/test_d09_replay.py`
  - `poc/medical_monitoring_ai_native_r4/tests/test_d09_verifier_probes.py`
  - `poc/medical_monitoring_ai_native_r4/tests/test_d09_runtime_closure.py`
  Missing authorized test targets are expected. Additional test or configuration
  reads are allowed only when required by a failing declared verification and
  must be recorded.
- Runner-managed report path:
  `runs/execution/medical_monitoring_r4_d09_runtime_20260815/worker_03.md`.
  Never write or edit this report through tools; return the report in the final
  response for the runner to persist. Do not create sibling process reports.

The original hard boundaries remain unchanged. Write only the four still
missing authorized test files:

- `poc/medical_monitoring_ai_native_r4/tests/test_d09_mutation_suite.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d09_replay.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d09_verifier_probes.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d09_runtime_closure.py`

The already edited `src/mm_r4/__init__.py` is read-only during this follow-up
unless a test proves its D09-only export block is incorrect; any correction
must remain strictly inside that D09 block and be reported. All immutable
Worker01/02 files and every other subsystem remain read-only.

Implement the four suites exactly from the empirically grounded resume plan in
your prior report, then run the complete verification chain required by the
original prompt. If the full R4 or R1-R3 run is too large for one command, run
the suites serially and retain every exact count. Do not stop after writing the
tests; continue through failures, bounded fixes to the five authorized files,
Ruff, in-memory compile/import, generator checks, immutable SHA recheck and TCP
8911 STOPPED.

Important acceptance probes that must be executable tests, not report prose:

1. all-hidden/partial-hidden audience counts and payload isolation;
2. Query evidence/source-locator independent and joint tamper with recomputed
   content hash;
3. R2 joint handoff/idempotency forgery and prior/public/lineage checks;
4. 63 non-PD + 2 exact PD Query distribution;
5. risk/gap/trend missing-anchor unavailable links;
6. paired source revision permutation with canonical Query identity;
7. actual 179-case double replay and exact oracle parity;
8. AST/import closure preventing runtime dependency on test artifacts,
   expected leaves, mutation descriptions, case/fixture/test identifiers and
   synthetic sentinel branches;
9. package public export identity and clean fresh-interpreter import;
10. D07/D08 adjacency plus full R4 and full R1/R2/R3 regressions.

Return one consolidated complete execution report replacing the earlier
partial report. Include exact session continuity, all changed-file SHAs, all
test/subtest counts, failed attempts and residual uncertainty. Do not claim
D09 acceptance; Codex and the independent verifier own it.
