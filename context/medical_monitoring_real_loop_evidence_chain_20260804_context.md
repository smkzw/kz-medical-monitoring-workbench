# Task Context: medical_monitoring_real_loop_evidence_chain_20260804

Created: 2026-08-04 09:32:13
Objective: 将 generalization evidence hash 沿 real-loop execution/acceptance evidence 链路只读绑定并 fail-closed，完成聚焦/相邻验证，不启动运行时
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- 最新 global/workspace/workbench `AGENTS.md` 与当前文件系统。
- `monitoring_real_loop_readiness.py`, `monitoring_real_loop_execution.py`,
  `monitoring_real_loop_acceptance.py`, `monitoring_real_loop_acceptance_revalidation.py`
  及其测试。
- LOOP 5.86 anti-overfit generalization contract 与 LOOP 5.89 readiness binding 记录。
- B6/C14 gate artifacts；本切片不得绕过或改变它们。

## Scope

- In scope: 在 execution/acceptance/revalidation evidence 中携带并校验 upstream
  readiness report hash 与 generalization snapshot hash；保持旧位置参数兼容；将
  受影响 evidence schema 明确升级为 v2；新增缺失/不一致/有效路径测试和记录。
- Out of scope: provider/runtime/queue/database/API server/browser/Playwright、五个真实
  项目、B6/C14、source/CAS/approved-input 写入或任何商业化结论。

## Success Criteria

- readiness hash 能确定性地传入 execution evidence report；任何缺失或与 readiness
  不一致的链路值 fail-closed。
- acceptance/revalidation persisted evidence 能绑定相同链路标识；旧调用没有新标识时
  保持 blocked，不把兼容默认误当作证据。
- focused/adjacent suites pass，reserved ports remain empty，review-gate 无 warning/error。

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- 仅修改 workbench 内直接相关的 evidence-contract modules/tests/records；不启动服务。
- hash 是证据身份绑定，不代表 AI 正确性、医学确认、浏览器验收或 release readiness。
- Codex 为最终审查者；不能以本切片开放 B6/C14 或 runtime/write authority。

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 09:32:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 09:33:00: Static audit found execution and acceptance reports did not carry
  the readiness/generalization snapshot identity; acceptance revalidation only compared its
  local matrix report hash.
- 2026-08-04 09:38:51: Focused evidence-chain tests passed 50/50; adjacent real-loop suite
  passed 71/71. Execution, acceptance and revalidation schema versions were upgraded to v2
  with explicit chain hash fields and mutation tests.
- 2026-08-04 09:47:11: Clean full `tests/test_monitoring*.py` passed 1964/1964 with 25
  existing warnings in 490.96s; reserved ports remained empty. Records/review/metrics were
  written.
- 2026-08-04 09:47:28: `review-gate --require-verification` returned
  `{"ok":true,"warnings":[],"errors":[]}`; LOOP 5.90 closed.
