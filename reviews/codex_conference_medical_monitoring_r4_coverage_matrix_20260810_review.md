# Codex Conference Review: medical_monitoring_r4_coverage_matrix_20260810

Date: 2026-08-10

## Verdict

`PASS — FROZEN_R4_CONTRACT_V1`

The R4 all-domain coverage matrix and common risk contract may be used as the implementation contract for the isolated AE/MH first slice. This accepts the contract text only; it is not code, product, real-project, clinical-readiness or R5 UI acceptance.

Frozen artifact:

- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`
- SHA-256: `6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705`

## Boundary Compliance

- The Codex x Hermes workflow guard initialized and recorded the conference; the effective participant routes were Pi and native Grok Build, with no undeclared Hermes model substitution.
- Review and corrections stayed in the R4 contract/conference records.
- No product/runtime, medical-writing, real-project or frozen R1-R3 source was edited.
- No real medical project or product AI provider was run.
- Port 8911 had no listener at final freeze check.
- The task did not design or test system security.

## Participant Outputs Reviewed

| Role | Effective route | Session | Review path | Final result |
|---|---|---|---|---|
| `general_pi_qwen38` | `pi/cms-smk/cms-model:high` under Beijing daytime substitution | `019feba4-c0ba-7000-8acb-022ab80e1b51` | `runs/conference/medical_monitoring_r4_coverage_matrix_20260810/general_pi_qwen38.md` | `ACCEPT`; no P0-P2; identified fixed-window, seriousness/severity and lifecycle wording gaps |
| `general_grok45` | `grok-build/grok-4.5` | `b78ae951-5e3d-4eb4-859d-427ce21d5d66` | `runs/conference/medical_monitoring_r4_coverage_matrix_20260810/general_grok45.md` | Initial engineering `VETO`; same-session delta review after correction: `ACCEPT`, all prior P1-P3 resolved |

The two roles were independent. Grok did not read the Pi output. Codex, not either participant, performed final acceptance.

## Conference Panel Review

Pi confirmed the medical/domain shape and required a protocol/version-driven AE/MH match strategy, strict separation of event intensity from seriousness and monitoring priority, and an explicit R2 lifecycle projection.

Grok found the decisive contract defect: the draft mixed execution coverage, medical disposition, evidence polarity and risk lifecycle. It also found an undefined denominator identity, overloaded `not_evaluable`, dual R1/R2 lifecycle authority, incomplete numeric joins, partial-date ambiguity and insufficient domain-grain authority rules. Codex accepted these findings because each could produce non-deterministic tests or false clean coverage.

After the patch, the same Grok session marked F-P1-01 through F-P4 `RESOLVED` and returned `VERDICT: ACCEPT`. Its remaining P4 wording suggestions were applied before freeze:

1. §3.1 now qualifies L0 versus L1 `not_evaluable` outcomes.
2. §3.2 explicitly allows L1b counterevidence with L1 negative, positive or boundary.
3. D01 names `reported_ae/reported_mh` semantic-role data rather than a fixed “AE/MH table”.

## Main-Venue Codex Review

Codex independently pinned the contract to four layers:

- L0: frozen R1 execution/input coverage only;
- L1: one exclusive medical evaluation disposition per versioned EvaluationUnit;
- L1b: multi-valued evidence polarity;
- L3: frozen R2 as the sole risk lifecycle authority.

It also froze the EvaluationUnit identity/hash, exact denominator equation, object-join invariants, partial-date precision rule, domain authority matrix, R2 close mapping, high-risk close gate, D01 semantic roles and versioned matching strategy, D09 denominator gate, and the R4-only projection boundary.

Evidence authority used for the decision:

| Evidence | Authority | Directness | Decision use |
|---|---:|---:|---|
| Approved Design v1.1 / R4 plan / frozen R1-R3 contracts | 5/5 | 5/5 | Project contract and implementability |
| ICH E2A, ICH E6(R3), CDISC SDTMIG, NMPA guidance, NCI CTCAE | 5/5 | 4/5 | Medical boundary, traceability and risk-method anchors |
| Participant reports | 2/5 | 4/5 | Independent challenge only; not source authority |

## Codex Independent Verification

- Both final reports contain exactly `VERDICT: ACCEPT`.
- Text search found no remaining draft status, old domain-table `counterevidence` row, bare `not evaluable` row, old coexistence phrase or fixed “AE/MH 表” wording.
- The frozen artifact digest was computed after the final editorial corrections.
- `lsof -nP -iTCP:8911 -sTCP:LISTEN` returned no listener.
- No code test or browser check was applicable to this design-contract freeze. Implementation tests are required in the next R4 slice.

## Final Decision

Freeze the matrix as `FROZEN_R4_CONTRACT_V1` and proceed to a new isolated `poc/medical_monitoring_ai_native_r4` package. The first implementation must remain synthetic/offline and prove the four-layer state model, EvaluationUnit joins, AE/MH reconciliation, R2 lifecycle projection, Query draft and audience projection payload before any later R5 UI work.
