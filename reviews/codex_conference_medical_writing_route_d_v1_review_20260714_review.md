# Codex Conference Review: medical_writing_route_d_v1_review_20260714

Date: 2026-07-14

## Verdict

**PASS for isolated Route D controls and the SYN-RA-201 greenfield pilot. NO-GO for production medical-writing enablement.**

## Boundary Compliance

- All roles used the assigned provider/model and completed three rounds in one Hermes session; no fallback was used.
- Participants and chair stayed inside their explicit read lists. Hermes did not perform Codex-owned rendered-document acceptance, live web verification, medical approval, or production writes.
- The brief user-requested pause interrupted only the outer chair runner after Round 1 had already persisted. Rounds 2/3 resumed session `20260714_143018_794ec8`; no conference reasoning was discarded or recreated.

## Participant Outputs Reviewed

- MiniMax-M3: provenance/source-span and auditability review.
- DeepSeek-v4-pro: binding-to-fact integrity, expression provenance, and hash-chain review.
- MiMo-v2.5: applicability enforcement, realistic-gap validation, and merge-boundary review.
- All three outputs are a pre-remediation baseline. They did not themselves verify the later fixes; Codex verified those fixes through current code and tests.

## Hermes Sub-Venue Review

The GLM-5.2 chair supports reuse of source/fact binding, realization rules, terminology locks, conflict blocking, gap contracts, and provenance controls in isolated research branches. It correctly keeps approved-expression governance and senior medical validation as production blockers.

Codex corrections to the chair package:

- The unresolved `2周/4周` evidence conflict belongs to D001; it is not a RUX conflict.
- Participant outputs raised pre-remediation defects; they did not “confirm resolution.” Resolution is proven by the current code, regenerated artifacts, and 22 passing Route D tests.
- Not every artifact contains `production_eligible=false`. The actual enforced boundary is the combination of isolated slice location, no production route write, `production_write=false` where present, and `production_use_prohibited=true` for the synthetic RA candidate.
- `engineering_candidate` is an internal provenance category already paired with `pilot_engineering_candidate_not_medically_approved`. Renaming frozen pilot artifacts would add audit churn without changing safety. Product-facing surfaces must use the Chinese label `待医学批准候选` and never expose `engineering_candidate` as an approval state.

## Main-Venue Codex Review

- Applicability is enforced against `section_schema_id` in builder and runtime.
- Required slots, bindings, and `binding_fact_map` must be equal; mapped facts must exist and bound values must equal fact values.
- Fact spans must be within section spans and pass content assertions.
- Renderer and orchestrator hashes are frozen; the three-stage live probe history is preserved.
- RUX, PNH, and MY009 complete with zero model calls; D001 blocks before model invocation.
- Direct structured `buddy/deepseek-v4-pro` and bounded Agent fallback both passed the SYN-RA-201 gap contract. Direct invocation is retained only as the default for sentence-sized bounded gaps; this sample does not prove that Agent orchestration is inferior for chapter planning, source conflict review, or tool-assisted retrieval.
- Route D: 22/22 tests passed. Greenfield: 25/25 tests passed. Compileall passed.
- Candidate v0.2 DOCX was reopened structurally and rendered to six pages; all six original-resolution pages were inspected with no clipping, raw Markdown, missing CJK glyphs, or table overflow.

## Codex Independent Verification

- Current source profiles, schemas, controller, runner, regenerated manifests and preserved probe history were inspected directly.
- Route D ran from its canonical slice directory: 22/22 tests passed.
- SYN-RA-201 ran through test discovery: 25/25 tests passed, including v0.2 Word structural assertions.
- Compileall passed for both slices; transient caches were removed after verification.
- All six original-resolution v0.2 rendered pages were inspected. Live web authority checks were not repeated in this final gate because the source files, queryable identifiers, document dates, type/indication checks and SHA-256 evidence manifest were already frozen in the pilot.

## Final Decision

1. Keep Route D and SYN-RA-201 isolated; do not merge their candidate medical text into real projects.
2. Reuse the validated controls in subsequent writing architecture: source-to-fact checks, exact fact binding, applicability, conflict blocking, bounded gap contracts, deterministic regulatory style lint, and medical-approval state separation.
3. Keep direct structured LLM as the default only for small, fully bounded sentence gaps. Use Agent orchestration conditionally where planning, retrieval, or multi-source reconciliation can justify its state and cost.
4. Production enablement still requires company-approved expression sources and senior medical blind review on at least two real projects. D001 remains blocked until authoritative source clarification; no model or template may choose the value.
5. SYN-RA-201 proves a from-zero workflow path, not the medical validity of its fictional doses, sample size, endpoints, or design.
