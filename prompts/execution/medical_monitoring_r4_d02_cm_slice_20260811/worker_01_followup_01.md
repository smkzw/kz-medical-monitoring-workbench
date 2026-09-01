You are continuing the same `worker_01` execution session for task `medical_monitoring_r4_d02_cm_slice_20260811`. Read the frozen D02 contract and the current five authorized worker_01 files. Make only the following bounded contract corrections; do not begin CM implementation and do not touch any other path.

## Hard boundaries

- Work only inside the runner-provided current workspace root (`.`).
- Modify only `poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py` and `poc/medical_monitoring_ai_native_r4/tests/test_shared_domain_protocol.py`. The other three worker_01 source files are read-only for this correction.
- Do not touch product, frontend/backend, medical-writing, R1/R2/R3, real projects, services, providers, dictionaries, port 8911, task records, prompts, runs, logs, reviews, plans, context, or metrics.
- Runner-managed output file: `runs/execution/medical_monitoring_r4_d02_cm_slice_20260811/worker_01_round2.md`. Return the report in your final response; do not write this path with tools.

## Read these files only

- `reviews/medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/lifecycle.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_shared_domain_protocol.py`
- Existing R4 tests may be executed but not modified.

Codex independently reran the gate after your first pass:

- original D01 suite excluding `test_shared_domain_protocol.py`: `224 passed`
- new shared-protocol test: `35 passed`

Two load-bearing precision gaps remain:

1. `RiskDomainUnitResult` is frozen with exact return types `Sequence[RiskCandidate]`, `Sequence[RiskCandidateRef]`, and `Sequence[RiskInstanceRef]`. The current Protocol uses `Sequence[Any]` for all three. Import the public R2 `RiskCandidate` type on the neutral contract surface and use the exact frozen types. Add a deterministic test that resolves/type-inspects these property return annotations and fails on `Any`.
2. The frozen contract says `CrossDomainEvidenceRef.content_hash` is the canonical hash of its determinant fields. The current constructor accepts any syntactically valid 64-character hash, permitting a non-canonical immutable ref. Canonicalize `context_payload` storage into key-sorted order, compute the canonical hash after validation, and reject a well-formed but mismatched hash in `__post_init__` with `CoverageValidationError`. Preserve `verify_content_hash()` as a post-construction/tamper check. Add tests for sorted stored payload and rejection of a well-formed mismatched hash.

Keep all existing D01 semantics and exports unchanged. Re-run:

1. `python3 -m pytest -q -p no:cacheprovider tests --ignore=tests/test_shared_domain_protocol.py` and require exactly `224 passed`.
2. `python3 -m pytest -q -p no:cacheprovider tests/test_shared_domain_protocol.py`.
3. `python3 -m ruff check src/mm_r4 tests` plus compile/import checks.

Return the complete worker report schema with exact files, commands, results, uncertainty, and next step. Do not claim Gate 1 acceptance; Codex owns acceptance.
