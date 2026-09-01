# Execution Context: mw_final_release_matrix_20260727

Created: 2026-07-27 05:07:33
Objective: 医学写作系统最终上线门：仅在隔离运行时中，由四类测试者完成十二个互异非肿瘤适应症、两种用户视角的真实浏览器端到端写作、独立AI、语料、引用与完整DOCX闭环；修复后复测直至通过。
Task type: `long_horizon_code`
Risk: `critical`
Execution module trigger: Codex identified 4 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_k3` -> `kimi` / `kimi-code` / `kimi-code/k3`
- Execution manager: `complex_manager_grok` -> `pi` / `alibaba` / `qwen3.8-max-preview`
- Execution-manager fallback: `use the declared role fallbacks`

## Source Of Truth

- `records/handoffs/CODEX_RESUME_P0_18_20260726.md`
- `records/handoffs/AGENT_1_CURSOR_HANDOFF_20260725.md`
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`
- `records/handoffs/codex_retake_20260726/FINAL_4X3_TEST_MATRIX_DRAFT.md`
- `plans/codex_final_4x3_isolated_runtime_20260727.md`
- `scripts/qc/mw_final_4x3_matrix.json`
- `scripts/qc/mw_final_4x3_harness.py`
- `prompts/final_4x3_e2e_20260727/CLEAN_STATE_BACKUP_RESET_CHECKLIST.md`
- `runs/execution/mw_final_4x3_harness_20260727/REPORT.md`
- Current workspace source, tests and generated artifacts only where a failed
  acceptance locator requires them.
- The shared product runtime at
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime` is read-only
  evidence and must not be copied, reset, purged or modified by an external
  role. Secrets must never be printed or included in reports.

## Risk Boundaries

- No writes to the shared product runtime or existing user projects.
- Test runs write only to fresh isolated runtimes and their declared run
  directories.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- Do not repeat broad codebase review already accepted. Inspect only conflicts,
  missing gates, failed locators and cross-lane risks.

## Work Items

1. 隔离运行时与独立AI/OCR/Hy-MT2翻译可用性基线，禁止触碰共享真实项目。
2. DOCX精确导出门：封面、目录跳转、标题样式、字体、摘要嵌套表、图表量表、引用与Word实际打开。
3. Pi Alibaba Qwen3.8 和 Pi CMS 两条真实浏览器三适应症测试通道。
4. CodeBuddy Hy3 和 Cursor composer-2.5 两条真实浏览器三适应症测试通道。

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
