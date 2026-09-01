#!/usr/bin/env python3
"""Verify typed D06 fixtures and generate the frozen challenge registry."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md"
CATALOG = ROOT / "reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json"
OUTPUT = ROOT / "reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json"
OUTCOME_ORACLE = ROOT / "reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json"
FROZEN_AT = "2026-08-12T00:00:00+08:00"
CANONICAL_CATALOG_ID = "medical-monitoring-r4-d06-typed-fixtures"
CANONICAL_CATALOG_VERSION = "8.0.3"
CANONICAL_CATALOG_HASH = "44287f1277790ad0bbbd21045565c50049a67d5451c6eefcb30e68f12d64b774"
CANONICAL_CONTRACT_SEMANTIC_HASH = "247eb0bc4a4c97428714f069639161ac832bed05cfcb7dfc4c01240a7ef84642"
CANONICAL_CONTRACT_FILE_SHA256 = "460aba75857f72527453914b5ea5c205ecf8d5032ec5b83b22c6960ccbc8baeb"
CANONICAL_CONTRACT_PREFIX = (
    "# R4-D06 疗效终点、量表与个体趋势纵切合同 v1.18\n\n"
    "Date: 2026-08-12  \n"
    "Status: `FROZEN_R4_D06_CONTRACT_V1_18`  \n"
    "Scope: 仅限合成/离线 R4 纵切及据此开展 R4 POC 有界实现纠偏；不代表实现、R4 总体、R5 UI、真实项目、统计分析、产品或生产接受。\n\n"
)

CANONICAL_SYNTHETIC_SCOPE = {
    "accepted_snapshot_ref": "SYN-SNAPSHOT-001",
    "clinical_event_cutoff": "2026-01-31T23:59:59+08:00",
    "episode_key": "EPISODE-001",
    "monitoring_mode": "full",
    "project_ref": "SYN-D06-PROJECT",
    "run_ref": "SYN-D06-RUN-001",
    "scope_binding_id": "SYN-D06-SCOPE-001",
    "site_ref": "SYN-D06-SITE-001",
    "snapshot_as_of": "2026-01-31T23:59:59+08:00",
    "source_revision": "SYN-REV-001",
    "subject_ref": "SYN-D06-SUBJECT-001",
}

OUTCOME_ORACLE_HASH = "16b8b9648670adcae14fa16b1fe03c2570a2449e3835671bab00345f6fe9244a"
AUDIENCE_VALIDATOR_VERSION = "d06-audience-validator-v1"
AUDIENCE_VALIDATOR_DEFINITION = {
    "payload_schemas": {
        "journey": ["display_text", "endpoint_lanes", "payload_kind", "payload_schema_version", "visit_axis_label"],
        "query": ["action_sentence", "basis_sentence", "finding_sentence", "payload_kind", "payload_schema_version", "query_context"],
        "risk_label": ["finding_summary", "jump_target", "payload_kind", "payload_schema_version", "priority_label", "risk_category"],
    },
    "validator_version": AUDIENCE_VALIDATOR_VERSION,
}
CANONICAL_AUDIENCE_CHECKS = [
    "payload_schema", "payload_schema_version", "validator_version", "validator_hash",
    "lexicon_version", "forbidden_lexicon_hash", "forbidden_fragment_hits",
    "validated_display_string_paths", "validation_state", "audience_payload_absent",
]

SUBTYPE_TO_UNIT_KIND = {
    "required_component_missing": "item_completeness",
    "component_value_invalid": "item_value_validity",
    "score_inconsistent": "score_recalculation",
    "baseline_inconsistent": "baseline_selection",
    "change_value_inconsistent": "change_recalculation",
    "response_class_inconsistent": "response_classification",
    "endpoint_composition_inconsistent": "endpoint_composition",
    "rater_or_mode_inconsistent": "rater_or_mode_consistency",
    "individual_trend_inconsistent": "individual_trend_pattern",
    "reported_result_inconsistent": "accepted_report_consistency",
}

PRIORITY_REASON_BY_STEP = {
    1: ["rights_or_critical_treatment"],
    2: ["priority_input_unresolved"],
    3: ["primary_or_mandatory_critical"],
    4: ["key_secondary_or_other_required"],
    5: ["administrative_precedence"],
}

AUDIENCE_PHRASES = [
    "positive", "negative", "boundary", "not_applicable", "not_evaluable",
    "candidate", "formal fact", "model confidence", "backend", "debug", "log",
    "classifier", "payload", "lineage", "hash", "QC", "正式事实", "候选信号",
    "只读投影", "规则命中", "后端", "模型置信度", "算法异常", "模型判断",
]
AUDIENCE_DISPLAY_KEYS = [
    "id", "*_id", "hash", "*_hash", "ref", "*_ref", "classifier", "payload",
    "lineage", "backend", "debug", "log", "confidence",
]
AUDIENCE_LEXICON_HASH = "d73a3da6fb9e5643c17673273bff042af5df75259979dcc59cb8adff917e5a75"


def canonical_priority_policy() -> dict[str, Any]:
    policy = {
        "object_type": "D06PriorityPolicy",
        "policy_id": "D06-PRIORITY-V1",
        "version": "1.0",
        "ordered_precedence_rules": [
            {"step":1,"impact_classes":["rights_safety","critical_treatment"],"monitoring_priority":"high","machine_close_forbidden":True,"reason_codes":["rights_or_critical_treatment"]},
            {"step":2,"trigger_any":["impact_unresolved","recoverability_unknown","actionability_context_only_or_unknown"],"monitoring_priority":"unknown","machine_close_forbidden":False,"reason_codes":["priority_input_unresolved"]},
            {"step":3,"impact_classes":["primary_endpoint","mandatory_critical_sample"],"high_if_recoverability":["time_critical","irrecoverable"],"otherwise_priority":"medium","high_machine_close_forbidden":True,"reason_codes":["primary_or_mandatory_critical"]},
            {"step":4,"impact_classes":["key_secondary_endpoint","other_required"],"high_if_recurrence":["repeated_site"],"high_if_recoverability":["irrecoverable"],"otherwise_priority":"medium","high_machine_close_forbidden":True,"reason_codes":["key_secondary_or_other_required"]},
            {"step":5,"impact_classes":["administrative"],"high_if_recurrence":["repeated_site"],"high_if_recoverability":["irrecoverable","time_critical"],"medium_if_recurrence":["repeated_subject"],"otherwise_priority":"low","high_machine_close_forbidden":True,"reason_codes":["administrative_precedence"]},
        ],
        "source_locator_ids": ["SYN-LOC-D06-PRIORITY-POLICY-001"],
    }
    policy["policy_hash"] = f"sha256:{sha256_text(canonical_json(policy))}"
    return policy


def audience_phrase_hits(strings: list[str]) -> list[str]:
    normalized = [
        " ".join(unicodedata.normalize("NFKC", value).casefold().split())
        for value in strings
    ]
    hits: list[str] = []
    for phrase in AUDIENCE_PHRASES:
        normalized_phrase = " ".join(unicodedata.normalize("NFKC", phrase).casefold().split())
        if normalized_phrase.isascii():
            needle = normalized_phrase.split()
            matched = False
            for text in normalized:
                tokens = re.sub(r"[^a-z0-9_]+", " ", text).split()
                if any(tokens[index:index + len(needle)] == needle for index in range(max(0, len(tokens) - len(needle) + 1))):
                    matched = True
                    break
        else:
            matched = any(normalized_phrase in text for text in normalized)
        if matched:
            hits.append(phrase.casefold())
    return hits


def audience_visible_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(audience_visible_strings(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(audience_visible_strings(item))
        return result
    return []


def audience_string_paths(value: Any, prefix: tuple[str, ...] = ()) -> list[str]:
    if isinstance(value, str):
        return [".".join(prefix)]
    if isinstance(value, list):
        result: list[str] = []
        for index, item in enumerate(value):
            result.extend(audience_string_paths(item, prefix + (str(index),)))
        return result
    if isinstance(value, dict):
        result = []
        for key, item in value.items():
            result.extend(audience_string_paths(item, prefix + (str(key),)))
        return result
    return []


def audience_display_view(payload: dict[str, Any]) -> dict[str, Any]:
    kind = payload.get("payload_kind")
    if kind == "journey":
        return {
            "display_text": payload.get("display_text"),
            "endpoint_lanes": payload.get("endpoint_lanes"),
            "visit_axis_label": payload.get("visit_axis_label"),
        }
    if kind == "query":
        return {
            "action_sentence": payload.get("action_sentence"),
            "basis_sentence": payload.get("basis_sentence"),
            "finding_sentence": payload.get("finding_sentence"),
        }
    if kind == "risk_label":
        return {
            "finding_summary": payload.get("finding_summary"),
            "jump_target": payload.get("jump_target"),
            "priority_label": payload.get("priority_label"),
            "risk_category": payload.get("risk_category"),
        }
    return payload


def attempted_display_view(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = unicodedata.normalize("NFKC", str(key)).casefold()
            if any(token in normalized_key for token in ("text", "label", "sentence")):
                result[str(key)] = item
            elif isinstance(item, (dict, list)):
                nested = attempted_display_view(item)
                if nested not in ({}, []):
                    result[str(key)] = nested
        return result
    if isinstance(value, list):
        result = [attempted_display_view(item) for item in value]
        return [item for item in result if item not in ({}, [])]
    return {}


def has_chinese(value: str) -> bool:
    return bool(re.search(r"[\u3400-\u9fff]", value))


def validate_audience_payload_schema(payload: dict[str, Any]) -> str:
    kind = payload.get("payload_kind")
    required = AUDIENCE_VALIDATOR_DEFINITION["payload_schemas"].get(kind)
    if required is None or sorted(payload) != required:
        raise SystemExit("audience payload schema/unknown fields mismatch")
    expected_version = f"d06-{kind}-audience-v1"
    if payload.get("payload_schema_version") != expected_version:
        raise SystemExit("audience payload schema version mismatch")
    if kind == "journey":
        if not has_chinese(payload.get("display_text", "")) or not has_chinese(payload.get("visit_axis_label", "")):
            raise SystemExit("journey audience text must be nonempty Chinese")
        lanes = payload.get("endpoint_lanes")
        if not isinstance(lanes, list) or not lanes:
            raise SystemExit("journey audience payload needs endpoint lane")
        required_lane = ["endpoint_label", "marker_label", "source_jump_target"]
        for lane in lanes:
            if not isinstance(lane, dict) or sorted(lane) != required_lane or any(
                not isinstance(lane[field], str) or not lane[field].strip() or not has_chinese(lane[field])
                for field in required_lane
            ):
                raise SystemExit("journey audience lane schema/content mismatch")
    elif kind == "query":
        if payload.get("query_context") not in {
            "enrollment_not_occurred", "enrolled_or_post_enrollment", "enrollment_state_unresolved"
        }:
            raise SystemExit("query audience context mismatch")
        for field, prefix in (
            ("basis_sentence", "依据："), ("finding_sentence", "发现："),
            ("action_sentence", "行动项："),
        ):
            value = payload.get(field)
            if not isinstance(value, str) or not value.startswith(prefix) or not has_chinese(value):
                raise SystemExit("query audience three-sentence schema/content mismatch")
    else:
        for field in ("finding_summary", "jump_target", "priority_label", "risk_category"):
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip() or not has_chinese(value):
                raise SystemExit("risk-label audience schema/content mismatch")
    return expected_version


def forbidden_audience_keys(value: Any) -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = unicodedata.normalize("NFKC", str(key)).casefold()
            if (
                normalized_key in {"id", "hash", "ref", "classifier", "payload", "lineage", "backend", "debug", "log", "confidence"}
                or normalized_key.endswith("_id") or normalized_key.endswith("_hash") or normalized_key.endswith("_ref")
            ):
                hits.append(str(key))
            hits.extend(forbidden_audience_keys(item))
    elif isinstance(value, list):
        for item in value:
            hits.extend(forbidden_audience_keys(item))
    return hits


def normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {
            unicodedata.normalize("NFC", str(key)): normalize_value(item)
            for key, item in value.items()
        }
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        normalize_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def semantic_hash(text: str) -> str:
    normalized = unicodedata.normalize(
        "NFC", text.replace("\r\n", "\n").replace("\r", "\n")
    )
    start = normalized.index("## 1.")
    end = normalized.index("\n## 15.")
    return sha256_text(normalized[start:end])


def validate_contract_preamble(text: str) -> None:
    normalized = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    marker = "## 1."
    if marker not in normalized or normalized[:normalized.index(marker)] != CANONICAL_CONTRACT_PREFIX:
        raise SystemExit("complete contract preamble prefix does not match canonical review snapshot")


def matrix_numbers(text: str) -> list[int]:
    numbers: list[int] = []
    in_matrix = False
    for line in text.splitlines():
        if line.startswith("## 13."):
            in_matrix = True
            continue
        if in_matrix and line.startswith("## 14."):
            break
        match = re.match(r"^\|\s*(\d+)\s*\|", line)
        if match:
            numbers.append(int(match.group(1)))
    return numbers


def resolve_priority(decision: dict[str, Any]) -> tuple[str, int, bool]:
    impact = decision.get("impact_class")
    recurrence = decision["recurrence_class"]
    recoverability = decision["recoverability"]
    actionability = decision["actionability"]
    if impact in {"rights_safety", "critical_treatment"}:
        return "high", 1, True
    if decision.get("impact_resolution_state") == "unresolved" or recoverability == "unknown" or actionability in {"context_only", "unknown"}:
        return "unknown", 2, False
    if impact in {"primary_endpoint", "mandatory_critical_sample"}:
        priority = "high" if recoverability in {"time_critical", "irrecoverable"} else "medium"
        return priority, 3, priority == "high"
    if impact in {"key_secondary_endpoint", "other_required"}:
        priority = "high" if recurrence == "repeated_site" or recoverability == "irrecoverable" else "medium"
        return priority, 4, priority == "high"
    if impact == "administrative":
        if recurrence == "repeated_site" or recoverability in {"irrecoverable", "time_critical"}:
            priority = "high"
        elif recurrence == "repeated_subject":
            priority = "medium"
        else:
            priority = "low"
        return priority, 5, priority == "high"
    raise SystemExit(f"unsupported resolved priority impact: {impact}")


def verify_embedded_hash(obj: dict[str, Any], label: str) -> None:
    supplied = obj.get("hash")
    core = {key: value for key, value in obj.items() if key != "hash"}
    expected = f"sha256:{sha256_text(canonical_json(core))}"
    if supplied != expected:
        raise SystemExit(f"{label} hash mismatch")


def verify_lineage_hash(obj: dict[str, Any], label: str) -> None:
    supplied = obj.get("lineage_hash")
    core = {key: value for key, value in obj.items() if key != "lineage_hash"}
    expected = f"sha256:{sha256_text(canonical_json(core))}"
    if supplied != expected:
        raise SystemExit(f"{label} lineage hash mismatch")


def load_outcome_oracle() -> tuple[dict[int, dict[str, Any]], str]:
    oracle = json.loads(OUTCOME_ORACLE.read_text(encoding="utf-8"))
    supplied_hash = oracle.get("oracle_hash")
    core = {key: value for key, value in oracle.items() if key != "oracle_hash"}
    calculated_hash = sha256_text(canonical_json(core))
    if supplied_hash != calculated_hash or calculated_hash != OUTCOME_ORACLE_HASH:
        raise SystemExit("independent expected-outcome oracle hash mismatch")
    cases = oracle.get("cases")
    if (
        oracle.get("oracle_id") != "medical-monitoring-r4-d06-expected-outcome-oracle"
        or oracle.get("version") != "1.0.0"
        or oracle.get("case_count") != 219
        or not isinstance(cases, list)
        or [item.get("challenge_number") for item in cases] != list(range(1, 220))
    ):
        raise SystemExit("independent expected-outcome oracle identity/count/order mismatch")
    return {item["challenge_number"]: item for item in cases}, calculated_hash


def substantive_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(canonical_json(fixture))
    result.pop("challenge_number", None)
    return result


def non_case_bound_outcome(outcome: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(canonical_json(outcome))
    assertions = result.get("domain_assertions", {})
    assertions.pop("challenge_assertion_code", None)
    assertions.pop("evaluated_fixture_hash", None)
    result.get("object_hashes", {}).pop("fixture_hash", None)
    return result


def resolve_definition_boundary_clinical_contract(case: dict[str, Any]) -> str:
    fixture = case["fixture"]
    typed_parameters = fixture["case_inputs"]["typed_parameters"]
    if case["entrypoint_id"] != "d06.gate_evaluator" or typed_parameters != {
        "applicable_instrument_ids": ["INST-001", "INST-002"]
    }:
        raise SystemExit("duplicate fixture lacks authoritative definition-boundary semantics")
    instrument = fixture["definitions"].get("instrument", {})
    endpoint = fixture["definitions"].get("endpoint", {})
    expected_instrument = {
        "id": "INST-001",
        "stable_key": "SYN-SCALE",
        "version": "1.0",
        "object_type": "instrument_definition",
        "content_hash": "sha256:6e1a6df3fe5dff77146c971b6e8044c026c12f66c67723213aee4fa8b80a482b",
    }
    expected_endpoint = {
        "id": "EP-001",
        "stable_key": "SYN-ENDPOINT",
        "version": "1.0",
        "object_type": "endpoint_definition",
        "content_hash": "sha256:ce8cc03a00c98dafa6ec0cb196a8314f0f53591f1a2f8dcaea4e74c4e6bb0eb9",
    }
    exact_definition_fields = (
        {
            "admin_mode", "content_hash", "definition_scope", "id",
            "object_type", "recall_period", "reporter_type",
            "source_locator_ids", "stable_key", "version",
        },
        {
            "content_hash", "definition_scope", "directionality", "id",
            "object_type", "role", "source_locator_ids", "stable_key",
            "version",
        },
    )
    exact_definition_scope_fields = {
        "project_ref", "run_ref", "monitoring_mode", "subject_ref",
        "site_ref", "episode_key", "source_revision",
        "accepted_snapshot_ref", "scope_binding_id", "cutoff",
    }
    for definition, expected, exact_fields in (
        (instrument, expected_instrument, exact_definition_fields[0]),
        (endpoint, expected_endpoint, exact_definition_fields[1]),
    ):
        if set(definition) != exact_fields:
            raise SystemExit("definition-boundary semantic source schema mismatch")
        if any(definition.get(key) != value for key, value in expected.items()):
            raise SystemExit("definition-boundary semantic source identity mismatch")
        if not definition.get("source_locator_ids"):
            raise SystemExit("definition-boundary semantic source lacks locator")
        definition_scope = definition.get("definition_scope")
        if (
            not isinstance(definition_scope, dict)
            or set(definition_scope) != exact_definition_scope_fields
        ):
            raise SystemExit("definition-boundary semantic source scope schema mismatch")
        for field in (
            "project_ref", "run_ref", "monitoring_mode", "subject_ref",
            "site_ref", "episode_key", "source_revision",
            "accepted_snapshot_ref", "scope_binding_id",
        ):
            if definition_scope.get(field) != fixture["scope"].get(field):
                raise SystemExit("definition-boundary semantic source scope mismatch")
        if definition_scope.get("cutoff") != fixture["scope"].get("clinical_event_cutoff"):
            raise SystemExit("definition-boundary semantic source cutoff mismatch")
        content_core = {
            key: value for key, value in definition.items()
            if key != "content_hash"
        }
        expected_content_hash = f"sha256:{sha256_text(canonical_json(content_core))}"
        if definition.get("content_hash") != expected_content_hash:
            raise SystemExit("definition-boundary semantic source content hash mismatch")
    return "definition boundary gate"


def validate_catalog(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    outcome_oracle, _ = load_outcome_oracle()
    if set(catalog) != {"catalog_id", "version", "case_count", "catalog_hash", "cases"}:
        raise SystemExit("typed fixture catalog fields are not exact and complete")
    if (
        catalog.get("catalog_id") != CANONICAL_CATALOG_ID
        or catalog.get("version") != CANONICAL_CATALOG_VERSION
    ):
        raise SystemExit("typed fixture catalog identity/version is not canonical")
    cases = catalog.get("cases")
    if catalog.get("case_count") != 219 or not isinstance(cases, list) or len(cases) != 219:
        raise SystemExit("typed fixture catalog must contain exactly 219 cases")
    expected_case_fields = {
        "assertion_dsl", "assertion_dsl_version", "challenge_number",
        "entrypoint_id", "expected_outcome", "fixture", "fixture_id",
        "required_audience_checks", "required_hash_relations",
        "required_outcome_fields", "required_trace_edge_types", "test_id",
    }
    if any(set(case) != expected_case_fields for case in cases):
        raise SystemExit("typed fixture case fields are not exact and complete")
    supplied_hash = catalog.get("catalog_hash")
    core = {key: value for key, value in catalog.items() if key != "catalog_hash"}
    calculated_hash = sha256_text(canonical_json(core))
    if supplied_hash != calculated_hash or calculated_hash != CANONICAL_CATALOG_HASH:
        raise SystemExit("typed fixture catalog hash mismatch")
    numbers = [case.get("challenge_number") for case in cases]
    if numbers != list(range(1, 220)):
        raise SystemExit("typed fixture cases must be ordered and contiguous 1..219")
    fixture_ids = [case.get("fixture_id") for case in cases]
    test_ids = [case.get("test_id") for case in cases]
    if len(set(fixture_ids)) != 219 or len(set(test_ids)) != 219:
        raise SystemExit("fixture and test IDs must be unique")
    for case in cases:
        fixture = case.get("fixture")
        outcome = case.get("expected_outcome")
        if not isinstance(fixture, dict) or not isinstance(outcome, dict):
            raise SystemExit("every case requires typed fixture and expected outcome objects")
        if fixture.get("fixture_schema_version") != "d06-typed-fixture-v2":
            raise SystemExit("unknown fixture schema")
        if fixture.get("challenge_number") != case["challenge_number"]:
            raise SystemExit("fixture challenge number mismatch")
        for required in ("scope", "definitions", "records", "bindings", "policies", "case_inputs"):
            if required not in fixture:
                raise SystemExit(f"fixture missing required object: {required}")
        if not case.get("entrypoint_id") or not case.get("required_trace_edge_types"):
            raise SystemExit("case missing entrypoint or trace contract")
        scope = fixture["scope"]
        if scope != CANONICAL_SYNTHETIC_SCOPE:
            raise SystemExit("fixture scope does not match immutable canonical synthetic D06 scope")
        scope_fields = (
            "project_ref", "run_ref", "monitoring_mode", "subject_ref", "site_ref",
            "episode_key", "source_revision", "accepted_snapshot_ref", "scope_binding_id",
        )
        for field in scope_fields:
            if not scope.get(field):
                raise SystemExit(f"fixture scope missing {field}")
        if not scope.get("clinical_event_cutoff"):
            raise SystemExit("fixture scope missing clinical_event_cutoff")
        case_inputs = fixture["case_inputs"]
        if case_inputs.get("case_input_schema") != "d06-case-input-v4":
            raise SystemExit("unknown case input schema")
        typed_parameters = case_inputs.get("typed_parameters")
        if not isinstance(typed_parameters, dict):
            raise SystemExit("typed case parameters must be an object")
        def reject_dotted_keys(value: Any) -> None:
            if not isinstance(value, dict):
                return
            for key, item in value.items():
                if "." in str(key):
                    raise SystemExit("typed case parameters contain dotted shorthand")
                reject_dotted_keys(item)
        reject_dotted_keys(typed_parameters)
        for definition in fixture["definitions"].values():
            if isinstance(definition, dict) and (
                not definition.get("object_type") or
                not definition.get("definition_scope") or
                not definition.get("source_locator_ids") or
                not definition.get("content_hash")
            ):
                raise SystemExit("definition is not a full typed object")
        for result_name in ("accepted_result", "recalculated_result"):
            result = fixture["records"].get(result_name)
            if isinstance(result, dict):
                for field in scope_fields:
                    if result.get(field) != scope.get(field):
                        raise SystemExit(f"{result_name} wrong scope: {field}")
                if result.get("cutoff") != scope.get("clinical_event_cutoff"):
                    raise SystemExit(f"{result_name} wrong scope: cutoff")
                if not result.get("source_locator_ids") or not result.get("lineage_hash"):
                    raise SystemExit(f"{result_name} missing trace")
                verify_lineage_hash(result, result_name)
        for binding_name in (
            "d07_value_ref", "d07_consumption_binding", "d08_relationship_ref",
            "tte_precedence_binding",
        ):
            binding = fixture["bindings"].get(binding_name)
            if not isinstance(binding, dict) or not binding.get("object_type"):
                raise SystemExit(f"{binding_name} must be a full typed object")
            for field in scope_fields:
                if binding.get(field) != scope.get(field):
                    raise SystemExit(f"{binding_name} wrong scope: {field}")
            if binding.get("cutoff") != scope.get("clinical_event_cutoff"):
                raise SystemExit(f"{binding_name} wrong scope: cutoff")
        d05_refs = fixture["bindings"].get("d05_refs", [])
        if not all(isinstance(item, dict) and item.get("object_type") == "D05AssessmentBindingRef" for item in d05_refs):
            raise SystemExit("D05 refs must be full typed objects")
        required_d05_fields = (
            "binding_ref_id", "d05_unit_id", "d05_planned_activity_key",
            "d05_actual_activity_key", "occurrence_disposition", "timing_disposition",
            "assignment_status", "actual_time_ref", "producer_payload_hash",
            "source_record_id", "source_locator_ids", "hash",
        )
        for ref in d05_refs:
            if any(ref.get(field) in (None, "", []) for field in required_d05_fields):
                raise SystemExit("D05 ref is missing occurrence/timing/assignment trace")
            for field in scope_fields:
                if ref.get(field) != scope.get(field):
                    raise SystemExit(f"D05 ref wrong scope: {field}")
            if ref.get("cutoff") != scope.get("clinical_event_cutoff"):
                raise SystemExit("D05 ref wrong scope: cutoff")
            verify_embedded_hash(ref, "D05 ref")
        registries = fixture.get("source_registries", {})
        d05_foreign_keys = registries.get("d05_assessment_foreign_keys", [])
        expected_ref_ids = [item.get("binding_ref_id") for item in d05_refs]
        if registries.get("required_d05_binding_ref_ids") != expected_ref_ids:
            raise SystemExit("D05 required binding set mismatch")
        if [item.get("binding_ref_id") for item in d05_foreign_keys] != expected_ref_ids:
            raise SystemExit("D05 foreign-key registry set mismatch")
        assessments = {item.get("id"): item for item in fixture["records"].get("assessments", [])}
        if list(assessments) != ["ASM-BASE-D7", "ASM-BASE-D1", "ASM-W4-A", "ASM-W4-B"]:
            raise SystemExit("accepted D05 assessment inventory identity set is not canonical")
        for assessment in assessments.values():
            if assessment.get("object_type") != "ActualAssessmentRecord" or not assessment.get("id") or not assessment.get("time") or not assessment.get("lineage_hash") or not assessment.get("source_locator_ids"):
                raise SystemExit("D05 source assessment is incomplete")
            for field in scope_fields:
                if assessment.get(field) != scope.get(field):
                    raise SystemExit(f"D05 source assessment wrong scope: {field}")
            suffix = assessment["id"].removeprefix("ASM-")
            if (
                assessment.get("cutoff") != scope.get("clinical_event_cutoff")
                or assessment.get("assessment_id") != assessment.get("id")
                or assessment.get("stable_assessment_key") != f"ASSESSMENT-{suffix}"
                or assessment.get("instrument_definition_id") != fixture["definitions"]["instrument"].get("id")
                or assessment.get("assessment_time_ref") != assessment.get("time")
                or assessment.get("record_status") != "accepted_current"
                or assessment.get("correction_status") != "original"
                or assessment.get("prior_assessment_id") is not None
                or assessment.get("supersedes_assessment_id") is not None
                or assessment.get("scope_decision_id") != f"SCOPE-DEC-{suffix}"
                or not assessment.get("item_record_ids")
            ):
                raise SystemExit("D05 source assessment status/correction identity mismatch")
            verify_lineage_hash(assessment, "D05 source assessment")
        assessment_items = fixture["records"].get("assessment_items")
        if not isinstance(assessment_items, list) or len(assessment_items) != 24:
            raise SystemExit("typed assessment item collection must contain exactly 24 records")
        items_by_id: dict[str, dict[str, Any]] = {}
        items_by_assessment: dict[str, list[dict[str, Any]]] = {key: [] for key in assessments}
        for item in assessment_items:
            if item.get("object_type") != "AssessmentItemRecord" or not item.get("item_record_id"):
                raise SystemExit("assessment item record type/identity mismatch")
            if item["item_record_id"] in items_by_id:
                raise SystemExit("assessment item identity is not unique")
            assessment_id = item.get("assessment_id")
            if assessment_id not in assessments:
                raise SystemExit("assessment item does not resolve parent assessment")
            if (
                item.get("stable_item_record_key") != f"ITEMREC-{item['item_record_id'].removeprefix('ITEM-')}"
                or item.get("item_definition_id") not in {f"ITEM-DEF-I{index}" for index in range(1, 7)}
                or item.get("record_status") != "accepted_current"
                or item.get("correction_status") != "original"
                or item.get("prior_item_record_id") is not None
                or item.get("supersedes_item_record_id") is not None
                or not item.get("source_locator_ids")
                or not item.get("content_hash")
            ):
                raise SystemExit("assessment item status/correction/source identity mismatch")
            content_core = {key: value for key, value in item.items() if key != "content_hash"}
            if item["content_hash"] != f"sha256:{sha256_text(canonical_json(content_core))}":
                raise SystemExit("assessment item content hash mismatch")
            items_by_id[item["item_record_id"]] = item
            items_by_assessment[assessment_id].append(item)
        for assessment_id, assessment in assessments.items():
            expected_item_ids = [f"ITEM-{assessment_id.removeprefix('ASM-')}-I{index}" for index in range(1, 7)]
            if assessment.get("item_record_ids") != expected_item_ids:
                raise SystemExit("assessment item membership/order is not canonical")
            resolved = items_by_assessment[assessment_id]
            if [item["item_record_id"] for item in resolved] != expected_item_ids:
                raise SystemExit("assessment item collection does not preserve parent membership/order")
            if any(item["assessment_id"] != assessment_id for item in resolved):
                raise SystemExit("assessment item parent binding mismatch")
        current_items = items_by_assessment["ASM-W4-A"]
        expected_current_values = fixture["records"].get("item_values")
        if {
            item["item_definition_id"].removeprefix("ITEM-DEF-"): item["normalized_value"]
            for item in current_items
        } != expected_current_values:
            raise SystemExit("current assessment item values do not resolve evaluator item inputs")
        accepted_d05_inventory = registries.get("accepted_d05_assessment_inventory", [])
        if [item.get("source_record_id") for item in accepted_d05_inventory] != list(assessments):
            raise SystemExit("accepted D05 inventory does not exactly cover assessment records")
        accepted_d05_by_id = {}
        for item in accepted_d05_inventory:
            if item.get("object_type") != "AcceptedD05AssessmentInventoryItem":
                raise SystemExit("accepted D05 inventory object type mismatch")
            verify_embedded_hash(item, "accepted D05 inventory")
            source = assessments[item["source_record_id"]]
            suffix = source["id"].removeprefix("ASM-")
            canonical_fields = {
                "d05_unit_id": f"D05-UNIT-{suffix}",
                "d05_planned_activity_key": f"PLAN-{suffix}",
                "d05_actual_activity_key": f"ACTUAL-{suffix}",
                "occurrence_disposition": "negative",
                "timing_disposition": "negative",
                "assignment_status": "unique",
                "actual_time_ref": source["time"],
                "producer_payload_hash": source["lineage_hash"],
            }
            source_semantics = {
                "d05_unit_id": source.get("d05_unit_id"),
                "d05_planned_activity_key": source.get("d05_planned_activity_key"),
                "d05_actual_activity_key": source.get("d05_actual_activity_key"),
                "occurrence_disposition": source.get("occurrence_disposition"),
                "timing_disposition": source.get("timing_disposition"),
                "assignment_status": source.get("assignment_status"),
                "actual_time_ref": source.get("time"),
                "producer_payload_hash": source.get("lineage_hash"),
            }
            if source_semantics != canonical_fields or any(item.get(field) != value for field, value in canonical_fields.items()):
                raise SystemExit("accepted D05 inventory identity/activity semantics mismatch")
            accepted_d05_by_id[item["source_record_id"]] = item
        for ref, foreign_key in zip(d05_refs, d05_foreign_keys):
            if foreign_key.get("object_type") != "D05AssessmentForeignKey":
                raise SystemExit("D05 foreign-key registry object type mismatch")
            verify_embedded_hash(foreign_key, "D05 foreign key")
            for field in (
                "binding_ref_id", "d05_unit_id", "d05_planned_activity_key",
                "d05_actual_activity_key", "occurrence_disposition", "timing_disposition",
                "assignment_status", "actual_time_ref", "producer_payload_hash", "source_record_id",
            ):
                if ref.get(field) != foreign_key.get(field):
                    raise SystemExit(f"D05 foreign-key mismatch: {field}")
            if ref.get("occurrence_disposition") != "negative" or ref.get("timing_disposition") not in {"negative", "positive"} or ref.get("assignment_status") != "unique":
                raise SystemExit("D05 closed disposition/assignment vocabulary mismatch")
            source = assessments.get(ref.get("source_record_id"))
            if not source or source.get("time") != ref.get("actual_time_ref") or source.get("lineage_hash") != ref.get("producer_payload_hash"):
                raise SystemExit("D05 source record cannot resolve binding")
            inventory_item = accepted_d05_by_id.get(ref.get("source_record_id"))
            if not inventory_item or any(
                ref.get(field) != inventory_item.get(field)
                for field in (
                    "d05_unit_id", "d05_planned_activity_key", "d05_actual_activity_key",
                    "occurrence_disposition", "timing_disposition", "assignment_status",
                    "actual_time_ref", "producer_payload_hash", "source_record_id",
                )
            ):
                raise SystemExit("D05 binding does not resolve accepted inventory")
            if ref.get("binding_ref_id") != f"D05-BIND-{ref['source_record_id'].removeprefix('ASM-')}":
                raise SystemExit("D05 binding identity does not resolve source record identity")
        binding_states = fixture.get("evaluation_binding_states")
        if outcome.get("output_kind") == "definition_binding":
            if binding_states is not None or d05_refs:
                raise SystemExit("control-plane definition binding cannot create medical-unit bindings")
            if outcome.get("l1_disposition") is not None or outcome.get("domain_assertions", {}).get("medical_expected_unit_created") is not False:
                raise SystemExit("control-plane definition binding cannot create L1 unit")
            binding_states = {}
        elif not isinstance(binding_states, dict):
            raise SystemExit("medical-unit case missing evaluation binding states")
        if binding_states.get("d05_binding_state") == "required" and not d05_refs:
            raise SystemExit("required D05 binding has no refs")
        if binding_states.get("d05_binding_state") == "required":
            canonical_ref_ids = [
                f"D05-BIND-{assessment_id.removeprefix('ASM-')}"
                for assessment_id in assessments
            ]
            if expected_ref_ids != canonical_ref_ids:
                raise SystemExit("required D05 binding set does not cover accepted assessment inventory")
        if binding_states.get("d05_binding_state") == "not_required_by_unit_applicability" and d05_refs:
            raise SystemExit("not-applicable unit cannot carry D05 refs")
        if binding_states.get("maturity_binding_state") == "required" and not binding_states.get("maturity_anchor_selection_decision_id"):
            raise SystemExit("required maturity binding has no decision")
        if binding_states.get("maturity_binding_state") == "not_required" and binding_states.get("maturity_anchor_selection_decision_id"):
            raise SystemExit("not-required maturity binding carries a decision")
        spine = fixture["bindings"].get("shared_temporal_spine_binding")
        maturity_refs = fixture["bindings"].get("maturity_anchor_refs", [])
        maturity_decision = fixture["bindings"].get("maturity_anchor_selection_decision")
        if binding_states.get("d05_binding_state") == "required":
            if not isinstance(spine, dict) or spine.get("object_type") != "SharedTemporalSpineBinding":
                raise SystemExit("required D05 binding has no typed temporal spine")
            for field in scope_fields:
                if spine.get(field) != scope.get(field):
                    raise SystemExit(f"temporal spine wrong scope: {field}")
            if spine.get("cutoff") != scope.get("clinical_event_cutoff") or not spine.get("axis_version") or not spine.get("axis_hash"):
                raise SystemExit("temporal spine missing cutoff/version/hash")
            verify_embedded_hash(spine, "temporal spine")
            if fixture["bindings"].get("shared_spine_hash") != spine.get("axis_hash"):
                raise SystemExit("shared temporal spine hash mismatch")
        elif spine is not None or maturity_refs or maturity_decision is not None or registries.get("maturity_consumer_bindings"):
            raise SystemExit("not-required unit cannot carry temporal/maturity bindings")
        if binding_states.get("maturity_binding_state") == "required":
            if not isinstance(maturity_decision, dict) or maturity_decision.get("object_type") != "MaturityAnchorSelectionDecision":
                raise SystemExit("required maturity binding has no typed decision")
            if maturity_decision.get("decision_id") != binding_states.get("maturity_anchor_selection_decision_id"):
                raise SystemExit("maturity decision ID mismatch")
            if not maturity_refs or any(item.get("object_type") != "TypedMaturityAnchorRef" for item in maturity_refs):
                raise SystemExit("maturity candidates are not typed anchors")
            anchor_ids = [item.get("anchor_ref_id") for item in maturity_refs]
            if maturity_decision.get("candidate_typed_anchor_ids") != anchor_ids:
                raise SystemExit("maturity candidate set mismatch")
            for item in maturity_refs + [maturity_decision]:
                for field in scope_fields:
                    if item.get(field) != scope.get(field):
                        raise SystemExit(f"maturity object wrong scope: {field}")
                if item.get("cutoff") != scope.get("clinical_event_cutoff"):
                    raise SystemExit("maturity object wrong scope: cutoff")
                if not item.get("source_locator_ids"):
                    raise SystemExit("maturity object missing source locators")
                verify_embedded_hash(item, "maturity object")
            if maturity_decision.get("decision_status") == "unique":
                if maturity_decision.get("selected_typed_anchor_id") not in anchor_ids or not maturity_decision.get("selected_normalized_time_ref"):
                    raise SystemExit("unique maturity decision lacks selected anchor/time")
            elif maturity_decision.get("decision_status") in {"multi_feasible_boundary", "not_evaluable"}:
                if maturity_decision.get("selected_typed_anchor_id") is not None or maturity_decision.get("selected_normalized_time_ref") is not None:
                    raise SystemExit("non-unique maturity decision selected an anchor/time")
            else:
                raise SystemExit("unknown maturity decision status")
            ref_ids = {item["binding_ref_id"] for item in d05_refs}
            if any(item.get("d05_assessment_binding_ref_id") not in ref_ids for item in maturity_refs):
                raise SystemExit("maturity anchor D05 reverse link mismatch")
            d05_by_ref = {item["binding_ref_id"]: item for item in d05_refs}
            for item in maturity_refs:
                source_ref = d05_by_ref[item["d05_assessment_binding_ref_id"]]
                if item.get("stable_source_identity") != source_ref.get("source_record_id") or item.get("normalized_time_ref") != source_ref.get("actual_time_ref"):
                    raise SystemExit("maturity anchor does not resolve D05 source identity/time")
            anchor_ref_ids = [item["d05_assessment_binding_ref_id"] for item in maturity_refs]
            if maturity_decision.get("d05_assessment_binding_ref_ids") != anchor_ref_ids:
                raise SystemExit("maturity decision D05 candidate links mismatch")
            if maturity_decision.get("consumer_unit_or_result_id") not in registries.get("consumer_unit_ids", []):
                raise SystemExit("maturity decision consumer identity mismatch")
            maturity_consumers = registries.get("maturity_consumer_bindings", [])
            if len(maturity_consumers) != 1:
                raise SystemExit("required maturity decision must have one typed consumer")
            consumer = maturity_consumers[0]
            if consumer.get("object_type") != "D06MaturityConsumerBinding" or consumer.get("consumer_id") != "UNIT-001":
                raise SystemExit("maturity consumer type/identity mismatch")
            verify_embedded_hash(consumer, "maturity consumer")
            for field in scope_fields:
                if consumer.get(field) != scope.get(field):
                    raise SystemExit(f"maturity consumer wrong scope: {field}")
            if (
                consumer.get("cutoff") != scope.get("clinical_event_cutoff")
                or consumer.get("maturity_decision_id") != maturity_decision.get("decision_id")
                or maturity_decision.get("consumer_unit_or_result_id") != consumer.get("consumer_id")
                or consumer.get("stable_endpoint_key") != fixture["definitions"]["endpoint"].get("stable_key")
                or consumer.get("stable_timepoint_key") != maturity_decision.get("stable_timepoint_key")
                or consumer.get("shared_spine_hash") != maturity_decision.get("shared_spine_hash")
            ):
                raise SystemExit("maturity decision/consumer bidirectional binding mismatch")
            if maturity_decision.get("shared_spine_hash") != spine.get("axis_hash"):
                raise SystemExit("maturity decision temporal spine mismatch")
            selected_anchor_id = maturity_decision.get("selected_typed_anchor_id")
            selected_anchor = next((item for item in maturity_refs if item.get("anchor_ref_id") == selected_anchor_id), None)
            if selected_anchor is not None and maturity_decision.get("selected_normalized_time_ref") != selected_anchor.get("normalized_time_ref"):
                raise SystemExit("maturity decision selected time does not resolve selected anchor")
        estimator_state = fixture["bindings"].get("estimator_binding_state")
        estimator_binding = fixture["bindings"].get("estimator_binding")
        active_estimator_id = fixture["bindings"].get("active_estimator_binding_id")
        ice = typed_parameters.get("ice")
        def nested_estimator_objects(value: Any) -> list[Any]:
            found: list[Any] = []
            if isinstance(value, dict):
                for key, item in value.items():
                    if key == "estimator_binding" and item is not None:
                        found.append(item)
                    found.extend(nested_estimator_objects(item))
            elif isinstance(value, list):
                for item in value:
                    found.extend(nested_estimator_objects(item))
            return found
        if estimator_state in {"not_applicable", "not_required", "missing_required"}:
            if estimator_binding is not None or active_estimator_id is not None or nested_estimator_objects(typed_parameters):
                raise SystemExit("inactive/missing estimator state carries a usable binding")
        elif estimator_state == "active":
            if not isinstance(estimator_binding, dict) or active_estimator_id != estimator_binding.get("binding_id"):
                raise SystemExit("active estimator state lacks exact binding")
            for field in scope_fields:
                if estimator_binding.get(field) != scope.get(field):
                    raise SystemExit(f"estimator binding wrong scope: {field}")
            if estimator_binding.get("cutoff") != scope.get("clinical_event_cutoff"):
                raise SystemExit("estimator binding wrong scope: cutoff")
            if not estimator_binding.get("stable_endpoint_key") or not estimator_binding.get("estimand_context_ref") or not estimator_binding.get("source_locator_ids"):
                raise SystemExit("estimator binding missing endpoint/estimand/trace")
            verify_embedded_hash(estimator_binding, "estimator binding")
        else:
            raise SystemExit("unknown estimator binding state")
        if isinstance(ice, dict):
            missing_input_binding = ice.get("estimator_binding", object()) is None
            if ice.get("estimator_availability") == "available" and missing_input_binding and estimator_state != "missing_required":
                raise SystemExit("available ICE without binding must be missing_required")
            if ice.get("estimator_availability") == "not_required" and estimator_state != "not_required":
                raise SystemExit("not-required ICE has contradictory estimator state")
        enrollment_state = fixture["bindings"].get("enrollment_binding_state")
        enrollment_decisions = fixture["bindings"].get("enrollment_context_decisions", [])
        source_events = {
            item.get("event_id"): item
            for item in fixture.get("source_registries", {}).get("enrollment_source_events", [])
        }
        if len(source_events) != len(fixture.get("source_registries", {}).get("enrollment_source_events", [])):
            raise SystemExit("enrollment source event IDs must be unique")
        for event in source_events.values():
            if event.get("object_type") != "EnrollmentSourceEvent":
                raise SystemExit("enrollment source event object type mismatch")
            verify_embedded_hash(event, "enrollment source event")
        enrollment_event_contract = {
            "enrollment_not_occurred": ("SCREENING-STATUS-001", "screening_status"),
            "enrolled_or_post_enrollment": ("ENROLLMENT-001", "enrollment"),
            "enrollment_state_unresolved": ("ENROLLMENT-CONFLICT-001", "enrollment_conflict"),
        }
        enrollment_rule = registries.get("enrollment_rule_registry")
        if not isinstance(enrollment_rule, dict) or enrollment_rule.get("object_type") != "EnrollmentDecisionRule":
            raise SystemExit("enrollment rule registry missing or wrong type")
        verify_embedded_hash(enrollment_rule, "enrollment rule registry")
        if (
            enrollment_rule.get("decision_rule_id") != "ENROLL-RULE-001"
            or enrollment_rule.get("rule_version") != "1.0"
            or enrollment_rule.get("allowed_contexts") != list(enrollment_event_contract)
        ):
            raise SystemExit("enrollment rule registry is not canonical")
        if not all(item.get("object_type") == "EnrollmentContextDecisionRef" for item in enrollment_decisions):
            raise SystemExit("enrollment decisions must be typed objects")
        for decision_index, item in enumerate(enrollment_decisions, 1):
            for field in scope_fields:
                if item.get(field) != scope.get(field):
                    raise SystemExit(f"enrollment decision wrong scope: {field}")
            if item.get("cutoff") != scope.get("clinical_event_cutoff") or not item.get("effective_time_ref") or not item.get("source_event_refs") or not item.get("rule_version"):
                raise SystemExit("enrollment decision missing time/source/rule trace")
            verify_embedded_hash(item, "enrollment decision")
            if item.get("decision_id") != f"ENROLL-DEC-{decision_index:03d}":
                raise SystemExit("enrollment decision identity is not canonical")
            if item.get("decision_rule_id") != enrollment_rule.get("decision_rule_id") or item.get("rule_version") != enrollment_rule.get("rule_version"):
                raise SystemExit("enrollment decision rule/version mismatch")
            expected_event = enrollment_event_contract.get(item.get("query_context"))
            if expected_event is None or item.get("source_event_refs") != [expected_event[0]]:
                raise SystemExit("enrollment decision uses a non-canonical source event")
            for event_id in item["source_event_refs"]:
                event = source_events.get(event_id)
                if not event or event.get("event_role") != expected_event[1] or event.get("effective_time_ref") != item.get("effective_time_ref") or event.get("query_context") != item.get("query_context"):
                    raise SystemExit("enrollment decision source event cannot resolve")
        if enrollment_state == "variant_matrix":
            expected_contexts = typed_parameters.get("query_context_variants")
            if [item["query_context"] for item in enrollment_decisions] != expected_contexts:
                raise SystemExit("enrollment variant decisions do not match inputs")
            mapping = fixture["bindings"].get("active_enrollment_decision_ids_by_context", {})
            if mapping != {item["query_context"]: item["decision_id"] for item in enrollment_decisions}:
                raise SystemExit("enrollment variant active mapping mismatch")
            assertions = outcome.get("domain_assertions", {})
            expected_rules = {item["query_context"]: {"decision_rule_id": item["decision_rule_id"], "rule_version": item["rule_version"]} for item in enrollment_decisions}
            if assertions.get("enrollment_decision_ids_by_context") != mapping or assertions.get("enrollment_source_events_by_context") != {item["query_context"]: item["source_event_refs"] for item in enrollment_decisions} or assertions.get("enrollment_rules_by_context") != expected_rules:
                raise SystemExit("enrollment variant expected identity mismatch")
        elif enrollment_state == "active":
            if len(enrollment_decisions) != 1 or fixture["bindings"].get("active_enrollment_decision_id") != enrollment_decisions[0]["decision_id"]:
                raise SystemExit("active enrollment decision mismatch")
            expected_context = outcome.get("domain_assertions", {}).get("query_context")
            if expected_context and enrollment_decisions[0].get("query_context") != expected_context:
                raise SystemExit("active enrollment Query context mismatch")
            assertions = outcome.get("domain_assertions", {})
            if assertions.get("enrollment_decision_id") != enrollment_decisions[0]["decision_id"] or assertions.get("enrollment_source_event_refs") != enrollment_decisions[0]["source_event_refs"] or assertions.get("enrollment_decision_rule_id") != enrollment_decisions[0]["decision_rule_id"] or assertions.get("enrollment_rule_version") != enrollment_decisions[0]["rule_version"]:
                raise SystemExit("active enrollment expected identity mismatch")
        elif enrollment_state == "not_required":
            if enrollment_decisions or fixture["bindings"].get("active_enrollment_decision_id") is not None:
                raise SystemExit("not-required enrollment state carries a decision")
        else:
            raise SystemExit("unknown enrollment binding state")
        tte_registry = fixture.get("source_registries", {}).get("tte_source_registry")
        if not isinstance(tte_registry, dict) or tte_registry.get("object_type") != "TTESourceRegistry":
            raise SystemExit("TTE source registry missing")
        verify_embedded_hash(tte_registry, "TTE source registry")
        tte_binding = fixture["bindings"].get("tte_precedence_binding", {})
        if tte_binding.get("object_type") != "TTEEndpointPrecedenceBinding":
            raise SystemExit("TTE precedence binding object type mismatch")
        verify_lineage_hash(tte_binding, "TTE precedence binding")
        tte_rule = registries.get("tte_rule_registry")
        if not isinstance(tte_rule, dict) or tte_rule.get("object_type") != "TTEPrecedenceRule":
            raise SystemExit("TTE rule registry missing or wrong type")
        verify_embedded_hash(tte_rule, "TTE rule registry")
        if tte_rule.get("event_precedence_rule_id") != "TTE-RULE-001" or tte_rule.get("allowed_tie_policies") != ["first_in_order", "boundary"]:
            raise SystemExit("TTE rule registry is not canonical")
        typed_tte_events = {item.get("event_id"): item for item in registries.get("tte_source_events", [])}
        if list(typed_tte_events) != ["EV-TARGET-001", "EV-COMP-001"]:
            raise SystemExit("TTE typed source event identity set mismatch")
        for event_id, role in (("EV-TARGET-001", "target_event"), ("EV-COMP-001", "competing_event")):
            event = typed_tte_events[event_id]
            if event.get("object_type") != "TypedTTEEventSource" or event.get("event_role") != role:
                raise SystemExit("TTE typed source event type/role mismatch")
            verify_embedded_hash(event, "TTE typed source event")
        endpoint_definition = fixture["definitions"].get("endpoint", {})
        timepoint_definition = fixture["definitions"].get("timepoint", {})
        tte_records = fixture["records"].get("tte", {})
        if (
            tte_registry.get("stable_endpoint_key") != endpoint_definition.get("stable_key")
            or tte_registry.get("stable_timepoint_key") != timepoint_definition.get("key")
            or tte_binding.get("stable_endpoint_key") != tte_registry.get("stable_endpoint_key")
            or tte_binding.get("stable_timepoint_key") != tte_registry.get("stable_timepoint_key")
            or tte_binding.get("event_precedence_rule_id") != tte_registry.get("event_precedence_rule_id")
            or tte_registry.get("event_precedence_rule_id") != tte_rule.get("event_precedence_rule_id")
            or tte_registry.get("tie_policy") not in tte_rule.get("allowed_tie_policies", [])
        ):
            raise SystemExit("TTE precedence binding does not resolve frozen endpoint/timepoint/rule")
        for registry_field, record_field in (
            ("origin_time_ref", "origin"), ("event_time_ref", "event_time"),
            ("censor_time_ref", "censor_time"), ("target_event_ref", "target_event_ref"),
            ("competing_event_ref", "competing_event_ref"),
        ):
            if tte_registry.get(registry_field) != tte_records.get(record_field):
                raise SystemExit(f"TTE source registry does not resolve record: {registry_field}")
        if tte_records.get("event_time") != timepoint_definition.get("nominal_time") or tte_records.get("censor_time") != timepoint_definition.get("nominal_time"):
            raise SystemExit("TTE event/censor time does not resolve frozen timepoint")
        if (
            tte_records.get("target_event_ref") != "EV-TARGET-001"
            or tte_records.get("competing_event_ref") != "EV-COMP-001"
            or typed_tte_events["EV-TARGET-001"].get("effective_time_ref") != tte_records.get("event_time")
            or typed_tte_events["EV-COMP-001"].get("effective_time_ref") != tte_records.get("event_time")
        ):
            raise SystemExit("TTE record does not resolve canonical typed source events")
        if case["challenge_number"] == 219:
            tte_inputs = typed_parameters.get("tte", {})
            if tte_inputs.get("tie_policy") != "boundary" or tte_registry.get("tie_policy") != "boundary":
                raise SystemExit("TTE boundary tie policy mismatch")
            interpretations = fixture["records"].get("tte", {}).get("feasible_interpretations", [])
            expected_ids = outcome.get("domain_assertions", {}).get("feasible_interpretation_ref_ids")
            if [item.get("interpretation_ref_id") for item in interpretations] != expected_ids or len(interpretations) < 2:
                raise SystemExit("TTE boundary interpretation set mismatch")
            for item in interpretations:
                if item.get("object_type") != "TimeToEventInterpretationRef" or not item.get("validation_state") or not item.get("stable_source_identity") or not item.get("source_locator_ids"):
                    raise SystemExit("TTE boundary interpretation is incomplete")
                for field in scope_fields:
                    if item.get(field) != scope.get(field):
                        raise SystemExit(f"TTE interpretation wrong scope: {field}")
                if item.get("cutoff") != scope.get("clinical_event_cutoff"):
                    raise SystemExit("TTE interpretation wrong scope: cutoff")
                if item.get("state") == "event" and not item.get("event_time_ref"):
                    raise SystemExit("TTE event interpretation lacks event time")
                if item.get("state") == "censored" and not item.get("censor_time_ref"):
                    raise SystemExit("TTE censor interpretation lacks censor time")
                if item.get("origin_time_ref") != tte_registry.get("origin_time_ref"):
                    raise SystemExit("TTE interpretation origin time mismatch")
                if item.get("state") == "event" and (item.get("event_time_ref") != tte_registry.get("event_time_ref") or item.get("target_event_ref") != tte_registry.get("target_event_ref")):
                    raise SystemExit("TTE event interpretation source mismatch")
                if item.get("state") == "censored" and item.get("censor_time_ref") != tte_registry.get("censor_time_ref"):
                    raise SystemExit("TTE censor interpretation source mismatch")
                verify_embedded_hash(item, "TTE interpretation")
            if interpretations[0].get("event_time_ref") != interpretations[1].get("censor_time_ref") or outcome.get("domain_assertions", {}).get("single_duration") is not None:
                raise SystemExit("TTE boundary is not same-time/no-duration")
        policies = fixture["policies"]
        resolver_input = policies.get("priority_resolution_input")
        decision = policies.get("priority_decision")
        priority_policy = policies.get("priority_policy")
        expected_priority_policy = canonical_priority_policy()
        if priority_policy != expected_priority_policy:
            raise SystemExit("fixture priority policy does not match canonical full definition")
        if outcome.get("output_kind") == "definition_binding":
            if resolver_input is not None or decision is not None:
                raise SystemExit("control-plane binding cannot materialize priority input/decision")
        elif not isinstance(resolver_input, dict) or resolver_input.get("object_type") != "D06PriorityResolverInput":
            raise SystemExit("medical case missing priority resolver input")
        priority_source = decision if isinstance(decision, dict) else resolver_input
        for field in (
            "priority_policy_id", "priority_policy_version", "priority_policy_hash", "endpoint_definition_id", "stable_endpoint_key",
            "stable_timepoint_key", "endpoint_role", "impact_resolution_state", "impact_class", "recurrence_class",
            "recoverability", "actionability", "monitoring_priority", "reason_codes",
            "machine_close_forbidden", "source_locator_ids",
        ):
            if priority_source is not None and (field not in priority_source or priority_source[field] in ("", [])):
                raise SystemExit(f"priority source missing {field}")
        if priority_source is not None and priority_source.get("impact_resolution_state") == "resolved" and priority_source.get("impact_class") is None:
            raise SystemExit("resolved priority impact is missing")
        if priority_source is not None and priority_source.get("impact_resolution_state") == "unresolved" and priority_source.get("impact_class") is not None:
            raise SystemExit("unresolved priority impact must not be guessed")
        resolution = outcome.get("domain_assertions", {}).get("priority_resolution")
        if not isinstance(resolution, dict):
            raise SystemExit("expected outcome does not assert priority resolution")
        if priority_source is None:
            if resolution.get("projection_state") != "not_run_control_plane" or any(
                resolution.get(field) is not None for field in (
                    "priority_resolver_input_hash", "priority_decision_id", "endpoint_role",
                    "impact_resolution_state", "impact_class", "recurrence_class",
                    "recoverability", "actionability", "monitoring_priority",
                    "matched_precedence_step", "machine_close_forbidden",
                )
            ):
                raise SystemExit("control-plane binding must not run priority resolution")
        else:
            resolved_priority, resolved_step, resolved_machine_close = resolve_priority(priority_source)
            if (priority_source.get("monitoring_priority"), priority_source.get("matched_precedence_step"), priority_source.get("machine_close_forbidden")) != (resolved_priority, resolved_step, resolved_machine_close):
                raise SystemExit("priority source does not match frozen precedence")
            for field in scope_fields:
                if priority_source.get(field) != scope.get(field):
                    raise SystemExit(f"priority source wrong scope: {field}")
            if priority_source.get("cutoff") != scope.get("clinical_event_cutoff"):
                raise SystemExit("priority source wrong scope: cutoff")
            if (
                priority_source.get("priority_policy_id") != priority_policy.get("policy_id")
                or priority_source.get("priority_policy_version") != priority_policy.get("version")
                or priority_source.get("priority_policy_hash") != priority_policy.get("policy_hash")
            ):
                raise SystemExit("priority source does not resolve canonical policy")
            endpoint_definition = fixture["definitions"]["endpoint"]
            timepoint_definition = fixture["definitions"]["timepoint"]
            if (
                priority_source.get("endpoint_definition_id") != endpoint_definition.get("id")
                or priority_source.get("stable_endpoint_key") != endpoint_definition.get("stable_key")
                or priority_source.get("stable_timepoint_key") != timepoint_definition.get("key")
                or endpoint_definition.get("id") != "EP-001"
                or endpoint_definition.get("stable_key") != "SYN-ENDPOINT"
                or timepoint_definition.get("key") != "WEEK-4"
                or priority_source.get("endpoint_role") != endpoint_definition.get("role")
                or priority_source.get("reason_codes") != PRIORITY_REASON_BY_STEP.get(resolved_step)
            ):
                raise SystemExit("priority source does not resolve endpoint/timepoint/reason semantics")
            verify_embedded_hash(resolver_input, "priority resolver input")
            for field in (
                "priority_policy_id", "priority_policy_version", "priority_policy_hash",
                "endpoint_definition_id", "stable_endpoint_key", "stable_timepoint_key", "reason_codes",
                "endpoint_role", "impact_resolution_state", "impact_class", "recurrence_class",
                "recoverability", "actionability", "monitoring_priority",
                "matched_precedence_step", "machine_close_forbidden",
            ):
                if resolution.get(field) != priority_source.get(field):
                    raise SystemExit(f"expected priority resolution mismatch: {field}")
            if resolution.get("priority_resolver_input_hash") != resolver_input.get("hash"):
                raise SystemExit("expected priority resolver input hash mismatch")
            expected_decision_id = decision.get("priority_decision_id") if isinstance(decision, dict) else None
            if resolution.get("priority_decision_id") != expected_decision_id:
                raise SystemExit("expected priority decision identity mismatch")
        expected_risks = (outcome.get("l2_counts") or {}).get("risks", 0)
        risk_binding = fixture.get("risk_binding")
        identity = fixture.get("public_r4_risk_identity")
        if expected_risks:
            if fixture.get("risk_binding_state") != "created" or not isinstance(risk_binding, dict) or not isinstance(decision, dict):
                raise SystemExit("risk-producing case missing D06 risk binding")
            if fixture.get("public_r4_identity_state") != "created" or not isinstance(identity, dict):
                raise SystemExit("risk-producing case missing public R4 identity")
            if decision.get("object_type") != "D06PriorityDecision" or risk_binding.get("object_type") != "D06RiskBinding" or identity.get("object_type") != "PublicR4RiskIdentity":
                raise SystemExit("risk/priority/public identity object type mismatch")
            if risk_binding.get("classifier") != "efficacy_evaluation" or risk_binding.get("primary_subtype") != outcome.get("primary_subtype"):
                raise SystemExit("risk binding classifier/subtype does not match expected outcome")
            for field in ("priority_decision_id", "risk_id", "unit_id", "lineage_hash"):
                if not decision.get(field):
                    raise SystemExit(f"emitted priority decision missing {field}")
            canonical_unit_suffix = decision["unit_id"].removeprefix("UNIT-")
            if decision.get("priority_decision_id") != f"PRIORITY-DEC-{canonical_unit_suffix}" or decision.get("risk_id") != f"RISK-{canonical_unit_suffix}":
                raise SystemExit("emitted priority/risk identity is not canonical")
            for field in scope_fields:
                if decision.get(field) != scope.get(field):
                    raise SystemExit(f"priority decision wrong scope: {field}")
            if decision.get("cutoff") != scope.get("clinical_event_cutoff"):
                raise SystemExit("priority decision wrong scope: cutoff")
            verify_lineage_hash(decision, "priority decision")
            if decision.get("priority_resolver_input_hash") != resolver_input.get("hash"):
                raise SystemExit("priority decision does not bind resolver input")
            for field in (
                "priority_policy_id", "priority_policy_version", "priority_policy_hash",
                "endpoint_definition_id", "stable_endpoint_key", "stable_timepoint_key", "endpoint_role",
                "impact_resolution_state", "impact_class", "recurrence_class",
                "recoverability", "actionability", "monitoring_priority", "reason_codes",
                "matched_precedence_step", "machine_close_forbidden",
            ):
                if decision.get(field) != resolver_input.get(field):
                    raise SystemExit(f"priority decision diverges from resolver input: {field}")
            for field in scope_fields:
                if risk_binding.get(field) != scope.get(field):
                    raise SystemExit(f"risk binding wrong scope: {field}")
            if risk_binding.get("cutoff") != scope.get("clinical_event_cutoff"):
                raise SystemExit("risk binding wrong scope: cutoff")
            if (
                risk_binding.get("priority_decision_id") != decision.get("priority_decision_id")
                or risk_binding.get("unit_id") != decision.get("unit_id")
                or risk_binding.get("risk_id") != decision.get("risk_id")
            ):
                raise SystemExit("risk binding priority/unit/risk decision mismatch")
            if risk_binding.get("public_r4_risk_identity_id") != identity.get("public_r4_risk_identity_id"):
                raise SystemExit("risk binding public identity mismatch")
            if identity.get("risk_id") != risk_binding.get("risk_id") or identity.get("unit_id") != risk_binding.get("unit_id"):
                raise SystemExit("public identity reverse risk binding mismatch")
            verify_lineage_hash(risk_binding, "risk binding")
            if identity.get("domain_id") != "D06" or identity.get("scope_type") != "subject_endpoint_timepoint_episode":
                raise SystemExit("public R4 identity wrong D06 domain/scope type")
            for field in ("subject_ref", "site_ref", "episode_key", "scope_binding_id"):
                if identity.get(field) != scope.get(field):
                    raise SystemExit(f"public R4 identity wrong scope: {field}")
            if identity.get("cutoff") != scope.get("clinical_event_cutoff") or identity.get("unit_id") != risk_binding.get("unit_id") or identity.get("stable_endpoint_key") != decision.get("stable_endpoint_key") or identity.get("stable_timepoint_key") != decision.get("stable_timepoint_key"):
                raise SystemExit("public R4 identity D06 binding mismatch")
            stable_core = registries.get("d06_unit_stable_core")
            if not isinstance(stable_core, dict) or stable_core.get("object_type") != "D06UnitStableCore":
                raise SystemExit("D06 unit stable core missing or wrong type")
            verify_embedded_hash(stable_core, "D06 unit stable core")
            expected_unit_kind = SUBTYPE_TO_UNIT_KIND.get(risk_binding.get("primary_subtype"))
            expected_component = "overall" if expected_unit_kind == "endpoint_composition" else "none"
            expected_rule_lineage = f"{fixture['definitions']['algorithm']['id']}@{fixture['definitions']['algorithm']['version']}"
            if (
                stable_core.get("unit_id") != "UNIT-001"
                or stable_core.get("domain_id") != "D06"
                or stable_core.get("classifier") != risk_binding.get("classifier")
                or stable_core.get("unit_kind") != expected_unit_kind
                or stable_core.get("stable_endpoint_key") != fixture["definitions"]["endpoint"].get("stable_key")
                or stable_core.get("stable_instrument_key_or_none") != fixture["definitions"]["instrument"].get("stable_key")
                or stable_core.get("stable_timepoint_key") != fixture["definitions"]["timepoint"].get("key")
                or stable_core.get("stable_item_or_component_key_or_none") != expected_component
                or stable_core.get("stable_source_record_id") != "ASM-W4-A"
                or stable_core.get("stable_source_record_id") not in assessments
                or stable_core.get("temporal_window") != [fixture["definitions"]["timepoint"].get("key"), scope.get("episode_key")]
                or stable_core.get("rule_or_knowledge_lineage") != expected_rule_lineage
            ):
                raise SystemExit("D06 unit stable core does not resolve frozen sources/definitions")
            expected_normalized_concept = [
                stable_core["classifier"], stable_core["unit_kind"],
                stable_core["stable_endpoint_key"], stable_core["stable_instrument_key_or_none"],
                stable_core["stable_timepoint_key"], stable_core["stable_item_or_component_key_or_none"],
            ]
            if (
                decision.get("unit_id") != stable_core.get("unit_id")
                or identity.get("stable_source_or_event_identity") != stable_core.get("stable_source_record_id")
                or identity.get("normalized_concept") != expected_normalized_concept
                or identity.get("temporal_window") != stable_core.get("temporal_window")
                or identity.get("rule_or_knowledge_lineage") != stable_core.get("rule_or_knowledge_lineage")
                or identity.get("scope_key") != [scope.get("subject_ref"), scope.get("site_ref"), scope.get("episode_key")]
            ):
                raise SystemExit("public R4 identity does not resolve D06 stable core")
            tuple_keys = ("project_ref","domain_id","scope_type","scope_key","stable_source_or_event_identity","normalized_concept","temporal_window","rule_or_knowledge_lineage","public_identity_version","risk_id","unit_id","scope_binding_id","cutoff")
            expected_tuple = [identity.get(key) for key in tuple_keys]
            expected_identity_hash = f"sha256:{sha256_text(canonical_json(expected_tuple))}"
            if identity.get("canonical_tuple") != expected_tuple or identity.get("public_identity_hash") != expected_identity_hash or identity.get("public_r4_risk_identity_id") != f"R4ID-{expected_identity_hash[-16:]}":
                raise SystemExit("public R4 identity canonical binding mismatch")
        elif fixture.get("risk_binding_state") != "not_created" or risk_binding is not None or decision is not None or fixture.get("public_r4_identity_state") != "not_created" or identity is not None or registries.get("d06_unit_stable_core") is not None:
            raise SystemExit("non-risk case must not create risk/priority/identity objects")
        if case.get("assertion_dsl_version") != "d06-assert-v1":
            raise SystemExit("unknown assertion DSL version")
        clauses = case.get("assertion_dsl")
        if not isinstance(clauses, list) or not clauses:
            raise SystemExit("missing assertion DSL")
        def leaves(value: Any, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
            if isinstance(value, dict):
                result: set[tuple[str, ...]] = set()
                for key, item in value.items():
                    result |= leaves(item, prefix + (str(key),))
                return result
            return {prefix}
        expected_leaf_paths = leaves(outcome)
        clause_paths = [tuple(clause.get("outcome_path", [])) for clause in clauses]
        if len(clauses) != len(expected_leaf_paths) or set(clause_paths) != expected_leaf_paths:
            raise SystemExit("assertion DSL paths are not an exact bijection to expected leaves")
        for index, clause in enumerate(clauses, 1):
            if set(clause) != {
                "canonicalization_rule", "clause_id", "operator",
                "outcome_path", "typed_expected_value",
            }:
                raise SystemExit("assertion DSL clause fields are not exact and complete")
            if clause.get("clause_id") != f"assert-{index:03d}" or clause.get("operator") not in {"equals", "is_null"} or clause.get("canonicalization_rule") != "d06-canonical-v1":
                raise SystemExit("assertion DSL contains unknown, extra, or non-canonical clause")
            operator = clause["operator"]
            expected_value = clause["typed_expected_value"]
            if (operator == "is_null" and expected_value is not None) or (
                operator == "equals" and expected_value is None
            ):
                raise SystemExit("assertion DSL operator/value compatibility mismatch")
        fixture_hash = sha256_text(canonical_json(fixture))
        assertions = outcome.get("domain_assertions", {})
        if assertions.get("evaluated_fixture_hash") != fixture_hash:
            raise SystemExit("expected outcome does not bind exact fixture hash")
        if outcome.get("invoked_entrypoint") != case.get("entrypoint_id"):
            raise SystemExit("expected entrypoint does not match case entrypoint")
        if outcome.get("input_scope_hash") != f"sha256:{sha256_text(canonical_json(scope))}":
            raise SystemExit("expected input scope hash mismatch")
        expected_object_hashes = outcome.get("object_hashes", {})
        if expected_object_hashes.get("fixture_hash") != fixture_hash or expected_object_hashes.get("scope_hash") != sha256_text(canonical_json(scope)):
            raise SystemExit("expected object hashes do not bind fixture/scope")
        expected_resolver_hash = resolver_input.get("hash") if isinstance(resolver_input, dict) else None
        expected_identity_object_hash = identity.get("public_identity_hash") if isinstance(identity, dict) else None
        if expected_object_hashes.get("priority_resolver_input_hash") != expected_resolver_hash or expected_object_hashes.get("public_r4_identity_hash") != expected_identity_object_hash:
            raise SystemExit("expected object hashes do not bind priority/public identity")
        if expected_object_hashes.get("priority_policy_hash") != priority_policy.get("policy_hash"):
            raise SystemExit("expected object hashes do not bind canonical priority policy")
        required_trace_edges = case["required_trace_edge_types"]
        if required_trace_edges != sorted(set(required_trace_edges)):
            raise SystemExit("required trace edges are not canonical sorted-unique")
        if outcome.get("trace_edges") != required_trace_edges:
            raise SystemExit("expected trace edges mismatch")
        if case.get("required_outcome_fields") != sorted(outcome):
            raise SystemExit("catalog required outcome fields do not exactly match expected outcome")
        hash_relation = assertions.get("hash_relation")
        exact_hash_relations = (
            [] if hash_relation is None else
            hash_relation if isinstance(hash_relation, list) else [hash_relation]
        )
        if case.get("required_hash_relations") != exact_hash_relations:
            raise SystemExit("catalog required hash relations mismatch")
        audience_checks = case.get("required_audience_checks", [])
        is_audience_entrypoint = case.get("entrypoint_id") == "d06.audience_projection_validator"
        if is_audience_entrypoint and audience_checks != CANONICAL_AUDIENCE_CHECKS:
            raise SystemExit("audience entrypoint required checks do not match canonical complete set")
        if not is_audience_entrypoint and audience_checks:
            raise SystemExit("non-audience entrypoint cannot declare audience checks")
        if audience_checks:
            audience_result = outcome.get("audience_validation_result")
            if not isinstance(audience_result, dict) or audience_result.get("validation_state") != outcome.get("audience_validation_state"):
                raise SystemExit("audience validation outcome mismatch")
            if audience_result.get("payload_schema") is not True:
                raise SystemExit("audience payload schema validation is not authoritative")
            if audience_result.get("audience_payload_absent") != outcome.get("audience_payload_absent"):
                raise SystemExit("audience nested/top-level suppression mismatch")
            calculated_lexicon_hash = sha256_text(canonical_json({"display_keys": AUDIENCE_DISPLAY_KEYS, "phrases": AUDIENCE_PHRASES}))
            if calculated_lexicon_hash != AUDIENCE_LEXICON_HASH or audience_result.get("forbidden_lexicon_hash") != AUDIENCE_LEXICON_HASH:
                raise SystemExit("audience lexicon hash mismatch")
            validator_hash = sha256_text(canonical_json(AUDIENCE_VALIDATOR_DEFINITION))
            if (
                audience_result.get("validator_version") != AUDIENCE_VALIDATOR_VERSION
                or audience_result.get("validator_hash") != validator_hash
                or audience_result.get("lexicon_version") != "d06-audience-zh-v1"
            ):
                raise SystemExit("audience validator/lexicon identity mismatch")
            suppressed = outcome.get("audience_payload_absent") is True
            if suppressed and "audience_payload" in outcome:
                raise SystemExit("suppressed audience outcome leaked payload")
            if not suppressed and "audience_payload" not in outcome:
                raise SystemExit("non-suppressed audience outcome lacks payload")
            payload = outcome.get("audience_payload")
            if payload is not None:
                if not isinstance(payload, dict):
                    raise SystemExit("audience payload must be a typed object")
                payload_schema_version = validate_audience_payload_schema(payload)
                if audience_result.get("payload_schema_version") != payload_schema_version:
                    raise SystemExit("audience validation result payload schema mismatch")
                if audience_result.get("validation_state") != "passed" or suppressed:
                    raise SystemExit("valid audience payload state/suppression mismatch")
            elif audience_result.get("payload_schema_version") != "none":
                raise SystemExit("suppressed/absent audience payload schema must be none")
            attempted_payload = payload if payload is not None else {
                key: typed_parameters[key]
                for key in ("audience", "projection", "query")
                if key in typed_parameters
            }
            display_view = (
                audience_display_view(payload)
                if payload is not None else attempted_display_view(attempted_payload)
            )
            computed_fragment_hits = audience_phrase_hits(audience_visible_strings(display_view))
            computed_key_hits = forbidden_audience_keys(attempted_payload)
            computed_string_paths = audience_string_paths(display_view)
            if audience_result.get("validated_display_string_paths") != computed_string_paths:
                raise SystemExit("audience visible string paths are not independently reproducible")
            if audience_result.get("forbidden_fragment_hits") != computed_fragment_hits:
                raise SystemExit("audience forbidden phrase hits are not independently reproducible")
            if computed_key_hits:
                raise SystemExit("audience payload contains forbidden visible keys")
            if computed_fragment_hits and (audience_result.get("validation_state") != "failed" or not suppressed):
                raise SystemExit("audience forbidden language was not failed and suppressed")
            if audience_result.get("validation_state") == "failed" and not suppressed:
                raise SystemExit("failed audience payload was not suppressed")
        if assertions.get("challenge_assertion_code") != f"D06-CH-{case['challenge_number']:03d}":
            raise SystemExit("challenge assertion code mismatch")
        if not assertions.get("clinical_outcome_contract"):
            raise SystemExit("missing exact clinical outcome contract")
        expected_leaf_values: dict[tuple[str, ...], Any] = {}
        def collect_leaves(value: Any, prefix: tuple[str, ...] = ()) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    collect_leaves(item, prefix + (str(key),))
            else:
                expected_leaf_values[prefix] = value
        collect_leaves(outcome)
        for path, value in expected_leaf_values.items():
            matching = [clause for clause in clauses if tuple(clause.get("outcome_path", [])) == path]
            if len(matching) != 1 or matching[0].get("typed_expected_value") != value:
                raise SystemExit(f"assertion DSL is not exact for outcome leaf: {path}")
        oracle_case = outcome_oracle.get(case["challenge_number"])
        if (
            not isinstance(oracle_case, dict)
            or oracle_case.get("fixture_hash") != fixture_hash
            or oracle_case.get("expected_outcome") != outcome
        ):
            raise SystemExit("catalog fixture/outcome diverges from independent immutable oracle")
    substantive_groups: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        group_key = sha256_text(canonical_json(substantive_fixture(case["fixture"])))
        substantive_groups.setdefault(group_key, []).append(case)
    for group in substantive_groups.values():
        if len(group) < 2:
            continue
        reference = group[0]
        authoritative_contract = resolve_definition_boundary_clinical_contract(reference)
        reference_outcome = non_case_bound_outcome(reference["expected_outcome"])
        for candidate in group[1:]:
            if candidate["entrypoint_id"] != reference["entrypoint_id"]:
                raise SystemExit("identical substantive fixture has contradictory entrypoint")
            if candidate["required_trace_edge_types"] != reference["required_trace_edge_types"]:
                raise SystemExit("identical substantive fixture has contradictory trace contract")
            if non_case_bound_outcome(candidate["expected_outcome"]) != reference_outcome:
                raise SystemExit("identical substantive fixture has contradictory runtime outcome")
            if resolve_definition_boundary_clinical_contract(candidate) != authoritative_contract:
                raise SystemExit("identical substantive fixture has contradictory semantic binding")
        for candidate in group:
            if (
                candidate["expected_outcome"]["domain_assertions"].get(
                    "clinical_outcome_contract"
                )
                != authoritative_contract
            ):
                raise SystemExit("clinical outcome contract diverges from typed semantic resolver")
    return cases


def build_manifest(
    case: dict[str, Any], contract_semantic_hash: str, catalog_hash: str,
    outcome_oracle_hash: str, catalog_id: str, catalog_version: str,
) -> dict[str, Any]:
    fixture = case["fixture"]
    expected = case["expected_outcome"]
    fixture_hash = sha256_text(canonical_json(fixture))
    core = {
        "assertion_dsl": case["assertion_dsl"],
        "assertion_dsl_hash": sha256_text(canonical_json(case["assertion_dsl"])),
        "assertion_dsl_version": case["assertion_dsl_version"],
        "catalog_hash": catalog_hash,
        "catalog_id": catalog_id,
        "catalog_version": catalog_version,
        "challenge_number": case["challenge_number"],
        "contract_semantic_hash": contract_semantic_hash,
        "entrypoint_id": case["entrypoint_id"],
        "fixture_hash": fixture_hash,
        "fixture_id": case["fixture_id"],
        "outcome_oracle_hash": outcome_oracle_hash,
        "required_audience_checks": case["required_audience_checks"],
        "required_exact_values": expected,
        "required_hash_relations": case["required_hash_relations"],
        "required_outcome_fields": case["required_outcome_fields"],
        "required_trace_edge_types": case["required_trace_edge_types"],
        "test_id": case["test_id"],
    }
    digest = sha256_text(canonical_json(core))
    return {
        "manifest_id": f"d06m-{case['challenge_number']:03d}-{digest[:16]}",
        "manifest_hash": digest,
        **core,
    }


def render_registry() -> tuple[dict[str, Any], str]:
    contract_text = CONTRACT.read_text(encoding="utf-8")
    if hashlib.sha256(CONTRACT.read_bytes()).hexdigest() != CANONICAL_CONTRACT_FILE_SHA256:
        raise SystemExit("contract file bytes do not match canonical review snapshot")
    validate_contract_preamble(contract_text)
    numbers = matrix_numbers(contract_text)
    if numbers != list(range(1, 220)):
        raise SystemExit("contract challenge rows must be ordered and contiguous 1..219")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    cases = validate_catalog(catalog)
    _, outcome_oracle_hash = load_outcome_oracle()
    contract_semantic_hash = semantic_hash(contract_text)
    if contract_semantic_hash != CANONICAL_CONTRACT_SEMANTIC_HASH:
        raise SystemExit("contract semantic hash does not match canonical reviewed D06 contract")
    manifests = [
        build_manifest(
            case, contract_semantic_hash, catalog["catalog_hash"], outcome_oracle_hash,
            catalog["catalog_id"], catalog["version"],
        )
        for case in cases
    ]
    for manifest in manifests:
        manifest_core = {
            key: value for key, value in manifest.items()
            if key not in {"manifest_id", "manifest_hash"}
        }
        manifest_hash = sha256_text(canonical_json(manifest_core))
        expected_id = f"d06m-{manifest['challenge_number']:03d}-{manifest_hash[:16]}"
        if manifest.get("manifest_hash") != manifest_hash or manifest.get("manifest_id") != expected_id:
            raise SystemExit("manifest identity/hash mismatch")
    row_to_manifest = {
        str(item["challenge_number"]): item["manifest_id"] for item in manifests
    }
    test_to_row = {item["test_id"]: item["challenge_number"] for item in manifests}
    core = {
        "catalog_hash": catalog["catalog_hash"],
        "catalog_id": catalog["catalog_id"],
        "catalog_version": catalog["version"],
        "challenge_count": len(manifests),
        "contract_semantic_hash": contract_semantic_hash,
        "manifests": manifests,
        "ordered_manifest_ids": [item["manifest_id"] for item in manifests],
        "outcome_oracle_hash": outcome_oracle_hash,
        "registry_id": "medical-monitoring-r4-d06-challenge-registry",
        "row_to_manifest": row_to_manifest,
        "test_to_row": test_to_row,
        "version": "4.0.0",
    }
    registry_hash = sha256_text(canonical_json(core))
    registry = {**core, "frozen_at": FROZEN_AT, "registry_hash": registry_hash}
    return registry, json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    check_only = "--check" in sys.argv[1:]
    registry, rendered = render_registry()
    if check_only:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            raise SystemExit("frozen registry differs from typed catalog and contract")
    else:
        OUTPUT.write_text(rendered, encoding="utf-8")
    print(canonical_json({
        "catalog_hash": registry["catalog_hash"],
        "challenge_count": registry["challenge_count"],
        "contract_semantic_hash": registry["contract_semantic_hash"],
        "output": str(OUTPUT),
        "registry_hash": registry["registry_hash"],
        "registry_file_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
