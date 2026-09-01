# Conference Context: mm_r7_slice08c3_contract_20260829

Created: 2026-08-29 23:52:07 CST
Objective: 独立只读挑战并验收R7 Slice-08C-3 Patient Journey变化标记与详情抽屉最小实施合同；关闭P0-P2后才允许实现
Task type: `code_scoped_patch_plan`
Risk: `medium`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
  - This packet uses one Codex-led conference object (`general_single_object`) with no sub-venue chair. Its effective `CST` route chain is `codebuddy-cli/deepseek-v4-flash:max -> codebuddy-cli/glm-5.3-flash:max -> grok-build/grok-4.6:medium -> cursor/cursor-grok-4.6:medium -> openai-codex/gpt-5.6-luna:max`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice08c3_contract_20260829`
- Execution evidence status: `no linked execution packet`
- Excluded provider/model nodes: none
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `context/medical_monitoring_r7_slice08c3_journey_changes_drawer_contract_20260829.md`
- `context/mm_r7_slice08c3_contract_conference_prompt_20260829.md`
- `reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_1_20260829.md` §8
- `reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md` §19–20（冲突时 v0.2 胜出）
- `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`
- `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Timeline.mjs`
- `frontend/src/features/medical-monitoring/r7/MedicalMonitoringR7ProductLoop.jsx`
- `frontend/src/features/medical-monitoring/r7/medicalMonitoringR7ContinuityFilter.mjs`
- `frontend/src/features/medical-monitoring/r7/medicalMonitoringR7ContinuityProjection.mjs`
- `context/medical_monitoring_r7_slice08c2_frontend_vertical_contract_20260829.md`
- 上述路径均为当前工作台内已授权只读对象，不包含生产写入。

## Scope

- In scope: 独立只读挑战 08C-3 最小合同的身份/轴窗、变化节点、详情抽屉、中文、可访问行为、legacy 边界、离线门禁与 08C-4 边界。
- Out of scope: 修改任何文件、实现源码、启动服务/浏览器/模型/真实项目、视觉验收、医学质量、R7 总体、生产或商业化。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- 结论必须为 ACCEPT 或 REVISE；只有全部 P0-P2 关闭后才可 ACCEPT。

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

## Loop Log

- 2026-08-29 23:52:07 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-30 00:00 CST: Round 1 returned REVISE. Generated review/metrics/run paths are the current packet's declared artifacts, not historical output; participant output file was created by this first runner pass. Codex adopted the substantive P1/P2 findings and updated contract to v0.2 plus this source packet.
