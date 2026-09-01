# Execution Context: mm_r7_slice09e_implementation_20260831

Created: 2026-08-31 09:42:40 CST
Objective: 按冻结合同v0.2实现医学监查Slice-09E本地分发与数据处置synthetic/offline闭环，保持医学写作与真实项目不变。
Task type: `finite_code_task`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.
Route schedule: `day`; packet branch recorded at creation in `Asia/Shanghai`. Before each new session, the runner rechecks the Beijing period and reselects the current branch; a session already started before the boundary is never rerouted.
Effective worker chain: `cursor/default -> google-antigravity/gemini-3.7-flash:high -> mtplx/mtplx-qwen38-27b-optimized-quality:medium -> opencode-go/muse-spark-1.2-contributor:xhigh -> openai-codex/gpt-5.6-luna:max`

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor` -> `pi` / `cursor` / `default`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `reviews/medical_monitoring_r7_slice09e_local_distribution_contract_v0_2_20260831.md`
- `context/medical_monitoring_r7_slice09e_contract_acceptance_record_20260831.md`
- `context/medical_monitoring_r7_slice09_overall_and_r7_phase_review_20260831.md`
- `context/medical_monitoring_r7_slice09a_implementation_acceptance_record_20260830.md`
- `context/medical_monitoring_r7_slice09b_implementation_acceptance_record_20260830.md`
- `context/medical_monitoring_r7_slice09c_implementation_acceptance_record_20260830.md`
- `deploy/medical_writing_local/manage.zsh` and `build_release_bundle.py` may be read only as a structural precedent; they must not be edited or packaged.
- Do not add production paths without explicit Codex authorization.

## Authorized Writes And Checks

- Worker 01: `deploy/medical_monitoring_local/manage.py`, `manage.zsh`, `README.md` only.
- Worker 02: `deploy/medical_monitoring_local/distribution.py`, `release_sources.json` only; may minimally amend worker-01 files only if required to expose the frozen commands.
- Worker 03: `tests/test_medical_monitoring_local_distribution.py` and `artifacts/mm_r7_slice09e_implementation_20260831/**` only; production files are read-only for this worker.
- Commands may use temporary directories and synthetic fixture data only. Do not start 8911/5174/8984, do not invoke a model/browser, and do not read the five real project roots.
- Use only Python standard library and existing shell tools; add no dependency.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- `deploy/medical_writing_local/**`, all medical-writing source, real project roots, credentials and existing runtime databases are immutable boundaries.

## Work Items

1. 实现deploy/medical_monitoring_local中文管理入口、preflight、端口归属与退出码合同。
2. 实现发布清单、prepare-upgrade受控synthetic演练与preview-only uninstall plan，复用09A/09B语义。
3. 实现聚焦测试、normal/-O/-OO与三个hash seed确定性、边界和相邻R7验证证据。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
