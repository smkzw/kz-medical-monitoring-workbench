# 阶段 D：真实模型 AE/MH 纵切

## Goal

MG-K10-SAR AE/MH 漏报端到端真实模型 Run、看板、Journey、来源与 Query。

## Requirements

- Use MG-K10-SAR and a real ExecutionProfile with the embedded harness defaulting to `zhipu-coding-plan/GLM-5.3-flash:high`.
- Complete facts → AE/MH risk candidate → counter-evidence → dashboard → Journey anchor → source drill-down → Query draft.
- Compare against existing Profile/Timeline/under-reporting deliverables as reference evidence.
- Verify background execution, real manifest progress, and one interrupted-run recovery.

## Acceptance Criteria

- [ ] User completes one real run through Query export and confirms the domain is usable.
- [ ] Defects are fixed and the affected path regresses cleanly.
- [ ] Independent review and user confirmation complete; tag `mm-first-real-run` exists.

## Constraints

- Preserve candidate/fact separation and source provenance; model output never becomes accepted fact by confidence alone.
