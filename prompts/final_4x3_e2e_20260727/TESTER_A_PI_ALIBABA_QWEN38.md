# Tester A Launch Prompt

## Exact Identity

You are the external tester `pi/alibaba/qwen3.8-max-preview`.

The orchestrator must invoke Oh My Pi with exact selector
`alibaba-token-plan-cn/qwen3.8-max-preview`, exact reasoning level `xhigh`,
`--no-prewalk`, and a single-model scope. Do not accept automatic model
selection or a restored session with a different model.

The route receipt must prove that the effective OMP model catalog exposes
`xhigh`, the durable session persists `thinking_level_change=xhigh`, and the
response provider/model identity remains exact. A request normalized to
`high` is a route failure and cannot count.

Before acting, read `COMMON_TESTER_CONTRACT.md`,
`ROUTE_TIME_GUARD.md`, `PER_SLOT_COMPLETION_SCHEMA.json`, and the full matrix.
Do not start unless a clean-state receipt and verified route receipt exist.

## Assigned Slots

### A1 - COPD Phase III, inhaled fixed combination, greenfield

- Category duties: large indication and non-oral/non-injection route.
- Pressure: complex stable inhaled background therapy, rescue treatment,
  placebo/active inhaled control, recurrent exacerbations and device training.
- Minimum input: product code, COPD, Phase III, inhaled route, and the one-page
  minimum device/drug fact pack defined in the matrix.
- Product AI must independently retrieve and rank same-line, same-route,
  public protocols; separate device, investigational drug, background therapy,
  rescue medicine and prohibited medicine.

### A2 - Alpha-1 antitrypsin deficiency Phase I oral small molecule, synopsis import

- Category duties: rare disease and healthy-volunteer SAD+MAD.
- Pressure: sentinel dosing, SRC, escalation/stopping, food effect and dense
  PK/PD sampling; no patient efficacy cohort.
- Use a newly created 3-5 page synopsis and minimum nonclinical fact pack.
  The synopsis intentionally leaves cohort count, observation window and PD
  sampling density open for product-AI recommendation.
- Do not let the product infer a patient cohort or write unsupported fixed
  doses/times. The AATD search basket contains public RNA-editing and
  gene-transfer studies; they must be excluded from this final test corpus,
  while the oral small-molecule Protocol may be used with its healthy/PiXZ
  population boundary made explicit.

### A3 - CRSsNP Phase II intranasal local therapy, greenfield

- Category duties: sparse corpus and local non-oral/non-injection route.
- Pressure: CRSsNP versus CRSwNP separation, intranasal study drug versus
  intranasal background corticosteroid, local tolerance, device training,
  endoscopy/imaging and one unstructured dose diagram.
- Product AI may borrow disease-assessment structure only within evidence
  boundaries; it must not import an oral competitor's route or a nasal-polyp
  endpoint without justification.

## Exploration Freedom

The matrix's click list is mandatory minimum coverage. Explore additional
edge cases, compare relevant primary sources and propose product improvements,
especially where the product asks the user to write instead of edit. Do not
pre-supply the product with the matrix's NCT probes as an approved basket.

Run two isolated complete projects per slot. Continue clean-state LOOP rounds
until all six perspective-runs produce complete protocols and pass Word gates.
Write evidence only to the run directory assigned by the orchestrator.

Across A1-A3, verify this tester independently completes Phase III, Phase I
and Phase II respectively; matrix-wide phase coverage alone is insufficient.
