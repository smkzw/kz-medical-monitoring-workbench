# Codex Review: mw_corpus_cluster_c_indication_20260726

Date: 2026-07-26
Delegated-agent output: `runs/hermes_mw_corpus_cluster_c_indication_20260726.md`

## Verdict

Pass after narrow Codex remediation and independent verification.

The runner rejected the delegated report because its raw output exceeded the
hard output ceiling and no usable session was registered. That transport
failure does not invalidate the bounded source writes. Codex recovered the
compact final report from the paired stdout, inspected only the four authorized
files and independently verified the implementation.

## Boundary Check

- Production changes were confined to the two authorized implementation files
  and the corpus-analysis test file. The policy test file remained unchanged.
- Task-owned evidence was written only under
  `evidence/mw_corpus_cluster_c_indication_20260726/`.
- No browser, OCR, translation, runtime, database or downloaded-corpus path
  was changed.

## Codex Verification

- Confirmed G9 was closed at both load-bearing loci:
  `_candidate_indication_relation` and policy `_layer_mismatches`.
- Confirmed G8 no longer seeds a span's indication layer from unrelated
  artifact-level basket conditions.
- Found and repaired one narrow residual risk in delegated code: controlled
  acronym expansion used compact substring matching. It now uses the existing
  boundary-aware `_matches_controlled_alias`; a negative embedded-token test
  was added.
- Independent results:
  - focused S7-S9 plus alias-boundary negative: `10 passed`;
  - full analysis-AI plus generalization-policy suites: `54 passed`;
  - broad nine-file selection: `181 passed, 10 warnings`.
- Evidence:
  - `evidence/pytest_corpus_cluster_c_codex_acceptance_v2.log`;
  - `evidence/pytest_corpus_cluster_c_broad_codex_acceptance_v2.log`.

## Delegated-Agent Output Review

- The worker's claimed red-before-fix evidence exists and records nine expected
  failures.
- The worker's final result was useful but excessively verbose; acceptance
  relied on local source and test evidence, not its PASS claim.
- The worker placed the policy-locus test in the AI test file rather than the
  policy test file. This is acceptable because it imports and exercises the
  policy function directly and the independent policy suite remains green.

## Residual Risk

- Span-level indication proof is intentionally conservative. A source where
  the disease appears only in artifact metadata and not in the bound span
  cannot reach high confidence.
- Unregistered cross-language and acronym equivalence remains fail-closed and
  is owned by later controlled alias work, not Cluster C.
- Cluster B route/modality/dosage-form taxonomy remains open.
