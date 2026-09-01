# Codex Main-Venue Plan: monitoring_source_revision_gate_20260713

Date: 2026-07-13
Objective: 审阅并收敛医学监查真实项目source revision绑定、全目录drilldown和真实项目增量上传服务端失败关闭方案

## Task Decomposition

1. Define a shared, cached content-revision primitive for listing+protocol pairs.
2. Bind adapter cache state, catalogs, drilldowns, risks and inbox CAS to that revision.
3. Fix MY009 missing-DM identity fallback without inferring demographics.
4. Fail closed on real-project generic monitoring intake execution while preserving source registration/content validation.
5. Prove 267/267 drilldowns and stale-token rejection with synthetic mutation fixtures.

## Source Packet

Use only the bounded files listed in the conference context. Real files remain read-only; mutation tests must use temporary synthetic copies.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/monitoring_source_revision_gate_20260713/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/monitoring_source_revision_gate_20260713/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/monitoring_source_revision_gate_20260713/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/monitoring_source_revision_gate_20260713/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Participants start after prompt preflight. Chair starts only after available participant outputs are complete or explicitly excluded.

## Codex Verification Checklist

- Shared token is content-derived and path-free.
- Real-project adapters reload or fail closed on changed revision.
- 267/267 real drilldowns pass.
- Generic intake cannot run against RUX/MY009.
- CM/IP boundary and existing demo behavior remain intact.
- Focused, affected and full regression pass; desktop browser verification follows any UI-visible behavior change.
