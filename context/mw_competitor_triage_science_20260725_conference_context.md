# Conference Context: mw_competitor_triage_science_20260725

Created: 2026-07-25 08:57:32
Objective: 独立审阅UC、CRSwNP、D017真实ClinicalTrials.gov竞品分诊结果的适应症、分期、药理干预、公开Protocol/SAP价值和误纳误排风险；不得替代产品独立AI，不得修改生产状态
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

- Product runtime is only a source of independently generated results; reviewers
  must not call their own model instead of the product AI.
- Frozen review packet:
  `records/active_slices/medical_writing_production_rebaseline_20260722/evidence/three_project_competitor_triage_20260725/`.
- D017 snapshot and pre-version-gate run:
  `d017_snapshot.json`, `d017_v10_run_pre_version_gate.json`.
- CRSwNP snapshot and rejected run:
  `crswnp_snapshot.json`, `crswnp_v10_run_rejected.json`.
  The v10 run is defect evidence, not an acceptable recommendation set.
- UC snapshot/run and the CRSwNP/D017 v12 replacement runs will be added to
  the same packet before dispatch. Do not dispatch while those files are absent.
- Relevant deterministic implementation and tests:
  `services/api/app/medical_writing_competitor_triage.py`,
  `tests/test_medical_writing_competitor_triage_crswnp.py`,
  `scripts/qc/d017_competitor_triage_v5_acceptance.py`.
- ClinicalTrials.gov study-record and document URLs embedded in the frozen
  snapshots are external source locators. Web verification may use those public
  records but must not mutate product state.

## Scope

- In scope: independently assess indication relation, phase relevance,
  pharmacologic/non-pharmacologic intervention, public Protocol/SAP utility,
  false-positive and false-negative risk, and whether each v12 basket is safe
  for a medical writer to confirm.
- In scope: identify exact NCT IDs that should change classification, with a
  source-bounded reason and confidence.
- In scope: compare the rejected CRSwNP v10 output with deterministic v12
  semantics and the new product-AI v12 output.
- Out of scope: editing code, confirming any basket, downloading or translating
  documents, writing protocol text, security review, or replacing product
  `deepseek-v4-pro` results with conference prose.

## Success Criteria

- Every recommendation is traceable to an NCT record from the supplied snapshot.
- CRSwNP mixed-population, registry-typo, explicit-without-polyps,
  allergic-fungal-rhinosinusitis, and non-pharmacologic boundaries are reviewed.
- D017 and UC are checked for broad-query false positives rather than accepted
  merely because every chunk completed.
- Reviewers distinguish clinical relevance from document availability.
- Output names exact blocking findings, safe-to-confirm findings, and residual
  uncertainty; no production writes occur.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 240 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; participant and chair budgets
  are 128 and 192 respectively.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Conference outputs may not be copied into product results or used as protocol
  corpus content. No participant may approve or confirm a competitor basket.
- Current routing boundary: after 2026-07-25 08:30 Asia/Shanghai,
  `Hermes/aishuo/cms-model` is active again. Existing QoderVIP
  `qodercli/qwen3.8-max-preview` remains first for roles otherwise assigned to
  Grok under the project conference override.

## Loop Log

- 2026-07-25 08:57:32: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-25 09:10: Source authority, no-write boundary, and clinical acceptance
  questions were filled. Dispatch remains gated on UC terminal output and
  CRSwNP/D017 v12 replacement runs.
- 2026-07-25 09:47: UC v10 evidence showed a product input-layer defect:
  search used the active draft English condition term while triage used only
  confirmed Chinese framing. v12 unifies both paths on effective draft facts
  and changes the canonical run identity. Dispatch remains gated on fresh
  UC/CRSwNP/D017 v12 product-AI runs.


---

## Agent #1 update 2026-07-25T18:13:24.938629+08:00 — v13 evidence ready

Frozen v13 product AI packet (replace v12 as review target; v12 remains historical only):

- `records/active_slices/medical_writing_production_rebaseline_20260722/evidence/three_project_competitor_triage_20260725/uc_v13_run.json`
- `.../uc_v13_job_result.json` / `uc_v13_acceptance.json` (**accepted=true**; v12 false-exclude sentinels NCT07229950/07335055/07535489 now retained)
- `.../crswnp_v13_run.json` / `crswnp_v13_acceptance.json` (**accepted=true**, 11/11 boundary)
- `.../d017_v13_run.json` / `d017_v13_acceptance.json` (**accepted=true**)
- `.../SHA256SUMS.v13`
- prompt_version: `competitor_triage_deepseek_v13_controlled_condition_qualifiers`
- provider/model: deepseek / deepseek-v4-pro; codex_runtime_dependency=false

Reviewers must not call their own model as product AI. Do not confirm baskets. Challenge false include/exclude only with NCT-bounded reasons.
