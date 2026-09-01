# Conference Context: mm_r7_slice09e_implementation_acceptance_20260831

Created: 2026-08-31 10:32:39 CST
Objective: 独立审阅 R7 Slice-09E 本地分发与数据处置壳层的实际源码、测试与执行证据；核查其是否严格限于合成离线验收，是否存在并发升级、端口归属、路径身份、卸载数据处置、医学写作隔离、过度工程化或虚假完成声明；仅在所有 P0-P2 阻断关闭且证据充分时接受。
Task type: `code_open_audit`
Risk: `medium`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.


## Preferred Browser Advisory Chair

- Role: `chatgpt-web-pro-advisory` via `codex-with-chatgpt`.
- Assignment: preferred advisory chair for code review.
- UI selection: `Pro` / `GPT-5.6 Sol`; the visible UI state must be positively verified.
- Boundary: read-only C2C advisory chair, not a runner subprocess or executable participant. Reuse the same session, perform 20-30 second foreground DOM checks, and persist `c2c session` / `c2c record` state. A browser timeout is pending, not failure; there is no automatic callback.
- Codex remains the formal packet chair and final authority. If the advisory response is unavailable or invalid, continue the declared executable panel.


## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
  - This packet uses one Codex-led conference object (`general_single_object`) with no sub-venue chair. Its effective `CST` route chain is `cms-router/minimax-m3:xhigh -> google-antigravity/gemini-3.7-flash:high -> opencode-go/muse-spark-1.2-contributor:xhigh -> openai-codex/gpt-5.6-luna:max`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice09e_implementation_20260831`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `cursor/default`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- `reviews/medical_monitoring_r7_slice09e_local_distribution_contract_v0_2_20260831.md`（冻结验收合同）
- `context/medical_monitoring_r7_slice09e_contract_acceptance_record_20260831.md`
- `deploy/medical_monitoring_local/manage.py`
- `deploy/medical_monitoring_local/manage.zsh`
- `deploy/medical_monitoring_local/distribution.py`
- `deploy/medical_monitoring_local/release_sources.json`
- `deploy/medical_monitoring_local/README.md`
- `tests/test_medical_monitoring_local_distribution.py`
- `reviews/codex_execution_mm_r7_slice09e_implementation_20260831_review.md`
- `metrics/mm_r7_slice09e_implementation_20260831_execution_metrics.md`
- `artifacts/mm_r7_slice09e_implementation_20260831/`
- `runs/execution/mm_r7_slice09e_implementation_20260831/`
- 上述文件与当前文件系统为唯一事实来源；不得读取真实研究项目，也不得把历史过程说明当成运行事实。

## Scope

- In scope: 源码和测试的只读独立审计；合成离线行为；端口归属；路径身份；升级准备并发；卸载预览；发布清单；医学写作隔离；中文用户表达；最小实现；完成声明边界。
- Out of scope: 修改源码；启动 8911/5174/8984；浏览器/UI；真实安装包、签名、公证、Windows 安装器；真实项目；模型调用；任何删除；医学写作源码。

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- 所有 P0-P2 均关闭；P3/P4 必须有明确处置或接受理由。
- 验收词只能是“R7 Slice-09E 合成离线本地分发与数据处置壳层”，不得扩张为真实可发布安装包、R7 整阶段完成或 R8 就绪。
- 独立审阅者必须直接检查实现和测试，并至少挑战一个高影响假设。

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

- 2026-08-31 10:32:39 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
