# Task Context: monitoring_p10_loop316_protocol_v4_audit_20260731

Created: 2026-08-01 00:22:24
Objective: Read-only scientific audit of the eight current RUX protocol v4 proposed candidates and six fail-closed topics; preserve candidate decision boundary and determine the next safe action before MY009.
Task type: `high_risk_contradiction_review`
Risk: `high`
Selected agent route: `codex` / `gpt-5.6-luna` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem and the read-only GET response from the single stable API are
  authoritative for current state.
- Project: `proj_rux_03_002`.
- Protocol version: `protov_21c4b5a4a3883a8119d74e18`.
- Prompt/workflow generation: current provider-visible protocol v4.
- Recovery anchor:
  `context/monitoring_p10_loop316_protocol_focus_pause_20260731.md`.
- Mapping closure review:
  `reviews/codex_monitoring_p10_loop316_mapping_quarantine_20260731_review.md`.
- Current GET aggregate:
  `2 candidate_review / 6 failed / 0 running / 0 queued`.
- All eight current candidates remain `proposed/pending_user_confirmation`.
- The six failed jobs each have one provider attempt with one controlled repair
  inside that attempt. No failed output was persisted as a candidate.

## Scope

- In scope:
  - challenge the scientific/source fidelity and topic placement of the eight
    current v4 candidates;
  - distinguish direct facts, inference and data gaps;
  - challenge whether the six failed topics should remain fail-closed;
  - evaluate the proposed next engineering action: deterministic structural-bundle
    expansion from a provider-selected frozen evidence member before validation,
    without changing the frozen input or weakening the existing validators.
- Out of scope:
  - no candidate accept/reject decision;
  - no provider call, retry, start, service change, SQLite write, mapping draft,
    confirmation, activation or MY009 start;
  - no medical-writing file changes;
  - do not reinterpret old v3 candidates as current facts.

## Success Criteria

- Return delta-only contradictions, overreach, topic mismatch and missing evidence.
- State which candidates are scientifically coherent enough to remain in manual
  review, which require split/limited scope, and which require topic quarantine.
- State whether the six failed outputs are safe to salvage automatically.
- Challenge the proposed structural-bundle expansion design and identify the
  invariants needed if Codex chooses it.
- Preserve the user-decision boundary and fail closed on unresolved clinical scope.

## Risk Boundaries

- Read only the context packet. Do not query the live API or runtime database.
- Do not write product or runtime files.
- Do not make or simulate a candidate decision.
- Do not recommend relaxing same-row, header, list title/item, conflict, absence,
  eligibility, CM/IP or evidence-limit validators.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Current Candidate Audit Packet

The following is a compact transcription of the current GET result and its embedded
source locators. It is evidence for contradiction review, not a candidate decision.

### Early withdrawal and deviation

1. `moncand_1907bbec5840197b3605ece7e148` — "提前退出/撤回同意后的退出访视与安全性随访条款"
   - 16 evidence IDs; direct locators: paragraphs 474, 753, 758, 846,
     864, 870-874, 1165-1170.
   - Directly supported subclaims include: best effort to return within 7 days;
     best effort but not mandatory exit visit before consent withdrawal; different
     double-blind/open-label exit assessments; no automatic protocol deviation when
     incomplete exit assessments are compatible with subject safety; pre-withdrawal
     data retention and no post-withdrawal collection; treatment-consent withdrawal
     may coexist with safety follow-up.
   - Embedded data gap: section 1.2 schedule was not retrieved, so all final-visit
     procedures cannot be verified.
   - Codex preliminary concern: one decision object combines several independent
     withdrawal, visit, PK, data-use and follow-up obligations.
2. `moncand_29187c0ae91947cdd95814591b1f` — "受试者停止研究时的最低信息收集与永久停药/禁止再入组条款"
   - 6 evidence IDs; paragraphs 864-868 and 934.
   - Supported subclaims: discontinuation is permanent/no re-entry; collect reason,
     last study-drug date and last assessment/contact; emergency unblinding is handled
     as early withdrawal and the reason is recorded.
   - Codex preliminary concern: permanent discontinuation, minimum stop information
     and emergency-unblinding handling are separable obligations.
3. `moncand_7dad174faf50e0f9fcd2b8e0472d` — "依从性/研究药物管理问题咨询医学监查员及退出访视药物回收条款"
   - 6 evidence IDs; paragraphs 487-489, 855, 1167-1168.
   - Claims concern consultation with the medical monitor, IP distribution/return/
     weighing and diary-card return.
   - Codex preliminary concern: this is predominantly IP accountability/compliance,
     not an early-withdrawal clause. It must not become CM semantics.
4. `moncand_8cd4e866f95c1e2f454266bf13ad` — "失访认定与失访前联系努力条款"
   - 7 evidence IDs; paragraphs 759, 856-860, 1333 and 1339.
   - Supported subclaims: repeated missed visits/unreachable subject; contact effort
     and prompt rescheduling; if possible three telephone attempts documented in the
     medical record; final classification as withdrawal due to lost follow-up and
     last-known-contact end date; AE follow-up may end after maximal effort.
   - Codex preliminary view: coherent topic placement, but still requires manual
     confirmation of exact contact-attempt wording and operational record.
5. `moncand_9cb047e8a47e19f60a9ddf72aa14` — "伴发事件/提前退出对主要终点数据处理策略条款"
   - 10 evidence IDs; paragraph 1446 and table 7 headers/rows 3-4.
   - Supported subclaims concern composite/hypothetical estimand strategies,
     multiple imputation and worst-value sensitivity handling for missing week-8 IGA.
   - Codex preliminary concern: scientifically relevant to efficacy/statistics and
     estimands, but not an operational early-withdrawal monitoring clause.

### Data quality

6. `moncand_22a70a484b5fbe171399e7cf95a0` — "EDC/eCRF数据录入、培训、审核与质疑处理条款"
   - 9 evidence IDs; paragraphs 1412-1415 and the EDC abbreviation table.
   - Direct support: authorized investigator staff enter/correct data; user identity,
     role/permission, monitor review and source comparison, audit trail and query
     handling.
   - One explicit inference says training is a strict prerequisite to data entry.
     Source wording is "before site initiation or data entry" and does not establish
     whether both milestones or one applicable milestone governs.
   - Data gap: no query response/closure deadline.
7. `moncand_5feb304e53b7e467afeff19f712b` — "源数据/源文件定义、质量责任、电子记录与访问保存条款"
   - 5 evidence IDs; paragraphs 1513-1517.
   - Direct support: source definitions, monitoring-plan source list, source-data
     qualities, electronic-record requirements, audit trail, preservation and access.
   - One inference extends certified-copy signature/date and equivalence language to
     general traceability. Record-retention duration in section 9.3 is absent.
   - Codex preliminary concern: coherent domain but composite; retention duration
     and signature granularity must not be invented.
8. `moncand_fa1a9048250c7f806fb46f54fe02` — "统计分析计划与缺失数据处理程序时限条款"
   - 2 evidence IDs; paragraphs 1433 and 1439.
   - Direct support: SAP is developed/finalized before database lock and describes
     missing-data calculation procedures.
   - Data gap: no actual imputation method, threshold or sensitivity-analysis detail.
   - Codex preliminary view: narrow source-faithful candidate if it remains limited
     to SAP timing/content and does not imply a missing-data method.

## Six Fail-Closed Jobs

| Topic | Job | Persisted terminal reason |
|---|---|---|
| eligibility_continuity | `monai_e847991f1943e2e6c2c14d1c80c1` | table header not bound |
| visit_window_and_order | `monai_e963986fbc88d53a1dd77f56c829` | same-row condition/action cells not bound |
| study_treatment | `monai_df9856664e7dd77163c8bcf6d246` | list title and entries not jointly bound |
| concomitant_medication_policy | `monai_33f533ed3d93fcffb8be848e8d9b` | list title and entries not jointly bound |
| safety_assessment | `monai_16f6004c23df2398c9b8a9e9d3c5` | table header not bound |
| efficacy_assessment | `monai_b9f2baa24baca94744523799e64c` | table header not bound |

All six are `invalid_ai_output`, attempt 1, after the one allowed controlled repair.
The response bodies contain readable claims, but at least one candidate in each
response still lacks the frozen structural evidence required by the validator.
Request sizes were approximately 158k-341k characters and response sizes 25k-37k.
This supports provider adherence/selection failure, not proof that the protocol lacks
the underlying clause. Failed response content is not a safe candidate source.

## Proposed Next Engineering Action For Challenge

Do not retry the six jobs as-is. Consider a bounded deterministic repair in which:

1. the provider continues to select evidence from the frozen focused packet;
2. for each selected table/list member, server code expands only its already-frozen
   structural bundle (same row + available headers, or list title + sibling items);
3. expansion is recorded as deterministic repair lineage and occurs before the
   unchanged fail-closed validators;
4. no new source, semantic claim, topic, action modality or candidate decision is
   introduced;
5. the 50-ID candidate cap remains enforced after expansion;
6. ambiguous bundle membership, over-budget expansion or multiple incompatible
   bundles fails closed.

Challenge whether this is safe and sufficient. In particular, identify how to avoid
turning evidence closure into semantic endorsement or attaching a structurally
adjacent but claim-irrelevant row/list.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-01 00:22:24: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01: Codex read the current API status and immutable attempt records
  read-only, prepared this compact contradiction-review packet, and made no candidate
  or runtime write.
