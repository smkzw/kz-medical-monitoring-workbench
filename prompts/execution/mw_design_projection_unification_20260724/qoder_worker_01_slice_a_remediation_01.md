# Qoder Slice A acceptance remediation 01

Continue the same `mw_design_projection_unification_20260724` Slice A session.
Codex did not accept Freeze A. Fix all defects below in one pass, rerun the
real tests, update the existing report, and recreate/touch the same completion
marker only after the final test command passes.

## Reproduced failures

1. `python3 -m pytest -q tests/test_medical_writing_design_projection.py ...`
   fails during collection because the new normalized projection contracts are
   not exported from `packages/contracts/workbench_contracts/__init__.py`.
   Export all Slice A public contracts consistently in the import list and
   `__all__`.
2. The report's Python architecture blocker is not the actual current
   environment. `/usr/bin/python3` on this machine imports `pytest 8.4.2` and
   `pydantic_core` under arm64. The current decisive failure is the missing
   contract export above. Use the workspace command `python3 -m pytest ...`;
   do not claim an environment blocker unless a newly reproduced error proves
   it after the import fix.

## Contract and implementation defects

3. `normalize_study_design()` claims legacy fallback but never calls
   `enforce_structured_authority()` and always returns `undecided` when the
   structured fields are undecided. Implement actual normalization through the
   one entry point. Reuse or centralize the project's existing deterministic
   parsing semantics for `framing.design_pattern` and
   `picos.design_archetype`; do not create a second contradictory heuristic.
   Add tests that call `normalize_study_design()` itself, not only the helper:
   - decided structured values win over contradictory legacy text;
   - undecided structured values are seeded from recognized legacy/PICOS
     design facts;
   - unsupported free text remains undecided rather than invented.
4. `_is_phase_one()` must pass the declared cases, including `I 期`,
   `I/II 期`, `I期/II期`, `PHASE1`, and FIH/first-in-human, while rejecting
   II/III/IV. The current split implementation fails its own I/II and FIH
   tests. Use a bounded normalized-token implementation and add these exact
   cases.
5. `MedicalWritingNormalizedDesignProjectionWithSources.design_fact_paths` is
   typed `Dict[str, str]` but `normalize_study_design(include_sources=True)`
   inserts a list of dictionaries. Its uniqueness validator also attempts to
   hash list values and is semantically wrong. Make this a real source-path
   binding map such as semantic fact name -> canonical StudyDefinition path;
   do not put fact values in a field named `design_fact_paths`. Add a direct
   `include_sources=True` construction test.
6. Remove the duplicate `_PHASE1_BLOCKED_PROJECTIONS` definition.
7. The non-Phase-I consistency hook checks
   `projection.design_view.phase1_parts` only after the normalizer has already
   filtered it to empty, so the branch is unreachable. Check the authoritative
   original structured parts. Preserve the consumer-safe filtered view and
   surface an explicit nonblocking consistency warning, or fail closed with a
   blocker; do not silently claim the hook works while it is unreachable.
   Add a direct consistency-hook test if the service can be constructed
   cheaply; otherwise add a pure helper test that proves the original residual
   input is detected.
8. Do not treat ordinary structured authority as a blocker merely because raw
   `design_pattern` text is not exactly equal to enum token `randomized`.
   Compare normalized semantics. A decided structured value remains
   authoritative; a legacy contradiction should be a consistency warning and
   must not set `deterministic_projection_allowed=false` unless a real clinical
   fact remains unresolved.
9. `_resolve_phase1_parts()` currently sets every phase-I module, including
   unselected modules, to `deterministic_projection_allowed=false` whenever any
   Part is unresolved. Block only the selected unresolved Part's module; keep
   unselected modules `not_applicable` and deterministic. Bind the question to
   the actual part index or part code, fix the `population_cohod_required`
   typo, and list the actually missing required fields. Do not describe
   optional `pk_pd`, `safety`, `stopping_rules`, `soa_summary`, or transitions
   as required when the current typed contract only defines population and
   cohort_dose as resolution requirements.

## Acceptance

Run at minimum:

```bash
python3 -m pytest -q \
  tests/test_medical_writing_design_projection.py \
  tests/test_medical_writing_structured_design_contract.py \
  tests/test_worker01_typed_phase1_parts_and_safe_prefill.py
```

Also run directly adjacent assembly-plan and consistency tests touched by the
fix. Update
`reviews/qoder_worker01_design_projection_slice_a_20260724.md` with the exact
commands and real results. Do not start Slice B or edit Slice B/C consumers.
Do not perform security work.
