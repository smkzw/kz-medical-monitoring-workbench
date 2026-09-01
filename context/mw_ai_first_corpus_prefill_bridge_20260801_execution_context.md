# Execution Context: mw_ai_first_corpus_prefill_bridge_20260801

Created: 2026-08-01 12:20:21
Objective: 把已持久化且来源绑定的第一轮Protocol语料分析接入authoring prefill，生成可审阅设计候选并保持精确事实fail-closed
Task type: `finite_code_task`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `pi` / `deepseek` / `deepseek-v4-flash`
- Execution manager: `finite_code_manager_cursor` -> `cursor` / `cursor-cli` / `auto`
- Execution-manager fallback: `Codex takes over finite-code execution management directly`

## Source Of Truth

- `context/mw_ai_first_corpus_prefill_bridge_20260801_context.md` is the
  project contract and observed-runtime evidence summary.
- Authoritative source paths:
  - `services/api/app/main.py`
  - `services/api/app/medical_writing_authoring_prefill.py`
  - `services/api/app/medical_writing_authoring_prefill_ai.py`
  - `services/api/app/medical_writing_authoring_prefill_evidence.py`
  - `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`
  - `services/api/app/medical_writing_corpus_analysis_ai.py`
  - `services/api/app/medical_writing_research_pipeline.py`
  - `packages/contracts/workbench_contracts/models.py`
  - focused `tests/test_medical_writing_authoring_prefill*.py`
- The immutable runtime row is evidence only. Workers must not open or modify
  the isolated runtime database.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- Do not start services, call a live model, regenerate the live package, or
  replay triage/preparation/OCR/translation.
- Preserve exact-fact gates for dose, endpoint, AESI, sample size and washout.
- Competitor Protocol observations may produce review candidates only; they
  may never be promoted to current-project facts.
- Allowed source writes are limited to
  `services/api/app/medical_writing_authoring_prefill*.py`, minimal wiring in
  `services/api/app/main.py`, and focused prefill tests. Preserve unrelated
  user changes.

## Acceptance Checks

- Fail closed on project/pipeline/snapshot/analysis ID or output-hash drift.
- Every supplemental entry retains immutable source locator/hash and analysis
  lineage.
- Module-to-target compatibility is explicit and bounded.
- Generation and adoption verification reconstruct the same catalog.
- Deterministic tests cover valid bridge, identity/hash rejection, unsupported
  target rejection, competitor-option semantics and exact-fact preservation.
- Run focused tests only; no full-app import or service startup.

## Work Items

1. 设计并实现exact round1 analysis identity/hash到prefill evidence catalog的只读桥接
2. 实现模块到target path的保守兼容及生成/采用目录同源重建
3. 补齐确定性测试并验证不放宽剂量终点等精确事实门

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
