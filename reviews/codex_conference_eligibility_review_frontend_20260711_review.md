# Codex Conference Review: eligibility_review_frontend_20260711

Date: 2026-07-11

## Verdict

Pass for the first desktop eligibility-review slice. This does not close the eligibility subsystem: evidence artifact jobs, controlled OCR/VLM routing, independent-AI criterion batches and the six-subject evidence-to-review matrix remain open.

## Boundary Compliance

- The production UI consumes the versioned `/review` and criterion-action APIs and does not reuse legacy review conclusions.
- IN and EX retain independent decision vocabularies. Decisive decisions require completed current-version evidence.
- AI draft, medical decision and mandatory user-authored medical reason remain separate.
- The page makes no formal eligibility conclusion and no randomization-release decision.
- Provider names, local paths and content hashes are absent from the public work surface.

## Participant Outputs Reviewed

- Buddy Kimi `kimi-k2.7-code`: completed a bounded frontend proposal. Codex rejected direct application because it fabricated a reason, used the wrong subject identity level, mixed aliases with canonical identity, treated raw source ids as evidence ids and omitted conflict/action paths. Reviewable layout ideas were retained only after independent implementation.
- Buddy GLM-5.2: the first run exceeded the read allowlist and was excluded. The bounded retry completed and supplied medical-monitor acceptance criteria and error/action-state findings.
- Placeholder Qwen, Mimo and DeepSeek Flash conference files were not dispatched for this implementation-specific frontend review and were excluded from evidence.

## Hermes Sub-Venue Review

`aishuo/MiniMax-M3` completed the actual Hermes sub-venue synthesis in session `20260711_154413_baf55e`. It compared the bounded GLM and Kimi outputs, rejected unsafe patch elements and returned a rewrite list. This route is also the user-approved default for future Hermes sub-venue review and chair tasks.

## Main-Venue DeepSeek Pro Review

Reasonix `deepseek-pro` completed the high-risk main-venue review. It found no P0 issue and identified three P1 defects: loss of an unsaved reason after 409 refresh, collapsed evidence-processing labels and no retry for non-409 errors. It also identified a Chinese forbidden-conclusion test gap and project-tab persistence as P2 items. Codex accepted and fixed all five actionable findings.

## Codex Independent Verification

- `npm run build`: passed; only the pre-existing Vite chunk-size warning remains.
- Focused SQLite/workflow/API/frontend contract regression: 25 tests passed.
- `npm run lint` was not available because the project defines no lint script; this is an environment/tooling gap, not a passing lint claim.
- Isolated Chrome action/QC loop passed for real D001 and MY009 projects at `1600x1000` and `2048x1024`.
- The loop exercised request-evidence, an external concurrent defer, stale action 409, refresh to revision 2 and preservation of the user's unsaved reason.
- Final report: `records/visual_qc_20260711/eligibility_review_workspace/eligibility_review_workspace_qc.json`, `completed: true`, `failures: []`.
- Codex inspected all four original-resolution screenshots. The three-column work surface is dense, aligned and free of incoherent overlap or clipping; candidate and criterion lists remain internally scrollable.
- The isolated test services were stopped and their temporary runtime directory was destroyed.
- Active runtime SHA-256 remained `987464f7f150bb1cf2ff68aeb738355c3fb57e96fef59136ab6e0c4d9b7ec102`.

## Final Decision

Accept the desktop frontend closure and proceed to the evidence-job/OCR/VLM slice. Do not describe the eligibility subsystem as complete until at least two real projects pass the full evidence and independent-AI workflow.
