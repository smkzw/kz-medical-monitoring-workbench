# D04 v2 medical/protocol semantic recheck — same session

Continue the same medical/protocol reviewer session `019ff258-f1a3-7000-a33b-5aa39344dc8e`. Do not restart the audit or open a new session. Your prior `REVISE` identified amendment-transition false certainty and two audience-token leaks; Codex reproduced them and froze a corrected snapshot.

## Hard boundaries

- Remain read-only inside workspace `.`.
- Runner-managed report path: `runs/conference/medical_monitoring_r4_d04_implementation_acceptance_20260812/general_pi_qwen38_recheck_v2.md`. Return the report; never write it through tools.
- Do not read worker, manager, engineering-reviewer, Grok/Cursor, or other participant reports.
- No real studies, services, R5, medical writing, security work, installs, or edits. Port 8911 must remain stopped.
- Review exact snapshot `context/medical_monitoring_r4_d04_implementation_snapshot_v2_20260812.md`, SHA-256 `ca8a55044d83f7f5af5b378d0ba1c938b9e6c100e9fad57d657182186fded4b7`. Verify every manifest hash before and after; any drift is `REVISE`.

## Targeted recheck

Inspect the corrective delta and enough adjacent code/tests to exclude regression:

1. `resolve_protocol_applicability` must assess transition scope before the one-feasible shortcut. Verify all five closed scopes: `all_switch`, `new_enrollment_only`, `existing_continue_old`, `next_visit_or_reconsent`, and `undetermined`.
2. Reproduce the prior A/B/C scenarios. Existing subjects must never be pushed to V2 under `existing_continue_old`; with one supported predecessor they stay on V1, otherwise one fail-closed applicability gate. Missing enrollment for `new_enrollment_only` and missing versioned trigger for next-visit/re-consent must produce one gate, zero candidate/risk/Query.
3. Confirm subject consent is not silently reinterpreted as re-consent and no earliest/AND/OR semantics are invented without a versioned trigger policy.
4. Verify generated audience payloads no longer leak raw `not_evaluable` or `AND/OR`, while internal enum names may remain in code/tests.
5. Confirm challenge 78 now maps to a resolver-driven test and relevant deterministic tests/goldens are honest.
6. Check the frozen contract remains unchanged and no D02/D03/D05 ownership or Query neutrality regression was introduced.

Run the smallest decisive focused/full checks needed. Do not repeat a broad unrelated audit when hashes outside the corrective delta are unchanged. Return a complete seven-section conference report and end with `## Verdict` containing exactly `ACCEPT` or `REVISE`. Any blocker must cite exact source/test evidence and the smallest owner-scoped repair. State clearly that this is D04 implementation recheck, not final clinical/regulatory or R5/UI acceptance.

