# Codex Review: mw_corpus_ai_analysis

Date: 2026-07-26
Delegated-agent output: `runs/codex_mw_corpus_ai_analysis.md`

## Verdict

Pass for the scoped corpus-analysis slice. Adjacent suite has a separately
owned concurrent competitor-triage regression and is not globally green.

## Boundary Check

- Product code writes are limited to the research pipeline and the new corpus
  analysis service; dedicated tests and requested evidence report were added.
- Authoring prefill/evidence binding and translation were not modified.
- Competitor triage changed concurrently in the shared workspace; this slice
  did not claim or remediate that change.

## Codex Verification

- Focused corpus analysis and policy tests: 26 passed.
- Initial adjacent regression: 445 passed.
- Final adjacent regression after a concurrent triage edit: 439 passed,
  6 competitor-triage call-count failures.
- Real product-AI PNH acceptance completed on
  `alibaba_token_plan/qwen3.8-max-preview`; 4 evidence-bound findings were
  persisted in a temporary copy and inspected before cleanup.

## Delegated-Agent Output Review

Codex directly inspected the source, validated the immutable persistence path,
reviewed the real model rejection, and confirmed single-NCT/sponsor confidence
did not become high. No external model output was used as acceptance authority.
Hermes was not dispatched for this bounded implementation; the frozen product
AI was called only as the system under test, not as a reviewing agent.

## Residual Risk

- Controlled terminology currently covers PNH only; other cross-language
  non-matches remain pending medical confirmation.
- Running API process requires restart to load the code.
- Concurrent competitor-triage regression must be resolved in its owning slice.
