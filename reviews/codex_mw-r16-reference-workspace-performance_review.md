# Codex Review: mw-r16-reference-workspace-performance

Date: 2026-07-29
Delegated review: Codex subAgent `019fab3a-2cb5-7553-9d53-97778c3a6406`

## Verdict

**PASS for the r15 D1 technical repair.** The original r15 A1 remains
`BLOCKED`; product acceptance requires a new clean visible-browser A1 run.

## Boundary Check

- The delegated agent was read-only and returned delta findings; it did not
  modify product, test, configuration, or frozen evidence files.
- Concurrent medical-monitoring changes in `main.py` and `App.jsx` were
  preserved. This slice changed only the reference repository, its direct
  tests, the one snapshot parameter at the workspace endpoint, harness hashes,
  and task records.

## Codex Verification

- `python3 -m py_compile ...`: passed.
- Focused reference/API/frontend regression: `148 passed`.
- Broad medical-writing chain: `1,032 passed`.
- Shared monitoring protection: `227 passed`; Node suites reported
  `37`, `40`, `27`, and subject-model suite passed.
- Concurrent initialization: 20 rounds, 8 independent processes per round,
  covering fresh and v6 databases.
- Frozen r15 copy: schema `6 -> 7` in `0.2734s`; actual FastAPI workspace
  response HTTP 200 in `0.0791s`, `1,680,912` bytes, 665 candidates,
  70 artifacts, and 70 artifact span-count entries.
- API contract test asserts that an exact requested snapshot is propagated to
  `source_span_counts`.

## Delegated-Agent Output Review

- Accepted findings: cross-process initialization race, missing snapshot
  isolation, and deterministic latest-extraction ordering.
- Remediation was independently reproduced with real processes and the frozen
  r15 database copy; model confidence was not used as acceptance evidence.
- Index growth is intentional and bounded by the performance requirement. No
  corpus gate, document validation, or medical conclusion logic was changed.

## Residual Risk

- This repair proves the timeout path, not the remaining end-to-end authoring
  journey. A new clean A1 must still pass document validation, corpus admission,
  OCR/translation, chapter authoring, references, DOCX/PDF export, and native
  Word reopen/edit/save/reopen.
- The file-lock implementation is POSIX/macOS oriented, which matches the
  current local deployment. A future non-POSIX deployment needs an equivalent
  cross-process migration lock.
