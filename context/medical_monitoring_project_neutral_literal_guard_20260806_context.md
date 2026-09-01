# Task Context: medical_monitoring_project_neutral_literal_guard_20260806

Created: 2026-08-06 05:50:36
Objective: 为 feature-owned 医学监查生产前端增加项目中立静态守卫，禁止嵌入已知项目/公司名称、本机绝对路径或 `file://`；明确该守卫不能替代至少三个真实研究的原始方案/listing 泛化验收。
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

PRD P0-07 要求至少三个结构差异明显的研究从原始文件开始验证，并警惕项目硬编码/隐性过拟合。当前真实 LOOP gate 仍阻断，不能运行真实项目，因此先增加可重复的静态负向合同，防止把已知项目名称或本机文件路径写进可交付 feature-owned 前端。

## Source Of Truth

- `docs/medical_monitoring_manual/医学监查子系统_PRD审阅与差距矩阵.md` P0-07 及 `frontend/AGENTS.md` 的 Source Registry boundary。
- Production feature-owned files under `frontend/src/features/medical-monitoring/` (exclude `*.test.*` and test fixtures from the scan).
- Existing project-switch/consumer-contract Node tests.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json` (read-only/blocked).

## Scope

- In scope: add a small Node static contract that scans feature-owned production frontend source for known project/company literals and local absolute/protocol paths; add adversarial positive/negative test cases and evidence.
- Out of scope: changing product runtime behavior, source registry configuration, backend/API/database, project adapters, real project files, browser/provider/service, B6/C14, P8 authority, Safety/PV, medical writing, or shared App/styles/main.

## Success Criteria

- The guard scans deterministic production file extensions and excludes test files so the contract itself can mention adversarial literals.
- Known project terms (`MG-K10`, `Ruxolitinib`, `MY008`, `MY009`) and company/path forms (`康哲`, `朗来`, `/Users/`, `/private/`, `file://`) fail the guard.
- Current feature-owned production source passes with no matches.
- The contract explicitly states that passing is only a static anti-overfitting guard, not real three-project generalization or clinical acceptance.
- Full medical-monitoring Node/static/build checks remain green; no runtime starts.

## Risk Boundaries

- This is a negative source guard; do not weaken it to accommodate an actual project-specific feature.
- Do not scan or copy real project data. No browser/API login/provider/service/real project/SQLite/CAS/B6/C14/P8/Safety-PV/medical-writing action.
- Do not change shared shell source or product files outside the feature contract test.
- Keep 8911/5174/8910/4173 stopped.

## Timeout Policy

- Direct Codex only; no delegated agent or external provider.
- If a forbidden token is found, record the exact production file and stop for review rather than silently deleting a possibly user-intended business label.

## Loop Log

- 2026-08-06 05:50:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-06 05:50:xx: Re-read P0-07 and current feature source; no known project/company/path literal was observed in production feature files. Chose a test-only guard as the smallest reversible action while real multi-project execution remains blocked.
