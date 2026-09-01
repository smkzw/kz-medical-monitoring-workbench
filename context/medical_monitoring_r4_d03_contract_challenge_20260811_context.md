# Task Context: medical_monitoring_r4_d03_contract_challenge_20260811

Created: 2026-08-11 20:27:14
Objective: 独立挑战 FROZEN_R4_D03_CONTRACT_V1 的研究药暴露、依从性分母、治疗角色、处置关系、Query 与 Patient Journey 边界；仅审阅，不修改文件
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/medical_monitoring_r4_d03_ip_slice_contract_v1_20260811.md` — artifact under review, SHA-256 `859b9fd340cdce18d12d34dbd357f07375b886c76d4c6d21f50de80d18ab339c`.
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` — frozen common/D03 authority.
- `reviews/medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md` — accepted adjacent contract pattern, not D03 truth.
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py`, `coverage.py`, `lifecycle.py`, `cm.py`, `cm_projection.py` and their tests — currently accepted reusable surface.
- `context/medical_monitoring_r4_d03_ip_contract_20260811_context.md` — recovery boundary and success criteria.
- Codex external verification summary: CDISC distinguishes protocol-defined treatment in EC/EX from other treatments in CM and preserves planned versus actual arm distinctions; FDA June 2026 Study Data Technical Conformance Guide is current regulatory technical context. This review must not invent regulatory requirements beyond the frozen local contract.
- Codex implementation-pattern summary: `vis-timeline` supports point/range items and zoom/pan under Apache-2.0 OR MIT; Apache ECharts supports interactive customizable browser visualization under Apache-2.0. No library is adopted in D03; projection must remain renderer-neutral.
- Skill-derived constraints already accepted by Codex: actual medication days are not treatment span/DOT; overlapping EX intervals cannot be naively summed; source row/rule/calculation/status/match key must remain traceable; Patient Profile/timeline is a view, not source authority.

## Scope

- In scope: independently challenge completeness, internal consistency and implementability of the frozen D03 contract before code changes.
- In scope: treatment-role/phase identity, expected-set construction, planned-versus-actual exposure, actual medication days versus treatment span, overlapping intervals, adherence numerator/denominator/unit/window/threshold, allowed actions, exact cross-domain links, Query wording, lifecycle and renderer-neutral Patient Journey payload.
- Out of scope: editing any file, implementing code, running real projects, starting services, selecting a final frontend library, security design/testing, clinical or regulatory acceptance.

## Success Criteria

- Produce a prioritized list of blocking and nonblocking findings, each tied to an exact contract section and a concrete amendment or test.
- Explicitly test the contract against false-positive/false-negative cases: one missing row, overlapping exposure intervals, incomplete denominator, threshold equality, planned pause, blinded treatment role, wrong subject/site/episode link, partial dates and rule/algorithm version change.
- State whether the six positive subtypes cover the frozen D03 matrix without collapsing event types or formal PD status.
- End with `ACCEPT` only if implementation can proceed without inventing semantics; otherwise `REVISE` and identify the minimum required amendments.

## Risk Boundaries

- Read-only review. Do not modify the contract, source, tests, prompt, context, review or run artifacts.
- Do not inspect real-project data or any medical-writing path.
- Do not evaluate system security or propose product/service expansion.
- Do not treat model opinion as clinical truth or formal PD determination.
- Keep user-facing language Chinese-native and keep engineering labels out of audience-facing recommendations.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- A provider catalog/auth/transport preflight is diagnostic, not a live capability verdict: timeout, auth refresh failure, or malformed probe output must be recorded and followed by one real route attempt. Only a missing executable or explicit invalid/retired/unlisted model may stop before that attempt.

## Loop Log

- 2026-08-11 20:27:14: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-11 20:30: Codex populated the current-source, read-only, no-real-project contract and recorded the current day-route manifest; no predecessor session exists to resume.
- 2026-08-11 20:33: Native Codex subAgent probe explicitly rejected `gpt-5.6-luna` (`Available models: gpt-5.6-sol, gpt-5.6-terra`) before creating a child handle. Per global routing, use the labeled Luna CLI compatibility fallback; do not substitute Sol/Terra.
