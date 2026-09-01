# Conference Context: eligibility_ai_packet_gate_20260712

Created: 2026-07-12 01:55:48
Objective: 复核入排审核AI受控证据packet、调用前版本/QC门禁、packet幂等和公共API身份边界
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Independent participants: OpenCode Go `qwen3.7-plus` and OpenCode Go `mimo-v2.5`.
- Required Hermes sub-venue chair: exact `aishuo/MiniMax-M3` for comparison, synthesis, dispute resolution and review.
- High-risk main-venue reviewer: Reasonix CLI `deepseek-pro`; it is not a Hermes provider.
- Generated Buddy DeepSeek and GLM-chair prompts are excluded because they conflict with current project routing.
- Provider/model/completion markers must be verified. A chair failure is recorded and retried on the same aishuo route; no silent substitute is allowed.

## Source Of Truth

- `services/api/app/eligibility_ai_packet.py`
- `services/api/app/eligibility_ai_review.py`
- `services/api/app/eligibility.py`
- `services/api/app/ai_gateway.py`
- `services/api/app/ai_execution_policy.py`
- `services/api/app/ai_task_runner.py`
- `services/api/app/sqlite_runtime_store.py`
- `tests/test_eligibility_ai_packet.py`
- `tests/test_eligibility_ai_review.py`
- `tests/test_eligibility_ai_contract.py`
- `tests/test_eligibility_review_api.py`
- `tests/test_eligibility_review_workflow.py`
- `records/active_slices/eligibility_next_slice_20260711/six_subject_matrix_v1.json`
- `records/active_slices/eligibility_next_slice_20260711/IMPLEMENTATION_LOOP_LOG.md`
- Verified Codex results: focused suites passed; authoritative backend 568/568 in 196.448s.

## Scope

- In scope: server-owned packet assembly; controlled-artifact integrity; current rule/source/QC preflight; packet echo/schema; stable business idempotency; public API AI-identity boundary; corrected T1-T12 interpretation.
- Out of scope: real clinical-image processing, visual acceptance, medical conclusions, production authentication/RBAC/tenant identity, safe archive extraction, DOC/DOCX subject extraction and frontend redesign.

## Success Criteria

- No caller-controlled rule/evidence body can reach the provider through the public route.
- Stale rule/source, missing binding, failed QC, artifact tamper/schema/revision mismatch all fail before provider disclosure.
- Packet digest and output echo cover current revisions, criteria and evidence text.
- Completed batch replay skips a second provider call and creates no duplicate drafts.
- Public medical action cannot forge `save_ai_draft` or an authenticated system actor.
- Findings distinguish bounded implementation defects from explicitly closed production gates.

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

## Loop Log

- 2026-07-12 01:55:48: Conference initialized by `hermes_workflow_guard.py init-conference`.
