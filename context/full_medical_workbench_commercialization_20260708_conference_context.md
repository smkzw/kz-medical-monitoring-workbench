# Conference Context: full_medical_workbench_commercialization_20260708

Created: 2026-07-08 03:40:38
Objective: 推进AI医学经理工作台所有医学相关子系统的商业化落地：基于当前代码、真实项目文件、外部商业产品和开源标准调研，确定下一批P0实现切片并执行闭环验证
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes Sub-Venue

- Lead/chair: OpenCode Go `minimax-m3`.
- Participant models: OpenCode Go `qwen3.7-plus`, OpenCode Go `mimo-v2.5`, and DeepSeek supplier `deepseek-v4-flash`, all default reasoning effort unless Codex overrides.
- All `deepseek-v4-flash` routes must use the DeepSeek supplier. OpenCode Go `deepseek-v4-flash` is not allowed for this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: DeepSeek supplier `deepseek-v4-pro` only. OpenCode Go `deepseek-v4-pro` is not allowed for this role.

## Source Of Truth

- Current workspace:
  - `README.md`
  - `logs/system_build_log.md`
  - `logs/subsystems/module_scope_log.md`
  - `services/api/app/*.py`
  - `packages/contracts/workbench_contracts/*.py`
  - `frontend/AGENTS.md`
  - `frontend/src/App.jsx`
  - `frontend/src/styles.css`
  - `frontend/tests/*.mjs`
  - `tests/*.py`
  - `reviews/*.md`
  - `metrics/*.md`
  - `records/visual_qc_20260707/*.json`
  - `records/visual_qc_20260708/*/*.json`
  - `research/commercial_and_open_source_research_20260708.md`
- User-authorized read-only real project roots:
  - `/Users/smkzw/Documents/康哲项目资料`
  - `/Users/smkzw/Documents/朗来项目资料`
- Known high-value local real project sources:
  - `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD`
  - `/Users/smkzw/Documents/康哲项目资料/AI/入排/test-D001项目`
  - `/Users/smkzw/Documents/康哲项目资料/MG-K10/SAR`
  - `/Users/smkzw/Documents/康哲项目资料/竞品调研/CRSwNP`
- External research record:
  - `research/commercial_and_open_source_research_20260708.md`

## Scope

- In scope:
  - All medical-manager relevant subsystems: 证据调研与方案设计, 入排审核, 医学监查, 数据分析与TFL, 医学写作, 安全信号与PV协同.
  - Workbench-level: 项目总看板, 审批中心, source registry, AI gateway, audit/approval quality gates.
  - Real raw-source validation planning and next P0 implementation slice selection.
  - Private/local-first architecture that can later move to intranet/private multi-end deployment.
- Out of scope:
  - Standalone non-medical lifecycle subsystems such as project startup/activation, EDC/data-collection-system construction, site operations, visit execution, and recruitment operations.
  - Deleting, moving, or modifying original project files under the user-provided roots.
  - Claims of automatic medical approval, regulatory readiness, or PV-system replacement.

## Success Criteria

- Current-state gap matrix covers every in-scope subsystem and separates implemented evidence from unverified/incomplete work.
- Next implementation slice is selected from evidence, not convenience, and has explicit P0 acceptance criteria.
- Hermes/subagent review is attempted and runtime/provider failures are recorded honestly.
- Real project input candidates are identified for every subsystem before broad production claims.
- Any implemented slice preserves business module names, source boundaries, independent AI provider boundaries, human approval gates, and browser QC expectations.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-08 03:40:38: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-08 03:40 CST: Hermes CLI status showed only DeepSeek configured; GLM/Kimi/MiniMax buddy providers were not configured in the current CLI environment. Treat buddy/OpenCode model absence as a provider-configuration gap, not as a successful consultation.
- 2026-07-08 03:40 CST: Added external research notes and current local source-of-truth list. User has authorized read-only access to `/Users/smkzw/Documents/康哲项目资料` and `/Users/smkzw/Documents/朗来项目资料`.
- 2026-07-08 04:00 CST: Parallel participant outputs completed:
  - `participant_ds_flash.md`: recommended 数据分析与TFL review workbench; flagged SAS7BDAT limitations, hardcoded path risk, and demo frontend data.
  - `participant_mimo.md`: independently identified manifest/inventory maturity but missing executable AI and cross-system handoff; recommended 数据分析与TFL analytical review workspace.
  - `participant_qwen_plus.md`: recommended real SDTM/ADaM ingestion and reproducible TFL workflow, with source-bound and human-confirmation gates.
- 2026-07-08 04:00 CST: SubAgent backend review and real-data inventory completed. Backend review recommended a shared source registry -> AI artifact -> approval gate -> dashboard health spine; real-data inventory identified RUX-03-002, D001, MG-K10-SAR, CRSwNP, MY008/MY009/QR059 source candidates by subsystem.
- 2026-07-08 04:10 CST: Codex selected 数据分析与TFL P0审阅工作台 as the next implementation slice because it uses real RUX/MY008 packages, has immediate cross-module value for writing, and carries lower overclaim risk than formal TFL generation.
- 2026-07-08 04:25 CST: Codex implemented TFL review contracts, JSONL review store, API routes, frontend review workbench, manifest cache, frontend request-order guard, and browser QC script updates.
- 2026-07-08 04:30 CST: Verification passed: 96 backend tests OK, frontend build OK with known bundle warning, and `tfl_manifest_qc.mjs` desktop/mobile browser QC passed. QC artifacts are under `records/visual_qc_20260708/tfl_review/`.
- 2026-07-08 04:35 CST: Hermes lead (`opencode-go/minimax-m3`) wrote `hermes_lead.md` (214 lines). Codex manually closed the Hermes CLI process after output was written because it did not exit cleanly.
- 2026-07-08 04:40 CST: Main DeepSeek Pro (`deepseek/deepseek-v4-pro`) wrote `main_deepseek_pro.md` (311 lines). Codex manually closed the Hermes CLI process after output was written because it did not exit cleanly.
- 2026-07-08 04:42 CST: Codex updated `metrics/full_medical_workbench_commercialization_20260708_conference_metrics.md` and `reviews/codex_conference_full_medical_workbench_commercialization_20260708_review.md`. Conference synthesis accepted the conservative TFL审阅工作台 slice and explicitly deferred ADaM computation/TFL reproducibility, 医学写作 citation handoff, and AI gateway wiring.
