"""Generate the contract-spec-only R5-S5 public authority contract v0.4."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import pathlib
import socket
import sys
import unicodedata
from typing import Any

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-implementation-contract-v0.4"
SCHEMA_VERSION = "2026-08-21.4"
SUBJECT = "subject-temporal-public-v1"
AEMH = "aemh-match-history-public-v1"
PARENT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
SEMANTIC_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1"
TEMPORAL_V01_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1"
TEMPORAL_V02_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2"
OUT_REL = pathlib.Path("artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4")
GENERATOR_REL = "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4.py"
VERIFIER_REL = "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4.py"

EXACT_PATHS = (
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_20260821_context.md",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_20260821.md",
    f"{OUT_REL}/public_api.json",
    f"{OUT_REL}/source_join_matrix.json",
    f"{OUT_REL}/invariant_error_matrix.json",
    f"{OUT_REL}/test_matrix.json",
    f"{OUT_REL}/manifest.json",
    GENERATOR_REL,
    VERIFIER_REL,
)

PRODUCER_ALLOWLIST = (
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py",
    "poc/medical_monitoring_ai_native_r5/tests/public_authority_runtime_fixtures.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_readonly_gate.py",
    "poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_public_authority_readonly_sha256.json",
)

AUTHORITY_PINS = {
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json": "92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270",
    "context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md": "23fed5b186057a79cd0ec43a7718e43934ebafdc8f62fd251077d4fb6891639d",
    "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/manifest.json": "66605a46c10e2aa4d36b06e566158666a08cdc92ec0e630364aad5b9ffb2385d",
    "context/medical_monitoring_r5_s5_semantic_authority_delta_acceptance_record_20260820.md": "bf50156fa82d825309fce72115ddf971fc4e0bdbd60936ea45e2362a6aa3eb4c",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/manifest.json": "e606e517c07dcb499657b418dbd16e4dacd98c7e7010770845dbccb91af59f97",
    "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_acceptance_record_20260820.md": "523351f1b5536b12c1a5be9251ad01f4e8b7a70f5088073a2333aefc241d1b79",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/manifest.json": "466b0ae605b83a57f0e184446db311beb05ff5e4e1998a7dc5be9bb44d2b7de8",
    "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2_acceptance_record_20260821.md": "d08b4ed27f9829db4cdcab0837f3623c244ee8c888cce699c55580621bd68ef4",
}


def read_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"object required: {path}")
    return value


def canonicalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", str(key)): canonicalize(item) for key, item in value.items()}
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def load_module(path: pathlib.Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_pins() -> tuple[dict[str, str], dict[str, Any]]:
    for relative, expected in AUTHORITY_PINS.items():
        actual = raw_sha(ROOT / relative)
        if actual != expected:
            raise SystemExit(f"STOP accepted pin drift: {relative}:{actual}")
    parent_manifest = read_json(PARENT_DIR / "manifest.json")
    typed = parent_manifest["source_file_sha256"]
    if not isinstance(typed, dict) or len(typed) != 15:
        raise SystemExit("STOP typed pin cardinality")
    for relative, expected in typed.items():
        if raw_sha(ROOT / relative) != expected:
            raise SystemExit(f"STOP typed pin drift: {relative}")
    temporal = read_json(TEMPORAL_V02_DIR / "manifest.json")
    if temporal["typed_source_pins"] != typed:
        raise SystemExit("STOP duplicate typed pin disagreement")
    return typed, temporal


def v02_generator() -> Any:
    return load_module(
        ROOT / "tools/generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
        "accepted_temporal_v02_generator_for_implementation_v04",
    )


def json_get(value: Any, pointer: str) -> Any:
    current = value
    for token in pointer.strip("/").split("/") if pointer != "/" else []:
        current = current[int(token)] if isinstance(current, list) else current[token]  # type: ignore[index]
    return current


def locate_exact_object(value: Any, keys: set[str], pointer: str = "") -> str | None:
    if isinstance(value, dict):
        if set(value) == keys:
            return pointer or "/"
        for key, item in value.items():
            found = locate_exact_object(item, keys, f"{pointer}/{key}")
            if found is not None:
                return found
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found = locate_exact_object(item, keys, f"{pointer}/{index}")
            if found is not None:
                return found
    return None


def locate_equal_object(value: Any, expected: dict[str, Any], pointer: str = "") -> str | None:
    if isinstance(value, dict):
        if value == expected:
            return pointer or "/"
        for key, item in value.items():
            found = locate_equal_object(item, expected, f"{pointer}/{key}")
            if found is not None:
                return found
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found = locate_equal_object(item, expected, f"{pointer}/{index}")
            if found is not None:
                return found
    return None


def output_packet(target: str, result: Any) -> dict[str, Any]:
    if target == SUBJECT:
        return result  # type: ignore[return-value]
    return result[1]  # type: ignore[index,return-value]


def replay_inventory() -> tuple[dict[str, Any], dict[str, Any]]:
    engine = v02_generator()
    recipes = read_json(TEMPORAL_V02_DIR / "emitter_recipe_registry.json")
    traces = read_json(TEMPORAL_V02_DIR / "trace_realization_registry.json")
    fixtures = read_json(TEMPORAL_V02_DIR / "full_graph_fixture_registry.json")
    parent = engine.parent_validator()
    subject_schema = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh_schema = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    bases = traces["base_authority_inputs"]
    baseline_results: dict[str, Any] = {}
    for row in fixtures["baselines"]:
        bundle = copy.deepcopy(row["authority_input"])
        target = bundle["target_contract"]
        result, outputs = engine.execute_recipe_dag(bundle, recipes, capture_outputs=True)
        if target == SUBJECT:
            issues = parent.validate_subject(result, subject_schema)
        else:
            previous, current = result
            issues = [*parent.validate_aemh(previous, aemh_schema, None), *parent.validate_aemh(current, aemh_schema, previous)]
        if issues:
            raise SystemExit(f"STOP v0.4 baseline closure: {target}:{issues}")
        baseline_results[target] = {"bundle": bundle, "result": result, "outputs": outputs}
    executed = []
    identities = set()
    positive_count = 0
    reject_count = 0
    for record in traces["records"]:
        base = copy.deepcopy(bases[record["base_input_ref"]])
        target = record["contract"]
        previous = None
        if record["expected_disposition"] == "accept":
            operations = [record["realized_mutation"], *record["linked_operations"]]
            operations = sorted(operations, key=lambda item: item["sequence"])
            for operation in operations:
                if json_get(base, operation["path"]) != operation["pre_value"]:
                    raise SystemExit(f"STOP trace pre: {record['source_case_ref']}")
                engine.apply_source_operation(base, operation)
                if json_get(base, operation["path"]) != operation["post_value"]:
                    raise SystemExit(f"STOP trace post: {record['source_case_ref']}")
            engine.reseal_bundle(base)
            result, outputs = engine.execute_recipe_dag(base, recipes, capture_outputs=True)
            if target == SUBJECT:
                graph = result
                issues = parent.validate_subject(graph, subject_schema)
            else:
                previous, graph = result
                issues = [*parent.validate_aemh(previous, aemh_schema, None), *parent.validate_aemh(graph, aemh_schema, previous)]
            positive_count += 1
        else:
            built = engine.execute_recipe_dag(base, recipes)
            if target == SUBJECT:
                graph = copy.deepcopy(built)
            else:
                previous, current = built
                graph = copy.deepcopy(current)
            parent.apply_mutation(graph, record["realized_mutation"])
            if record["reseal_mode"] != "none":
                preserve = any("EVALUATION_IDENTITY" in code for code in record["observed_ordered_issues"])
                if target == SUBJECT:
                    parent.reseal_subject_packet(graph, subject_schema, preserve_evaluation=preserve)
                else:
                    parent.reseal_aemh_packet(graph, aemh_schema, preserve_evaluation=preserve)
            issues = parent.validate_subject(graph, subject_schema) if target == SUBJECT else parent.validate_aemh(graph, aemh_schema, previous)
            outputs = {}
            reject_count += 1
        identity = digest({
            "base_input_content_identity": record["base_input_content_identity"],
            "realized_mutation": record["realized_mutation"],
            "linked_operations": record["linked_operations"],
            "lane": record["lane"],
        })
        disposition = "accept" if not issues else "reject"
        if identity != record["trace_identity"] or identity in identities:
            raise SystemExit(f"STOP trace identity: {record['source_case_ref']}")
        identities.add(identity)
        if issues != record["observed_ordered_issues"] or disposition != record["expected_disposition"]:
            raise SystemExit(f"STOP trace issues: {record['source_case_ref']}:{issues}")
        if graph["packet_content_hash"] != record["post_graph_content_hash"]:
            raise SystemExit(f"STOP trace graph: {record['source_case_ref']}")
        executed.append({
            "trace_identity": identity,
            "contract": target,
            "lane": record["lane"],
            "base_input_ref": record["base_input_ref"],
            "base_input_content_identity": record["base_input_content_identity"],
            "instance_selector": record["instance_selector"],
            "primary_operation": record["realized_mutation"],
            "linked_operations": record["linked_operations"],
            "reseal_mode": record["reseal_mode"],
            "reseal_order": record["reseal_order"],
            "actual_ordered_issues": issues,
            "future_validator_expected": {
                "ok": not issues,
                "primary_code": issues[0] if issues else None,
                "ordered_issue_codes": issues,
                "packet_emitted": not issues,
            },
            "post_packet_content_hash": graph["packet_content_hash"],
            "post_projection_content_hash": graph["projection"]["projection_content_hash"],
            "generator_executed": True,
            "producer_executed": False,
        })
    if len(executed) != 236 or len(identities) != 236 or positive_count != 10 or reject_count != 226:
        raise SystemExit(f"STOP inventory closure: {len(executed)}/{len(identities)}/{positive_count}/{reject_count}")
    return {
        "baselines": baseline_results,
        "runtime_specs": executed,
        "counts": {"subject": 143, "aemh": 93, "positive": positive_count, "reject": reject_count},
    }, {"recipes": recipes, "traces": traces, "fixtures": fixtures}


def py_type(type_name: str, enums: dict[str, list[str]]) -> str:
    if type_name.startswith("nullable:"):
        return f"Optional[{py_type(type_name[9:], enums)}]"
    if type_name.startswith("list:"):
        return f"tuple[{py_type(type_name[5:], enums)}, ...]"
    if type_name.startswith("union:"):
        return "Union[" + ", ".join(py_type(item, enums) for item in type_name[6:].split("|")) + "]"
    if type_name.startswith("enum:"):
        values = enums[type_name[5:]]
        return "Literal[" + ", ".join(repr(item) for item in values) + "]"
    return {"string": "str", "date": "str", "sha256": "str", "integer": "int", "boolean": "bool"}.get(type_name, type_name)


def v02_source_classes() -> list[dict[str, Any]]:
    schema = read_json(TEMPORAL_V02_DIR / "schema.json")
    names = {
        "AuthorityBundleV02", "SubjectFullGraphInputV02", "AEMHFullGraphInputV02", "AEMHDecisionInputV02",
        "AEMHThreadInputV02", "AxisInputV02", "CutoffEndpointBindingV02", "DomainInputV02", "EndpointInputV02",
        "IdentityScopeInputV02", "LocatorInputV02", "PhaseInputV02", "RevisionInputV02", "RiskInputV02",
        "ScopeInputV02", "SubjectEventInputV02", "VisitInputV02",
    }
    result = []
    for name, spec in schema["objects"].items():
        if name in names:
            result.append({
                "name": name,
                "decorator": "dataclasses.dataclass(frozen=True)",
                "fields": [[field, py_type(type_name, schema["enums"])] for field, type_name in spec["fields"].items()],
                "exact_field_order": list(spec["fields"]),
            })
    return result


def output_classes(schema: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for name, fields in schema["objects"].items():
        converted = []
        for field, spec in fields.items():
            type_name = py_type(spec["type"], schema["enums"])
            if spec["cardinality"] == "many":
                type_name = f"tuple[{type_name}, ...]"
            if spec["nullable"]:
                type_name = f"Optional[{type_name}]"
            converted.append([field, type_name])
        result.append({"name": name, "decorator": "dataclasses.dataclass(frozen=True)", "fields": converted, "exact_field_order": list(fields)})
    return result


def public_api() -> dict[str, Any]:
    subject_schema = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh_schema = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    common_names = {"PublicAuthorityReceipt", "PublicCutoffEndpoint", "PublicScopeIdentity", "PublicSourceLocator", "SourceRevisionContentPair", "VisibilityClosure"}
    subject_outputs = output_classes(subject_schema)
    aemh_outputs = output_classes(aemh_schema)
    source_common = v02_source_classes()
    common_inputs = [
        {
            "name": "SubjectTemporalSourceBundle", "decorator": "dataclasses.dataclass(frozen=True)",
            "fields": [
                ["monitoring_run", "mm_r1.domain.MonitoringRun"], ["temporal_spine", "mm_r1.domain.SubjectTemporalSpine"],
                ["d08_input", "mm_r4.d08_contracts.D08TypedInput"], ["visit_projection", "mm_r4.visit_schedule.VisitJourneyProjection"],
                ["semantic_records", "tuple[mm_r4.aemh.SemanticRecord, ...]"], ["risk_candidates", "tuple[mm_r2.risk.RiskCandidate, ...]"],
                ["risk_instances", "tuple[mm_r2.risk.RiskInstance, ...]"], ["s4_anchor", "mm_r5.s4_contracts.S4AcceptedAuthorityAnchor"],
                ["temporal_authority", "AuthorityBundleV02"],
            ], "temporal_source_variant": "SubjectFullGraphInputV02",
        },
        {
            "name": "AEMHMatchHistorySourceBundle", "decorator": "dataclasses.dataclass(frozen=True)",
            "fields": [
                ["current_result", "mm_r1.ae_mh.AEMHResult"], ["current_slice", "mm_r4.aemh.AEMHSliceResult"],
                ["d08_input", "mm_r4.d08_contracts.D08TypedInput"], ["semantic_records", "tuple[mm_r4.aemh.SemanticRecord, ...]"],
                ["risk_candidates", "tuple[mm_r2.risk.RiskCandidate, ...]"], ["risk_instances", "tuple[mm_r2.risk.RiskInstance, ...]"],
                ["risk_transitions", "tuple[mm_r2.risk.RiskTransition, ...]"], ["s4_anchor", "mm_r5.s4_contracts.S4AcceptedAuthorityAnchor"],
                ["temporal_authority", "AuthorityBundleV02"],
            ], "temporal_source_variant": "AEMHFullGraphInputV02",
        },
    ]
    issue_classes = [
        {"name": "PublicAuthorityValidationIssue", "decorator": "dataclasses.dataclass(frozen=True)", "fields": [["code", "str"], ["path", "str"], ["message", "str"], ["origin", "Literal['parent', 'semantic_delta', 'temporal_delta', 'consumer']"], ["priority", "int"]]},
        {"name": "PublicAuthorityValidationResult", "decorator": "dataclasses.dataclass(frozen=True)", "fields": [["ok", "bool"], ["primary_code", "Optional[str]"], ["issues", "tuple[PublicAuthorityValidationIssue, ...]"], ["packet_emitted", "bool"]]},
        {"name": "PublicAuthorityConstructionError", "decorator": "dataclasses.dataclass(frozen=True)", "base": "RuntimeError", "fields": [["result", "PublicAuthorityValidationResult"]], "partial_packet_forbidden": True},
    ]
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-api-v0.4", "schema_version": SCHEMA_VERSION, "contract_id": CONTRACT_ID,
        "python": {"minimum": "3.9", "frozen_dataclasses": True, "dynamic_attributes": False, "reflection": False, "mutable_fields": False, "free_mapping_fields": False, "untyped_fields": False},
        "internal_authority_pins": {"caller_may_supply": False, "manifest_refs_are_module_internal": True},
        "authority_bundle_contract": {"authority_scope": "synthetic_test_only", "execution_profile": "full_parent_graph", "temporal_v01_manifest_sha256": AUTHORITY_PINS[str(TEMPORAL_V01_DIR.relative_to(ROOT) / "manifest.json")], "temporal_v02_manifest_sha256": AUTHORITY_PINS[str(TEMPORAL_V02_DIR.relative_to(ROOT) / "manifest.json")], "exact_target_contracts": [SUBJECT, AEMH], "candidate_backfill_forbidden": True, "dual_plane_exact_cross_check": True},
        "modules": {
            "mm_r5.public_authority_common": {
                "input_classes": [*source_common, *common_inputs], "result_classes": issue_classes,
                "output_classes": [item for item in subject_outputs if item["name"] in common_names],
                "functions": ["canonical_json_bytes(value: object) -> bytes", "canonical_sha256(value: object) -> str", "validation_result(issues: Iterable[PublicAuthorityValidationIssue]) -> PublicAuthorityValidationResult"],
            },
            "mm_r5.subject_temporal_public": {
                "output_classes": [item for item in subject_outputs if item["name"] not in common_names],
                "functions": ["build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket", "validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle) -> PublicAuthorityValidationResult"],
            },
            "mm_r5.aemh_match_history_public": {
                "output_classes": [item for item in aemh_outputs if item["name"] not in common_names],
                "functions": ["build_aemh_match_history_authority(source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> AEMHMatchHistoryAuthorityPacket", "validate_aemh_match_history_authority(candidate: AEMHMatchHistoryAuthorityPacket, source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> PublicAuthorityValidationResult"],
            },
        },
        "exact_output_schema": {"subject_object_count": 17, "aemh_object_count": 13, "subject_schema_raw_sha256": raw_sha(PARENT_DIR / "subject_temporal_schema.json"), "aemh_schema_raw_sha256": raw_sha(PARENT_DIR / "aemh_match_history_schema.json"), "extra_serialization_leaves_forbidden": True},
        "result_semantics": {"success": {"ok": True, "primary_code": None, "issues": [], "packet_emitted": True}, "failure": {"ok": False, "primary_code": "issues[0].code", "issues": "nonempty total order", "packet_emitted": False}, "builder_zero_issue_only": True},
    }


def typed_selector(leaf: str) -> dict[str, str]:
    lowered = leaf.lower()
    candidates = [
        (("project",), "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "MonitoringRun", "project_id"),
        (("run",), "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "MonitoringRun", "run_id"),
        (("snapshot",), "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "ListingSnapshot", "snapshot_version"),
        (("revision",), "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "SourceRevision", "revision_id"),
        (("cutoff", "date", "endpoint", "timezone", "study_day"), "poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py", "TimeRef", "value"),
        (("locator", "source"), "poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py", "SourceLocator", "source_locator_id"),
        (("visit",), "poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule.py", "PlannedVisitMarker", "planned_visit_id"),
        (("event",), "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "TemporalEvent", "event_id"),
        (("risk", "severity"), "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py", "S4AcceptedRiskIdentity", "risk_ref"),
        (("thread", "match", "candidate", "fact", "history", "evidence"), "poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py", "AEMHResult", "reported_facts"),
        (("domain", "subtype"), "poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py", "SemanticRecord", "role"),
        (("subject", "site", "spine"), "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py", "S4AcceptedRiskIdentity", "subject_ref"),
    ]
    for tokens, path, class_name, field in candidates:
        if any(token in lowered for token in tokens):
            return {"path": path, "class": class_name, "field": field, "selector": f"{class_name}.{field}"}
    return {"path": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py", "class": "D08TypedInput", "field": "scope_binding", "selector": "D08TypedInput.scope_binding"}


def recipe_for_object(target: str, object_type: str) -> str:
    if target == SUBJECT:
        groups = {
            "identity_cutoff": {"PublicScopeIdentity", "PublicCutoffEndpoint"},
            "locators_revisions": {"PublicSourceLocator", "SourceRevisionContentPair", "VisibilityClosure"},
            "temporal_members": {"TemporalVisit", "TemporalEvent", "TemporalRiskAnchor", "TemporalPhaseBand", "TemporalDateEndpoint"},
            "domains_pending_membership": {"TemporalDomainTrack", "TemporalPendingDateItem", "TemporalMembershipIndex"},
            "axis": {"TemporalAxisBasis"}, "projection": {"SubjectTemporalPublicProjection"},
            "receipt": {"PublicAuthorityReceipt"}, "packet": {"SubjectTemporalAuthorityPacket"},
        }
        prefix = "recipe.v02.subject_"
    else:
        groups = {
            "identity_locators_revisions": {"PublicScopeIdentity", "PublicSourceLocator", "SourceRevisionContentPair"},
            "current_threads": {"AEMHMatchHistoryEntry", "AEMHIdentityEvidence", "AEMHMatchThread"},
            "current_membership_prefix_cutoff": {"AEMHHistoryMembershipIndex", "AEMHThreadPrefixAnchor", "PublicCutoffEndpoint"},
            "projection": {"AEMHMatchHistoryPublicProjection"},
            "receipt": {"PublicAuthorityReceipt", "VisibilityClosure"}, "packet": {"AEMHMatchHistoryAuthorityPacket"},
        }
        prefix = "recipe.v02.aemh_"
    for phase, names in groups.items():
        if object_type in names:
            return prefix + phase
    raise ValueError(f"no recipe for {target}:{object_type}")


def source_join_matrix(runtime: dict[str, Any], accepted: dict[str, Any]) -> dict[str, Any]:
    recipes = accepted["recipes"]
    by_id = {row["recipe_id"]: row for row in recipes["executable_v02_recipes"]}
    rows = []
    ordinal = 0
    for target, schema_name in ((SUBJECT, "subject_temporal_schema.json"), (AEMH, "aemh_match_history_schema.json")):
        schema = read_json(PARENT_DIR / schema_name)
        baseline = runtime["baselines"][target]
        packet = output_packet(target, baseline["result"])
        outputs = baseline["outputs"]
        local_rows = []
        for object_type, fields in schema["objects"].items():
            final_base = locate_exact_object(packet, set(fields))
            virtual_cutoff = target == SUBJECT and object_type == "PublicCutoffEndpoint"
            if final_base is None and not virtual_cutoff:
                raise SystemExit(f"STOP final object reachability: {target}:{object_type}")
            if virtual_cutoff:
                binding = baseline["bundle"]["source"]["cutoff_binding"]
                virtual_value = {
                    "state": binding["state"], "exact_date": binding["exact_date"],
                    "source_locator_refs": sorted(binding["source_locator_refs"]),
                }
                virtual_value["cutoff_content_hash"] = digest(virtual_value)
                final_base = "/$common/PublicCutoffEndpoint"
            recipe_id = recipe_for_object(target, object_type)
            recipe = by_id[recipe_id]
            output_ref = recipe["nodes"][1]["outputs"][0]
            stage_value = outputs[output_ref]["value"]
            aemh_current_paths = {
                "AEMHMatchHistoryAuthorityPacket": "/current",
                "PublicScopeIdentity": "/current_identity",
                "PublicSourceLocator": "/current_locators/0",
                "SourceRevisionContentPair": "/current_pairs/0",
            }
            if target == AEMH and object_type in aemh_current_paths:
                stage_base = aemh_current_paths[object_type]
            else:
                stage_base = locate_exact_object(stage_value, set(fields)) if not virtual_cutoff else "/cutoff"
            if stage_base is None:
                raise SystemExit(f"STOP recipe object reachability: {recipe_id}:{object_type}")
            if not virtual_cutoff:
                stage_object = json_get(stage_value, stage_base)
                final_base = locate_equal_object(packet, stage_object)
                if final_base is None:
                    raise SystemExit(f"STOP final-stage object equality: {target}:{object_type}")
            ordered_fields = sorted(fields, key=lambda name: (name.endswith(("_hash", "_id", "_ref")), name))
            prior = []
            for field in ordered_fields:
                ordinal += 1
                spec = fields[field]
                packet_pointer = f"{final_base.rstrip('/')}/{field}"
                final_pointer = f"/{target}{packet_pointer}"
                recipe_pointer = f"{stage_base.rstrip('/')}/{field}" if not virtual_cutoff else stage_base
                final_value = virtual_value[field] if virtual_cutoff else json_get(packet, packet_pointer)
                recipe_value = virtual_value[field] if virtual_cutoff else json_get(stage_value, recipe_pointer)
                if final_value != recipe_value:
                    raise SystemExit(f"STOP join value drift: {target}:{object_type}.{field}")
                qualified = f"{target}::{object_type}.{field}"
                direct_pointers = recipe["nodes"][0]["params"]["authority_input_pointers"]
                v02_selector = direct_pointers[0] if direct_pointers else "/source"
                semantic = qualified in {
                    f"{SUBJECT}::TemporalEvent.domain", f"{SUBJECT}::TemporalEvent.subtype",
                    f"{SUBJECT}::TemporalRiskAnchor.risk_type_zh", f"{SUBJECT}::TemporalRiskAnchor.severity",
                }
                local_rows.append({
                    "ordinal": ordinal, "contract": target, "object_type": object_type, "leaf": field,
                    "qualified_leaf": qualified, "output_json_pointer": final_pointer, "output_type": spec["type"],
                    "nullable": spec["nullable"], "cardinality": spec["cardinality"],
                    "ordering_rule": "canonical sorted unique" if spec["cardinality"] == "many" else "scalar exact",
                    "key_selector": f"{object_type}.{next(iter(fields))}", "authority_source_kind": "dual_typed_and_accepted_v02",
                    "typed_source_selector": typed_selector(field), "v02_authority_selector": {"root_type": "AuthorityBundleV02", "source_variant": "SubjectFullGraphInputV02" if target == SUBJECT else "AEMHFullGraphInputV02", "json_pointer": v02_selector},
                    "selector_cardinality": "ordered-many" if spec["cardinality"] == "many" else "zero-or-one" if spec["nullable"] else "exact-one",
                    "selector_zero_policy": "emit null only when accepted nullable; otherwise fail closed",
                    "selector_many_policy": "fail closed unless cardinality is ordered-many and keys are unique",
                    "reducer_id": recipe["nodes"][0]["op"], "recipe_id": recipe_id,
                    "recipe_content_hash": recipe["recipe_content_hash"], "recipe_node_id": recipe["nodes"][1]["node_id"],
                    "recipe_node_output_ref": output_ref, "recipe_output_json_pointer": recipe_pointer,
                    "recipe_leaf_selector": {"virtual_common_type": "PublicCutoffEndpoint", "field": field, "source": "/source/cutoff_binding", "hash_recipe": "canonical_sha256(fields excluding cutoff_content_hash)"} if virtual_cutoff else None,
                    "recipe_registry_content_hash": recipes["registry_content_hash"],
                    "dependency_output_leaves": list(prior),
                    "dependency_recipe_nodes": [ref.removesuffix(".sealed") + ".n02" for ref in recipe["nodes"][0]["params"]["prior_recipe_output_refs"]],
                    "construction_phase": recipe["nodes"][0]["params"]["phase"],
                    "parent_schema_ref": f"artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/{schema_name}#/objects/{object_type}/{field}",
                    "semantic_ref": "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/schema.json#/future_bundle_integration/leaf_projection" if semantic else None,
                    "expected_plane_ref": f"artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json#/baselines/{0 if target == SUBJECT else 1}",
                    "fail_closed_codes": ["PUB_TYPE_MISMATCH", "PUB_HASH_MISMATCH"],
                    "candidate_backfill_forbidden": True, "mirror_forbidden": True,
                    "generator_join_executed": True,
                })
                prior.append(qualified)
        rows.extend(local_rows)
    if len(rows) != 272 or len({row["qualified_leaf"] for row in rows}) != 272 or len({row["output_json_pointer"] for row in rows}) != 272:
        raise SystemExit("STOP 272 join bijection")
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-source-join-matrix-v0.4", "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID, "row_count": 272, "subject_count": 156, "aemh_count": 116,
        "alias_count": 0, "unexplained_count": 0, "rows": rows,
        "dag_contract": {"independent_per_contract": True, "acyclic": True, "self_or_future_edges": False, "recipe_count": 16, "recipe_node_count": 32},
        "forbidden": ["target_output_path", "candidate output mirror", "example output mirror", "fixture output mirror", "prose resolver", "class-wide closure", "nearest fallback", "temporal constant override", "D07 OTHER", "S4 value transfer"],
    }


def invariant_error_matrix() -> dict[str, Any]:
    subject = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    parent_registry = read_json(PARENT_DIR / "challenge_registry.json")
    semantic_schema = read_json(SEMANTIC_DIR / "schema.json")
    semantic_challenges = read_json(SEMANTIC_DIR / "challenge_registry.json")
    temporal_challenges = read_json(TEMPORAL_V01_DIR / "challenge_registry.json")
    parent_codes = list(dict.fromkeys(subject["error_codes"] + aemh["error_codes"]))
    semantic_codes = list(semantic_schema["typed_error_priority"])
    temporal_codes = sorted({row["expected_error"] for row in temporal_challenges["cases"]})
    parent_cases = parent_registry["inherited_cases"] + parent_registry["public_authority_specific_cases"]
    semantic_cases = semantic_challenges["cases"]
    temporal_cases = temporal_challenges["cases"]
    records = []
    priority = 0
    for origin, codes, cases in (("parent", parent_codes, parent_cases), ("semantic_delta", semantic_codes, semantic_cases), ("temporal_delta", temporal_codes, temporal_cases)):
        for code in codes:
            priority += 1
            if origin == "parent":
                matches = [row for row in cases if row["expected_typed_outcome_or_error"] == f"reject:{code}"]
                contracts = sorted({row["contract"] for row in matches}) or [name for name, schema in ((SUBJECT, subject), (AEMH, aemh)) if code in schema["error_codes"]]
                path = matches[0]["single_mutation"]["path"] if matches else "/"
                invariant = matches[0]["stage_oracle_contract"]["rule_id"] if matches else f"accepted parent error code {code}"
            elif origin == "semantic_delta":
                matches = [row for row in cases if row["expected_typed_error"] == code]
                contracts = [SUBJECT]
                path = matches[0]["mutation"].get("path", matches[0]["mutation"].get("target", "/semantic")) if matches else "/semantic"
                invariant = matches[0]["non_llm_oracle"] if matches else f"accepted semantic typed error {code}"
            else:
                matches = [row for row in cases if row["expected_error"] == code]
                contracts = sorted({row["covered_leaf"].split("::", 1)[0] for row in matches if row.get("covered_leaf")}) or [SUBJECT, AEMH]
                path = matches[0]["covered_leaf"] if matches and matches[0].get("covered_leaf") else "/temporal"
                invariant = matches[0]["required_non_llm_anchor"] if matches else f"accepted temporal error {code}"
            records.append({"code": code, "priority": priority, "origin": origin, "contract": contracts, "invariant": invariant, "path": path, "message_semantics": f"{origin}:{code}:fail_closed"})
    if (len(parent_codes), len(semantic_codes), len(temporal_codes), len(records)) != (81, 49, 62, 192):
        raise SystemExit("STOP error union closure")
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-invariant-error-matrix-v0.4", "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID, "counts": {"parent": 81, "semantic_delta": 49, "temporal_delta": 62, "union": 192},
        "dedup_key": ["code", "path", "origin", "message"], "total_order": ["priority", "path", "code", "origin", "message"],
        "primary_code": "first ordered issue code", "any_issue_forbids_packet": True, "errors": records,
        "temporal_v02_closure_failures": "STOP_not_public_error",
    }


def apply_mutation(document: dict[str, Any], mutation: dict[str, Any]) -> None:
    parts = str(mutation["path"]).strip("/").split("/")
    current: Any = document
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]  # type: ignore[index]
    key = parts[-1]
    if mutation["op"] == "replace":
        if isinstance(current, list):
            current[int(key)] = copy.deepcopy(mutation["value"])
        else:
            current[key] = copy.deepcopy(mutation["value"])  # type: ignore[index]
    elif mutation["op"] == "reverse":
        target = current[int(key)] if isinstance(current, list) else current[key]  # type: ignore[index]
        target.reverse()
    else:
        raise ValueError(f"unsupported governance mutation {mutation['op']}")


def governance_probes() -> list[dict[str, Any]]:
    parent_registry = read_json(PARENT_DIR / "challenge_registry.json")
    rows = [row for row in parent_registry["inherited_cases"] + parent_registry["public_authority_specific_cases"] if str(row.get("base_input_key", "")).endswith("_artifact")]
    parent = load_module(ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py", "accepted_parent_governance_for_v04")
    parent_exact = read_json(ROOT / "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json")
    result = []
    for row in rows:
        base = row["base_input_key"]
        if base == "exact_overlay_artifact":
            candidate = read_json(PARENT_DIR / "exact_overlay.json"); apply_mutation(candidate, row["single_mutation"]); issues = parent.overlay_validation_issues(candidate, parent_exact)
        elif base == "source_matrix_artifact":
            candidate = read_json(PARENT_DIR / "source_matrix.json"); apply_mutation(candidate, row["single_mutation"]); issues = parent.source_matrix_validation_issues(candidate)
        else:
            candidate = read_json(PARENT_DIR / "manifest.json"); apply_mutation(candidate, row["single_mutation"]); candidate["manifest_content_hash"] = parent.canonical_hash({key: value for key, value in candidate.items() if key != "manifest_content_hash"}); issues = parent.manifest_contract_validation_issues(candidate)
        expected = row["expected_typed_outcome_or_error"].split(":", 1)[1]
        if expected not in issues:
            raise SystemExit(f"STOP governance probe {row['case_id']}:{issues}")
        result.append({"probe_identity": digest({"base": base, "mutation": row["single_mutation"]}), "base_artifact": base, "mutation": row["single_mutation"], "actual_ordered_issues": issues, "required_issue": expected, "generator_executed": True})
    if len(result) != 22:
        raise SystemExit("STOP governance probe count")
    return result


def test_matrix(runtime: dict[str, Any], governance: list[dict[str, Any]], errors: dict[str, Any]) -> dict[str, Any]:
    error_by_code = {row["code"]: row for row in errors["errors"]}
    specs = copy.deepcopy(runtime["runtime_specs"])
    for spec in specs:
        issue_objects = [
            {
                "code": code, "path": error_by_code[code]["path"],
                "message": error_by_code[code]["message_semantics"],
                "origin": error_by_code[code]["origin"], "priority": error_by_code[code]["priority"],
            }
            for code in spec["actual_ordered_issues"]
        ]
        spec["actual_ordered_issue_objects"] = issue_objects
        spec["future_validator_expected"]["ordered_issues"] = issue_objects
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-test-matrix-v0.4", "schema_version": SCHEMA_VERSION, "contract_id": CONTRACT_ID,
        "current_contract_verification": {
            "spec_count": 236, "unique_trace_count": 236, "alias_count": 0, "subject_count": 143, "aemh_count": 93,
            "positive_count": 10, "reject_count": 226, "artifact_governance_probe_count": 22,
            "runtime_specifications": specs, "artifact_governance_probes": governance,
            "all_rejects_compare_complete_ordered_issue_sequence": True,
        },
        "future_producer_acceptance": {
            "create_only_allowlist": list(PRODUCER_ALLOWLIST), "files_present": False, "producer_executed": False,
            "runtime_tests_executed": False, "ast_executed": False, "sensitivity_executed": False, "isolation_executed": False,
            "ast_policy": {"dynamic_code": "forbidden", "reflection": "forbidden", "file_io": "forbidden", "network": "forbidden", "subprocess": "forbidden", "case_label_sentinel_branch": "forbidden"},
            "sensitivity_vectors": ["subject.source", "subject.temporal_authority", "subject.d08", "subject.visit", "subject.risk", "aemh.source", "aemh.previous", "aemh.temporal_authority", "aemh.decision", "common.canonicalization"],
            "isolation_command": "python3 -I -B <future isolated producer probe>",
        },
        "contract_spec_only": True, "producer_executed": False, "evidence_created": False,
    }


def context_markdown() -> bytes:
    return b"""# R5-S5 public authority implementation contract v0.4 context\n\nState: `CANDIDATE_UNACCEPTED`\n\nThis nine-file contract projects only the accepted chain public parent v0.1 -> semantic delta v0.1 -> temporal v0.1 primitives -> temporal v0.2 full-parent-graph. Rejected implementation contracts v0.1-v0.3 are immutable negative evidence and supply no expected plane, alias, resolver, authority value or acceptance implication.\n\nThe generator executes 2/2 parent-valid baselines, 10/10 positive post-graphs, 236 unique traces with zero aliases, 226 complete ordered rejects, 272 dual-plane joins, 16 recipes/32 nodes and 22 artifact-governance probes. The future eleven producer paths remain absent and locked. No producer, runtime test, evidence, S5, UI/browser, real project/model, clinical authority, product, production, medical-writing state or port 8911 is accepted.\n"""


def review_markdown() -> bytes:
    return b"""# R5-S5 public authority implementation contract v0.4 author review\n\nDisposition: `CANDIDATE_FOR_FRESH_ISOLATED_REVIEW`. This author does not accept the candidate.\n\nThe candidate freezes Python >=3.9 frozen dataclasses and exact public signatures, rebuilds the parent 17/13 object schemas, makes accepted manifest references module-internal, and requires exact cross-checking between real typed inputs and one accepted temporal v0.2 AuthorityBundleV02. Candidate output cannot authorize or backfill source authority.\n\nAll 236 specifications are executed during generation; the independent verifier must replay them through its separate accepted IndependentExecutor, compare all 226 full ordered issue sequences, and execute 272 recipe-output joins. Future producer AST, sensitivity, isolation and runtime-test gates are frozen but truthfully unexecuted while all eleven producer files are absent.\n\nOnly a later fresh isolated reviewer may accept one immutable v0.4 manifest. Such acceptance can unlock only the exact eleven-file create-only producer stage.\n"""


def build_manifest(outputs: dict[str, bytes], typed: dict[str, str], temporal: dict[str, Any], joins: dict[str, Any], tests: dict[str, Any]) -> dict[str, Any]:
    rejected = {
        "v0_1": temporal["rejected_v01_v02_negative_evidence_only"]["v0_1"],
        "v0_2": temporal["rejected_v01_v02_negative_evidence_only"]["v0_2"],
        "v0_3": temporal["rejected_v03_negative_evidence_only"],
        "rejection_records": {
            temporal["rejected_v01_v02_negative_evidence_only"]["rejection_record_path"]: temporal["rejected_v01_v02_negative_evidence_only"]["rejection_record_raw_sha256"],
            "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_rejection_record_20260820.md": "11b2baf15c1c89cc22a0a052c2e591ba6ce88e79cf660535578f6ba07e98099a",
        },
    }
    pre = {
        "schema": "medical-monitoring-r5-s5-public-authority-implementation-contract-manifest-v0.4", "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID, "status": "candidate_unaccepted", "contract_spec_only": True, "non_clinical": True,
        "authority_scope": "synthetic_test_only", "execution_profile": "full_parent_graph",
        "exact_nine_paths": list(EXACT_PATHS),
        "file_raw_sha256": {path: hashlib.sha256(outputs[path]).hexdigest() for path in EXACT_PATHS if path != f"{OUT_REL}/manifest.json"},
        "manifest_self_raw_sha256": "external_fresh_review_pin_required",
        "authority_chain_pins": AUTHORITY_PINS, "typed_source_pins": typed,
        "temporal_v02_nine_file_pins": {**temporal["file_raw_sha256"], str(TEMPORAL_V02_DIR.relative_to(ROOT) / "manifest.json"): AUTHORITY_PINS[str(TEMPORAL_V02_DIR.relative_to(ROOT) / "manifest.json")]},
        "rejected_implementation_snapshots_negative_evidence_only": rejected,
        "protected_pins": temporal["protected_accepted_pins"],
        "temporal_v02_identities": {
            "schema_baseline_content_hash": temporal["schema_baseline_content_hash"],
            "emitter_recipe_registry_content_hash": temporal["emitter_recipe_registry_content_hash"],
            "full_graph_fixture_registry_content_hash": temporal["full_graph_fixture_registry_content_hash"],
            "trace_realization_registry_content_hash": temporal["trace_realization_registry_content_hash"],
        },
        "counts": {
            "spec_count": 236, "unique_trace_count": 236, "alias_count": 0, "positive_count": 10, "reject_count": 226,
            "leaf_count": joins["row_count"], "recipe_count": 16, "recipe_node_count": 32, "artifact_governance_probe_count": 22,
        },
        "producer_executed": False, "runtime_tests_executed": False, "evidence_created": False,
        "future_producer_allowlist": list(PRODUCER_ALLOWLIST), "port_8911_must_be_stopped": True,
        "absence_required": {"producer_files": True, "s5_files": True, "bytecode_and_cache": True},
        "test_matrix_content_hash": digest(tests), "source_join_matrix_content_hash": digest(joins),
        "acceptance_token_forbidden": True, "self_acceptance": False,
        "manifest_hash_recipe": "sha256(canonical_json(all fields except manifest_content_hash))",
    }
    return {**pre, "manifest_content_hash": digest(pre)}


def port_stopped() -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", 8911)) != 0


def render() -> dict[str, bytes]:
    typed, temporal = check_pins()
    if not port_stopped():
        raise SystemExit("STOP port 8911 listening")
    runtime, accepted = replay_inventory()
    api = public_api()
    joins = source_join_matrix(runtime, accepted)
    errors = invariant_error_matrix()
    governance = governance_probes()
    tests = test_matrix(runtime, governance, errors)
    outputs = {
        EXACT_PATHS[0]: context_markdown(), EXACT_PATHS[1]: review_markdown(),
        EXACT_PATHS[2]: pretty(api), EXACT_PATHS[3]: pretty(joins), EXACT_PATHS[4]: pretty(errors), EXACT_PATHS[5]: pretty(tests),
        GENERATOR_REL: (ROOT / GENERATOR_REL).read_bytes(), VERIFIER_REL: (ROOT / VERIFIER_REL).read_bytes(),
    }
    manifest = build_manifest(outputs, typed, temporal, joins, tests)
    outputs[EXACT_PATHS[6]] = pretty(manifest)
    return outputs


def write_or_check(outputs: dict[str, bytes], output_root: pathlib.Path, check: bool) -> None:
    for relative, data in outputs.items():
        path = output_root / relative
        if check:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit(f"drift: {relative}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.resolve() not in {(output_root / item).resolve() for item in EXACT_PATHS}:
                raise SystemExit(f"write boundary: {path}")
            path.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output-root", type=pathlib.Path, default=ROOT)
    args = parser.parse_args()
    outputs = render()
    write_or_check(outputs, args.output_root.resolve(), args.check)
    print(json.dumps({"status": "PASS", "specs": "236/236/0", "positives": "10/10", "rejects": "226/226", "joins": "272/272", "recipes": "16/32", "governance": "22/22", "producer_executed": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
