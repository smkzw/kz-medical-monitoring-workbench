# Codex Execution Plan: mw_prefill_deepseek_prod_exec_20260720

Objective: Integrate direct production deepseek-v4-pro into medical-writing AI-first prefill with evidence-bounded bulk generation, English ClinicalTrials.gov condition term, deterministic fallback, and real RA/PNH validation

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Implement one bulk production AI prefill adapter and wire it outside SQLite write transactions; preserve existing deterministic fallback and exact-fact evidence gates. | `runs/execution/mw_prefill_deepseek_prod_exec_20260720/worker_01.md` |
| `worker_02` | Add focused tests for AI JSON/schema handling, model identity, timeout/partial fallback, English ClinicalTrials.gov condition candidate, evidence source IDs, and exact-fact blocking. | `runs/execution/mw_prefill_deepseek_prod_exec_20260720/worker_02.md` |
| `worker_03` | Run independent RA and PNH end-to-end production-model quality checks, inspect ClinicalTrials.gov retrieval and candidate usability, and write bounded evidence without touching stable databases. | `runs/execution/mw_prefill_deepseek_prod_exec_20260720/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `grok-build` | `grok-4.5` | `runs/execution/mw_prefill_deepseek_prod_exec_20260720/manager.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
