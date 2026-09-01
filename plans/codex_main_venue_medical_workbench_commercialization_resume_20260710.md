# Codex Main-Venue Plan: medical_workbench_commercialization_resume_20260710

Date: 2026-07-10
Objective: 恢复并持续构建康哲AI全流程医学经理工作台，覆盖全部医学相关子系统，完成跨项目、独立AI、逐功能商业化验收

## Task Decomposition

1. Re-baseline requirements and maturity. Produce a traceable matrix from each requirement to current code, current evidence, gap, and next proof.
2. Inventory real-study inputs. Select at least two original-source projects per subsystem and record data-shape differences before implementation.
3. Harden shared contracts. Remove project-specific routing assumptions, externalize private source configuration, version schemas/prompts, and prove project isolation/restart recovery.
4. Implement the cross-project critical paths in parallel-safe slices:
   - Evidence and PICOS: real evidence catalog, regulatory/competitor source ingestion, decision questions, and writing handoff.
   - Eligibility: raw protocol to IN/EX rules, raw subject bundle to evidence map, AI suggestion, human review, approval.
   - Monitoring: raw protocol/listing intake, incremental batch diff, risk lifecycle, Subject Timeline, Patient Profile, Query and approval.
   - TFL: SDTM/ADaM manifest, validated derivation, T/F/L review, provenance, and writing handoff.
   - Writing: real document structure, rich editor, AI revision threads, accept/reject/rewrite, pending-medical-approval output, approval handoff.
   - Safety/PV: safety source intake, case/signal medical review, PV boundary, approval, and DSUR/IB/CTD handoff.
5. Productize the total dashboard and approval center: dense project overview, explicit unread state, filtering/sorting/paging, stable links, audit trail, and cross-module state consistency.
6. Run the commercial acceptance loop: two-plus real studies per subsystem, 3-5 subject samples where applicable, every control and hidden state, independent provider runs, API/browser/restart/security checks, third-party model review, fixes, and rerun.

Exit rule: no task is complete because a page renders or a unit test passes. Completion requires the task's real-source, cross-project, independent-AI, browser, audit, and restart evidence.

## Source Packet

- `context/medical_workbench_commercialization_resume_20260710_conference_context.md`
- `records/soft_pause_20260709_1105_lossless_full_backup/USER_REQUIREMENTS_FULL_LEDGER.md`
- `records/soft_pause_20260709_1105_lossless_full_backup/FUTURE_EXECUTION_PLAN.md`
- `logs/SOFT_PAUSE_20260709_1324_CST.md`
- `README.md` and `KNOWN_ISSUES.md`
- `runs/subagents/20260710_commercialization_baseline/*.md`

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/medical_workbench_commercialization_resume_20260710/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_workbench_commercialization_resume_20260710/participant_mimo.md` |
| `participant_ds_flash` | `reasonix-cli` | `deepseek-v4-flash` | `runs/conference/medical_workbench_commercialization_resume_20260710/participant_ds_flash.md` |
| `participant_buddy_minimax` | `buddy` | `minimax-m3` | `runs/conference/medical_workbench_commercialization_resume_20260710/participant_buddy_minimax.md` |
| `participant_glm52_product` | `buddy` | `glm-5.2` | `runs/conference/medical_workbench_commercialization_resume_20260710/participant_glm52_product.md` |
| `participant_kimi_frontend` | `buddy` | `kimi-k2.7-code` | `runs/conference/medical_workbench_commercialization_resume_20260710/participant_kimi_frontend.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/medical_workbench_commercialization_resume_20260710/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Agent/model: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro`.
- Reasoning: maximum configured Reasonix effort. Verify stdout/metrics when possible.
- Forbidden: Hermes, OpenCode Go, Hermes custom providers, or direct DeepSeek provider `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/medical_workbench_commercialization_resume_20260710/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Record start/end time, initialized provider/model markers, API-call completion, pending/failed/incorporated status, retry reason, and whether late outputs were used.
- Buddy GLM/Kimi/Minimax prompts stay compact. On terminal failure, preserve stdout and retry once with a smaller packet; then use the approved qwen/mimo fallback without erasing the failure record.
- DeepSeek V4 routes follow the mandatory Reasonix governance route in this workspace; their model output still serves the requested Chinese/clinical review role.

## Codex Verification Checklist

- [x] Baseline reports exist and contain current file evidence rather than old review assertions.
- [x] At least three independent model outputs are complete before a material next-slice decision.
- [x] Conference prompts pass preflight and contain no `TODO` placeholders.
- [x] Participant outputs remain advisory and do not claim browser, medical, regulatory, or production authority.
- [x] Codex verified current tests, runtime, browser flows, screenshots, and real-source data directly for the canonical-project-context slice.
- [x] Every accepted finding is mapped to the current slice, an explicit deferment, or the recovery plan.
- [x] System/subsystem logs and the current-slice verification matrix are updated before manual soft pause.

Closure evidence: `reviews/codex_conference_medical_workbench_commercialization_resume_20260710_review.md` and `records/active_slices/canonical_project_context_20260710/`.
