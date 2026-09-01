# Codex Main-Venue Plan: medical_writing_sites_feasibility_20260714

Date: 2026-07-14
Objective: 从医学写作生产系统、公司内网私有化和临床数据治理角度，复核OpenAI Sites用于康哲AI医学经理工作台上线的适用边界、迁移成本、混合部署方案与阶段性建议

## Task Decomposition

1. Verify current workbench runtime boundaries against official local Sites contracts.
2. Separate deployable frontend/demo surfaces from Python, SQLite, file, OCR and AI-service dependencies.
3. Assess four routes: local/private only, Sites demo, Sites frontend plus private API, full Worker/D1/R2 migration.
4. Test each route against clinical-data governance, identity/RBAC, auditability, document processing, long tasks, portability and delivery priority.
5. Produce a staged recommendation and explicit production prerequisites; do not deploy.

## Source Packet

- Latest global `AGENTS.md` and Hermes `SOUL.md`.
- Medical-writing task record, source manifest and Codex Sites feasibility audit.
- Local official Sites building, hosting, persistence and authentication skills.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_sites_feasibility_20260714/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/medical_writing_sites_feasibility_20260714/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_sites_feasibility_20260714/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_sites_feasibility_20260714/general_chair_glm.md` |
| `general_chair_qwen_fallback` | `opencode-go` | `qwen3.7-plus` | `runs/conference/medical_writing_sites_feasibility_20260714/general_chair_qwen_fallback.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Record per-role session ID, all three round durations, fallback, terminal errors and whether late outputs were incorporated. Slow output remains pending until the documented failure threshold.

- Primary GLM chair: terminal before resumable session; excluded as chair output.
- Replacement route: OpenCode Go qwen3.7-plus, explicitly activated under the user's GLM-failure fallback instruction.

## Codex Verification Checklist

- Verify all three participants and chair use the assigned provider/model and one stable session per role.
- Reject any claim based on unlisted code or web research.
- Compare recommendations to the current absence of `.openai/hosting.json`, Vite frontend, Python FastAPI, SQLite/local files and local/independent gateways recorded by Codex.
- Verify connector availability separately; no production Site creation or deployment.
- Ensure final advice preserves medical-writing P0 and the local/private deployment path.
