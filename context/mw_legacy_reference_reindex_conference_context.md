# Conference Context: mw_legacy_reference_reindex

Created: 2026-07-15 17:24:38
Objective: 设计并审查医学写作导入方案中既有正文引文与参考文献的统一索引、重编号、编辑器绑定和DOCX导出闭环
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3` and Grok Build `grok-4.5`. If either is unavailable, the runner tries Hermes OpenCode Go `qwen3.7-plus`, then `mimo-v2.5`. Hermes' own Grok route is not used.
- Chinese labels or Chinese sentence review is handled directly by Codex and does not start a conference.
- Other complex tasks use Grok Build `grok-4.5` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3` and Hermes OpenCode Go `deepseek-v4-flash`. If the OpenCode Go Flash role fails, the runner first switches to Reasonix CLI `deepseek-v4-flash`, then tries Hermes OpenCode Go `qwen3.7-plus` and `mimo-v2.5`. Hermes' own Grok route is not used.
- Reasonix is used here only as the declared Flash fallback, not as a second review.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- User decision: imported protocols' pre-existing bibliography entries and in-text citations must be indexed and renumbered together with newly inserted references; keeping a second legacy numbering system is unacceptable.
- `services/api/app/medical_writing_document_exporter.py`
- `services/api/app/medical_writing_literature.py`
- `services/api/app/medical_writing_repository.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/MedicalWritingLiteraturePanel.jsx`
- `tests/test_medical_writing_citation_export.py`
- `tests/test_medical_writing_literature.py`
- Real imported RUX protocol: the registered `参考文献` section contains 19 bracket-numbered bibliography paragraphs.

## Scope

- In scope: import-time/backfill extraction of legacy bibliography entries; binding legacy in-text numeric citations to those entries; deterministic first-occurrence renumbering across legacy and new managed citations; ambiguous/missing/orphan handling; rich-text editor representation; project literature identity/deduplication; DOCX superscript hyperlinks/bookmarks; audit and rollback; real RUX/PNH verification.
- Out of scope: external web literature discovery, scientific appraisal of each cited paper, automatic replacement of a citation when no unique bibliography match exists, and final browser/Word acceptance (Codex only).

## Success Criteria

- One canonical reference object per project reference, including imported legacy entries and newly retrieved DOI/PMID entries.
- All uniquely resolvable legacy body citations and all new citations use the same structured mark; numbering is a projection based on first body occurrence.
- Existing bibliography paragraphs are regenerated once from indexed objects, with no duplicate numbering or silent loss.
- Ranges/multiple citations, uncited bibliography entries, missing bibliography numbers, duplicate numbers and ambiguous text are handled explicitly and audibly.
- Original source remains immutable; migration writes a versioned working representation and can be rolled back/rebuilt.
- DOCX links, bookmarks and reference list can be verified from XML; project isolation and validation status remain enforced.

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
- Do not propose silently guessing a bibliography target from citation context.
- Do not modify production code or runtime data; this conference is read-only architecture review.

## Loop Log

- 2026-07-15 17:24:38: Conference initialized by `hermes_workflow_guard.py init-conference`.
