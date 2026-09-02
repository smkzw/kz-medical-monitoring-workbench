# Phase C Implementation Plan

## C1 — Deterministic Admission Contract

1. Inventory existing source/snapshot/store/profile APIs and their product callers; identify the smallest missing seam for real-file isolated-copy admission.
2. Add a stdlib-first staging copier with streaming SHA-256, source/copy manifest and atomic completion. It must never write into the source tree.
3. Add a format-neutral structure-profile contract and bounded parser adapters only for formats already supported by installed workspace dependencies.
4. Persist `SourceRevision` and complete `ListingSnapshot` through the existing Store; retain source cell locators and raw values.
5. Expose thin medical-monitoring product endpoints for create/status/profile preview. Keep `services/api/app/main.py` to mounting/wiring only.
6. Verify with generated, non-real test files: source tree byte/metadata snapshot unchanged, source/copy hashes equal, interrupted copy not accepted, profile is deterministic, cell locator round-trips.
7. Run focused Python tests, adjacent product-route tests, `py_compile`, `git diff --check`, and protected medical-writing route tests. Commit C1 before any real project is opened.

## C2 — Admission Wizard

1. Add one project admission card and a three-step Chinese wizard in the existing medical-monitoring feature.
2. Render structure summary first; place hashes, paths and internal identity in collapsed technical details.
3. Present one primary next action and explicit impact/recovery text for unsupported or ambiguous inputs.
4. Run frontend unit tests and Vite build, then ego(lite) at 1600px with a generated admission fixture. Commit after Codex visual acceptance.

## C3 — First Real Project Pilot

1. Resolve the first project source and isolated output roots read-only; record only non-sensitive inventory summaries in the Trellis journal.
2. Copy one listing batch into the isolated workspace and generate its profile. Do not run medical risk models.
3. Configure optional harness mapping prompts to return evidence-bound candidates only; keep direct API GLM default and DeepSeek capability in the existing adapter boundary.
4. Ask the user to confirm critical mappings in the product, then generate the first facts.
5. Spot-check facts against exact original cells and record counts/outcomes without copying sensitive row content into the journal.

## C4 — Remaining Four Projects

1. Repeat the same admission path one project at a time.
2. Fix shared parser/profile/prompt contracts when a new shape exposes a gap; do not add project, drug, disease or proprietary-column branches.
3. Complete mapping confirmation and fact-location spot checks per project before moving to the next.

## C5 — Diff And Stage Review

1. Identify compatible real dual snapshots and run one full-snapshot diff with added/changed/deleted/uncertain classification.
2. Scan the shared core for the five project names, drug/disease names and proprietary columns observed during admission; dispose every match as code, test-only evidence, or false positive.
3. Run five-project deterministic regression, protected medical-writing checks and ego(lite) admission/fact drill-down.
4. Run one fresh-context independent review focused on provenance, candidate/fact separation, source immutability, anti-overfitting and user comprehension.
5. Fix findings, rerun affected checks, write the Phase C retrospective/Phase D plan in the Trellis journal, and obtain user confirmation.

## Stop And Rollback Conditions

- Stop the current batch on source write detection, copy/hash mismatch, cross-project identity, critical unconfirmed mapping, or locator mismatch.
- Remove only the current unaccepted staging attempt when cleanup is needed; preserve accepted snapshots and all original sources.
- Do not continue to another real project while the current project's locator spot check is unresolved.
