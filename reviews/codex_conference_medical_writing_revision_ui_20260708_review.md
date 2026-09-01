# Codex Conference Review: medical_writing_revision_ui_20260708

Date: 2026-07-08 CST

## Verdict

Pass for this bounded 医学写作 revision-interaction and desktop-first layout slice.

This does not certify the full 医学写作 subsystem. It accepts only the verified behavior currently in scope: the rich editor page has a real revision request/action workflow, talks to the existing backend revision-thread API, keeps AI suggestions as `待医学批准` candidates, does not auto-write AI text into the formal editor body, and now presents document editing plus AI interaction as the first-screen core workspace.

## Boundary Compliance

- Original project materials remain read-only; this slice changes only the workbench implementation and conference records.
- User-facing subsystem naming remains business-name only; no lifecycle labels such as `第8环节`, `阶段8`, or `Stage 8` are visible in the QC DOM.
- The UI explicitly states that AI revision suggestions are `待医学批准` content candidates and do not automatically enter formal正文.
- Browser QC confirmed no local absolute paths leak into rendered medical-writing content.
- Browser QC confirmed no overclaim text such as `自动定稿`, `正式方案已生成`, or `可直接提交监管`.
- Global frontend acceptance rule is desktop-first for all subsystems. Mobile is smoke/degradation only and must not drive desktop feature cuts.
- Buddy GLM/Kimi failures are retained as supplier-route evidence. Per the user's latest instruction, failed Buddy coverage is replaced by `opencode-go/qwen3.7-plus` and `opencode-go/mimo-v2.5`.

## Participant Outputs Reviewed

- `runs/conference/medical_writing_revision_ui_20260708/participant_qwen_plus.md`: accepted as advisory and as fallback product/Chinese-clinical wording coverage after the Buddy GLM failure.
- `runs/conference/medical_writing_revision_ui_20260708/participant_mimo.md`: accepted as advisory and as fallback frontend/interaction coverage after the Buddy Kimi failure.
- `runs/conference/medical_writing_revision_ui_20260708/participant_ds_flash.md`: accepted as advisory scoped-code review; strongest detail on TDD, no-auto-write, and revision-boundary risks.
- `runs/conference/medical_writing_revision_ui_20260708/participant_glm52_product.md`: route-failure record retained. HTTP 400 `不支持的模型: GLM-5.2`; not treated as evidence about product correctness.
- `runs/conference/medical_writing_revision_ui_20260708/participant_kimi_frontend.md`: route-failure record retained. HTTP 400 invalid request parameters; not treated as evidence about frontend correctness.

## Hermes Sub-Venue Review

`runs/conference/medical_writing_revision_ui_20260708/hermes_lead.md` was reviewed.

The Hermes chair found high convergence among qwen, mimo, and DeepSeek Flash:

- backend revision endpoints already exist;
- frontend revision rail was the primary gap;
- AI suggestions must stay pending medical approval;
- accepted suggestions must not automatically alter protocol正文;
- TDD and browser QC are required;
- no final clinical/regulatory or visual acceptance should be delegated to Hermes.

Hermes also flagged useful Codex verification items: section-id mapping, AI gateway status disclosure, visual/browser verification, local path leak checks, lifecycle-label checks, overclaim checks, and backend/API tests.

The Hermes chair output predates the user's new fallback instruction. Codex applies the updated instruction here: failed Buddy routes are replaced for coverage by qwen/mimo, while failure evidence remains in metrics.

## Main-Venue DeepSeek Pro Review

`runs/conference/medical_writing_revision_ui_20260708/main_deepseek_pro.md` was produced through the DeepSeek supplier `deepseek-v4-pro` route.

DeepSeek Pro recommended conditional acceptance and asked Codex to verify three pre-signoff items:

- section-id mapping between frontend business section `endpoints` and backend protocol section `sec_objectives_endpoints`;
- accepted-state badge wording, so `accepted_pending_medical_approval` cannot be misunderstood as formal medical approval;
- known lower-priority product gaps filed into the subsystem log.

Codex completed those checks and made one implementation refinement:

- `frontend/src/App.jsx` maps `endpoints` to `sec_objectives_endpoints`, and `tests/test_contracts.py` plus `tests/test_medical_writing_revision_api.py` use the same backend section id.
- `accepted_pending_medical_approval` now renders as `已接受，仍待医学批准`.
- `frontend/tests/medical_writing_manifest_qc.mjs` now checks for `已接受，仍待医学批准`.
- `logs/subsystems/medical_writing_log.md` records the remaining product gaps after this slice.
- User corrected the page hierarchy: 医学写作 should center on document editing and AI interaction, not show the source package first. Codex moved the source manifest below the core writing workspace and added static/browser checks to lock that hierarchy.

## Codex Independent Verification

Source/contract checks already performed:

- `frontend/src/App.jsx` contains `refreshRevisionThreads`, `submitRevisionRequest`, and `submitRevisionAction`.
- `frontend/src/App.jsx` calls:
  - `GET /api/projects/${PROJECT_ID}/revision-threads`;
  - `POST /api/projects/${PROJECT_ID}/revision-threads`;
  - `POST /api/projects/${PROJECT_ID}/revision-threads/${thread.thread_id}/actions`.
- `activeThread` is now derived from current-section `sectionThreads` first, avoiding project-level revision-thread bleed across sections.
- Static thread text `AI 修订线程 #3` is no longer the source contract for the revision rail.
- `frontend/tests/medical_writing_manifest_qc.mjs` treats desktop as the blocking viewport and mobile as `mobile-smoke`, matching the user's desktop-first requirement.
- `frontend/src/App.jsx` now renders `.writing-layout` before `MedicalWritingManifestPanel`, so the first screen is the chapter tree, rich editor, and AI rail.
- `frontend/tests/medical_writing_manifest_qc.mjs` now asserts `editorInFirstViewport`, `aiRailInFirstViewport`, `editorBeforeSourceManifest`, and `aiRailBeforeSourceManifest`.

Executed checks:

- `python3 -m unittest tests.test_frontend_medical_writing_contract -v`: 5 OK.
- `python3 -m unittest tests.test_frontend_medical_writing_contract tests.test_medical_writing_revision_api tests.test_medical_writing_manifest -v`: 14 OK.
- After DeepSeek Pro and user layout correction: `python3 -m unittest tests.test_frontend_medical_writing_contract tests.test_medical_writing_revision_api tests.test_medical_writing_manifest -v`: 17 OK.
- `npm --prefix frontend run build`: passed with the known Vite chunk-size warning only.
- `APP_URL=http://127.0.0.1:5174/ QC_OUTPUT_DIR=.../records/visual_qc_20260708/medical_writing_revision_ui CHROME_DEBUG_PORT=9394 node frontend/tests/medical_writing_manifest_qc.mjs`: passed.
- Refreshed after layout correction: same browser QC route passed with `CHROME_DEBUG_PORT=9397`.
- Full regression before layout correction: `python3 -m unittest discover -s tests -v`: 150 OK.
- Final post-layout full regression: `python3 -m unittest discover -s tests -v`: 151 OK.

Browser/QC evidence:

- Metrics: `records/visual_qc_20260708/medical_writing_revision_ui/medical_writing_manifest_qc.json`.
- Desktop screenshot: `records/visual_qc_20260708/medical_writing_revision_ui/medical_writing_manifest_desktop.png`.
- Mobile smoke screenshot: `records/visual_qc_20260708/medical_writing_revision_ui/medical_writing_manifest_mobile-smoke.png`.
- Desktop metrics confirmed: no horizontal overflow, no local path leak, no lifecycle label, no overclaim, rich editor present, revision form present, revision thread list present, accepted-candidate state present, approval button blocked, and `editorTextContainsAiSuggestion=false`.
- Refreshed desktop metrics additionally confirmed: editor and AI rail are in the first viewport and both are above the source manifest.
- Codex visually inspected the refreshed desktop screenshot and accepted the current three-column workbench layout for this slice.

## Final Decision

Accept this slice as implemented and verified with these remaining product gaps:

- real independent LLM provider is not configured;
- deterministic backend stub still produces the revision suggestion;
- accepted candidates are not DOCX tracked changes or formal exports;
- full approval-center synchronization is not complete;
- IB/ICF/CTD writing expansion remains future scope;
- mobile is intentionally only smoke/degradation, not the product-design target.
