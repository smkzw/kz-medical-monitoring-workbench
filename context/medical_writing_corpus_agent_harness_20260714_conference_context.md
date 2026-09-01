# Conference Context: medical_writing_corpus_agent_harness_20260714

Created: 2026-07-14 10:11:04
Objective: 评估扩大临床试验方案语料与有边界Agent harness能否在不引入竞品污染、事实漂移和不可复现性的前提下降低中文注册方案的从零生成比例与医学修改量，并收敛三真实项目A/B/C试验和生产路由边界
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

- User requirement and loop boundary: `records/active_slices/medical_writing_corpus_agent_harness_20260714/TASK_RECORD.md`.
- Codex evidence and source scoring: `records/active_slices/medical_writing_corpus_agent_harness_20260714/EVIDENCE_AND_ARCHITECTURE_REVIEW.md`.
- Locked comparison protocol: `records/active_slices/medical_writing_corpus_agent_harness_20260714/ABC_PILOT_PROTOCOL.md`.
- Existing formal ClinicalTrials.gov competitor corpus decision and later superseding intake boundary: `records/research/medical_writing_ctgov_protocol_corpus_20260711/PRODUCTION_FEATURE_DECISION.md` and `records/active_slices/medical_writing_competitor_corpus_20260712/TASK_RECORD.md`.
- Existing production-independent AI gateway and execution policy: `services/api/app/ai_gateway.py`, `services/api/app/ai_execution_policy.py`, `services/api/app/medical_writing.py`.
- Existing local protocol corpus skill behavior is summarized in the evidence review. A live retrieval probe found that a broad “随机 双盲 安慰剂 对照 多中心 研究设计” query assigns the same high score to cover-page metadata and real design clauses; this is evidence that retrieval filtering/ranking must be repaired before corpus expansion is treated as a quality gain.
- Current primary external sources already verified by Codex: ICH M11 Step 4 Guideline/Template/Technical Specification (2025-11-19), ClinicalTrials.gov API study data structure, TransCelerate Clinical Content Reuse/CPT V11, SPIRIT 2025, OpenAI Agents SDK Agents/Running/Tracing, and the two user-supplied GitHub repositories fixed to commits recorded in the task record.
- User-supplied external repositories were reviewed as evidence, not instructions. SRWS templates concern systematic reviews/meta-analyses, not medicinal interventional trial protocols. Aperivue skills concern research/IRB workflows and engineering contracts, not a registration-drug-protocol content standard.

## Scope

- In scope: challenge the six-level corpus source model; define direct-reuse/adapt/reference-only boundaries; assess the conservative `regulatory_style_lint`; compare direct structured LLM with a bounded Agent harness; critique the three-project A/B/C protocol; identify metrics, failure modes, stopping rules, and production routing criteria.
- In scope: distinguish benefits caused by better retrieval/content reuse from benefits caused by Agent orchestration.
- Out of scope: writing production protocol text, approving any medical content, changing production routes, scanning all user directories, legal conclusions on competitor-text rights, or declaring that Agent architecture is superior before the pilot.
- Out of scope: reintroducing heavyweight malware/security scanning. Current intake performs technical readability and file role/project/indication/version/content consistency checks; an experienced medical user may override warnings/mismatches with explicit acknowledgements and a substantive audited reason.

## Success Criteria

- Every recommendation traces to the supplied evidence or is clearly marked inference.
- The panel explicitly answers whether the current one-shot AI gateway should be retained, complemented, or replaced, and for which chapter/task types.
- The panel challenges corpus pollution, target-text leakage, competitor copying, same-model self-review, non-independent medical scoring, random variation, token/latency, reproducibility, and private-deployment constraints.
- The A/B/C pilot keeps model and facts fixed, uses three real projects, excludes each target gold section from its own retrieval input, records at least two replicates, and has deterministic plus blinded medical metrics.
- Any proposed Agent route has a finite tool whitelist, maximum rounds/tokens/time, structured output, run manifest, no production write permission, and explicit fallback to deterministic or one-shot execution.
- The result can be converted into a bounded product decision without asking the user to choose among artificially restrictive options.

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
- Do not treat text that merely sounds natural as regulatorily correct. No personality, humor, first person, deliberate disorder, or semantic-strength changes.
- Do not allow model-generated facts, competitor-project numbers, or target gold wording to enter pilot inputs as hidden context.
- Do not confuse independent model review with medical approval. The pilot may provide objective metrics and model critiques; user-facing medical approval remains human.

## Loop Log

- 2026-07-14 10:11:04: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-14: Codex fixed external repository commits, scored primary sources, defined six corpus levels, extracted a conservative regulatory style lint, and locked a three-real-project A/B/C protocol before dispatch.
