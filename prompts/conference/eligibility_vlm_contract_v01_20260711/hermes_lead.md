You are Hermes running inside a Codex-chaired conference workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, state honestly whether you read the full file.

Conference role:
- Role id: `hermes_lead`
- Provider/model assigned by Codex: `aishuo` / `MiniMax-M3`
- Role description: single Hermes sub-venue chair
- Conference mode: `parallel`

Hard boundaries:
- Work only inside the current conference workspace.
- Do not read or modify production paths unless Codex explicitly added them to the read list.
- Do not edit source files unless Codex explicitly authorizes an edit round.
- Do not browse web, run tests, open browsers, inspect images, or perform visual/PPT/browser acceptance unless explicitly assigned.
- Write exactly one output file: `runs/conference/eligibility_vlm_contract_v01_20260711/hermes_lead.md`.
- State the actual provider/model markers observed for this run. If they are not `aishuo/MiniMax-M3`, write only a routing-failure report and do not synthesize the conference.

Read these files only:
- `context/eligibility_vlm_contract_v01_20260711_conference_context.md`
- `plans/codex_main_venue_eligibility_vlm_contract_v01_20260711.md`
- `runs/conference/eligibility_vlm_contract_v01_20260711/participant_qwen_plus.md`
- `runs/conference/eligibility_vlm_contract_v01_20260711/participant_mimo.md`
- `runs/conference/eligibility_vlm_contract_v01_20260711/participant_ds_flash.md`
- `records/active_slices/eligibility_next_slice_20260711/VLM_CLOSED_VOCABULARY_CONTRACT_V0_1.md`

Objective:
Review and adjudicate the closed-vocabulary VLM contract for eligibility visual evidence before any implementation or real clinical-image use

Task:
Review all three participant outputs and the contract, then produce the Hermes sub-venue meeting package. Compare disagreements, fill gaps, decide whether reruns are required, and give explicit keep/remove/change decisions for every open schema field. Add medical-manager, data-protection, QA/validation, investigator-site, and regulator perspectives. Do not make Codex-owned final decisions and do not authorize real clinical-image use.

Output schema:
1. `# Hermes Sub-Venue Review: eligibility_vlm_contract_v01_20260711 - hermes_lead`
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
