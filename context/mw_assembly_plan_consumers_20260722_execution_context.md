# Execution Context: mw_assembly_plan_consumers_20260722

Created: 2026-07-22 13:52:07
Objective: 将ProtocolAssemblyPlan真正接入医学写作所有下游消费者，并关闭I期typed Parts和AI失败时确定性临床设计候选问题
Task type: `complex_delivery_conference`
Risk: `critical`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `complex_executor_cms` -> `hermes` / `aishuo` / `cms-model`
- Execution manager: `complex_manager_grok` -> `grok` / `grok-build` / `grok-4.5`
- Execution-manager fallback: `use the declared role fallbacks`

## Source Of Truth

- Global and project `AGENTS.md`.
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/CURRENT_GAP_MATRIX.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/PROTOCOL_ASSEMBLY_PLAN_DECISION.md`
- `runs/conference/mw_current_full_audit_20260722/qoder_qwen38_current_audit.md`
- Current contracts, services, frontend and tests under this workbench. The current filesystem is
  authoritative; no Git history exists.
- Accepted baseline: `ProtocolAssemblyPlan` persistence/projection API and author freeze E2 pass.
  Critical remaining truth: downstream generators do not yet call the plan service; I期 Parts remain
  `List[str]`; deterministic prefill can still emit adoptable SAD/MAD defaults without product-AI evidence.

## Risk Boundaries

- This is the local implementation workbench; bounded source/test writes are authorized only after the
  manager defines disjoint file ownership. Do not touch user source DOCX/PDF, runtime databases, stable
  ports, external accounts or repository-external production AI configuration.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- Product AI must remain direct DeepSeek through the product gateway. Workers may use fake providers only
  through `test_only_provider_injection`; they must not substitute their own model output for product AI.
- Preserve the existing author-freeze, StudyDefinition binding, citation guard, DOCX source fidelity and
  non-writing ApprovalGate behavior.

## Required Success Criteria

1. `phase1_parts` becomes a typed per-Part structure with population/cohort/dose, PK/PD, safety,
   stopping, SoA and transition dependencies; legacy string input may be read-only migrated, never remain
   the downstream authority.
2. When product AI/evidence is absent or fails, deterministic prefill produces facts/scaffolding and
   explicit unknowns only; no adoptable clinical design conclusion.
3. Summary, section applicability/content context, SoA, flowchart, evidence intent, corpus retrieval,
   AI candidate/revision context and DOCX TOC/export each consume one confirmed current plan revision or
   fail closed. A projection endpoint alone is not consumption.
4. `interim_analysis=false`, active comparator, complex background treatment, modality/route and
   multi-Part Phase I counterexamples remain identical across every projection.
5. Tests cover CAS/staleness, project isolation, unknown driver blocking and no regression to author
   freeze, citations, tables, attachments or non-writing approvals.

## Work Items

1. Typed Phase I parts and safe AI-first prefill
2. Synopsis chapter SoA flowchart DOCX projection consumption
3. Evidence corpus and AI candidate projection consumption

## Manager First-Pass Contract

The manager runs before workers. It must map exact consumer call sites, dependencies and disjoint write
sets; identify unavoidable serial files (`models.py`, `main.py`, plan service); decide whether worker 01
must land before workers 02/03; and provide acceptance commands and stop conditions. It must not claim
implementation complete in this first pass.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
