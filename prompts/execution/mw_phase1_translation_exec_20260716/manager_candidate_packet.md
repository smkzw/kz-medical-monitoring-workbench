You are Grok Build continuing the existing execution-manager session for task `mw_phase1_translation_exec_20260716`. Follow the workspace `AGENTS.md` and preserve all prior source-boundary rulings.

This is a bounded mechanical consolidation pass, not a new translation pass and not a conference.

Hard boundaries:
- Work only inside the current workspace supplied by the runner.
- Do not edit source, application, test, corpus, or production files.
- Do not create sibling process files.
- Do not browse or add external facts.
- Write exactly one output file: `runs/execution/mw_phase1_translation_exec_20260716/executor_candidate_packet.json`. The runner persists the final response there.

Read these files only:
- `records/active_slices/medical_writing_phase1_autoimmune_mnc_corpus_20260716/translations/translation_selection.json`
- `runs/execution/mw_phase1_translation_exec_20260716/normalized/worker_01.md`
- `runs/execution/mw_phase1_translation_exec_20260716/normalized/worker_02.md`
- `runs/execution/mw_phase1_translation_exec_20260716/normalized/worker_03.md`
- `runs/execution/mw_phase1_translation_exec_20260716/normalized/worker_04.md`

Output exactly one raw JSON object and no prose, comments, Markdown fence, or trailing text. The runner will persist the final response to:
`runs/execution/mw_phase1_translation_exec_20260716/executor_candidate_packet.json`

Required schema:
{
  "schema_version": "phase1_executor_candidate_packet_v1",
  "task_id": "mw_phase1_translation_exec_20260716",
  "executor": {
    "agent": "hermes",
    "provider": "aishuo",
    "model": "MiniMax-M3",
    "role": "translation_and_humanizer_candidate_generator"
  },
  "records": [
    {
      "segment_id": "exact current segment id",
      "source_text_sha256": "exact current source hash",
      "source_locator": "exact current source locator",
      "selection_status": "translation_pending or hold_translation_pending",
      "corpus_tier": "exact current corpus tier",
      "literal_candidate": "full literal Chinese candidate copied exactly from normalized worker report",
      "humanizer_candidate": "full regulatory-Chinese candidate copied exactly from normalized worker report",
      "source_report": "runs/execution/mw_phase1_translation_exec_20260716/normalized/worker_0x.md",
      "candidate_status": "executor_draft_untrusted_pending_independent_finalization"
    }
  ]
}

Contract:
1. Produce exactly 12 records: worker_01 two, worker_02 two, worker_03 two, worker_04 six.
2. Copy Chinese candidates exactly; do not revise, summarize, normalize punctuation, or silently repair them.
3. Verify every id/hash/locator/status/tier against the current selection JSON.
4. Reject the superseded ids `phase1_nct02352493_sirna_sad_mad_escalation` and `phase1_nct02352493_sirna_patient_transition` if encountered.
5. The five current NCT02352493 records must remain `hold_translation_pending` and `phase1_2_boundary_exception`.
6. Do not include English source text, ledgers, commentary, approval recommendations, or model judgments.
7. If any candidate cannot be extracted unambiguously and in full, emit a valid JSON object with `records: []` plus top-level `error` naming the exact segment and ambiguity; do not guess.
8. Do not use file-write/edit tools. Return the raw JSON in the final response; the runner owns persistence.
