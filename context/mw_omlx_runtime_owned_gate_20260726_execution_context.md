# Execution Context: mw_omlx_runtime_owned_gate_20260726

Created: 2026-07-26 22:14:41
Objective: 让oMLX共享gate成为OCR与翻译模型选择和并发准入的唯一权威，产品消费lease模型并阻止任何绕过或人工覆盖，同时保持8/8/16合同和现有专用链路
Task type: `finite_code_task`
Risk: `critical`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `hermes` / `aishuo` / `cms-model`
- Execution manager: `finite_code_manager_cursor` -> `cursor` / `cursor-cli` / `auto`
- Execution-manager fallback: `Codex takes over finite-code execution management directly`

## Source Of Truth

- Latest global contract:
  `/Users/smkzw/.codex/AGENTS.md`, sections
  `Active 2026-07-26 oMLX OCR/Translation Concurrency Contract` and current
  routing/blackout amendments.
- Shared gate:
  `/Users/smkzw/.codex/tools/omlx_workload_gate.py`.
- Incremental audit:
  `records/handoffs/codex_retake_20260726/OMLX_GATE_INTEGRATION_AUDIT_20260726.md`.
- Product gate/client and role settings:
  - `services/api/app/omlx_workload_gate_client.py`
  - `services/api/app/ai_role_runtime_settings.py`
  - `services/api/app/ocr_gateway.py`
  - `services/api/app/chapter_translation_pipeline.py`
  - `services/api/app/main.py`
  - `services/api/app/ai_gateway.py`
  - `services/api/app/ai_task_runner.py`
  - `frontend/src/App.jsx`
- Focused tests:
  - `tests/test_omlx_role_gate_integration.py`
  - `tests/test_ai_role_runtime_settings.py`
  - `tests/test_chapter_translation_pipeline.py`
  - directly implicated transport and API contract tests only.
- Runtime observations are read-only evidence:
  - `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/ai_role_bindings.json`
  - `/Users/smkzw/.omlx/settings.json`

The latest global contract is authoritative: model selection is runtime-owned
by the shared gate. Prompts and product role settings must not choose or
override the OCR/translation model.

## Risk Boundaries

- Manager pass: no production writes; refine file ownership, sequence and
  acceptance only.
- Worker writes require Codex's updated per-worker prompt after manager review.
- The global gate file is outside the project workspace. Worker 01 may propose
  an exact patch and tests in its runner report, but must not write outside the
  workbench. Codex owns any eventual precise edit to that global file.
- Runtime JSON files are read-only evidence. Do not hand-edit active bindings
  or oMLX service settings.
- Do not change live oMLX `max_concurrent_requests` or launch real OCR or
  translation in this repair pass.
- Do not create nested or duplicate leases. Exactly one boundary must own each
  request's lease lifecycle.
- Preserve OCR<=8, translation<=8 and combined<=16 as admission limits while
  explicitly distinguishing them from the engine scheduler's throughput.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.

## Work Items

1. global gate: selection/config contract, caller override fail-closed, deterministic tests
2. product client and role runtime: consume the gate-owned model, remove all manual OCR/body-model choice, migrate runtime projection and tests
3. oMLX transport boundary: enforce one shared lease without double acquisition, add product-combination concurrency and failure-path regression tests

## Manager Deliverable

Return a concrete sequence and disjoint file mapping for all three work items.
Resolve these risks before worker dispatch:

1. how the product obtains the gate-selected model without caller override;
2. where the single lease-owning boundary lives for dedicated and generic
   oMLX OCR/translation paths;
3. how old non-authoritative UI/runtime values migrate to the gate-owned
   Hy-MT2 binding without hand-editing
   runtime data;
4. how a global gate patch is delivered for Codex to apply without granting a
   worker broad home-directory writes;
5. which focused tests prove ordering, fail-closed behavior, release in
   `finally`, no double acquisition and the 8/8/16 product-combination
   admission contract.

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
