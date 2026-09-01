# Codex Main-Venue Plan: eligibility_review_frontend_20260711

Date: 2026-07-11
Objective: 设计并实现资格审核桌面三列审阅工作区，基于真实review API，保持IN/EX语义、证据与医学决策边界、项目隔离和无正式资格结论

## Task Decomposition

1. Buddy GLM independently audits clinical terminology, decision semantics, hierarchy and failure states.
2. Buddy Kimi independently produces a bounded patch proposal without writing production files.
3. Hermes `aishuo/MiniMax-M3` compares GLM and Kimi outputs and records conflicts.
4. Codex applies or rewrites accepted hunks, runs tests/build, and performs Chrome desktop QC.

## Source Packet

Use the authoritative files and boundaries in `context/eligibility_review_frontend_20260711_conference_context.md`.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_glm` | `buddy` | `glm-5.2` | `runs/conference/eligibility_review_frontend_20260711/participant_glm.md` |
| `participant_kimi` | `buddy` | `kimi-k2.7-code` | `runs/conference/eligibility_review_frontend_20260711/participant_kimi.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead_aishuo` | `aishuo` | `MiniMax-M3` | `runs/conference/eligibility_review_frontend_20260711/hermes_lead_aishuo.md` |

## Main-Venue DeepSeek Pro Review

- Agent/model: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro`.
- Reasoning: maximum configured Reasonix effort. Verify stdout/metrics when possible.
- Forbidden: Hermes, OpenCode Go, Hermes custom providers, or direct DeepSeek provider `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/eligibility_review_frontend_20260711/main_deepseek_pro.md`

## Timeout And Retry Tracking

Use the conference timeout policy. If a Buddy route terminally fails, retry once, then use the user-authorized OpenCode Go Qwen/Mimo fallback and record the substitution.

## Codex Verification Checklist

- Unit contracts and frontend production build.
- Fixed 1600x1000 and maximized desktop Chrome inspection.
- D001 and MY009 subject/criterion switching, stale-response harness and text-overflow checks.
- No path/hash/provider/formal-conclusion leakage.
