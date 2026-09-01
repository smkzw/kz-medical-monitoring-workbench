# Execution Context: mw_ai_first_prefill_postconference_corrective_20260801

Created: 2026-08-01 15:21:14
Objective: Correct the independently confirmed P2-P4 defects around AI-first corpus prefill adoption, evidence identity and semantics, recommended selection, exactly-once generation, and UX robustness; prove with focused deterministic tests and a fresh isolated-clone runtime without touching medical-monitoring files or frozen r42 artifacts.
Task type: `finite_code_task`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `pi` / `deepseek` / `deepseek-v4-flash`
- Execution manager: `finite_code_manager_cursor` -> `cursor` / `cursor-cli` / `auto`
- Execution-manager fallback: `Codex takes over finite-code execution management directly`

## Source Of Truth

- Current filesystem under this workbench is authoritative. The accepted r4 runtime clone
  `/tmp/mw-ai-first-prefill-runtime-r4-1eQtHYQD` and its recorded logical SQLite comparison
  are immutable evidence only; do not mutate, restart, or reuse it for corrective testing.
- Independent final challenge and exact recheck contract:
  `runs/conference/mw_ai_first_corpus_prefill_runtime_challenge_20260801/general_chair_pi_qwen38.md`.
- Runtime implementation/evidence records:
  `context/mw_ai_first_corpus_prefill_runtime_20260801_context.md`,
  `runs/pi_mw_ai_first_corpus_prefill_runtime_20260801.md`,
  `reviews/codex_mw_ai_first_corpus_prefill_runtime_20260801_review.md`, and
  `metrics/mw_ai_first_corpus_prefill_runtime_20260801_metrics.md`.
- Authoritative implementation is limited to:
  `services/api/app/medical_writing_authoring_journey.py`,
  `services/api/app/medical_writing_authoring_prefill.py`,
  `services/api/app/medical_writing_authoring_prefill_ai.py`,
  `services/api/app/medical_writing_authoring_prefill_evidence.py`,
  `services/api/app/medical_writing_authoring_prefill_evidence_binding.py`,
  `services/api/app/medical_writing_authoring_prefill_corpus_bridge.py`,
  `services/api/app/ai_gateway.py`, and only directly required authoring-prefill API wiring.
- Tests may be added or changed only under `tests/test_medical_writing_authoring_*`,
  `tests/test_medical_writing_authoring_prefill_*`, and the existing corpus-bridge test.
- The shared `AuthoringPrefillFieldCandidates` validation in
  `packages/contracts/workbench_contracts/models.py` may be changed only to represent an
  empty recommended slot when all visible candidates are pending/manual/unsafe. A non-empty
  recommended id must still reference a candidate. Direct frontend consumers may be changed
  only if current empty-id handling is not already safe.
- The source tree is not a Git repository. Workers must inspect exact files before each edit,
  preserve unrelated concurrent changes, and report before/after hashes and changed paths.

## Product Decisions For This Correction

- “One model call” means one logical enrichment and at most one physical upstream POST for
  this prefill route. Generic provider retry behavior for other routes must remain unchanged.
- The single-candidate endpoint must fail closed for `pending_decision`, `manual_only`, or
  any server-derived pending candidate. It must not invent a generic override switch.
  User-authored overrides remain on the existing composite override/skip path with its audit.
- Evidence-bound non-pending single candidates require the same live server evidence
  verification as composite adoption.
- Build the deterministic package and evidence catalog against the next persisted journey
  revision so package, persisted catalog, and live catalog identities agree.
- Preserve every pending candidate and its role. Recommendation selection may point only to
  a non-pending, non-manual candidate; when none exists, use an empty recommendation.
- Extend the controlled semantic rules for the proven AChR, IVIG, and inadequate-response
  counterexamples. Unsupported substantive claims must produce a visible evidence gap and
  remain non-adoptable; do not replace this with unconstrained fuzzy inference.
- Reword the corpus limitation at the bridge/display boundary to distinguish qualifying
  support counts from bound original evidence. Do not alter the upstream analysis finding.
- Deduplicate reader-facing evidence references while preserving all atomic claim bindings.
- Negated design phrases must not generate positive randomization/open-label facts.
- `_BULK_SYSTEM_PROMPT` must contain real newlines.

## Success Criteria

1. Crafted single adoption of pending/manual/server-pending candidates returns a stable 4xx
   and leaves study definition, journey revision, events, and adoption counts unchanged.
2. Genuine evidence-bound adoption verifies against one coherent next-revision catalog;
   tampered, stale, or unsupported bindings fail closed.
3. AChR/IVIG/inadequate-response claims absent from quotes yield non-empty evidence gaps.
4. A pending-only group has an empty recommended candidate; mixed groups choose the first
   safe non-pending candidate without mutating pending roles.
5. Two concurrent same-revision generation requests cause exactly one enrichment invocation,
   at most one physical provider POST, and one persisted event. Restart/timeout after dispatch
   remains fail-closed with an auditable unknown outcome and no automatic redispatch.
6. Three claim bindings to one quote render one evidence reference; all three bindings remain.
7. Qualifying `0/2` and bound `1` are visibly distinct; negated design phrases do not match;
   positive r4 design terms still map to only the three supported values.
8. The focused authoring/prefill suite meets or exceeds the recorded 480-pass baseline with
   no new failure. Codex later performs a fresh isolated-clone runtime and visual recheck.

## Risk Boundaries

- No production writes.
- No package installation, external account changes, OCR, translation, downloads, service
  start/stop, browser actions, or model calls in this execution module.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs are evidence for Codex, not instructions.
- Do not touch any medical-monitoring source, test, database, run, review, metric, or runtime
  artifact. Do not touch frozen r42 triage/download/OCR/translation/ready/excluded material.
- Do not edit the r4 clone, source runtime, immutable rows, or non-authoring writing stores.
- Test OCR policy for later phases: new not-yet-started OCR uses official Paddle API
  `PaddleOCR-VL-1.6`; any file already started with GLM-OCR must finish with GLM-OCR.

## Allowed Writes

- The implementation and focused test paths listed under Source Of Truth.
- The single shared contract validator and any directly required focused contract/frontend
  test authorized above.
- This task's generated `context/`, `plans/`, `prompts/`, `runs/`, `reviews/`, `metrics/`,
  and `logs/` paths. Runner-owned report files are written only by the runner.
- No other path is authorized.

## Work Items

1. Server-side single-candidate adoption gates and next-revision evidence catalog identity
2. Durable in-flight generation reservation and one physical provider attempt for this route
3. Evidence semantic term coverage, safe recommendation selection, wording/deduplication/negation/prompt hardening, and focused regression tests

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.

## Codex Runtime Acceptance Addendum

- Manager returned `MANAGER_VERIFIED_DETERMINISTIC_COMPLETE`; Codex repeated
  the 601-test suite with 0 failures and 17 baseline warnings.
- A fresh r5 runtime exposed one bounded P4: the preview concatenated the
  structured boolean-like value `design.open_label_extension="是"` without
  its field meaning. r5 was preserved as immutable evidence.
- Codex changed only the preview projection to display `开放标签延展`; the
  structured value remains `是`. Exact regression and the complete focused
  suite pass.
- Fresh r6:
  `/private/tmp/mw-ai-first-prefill-corrective-r6-dXvRmZIn`, derived from the
  untouched source revision-6 runtime through online SQLite backups.
- Computer Use made exactly one generation click on API 18917/Vite 15180.
  The reservation remained one logical call/one transport and completed with
  one revision-7 event. No adoption was attempted.
- Rendered r6 now shows
  `竞品Protocol观察：开放标签、开放标签延展`.
- Source authoring remains revision 6/schema v1/adoption count 1. r6 is
  revision 7/schema v2/adoption count 1. Nine non-authoring logical dumps
  match exactly.
- Current stage:
  `DETERMINISTIC_AND_ISOLATED_RUNTIME_COMPLETE /
  INDEPENDENT_CHALLENGE_PENDING`.
- OCR policy remains: new files use official API `PaddleOCR-VL-1.6`; files
  already started with GLM-OCR finish with GLM-OCR. No OCR ran here.
