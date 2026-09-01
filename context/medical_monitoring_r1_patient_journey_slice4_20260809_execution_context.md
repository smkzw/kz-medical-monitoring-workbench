# Execution Context: medical_monitoring_r1_patient_journey_slice4_20260809

Created: 2026-08-09 17:33:53
Objective: 在全新隔离 R1 切片实现共享访视轴的受试者医学旅程：同步 Profile/Timeline、风险锚点、证据回跳、中文原生、离线本地，并完成真实浏览器验收；不得修改 Slice 3、产品、医学写作、服务、共享运行库或真实项目
Task type: `html_ppt_visual_browser`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `visual_executor_pi_qwen38` -> `pi` / `alibaba` / `qwen3.8-max`
- Execution manager: `visual_manager_cursor` -> `cursor` / `cursor-cli` / `auto`
- Execution-manager fallback: `Codex takes over execution management directly`

## Source Of Truth

- Global instructions: `/Users/smkzw/.codex/AGENTS.md`
- Workbench instructions: `AGENTS.md`
- Visual contract: `/Users/smkzw/Documents/康哲项目资料/模版/design.md`
- Research decision: `reviews/medical_monitoring_patient_journey_research_20260809.md`
- System design: `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- Implementation plan: `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- Accepted read-only data/UI reference: `poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench/`
- Prior visual references: `records/visual_qc_20260708/rux_monitoring_inbox/` and `records/visual_qc_20260708/subject_timeline_lane_subcategory_colors/`
- Applicable skill contracts (read-only): `/Users/smkzw/.cc-switch/skills/subject-timeline-builder/SKILL.md`, `/Users/smkzw/.cc-switch/skills/clinical-patient-profile-html/SKILL.md`, `/Users/smkzw/.cc-switch/skills/ae-risk-assessment/SKILL.md`

## Authorized Outputs

- New slice only: `poc/medical_monitoring_ai_native_r1/slices/patient_journey/`
- Browser evidence only: `output/playwright/medical_monitoring_r1_patient_journey_slice4_20260809/`
- Runner-owned reports/logs under the generated execution task paths.
- Workers must not modify `aemh_audience_workbench`; it is a read-only accepted reference and data source.
- No file outside the explicit output paths may be created, changed, moved, or deleted.

## Implementation Contract

- Standalone `file://` experience with no server and no remote requests. It may read the existing synthetic `window.MM_R1_DATA` script from Slice 3 plus a new Slice 4 synthetic journey fixture; do not copy or edit Slice 3 files.
- New slice root contains at minimum `index.html`, `styles.css`, `app.js`, `data/journey_fixture.js`, `docs/DATA_CONTRACT.md`, `docs/SLICE4_EVIDENCE.md`, and deterministic/browser tests.
- Default subject: `SYNTHETIC-SUBJECT-001`; all content remains conspicuously synthetic in data/evidence but audience UI must use natural Chinese and must not expose backend field names, hashes, log labels, raw JSON, or English-only Profile/Timeline tabs.
- Fixture must explicitly model actual-date axis, derived study day, planned/actual/unscheduled visit anchors, phase bands, point events, an open/closed interval, candidate/fact/established-risk distinctions, source locators, and one medium-or-higher risk anchored to a dated event.
- Production semantics are not hard-coded: fixture schedule lives in data, rendering consumes contract fields generically, and missing/partial/conflicted dates have a separate pending-date surface.
- Default shell tabs: `旅程总览`、`指标趋势`、`事件明细`、`风险证据`; all share one `spine_id`, time window, axis mode and selection state.
- Journey overview uses one horizontally scrollable/zoomable SVG or DOM time coordinate with sticky visit ruler and at least four visible lanes. Point and interval events, risk markers and visits are spatially aligned.
- Risk marker click selects/cross-highlights the matching event/card and opens an evidence panel with basis/finding/action, positive/counter evidence, source locator and Query draft when present. Browsing is read-only and never writes user confirmation or risk disposition.
- Marker semantics are not color-only: fact solid square/bar; candidate dashed circle; established risk diamond. Red/orange remain restrained risk accents; UI otherwise follows the visual contract.
- Time-window controls and a brush/range control update Journey/Profile/Timeline together. Filtering a risk or moving it outside the window must not mutate or imply closure.
- Keyboard focus, visible focus, reduced motion, narrow-view horizontal handling, long Chinese text wrapping and minimum practical hit targets are required.

## Success Criteria

1. Deterministic tests prove schema, unique identities, visit/date ordering, source locator presence, risk-to-event/query binding, same-spine state and no candidate counted as a formal AE/MH fact.
2. Real Chromium and WebKit runs pass at 1280×800, 1440×900 and one wide viewport (1920×1080 or 2048×1024); screenshots cover journey overview, risk selection/evidence, metrics, events and narrow viewport.
3. Browser checks prove no console/page errors, no remote HTTP(S) request, working keyboard tab/arrow/Enter/Escape flows, synchronized time window and selection, and no horizontal page overflow (internal journey scrolling is allowed).
4. Audience-language scan has zero backend/internal/log/debug field leakage and no English-only UI tab labels.
5. Codex visually reopens representative screenshots and verifies first-screen risk salience, visit-axis legibility, spatial alignment, Chinese-native labels and design consistency.
6. Existing R1 tests and Slice 3 checks remain unchanged and passing; protected path hashes are unchanged.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- Do not start 8911 or any service. Do not read or run real projects. Do not modify medical-writing or shared runtime/package configuration.
- Do not delete or clean prior evidence during implementation; cleanup is runner archival only after Codex acceptance.

## Sequence And Ownership

1. `worker_01` runs first and owns only data contract, synthetic fixture, deterministic tests and related docs inside the new slice.
2. `worker_02` runs after worker_01 terminal completion and owns only `index.html`, `styles.css`, `app.js` and audience implementation notes inside the new slice.
3. `worker_03` runs after worker_02 terminal completion and owns only browser test code/evidence under the new slice/output path; it must report defects rather than silently editing worker_01/02 files.
4. Manager runs after all workers, checks every report/artifact, may perform only explicitly bounded remediation inside the new slice, and must not claim final visual acceptance.

## Work Items

1. 定义合成访视/阶段/点与区间事件/风险锚点数据合同和确定性测试
2. 实现离线 Patient Journey 前端、共享访视轴、泳道、时间窗、风险与证据联动
3. 完成 Chromium/WebKit 多视口、键盘、无远程请求、中文受众语言和视觉验收

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.

## User-Language Correction (2026-08-09)

- 用户明确否决界面中的“正式事实”“候选信号”“已建立风险”“正反证”“开放区间”“只读投影”等工程术语。
- 本执行合同第 44、48、49 条中的 `fact/candidate/established-risk`、positive/counter evidence、interval 等仍可作为内部数据合同与测试分类，但不得原样进入受众界面。
- 受众界面统一使用具体事件域名称（AE、MH、CM/合并用药、IP给药、实验室/检查、住院/操作、症状/体征线索）、“具体风险类型＋风险等级”“支持依据/排除依据”“持续记录/仍在持续”“只读查看”；不得再以“已记录事项”作为跨域总类标签。
- “信号”保留给确切的安全性信号语境；源数据已存在不代表医学事实已被核实。
- 用户进一步否决用单个“已记录事项”或通用风险菱形覆盖全部内容。事件与风险图例都必须按 AE/MH/CM/IP给药/实验室检查/住院操作/症状体征线索分域；风险标记还必须显示所属临床域，并独立显示高/中/低等级。
