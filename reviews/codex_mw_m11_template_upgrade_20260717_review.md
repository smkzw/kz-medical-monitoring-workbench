# Codex Review: mw_m11_template_upgrade_20260717

Date: 2026-07-17
Delegated-agent output: `runs/codex_mw_m11_template_upgrade_20260717.md`

## Verdict

Pass. The explicit legacy-template upgrade is fit for stable read-only exposure. No stable project was upgraded by Codex; execution remains a user-confirmed action.

## Boundary Check

- This task followed the workflow guard's Codex-direct route; no Hermes conference, Execution Module, or Codex SubAgent was used.
- Changes stayed within contracts, medical-writing services/endpoints, the writing frontend, focused tests, and this slice's records/QC artifacts.
- Stable SQLite files were not edited during QC: before/after SHA-256 values were equal. Temporary copied runtimes were removed after each run.

## Codex Verification

- Read the current 160-node CDE Chinese M11 template, legacy 14-section greenfield service, working-copy repository, SQLite event schema, export path, and real CRSwNP/RA runtime state before implementation.
- `python3 -m ruff check ...`: all selected changed Python files passed.
- Focused backend: 26 passed. Frontend contracts: 76 passed. Full medical-writing regression: 431 passed in 116.35s.
- `npm run build`: passed; existing single-chunk size warning remains.
- Isolated CRSwNP/RA browser/API/DOCX QC: `browser_qc/qc_report.json` passed all checks.
- Original-resolution visual review covered the 1920x1080 mapping drawer and 1440x900 upgraded/restored editor states. The checkbox/label spacing defect found in the first visual pass was fixed and rechecked.
- Stable backend was restarted on `127.0.0.1:8911`; health, SQLite integrity, foreign keys, audit chains, 18 shared-corpus items, and live CRSwNP read-only 14/14 preview all passed. Stable frontend remained HTTP 200 on `127.0.0.1:5174`.

## Delegated-Agent Output Review

No delegated-agent output exists for this Codex-direct route. The implementation is deterministic and does not rely on a model judgment for section mapping. The adjacent authoring-journey availability probe was checked because template identity changes exposed repeated requests; its dependency was narrowed without changing the authoring workflow.

## Residual Risk

- Consolidating two legacy background sections into M11 `2 引言` preserves both blocks and provenance but still requires medical restructuring after upgrade; the UI and approval reset make this explicit.
- Immediate rollback is deliberately blocked after any save under the upgraded document identity. Later historical restoration needs a separate controlled version-recovery design.
- Development StrictMode issues two expected 404 probes for legacy projects without an authoring journey; these are classified separately and do not occur because of upgrade/rollback.
- The existing production bundle remains about 1.33 MB minified and emits a Vite chunk-size warning; this slice did not introduce a speculative code-splitting refactor.
