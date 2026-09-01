# Conference Context: medical_monitoring_r4_d04_implementation_acceptance_20260812

Created: 2026-08-12 03:39:43
Objective: 对冻结的R4 D04实现快照进行独立医学方案语义与工程确定性双角色会商验收
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3-256k` (high). If unavailable, the runner tries Grok Build `grok-4.5`, then the distinct Cursor `cursor-grok-4.5-high` route, then the distinct Pi/OpenCode Go `gpt-5.6-luna` (max) route. The Codex subAgent Luna route remains a separate native/CLI compatibility path.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use a Codex-chaired panel with no sub-venue chair. Participant 1 is Pi/Alibaba `qwen3.8-max` (xhigh) during the Beijing 22:00-07:00 window. Outside that window its exact Qwen Max node is replaced by Pi/OpenCode Go `deepseek-v4-flash` (max); during the night window, every exact Pi/cms-smk `deepseek-v4-flash` node is replaced by the same Pi/OpenCode Go route. Its remaining fallbacks are Pi/cms-smk `deepseek-v4-flash` (max), Pi/OpenCode Go `deepseek-v4-flash` (max), and Pi/DeepSeek `deepseek-v4-flash` (max), with effective-route deduplication. Participant 2 is Grok Build `grok-4.5`, with the distinct Cursor `cursor-grok-4.5-high` and Pi/cms-router `minimax-m3` as fallbacks. Codex remains the final authority. The explicit Luna native/CLI compatibility route remains available for execution roles that declare Codex subAgent.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- Frozen D04 contract: `reviews/medical_monitoring_r4_d04_protocol_pd_slice_contract_v1_20260812.md`, SHA-256 `6d0a7ee2fe507555f68f7a719c60dfa2cc92f995fcaf2c4a3825bbcb3bc6d6b5`.
- Rejected v1 implementation snapshot: `context/medical_monitoring_r4_d04_implementation_snapshot_20260812.md`.
- Authoritative corrective snapshot for final acceptance: `context/medical_monitoring_r4_d04_implementation_snapshot_v2_20260812.md`, SHA-256 `ca8a55044d83f7f5af5b378d0ba1c938b9e6c100e9fad57d657182186fded4b7`.
- Current implementation/tests under `poc/medical_monitoring_ai_native_r4/`; frozen dependencies under R1/R2/R3 are read-only.
- Independent execution-manager report: `runs/execution/medical_monitoring_r4_d04_implementation_20260812/manager.md` is Codex context only. Conference participants must not read worker or manager reports and must derive their own result from the contract, snapshot, code and tests.
- Current filesystem is authoritative. No production path or real project may be read.

## Scope

- In scope: frozen D04 protocol/applicability/evidence/combination/coverage/priority/lifecycle adapter/Journey projection semantics; 83-row challenge traceability; deterministic identities; public object identity; D02/D03/D05 ownership boundaries; Chinese-native audience labels; focused/full isolated tests.
- Out of scope: R5 renderer/UI, visual browser acceptance, real projects, production services, OCR/VLM, provider integration, commercial release claims, security design/testing, medical-writing subsystem, edits of any kind.

## Success Criteria

- Each reviewer independently verifies the frozen contract and every snapshot hash before/after review; drift is automatic `REVISE`.
- Medical/clinical reviewer tests whether the implementation preserves official criterion numbering, version/phase/cohort/subject applicability, rule-specific evidence gates, uncertainty boundaries and neutral potential-PD wording without claiming confirmed/reportable PD.
- Engineering reviewer tests deterministic identities, immutable values, exact expected-set/cardinality/count invariants, generated-and-consumed evidence requirements, strict bool flags, single lifecycle/identity/Query/coverage authority, typed Journey joins and public object identity.
- 83 challenges are continuous and traceable to executable or named adjacent accepted tests; final v2 full R4=985, R2=598 and R3=339 remain green, Ruff/compileall pass, and 8911 stays stopped.
- Each reviewer returns `ACCEPT` or `REVISE` with file/line-level evidence and one minimal remediation per blocking finding. No reviewer edits files or reads another reviewer/worker/manager output.
- Codex compares both independent outputs, performs final deterministic checks and owns acceptance.

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
- Review is synthetic/offline and read-only. Do not start services, inspect real studies, touch R5 or medical writing, install packages, run security work, or infer regulatory finality beyond the frozen contract.

## Loop Log

- 2026-08-12 03:39:43: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-12: v1 was rejected by both usable independent reviewers; Codex reproduced the amendment-transition defect.
- 2026-08-12: v2 corrective snapshot frozen; Qwen and Cursor fallback rechecked their own original sessions and both returned `ACCEPT` with stable hashes.
