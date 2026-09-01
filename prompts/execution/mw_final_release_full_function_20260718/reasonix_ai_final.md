You are Reasonix CLI using `deepseek-v4-pro` for a bounded independent AI,
evidence and persistence acceptance test. Read `/Users/smkzw/.codex/AGENTS.md`
and `/Users/smkzw/.hermes/SOUL.md`.

Hard boundaries:

- Work only inside the current workspace, except the two explicit global
  instruction files above.
- Stable real projects, original clinical sources and product source are
  read-only.
- Use a disposable runtime and random ports for all writes and product-AI
  calls.
- Do not expose credentials, protected prompts or full clinical source text.
- Write exactly one output file:
  `runs/execution/mw_final_release_full_function_20260718/reasonix_ai_final.md`.

Read these files only:
- `context/mw_final_release_full_function_20260718_context.md`
- `plans/codex_execution_mw_final_release_full_function_20260718.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ACCEPTANCE_CONTRACT.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ai_final_qc/ai_apply_gate_results_v2.json`

Actually enter `http://127.0.0.1:5174/` and inspect the current workbench.
Stable real projects are read-only. Use a disposable runtime/random ports for
writes and direct product-AI calls.

Independently verify that the product, not your own answer, calls configured
DeepSeek `deepseek-v4-pro`. Inspect the four distinct intent contracts
(改写、监管语气、查一致性、补证据), 3-5 candidate behavior where generative,
candidate medical usefulness, evidence/corpus traceability, selection,
approval/application, synchronized rich text, save/reload/restart, stale
revision rejection and audit persistence. Reuse current direct-AI evidence
when valid; perform only the minimum real replay needed to prove the current
running code matches it. Also spot-check greenfield and imported workflows so
AI findings remain grounded in actual writer context.

Product source is read-only. Put compact evidence and exact paths inside the
single execution report; do not create product or sibling report files.

Use PASS/FAIL/UNVERIFIED. Distinguish product-AI output from your assessment,
and observation from inference. Codex owns final clinical/regulatory and
release acceptance.

Required headings:
1. `# Execution Output: mw_final_release_full_function_20260718 - reasonix_ai_final`
2. `## Boundary And Context Check`
3. `## Live Work Performed`
4. `## AI And Persistence Matrix`
5. `## Defect Ledger`
6. `## Evidence And Commands`
7. `## Unverified Or Blocked`
8. `## Recommended Reruns`
