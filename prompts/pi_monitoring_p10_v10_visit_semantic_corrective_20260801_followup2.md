Continue the same bounded v10 corrective session for the second and final
completion pass. Do not restart or revisit already-green work.

Hard boundaries:

- Work only inside the runner-provided workspace root (`.`).
- Do not access or modify runtime, provider configuration, databases, ports,
  browsers, real projects or production paths.
- Runner-managed output path:
  `runs/pi_monitoring_p10_v10_visit_semantic_corrective_20260801_followup2.md`.
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

Luna independently confirmed four remaining blockers. Close exactly these:

1. Reference-complement must remain fail-closed for common Chinese numeric,
   week/day and ordering forms. The following all currently or plausibly
   over-exempt and must classify `reschedule + schedule`, then fail the
   exactly-one-family gate:
   - `以第十二周的计划访视为参照`;
   - `以D15的访视计划为参照`;
   - `以72小时的访视窗口为参照`;
   - `以3个工作日的访视窗口为参照`;
   - `以原定访视先后次序和访视安排为参照`;
   - independent `须遵循原定访视先后顺序`.
   Prefer a readable independent-reference assertion regex over further
   brittle negative lookarounds. Cover Arabic and common Chinese week numbers,
   D-day forms with or without ±, numeric hours/calendar days/working days/
   weeks/months, and visit order/sequence synonyms. Preserve the exact
   nonnumeric `以试验流程表规定的时间窗为原始参照` reschedule-only fix.
2. The study-completion/end boundary must not reject a true visit schedule
   merely because study end is its visit name or temporal anchor. These must
   remain schedule and pass:
   - `末次访视应在研究结束前7天内完成`;
   - `研究结束访视应于第24周完成`;
   - `试验结束访视应在D169±7d完成`;
   - `研究结束时应完成末次访视`.
   Continue to reject actual determinations such as
   `视为该例受试者完成试验`, `视为整个试验结束`, standalone study
   start/end determinations, and the original v9 candidate 5. Use semantic
   suffix/role guards rather than disabling the boundary.
3. Conflict-only evidence cannot authorize affirmative `补访`. Derive the
   direct-support ID set by excluding every
   `normalized.source_conflicts[*].evidence_ids` from support, even if those
   IDs were structurally expanded into `normalized.evidence_ids`. The exact
   term may pass only when a bound non-conflict evidence quote directly
   contains `补访`. Add a deterministic end-to-end regression in which the
   only quote containing `补访` is conflict-only and the affirmative candidate
   fails; also keep a non-conflict supported case green.
4. In the cleaned five-candidate replay, candidate 2 still asserts
   `开放治疗期/进入开放治疗期` in title, text, subject_scope and conditions,
   while its replay packet has no direct evidence for that scope. For
   `cleaned=True`, remove that phase premise from every user-visible and
   structured field, or bind an actual direct heading/source quote. Add
   assertions over title, text, subject_scope, conditions and claims, not only
   claim count. Do not alter the exact original replay fixture.

Run compilation, focused new regressions, full service, protocol-preparation,
API and the same adjacent suites. Return only a delta report with exact changed
paths, commands/results, hashes and residual risk. This is the final recovery
pass; do not claim canary, runtime or release acceptance.
