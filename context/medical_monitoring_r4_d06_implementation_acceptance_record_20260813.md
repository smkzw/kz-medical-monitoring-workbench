# R4-D06 Implementation Acceptance Record — 2026-08-13

Status: `ACCEPTED_SYNTHETIC_OFFLINE_D06_V1_18`

## Accepted scope

The frozen contract `FROZEN_R4_D06_CONTRACT_V1_18` (SHA-256
`460aba75857f72527453914b5ea5c205ecf8d5032ec5b83b22c6960ccbc8baeb`;
semantic SHA-256
`247eb0bc4a4c97428714f069639161ac832bed05cfcb7dfc4c01240a7ef84642`)
is accepted for the isolated synthetic/offline R4-D06 efficacy endpoint,
assessment, baseline, individual-trend, Query and renderer-neutral Patient
Journey slice.

This does not accept R4 overall, R5 UI, real projects or data, real models,
services, medical-writing, product, production, commercial use, or system
security design/testing.

## Frozen validation authority

| Artifact | SHA-256 |
|---|---|
| typed fixture catalog | `d4774a82e3d34dae28d6f25145f672cb62b28c506453d1bcc49ce0d60021a8e9` |
| expected outcome oracle | `772bca08198b7e6279915c22077f74e328f97d2563f95a0f49db1f9d4d63e26b` |
| challenge registry | `a02c4f8b7969e7b86673fc32903929f333adbf2f68fac401551056b23b7e0aba` |
| registry generator | `fea1ad5692d81aabb19419709fbd3f5b9c4b9a7efdef9f4280db9668383fc3f2` |

## Accepted implementation snapshot

| Artifact | SHA-256 |
|---|---|
| `src/mm_r4/efficacy.py` | `f4c9661de919018794d4cbe615664eb192bfac16d31a2e960ef9d5425fc69314` |
| `src/mm_r4/efficacy_evaluator.py` | `f9638957b95eabff9f654ccd5657d679e0044f169226228d4752daf782f821b0` |
| `src/mm_r4/efficacy_projection.py` | `12ef2eeec7159ed3b5d29966922894739c141df9ee8ebb61f9b33c53b8556da4` |
| `src/mm_r4/efficacy_fixtures.py` | `88d0f9a28d7eb1b3c58db89febc580574f9d70b5dd3624c4b662c08ea811e849` |
| `src/mm_r4/__init__.py` | `cb05b4020af85a9f78dcc9565bd0e6ccedff40036536a27f4d0ceedaf6acf129` |
| `README.md` | `01b82d608854409df4703ffb14f6c84659ff1ca927cd8eb5d895745a5213a2a8` |
| `tests/test_efficacy_contract.py` | `2633d695afc496da83062969b527351c90ec5c6d5b9ddd5137cb0535a3ce79fd` |
| `tests/test_efficacy_slice.py` | `1f4a15958ed02a4c3b28f0400c25090dc16d434c7db5dcd516f576839f323c80` |
| `tests/test_efficacy_projection.py` | `3b54c5a1698aa00746672ce0c34acd3c448f987b00e6fc9d3a12988dd9cba38b` |
| `tests/test_efficacy_challenge_matrix.py` | `518c8b258b7625ec3c2f6725cfcc8ffda9c6bef25a17a2cac72da421df28a78f` |
| `tests/test_efficacy_mutations.py` | `a7725f6f353445ff9ab2c84d5b92e8b4746aceb92582eaaaefe686ae71361aea` |

## Decisive acceptance evidence

- Raw runtime/oracle/DSL replay: `219/219`, deterministic, zero failures.
- Mutation suite: `119 passed`; focused D06: `912 passed`; full R4:
  `2239 passed`; adjacent R2/R3/R1: `598/339/327 passed`.
- Frozen authority audit: accepted inventory `876`, foreign keys `868`, D05
  references `868`, all with zero embedded-hash mismatches; runtime and catalog
  both expose `37` schema types with no missing or extra type.
- Hash-only mutation of accepted D05 inventory, D05 foreign key and D05 binding
  reference fails closed with `D06ContractViolationError` at
  `pre_medical_output_validation`.
- Generator, fatal Ruff, changed-file Ruff E/F, compilation/import/export and
  root identity checks passed; `706` exports resolve and the R2 lifecycle alias
  is preserved.
- Original independent verifier session
  `019ff7e2-f2ef-71a0-9c84-fa5e303cad24` returned `VERDICT: ACCEPT`, no P0-P4,
  in `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813_followup6.md`
  (SHA-256
  `b4381db0823df66d355528eb96403138ffe7d7e4d64078523262168ce5ec2045`).

## Bounded limitation

Opaque TTE/enrollment locator values and fully synchronized multi-object
rewrites cannot be validated against an authority that the frozen fixture does
not contain. The accepted boundary is non-empty typed linkage, bidirectional
cross-authority checks and content-addressed lineage. Exact locator-value
authority would require a controlled future contract/fixture erratum; no
hard-coded canonical strings or oracle lookups were introduced.

## Cleanup and runtime boundary

Task-created `__pycache__`, `.pytest_cache` and `.ruff_cache` directories under
R1-R4 were removed after verification. Port 8911 remains stopped. No real
project, product service or medical-writing path was used.

## Next safe action

Proceed in R4 sequence to D07 clinical safety/laboratory/examination reasoning:
first freeze its coverage, ownership, temporal/exposure linkage, grading,
counter-evidence, Query and Journey projection contract using synthetic/offline
fixtures; only then implement it. “Safety” here is the medical-monitoring
clinical domain, not system security engineering. Keep 8911 stopped and do not
run real projects or enter R5 UI before D07 acceptance.
