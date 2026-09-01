# Codex Main-Venue Plan: mm_r8_gate2_synthetic_runtime_review_20260831

Date: TODO
Objective: 以全新审阅上下文对 R8 G2 synthetic runtime 实现做开放式代码和合同一致性审阅。重点判定：纯内存 source_access_profile 是否真正满足目标 macOS synthetic shadow-root；三模块 canonicalization 是否发生规范漂移；source/output manifest 与 source-access 证据是否实际绑定；lifecycle 是否证明依赖闭包和一键入口而不是自证模拟。只读审阅，不修改文件，不访问真实项目，不启动模型、服务或浏览器。按 P0-P4 给出可定位发现和 ACCEPT/REVISE 结论。

## Task Decomposition

TODO

## Source Packet

TODO

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `cms-router` | `minimax-m3` | `runs/conference/mm_r8_gate2_synthetic_runtime_review_20260831/general_single_object.md` |

## Conference Panel Coordination

- Preferred browser advisory chair: `chatgpt-web-pro-advisory` via `codex-with-chatgpt` (`Pro` / `GPT-5.6 Sol`). Codex remains the formal packet chair and final authority; the browser role is not dispatched through the runner.
- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

TODO: Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.

## Codex Verification Checklist

TODO
