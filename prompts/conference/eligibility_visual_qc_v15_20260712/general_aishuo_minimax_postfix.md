Continue the existing `aishuo/MiniMax-M3` sub-venue session. Codex independently adjudicated your findings and applied two narrow fixes.

Read and comply with `/Users/smkzw/.hermes/SOUL.md` in full before reviewing the fixes.

Hard boundaries:

- Work only inside the current workspace.
- Do not edit source, run tests, browse web, open browsers/images, read original clinical folders or inspect controlled artifacts.
- Write exactly one output file: `runs/conference/eligibility_visual_qc_v15_20260712/general_aishuo_minimax_postfix.md`.

Read these files only:

- `services/api/app/eligibility_visual_qc_service.py`
- `tests/test_eligibility_visual_qc_service.py`
- `context/eligibility_visual_qc_v15_20260712_conference_context.md`

Task:

Verify from current source that:

1. the visual-QC image route can no longer serve an artifact whose source revision is not current;
2. a production POST route test now proves `sampled_pass` closes a processing unit and a later `sampled_fail` reopens it as `manual_review_required`;
3. no new P0/P1 defect was introduced by these fixes.

The 100,000-character queue limit remains an intentional fail-closed design. Codex rejects truncation because it could let a reviewer pass an incomplete OCR representation. Treat it as an accepted operational gate, not a correction request.

Return a concise Markdown follow-up with source references, accepted/refuted status for the two fixes, any newly reproducible P0/P1 defect, and a go/revise recommendation. Do not claim visual, clinical or production authority.
