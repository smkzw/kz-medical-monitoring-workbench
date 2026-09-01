# Codex Review: eligibility_source_admission_ui_v1

Date: 2026-07-13

## Verdict

Pass after provider fallback failure and Codex completion.

## Delegation Trace

- buddy/kimi-k2.7-code completed one bounded implementation round but reached the maximum iteration count before adding styles/tests and left state defects.
- OpenCode Go/qwen3.7-plus fallback established a session but terminated after repeated provider HTTP 500 timeout; it did not edit source files.
- Codex retained Kimi's useful state skeleton, corrected the implementation and performed all browser/visual acceptance.

## Boundary Compliance

- Delegated models were restricted to `App.jsx`, `styles.css` and the focused frontend contract test; neither changed backend files.
- Source documents, browser output and model output were treated as evidence, not instructions.
- Codex owned backend writes, final Chinese clinical wording, Chrome acceptance and the final review decision.

## Hermes And Fallback

- Hermes buddy/Kimi produced a partial implementation and a recoverable session record.
- Hermes OpenCode Go/Qwen fallback failed with provider HTTP 500 before any write.
- No unapproved model substitution was made; Codex completed the bounded remainder after both user-approved frontend routes had terminated.

## Corrected Defects

- Preserved the confirmation audit instead of clearing it immediately through the reset helper.
- A confirmed warning no longer continues to show the `确认该来源` action.
- Standardized all copy to `确认沿用` and retained the original `warning/mismatch` content state.
- Moved the source-admission band directly below the page title and before project/review status.
- Added bounded two-source desktop layout, all-check display, bundle scope disclaimer and disabled-button explanations.

## Backend Gate

- Human write actions and independent-AI draft execution call the same server-side source-admission guard.
- Missing validation, technical failure or unconfirmed warning/mismatch returns structured 409.
- Read-only source, subject, review and visual-QC access remains available.
- Directory source identity now includes per-file byte digests with path/stat cache; same-size replacement creates a new source version and invalidates the old confirmation.

## Independent Verification

- D001 and MY009 real source refreshes each returned protocol plus raw subject bundle.
- D001: protocol matched/allowed; bundle warning/requires_confirmation; exact check plus 10+ character reason changed only use status to confirmed_after_warning.
- MY009 remained unconfirmed after project switch; D001 reason did not leak. Returning to D001 preserved its isolated confirmation.
- MY009 displayed three disabled write actions while admission was not ready.
- Chrome 1600x1000 and 1920x1080 checks found no page horizontal overflow, path/hash leak or security-scan wording.
- Browser evidence: `records/visual_qc_20260713/eligibility_source_admission/eligibility_source_admission_qc.json` and adjacent PNGs.
- Focused backend/frontend tests and production build passed before full regression.

## Residual Scope

This closes eligibility source admission and write/AI gating, not the remaining OCR/VLM visual review queue, full subject evidence processing or medical completion of every IN/EX criterion.
