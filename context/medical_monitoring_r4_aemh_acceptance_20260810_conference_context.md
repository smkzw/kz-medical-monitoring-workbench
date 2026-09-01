# Conference Context: medical_monitoring_r4_aemh_acceptance_20260810

Created: 2026-08-10 23:11:04
Objective: Independent acceptance review of stable synthetic R4 AE/MH longitudinal risk slice against FROZEN_R4_CONTRACT_V1, with public R2/R3 integration, fail-closed identity and close gates, Query/journey projections, and protected boundaries
Task type: `high_risk_contradiction_review`
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

- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` at SHA-256 `6bb9f73a56de7e3ba38532b4fd3edadc76d788a099186f7c60212fb9c4a92705`.
- `poc/medical_monitoring_ai_native_r4/` current filesystem snapshot. Its cache-excluded file-manifest digest before conference dispatch is `545605e34bbda2b8eb67794952c3689edc17dc21a512b583dd73f3d343b7b277`.
- Frozen public authorities used read-only: `poc/medical_monitoring_ai_native_r2/src/mm_r2/{risk,identity,acceptance}.py`, `poc/medical_monitoring_ai_native_r3/src/mm_r3/normalization.py`, and their focused tests.
- Design/plan boundary: `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` and `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`.
- Deterministic pre-dispatch anchors: R4 `213 passed`; focused R2 risk/identity `213 passed, 385 deselected`; focused R3 normalization/mapping/date `126 passed, 213 deselected`; Ruff/compile/root import green; port 8911 stopped.

### Cache-Excluded R4 Digest Recipe

The digest is path-sensitive and must be run from `poc/medical_monitoring_ai_native_r4` so paths begin with `./`:

```bash
find . -type f \
  ! -path '*/__pycache__/*' \
  ! -path '*/.pytest_cache/*' \
  ! -path '*/.ruff_cache/*' \
  -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256
```

Running the same pipeline from the workbench root intentionally produces a different digest because the path strings differ.

## Scope

- In scope: independent read-only contradiction review of R4 common coverage primitives and the D01 AE/MH longitudinal slice: identity stability and pre-side-effect validation, exact close proof, L0/L1/L1b/L2/L3 separation, partial-date uncertainty, NCS/alternative-diagnosis handling, monitoring priority, Query draft and journey projection joins, package exports, deterministic synthetic tests.
- Out of scope: edits; product/runtime integration; frontend or browser acceptance; other R4 domains; R5-R8; real project data; medical-writing; services; port 8911; security design/testing; clinical or regulatory final authority.

## Success Criteria

- Each reviewer independently inspects actual code and tests and returns ACCEPT, ACCEPT_WITH_GAPS, or VETO with file/line evidence and reproducible commands.
- No material contract clause is accepted solely because an existing test passes; reviewers challenge identity tampering, cross-export identity, exact historical-negative linkage, uncertainty carry-forward, and object-count/query-source joins.
- The R4 snapshot is unchanged throughout review; any source drift invalidates the verdict and requires a fresh digest.
- No product, medical-writing, real-project, R1-R3, or service write; 8911 remains stopped; Codex retains final acceptance.

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

- 2026-08-10 23:11:04: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-08-10: Source packet frozen at cache-excluded manifest digest `545605e34bbda2b8eb67794952c3689edc17dc21a512b583dd73f3d343b7b277`; reviewers assigned read-only independent passes.
- 2026-08-11: Initial reviewers independently identified public machine-close proof, unknown priority, identity ambiguity, study-start boundary, `same_day`, and SAE/AESI projection gaps. Codex repaired only R4 source/tests and reran all deterministic anchors.
- 2026-08-11: Final R4 cache-excluded digest `f100a0344db27f1d6e404a8b1fdd88a849dd43e5f0996a2e9e609b1c42546550`; R4 224, focused R2 213, focused R3 126, Ruff/compile/import/hash/8911 gates green.
- 2026-08-11: Beijing daytime participant-1 effective route `cms-smk/cms-model` returned ACCEPT after running focused/full tests; Cursor fallback same session returned ACCEPT after targeted source re-review. Codex accepted the isolated synthetic R4-D01 slice only.
