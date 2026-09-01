# Conference Context: medical_writing_reference_drawer_20260712

Created: 2026-07-12 11:37:18
Objective: Design and review a desktop-first competitor protocol reference drawer integrated into the existing medical-writing editor and AI rail, covering discovery, medical relevance, document status, pending translation review, approved evidence insertion, source traceability and invalidation without displacing document editing or AI interaction.
Task type: `visual_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Independent visual participants are exact `buddy / kimi-k2.7-code`, `buddy / glm-5.2`, and `opencode-go / qwen3.7-plus`.
- Per the user's project override, exact `aishuo / MiniMax-M3` performs the sole Hermes sub-venue review after the independent outputs complete. No silent substitution is allowed.
- Chinese labels receive a separate `buddy / deepseek-v4-pro` gate before Codex browser acceptance.
- This conference route does not invoke Reasonix for a high-risk second review.
- Every conference role is dispatched through a three-round same-session loop: independent pass, skeptical challenge, and corrected final pass. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `records/visual_qc_20260710/medical_writing_proj_rux_03_002_desktop.png`
- `records/visual_qc_20260710/medical_writing_proj_d001_desktop.png`
- `records/active_slices/medical_writing_competitor_corpus_20260712/TASK_RECORD.md`
- `reviews/codex_conference_medical_writing_competitor_corpus_production_20260712_review.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/main.py`

## Scope

- In scope: desktop interaction hierarchy, editor/AI primacy, evidence tab/drawer states, discovery form, candidate classification, document status, translation review, approved evidence selection, citation traceability, invalidation and error/empty/loading states.
- Out of scope: editing source code, running browsers, changing the overall brand system, mobile feature reduction, inventing new routes beyond the approved writing-reference workflow.

## Success Criteria

- Preserve the current editor-first composition and keep AI interaction visible.
- Define every control and state needed for discovery through approved evidence insertion.
- Use existing typography, spacing, colors, icons and panel conventions; no marketing cards or nested cards.
- Fit a desktop 1600x1000 minimum workflow without page-level horizontal overflow.
- Make unapproved, blocked, approved and invalidated evidence unmistakable in Chinese clinical-trial language.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Desktop experience has priority; do not remove workflow controls to support mobile.
- Pending translations may be visible but cannot be selected for approved AI evidence.
- The drawer must never obscure source document editing or silently inject competitor text.

## Loop Log

- 2026-07-12 11:37:18: Conference initialized by `hermes_workflow_guard.py init-conference`.
- Generic no-chair visual routing was replaced before dispatch by the user's exact aishuo sub-venue-review rule and explicit Kimi/GLM design participation rule.
