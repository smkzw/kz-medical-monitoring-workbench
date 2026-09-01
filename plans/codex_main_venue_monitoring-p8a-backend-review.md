# Codex Main-Venue Plan: monitoring-p8a-backend-review

Date: 2026-07-29
Objective: 独立审阅 P8-A 后端权威风险分类与 Checklist 查询实现，寻找分类边界、兼容降级、稳定分页、API 关闭失败及测试遗漏；只读，不修改文件

## Task Decomposition

1. Have two participants independently inspect the full P8-A backend contract
   and current implementation without editing.
2. Have the chair adjudicate conflicts against source and tests.
3. Let Codex accept, reject, or repair findings and rerun decisive validation.

## Source Packet

- P8-A context and prior P8 gap review.
- Taxonomy, repository, summary/router, rule and AI bridges.
- RUX, MG-K10, and MY009 adapter paths.
- Taxonomy, repository, API, bridge, assembly, and adapter tests.
- Observed pre-conference test evidence recorded in conference context.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/monitoring-p8a-backend-review/general_aishuo_cms.md` |
| `general_codebuddy_deepseek_pro` | `codebuddy-cli` | `deepseek-v4-pro` | `runs/conference/monitoring-p8a-backend-review/general_codebuddy_deepseek_pro.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/monitoring-p8a-backend-review/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- All three roles completed one primary pass without timeout, retry, or fallback.
- Participant durations: 250.549 s and 139.365 s.
- Chair duration: 410.755 s.
- All outputs were available and reviewed before Codex final acceptance.

## Codex Verification Checklist

- Confirm classification never consumes display text.
- Confirm legacy degradation and lineage.
- Confirm Safety/PV remains additive.
- Confirm CM versus EX/EC/DA/IP across every persistence path.
- Confirm seven closed query/sort fields, invalid-input rejection, deterministic
  ties, and snapshot-pinned pagination.
- Correct reviewer factual errors against current source.
- Repair accepted findings and rerun focused plus full monitoring tests.
