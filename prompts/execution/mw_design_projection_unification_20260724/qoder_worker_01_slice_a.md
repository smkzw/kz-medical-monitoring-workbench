# Qoder Execution Contract: Slice A

You are the first-line implementation worker for task
`mw_design_projection_unification_20260724`.

## Runtime and workspace

- Active model must remain `Qwen3.8-Max-Preview`.
- Work only in:
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`
- Begin by reading:
  - the applicable global and project `AGENTS.md`;
  - `context/mw_design_projection_unification_20260724_execution_context.md`;
  - `plans/codex_execution_mw_design_projection_unification_20260724.md`;
  - `reviews/medical_writing_dynamic_design_projection_review_20260724.md`;
  - `runs/execution/mw_design_projection_unification_20260724/manager.md`.
- This is product functionality and scientific-validity work only. Do not perform
  engineering-security, backdoor, penetration, or vulnerability auditing.
- Preserve unrelated user changes. Do not reset, revert, or broadly reformat.
- Do not install packages.

## Objective

Implement only Slice A, the independently testable foundation for one
authoritative study-design projection:

1. Add a read-only `NormalizedDesignProjection` contract and any minimal nested
   fact/blocker views needed for this slice.
2. Add one entry point:
   `normalize_study_design(StudyDefinition) -> NormalizedDesignProjection`.
3. Enforce authority:
   - decided typed structured facts win;
   - PICOS, `intrinsic_objectives`, `design_pattern`, and free text may be used
     only when the matching structured fact is undecided or absent;
   - no consumer in this slice may silently prefer legacy text over a decided
     structured fact.
4. Make typed Phase I `part_code` authoritative for Phase I module planning.
5. Selected Phase I Parts with unresolved required facts must produce precise
   blockers and set `deterministic_projection_allowed=false` for only the
   affected projection targets. Never invent dose, population, sequence, or
   cohort facts.
6. Non-Phase-I studies must not surface stale Phase I Parts as applicable design
   content. Filter or fail closed with an explicit consistency issue.
7. Add focused consistency hooks for contradictions between decided structured
   facts and legacy text.

## Ownership

You may edit only the smallest coherent set needed for Slice A, primarily:

- `packages/contracts/workbench_contracts/models.py`
  - only `NormalizedDesignProjection*` and minimal Slice-A blocker fields;
- new `services/api/app/medical_writing_design_projection.py`;
- Phase-I normalization/blocker logic in
  `services/api/app/medical_writing_protocol_assembly_plan.py`;
- Slice-A consistency hooks in
  `services/api/app/medical_writing_study_consistency.py`;
- focused tests:
  - new `tests/test_medical_writing_design_projection.py`;
  - `tests/test_medical_writing_structured_design_contract.py`;
  - `tests/test_worker01_typed_phase1_parts_and_safe_prefill.py`;
  - only directly adjacent test files required by a demonstrated contract.

Do not implement typed treatment-switch, crossover, OLE, sample-size
re-estimation, or adaptive-design objects; those belong to Slice B. Do not
rewrite synopsis, SoA, flowchart, or DOCX consumers; those belong to Slice C.

## Required counterexamples

Add tests that fail before and pass after the fix:

1. A selected unresolved SAD part with missing population or cohort dose blocks
   affected deterministic projection and exposes the precise missing facts.
2. A Phase III definition containing residual Phase I Parts does not treat them
   as applicable Phase I modules or leak them into projections.
3. Decided structured randomization projects correctly even when
   `picos.design_archetype` is empty or contradictory.
4. Legacy free text is used only when the corresponding structured field is
   undecided.

Run the focused suite and any directly affected adjacent tests. Do not claim
browser, Word, clinical, regulatory, or release acceptance.

## Completion evidence

Write a compact implementation report to:
`reviews/qoder_worker01_design_projection_slice_a_20260724.md`

The report must list files changed, contract decisions, commands and test
results, failed attempts, residual risks, and exact handoff constraints for
Slice B and Slice C.

When implementation, tests, and the report are complete, create this zero-byte
completion marker:
`runs/execution/mw_design_projection_unification_20260724/qoder_worker01.done`

Do not create the marker before the report exists and the final focused test
command has completed. Work autonomously to completion; do not ask for routine
implementation approval.
