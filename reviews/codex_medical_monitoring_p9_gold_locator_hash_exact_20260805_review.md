# Codex Review: medical_monitoring_p9_gold_locator_hash_exact_20260805

Date: 2026-08-05 19:40:00 +0800
Mode: Codex direct source-only review
Delegated-agent output: none; the direct Codex route was selected.

## Verdict

Pass for the bounded canonical gold-case row-locator hash boundary. Embedded
uppercase hash bytes now fail closed before canonical locator construction;
valid lowercase locators and frozen-row authority semantics remain intact.

## Boundary Check

- Source and regression edits are confined to the gold-case authority parser,
  its focused test and task-scoped evidence.
- No frozen batch mutation, source registry write, provider/runtime/browser
  activation, API login, real-project workflow or medical-writing path was
  activated. The formal gate remains `read_only / blocked`; ports are empty.

## Codex Verification

- Focused gold-case authority suite: **39 passed**.
- Selected protocol-rules/repository-hardening/shadow-sample/gold-shadow and
  real-loop readiness/revalidation adjacency: **158 passed**.
- `python3 -m py_compile` and targeted `compileall` passed.
- The new regression proves an uppercase digest embedded in a canonical row
  locator raises the existing explicit-locator hash error rather than being
  lowercased.
- `hermes_workflow_guard.py review-gate --require-verification` is the final
  task gate; live provider/runtime/browser/clinical/visual/commercial checks
  remain intentionally unrun.

## Delegated-Agent Output Review

- No delegated output was used; Codex performed source inspection and
  verification directly.
- The existing case/source equality and locator-coordinate ambiguity checks
  were preserved; only hash-byte normalization was removed.

## Residual Risk

Live source-registry authority, source-token/CAS replay, server authorization,
provider/runtime identity, Playwright workflow, clinical/scientific accuracy,
visual usability and commercial release remain unverified. Five formal
reviewer outcomes and gate revalidation are still required before P10
real-loop activation.
