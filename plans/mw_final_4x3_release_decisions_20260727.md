# Final 4x3 Release Decisions

Date: 2026-07-27
Status: ACTIVE

## Per-run isolation

Each tester slot and each perspective is a separate physical run:

1. Create a new isolated runtime, browser profile and download directory.
2. Start the API before the frontend.
3. Write a fresh clean-state receipt naming tester, slot and perspective.
4. Complete exactly one new project and retain its evidence.
5. Stop only the services started for that run.
6. Prove the completed runtime is dirty, then create a different clean runtime
   for the next run. Never clean and reuse the completed runtime in place.

The shared product runtime and any prior project, parsed source, corpus result,
browser profile or download directory are not final-matrix inputs.

## B1 distributed-fact reconciliation

The product must collect comparator, background metformin, rescue therapy and
estimand statements from every imported synopsis location into one
reconciliation view. It may:

- preselect an internally consistent interpretation when the supplied facts
  support one;
- show concise alternatives when multiple interpretations remain plausible;
- cite the source text for each material difference.

The product must not invent a placebo-calibration arm, noninferiority margin,
multiplicity sequence or rescue threshold. The author confirms or edits the
single reconciled design before it becomes an approved study fact.

## C2 clinical-operational gaps

The product may propose a small number of corpus-supported options for repeat
biopsy, central reading and adjudication. Each option must separate:

- evidence-supported design implications;
- operational feasibility assumptions;
- facts still requiring sponsor or medical confirmation.

It must not choose a validated registrational endpoint, effect size, sample
size or biopsy feasibility conclusion without project evidence. Open
feasibility questions remain editable confirmations, not warning cards and not
blank free-text requirements.

## Leakage assertions

Every synopsis fixture must include positive supplied-fact assertions and
negative leakage assertions. A generated value fails the fixture when it is a
study-specific decision absent from the synopsis, admitted corpus or an
explicit author confirmation. General evidence-bounded options are allowed
only when clearly presented as options rather than confirmed study facts.

## DOCX visual evidence

`scripts/render_docx_visual_qc.py` records the exact expected text in its JSON
report. A failed expected-text check is not interpreted until that recorded
string is compared with the PDF text layer. Native Word field update, TOC
navigation, editable styles, tables, figures and save/reopen remain separate
release gates.
