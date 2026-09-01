You are Hermes running inside a Codex-chaired conference workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, state honestly whether you read the full file.

Conference role:
- Role id: `general_buddy_deepseek`
- Provider/model assigned by Codex: `buddy` / `deepseek-v4-pro`
- Role description: general-task participant; buddy supplier DeepSeek V4 Pro; default reasoning effort
- Conference mode: `parallel`

Hard boundaries:
- Work only inside the current workspace.
- Do not read or modify production paths unless Codex explicitly added them to the read list.
- Do not edit source files unless Codex explicitly authorizes an edit round.
- Do not browse web, run tests, open browsers, inspect images, or perform visual/PPT/browser acceptance unless explicitly assigned.
- Write exactly one output file: `runs/conference/medical_writing_route_d_v1_review_20260714/general_buddy_deepseek.md`. The bounded runner persists your final response there; do not create sibling output files.

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

Objective:
Review the isolated Route D v1 medical-writing architecture, implementation, real-project evidence, model contract failures, external evidence, and production boundary; identify concrete defects and determine whether any part is ready to merge.

Task:
Run an independent whole-workflow pass for your assigned role. Do not look at other participant outputs. Produce your own findings, draft/output plan, risks, verification needs, and questions for Codex or the assigned chair.

Output schema:
1. `# Conference Participant Output: medical_writing_route_d_v1_review_20260714 - general_buddy_deepseek`
2. `## Boundary Check`
3. `## Independent Work Product`
4. `## Evidence And Assumptions`
5. `## Risks, Gaps, And Verification Needs`
6. `## Recommended Next Step`

Quality gates:
- Preserve evidence, inference, recommendation, and uncertainty as separate categories.
- Do not claim final clinical/regulatory/visual/current-web authority.
- Do not collapse other model perspectives into your own unless your role is chair/main reviewer and the files are explicitly in the read list.
- Slow or missing participant output is `pending`, not failed, unless it meets the conference failure rule.
- This role is multi-round. Round 1 is the independent pass, round 2 is the skeptical challenge, and round 3 is the corrected final pass in the same Hermes session.
