# Conference Context: mw_word_engine_open_source_gate_20260718

Created: 2026-07-18 10:47:31
Objective: Review the no-cost production DOCX generation/export pipeline using current POC evidence and recommend a bounded integration and acceptance plan for the medical-writing subsystem
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no sub-venue chair: Grok Build `grok-4.5` (`grok-build`) and Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, max reasoning). For either unavailable primary role, the runner tries Hermes OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / cms-model` and Hermes OpenCode Go `deepseek-v4-flash`. Any unavailable complex-task role follows Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, max reasoning), then Reasonix CLI `deepseek-v4-flash`, then Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as a declared fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `services/api/app/medical_writing_document_exporter.py`
- `services/api/app/medical_writing_table_exporter.py`
- `tests/test_medical_writing_document_exporter.py`
- `tests/test_medical_writing_table_exporter.py`
- `research/medical_writing_word_engine_comparison_20260718.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_engine_poc/reports/openxml_greenfield_schema_fix_v2_m365.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_engine_poc/reports/aspose_greenfield_schema_clean.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_engine_poc/reports/openxml_aspose_greenfield_schema_clean_m365.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_engine_poc/reports/syncfusion_greenfield_schema_clean.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_engine_poc/reports/openxml_libreoffice_roundtrip_v1_m365.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_final_qc/greenfield_ra/greenfield_ra_production.docx`
- Official sources recorded in the research note: Microsoft Open XML SDK, python-docx, LibreOffice, docx4j, Aspose and Syncfusion documentation/license pages.

## Scope

- In scope: independently review the POC evidence; choose a sustainable no-cost DOCX generation, validation, rendering and final-acceptance toolchain; define exactly what belongs in runtime, release gate and manual/native Word acceptance; identify the smallest safe production integration.
- In scope: challenge whether Open XML SDK validation should block every export, only greenfield exports, or only release artifacts; assess template-first and source-preserving export boundaries; define font, pagination, TOC/TOF, table, figure, header/footer and editability gates.
- Out of scope: using any commercial engine that requires purchase for watermark-free or unrestricted production operation; rewriting the full editor; modifying production code in this conference; declaring the writing subsystem released.

## Success Criteria

- Recommendation requires no new paid license and can run locally/private-network without Codex or Hermes.
- Recommendation preserves imported DOCX source fidelity and does not round-trip authoritative content through LibreOffice.
- Recommendation explains the evidence boundary: Open XML schema validity is necessary but not sufficient for Word layout fidelity.
- Recommendation gives a bounded implementation plan, failure behavior, rollback path, and tests.
- Every claim distinguishes measured POC evidence from inference.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use 30 and 40 respectively.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- The user explicitly prohibited paid production dependencies. Aspose.Words and Syncfusion DocIO are rejected regardless of technical capability.
- LibreOffice remains a secondary deterministic renderer only. The measured round-trip changed a zero-error DOCX into a 66-error DOCX.
- The current greenfield exporter now passes Microsoft365 Open XML SDK validation with zero errors; commercial engines and LibreOffice introduced 1, 7 and 66 errors respectively on the same schema-clean input.
- Microsoft Word native rendering/editability remains the final desktop acceptance authority, but unattended server-side Office automation is not a permitted production dependency.

## Loop Log

- 2026-07-18 10:47:31: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-18 10:50: POC rebaselined after fixing table/settings schema order. Targeted exporter tests 29/29 pass; the greenfield DOCX has zero Microsoft365 Open XML errors.
- 2026-07-18 10:51: User prohibited paid production engines. Commercial trial outputs are evidence-only.
