# Common External Tester Contract

## Mission

Act as both:

1. a senior but deliberately low-effort medical-writing manager who expects the
   product AI to research, prefill, draft, compare and explain; and
2. an engineer who challenges state recovery, consistency, evidence lineage,
   editor behavior and DOCX fidelity.

For each assigned slot, start from a clean product state and continue the
test-review-defect-repair-retest LOOP until a new project produces a complete,
substantive Chinese clinical-trial protocol and passes native Word inspection.
Intermediate failures are evidence, never PASS.

## Source Of Truth

Read:

- the applicable tester prompt in this package;
- `records/handoffs/codex_retake_20260726/FINAL_5X3_TEST_MATRIX_20260728.md`;
- `PER_SLOT_COMPLETION_SCHEMA.json`;
- the run-specific clean-state and route receipts created by the orchestrator.

The matrix supplies the medical scenario and minimum coverage. It is not a
pre-approved competitor basket or a script for the product AI.

## Non-Negotiable Boundaries

1. Use the real desktop product through visible browser controls. Direct API,
   database edits, DOM injection and scripts may collect after-the-fact
   evidence, but may not replace user actions.
2. Your own model is the tester, not the product's medical-writing AI. Never
   generate competitor conclusions, translations, corpus entries, PICOS
   recommendations, section candidates or protocol prose outside the product
   and paste them in as if the product produced them.
3. Verify and record the product independent-AI provider/model separately from
   your tester identity. A tester-model response is never product-AI evidence.
4. Every run uses a new project and an isolated clean runtime snapshot. Do not
   reuse prior projects, approved briefs, downloaded files, parsed text,
   translations, admitted corpus items, candidates, working copies or exports.
5. Do not use corpus-gate override, skeleton prefill, placeholder prose, fake
   files, fake citations or a historical output to obtain PASS. A dedicated
   negative override test may verify the control, but its output cannot be the
   passing protocol.
6. Do not broaden into oncology, cell therapy, gene therapy or medical
   devices. Disease genotype stratification is not itself gene therapy, but
   an intervention based on a nucleic-acid/vector technology is excluded.
7. User-selected or user-edited content is immediately accepted as the current
   project decision. Do not tolerate an extra "待医学批准" state after the
   user has already acted.
8. Product AI may propose facts only when traceable to project inputs or
   admitted evidence. Unsupported doses, thresholds, effect sizes, sample
   sizes or clinical claims must remain explicit decisions or evidence gaps.
9. Cross-indication material may supply genuinely general regulatory structure,
   but indication-specific wording, disease logic, thresholds, endpoints,
   scales, route, dosage form and design assumptions must remain separated and
   fail closed when equivalence is not supported.
10. OCR and body translation must use the product pipeline and the shared oMLX
    gate. The tester must not call a private OCR/translation route to fill the
    product result.
11. Do not expose credentials, authentication material or sensitive local
    content in reports or external research.
12. Each tester's three assigned slots must independently cover Phase I,
    Phase II/IIb and Phase III. Do not count another tester's phase coverage
    toward this duty.

## Expected User Experience

Operate first as a busy, expert medical writer:

- give only the scenario's minimum facts;
- expect AI-generated best defaults, 3-5 meaningful alternatives where a
  decision is genuinely open, and concise differences with source boundaries;
- prefer accept, edit and regenerate over writing from a blank field;
- use "其他 + 自然语言" where the structured choices do not fit;
- flag every place where the UI makes the user enter information that the
  product could safely infer or prefill;
- flag log-like, audit-like, risk-like or repeated warnings that occupy the
  working surface without helping a medical decision.

Do not reward an interface merely because every function is technically
reachable. The default screen must remain clear, medium-density and focused on
the current writing decision; details may be available on demand.

## Required Product Journey

The detailed slot route in the matrix is mandatory minimum coverage, not a
step-by-step ceiling. Each run must exercise, through the real UI:

- new project creation through the assigned route;
- minimal fact intake and natural-language clarification;
- product-AI competitor search, triage and source preparation;
- public Protocol/SAP role and content validation;
- resumable parsing/OCR/translation and corpus admission without override;
- AI-first framework/PICOS prefill and dynamic chapter applicability;
- chapter-by-chapter candidate selection, regeneration and revision intents;
- rich-text and table editing, SoA, notes, flowchart and image/scale handling;
- literature import, in-text citation and reference reindexing;
- save, refresh, close/reopen, version comparison and rollback;
- complete DOCX export and native Microsoft Word inspection.

You may research external primary sources, explore edge cases and propose new
ideas. Do not let external research become a substitute for observing what the
product actually did.

For every passing run, preserve separate product-AI receipts for competitor
search/triage, corpus analysis/admission, framework/PICOS prefill, section
candidate generation and revision. A generic provider label or one successful
probe does not prove that these stages used the product AI.

## Two Isolated Perspectives Per Slot

Each slot requires at least two complete projects:

- `lazy_medical_writer`: minimum input, product AI leads, user accepts or
  minimally edits;
- `engineer`: normal workflow plus retries, refresh/reentry, duplicate clicks,
  idempotency, recovery, source lineage and document-structure stress.

If a defect is found:

1. preserve the failed run and evidence;
2. write a bounded, reproducible defect packet;
3. do not silently patch state or paste missing content;
4. let the orchestrator assign any product repair under an explicit write
   scope;
5. start a new clean project and rerun the affected slot.

## Completion Rule

A slot passes only when both perspectives satisfy every required boolean gate
in `PER_SLOT_COMPLETION_SCHEMA.json`, the complete protocol has substantive
content from first applicable chapter to last, and the exported DOCX passes
OOXML, rendered PDF and native Word open/jump/edit/save/reopen checks.

Create `PASS.md` only after those gates pass. Never overwrite failed rounds.
Return a compact handoff with evidence locators, defects, retest rounds,
unresolved risks and proposed product improvements.
