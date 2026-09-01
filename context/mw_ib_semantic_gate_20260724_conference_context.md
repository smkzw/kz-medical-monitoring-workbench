# Conference Context: mw_ib_semantic_gate_20260724

Created: 2026-07-24 15:53:53
Objective: 基于真实MY004研究者手册独立AI提取结果，设计并复核医学事实语义门：既往试验事实不得污染当前方案设计；测试剂量不得等同RP2D；IB版本不得覆盖方案版本；随后形成可执行修复与真实重测标准。仅做功能和医学科学性，不做工程安全审计。
Task type: `complex_delivery_conference`
Risk: `high`
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

- `services/api/app/medical_writing_fact_intake.py`
- `services/api/app/source_intake.py`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_medical_writing_fact_intake.py`
- `tests/test_source_intake.py`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/CURRENT_GAP_MATRIX.md`
- Real E3 project: `proj_user_f5c768c5bc9f`, indication rheumatoid arthritis,
  product MY004567 tablets, Phase II, created through the public API.
- Real source entry:
  `src_proj_user_f5c768c5bc9f_investigator_brochure_88b747c5acf3`.
  The registered DOCX has 240 source spans, matched document role and matched
  indication. Review through the Source Registry/runtime API or local runtime
  stores; do not disclose the underlying confidential document externally.
- Real independent-AI run:
  `mwfactrun_218d76b642c78bf0`, provider/model
  `deepseek/deepseek-v4-pro`. The source-ID allowlist worked, but the run
  produced clinically unsafe semantic mappings:
  1. prior Phase II tested doses 40 mg and 80 mg were labeled as RP2D;
  2. prior MAD and Phase II dosing were mapped to the current study treatment
     interval, including the phrase "很可能";
  3. the IB title/version were proposed as the current protocol title/version;
  4. a prior Phase II design and population were proposed as the current
     study's design pattern and population;
  5. lowest observed SAD dose was equated to FIH starting dose without an
     explicit source statement that it was the actual FIH starting dose.
- Three completed Codex sub-agent reviews are summarized in the active task
  record. Their common P0s are file-first synopsis import, evidence before
  final PICOS, typed Phase-I Parts as the single downstream authority, and
  real E3/E4/E5 acceptance.

## Scope

- In scope: scientific semantics of IB-derived facts; prompt and deterministic
  server validation; distinction between direct source fact, inference,
  historical-study fact, current-study design decision and unresolved fact;
  regression scenarios and a real independent-AI rerun.
- In scope: review-only recommendations for how the same fact taxonomy should
  later feed product profile, current StudyDefinition, PICOS and dynamic
  ProtocolAssemblyPlan.
- Out of scope: security, vulnerability, attack-surface or backdoor review;
  unrelated refactors; replacing the independent production model; treating
  another Agent's answer as product-AI output.

## Success Criteria

- A field-level semantic policy states which IB facts may populate product
  profile directly, which must remain historical evidence, and which require
  an explicit current-study user decision.
- Tested dose is never treated as RP2D without an explicit recommendation
  statement; observed regimen never becomes the planned regimen by inference.
- IB metadata never overwrites protocol metadata.
- Invalid current-study mappings are rejected or quarantined server-side even
  if the model returns them.
- The prompt requires direct wording for exact high-impact facts and forbids
  "很可能/可视为/推测" under `source_extracted`.
- Focused tests cover the observed real failures and preserve valid
  source-grounded product facts.
- The same real IB is rerun using independent DeepSeek V4 Pro and returns only
  medically admissible proposals or explicit unknowns.

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

## Loop Log

- 2026-07-24 15:53:53: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-24 15:56: Source of truth and real E3 failure observations recorded.
  Conference is review-only; Codex retains production-write and final medical
  acceptance authority.
