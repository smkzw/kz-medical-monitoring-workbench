You are continuing the same Hermes/aishuo/cms-model execution session
`20260720_131451_db86d8` for task
`mw_release_execution_round2_20260720`, role `worker_02`.

Before doing anything else, fully read `/Users/smkzw/.hermes/SOUL.md` and
honestly state in the final report that it was read.

This is a targeted same-session remediation pass. Do not restart analysis from
scratch and do not ask Codex routine questions. You remain the write-capable
owner of only these files:

- `frontend/tests/final_release_12lane_config.mjs`
- `frontend/tests/final_release_12lane_child.mjs`
- `frontend/tests/final_release_12lane_parent.mjs`
- `frontend/tests/final_release_12lane_structure_qc.mjs`

You may also add narrowly scoped harness-only helper files under
`frontend/tests/` when they are necessary to keep the parent/child code
maintainable. Do not modify contracts, product API/frontend implementation,
exporter, stable runtime, or production data. You have full tool, web, browser,
and terminal permissions within this boundary. The runner writes the report;
do not edit the runner-managed report path.

## Hard boundaries

- Work only inside the current workspace root except for read-only inspection
  of the explicitly named local synopsis/protocol inputs and primary web
  evidence.
- Modify only the owned harness files listed above and any strictly necessary
  helper under `frontend/tests/`.
- Never modify or clear stable runtime, product source, contracts, exporter,
  user originals, credentials, or production data.
- Do not install dependencies or disable tools.
- Codex retains final browser, Microsoft Word, medical, regulatory, and release
  acceptance.
- Runner-managed output path: `runs/execution/mw_release_execution_round2_20260720/worker_02_rerun_01.md`.
  Return the complete report in final text; never call a write/edit tool on
  that report path.

## Read these files only:

- `AGENTS.md`
- `context/mw_release_execution_round2_20260720_execution_context.md`
- `plans/codex_execution_mw_release_execution_round2_20260720.md`
- `records/active_slices/medical_writing_final_release_e2e_20260720/ACCEPTANCE_CONTRACT.md`
- `runs/execution/mw_release_execution_round2_20260720/manager_plan.md`
- `runs/execution/mw_release_execution_round2_20260720/worker_02.md`
- `reviews/codex_execution_mw_release_execution_round2_20260720_review.md`

This is an initial context list, not a prohibition on tools or on reading
direct propagation-path source, the completed manager review when present, or
the four owned harness files and real local protocol/synopsis inputs needed to
implement and verify the harness. Record every additional target and why it
was necessary.

## Why the first pass is rejected

Codex directly reproduced these defects:

1. The real RA source exists:
   `/Users/smkzw/Documents/朗来项目资料/MY004/RA/MY004-RA-2b 研究方案摘要_V0.3-with Comments to ABBV.docx`
   (SHA-256
   `f6c8fdf53535a58f0f05055fe07c3a34bb0932f30c8bc2a7cdb6f8fc97dc8be4`).
   The first pass incorrectly set all RA synopsis sources to `null`.
2. The first pass reused one NCT sentinel for every phase and entry mode of an
   indication. It assigned `NCT04654468` to RA although the existing project
   config maps it to PNH. Sentinels must be established from current primary
   ClinicalTrials.gov evidence and must match indication, phase, product
   modality, public document role, and the intended design pressure. Do not
   copy old config values or use one convenient trial across unrelated lanes.
3. `final_release_12lane_parent.mjs` creates one shared
   `mw-12lane-runtime-*` directory and runs all 12 lane projects in it. The
   acceptance contract requires a fresh isolated runtime and a fresh project
   for every lane. A new lane must start with no prior lane databases,
   projects, sources, corpus, AI runs, citations, or documents.
4. `final_release_12lane_child.mjs` explicitly stops after project
   creation/synopsis confirmation/framing and delegates competitor search,
   download, validation, parsing/OCR/translation, corpus mapping, chapter
   candidates, references, editing, and DOCX export to Worker 03. Worker 03 is
   an execution runner, not the owner of missing harness source. The harness
   itself must drive the entire product journey before the expensive run is
   authorized.
5. Several imported sources do not match their declared lane. An AD Phase III
   protocol cannot serve as an AD Phase I synopsis; an AD Phase II template
   cannot prove an AD Phase III active-comparator import; one PsO Phase II/III
   protocol cannot be silently relabelled as both a Phase I SAD/MAD source and
   a Phase III design source. Use the real RA synopsis above and search the
   authorized local corpus for content-compatible real inputs. If an exact
   synopsis source is unavailable, use a clearly justified content-compatible
   source only when the product's basic-information/content validator detects
   the mismatch and the simulated user explicitly overrides it with a recorded
   reason. Never hide a mismatch in config comments.
6. The current structure QC checks implementation shape but does not fail on
   the five defects above, so 20/20 is a false-green gate.

## Required remediation

### A. Correct and auditable 12-lane matrix

- Keep exactly RA/AD/plaque psoriasis × Phase I/III × greenfield/synopsis
  import.
- Bind the provided RA synopsis to the appropriate RA synopsis-import lane(s)
  based on its actual content. Inspect its basic metadata and extracted content
  through the product path; do not infer from filename alone.
- Locate content-compatible local sources for the other synopsis-import lanes
  with `rg`, `find`, and document metadata/content inspection. Record path,
  SHA-256, declared role, detected indication/phase/role, validation result,
  and any explicit override reason in evidence.
- Use current ClinicalTrials.gov primary evidence to define lane-specific
  expected study and document sentinels. Record NCT ID, phase, condition,
  sponsor, intervention/modality, document filename/date/role, query, and
  retrieval timestamp. Prefer recent innovative-drug MNC studies with public
  Protocol/SAP. A sentinel may be reused only when the same public study
  legitimately satisfies both entry modes of the same indication/phase; the
  evidence must show why.
- A sentinel is an assertion target, not an input that bypasses product search.
  The product must rediscover it from the lane's minimal facts.

### B. True per-lane isolation

- For each lane, create a new `mkdtemp` runtime before starting its API.
- Start and stop isolated API/Vite as needed so `WORKBENCH_RUNTIME_DIR` is read
  at startup for that lane.
- Capture stable-runtime hash before and after each lane, isolated SQLite
  integrity, lane runtime identifier, and cleanup status.
- Never share isolated SQLite state across lanes. Add deterministic structure
  assertions that reject a parent with a single runtime outside the lane loop.

### C. Full product-owned journey in the child harness

The full-mode child must use real product UI/product APIs, in the user's real
order, to drive and record:

1. minimal new-project input and entry-mode selection;
2. optional IB/no-IB path and product AI framing prefill;
3. real synopsis import/extract/review/confirm when applicable;
4. ClinicalTrials.gov competitor discovery and public Protocol/SAP download;
5. basic file information/content validation and explicit override when
   justified;
6. product OCR/section recognition/Hy-MT2 translation/Flash integration QC and
   corpus-candidate admission, with production route evidence;
7. product DeepSeek-v4-pro complete PICOS/design prefill and user
   select/edit/confirm;
8. dynamic chapter matrix, synopsis, study flow diagram, SoA/notes, and
   structured tables;
9. 3-5 chapter candidates and actual accept/edit/regulatory tone/consistency/
   evidence/expand/shorten/undo/redo/save/reload operations;
10. literature import paths available in the product (DOI/PMID/PubMed URL/
    publisher URL), inline superscript hyperlink and reference reindex QC;
11. full contents/table/figure lists, study-flow vector/fallback and image/
    assessment attachment paths;
12. real DOCX export through the product.

The execution model must never generate clinical text or fabricate evidence in
place of product AI. Use bounded retries, medical-language progress capture,
and failed-stage-only retry where the product supports it. Dry-run may use
short deterministic no-external-call checks, but full mode must implement the
complete chain now.

### D. Evidence and false-green prevention

Every successful full lane must emit all ten JSON artifacts required by
`ACCEPTANCE_CONTRACT.md`, plus screenshots and exported DOCX paths. Evidence
must contain real stage timestamps/status, not empty arrays or placeholder
objects. Add schema/semantic checks that fail when:

- synopsis-import does not actually import a file;
- source indication/phase/role is unchecked;
- product search does not rediscover a matching public trial/document;
- OCR/translation/corpus or product-AI evidence is missing;
- candidate count is outside 3-5;
- citations/edit/save-reload/export are not exercised;
- lane runtime is reused;
- exported DOCX does not exist or is zero bytes.

### E. Verification before returning

Run and report:

- structure QC;
- one greenfield dry-run;
- one synopsis-import dry-run using the real RA file;
- old 4-lane structure/regression dry-run;
- static checks proving the complete full-mode chain is reachable;
- stable-runtime hash comparison and isolated SQLite integrity.

Do not start the 12-lane production-AI long run. Return only after all owned
files are corrected and these gates pass. If a product endpoint/control is
missing, provide the exact endpoint/control, observed response, smallest
product-source patch needed, and a harness regression assertion; do not mark
the chain complete.

## Output

Return a compact complete execution report with:

1. `# Execution Output: mw_release_execution_round2_20260720 - worker_02 rerun 01`
2. `## Boundary And Context Check`
3. `## Defects Reproduced`
4. `## Remediation Implemented`
5. `## ClinicalTrials And Local Source Evidence`
6. `## Commands And Test Results`
7. `## Remaining Product Blockers`
8. `## Worker 03 Gate Recommendation`

Only recommend Worker 03 when the harness source itself can perform the full
product journey and all deterministic/dry-run gates are green.
