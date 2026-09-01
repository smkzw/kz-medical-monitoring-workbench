# Codex Conference Review: medical_writing_ctgov_pilot_v2_review_20260712

Date: 2026-07-12

## Verdict

Pass for the isolated Pilot V2 Pass7 evidence packet. The product direction remains formally approved, but production integration, translation, corpus/RAG admission and user exposure remain blocked.

## Route And Boundary Compliance

- Participants completed three same-session rounds: `buddy/deepseek-v4-pro`, `opencode-go/mimo-v2.5`, and `buddy/glm-5.2`.
- The sole Hermes sub-venue chair was exact `aishuo/MiniMax-M3`, session `20260712_101811_fff274`, three rounds, no fallback.
- Generated GLM-chair configuration was removed before dispatch because it conflicted with the user's project-specific aishuo-chair override.
- Models read only bounded manifests, reports, code or review outputs. No model read raw PDFs, extracted protocol text or page renders; no model translated source content or changed production code.
- Two Codex SubAgent audits failed before execution because the quota was exhausted. They provide no evidence and are recorded only as a process limitation.

## Reproducible Finding And Fix

MiMo and GLM independently identified that the AD query index recorded `reported_total_count=null`. Codex reproduced the defect: the script read `totalCount` only after the final page, while ClinicalTrials.gov supplied it on the first page. Pass7 now retains the first non-null total, rejects cross-page drift, and fails closed if no total is supplied. Four unit tests pass.

Pass7 then ran twice from the immutable snapshots. AD verifies 453 returned = 453 reported across five pages; PNH verifies 49 = 49 across one page. The immutable manifest SHA-256 is `4e477844968c8dc6a113561f5634ed1cef3be5ca05feb4979cdc54b1115bc946`.

## Codex Verification

- Six selected studies, six sponsors, two indication/phase combinations and nine official protocol/SAP documents.
- All nine receipts match PDF magic, declared size and SHA-256.
- All nine analyses remain `corpus_admission=blocked` and `writing_rag_visibility=prohibited`; no translation or medical/statistical approval was run.
- Thirty-seven page renders were generated. Codex inspected six original-resolution pages across NCT02615249, NCT04246372 and NCT05014438; the sample had no blank, crop or rotation defect.
- The two low structure-coverage documents are recorded medical-relevance negative samples. Their 0.5/0.667 category coverage cannot prove that direct AD competitor extraction has architecturally failed. The new direct AD competitor NCT05014438 has 1.0 category coverage and readable title/statistics renders.
- The 13-hour NCT05014438 timing difference is a cross-day continuation artifact, not a source-integrity defect.

## Accepted Open Gates

- Written legal/compliance policy for translation, model processing, retention, deletion, internal reuse and third-party materials.
- Production-grade quarantine, malicious-PDF handling, sandboxed parsing, resource limits and prompt-injection/content-poisoning controls.
- Generic page/block/table/footnote/formula/OCR-VLM extraction with visual truth and immutable span lineage.
- Versioned CDE/company terminology, numeric/unit/negation/endpoint checks and medical/statistical approval.
- Source-constrained, project-isolated RAG with version withdrawal, no-near-copy controls and complete usage audit.
- At least two real end-to-end production projects with all buttons and failure branches tested.

## Final Decision

Accept Pass7 as a completed research pilot and preserve all artifacts. Keep the feature in the formal medical-writing roadmap. Do not merge downloader, parser, translation, database, index, API or frontend entry into production until the P0 gates above pass and the user chooses the next integration boundary.
