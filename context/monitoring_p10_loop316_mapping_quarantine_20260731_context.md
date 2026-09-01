# Task Context: monitoring_p10_loop316_mapping_quarantine_20260731

Created: 2026-07-31 23:28:11
Objective: 对 RUX V16 mapping 审计的 IP 多动作角色折叠与不完整标准编码链实施候选保留、草稿失败关闭的确定性隔离，并完成聚焦回归
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `deepseek` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/rux_candidate_audit.json`
- `runs/execution/medical_monitoring_p10_20260730/loop_3_16_v16/rux_candidate_audit.md`
- `services/api/app/monitoring_mapping_draft_repository.py`
- `services/api/app/monitoring_mapping_semantic_quality.py`
- `scripts/monitoring_mapping_candidate_audit.py`
- `tests/test_monitoring_mapping_draft_repository.py`
- `tests/test_monitoring_mapping_candidate_audit.py`
- Current real RUX V16 evidence is summarized here; the worker must not inspect or
  mutate runtime SQLite:
  - batch `monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb`
  - 173 completed / 2 failed jobs; current audit covers 1,781 field occurrences
  - audit: 3 errors / 70 warnings / 8 observations
  - two `XJOB-IP-ACTION-COLLAPSE` errors are `DAB.DABMECO` and
    `DAB.DABMECO_UNIT`, with provider roles
    `drug_return_compliance_percent` / `_unit`
  - one `XJOB-CODING-CHAIN-DRIFT` error is the PR MedDRA chain: provider candidates
    mix `standardized_coded` HLT/HLGT/LLT/SOC fields with `source_collected`
    `PTCODE` and a declared `meddra_dictionary_version` support field
  - none of the inconsistent standardized PR fields carries complete verifiable
    coding system + real source field + independent version-field lineage
- Current filesystem and tests are authoritative. Historical model output is not
  acceptance evidence.

## Scope

- In scope:
  - Add a project-neutral draft-assembly quarantine for a provider role containing
    more than one IP action family. Preserve the immutable candidate, source value,
    evidence and uncertainty; the assembled field must not authorize return,
    compliance or exposure conclusions.
  - Add a whole-source-set normalization after existing MedDRA anchoring: any
    `standardized_coded` field whose coding lineage is not complete and verifiable
    against same-domain assembled fields must be downgraded to `source_collected`.
    Closed AE/MH chains that satisfy the existing anchor contract must remain
    standardized.
  - Add explicit audit resolution markers and downgrade the corresponding candidate
    findings from error to warning only when the deterministic draft quarantine
    guarantees the unsafe semantics cannot reach a formal draft unchanged.
  - Add positive and negative tests for candidate immutability, action quarantine,
    unclosed PR chain downgrade, and closed MedDRA chain preservation.
- Allowed writable paths:
  - `services/api/app/monitoring_mapping_draft_repository.py`
  - `scripts/monitoring_mapping_candidate_audit.py`
  - `tests/test_monitoring_mapping_draft_repository.py`
  - `tests/test_monitoring_mapping_candidate_audit.py`
- Out of scope:
  - Runtime SQLite, source listing/protocol files, API/service lifecycle, real job
    retries, candidate decisions, draft confirmation/activation, frontend, and
    medical-writing files.
  - Inferring a coding system, treatment identity or specific IP action from field
    names or values.
  - Relaxing semantic-quality gates, deleting candidate evidence, or rewriting
    immutable AI candidates.

## Success Criteria

- Assembled fields with multi-action provider roles are represented by a closed
  project-neutral source-value role and carry an explicit quarantine action; no
  return/compliance/exposure capability can become ready from that field.
- A standardized coding claim remains standardized only when its explicit lineage
  names a non-generic coding system, existing real source fields and a separate
  declared dictionary-version support field in the same assembled domain.
- Incomplete standardized claims are downgraded as one fail-closed source-set
  operation; original candidate JSON is byte-for-byte unchanged.
- Existing complete AE/MH MedDRA anchor tests remain green.
- Candidate audit reports deterministic resolution as warning, but continues to
  emit errors for unsafe shapes not covered by the assembly normalization.
- Focused tests pass and the worker reports exact commands/counts, changed files,
  failed paths and residual risk.

## Risk Boundaries

- Write only the four allowed source/test paths.
- Do not inspect or modify runtime databases or call a product API/provider.
- Do not use RUX-specific field names in product logic or tests as the rule trigger.
- Do not turn incomplete coding into standardized coding; fail closed by downgrade.
- Do not interpret a collapsed action as one preferred IP action.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-31 23:28:11: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-31 23:31 CST: Codex reviewed the real RUX v16 candidate audit and authorized
  only the project-neutral fail-closed quarantine above.
