# Codex Main-Venue Plan: medical_workbench_lower_half_gap_baseline_20260708

Date: 2026-07-08 CST
Objective: Audit the AI Medical Manager Workbench lower-half commercialization baseline, verify subsystem gaps against current code/logs/real-data evidence and recommend the next implementable product slice with risk/benefit record.

## Task Decomposition

- Build a current-state baseline from workbench source, logs, visual QC, conference metrics, and external product/open-source reference checks.
- Run independent read-only SubAgent audits for backend/API, frontend/QC, and record closure.
- Convene Hermes conference to adjudicate the next implementable product slice across three candidate routes:
  - 医学写作独立AI Gateway最小闭环.
  - RUX医学监查真实风险处置闭环.
  - TFL真实数据审阅 -> 独立AI解释 -> 医学写作引用候选 -> 审批阻断.
- Codex reviews Hermes/DeepSeek outputs, resolves conflicts, and chooses one implementation slice.
- Before code landing, Codex must create/adjust tests first and keep output boundaries explicit.

## Source Packet

- Primary baseline and subagent audits:
  - `records/commercialization_audit_20260708/medical_workbench_current_state_and_gap_baseline.md`
  - `records/commercialization_audit_20260708/subagent_backend_api_audit.md`
  - `records/commercialization_audit_20260708/subagent_frontend_interaction_audit.md`
  - `records/commercialization_audit_20260708/subagent_records_closure_audit.md`
- Scope and instructions:
  - `README.md`
  - `frontend/AGENTS.md`
  - `KNOWN_ISSUES.md`
  - `logs/system_build_log.md`
  - `logs/subsystems/*.md`
- Backend/frontend surfaces listed in `context/medical_workbench_lower_half_gap_baseline_20260708_conference_context.md`.
- No original real-project folder writes are allowed in this review.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/medical_workbench_lower_half_gap_baseline_20260708/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_workbench_lower_half_gap_baseline_20260708/participant_mimo.md` |
| `participant_ds_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/medical_workbench_lower_half_gap_baseline_20260708/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/medical_workbench_lower_half_gap_baseline_20260708/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Provider/model: DeepSeek supplier `deepseek-v4-pro`.
- Reasoning: maximum available effort. Verify logs/usage when possible.
- Forbidden: OpenCode Go `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/medical_workbench_lower_half_gap_baseline_20260708/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used in `metrics/medical_workbench_lower_half_gap_baseline_20260708_conference_metrics.md`.
- If Buddy GLM/Kimi routes are unavailable in this conference, use the current default conference participants plus the user-approved fallback principle already captured in prior metrics.

## Codex Verification Checklist

- Preflight all prompts after adding source packet.
- Verify each model wrote exactly one output file.
- Review output boundary compliance before using recommendations.
- Run no code edits from Hermes automatically.
- After selection, Codex must write tests/QC for the chosen slice before claiming implementation.
- Keep review files free of TODO before review-gate.
