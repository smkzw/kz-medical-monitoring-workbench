# Codex Review — P10 v12 visit-topic structured diagnostics

Date: 2026-08-01 22:22 CST  
Reviewer: Codex direct  
Scope: Phase A A1-A5 offline corrective only  
Verdict: **PASS for the offline gate; no authority granted for clone, zero-submit, provider call or canary**

## 1. Reviewed delta

- Protocol-clause prompt identity advanced from v11 to v12.
- v11 was added to the immutable retirement-audit set and remains outside
  status-compatible legacy versions.
- A visit-topic validation failure now carries deterministic structured
  diagnostics without replacing the bounded legacy validation text.
- The single controlled repair receives the exact candidate, user-visible
  field path, token, forbidden family and required full-field repair action.
- An invalid repair persists residual structured diagnostics and remains
  terminal `failed / invalid_ai_output / retryable=false`.
- Exact fixtures cover every governed user-visible surface, unchanged/partial
  repair, complete-field regeneration and frozen v11 history.

## 2. Source review

### 2.1 Identity and frozen history

- `services/api/app/monitoring_ai_service.py:99-104` selects
  `monitoring-protocol-clause-structuring-v12`.
- `services/api/app/monitoring_protocol_preparation_service.py:112-124`
  includes v11 in the retirement-audit set but does not make it
  status-compatible or reusable.
- `tests/test_monitoring_protocol_preparation.py:2272` proves a terminal v11
  failure keeps its status, attempt hashes, zero candidates and retry
  prohibition while the same business key creates a distinct v12 job.

### 2.2 Diagnostic contract

- `MonitoringAiOutputValidationError` stores an immutable copy of structured
  diagnostics (`monitoring_ai_service.py:796`).
- `_visit_boundary_surfaces` (`:3839`) enumerates the same complete
  user-visible boundary already used by validation: title, text,
  `subject_scope`, structured arrays and claim text/uncertainty/user_action.
- `_visit_boundary_diagnostics` (`:3893`) emits deterministic,
  duplicate-controlled entries with zero-based JSON `candidate_index`,
  one-based `candidate_number`, exact path/token/span, family, code and
  `regenerate_entire_user_visible_field`.
- Ordering is candidate order, configured family precedence, surface order and
  regex match order. Validation scope was not weakened and uncertainty remains
  in the boundary.

### 2.3 Repair and terminal failure behavior

- Initial validation diagnostics are injected only when available
  (`monitoring_ai_service.py:1961-1969`), so unrelated repair envelopes retain
  their prior shape.
- The repair contract (`:2843-2874`) requires complete affected-field
  regeneration and explicitly forbids token-only deletion, post-generation
  mutation and new facts/sources.
- A second invalid output stores residual diagnostics with both provider
  outputs and returns the existing non-retryable invalid-output path
  (`:2005-2024`).
- No provider output is edited after generation; no salvage, second repair or
  validator bypass was introduced.

## 3. Exact regression evidence

| Gate | Result |
|---|---|
| Python compilation, six governed files | PASS |
| Ruff semantic/static check, six governed files | PASS |
| New v12 focused cases | `5 passed` |
| `test_monitoring_ai_service.py` | `432 passed` |
| Preparation tests | `40 passed` |
| API + startup recovery | `20 passed, 17 warnings` |
| Core monitoring suite | `533 passed, 17 warnings in 16.83s` |
| Adjacent monitoring suite | `146 passed, 17 warnings in 5.23s` |
| Accepted full monitoring selector | `1494 passed, 4480 deselected, 27 warnings in 695.60s` |

The standard repository selector
`python3 -m pytest tests -q -k monitoring` is still blocked during collection
by the unrelated medical-writing test
`tests/test_medical_writing_dynamic_section_matrix.py`, which imports the
removed private symbol `_REQUIRED_CORE_BODY_SEMANTIC_IDS`. The accepted
monitoring run used the exact same selector with only that known unrelated
module ignored. No medical-writing file was changed.

`ruff format --check` reports that all six files follow the repository's
existing non-Ruff-format style and would be reformatted. It was intentionally
not applied because formatting churn is outside this corrective and includes
unchanged baseline files.

## 4. Findings

- P0: none.
- P1: none.
- P2: none.
- P3: none.
- P4: none within the reviewed offline delta.

The v12 deterministic contract closes the v11 loss of exact repair location
without relaxing a medical boundary. It does not prove that a live provider
will obey full-field regeneration; that is an A6 runtime-canary question.

## 5. Residual risk and authorization boundary

- A fresh provider output may still fail. The correct outcome is a precise,
  persisted, non-retryable fail-closed result with zero candidates.
- The legacy failure-message field may truncate a large diagnostic list;
  complete structured diagnostics remain in the attempt response payload.
- No fresh clone, zero-submit, runtime migration, POST, browser run, real
  project or commercial-release decision was performed.
- v9/v10/v11 remain frozen and must not be retried, reused, salvaged or
  reclassified.
- 8911 and 5174 were confirmed stopped at closure. PID 43191 on 18911 is
  unrelated and was not touched.

## 6. Final review decision

Phase A A1-A5 may be closed as an offline evidence gate. A6 remains unopened.
Only a later, explicit runtime authorization may permit a brand-new isolated
clone, zero-submit proof and at most one project/topic POST. That result must be
reviewed before Phase B implementation or any commercial-readiness claim.
