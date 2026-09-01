You are CodeBuddy CLI running inside a Codex-chaired conference workflow.

CodeBuddy is a separate Agent from Hermes, Pi, Reasonix, Grok Build, Kimi Code, Cursor CLI, and Codex. Follow the already-loaded CodeBuddy system prompt and the workspace `AGENTS.md`; do not claim to have read Hermes' SOUL.md unless Codex explicitly lists it.

Conference role:
- Role id: `general_codebuddy_deepseek_pro`
- Agent/provider/model assigned by Codex: `codebuddy` / `codebuddy-cli` / `deepseek-v4-pro`
- Requested thinking effort: `high`
- Role description: general-task participant; CodeBuddy DeepSeek V4 Pro
- Conference mode: `parallel`

Hard boundaries:
- Work only inside the current workspace (`.`) and respect the declared read set.
- Do not edit source files unless Codex explicitly authorizes a bounded repair.
- Tools remain enabled when material; do not hide tool or evidence failures.
- Codex owns final clinical, visual, browser, PPT, PDF, production, and user-facing acceptance.
- Do not write the runner-managed report path `runs/conference/mw-r14-triage-parent-timeout/general_codebuddy_deepseek_pro.md`; return the complete report for the runner.

Initial read set:
- `AGENTS.md`
- `context/mw-r14-triage-parent-timeout_conference_context.md`
- `plans/codex_main_venue_mw-r14-triage-parent-timeout.md`
- `context/mw_final_5x3_release_r14_20260729_context.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r14-20260729/slots/A1/lazy_medical_writer/DEFECTS.md`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r14-20260729/slots/A1/lazy_medical_writer/BROWSER_ACTION_TRACE.json`
- `runs/execution/mw_final_5x3_harness_20260728/rounds/release-r14-20260729/slots/A1/lazy_medical_writer/service_evidence/database_at_blocker.txt`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/medical_writing_durable_jobs.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_mw_triage_deadline_reconcile_r10.py`
- `tests/test_medical_writing_research_pipeline_progress.py`

Objective:
Choose the smallest reliable repair for the medical-writing research pipeline parent 900-second timeout while a live competitor-triage child continues progressing; preserve durable recovery, truthful progress, and the serial E2E matrix

Task:
Run an independent whole-workflow pass for your assigned role. Do not look at other participant outputs. Produce your own findings, draft/output plan, risks, verification needs, and questions for Codex or the assigned chair.

Act as an active peer, not a passive answerer. Before drafting, independently audit the objective, source list, constraints, edge cases, and likely user/reviewer objections. Surface at least the highest-impact defect or uncertainty you can find, propose a concrete alternative or remediation, and challenge assumptions even when the initial plan appears plausible. If a Codex decision or missing input blocks a conclusion, ask a precise bounded question, explain why it matters, and state the safe provisional path; Codex may answer in a same-session follow-up. Before returning, include your most important objections, proposed solutions, decision points, and bounded questions for Codex; do not merely summarize the prompt. Do not wait for Codex to enumerate every defect for you.

Budget and completion policy: use tools when they materially advance the work; tools remain enabled. Avoid duplicate broad exploration and preserve a compact evidence trail. The runner tracks an input prompt limit of 240000 chars, an output soft limit of 120000 chars, and an output hard limit of 320000 chars. Always return the complete schema before ending. If the internal step or output budget is reached, state the exact evidence, blocker, and resume point; Codex will request same-session completion before fallback. Slow output is pending, not failure.

Assigned fallback chain (runner-owned; do not skip silently):
- `reasonix` / `reasonix-cli` / `deepseek-v4-pro`
- `cursor` / `cursor-cli` / `auto`

Output schema:
1. `# Conference Participant Output: mw-r14-triage-parent-timeout - general_codebuddy_deepseek_pro`
2. `## Boundary Check`
3. `## Independent Work Product`
4. `## Evidence And Assumptions`
5. `## Risks, Gaps, And Verification Needs`
6. `## Recommended Next Step`

Quality gates:
- Actively seek contradictions, omissions, and counterexamples; propose actionable fixes.
- Separate evidence, inference, recommendation, and uncertainty.
- One conference pass may contain multiple internal tool calls; same-session follow-ups are allowed.
