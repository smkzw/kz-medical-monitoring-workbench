# B3 implementation plan

## Router decomposition

- [ ] Extract shared DTOs, public wording and pure projections.
  - [x] Move request contracts and publication error to one authoritative module.
  - [x] Move continuity response contracts and semantic projection helpers.
  - [ ] Move shared public-text sanitization and remaining pure projections.
    - [x] Move backup, restore and preflight audience projections.
    - [x] Move public secret-field filtering and generic projection sanitization.
    - [x] Move launch, publication-state and public-result projections.
- [ ] Extract project lifecycle, backup and restore capability router.
- [ ] Extract setup, special-risk rule and profile capability router.
- [ ] Extract run preparation, execution and progress capability router.
- [ ] Extract publication, result and continuity capability router.
- [ ] Reduce the root R7 product factory to dependency wiring and mounting.

## Backend decomposition

- [ ] Split protocol contracts/applicability/evidence/evaluation/materialization.
- [ ] Split efficacy validation/resolution/engine/output gates.
- [ ] Split launch registry records, publication store and continuity store.
- [ ] Split remaining files above the hard limit by cohesive domain.

## Acceptance

- [ ] No non-generated authoritative source file exceeds 1,500 lines without a documented exception.
- [ ] Public route behavior remains compatible.
- [ ] Complete affected risk suites pass.
- [ ] Medical-writing route mounts and assets remain unchanged.
- [ ] Trellis journal and git commits contain the phase evidence.
