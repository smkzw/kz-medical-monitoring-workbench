# Codex Source Acceptance: Production Prefill AI Boundary

Date: 2026-07-20
Scope:
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_journey.py`

## Routing Note

The second same-session Hermes remediation produced source edits and a complete
final report, but the runner rejected the report because no matching turn
identity was appended to `agent.log`. This is a runner identity-evidence
failure, not a source or test failure. The rejected report remains preserved
with its stdout diagnostics. Codex independently inspected and tested the
actual source before this acceptance record.

## Accepted Invariants

- AI write scope is an explicit minimal allowlist; creation minimum, protocol
  identity, version and target mechanism cannot be rewritten by AI prefill.
- One bulk call is retained; no per-field model calls were introduced.
- AI inference occurs outside the SQLite write transaction.
- English ClinicalTrials.gov condition text remains a candidate until the
  medical manager adopts it.
- Adoption atomically rebuilds the versioned search plan, replaces the
  registry condition term and clears the old snapshot binding.
- AI provenance is carried by candidate state/rationale/limitations, not by a
  fabricated evidence source.
- The condition candidate cites only the original `framing.indication` source
  text.
- English and Chinese exact-fact content is quarantined unless it cites a
  source ID explicitly supplied in the bulk request.
- A retained exact-fact candidate carries the registered source ID as its
  evidence reference.
- Trial hints require structured condition, phase and study-type relevance plus
  a public Protocol/SAP hard gate.
- Generic providers must explicitly return the exact model identity.
- Only the concrete configured `OpenAICompatibleAiProvider` may assert a
  previously verified HTTP response-model identity; a generic object cannot
  gain trust by exposing a similarly named attribute.

## Codex Verification

- Python syntax compilation passed for the AI adapter, journey service and API
  module.
- Source-owned focused regression: `87 passed`.
- With the configured runtime environment, the factory returned the concrete
  `OpenAICompatibleAiProvider` with both `model_name` and
  `expected_response_model` equal to `deepseek-v4-pro`, and base URL
  `https://api.deepseek.com/v1`; no credentials were printed.
- Chinese detection spot checks passed for dose/regimen, endpoint, sample size,
  washout, visit timing and AESI examples.
- The separately authored AI test suite remains intentionally unaccepted until
  its false evidence assertions and missing integration checks are remediated.

## Residual Boundaries

- Registered artifact IDs are currently represented with
  `source_kind="study_definition"` when an exact-fact candidate cites them.
  This is acceptable only as an internal ID pointer for the current slice; the
  future source registry should preserve the artifact's actual source kind.
- Regex detection is defense in depth. Structured exact-fact fields remain the
  primary hard boundary.
- Real RA/PNH production-model and registry tests are still required before
  product acceptance.
