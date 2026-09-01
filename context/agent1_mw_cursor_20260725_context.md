# Task Context: agent1_mw_cursor_20260725

Created: 2026-07-25 17:19:29
Objective: Agent #1 Cursor temporary takeover: full project ledger/baseline, then medical writing production continuation per AGENT_1_CURSOR_HANDOFF_20260725 (restart 8911 N+1 patch, UC/CRSwNP/D017 v13 independent AI triage, Word gates, gap-matrix causal fixes).
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`
MODE note: Agent #1 (Cursor) is acting as temporary main venue; product AI remains deepseek-v4-pro only.

## Source Of Truth

- `records/handoffs/AGENT_1_CURSOR_HANDOFF_20260725.md`
- `/Users/smkzw/.codex/AGENTS.md`, `/Users/smkzw/.codex/RTK.md`, `/Users/smkzw/.codex/codex_agent_mode_overlay.md`
- Project `AGENTS.md`, `frontend/AGENTS.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/SOFT_PAUSE_RESUME.md` (2026-07-25 11:12 top block)
- Same slice `TASK_RECORD.md`, `CURRENT_GAP_MATRIX.md`, decision docs
- Live runtime 5174/8911, SQLite under `runtime/`, Word artifacts
- Agent #1 ledger: `records/handoffs/agent_1_cursor_20260725/`

## Scope

- In scope: medical writing subsystem production work; ledger; restart; v13 triage; Word; gap causal chain
- Out of scope: unrelated subsystem feature expansion; security audits; substituting Cursor for product AI; claiming go-live early

## Success Criteria

- Ledger 00–10 maintained with SHA/diff/evidence
- 8911 loads N+1 patch; RUX document-session <15s; AI readiness independent
- Fresh UC/CRSwNP/D017 v13 product AI runs accepted or LOOP-fixed with evidence
- Word native gates when available
- Gap matrix advanced with E-grades honest

## Risk Boundaries

- Non-git: never destructive reset; preserve user/prior agent edits
- No production AI impersonation by Agent #1
- Conference only after v13 freeze
- Writable product paths only after explicit repair LOOP with backups

## Timeout Policy

- Long AI triage: poll job status/files infrequently; do not nag models
- Hard waits per conference/execution overlay when dispatched

## Loop Log

- 2026-07-25 17:19:29: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-25 17:19–17:25: Baseline ledger + SHA snapshot + runtime DB backup; frontend down; backend pre-patch; next=restart.
