# Same-session follow-up 2: worker_01 evidence correction

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`.

## Hard boundaries

- Work only inside the current workspace (`.`), with the same authorized
  backend/test/evidence write set.
- Use disposable runtimes only. Do not touch stable ports, stable databases,
  credentials, or clinical source files.
- Tools remain available and must not be disabled.
- Write exactly one output file:
  `runs/execution/medical_writing_prelaunch_release_20260717_v2/worker_01.md`.

Read these files only for initial context:
- `/Users/smkzw/.hermes/SOUL.md`
- `/tmp/worker01_v2_e2e.py`
- `/tmp/worker01_v2_stdout.json`
- `/tmp/worker01_v2_stderr.log`

Continue the worker_01 session. Do not rerun the already successful D017
synopsis parsing or the expensive real DeepSeek call unless a new product
change affects them.

Correct and finish the evidence:

1. Add the required greenfield document-creation fields, including
   `protocol_id`, `version`, `study_phase`, template identity, and the existing
   study-definition binding. Complete greenfield document creation, working
   copy, structured table/literature availability, Word export, save/reload,
   stale reject, and backend restart.
2. The competitor execute stage returned HTTP 404 while the script labelled
   the stage pass. Diagnose the exact endpoint/identifier contract. Mark it pass
   only if plan-to-execute truly succeeds; otherwise report a product or fixture
   defect accurately and add a focused test if product code changes.
3. The second-intent stage returned 200 while its explanation says an expected
   409. Inspect actual thread state and correct the contract conclusion. Do not
   invent a busy-state rule.
4. Preserve the already recorded successful facts from
   `/tmp/worker01_v2_stdout.json`: D017 import with framing prefill, direct
   DeepSeek candidate count/lengths, RUX save/stale/concurrency, SQLite
   integrity, and restart persistence. State that candidate texts were
   punctuation-level variants of the same confidentiality paragraph and are
   not yet sufficient evidence of broad clinical-writing quality.
5. Run focused tests for any changed backend path and write a corrected
   pass/fail/unverified report with the standard execution-report headings.

Do not call an HTTP 404 a pass and do not leave the report as runner rejection.
