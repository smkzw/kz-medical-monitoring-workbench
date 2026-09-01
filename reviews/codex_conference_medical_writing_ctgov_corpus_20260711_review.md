# Codex Conference Review: medical_writing_ctgov_corpus_20260711

Date: 2026-07-11

## Verdict

Pass as an isolated research and product-architecture decision; **NO-MERGE for production code/runtime**. The direction is technically and strategically valid, but production remains blocked by rights governance, secure ingestion, generic parsing/OCR, controlled terminology, immutable revision lineage, source-constrained RAG and medical/statistical approval.

## Boundary Compliance

- Qwen, Mimo, DeepSeek Flash, and Minimax wrote only their assigned conference outputs.
- Qwen had one controlled HTTP 500 retry and then completed.
- Mimo read `pilot_ctgov_protocol_ingest.py` although that script was not in its prompt's explicit read list. This is a minor boundary overread; its conclusions remain reviewable but are not accepted without Codex source verification.
- No participant had authority to modify production code, browse current web sources, or make the final clinical/regulatory decision.

## Participant Outputs Reviewed

- `participant_qwen_plus`: completed; useful architecture and rights controls, but its Chinese candidate uses non-authoritative E9(R1) terms and mis-expands SCS in one discussion.
- `participant_mimo`: completed; useful risk inventory, but uses materially incorrect terms such as “期中事件” and “复合终点” for E9(R1) strategy language.
- `participant_ds_flash`: completed through Reasonix; strongest factual handling of SCS and “伴发事件”, but still shortens CDE “疗法策略/复合变量策略”.
- `hermes_lead`: completed; correctly rejects Mimo's major terminology errors and supports a research-only gate, but over-rates Qwen because it lacked the later authoritative CDE terminology check.

## Hermes Sub-Venue Review

The Hermes chair recommends architecture approval for isolated research only. It identifies three hard production prerequisites: written legal/compliance policy, OCR/VLM fallback for poor PDFs, and revision-chain data modeling. Codex accepts those as necessary but not sufficient; prompt-injection/content-poisoning controls, source-constrained retrieval, and medical corpus admission are also hard gates.

## Main-Venue DeepSeek Pro Review

- Completed through Reasonix `deepseek-pro` with the authoritative CDE terminology check.
- Confirmed that none of the three candidate translations meets the full CDE term standard.
- Ranked DeepSeek Flash as the closest working candidate but still requiring `疗法策略` and `复合变量策略` corrections.
- Invalidated the Hermes chair's earlier preference for Qwen because Qwen used `间发事件` and `治疗策略法` and overclaimed ICH alignment.
- Recommended research-only continuation with hard prerequisites; it did not authorize production.

## Codex Independent Verification

- Re-ran the official ClinicalTrials.gov API/download pilot on two public CRSwNP Phase 3 protocols and verified PDF signatures, hashes, extracted character counts, and source locators through the pilot manifest.
- Verified ClinicalTrials.gov API/terms/results-document requirements against official pages during the research pass.
- Verified Chinese E9(R1) terminology against the local CDE official extraction: 估计目标、伴发事件、疗法策略、复合变量策略、假想策略、在治策略、主层策略、群体层面汇总.
- Found a material participant overclaim: the pilot has no authoritative CDE mapping for `Worst Possible Carried Forward` or `Worst Observation Carried Forward`; both English phrases must be retained and sent to statistical review.
- Live API recheck on 2026-07-11 still returned 45 studies and 17 with protocol/protocol+SAP; API v2.0.5 and data timestamp matched the manifest.
- Recalculated both PDF SHA-256 values; both matched the manifest.
- Verified directly in the AZ PDF that SCS means `systemic corticosteroids`, `Populationa` is a real footnote marker, and both WPCF/WOCF phrases occur in the source page. This closes three main-review uncertainties without relying on model inference.
- No production code has been changed for this feature.

## Final Decision

- Approve the product direction and the layered architecture as a formal medical-writing roadmap item.
- Preserve the pilot, conference outputs and downloaded artifacts in the isolated research directory.
- Do not merge any downloader, parser, translation path, database table, vector index, API route or frontend entry into the production workbench yet, including a disabled research flag.
- Reopen production integration only after the seven P0 gates in `PRODUCTION_FEATURE_DECISION.md` pass and at least two different real projects complete end-to-end regression.
