# Conference Context: medical_monitoring_r1_overall_acceptance_20260810

Created: 2026-08-10 04:18:19
Objective: 对隔离 synthetic 医学监查 R1 步骤1-13进行总体验收：逐项建立代码/测试/浏览器/独立审阅证据矩阵，识别仍断链或未证明项；只更新验收记录，不修改产品或医学写作源码，不启动8911，不运行真实项目，只有全部R1完成证据通过才允许进入R2
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

- Approved requirements: `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
  and `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`, especially R1
  steps 1-13 and their completion evidence.
- Current isolated implementation: `poc/medical_monitoring_ai_native_r1/`.
- Stage evidence and decisions: `poc/medical_monitoring_ai_native_r1/docs/`,
  `poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/docs/`, and the accepted Codex
  execution/conference reviews under `reviews/`.
- Audience-facing browser anchors:
  `output/playwright/medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809/`
  and `output/playwright/medical_monitoring_r1_patient_journey_slice4_20260809/`.
- The current filesystem is authoritative. Historical counts and hashes remain historical evidence;
  current acceptance uses current files and newly rerun checks.

## Scope

- In scope: read-only/code-neutral audit of every R1 step; a 13-row code/test/browser/review
  evidence matrix; correction of stale or ambiguous acceptance records; deterministic reruns;
  fresh-context independent challenge; final R1 decision and recovery checkpoint.
- Allowed writes: this task context, `poc/medical_monitoring_ai_native_r1/docs/`, R1 review/metrics
  records, and the implementation-plan recovery point. No implementation repair is allowed unless
  the audit first demonstrates a concrete R1 blocker and the repair remains inside the isolated POC.
- Out of scope: product source/runtime/database, medical-writing subsystem, real project data,
  provider credentials or calls, 8911, five real projects, commercial/clinical/regulatory readiness,
  R2 implementation before R1 acceptance.

## Success Criteria

- Every R1 step 1-13 has a current locator to implementation/decision, deterministic test evidence,
  and—where applicable—real browser evidence; no stage is accepted from a TODO or worker self-report.
- R1-specific blockers are separated from R4/R7/product residuals. The matrix may not downgrade an
  explicit R1 requirement merely by relabeling it.
- Current core, AE/MH audience and Patient Journey suites pass; browser summaries are green and
  user-facing language remains free of internal/runtime labels.
- Independent fresh-context review receives the requirements, matrix, artifacts and check output,
  may veto, and owns the final R1 completion recommendation. Codex independently decides acceptance.
- No protected path is modified, no real project/provider is used, and port 8911 remains stopped.

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

- 2026-08-10 04:18:19: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-10 04:35: Pi/Qwen completed a full tool-backed falsification pass and recommended isolated-R1
  ACCEPT; it found a documentation overclaim on performance and non-blocking evidence-provenance residuals.
- 2026-08-10 04:43: Grok rounds 1-2 were cancelled during MCP initialization; the same session completed
  round 3 without tools and recommended a scope-limited ACCEPT. Its conclusion was treated as weaker than
  the Pi/Qwen and Codex deterministic evidence, not as replacement evidence.
- 2026-08-10 04:45-04:53: Codex reopened audience screenshots, found prohibited internal/English labels
  missed by the panel, corrected only the isolated R1 assets/core Query copy, regenerated synthetic data,
  added source/browser language gates, and reran 326 core + 19 audience + 17 Journey tests green.
- 2026-08-10 04:54: port 8911 remained stopped; no product, medical-writing, provider or real-project path
  was used. R1 was accepted only as a synthetic/offline isolated POC and R2 became the next safe stage.
- 2026-08-10 05:06: Luna CLI compatibility review exposed one real public-API gap:
  `AttemptLifecycleObserver` was module-public but not root-package-public. Codex added the missing root
  import plus a deterministic contract test; core became 327 green. The old SHA review was invalidated
  deliberately and the repaired snapshot was sent back to the existing independent verifier.
