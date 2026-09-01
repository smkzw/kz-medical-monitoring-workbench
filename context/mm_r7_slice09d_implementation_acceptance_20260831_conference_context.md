# Conference Context: mm_r7_slice09d_implementation_acceptance_20260831

Created: 2026-08-31 01:16:49 CST
Objective: 对 R7 Slice-09D synthetic/offline 实现做独立反证验收：核查冻结合同 v0.2 的 corpus/oracle/measurement/fault-recovery/DTO/anti-overfit/回归证据是否真实闭合，特别识别自证 oracle、伪故障注入、环境不可比误声明、硬编码与未覆盖合同条款；输出 P0-P4、ACCEPT/REVISE 和最小修订。禁止真实项目/模型/浏览器/服务/三端口/医学写作/安全专项。
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.


## Preferred Browser Advisory Chair

- Role: `chatgpt-web-pro-advisory` via `codex-with-chatgpt`.
- Assignment: preferred advisory chair for complex, logic-, evidence-, or artifact-heavy work.
- UI selection: `Pro` / `GPT-5.6 Sol`; the visible UI state must be positively verified.
- Boundary: read-only C2C advisory chair, not a runner subprocess or executable participant. Reuse the same session, perform 20-30 second foreground DOM checks, and persist `c2c session` / `c2c record` state. A browser timeout is pending, not failure; there is no automatic callback.
- Codex remains the formal packet chair and final authority. If the advisory response is unavailable or invalid, continue the declared executable panel.


## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
  - This packet uses one Codex-led conference object (`general_single_object`) with no sub-venue chair. Its effective `CST` route chain is `codebuddy-cli/deepseek-v4-flash:max -> codebuddy-cli/glm-5.3-flash:max -> grok-build/grok-4.6:medium -> cursor/cursor-grok-4.6:medium -> openai-codex/gpt-5.6-luna:max`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice09d_implementation_20260831`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `codex/gpt-5.6-luna`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice09d_capacity_performance_recovery_contract_v0_2_20260831.md` — 冻结接受的 09D 合同。
- `artifacts/mm_r7_slice09d_implementation_20260831/` — 本轮隔离实现、固定证据与有界测量产物；须审查源码而非仅信任 JSON 自报。
- `runs/execution/mm_r7_slice09d_implementation_20260831/worker_01.md`、`worker_02.md`、`worker_03.md` — 三个执行角色的声明与限制。
- `context/medical_monitoring_r7_slice09a_implementation_acceptance_record_20260830.md`、`...slice09b...`、`...slice09c...` — 已接受接缝的范围与计数基线。
- Codex 当前复验：09D focused `26 passed`、R1 `327 passed`、R7 `526 passed, 19 warnings`；8911/5174/8984 无监听。
- 当前文件系统为事实；不得以执行角色自述替代源码、测试和 manifest 的重算。

## Scope

- In scope: 逐条对照合同 §2–§8，审查 corpus/oracle、测量 runner/schema、故障/恢复矩阵、中文 DTO、静态与 mutation guard、环境不可比裁决及固定证据可重算性。
- In scope: 明确区分“矩阵声明/模拟证据”“真实 seam 故障注入”“容量观察”“通用容量声明”，寻找自证循环、覆盖缺口和误导性通过。
- Out of scope: 修改文件、读取真实项目、调用真实模型或 harness、运行浏览器/服务、启动三端口、医学写作、安全专项、R8 source admission。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- 每个发现引用合同条款与具体源码/证据路径；按 P0-P4 分类并给出 `ACCEPT` 或 `REVISE`。
- 对阻断项给出最小、可验证且不触碰真实项目的修订；不得以测试数量替代条款闭合。

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

- 2026-08-31 01:16:49 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
