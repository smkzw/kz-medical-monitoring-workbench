Continue the same independent Luna verifier session after your
`REVISE_D09_CORRECTED_FREEZE`. Perform a read-only re-freeze review of the
CURRENT SNAPSHOT. Do not modify files. Codex remains final authority.

Read first:

- `runs/review/medical_monitoring_r4_d09_artifact_freeze_luna_followup3_20260816.md`
- `context/medical_monitoring_r4_d09_fact_completeness_correction_20260816.md`
- `reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md`
- the seven D09 artifact/generator/test files and four D09 runtime/test files.

Candidate SHA-256 snapshot:

- contract `9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40`
- catalog generator `4a257242c83cafe212c2a6749236f894da569c83c173934f77f894e24e8f1702`
- oracle generator `19a73474174bbe7ff3d887fbda13c8ac86707c5ebb5de0d6ab51e8e1a738ee5e`
- catalog `93a737989eb05d75cb15ca09860949890013059663c601868b2f2a93c5c710eb`
- quota `4b80f36a4904e0beb0f7f14b428db010109de4d3bd71becdc367996e9085b50a`
- registry `b697c43199047a15ed5666f55ef1b1d99762c34b3925c9e36815497ebd92f179`
- oracle `045990cfa9d0286e5b8c007d5c942faff0489a8afb06d09158c0f4733cb0c86a`
- artifact tests `170418760176906c3f6e01d9a9dd5ceb3f7ef880673a0c5472c16e843cf1e78f`
- runtime contracts `42fdda3b36e08e77810847f8dcea4cd13572c3d1a6f08eaea80a7eca0c14765f`
- runtime evaluator `0b4aa08a51b84d0020133313ad30a886bcebdde67846d0efc639852e90c06743`
- adapter tests `9788183fd0193e60f9b69283078f2784c7961c3b0e37bf6baddc50ece7c9f6b4`
- runtime tests `d38b50ff76f1efcb409417aadcddf7ad678b9a22acc70ee2eebd3d84bcd9984c`
- normalized stage-A generator pin
  `ea5e56a9b5996003122149b7d12317e13a7ce16246c3090a2757cf89b42aee23`

Reproduce the decisive checks and independently probe your exact prior
blockers:

1. D09 artifact 99 tests; D09 runtime/adapter 71 tests + 3 subtests; 179/179
   cases and 537/537 expected/trace/source leaf sets; D08 artifact 54 + 10
   subtests and D08 runtime 186; both generator checks; Ruff/compile; TCP 8911
   stopped.
2. Confirm no runtime/oracle fallback or hard-coded semantic thresholds remain.
   Repeated-risk minimum, gap positive minimum and trend positive minimum must
   come from versioned/hash-bound ModeContract authority and fail closed when
   missing/illegal.
3. Confirm `max_query_member_fanout` has no runtime dataclass default and equals
   a hash-bound `CenterQueryPolicy` value.
4. Tamper unit-member hash, covered/uncovered partition, member-query refs,
   coverage proof, policy fanout/content hash and call public `evaluate()`
   directly. Every inconsistent input must fail before output; fully covered
   cases must carry real member Query refs.
5. Probe empty/duplicate/wrong source revision records, declared/top-level hash
   mismatch, verified unequal hashes and mismatch equal hashes. Every one must
   fail; valid mismatch state may yield the intended not-evaluable result.
6. Confirm runtime/oracle decisions remain independent of mutation metadata,
   case/fixture IDs, prose/display labels, sentinel spelling and synthetic hash
   recipes; adapter does not translate them.
7. Confirm current files do not drift during review and the contract SHA is
   unchanged.

Return exactly one verdict token followed by concise evidence:

- `ACCEPT_D09_CORRECTED_FREEZE` only if both clean parity and runtime fact
  completeness/fail-closed pass; or
- `REVISE_D09_CORRECTED_FREEZE` with the smallest exact remaining repair.

Do not review Worker02/03, UI, services, real projects/models, or
medical-writing.
