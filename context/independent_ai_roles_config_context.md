# Task Context: independent_ai_roles_config

Created: 2026-07-29 02:56:49
Objective: 修复医学写作工作台四类独立 AI 可配置，保留角色绑定 adapter，补齐迁移兼容与回归测试并验证构建
Task type: `finite_code_task`
Risk: `medium`
Selected agent route: `aishuo` / `cms-model` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- User-specified workspace: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Authoritative inputs: project `AGENTS.md`, `context/mw_ai_roles_and_progress_contract_20260728.md`, the named role/runtime/adapter sources, and their named regression tests.
- User boundary: do not modify `frontend/src/features/medical-writing/AuthoringCompetitorDrawer.jsx`, `frontend/src/features/writing-reference/WritingReferencePanel.jsx`, r11 evidence/database/matrix, or `frontend/dist`.

## Scope

- In scope: independent role profiles and bindings, migration compatibility, role-bound OCR/translation adapters, oMLX gate boundary, AiGatewayPanel, and focused regression tests.
- Out of scope: the two protected feature files, r11 evidence/database/matrix surfaces, and generated frontend distribution output.

## Success Criteria

- Four roles expose independent provider/profile, Base URL, model, and local credential bindings.
- OCR accepts only specialized allowlisted models until a real visual probe exists; unsupported vision claims are blocked explicitly.
- oMLX contributes only OCR/translation admission and concurrency limits of 8/8/16.
- Existing OCR, body-translation, and support-LLM execution paths resolve the current role binding at call time.
- Relevant pytest, Python compilation, and frontend production build pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- API keys remain in the local encrypted credential store and are never included in public payloads.
- No fabricated visual capability probe is accepted; non-specialized OCR remains blocked with an explicit capability state.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-29 02:56:49: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-29: Implemented role-settings v2 migration with role-scoped profiles, independent defaults, recommendations, OCR capability state, and local credential preservation.
- 2026-07-29: Rebound OCR, body translation, and support-LLM adapters to role settings; removed model authority from the oMLX gate boundary.
- 2026-07-29: Added/updated focused regression tests and preserved test-injected OCR gateways.
- 2026-07-29: Validation: focused role/gateway/pipeline/contract tests `102 passed`; targeted `py_compile` passed; frontend `npm run build` passed. Build output was moved to `/tmp/codex_independent_ai_roles_config_dist_20260729_final`; `frontend/dist` is absent.
- 2026-07-29: Full suite was also run: `4117 passed, 30 failed, 24 warnings`; remaining failures are outside this slice (authoring prefill/export/structured-design/bootstrap, frontend contract fixtures, and ctgov fixtures). The directly affected OCR runner failure was fixed and is covered by the passing focused suite.
- 2026-07-29 03:31: Codex conflict review found two release-blocking gaps:
  non-specialized OCR had no real visual probe path, and the active
  comprehensive-AI compatibility check ignored v2 role bindings.
- 2026-07-29 03:37: Added an exact profile+model-bound OCR visual probe. The
  endpoint generates a real PNG containing a fixed token, sends it through the
  selected OpenAI-compatible vision route, validates the extracted token, and
  persists capability evidence only for that exact binding. Model/profile
  changes invalidate the proof. oMLX probes and subsequent OCR requests retain
  the shared OCR lease.
- 2026-07-29 03:37: Updated active comprehensive-AI gating to treat
  `ai_role_bindings_v2` as authority. A disabled or mismatched v2 binding now
  fails closed instead of falling through to the active provider profile.
- 2026-07-29 03:39: Added concise UI action `验证视觉能力` for OCR and an
  OpenAI-compatible Base URL example. No extra status card or persistent
  warning surface was introduced.
- 2026-07-29 03:42: Codex verification: `77` focused tests and `321` broader
  related tests passed; Python compilation and frontend production build
  passed. Source accepted for r12 freeze. Real configured provider/oMLX calls
  remain part of r12 runtime acceptance.
