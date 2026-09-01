# Task Context: medical_writing_route_d_v1_20260714

Created: 2026-07-14 13:03:59
Objective: 在不写生产库的前提下实现通用医学方案Route D v1：v3事实包与术语锁、受控表达合同、确定性组装、低风险缺口计算与独立AI填充、事实实现清单，并以RUX/PNH/MY009和阻断D001验证跨项目泛化
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `reasonix-cli` / `deepseek-v4-pro` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_writing_corpus_agent_harness_20260714/TASK_RECORD.md`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/FACT_PACK_V2_AND_TERMINOLOGY_LOCK_SPEC.md`
- `records/active_slices/medical_writing_corpus_agent_harness_20260714/ROUTE_D0_FEASIBILITY_RESULTS.md`
- D0 builder/runner/tests under the same active-slice directory.
- Raw current-project protocols: RUX-03-002 V1.3, MY008211A-PNH-3-01 V1.1, CMS-D001 V1.0 and MY009-UC V3.0. Raw documents are read-only and remain outside the workbench.
- Current independent-model transport and strict JSON parser in `run_direct_routes.py`; credentials stay in Hermes configuration and never enter artifacts.

## Scope

- In scope: isolated v3 fact-pack and expression contracts; data-driven source profiles; generic runner without project-ID branches; deterministic assembly; terminology and realization checks; high/low-risk gap calculation; bounded independent-AI fill for low-risk gaps; run manifests; four-project positive/negative verification.
- Out of scope: production API/database writes, changing the default medical-writing route, declaring an engineering template medically approved, auto-resolving D001's 2/4-week source conflict, copying competitor prose, or treating model review as medical approval.

## Success Criteria

- Generic runner contains no project identifiers or project-specific fact constants.
- Every input/output is frozen by SHA-256 and every sentence has source/fact/template/gap provenance.
- High-risk missing facts, source conflicts, unapproved-template misuse, terminology drift, unsupported numbers/conditions and stale hashes fail closed.
- RUX, PNH and MY009 complete from read-only raw protocols; D001 blocks before model invocation and deletes stale output.
- Low-risk generated gaps use the independent configured model, strict schema and deterministic post-validation; no full-section free generation occurs.
- Focused tests, compileall, rerun determinism, conference/review gate and complete local records pass before any production recommendation.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This task does not dispatch the generated Reasonix route because the user's model boundary requires the workbench pilot's independent buddy/deepseek-v4-pro transport and Hermes conference for complex critique. Codex implements and verifies; any model output remains advisory.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-14 13:03:59: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-14: Codex restored the prior corpus/Agent-harness task record and fixed the v1 scope to three successful real projects plus D001 source-conflict blocking. Production route remains unchanged.
