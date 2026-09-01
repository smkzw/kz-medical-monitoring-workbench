# Task Context: medical_monitoring_my008_3_01_manifest_20260804

Created: 2026-08-04 18:57:45
Objective: Register MY008-3-01 medical-monitoring source manifest as source_manifest_only without activation or medical-writing changes, aligning the five-project source boundary.
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/project_source_manifest.py` — canonical MY008-3-01 source manifest builder.
- User-authorized MY008-3-01 source root: `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-01（MM外包）`.
- Existing read-only structure intake evidence:
  `records/active_slices/medical_monitoring_five_project_structure_intake_20260804/`.
- Focused manifest and canonical-context tests.
- B6/C14/real-loop gates remain authoritative and closed.

## Scope

- In scope: register the exact MY008-3-01 locked listing and protocol as a
  `source_manifest_only` medical-monitoring binding, with TFL/CSR supplemental
  sources; keep the existing medical-writing/TFL bindings unchanged.
- Out of scope: adapter registration, source parsing, mapping, source promotion,
  runtime/provider/browser/Playwright, database writes, B6/C14, real-loop or
  commercial-release changes.

## Success Criteria

- Public manifest exposes `medical_monitoring` with the exact primary and
  supplemental source IDs and `implementation_status=source_manifest_only`.
- The locked listing and protocol source refs are available and public payload
  remains sanitized; no candidate alias is silently promoted.
- Existing canonical context and medical-writing/TFL tests remain green.

## Risk Boundaries

- Only the source manifest, focused tests, and this task's evidence may change.
- Do not activate a monitoring adapter, change the runtime registry, or alter
  medical-writing/TFL source/runtime behavior.
- Do not start listeners, API/provider/browser/Playwright, real projects or
  external testers; do not cross B6/C14/real-loop authority.
- Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 18:57:45: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 18:58–19:00: Added the exact 3-01 locked listing source ref, bound
  the existing V1.1 protocol plus TFL/CSR sources to a source-only monitoring
  module, and retained all existing writing/TFL bindings. No adapter or runtime
  registry changed.
- 2026-08-04 19:00–19:02: Manifest/canonical-context regression passed (24
  tests, existing deprecation warnings only); source availability and payload
  sanitization assertions passed. No services or external routes ran.
