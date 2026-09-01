# R6 runtime slice-07 Agent Harness limited acceptance record

Date: 2026-08-28
Decision: `ACCEPT_R6_RUNTIME_SLICE_07_AGENT_HARNESS_ADAPTER_LIMITED`

## Accepted scope

The isolated R6 POC `ExecutionProfile` registry and `omp_print_v1` adapter. Acceptance covers layered profile freeze, exact alias-to-selector mapping, deterministic profile identity, public catalog and frozen-profile preflight, argv construction, invocation receipt, fail-closed parse/coverage/exit handling, Chinese user-progress projection, and explicit no-fallback behavior.

The default user-facing profile is `mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`; the effective OMP selector is `mtplx/Youssofal/Qwen3.8-27B-MTPLX-Optimized-Quality`. Explicit `deepseek/DeepSeek V4 flash:max` maps to `deepseek/deepseek-v4-flash:max`. Model configuration remains in the harness registry and is not embedded in medical business objects.

## Frozen candidate

- Source: `poc/medical_monitoring_ai_native_r6/src/mm_r6/agent_harness.py` — `0546c10c51a57795c521b2f605276e02c06c676bfe8625268863d8ddc961a515`
- Tests: `poc/medical_monitoring_ai_native_r6/tests/test_agent_harness.py` — `57326dced117c1ae29499b265bdd7a1859ae375e05b56e094843725141147155`
- Receipt: `poc/medical_monitoring_ai_native_r6/evidence/r6_agent_harness_runtime_receipt.json` — `fd61f5483360476d4f76d6a9f61642fe83aa69799a64f7aefb36cd44c126d98d`
- Contract: `context/medical_monitoring_r6_runtime_slice_07_agent_harness_contract_20260828.md`

## Decisive evidence

- Focused suite: `35 passed in 0.95s`; full R6 POC: `763 passed in 7.12s`.
- Parent-asserted normal/`-O`/`-OO` × `PYTHONHASHSEED=0/1/42` identity/argv matrix: 9/9 cells passed.
- Post-repair authentic synthetic OMP smoke, MTPLX medium: exit 0, parsed, `analysis_complete=true`, zero missing units, no fallback; stdout SHA-256 `044834adf2119be39a9d4e3e9e84acba68536591d59051d4d7a151e3cda9fc7a`.
- Post-repair authentic synthetic OMP smoke, DeepSeek max: exit 0, parsed, `analysis_complete=true`, zero missing units, no fallback; stdout SHA-256 `2bb411a1df3ffa789df7b8edcaf229555fae808c41f7cd70abe07da02078acd8`.
- Medical-writing protected tree remained 542 files at aggregate `feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca`.
- Ports 8911 and 5174 remained stopped. No product service, browser, OCR, real project, frontend or medical conclusion was used.

## Defects closed

Codex reconciled concurrent worker writes and closed inherited allowlist failures, profile-ID-only rebase failure, forged frozen identity acceptance, injected-preflight bypass, unsafe invocation IDs, duplicate expected units, catalog provider/model mismatch, unknown exit-code fail-open, and NDJSON coverage fail-open.

The independent Grok round-1 review reproduced the NDJSON P1: the prior extractor could select the first valid object and promote incidental brace fragments from prose. The repaired parser accepts only a whole assistant chunk or whole fenced JSON object, uses the last valid object, routes single-event OMP envelopes through the same extractor, and rejects incomplete coverage. The original Grok session reproduced both counterexample closures and accepted the current SHA-pinned candidate.

## Independent-review qualification

The Pi participant accepted the pre-repair candidate, but its later same-session reports continued to cite obsolete test counts and SHAs. It is retained as round-1 corroboration only and is not counted as current-candidate acceptance evidence. Final current-candidate evidence is the Grok same-session repair verification plus Codex's independent reruns and SHA checks.

## Explicit limitations

- The print adapter does not provide continue/resume/cancel lifecycle support.
- `produced_units` is a model-claimed name set adequate only for this synthetic connectivity contract; it is not sufficient evidence of future medical coverage.
- The last valid assistant JSON object is trusted only within this bounded synthetic contract.
- Raw smoke stdout remains temporary under `/tmp`; durable evidence records its hash and byte length.
- The frozen worker receipt correctly does not claim Codex acceptance; this record supplies the later authority without altering the frozen receipt.

## Not accepted

Product persistence/API/runner integration, background long-task control, real project or report use, medical correctness or quality, browser/visual behavior, Patient Journey, Query dispatch, R6 overall, R7, or R8.

## Governance closure

- Governed execution task `mm_r6_runtime_slice_07_agent_harness_20260828` passed execution review-gate and audit with no warnings or errors.
- Linked conference task `mm_r6_runtime_slice_07_agent_harness_acceptance_20260828` passed conference review-gate and `validate-conference`.
- Conference topology was the live Codex-led panel with no sub-venue chair; no fallback or Hermes transport was used.
- After all gates passed, the execution prompt/run/log packet was moved recoverably to `archives/execution/mm_r6_runtime_slice_07_agent_harness_20260828/`; contract, source, tests, receipt, reviews, metrics and this acceptance record remain durable.
- The Pi/Grok conference session IDs are not Hermes `state.db` sessions. The archive tool's dry run returned `session not found`, so no false session-archive claim or destructive cleanup was made. Their durable review/metrics evidence remains in the workspace.
- A post-cleanup `audit-execution` cannot rediscover a packet after it has been moved and therefore reports zero prompts; the authoritative audit is the successful pre-cleanup audit already captured in the execution review. This expected post-archive diagnostic is not a candidate regression.

## Next safe action

Freeze the first R7 product-integration contract for ExecutionProfile persistence/API and the run-entry binding. Keep credentials as references, keep model/provider/effort out of medical objects, preserve explicit MTPLX-default and DeepSeek-max behavior, and defer frontend/Patient Journey, long-session recovery, real projects and medical-quality claims until their own governed slices.
