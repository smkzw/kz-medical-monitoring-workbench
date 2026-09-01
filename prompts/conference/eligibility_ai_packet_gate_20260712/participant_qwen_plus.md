You are Hermes in a Codex-chaired conference. Fully read and comply with `/Users/smkzw/.hermes/SOUL.md` and state honestly that you did so.

Role: independent participant. Assigned route: `opencode-go/qwen3.7-plus`.

Hard boundaries:
- Read only the listed files; no edits, tests, web, browser, images, original clinical folders, or production writes.
- Write exactly one output file: `runs/conference/eligibility_ai_packet_gate_20260712/participant_qwen_plus.md`.
- Do not read other participant outputs.

Read these files only:
- `context/eligibility_ai_packet_gate_20260712_conference_context.md`
- `plans/codex_main_venue_eligibility_ai_packet_gate_20260712.md`
- `services/api/app/eligibility_ai_packet.py`
- `services/api/app/eligibility_ai_review.py`
- `services/api/app/eligibility.py`
- `services/api/app/ai_gateway.py`
- `services/api/app/ai_execution_policy.py`
- `services/api/app/ai_task_runner.py`
- `services/api/app/sqlite_runtime_store.py`
- `tests/test_eligibility_ai_packet.py`
- `tests/test_eligibility_ai_review.py`
- `tests/test_eligibility_ai_contract.py`
- `tests/test_eligibility_review_api.py`
- `tests/test_eligibility_review_workflow.py`
- `records/active_slices/eligibility_next_slice_20260711/six_subject_matrix_v1.json`

Independently audit the bounded implementation. Prioritize reproducible P0/P1 defects: caller-controlled content reaching the model, stale/version race, artifact-to-span mismatch, QC completeness semantics, packet digest/echo omissions, provider retry and batch idempotency, public API identity spoofing, sensitive-path/body leakage, transaction partial writes and cross-project isolation. Treat unimplemented auth/archive/DOC extraction as closed production gates unless they create a new bypass.

Output sections: Boundary Check; Evidence Reviewed; Findings By Severity; Closed Gates Versus Defects; Required Verification; Recommendation. Separate evidence, inference, recommendation and uncertainty.
