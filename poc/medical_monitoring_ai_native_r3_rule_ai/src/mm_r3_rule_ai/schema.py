"""JSON Schema 2020-12 compatible contract for the structured rule-candidate
output that a model produces when converting a Chinese natural-language risk
rule into structured conditions.

Design grounding
----------------
* ``reviews/medical_monitoring_r3_nl_rule_adapter_external_discovery_20260810.md``
  §4.1: schema uses a JSON Schema 2020-12 expressible subset; a stdlib
  *isomorphic* strict parser lives in :mod:`mm_r3_rule_ai.parser`.  Both reject
  every undeclared property at every level.
* §4.2: the model output MUST be a single JSON object; the parser never strips
  Markdown fences and never salvages a substring from prose or concatenated
  objects.
* §4.3: condition ``field`` MUST hit the frozen field catalog at call time;
  allowed operators and value types are catalog-driven.  Unknown fields enter a
  blocking question; no implicit aliasing.

This module is the **single authoritative schema source**.  The parser imports
``RULE_CANDIDATE_SCHEMA`` and validates isomorphically; nothing in the package
re-declares the field set.
"""

from __future__ import annotations

import copy
import json
from typing import Any, Dict

__all__ = [
    "SCHEMA_DIALECT",
    "RULE_CANDIDATE_SCHEMA",
    "freeze_schema",
    "schema_json",
    "schema_content_hash",
]

#: The JSON Schema dialect declared on every contract document.
SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

#: The single authoritative JSON Schema 2020-12 contract for a rule candidate.
#:
#: Design rules reflected here (discovery review §4):
#: * ``additionalProperties: false`` at every object level.
#: * ``rule_name``, ``logical_combination``, ``severity_hint``, ``domain_hint``
#:   are constrained enums / non-empty strings.
#: * Each ``condition`` binds one ``field`` (string), one ``operator`` (enum
#:   identical to frozen R3 ``CONDITION_OPERATORS``), one ``threshold`` (typed
#:   per catalog at call time, not here), and a non-empty ``extracted_from``
#:   Chinese source phrase.
#: * ``assumptions`` and ``open_questions`` are arrays of non-empty strings;
#:   presence of open questions is a blocking parse status, never silent.
RULE_CANDIDATE_SCHEMA: Dict[str, Any] = {
    "$schema": SCHEMA_DIALECT,
    "$id": "https://medical-monitoring.local/r3-rule-ai/rule-candidate/v1",
    "title": "RuleCandidate",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "rule_name",
        "conditions",
        "logical_combination",
        "severity_hint",
        "domain_hint",
        "assumptions",
        "open_questions",
    ],
    "properties": {
        "rule_name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200,
            "description": "Concise Chinese or machine name for the rule.",
        },
        "conditions": {
            "type": "array",
            "minItems": 1,
            "description": "One or more structured conditions; never empty.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "field",
                    "operator",
                    "threshold",
                    "extracted_from",
                ],
                "properties": {
                    "field": {
                        "type": "string",
                        "minLength": 1,
                        "description": (
                            "Must match a field name in the frozen field "
                            "catalog supplied at call time; never invented."
                        ),
                    },
                    "operator": {
                        "type": "string",
                        # Kept in sync with frozen R3 CONDITION_OPERATORS.
                        "enum": [
                            "eq",
                            "ne",
                            "gt",
                            "ge",
                            "lt",
                            "le",
                            "contains",
                            "in",
                            "not_in",
                            "is_missing",
                            "is_present",
                        ],
                    },
                    "threshold": {
                        "description": (
                            "Scalar, string, or array depending on the "
                            "operator; validated for type/operator "
                            "compatibility by the parser against the catalog."
                        ),
                    },
                    "extracted_from": {
                        "type": "string",
                        "minLength": 1,
                        "description": (
                            "Verbatim Chinese source phrase this condition "
                            "was extracted from; required for audit."
                        ),
                    },
                },
            },
        },
        "logical_combination": {
            "type": "string",
            "enum": ["all", "any"],
            "description": "How multiple conditions combine (AND / OR).",
        },
        "severity_hint": {
            "type": "string",
            "enum": ["", "info", "warning", "serious", "critical"],
            "description": "Optional severity hint; empty string allowed.",
        },
        "domain_hint": {
            "type": "string",
            "enum": ["", "AE", "MH", "CM", "IP", "PD", "IE", "LB", "DS", "SV"],
            "description": "Optional clinical domain hint.",
        },
        "assumptions": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "description": "Assumptions the model made while structuring.",
        },
        "open_questions": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "description": (
                "Unresolved ambiguities. Non-empty blocks RuleDraft "
                "construction; the user must resolve them first."
            ),
        },
    },
}


def freeze_schema(schema: Dict[str, Any] = RULE_CANDIDATE_SCHEMA) -> Dict[str, Any]:
    """Return a deep, private copy so callers cannot mutate the authoritative
    schema object.  Intended for read-only sharing across the adapter."""
    return copy.deepcopy(schema)


def schema_json(schema: Dict[str, Any] = RULE_CANDIDATE_SCHEMA, *, indent: int = 2) -> str:
    """Deterministic JSON serialization of the schema (sorted keys)."""
    return json.dumps(schema, ensure_ascii=False, sort_keys=True, indent=indent)


def schema_content_hash() -> str:
    """Stable SHA-256 of the canonical schema serialization.

    Used by the prompt contract so a model request is bound to an exact schema
    revision; two identical schema documents always produce the same hash.
    """
    import hashlib

    return hashlib.sha256(
        schema_json(indent=0).encode("utf-8")
    ).hexdigest()
