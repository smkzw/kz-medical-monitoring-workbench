# Conference Context: mm_r7_slice07b_subject_flow_visual_acceptance_20260828

Created: 2026-08-28 23:55:51 CST
Objective: 独立审阅医学监查项目/中心受试者阶段流向看板的真实宽屏视觉与交互质量，重点核查阶段先后、分支方向、风险层级、中文可读性、表图联动与不横向溢出；仅使用合成数据，不触碰真实项目与医学写作子系统。
Task type: `visual_delivery_conference`
Risk: `high`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
- This packet uses one Codex-led conference object (`visual_single_object`) with no sub-venue chair. Its effective `CST` route chain is `grok-build/grok-4.6:high -> cursor/cursor-grok-4.6:high`; it is resolved once at packet creation and filtered against the actual execution route nodes recorded below before dispatch.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice07b_subject_flow_implementation_20260828`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `codebuddy-cli/glm-5.3-flash`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- Frozen behavior contracts:
  - `reviews/medical_monitoring_r7_slice07b_subject_flow_dashboard_contract_v0_2_20260828.md`
  - `reviews/medical_monitoring_r7_slice07b_subject_flow_dashboard_contract_v0_3_20260828.md` (§9 overrides v0.2 on conflicts)
- Audience-facing 1920px evidence: `artifacts/mm_r7_slice07b_subject_flow_ego_20260828/project_flow_clip_fixed_v2_1920.png`
- Audience-facing 1280px evidence: `artifacts/mm_r7_slice07b_subject_flow_ego_20260828/project_flow_clip_1280.png`
- Frontend implementation: `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx` and `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5.css`
- Deterministic render contract: `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5SubjectFlowRender.test.mjs`
- Synthetic fixture only: `artifacts/mm_r7_slice07a_progress_ui_ego_fixture_20260828/synthetic_fixture.py`
- Codex live ego(lite) observations: 1920px and 1280px page horizontal overflow were both 0; project view rendered 7 nodes/5 links; node, link, risk-band, detail expansion, center drill-down and Journey jump were exercised. The Journey jump opened the visit-axis subject view. Native select automation for `累计到达` was inconclusive, so that mode is supported only by deterministic route/render tests in this pass.

## Scope

- In scope: project and center overview flow readability, chronological left-to-right grammar, branch direction, node/link hierarchy, medium/high-risk cues, Chinese labels, wide-screen fit, detail-table linkage, and Journey entry discoverability.
- Out of scope: source edits, real clinical project data, medical-writing files, clinical correctness of synthetic content, security design/testing, service startup, and final acceptance.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Reviewer must open both screenshots and state concrete visual evidence rather than reviewing code alone.
- Findings must distinguish blocking defects from later polish and must not infer a failure from intentionally zero-count catalog nodes.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. A catalog/auth/transport health preflight timeout or malformed response is diagnostic and must still allow one live route attempt; explicit user routes also proceed when the catalog is stale or incomplete, while a genuinely missing CLI or native transport boundary may block. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Read only the listed workspace artifacts and directly related local source/tests; do not read user clinical-project directories.
- Do not modify files or run the real projects. The synthetic localhost fixture is evidence only.

## Loop Log

- 2026-08-28 23:55:51 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-29 CST: Round 1 returned `revise`. Codex accepted the three material findings and changed the implementation: `row_order` now controls same-column terminal placement; zero-count catalog nodes are visibly labelled `本截止点无人到达`; columns use a capped centered gap; the SVG canvas is 1220×151 with a 128px wide-screen cap and enlarged source-unit typography; overview chrome, waiting and active progress, KPI cards, and flow spacing are compacted; center calculation details now follow flow and current-risk sections.
- New ego(lite) evidence after remediation:
  - `artifacts/mm_r7_slice07b_subject_flow_ego_20260828/project_overview_1280x800_waiting_accepted.png`
  - `artifacts/mm_r7_slice07b_subject_flow_ego_20260828/project_overview_1920x800_waiting_accepted.png`
  - `artifacts/mm_r7_slice07b_subject_flow_ego_20260828/project_overview_1280x800_active_accepted_v2.png`
  - `artifacts/mm_r7_slice07b_subject_flow_ego_20260828/center_overview_1280x800_waiting_accepted.png`
- Browser measurements after the final post-Round-2 correction at scrollY=0: waiting project flow top/bottom 526/654px, risk-section top 759px and `高、中风险定位` top 799px at 1280×800 and 1920×800; interrupted-resumable progress is 82px, risk-section top 762px and heading top 799px. Center flow remains complete, with 7 nodes/2 links after the empty-main placement fix. All views have page overflow 0. `not_provided` and empty-center render distinct Chinese notices with zero nodes.
- Post-Round-2 source correction: two-line labels use non-overlapping 16/34px baselines with counts at 50px and risk/empty copy at 64px; an empty `main` node keeps its canonical row while an empty `branch_terminal` uses the lower row, preventing the center `治疗中`/`完成研究` collision. The reviewer’s remaining label and missing-center-node observations therefore describe the pre-final screenshots, not the accepted filesystem.
- Deterministic evidence after final remediation: focused Python/fixture `69 passed`; all 49 medical-monitoring frontend test files passed including `medicalMonitoringR5SubjectFlowRender: 99 checks passed`; Vite build passed (`1968 modules transformed`) with only the existing bundle-size advisory.
