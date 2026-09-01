# Medical Writing Revision UI Research - 2026-07-08

## Scope

This note supports the `medical_writing_revision_ui_20260708` slice. The implementation target is not a new writing engine; it is the frontend interaction layer that connects the existing rich protocol editor to the existing revision-thread backend while preserving medical approval and independent-AI boundaries.

## Current Local Baseline

- The frontend already depends on Tiptap 3 (`@tiptap/react`, `@tiptap/starter-kit`, table extensions) and renders a contenteditable protocol editor.
- The backend already exposes:
  - `GET /api/projects/{project_id}/revision-threads`
  - `POST /api/projects/{project_id}/revision-threads`
  - `POST /api/projects/{project_id}/revision-threads/{thread_id}/actions`
- The current backend suggestion generator is explicitly deterministic and non-production:
  - provider: `deterministic_demo_non_production`
  - model: `medical_writing_revision_stub_requires_ai_gateway`
  - status: `not_configured_demo_stub_only`
  - accepted suggestions do not apply text into the protocol body.

## Technical Sources Reviewed

1. Tiptap official documentation
   - URL: https://tiptap.dev/docs/editor/getting-started/install/react
   - URL: https://tiptap.dev/docs/editor/api/events
   - Evidence strength: high for current frontend editor choice.
   - Relevance: confirms staying within the installed Tiptap/ProseMirror stack is appropriate for React editor integration and editor event handling. No second editor framework should be introduced for this slice.

2. ProseMirror official reference
   - URL: https://prosemirror.net/docs/ref/
   - Evidence strength: high for selection/transaction concepts behind Tiptap.
   - Relevance: selection state and document transactions should remain editor-controlled. For this slice, submitting selected text to a revision API is lower risk than attempting document-transform application.

3. Tiptap GitHub repository
   - URL: https://github.com/ueberdosis/tiptap
   - Evidence strength: medium-high for maintenance posture and ecosystem fit.
   - Relevance: installed dependency is actively maintained enough for a local prototype/commercialization path; no need to switch to Slate/Lexical now.

## Commercial / Regulatory Workflow Sources Reviewed

1. ICH M11 / clinical electronic structured harmonised protocol materials
   - URL: https://www.ich.org/page/multidisciplinary-guidelines
   - Evidence strength: high for protocol-structure direction.
   - Relevance: supports a structured protocol-writing model with section anchors and traceable content blocks rather than freeform AI text only.

2. FDA Part 11 / electronic records and electronic signatures topic
   - URL: https://www.fda.gov/regulatory-information/search-fda-guidance-documents
   - Evidence strength: high for future compliance direction, although this slice is not implementing Part 11.
   - Relevance: approval/audit boundaries should be preserved. This slice must not imply electronic signature, formal approval, or regulatory-ready output.

3. Veeva official product materials for clinical document workflows
   - URL: https://www.veeva.com/products/vault-clinical/
   - Evidence strength: medium for product pattern only.
   - Relevance: mature clinical platforms emphasize controlled clinical content, review workflows, and document governance. The comparable pattern here is a bounded review suggestion rail, not AI overwrite.

## Decision

Use the existing Tiptap editor and existing backend revision-thread API. Build the smallest usable frontend loop:

1. Capture a selected text snippet from the Tiptap editor, with a fallback to the current section body.
2. Let the user enter a revision instruction and choose an intent.
3. Submit the request to `/revision-threads`.
4. Render returned thread/suggestion as `待医学批准` content candidate.
5. Support accept/reject/request-rewrite actions through the existing action endpoint.
6. Preserve the boundary that accepted suggestions are not written into the formal protocol text.

## Rejected Alternatives

- Introduce Lexical/Slate: rejected because Tiptap is already installed and integrated.
- Directly mutate protocol正文 on accept: rejected because backend tests explicitly require accepted suggestions not to apply text.
- Implement DOCX roundtrip/export now: rejected as a separate larger slice requiring source-format preservation, comments, revision marks, and export QC.
- Hide the deterministic AI stub status: rejected because the system must run independently from Codex and must honestly show when the independent provider is not configured.

## Acceptance Criteria For This Slice

- Frontend code calls `GET /revision-threads`, `POST /revision-threads`, and `POST /revision-threads/{thread_id}/actions`.
- The AI rail no longer presents only a static `AI 修订线程 #3`.
- The user can submit a revision instruction from the editor page.
- Returned suggestions visibly show:
  - user instruction,
  - proposal text/diff,
  - uncertainty,
  - AI gateway status,
  - `待医学批准` boundary,
  - no automatic formal正文 overwrite.
- Browser QC covers desktop and mobile and exercises submit + action flow.
- Static tests verify API wiring and boundary wording.
