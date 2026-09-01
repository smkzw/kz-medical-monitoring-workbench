# Execution Context: mw_prefill_deepseek_prod_exec_20260720

Created: 2026-07-20 00:15:13
Objective: Integrate direct production deepseek-v4-pro into medical-writing AI-first prefill with evidence-bounded bulk generation, English ClinicalTrials.gov condition term, deterministic fallback, and real RA/PNH validation
Task type: `complex_delivery_conference`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `complex_executor_cms` -> `hermes` / `aishuo` / `cms-model`
- Execution manager: `complex_manager_grok` -> `grok` / `grok-build` / `grok-4.5`
- Execution-manager fallback: `use the declared role fallbacks`

## Source Of Truth

- Product behavior and architecture:
  - `context/mw_prefill_deepseek_prod_20260720_context.md`
  - `services/api/app/medical_writing_authoring_prefill.py`
  - `services/api/app/medical_writing_authoring_journey.py`
  - `services/api/app/medical_writing_fact_intake.py`
  - `services/api/app/ai_gateway.py`
  - `services/api/app/main.py`
  - `services/api/app/writing_reference.py`
  - `packages/contracts/workbench_contracts/models.py`
- Existing regression contracts:
  - `tests/test_medical_writing_authoring_prefill.py`
  - `tests/test_medical_writing_authoring_journey.py`
  - `tests/test_ai_gateway.py`
  - `tests/test_frontend_medical_writing_contract.py`
- Current durable task record:
  - `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/TASK_RECORD.md`
- Primary external behavior:
  - DeepSeek JSON output: `https://api-docs.deepseek.com/guides/json_mode`
  - ClinicalTrials.gov API search areas: `https://clinicaltrials.gov/data-api/about-api/search-areas`
- Current observed defect: Chinese indication text is copied into
  `framing.clinicaltrials_condition_term`; RA and PNH searches therefore
  returned zero useful studies. The production AI stage must propose a
  medically correct English condition term before retrieval.
- Independent product AI route: use the configured direct DeepSeek supplier
  with model `deepseek-v4-pro`. Do not route product inference through Codex,
  Hermes, Grok, Qoder or another conference model. Do not print or persist
  credentials.

## Risk Boundaries

- No stable database writes or production deployment.
- Use isolated temporary databases and test projects only.
- No silent package installation, credential changes, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- The model/network call must occur outside `BEGIN IMMEDIATE` or any SQLite
  write transaction.
- One bulk AI call per prefill stage is the target. Do not implement 17
  field-by-field model calls.
- Deterministic output must remain a complete fallback when the provider is
  unavailable, times out, returns invalid JSON, returns the wrong model
  identity, or only partially covers the schema.
- AI output is a candidate package, not an approved project fact. Exact
  endpoints, thresholds, doses, schedules, sample sizes, durations, AESI or
  other exact facts remain blocked unless directly supported by registered
  source IDs.
- User adoption is the medical-manager decision. Do not add a second
  “待医学批准” workflow.

## Disjoint Write Authority

- `worker_01` may edit only:
  - `services/api/app/medical_writing_authoring_prefill_ai.py` (new if useful)
  - `services/api/app/medical_writing_authoring_prefill.py`
  - `services/api/app/medical_writing_authoring_journey.py`
  - `services/api/app/main.py`
  - `services/api/app/ai_gateway.py` only if an adjacent shared adapter defect
    cannot be solved in the prefill-specific module.
  - Targeted same-session remediation report:
    `runs/execution/mw_prefill_deepseek_prod_exec_20260720/worker_01_remediation.md`
- `worker_02` may edit only:
  - `tests/test_medical_writing_authoring_prefill_ai.py` (new)
  - `tests/test_medical_writing_authoring_prefill.py`
  - `tests/test_ai_gateway.py`
- `worker_03` is read/test-only except for isolated QC artifacts under:
  - `records/active_slices/medical_writing_ai_first_authoring_redesign_20260718/prefill_ai_prod_qc_20260720/`
- No worker may edit frontend files, runtime databases, task logs, global
  configuration or another worker's write set.

## Acceptance Checks

- Established interpreter: `/usr/bin/python3`.
- Focused regression:
  - `/usr/bin/python3 -m pytest -q tests/test_medical_writing_authoring_prefill.py tests/test_medical_writing_authoring_prefill_ai.py tests/test_medical_writing_authoring_journey.py tests/test_ai_gateway.py`
- Existing frontend contracts must remain green after Codex integration.
- Direct production-model checks must cover at least:
  - rheumatoid arthritis, phase II;
  - paroxysmal nocturnal hemoglobinuria, phase III.
- Each real-model result must record actual provider/model identity, latency,
  fallback status, candidate counts, evidence/source IDs, blocked exact facts,
  and whether the English condition term returns relevant ClinicalTrials.gov
  studies.
- Never log secrets or direct personal identifiers.

## Work Items

1. Implement one bulk production AI prefill adapter and wire it outside SQLite write transactions; preserve existing deterministic fallback and exact-fact evidence gates.
2. Add focused tests for AI JSON/schema handling, model identity, timeout/partial fallback, English ClinicalTrials.gov condition candidate, evidence source IDs, and exact-fact blocking.
3. Run independent RA and PNH end-to-end production-model quality checks, inspect ClinicalTrials.gov retrieval and candidate usability, and write bounded evidence without touching stable databases.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
