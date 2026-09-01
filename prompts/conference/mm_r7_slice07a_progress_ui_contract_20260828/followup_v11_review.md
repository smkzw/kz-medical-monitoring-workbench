Delegated mode. Continue the same bounded Kimi Code conference session.

Read only `reviews/medical_monitoring_r7_slice_07a_progress_ui_contract_v1_20260828.md` v1.1 and the source files already used in round 1 when needed.

Confirm whether round-1 P0-P3 findings are incorporated. Focus on these Codex decisions:

- Do not modify the authorization model in this slice. A medical monitor is accepted only for progress viewing; the existing runtime administrator is separately accepted for start/stop/resume actions. Do not confuse the two identities.
- Prepare and work-unit construction belong to the upstream workflow or the synthetic acceptance fixture.
- The run identity comes from R5 route `run_ref`.
- The public progress payload will add stable `run_state`.

Return only remaining implementation-blocking P0/P1 issues, directly fixable wording defects, and a final `PASS` or `REVISE` conclusion. Do not edit files, start services or browsers, or run projects.
