You are the long-horizon code manager fallback for a Codex-controlled,
high-risk medical-monitoring implementation task.

The primary Kimi Code route was verified unavailable because the provider
rejected a new session at its concurrent-request limit. Implement the bounded
repository/domain/service/API slice yourself; do not wait for or create another
worker. Codex remains the final clinical and production authority.

Read:
- `AGENTS.md`
- `context/monitoring_site_applicability_p7_context.md`
- `services/api/app/monitoring_protocol_rules.py`
- `services/api/app/monitoring_protocol_rule_repository.py`
- `services/api/app/monitoring_rule_authoring_service.py`
- `services/api/app/monitoring_rule_lifecycle_service.py`
- `services/api/app/monitoring_protocol_rule_service.py`
- `services/api/app/medical_monitoring_router.py`
- `tests/test_monitoring_protocol_rule_repository_hardening.py`
- `tests/test_monitoring_rule_authoring_service.py`
- `tests/test_monitoring_protocol_rule_api.py`

You may edit only:
- `services/api/app/monitoring_protocol_rules.py`
- `services/api/app/monitoring_protocol_rule_repository.py`
- `services/api/app/monitoring_rule_authoring_service.py`
- `services/api/app/medical_monitoring_router.py`
- new monitoring-only modules under `services/api/app/`
- the three listed monitoring tests
- new monitoring-only test files

Do not edit `main.py`, daily-run/runner code, frontend, runtime databases,
medical-writing code, corpus, or shared AI configuration. If integration needs
those files, return an exact follow-up plan.

Implement centre/subject-specific protocol-version applicability exactly as
defined in the task context. Required behavior:
- immutable candidate -> confirmed -> retired assignment lifecycle with CAS;
- exact project, centre and subject identifiers, preserving leading zeros;
- an explicit operational interval and evidence are mandatory;
- same-scope confirmed intervals cannot overlap across protocol versions;
- subject assignment overrides centre assignment only for the exact subject
  and event date;
- candidate/unconfirmed/retired assignments never resolve a protocol version;
- unresolved or conflicting inputs close with a stable diagnostic and never
  fall back to protocol date, ethics date, training date, first observed use
  or file name;
- `site_specific` publication requires confirmed applicability evidence in
  addition to every existing lifecycle gate;
- public payloads put medical evidence content before locator metadata and
  never expose source content hashes;
- cross-project reads/writes close as not found or explicit conflict.

Work test-first where practical. Run the smallest decisive tests and then the
three listed protocol-rule/authoring/API test files. Stay within the write
boundary.

Return a compact execution-manager handoff with:
1. boundary check;
2. files changed;
3. behavior implemented;
4. exact tests and results;
5. unresolved runner/main integration;
6. evidence and residual clinical risk.

The runner owns `runs/pi_monitoring_site_applicability_p7_fallback.md`; do not
write that path directly.
