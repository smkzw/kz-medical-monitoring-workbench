# Codex Conference Review: medical_workbench_lower_half_gap_baseline_20260708

Date: 2026-07-08 CST

## Verdict

Pass for next-slice decision, with implementation gates.

Codex accepts the conference package as sufficient to proceed toward Candidate 1: 医学写作独立AI Gateway最小闭环. The package does not certify commercial completion of any subsystem.

## Boundary Compliance

- Conference inputs were bounded to the workbench source packet and existing review/log files.
- No original real-project files were modified during the conference.
- Hermes and DeepSeek outputs are advisory. Codex retains authority over code edits, browser QC, final source-boundary checks, and user-facing completion claims.
- No final clinical, regulatory, PV, or statistical conclusion was accepted from the conference.

## Participant Outputs Reviewed

- `participant_qwen_plus.md`: retry completed with 288 substantive lines after the first run left only the guard placeholder. Recommends Candidate 1.
- `participant_mimo.md`: 213 substantive lines. Recommends Candidate 1 and highlights that the AI Gateway infrastructure already exists but the writing module is still using a deterministic demo stub.
- `participant_ds_flash.md`: 200 substantive lines. Recommends Candidate 1, with Candidate 3 as fallback if provider wiring blocks.
- All participant outputs remain advisory and were not treated as direct implementation instructions.

## Hermes Sub-Venue Review

`hermes_lead.md` completed with 322 lines using OpenCode Go `minimax-m3`. The lead compared participant outputs, accepted Candidate 1 as primary, preserved Candidate 3 as fallback, and placed Candidate 2 after the AI Gateway pattern is proven.

## Main-Venue DeepSeek Pro Review

`main_deepseek_pro.md` completed with 343 lines using DeepSeek supplier `deepseek-v4-pro`.

Codex accepts these main-venue additions as material gates:

- Provider integration is the highest-risk gap. The current gateway expects JSON; Buddy-style proxy routes may return SSE or exceed current timeout assumptions.
- If no external provider is configured, the product must show an explicit BLOCKED state rather than generating a deterministic or Codex-backed suggestion.
- The approval handoff must use a reusable entity pattern with module/source identifiers, not a writing-only shortcut.
- The first accepted writing workflow must bind to real protocol source spans, not to the current static editor demo text.

## Codex Independent Verification

- Read the main DeepSeek Pro output and stdout evidence after the run ended.
- Verified the stdout reported provider `deepseek`, model `deepseek-v4-pro`, 6 API calls, and normal completion before Hermes cleanup warnings.
- Verified the main review directly points to the current deterministic writing stub in `services/api/app/medical_writing.py` and the existing AI Gateway path in `services/api/app/ai_task_runner.py`.
- Earlier in the same loop, browser QC confirmed the medical writing first viewport now prioritizes the editor and AI rail ahead of source manifests.
- Provider connectivity and business-code implementation remain pending. They are the next Codex-owned loop, not a conference output.

## Final Decision

Proceed with Candidate 1 unless the provider preflight exposes a structural gateway incompatibility that would turn this from wiring into a broader gateway rebuild.

Implementation route:

1. Preflight current `WORKBENCH_AI_*` configuration and response compatibility.
2. Write/update tests before code changes for configured-provider success, unconfigured-provider BLOCKED behavior, invalid-output rejection, and no editor auto-write on accept.
3. Wire `MedicalWritingRevisionService` to the existing `AiTaskRunner` and `AiGateway` rather than creating a second AI path.
4. Keep AI outputs as `待医学批准` candidates and route accepted suggestions to a reusable approval entity.
5. Rerun backend tests, frontend build, desktop browser QC, and no-local-path/no-lifecycle-number scans before treating the slice as landed.
