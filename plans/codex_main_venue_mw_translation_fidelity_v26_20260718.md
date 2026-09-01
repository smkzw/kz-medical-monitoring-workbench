# Codex Main-Venue Plan: mw_translation_fidelity_v26_20260718

Date: 2026-07-19
Objective: 审阅AD竞品方案真实Hy-MT2翻译v26的ch07/ch09忠实度阻断，区分真实错译与门禁误报，在Hy-MT2独占正文翻译且DeepSeek只做上层识别/QC/语料选取的边界下提出最小可验证修复

## Task Decomposition

1. Independently reconstruct ch07 and ch09 source/Hy pairs from the immutable
   v26 runtime and classify every failure.
2. Audit Flash non-authoring QC and deterministic fidelity checks for false
   positives, missing localization and unsafe bypass routes.
3. Compare independent findings, resolve disagreements and define the smallest
   patch/test set. No participant edits production files.
4. Codex implements only evidence-supported changes, runs focused and broad
   tests, performs real Hy probes and reruns isolated AD E2E.

## Source Packet

- Boundary and requirements:
  `records/USER_REQUIREMENTS_CURRENT_20260718.md`
- Conference context:
  `context/mw_translation_fidelity_v26_20260718_conference_context.md`
- v26 report:
  `runs/execution/mw_cross_indication_reference_release_gate_20260718/cross_indication_e2e_run_v26_ad/AD/lane_report.json`
- Read-only v26 evidence DB snapshot:
  `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/v26_writing_reference_readonly.sqlite3`
- Current implementation and relevant tests listed in the conference context.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_aishuo_cms` | `aishuo` | `cms-model` | `runs/conference/mw_translation_fidelity_v26_20260718/general_aishuo_cms.md` |
| `general_opencode_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_translation_fidelity_v26_20260718/general_opencode_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_grok45` | `grok-build` | `grok-4.5` | `runs/conference/mw_translation_fidelity_v26_20260718/general_chair_grok45.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Participants run in parallel under the guard-generated 128-turn budget and
  120-minute hard wait. A slow route remains pending.
- Chair starts only after both participant reports are available or a route is
  terminally failed under the global policy.
- Record provider/model/session/pass/fallback and whether each output was
  incorporated in the metrics and main review.

## Codex Verification Checklist

- [ ] Each failure is tied to exact source and Hy text.
- [ ] Real defects remain blocked; false positives are fixed narrowly.
- [ ] No DeepSeek text can enter final body.
- [ ] New adversarial tests fail before and pass after the patch.
- [ ] Relevant regression suite passes.
- [ ] Real Hy target probes pass deterministic gates.
- [ ] Fresh isolated AD E2E passes or yields a newly localized valid blocker.
- [ ] Task record captures evidence, failed attempts and next safe action.
