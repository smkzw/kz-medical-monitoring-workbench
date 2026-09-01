# Task Context: medical_monitoring_p9_rule_pack_identity_digest_exact_20260805

Created: 2026-08-05 10:40:27
Objective: Harden protocol-rule mapping identity factories and repository read-side checks so persisted rule-pack SHA-256 fields are exact lowercase 64-hex bytes, without changing rule revision or clinical execution semantics
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_rules.py`
- `services/api/app/monitoring_protocol_rule_repository.py`
- `tests/test_monitoring_protocol_rules.py`
- `tests/test_monitoring_rule_release_chain_p0_20260730.py`
- `context/medical_monitoring_p9_source_only_checkpoint_20260805.md`
- `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

The current filesystem and these contracts are authoritative for this bounded
source-only slice. The formal real-loop gate is still blocked; no runtime,
provider, browser or real project may be activated.

## Scope

- In scope: exact canonical validation for immutable rule-pack mapping digest
  fields at rule creation and repository read/lifecycle boundaries; focused
  negative tests and evidence records.
- Out of scope: protocol interpretation, provider/runtime activation, ports,
  browser/Playwright or API login, real-project data, clinical acceptance,
  database migration, and the medical-writing subsystem.

## Success Criteria

- `mapping_content_sha256`, `capability_manifest_sha256` and
  `effective_capabilities_sha256` are accepted only as exact lowercase 64-hex
  values wherever an immutable rule identity is complete.
- No trim/lower/string coercion can turn a malformed persisted rule identity
  into an accepted pack identity; legacy partial identity remains the existing
  explicit legacy path.
- Lifecycle and repository read-side checks fail closed with existing error
  classes/messages where possible; revision-token and clinical rule semantics
  stay unchanged.
- Focused rule-factory, repository and release-chain tests pass; formal runtime
  and browser evidence remain unverified under the gate.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This slice is performed directly by Codex; the route recorded by task
  initialization is not dispatched because no external model call is needed.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 10:40:27: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 10:41: re-anchored the P9 checkpoint, LOOP ledger and blocked
  gate; selected a narrow rule-pack identity boundary slice after the
  daily-run service hardening.
- 2026-08-05 10:47: changed rule-factory SHA-256 identity handling to exact
  lowercase raw bytes and hardened repository pack uniformity checks; added
  padded/uppercase/non-string factory regressions and a persisted DB-tamper
  read-side regression.
- 2026-08-05 10:49: focused rule/factory/repository suite passed **53 tests**;
  protocol API/lifecycle/review/cross-project adjacency passed **57 tests**;
  daily-run/record-resolver/repository adjacency passed **96 tests and 41
  subtests**; compileall and source contract scans passed. The real MY008
  fixture collection remains blocked by the environment's missing
  `cryptography` dependency; no dependency was installed.
