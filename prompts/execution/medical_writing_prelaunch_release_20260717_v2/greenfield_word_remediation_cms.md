# Same-session follow-up: greenfield Word production-format gate

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`.

## Hard boundaries

- Work only inside the current workspace (`.`).
- Use disposable runtimes only. Do not touch stable ports, stable databases,
  credentials, or original company/clinical documents.
- Tools remain available and must not be disabled.
- Authorized product writes are limited to
  `services/api/app/medical_writing_document_exporter.py`, directly related
  medical-writing export/template modules, directly related tests, and
  durable evidence under
  `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_final_qc/greenfield_ra/`.
- Preserve the passing imported source-preserving export path.
- Write exactly one output file:
  `runs/execution/medical_writing_prelaunch_release_20260717_v2/greenfield_word_remediation.md`.

Read these files only for initial context:

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `context/medical_writing_prelaunch_release_20260717_v2_execution_context.md`
- `runs/execution/medical_writing_prelaunch_release_20260717_v2/worker_02.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ACCEPTANCE_CONTRACT.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/TASK_RECORD.md`

Continue the original worker_02 session. Codex owns final Word acceptance.

## Objective

Do not treat the current three-page greenfield sample as a production-format
pass. Build and verify a realistic greenfield protocol export that uses the
approved company formatting authority while preserving ICH M11 as structure
guidance only.

Use the formatting-authority paths and priority already recorded in the
execution context and task record. All source documents are read-only.

## Required investigation

Inspect the current exporter and the OOXML structures in the company examples.
When implementation uncertainty exists, search official Microsoft/Open XML
documentation or a maintained DOCX implementation before editing. Record
source URLs, applicability, and rejected alternatives.

## Required artifact and checks

Create a realistic greenfield RA protocol document from project inputs, not
from an already deconstructed protocol. It must include enough representative
content to test:

- company-style cover and version information;
- research synopsis as a distinct large table;
- multi-level numbered headings;
- table of contents, table list, and figure list fields;
- headers, footers, page fields, section breaks, margins, and page orientation;
- at least one structured ordinary table;
- a populated schedule of activities with notes;
- a study flow diagram as vector or other print-safe object;
- references with GB/T 7714-style entries and in-text superscript citation;
- body text, note style, page breaks, and at least one landscape section.

Compare OOXML styles, numbering, section properties, headers/footers, tables,
and key typography against the authority documents. Render with the repository
CJK QC script and inspect every page. A field placeholder such as
`更新域后显示目录` and a footer that renders every page as `第1页 共1页` are
not production acceptance.

Preserve the already passing RUX/D001 source-preserving tests. Run focused
tests plus those source-preserving regressions.

Write an exact checklist with PASS/FAIL/UNVERIFIED. Do not claim Microsoft Word
GUI opening; Codex performs that final gate.

Use the required execution-report headings.
