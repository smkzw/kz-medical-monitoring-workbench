Continue the same `cms-model` execution session. Do not create another large harness and do not repeat source discovery.
Continue to comply with `/Users/smkzw/.hermes/SOUL.md` and `/Users/smkzw/.codex/AGENTS.md` as already read in this session.

Hard boundaries:
- Do not publish, touch stable ports/databases, overwrite original clinical documents, or expose secrets.
- Use only the existing workspace and disposable `/tmp` evidence.
- Write only the single assigned report in the workspace.

Read these files only:
- `frontend/tests/worker_02_desktop_editor_isolated_qc.mjs`
- `frontend/tests/worker_02_evidence/test_results.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_source_preserving_qc/manifest.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_source_preserving_qc/render_compare_report.json`
- `tests/test_medical_writing_source_preserving_export.py`

Codex has corrected and executed the editor harness and the imported Word export path. RUX now preserves 141 pages and CMS-D001 195 pages; at 72dpi all pages are pixel-identical except the single page containing the isolated equal-length edit. Treat those files as current evidence, not the stale generic-export baseline.

Use at most one compact temporary script. Complete only these remaining actions:
1. Run the corrected editor harness once if current evidence is insufficient; distinguish script misuse from product failure.
2. Trigger one real direct product AI request against the isolated runtime using configured DeepSeek `deepseek-v4-pro`; record provider/model, HTTP/result state, latency, and candidate count without sensitive content. Test one candidate action or stale-revision rejection if reachable.
3. Verify one saved working-copy value survives page reload and isolated backend restart by API/database observation.
4. Write the required report. Explicitly list anything not completed as unverified; do not burn turns building another framework.

Write exactly one output file: `runs/execution/medical_writing_prelaunch_acceptance_20260717/cms_full_retest.md`. Use all required headings from the original assignment. Keep it under 4000 Chinese characters and include the session continuation evidence.
