You are continuing the same Hermes/Pi finite-code session. Codex reviewed the first
pass and found two in-scope acceptance gaps. Make one consolidated corrective pass;
do not re-open completed scope.

Hard boundaries:
- Work only in the current workspace (`.`).
- Edit only:
  - `services/api/app/monitoring_ai_service.py`
  - `tests/test_monitoring_ai_service.py`
- Do not edit the runner-owned report, other source/tests, runtime DBs, services,
  APIs, real projects, candidates, frontend or medical-writing files.
- Keep prompt v7, legacy v3-v6, packet v3 and repair v2 unchanged.
- Do not weaken existing fail-closed gates.
- Runner-managed output path: `runs/pi_monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801.md`. Never invoke a
  write/edit tool on this report path; return the complete follow-up report and let
  the runner persist it.

Read these files only:
- `context/monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801_context.md`
- `runs/codex-subagent_monitoring_p10_loop316_protocol_v6_visit_canary_20260801.md`
- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_service.py`

Writable paths:
- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_service.py`

Gap 1 — separate full topic boundary from operative family classification:

- The independent review and task context require two distinct field-aware views.
- The topic-boundary view must cover all user-visible candidate content:
  title/text; normalized subject scope, conditions, time windows, thresholds,
  exceptions and required actions; claim text, uncertainty and user_action.
- Run medication/first-dose, dispensing/PK, withdrawal, safety follow-up and AE/CM
  collection gates against that full view.
- The visit-family view must cover operative content only and must exclude claim
  uncertainty and user_action. Run the exactly-one-family classifier only on this
  operative view.
- Required tests:
  1. pure schedule candidate with first-dose/IP content only in uncertainty fails
     the medication boundary but does not gain another family;
  2. distributed AE/CM collection only in user_action fails the collection boundary;
  3. reschedule and unscheduled phrases only in uncertainty/user_action do not
     create extra families and otherwise pure schedule still passes.

Gap 2 — truly complete candidate-indexed repair diagnostics:

- The current flat `deferred_generic_errors` loses candidate identity and raises only
  its first item. Replace it with per-candidate ordered error accumulation.
- For protocol tasks, every safely collectable deterministic validation failure must
  be attached to `candidate N (title)`, including protocol-specific failures and
  generic candidate failures (missing claims/evidence, internal IDs, forbidden SDTM
  assertions, unknown evidence references, definitive approval language and
  provider-supplied evidence objects). Candidate type, provider repair lineage,
  structured payload validation, structural repair and evidence materialization
  failures must also be candidate-indexed; continue to later candidates when safe.
- Do not generate cascading/spurious errors after a prerequisite stage fails. Skip
  dependent checks for that candidate, continue collecting independent candidates,
  then raise one ordered response-level diagnostic before repair.
- Non-protocol task behavior must remain unchanged.
- Add a multi-candidate regression where distinct schema/structural/generic/topic
  failures are all present in the one repair payload with stable candidate
  index/title; add a terminal mixed-valid/invalid case proving zero partial
  persistence and exactly one repair.

Run:
- `.venv/bin/python -m py_compile services/api/app/monitoring_ai_service.py`
- `.venv/bin/python -m pytest -q tests/test_monitoring_ai_service.py`

Return:
- exact changes, tests/results and final SHA-256 for both writable files;
- any residual uncertainty;
- no final acceptance claim.
