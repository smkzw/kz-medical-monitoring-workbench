# Conference Context: mw_translation_fidelity_v26_20260718

Created: 2026-07-19 04:19:25
Objective: 审阅AD竞品方案真实Hy-MT2翻译v26的ch07/ch09忠实度阻断，区分真实错译与门禁误报，在Hy-MT2独占正文翻译且DeepSeek只做上层识别/QC/语料选取的边界下提出最小可验证修复
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no sub-venue chair: Grok Build `grok-4.5` (`grok-build`) and Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning). For either unavailable primary role, the runner tries Hermes OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / cms-model` and Hermes OpenCode Go `deepseek-v4-flash`. Any unavailable complex-task role follows Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning), then Reasonix CLI `deepseek-v4-flash`, then Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as a declared fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- User boundary recorded in
  `records/USER_REQUIREMENTS_CURRENT_20260718.md`: Hy-MT2 is the sole body
  translator; DeepSeek Flash/Pro may perform chapter recognition/decomposition,
  post-Hy continuity/fidelity QC and corpus selection, but may never translate,
  rewrite or replace body text.
- Current source and implementation:
  - `services/api/app/chapter_translation_pipeline.py`
  - `services/api/app/writing_reference.py`
  - `services/api/app/regulatory_translation_glossary.py`
  - `services/api/app/main.py`
  - `tests/test_mw_v11_translation_alignment.py`
  - `tests/test_writing_reference.py`
  - `tests/test_mw_round3_backend_remediation.py`
- v26 evidence:
  - `runs/execution/mw_cross_indication_reference_release_gate_20260718/cross_indication_e2e_run_v26_ad/AD/lane_report.json`
  - read-only snapshot of the preserved runtime database:
    `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/v26_writing_reference_readonly.sqlite3`.
    It was copied from the isolated v26 runtime after completion and is
    conference evidence only.
- The official source artifact is ClinicalTrials.gov Protocol/SAP for
  NCT05923099, SHA-256
  `b7e58931f716336f05d3c36a3f712204234868190b283af70bb270e408268b56`.

## Scope

- In scope: identify the exact source/Hy output behind every ch07 and ch09 v26
  failure code; classify each as true translation defect, extraction/chunking
  defect, Flash-QC false positive, or deterministic-gate false positive; propose
  the smallest testable correction that preserves the model-role boundary.
- In scope: inspect whether failure evidence is sufficiently unit-localized and
  auditable for production diagnosis.
- Out of scope: editing production source, changing medical meaning, admitting
  blocked corpus, replacing Hy text with DeepSeek text, weakening a valid
  fidelity gate merely to make E2E pass, frontend redesign, or final release.

## Success Criteria

- Each failure code has source text, Hy text, classification, confidence and
  locator.
- Recommendations preserve Hy-MT2 as sole body translator and keep DeepSeek
  non-authoring.
- True defects remain blocked until corrected by Hy-MT2 and rechecked;
  demonstrable false positives receive a narrow deterministic fix plus an
  adversarial regression test.
- Proposed changes include a rerun plan for focused tests, real Hy probes and a
  fresh isolated AD E2E; no recommendation relies on HTTP 200 alone.
- Output clearly separates evidence, inference, recommendation and uncertainty.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 240 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use 30 and 40 respectively.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- All participants are read-only. Do not modify source, tests, the preserved
  runtime database or official artifact.
- DeepSeek output is review evidence only. It cannot become, repair or replace
  translated body text.

## Loop Log

- 2026-07-19 04:19:25: Conference initialized by `hermes_workflow_guard.py init-conference`.
