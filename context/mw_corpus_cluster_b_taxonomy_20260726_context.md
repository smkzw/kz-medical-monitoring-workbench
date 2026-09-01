# Task Context: mw_corpus_cluster_b_taxonomy_20260726

Created: 2026-07-26 22:57:38
Objective: Close G3/G4/G5 facet taxonomy false-high by splitting clinically distinct route, modality and dosage-form concepts with red-first tests.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `runs/conference/mw_corpus_v7_gap_adjudication_20260726/general_chair_pi_qwen38.md`,
  especially G3-G5 and S4-S6.
- Accepted Cluster C state:
  - `services/api/app/medical_writing_corpus_policy.py`
  - `tests/test_medical_writing_corpus_generalization_policy.py`
  - `reviews/codex_mw_corpus_cluster_c_indication_20260726_review.md`
- The current filesystem is authoritative. The workspace is not Git-backed;
  record before/after SHA-256 and a focused unified diff.

## Scope

- In scope:
  - add red-first S4-S6 tests;
  - split SC, IV and IM route concepts;
  - split siRNA, mRNA and oligonucleotide modality concepts;
  - split cell therapy, gene therapy, monoclonal antibody and ADC concepts;
  - split tablet/capsule and cream/ointment dosage-form concepts;
  - retain same-subtype Chinese/English equivalence;
  - make generic terms such as `injection` or `RNA therapy` insufficient to
    prove a specific subtype rather than treating them as every subtype.
- Writable files only:
  - `services/api/app/medical_writing_corpus_policy.py`
  - `tests/test_medical_writing_corpus_generalization_policy.py`
  - task evidence under
    `evidence/mw_corpus_cluster_b_taxonomy_20260726/`
- Out of scope:
  - Cluster A binding logic;
  - Cluster C indication logic;
  - Cluster D phase and controlled indication aliases;
  - schema migration, prompts, UI, runtime, browser, OCR or translation.

## Success Criteria

1. Parametrized negatives prove SC/IV/IM are clinically distinct.
2. Parametrized negatives prove mRNA/siRNA/oligonucleotide, cell/gene and
   mAb/ADC are clinically distinct.
3. Parametrized negatives prove tablet/capsule and cream/ointment are distinct.
4. Chinese/English expressions of the same exact subtype still match.
5. Generic parent terms do not silently prove a specific subtype.
6. Tests are run before production edits and show the intended red state.
7. Focused, full policy, full analysis-AI and accepted nine-file broad
   regression pass after the minimal fix.

## Risk Boundaries

- Production writes are authorized only for the two explicit files above.
- Do not remove facet comparison, weaken high-confidence gates, add catch-all
  aliases or use corpus override/fallback to make tests pass.
- Preserve conservative behavior for unknown/generic subtype evidence.
- Do not reopen accepted Cluster A/C implementation.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-26 22:57:38: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- Cluster A and C are accepted. Cluster B is next in the chair-approved
  A -> C -> B -> D sequence.
