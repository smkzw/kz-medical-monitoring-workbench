# Codex Main-Venue Plan: full_medical_workbench_commercialization_20260708

Date: 2026-07-08 CST
Objective: 推进AI医学经理工作台所有医学相关子系统的商业化落地：基于当前代码、真实项目文件、外部商业产品和开源标准调研，确定下一批P0实现切片并执行闭环验证

## Task Decomposition

1. Establish current-state baseline from the workbench code, tests, logs, metrics, reviews, visual QC records, and real project material inventory.
2. Build a subsystem commercialization gap matrix for:
   - 证据调研与方案设计
   - 入排审核
   - 医学监查
   - 数据分析与TFL
   - 医学写作
   - 安全信号与PV协同
   - 项目总看板
   - 审批中心
3. Compare current implementation against external commercial/open-source/standards patterns recorded in `research/commercial_and_open_source_research_20260708.md`.
4. Select the next P0 implementation slice by impact on real raw-source workflow, not by easiest UI work.
5. Implement only the selected slice after Codex reviews current code and available subagent/Hermes feedback.
6. Verify with unit tests, frontend build, browser QC, and real project input smoke where available.
7. Record decisions, provider failures, risks, and verification in `logs/system_build_log.md` and subsystem logs.

## Source Packet

- Current workbench source:
  - `README.md`
  - `services/api/app/*.py`
  - `packages/contracts/workbench_contracts/*.py`
  - `frontend/AGENTS.md`
  - `frontend/src/App.jsx`
  - `frontend/src/styles.css`
  - `frontend/tests/*.mjs`
  - `tests/*.py`
- Current records:
  - `logs/system_build_log.md`
  - `logs/subsystems/module_scope_log.md`
  - `reviews/*.md`
  - `metrics/*.md`
  - `records/visual_qc_20260707/*.json`
  - `records/visual_qc_20260708/*/*.json`
- External design/research notes:
  - `research/commercial_and_open_source_research_20260708.md`
- Real project material roots are user-authorized read-only:
  - `/Users/smkzw/Documents/康哲项目资料`
  - `/Users/smkzw/Documents/朗来项目资料`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/full_medical_workbench_commercialization_20260708/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/full_medical_workbench_commercialization_20260708/participant_mimo.md` |
| `participant_ds_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/full_medical_workbench_commercialization_20260708/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/full_medical_workbench_commercialization_20260708/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Provider/model: DeepSeek supplier `deepseek-v4-pro`.
- Reasoning: maximum available effort. Verify logs/usage when possible.
- Forbidden: OpenCode Go `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/full_medical_workbench_commercialization_20260708/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Current Hermes CLI status: DeepSeek configured; GLM/Kimi/MiniMax buddy providers not configured in CLI. Record unavailable routes honestly and do not substitute silently.
- Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.

## Codex Verification Checklist

- API module catalog contains only business-key medical related modules; no lifecycle numbering or non-medical standalone modules.
- Selected implementation slice has real raw-source inputs or an explicit blocked-provider state.
- Independent AI boundary is preserved: no Codex fallback for semantic AI extraction/generation.
- Public API and frontend do not leak local absolute paths.
- UI does not claim automatic final medical approval or regulatory/PV readiness.
- Unit tests and browser QC cover the selected slice and adjacent surfaces.
- Logs and metrics are updated with exact commands and results.
