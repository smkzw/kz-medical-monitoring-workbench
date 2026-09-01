# Task Context: medical_monitoring_my008_3_02_manifest_20260804

Created: 2026-08-04 16:22:51
Objective: Register MY008-3-02 as a canonical read-only project source manifest for future medical-monitoring LOOP without importing data or granting runtime authority.
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Canonical source registry: `services/api/app/project_source_manifest.py`.
- Project source of truth (read-only discovery only): `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-02（MM外包）`.
- Selected protocol: `方案/2.1版方案/MY008211A-PNH-3-02_研究方案_V2.1_2024.11.08-clean.docx`.
- Selected locked listing: `原始数据/【3-02初治锁库后数据集】MY008211A-PNH-3-02-锁库后EXCEL数据集.xlsx`.
- Supporting source roots: `TFL/定稿TFL` and `CSR/【CSR】MY008211A-PNH-3-02-CSR （最最终定稿-清洁版）.docx`.
- Existing project manifest and canonical-project tests are the implementation contract; the selected paths were verified by read-only `find`/`stat` checks.

## Scope

- In scope: register canonical project ID `proj_my008_pnh_3_02`, aliases, header metadata, and read-only source references; expose only dashboard and medical-monitoring bindings with an explicit source-only readiness boundary; add focused contract tests and durable evidence.
- Out of scope: importing workbook rows, parsing/normalizing subjects, creating runtime batches/risk snapshots, AI/provider calls, service/browser/Playwright execution, edits to medical-writing registries or source files, and any 8911/5174/8910/4173 startup.

## Success Criteria

- `ProjectSourceManifestService` resolves the canonical ID and `my008_pnh_3_02` alias.
- The manifest points to the verified protocol, locked listing, TFL directory, and CSR without persisting row-level data or exposing internal paths in public payloads.
- The medical-monitoring binding is explicitly `source_manifest_only`, and unsupported module bindings (especially medical writing) fail closed rather than falling through to another project.
- Focused canonical/source-manifest tests and Python syntax checks pass; the pre-existing B6/C14/real-loop gates remain blocked and all prohibited listeners remain stopped.

## Risk Boundaries

- This is a source-registry declaration, not runtime authority. No source rows, subject identifiers, runtime database records, or AI output may be created.
- Do not add the project to medical-writing/TFL/safety implementation registries in this slice; those routes remain unconfigured and fail closed.
- Do not write to the user project source tree or medical-writing source; only scoped workbench code/tests/context/evidence surfaces may change.
- Codex owns verification and acceptance; the existing B6/C14/real-loop gates are not crossed by this slice.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 16:22:51: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 16:24–16:26: Added `proj_my008_pnh_3_02` and `my008_pnh_3_02` to the canonical source manifest. The binding is limited to `dashboard` and `medical_monitoring`, with four verified read-only source paths and `source_manifest_only` status. Medical-writing/TFL registries were not changed.
- 2026-08-04 16:27: Focused contract suite passed: `23 passed` for `tests/test_project_source_manifest.py` and `tests/test_canonical_project_context.py`; `py_compile` passed for the changed service module. FastAPI route checks proved 3-02 does not fall through to medical-writing or TFL.
- 2026-08-04 16:28: Source tree and unrelated module mtimes rechecked; no user project source or medical-writing/TFL implementation file was modified. Runtime listeners and B6/C14/real-loop gates remain subject to their existing blocked state.
