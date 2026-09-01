# Codex Execution Review: mw_release_execution_round2_20260720

## Verdict

RERUN REQUIRED. Worker 03 remains blocked.

## Worker Outputs

- Worker 01: implementation present; Qoder has reproduced 25 focused and 95
  adjacent tests under arm64 Python. Semantic review remains pending.
- Worker 02: first implementation is structurally present but materially below
  the acceptance contract and must continue in the same session.
- Worker 03: intentionally not dispatched until Worker 01/02 gates pass.

## Manager Assessment

- Phase A plan received from QoderVIP/qodercli Qwen3.8-Max-Preview.
- Phase B corrected review is complete. It independently retained Worker 01's
  25 focused and 95 adjacent passing tests, reproduced all seven Worker 02
  defects, and issued `BLOCK_WORKER_03`.
- Worker 02 same-session rerun is active under original Hermes session
  `20260720_131451_db86d8`; execution process session is `46171`.

## Directly Reproduced Worker 02 Defects

1. The supplied RA synopsis exists at the user-provided path and hashes to
   `f6c8fdf53535a58f0f05055fe07c3a34bb0932f30c8bc2a7cdb6f8fc97dc8be4`;
   all RA import lanes currently set `synopsisSourcePath: null`.
2. `NCT04654468` is reused for every RA lane although the existing corpus config
   maps it to PNH. Other indications likewise reuse one NCT across Phase I and
   Phase III without phase/design evidence.
3. Parent creates one shared isolated runtime before the lane loop.
4. Child full mode stops after framing/synopsis confirmation and explicitly
   assigns the rest of the product pipeline to Worker 03.
5. Several import sources are phase-incompatible with their declared lanes.
6. Existing 20/20 structure QC does not reject any of the above false-green
   conditions.

Primary-source verification:

- ClinicalTrials.gov identifies `NCT04654468` as a Phase III PNH crovalimab
  study, not RA.
- ClinicalTrials.gov identifies `NCT05923099` as a Phase IIb atopic dermatitis
  temtokibart study, not a Phase I/III universal sentinel.
- ClinicalTrials.gov identifies `NCT03451422` as a Phase Ib/IIa SLE
  efavaleukin alfa study, not plaque psoriasis.

Same-session remediation contract:
`prompts/execution/mw_release_execution_round2_20260720/worker_02_rerun_01.md`.

## Hy3 Evidence Review

Hy3's report is accepted only as a lower-level isolated API/OOXML probe. Its
release recommendation is rejected because it did not trigger product AI,
browser, Word, real synopsis extraction, competitor discovery, OCR/translation,
citations, or candidate writing, and its temporary runner manually injected
clinical facts. Three new rerun targets are retained:

1. explain and correct `期中分析` appearing in every Phase I DOCX;
2. keep active-comparator regimen details solely in the structured IP regimen,
   not `structured_design.comparator_intervention` free text;
3. project background therapy through structured non-IP `BACKGROUND` rules,
   not only `picos.required_background_rules` strings.

Codex independently parsed the two retained follow-up DOCX artifacts before
Hy3 issued its report:

- `phase1_no_interim.docx`
  SHA-256 `4a64e763d1e5d09f02cd28beaeef0f397eee253e789226aa925076658646e0a9`
  still contains two real empty headings despite
  `structured_design.interim_analysis.planned=false`:
  `期中分析的依据` (`Heading3`) and `期中分析` (`Heading2`). These are not
  TOC field-cache strings. The false branch therefore fails dynamic chapter
  omission.
- `phase3_interim_authority.docx`
  SHA-256 `f174a8b28895015452be695572b8f692363a11a1aed3833d7ce6fa4bdd44fa66`
  contains expected interim-analysis narrative and headings, but
  `TEST_DOSE / TEST_ROUTE / TEST_FREQUENCY / TEST_DURATION` appears only in a
  generic `剂量与给药方案` synopsis row while `TEST_ACTIVE_COMPARATOR` appears
  separately in the comparator row. Structured JSON evidence is still needed
  to prove or refute active-comparator IP-regimen authority.
- `TEST_BACKGROUND_THERAPY` does not appear anywhere in the Phase III DOCX,
  so background-treatment structured projection is currently failed or was
  not created. The expected structured JSON remains pending.

These are direct OOXML observations, not Hy3 conclusions. The minimum current
classification is P1 for false Phase I interim headings and P1 for missing
background-therapy output. Active-comparator single-authority status remains
pending the structured evidence JSON.

Hy3 subsequently wrote
`hy3/artifacts/structured_authority_evidence.json`. Codex accepts its direct
API/state evidence but rejects its Phase I `PASS` label:

- Phase III standard flow persisted
  `structured_design.comparator_intervention=TEST_ACTIVE_COMPARATOR`,
  `picos.intervention_dose_regimen=TEST_DOSE / TEST_ROUTE /
  TEST_FREQUENCY / TEST_DURATION`, and
  `picos.required_background_rules=[TEST_BACKGROUND_THERAPY]`, while
  `picos.intervention_rules` was absent and both structured IP/non-IP
  collections were empty.
- A supplementary manual commit proved the schema can persist
  `product_role=active_comparator` and `rule_class=background`, but this manual
  injection is not the standard AI-prefill/adoption workflow and its projection
  calls returned 404 because no greenfield working copy existed in that probe.
- Therefore active-comparator and background-therapy failures are pipeline
  wiring defects, both P1.
- Phase I remains P1 because the accepted contract requires the non-applicable
  module to be omitted, not merely rendered as an empty Heading2/Heading3 pair.

Current Codex verdict for all three structured-authority targets: `P1 / P1 /
P1`.

## Codex Independent Verification

Pending. Required checks:

1. Parse old and new journey JSON through current Pydantic contracts.
2. Adopt each orthogonal design candidate, save/reload/regenerate, and verify
   only the intended structured fact and compatibility projection change.
3. Verify interim true/false/unknown across synopsis, dynamic chapter matrix,
   source bindings, body seed and DOCX.
4. Verify active comparator regimen and complex background therapy have one
   authoritative structured source and deterministic compatibility projection.
5. Run focused and adjacent backend tests; build frontend.
6. Run CDP structure QC and isolated dry-run; compare stable runtime hashes.
7. Run the 12 product-AI lanes only after steps 1-6 pass.
8. Reproduce every P0/P1, fix, and rerun the same lane from a fresh runtime.
9. Inspect exported OOXML plus actual Microsoft Word rendering, navigation,
   TOC, typography, tables, SVG/fallback, attachments and citations.

## Cleanup Decision

Do not archive until Worker 03, manager Phase B, and Codex independent
acceptance are complete.

## Structured-Authority P1 Acceptance

Codex accepts the bounded product fix produced under Hermes session
`20260720_150111_3d9c06`.

Direct verification:

- `tests/test_medical_writing_structured_authority_p1_fix.py` plus four
  adjacent protocol-template/prefill/intervention-rules suites: `99 passed`.
- The retained Phase I DOCX
  `runs/execution/mw_structured_authority_p1_fix_20260720/artifacts/phase1_no_interim.docx`
  has SHA-256
  `fa52a9c7ac5de8d538f38d24bd0b32646e8a66d7f5e75497848371c49df28306`
  and zero `期中分析` headings/body occurrences.
- The retained Phase III DOCX
  `runs/execution/mw_structured_authority_p1_fix_20260720/artifacts/phase3_interim_authority.docx`
  has SHA-256
  `7a5da33c3542e0620f305106590011911b0047f96ae094039fd151bb4b722b47`
  and retains the two applicable interim-analysis headings.
- `design.comparator_type=活性对照` now upserts exactly one
  `product_role=active_comparator` IP regimen. Dose/frequency, route and
  treatment period are accepted only from that explicit candidate map, never
  from the generic investigational-product free-text regimen.
- `picos.required_background_rules` now materializes one structured
  `rule_class=background` non-IP rule per source statement while preserving
  CM, rescue and IP action-rule classes. The legacy fields are one-way
  deterministic compatibility projections when structured authority is active.

Residual, separately tracked upstream gap:

- The production DeepSeek prefill adapter's current `_AI_ELIGIBLE_FIELDS`
  excludes `design.comparator_type`, so it cannot yet originate an
  evidence-backed structured active-comparator regimen candidate itself.
  This does not invalidate the now-correct adoption/materialization layer; it
  remains a required AI-first prefill enhancement before final release.
