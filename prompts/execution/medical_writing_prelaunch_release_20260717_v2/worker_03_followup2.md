# Same-session follow-up 2: worker_03 evidence closure

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`.

## Hard boundaries

- Work only inside the current workspace (`.`).
- Keep the existing frontend/test/browser-evidence write set.
- Use disposable runtimes only. Do not touch stable ports or stable databases.
- Tools remain available and must not be disabled.
- Write exactly one output file:
  `runs/execution/medical_writing_prelaunch_release_20260717_v2/worker_03.md`.

Read these files only for initial context:
- `/Users/smkzw/.hermes/SOUL.md`
- `runs/execution/medical_writing_prelaunch_release_20260717_v2/worker_03.md`
- `frontend/tests/medical_writing_worker03_matrix_v2_qc.mjs`

Continue the latest worker_03 session. Do not inventory features or change
product behavior unless the rerun exposes a new reproduced defect.

Close the evidence gap now:

1. Fix the brittle document-map selector with a stable accessible or
   data-attribute locator. Do not use an arbitrary first button if a unique
   semantic target is available.
2. Run the matrix to completion against a fresh disposable runtime.
3. Prove greenfield Enter-created top-level paragraph persistence through save,
   page reload, exit/re-entry, and backend restart. Verify the saved API payload
   contains the generated `greenfield_authoring` block.
4. Prove imported RUX remains source-preserving: Enter must not create an
   unpersistable top-level block or silently diverge from the saved payload.
5. Complete 1440x900, 1920x1080, and 2560x1440 screenshots and horizontal
   overflow checks; include new-project validation, PICOS required-row
   accessibility, footer, document map, paragraph/table full-screen editors,
   literature/citations, AI apply/undo, save/reload, and recovery states.
6. Write machine-readable JSON, screenshots, console/network summaries, and
   backend-restart proof under
   `records/active_slices/medical_writing_prelaunch_acceptance_20260717/browser_final_qc/`.
7. Run `npm run build` and the focused browser test again after any selector
   repair.

Overwrite worker_03.md with the standard execution-report headings and an
explicit pass/fail/unverified matrix. Do not mark REL-P1-01/02/03 or
REL-GAP-02 closed without durable files.
