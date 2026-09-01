# Same-session independent verifier follow-up — D08 remediation

Resume your verifier session. Read the worker remediation report `runs/pi_medical_monitoring_r4_d08_runtime_followup2_20260814.md`, then re-read and independently test the **current** D08 snapshot. Do not modify files. Reproduce every prior P0-P2 probe and assess whether it is fixed rather than trusting new tests.

Current hashes:
- contracts `2c5baa0a8a31d480ce142b464c35cfdbc913e4bfb06061c22d9c37e041529c7a`
- evaluator `253ba32d3e07dcea61142cb7b052f055241e6632459cd2382dcb9fe956e7fe31`
- projection `5af0bb5af7ba12331c7d2f4ade96a239a4b0a4ee5a289227efa8e4f10d59785d`
- init `70a7f42c1e8fd268a346d396d86f6f10cb07810852864d2848a42b96413afd3b`
- adapter `e5f430a3ba798bf2f5cac9ba129d7980f323692122e9e84d4e26bcaa312f01e7`
- replay `639ef4d0cbadd4898b1ad9959cc2e709665dd26453bdda069be7897d0f6ddc80`
- runtime contract `21683deeeb4c00eb81a16ab8c9d6189347b647baa025682e1074bbb48e3e2771d`
- verifier probes `b567a99a4a1e2b022baa294e81fe4ff20a0c9e0868e3bf164f48cda022a8a6f5`

Codex reproduced from workbench root: D08 171 passed, full R4 3828 passed, R1-R3 1264 passed, Ruff/compile pass. Reproduce decisive checks available to you and pin hashes start/end.

Pay special attention to the reported four oracle-pinned semantics. Decide from contract meaning, not worker convenience:
- required-producer coverage gaps may be represented as a pre-evaluation `not_evaluable` unit if they block before medical relation evaluation and emit no risk/query/journey; they need not necessarily use the `integrity_error` object if the contract/oracle intentionally models the blocked expected unit.
- multi-subject nodes are legitimate inputs for the identity-collision family; do not incorrectly reject the very cross-subject comparison being evaluated. A scope mismatch outside that family must fail closed.
- rule-window exclusion may be `not_applicable` if rule applicability is deterministically established before relation evaluation.
- raw/materialized resolve-admission may yield a typed not-evaluable/positive relation unit only when a structured obligation and closed resolution state prove it; missing data alone must not invent risk.

These clarifications do not waive ordering, zero audience/risk on integrity/coverage gaps, or any prior defect. If any prior probe still fails, any magic runtime sentinel remains, or exceptions are ID/prose/fixture coupled, verdict remains REVISE.

Return exact evidence, unresolved P0-P4 findings, start/end hashes, residual scope, and exactly one verdict token on its own line: `ACCEPT_D08_RUNTIME` or `REVISE_D08_RUNTIME`. Do not accept R4 overall/R5/UI/production/real endpoints.
