# Same-session remediation: flowchart edge-label integrity

Continue the existing Grok Build session
`00723d75-68c5-4dee-9187-9e1f81de030b`. Do not start a replacement task.

## Read these files only

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `context/mw_flowchart_label_clip_20260724_context.md`
- `runs/execution/mw_flowchart_label_clip_20260724/grok_worker_01.md`
- `services/api/app/medical_writing_study_schema.py`
- `tests/test_medical_writing_study_schema.py`
- `records/active_slices/medical_writing_real_scale_word_e5_20260724/scripts/run_real_ibdq_docx_gate.py`
- `reviews/codex_real_ibdq_word_gate_final_20260724.md`
- task-scoped generated evidence under
  `records/active_slices/medical_writing_real_scale_word_e5_20260724/`

Write exactly one output file:
`runs/execution/mw_flowchart_label_clip_20260724/grok_worker_02.md`.
This is the runner-managed report. Do not write it with tools; return the
complete report in final text and let the runner persist it.

## Hard boundaries

Authorized source/evidence write set:

- `services/api/app/medical_writing_study_schema.py`
- `tests/test_medical_writing_study_schema.py`
- task-scoped regenerated evidence under
  `records/active_slices/medical_writing_real_scale_word_e5_20260724/`

Preserve unrelated changes. Do not edit any other production code. Do not add
project-specific branches, text substitutions, or literals. Do not claim final
visual or Word acceptance; Codex owns it.

## Why the prior pass is not accepted

Codex source review found two residual correctness failures:

1. `_edge_label_wrap_candidates()` slices wrapped lines to
   `_EDGE_LABEL_MAX_LINES`. This can silently discard the tail of an allowed
   edge label, including labels near the current 300-character contract.
2. `_place_edge_label()` remembers an intersecting `best` candidate and emits
   it when no clear slot exists. That silently permits node-label overlap
   instead of reflowing or expanding the layout or failing explicitly.

The prior real IBDQ label clipping fix must remain intact.

## Required remediation

1. Preserve every edge-label character exactly. Wrapping may insert visual line
   breaks, but must never truncate, elide, summarize, replace, or reorder source
   text.
2. Never emit an edge label that intersects a node or falls outside the SVG
   canvas.
3. If ordinary placement candidates do not fit, deterministically expand or
   reflow the SVG canvas or relevant routing band and retry. If a valid
   placement still cannot be produced, fail explicitly with a precise
   validation error. Do not use a least-bad overlap fallback.
4. Add a stable `data-edge-label-for="<edge id>"` attribute to every edge-label
   group or text container so automated acceptance can associate label text
   with the exact edge.
5. Preserve the current public API and all unrelated rendering behavior.
6. Regenerate the real IBDQ SVG and PNG evidence using the existing workflow.

## Required tests

Add focused deterministic tests that prove:

- a near-maximum-length mixed Chinese and Latin label preserves its complete
  normalized source text in the SVG;
- every edge label is associated with the correct edge through
  `data-edge-label-for`;
- all edge-label bounding boxes are fully inside the canvas;
- no edge-label bounding box intersects any node bounding box;
- the same assertions hold for the real IBDQ fixture and for both SVG and PNG
  generation paths;
- a deliberately dense fixture either reflows or expands successfully or
  raises the explicit validation error; it must never silently emit overlap;
- the prior `240 mg BID安全性不佳` clipping regression remains fixed.

Run the focused flowchart tests, relevant DOCX or Word-native tests, and the
broader medical-writing regression suite used in the prior pass. Reopen the
regenerated 200-DPI visual evidence and report concrete observations.

## Completion report

Return a compact loop trace: files read and changed, exact tests and results,
regenerated artifact paths, visual observations, failed paths, residual
uncertainty, and recommended next action.

End with exactly:

`GROK_FLOWCHART_LABEL_CLIP_02_COMPLETE`
