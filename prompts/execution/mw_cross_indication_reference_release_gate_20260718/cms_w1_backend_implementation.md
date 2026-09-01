You are Hermes/aishuo/cms-model, the first-line implementation worker for a
critical medical-writing production release gate. First fully read and comply
with `/Users/smkzw/.hermes/SOUL.md` and `/Users/smkzw/.codex/AGENTS.md`.

Task id: `mw_cross_indication_reference_release_gate_20260718`
Role: W1 backend architecture remediation.

Read these files only:
- `context/mw_cross_indication_reference_release_gate_20260718_context.md`
- `runs/execution/mw_cross_indication_reference_release_gate_20260718/manager_plan.md`
- `records/USER_REQUIREMENTS_CURRENT_20260718.md`
- `services/api/app/writing_reference.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/ocr_gateway.py`
- `services/api/app/ai_gateway.py`
- `services/api/app/ai_execution_policy.py`
- `services/api/app/ai_task_runner.py`
- `packages/contracts/workbench_contracts/models.py`
- relevant `tests/test_writing_reference_*` and `tests/test_ocr_gateway.py`

The read list is a starting context, not a blanket prohibition on bounded
adjacent inspection needed for correct implementation.

Hard boundaries:
- You MAY edit product backend source, contracts, and focused tests only.
- Do not edit frontend files in this pass.
- Do not modify stable databases, source clinical documents, ports 5174/8911,
  runtime configuration, credentials, release bundles, or existing evidence
  reports.
- Do not make live ClinicalTrials.gov, DeepSeek, oMLX, OCR or translation calls
  in this implementation pass. Use deterministic fakes in tests.
- Preserve existing API behavior where possible. Additive contract fields and
  backward-compatible repository migration are preferred.
- No Codex/Hermes prose may substitute for product-model output.

Implement the smallest coherent backend slice that closes the architecture
gap, not a paper-only design:

1. Introduce an explicit, auditable chapter translation pipeline whose
   authoritative stages are:
   text extraction -> optional GLM-OCR-bf16 page recovery at >=200 DPI and
   <=8 concurrency -> deepseek-v4-flash TOC/chapter planning -> exact local
   model `dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX` chapter/chunk translation ->
   deepseek-v4-flash integration QC -> pending medical approval.
2. Keep deterministic number, unit, time-window, negation and abbreviation
   fidelity checks blocking. Flash must no longer be the sole protocol-body
   translator under the new current contract.
3. Persist enough lineage to prove document/extraction revision, page and text
   versus OCR provenance, OCR model/DPI/profile, chapter/chunk identity,
   glossary version, Hy-MT2 model, Flash planning/QC prompt versions, input and
   output hashes, retry state and current stage.
4. Extend the existing durable batch state machine so APIs can expose
   human-meaningful progress and failed-stage retry without reading logs.
   Preserve outer terminal semantics where compatibility requires it.
5. Keep idempotency and stale-lineage behavior. Restart recovery must not
   duplicate admission or translation candidates.
6. Wire dependencies through product services cleanly. Reuse the existing OCR
   gateway and OpenAI-compatible provider abstractions; do not hardcode secrets.
7. Add focused unit/integration tests for:
   - text page skips OCR; empty/image/spatial page uses OCR;
   - OCR render DPI >=200 and concurrency <=8;
   - exact model allowlists;
   - body translator is Hy-MT2, not Flash-only;
   - Flash planning before translation and Flash QC after translation;
   - fidelity drift blocks candidate readiness;
   - persisted stage/lineage/idempotency/restart/retry behavior;
   - backward compatibility of existing writing-reference translation APIs.

Use `apply_patch` or the model's structured editing tools. Run the smallest
focused tests, then the broader writing-reference test group if focused tests
pass. Do not run the full repository suite.

Write exactly one output file:
`runs/execution/mw_cross_indication_reference_release_gate_20260718/cms_w1_backend_implementation.md`.
This is the execution report; the runner persists your final response there.

Use exactly these headings:
# Execution Output:
## Boundary And Context Check
## Work Performed
## Artifacts And Evidence
## Commands And Observations
## Blockers Or Missing Environment
## Rerun Requests Or Next Step

List every changed file and exact test result. Separate observed behavior,
inference, and remaining uncertainty. Codex owns final source, clinical,
regulatory and release acceptance.
