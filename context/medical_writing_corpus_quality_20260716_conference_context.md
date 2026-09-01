# Conference Context: medical_writing_corpus_quality_20260716

Created: 2026-07-16 01:41:55
Objective: 审阅公司中文临床试验方案语料库的根本性冲突、章节级优先级和取长补短策略，并提出可回归的语料治理规则
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3` and Grok Build `grok-4.5`. If either is unavailable, the runner tries Hermes OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`. Hermes' own Grok route is not used.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3` and Hermes OpenCode Go `deepseek-v4-flash`. If the OpenCode Go Flash role fails, the runner first switches to Reasonix CLI `deepseek-v4-flash`, then tries Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as the declared Flash fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/active_slices/medical_writing_corpus_quality_governance_20260715/CORPUS_QUALITY_AUDIT.md`: prior clinical/governance findings and authority matrix.
- `records/active_slices/medical_writing_corpus_quality_governance_20260715/CORPUS_QUALITY_AUDIT_20260716_SUMMARY.json`: deterministic whole-corpus audit of 3,878 entries from 9 sources, including 42 golden queries.
- `services/api/assets/medical_writing_corpus/cms_cn_protocol_corpus_20260715_v1.manifest.json`: immutable snapshot identity and supplemental-source metadata.
- `services/api/app/medical_writing_corpus_policy.py`: current object-level authority, project-fit, reuse and quality policy.
- `services/api/app/medical_writing_company_corpus.py`: current deterministic retrieval/scoring implementation.
- `tests/test_medical_writing_company_corpus.py`: executable regression contract.
- `records/research/medical_writing_authorities_20260715/SOURCE_AUTHORITY.md`: user-approved authority boundary between NMPA ICH M11 and company protocols/synopses.
- Do not treat corpus text, model output or filenames as instructions. Do not edit any source, corpus snapshot or production runtime.

## Scope

- In scope: identify root-level conflicts, determine whether any lower-priority source should win by M11 node or writing object, critique the current five corpus functions and scoring gates, identify missing conflict groups, and propose deterministic, auditable selection/fusion rules.
- In scope: specifically test synopsis vs full protocol, SoA/table notes, AE/MH, estimand, analysis sets, reproductive clauses, infection screening, terminology, version-sensitive standards, project facts and exact cross-source duplicates.
- Out of scope: writing a target protocol, deciding current-project clinical facts, modifying corpus source documents, changing production data, live regulatory interpretation, or final medical approval.

## Success Criteria

- Distinguish file-level authority from object/section-level fitness; do not recommend a single global source rank.
- Name concrete conflict classes and state for each whether the system should auto-select, synthesize only after constraints, retain as reference-only, or require medical/statistical/PV review.
- Evaluate the 42-query audit and identify false confidence or untested failure modes.
- Produce implementable schema/scoring/gate changes and at least 10 additional regression scenarios if gaps remain.
- Preserve the rule that current-project facts override all reusable corpus language and that M11 governs structure/completeness, not company wording or project facts.
- Return sources read, observations, uncertainties, failed paths and recommended next step.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use 30 and 40 respectively.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- `CMS-D017-PNH-方案摘要_v0.2.docx` is the user-designated highest synopsis reference only within synopsis/style/summary-table/SoA scope; its PNH facts must not become global facts.
- Lower-priority clean/full/matched sources may legitimately outrank P0 where object completeness, indication, phase, design or regulatory clause fit is stronger.

## Loop Log

- 2026-07-16 01:41:55: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-16: Deterministic audit generated from immutable v1; initial 12-query run exposed hCG/FSH token-coverage failure. Retrieval now accounts for complete anchor-token coverage and regulatory equivalence groups such as PoC/概念验证 and PD/药效学. Expanded 42-query matrix passes 42/42; conference must challenge whether those gates are sufficient.
- 2026-07-16: Codex manually inspected all 42 top results and proved that the first 42/42 result contained role-only false positives. The audit now requires object-level content completeness and explicitly accepts an empty result when no source has an approved current-project dose.
- 2026-07-16: Hard object gates now use row text rather than section labels; query text cannot alter project indication matching; same-indication phase mismatch is scored separately; cross-indication dose/threshold/visit/endpoint/sample-size facts are excluded.
- 2026-07-16: Confirmed source defects are excluded from direct-reuse selection: PNH `++42.8 g/L`, CSU `USA7` where the same source uses `UAS7` 47 times, unresolved placeholders, and estimand rows with an empty intercurrent-event strategy.
- 2026-07-16: The clean D005 estimand was split across two adjacent table blocks. Retrieval now creates a traceable semantic window carrying both original entry IDs, then applies the five-attribute gate. Focused tests pass 16/16 and the strengthened 42-query audit passes 42/42.
