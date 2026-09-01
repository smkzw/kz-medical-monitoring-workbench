# Task Context: monitoring_p10_identity_boundary_corrective_20260730

Created: 2026-07-30 16:35:02
Objective: 修复医学监查非试验治疗身份自证、规则身份缺失/混合、影子包身份与project-effective执行前漂移，并通过聚焦及相邻回归
Task type: `finite_code_task`
Risk: `high`
Selected agent route: requested `aishuo` / `cms-model` / `high`; effective
fallback `kimi-code` / `kimi-code/k3-256k` / `high` because the aishuo
participant terminated twice with `stop_reason=error` and no usable report in
the immediately preceding gate.

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `context/monitoring_p10_release_chain_mapping_gate_20260730_conference_context.md`
- `runs/conference/monitoring_p10_release_chain_mapping_gate_20260730/general_kimi_k3_fallback.md`
- `runs/conference/monitoring_p10_release_chain_mapping_gate_20260730/general_codebuddy_deepseek_pro.md`
- `runs/conference/monitoring_p10_release_chain_mapping_gate_20260730/general_chair_pi_qwen38.md`
- Current medical-monitoring source and tests named by those reports.
- Current filesystem is authoritative. A medical-writing session is concurrently
  editing shared files; reread any shared file immediately before a minimal patch.

## Scope

- In scope: four confirmed corrective findings only:
  1. project-specific non-IP/prior/background/rescue treatment must not
     self-anchor as investigational product;
  2. every confirmed/publishable/executable rule must carry a complete
     immutable 4-field mapping/capability identity, and packs must not hide an
     empty member identity;
  3. shadow preparation and confirmation must unify all four identity fields
     and compare the frozen batch effective-capabilities hash;
  4. project-effective daily runs must revalidate the frozen rule identity
     immediately before first execution.
- In scope: trace and close the legacy confirm endpoint and manual trusted
  shadow-run route if either bypasses those contracts.
- In scope: focused tests, all medical-monitoring regression, adjacent
  writing contract/import tests, compile/lint/build as applicable.
- Out of scope: real runtime writes, backend start, UI redesign, unrelated
  refactors, security/privacy review, medical-writing business changes.

## Success Criteria

- The executed PM/prior-medication counterexample cannot activate
  `ip_exposure_adherence` as READY without independently verifiable treatment
  identity.
- A legacy/partial/empty identity rule cannot become confirmed, enter a
  publishable pack, pass shadow, or make project-effective readiness appear
  valid.
- A pack with any mixed value among mapping revision, mapping-content hash,
  capability-manifest hash, or effective-capabilities hash fails before a
  provisional sample set or trusted shadow confirmation is stored.
- Record-applicability behavior remains frozen and passing; fresh-load lineage
  tests remain passing.
- Adoption remains the single medical rule decision. No second “医学批准” action
  or wording is introduced.
- All focused and all medical-monitoring tests pass; adjacent writing imports/
  contracts show no regression attributable to this slice.
- 8911 remains stopped and real runtime databases remain unchanged.

## Risk Boundaries

- Authorized writable paths are medical-monitoring implementation/test files
  in this workspace and the runner-owned report only. A minimal edit in
  `services/api/app/main.py` is allowed only inside
  `_current_monitoring_rule_runtime` after rereading the current function.
- Do not overwrite or reformat concurrent writing code in `main.py`,
  `frontend/src/App.jsx`, or shared styles. Prefer monitoring-owned modules.
- Read-only `mode=ro/query_only` projection of the medical-monitoring runtime
  database is allowed solely to determine whether empty/mixed published
  identities already exist. Do not mutate it.
- Do not start 8911 or write real runtime state.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-30 16:35:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-30: Conference gate rejected release with two P1 and two P2
  identity/treatment-boundary findings; false fresh-load and record-applicability
  findings were explicitly rejected.
