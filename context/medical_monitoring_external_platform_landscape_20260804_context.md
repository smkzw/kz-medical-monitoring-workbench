# Task Context: medical_monitoring_external_platform_landscape_20260804

Created: 2026-08-04 15:04:27
Objective: Bounded official-source landscape scan for AI medical monitoring/RBQM patterns; record applicability to the local workbench without adopting proprietary components or changing product code.
Task type: `competitive_intelligence`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Official public pages opened during this bounded scan: CluePoints RBQM, Veeva Clinical Data/DQS,
  Medidata Clinical Data Studio, CogniCRO/OneMedicalData, and the Chinese CFDI AI-clinical-trial survey.
- Local system authority: `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md`,
  current real-loop gate audits/manifests, and the existing monitoring source/UI contracts.
- Global/workspace `AGENTS.md` rules: proprietary platforms may inform the design, but no executable
  proprietary component is adopted; claims remain source-grounded and evidence/inference are separated.

## Scope

- In scope: a bounded English/Chinese official-source landscape scan; compare workflow patterns,
  evidence/traceability, data integration, risk detection, patient/site/study views, and human-action
  handoff; map patterns to the existing workbench and record design implications.
- Out of scope: vendor procurement, licensing/adoption, live demos, account creation, product login,
  external data upload, model/provider selection, product source changes, real-project reads, or a claim
  that marketing statements are independently validated.

## Success Criteria

- At least four authoritative platform/oversight sources are compared with direct URLs and claims limited
  to what their public materials state.
- Reusable patterns, non-transferable vendor claims, and local project gaps are separated.
- A concrete design decision record identifies what to preserve, what to add later, and what not to adopt;
  no product or runtime mutation occurs.
- Review and metrics files pass `review-gate` without TODO placeholders.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 15:04:27: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Completed two bounded web passes and opened official CluePoints, Medidata, Veeva and CFDI
  pages plus public descriptions for CogniCRO and ComTrial. Wrote the comparison/design record; no
  proprietary tool was adopted and no local product/runtime state changed.
