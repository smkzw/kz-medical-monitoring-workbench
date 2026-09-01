# Codex Main-Venue Plan: medical_writing_corpus_quality_20260716

Date: 2026-07-16
Objective: 审阅公司中文临床试验方案语料库的根本性冲突、章节级优先级和取长补短策略，并提出可回归的语料治理规则

## Task Decomposition

1. Preserve immutable v1 and run a deterministic whole-corpus audit.
2. Challenge global source priority using object-level/M11/project-fit cases.
3. Have two independent participants review conflict classes and retrieval gates.
4. Have Grok Build chair compare the evidence and identify missing safeguards.
5. Codex accepts only recommendations supported by source/code/test evidence, then applies narrow changes and reruns regressions.

## Source Packet

- Prior audit and authority matrix.
- Compact whole-corpus audit summary, 9-source manifest and 42 golden-query results.
- Current policy, retrieval implementation and regression tests.
- No production writes and no direct edits to the immutable corpus snapshot.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_minimax` | `aishuo` | `MiniMax-M3` | `runs/conference/medical_writing_corpus_quality_20260716/general_aishuo_minimax.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/medical_writing_corpus_quality_20260716/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/medical_writing_corpus_quality_20260716/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Participants start independently after prompt preflight.
- Chair starts after participant outputs are available so it can compare them.
- One complete pass per role; Codex requests same-session follow-up only if the first pass lacks concrete evidence or implementable detail.

## Codex Verification Checklist

- [x] Immutable snapshot hash verified by service.
- [x] Whole-corpus deterministic audit generated.
- [x] 42 golden queries pass after two retrieval defects were fixed.
- [ ] Participant outputs reviewed for evidence and unsupported claims.
- [ ] Chair comparison reviewed; any consensus challenged against code and source evidence.
- [ ] Focused and broader medical-writing tests pass.
- [ ] Task records updated with decisions, failures and remaining v2-governance work.
