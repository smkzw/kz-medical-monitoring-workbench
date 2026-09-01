# Codex Review: independent_ai_roles_config

Date: 2026-07-29
Delegated-agent output: `runs/hermes_independent_ai_roles_config.md`

## Verdict

Pass after Codex revision. Four-role isolation and adapter consumption are
accepted; a real visual capability probe and v2 comprehensive-AI authority fix
were added before release acceptance.

## Boundary Check

- Changes are limited to AI provider/role settings, OCR/translation runtime
  wiring, the existing settings dialog, and focused tests.
- Frozen r11 evidence/databases/matrix and protected writing-reference surfaces
  were not modified.
- Credentials remain in the local credential store and are absent from public
  payloads and records.

## Codex Verification

- Verified four independent role bindings: comprehensive AI, OCR AI,
  translation AI, and translation-support LLM.
- Verified role-specific provider, OpenAI-compatible Base URL, model, and
  credential resolution at call time.
- Verified oMLX gate owns only OCR/translation admission and 8/8/16 concurrency,
  never the selected model.
- Verified non-specialized OCR is blocked until a real generated-PNG probe
  succeeds and that proof is invalidated by profile/model change.
- Verified v2 disabled comprehensive-AI binding fails closed.
- Focused suite: `77 passed`; broad related suite: `321 passed`.
- Python compilation and frontend production build passed.

## Delegated-Agent Output Review

The delegated change correctly separated role profiles and removed model
authority from the workload gate. Its stated residual gap, lack of a real OCR
visual probe, was a user-required capability rather than an acceptable
post-release risk; Codex implemented and tested it. The v2 active-provider
compatibility gap was independently found during adjacent contract review.

## Residual Risk

Network-backed provider acceptance is not established by mocked regression
tests. r12 must exercise the actual configured comprehensive AI,
DeepSeek translation-support route, oMLX GLM-OCR, and oMLX Hy-MT2 with the
runtime settings UI and confirm no role or credential cross-contamination.
