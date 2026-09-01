# Codex Review: Medical Writing Corpus And Agent Harness

Date: 2026-07-14  
Decision: `research_slice_pass / production_route_no_go`

## Verdict

The bounded research and D0 feasibility slice passes. No production writing route is approved or changed.

## Boundary

This review covers the isolated research scripts, frozen pilot artifacts, deterministic metrics, D0 feasibility outputs and review records. It does not approve a generic Route D, production renderer, medical content, external text-reuse rights or any provider/model as a default production route.

## Highest-Risk Findings

1. **Corrected**: The first audit falsely classified RUX `parallel design` as absent from the fact pack. The frozen pack contained it; all valid A/B/C outputs failed to realize it despite claiming the parent fact ID. The 0.972 metric was withdrawn, and source-to-fact versus fact-to-text gates are now separate.
2. **Corrected**: D001 silently collapsed a 2-week/4-week source conflict, and PNH changed the ethics/informed-consent meaning in a working summary. A/B/C route-quality ranking was withdrawn.
3. **Corrected**: The first D0 template added an unsupported PNH objective. It was removed, and a mutation test now fails if the RUX objective is replaced with unsupported text.
4. **Corrected**: Engineering templates were mislabeled as approved expressions and template IDs were written as evidence. They are now unapproved template candidates, use `template_candidate_ids`, and leave `evidence_ids` empty.
5. **Residual, explicitly bounded**: D0 still uses three project-specific builders and manually curated bindings. It is an engineering feasibility cell, not a generic renderer or complete Route D.

## Verification

- A/B/C source and metric correction: deterministic comparison regenerated; RUX fact pack source coverage is 1.000, while audited critical fact realization is 0/2 for A, 0/2 for B and 0/1 for C.
- D0: RUX and PNH completed with zero model calls; D001 returned `blocked_source_conflict` and no output.
- Negative gates cover required-fact omission, unsupported objective mutation, frozen fact-pack hash drift, missing project pack, preferred terminology, critical text realization and stale blocked output removal.
- Hermes DeepSeek Chinese gate found no v2-relative factual errors in the two D0 outputs and accepted D001 blocking. Codex limits this to v2-relative fidelity because the reviewer did not read the original gold sections.
- Final isolated test gate: `36 passed in 0.81s`.
- Python compileall: passed.
- Persistent D0 rerun after final freeze: passed hash checks with two completed projects and one blocked project.

## Production Decision

Approved as architecture principles only: controlled source tiers, Fact Pack v2 separation, project terminology locks, source-to-fact and fact-to-text gates, unapproved-template isolation and detect-only regulatory lint.

Not approved: production route switch, generic Agent replacement, automatic competitor-text reuse, current D0 builders, current template candidates, B/C/D default selection or model-only medical approval.

## Remaining Work

- Replace project-specific builders with a generic chapter schema and structured transformations.
- Create a medically approved expression contract with source span, version, applicability, approval and supersession metadata.
- Implement gap computation and bounded one-shot generation for only low-risk residual units.
- Run randomized B/C/D comparisons on structured and complex chapters, followed by at least two senior medical reviewers.
