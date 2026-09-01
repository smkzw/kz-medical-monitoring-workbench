# Task Context: mw_final_release_12lane_e2e_20260720

Created: 2026-07-20 12:10:13
Objective: 医学写作子系统发布前12-lane双入口I期/III期全流程实机验收，由Qoder/Hy3等执行模型操作产品独立AI，Codex复现并修复
Task type: `code_open_audit`
Risk: `critical`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_writing_final_release_e2e_20260720/ACCEPTANCE_CONTRACT.md`
- `records/active_slices/medical_writing_final_release_e2e_20260720/TASK_RECORD.md`
- `records/USER_REQUIREMENTS_CURRENT_20260718.md`
- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/`
- 当前源码、测试、常态运行时和用户提供的只读真实方案/摘要/IB。
- 全局`/Users/smkzw/.codex/AGENTS.md`及项目`AGENTS.md`。

## Scope

- In scope: 12条隔离用户旅程、产品独立AI、竞品文档管线、PICOS预填、
  动态章节、逐章候选、引用、编辑、保存恢复、图表/量表、DOCX与Word验收。
- In scope: 执行模型实际操作、缺陷复现、重点修复、同场景重跑和日志。
- Out of scope: 使用执行模型自身文本代替产品AI；污染稳定项目；降低医学、
  Word或桌面体验要求；在P0/P1开放时宣布上线。

## Success Criteria

- 12条lane均有完整证据或明确阻断码；不能静默跳过。
- 三个适应症、I/III期、从零/摘要双入口及指定设计压力全部覆盖。
- P0/P1由Codex复现后关闭并同场景重跑。
- Word目录、样式、字体、图表、引用、分页和可编辑性通过实机检查。
- 稳定运行时未被隔离测试污染，最终发布有回滚与上线后冒烟。

## Risk Boundaries

- 常态5174/8911仅用于只读查看；lane写入使用隔离运行时和临时端口。
- 用户已授权本项目资料只读以及备份后读写；原始临床文件始终只读。
- Qoder只通过现有`~/Downloads/QoderVIP`可见会话和AppleScript输入，
  禁止无头或新建qodercli。
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-20 12:10:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-20: 研究流程图治疗转组/OLE切片完成，相关回归162项通过；
  进入12-lane最终发布E2E。
