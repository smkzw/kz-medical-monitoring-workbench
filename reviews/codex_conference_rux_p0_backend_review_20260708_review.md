# Codex Conference Review: rux_p0_backend_review_20260708

Date: 2026-07-08 CST

## Interim Verdict

Participant and Hermes sub-venue review package is accepted for main-venue DeepSeek Pro review.

No product-code change is accepted yet. No source edits should be landed from this conference until Codex writes a failing test and independently verifies the recommendation against current source files.

## Boundary Compliance

- All participant work was read-only against the workbench packet and listed files.
- No participant was authorized to edit product code, run browser/visual acceptance, browse web, or make final clinical/regulatory conclusions.
- GLM-5.2 produced substantive stdout findings but failed to write its own output file due Hermes Studio MCP reconnection/path issues. Codex transcribed those stdout findings into `participant_glm52_product.md` and clearly labeled the transcription boundary.
- Hermes lead acknowledged the GLM transcription as advisory evidence and did not treat it as a normal `write_file` success.

## Participant Outputs Reviewed

- `runs/conference/rux_p0_backend_review_20260708/participant_qwen_plus.md` - complete.
- `runs/conference/rux_p0_backend_review_20260708/participant_mimo.md` - complete.
- `runs/conference/rux_p0_backend_review_20260708/participant_ds_flash.md` - complete.
- `runs/conference/rux_p0_backend_review_20260708/participant_glm52_product.md` - Codex transcription from GLM retry stdout, usable as corroborating advisory evidence.
- `runs/conference/rux_p0_backend_review_20260708/hermes_lead.md` - complete.

## Hermes Sub-Venue Review

Accepted for DeepSeek Pro review. The main points requiring Codex decision are:

1. Keep `RuxMonitoringService` additive; do not rewrite `monitoring_intake.py` as a RUX engine.
2. RUX unified inbox should use a RUX-specific adapter/projection and must not mutate demo repository data.
3. Before inbox projection, fix or explicitly test the ECB `暂停用药` / `重新用药` event semantics so protocol-aligned dose modification is not mislabeled as `protocol_deviation`.
4. Add RUX inbox tests with no local path/hash leakage and preserve demo inbox behavior.
5. Keep P0 wording explicit: selected deterministic anchors only, `待医学确认`, not full 192-subject monitoring coverage.

## Main-Venue DeepSeek Pro Review

Accepted as advisory evidence with transcription boundary. DeepSeek Pro produced a substantive review in stdout but stalled while preparing `write_file`; Codex transcribed the review into `runs/conference/rux_p0_backend_review_20260708/main_deepseek_pro.md`.

Main points accepted for Codex verification:

- The Hermes sub-venue package is thorough and actionable; all 4-of-4 converged points can be accepted as planning input.
- The next slice must start with source freshness checks, then a 404-baseline test, then a 200-target failing test, then the smallest patch, then focused/full regression.
- ECB `暂停用药` / `重新用药` being typed as `protocol_deviation` is a real product-semantics defect and should be fixed before or together with RUX inbox projection.
- Additive `_rux_monitoring_risk_items()` on `WorkbenchInboxService` is the preferred P0 adapter location, subject to Codex source-level verification.
- `RiskCase.source_locator` and evidence-source splitting are valid candidates, but Codex must inspect current contracts and write tests before changing them.
- `treatment_arm` placeholder becomes blocking only if the inbox response surfaces it.

## Codex Independent Verification

Completed so far:

- verified output files exist and are substantive;
- verified Hermes lead output is 274 lines and includes convergence, conflicts, deferred work, and resume notes;
- verified GLM route issue is a Hermes Studio MCP/write-file issue, not absence of product findings;
- confirmed no product-code edits were made during this conference pass.
- verified current source code confirms several accepted findings:
  - `services/api/app/workbench_inbox.py` calls `self.repo.project(project_id)` before item construction, so unknown RUX projects are blocked before any RUX-specific projection can run;
  - `services/api/app/rux_monitoring_service.py` maps ECB `暂停用药` / `重新用药` to `SubjectTimelineEventType.PROTOCOL_DEVIATION`;
  - `packages/contracts/workbench_contracts/models.py` has `RiskCase.evidence_span_ids` but no direct `RiskCase.source_locator`;
  - `WorkbenchItemSourceRef` already has a `locator` field, so RUX inbox projection can expose row/protocol locators without inventing a new source-ref contract.
- verified current RUX source file mtimes for handoff:
  - listing workbook: 2026-06-01 22:51 CST, 18,855,463 bytes;
  - subject report XLS: 2026-04-13 16:15 CST, 41,984 bytes;
  - protocol DOCX: 2025-01-13, 2,307,102 bytes.

Still required before code changes:

- run TDD red tests before product-code edits;
- run focused backend tests and relevant full backend regression after any patch;
- update `KNOWN_ISSUES.md` and subsystem logs after accepted decisions.
- rerun parser/anchor stability if the next slice modifies RUX dispatch or inbox projection.

## Final Decision

No product-code change will be landed from this review pass.

Accepted next implementation sequence for resume:

1. Verify current source files and parser/anchor baseline.
2. Add a red test that records the current RUX inbox 404 baseline.
3. Add the target failing test for `GET /api/projects/proj_rux_03_002/workbench-inbox?limit=20`.
4. Fix ECB dose-adjustment semantics with tests before or together with RUX inbox projection.
5. Implement the smallest additive RUX inbox projection, keeping demo inbox behavior unchanged.
6. Run focused RUX/inbox tests and full backend regression before any frontend work.
