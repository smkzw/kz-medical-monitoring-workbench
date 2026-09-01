# Conference Context: mm_r7_slice07a_progress_ui_visual_acceptance_20260828

Created: 2026-08-28 22:31:55 CST
Objective: 独立审阅修复后的 R7 Slice-07A synthetic 进度界面是否满足中文原生医学监察员的视觉与交互合同；核对最终 v2 失败态层级、ego(lite) DOM/键盘证据、1280 宽屏、R5/R7 同页呈现及最小修复，不修改文件、不运行真实项目、不触碰医学写作，并给出 accept_limited 或 revise。
Task type: `visual_delivery_conference`
Risk: `high`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
- This packet uses one Codex-led conference object (`visual_single_object`) with no sub-venue chair. Its effective `CST` route chain is `cursor/cursor-grok-4.6:high -> codebuddy-cli/glm-5.3:max`; it is resolved once at packet creation and filtered against the actual execution route nodes recorded below before dispatch.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice07a_progress_ui_ego_acceptance_20260828`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `kimi-code/k3-256k`, `grok-build/grok-4.6`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice_07a_progress_ui_contract_v1_20260828.md`
- `evidence/mm_r7_slice07a_progress_ui_ego_acceptance_20260828/postfx_r5/failed_fullpage_r5_1920x1080_chrome_v2.png`
- `evidence/mm_r7_slice07a_progress_ui_ego_acceptance_20260828/postfx_r5/ego_live_postfix_observations.json`
- `evidence/mm_r7_slice07a_progress_ui_ego_acceptance_20260828/postfx_r5/README.md`
- Current R7 source under `frontend/src/features/medical-monitoring/r7/` and
  the shared synthetic fixture under
  `artifacts/mm_r7_slice07a_progress_ui_ego_fixture_20260828/`.
- Do not add production paths unless the user explicitly authorized reading them for this task.

## Scope

- In scope: final v2 failed-state glance hierarchy; R5/R7 full-page
  co-rendering; ego(lite) 1280, identity and stop-confirm evidence; bounded
  synthetic Slice-07A acceptance.
- Out of scope: real projects, medical findings quality, Patient Journey,
  Slice-07B flow dashboard, medical-writing source and security design/testing.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.

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

- 2026-08-28 22:31:55 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
- This packet refreshes the live guard role schema only. It must reuse the
  existing Cursor session `01a0489c-7345-7000-a341-14d0fd929b11`; the prior
  same-session participant already challenged and then accepted the v2 visual.
