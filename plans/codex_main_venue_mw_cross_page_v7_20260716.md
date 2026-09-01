# Codex Main-Venue Plan: mw_cross_page_v7_20260716

Date: 2026-07-16
Objective: 审查医学写作竞品Protocol跨页语义片段合并v7、可追溯provenance、结构审核门和双真实方案验证设计；只读审查，不修改生产文件

## Task Decomposition

1. 建立原始PDF block的typed provenance和跨页合并理由模型，保证旧抽取JSON可读。
2. 将提取器升级为v7：先识别重复页边元素，再做保守跨页阅读顺序修复，最后进行M11映射。
3. 把当前内容校验与当前抽取结构审核统一为AI前门禁，覆盖单片段translate/revise和批量preview/create/claim。
4. 用合成正反例锁定规则；以PNH及NCT04157335两个真实Protocol验证同类断句和保密叠加边界。
5. 重启隔离后端，执行聚焦/广泛测试、真实API、审计和桌面浏览器回归；Codex结合会商输出作最终裁决并更新任务记录。

## Source Packet

- `context/mw_cross_page_v7_20260716_conference_context.md`中的只读清单是唯一允许的source packet。
- 参与者独立审查合并规则、误合并边界、provenance、失效与门禁，不做源码修改或最终临床/监管裁决。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/mw_cross_page_v7_20260716/general_aishuo_minimax.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_cross_page_v7_20260716/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_cross_page_v7_20260716/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

TODO: Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.

## Codex Verification Checklist

- 合成正例和至少五类负例。
- PNH、NCT04157335两个真实Protocol跨页目标句。
- 当前内容校验、当前抽取版本、当前结构批准三者AI前失败关闭。
- 新抽取导致旧翻译和brief失效，无自动医学批准或语料准入。
- 聚焦、广泛后端测试和隔离浏览器回归。
