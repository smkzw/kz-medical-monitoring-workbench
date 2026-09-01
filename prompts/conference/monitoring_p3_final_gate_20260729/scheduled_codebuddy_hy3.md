You are CodeBuddy CLI / hy3 acting as an independent read-only reviewer in a
Codex-chaired conference.

This pass replaces the forbidden 00:00-08:30 Beijing-time aishuo route. Do not
edit any file. Work only in the current workbench.

Hard boundaries:
- Read these files only:
  - `AGENTS.md`
  - `context/monitoring_p3_final_gate_20260729_conference_context.md`
  - `services/api/app/monitoring_protocol_rules.py`
  - `services/api/app/monitoring_protocol_rule_repository.py`
  - `services/api/app/monitoring_protocol_rule_service.py`
  - `services/api/app/monitoring_rule_lifecycle_service.py`
  - `services/api/app/monitoring_rule_templates.py`
  - `tests/test_monitoring_rule_lifecycle.py`
  - `tests/test_monitoring_real_listing_shadow_cases.py`
  - `tests/test_monitoring_protocol_rules.py`
  - `tests/test_monitoring_protocol_rule_repository_hardening.py`
  - `tests/test_monitoring_rule_evaluation_fail_closed.py`
- Do not edit source, tests, records, data, or configuration.
- Do not write the runner-managed output file
  `runs/conference/monitoring_p3_final_gate_20260729/scheduled_codebuddy_hy3.md`;
  return the report and let the runner persist it.

Review only these P3 attack surfaces:

1. `RuleGoldStandardCase` immutable binding to exact rule revision, source entry,
   source content SHA-256, source revision and batch revision; `case_id` coverage;
   non-empty evidence locators that bind the same source hash.
2. Repository storage validates exact project/rule_key/rule_revision; strict
   shadow validation accepts only exact pack revisions; default cases are
   revision-filtered.
3. The complete case-set hash covers rule/source/input/related/expected/locators,
   is persisted, checked at confirm, and rechecked before publish. Added/replaced
   cases after confirm must fail closed; legacy hashless runs cannot publish.
4. Core canonical field-lineage validation is called at strict draft storage and
   publish integrity. Used predicate/evidence fields must be raw listing fields
   with stable header locators or auditable deterministic base values with raw
   inputs, expression, unit, locator. Conclusions/model/review fields are banned.
   CM and investigational-product domains remain mutually exclusive.
5. lifecycle_version=0 remains historically readable but can never be returned by
   current production selection.
6. Negative tests actually exercise the bypasses rather than only constructor
   validation.
7. RUX/MY009 real listing cases remain exact-source bound and AE-03 remains
   indeterminate and outside gold cases.

Try direct-dataclass forging, direct repository calls, post-confirm mutation,
SQLite migration defaults, source locator/hash mismatch, legacy rows, empty or
syntactically plausible but noncanonical lineage, and transaction ordering.

Return:
- P0/P1 findings only, each with file:line, reproduction and minimal repair; or
- explicit PASS with attack surfaces checked and residual risk.
Do not summarize unrelated architecture. Do not write the runner output path.
