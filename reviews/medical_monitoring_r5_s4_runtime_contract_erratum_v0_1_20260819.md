# R5-S4 Runtime Contract Erratum v0.1

Date: 2026-08-19  
Status: `R5_S4_RUNTIME_ERRATUM_READY_FOR_REVIEW`  
Supplements, and does not rewrite: `reviews/medical_monitoring_r5_s4_runtime_contract_v0_1_20260819.md`  
Parent contract SHA-256: `58848c51bbf25acddf1b34e2631d32f9294f8df22ecf6b5df438705ddcf16f54`

The only valid review verdicts are `ACCEPT_R5_S4_RUNTIME_ERRATUM` and
`REVISE_R5_S4_RUNTIME_ERRATUM`.

## 1. Reason

The accepted parent contract states both that multi-analysis supports `2 <= N <= 10`
and that the valid runtime matrix must include `N=10`. The separately accepted external
authority anchor contains exactly six unique `attempt_authority_rows`: `a1`, `a2`, `m1`,
`m2`, `g1`, and `g2`. Each runtime attempt must bind to one unique accepted row; worker
binding, session, and independent-context identities may not be duplicated, and runtime
tests may not invent authority absent from the accepted anchor. Therefore the parent
contract's fixed `N=10` acceptance case is not constructible from its accepted source of
authority.

This erratum closes only that contradiction. It does not weaken identity isolation,
authority binding, ModelEvidence permits, verification, conflict visibility, hash,
history, source, Query, adjudication, audience, readonly, or challenge requirements.

## 2. Replacement rule for parent section 5.1

Replace only the upper-bound meaning of the parent clause
`multi_analysis: 2 <= N <= 10` with:

> `multi_analysis`: `2 <= N <= min(10, A)`, where `A` is the number of unique,
> fully valid `attempt_authority_rows` in the exact accepted external authority anchor
> supplied to the runtime. Every active attempt consumes one different accepted row.
> The frozen audience ordinal vocabulary remains “分析一” through “分析十”; a smaller
> accepted anchor limits the executable cardinality but does not change that vocabulary.

For the accepted anchor SHA referenced by the parent contract, `A=6`; the executable
and testable maximum is therefore `N=6`.

Fail-closed consequences:

- `N > min(10, A)` returns the accepted cardinality failure and never synthesizes,
  copies, aliases, or reuses an authority row.
- Duplicate attempt, binding, session, or independent-context identities remain invalid.
- A later versioned anchor with at least ten unique valid rows may exercise `N=10`
  without another semantic change, but it must be independently accepted; the current
  accepted anchor is never edited or re-signed in place.

## 3. Replacement rule for parent section 9 valid matrix

Replace only `N=10` in the sentence beginning “有效矩阵至少包含” with:

> `N=min(10, A)` for the exact accepted external authority anchor.

For the current accepted anchor the required valid matrix is therefore `N=0`, `N=1`,
`N=2`, and the honest maximum `N=6`, plus every other matrix dimension already listed
in the parent contract. No test or completion claim may state that `N=10` was exercised
for this anchor.

## 4. ModelEvidence clarification

This erratum does not broaden a ModelEvidence permit. A ModelEvidence object is legal
only when all of its fields exactly equal one accepted permit and its ensemble identity,
ensemble size, member analysis refs, model/output identity, and active membership all
exactly match the current active ensemble. When no exact permit exists for that active
ensemble, ModelEvidence must be absent. A permit for the `a1/a2` two-member ensemble is
not authority for the current six-member ensemble.

## 5. Acceptance and scope

Acceptance requires:

- the parent contract SHA above remains unchanged;
- the accepted external authority anchor remains unchanged and contains exactly the six
  unique rows named above;
- a fresh isolated reviewer returns `ACCEPT_R5_S4_RUNTIME_ERRATUM` for this exact raw SHA;
- 8911 remains stopped and no product/UI/browser/real-project/real-model work is implied.

Acceptance of this erratum only resolves the cardinality contradiction for the already
unlocked synthetic/offline renderer-neutral S4 runtime. It does not accept the runtime
implementation, S5+, UI/browser behavior, clinical truth, medical writing, product, or
production behavior.
