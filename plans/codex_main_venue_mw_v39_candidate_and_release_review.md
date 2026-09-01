# Codex Main-Venue Plan: mw_v39_candidate_and_release_review

Date: TODO
Objective: 以中国创新药临床试验医学撰写经理视角，复核真实AD竞品方案翻译后语料、3至5个写作候选的事实等价性与监管中文质量，并在医学写作工作台真实运行时完成候选选用、编辑、版本化写入、浏览器交互及DOCX导出的发布前多视角验收；Hy-MT2独占正文翻译，DeepSeek仅执行章节识别拆分、译后整合衔接QC和语料筛选等上层任务。

## Task Decomposition

TODO

## Source Packet

TODO

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_v39_candidate_and_release_review/general_aishuo_cms.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_v39_candidate_and_release_review/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_v39_candidate_and_release_review/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

TODO: Record start/end time, pending/failed/incorporated status, retry reason, and whether late outputs were used.

## Codex Verification Checklist

TODO
