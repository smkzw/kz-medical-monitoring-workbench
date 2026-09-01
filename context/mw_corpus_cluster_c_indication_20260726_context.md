# Task Context: mw_corpus_cluster_c_indication_20260726

Created: 2026-07-26 22:30:40
Objective: Close G8/G9 indication-alignment false admission at both AI and policy loci with red-first tests and broad corpus regression.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `runs/conference/mw_corpus_v7_gap_adjudication_20260726/general_chair_pi_qwen38.md`,
  especially G8/G9 and S7-S9.
- Accepted Cluster A implementation and tests:
  - `services/api/app/medical_writing_corpus_analysis_ai.py`
  - `services/api/app/medical_writing_corpus_policy.py`
  - `tests/test_medical_writing_corpus_analysis_ai.py`
  - `tests/test_medical_writing_corpus_generalization_policy.py`
- Independent Cluster A evidence:
  - `evidence/pytest_corpus_cluster_a_focused_codex_acceptance.log`
  - `evidence/pytest_corpus_cluster_a_suites_codex_acceptance.log`
  - `evidence/pytest_corpus_cluster_a_broad_codex_acceptance.log`
- The current filesystem is authoritative. The workspace is not Git-backed;
  record before/after SHA-256 and a focused diff.

## Scope

- In scope:
  - add red-first tests S7-S9 for G8/G9;
  - prevent artifact-level conditions from proving that a bound span/cohort
    supports the target indication;
  - stop broader/narrower indication substring containment from being treated
    as verified equality at both the AI relation layer and policy
    high-confidence layer;
  - preserve exact normalized equality and explicit controlled bilingual or
    acronym aliases;
  - run focused, full two-suite and the accepted nine-file broad regression.
- Writable files only:
  - `services/api/app/medical_writing_corpus_analysis_ai.py`
  - `services/api/app/medical_writing_corpus_policy.py`
  - `tests/test_medical_writing_corpus_analysis_ai.py`
  - `tests/test_medical_writing_corpus_generalization_policy.py`
  - task-owned evidence files under
    `evidence/mw_corpus_cluster_c_indication_20260726/`
- Out of scope:
  - Cluster B route/modality/dosage-form taxonomy;
  - Cluster D phase and alias-registry work;
  - schema migration or full per-binding tuple redesign;
  - prompts, UI, browser, OCR, translation, shared services, runtime state,
    downloads and corpus contents.

## Success Criteria

1. S7 proves a multi-condition/basket artifact cannot lend the target
   indication to a span or cohort whose bound text supports another
   indication.
2. S8 covers at least:
   - `慢性鼻窦炎` versus `慢性鼻窦炎伴鼻息肉`;
   - `asthma` versus `severe eosinophilic asthma`;
   and neither pair is verified as the same indication merely by substring.
3. S9 proves the policy-side substring gate is independently closed; an
   AI-only fix cannot make the test pass.
4. Exact same indication and controlled bilingual/acronym aliases remain
   accepted.
5. Tests are run once before implementation to capture the intended red
   behavior, then after the minimal implementation.
6. Focused tests, both full suites and the nine-file broad selection pass.
7. Report changed files, before/after hashes, red evidence, green evidence,
   residual uncertainty and precise evidence locators.

## Risk Boundaries

- Production writes are authorized only for the four explicit files above.
- Do not weaken confidence globally, add broad substring aliases or use a
  corpus override to make tests pass.
- Fail closed to confirmation/review when a span-level indication cannot be
  substantiated. Do not infer a cohort's indication from another cohort in the
  same protocol.
- Preserve user-visible semantics: exact equality and explicit controlled
  aliases are acceptable; parent disease versus phenotype/subtype is not
  silently equivalent.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-26 22:30:40: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-26 22:30: Cluster A independently accepted; Cluster C is next in
  the chair-approved A -> C -> B -> D sequence.
