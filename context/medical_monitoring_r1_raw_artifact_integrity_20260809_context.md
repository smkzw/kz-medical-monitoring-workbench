# Task Context: medical_monitoring_r1_raw_artifact_integrity_20260809

Created: 2026-08-09 20:02:07
Objective: 为隔离R1实现raw output artifact读取时完整性校验、损坏隔离、审计与恢复边界；不得触碰产品、医学写作、服务、共享运行库、真实provider或真实项目
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §9 and §12.
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R1 recovery point.
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py` artifact/domain-object/recovery APIs.
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/adapters.py` raw provenance and raw-first persistence.
- `poc/medical_monitoring_ai_native_r1/src/mm_r1/capability_runtime.py` capability persistence path.
- `poc/medical_monitoring_ai_native_r1/tests/test_capability_runtime.py`,
  `test_adapters_modes_report.py`, `test_failure_injection.py` and `test_domain_store_graph.py`.
- Current accepted decision record: `poc/medical_monitoring_ai_native_r1/docs/R1_ADAPTER_FAILURE_MATRIX.md`.

## Scope

- In scope: read-time hash verification for versioned domain objects; typed adapter raw-output
  retrieval; nested raw-output content verification; recovery reporting for corrupted raw records;
  fail-closed behavior before a raw record can be reused as evidence; synthetic regression tests.
- Allowed writes: isolated R1 POC source/tests/docs and this task's context/review/metrics only.
- Out of scope: product source, medical writing, shared runtime/dependencies, service/8911,
  credentials, real provider/harness, five real projects, product migration, deletion or repair of
  authoritative evidence, and OS-level sandboxing.

## Success Criteria

1. A modified `domain_objects.object_json` or stored content hash is rejected on read.
2. Adapter raw output can be retrieved only through a typed API that verifies object identity,
   provenance identity and the nested raw JSON content hash.
3. A corrupted raw output is listed by recovery as an integrity violation; recovery does not
   overwrite, delete or silently repair the record.
4. Candidate evidence remains candidate-only; corrupted raw evidence cannot be treated as
   verified or publishable.
5. Focused and full isolated R1 tests pass and an independent fresh-context reviewer accepts the
   frozen slice.

## Risk Boundaries

- Do not write outside the explicit isolated R1/task-record paths.
- Preserve append-only history. Corruption handling is detect-and-isolate, not destructive repair.
- Do not add a second persistence store or falsely claim that SQLite record validation proves
  filesystem crash safety or OS sandboxing.
- The delegated reviewer is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-09 20:02:07: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-09: Reused the current content-addressing/SQLite decision; no new dependency or material
  architecture choice is needed. The observed gap is local: `domain_objects.content_hash` is
  written but `get_domain_object` does not verify it, and recovery does not inspect raw domain
  records. The smallest coherent repair is to validate the existing authoritative representation.
- 2026-08-09: Implemented verified domain-object reads, raw ref/run/hash/immutability/nested-content
  checks, typed raw retrieval, linked candidate-artifact verification and non-destructive recovery
  reporting. Initial writable-root evidence was focused `46 passed` and full core `149 passed`.
- 2026-08-09: Independent reviewer session `019fe66c-0ba1-7111-89ae-8b467544f51c` returned VETO
  after reproducing two gaps: `NaN` could escape recovery as `ValueError`, and a deleted raw row
  could still replay its idempotency-ledger version number.
- 2026-08-09: Remediated both findings without repairing or recreating evidence. Noncanonical
  canonicalization now becomes `StoreError`; raw idempotent execution re-reads the exact returned
  version before success. Added regression coverage for deleted-row replay and noncanonical nested
  raw JSON. Writable-root rerun: focused `47 passed in 0.69s`; full isolated core
  `150 passed in 1.33s`; compile checks passed.
- 2026-08-09: The same reviewer session rechecked frozen hashes, independently reran focused
  `47 passed in 0.72s` and full core `150 passed in 1.43s`, then returned `ACCEPT`. Final frozen
  hashes: `store.py` `e47fa6b67cac709192886cf4f63dc42504df8b979a982d8076d1d2c1dfde83e7`,
  `adapters.py` `a60a2fbe374f49b23f411c6798d006607b7fe505e6ce7cc65f3bcd6e180d2c96`,
  `test_capability_runtime.py` `76c673b6cef78dba378d92948123b9c648939ee4cb30c42d28fb19263e3e4ba4`.
  Acceptance is limited to this synthetic slice; OS isolation, coordinated store+hash tamper
  resistance, full crash atomicity and R1 overall completion remain open.
