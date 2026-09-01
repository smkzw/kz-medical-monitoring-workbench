# Conference Context: mw_corpus_v7_gap_adjudication_20260726

Created: 2026-07-26 18:46:20
Objective: 仅裁决CORPUS_V7_GENERALIZATION_GAP中的G1-G10哪些是上线阻断、哪些可保持fail-closed延后，并把重叠缺口合并为最小修复/测试簇；禁止重复审阅已通过v7/PNH范围
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

    - Visual/design/HTML/PPT tasks use a Codex-led panel with no sub-venue chair: Pi/Oh My Pi `kimi-code/k3` (high). If unavailable, the runner tries Cursor CLI `cursor-grok-4.5-high`, then Grok Build `grok-4.5`, then Kimi Code `k3`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
    - Other complex tasks use Pi/Alibaba `qwen3.8-max-preview` (xhigh) as the sub-venue chair, leading Pi `aishuo / cms-model` and CodeBuddy CLI `deepseek-v4-pro`. The chair fallback is Cursor CLI `cursor-grok-4.5-high`, then Cursor CLI `auto`.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/handoffs/codex_retake_20260726/CORPUS_V7_GENERALIZATION_GAP.md`
- `services/api/app/medical_writing_corpus_analysis_ai.py`
- `services/api/app/medical_writing_corpus_policy.py`
- `tests/test_medical_writing_corpus_analysis_ai.py`
- `tests/test_medical_writing_corpus_generalization_policy.py`
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`, only
  the v7/corpus-generalization acceptance paragraphs and referenced evidence
- `records/handoffs/codex_retake_20260726/evidence/CORPUS_STRICT_GATE_PRODUCTION_INTEGRATION_20260726.md`
- `records/handoffs/codex_retake_20260726/evidence/pytest_corpus_strict_gate_codex_acceptance.log`
- `records/handoffs/codex_retake_20260726/evidence/pytest_corpus_generalization_codex_acceptance.log`

## Scope

- In scope:
  - determine whether each G1-G10 is a reachable false-admission or
    false-high-confidence path, not merely a theoretical improvement;
  - merge shared root causes into the smallest coherent repair/test clusters;
  - rank each cluster as launch-blocking, Slice C quality gate, or safely
    deferrable while fail-closed behavior remains;
  - challenge the claim that G1-G9 must all close before Slice C;
  - state exact negative tests and deterministic acceptance behavior.
- Out of scope:
  - broad corpus or repository audit;
  - code, test, runtime or prompt-version changes;
  - PNH triage, OCR/translation, browser, DOCX or deployment;
  - repeating the accepted 49/40 suites;
  - treating consensus as final launch authority.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is modified; Codex retains final acceptance.
- The chair returns one G1-G10 disposition table, no more than four merged
  repair clusters, exact locators and a minimal ordered execution plan.
- A gap is launch-blocking only when the current deterministic system can
  accept or promote unsupported content; conservative low recall alone is not
  a launch blocker.

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
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Participants do not read each other's outputs before the chair stage.
- Keep the conference read-only and do not create alternate corpus artifacts.

## Loop Log

- 2026-07-26 18:46:20: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-26: Codex supplied the bounded sidecar report and exact v7
  implementation/test evidence. This conference adjudicates severity and
  overlap only; it does not repeat the earlier audit.
