# Live Tester Contract: release-r6 A1 lazy medical writer

Use exact external tester `pi/alibaba/qwen3.8-max-preview`, OMP selector
`alibaba-token-plan-cn/qwen3.8-max-preview`, thinking `xhigh`,
`--no-prewalk`, and single-model scope. You are the visual tester and browser
operator, not the product medical-writing AI.

Read the common tester contract, route/time guard, Tester A contract,
completion schema, current matrix and
`release-r6-20260728/slots/A1/SLOT_CONTRACT.json` before acting. Use only:

- product: `http://127.0.0.1:51365/`
- API: `http://127.0.0.1:51364/`
- evidence:
  `runs/execution/mw_final_4x3_harness_20260727/rounds/release-r6-20260728/slots/A1/lazy_medical_writer/`

## Scenario And Minimum Facts

Create a new greenfield Phase III COPD inhaled fixed-combination project.
Provide only:

- study drug code `CMS-COPD-301`;
- COPD, Phase III, inhaled DPI, no Investigator's Brochure;
- a new inhaled small-molecule fixed combination on stable maintenance
  inhaled therapy, intended to reduce moderate/severe exacerbations;
- likely twice-daily administration;
- bronchodilator plus anti-inflammatory pharmacology;
- plausible reversible local respiratory irritation and exposure-related
  tachycardia, with exact human thresholds unknown.

Do not provide a completed study design. The product independent AI must
research, triage, prepare evidence, recommend the design, prefill framework
and PICOS, and draft every applicable protocol chapter.

## Required Journey

Act as a busy, expert, deliberately low-effort Chinese medical-writing
manager. Use real visible browser controls for every product action. Enter
only facts the product cannot safely infer; prefer the best AI default,
minimal edits and regeneration over writing from blank fields.

Run the complete journey:

1. Create the clean project and verify the configured product AI identity.
2. Run ClinicalTrials.gov research and AI triage. Inspect at least three
   original public Protocol/SAP documents where available.
3. Confirm that COPD Chinese/English equivalence is exact and does not admit
   asthma, bronchiectasis, chronic bronchitis, emphysema or COPD-like labels.
4. Confirm public Protocol/SAP lineage remains attached to the correct NCT.
5. Confirm a triage retry that reaches review-ready reconciles the parent
   research pipeline without restarting search or losing the locked basket.
6. Continue with the locked retained basket. During preparation, record the
   visible sequence of truthful progress messages. It must identify locked
   candidate count, public-document count, completed count and current
   NCT/document; it must not claim that every search result is being prepared
   and must not display a fabricated fixed ETA.
7. Complete file-content validation, OCR/translation/resume where applicable,
   corpus admission without override, framework/PICOS, dynamic chapter
   applicability, all chapter candidate generation and selection, AI
   revisions, rich-text editing, tables, SoA and notes, flowchart, literature
   citations, save/reload/versioning, complete DOCX, rendered PDF and native
   Word navigation/edit/save/reopen.

Check COPD-specific background therapy, inhaled route/device, exacerbation
endpoints, rescue medication, local/systemic safety and PK/PD logic. The
product may borrow evidence only with explicit indication, phase and modality
boundaries. Do not write medical prose with the tester model and paste it into
the product.

Explore freely beyond the mandatory journey. Flag unnecessary typing, option
walls, repeated warnings, audit/log clutter, or any state where the product
expects the tester to replace independent-AI work.

Do not modify product source, tests, prompts, shared runtime or historical
evidence. Do not use direct API/database/DOM injection instead of UI actions.
Do not use skeleton content, placeholders, corpus override or create
`PASS.md`.

Create every required structured evidence file plus
`EXTERNAL_TESTER_REPORT.md`. End the report exactly with:

- `A1_LAZY_EXTERNAL_TEST_COMPLETE`, or
- `A1_LAZY_EXTERNAL_TEST_BLOCKED:<short reason>`.
