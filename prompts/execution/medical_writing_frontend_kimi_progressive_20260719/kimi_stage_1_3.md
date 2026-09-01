# Kimi Code/k3 Assignment: Medical-Writing Frontend Design and Progressive Integration

You are Kimi Code running as the primary independent product designer, frontend
architect, interaction auditor, and execution manager for this bounded slice.
Use model `kimi-code/k3` with high reasoning. Codex remains final acceptance
authority.

Read these files only:
- `context/medical_writing_frontend_kimi_progressive_20260719_context.md`

The initial read list is the starting context, not a blanket prohibition. Follow
the source-of-truth list inside the context, read every named authority before
acting, and record every additional source or tool target in your route/source
log. Before any other action, fully read both the global and project
`AGENTS.md` files named by the context.

For `design.md`, use the Kangzhe brand, color, typography, contrast, logo, and restrained clinical visual language as primary reference. The user explicitly exempts this product application from unrelated fixed HTML-PPT layout/component rules. Do not turn the application into a slide deck.

Hard boundaries:

- Do not modify production frontend source in this pass.
- Do not modify:
  - services/api/app/medical_writing_document_exporter.py
  - services/api/app/medical_writing_protocol_template.py
  - services/api/app/medical_writing_greenfield.py
  - their tests.
- Do not stop stable services:
  - frontend `http://127.0.0.1:5174`
  - API `http://127.0.0.1:8911`
  - Qoder anti-example `http://127.0.0.1:4321`
- Treat the Qoder demo only as an anti-example. Do not copy its DOM, styles, layout, or information architecture.
- Write only under:
  records/active_slices/medical_writing_frontend_kimi_progressive_20260719/
- Build the independent demo under:
  records/active_slices/medical_writing_frontend_kimi_progressive_20260719/kimi_demo/
- Use a separate port such as 4322 for the Kimi demo.
- Use disposable test state for mutating flows; do not change real clinical source files.
- Do not conclude from source inspection alone. Use browser automation, screenshots, console/network observations, keyboard/mouse interaction, and rendered pixel inspection.
- Desktop is the target. Do not remove desktop functionality for mobile responsiveness.

## User Persona and First-Principles Lens

Act as a highly experienced but deliberately lazy Chinese clinical medical writer/medical manager:

- The user wants the system to retrieve, analyze, prefill, and propose; the user edits and decides instead of writing from zero.
- Every repeated field should be prefilled or proposed when evidence exists.
- System state, evidence availability, missing prerequisites, AI progress, errors, and recovery actions must be understandable without reading logs.
- Editing the protocol is the primary experience. Navigation, evidence, AI candidates, citation, table editing, review, and export must support that experience rather than compete with it.
- Clinical rigor does not justify information overload. Source details and audit metadata belong in progressive disclosure.
- A user selection is already a user decision. Do not add redundant “待医学批准” states after the medical user explicitly selected/accepted an item.

## Stage 1: Full Product and Interface Audit

Operate the current stable workbench, not only the source code. Test all meaningful controls and states you can reach, including:

- system shell, project switcher, navigation collapse/expand, logo and header behavior;
- create project from imported synopsis and from greenfield minimal facts;
- study phase, objective, design, phase-I subtype multi-select, drug modality/route, optional IB and no-IB conversational facts;
- evidence/corpus search, candidate studies, import/download/parse/translate/admit workflows, progress and error recovery;
- framing, PICOS, structured prefill, “other” natural-language paths, AI proposal/reproposal;
- chapter/tree navigation, search, default workspace, full-screen editor and return from full-screen;
- rich-text paragraph editing, Enter/new paragraph, formatting, styles, tables, table full-screen/editing, prefilled domain tables;
- AI intent/candidate panel, 3-5 options, replace/insert/refine, evidence context and no silent working-copy mutation;
- references, DOI/PMID/PubMed/URL import, citation insertion, reindexing, bibliography;
- save/version/conflict/offline states and recovery;
- export, progress, success/failure, and generated-file access;
- every button, tab, menu, icon, keyboard path, chart/table/display state, empty/loading/error/disabled state that is present.

For each item, record:

- user intent;
- visible control and exact label;
- default state and preconditions;
- action taken;
- observed visual/interaction result;
- network/API call and important request/response fields;
- frontend source/component;
- backend route/service/contract;
- persistence or job state;
- status: working / partial / blocked by prerequisite / misleading / redundant / missing;
- severity and recommended change;
- screenshot, console, or network evidence locator.

Use the existing Qoder demo as a negative comparator and state exactly which design or product mistakes must not be inherited.

## Stage 2: Independent Kimi Demo and Visual Iteration

Create a runnable, isolated desktop-first demo that independently expresses the preferred experience. It must cover the overall system shell and these medical-writing modules:

1. Minimal new-project intake with AI-prefill.
2. Evidence/corpus preparation and batch progress.
3. Framing/PICOS confirmation through editable recommendations.
4. Main writing workspace centered on document editing.
5. Full-screen paragraph editor and full-screen table editor.
6. AI/evidence panel with 3-5 candidate texts and one-click application.
7. Reference/citation workflow.
8. Export and long-running progress.
9. Empty, loading, error, offline, conflict, and recoverable blocked states.

Visual requirements:

- Kangzhe orange/yellow are restrained brand accents, not the page background.
- White/light surfaces dominate; use neutral deep text and limited medical blue/green/brown only for stable semantics.
- Use the accurate Kangzhe logo asset already in the workbench or design authority.
- No purple tech gradients, decorative orbs, nested card stacks, excessive large-radius pills, or marketing hero.
- Use Lucide icons where applicable, with tooltips for unfamiliar icons.
- Cards have 8px radius or less unless a local established component requires otherwise.
- Every component has deliberate icon, typography, spacing, border, hover, focus, active, selected, disabled, loading, success, warning, error, and empty states.
- Process visibility must distinguish queued, retrieving, downloading, parsing, OCR, chapter recognition, translating, integration QC, ready for review, failed, retrying, and complete.
- Default and full-screen editors must preserve stable toolbar, document structure, AI/evidence access, table capabilities, and return path without white-screen or layout shift.
- Fit 1440x900, 1920x1080, 2048x1024, and 2560x1440 desktop viewports; target mouse/keyboard efficiency.

Run the demo and iteratively inspect it with browser automation and screenshots. Do not claim visual success until you have revisited the rendered images. Record each iteration and what changed.

## Stage 3: Auditable Deliverables

Create at least:

1. `KIMI_ROUTE_AND_SOURCE_LOG.md`
2. `CURRENT_WORKBENCH_FUNCTION_INTERFACE_MAP.md`
3. `KIMI_PRODUCT_INTERACTION_SPEC.md`
4. `KIMI_VISUAL_DESIGN_SPEC.md`
5. `KIMI_DEMO_IMPLEMENTATION_GUIDE.md`
6. `CURRENT_VS_KIMI_GAP_REPORT.md`
7. `PROGRESSIVE_INTEGRATION_BACKLOG.md`
8. `KIMI_BROWSER_VISUAL_QC.md`
9. `kimi_demo/` runnable source and build output.
10. `screenshots/` and machine-readable interaction/QC evidence.

The implementation guide must teach Codex how to reproduce the design in the existing React/Vite/Tiptap architecture:

- design tokens and CSS variable mapping;
- component/state contracts;
- exact class/component insertion points;
- icon mapping;
- layout dimensions and responsive desktop constraints;
- API and state-machine mapping;
- suggested small merge slices;
- tests to add or update;
- rollback steps;
- explicitly deferred ideas.

The integration backlog must separate:

- CSS-only low-risk improvements;
- local interaction/state improvements without backend changes;
- changes needing existing API wiring;
- changes needing new backend contracts;
- rejected ideas that would rewrite the architecture or create new clinical risk.

## Final Response

Runner-managed report path:
`runs/execution/medical_writing_frontend_kimi_progressive_20260719/kimi_stage_1_3.md`.
Never invoke a write/edit tool on this report path. Return the complete report in
your final response and let the runner persist it.

Return a concise loop trace:

- exact files read;
- Kimi model and session evidence;
- browser/tool activity;
- demo path and run command;
- reports and screenshots created;
- tests/build/QC results;
- critical findings;
- uncertainties;
- recommended first production integration slice.

Do not begin production integration in this pass. Codex will inspect the artifacts and continue the same session with an explicit stage-4 write set.
