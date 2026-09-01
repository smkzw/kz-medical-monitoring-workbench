# Conference Context: medical_monitoring_r4_d07_oracle_adjudication_20260814

Created: 2026-08-14 06:00:53
Objective: 独立裁定 D07 当前 63 条 runtime/oracle 差异中的冻结工件矛盾与可修复实现缺陷，给出 case-id-free 的最小勘误或实现准则；不得修改文件。
Task type: `high_risk_contradiction_review`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.6` (high), then the distinct Cursor `cursor-grok-4.6-high` route, then the distinct Pi/OpenCode Go `gpt-5.6-luna` (max) route. The Codex subAgent Luna route remains a separate native/CLI compatibility path.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/Alibaba `qwen3.8-max` (xhigh) during the Beijing 22:00-07:00 window, with first backup Pi/OpenCode Go `deepseek-v4-pro` (max) and the original Flash fallback retained after it; during the night window, its CMS-SMK Flash fallback is rewritten to Pi/OpenCode Go `deepseek-v4-flash` (max). Outside that window, participant 1 uses the specific daytime chain Pi/CMS-SMK `deepseek-v4-flash` (max) -> Pi/OpenCode Go `deepseek-v4-pro` (max) -> Pi/OpenCode Go `deepseek-v4-flash` (max). Other exact Qwen Max nodes use the global daytime replacement Pi/OpenCode Go `deepseek-v4-pro` (max). Participant 2 is Grok Build `grok-4.6` (high), with the distinct Cursor `cursor-grok-4.6-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority. The explicit Luna native/CLI compatibility route remains available for execution roles that declare Codex subAgent.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- Frozen D07 contract `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md` SHA-256 `0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84` and its frozen catalog/oracle/registry.
- Freeze acceptance record `context/medical_monitoring_r4_d07_artifact_freeze_acceptance_record_20260813.md`.
- Current runtime and test harness under `poc/medical_monitoring_ai_native_r4/`.
- Current execution evidence: `runs/execution/medical_monitoring_r4_d07_runtime_20260813/worker_01_followup1.md`, `worker_02.md`, `worker_03.md`, and `manager.md`.
- Filesystem and reproducible commands are authoritative; reports are claims to verify.

## Scope

- In scope: read-only reproduction and adjudication of the 63 current case-level mismatches; decide for each band whether contract+typed input determine runtime behavior, oracle is inconsistent, fixture lacks authority, or runtime remains wrong.
- Required bands: 42 source-jump cases, 6 anchored-count cases, AST grade cases 010/085/093/094/100/101/102/106, visit-ref cases 012/039/060/076/090/103, case 017 grade state, case 103 priority, case 106 trend.
- Out of scope: editing any source/artifact; case-id-dependent fixes; weakening exact-leaf checks; product/R5 UI/real project/medical-writing work; services; regulatory conclusions.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Each participant returns a case-band decision table with direct contract/input/oracle/runtime evidence, a minimal case-id-free correction rule when derivable, and an explicit `oracle_erratum_required` decision only when impossibility is demonstrated.
- For AST, identify the actual selected range and grade-rule operands and show the Decimal calculation; do not substitute external clinical memory for the frozen project-bound rule.
- For Journey anchored count, compare normalized typed inputs and explain whether any contract predicate can distinguish case 134.
- For source jumps and visit refs, derive target membership from typed join roles, accepted locators, reverse binding and shared-spine rules; arbitrary oracle mimicry is rejected.

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

- 2026-08-14 06:00:53: Conference initialized by `hermes_workflow_guard.py init-conference`.
