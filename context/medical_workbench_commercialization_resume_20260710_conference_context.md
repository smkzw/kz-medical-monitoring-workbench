# Conference Context: medical_workbench_commercialization_resume_20260710

Created: 2026-07-10 07:57:59
Objective: 恢复并持续构建康哲AI全流程医学经理工作台，覆盖全部医学相关子系统，完成跨项目、独立AI、逐功能商业化验收
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes And Reasonix Delegation

- Lead/chair: OpenCode Go `minimax-m3`.
- Hermes participant models: OpenCode Go `qwen3.7-plus` and OpenCode Go `mimo-v2.5`, all default reasoning effort unless Codex overrides.
- Reasonix CLI participant model: `deepseek-flash` alias for `deepseek-v4-flash`.
- All `deepseek-v4-flash` and `deepseek-v4-pro` routes must leave Hermes and run through Reasonix CLI. OpenCode Go, Hermes custom providers, and the direct DeepSeek provider are not allowed for these models in this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro` only. Hermes/OpenCode Go/direct DeepSeek routes are not allowed for this role.

## Source Of Truth

- Current implementation: this workbench directory, especially `README.md`, `KNOWN_ISSUES.md`, `services/api/app/`, `frontend/src/`, `tests/`, `logs/`, `records/`, and prior `reviews/`/`metrics/`.
- Binding requirement ledger: `records/soft_pause_20260709_1105_lossless_full_backup/USER_REQUIREMENTS_FULL_LEDGER.md`.
- Resume plan: `records/soft_pause_20260709_1105_lossless_full_backup/FUTURE_EXECUTION_PLAN.md`.
- Latest manual-pause handoff: `logs/SOFT_PAUSE_20260709_1324_CST.md` and `records/active_slices/rux_timeline_cm_ip_boundary_20260709/README.md`.
- Product brief and approved interaction direction: `../../records/Product_Design_Brief_Gate_V0.2_20260707.md`, `../../records/Product_Design_Commercial_UX_Research_Addendum_20260707.md`, and `frontend/AGENTS.md`.
- Lifecycle source: `/Users/smkzw/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/SmkFat_310f/msg/file/2026-07/临床研发是一条九环长链路 20260630(1).html`, chapter 3.
- Authorized real-project roots, read-only in place: `/Users/smkzw/Documents/康哲项目资料` and `/Users/smkzw/Documents/朗来项目资料`.
- Original files under those roots must never be deleted, moved, renamed, or modified. Writable derivatives must live inside the medical-manager-workbench project.
- Current baseline sidecar reports, when present:
  - `runs/subagents/20260710_commercialization_baseline/module_maturity_audit.md`
  - `runs/subagents/20260710_commercialization_baseline/real_project_source_candidates.md`
  - `runs/subagents/20260710_commercialization_baseline/architecture_generalization_audit.md`
  - `runs/subagents/20260710_commercialization_baseline/frontend_audit_capture_plan.md`

## Scope

- In scope business modules: `证据调研与方案设计`, `入排审核`, `医学监查`, `数据分析与TFL`, `医学写作`, `安全信号与PV协同`.
- In scope shared surfaces: `项目总看板`, `审批中心`, source registry, independent AI/OCR/VLM gateway, project context, audit trail, read/disposition/approval/handoff states, backup/recovery, deployment configuration, and observability.
- Priority remains the first commercial delivery group (`入排审核`, `医学监查`, `医学写作`, `项目总看板`) while the other medical modules advance in parallel behind the same contracts.
- Out of scope as standalone subsystems: lifecycle links 1 (`靶点发现/药物设计`), 4 (`临床运营/DCT`), and 5 (`数据采集与管理`). Link 3 is represented only by medical eligibility review, not recruitment/site-selection operations.
- User-facing names must not contain lifecycle numbers, `阶段`, `Stage`, or similar labels.
- Desktop is the primary product. Mobile checks are degradation smoke only and may not drive removal of desktop functions or information density.

## Success Criteria

1. Every in-scope module exposes a usable end-to-end workflow, not a manifest-only or static-demo page.
2. Every subsystem is tested from original raw materials with at least two different real studies; subject-level workflows sample at least 3-5 real subjects per study where the source permits it.
3. Tests explicitly vary protocol structure, study stage/design, visits, subject identifiers, listing sheets/columns, document layout, and data availability so project-specific hardcoding is detectable.
4. AI-dependent parsing, mapping, risk explanation, drafting, and revision run through independently configured product providers. Missing providers produce an explicit blocked state; Codex reasoning is never presented as product runtime output.
5. OCR routes use local `GLM-OCR-bf16` or `PaddleOCR-vl-1.6`; every AI/OCR/VLM run records provider/model, prompt version, source spans, output, status, and medical-review disposition.
6. All medical content remains `待医学批准` until an authorized approval action. The product never auto-claims final medical approval or regulatory conclusion.
7. Every visible risk, criterion decision, trend point, writing suggestion, and handoff retains a source locator without exposing local absolute paths, hashes, storage keys, or sensitive patient content in public payloads.
8. Project context and state transitions remain isolated across projects and survive process restart. Shared identifiers cannot collide silently.
9. Desktop browser acceptance covers every visible control, navigation path, loading/empty/error/blocked state, keyboard path, overflow/alignment, and cross-module handoff. Chinese clinical terminology is independently reviewed. Mobile remains smoke-only.
10. Backend unit/contract/integration tests, frontend build, browser workflow tests, restart-recovery checks, and cross-module conflict tests all pass with fresh evidence before any module is called commercializable.
11. The local single-machine product remains runnable, while storage, secrets, provider routing, RBAC, audit, queueing, backup, and migration boundaries are documented for later private-network deployment.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes and Reasonix are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- External research and competitor-product claims require current, queryable sources; vendor claims must be labeled as vendor claims.
- No participant may alter product code in this baseline conference. Outputs are planning/review artifacts only.
- Patient-level source content must not be copied into conference reports. Use opaque subject ids only when a concrete test example is essential.
- Any material design, architecture, medical, or scope decision requires at least three independent model perspectives plus Codex adjudication and a recorded benefit/risk analysis.

## Current LOOP Contract

- Objective: replace the stale scaffold-based status picture with a requirement-by-requirement commercial-delivery baseline and select the next implementation slices that increase cross-project end-to-end truth.
- Hypothesis: the current code has useful P0 slices, but manifest pages, RUX-specific services, demo repository fallbacks, and incomplete provider/test routes still prevent commercial completion.
- Action: audit current code and records, inventory real-project sources, run independent model critiques, then land the smallest shared-contract and second-project slices.
- Observation: evidence must be exact file references, source inventories, fresh tests, browser captures, and provider stdout/metrics.
- Evaluation: a module advances only when evidence proves real behavior; static labels, demo data, old screenshots, or a single-project pass do not count.
- Decision: continue, revise, or reroute based on evidence. Ask the user only when a decision changes medical scope, data interpretation, or risk acceptance.
- Record: update system/subsystem logs, conference artifacts, source matrix, cross-module test matrix, and the live plan after every material loop.

## Loop Log

- 2026-07-10 07:57:59: Conference initialized by `hermes_workflow_guard.py init-conference`.
