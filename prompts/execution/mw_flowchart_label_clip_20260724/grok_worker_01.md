# Bounded visual execution: generic study-schema edge-label layout

You are Grok Build / grok-4.5 acting as the write-capable first-line visual
execution worker. Fully read and comply with global and project `AGENTS.md` and
your normal operating instructions. Work only in the runner-provided workbench.
This run uses `permission-mode=bypassPermissions`.

## Read these files only

- `context/mw_flowchart_label_clip_20260724_context.md`
- `services/api/app/medical_writing_study_schema.py`
- `tests/test_medical_writing_study_schema.py`
- `records/active_slices/medical_writing_real_scale_word_e5_20260724/scripts/run_real_ibdq_docx_gate.py`
- `runs/execution/mw_real_ibdq_word_gate_20260724/kimi_manager_review_01.md`
- `records/active_slices/medical_writing_real_scale_word_e5_20260724/rendered_200dpi/page_03.png`

Write exactly one output file:
`runs/execution/mw_flowchart_label_clip_20260724/grok_worker_01.md`. This is the
runner-managed report. Do not write it with tools; return the complete concise
report in final text and let the runner persist it.

## Hard boundaries

Authorized source/evidence write set:

- `services/api/app/medical_writing_study_schema.py`
- `tests/test_medical_writing_study_schema.py`
- task-scoped regenerated evidence under
  `records/active_slices/medical_writing_real_scale_word_e5_20260724/`

Preserve unrelated changes. Do not edit any other production code. Do not add
project-specific branches or literals.

## Required implementation

1. Reproduce the actual overlap from current source. The affected conditional
   edge label is wider than the inter-node corridor and is drawn before nodes,
   so a node masks its prefix.
2. Implement a generic deterministic edge-label layout for horizontal,
   vertical, conditional, switching, continuation and activation edges. Labels
   may wrap into multiple lines or move to a clear side of the route, but every
   line and background must remain inside the SVG canvas and outside both
   endpoint node rectangles. Preserve restrained clinical-document styling.
3. Keep SVG and PNG fallback semantically equivalent. Do not solve only the SVG
   path or only the fixture.
4. Add executable geometry tests. At minimum prove:
   - the real long mixed Chinese/Latin conditional label does not intersect
     source or target node rectangles;
   - a long label near the canvas edge stays inside the canvas;
   - short existing labels and node text still render;
   - SVG and PNG rendering succeed.
   Do not use only source-string assertions.
5. Run focused study-schema tests and relevant exporter/OOXML tests. Regenerate
   the fixture output needed for Codex visual review, but do not operate Word or
   overwrite the accepted Word-roundtrip evidence unless the task script
   explicitly creates a new revisioned artifact.
6. Report exact changed files, test counts, regenerated artifacts, remaining
   uncertainty, and a compact loop trace.

Do not claim final visual or Word acceptance. Codex owns it.

Completion marker:
`GROK_FLOWCHART_LABEL_CLIP_01_COMPLETE`
