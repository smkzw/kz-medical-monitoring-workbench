# Conference Context: medical_monitoring_r1_integrated_closure_review_20260810

Created: 2026-08-10 03:59:56
Objective: 对R1隔离合成集成闭环做哈希绑定的独立反证审阅：重现幂等重入、双断点续跑、失败/跳过终态、QC证据损坏阻断、候选与事实隔离、7节点进度和同一run身份链；只读，不修改任何文件，不启动服务，不读取真实项目数据
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.5`, then Cursor CLI `cursor-grok-4.5-high`, then Pi/OpenCode Go `gpt-5.6-luna` (max), then Pi/Kimi `k3-256k` (high).
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/Alibaba `qwen3.8-max` (xhigh) during the Beijing 22:00-07:00 window, and outside that window its exact Qwen Max node is replaced by Pi/cms-smk `cms-model` (high); its remaining fallbacks are Pi/cms-smk `cms-model` (high), Pi/cms-smk `deepseek-v4-flash` (max), Pi/OpenCode Go `deepseek-v4-flash` (max), and Pi/DeepSeek `deepseek-v4-flash` (max). Participant 2 is Grok Build `grok-4.5`, with Cursor CLI `cursor-grok-4.5-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority. The explicit Luna native/CLI compatibility route remains available for execution roles that declare Codex subAgent.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `poc/medical_monitoring_ai_native_r1/src/mm_r1/integrated_closure.py` — SHA256 `508cb5b62e037d99ec7f77bdcde370a40e4fb3036dd2dfc7f4360d8c129a03a8`.
- `poc/medical_monitoring_ai_native_r1/scripts/run_integrated_closure.py` — SHA256 `e06325e8fdaa78ee47cc395c6633968c06277de6904205689e97b1e878815b5e`.
- `poc/medical_monitoring_ai_native_r1/tests/test_integrated_closure.py` — SHA256 `344d5beecea8ce1081f137bff6ee14625d9d69a624bd4730a8a0bb0ccad4d7d1`.
- `poc/medical_monitoring_ai_native_r1/docs/R1_INTEGRATED_CLOSURE_GAP_AUDIT.md` — SHA256 `8259c9259405ce1273941893f5cea7227ed0fcca461b4db7092af93d9bf1646c`.
- Only the isolated synthetic POC and its generated temporary directories are source material. Real study data and production paths are forbidden.

## Scope

- In scope: hash verification; read-only source review; isolated synthetic tests; adversarial reproduction of identity, idempotency, resume, failure/skip, QC corruption, publication, Query, progress, and CLI directory gates.
- Out of scope: code edits, service startup, port 8911, real providers, real projects, medical-writing subsystem, visual redesign, and R1-wide completion claims.

## Success Criteria

- Frozen hashes match before review; drift is an automatic rejection of the review target.
- Reviewer independently reproduces or directly falsifies completed re-entry, both close/reopen continuation points, failure and skip terminal states, raw/candidate evidence integrity gating, candidate/fact separation, shared temporal spine, three-part Query, 7-unit audience progress, and CLI empty-directory gate.
- Every acceptance claim cites an executed command or a precise source locator; author tests alone are insufficient.
- No source file is modified, no service/provider is started, no real project is read, and Codex retains final acceptance.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. A catalog/auth/transport health preflight timeout or malformed response is diagnostic and must still allow one live route attempt; only a missing CLI or an explicitly invalid, retired, or unlisted model may block before live dispatch. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-08-10 03:59:56: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-10 04:00 CST: native `gpt-5.6-luna` spawn was explicitly probed and rejected as an unknown model (runtime exposed only Sol/Terra). Per the global runtime contract, route changed to labeled ChatGPT Codex CLI compatibility fallback with the same Luna model and max effort; no substitute model was used.
