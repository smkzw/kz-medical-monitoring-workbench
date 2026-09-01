# Conference Context: medical_writing_domain_table_designers_20260714

Created: 2026-07-14 02:28:02
Objective: 基于真实跨项目方案表格，将现有11类医学写作模板中高复用、高风险的非研究流程表升级为领域化交互设计器、服务端语义验证和确定性Word输出，并保持统一工作副本、AI修订、审批和审计链
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3`, Hermes `buddy / kimi-k2.7-code`, and Hermes OpenCode Go `qwen3.7-plus`.
- Chinese labels or Chinese sentence review uses a single Hermes `buddy / deepseek-v4-pro` gate and does not start a conference.
- Other complex tasks use Hermes `buddy / glm-5.2` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3`, Hermes `buddy / deepseek-v4-pro`, and Hermes OpenCode Go `mimo-v2.5`.
- This conference route does not invoke Reasonix for a high-risk second review.
- Every conference role is dispatched through a three-round same-session loop: independent pass, skeptical challenge, and corrected final pass. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/active_slices/medical_writing_domain_table_designers_20260714/TASK_RECORD.md`
- `records/active_slices/medical_writing_domain_table_designers_20260714/REAL_PROTOCOL_TABLE_PATTERN_EVIDENCE.md`
- `records/active_slices/medical_writing_soa_builder_20260713/TASK_RECORD.md`
- `records/active_slices/medical_writing_table_ai_revision_20260714/TASK_RECORD.md`
- `services/api/app/medical_writing_table_templates.py`
- `services/api/app/medical_writing_tables.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`
- `tests/test_medical_writing_table_templates.py`
- `tests/test_frontend_structured_table_designer_contract.py`
- Participants may read only these listed files plus this context and the main-venue plan. The original DOCX paths are represented by the verified evidence record and are not to be opened by Hermes.

## Scope

- In scope: decide which non-SoA tables merit domain profiles now; propose the smallest reusable schema for semantic roles, controls, mapping confirmation, validation and Word persistence; define desktop interaction and tests; preserve existing work-copy/AI/approval/audit architecture.
- Out of scope: project-specific medical thresholds; automatic clinical conclusions; rewriting source DOCX; building separate editors or version stores per table type; changing CM boundaries; browser or Word visual acceptance by Hermes; adding unsupported specializations merely because templates exist.

## Success Criteria

- Rank candidate domains by real cross-project evidence and medical review risk.
- Converge on a schema-driven architecture that does not duplicate large frontend/backend components.
- Define required semantic fields, controls, cross-field rules and human-confirmation boundaries for the first supported domains.
- Preserve arbitrary row/column layouts and map semantic roles without forcing one canonical visual shape.
- Specify tests with at least two real projects per promoted domain where evidence allows; explicitly retain generic mode where evidence is insufficient.
- Return a compact three-round loop trace with evidence, disagreements, uncertainty and an actionable recommendation.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Do not infer project requirements from another project's protocol table.
- Do not treat a PK result table as a PK sampling schedule, an SAE contact table as an AE management rule table, or narrative rules as validated structured-table evidence.
- Trial-drug dose modification/change remains distinct from concomitant medication.
- Generated templates are working-copy drafts, not original evidence or medically approved content.

## Loop Log

- 2026-07-14 02:28:02: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-14: Codex re-parsed the eight original DOCX table patterns and ranked domain evidence; no production source was modified.
