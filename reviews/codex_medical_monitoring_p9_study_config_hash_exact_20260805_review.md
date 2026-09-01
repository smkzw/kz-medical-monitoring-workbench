# Codex Review: medical_monitoring_p9_study_config_hash_exact_20260805

Date: 2026-08-05 19:36:00 +0800
Mode: Codex direct source-only review
Delegated-agent output: none; the direct Codex route was selected.

## Verdict

Pass for the bounded project-neutral study-config digest boundaries. Source
binding and declared configuration hashes now require raw exact lowercase
64-hex bytes; canonical round-trip and deterministic identity remain stable.

## Boundary Check

- Source and regression edits are confined to `monitoring_study_config.py`,
  `test_monitoring_study_config.py`, and task-scoped evidence.
- No source registry resolution, adapter, provider/runtime/browser activation,
  API login, real-project workflow or medical-writing path was activated. The
  formal gate remains `read_only / blocked`; reserved ports are empty.

## Codex Verification

- Focused study-config suite: **18 passed**.
- Selected mapping-batch/protocol-preparation/real-loop readiness and
  acceptance-revalidation adjacency: **87 passed**.
- `python3 -m py_compile` and targeted `compileall` passed.
- New regressions prove padded, uppercase and non-string source-binding and
  declared config hashes fail closed; omitted/empty optional config hashes
  retain the existing omission semantics.
- `hermes_workflow_guard.py review-gate --require-verification` is the final
  task gate; provider/runtime/browser/scientific/visual/commercial checks are
  intentionally unrun under the formal gate.

## Delegated-Agent Output Review

- No delegated output was used; Codex performed the source inspection and
  verification directly.
- The change removes lowercase coercion in `_sha256` and string/whitespace
  coercion of the optional declared config digest without touching project
  capability or mapping semantics.

## Residual Risk

Live source-registry authority, source-token/CAS replay, server authorization,
independent AI provider/runtime identity, Playwright workflow,
clinical/scientific accuracy, visual usability and commercial release remain
unverified. Five formal reviewer outcomes and gate revalidation are still
required before P10 real-loop activation.
