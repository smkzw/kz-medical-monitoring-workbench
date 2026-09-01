# Codex Review: mw-w4a-recommendation-ui

Date: 2026-07-25

## Verdict

PASS for the W4-A recommendation-first combination package UI and its
independent-AI setup/adoption workflow.

## Boundary Check

- The Codex x Hermes workflow guard selected a visual execution route.
  Delegated implementation and manager reports were treated as evidence;
  Codex inspected source, test logic and rendered pages before acceptance.
- Production changes are limited to the medical-writing combination package
  component, its journey wiring and shared styles. The later test-harness fix
  changes only W4-A QC files and a task-scoped runner.
- No backend adoption contract, TipTap editor, table designer or unrelated
  module was changed by this slice.

## Codex Verification

- Static W4-A contract test passed: one composite request, pending-field
  gating, override/skip payloads, receipt categories, idempotent replay,
  stale-package handling, 409 reload and field-level adoption preservation.
- W4-B/C appendix checks and the Vite production build passed after the W4-A
  merge. The only build warning is the existing large JavaScript chunk.
- The first real-AI browser run proved the complete RA and PNH paths but
  exposed a QC defect: a valid `partial` package with six recommendations and
  three core candidates was incorrectly rejected by a hard-coded
  `availableFields >= 10` assertion.
- The corrected acceptance checks package identity, `ready`/`partial` state,
  at least one available recommendation and at least one core identity
  candidate. It does not weaken product-side pending-field gates.
- A fresh isolated run used the configured direct
  `deepseek/deepseek-v4-pro` product AI and actual ClinicalTrials.gov searches.
  It passed with no failures across:
  - minimum-input RA and PNH project creation;
  - AI recommendation package generation;
  - English condition-term adoption;
  - 656-study/165-document RA and 49-study/37-document PNH searches;
  - single-field adoption and reload persistence;
  - design recommendation adoption;
  - stale revision conflict reload and second-click recovery;
  - 1920x1080 and 2560x1440 no-overflow checks.
- Rendered 1920x1080 evidence confirms unselected alternatives are compact,
  the selected recommendation keeps source text visible, and clinical
  trade-offs/evidence gaps/limitations/affected fields are collapsed until
  requested.
- The screen contains no `待医学批准` phrase. User adoption itself is the
  approval event.

## Residual Risk

- The combination package intentionally remains tall while a pending package
  exposes per-field completion controls; this is necessary work content, not
  a decorative card. Future usability testing may refine field grouping
  without weakening the completion gate.
- This slice accepts setup and recommendation adoption. It does not by itself
  accept chapter drafting, full-document editing or final DOCX export.
