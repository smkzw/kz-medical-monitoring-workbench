# R5-S4 Runtime Contract Erratum Acceptance Record

Date: 2026-08-19  
Verdict: `ACCEPT_R5_S4_RUNTIME_ERRATUM`

## Frozen object

- Erratum: `reviews/medical_monitoring_r5_s4_runtime_contract_erratum_v0_1_20260819.md`
- Raw SHA-256: `6faa30ffc0b09741bcfaa166972780bddeeb5163e77bcc01daa08324f0398792`
- Parent contract: `reviews/medical_monitoring_r5_s4_runtime_contract_v0_1_20260819.md`
- Parent raw SHA-256: `58848c51bbf25acddf1b34e2631d32f9294f8df22ecf6b5df438705ddcf16f54`
- Accepted authority anchor raw SHA-256: `1fb07001aa1163bfe4044ad0b36d6879a454b740a1cda912b7acc11d503da0c4`
- Independent reviewer: fresh-context `codex/gpt-5.6-sol:high`
- Reviewer result: `ACCEPT_R5_S4_RUNTIME_ERRATUM`

## Accepted correction

For the exact accepted authority anchor, the executable multi-analysis upper
bound and maximum valid-matrix case are `min(10, A)`, where `A` is the number
of unique fully valid accepted attempt-authority rows. The frozen anchor has
six such rows, so the current honest maximum is `N=6`; `N=10` must not be
claimed or fabricated.

The erratum also confirms that ModelEvidence requires an exact accepted permit
for the exact active ensemble. It does not relax any other parent-contract
gate and does not accept the runtime implementation.

## Boundary evidence

- The parent contract was not rewritten.
- The accepted anchor was not rewritten or re-signed.
- 8911 had no listener at review dispatch.
- No product/UI/browser/real-project/real-model/medical-writing scope was
  unlocked.
