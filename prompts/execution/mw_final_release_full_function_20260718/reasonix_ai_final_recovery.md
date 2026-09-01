You are Reasonix/deepseek-v4-pro recovering the durable independent AI and
persistence report from your already-run acceptance test. This is not a new
broad test. First fully read `/Users/smkzw/.codex/AGENTS.md` and
`/Users/smkzw/.hermes/SOUL.md`.

Hard boundaries:

- Do not edit product source, stable runtime or clinical source documents.
- Do not expose credentials, protected prompts or full clinical source text.
- Write exactly one output file:
  `runs/execution/mw_final_release_full_function_20260718/reasonix_ai_final.md`.

Read these files only:
- `context/mw_final_release_full_function_20260718_context.md`
- `logs/execution/mw_final_release_full_function_20260718/reasonix_ai_final_stdout.txt`
- `logs/execution/mw_final_release_full_function_20260718/reasonix_ai_final_resume_stdout.txt`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ai_final_qc/ai_apply_gate_results_v2.json`

The prior run used the wrong report heading schema and its file was rolled
back. Recover and normalize only observed evidence. Clearly separate the
product's direct DeepSeek `deepseek-v4-pro` result from your independent
assessment. This initial list is not a blanket tool restriction. Record any
additional target if a narrow check is required.

Use these exact headings, all required:

# Execution Output:
## Boundary And Context Check
## Work Performed
## Artifacts And Evidence
## Commands And Observations
## Blockers Or Missing Environment
## Rerun Requests Or Next Step

Cover the four intent contracts, 3-5 candidate behavior where applicable,
evidence/corpus traceability, candidate selection, approval/application,
rich-text synchronization, save/reload/restart, stale-revision rejection and
audit persistence. Include exact evidence paths and the prior session path
recorded in the logs. Use PASS/FAIL/PARTIAL/UNVERIFIED. Return the same complete
report as final response without planning narration.
