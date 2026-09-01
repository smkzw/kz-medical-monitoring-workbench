# Codex Execution Plan: mw_phase1_translation_exec_20260716

Objective: 为自身免疫疾病I期方案语料生成逐段可溯源的监管中文初译与humanizer-zh候选，并定位现有保真门禁失败；不得直接写入生产语料库

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 翻译并润色制剂桥接、洗脱/DDI依据和自适应制剂研究设计片段，逐项核对数字单位比较方向 | `runs/execution/mw_phase1_translation_exec_20260716/worker_01.md` |
| `worker_02` | 翻译并润色局部给药哨兵释放与受试者内治疗区域设计片段，保持给药顺序和随机化边界 | `runs/execution/mw_phase1_translation_exec_20260716/worker_02.md` |
| `worker_03` | 翻译并润色固定序列DDI分组与给药时间窗片段，严格保持日期、剂量、例外和漏服处理 | `runs/execution/mw_phase1_translation_exec_20260716/worker_03.md` |
| `worker_04` | 复核RNA SAD/MAD剂量递增、患者转换及漏服/减量片段的现有直连译文，给出保真修订候选和错误定位 | `runs/execution/mw_phase1_translation_exec_20260716/worker_04.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `grok-build` | `grok-4.5` | `runs/execution/mw_phase1_translation_exec_20260716/manager.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
