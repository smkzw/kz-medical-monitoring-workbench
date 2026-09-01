# Task Context: mw_ai_first_corpus_prefill_bridge_20260801

## Goal

Connect the already-persisted, source-bound round-1 Protocol corpus analysis
to authoring prefill so the independent AI can propose reviewable design
packages instead of leaving the medical writer to fill a blank form.

## Source Of Truth

- Current workbench filesystem.
- Isolated runtime evidence under
  `/private/var/folders/yb/31r9763x6_54mdxswxk36c4w0000gn/T/mw-phase0b-browser-rwanbzol/runtime_glm_retest4`.
- Journey `proj_user_cfd2d29284c8`, revision 6.
- Immutable corpus analysis `mwca_15cf6351e9fbc8edc157164d`.
- Existing prefill package `mwprefill_c9dda751f902c673a122`.

## Observed Defect

- A real Computer Use `更新建议` request completed with product route
  `alibaba_token_plan / qwen3.8-max-preview`, 27 fields and a persisted AI run.
- The package remained `partial`; `package.design` stayed the deterministic
  empty scaffold and the UI still demanded 13 design decisions.
- The prefill evidence catalog currently reads only journey framing, confirmed
  Synopsis spans and the registry snapshot. It does not consume the persisted
  round-1 Protocol corpus-analysis artifact or its page/span bindings.
- Consequently the model never receives the source excerpts that the pipeline
  already extracted, validated, translated/analyzed and persisted.

## Scope

In scope:

- server-authoritative loading of the exact round-1 analysis ID/hash bound to
  the current journey;
- deterministic conversion of eligible source bindings into immutable prefill
  evidence-catalog entries;
- explicit, conservative target-path compatibility by analysis module;
- identical catalog reconstruction for generation and later adoption;
- tests proving direct source binding, fail-closed hash/identity behavior,
  no unsupported exact-fact promotion, and lower blank-form burden.

Out of scope:

- changing the current live runtime before offline acceptance;
- replaying triage, preparation, OCR or translation;
- weakening exact dose/endpoint/AESI/sample-size/washout gates;
- treating competitor observations as current-project facts;
- modifying monitoring files, Synopsis, CSR or release-matrix tests;
- manual filling of the 13 fields as a substitute for the product fix.

## Success Criteria

1. Prefill generation receives the exact persisted round-1 analysis only when
   project, pipeline, snapshot, analysis ID and output hash match the journey.
2. Each admitted analysis entry retains source ID, locator, source hash,
   finding ID and analysis lineage; mismatches fail closed.
3. Competitor evidence supports only an allowlisted set of compatible design
   paths and remains `competitor_option`, never `exact_fact`.
4. Generation and composite-adoption verification rebuild byte-identical
   catalog identity from the same authoritative artifact.
5. Deterministic tests prove unsupported clinical facts remain pending and
   valid Protocol evidence can yield non-empty reviewable design candidates.
6. Existing focused prefill/evidence/adoption suites remain green.

## Risk And Recovery

- High risk: evidence identity drift or an overbroad module-to-path map could
  fabricate project facts. Fail closed on every identity or compatibility
  mismatch.
- Preserve old immutable analysis and prefill rows. A new UI regeneration,
  if later authorized by offline acceptance, must create a new journey/package
  revision and never rewrite revision 6.
- Allowed write paths:
  - `services/api/app/medical_writing_authoring_prefill*.py`
  - minimal wiring in `services/api/app/main.py`
  - focused `tests/test_medical_writing_authoring_prefill*.py`
  - this task's `context/`, `plans/`, `prompts/`, `runs/`, `reviews/`,
    `metrics/`, and `logs/`.

## Timeout And Session Policy

- Use the workflow-guard-selected finite-code route.
- Launch each declared route once; hard wait up to 120 minutes.
- No fixed-interval polling, duplicate dispatch or latency-based fallback.
- External outputs are advisory. Codex owns file diffs, tests, real browser
  behavior and final acceptance.

## Codex Read-only Counterexample — 2026-08-01 12:55 CST

- Against the actual isolated runtime, journey
  `proj_user_cfd2d29284c8` revision 6 bound exactly to
  `mwca_15cf6351e9fbc8edc157164d` and output hash
  `d9ca29b2373d3650715d2a7807ce82a1de1c7a4f1b6456f9194597353a5e7151`.
- The first-pass bridge verified identity/hash and reconstructed 8 immutable
  entries from 7 findings across design, eligibility, and statistics. All
  entries remained `competitor_observation` with
  `round1_corpus_analysis` lineage.
- All 8 findings were source-specific single-source observations marked
  `insufficient_support_do_not_generalize`; the first-pass mapping gave all
  8 zero supported target paths. This preserved safety but failed the product
  objective because no review candidate could be generated.
- Corrected contract: these findings may inform only module-compatible
  `competitor_option` candidates, must remain `pending_decision` with visible
  sample limitations/unresolved gaps, and may never establish or auto-adopt
  a current-project fact. `conflict_preserved_do_not_select` remains
  unbindable.
- The probe was read-only. SHA-256 of both the authoring-journey main DB and
  writing-reference main DB was unchanged before/after.
- A same-session Worker 2 recovery was dispatched once to implement this
  correction, verify live source-span/document identity fail-closed, and add
  round-1 analysis identity to package staleness. No runtime package was
  regenerated.
