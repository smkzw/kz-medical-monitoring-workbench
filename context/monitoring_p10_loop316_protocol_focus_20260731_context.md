# Task Context: monitoring_p10_loop316_protocol_focus_20260731

Created: 2026-07-31 21:33:42
Objective: 在不放宽医学结构门、不做候选医学决定的前提下，为RUX P10方案准备实现结构证据聚焦与输出压缩，验证后受控恢复六个失败主题。
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `deepseek` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/monitoring_p10_loop316_v16_protocol_pause_20260731.md`
- `context/monitoring_p10_loop316_runtime_v15_20260731.md`
- `services/api/app/monitoring_ai_source_packet.py`
- `services/api/app/monitoring_protocol_preparation_service.py`
- `services/api/app/monitoring_ai_service.py`
- `tests/test_monitoring_ai_source_packet.py`
- `tests/test_monitoring_protocol_preparation.py`
- `tests/test_monitoring_ai_service.py`
- Current persisted RUX evidence is summarized below; the worker must not inspect or
  mutate runtime SQLite:
  - protocol version `protov_21c4b5a4a3883a8119d74e18`
  - 2 `candidate_review`, 6 `failed`, 10 proposed candidates, no medical decisions
  - failed packet sizes: visit 200, study treatment 200, safety 200, efficacy 95,
    early withdrawal/deviation 169, data quality 53
  - final failures: same-row binding, list-title binding, 60 evidence IDs over the
    50-ID candidate limit, and missing table headers
  - provider request audit size reached roughly 125k-409k characters because broad
    evidence and repair material were repeated
- Current filesystem and tests are authoritative. Do not use historical model output
  as acceptance evidence.

## Scope

- In scope:
  - Diagnose why the v2 structure gates fail after one controlled repair.
  - Implement the smallest project-neutral input-focus and repair-compression change
    that preserves complete table-row/header and list-title/item structural bundles.
  - Keep each candidate's `structured_payload.evidence_ids` at no more than 50 and
    make that budget explicit to the provider.
  - Add focused deterministic tests for bundle closure, bounded provider input,
    repair payload behavior, and unchanged fail-closed validation.
- Allowed writable paths:
  - `services/api/app/monitoring_ai_source_packet.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
  - `services/api/app/monitoring_ai_service.py`
  - `tests/test_monitoring_ai_source_packet.py`
  - `tests/test_monitoring_protocol_preparation.py`
  - `tests/test_monitoring_ai_service.py`
- Out of scope:
  - Runtime SQLite, provider settings, source documents, frontend, medical-writing
    files, product activation, candidate decisions, rule/fact adoption, service
    start/stop, real API retries, and full-suite execution.
  - Relaxing the v2 absence, table, list, evidence-count, CM/IP, conflict, or
    eligibility/estimand gates.

## Success Criteria

- The provider receives a materially smaller, deterministic, auditable evidence view
  built from the frozen authoritative payload.
- Selection never leaves a selected table row without its available header and
  same-row companion cells, or a selected list item without its title.
- Focus/compression does not silently assert full-document coverage and does not
  mutate the persisted input identity.
- Controlled repair carries actionable structure/evidence-budget constraints without
  duplicating unnecessary full invalid output.
- Focused tests pass and demonstrate the old gates remain fail-closed.
- Worker returns changed files, exact tests, observations, residual risk, and next
  recommended Codex verification. Codex independently reviews every edit.

## Risk Boundaries

- Write only the six allowed source/test paths listed above.
- Do not touch runtime databases, services, ports, product data, candidates, facts,
  rules, mappings, or medical decisions.
- Do not weaken any clinical boundary or structural validation.
- Do not change the existing RUX jobs or retry them.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-31 21:33:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-31 21:36 CST: Codex confirmed the six failures are structural packet/output
  failures, not a reason to loosen medical gates; bounded implementation authorized
  only in the listed source and test files.
