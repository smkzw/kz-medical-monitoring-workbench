# Conference Context: medical_writing_sites_feasibility_20260714

Created: 2026-07-14 21:55:16
Objective: 从医学写作生产系统、公司内网私有化和临床数据治理角度，复核OpenAI Sites用于康哲AI医学经理工作台上线的适用边界、迁移成本、混合部署方案与阶段性建议
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

- Latest global governance extract: `context/global_agents_conference_rules_20260714.md`.
- User requirements, current stack evidence and loop state: `records/active_slices/medical_writing_full_gap_review_20260714/TASK_RECORD.md`.
- Sites and medical-writing source manifest: `records/active_slices/medical_writing_full_gap_review_20260714/SOURCE_MANIFEST.md`.
- Codex preliminary compatibility audit: `records/active_slices/medical_writing_full_gap_review_20260714/SITES_DEPLOYMENT_FEASIBILITY.md`.
- Official local Sites contract extract with source hashes: `context/sites_contract_extract_20260714.md`.
- Participants may use only the files listed above plus this context and main-venue plan. They must not inspect production code, browse, deploy, or infer undocumented platform behavior.

## Scope

- In scope: whether Sites can host the current medical-writing workbench unchanged; what must migrate; suitability for decision/demo, de-identified pilot, hybrid frontend/private backend and full production; D1/R2/auth/access-control implications; alignment with local/private deployment strategy; product and clinical-data governance risks.
- Out of scope: creating or deploying a Site, changing production code, committing to vendor security/compliance, asserting private-network connectivity, or replacing the approved medical-writing roadmap.

## Success Criteria

- Distinguish verified Sites capability, current-workbench fact, inference and unresolved company-governance question.
- Produce a clear `use now / conditional pilot / do not use yet` matrix.
- Identify the smallest migration boundary and reject a needless full rewrite if the same value can be obtained with a separate demo adapter.
- Address clinical source documents, subject-level data, company confidentiality, identity/RBAC, audit, document processing, long-running AI tasks, network reachability and private deployment portability.
- Return actionable conditions for a future production decision without slowing the medical-writing P0 implementation.

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
- Sites private deployment or SIWC must not be described as company security/compliance approval.
- Do not claim that Sites can execute Python FastAPI, SQLite, local filesystem, local OCR or local AI gateways unchanged.
- Do not recommend uploading real clinical/source data to a cloud service before company security, legal, privacy, data-residency and supplier-governance review.
- Do not turn deployment exploration into a second business-logic implementation.

## Loop Log

- 2026-07-14 21:55:16: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-14 22:24: Primary chair `buddy/glm-5.2` terminated before a usable resumable session was established (`rounds_completed=1`, `failure=no usable Hermes session was established`). This meets the global replacement condition. Per the user's standing fallback instruction for GLM failure, Codex declared `opencode-go/qwen3.7-plus` as replacement chair; the replacement must run a fresh three-round same-session chair review and record the primary failure.
