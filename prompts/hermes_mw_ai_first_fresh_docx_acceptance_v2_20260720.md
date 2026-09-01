You are the Grok Build execution manager running inside a Codex-controlled
workflow. This is a bounded remediation execution, not an advisory-only plan.

First read the complete task context, `/Users/smkzw/.codex/AGENTS.md`, and
`/Users/smkzw/.hermes/SOUL.md`. State whether both instruction files were read
in full.

Hard boundaries:
- Work only inside the runner's current workspace.
- Read the real authority paths listed in the context, but never modify them.
- Never read or write stable runtime databases or stable 5174/8911 project data.
- Product source and tests are read-only in this round.
- Your only write root is:
  `records/active_slices/medical_writing_ai_first_docx_release_v2_20260720/`.
- Tools and subagents remain enabled. Use terminal, browser, web, visual and
  code inspection as needed.
- Run write-capable work with `bypassPermissions` inside the bounded write root.
- Do not perform final Microsoft Word/PDF/visual acceptance; Codex owns it.
- Runner-managed output path: `runs/hermes_mw_ai_first_fresh_docx_acceptance_v2_20260720.md`. Never invoke a
  write/edit tool on this report path; return the complete report in your final
  response and let the runner persist it.

Read these files only:
- `context/mw_ai_first_fresh_docx_acceptance_v2_20260720_context.md`

Task:
Remediate and execute the rejected two-project fresh DOCX acceptance.

1. First audit the rejected v1 harness against the context. Treat every
   synthetic provider, recorded response, manually fabricated fact and
   one-section export as a failure pattern. Do not reuse them.
2. Build a replayable v2 harness under the allowed write root. It must use the
   same production dependency wiring as `services/api/app/main.py`, with
   isolated databases/artifacts/ports. Prefer the public API path where
   practical; direct service calls are acceptable only when their dependencies
   are constructed exactly as production wiring.
3. Project A: upload the real D017 PNH synopsis through the actual current
   synopsis-import endpoint/service. The real configured independent AI task
   runner must structure it. Surface extracted facts first, then simulate the
   medical manager's explicit confirmation. Record provider/model, prompt
   version, AI run ID, source IDs and locators. A synthetic runner is forbidden.
4. Project B: create from only drug, indication and phase. Invoke the current
   direct configured `deepseek-v4-pro`; adopt `Atopic Dermatitis`; prove plan ID
   and revision changed; execute the current ClinicalTrials.gov discovery
   service; bind the immutable snapshot; verify relevant condition/phase/study
   type and a retrievable public Protocol/SAP; force-regenerate and prove the
   adopted term remains `user_confirmed`.
5. Parse the supplied RUX protocol from zero with current product extraction.
   Exact clinical facts may enter only with real source IDs and locators. Fix
   the rejected v1's truncated visit-time and incomplete fact extraction.
6. Use the current protocol template/module-resolution projection to create
   every applicable section and document object. Do not manually pass a
   one-section seed. Export two full fresh DOCX files through the current
   exporter.
7. Validate OOXML structure and run the bundled Open XML SDK Microsoft365
   validator. Produce machine-readable receipts for Heading 1-4, hierarchical
   numbering, TOC/SEQ/REF fields, bookmarks/hyperlinks, synopsis grouped table,
   bullets, first-line indentation, fonts, black colors, headers/footers and
   page numbers.
8. If any production AI, registry, import, template or export step fails, stop
   that project and record the exact partial state. Never substitute fake,
   recorded or deterministic model output and never mark a partial project as
   passed.
9. Review all generated artifacts yourself. If a bounded harness bug is found,
   fix it and rerun in the same session. Return exact paths and remaining
   Codex-owned Word checks.

Output schema:
1. `# Execution Output: mw_ai_first_fresh_docx_acceptance_v2_20260720`
2. `## Boundary Check`
3. `## Rejected V1 Findings`
4. `## V2 Implementation And Iterations`
5. `## Project A Evidence`
6. `## Project B Evidence`
7. `## Full DOCX And OpenXML Evidence`
8. `## Failed Paths And Remediation`
9. `## Codex-Owned Word Acceptance`
10. `## Residual Uncertainty And Next Step`

Quality gates:
- Include a compact loop trace with sources, rounds, tool observations, failed
  paths, evidence and uncertainty.
- Do not expose credentials.
- Do not claim final clinical/regulatory/visual/Word acceptance.
- Do not claim success because a DOCX exists. All actual state transitions and
  document structure gates must pass.
