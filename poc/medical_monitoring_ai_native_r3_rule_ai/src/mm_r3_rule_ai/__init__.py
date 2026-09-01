"""mm_r3_rule_ai -- isolated R3 natural-language rule AI adapter slice.

Worker_01 owns the contract/parser layer (JSON Schema 2020-12 compatible
contract, immutable field catalog, strict single-object parser with typed
failure classification, and Chinese structured prompt contract).

Worker_02 owns the workflow bridge (:mod:`workflow`) -- consuming frozen R1
``CapabilityAttemptResult`` / ``AdapterRun`` public evidence, enforcing
fail-closed blocking gates, converting only fully-covered no-blocker
candidates to frozen R3 ``RuleDraft``, running local deterministic
simulation, generating the three fixed scope recommendations, and exposing
explicit user-confirmed activation.

Boundaries
----------
* Worker_01's modules (schema, catalog, parser, prompt) are stdlib-only and
  never import frozen R1/R3 at module load time.
* The :mod:`workflow` module (worker_02) imports frozen R1/R3 **public**
  contracts lazily inside functions so the stdlib-only contract is preserved
  for callers that do not need the bridge.
* No model/API/harness is called here.  No simulation records are constructed
  by the contract/parser layer.
* No project names, absolute project paths, vendor/model selectors, or
  listing-specific table/field names appear in public business logic.

Public surface
--------------
* :mod:`schema` -- the single authoritative JSON Schema 2020-12 document.
* :mod:`catalog` -- the immutable field catalog with operator/value-type
  compatibility.
* :mod:`parser` -- strict single-object parser with typed failure kinds.
* :mod:`prompt` -- Chinese structured prompt contract.
* :mod:`workflow` -- R1 → R3 bridge: conversion gates, local simulation,
  scope recommendations, explicit activation (worker_02).
"""

from __future__ import annotations

from .catalog import (
    CATALOG_OPERATORS,
    FieldCatalog,
    FieldSpec,
    ValueType,
    VALUE_TYPES,
    catalog_hash,
)
from .parser import (
    ConditionDraft,
    ParseError,
    ParseFailureKind,
    ParseResult,
    ParseStatus,
    RuleCandidateDraft,
    canonical_candidate_payload,
    candidate_content_hash,
    parse_rule_candidate,
)
from .prompt import (
    SYSTEM_PROMPT_ZH,
    PromptPayload,
    RULE_EXTRACTION_PROMPT_TEMPLATE_ZH,
    build_prompt,
    prompt_payload_hash,
)
from .schema import (
    RULE_CANDIDATE_SCHEMA,
    SCHEMA_DIALECT,
    freeze_schema,
    schema_content_hash,
    schema_json,
)

__all__ = [
    # schema
    "RULE_CANDIDATE_SCHEMA",
    "SCHEMA_DIALECT",
    "freeze_schema",
    "schema_json",
    "schema_content_hash",
    # catalog
    "CATALOG_OPERATORS",
    "FieldCatalog",
    "FieldSpec",
    "ValueType",
    "VALUE_TYPES",
    "catalog_hash",
    # parser
    "ConditionDraft",
    "ParseError",
    "ParseFailureKind",
    "ParseResult",
    "ParseStatus",
    "RuleCandidateDraft",
    "canonical_candidate_payload",
    "candidate_content_hash",
    "parse_rule_candidate",
    # prompt
    "SYSTEM_PROMPT_ZH",
    "PromptPayload",
    "RULE_EXTRACTION_PROMPT_TEMPLATE_ZH",
    "build_prompt",
    "prompt_payload_hash",
]

__version__ = "0.3.0"
