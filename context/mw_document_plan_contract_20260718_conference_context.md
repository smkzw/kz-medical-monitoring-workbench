# Conference Context: mw_document_plan_contract_20260718

Created: 2026-07-18 16:45:20
Objective: Design a production-safe document-level ClinicalTrials.gov protocol chapter planning contract that avoids LLM echo of thousands of span IDs, preserves deterministic complete ordered mapping, stops batch-wide repeated planner failures, and exposes honest progress for AD/PNH/obesity/SLE writing-reference translation.
Task type: `complex_delivery_conference`
Risk: `critical`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no sub-venue chair: Grok Build `grok-4.5` (`grok-build`) and Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning). For either unavailable primary role, the runner tries Hermes OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / cms-model` and Hermes OpenCode Go `deepseek-v4-flash`. Any unavailable complex-task role follows Kimi Code (`kimi-code` / `kimi-code/k3` = `k3`, high reasoning), then Reasonix CLI `deepseek-v4-flash`, then Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as a declared fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `records/active_slices/medical_writing_cross_indication_reference_gate_20260718/TASK_RECORD.md`
- `services/api/app/main.py`, especially `_flash_planner_adapter` and the
  composite OCR/Hy-MT2/Flash adapters.
- `services/api/app/writing_reference_translation_batch.py`, especially
  `_process_with_composite_pipeline()` and `_get_or_create_document_plan()`.
- `services/api/app/chapter_translation_pipeline.py`, especially
  `validate_document_plan()` and `build_chunks_from_plan()`.
- `frontend/tests/cross_indication_e2e_child.mjs` and
  `frontend/tests/cross_indication_e2e_config.mjs`.
- `tests/test_writing_reference_translation_batch.py`,
  `tests/test_mw_round3_backend_remediation.py`, and Round 8 pipeline tests.
- ClinicalTrials.gov official AD reference:
  `NCT05923099 / Prot_SAP_000.pdf`.
- Fresh 2026-07-18 product evidence:
  - product search returned 454/454 studies over 5 pages and found the exact AD
    study/document;
  - download, 200-DPI GLM-OCR/native extraction and validation succeeded;
  - a real translation batch created 604 span items;
  - 41 consecutive items failed retryably at `toc_planning` before Codex
    stopped the isolated run;
  - controlled reproduction over the same public PDF produced 3,124 native
    text blocks; DeepSeek Flash returned four chapter-title strings, zero
    `source_span_ids`, while the downstream validator requires every source
    span exactly once and in order.
- Local production constraints: body translation is Hy-MT2, Flash is only
  document planning/integration QC, OCR is GLM-OCR at >=200 DPI and <=8
  concurrent calls. No production secrets may be logged.

## Scope

- In scope:
  - define the exact AI/deterministic boundary for document-role and chapter
    planning;
  - map all spans once, in order, without asking an LLM to echo thousands of
    opaque IDs;
  - preserve meaningful ICH M11 anchor/heading structure across protocols and
    Protocol+SAP packages;
  - define a document-level planner failure state and batch-wide retry/fuse
    semantics so one failure is not repeated per span;
  - define honest document/chapter/chunk progress;
  - propose focused implementation and regression tests.
- Out of scope:
  - changing the user-approved OCR, Hy-MT2 or DeepSeek model routes;
  - weakening source/content/extraction/medical-review gates;
  - editing production code during the conference;
  - claiming medical/regulatory approval of translated text;
  - accepting a single-chapter fallback that erases real document structure.

## Success Criteria

- A proposed contract uses bounded semantic inputs such as ordered headings,
  anchors, page/block ordinals or boundary indices; it never requires the model
  to return every opaque span ID.
- Deterministic code expands validated boundaries to a complete, duplicate-free,
  order-preserving assignment of every span.
- Malformed AI output fails once at document-plan level and blocks/retries the
  document, rather than generating one identical provider call per span item.
- The design handles repeated headings, tables crossing pages, unmapped spans,
  Protocol+SAP composites, appendices and OCR-only headings.
- Progress and blocker records distinguish document plan, chapter, chunk,
  integration and terminal/retryable states.
- Proposed tests include realistic large-span and malformed-string output
  cases and preserve the existing immutable-plan/chapter-reuse contract.

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
- Do not recommend feeding full protocol text or thousands of source IDs into a
  single planning prompt merely to satisfy the existing validator.
- Do not silently assign all spans to one chapter when structured evidence is
  available; ambiguity must remain explicit and reviewable.

## Loop Log

- 2026-07-18 16:45:20: Conference initialized by `hermes_workflow_guard.py init-conference`.
