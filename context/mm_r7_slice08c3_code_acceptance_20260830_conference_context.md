# Conference Context: mm_r7_slice08c3_code_acceptance_20260830

Created: 2026-08-30 00:46:54 CST
Objective: 独立审阅R7 Slice-08C-3合并后当前源码与测试，重点验证同身份同轴窗变化绑定、R7-only抽屉路由、overlay/push焦点键盘语义、中文医学标签、legacy R5隔离和离线回归；列出P0-P4并仅在P0-P2关闭后接受，视觉浏览器验收明确留08C-4
Task type: `code_open_audit`
Risk: `medium`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
  - This packet uses one Codex-led conference object (`general_single_object`) with no sub-venue chair. Its effective `CST` route chain is `codebuddy-cli/deepseek-v4-flash:max -> grok-build/grok-4.6:medium -> cursor/cursor-grok-4.6:medium -> openai-codex/gpt-5.6-luna:max`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice08c3_implementation_20260830`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `codebuddy-cli/glm-5.3-flash`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `context/medical_monitoring_r7_slice08c3_journey_changes_drawer_contract_20260829.md`（冻结合同）
- `context/medical_monitoring_r7_slice08c3_contract_acceptance_record_20260830.md`
- `reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md` §19–20
- `frontend/src/features/medical-monitoring/r7/medicalMonitoringR7JourneyChanges.mjs` 及测试
- `frontend/src/features/medical-monitoring/r7/medicalMonitoringR7JourneyDrawerModel.mjs`
- `frontend/src/features/medical-monitoring/r7/MedicalMonitoringR7JourneyDrawer.jsx` 与 CSS、渲染/交互测试
- `frontend/src/features/medical-monitoring/r7/MedicalMonitoringR7ProductLoop.jsx` 及 continuity 集成测试
- `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`、`medicalMonitoringR5.css` 及相邻测试
- `reviews/codex_execution_mm_r7_slice08c3_implementation_20260830_review.md`
- `metrics/mm_r7_slice08c3_implementation_20260830_execution_metrics.md`
- 当前文件系统与实际测试输出为最终真相；不得以 worker 自述替代源码和测试。

## Scope

- In scope: 只读审阅合并后的 08C-3 源码与测试；验证同项目/结果/中心/受试者/访视轴/时间窗绑定、七类变化语义、八域中文标签、R7-only 路由、关闭/切换行的身份保持、overlay/push 焦点与键盘合同、legacy R5 隔离、项目/路径中性和离线回归。输出 P0-P4、证据行与可执行修复建议。
- Out of scope: 不修改任何源码或过程文件；不启动 8911/5174、浏览器、真实项目或模型；不进行视觉质量、动效、真实焦点、1280/1440/1920 或 ego(lite) 验收；不触碰医学写作子系统；不声称 R7 总体或生产完成。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- 所有 P0-P2 均有源码级证据；若存在则结论必须为 REVISE，关闭后使用同一 session 复核；无 P0-P2 时方可给出 ACCEPT。

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

- 2026-08-30 00:46:54 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
