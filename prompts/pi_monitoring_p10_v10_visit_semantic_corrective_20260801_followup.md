Continue the same bounded v10 corrective session. Do not restart the task or
revisit already-green work. Codex accepts `tests/test_monitoring_ai_api.py` as
an authorized adjacent contract test, so the writable set is now exactly:

Hard boundaries:

- Work only inside the runner-provided workspace root (`.`).
- Do not access or modify runtime, provider configuration, databases, ports,
  browsers, real projects or production paths.
- Runner-managed output path:
  `runs/pi_monitoring_p10_v10_visit_semantic_corrective_20260801_followup.md`.
  Return the report and never write/edit that path directly.

Read these files only:

- `context/monitoring_p10_v10_visit_semantic_corrective_20260801_context.md`
- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_api.py`

Authorized writable paths:

- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_api.py`

No other product file may change. Do not start services, providers, ports,
browsers, runtime databases or real projects.

Codex found four concrete acceptance gaps in the completed pass:

1. The reference-complement exemption currently uses `family_has_action`,
   which includes unscheduled actions. A candidate containing only an
   unscheduled action plus an original-window reference currently returns only
   `unscheduled`. The exemption is authorized only for a real reschedule
   action (`_VISIT_RESCHEDULE_FAMILY_RE` or
   `_VISIT_RESCHEDULE_OBJECT_RE`), never unscheduled alone.
2. The exemption currently suppresses independently meaningful schedule terms
   inside the complement. Direct probes incorrectly return reschedule-only for:
   - `以第2周访视为参照`;
   - `以D15±3d访视为参照`;
   - `以访视顺序为参照`;
   - `以±3天访视窗口为参照`.
   Week/day, numeric-window and ordering assertions must remain schedule and
   therefore mixed with reschedule. Keep the exact nonnumeric
   `以试验流程表规定的时间窗为原始参照` false positive corrected.
3. The cleaned exact five-candidate replay is not source-faithful enough:
   - delete candidate 2's unsupported transition/scope inference unless a
     directly supporting evidence quote is added;
   - delete candidate 4's unsupported skin-lesion/treatment-context inference
     unless its real source evidence is added;
   - in cleaned candidate 3, remove the unsupported final
     `时间窗为原始参照` sentence, do not cite the drug-dispensing-adjacent
     duplicate for a repeated-context inference, and remove that duplicate
     inference. Keep only the source-faithful reschedule rule and exact
     `原始访视日` constraint.
4. Unsupported `补访` expansion must fail deterministically, not only by prompt.
   For `visit_window_and_order`, if the operative candidate uses the exact
   action term `补访`, at least one of its actually bound `used_ids` must carry
   direct source quote support for `补访` (or an explicitly justified narrow
   equivalent you document). The exact v9 repaired candidate 3 must therefore
   still fail after the family false positive is fixed because none of its
   bound quotes supports `补访`. Update synthetic valid fixtures that use
   `补访` so their evidence directly supports it; do not weaken the gate.

Add direct regressions for all four probe strings, the unscheduled-only case,
unsupported/supported `补访`, and the truly cleaned five-candidate bundle.
Correct the duplicated `trigger protection` docstring phrase. Run compilation,
focused visit tests, the full service test, protocol-preparation test, API
test, and the same adjacent suites. Return only the delta report: changed
paths, exact checks/results/hashes and residual risk. Do not claim canary or
release acceptance.
