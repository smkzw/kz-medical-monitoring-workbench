# Codex Review: monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801

Date: 2026-08-01
Delegated-agent output: `runs/pi_monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801.md`
Independent final review:
`runs/codex-subagent_monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801_final_recheck.md`

## Verdict

**PASS for the offline v7 corrective.** The next gate may be one bounded RUX v7
`visit_window_and_order` canary. This is not a release decision, does not authorize
MY009, and does not authorize candidate accept/reject/adopt/confirm/activate.

## Boundary Check

- Pi changed three authorized product/test paths. Its initial/recovery reports also
  disclose read-only inspection of `monitoring_ai_contracts.py`,
  `monitoring_ai_repository.py`, and `main.py` beyond the explicit read-only list.
  This is a process deviation, but no unauthorized product edit or runtime action
  was observed.
- The native Codex fallback changed only
  `services/api/app/monitoring_ai_service.py` and
  `tests/test_monitoring_ai_service.py`.
- The independent Luna recheck was read-only. No provider call, service start,
  runtime DB write, v6 retry/reuse, candidate decision, MY009 workflow, or
  medical-writing source change occurred.
- 8911 and 5174 were confirmed without listeners before and after verification.

## Codex Verification

- Final SHA-256:
  - `monitoring_ai_service.py`:
    `d62ff1162794f65cc8894d313d84c5c25c7d043641589608118146de5cb20aba`
  - `monitoring_protocol_preparation_service.py`:
    `1e43424adb7076fd6a7acf17e933833cde2f942dbd8778b5af03e47262ca1798`
  - `test_monitoring_ai_service.py`:
    `7e0fb132f2bfd081e1f860422d563fbdd9594aea3f833b29b61d7c16a2234cb5`
  - `test_monitoring_protocol_preparation.py`:
    `9ad21eb72141f58ced1ce265b98779a851af98b32ac859cdb68c8da59dc0ef1c`
  - `test_monitoring_ai_api.py`:
    `52691a1ec1f6a35cf4359bdea4aad41d50b1fd2f90f4ad80f48f6d35710768a2`
- `py_compile` for both implementation files: passed.
- Focused three-file suite: `336 passed in 9.51s`.
- Adjacent medical-writing suite: `200 passed in 2.44s`.
- Full monitoring suite: `1331 passed, 4299 deselected, 27 warnings,
  0 failed in 615.38s`.
- The broad selector includes offline tests that read frozen RUX/MY009 source
  shapes. It did not start a real-project workflow, create jobs/candidates, or call
  a provider; this distinction is preserved as a scope note rather than hidden.
- Direct in-memory phrase probes passed for all final medication, timing,
  withdrawal, collection, CMV, unscheduled and reschedule controls.

## Delegated-Agent Output Review

- The Hermes/Pi delegated route established the v7 prompt/cutover, two-view boundary/family architecture,
  complete candidate-indexed error aggregation, C1-C5 coverage, C3 8→15 closure,
  strict blocker order and one-repair atomicity.
- Two same-session Pi recovery rounds did not close all ordinary lexical cases.
  The declared fallback was therefore used once through a native Codex child for
  a two-file lexical corrective. No Pi re-dispatch or route invention occurred.
- The same Luna review session first returned REVISE, then verified the final
  fallback and returned PASS.
- The Pi report's final hashes and `297 passed` predate the native fallback and
  are superseded by Codex-observed hashes and final suites above.

## Residual Risk

- Known non-blocking adjacent forms remain: `研究者无法联系受试者`, subjectless or
  `未能联系受试者`, `临时的访视`, and `调整计划访视日期`.
- Standalone case-insensitive `AE/CM` is intentionally conservative and may match
  lowercase `cm` as a measurement unit in some contexts.
- These observations must be explicitly checked in the single canary. Any material
  misclassification reopens lexical hardening; it does not authorize broader
  execution.
- v6 remains terminal and must never be retried or reused. MY009 and the other real
  projects remain blocked. 8911 must remain stopped until the future canary is
  deliberately begun.
