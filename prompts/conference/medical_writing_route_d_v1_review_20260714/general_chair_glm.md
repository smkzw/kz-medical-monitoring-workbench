You are Hermes running inside a Codex-chaired conference workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, state honestly whether you read the full file.

Conference role:
- Role id: `general_chair_glm`
- Provider/model assigned by Codex: `buddy` / `glm-5.2`
- Role description: Hermes sub-venue chair; conducts multi-round discussion in one session
- Conference mode: `parallel`

Hard boundaries:
- Work only inside the current workspace.
- Do not read or modify production paths unless Codex explicitly added them to the read list.
- Do not edit source files unless Codex explicitly authorizes an edit round.
- Do not browse web, run tests, open browsers, inspect images, or perform visual/PPT/browser acceptance unless explicitly assigned.
- Write exactly one output file: `runs/conference/medical_writing_route_d_v1_review_20260714/general_chair_glm.md`. The bounded runner persists your final response there; do not create sibling output files.

Read these files only:
- `context/medical_writing_route_d_v1_review_20260714_conference_context.md`
- `plans/codex_main_venue_medical_writing_route_d_v1_review_20260714.md`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/TASK_RECORD.md`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/EVIDENCE_AND_ARCHITECTURE_REVIEW.md`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/PILOT_RESULTS_AND_PRODUCTION_DECISION.md`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/FACT_PACK_V2_AND_TERMINOLOGY_LOCK_SPEC.md`
- `records/active_slices/medical_writing_route_d_v1_20260714/TASK_RECORD.md`
- `records/active_slices/medical_writing_route_d_v1_20260714/source_profiles.json`
- `records/active_slices/medical_writing_route_d_v1_20260714/expression_library_v2.json`
- `records/active_slices/medical_writing_route_d_v1_20260714/build_route_d_v1_inputs.py`
- `records/active_slices/medical_writing_route_d_v1_20260714/route_d_v1.py`
- `records/active_slices/medical_writing_route_d_v1_20260714/run_route_d_v1.py`
- `records/active_slices/medical_writing_route_d_v1_20260714/run_gap_contract_probe.py`
- `records/active_slices/medical_writing_route_d_v1_20260714/test_route_d_v1.py`
- `records/active_slices/medical_writing_route_d_v1_20260714/harness/LOW_RISK_GAP_WRITER.md`
- `records/active_slices/medical_writing_route_d_v1_20260714/schemas/project_fact_pack_v3.schema.json`
- `records/active_slices/medical_writing_route_d_v1_20260714/schemas/expression_library_v2.schema.json`
- `records/active_slices/medical_writing_route_d_v1_20260714/pilot_v3/source_manifest.json`
- `records/active_slices/medical_writing_route_d_v1_20260714/pilot_v3/route_d_v1_fake_summary.json`
- `records/active_slices/medical_writing_route_d_v1_20260714/pilot_v3/runs/proj_rux_03_002/fake/output.json`
- `records/active_slices/medical_writing_route_d_v1_20260714/pilot_v3/runs/proj_my008_pnh_3_01/fake/output.json`
- `records/active_slices/medical_writing_route_d_v1_20260714/pilot_v3/runs/proj_my009_uc/fake/output.json`
- `records/active_slices/medical_writing_route_d_v1_20260714/pilot_v3/runs/proj_d001/fake/run_manifest.json`
- `records/active_slices/medical_writing_route_d_v1_20260714/pilot_v3/probes/live/proj_rux_03_002/gap_contract_probe.first_semantic_leak.json`
- `records/active_slices/medical_writing_route_d_v1_20260714/pilot_v3/probes/live/proj_rux_03_002/gap_contract_probe.second_abstention_misclassified.json`
- `records/active_slices/medical_writing_route_d_v1_20260714/pilot_v3/probes/live/proj_rux_03_002/gap_contract_probe.json`
- `runs/conference/medical_writing_route_d_v1_review_20260714/general_aishuo_minimax.md`
- `runs/conference/medical_writing_route_d_v1_review_20260714/general_buddy_deepseek.md`
- `runs/conference/medical_writing_route_d_v1_review_20260714/general_opencode_mimo.md`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/TASK_RECORD.md`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/source_brief/synthetic_target_product_profile_v1.json`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/generated/evidence_manifest.json`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/generated/competitor_design_matrix.json`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/generated/decision_ledger.json`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/generated/draftability.json`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/generated/greenfield_candidate_with_gap.json`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/generated/greenfield_route_comparison.json`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/generated/gap_application_summary.json`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/harness/RA_REGULATORY_GAP_WRITER.md`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/run_greenfield_gap_routes.py`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/evaluate_greenfield_routes.py`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/regulatory_style_lint.py`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/tests/test_greenfield_candidate.py`
- `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/tests/test_greenfield_gap_routes.py`

Objective:
Reconcile the participant findings against the remediated Route D v1 implementation and the SYN-RA-201 greenfield pilot. Identify which findings are resolved, which remain, whether the direct-model versus Agent boundary is justified by the frozen evidence, and which reusable controls are pilot-ready without approving medical text or production writes.

Task:
Review all available participant outputs and the updated implementation artifacts, then produce a Hermes sub-venue meeting package. Distinguish pre-remediation findings from current defects. Explicitly examine applicability enforcement, binding/fact equality, source-span containment, metric naming, hash coverage, probe preservation, D001 fail-closed behavior, the RA from-zero workflow, the modular study-flow table, and the bounded direct/Agent comparison. This is a multi-round discussion in the same Hermes session: first compare, then challenge your own synthesis, then issue a corrected recommendation. Do not approve clinical design choices, Chinese regulatory wording, rendered pages, or production writes.

Output schema:
1. `# Hermes Sub-Venue Review: medical_writing_route_d_v1_review_20260714 - general_chair_glm`
2. `## Inputs Reviewed`
3. `## Participant Comparison`
4. `## Conflicts And Missing Work`
5. `## Third-Party Perspectives`
6. `## Rerun Or Supplemental Work Plan`
7. `## Sub-Venue Recommendation To Codex`
8. `## Archive And Resume Notes`

Quality gates:
- Preserve evidence, inference, recommendation, and uncertainty as separate categories.
- Do not claim final clinical/regulatory/visual/current-web authority.
- Do not collapse other model perspectives into your own unless your role is chair/main reviewer and the files are explicitly in the read list.
- Slow or missing participant output is `pending`, not failed, unless it meets the conference failure rule.
- This role is multi-round. Round 1 is the independent pass, round 2 is the skeptical challenge, and round 3 is the corrected final pass in the same Hermes session.
