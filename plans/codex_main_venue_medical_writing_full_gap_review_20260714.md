# Codex Main-Venue Plan: medical_writing_full_gap_review_20260714

Date: 2026-07-14
Objective: 从中国创新药医学经理用户视角，审阅现有医学写作子系统与两阶段项目向导、PICOS设计、ClinicalTrials.gov竞品语料准备、中文ICH M11全章节模块化写作、真实表格/研究摘要/矢量流程图/量表/目录索引之间的差距，提出不推翻现有系统的最优产品路径和需用户决策项

## Task Decomposition

1. Re-anchor the current runtime, task record and stable medical-writing endpoint.
2. Audit current frontend, contracts, services, tests and DOCX object behavior.
3. Parse current Chinese M11 materials into canonical chapters and interaction/object boundaries.
4. Review official standards and domestic-first commercial patterns without treating marketing as implementation evidence.
5. Ask each participant to challenge the target journey, state machine, object boundaries and implementation order from a Chinese medical-manager perspective.
6. Ask the GLM chair to compare participant contradictions and return decisions, not a consensus summary.
7. Codex verifies the real browser, writes the final gap matrix/backlog and produces the clickable decision page.

## Source Packet

- `records/active_slices/medical_writing_full_gap_review_20260714/TASK_RECORD.md`
- `records/active_slices/medical_writing_full_gap_review_20260714/SOURCE_MANIFEST.md`
- `records/active_slices/medical_writing_full_gap_review_20260714/M11_TARGET_MODEL.md`
- `records/active_slices/medical_writing_full_gap_review_20260714/source/ich_m11_cn_20250114_extracted.txt`
- `research/medical_writing_gap_20260714/sources/CDE_M11_template_cn_20260612.txt`
- Current code paths named in the task record, read-only.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_full_gap_review_20260714/general_aishuo_minimax.md` |
| `general_buddy_deepseek` | `buddy` | `deepseek-v4-pro` | `runs/conference/medical_writing_full_gap_review_20260714/general_buddy_deepseek.md` |
| `general_opencode_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_full_gap_review_20260714/general_opencode_mimo.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_glm` | `buddy` | `glm-5.2` | `runs/conference/medical_writing_full_gap_review_20260714/general_chair_glm.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Participant soft wait: 20 minutes; large-task wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Slow runs stay pending. Terminal error, exhausted provider after controlled retry, empty/truncated retry output, or no progress after the hard wait plus one retry may be marked failed.
- Record provider/model, same-session continuation evidence, all three round timestamps, fallback and final inclusion status in metrics/review files.

## Codex Verification Checklist

- Current medical-writing endpoint remains reachable after analysis/prototype work.
- Code-level claims cite exact files/lines and are checked against tests.
- M11 claims distinguish user draft, ICH Step 4 and CDE 2026 Chinese materials.
- Commercial-product claims stay within public evidence.
- Participant outputs completed three rounds in the same session or have an explicit failure record.
- Final decision page uses the existing workbench visual language, works at desktop target viewports and persists/exports selections.
- No production feature is implemented before unresolved architecture choices are surfaced to the user.
