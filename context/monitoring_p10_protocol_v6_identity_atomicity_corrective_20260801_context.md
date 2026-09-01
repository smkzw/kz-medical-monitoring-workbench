# Task Context: monitoring_p10_protocol_v6_identity_atomicity_corrective_20260801

Created: 2026-08-01 02:33:31
Objective: Implement offline protocol evidence packet v3, stable typed list bundle identity, stricter list-role detection, topic-scoped conflicts, visit candidate fact-type/atomicity gates, protocol output-schema cleanup, repair schema v2 and prompt v6; add the full v5-canary negative matrix without starting services or writing runtime data.
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `deepseek` / `deepseek-v4-flash` / `max`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current filesystem under
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Independent v5 canary review and its 14 required negative tests:
  `runs/codex-subagent_monitoring_p10_loop316_protocol_v5_visit_canary_20260801.md`.
- Current implementation:
  - `services/api/app/monitoring_ai_source_packet.py`
  - `services/api/app/monitoring_ai_service.py`
  - `services/api/app/monitoring_protocol_preparation_service.py`
- Current focused tests:
  - `tests/test_monitoring_ai_source_packet.py`
  - `tests/test_monitoring_ai_service.py`
  - `tests/test_monitoring_protocol_preparation.py`
- Existing source quotes/fixtures in those tests are sufficient for this offline repair.
  No production path, runtime database, real project, live provider response, or web
  discovery is authorized or needed.

Baseline SHA-256 before this edit round:

- `monitoring_ai_source_packet.py`:
  `6263537d3443b1a2c477814f36c54abf10b67d0da7b39621652eb88132de1b98`
- `monitoring_ai_service.py`:
  `c185d251b39151ff0598d231214d32ec59b2ffda4ff122552269f031e74fd955`
- `monitoring_protocol_preparation_service.py`:
  `23a436e6d240de8d83d1cf187471f7182a82ec62c5d8baf1e6304ae5f4ee8273`
- `test_monitoring_ai_source_packet.py`:
  `829401956c11326f200639c0dc016d38c8c8fbc15edbf358f219c8c94858fa05`
- `test_monitoring_ai_service.py`:
  `fdc3baa662dd377a532d222105ac2df8f004d6b2e223946b6ea3397796e9e97d`
- `test_monitoring_protocol_preparation.py`:
  `7db70727ea5383998c2cc7b9c2bb1a015f8f08af609eee9545523bb0666577a8`

## Scope

- In scope:
  - Bump protocol evidence packet to v3, structural repair lineage to v2, and
    protocol prompt identity to `monitoring-protocol-clause-structuring-v6`.
  - Add stable typed list membership independent of
    `parent_match_source_ids`. Keep that field as causal expansion lineage only.
  - Use exact detected ancestor-title source identity for a stable bundle ID.
    Multiple bundle memberships are ambiguous and must fail closed.
  - Tighten list-title and list-item detection. A colon-ending short title is
    eligible; prose ending in `。` must not become a term-based title. Only explicit
    list-item syntax is a list item; following unmarked paragraphs remain paragraphs.
  - Provider focus must include the exact stable ancestor of a selected list item or
    omit/fail closed on the orphan; it must not add siblings.
  - Structural repair and typed repair lineage must group by stable list bundle ID,
    never by a frozenset of `parent_match_source_ids`.
  - Add required protocol candidate `fact_type` and validate it against the topic's
    `candidate_fact_types`.
  - For `visit_window_and_order`, deterministically reject candidate content about
    IP/CM actions, dispensing/return/weighing/adherence/PK, early or consent
    withdrawal, safety follow-up, AE collection, or CM collection. Allow visit
    schedule/window, reschedule/makeup/missed visit, and unscheduled visit content.
  - Enforce one visit action family per candidate:
    schedule/window, reschedule/makeup, or unscheduled visit.
  - Make source-conflict detection topic-scoped. Medication-action conflicts are
    eligible only for `study_treatment` and `concomitant_medication_policy`; they
    must not be injected into a visit job.
  - Remove protocol candidate-level `system_generated_evidence` from the provider
    output schema. Preserve the instruction outside the output schema, and do not
    alter other prompt identities.
  - Add all 14 v5-review negative tests, including stable identity, orphan
    prevention, true cross-list rejection, separate topic/atomicity rejection,
    topic-scoped conflicts, exact conflict evidence, schema cleanup, and one-cell
    row lineage-only behavior.
  - Add v5 to `PROTOCOL_STATUS_LEGACY_PROMPT_VERSIONS` so terminal v3/v4/v5 history
    can remain status-compatible during a future v6 startup.
- Writable paths are limited to the six implementation/test files listed under
  Source Of Truth. Do not write the runner-owned report.
- Out of scope:
  - Starting 8911 or 5174; calling APIs/providers; writing or restoring runtime DBs.
  - Running real projects, RUX, or MY009.
  - Candidate accept/reject/adopt/confirm/activate decisions.
  - Changing `main.py`, repository startup logic, frontend, medical-writing code,
    package dependencies, product configuration, or any file outside the six
    writable paths.
  - Retrying/reusing v5 or creating a v6 canary.

## Success Criteria

- The six-file change is narrow and directly implements the contract above.
- Packet v3 exposes stable list bindings whose identity does not change with causal
  keyword-hit windows; `parent_match_source_ids` remains lineage only.
- PROMIS-like prose cannot become an ancestor title, real title/item closure works,
  orphan focused items are impossible, and genuinely different physical lists remain
  distinct.
- Protocol output requires an allowed `fact_type`; visit candidates are topic-scoped
  and contain only one permitted visit action family.
- Visit packets do not carry medication-action conflicts; qualifying conflicts retain
  exact evidence sets and permitted claim kinds.
- Protocol output schema does not expose `system_generated_evidence`, so that
  pseudo-field cannot consume the controlled repair opportunity.
- All 14 required negative behaviors have focused regression coverage.
- Worker runs only the three focused test files and Python compilation. Codex will
  independently inspect the diff/hashes and run broader monitoring and adjacent
  medical-writing regressions before acceptance.

## Risk Boundaries

- 8911 and 5174 must remain stopped throughout this offline edit round.
- Do not read or write production paths, runtime data, backups, credentials, or real
  project content.
- Do not start services, providers, browsers, long-lived processes, sub-agents, or
  another execution route.
- Preserve medical-writing behavior and unrelated user changes.
- Do not salvage failed provider prose or create/decide any protocol candidate.
- Fail closed on ambiguous list identity, disallowed fact type, mixed topic, or mixed
  action family.
- Do not write to any path except the six explicit writable files.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Launch the selected route once and use the runner's hard wait, up to 120 minutes.
- Do not issue fixed-interval status prompts, re-dispatch because of latency, or
  force-kill an unchanged running session.
- Same-session follow-up is allowed only after terminal completion for a concrete
  missing artifact, failed focused check, or resumable truncation.
- Fallback requires verified terminal failure, exhausted controlled recovery,
  empty/truncated output, or failed acceptance after the allowed recovery.

## Loop Log

- 2026-08-01 02:33:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-01: Re-anchored after compaction. Confirmed ports 8911/5174 stopped and all
  six target hashes still match the recorded baseline. Selected the existing local
  surgical repair over external discovery because the defect and required behaviors
  are fully characterized by immutable v5 evidence and existing contracts; no new
  dependency or architecture choice is involved.
- 2026-08-01: Pi initial pass completed in session
  `019fb977-9636-7000-876b-15f3ea49de8a`; focused tests reported 240 passed.
  Codex review rejected acceptance for two in-scope gaps: a bundle-less primary
  `list_item` remained in provider-focused evidence despite required orphan omission,
  and topic-scoped conflict detection did not pair study-treatment with IP-only /
  concomitant-medication with CM-only object scopes. One consolidated same-session
  corrective pass is authorized.
