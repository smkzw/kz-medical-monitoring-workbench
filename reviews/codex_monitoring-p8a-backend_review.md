# Codex Review: monitoring-p8a-backend

Date: 2026-07-29
Delegated-agent output: `runs/codex_monitoring-p8a-backend.md`

## Verdict

Pass for the requested P8-A backend slice.

## Boundary Check

- Product edits are limited to the eight authorized monitoring backend files
  listed in the handoff plus monitoring-specific tests.
- Task records and read-only conference records were written under `context/`,
  `plans/`, `prompts/`, `runs/`, `reviews/`, `metrics/`, `logs/`, and
  `records/handoffs/`.
- No `App.jsx`, global CSS, medical writing, shared AI, P7B/P7C, shared contract,
  live API, or real runtime database edit was made.
- The workspace has no Git metadata, so the boundary check uses the explicit
  edit inventory and observed tool writes rather than a Git diff.

## Main-agent conflict review

- Delegated implementation and its manager/conference evidence were read as
  advisory output, then the main agent re-read the taxonomy-relevant creation,
  persistence, query, projection, and adapter boundaries.
- The main agent confirmed that classification inputs exclude title, rationale,
  risk type, and evidence prose.
- The main agent confirmed that legacy coarse degradation retains lineage and
  that the repository write gate rejects CM/study-treatment crossing.
- The delegated worker reported: focused 88 passed, repository 19 passed, API
  contract 13 passed, full monitoring 716 passed, Python compilation and scoped
  Ruff passed. These counts are delegated execution evidence, not a claim that
  the main agent personally ran every command.
- The main agent independently reran the seven highest-conflict taxonomy,
  repository, API, deterministic/AI bridge, RUX and MY009 test files; the run
  completed without a reported failure. The full 716-test suite was not
  redundantly rerun by the main agent.
- Browser/runtime verification was intentionally not run because frontend
  integration and API restart were outside scope.

## Delegated-Agent Output Review

- Two independent participants and one chair performed read-only review.
- Codex rejected the suggestion that Safety/PV must be a function of the
  primary category: the contract requires an independent additive projection,
  so evidence/domain may set the flag without replacing classification.
- Codex accepted the chair's persistence-firewall finding and added uniform
  write-gate validation plus negative and EX2-alias tests.
- The review's taxonomy-version persistence concern is valid before a future v2
  migration but is not an authorized real-DB change in this v1 slice.
- Reviewer claims about missing DESC coverage and legacy MY009
  `primary_category` were corrected against current source.

## Delegation and conference

The P8-A implementation was delegated to a Codex subagent. Its independent
review used the declared Pi/aishuo, CodeBuddy and Pi/Alibaba conference routes.
Those reports remained advisory; the main agent reviewed only the medical and
interface conflict points and retained final acceptance authority.

## Residual Risk

- The frontend still contains its old inference and client-side list behavior;
  it must consume the new backend projection in the next P8 slice.
- Historical snapshots do not persist taxonomy version as a dedicated column;
  design and migrate before v2.
- MG-K10 remains risk-not-enabled, so it contributes no classification examples.
- Existing FastAPI lifecycle, OpenPyXL, and one RUX unused-variable warning
  remain outside this bounded change.
