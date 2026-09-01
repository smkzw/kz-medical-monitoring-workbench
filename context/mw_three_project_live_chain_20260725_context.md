# Task Context: mw_three_project_live_chain_20260725

Created: 2026-07-25 08:41:35
Objective: 在稳定5174/8911运行态中，使用产品自身独立AI完成UC、CRSwNP、D017三个真实项目的事实框架、竞品检索分诊、来源核验和方案预填充，并由Codex做科学性与真实浏览器验收
Task type: `clinical_document_router`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Stable product runtime: `http://127.0.0.1:5174/`, backend `http://127.0.0.1:8911/`.
- Durable runtime store and project APIs exposed by the backend; all state changes must use product APIs or the real UI.
- UC project: `proj_my009_uc`, source protocol registry entry
  `src_proj_my009_uc_protocol_docx_eeb7200d37e5` and the original protocol identified there.
- CRSwNP project: `proj_user_4ef4aa3da246`; current journey must be read before any correction because it contains known stale cross-indication data.
- D017 project: `proj_user_3ecb0bc287c0`; sparse from-zero path used for cross-indication validation.
- Product AI policy and runtime receipts from `/api/ai-gateway/status` and durable medical-writing job APIs.
- Recovery and decision history:
  `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md` and
  `SOFT_PAUSE_RESUME.md`.

## Scope

- In scope: project fact framing, formal impact preview/commit, competitor search, independent-AI triage,
  evidence/source validation, corpus readiness, AI prefill generation/adoption, real browser interaction,
  deterministic and scientific acceptance evidence, and narrowly scoped fixes exposed by those workflows.
- In scope: using authorized real project data and current production AI configurations.
- Out of scope: security/backdoor auditing, direct SQLite mutation, replacing product AI with Codex or an
  external reviewer, auto-approving unreviewed medical facts, and unrelated module refactors.

## Success Criteria

- Each project starts from a factually correct product/indication/phase state without cross-project residue.
- Search plans and triage use the product's independently configured AI and durable jobs; receipts declare
  `codex_runtime_dependency=false`.
- Selected competitor studies are indication- and phase-relevant, source traceable, and medically plausible.
- Project prefill is evidence-linked and adopted through the normal author workflow; optional or unknown
  fields remain explicit rather than fabricated.
- Reload/reconnect preserves the workflow state, and the real desktop UI remains usable at the stable port.
- Original imported documents and authoritative sources remain byte-identical.

## Risk Boundaries

- Runtime state writes are authorized only through the product UI/API and must include current revision/CAS,
  actor, reason and idempotency keys where required.
- Source documents are read-only. Existing RUX reconciliation work is not part of this three-project loop.
- External execution/conference outputs are review evidence only and may not substitute for product AI.
- At the current 2026-07-25 08:30 boundary, new roles resolving to
  `Hermes/aishuo/cms-model` use Hermes again; do not apply the expired Qoder replacement.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-25 08:41:35: Task initialized by `tools/hermes_workflow_guard.py init-task`.
