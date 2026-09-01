# Conference Context: medical_writing_route_d_v1_review_20260714

Created: 2026-07-14 13:22:11
Objective: Reconcile the participant findings against the remediated Route D v1 implementation and the independent SYN-RA-201 greenfield writing pilot; determine which reusable controls are pilot-ready and which production gates remain open.
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3`, Hermes `buddy / kimi-k2.7-code`, and Hermes OpenCode Go `qwen3.7-plus`.
- Chinese labels or Chinese sentence review uses a single Hermes `buddy / deepseek-v4-pro` gate and does not start a conference.
- Other complex tasks use Hermes `buddy / glm-5.2` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3`, Hermes `buddy / deepseek-v4-pro`, and Hermes OpenCode Go `mimo-v2.5`.
- This conference route does not invoke Reasonix for a high-risk second review.
- Every conference role is dispatched through a three-round same-session loop: independent pass, skeptical challenge, and corrected final pass. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- User requirements and research decision: `records/active_slices/medical_writing_corpus_agent_harness_20260714/TASK_RECORD.md`, `EVIDENCE_AND_ARCHITECTURE_REVIEW.md`, `PILOT_RESULTS_AND_PRODUCTION_DECISION.md`, `FACT_PACK_V2_AND_TERMINOLOGY_LOCK_SPEC.md`.
- Route D v1 implementation and record: `records/active_slices/medical_writing_route_d_v1_20260714/TASK_RECORD.md`, `source_profiles.json`, `expression_library_v2.json`, `build_route_d_v1_inputs.py`, `route_d_v1.py`, `run_route_d_v1.py`, `run_gap_contract_probe.py`, `test_route_d_v1.py`, `harness/LOW_RISK_GAP_WRITER.md`, and both JSON schemas.
- Frozen evidence: `records/active_slices/medical_writing_route_d_v1_20260714/pilot_v3/source_manifest.json`, three successful fake outputs/manifests, D001 blocked manifest, and the live probe files under `pilot_v3/probes/live/proj_rux_03_002/`.
- Test evidence: participant reviews described the pre-remediation 17-test state. Current reported evidence is 22 Route D tests plus 25 greenfield tests passing before one additional v0.2 DOCX assertion; Codex will rerun after the chair packet is frozen. Participants audit code and artifacts but do not run commands.
- Current external evidence is summarized with queryable URLs in `EVIDENCE_AND_ARCHITECTURE_REVIEW.md`; participants must not browse.
- Remediated Route D evidence: updated task record, schemas, expression library, controller, runner, tests, rebuilt `pilot_v3`, and the archived three-stage live probe.
- Greenfield evidence: `records/active_slices/medical_writing_synthetic_ra_greenfield_20260714/TASK_RECORD.md`, source brief, evidence/decision/corpus matrices, bounded gap harness and runner, direct/Agent route comparison, v0.2 candidate JSON, application summary, and DOCX structural tests. Codex inspected all six rendered pages; chair must not make visual acceptance claims.

## Scope

- In scope: source-to-fact validation, schema generality, deterministic assembly, expression approval semantics, gap calculation, direct-model contract, abstention, provenance/coverage metrics, cross-project leakage, D001 conflict handling, stale artifact behavior, deployability, and whether any bounded component is merge-ready.
- In scope: compare direct structured LLM and bounded Agent only from the frozen prior evidence; determine where an Agent adds orchestration value versus unnecessary state/cost.
- In scope: verify whether participant defects about applicability, binding drift, source containment, hash coverage, probe preservation, and metric naming are resolved in the current files rather than repeating stale findings.
- In scope: assess the RA greenfield chain from synthetic brief and frozen public evidence through deterministic assembly, modular study-flow table, bounded generation, medical-approval gate, and production prohibition.
- Out of scope: medical approval of the candidate Chinese text, production routing changes, frontend changes, new corpus ingestion, web research, editing files, or reading raw protocol paths outside this workspace.

## Success Criteria

- Findings cite exact files/functions/JSON fields and separate confirmed defects from design preferences.
- Explicitly challenge the misleading equation of fact anchoring with approved/source text reuse.
- Verify that no project-specific ID/fact branch exists in the runtime controller and that the four project differences are data-driven.
- Inspect all three live probe stages: false pass with project-term leakage, controlled abstention misclassified, and corrected `abstained` result.
- Determine the smallest safe next step and list any blocker to production use; do not approve medical text.

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
- Read-only review only. No source or production edits, no test execution, no network, no browser, no shell exploration outside the explicit read list.
- Engineering candidate expressions are not medically approved. `fact_anchored_ratio=1.0` is not regulatory-language approval.
- D001 must remain blocked; no participant may choose between 2 and 4 weeks.

## Loop Log

- 2026-07-14 13:22:11: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-14: Context completed after Route D v1 17-test pass and three-stage live gap probe. No production route was changed.
- 2026-07-14: After participant findings, Codex added applicability enforcement, exact binding-to-fact maps, source-span containment/content assertions, controller/orchestrator hashes, clearer deterministic-fact-bound metrics, and probe preservation; Route D reached 22 tests.
- 2026-07-14: Added isolated SYN-RA-201 greenfield pilot and direct API versus Agent harness comparison. Direct structured invocation remains the bounded sentence-gap default; Agent use is conditional. Candidate remains medically unapproved and production-prohibited.
- 2026-07-14: GLM-5.2 chair completed three rounds in session `20260714_143018_794ec8`. Codex corrected the chair's D001/RUX mislabel, its unsupported universal `production_eligible=false` statement, and its claim that pre-remediation participants verified later fixes.
