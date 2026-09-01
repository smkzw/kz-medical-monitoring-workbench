# Same-session follow-up: worker_03

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`, and state
honestly in the report whether you read it.

## Hard boundaries

- Work only inside the current workspace (`.`).
- Keep the previously authorized frontend/test/evidence write set.
- Use only disposable backend/frontend runtimes. Do not touch stable ports,
  stable databases, credentials, or clinical source files.
- Tools remain available and must not be disabled.
- Write exactly one output file:
  `runs/execution/medical_writing_prelaunch_release_20260717_v2/worker_03.md`.
  Source/test edits explicitly authorized by the execution context are product
  work, not additional execution reports.

Read these files only for initial context:
- `/Users/smkzw/.hermes/SOUL.md`
- `runs/execution/medical_writing_prelaunch_release_20260717_v2/manager.md`
- `runs/execution/medical_writing_prelaunch_release_20260717_v2/grok_full_acceptance.md`

The initial list does not prohibit later evidence reads required by the task;
record every additional target and reason.

Continue the existing `Hermes/aishuo/cms-model` worker_03 session. Do not
repeat broad control inventory. Read:

- `runs/execution/medical_writing_prelaunch_release_20260717_v2/manager.md`
- `runs/execution/medical_writing_prelaunch_release_20260717_v2/grok_full_acceptance.md`

Close the desktop P1s with reproduce-fix-rerun evidence:

1. Reproduce why greenfield and RUX document-session APIs are ready while the
   browser remains in `正在加载研究方案文档会话` or
   `真实方案文档会话未就绪`. Capture URL, console, network requests, response
   status/body summary, React state transition, and backend logs. Fix the real
   hydration/fetch/state race; do not merely increase timeouts.
2. Separate editor behavior by document origin:
   - Greenfield authoring must support normal Enter-created paragraphs and
     persist them through save, reload, exit/re-entry, and backend restart.
   - Imported source-preserving content must not silently show a structural
     edit that will be discarded. Provide a usable explicit behavior such as a
     hard break or governed insertion, with clear feedback.
   Research official TipTap/ProseMirror guidance if the fix requires a custom
   keymap or transaction mapping.
3. Complete the durable interaction matrix at 1440x900, 1920x1080, and
   2560x1440. Exercise new-project empty validation and successful creation,
   PICOS required-row accessibility, footer overflow, document map, paragraph
   and table full-screen editors, keyboard/edit controls, literature, citations,
   product AI candidate apply/undo, save/reload, and error recovery.
4. Write machine-readable JSON plus original-resolution screenshots and network
   evidence under
   `records/active_slices/medical_writing_prelaunch_acceptance_20260717/browser_final_qc/`.
5. Run frontend build and focused browser/contract tests.

Use official/mature external sources only after reproducing a blocker, and
record source quality and fit. Keep desktop functionality; do not solve
1440x900 by removing features.

Overwrite the existing worker_03 report with the required headings and a
closed/open defect ledger. An empty evidence directory or source-only
explanation is not completion.
