You are the same independent Luna verifier that issued
`REOPEN_D09_ARTIFACTS`. Review the corrected CURRENT SNAPSHOT in a fresh
verification pass. Do not modify files. Codex remains final authority.

Read:

- `reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md`
- `context/medical_monitoring_r4_d09_runtime_worker01_overfit_correction_20260815.md`
- `runs/review/medical_monitoring_r4_d09_artifact_freeze_luna_followup2_20260815.md`
- `runs/execution/medical_monitoring_r4_d09_runtime_20260815/worker_01_followup2.md`
- the seven corrected D09 artifact/generator/test files
- the four corrected D09 runtime/test files

Candidate SHA-256 snapshot:

- catalog generator `0a6e27a528342ab10bbf6a597e5307574fb023347f7fa5246a203a5f8848ab95`
- oracle generator `a3923f5a5526d89421fc9b7efb23bcabc60824807f471479d3a055e813c50580`
- catalog `03b934ed5f4f1f9215ed652cf404c196fc723b48bfc99ce73cfccb14896a8548`
- quota `7ebc304bbc6e23c9c2fe0f634a2b56934dcf1321a4ab81d3461840ade3a678a0`
- registry `9efdb9b5ee5b56a4eb7f87ff1016fc414a46007373178018050427dacf3203a8`
- oracle `045990cfa9d0286e5b8c007d5c942faff0489a8afb06d09158c0f4733cb0c86a`
- artifact tests `e9ba9bef22fbd482570c3cf9306cb0dd446ac4664b82f7476d51af4f08edad9f`
- runtime contracts `0192ba75227cc81243b7d4bdff7a9e36b571749c5de186ace01aac44e2a8576a`
- runtime evaluator `1801df7e22e305c687667da732ff068d69d2e0289862c97e7c9331077fd02b11`
- adapter tests `e48719222866ae823349f9b12e72f749c82cecfec9d9191c637d72c942215b00`
- runtime tests `d6c36933a8f889910fcf199995301153f5dfb0932e2fbbd7f1d499afc193d7ff`
- contract must remain `9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40`

Independently reproduce the decisive tests and inspect source, not just the
worker report. Verify:

1. 179/179 cases and 537/537 expected/trace/source leaf dictionaries match
   with zero exceptions/skips/xfails/pinned-gap allowances.
2. Oracle semantic derivation and clean runtime do not decide from mutation
   metadata, fixture/case IDs, prose, display labels, sentinel spellings or
   synthetic hash recipes; adapter does not translate those into facts.
3. The new explicit authority/method/lineage/Query/source-resolution facts are
   complete, closed, internally consistent and actually drive behavior.
4. Contract §3.2 and §12 numerical authority is honored. In particular inspect
   whether `QueryRedundancyDecision.max_query_member_fanout=100` as a dataclass
   default violates “runtime must not provide default fanout”, and whether the
   hard-coded gap threshold `expected_opportunity_count <= 4` and trend
   threshold `len(subjects) < 3` violate the requirement that numerical and
   clinical thresholds come from versioned ModeContract/definition facts.
5. Repeated-risk minimum authority missing/illegal states fail closed instead
   of silently falling back to 2; Query member-set/proof hashes and producer
   verification records cannot be inconsistent while still accepted.
6. Artifact/runtime/D08 adjacency tests, deterministic generator checks,
   static scans, contract SHA stability and TCP 8911 stopped.

Return exactly one verdict token followed by concise evidence:

- `ACCEPT_D09_CORRECTED_FREEZE` only if runtime-ready fact completeness and
  clean parity are both proven; or
- `REVISE_D09_CORRECTED_FREEZE` with the smallest exact repair list and affected
  files/tests.

Do not accept merely because the current self-tests are green. Do not review
Worker02/03, UI, services, real projects, models, or medical-writing.
