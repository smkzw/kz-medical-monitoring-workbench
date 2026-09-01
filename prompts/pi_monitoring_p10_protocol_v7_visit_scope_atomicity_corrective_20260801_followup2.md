Continue the same Hermes/Pi session for the second and final consolidated recovery
pass. Codex and the independent Luna reviewer confirmed that the architecture from
the prior pass should be retained, but common protocol Chinese still bypasses or
false-triggers the visit gates. Correct the validator/tests only; do not broaden the
product slice.

Hard boundaries:
- Work only in the current workspace (`.`).
- Edit only:
  - `services/api/app/monitoring_ai_service.py`
  - `tests/test_monitoring_ai_service.py`
  - `tests/test_monitoring_protocol_preparation.py`
- Do not change prompt identity/instructions, preparation service, packet v3,
  structural repair v2, runtime DBs, services/APIs, real projects, candidates,
  frontend or medical-writing files.
- Do not edit the runner report with tools.
- Runner-managed output path: `runs/pi_monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801.md`. Return the full
  follow-up report for the runner.

Read these files only:
- `context/monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801_context.md`
- `runs/codex-subagent_monitoring_p10_loop316_protocol_v6_visit_canary_20260801.md`
- `services/api/app/monitoring_ai_service.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`

Writable paths:
- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_service.py`
- `tests/test_monitoring_protocol_preparation.py`

Confirmed failing current-state probes:
- misses medication: `访视当天完成第一次应用研究药物`,
  `访视当天完成第一次用药`, `访视当天首次应用研究药物`,
  `受试者在研究中心使用新药盒中的研究药物`,
  `开始合并用药`, `新增合并用药`;
- false medication: `研究药物给药前7天内完成计划访视`,
  `首次给药之前7天内完成计划访视`, `首次给药的前7天内完成计划访视`,
  `接受研究药物后7天完成计划访视`;
- misses withdrawal: `受试者退出本研究`, `终止参与研究`,
  `撤回其知情同意`, `被判定为脱落`;
- false withdrawal: `退出研究中心后回家`, `终止研究药物`;
- misses collection: `AE和合并用药均应予以记录`,
  `不良事件及伴随用药应进行收集`, long verb-first wording;
- false collection: `记录CMV检测结果`;
- family defects: `计划外的访视安排` is unscheduled, not schedule;
  `访视延期三天` and `调整访视日期` are reschedule;
  `第2周访视` and `D15±3d访视` are schedule.

Required implementation:
1. Preserve the two-view design and error precedence.
2. Make medication recognition cover first/initial dose and IP/CM administration
   in both action-object orders, with bounded intervening words. Deterministically
   exclude ordinary relative timing anchors, including object-prefixed forms and
   `前/后/之前/之后/的前/的后`; do not suppress the actual directive
   `访视当天首次给药`.
3. Cover inserted-word withdrawal/consent/lost-follow-up forms while excluding
   research-center and study-drug phrases from withdrawal classification.
4. Cover verb-first and object-first AE/CM/伴随用药 collection with a practical
   bounded distance. Treat English AE/CM as standalone tokens; `CMV` must not match.
5. Normalize optional `的` unscheduled phrases and add ordinary reschedule and
   week/day visit schedule forms without making unscheduled text count as schedule.
6. Keep error messages stable unless a precise distinction is required.

Required tests:
- Every confirmed probe above with the stated positive/negative result.
- Timing controls plus actual directive controls in the same parameterized group.
- Error precedence combinations:
  medication→PK→withdrawal, PK→withdrawal, withdrawal→safety,
  safety→collection.
- Exact v6 repaired-shape phrases for C1-C5 from the independent review, including
  `第一次应用研究药物`; C3-shaped structural closure must prove 8 selected IDs
  expand deterministically to 15 before topic failure.
- Candidate diagnostic marker positions strictly increase and each extracted block
  ends at the next marker; include structural-repair and evidence-materialization
  blockers in the mixed-class fixture.
- Decisive cutover integration: create same-business-key queued and failed v6 jobs,
  call protocol preparation `start()`, prove a distinct v7 job is created, the v6
  attempt counts do not increase, and no v6 job is claimed/retried/reused. Preserve
  terminal-history visibility semantics.

Run:
- `.venv/bin/python -m py_compile services/api/app/monitoring_ai_service.py`
- `.venv/bin/python -m pytest -q tests/test_monitoring_ai_service.py tests/test_monitoring_protocol_preparation.py`

Return exact changes, results, final three hashes, residual uncertainty and no final
acceptance claim.
