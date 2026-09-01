# Codex Review: PaddleOCR Primary / GLM Fallback

## Verdict

`CONDITIONAL_PASS`

Hermes produced the initial implementation, but Codex independently reviewed
the changed source, corrected the official transport and production wiring,
and ran the verification below. Hermes confidence was not treated as
acceptance evidence.

## Accepted

- Official multipart asynchronous Paddle Job API contract is implemented.
- Paddle request, polling, terminal failure, timeout, and nested JSONL parsing
  have deterministic coverage.
- GLM is no longer the active OCR role. It is a post-Paddle-failure fallback.
- Actual per-page model/provider/fallback provenance reaches immutable OCR
  evidence; fallback output is not mislabeled as Paddle.
- Mixed-model documents invoke one focused translation-support QC; non-pass
  outcomes are not admitted to corpus analysis.
- Standalone SAP is excluded from competitor corpus preparation and analysis.
- Existing OCR rows remain immutable and reusable.
- Four AI roles remain independently configurable; Paddle uses its actual
  non-OpenAI async transport label in the UI.

## Evidence

- Related backend test suites: 208 passed.
- Vite production build: passed, 1910 modules transformed.
- Persisted runtime OCR binding:
  `ocr_paddle_official / PaddleOCR-VL-1.6 / paddle_official`.

## Open Gate

- The encrypted credential store does not yet contain the Paddle credential.
  Live official API proof and a clean post-change runtime round therefore
  remain pending. This slice must not be called production-complete until the
  real request returns Paddle evidence and no unexpected GLM call occurs.

## Boundary

This verdict covers the Paddle-primary OCR slice and its corpus admission
boundary only. It does not approve the frozen r42 runtime or the complete
medical-writing release.
