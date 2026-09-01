# Conference Context: mw_ad_translation_fidelity_review_20260718

Created: 2026-07-18 19:10:54
Objective: 基于AD真实端到端证据，审阅ClinicalTrials.gov方案翻译、Flash整合QC与确定性忠实度门的架构，区分真实翻译缺陷与规则假阳性，提出不降低科学性和监管规范性的可执行修复与复测方案
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

- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
  records the original gate, model contract, prior failed paths and current
  decision boundary.
- `runs/execution/mw_cross_indication_reference_release_gate_20260718/cross_indication_e2e_run_v10/AD/lane_report.json`
  is the fresh end-to-end AD report from product search through translation.
- `runs/execution/mw_cross_indication_reference_release_gate_20260718/cross_indication_e2e_run_v10/AD/translation_fidelity_evidence.json`
  contains the two complete public ClinicalTrials.gov source chapters, each
  Hy-MT2 source/translation chunk, final integrated Chinese text, hashes and
  failure codes. It was extracted read-only from the preserved isolated v10
  SQLite runtime and contains no credentials.
- `services/api/app/main.py` contains the production Flash planner, Hy-MT2 and
  Flash integration-QC adapters.
- `services/api/app/chapter_translation_pipeline.py` contains document
  planning, chunking and integration contracts.
- `services/api/app/writing_reference_translation_batch.py` contains
  chapter-scoped orchestration and final fidelity handling.
- `services/api/app/writing_reference.py` contains
  `evaluate_translation_fidelity()` and controlled terminology checks.
- `frontend/tests/cross_indication_e2e_child.mjs` and
  `frontend/tests/cross_indication_e2e_config.mjs` define the release gate.
- Public source identity:
  `ClinicalTrials.gov NCT05923099 / Prot_SAP_000.pdf`, SHA-256
  `b7e58931f716336f05d3c36a3f712204234868190b283af70bb270e408268b56`.

## Scope

- In scope:
  - independently compare source, Hy-MT2 output and final integrated Chinese
    for the objectives/endpoints and trial-population chapters;
  - identify true scientific/regulatory translation defects, deterministic
    false positives and Flash self-review misses;
  - review chunk size, full-chapter QC, bounded corrective passes, protected
    fact manifests and hard/soft gate semantics;
  - propose concrete source-level changes and tests that retain fail-closed
    behavior for clinically material errors;
  - use current external primary documentation or mature open-source
    approaches when they materially improve the recommendation.
- Out of scope:
  - editing product source code or the stable 5174/8911 runtime;
  - replacing the required production routes
    (GLM-OCR-bf16, Hy-MT2, DeepSeek Flash, DeepSeek Pro);
  - admitting either blocked chapter, weakening the release threshold, or
    treating model self-confidence as acceptance evidence;
  - final clinical/regulatory or production acceptance, which remains Codex's
    responsibility.

## Success Criteria

- Separate every finding into observed evidence, inference and recommendation.
- For each current failure code, state whether it is a confirmed defect,
  probable defect, deterministic false positive, or unresolved.
- Inspect enough complete source/translation content to cite concrete examples,
  not only failure-code names.
- Produce a minimal prioritized remediation plan with exact affected modules,
  acceptance tests and a retry/stop rule.
- Preserve these non-negotiable gates: no unsupported medical concepts, no
  changed numbers/units/comparators/time windows/negation, no omitted endpoint
  or eligibility criteria, and no silent table/list cardinality loss.
- Return a compact LOOP trace: sources read, checks performed, evidence,
  uncertainty and recommended next step.

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
- The v10 source is a public protocol, but credentials, AI environment values
  and unrelated project data must not be read or reported.
- No participant may write product code; write only its assigned report.

## Loop Log

- 2026-07-18 19:10:54: Conference initialized by `hermes_workflow_guard.py init-conference`.
