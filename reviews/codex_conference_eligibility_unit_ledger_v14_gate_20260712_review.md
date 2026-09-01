# Codex Conference Review: eligibility_unit_ledger_v14_gate_20260712

Date: 2026-07-12

## Verdict

Pass after Codex patch and same-session exact-route aishuo follow-up. No bounded P0/P1 remains in the v14 source processing-unit ledger and strict eligibility AI packet gate.

## Boundary Compliance

- The only Hermes sub-venue reviewer was exact `aishuo/MiniMax-M3`, as required by the user's current route.
- Initial stdout verifies requested provider/model, return code 0, completion, session id and `fallback: null`.
- The follow-up resumed the same Hermes session and was explicitly invoked with `--provider aishuo --model MiniMax-M3`; no substitute route was used.
- Generated Buddy DeepSeek, Buddy GLM and OpenCode Mimo prompts were excluded and removed. DeepSeek V4 was not routed through Hermes.
- Hermes made no source edits, ran no tests, used no web/browser/images and did not read original clinical folders.

## Hermes Findings And Codex Adjudication

The first aishuo review reproduced two real P1 classes:

1. A caller-supplied `subject_source_revision` could differ from the locally calculated contract and still be persisted.
2. `aggregate_subject_review` used process-local source-revision memory, which was not safe across workers or restarts.

Codex confirmed both from source and patched them:

- one canonical function now binds project, subject, source id/revision, unit kind, expected count and count status;
- raw intake and workflow registration use the same function;
- mismatched supplied revisions fail before persistence;
- aggregate review reads the unique current revision from SQLite and raises an integrity error on inconsistent current rows;
- the obsolete process-local revision cache was removed.

The same-session aishuo follow-up independently accepted F-1/F-3 and F-2 as closed, found no new P0/P1, and reclassified the span-only branch as bounded legacy compatibility with no current public-path reproducer. Codex agrees. The strict AI packet never accepts that compatibility branch.

## Codex Independent Verification

- Verified raw-intake product mapping persists all six real-subject manifests into isolated SQLite with 297 expected units and zero resolved units.
- Verified every six-subject strict AI state is `not_started`; no provider call can occur.
- Focused post-fix workflow/API/matrix/raw-intake/packet/ledger suite passed 34/34.
- Ruff passed all changed Python files.
- Authoritative full backend regression passed 578/578 in 205.601 seconds after the final patch.
- Frontend production build passed; only the existing >500 kB chunk warning remains.
- No real clinical image was sent to VLM and no real clinical content was sent to an independent LLM.

## Final Decision

Accept the bounded v14 source processing-unit ledger and controlled eligibility AI packet gate.

Production remains blocked on safe archive member extraction, DOC/DOCX subject-file extraction, complete OCR/text extraction and visual QC for all six subjects, independent provider configuration, authentication/RBAC/tenant isolation and remote rate limiting. The six-subject matrix is a source and processing-contract inventory, not a medical-review result.
