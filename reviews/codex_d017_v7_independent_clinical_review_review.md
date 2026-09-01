# Codex Review: d017_v7_independent_clinical_review

Date: 2026-07-25
Final artifact: `reviews/d017_v7_independent_clinical_review_20260725.md`

## Verdict

Pass: the requested independent review is complete and verified. The reviewed
v7 50/17 classification itself requires revision before medical-manager
confirmation because two clinically relevant PNH drug studies remain excluded.

## Boundary Check

- No external agent was dispatched; the workflow guard selected Codex direct.
- No source code, frozen JSON, database, runtime, or source review file was
  modified.
- The requested final report and workflow guard task-record surfaces are the
  only task-created or task-updated files.

## Codex Verification

- Parsed 67 table rows and confirmed 67 unique NCT IDs.
- Confirmed exact set equality with the 67-candidate frozen snapshot.
- Confirmed table v7 classifications agree with the immutable run.
- Confirmed v7 distribution: 50 indirect_reference and 17 excluded.
- Confirmed all 50 indirect-reference records have an explicit pharmacologic
  intervention and indication match; zero reason/classification conflicts.
- Confirmed NCT05731050, NCT06978699, and NCT07212426 are indirect_reference.
- Confirmed NCT02591862 and NCT03439839 are clinically incorrect exclusions.
- Recomputed SHA-256 for all five source files; values remained unchanged.

## Delegated-Agent Output Review

Hermes: not dispatched. Not applicable because the workflow guard selected
Codex direct. Codex performed the source-level and NCT-level review directly.
The final report keeps structural acceptance separate from clinical correctness
and keeps candidate-basket recommendations separate from authoritative
medical-manager confirmation.

## Residual Risk

No live registry refresh or public Protocol/SAP full-text review was permitted.
D017 technology type, route, and target/mechanism remain absent, so direct
competitor status cannot be determined. Three historical/supportive-treatment
records still require medical-manager purpose confirmation.
