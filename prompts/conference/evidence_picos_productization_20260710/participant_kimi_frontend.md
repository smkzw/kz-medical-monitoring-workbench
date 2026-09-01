You are Hermes running inside a Codex-chaired conference workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output, state honestly whether you read the full file.

Conference role:
- Role id: `participant_kimi_frontend`
- Provider/model assigned by Codex: `buddy` / `kimi-k2.7-code`
- Role description: desktop frontend and interaction architecture reviewer
- Conference mode: `parallel`

Hard boundaries:
- Work only inside the current workspace root.
- Do not read or modify external project roots.
- Do not edit source files, browse web, run tests, open browsers, or claim final visual acceptance.
- Write exactly one output file: `runs/conference/evidence_picos_productization_20260710/participant_kimi_frontend.md`.

Read these files only:
- `context/evidence_picos_productization_20260710_conference_context.md`
- `plans/codex_main_venue_evidence_picos_productization_20260710.md`
- `records/active_slices/evidence_picos_productization_20260710/SOURCE_AUDIT.md`
- `records/research/evidence_design_external_benchmark_20260710.md`
- `frontend/AGENTS.md`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`

Objective:
Define a desktop-first Evidence/PICOS product experience that fits the current workbench design system and supports real clinical evidence review.

Task:
Independently specify page hierarchy, component anatomy, state transitions and key interactions for saved searches, evidence queue, screening, extraction/appraisal, conflict/update diff, evidence synthesis, anchored AI revision, PICOS decisions and writing handoff. Identify which evidence code should be extracted from monolithic `App.jsx`, how to avoid silent `.slice` truncation, and how to keep the evidence canvas primary. Do not redesign unrelated modules and do not look at other participant outputs.

Output schema:
1. `# Conference Participant Output: evidence_picos_productization_20260710 - participant_kimi_frontend`
2. `## Boundary Check`
3. `## Independent Work Product`
4. `## Evidence And Assumptions`
5. `## Risks, Gaps, And Verification Needs`
6. `## Recommended Next Step`

Quality gates:
- Preserve current workbench design tokens and desktop-first density.
- Do not make a landing page or card-heavy marketing surface.
- Do not remove desktop controls for mobile convenience.
- Do not claim final visual/browser acceptance.
