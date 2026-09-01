# R7 Slice-09C implementation conference round-2 remediation record

Date: 2026-08-30
Scope: synthetic/offline only. No service, model, browser, real project, or medical-writing change.

## Round-1 findings addressed

- P1-1: repaired publication verification locals and added populated-publication coverage for healthy, cross-project, and missing-anchor paths.
- P2-1: wired application startup to the shared `RecoveryCoordinator`; the coordinator now scans 09A public restore-recovery states without replaying filesystem switches and resumes only 09B states through the accepted migration runner. Retained-triage and failed/retry-only states remain excluded.
- P2-2: added a true two-process technical-log rotation/append test; every active/archive line is parsed after both processes finish.
- P2-3/P4-1: added a 15-cell subprocess matrix covering audit payload/chain hashes, verifier fingerprint, and technical-log JSONL under five hash seeds, normal/`-O`/`-OO`, three TZ values, and C/POSIX locale variants.
- P3-1: added SQLite `BEFORE UPDATE` and `BEFORE DELETE` abort triggers for root project-audit events; detached/out-of-band tamper detection remains tested by dropping the trigger only inside synthetic fault injection.
- P3-3: added `.rollback-*` sibling evidence scanning with symlink/non-directory classification.
- Deterministic fingerprint correction: canonical SQLite schema/row content is hashed instead of SQLite page bytes; generated R1 `meta.store_id` and `-wal`/`-shm` sidecars are excluded, while business rows and schema remain covered.

## Codex decisions on contract interpretation

- P3-2: a pre-existing broken root chain is a fail-closed safety exception to the pair-append rule. Appending a fresh `verification_started/completed` pair over a chain already proven invalid would manufacture a misleading continuation. The verifier therefore returns `发现异常` without mutating that root; all calls starting from a valid root append the required pair.
- P4-2: the 8 KiB limit applies to the complete serialized JSONL line, including `segment_bytes` and newline. This is intentionally stricter and fail-closed; no partial line is emitted.

## Current decisive checks

- Focused audit/verifier/technical-log tests: `33 passed`.
- New 09C determinism/TZ/locale matrix: `15 passed`.
- Full R7 suite after the first remediation batch: `522 passed`, 19 warnings; the later 09A startup-scan addition was then rechecked with `12 passed` focused verifier tests.
- Compile checks passed for all changed Python modules.

## Required independent round-2 decision

Reopen the frozen v0.2 contract, this remediation record, the current source, and current tests. Do not rely on counts alone. Report only remaining P0-P4 defects, with exact evidence locators. Explicitly challenge the startup scan boundary, canonical SQLite fingerprint exclusions, cross-process rotation assertions, append-only triggers, and the fail-closed root-chain exception. If no issue remains, state `P0=P1=P2=P3=P4=0` and list residual non-blocking limitations separately.
