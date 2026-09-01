# Conference Context: mw_dynamic_protocol_modules_20260719

Created: 2026-07-19 18:38:53
Objective: 基于公司方案模板、真实跨期方案与ICH M11，设计方案设计阶段驱动方案摘要、正文、统计、流程表及AI候选同步变化的动态章节适用性架构，并审阅当前实现缺口
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no sub-venue chair: Grok Build `grok-4.5` (`grok-build`) and Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning). For either unavailable primary role, the runner tries Hermes OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / cms-model` and Hermes OpenCode Go `deepseek-v4-flash`. Any unavailable complex-task role follows Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning), then Reasonix CLI `deepseek-v4-flash`, then Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as a declared fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- User correction: chapters are dynamically selected from the confirmed study
  design. If no interim analysis is planned, no interim-analysis synopsis row
  or body section should be emitted. If planned, the decision must propagate
  consistently into synopsis, statistics, schedule, evidence requirements and
  AI candidates. The same principle applies to all design-dependent modules.
- Company authority matrix:
  `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TEMPLATE_AUTHORITY_MATRIX.md`
- Current implementation:
  `services/api/app/medical_writing_protocol_template.py`,
  `services/api/app/medical_writing_greenfield.py`,
  `packages/contracts/workbench_contracts/models.py`,
  and `tests/test_medical_writing_protocol_template.py`.
- Highest-priority synopsis reference, read-only:
  `/Users/smkzw/Documents/康哲项目资料/CMS-D017/4.方案/PNH/方案摘要/CMS-D017-PNH-方案摘要_v0.2.docx`.
- Full protocol references, read-only:
  `/Users/smkzw/Documents/康哲项目资料/模版/方案模版/CMS-D017Ⅰ期方案-v1.1-20260209-clean.docx`,
  `/Users/smkzw/Documents/康哲项目资料/模版/方案模版/CMD-D001-AD II期临床方案-V1.0-tracked-20251212(1).docx`,
  `/Users/smkzw/Documents/康哲项目资料/模版/方案模版/MG-K10-青少年AD-3期方案V1.0-20251105-clean.docx`.
- ICH M11 files are secondary arbitration/coverage evidence only and must not
  override consistent company implementation:
  `/Users/smkzw/Documents/指导原则及临床试验规范合集/ICH指导原则/M11模板中文版.pdf`,
  `/Users/smkzw/Documents/指导原则及临床试验规范合集/ICH指导原则/M11指导原则中文版.pdf`,
  `/Users/smkzw/Documents/指导原则及临床试验规范合集/ICH指导原则/M11技术规范中文版.pdf`.

## Scope

- In scope: independently derive a structured applicability/propagation model
  for design decisions; identify all important cross-module dependencies;
  audit the current implementation for false-positive, false-negative and stale
  content risks; recommend a front-end confirmation model, backend contract,
  deterministic rule evaluation, AI boundary, traceability, conflict handling
  and cross-project test matrix.
- Out of scope: do not edit production source; do not create clinical content
  for one project; do not adopt M11 as the default visible chapter tree; do not
  treat model consensus as regulatory authority.

## Success Criteria

- Produce a practical design-decision-to-artifact matrix covering at minimum
  phase-I subtypes, randomization, blinding, comparator, PK/PD,
  immunogenicity, AESI, interim analysis, estimand, multiplicity, subgroup,
  adaptive/cohort/basket designs, rescue/background treatment, committees,
  special populations and optional assessments.
- Define explicit states such as applicable/not-applicable/unknown/deferred,
  including how users override AI proposals and how one decision updates every
  affected artifact without deleting accepted user text silently.
- Separate deterministic eligibility rules from LLM suggestions and define
  contradiction detection, versioning, migration and audit requirements.
- Recommend representative tests across at least Phase I, Phase II and Phase
  III designs, including negative-language cases like “不设置正式期中分析”.
- Identify current implementation gaps with file/function-level evidence and
  provide a prioritized remediation sequence for Codex.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 240 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use 30 and 40 respectively.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-19 18:38:53: Conference initialized by `hermes_workflow_guard.py init-conference`.
