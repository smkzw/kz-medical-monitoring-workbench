"""Independent verifier for temporal projection authority delta v0.2.

This file does not import the v0.2 generator.  It independently reconstructs
the graphs, invokes the accepted parent validator and challenges governance.
"""

from __future__ import annotations

import ast
import copy
import datetime as dt
import hashlib
import importlib.util
import inspect
import json
import os
import pathlib
import socket
import subprocess
import sys
import unicodedata
from typing import Any, NoReturn

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2"
MANIFEST = OUT / "manifest.json"
SCHEMA = OUT / "schema.json"
EMITTERS = OUT / "emitter_recipe_registry.json"
FIXTURES = OUT / "full_graph_fixture_registry.json"
TRACES = OUT / "trace_realization_registry.json"
GENERATOR = ROOT / "tools/generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py"
VERIFIER = pathlib.Path(__file__).resolve()
PARENT_VALIDATOR = ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py"
SUBJECT_SCHEMA = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json"
AEMH_SCHEMA = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json"
SUBJECT = "subject-temporal-public-v1"
AEMH = "aemh-match-history-public-v1"
CONTRACT_ID = "r5-s5-temporal-projection-authority-delta-v0.2"
SCHEMA_VERSION = "2026-08-21.1"
AUTHORITY_SCOPE = "synthetic_test_only"
V01_MANIFEST_SHA256 = "e606e517c07dcb499657b418dbd16e4dacd98c7e7010770845dbccb91af59f97"
PARENT_VERSION = "2026-08-19.1"
PROFILE = "full_parent_graph"
AUDIENCE = "contract.s4.1"
DOMAINS = ["ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure", "symptom_efficacy", "protocol_compliance"]
EXACT_PATHS = (
    "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2_20260821_context.md",
    "reviews/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2_20260821.md",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/manifest.json",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/schema.json",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/emitter_recipe_registry.json",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/trace_realization_registry.json",
    "tools/generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
    "tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
)
PARENT_MANIFEST = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json"
PARENT_CHALLENGES = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/challenge_registry.json"
TYPED_SOURCE_PINS = json.loads(PARENT_MANIFEST.read_text(encoding="utf-8"))["source_file_sha256"]
if len(TYPED_SOURCE_PINS) != 15:
    raise RuntimeError("accepted parent typed-source pin cardinality drift")


def fail(message: str) -> NoReturn:
    raise SystemExit(f"VERIFY_FAIL: {message}")


def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonicalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [canonicalize(row) for row in value]
    if isinstance(value, tuple):
        return [canonicalize(row) for row in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key in sorted(value):
            normalized = unicodedata.normalize("NFC", key)
            if normalized in result:
                fail("normalized duplicate key")
            result[normalized] = canonicalize(value[key])
        return result
    fail(f"unsupported canonical type {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_date(value: str) -> bool:
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_typed(value: Any, type_name: str, schema: dict[str, Any], path: str = "$") -> list[str]:
    if type_name.startswith("nullable:"):
        return [] if value is None else validate_typed(value, type_name[9:], schema, path)
    if type_name.startswith("list:"):
        if not isinstance(value, list):
            return [f"{path}:expected_list"]
        return [issue for index, item in enumerate(value) for issue in validate_typed(item, type_name[5:], schema, f"{path}[{index}]")]
    if type_name.startswith("enum:"):
        enum_name = type_name[5:]
        return [] if value in schema["enums"][enum_name] else [f"{path}:enum:{enum_name}"]
    if type_name.startswith("union:"):
        attempts = [validate_typed(value, name, schema, path) for name in type_name[6:].split("|")]
        return [] if any(not attempt for attempt in attempts) else [f"{path}:union"]
    if type_name in schema["objects"]:
        descriptor = schema["objects"][type_name]
        if not isinstance(value, dict):
            return [f"{path}:expected_object:{type_name}"]
        fields = descriptor["fields"]
        issues = []
        extra = set(value) - set(fields)
        missing = set(descriptor["required"]) - set(value)
        if extra:
            issues.append(f"{path}:extra_keys:{','.join(sorted(extra))}")
        if missing:
            issues.append(f"{path}:missing_keys:{','.join(sorted(missing))}")
        for key in sorted(set(value) & set(fields)):
            issues.extend(validate_typed(value[key], fields[key], schema, f"{path}.{key}"))
        return issues
    if type_name == "any":
        try:
            canonical_bytes(value)
        except (TypeError, ValueError):
            return [f"{path}:noncanonical_any"]
        return []
    checks = {
        "string": lambda item: isinstance(item, str),
        "boolean": lambda item: isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "object": lambda item: isinstance(item, dict),
        "sha256": lambda item: isinstance(item, str) and len(item) == 64 and all(char in "0123456789abcdef" for char in item),
        "date": lambda item: isinstance(item, str) and valid_date(item),
    }
    if type_name not in checks:
        return [f"{path}:unknown_type:{type_name}"]
    return [] if checks[type_name](value) else [f"{path}:type:{type_name}"]


def authority_issues(bundle: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    issues = validate_typed(bundle, "AuthorityBundleV02", schema)
    if issues:
        return issues
    constants = {
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "authority_scope": AUTHORITY_SCOPE,
        "execution_profile": PROFILE,
        "temporal_v01_manifest_sha256": V01_MANIFEST_SHA256,
    }
    for key, expected in constants.items():
        if bundle[key] != expected:
            issues.append(f"$.{key}:constant")
    source_type = "SubjectFullGraphInputV02" if bundle["target_contract"] == SUBJECT else "AEMHFullGraphInputV02"
    source_variant_issues = validate_typed(bundle["source"], source_type, schema, "$.source")
    issues.extend(source_variant_issues)
    if source_variant_issues:
        return issues
    if bundle["bundle_content_identity"] != digest({key: value for key, value in bundle.items() if key != "bundle_content_identity"}):
        issues.append("$.bundle_content_identity:hash")
    if bundle["target_contract"] == SUBJECT:
        source = bundle["source"]
        if len(source["events"]) != 2 or len(source["domain_applicability"]) != 8 or [row["domain"] for row in source["domain_applicability"]] != DOMAINS:
            issues.append("$.source:subject_cardinality")
        if source["axis"]["study_day_enabled"] != (source["axis"]["anchor_event_ref"] is not None):
            issues.append("$.source.axis:study_day_cardinality")
    else:
        source = bundle["source"]
        if len(source["thread_specs"]) != 2 or {row["domain"] for row in source["thread_specs"]} != {"ae", "mh"}:
            issues.append("$.source:thread_cardinality")
    return issues


def typed_source_pin_issues(pin_map: Any) -> list[str]:
    if not isinstance(pin_map, dict) or set(pin_map) != set(TYPED_SOURCE_PINS):
        return ["TPA_V02_TYPED_SOURCE_PIN_SET"]
    issues = []
    for rel, expected in sorted(TYPED_SOURCE_PINS.items()):
        if pin_map.get(rel) != expected:
            issues.append(f"TPA_V02_TYPED_SOURCE_PIN_VALUE:{rel}")
        elif raw_sha(ROOT / rel) != expected:
            issues.append(f"TPA_V02_TYPED_SOURCE_FILE_DRIFT:{rel}")
    return issues


def pin_surface_issues(manifest: dict[str, Any]) -> list[str]:
    issues = typed_source_pin_issues(manifest.get("typed_source_pins"))
    accepted_parent_pins = manifest.get("accepted_parent_pins")
    if not isinstance(accepted_parent_pins, dict) or "source_file_sha256" in accepted_parent_pins:
        issues.append("TPA_V02_DUPLICATE_TYPED_SOURCE_PIN_SURFACE")
    return issues


def sealed(value: dict[str, Any], hash_field: str) -> dict[str, Any]:
    result = copy.deepcopy(value); result.pop(hash_field, None); result[hash_field] = digest(result); return result


def parent_module() -> Any:
    spec = importlib.util.spec_from_file_location("accepted_parent_validator_independent", PARENT_VALIDATOR)
    if spec is None or spec.loader is None:
        fail("parent validator loader")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def pointer_get(document: Any, pointer: str) -> Any:
    value = document
    for part in pointer.strip("/").split("/") if pointer != "/" else []:
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def pointer_replace(document: Any, pointer: str, replacement: Any) -> None:
    parts = pointer.strip("/").split("/")
    parent = document
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    final = parts[-1]
    if isinstance(parent, list): parent[int(final)] = copy.deepcopy(replacement)
    else: parent[final] = copy.deepcopy(replacement)


def apply_source_operation(authority_bundle: dict[str, Any], operation: dict[str, Any]) -> None:
    if operation["op"] == "replace":
        pointer_replace(authority_bundle, operation["path"], operation["value"])
    elif operation["op"] == "append":
        target = pointer_get(authority_bundle, operation["path"])
        if not isinstance(target, list): fail("source append target")
        target.append(copy.deepcopy(operation["value"]))
    else:
        fail(f"source operation {operation['op']}")


def reseal_bundle(authority_bundle: dict[str, Any]) -> None:
    authority_bundle["bundle_content_identity"] = digest({key: value for key, value in authority_bundle.items() if key != "bundle_content_identity"})


def independent_replay_source_operations(base: dict[str, Any], operations: list[dict[str, Any]], expected_identity: str) -> tuple[dict[str, Any], list[str]]:
    transformed = json.loads(canonical_bytes(base))
    issues = []
    for expected_sequence, operation in enumerate(operations, start=1):
        if operation.get("sequence") != expected_sequence:
            return transformed, [f"TPA_V02_SOURCE_OPERATION_ORDER:{expected_sequence}"]
        try:
            actual_pre = copy.deepcopy(pointer_get(transformed, operation["path"]))
        except (KeyError, IndexError, TypeError):
            return transformed, [f"TPA_V02_SOURCE_OPERATION_PATH:{operation.get('path')}"]
        if actual_pre != operation.get("pre_value"):
            return transformed, [f"TPA_V02_SOURCE_OPERATION_PRE:{operation['path']}"]
        apply_source_operation(transformed, operation)
        if pointer_get(transformed, operation["path"]) != operation.get("post_value"):
            return transformed, [f"TPA_V02_SOURCE_OPERATION_POST:{operation['path']}"]
    reseal_bundle(transformed)
    if transformed["bundle_content_identity"] != expected_identity:
        issues.append("TPA_V02_SOURCE_OPERATION_FINAL_IDENTITY")
    return transformed, issues


def independent_structural_diff(before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
    if type(before) is not type(after):
        return [{"op": "replace", "path": path or "/", "value": copy.deepcopy(after)}]
    if isinstance(before, dict):
        if set(before) != set(after):
            return [{"op": "replace", "path": path or "/", "value": copy.deepcopy(after)}]
        return [operation for key in sorted(before) for operation in independent_structural_diff(before[key], after[key], f"{path}/{key}")]
    if isinstance(before, list):
        if len(after) >= len(before) and after[:len(before)] == before:
            return [{"op": "append", "path": path or "/", "value": copy.deepcopy(value)} for value in after[len(before):]]
        if len(before) == len(after):
            return [operation for index, (left, right) in enumerate(zip(before, after)) for operation in independent_structural_diff(left, right, f"{path}/{index}")]
        return [{"op": "replace", "path": path or "/", "value": copy.deepcopy(after)}]
    return [] if before == after else [{"op": "replace", "path": path or "/", "value": copy.deepcopy(after)}]


def trace_operation_completeness_issues(base: dict[str, Any], expected_transformed: dict[str, Any], primary: dict[str, Any], linked: list[dict[str, Any]], operation_count: int) -> list[str]:
    operations = sorted([primary, *linked], key=lambda item: item["sequence"])
    expected = independent_structural_diff(base["source"], expected_transformed["source"], "/source")
    recorded = [{key: operation[key] for key in ("op", "path", "value")} for operation in operations]
    issues = []
    if operation_count != len(operations):
        issues.append("TPA_V02_TRACE_OPERATION_COUNT")
    if expected != recorded:
        issues.append("TPA_V02_TRACE_OPERATION_DIFF_INCOMPLETE")
    if len(expected) == 1 and linked:
        issues.append("TPA_V02_TRACE_SINGLE_OPERATION_FALSE_LINK")
    if len(expected) > 1 and not linked:
        issues.append("TPA_V02_TRACE_MULTI_OPERATION_LINK_MISSING")
    return issues


def subject_endpoint_specs(source: dict[str, Any]) -> list[dict[str, Any]]:
    endpoints = [source["visit"]["nominal"], source["visit"]["actual"]]
    endpoints.extend(endpoint for event in source["events"] for endpoint in (event["start"], event["end"]))
    endpoints.extend((source["risk"]["start"], source["risk"]["end"], source["phase"]["start"], source["phase"]["end"]))
    return endpoints


def derived_study_day(anchor_date: str, target_date: str, day_zero: bool) -> int:
    delta = (dt.date.fromisoformat(target_date) - dt.date.fromisoformat(anchor_date)).days
    return delta if day_zero or delta < 0 else delta + 1


def recompute_subject_study_days(source: dict[str, Any]) -> None:
    if not source["axis"]["study_day_enabled"]:
        for endpoint in subject_endpoint_specs(source):
            endpoint["study_day"] = None
        return
    anchor_ref = source["axis"]["anchor_event_ref"]
    anchor = next(row for row in source["events"] if row["event_ref"] == anchor_ref)["start"]
    if anchor["state"] != "exact" or anchor["exact_date"] is None or not anchor["projectable"]:
        fail("study-day anchor invalid")
    day_zero = source["axis"]["day_zero_convention"] == "anchor_day_zero"
    for endpoint in subject_endpoint_specs(source):
        endpoint["study_day"] = (
            derived_study_day(anchor["exact_date"], endpoint["exact_date"], day_zero)
            if endpoint["state"] == "exact" and endpoint["exact_date"] is not None
            else None
        )


def validate_subject_study_days(source: dict[str, Any]) -> None:
    expected = copy.deepcopy(source)
    recompute_subject_study_days(expected)
    if [row["study_day"] for row in subject_endpoint_specs(source)] != [row["study_day"] for row in subject_endpoint_specs(expected)]:
        fail("study-day authority input mismatch")


class IndependentExecutor:
    def __init__(self, bundle: dict[str, Any]) -> None:
        self.bundle = copy.deepcopy(bundle); self.source = self.bundle["source"]
        typed_issues = authority_issues(self.bundle, load(SCHEMA))
        if typed_issues:
            fail("typed authority: " + "|".join(typed_issues))
        if bundle["execution_profile"] != PROFILE or bundle["target_contract"] not in (SUBJECT, AEMH): fail("supersession gate")
        if bundle["bundle_content_identity"] != digest({key: value for key, value in bundle.items() if key != "bundle_content_identity"}): fail("bundle identity")
        if bundle["target_contract"] == SUBJECT:
            validate_subject_study_days(self.source)
            binding = self.source["cutoff_binding"]
            present_valid = binding["state"] == "present" and binding["exact_date"] is not None and bool(binding["source_locator_refs"])
            absent_valid = binding == {"state": "absent", "exact_date": None, "source_locator_refs": []}
            if not (present_valid or absent_valid): fail("cutoff binding invalid")

    @staticmethod
    def scope(spec: dict[str, Any], cutoff_binding: dict[str, Any] | None = None) -> dict[str, Any]:
        if cutoff_binding is not None:
            return sealed({**spec, "cutoff_state": cutoff_binding["state"], "cutoff_ref": cutoff_binding["exact_date"]}, "identity_content_hash")
        return sealed({**spec, "cutoff_state": "present"}, "identity_content_hash")

    @staticmethod
    def locator(spec: dict[str, Any]) -> dict[str, Any]:
        return sealed({"locator_ref": spec["locator_ref"], "locator_variant": "r4_source_locator", "snapshot_ref": spec["snapshot_ref"], "source_revision_ref": spec["revision_ref"], "source_revision_content_hash": spec["revision_content_identity"], "source_file_ref": None, "table_semantic": "synthetic_listing", "record_ref": spec["record_ref"], "authority_entity_kind": spec["entity_kind"], "authority_entity_ref": spec["entity_ref"], "column_or_anchor": spec["anchor"], "canonical_location": None, "raw_payload_hash": digest({"record": spec["record_ref"], "anchor": spec["anchor"]})}, "locator_content_hash")

    @staticmethod
    def endpoint(spec: dict[str, Any]) -> dict[str, Any]:
        return sealed({"state": spec["state"], "exact_date": spec["exact_date"], "range_start": spec["range_start"], "range_end": spec["range_end"], "candidate_values": spec["candidates"], "source_locator_refs": sorted(spec["locator_refs"]), "main_axis_projectable": spec["projectable"], "range_projection_authorized": spec["range_authorized"], "study_day": spec["study_day"]}, "endpoint_content_hash")

    @staticmethod
    def visibility(identity: dict[str, Any]) -> dict[str, Any]:
        return sealed({"visibility_decision_id": f"visibility::{identity['subject_ref']}::{identity['snapshot_ref']}", "visibility_decision_hash": digest({**{key: identity[key] for key in ("project_ref", "run_ref", "snapshot_ref", "cutoff_state", "cutoff_ref", "site_ref", "subject_ref", "spine_ref")}, "state": "projectable"}), "evaluation_member_refs": [identity["subject_ref"]], "evaluation_site_refs": [identity["site_ref"]], "projectable_member_refs": [identity["subject_ref"]], "projectable_site_refs": [identity["site_ref"]], "hidden_member_refs": [], "hidden_site_refs": [], "hidden_member_count": 0, "hidden_site_count": 0, "subject_visibility_state": "projectable", "deep_link_eligible": True}, "closure_content_hash")

    @staticmethod
    def pairs(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted((sealed({"revision_id": row["revision_ref"], "accepted_content_hash": row["revision_content_identity"], "locator_refs": sorted(row["locator_refs"])}, "pair_content_hash") for row in specs), key=lambda row: row["revision_id"])

    @staticmethod
    def subject_evaluation(projection: dict[str, Any], revisions: list[str]) -> list[str]:
        values = [projection["projection_content_hash"], projection["scope_identity"]["identity_content_hash"], projection["membership_index"]["membership_content_hash"], projection["axis_basis"]["axis_content_hash"], *revisions]
        values += [row["visit_content_hash"] for row in projection["visits"]]
        values += [value for row in projection["events"] for value in (row["event_content_identity"], row["event_content_hash"])]
        values += [value for row in projection["risk_anchors"] for value in (row["risk_content_identity"], row["risk_anchor_content_hash"])]
        values += [row["pending_content_hash"] for row in projection["pending_date_items"]]
        values += [row["phase_content_hash"] for row in projection["phase_bands"]]
        values += [row["track_content_hash"] for row in projection["domain_tracks"]]
        values += [row["locator_content_hash"] for row in projection["source_locators"]]
        return sorted(set(values))

    @staticmethod
    def aemh_evaluation(projection: dict[str, Any], revisions: list[str]) -> list[str]:
        values = [projection["projection_content_hash"], projection["scope_identity"]["identity_content_hash"], projection["membership_index"]["membership_content_hash"], projection["cutoff_endpoint"]["cutoff_content_hash"], *revisions]
        if projection["previous_projection_content_hash"] is not None: values.append(projection["previous_projection_content_hash"])
        values += [row["prefix_content_hash"] for row in projection["accepted_thread_prefixes"]]
        for thread in projection["threads"]:
            values += [thread["candidate_content_identity"], thread["thread_content_hash"]]
            for entry in thread["history_entries"]:
                values += [entry["entry_hash"], *entry["later_fact_content_identities"], *[row["evidence_content_hash"] for row in entry["identity_evidence"]]]
        values += [row["locator_content_hash"] for row in projection["source_locators"]]
        return sorted(set(values))

    @classmethod
    def receipt(cls, variant: str, contract: str, identity: dict[str, Any], projection: dict[str, Any], pairs: list[dict[str, Any]], evaluation: list[str]) -> dict[str, Any]:
        return sealed({"receipt_id": digest({"receipt_variant": variant, "authority_contract_id": contract, "scope_identity_hash": identity["identity_content_hash"], "public_projection_id": projection["projection_id"]}), "receipt_variant": variant, "authority_contract_id": contract, "authority_contract_version": PARENT_VERSION, "scope_identity": identity, "public_projection_id": projection["projection_id"], "public_projection_content_hash": projection["projection_content_hash"], "evaluation_content_identities": evaluation, "visibility_closure": cls.visibility(identity), "source_revision_content_pairs": pairs, "audience_contract_id": AUDIENCE}, "receipt_content_hash")

    def subject_packet(self) -> dict[str, Any]:
        s = self.source; cutoff_binding = s["cutoff_binding"]; identity = self.scope(s["scope"], cutoff_binding); locators = sorted([self.locator(row) for row in s["locator_specs"]], key=lambda row: row["locator_ref"]); pairs = self.pairs(s["revision_specs"])
        vs = s["visit"]
        visit = sealed({"visit_ref": vs["visit_ref"], "visit_kind": "actual", "planned_visit_ref": vs["planned_visit_ref"], "actual_encounter_ref": vs["actual_encounter_ref"], "accepted_assignment_ref": vs["assignment_ref"], "phase_ref": vs["phase_ref"], "nominal_endpoint": self.endpoint(vs["nominal"]), "actual_endpoint": self.endpoint(vs["actual"]), "source_locator_refs": sorted(vs["locator_refs"])}, "visit_content_hash")
        events = sorted([sealed({"event_ref": row["event_ref"], "event_content_identity": row["content_identity"], "domain": row["domain"], "subtype": row["subtype"], "applicability_state": "applicable", "visit_ref": row["visit_ref"], "geometry": row["geometry"], "start_endpoint": self.endpoint(row["start"]), "end_endpoint": self.endpoint(row["end"]), "risk_anchor_refs": sorted(row["risk_refs"]), "source_locator_refs": sorted(row["locator_refs"])}, "event_content_hash") for row in s["events"]], key=lambda row: row["event_ref"])
        rs = s["risk"]
        risk = sealed({"risk_anchor_ref": rs["risk_anchor_ref"], "risk_ref": rs["risk_ref"], "risk_content_identity": rs["content_identity"], "domain": rs["domain"], "severity": rs["severity"], "risk_type_zh": rs["risk_type_zh"], "event_ref": rs["event_ref"], "visit_ref": rs["visit_ref"], "geometry": rs["geometry"], "start_endpoint": self.endpoint(rs["start"]), "end_endpoint": self.endpoint(rs["end"]), "source_locator_refs": sorted(rs["locator_refs"])}, "risk_anchor_content_hash")
        ps = s["phase"]
        phase = sealed({"phase_ref": ps["phase_ref"], "phase_label_zh": ps["label_zh"], "geometry": ps["geometry"], "start_endpoint": self.endpoint(ps["start"]), "end_endpoint": self.endpoint(ps["end"]), "source_locator_refs": sorted(ps["locator_refs"])}, "phase_content_hash")
        mh = next(row for row in events if row["domain"] == "mh")
        pending_event = sealed({"pending_ref": "pending::event::mh::1", "item_kind": "event", "item_ref": mh["event_ref"], "target_content_hash": mh["event_content_hash"], "domain": "mh", "start_endpoint": mh["start_endpoint"], "end_endpoint": mh["end_endpoint"], "source_locator_refs": mh["source_locator_refs"]}, "pending_content_hash")
        pending_phase = sealed({"pending_ref": "pending::phase::treatment", "item_kind": "phase", "item_ref": phase["phase_ref"], "target_content_hash": phase["phase_content_hash"], "domain": None, "start_endpoint": phase["start_endpoint"], "end_endpoint": phase["end_endpoint"], "source_locator_refs": phase["source_locator_refs"]}, "pending_content_hash")
        tracks = [sealed({"domain": row["domain"], "applicability_state": row["state"], "event_refs": sorted(row["event_refs"]), "risk_anchor_refs": sorted(row["risk_refs"])}, "track_content_hash") for row in s["domain_applicability"]]
        membership = sealed({"visit_refs": [visit["visit_ref"]], "event_refs": [row["event_ref"] for row in events], "risk_anchor_refs": [risk["risk_anchor_ref"]], "pending_date_refs": [pending_event["pending_ref"], pending_phase["pending_ref"]], "phase_refs": [phase["phase_ref"]], "source_locator_refs": [row["locator_ref"] for row in locators]}, "membership_content_hash")
        axis_spec = s["axis"]
        cutoff = self.endpoint({"state": "exact" if cutoff_binding["state"] == "present" else "missing", "exact_date": cutoff_binding["exact_date"], "range_start": None, "range_end": None, "candidates": [], "locator_refs": cutoff_binding["source_locator_refs"], "projectable": cutoff_binding["state"] == "present", "range_authorized": cutoff_binding["state"] == "present", "study_day": None})
        axis = sealed({"axis_ref": axis_spec["axis_ref"], "default_axis_mode": axis_spec["mode"], "timezone": axis_spec["timezone"], "study_day_anchor_event_ref": axis_spec["anchor_event_ref"] if axis_spec["study_day_enabled"] else None, "study_day_zero_exists": axis_spec["day_zero_convention"] == "anchor_day_zero" if axis_spec["study_day_enabled"] else None, "cutoff_endpoint": cutoff, "source_locator_refs": sorted(cutoff_binding["source_locator_refs"])}, "axis_content_hash")
        projection_id = digest({"contract_id": SUBJECT, "schema_version": PARENT_VERSION, "scope_identity_hash": identity["identity_content_hash"], "membership_index_hash": membership["membership_content_hash"], "axis_basis_hash": axis["axis_content_hash"]})
        receipt_id = digest({"receipt_variant": "subject_temporal", "authority_contract_id": SUBJECT, "scope_identity_hash": identity["identity_content_hash"], "public_projection_id": projection_id})
        projection = sealed({"contract_id": SUBJECT, "schema_version": PARENT_VERSION, "projection_id": projection_id, "receipt_ref": receipt_id, "scope_identity": identity, "fallback_policy": "fail_closed_no_nearest", "axis_basis": axis, "visits": [visit], "events": events, "risk_anchors": [risk], "pending_date_items": [pending_event, pending_phase], "phase_bands": [phase], "domain_tracks": tracks, "source_locators": locators, "membership_index": membership}, "projection_content_hash")
        receipt = self.receipt("subject_temporal", SUBJECT, identity, projection, pairs, self.subject_evaluation(projection, [row["accepted_content_hash"] for row in pairs]))
        packet = {"receipt": receipt, "projection": projection}; packet["packet_content_hash"] = digest({"receipt_content_hash": receipt["receipt_content_hash"], "projection_content_hash": projection["projection_content_hash"]}); return packet

    @staticmethod
    def entity_identity(kind: str, ref: str, locator: dict[str, Any]) -> str:
        return digest({"entity_kind": kind, "entity_ref": ref, "source_locator_ref": locator["locator_ref"], "source_raw_payload_hash": locator["raw_payload_hash"]})

    @classmethod
    def evidence(cls, ref: str, kind: str, entity: str, locator: dict[str, Any]) -> dict[str, Any]:
        return sealed({"evidence_ref": ref, "evidence_kind": kind, "entity_ref": entity, "entity_content_identity": cls.entity_identity(kind, entity, locator), "source_locator_ref": locator["locator_ref"], "source_locator_content_hash": locator["locator_content_hash"], "source_raw_payload_hash": locator["raw_payload_hash"]}, "evidence_content_hash")

    @staticmethod
    def required_evidence_locator(mapping: dict[tuple[str, str, str, str], dict[str, Any]], key: tuple[str, str, str, str]) -> dict[str, Any]:
        if key not in mapping: fail("evidence authority binding")
        return mapping[key]

    @staticmethod
    def entry(key: str, seq: int, kind: str, snapshot: str, state: str | None, facts: list[str], fact_ids: list[str], evidence: list[dict[str, Any]], retained: list[str], reason: str, prior: str | None) -> dict[str, Any]:
        if len(facts) != len(fact_ids): fail("fact identity cardinality")
        fact_pairs = sorted(zip(facts, fact_ids), key=lambda row: row[0])
        return sealed({"entry_id": f"history-entry::{key}::{seq}", "seq": seq, "event_kind": kind, "snapshot_ref": snapshot, "match_state": state, "later_fact_refs": [row[0] for row in fact_pairs], "later_fact_content_identities": [row[1] for row in fact_pairs], "identity_evidence_refs": sorted(row["evidence_ref"] for row in evidence), "identity_evidence": sorted(evidence, key=lambda row: row["evidence_ref"]), "retained_evidence_locator_refs": sorted(retained), "reason_code": reason, "risk_lifecycle_effect": "none", "prior_entry_hash": prior}, "entry_hash")

    @classmethod
    def aemh_packet(cls, identity: dict[str, Any], threads: list[dict[str, Any]], locators: list[dict[str, Any]], pairs: list[dict[str, Any]], previous: dict[str, Any] | None) -> dict[str, Any]:
        threads = sorted(threads, key=lambda row: row["thread_ref"]); locators = sorted(locators, key=lambda row: row["locator_ref"])
        later = sorted({ref for thread in threads for entry in thread["history_entries"] for ref in entry["later_fact_refs"]})
        membership = sealed({"thread_refs": [row["thread_ref"] for row in threads], "candidate_refs": sorted(row["original_candidate_ref"] for row in threads), "later_fact_refs": later, "source_locator_refs": [row["locator_ref"] for row in locators]}, "membership_content_hash")
        prefixes: list[dict[str, Any]] = []; previous_ref = previous_hash = None
        if previous is not None:
            old_projection = previous["projection"]; previous_ref = old_projection["projection_id"]; previous_hash = old_projection["projection_content_hash"]; old_by_ref = {row["thread_ref"]: row for row in old_projection["threads"]}
            for thread in threads:
                old = old_by_ref[thread["thread_ref"]]
                prefixes.append(sealed({"thread_ref": thread["thread_ref"], "accepted_prefix_seq": len(old["history_entries"]), "accepted_prefix_head_hash": old["history_entries"][-1]["entry_hash"], "previous_thread_content_hash": old["thread_content_hash"]}, "prefix_content_hash"))
        cutoff_ref = next(row["locator_ref"] for row in locators if row["authority_entity_kind"] == "candidate" and row["authority_entity_ref"] == "candidate::suspected-ae::1")
        cutoff = sealed({"state": "present", "exact_date": identity["cutoff_ref"], "source_locator_refs": [cutoff_ref]}, "cutoff_content_hash")
        projection_id = digest({"contract_id": AEMH, "schema_version": PARENT_VERSION, "scope_identity_hash": identity["identity_content_hash"], "membership_index_hash": membership["membership_content_hash"]})
        receipt_id = digest({"receipt_variant": "aemh_match_history", "authority_contract_id": AEMH, "scope_identity_hash": identity["identity_content_hash"], "public_projection_id": projection_id})
        projection = sealed({"contract_id": AEMH, "schema_version": PARENT_VERSION, "projection_id": projection_id, "receipt_ref": receipt_id, "scope_identity": identity, "cutoff_endpoint": cutoff, "fallback_policy": "fail_closed_no_nearest", "previous_projection_ref": previous_ref, "previous_projection_content_hash": previous_hash, "accepted_thread_prefixes": prefixes, "threads": threads, "source_locators": locators, "membership_index": membership}, "projection_content_hash")
        receipt = cls.receipt("aemh_match_history", AEMH, identity, projection, pairs, cls.aemh_evaluation(projection, [row["accepted_content_hash"] for row in pairs]))
        packet = {"receipt": receipt, "projection": projection}; packet["packet_content_hash"] = digest({"receipt_content_hash": receipt["receipt_content_hash"], "projection_content_hash": projection["projection_content_hash"]}); return packet

    def aemh_packets(self) -> tuple[dict[str, Any], dict[str, Any]]:
        s = self.source; prev_identity = self.scope(s["previous_scope"]); curr_identity = self.scope(s["current_scope"])
        prev_locs = [self.locator(row) for row in s["previous_locator_specs"]]; curr_locs = [self.locator(row) for row in s["current_locator_specs"]]
        prev_by_ref = {row["locator_ref"]: row for row in prev_locs}; previous_authority_by_ref = {row["locator_ref"]: row for row in s["previous_locator_specs"]}; current_by_ref = {row["locator_ref"]: row for row in curr_locs}
        current_by_entity = {(row["authority_thread_ref"], row["authority_domain"], row["entity_kind"], row["entity_ref"]): current_by_ref[row["locator_ref"]] for row in s["current_locator_specs"]}
        previous_threads = []
        for spec in s["thread_specs"]:
            loc = prev_by_ref[spec["candidate_locator_ref"]]; locator_authority = previous_authority_by_ref[spec["candidate_locator_ref"]]
            if (locator_authority["authority_thread_ref"], locator_authority["authority_domain"], locator_authority["entity_kind"], locator_authority["entity_ref"]) != (spec["thread_ref"], spec["domain"], "candidate", spec["candidate_ref"]): fail("evidence authority binding")
            ev = self.evidence(f"identity-evidence::candidate::{spec['domain']}1", "candidate", spec["candidate_ref"], loc)
            entry = self.entry(f"{spec['domain']}::1", 1, "reminder_created", s["previous_scope"]["snapshot_ref"], None, [], [], [ev], [loc["locator_ref"]], spec["reminder_reason"], None)
            previous_threads.append(sealed({"thread_ref": spec["thread_ref"], "project_ref": prev_identity["project_ref"], "site_ref": prev_identity["site_ref"], "domain": spec["domain"], "subject_ref": prev_identity["subject_ref"], "original_candidate_ref": spec["candidate_ref"], "candidate_content_identity": self.entity_identity("candidate", spec["candidate_ref"], loc), "original_reminder_ref": entry["entry_id"], "history_entries": [entry], "evidence_locator_refs": [loc["locator_ref"]]}, "thread_content_hash"))
        previous = self.aemh_packet(prev_identity, previous_threads, prev_locs, self.pairs(s["previous_revision_specs"]), None)
        old_by_ref = {row["thread_ref"]: row for row in previous_threads}; decisions = {row["thread_ref"]: [] for row in s["thread_specs"]}
        for row in s["decision_records"]: decisions[row["thread_ref"]].append(row)
        current_threads = []
        for spec in s["thread_specs"]:
            old = old_by_ref[spec["thread_ref"]]; entries = copy.deepcopy(old["history_entries"]); retained = {spec["candidate_locator_ref"]}
            for decision in decisions[spec["thread_ref"]]:
                evidence: list[dict[str, Any]] = []; fact_ids: list[str] = []
                if decision["event_kind"] == "match_decided":
                    loc = self.required_evidence_locator(current_by_entity, (spec["thread_ref"], spec["domain"], "candidate", spec["candidate_ref"])); evidence.append(self.evidence(f"identity-evidence::candidate::{spec['domain']}1", "candidate", spec["candidate_ref"], loc))
                for fact in decision["fact_refs"]:
                    loc = self.required_evidence_locator(current_by_entity, (spec["thread_ref"], spec["domain"], "later_fact", fact)); evidence.append(self.evidence(f"identity-evidence::later_fact::{digest(fact)[:12]}", "later_fact", fact, loc)); fact_ids.append(self.entity_identity("later_fact", fact, loc)); retained.add(loc["locator_ref"])
                for fact in decision["considered_fact_refs"]:
                    loc = self.required_evidence_locator(current_by_entity, (spec["thread_ref"], spec["domain"], "considered_fact", fact)); evidence.append(self.evidence(f"identity-evidence::considered_fact::{digest(fact)[:12]}", "considered_fact", fact, loc)); retained.add(loc["locator_ref"])
                entries.append(self.entry(f"{spec['domain']}::1", len(entries) + 1, decision["event_kind"], s["current_scope"]["snapshot_ref"], decision["match_state"], decision["fact_refs"], fact_ids, evidence, sorted(retained), decision["reason_code"], entries[-1]["entry_hash"]))
            current_threads.append(sealed({"thread_ref": spec["thread_ref"], "project_ref": curr_identity["project_ref"], "site_ref": curr_identity["site_ref"], "domain": spec["domain"], "subject_ref": curr_identity["subject_ref"], "original_candidate_ref": spec["candidate_ref"], "candidate_content_identity": old["candidate_content_identity"], "original_reminder_ref": old["original_reminder_ref"], "history_entries": entries, "evidence_locator_refs": sorted(retained)}, "thread_content_hash"))
        current = self.aemh_packet(curr_identity, current_threads, curr_locs, self.pairs(s["current_revision_specs"]), previous); return previous, current


def verify_no_asserts() -> None:
    for path in (GENERATOR, VERIFIER):
        tree = ast.parse(path.read_bytes(), filename=str(path))
        if any(isinstance(node, ast.Assert) for node in ast.walk(tree)): fail(f"assert statement {path}")
    verifier_tree = ast.parse(VERIFIER.read_bytes())
    for node in ast.walk(verifier_tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names]
            if any("generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2" in name for name in names): fail("verifier imports generator")


def verify_manifest(manifest: dict[str, Any]) -> None:
    if manifest["contract_id"] != "r5-s5-temporal-projection-authority-delta-v0.2" or manifest["schema_version"] != "2026-08-21.1" or manifest["execution_profile"] != PROFILE: fail("manifest identity")
    if manifest["status"] != "candidate_unaccepted" or manifest["no_self_acceptance"] is not True: fail("self acceptance")
    if tuple(manifest["exact_v02_paths"]) != EXACT_PATHS: fail("exact paths")
    if manifest["manifest_content_hash"] != digest({key: value for key, value in manifest.items() if key != "manifest_content_hash"}): fail("manifest content hash")
    for rel, expected in manifest["file_raw_sha256"].items():
        if raw_sha(ROOT / rel) != expected: fail(f"v0.2 file pin {rel}")
    for rel, expected in manifest["external_pins"].items():
        if raw_sha(ROOT / rel) != expected: fail(f"external pin {rel}")
    pin_issues = pin_surface_issues(manifest)
    if pin_issues: fail("typed source pins: " + "|".join(pin_issues))
    protected = manifest["protected_accepted_pins"]
    if raw_sha(ROOT / "poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py") != protected["r5_root_init_sha256"]: fail("root init drift")
    if protected["medical_writing_protected_file_count"] != 542: fail("medical writing count pin")


def verify_schema(schema: dict[str, Any], manifest: dict[str, Any]) -> None:
    required = {"AuthorityBundleV02", "SubjectFullGraphInputV02", "AEMHFullGraphInputV02", "CutoffEndpointBindingV02", "EmitterSupersessionRuleV02", "TraceRealizationBindingV02", "ExternalPinV02"}
    if not required <= set(schema["objects"]): fail("required exact types")
    if schema["baseline_content_hash"] != digest({"objects": schema["objects"], "enums": schema["enums"]}): fail("schema baseline")
    if schema["baseline_content_hash"] != manifest["schema_baseline_content_hash"]: fail("schema manifest pin")
    for name, row in schema["objects"].items():
        if set(row) != {"additional_properties", "fields", "optional", "required"} or row["additional_properties"] is not False or set(row["required"]) | set(row["optional"]) != set(row["fields"]): fail(f"exact schema {name}")
    if schema["forbidden_candidate_keys"] != ["packet", "expected_packet", "expected_hash", "expected_error", "acceptance_token", "target_output"]: fail("candidate forbidden keys")


def recipe_ir_issues(registry: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    issues = []
    recipes = registry.get("executable_v02_recipes")
    if not isinstance(recipes, list) or len(recipes) != 16:
        return ["TPA_V02_RECIPE_CARDINALITY"]
    recipe_ids = {row.get("recipe_id") for row in recipes if isinstance(row, dict)}
    if len(recipe_ids) != 16:
        issues.append("TPA_V02_RECIPE_ID_DUPLICATE")
    phase_order = {
        SUBJECT: ["identity_cutoff", "locators_revisions", "temporal_members", "domains_pending_membership", "axis", "projection", "receipt", "packet"],
        AEMH: ["identity_locators_revisions", "previous_threads", "previous_packet", "current_threads", "current_membership_prefix_cutoff", "projection", "receipt", "packet"],
    }
    authority_pointers = {
        "identity_cutoff": ["/source/scope", "/source/cutoff_binding"], "locators_revisions": ["/source/locator_specs", "/source/revision_specs"],
        "temporal_members": ["/source/visit", "/source/events", "/source/risk", "/source/phase"], "domains_pending_membership": ["/source/domain_applicability"],
        "axis": ["/source/axis"], "identity_locators_revisions": ["/source/previous_scope", "/source/current_scope", "/source/previous_locator_specs", "/source/current_locator_specs", "/source/previous_revision_specs", "/source/current_revision_specs"],
        "previous_threads": ["/source/thread_specs"], "current_threads": ["/source/decision_records"], "projection": [], "receipt": [], "packet": [], "previous_packet": [], "current_membership_prefix_cutoff": [],
    }
    exact_prior_refs = {
        (SUBJECT, "identity_cutoff"): [],
        (SUBJECT, "locators_revisions"): ["recipe.v02.subject_identity_cutoff.sealed"],
        (SUBJECT, "temporal_members"): ["recipe.v02.subject_locators_revisions.sealed"],
        (SUBJECT, "domains_pending_membership"): ["recipe.v02.subject_temporal_members.sealed", "recipe.v02.subject_locators_revisions.sealed"],
        (SUBJECT, "axis"): ["recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_domains_pending_membership.sealed"],
        (SUBJECT, "projection"): ["recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_locators_revisions.sealed", "recipe.v02.subject_temporal_members.sealed", "recipe.v02.subject_domains_pending_membership.sealed", "recipe.v02.subject_axis.sealed"],
        (SUBJECT, "receipt"): ["recipe.v02.subject_projection.sealed", "recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_locators_revisions.sealed"],
        (SUBJECT, "packet"): ["recipe.v02.subject_projection.sealed", "recipe.v02.subject_receipt.sealed"],
        (AEMH, "identity_locators_revisions"): [],
        (AEMH, "previous_threads"): ["recipe.v02.aemh_identity_locators_revisions.sealed"],
        (AEMH, "previous_packet"): ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_threads.sealed"],
        (AEMH, "current_threads"): ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_threads.sealed"],
        (AEMH, "current_membership_prefix_cutoff"): ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_packet.sealed", "recipe.v02.aemh_current_threads.sealed"],
        (AEMH, "projection"): ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_packet.sealed", "recipe.v02.aemh_current_threads.sealed", "recipe.v02.aemh_current_membership_prefix_cutoff.sealed"],
        (AEMH, "receipt"): ["recipe.v02.aemh_projection.sealed", "recipe.v02.aemh_identity_locators_revisions.sealed"],
        (AEMH, "packet"): ["recipe.v02.aemh_projection.sealed", "recipe.v02.aemh_receipt.sealed", "recipe.v02.aemh_previous_packet.sealed"],
    }
    seen = {SUBJECT: [], AEMH: []}
    for index, recipe in enumerate(recipes):
        issues.extend(validate_typed(recipe, "ExecutableRecipeV02", schema, f"$.executable_v02_recipes[{index}]"))
        if not isinstance(recipe, dict) or not {"target_contract", "nodes", "inputs", "dependency_edges", "external_pin_refs", "recipe_id", "recipe_content_hash"} <= set(recipe):
            continue
        if recipe["recipe_content_hash"] != digest({key: value for key, value in recipe.items() if key != "recipe_content_hash"}):
            issues.append(f"recipe:{recipe['recipe_id']}:hash")
        if len(recipe["nodes"]) != 2:
            issues.append(f"recipe:{recipe['recipe_id']}:node_cardinality")
            continue
        first, second = recipe["nodes"]
        phase = first.get("params", {}).get("phase")
        seen[recipe["target_contract"]].append(phase)
        target_name = "subject" if recipe["target_contract"] == SUBJECT else "aemh"
        if [first.get("op"), second.get("op")] != [f"emit_{target_name}_{phase}", f"seal_{target_name}_{phase}"]:
            issues.append(f"recipe:{recipe['recipe_id']}:op_sequence")
        params = first.get("params", {})
        expected_inputs = [*params.get("authority_input_pointers", []), *params.get("prior_recipe_output_refs", [])]
        if recipe["inputs"] != expected_inputs or first.get("inputs") != expected_inputs or second.get("inputs") != first.get("outputs"):
            issues.append(f"recipe:{recipe['recipe_id']}:dependency")
        expected_edges = [{"from": item, "to": first.get("node_id")} for item in expected_inputs] + [{"from": first.get("node_id"), "to": second.get("node_id")}]
        if recipe["dependency_edges"] != expected_edges:
            issues.append(f"recipe:{recipe['recipe_id']}:dag")
        expected_recipe_id = f"recipe.v02.{'subject' if recipe['target_contract'] == SUBJECT else 'aemh'}_{phase}"
        if params != second.get("params") or not isinstance(params, dict) or set(params) != {"operation_version", "phase", "authority_input_pointers", "prior_recipe_output_refs", "output_name", "canonicalization"}:
            issues.append(f"recipe:{recipe['recipe_id']}:params")
        elif params["operation_version"] != SCHEMA_VERSION or params["canonicalization"] != "utf8_nfc_canonical_json_sorted_keys_compact_no_nan" or recipe["recipe_id"] != expected_recipe_id or params["authority_input_pointers"] != authority_pointers.get(phase) or params["prior_recipe_output_refs"] != exact_prior_refs.get((recipe["target_contract"], phase)) or params["output_name"] != f"{recipe['recipe_id']}.value" or first["outputs"] != [params["output_name"]] or second["outputs"] != [f"{recipe['recipe_id']}.sealed"]:
            issues.append(f"recipe:{recipe['recipe_id']}:params_value")
        if set(recipe["external_pin_refs"]) != set(TYPED_SOURCE_PINS):
            issues.append(f"recipe:{recipe['recipe_id']}:pins")
    if seen != phase_order: issues.append("TPA_V02_RECIPE_PHASE_ORDER")
    recipe_target = {row.get("recipe_id"): row.get("target_contract") for row in recipes}
    for recipe in recipes:
        for ref in recipe.get("nodes", [{}])[0].get("params", {}).get("prior_recipe_output_refs", []):
            if recipe_target.get(ref.removesuffix(".sealed")) != recipe.get("target_contract"):
                issues.append(f"recipe:{recipe.get('recipe_id')}:cross_target")
    for index, rule in enumerate(registry.get("supersession_rules", [])):
        issues.extend(validate_typed(rule, "EmitterSupersessionRuleV02", schema, f"$.supersession_rules[{index}]"))
        if any(recipe_id not in recipe_ids for recipe_id in rule.get("replacement_recipe_ids", [])):
            issues.append(f"rule:{rule.get('rule_id')}:unknown_recipe")
    pin_map = {}
    for index, pin in enumerate(registry.get("external_pins", [])):
        issues.extend(validate_typed(pin, "ExternalPinV02", schema, f"$.external_pins[{index}]"))
        if isinstance(pin, dict):
            pin_map[pin.get("path")] = pin.get("sha256")
    if pin_map != TYPED_SOURCE_PINS:
        issues.append("TPA_V02_EXTERNAL_PIN_GATE")
    return issues


def seal_recipe_stage(value: Any) -> dict[str, Any]:
    return {"value": copy.deepcopy(value), "content_hash": digest(value)}


def independent_recipe_dispatch_issues(registry: dict[str, Any], executor: IndependentExecutor, method_override: dict[str, Any] | None = None) -> tuple[list[str], dict[str, Any], dict[str, tuple[str, ...]]]:
    method_dispatch = method_override or {
        "scope": executor.scope,
        "locator": executor.locator,
        "endpoint": executor.endpoint,
        "visibility": executor.visibility,
        "pairs": executor.pairs,
        "subject_evaluation": executor.subject_evaluation,
        "aemh_evaluation": executor.aemh_evaluation,
        "receipt": executor.receipt,
        "entity_identity": executor.entity_identity,
        "evidence": executor.evidence,
        "required_evidence_locator": executor.required_evidence_locator,
        "entry": executor.entry,
        "aemh_packet": executor.aemh_packet,
        "seal": seal_recipe_stage,
    }
    method_signatures = {
        "scope": ("spec", "cutoff_binding"),
        "locator": ("spec",),
        "endpoint": ("spec",),
        "visibility": ("identity",),
        "pairs": ("specs",),
        "subject_evaluation": ("projection", "revisions"),
        "aemh_evaluation": ("projection", "revisions"),
        "receipt": ("variant", "contract", "identity", "projection", "pairs", "evaluation"),
        "entity_identity": ("kind", "ref", "locator"),
        "evidence": ("ref", "kind", "entity", "locator"),
        "required_evidence_locator": ("mapping", "key"),
        "entry": ("key", "seq", "kind", "snapshot", "state", "facts", "fact_ids", "evidence", "retained", "reason", "prior"),
        "aemh_packet": ("identity", "threads", "locators", "pairs", "previous"),
        "seal": ("value",),
    }
    emit_requirements = {
        "emit_subject_identity_cutoff": ("scope", "endpoint"),
        "emit_subject_locators_revisions": ("locator", "pairs", "visibility"),
        "emit_subject_temporal_members": ("endpoint",),
        "emit_subject_domains_pending_membership": (),
        "emit_subject_axis": (),
        "emit_subject_projection": (),
        "emit_subject_receipt": ("receipt", "subject_evaluation"),
        "emit_subject_packet": (),
        "emit_aemh_identity_locators_revisions": ("scope", "locator", "pairs"),
        "emit_aemh_previous_threads": ("entity_identity", "evidence", "entry"),
        "emit_aemh_previous_packet": ("aemh_packet",),
        "emit_aemh_current_threads": ("entity_identity", "evidence", "required_evidence_locator", "entry"),
        "emit_aemh_current_membership_prefix_cutoff": (),
        "emit_aemh_projection": (),
        "emit_aemh_receipt": ("receipt", "aemh_evaluation"),
        "emit_aemh_packet": (),
    }
    op_methods = dict(emit_requirements)
    for emit_op in emit_requirements:
        op_methods[emit_op.replace("emit_", "seal_", 1)] = ("seal",)
    actual_ops = {node.get("op") for recipe in registry.get("executable_v02_recipes", []) for node in recipe.get("nodes", []) if isinstance(node, dict)}
    issues = []
    if actual_ops != set(op_methods):
        issues.append("TPA_V02_INDEPENDENT_DISPATCH_OP_SET")
    if set(method_dispatch) != set(method_signatures):
        issues.append("TPA_V02_INDEPENDENT_DISPATCH_METHOD_SET")
    for method_name, expected_parameters in method_signatures.items():
        method = method_dispatch.get(method_name)
        if not callable(method):
            issues.append(f"TPA_V02_INDEPENDENT_DISPATCH_METHOD_MISSING:{method_name}")
        elif tuple(inspect.signature(method).parameters) != expected_parameters:
            issues.append(f"TPA_V02_INDEPENDENT_DISPATCH_SIGNATURE:{method_name}")
    for op, required_methods in op_methods.items():
        if any(method not in method_dispatch for method in required_methods):
            issues.append(f"TPA_V02_INDEPENDENT_DISPATCH_UNREACHABLE:{op}")
    return issues, method_dispatch, op_methods


def execute_independent_recipe_dag(authority_bundle: dict[str, Any], registry: dict[str, Any]) -> tuple[Any, dict[str, dict[str, Any]]]:
    """Independently dispatch every recipe node and pass sealed stage outputs."""
    executor = IndependentExecutor(authority_bundle); source = executor.source; target = authority_bundle["target_contract"]
    dispatch_issues, method_dispatch, op_methods = independent_recipe_dispatch_issues(registry, executor)
    if dispatch_issues: fail("recipe dispatch: " + "|".join(dispatch_issues))
    recipes = [row for row in registry["executable_v02_recipes"] if row["target_contract"] == target]
    outputs: dict[str, dict[str, Any]] = {}; stage: dict[str, Any] = {}
    binding_specs = {
        "emit_subject_identity_cutoff": ("recipe.v02.subject_identity_cutoff", SUBJECT, "identity_cutoff", ["/source/scope", "/source/cutoff_binding"], []),
        "emit_subject_locators_revisions": ("recipe.v02.subject_locators_revisions", SUBJECT, "locators_revisions", ["/source/locator_specs", "/source/revision_specs"], ["recipe.v02.subject_identity_cutoff.sealed"]),
        "emit_subject_temporal_members": ("recipe.v02.subject_temporal_members", SUBJECT, "temporal_members", ["/source/visit", "/source/events", "/source/risk", "/source/phase"], ["recipe.v02.subject_locators_revisions.sealed"]),
        "emit_subject_domains_pending_membership": ("recipe.v02.subject_domains_pending_membership", SUBJECT, "domains_pending_membership", ["/source/domain_applicability"], ["recipe.v02.subject_temporal_members.sealed", "recipe.v02.subject_locators_revisions.sealed"]),
        "emit_subject_axis": ("recipe.v02.subject_axis", SUBJECT, "axis", ["/source/axis"], ["recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_domains_pending_membership.sealed"]),
        "emit_subject_projection": ("recipe.v02.subject_projection", SUBJECT, "projection", [], ["recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_locators_revisions.sealed", "recipe.v02.subject_temporal_members.sealed", "recipe.v02.subject_domains_pending_membership.sealed", "recipe.v02.subject_axis.sealed"]),
        "emit_subject_receipt": ("recipe.v02.subject_receipt", SUBJECT, "receipt", [], ["recipe.v02.subject_projection.sealed", "recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_locators_revisions.sealed"]),
        "emit_subject_packet": ("recipe.v02.subject_packet", SUBJECT, "packet", [], ["recipe.v02.subject_projection.sealed", "recipe.v02.subject_receipt.sealed"]),
        "emit_aemh_identity_locators_revisions": ("recipe.v02.aemh_identity_locators_revisions", AEMH, "identity_locators_revisions", ["/source/previous_scope", "/source/current_scope", "/source/previous_locator_specs", "/source/current_locator_specs", "/source/previous_revision_specs", "/source/current_revision_specs"], []),
        "emit_aemh_previous_threads": ("recipe.v02.aemh_previous_threads", AEMH, "previous_threads", ["/source/thread_specs"], ["recipe.v02.aemh_identity_locators_revisions.sealed"]),
        "emit_aemh_previous_packet": ("recipe.v02.aemh_previous_packet", AEMH, "previous_packet", [], ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_threads.sealed"]),
        "emit_aemh_current_threads": ("recipe.v02.aemh_current_threads", AEMH, "current_threads", ["/source/decision_records"], ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_threads.sealed"]),
        "emit_aemh_current_membership_prefix_cutoff": ("recipe.v02.aemh_current_membership_prefix_cutoff", AEMH, "current_membership_prefix_cutoff", [], ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_packet.sealed", "recipe.v02.aemh_current_threads.sealed"]),
        "emit_aemh_projection": ("recipe.v02.aemh_projection", AEMH, "projection", [], ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_packet.sealed", "recipe.v02.aemh_current_threads.sealed", "recipe.v02.aemh_current_membership_prefix_cutoff.sealed"]),
        "emit_aemh_receipt": ("recipe.v02.aemh_receipt", AEMH, "receipt", [], ["recipe.v02.aemh_projection.sealed", "recipe.v02.aemh_identity_locators_revisions.sealed"]),
        "emit_aemh_packet": ("recipe.v02.aemh_packet", AEMH, "packet", [], ["recipe.v02.aemh_projection.sealed", "recipe.v02.aemh_receipt.sealed", "recipe.v02.aemh_previous_packet.sealed"]),
    }

    def emit_handler(expected: tuple[Any, ...]) -> Any:
        def handle(recipe: dict[str, Any], node: dict[str, Any]) -> str:
            recipe_id, expected_target, expected_phase, pointers, prior_refs = expected
            params = node["params"]; inputs = [*pointers, *prior_refs]; output_name = f"{recipe_id}.value"
            expected_edges = [{"from": item, "to": node["node_id"]} for item in inputs] + [{"from": node["node_id"], "to": recipe["nodes"][1]["node_id"]}]
            if recipe["recipe_id"] != recipe_id or recipe["target_contract"] != expected_target or params != {"operation_version": SCHEMA_VERSION, "phase": expected_phase, "authority_input_pointers": pointers, "prior_recipe_output_refs": prior_refs, "output_name": output_name, "canonicalization": "utf8_nfc_canonical_json_sorted_keys_compact_no_nan"} or recipe["inputs"] != inputs or node["inputs"] != inputs or node["outputs"] != [output_name] or recipe["dependency_edges"] != expected_edges:
                fail(f"recipe emit handler binding {node['op']}")
            return expected_phase
        return handle

    def seal_handler(expected: tuple[Any, ...]) -> Any:
        def handle(recipe: dict[str, Any], node: dict[str, Any], value: Any) -> dict[str, Any]:
            recipe_id, expected_target, expected_phase, pointers, prior_refs = expected
            output_name = f"{recipe_id}.value"
            params = {"operation_version": SCHEMA_VERSION, "phase": expected_phase, "authority_input_pointers": pointers, "prior_recipe_output_refs": prior_refs, "output_name": output_name, "canonicalization": "utf8_nfc_canonical_json_sorted_keys_compact_no_nan"}
            if recipe["recipe_id"] != recipe_id or recipe["target_contract"] != expected_target or node["params"] != params or node["inputs"] != [output_name] or node["outputs"] != [f"{recipe_id}.sealed"]:
                fail(f"recipe seal handler binding {node['op']}")
            return method_dispatch["seal"](value)
        return handle

    emit_handlers = {op: emit_handler(spec) for op, spec in binding_specs.items()}
    seal_handlers = {op.replace("emit_", "seal_", 1): seal_handler(spec) for op, spec in binding_specs.items()}
    for recipe in recipes:
        emit_node, seal_node = recipe["nodes"]
        if emit_node["op"] not in op_methods or seal_node["op"] not in op_methods or emit_node["op"] not in emit_handlers or seal_node["op"] not in seal_handlers: fail(f"recipe dispatch unknown op {recipe['recipe_id']}")
        params = emit_node["params"]; semantic = emit_handlers[emit_node["op"]](recipe, emit_node)
        for pointer in params["authority_input_pointers"]: pointer_get(authority_bundle, pointer)
        for ref in params["prior_recipe_output_refs"]:
            if ref not in outputs or outputs[ref]["content_hash"] != digest(outputs[ref]["value"]): fail(f"recipe prior {recipe['recipe_id']}:{ref}")
        if target == SUBJECT:
            if semantic == "identity_cutoff":
                binding = source["cutoff_binding"]; identity = executor.scope(source["scope"], binding)
                cutoff = executor.endpoint({"state": "exact" if binding["state"] == "present" else "missing", "exact_date": binding["exact_date"], "range_start": None, "range_end": None, "candidates": [], "locator_refs": binding["source_locator_refs"], "projectable": binding["state"] == "present", "range_authorized": binding["state"] == "present", "study_day": None})
                value = {"identity": identity, "cutoff": cutoff}
            elif semantic == "locators_revisions":
                value = {"locators": sorted((executor.locator(row) for row in source["locator_specs"]), key=lambda row: row["locator_ref"]), "pairs": executor.pairs(source["revision_specs"]), "visibility": executor.visibility(stage["identity_cutoff"]["identity"])}
            elif semantic == "temporal_members":
                visit_spec = source["visit"]
                visit = sealed({"visit_ref": visit_spec["visit_ref"], "visit_kind": "actual", "planned_visit_ref": visit_spec["planned_visit_ref"], "actual_encounter_ref": visit_spec["actual_encounter_ref"], "accepted_assignment_ref": visit_spec["assignment_ref"], "phase_ref": visit_spec["phase_ref"], "nominal_endpoint": executor.endpoint(visit_spec["nominal"]), "actual_endpoint": executor.endpoint(visit_spec["actual"]), "source_locator_refs": sorted(visit_spec["locator_refs"])}, "visit_content_hash")
                events = sorted((sealed({"event_ref": spec["event_ref"], "event_content_identity": spec["content_identity"], "domain": spec["domain"], "subtype": spec["subtype"], "applicability_state": "applicable", "visit_ref": spec["visit_ref"], "geometry": spec["geometry"], "start_endpoint": executor.endpoint(spec["start"]), "end_endpoint": executor.endpoint(spec["end"]), "risk_anchor_refs": sorted(spec["risk_refs"]), "source_locator_refs": sorted(spec["locator_refs"])}, "event_content_hash") for spec in source["events"]), key=lambda row: row["event_ref"])
                risk_spec = source["risk"]; risk = sealed({"risk_anchor_ref": risk_spec["risk_anchor_ref"], "risk_ref": risk_spec["risk_ref"], "risk_content_identity": risk_spec["content_identity"], "domain": risk_spec["domain"], "severity": risk_spec["severity"], "risk_type_zh": risk_spec["risk_type_zh"], "event_ref": risk_spec["event_ref"], "visit_ref": risk_spec["visit_ref"], "geometry": risk_spec["geometry"], "start_endpoint": executor.endpoint(risk_spec["start"]), "end_endpoint": executor.endpoint(risk_spec["end"]), "source_locator_refs": sorted(risk_spec["locator_refs"])}, "risk_anchor_content_hash")
                phase_spec = source["phase"]; phase_band = sealed({"phase_ref": phase_spec["phase_ref"], "phase_label_zh": phase_spec["label_zh"], "geometry": phase_spec["geometry"], "start_endpoint": executor.endpoint(phase_spec["start"]), "end_endpoint": executor.endpoint(phase_spec["end"]), "source_locator_refs": sorted(phase_spec["locator_refs"])}, "phase_content_hash")
                value = {"visit": visit, "events": events, "risk": risk, "phase": phase_band}
            elif semantic == "domains_pending_membership":
                temporal = stage["temporal_members"]; mh_event = next(row for row in temporal["events"] if row["domain"] == "mh")
                pending_event = sealed({"pending_ref": "pending::event::mh::1", "item_kind": "event", "item_ref": mh_event["event_ref"], "target_content_hash": mh_event["event_content_hash"], "domain": "mh", "start_endpoint": mh_event["start_endpoint"], "end_endpoint": mh_event["end_endpoint"], "source_locator_refs": mh_event["source_locator_refs"]}, "pending_content_hash")
                band = temporal["phase"]; pending_phase = sealed({"pending_ref": "pending::phase::treatment", "item_kind": "phase", "item_ref": band["phase_ref"], "target_content_hash": band["phase_content_hash"], "domain": None, "start_endpoint": band["start_endpoint"], "end_endpoint": band["end_endpoint"], "source_locator_refs": band["source_locator_refs"]}, "pending_content_hash")
                tracks = [sealed({"domain": row["domain"], "applicability_state": row["state"], "event_refs": sorted(row["event_refs"]), "risk_anchor_refs": sorted(row["risk_refs"])}, "track_content_hash") for row in source["domain_applicability"]]
                locators = stage["locators_revisions"]["locators"]; membership = sealed({"visit_refs": [temporal["visit"]["visit_ref"]], "event_refs": [row["event_ref"] for row in temporal["events"]], "risk_anchor_refs": [temporal["risk"]["risk_anchor_ref"]], "pending_date_refs": [pending_event["pending_ref"], pending_phase["pending_ref"]], "phase_refs": [band["phase_ref"]], "source_locator_refs": [row["locator_ref"] for row in locators]}, "membership_content_hash")
                value = {"pending": [pending_event, pending_phase], "tracks": tracks, "membership": membership}
            elif semantic == "axis":
                axis_spec = source["axis"]; value = sealed({"axis_ref": axis_spec["axis_ref"], "default_axis_mode": axis_spec["mode"], "timezone": axis_spec["timezone"], "study_day_anchor_event_ref": axis_spec["anchor_event_ref"] if axis_spec["study_day_enabled"] else None, "study_day_zero_exists": axis_spec["day_zero_convention"] == "anchor_day_zero" if axis_spec["study_day_enabled"] else None, "cutoff_endpoint": stage["identity_cutoff"]["cutoff"], "source_locator_refs": sorted(source["cutoff_binding"]["source_locator_refs"])}, "axis_content_hash")
            elif semantic == "projection":
                identity = stage["identity_cutoff"]["identity"]; locator_stage = stage["locators_revisions"]; temporal = stage["temporal_members"]; closure = stage["domains_pending_membership"]; axis = stage["axis"]
                projection_id = digest({"contract_id": SUBJECT, "schema_version": PARENT_VERSION, "scope_identity_hash": identity["identity_content_hash"], "membership_index_hash": closure["membership"]["membership_content_hash"], "axis_basis_hash": axis["axis_content_hash"]}); receipt_id = digest({"receipt_variant": "subject_temporal", "authority_contract_id": SUBJECT, "scope_identity_hash": identity["identity_content_hash"], "public_projection_id": projection_id})
                value = sealed({"contract_id": SUBJECT, "schema_version": PARENT_VERSION, "projection_id": projection_id, "receipt_ref": receipt_id, "scope_identity": identity, "fallback_policy": "fail_closed_no_nearest", "axis_basis": axis, "visits": [temporal["visit"]], "events": temporal["events"], "risk_anchors": [temporal["risk"]], "pending_date_items": closure["pending"], "phase_bands": [temporal["phase"]], "domain_tracks": closure["tracks"], "source_locators": locator_stage["locators"], "membership_index": closure["membership"]}, "projection_content_hash")
            elif semantic == "receipt":
                identity = stage["identity_cutoff"]["identity"]; projection = stage["projection"]; locator_stage = stage["locators_revisions"]; value = method_dispatch["receipt"]("subject_temporal", SUBJECT, identity, projection, locator_stage["pairs"], method_dispatch["subject_evaluation"](projection, [row["accepted_content_hash"] for row in locator_stage["pairs"]]))
            else:
                projection = stage["projection"]; receipt = stage["receipt"]; value = {"receipt": receipt, "projection": projection, "packet_content_hash": digest({"receipt_content_hash": receipt["receipt_content_hash"], "projection_content_hash": projection["projection_content_hash"]})}
        else:
            if semantic == "identity_locators_revisions":
                value = {"previous_identity": executor.scope(source["previous_scope"]), "current_identity": executor.scope(source["current_scope"]), "previous_locators": sorted((executor.locator(row) for row in source["previous_locator_specs"]), key=lambda row: row["locator_ref"]), "current_locators": sorted((executor.locator(row) for row in source["current_locator_specs"]), key=lambda row: row["locator_ref"]), "previous_pairs": executor.pairs(source["previous_revision_specs"]), "current_pairs": executor.pairs(source["current_revision_specs"])}
            elif semantic == "previous_threads":
                authority = stage["identity_locators_revisions"]; previous_by_ref = {row["locator_ref"]: row for row in authority["previous_locators"]}; source_by_ref = {row["locator_ref"]: row for row in source["previous_locator_specs"]}; threads = []
                for spec in source["thread_specs"]:
                    locator = previous_by_ref[spec["candidate_locator_ref"]]; locator_source = source_by_ref[spec["candidate_locator_ref"]]
                    if (locator_source["authority_thread_ref"], locator_source["authority_domain"], locator_source["entity_kind"], locator_source["entity_ref"]) != (spec["thread_ref"], spec["domain"], "candidate", spec["candidate_ref"]): fail("recipe evidence binding")
                    evidence = executor.evidence(f"identity-evidence::candidate::{spec['domain']}1", "candidate", spec["candidate_ref"], locator); entry = executor.entry(f"{spec['domain']}::1", 1, "reminder_created", source["previous_scope"]["snapshot_ref"], None, [], [], [evidence], [locator["locator_ref"]], spec["reminder_reason"], None)
                    threads.append(sealed({"thread_ref": spec["thread_ref"], "project_ref": authority["previous_identity"]["project_ref"], "site_ref": authority["previous_identity"]["site_ref"], "domain": spec["domain"], "subject_ref": authority["previous_identity"]["subject_ref"], "original_candidate_ref": spec["candidate_ref"], "candidate_content_identity": executor.entity_identity("candidate", spec["candidate_ref"], locator), "original_reminder_ref": entry["entry_id"], "history_entries": [entry], "evidence_locator_refs": [locator["locator_ref"]]}, "thread_content_hash"))
                value = sorted(threads, key=lambda row: row["thread_ref"])
            elif semantic == "previous_packet":
                authority = stage["identity_locators_revisions"]; value = executor.aemh_packet(authority["previous_identity"], stage["previous_threads"], authority["previous_locators"], authority["previous_pairs"], None)
            elif semantic == "current_threads":
                authority = stage["identity_locators_revisions"]; old_by_ref = {row["thread_ref"]: row for row in stage["previous_threads"]}; current_by_ref = {row["locator_ref"]: row for row in authority["current_locators"]}; current_by_entity = {(row["authority_thread_ref"], row["authority_domain"], row["entity_kind"], row["entity_ref"]): current_by_ref[row["locator_ref"]] for row in source["current_locator_specs"]}; decisions = {row["thread_ref"]: [] for row in source["thread_specs"]}
                for decision in source["decision_records"]: decisions[decision["thread_ref"]].append(decision)
                threads = []
                for spec in source["thread_specs"]:
                    old = old_by_ref[spec["thread_ref"]]; entries = copy.deepcopy(old["history_entries"]); retained = {spec["candidate_locator_ref"]}
                    for decision in decisions[spec["thread_ref"]]:
                        evidence = []; fact_ids = []
                        if decision["event_kind"] == "match_decided":
                            locator = current_by_entity[(spec["thread_ref"], spec["domain"], "candidate", spec["candidate_ref"])]; evidence.append(executor.evidence(f"identity-evidence::candidate::{spec['domain']}1", "candidate", spec["candidate_ref"], locator))
                        for fact in decision["fact_refs"]:
                            locator = current_by_entity[(spec["thread_ref"], spec["domain"], "later_fact", fact)]; evidence.append(executor.evidence(f"identity-evidence::later_fact::{digest(fact)[:12]}", "later_fact", fact, locator)); fact_ids.append(executor.entity_identity("later_fact", fact, locator)); retained.add(locator["locator_ref"])
                        for fact in decision["considered_fact_refs"]:
                            locator = current_by_entity[(spec["thread_ref"], spec["domain"], "considered_fact", fact)]; evidence.append(executor.evidence(f"identity-evidence::considered_fact::{digest(fact)[:12]}", "considered_fact", fact, locator)); retained.add(locator["locator_ref"])
                        entries.append(executor.entry(f"{spec['domain']}::1", len(entries) + 1, decision["event_kind"], source["current_scope"]["snapshot_ref"], decision["match_state"], decision["fact_refs"], fact_ids, evidence, sorted(retained), decision["reason_code"], entries[-1]["entry_hash"]))
                    threads.append(sealed({"thread_ref": spec["thread_ref"], "project_ref": authority["current_identity"]["project_ref"], "site_ref": authority["current_identity"]["site_ref"], "domain": spec["domain"], "subject_ref": authority["current_identity"]["subject_ref"], "original_candidate_ref": spec["candidate_ref"], "candidate_content_identity": old["candidate_content_identity"], "original_reminder_ref": old["original_reminder_ref"], "history_entries": entries, "evidence_locator_refs": sorted(retained)}, "thread_content_hash"))
                value = sorted(threads, key=lambda row: row["thread_ref"])
            elif semantic == "current_membership_prefix_cutoff":
                authority = stage["identity_locators_revisions"]; threads = stage["current_threads"]; previous = stage["previous_packet"]; later = sorted({ref for thread in threads for entry in thread["history_entries"] for ref in entry["later_fact_refs"]})
                membership = sealed({"thread_refs": [row["thread_ref"] for row in threads], "candidate_refs": sorted(row["original_candidate_ref"] for row in threads), "later_fact_refs": later, "source_locator_refs": [row["locator_ref"] for row in authority["current_locators"]]}, "membership_content_hash"); old = {row["thread_ref"]: row for row in previous["projection"]["threads"]}; prefixes = [sealed({"thread_ref": thread["thread_ref"], "accepted_prefix_seq": len(old[thread["thread_ref"]]["history_entries"]), "accepted_prefix_head_hash": old[thread["thread_ref"]]["history_entries"][-1]["entry_hash"], "previous_thread_content_hash": old[thread["thread_ref"]]["thread_content_hash"]}, "prefix_content_hash") for thread in threads]
                cutoff_locator = next(row["locator_ref"] for row in authority["current_locators"] if row["authority_entity_kind"] == "candidate" and row["authority_entity_ref"] == "candidate::suspected-ae::1"); cutoff = sealed({"state": "present", "exact_date": authority["current_identity"]["cutoff_ref"], "source_locator_refs": [cutoff_locator]}, "cutoff_content_hash"); value = {"membership": membership, "prefixes": prefixes, "cutoff": cutoff}
            elif semantic == "projection":
                authority = stage["identity_locators_revisions"]; closure = stage["current_membership_prefix_cutoff"]; previous = stage["previous_packet"]; identity = authority["current_identity"]; projection_id = digest({"contract_id": AEMH, "schema_version": PARENT_VERSION, "scope_identity_hash": identity["identity_content_hash"], "membership_index_hash": closure["membership"]["membership_content_hash"]}); receipt_id = digest({"receipt_variant": "aemh_match_history", "authority_contract_id": AEMH, "scope_identity_hash": identity["identity_content_hash"], "public_projection_id": projection_id})
                value = sealed({"contract_id": AEMH, "schema_version": PARENT_VERSION, "projection_id": projection_id, "receipt_ref": receipt_id, "scope_identity": identity, "cutoff_endpoint": closure["cutoff"], "fallback_policy": "fail_closed_no_nearest", "previous_projection_ref": previous["projection"]["projection_id"], "previous_projection_content_hash": previous["projection"]["projection_content_hash"], "accepted_thread_prefixes": closure["prefixes"], "threads": stage["current_threads"], "source_locators": authority["current_locators"], "membership_index": closure["membership"]}, "projection_content_hash")
            elif semantic == "receipt":
                authority = stage["identity_locators_revisions"]; projection = stage["projection"]; value = method_dispatch["receipt"]("aemh_match_history", AEMH, authority["current_identity"], projection, authority["current_pairs"], method_dispatch["aemh_evaluation"](projection, [row["accepted_content_hash"] for row in authority["current_pairs"]]))
            else:
                projection = stage["projection"]; receipt = stage["receipt"]; current = {"receipt": receipt, "projection": projection, "packet_content_hash": digest({"receipt_content_hash": receipt["receipt_content_hash"], "projection_content_hash": projection["projection_content_hash"]})}; value = {"previous": stage["previous_packet"], "current": current}
        sealed_output = seal_handlers[seal_node["op"]](recipe, seal_node, value)
        outputs[recipe["nodes"][1]["outputs"][0]] = sealed_output
        stage[semantic] = outputs[recipe["nodes"][1]["outputs"][0]]["value"]
    final = stage["packet"]
    return (final if target == SUBJECT else (final["previous"], final["current"])), outputs


def verify_emitters(registry: dict[str, Any], manifest: dict[str, Any], schema: dict[str, Any], fixtures: dict[str, Any] | None = None) -> None:
    if registry["registry_content_hash"] != digest({key: value for key, value in registry.items() if key != "registry_content_hash"}): fail("emitter registry hash")
    if registry["registry_content_hash"] != manifest["emitter_recipe_registry_content_hash"]: fail("emitter manifest pin")
    if len(registry["preserved_v01_recipes"]) != 2 or len(registry["executable_v02_recipes"]) != 16 or len(registry["supersession_rules"]) != 24: fail("recipe/rule counts")
    if {row["recipe_id"] for row in registry["preserved_v01_recipes"]} != {"recipe.external_registry_receipt_resolution", "recipe.parent_semantic_snapshot_immutability"}: fail("preserved recipes")
    issues = recipe_ir_issues(registry, schema)
    if issues: fail("recipe IR: " + "|".join(issues))
    mapping_ids = set(registry["affected_mapping_content_hashes"]); realized = set()
    for rule in registry["supersession_rules"]:
        if rule["required_manifest_sha256"] != manifest["supersedes"]["manifest_sha256"] or rule["execution_profile"] != PROFILE or set(rule["target_contracts"]) != {SUBJECT, AEMH}: fail("supersession precondition")
        realized.update(rule["affected_mapping_ids"])
    if realized != mapping_ids or len(mapping_ids) != 119 or registry["affected_mapping_count"] != 119: fail("affected mapping closure")
    if fixtures is not None:
        bundles = {row["authority_input"]["target_contract"]: row["authority_input"] for row in fixtures["baselines"]}
        subject_result, subject_outputs = execute_independent_recipe_dag(bundles[SUBJECT], registry)
        aemh_result, aemh_outputs = execute_independent_recipe_dag(bundles[AEMH], registry)
        legacy_subject = IndependentExecutor(bundles[SUBJECT]).subject_packet()
        legacy_aemh = IndependentExecutor(bundles[AEMH]).aemh_packets()
        if subject_result != legacy_subject or aemh_result != legacy_aemh:
            fail("recipe DAG full-graph equivalence")
        all_outputs = {**subject_outputs, **aemh_outputs}
        if len(all_outputs) != 16 or any(row["content_hash"] != digest(row["value"]) for row in all_outputs.values()):
            fail("recipe 16/16 seal execution")
        dispatch_issues, method_dispatch, op_methods = independent_recipe_dispatch_issues(registry, IndependentExecutor(bundles[SUBJECT]))
        if dispatch_issues or len(op_methods) != 32: fail(f"recipe 16-op reachability/signatures {dispatch_issues}")
        missing_dispatch = dict(method_dispatch); missing_dispatch.pop("subject_evaluation")
        missing_issues, _, _ = independent_recipe_dispatch_issues(registry, IndependentExecutor(bundles[SUBJECT]), missing_dispatch)
        if "TPA_V02_INDEPENDENT_DISPATCH_METHOD_SET" not in missing_issues or "TPA_V02_INDEPENDENT_DISPATCH_METHOD_MISSING:subject_evaluation" not in missing_issues:
            fail(f"recipe missing method fail-closed {missing_issues}")
        unknown_dispatch_registry = copy.deepcopy(registry)
        unknown_dispatch_registry["executable_v02_recipes"][0]["nodes"][0]["op"] = "unknown_op"
        unknown_issues, _, _ = independent_recipe_dispatch_issues(unknown_dispatch_registry, IndependentExecutor(bundles[SUBJECT]))
        if "TPA_V02_INDEPENDENT_DISPATCH_OP_SET" not in unknown_issues: fail(f"recipe unknown op fail-closed {unknown_issues}")

    def refresh_recipe(changed: dict[str, Any], recipe: dict[str, Any]) -> None:
        if len(recipe["nodes"]) == 2:
            first, second = recipe["nodes"]
            params = first["params"]
            second["params"] = copy.deepcopy(params)
            inputs = [*params.get("authority_input_pointers", []), *params.get("prior_recipe_output_refs", [])]
            recipe["inputs"] = copy.deepcopy(inputs)
            first["inputs"] = copy.deepcopy(inputs)
            second["inputs"] = copy.deepcopy(first["outputs"])
            recipe["dependency_edges"] = [{"from": item, "to": first["node_id"]} for item in inputs] + [{"from": first["node_id"], "to": second["node_id"]}]
        recipe["recipe_content_hash"] = digest({key: value for key, value in recipe.items() if key != "recipe_content_hash"})
        changed["registry_content_hash"] = digest({key: value for key, value in changed.items() if key != "registry_content_hash"})

    attacks = []
    for mutate_ir in ("arbitrary_param", "unknown_op", "cross_target", "same_target_substitution", "recipe_id", "phase", "target", "output_name", "node_output", "missing_node", "extra_node", "reordered", "cycle"):
        changed = copy.deepcopy(registry)
        recipe = changed["executable_v02_recipes"][0]
        if mutate_ir == "arbitrary_param": recipe["nodes"][0]["params"]["arbitrary"] = True
        elif mutate_ir == "unknown_op": recipe["nodes"][0]["op"] = "unknown_op"
        elif mutate_ir == "cross_target":
            recipe = changed["executable_v02_recipes"][4]
            recipe["nodes"][0]["params"]["prior_recipe_output_refs"][0] = "recipe.v02.aemh_identity_locators_revisions.sealed"
        elif mutate_ir == "same_target_substitution":
            recipe = changed["executable_v02_recipes"][4]
            recipe["nodes"][0]["params"]["prior_recipe_output_refs"][0] = "recipe.v02.subject_temporal_members.sealed"
        elif mutate_ir == "recipe_id": recipe["recipe_id"] = "recipe.v02.subject_identity_cutoff_rebound"
        elif mutate_ir == "phase":
            recipe["nodes"][0]["params"]["phase"] = "axis"
            recipe["nodes"][0]["op"] = "emit_subject_axis"
            recipe["nodes"][1]["op"] = "seal_subject_axis"
        elif mutate_ir == "target":
            recipe["target_contract"] = AEMH
            recipe["nodes"][0]["op"] = "emit_aemh_identity_cutoff"
            recipe["nodes"][1]["op"] = "seal_aemh_identity_cutoff"
        elif mutate_ir == "output_name":
            recipe["nodes"][0]["params"]["output_name"] = "recipe.v02.subject_identity_cutoff.alternate"
            recipe["nodes"][0]["outputs"] = ["recipe.v02.subject_identity_cutoff.alternate"]
        elif mutate_ir == "node_output": recipe["nodes"][1]["outputs"] = ["recipe.v02.subject_identity_cutoff.resealed"]
        elif mutate_ir == "missing_node": recipe["nodes"] = recipe["nodes"][:1]
        elif mutate_ir == "extra_node": recipe["nodes"].append(copy.deepcopy(recipe["nodes"][-1]))
        elif mutate_ir == "reordered": recipe["nodes"].reverse()
        else: recipe["dependency_edges"].append({"from": recipe["nodes"][1]["node_id"], "to": recipe["nodes"][0]["node_id"]})
        if mutate_ir in {"missing_node", "extra_node", "reordered", "cycle"}:
            recipe["recipe_content_hash"] = digest({key: value for key, value in recipe.items() if key != "recipe_content_hash"})
            changed["registry_content_hash"] = digest({key: value for key, value in changed.items() if key != "registry_content_hash"})
        else:
            refresh_recipe(changed, recipe)
        attacks.append(bool(recipe_ir_issues(changed, schema)))
    if attacks != [True] * 13: fail(f"recipe fully resealed attacks {attacks}")
    if fixtures is not None:
        swapped = copy.deepcopy(registry)
        first_recipe, second_recipe = swapped["executable_v02_recipes"][:2]
        first_recipe["nodes"][0]["op"], second_recipe["nodes"][0]["op"] = second_recipe["nodes"][0]["op"], first_recipe["nodes"][0]["op"]
        first_recipe["nodes"][1]["op"], second_recipe["nodes"][1]["op"] = second_recipe["nodes"][1]["op"], first_recipe["nodes"][1]["op"]
        for recipe in (first_recipe, second_recipe):
            recipe["recipe_content_hash"] = digest({key: value for key, value in recipe.items() if key != "recipe_content_hash"})
        swapped["registry_content_hash"] = digest({key: value for key, value in swapped.items() if key != "registry_content_hash"})
        if not recipe_ir_issues(swapped, schema): fail("fully resealed recipe op swap outer gate")
        subject_bundle = next(row["authority_input"] for row in fixtures["baselines"] if row["authority_input"]["target_contract"] == SUBJECT)
        try:
            execute_independent_recipe_dag(subject_bundle, swapped)
        except SystemExit as exc:
            if "handler binding" not in str(exc): fail(f"recipe op swap wrong direct failure {exc}")
        else:
            fail("fully resealed recipe op swap direct interpreter")


def forbidden_candidate_key(value: Any) -> str | None:
    forbidden = {"packet", "expected_packet", "expected_hash", "expected_error", "acceptance_token", "target_output"}
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower()
            packet_contaminant = "packet" in normalized and any(token in normalized for token in ("candidate", "parent", "expected", "payload", "hash", "fixture", "copy", "source"))
            if key in forbidden or packet_contaminant: return key
            found = forbidden_candidate_key(child)
            if found: return found
    elif isinstance(value, list):
        for child in value:
            found = forbidden_candidate_key(child)
            if found: return found
    return None


def static_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str): return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = static_string(node.left), static_string(node.right)
        return left + right if left is not None and right is not None else None
    return None


def has_parent_packet_copy_entry(path: pathlib.Path) -> bool:
    tree = ast.parse(path.read_bytes(), filename=str(path))
    forbidden_name = "base_" + "inputs.json"
    reader_names = {"load", "loads", "open", "read_text", "read_bytes"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call): continue
        name = node.func.attr if isinstance(node.func, ast.Attribute) else (node.func.id if isinstance(node.func, ast.Name) else "")
        if name not in reader_names: continue
        for child in ast.walk(node):
            value = static_string(child)
            if value is not None and forbidden_name in value:
                return True
    return False


def validate_parent(target: str, packet: dict[str, Any], previous: dict[str, Any] | None = None) -> list[str]:
    parent = parent_module()
    if target == SUBJECT:
        return parent.validate_subject(packet, load(SUBJECT_SCHEMA))
    return parent.validate_aemh(packet, load(AEMH_SCHEMA), previous)


def verify_study_day_source_controls(authority_bundle: dict[str, Any]) -> None:
    controls = (
        ("anchor_date", "/source/events/0/start/exact_date", "2026-07-31"),
        ("target_date", "/source/events/0/end/exact_date", "2026-08-03"),
        ("convention", "/source/axis/day_zero_convention", "anchor_day_zero"),
    )
    for label, path, value in controls:
        changed = copy.deepcopy(authority_bundle)
        pointer_replace(changed, path, value)
        recompute_subject_study_days(changed["source"])
        changed["bundle_content_identity"] = digest({key: item for key, item in changed.items() if key != "bundle_content_identity"})
        packet = IndependentExecutor(changed).subject_packet()
        errors = validate_parent(SUBJECT, packet)
        if errors:
            fail(f"study-day positive control {label}: {errors}")
    wrong_leaf = copy.deepcopy(authority_bundle)
    wrong_leaf["source"]["events"][0]["end"]["study_day"] += 1
    wrong_leaf["bundle_content_identity"] = digest({key: item for key, item in wrong_leaf.items() if key != "bundle_content_identity"})
    try:
        IndependentExecutor(wrong_leaf).subject_packet()
    except SystemExit as exc:
        if "study-day authority input mismatch" not in str(exc):
            fail(f"study-day single-leaf control wrong failure: {exc}")
    else:
        fail("study-day single-leaf control inactive")


def cutoff_binding_closed(packet: dict[str, Any], binding: dict[str, Any]) -> bool:
    projection = packet["projection"]
    scope = projection["scope_identity"]
    endpoint = projection["axis_basis"]["cutoff_endpoint"]
    expected_state = "exact" if binding["state"] == "present" else "missing"
    expected_projectable = binding["state"] == "present"
    return (
        packet["receipt"]["scope_identity"] == scope
        and scope["cutoff_state"] == binding["state"]
        and scope["cutoff_ref"] == binding["exact_date"]
        and endpoint["state"] == expected_state
        and endpoint["exact_date"] == binding["exact_date"]
        and endpoint["range_start"] is None
        and endpoint["range_end"] is None
        and endpoint["candidate_values"] == []
        and endpoint["main_axis_projectable"] is expected_projectable
        and endpoint["range_projection_authorized"] is expected_projectable
        and endpoint["study_day"] is None
        and endpoint["source_locator_refs"] == sorted(binding["source_locator_refs"])
        and projection["axis_basis"]["source_locator_refs"] == sorted(binding["source_locator_refs"])
    )


def verify_cutoff_binding_controls(authority_bundle: dict[str, Any], baseline: dict[str, Any]) -> None:
    binding = authority_bundle["source"]["cutoff_binding"]
    if not cutoff_binding_closed(baseline, binding): fail("cutoff baseline closure")
    changed = copy.deepcopy(authority_bundle)
    changed["source"]["cutoff_binding"]["exact_date"] = "2026-08-18"
    changed["bundle_content_identity"] = digest({key: item for key, item in changed.items() if key != "bundle_content_identity"})
    changed_packet = IndependentExecutor(changed).subject_packet()
    changed_errors = validate_parent(SUBJECT, changed_packet)
    if changed_errors or not cutoff_binding_closed(changed_packet, changed["source"]["cutoff_binding"]):
        fail(f"cutoff full-chain change control: {changed_errors}")
    state_drift = copy.deepcopy(baseline)
    state_drift["projection"]["scope_identity"]["cutoff_state"] = "absent"
    state_errors = validate_parent(SUBJECT, state_drift)
    if cutoff_binding_closed(state_drift, binding) or not {"PUB_CUTOFF_STATE_MISMATCH", "PUB_IDENTITY_CUTOFF_MISMATCH"} <= set(state_errors):
        fail(f"cutoff state drift control: {state_errors}")
    date_drift = copy.deepcopy(baseline)
    date_drift["projection"]["axis_basis"]["cutoff_endpoint"]["exact_date"] = "2026-08-17"
    date_errors = validate_parent(SUBJECT, date_drift)
    if cutoff_binding_closed(date_drift, binding) or not {"PUB_CUTOFF_STATE_MISMATCH", "PUB_IDENTITY_CUTOFF_MISMATCH"} <= set(date_errors):
        fail(f"cutoff date drift control: {date_errors}")
    ref_drift = copy.deepcopy(baseline)
    ref_drift["projection"]["axis_basis"]["cutoff_endpoint"]["source_locator_refs"] = ["locator::event::ae1"]
    if cutoff_binding_closed(ref_drift, binding): fail("cutoff ref drift control inactive")
    mixed = copy.deepcopy(baseline)
    mixed["projection"]["scope_identity"]["cutoff_state"] = "absent"
    mixed["projection"]["axis_basis"]["cutoff_endpoint"]["exact_date"] = "2026-08-17"
    mixed["projection"]["axis_basis"]["cutoff_endpoint"]["source_locator_refs"] = ["locator::event::ae1"]
    mixed_errors = validate_parent(SUBJECT, mixed)
    if cutoff_binding_closed(mixed, binding) or not {"PUB_CUTOFF_STATE_MISMATCH", "PUB_IDENTITY_CUTOFF_MISMATCH"} <= set(mixed_errors):
        fail(f"cutoff mixed drift control: {mixed_errors}")


def evidence_authority_closed(authority_bundle: dict[str, Any], previous: dict[str, Any], current: dict[str, Any]) -> bool:
    source = authority_bundle["source"]
    authority_locators = {(row["snapshot_ref"], row["locator_ref"]): row for row in [*source["previous_locator_specs"], *source["current_locator_specs"]]}
    output_locators = {(row["snapshot_ref"], row["locator_ref"]): row for packet in (previous, current) for row in packet["projection"]["source_locators"]}
    pair_sets = {
        source["previous_scope"]["snapshot_ref"]: {row["revision_id"]: row for row in previous["receipt"]["source_revision_content_pairs"]},
        source["current_scope"]["snapshot_ref"]: {row["revision_id"]: row for row in current["receipt"]["source_revision_content_pairs"]},
    }
    for packet in (previous, current):
        for thread in packet["projection"]["threads"]:
            for entry in thread["history_entries"]:
                for evidence in entry["identity_evidence"]:
                    key = (entry["snapshot_ref"], evidence["source_locator_ref"])
                    authority = authority_locators.get(key); locator = output_locators.get(key)
                    if authority is None or locator is None: return False
                    pair = pair_sets[entry["snapshot_ref"]].get(authority["revision_ref"])
                    expected_identity = digest({"entity_kind": evidence["evidence_kind"], "entity_ref": evidence["entity_ref"], "source_locator_ref": evidence["source_locator_ref"], "source_raw_payload_hash": evidence["source_raw_payload_hash"]})
                    if (
                        authority["authority_thread_ref"] != thread["thread_ref"]
                        or authority["authority_domain"] != thread["domain"]
                        or authority["entity_kind"] != evidence["evidence_kind"]
                        or authority["entity_ref"] != evidence["entity_ref"]
                        or pair is None
                        or authority["locator_ref"] not in pair["locator_refs"]
                        or pair["accepted_content_hash"] != authority["revision_content_identity"]
                        or evidence["source_locator_content_hash"] != locator["locator_content_hash"]
                        or evidence["source_raw_payload_hash"] != locator["raw_payload_hash"]
                        or evidence["entity_content_identity"] != expected_identity
                        or evidence["evidence_content_hash"] != digest({key: value for key, value in evidence.items() if key != "evidence_content_hash"})
                    ):
                        return False
    return True


def resealed_wrong_entity_packet(current: dict[str, Any]) -> dict[str, Any]:
    changed = copy.deepcopy(current)
    thread = changed["projection"]["threads"][0]
    entry = thread["history_entries"][1]
    evidence = next(row for row in entry["identity_evidence"] if row["evidence_kind"] == "later_fact")
    evidence["entity_ref"] = "fact::reported-ae::wrong-entity"
    evidence["entity_content_identity"] = digest({"entity_kind": evidence["evidence_kind"], "entity_ref": evidence["entity_ref"], "source_locator_ref": evidence["source_locator_ref"], "source_raw_payload_hash": evidence["source_raw_payload_hash"]})
    evidence["evidence_content_hash"] = digest({key: value for key, value in evidence.items() if key != "evidence_content_hash"})
    for index in range(1, len(thread["history_entries"])):
        row = thread["history_entries"][index]
        row["prior_entry_hash"] = thread["history_entries"][index - 1]["entry_hash"]
        row["entry_hash"] = digest({key: value for key, value in row.items() if key != "entry_hash"})
    thread["thread_content_hash"] = digest({key: value for key, value in thread.items() if key != "thread_content_hash"})
    projection = changed["projection"]
    projection["projection_content_hash"] = digest({key: value for key, value in projection.items() if key != "projection_content_hash"})
    receipt = changed["receipt"]
    receipt["public_projection_content_hash"] = projection["projection_content_hash"]
    receipt["evaluation_content_identities"] = IndependentExecutor.aemh_evaluation(projection, [row["accepted_content_hash"] for row in receipt["source_revision_content_pairs"]])
    receipt["receipt_content_hash"] = digest({key: value for key, value in receipt.items() if key != "receipt_content_hash"})
    changed["packet_content_hash"] = digest({"receipt_content_hash": receipt["receipt_content_hash"], "projection_content_hash": projection["projection_content_hash"]})
    return changed


def verify_evidence_controls(authority_bundle: dict[str, Any], previous: dict[str, Any], current: dict[str, Any]) -> None:
    if not evidence_authority_closed(authority_bundle, previous, current): fail("baseline evidence authority closure")
    output_probes = (
        ("entity_ref", "/projection/threads/0/history_entries/1/identity_evidence/1/entity_ref", "wrong"),
        ("content_identity", "/projection/threads/0/history_entries/1/identity_evidence/1/entity_content_identity", "0" * 64),
        ("locator", "/projection/threads/0/history_entries/1/identity_evidence/1/source_locator_ref", "locator::reminder::mh1"),
        ("source_pair", "/receipt/source_revision_content_pairs/0/locator_refs", []),
    )
    for label, path, value in output_probes:
        errors = validate_parent(AEMH, mutate(current, path, value), previous)
        if not errors: fail(f"evidence {label} drift control inactive")
    for label, field, value in (
        ("thread", "authority_thread_ref", "aemh-thread::mh::1"),
        ("domain", "authority_domain", "mh"),
        ("wrong_entity", "entity_ref", "fact::reported-ae::wrong-entity"),
    ):
        changed = copy.deepcopy(authority_bundle)
        locator = next(row for row in changed["source"]["current_locator_specs"] if row["locator_ref"] == "locator::fact::ae1")
        locator[field] = value
        changed["bundle_content_identity"] = digest({key: item for key, item in changed.items() if key != "bundle_content_identity"})
        try:
            IndependentExecutor(changed).aemh_packets()
        except SystemExit as exc:
            if "evidence authority binding" not in str(exc): fail(f"evidence {label} wrong failure: {exc}")
        else:
            fail(f"evidence {label} source control inactive")
    resealed = resealed_wrong_entity_packet(current)
    resealed_errors = validate_parent(AEMH, resealed, previous)
    if "AEMH_IDENTITY_EVIDENCE_MISMATCH" not in resealed_errors or "PUB_HASH_MISMATCH" in resealed_errors:
        fail(f"fully resealed wrong entity control: {resealed_errors}")


def verify_fixtures(registry: dict[str, Any], manifest: dict[str, Any], emitters: dict[str, Any]) -> dict[str, Any]:
    if registry["registry_content_hash"] != digest({key: value for key, value in registry.items() if key != "registry_content_hash"}) or registry["registry_content_hash"] != manifest["full_graph_fixture_registry_content_hash"]: fail("fixture registry hash")
    if registry["baseline_valid_count"] != 2 or registry["baseline_error_count"] != 0 or registry["positive_valid_count"] != 10 or registry["positive_error_count"] != 0: fail("fixture closure counts")
    by_ref = {row["fixture_ref"]: row for row in registry["baselines"]}
    subject_row, aemh_row = by_ref["fixture.subject.full.v02"], by_ref["fixture.aemh.full.v02"]
    schema = load(SCHEMA)
    for row in (subject_row, aemh_row):
        found = forbidden_candidate_key(row["authority_input"])
        if found: fail(f"candidate forbidden key {found}")
        issues = authority_issues(row["authority_input"], schema)
        if issues: fail("baseline typed authority: " + "|".join(issues))
    authority_attacks = []
    for attack in ("root_extra", "nested_extra", "contract", "schema", "scope", "profile", "target", "v01_pin", "nested_type", "nested_enum", "cardinality"):
        changed = copy.deepcopy(subject_row["authority_input"])
        if attack == "root_extra": changed["extra"] = True
        elif attack == "nested_extra": changed["source"]["visit"]["extra"] = True
        elif attack == "contract": changed["contract_id"] = "wrong"
        elif attack == "schema": changed["schema_version"] = "wrong"
        elif attack == "scope": changed["authority_scope"] = "production"
        elif attack == "profile": changed["execution_profile"] = "partial"
        elif attack == "target": changed["target_contract"] = AEMH
        elif attack == "v01_pin": changed["temporal_v01_manifest_sha256"] = "0" * 64
        elif attack == "nested_type": changed["source"]["events"] = "wrong"
        elif attack == "nested_enum": changed["source"]["axis"]["mode"] = "other"
        else: changed["source"]["domain_applicability"] = changed["source"]["domain_applicability"][:-1]
        changed["bundle_content_identity"] = digest({key: value for key, value in changed.items() if key != "bundle_content_identity"})
        authority_attacks.append(bool(authority_issues(changed, schema)))
    if authority_attacks != [True] * 11: fail(f"fully resealed typed authority attacks {authority_attacks}")
    variant_attacks = []
    subject_authority = subject_row["authority_input"]
    aemh_authority = aemh_row["authority_input"]
    for label, original, mutate_bundle in (
        ("subject_to_aemh_target", subject_authority, lambda item: item.update({"target_contract": AEMH})),
        ("aemh_to_subject_target", aemh_authority, lambda item: item.update({"target_contract": SUBJECT})),
        ("subject_target_aemh_source", subject_authority, lambda item: item.update({"source": copy.deepcopy(aemh_authority["source"])})),
        ("aemh_target_subject_source", aemh_authority, lambda item: item.update({"source": copy.deepcopy(subject_authority["source"])})),
        ("extra_variant_field", subject_authority, lambda item: item["source"].update({"variant_extra": True})),
        ("missing_variant_field", subject_authority, lambda item: item["source"].pop("visit")),
    ):
        changed = copy.deepcopy(original)
        mutate_bundle(changed)
        changed["bundle_content_identity"] = digest({key: value for key, value in changed.items() if key != "bundle_content_identity"})
        first = authority_issues(changed, schema)
        second = authority_issues(copy.deepcopy(changed), schema)
        if not first or first != second:
            fail(f"typed authority variant fail-closed {label}: {first} / {second}")
        variant_attacks.append(first[0])
    if len(variant_attacks) != 6: fail("typed authority variant attack closure")
    subject, subject_recipe_outputs = execute_independent_recipe_dag(subject_row["authority_input"], emitters)
    if len(subject_recipe_outputs) != 8 or subject != IndependentExecutor(subject_row["authority_input"]).subject_packet():
        fail("subject recipe baseline equivalence")
    if validate_parent(SUBJECT, subject): fail("subject baseline parent errors")
    if subject["packet_content_hash"] != subject_row["observation"]["packet_content_hash"] or subject["projection"]["projection_content_hash"] != subject_row["observation"]["projection_content_hash"]: fail("subject observation")
    card = subject_row["observation"]["cardinalities"]
    expected_card = {"scope": 1, "visibility": 1, "axis": 1, "locators": 4, "revision_pairs": 1, "endpoints": 8, "visits": 1, "events": 2, "risks": 1, "phases": 1, "pending": 2, "domains": 8, "membership": 1, "projection": 1, "receipt": 1, "packet": 1}
    if card != expected_card: fail("subject cardinalities")
    if [row["domain"] for row in subject["projection"]["domain_tracks"]] != DOMAINS: fail("domain order")
    if [row["applicability_state"] for row in subject["projection"]["domain_tracks"]] != ["applicable", "applicable", *(["not_provided"] * 6)]: fail("domain applicability")
    verify_study_day_source_controls(subject_row["authority_input"])
    verify_cutoff_binding_controls(subject_row["authority_input"], subject)
    aemh_result, aemh_recipe_outputs = execute_independent_recipe_dag(aemh_row["authority_input"], emitters)
    previous, current = aemh_result
    if len(aemh_recipe_outputs) != 8 or (previous, current) != IndependentExecutor(aemh_row["authority_input"]).aemh_packets():
        fail("aemh recipe baseline equivalence")
    if validate_parent(AEMH, previous, None) or validate_parent(AEMH, current, previous): fail("aemh baseline parent errors")
    observed = aemh_row["observation"]
    if (previous["packet_content_hash"], current["packet_content_hash"], previous["projection"]["projection_content_hash"], current["projection"]["projection_content_hash"]) != (observed["previous_packet_content_hash"], observed["current_packet_content_hash"], observed["previous_projection_content_hash"], observed["current_projection_content_hash"]): fail("aemh observation")
    old_threads = {row["thread_ref"]: row for row in previous["projection"]["threads"]}; new_threads = {row["thread_ref"]: row for row in current["projection"]["threads"]}
    for ref, old in old_threads.items():
        if new_threads[ref]["history_entries"][:len(old["history_entries"])] != old["history_entries"]: fail("prefix bytes")
    verify_evidence_controls(aemh_row["authority_input"], previous, current)
    positive_ids = [row["case_id"] for row in registry["positive_paths"]]
    if positive_ids != ["R5C-109", "R5C-110", "R5C-116", "R5C-157", "R5C-158", "R5C-159", "R5C-160", "R5C-161", "R5C-162", "R5C-163"]: fail("positive paths")
    bases = registry["positive_base_inputs"]
    if set(bases) != {"positive.subject.axis.base", "positive.aemh.decision.seed"}: fail("positive base inventory")
    for base_ref, authority_bundle in bases.items():
        issues = authority_issues(authority_bundle, schema)
        if issues: fail(f"positive base typed authority {base_ref}: {issues}")
    challenge_rows = {row["case_id"]: row for row in load(PARENT_CHALLENGES)["inherited_cases"]}
    positive_bundles = {}
    positive_specs = {}
    for row in registry["positive_paths"]:
        if row["authority_input_ref"] not in bases: fail(f"positive base ref {row['case_id']}")
        if not row["source_transformation"]: fail(f"empty positive transformation {row['case_id']}")
        for expected_sequence, operation in enumerate(row["source_transformation"], start=1):
            typed = validate_typed(operation, "SourceOperationV02", schema)
            if typed or operation["sequence"] != expected_sequence: fail(f"positive transform typed/order {row['case_id']}:{typed}")
        transformed, replay_issues = independent_replay_source_operations(bases[row["authority_input_ref"]], row["source_transformation"], row["authority_input_content_identity"])
        if replay_issues: fail(f"positive transform replay {row['case_id']}:{replay_issues}")
        if row["case_id"] == "R5C-110":
            pre_from_post = copy.deepcopy(row["source_transformation"]); pre_from_post[0]["pre_value"] = copy.deepcopy(pre_from_post[0]["post_value"])
            wrong_order = copy.deepcopy(row["source_transformation"]); wrong_order[0], wrong_order[1] = wrong_order[1], wrong_order[0]
            missing_step = copy.deepcopy(row["source_transformation"][:-1])
            controls = [
                independent_replay_source_operations(bases[row["authority_input_ref"]], pre_from_post, row["authority_input_content_identity"])[1],
                independent_replay_source_operations(bases[row["authority_input_ref"]], wrong_order, row["authority_input_content_identity"])[1],
                independent_replay_source_operations(bases[row["authority_input_ref"]], missing_step, row["authority_input_content_identity"])[1],
            ]
            if any(not issues for issues in controls): fail(f"R5C-110 linked-operation negative controls {controls}")
        rule_id = challenge_rows[row["case_id"]]["stage_oracle_contract"]["rule_id"]
        positive_bundles[rule_id] = transformed
        positive_specs[rule_id] = {"base_ref": row["authority_input_ref"], "operations": row["source_transformation"]}
        if row["contract"] == SUBJECT:
            packet, stage_outputs = execute_independent_recipe_dag(transformed, emitters)
            if len(stage_outputs) != 8 or packet != IndependentExecutor(transformed).subject_packet(): fail(f"positive recipe equivalence {row['case_id']}")
            errors = validate_parent(SUBJECT, packet); projection_hash = packet["projection"]["projection_content_hash"]
        else:
            aemh_positive, stage_outputs = execute_independent_recipe_dag(transformed, emitters)
            old, packet = aemh_positive
            if len(stage_outputs) != 8 or (old, packet) != IndependentExecutor(transformed).aemh_packets(): fail(f"positive recipe equivalence {row['case_id']}")
            errors = [*validate_parent(AEMH, old, None), *validate_parent(AEMH, packet, old)]; projection_hash = packet["projection"]["projection_content_hash"]
            if row["observation"]["previous_prefix_byte_identical"] is not True: fail(f"positive prefix observation {row['case_id']}")
        if errors or packet["packet_content_hash"] != row["observation"]["packet_content_hash"] or projection_hash != row["observation"]["projection_content_hash"]: fail(f"positive graph {row['case_id']} {errors}")
    return {"subject": subject, "aemh_previous": previous, "aemh_current": current, "subject_bundle": subject_row["authority_input"], "aemh_bundle": aemh_row["authority_input"], "positive_bundles": positive_bundles, "positive_specs": positive_specs}


def independent_inherited_reject_adapter(rule_id: str, target: str) -> tuple[str, dict[str, Any]]:
    invalid = f"invalid::{rule_id}"
    if target == SUBJECT:
        if rule_id.startswith("visit_semantics."):
            path = {
                "nominal_date": "/projection/visits/0/nominal_endpoint/state", "actual_date": "/projection/visits/0/actual_endpoint/state",
                "unscheduled_visit": "/projection/visits/0/visit_kind", "between_visit_event": "/projection/events/0/geometry",
                "phase_band": "/projection/phase_bands/0/geometry", "first_dose": "/projection/events/0/start_endpoint/state",
                "last_dose": "/projection/events/0/end_endpoint/state", "cutoff_marker": "/projection/axis_basis/cutoff_endpoint/state",
            }[rule_id.split(".", 1)[1]]
        elif rule_id.startswith("axis_conversion."):
            suffix = rule_id.split(".", 1)[1]
            path = {
                "study_day_missing_anchor": "/projection/axis_basis/study_day_anchor_event_ref", "timezone_boundary": "/projection/axis_basis/default_axis_mode",
                "partial_anchor": "/projection/events/0/start_endpoint/state", "phase_anchor": "/projection/axis_basis/study_day_anchor_event_ref",
                "cutoff_anchor": "/projection/axis_basis/study_day_anchor_event_ref",
            }[suffix]
            if suffix == "study_day_missing_anchor": invalid = None
        elif rule_id.startswith("uncertain_dates."):
            path = {
                "partial_start": "/projection/events/1/start_endpoint/state", "partial_end": "/projection/events/1/end_endpoint/state",
                "conflicted_start": "/projection/events/1/start_endpoint/state", "conflicted_end": "/projection/events/1/end_endpoint/state",
                "missing_point": "/projection/risk_anchors/0/start_endpoint/state", "missing_interval": "/projection/events/0/start_endpoint/state",
                "open_start": "/projection/events/0/geometry", "open_end": "/projection/events/1/geometry",
            }[rule_id.split(".", 1)[1]]
        elif rule_id.startswith("eight_domain_adaptation."):
            ordinal = sorted([
                "ae_event", "ae_risk", "background_mapping", "cm_event", "efficacy_subtype", "hospital_event", "ip_event", "lab_event",
                "mh_event", "mh_risk", "non_drug_mapping", "not_applicable_vs_not_provided", "protocol_event", "protocol_risk", "symptom_event", "unknown_other_forbidden",
            ]).index(rule_id.split(".", 1)[1])
            path = f"/projection/domain_tracks/{ordinal % 8}/applicability_state"
        else:
            path = "/projection/risk_anchors/0/severity"
        return f"adapter.inherited.{rule_id}", {"op": "replace", "path": path, "value": invalid}
    if rule_id == "aemh_match_history.no_auto_close":
        return f"adapter.inherited.{rule_id}", {"op": "replace", "path": "/projection/threads/0/history_entries/2/event_kind", "value": "match_decided"}
    ordinal = sorted([
        "aemh_projection.ae_journey", "aemh_projection.ae_profile", "aemh_projection.ae_risk", "aemh_projection.ae_timeline",
        "aemh_projection.mh_journey", "aemh_projection.mh_profile", "aemh_projection.mh_risk", "aemh_projection.mh_timeline",
    ]).index(rule_id)
    return f"adapter.inherited.{rule_id}", {"op": "replace", "path": f"/projection/threads/{ordinal % 2}/domain", "value": invalid}


def pointer_after_mutation(document: dict[str, Any], path: str) -> Any:
    if path == "/": return digest(document)
    try: return copy.deepcopy(pointer_get(document, path))
    except (KeyError, IndexError, TypeError): return None


def verify_traces(registry: dict[str, Any], manifest: dict[str, Any], runtime: dict[str, Any]) -> None:
    if registry["registry_content_hash"] != digest({key: value for key, value in registry.items() if key != "registry_content_hash"}) or registry["registry_content_hash"] != manifest["trace_realization_registry_content_hash"]: fail("trace registry hash")
    if registry["counts"] != {SUBJECT: {"inherited": 48, "specific": 95}, AEMH: {"inherited": 16, "specific": 77}} or (registry["spec_count"], registry["unique_trace_count"], registry["alias_count"]) != (236, 236, 0): fail("trace counts")
    if registry["identity_excludes"] != ["source_case_ref", "source_rule_id", "source_single_mutation", "adapter_id", "exact_path", "instance_selector", "pre_value", "post_value", "operation_count", "label", "sentinel", "expected_disposition", "expected_code", "observed_disposition", "observed_ordered_issues", "post_authority_input_content_identity", "post_graph_content_hash"]: fail("trace identity exclusion")
    parent_registry = load(PARENT_CHALLENGES)
    source_rows = [*parent_registry["inherited_cases"], *parent_registry["public_authority_specific_cases"]]
    source_by_ref = {row["case_id"]: row for row in source_rows if row["contract"] in (SUBJECT, AEMH)}
    if {row["source_case_ref"] for row in registry["records"]} != set(source_by_ref): fail("trace case inventory")
    schema = load(SCHEMA); parent = parent_module(); subject_schema = load(SUBJECT_SCHEMA); aemh_schema = load(AEMH_SCHEMA)
    bases = registry["base_authority_inputs"]
    expected_base_refs = {"subject_temporal_valid_base", "subject_temporal_absent_cutoff_valid_base", "subject_temporal_conflicted_valid_base", "subject_temporal_no_study_day_valid_base", "aemh_match_history_valid_base", "positive.subject.axis.base", "positive.aemh.decision.seed"}
    if set(bases) != expected_base_refs: fail("trace authority base inventory")
    packet_cache = {}
    for base_ref, bundle in bases.items():
        issues = authority_issues(bundle, schema)
        if issues: fail(f"trace authority base {base_ref}: {issues}")
        if bundle["target_contract"] == SUBJECT:
            packet = IndependentExecutor(bundle).subject_packet(); errors = parent.validate_subject(packet, subject_schema); packet_cache[base_ref] = (None, packet)
        else:
            previous, packet = IndependentExecutor(bundle).aemh_packets(); errors = [*parent.validate_aemh(previous, aemh_schema, None), *parent.validate_aemh(packet, aemh_schema, previous)]; packet_cache[base_ref] = (previous, packet)
        if errors: fail(f"trace authority base parent validity {base_ref}: {errors}")
    identities = set(); positive_hashes = set()
    for row in registry["records"]:
        typed_issues = validate_typed(row, "TraceRealizationBindingV02", schema)
        if typed_issues: fail(f"trace typed {row.get('source_case_ref')}: {typed_issues}")
        source = source_by_ref[row["source_case_ref"]]; target = source["contract"]
        rule_id = source["stage_oracle_contract"]["rule_id"]
        if row["source_rule_id"] != rule_id or row["contract"] != target or row["source_single_mutation"] != source["single_mutation"]: fail(f"trace source drift {row['source_case_ref']}")
        expected_disposition, expected_code = source["expected_typed_outcome_or_error"].split(":", 1)
        if (row["expected_disposition"], row["expected_code"]) != (expected_disposition, expected_code): fail(f"trace expected freeze {row['source_case_ref']}")
        inherited = source["origin"] == "accepted_r5_v0_3_challenge_rule_projection"
        if inherited and expected_disposition == "accept":
            spec = runtime["positive_specs"].get(rule_id)
            expected_transformed = runtime["positive_bundles"].get(rule_id)
            if spec is None or expected_transformed is None: fail(f"trace accepted adapter missing {row['source_case_ref']}")
            base_ref = spec["base_ref"]; base = bases[base_ref]
            recorded_operations = sorted([row["realized_mutation"], *row["linked_operations"]], key=lambda item: item["sequence"])
            if recorded_operations != spec["operations"]: fail(f"trace/fixture operation bytes {row['source_case_ref']}")
            transformed, replay_issues = independent_replay_source_operations(base, recorded_operations, row["post_authority_input_content_identity"])
            if replay_issues: fail(f"trace accepted replay {row['source_case_ref']}:{replay_issues}")
            if transformed != expected_transformed: fail(f"trace accepted bundle byte equivalence {row['source_case_ref']}")
            completeness_issues = trace_operation_completeness_issues(base, expected_transformed, row["realized_mutation"], row["linked_operations"], row["operation_count"])
            if completeness_issues: fail(f"trace accepted operation completeness {row['source_case_ref']}:{completeness_issues}")
            if row["source_case_ref"] == "R5C-109" and (row["operation_count"] != 1 or row["linked_operations"]): fail("R5C-109 single-operation contract")
            if row["source_case_ref"] != "R5C-109" and row["operation_count"] <= 1: fail(f"positive multi-operation contract {row['source_case_ref']}")
            if rule_id == "axis_conversion.study_day_valid":
                def changed_study_day_paths(before: Any, after: Any, path: str = "") -> list[str]:
                    if isinstance(before, dict) and isinstance(after, dict):
                        return [leaf for key in sorted(before) if key in after for leaf in changed_study_day_paths(before[key], after[key], f"{path}/{key}")]
                    if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
                        return [leaf for index, (left, right) in enumerate(zip(before, after)) for leaf in changed_study_day_paths(left, right, f"{path}/{index}")]
                    return [path] if path.endswith("/study_day") and before != after else []
                expected_study_days = set(changed_study_day_paths(base, transformed))
                recorded_study_days = {operation["path"] for operation in row["linked_operations"] if operation["path"].endswith("/study_day")}
                if recorded_study_days != expected_study_days: fail(f"trace day-zero linked operations {row['source_case_ref']}")
            if target == AEMH:
                operation_paths = {operation["path"] for operation in recorded_operations}
                required_paths = {"/source/current_locator_specs", "/source/current_revision_specs", "/source/decision_records"}
                if not required_paths <= operation_paths or any(operation["op"] != "append" for operation in recorded_operations):
                    fail(f"trace AEMH append binding {row['source_case_ref']}:{sorted(operation_paths)}")
            if target == SUBJECT:
                previous = None; post_graph = IndependentExecutor(transformed).subject_packet(); issues = parent.validate_subject(post_graph, subject_schema)
            else:
                previous, post_graph = IndependentExecutor(transformed).aemh_packets(); issues = [*parent.validate_aemh(previous, aemh_schema, None), *parent.validate_aemh(post_graph, aemh_schema, previous)]
            realized = row["realized_mutation"]
            adapter_id = f"adapter.accepted.{rule_id}"
            pre = realized["pre_value"]; post = realized["post_value"]
            primary_path = {"axis_conversion.calendar_default": "/source/axis/mode", "axis_conversion.study_day_valid": "/source/axis/day_zero_convention", "axis_conversion.conversion_replay": "/source/events/0/end/exact_date"}.get(rule_id, "/source/decision_records")
            if realized["path"] != primary_path: fail(f"trace accepted primary path {row['source_case_ref']}:{realized['path']}")
            positive_hashes.add(post_graph["packet_content_hash"])
        else:
            base_ref = source.get("base_input_key", "subject_temporal_valid_base" if target == SUBJECT else "aemh_match_history_valid_base")
            base = bases[base_ref]; previous, base_packet = packet_cache[base_ref]; post_graph = copy.deepcopy(base_packet)
            if inherited:
                adapter_id, realized = independent_inherited_reject_adapter(rule_id, target); reseal = True
            else:
                adapter_id = f"adapter.parent-specific.{rule_id}"; realized = copy.deepcopy(source["single_mutation"]); reseal = source["fully_reseal_after_mutation"]
            pre = pointer_after_mutation(post_graph, realized["path"]); parent.apply_mutation(post_graph, realized); post = pointer_after_mutation(post_graph, realized["path"])
            if reseal:
                preserve = source["category"].startswith(("subject_evaluation_identity_", "aemh_evaluation_identity_"))
                if target == SUBJECT: parent.reseal_subject_packet(post_graph, subject_schema, preserve_evaluation=preserve)
                else: parent.reseal_aemh_packet(post_graph, aemh_schema, preserve_evaluation=preserve)
            issues = parent.validate_subject(post_graph, subject_schema) if target == SUBJECT else parent.validate_aemh(post_graph, aemh_schema, previous)
            expected_transformed = base
        observed_disposition = "accept" if not issues else "reject"
        if row["base_input_ref"] != base_ref or row["base_input_content_identity"] != base["bundle_content_identity"] or row["adapter_id"] != adapter_id or row["realized_mutation"] != realized or row["exact_path"] != realized["path"] or row["operation_count"] != 1 + len(row["linked_operations"]): fail(f"trace realization {row['source_case_ref']}")
        if row["pre_value"] != pre or row["post_value"] != post: fail(f"trace pre/post {row['source_case_ref']}")
        if row["observed_disposition"] != observed_disposition or row["observed_ordered_issues"] != issues or observed_disposition != expected_disposition: fail(f"trace observed {row['source_case_ref']}: {issues}")
        if not inherited and expected_code not in issues: fail(f"trace expected parent code {row['source_case_ref']}: {issues}")
        if row["post_authority_input_content_identity"] != expected_transformed["bundle_content_identity"] or row["post_graph_content_hash"] != post_graph["packet_content_hash"]: fail(f"trace post identities {row['source_case_ref']}")
        identity_payload = {"base_input_content_identity": base["bundle_content_identity"], "realized_mutation": realized, "linked_operations": row["linked_operations"], "lane": row["lane"]}
        if row["instance_selector"] != {"base_variant": base_ref, "semantic_rule_path": source["single_mutation"]["path"]} or digest(identity_payload) != row["trace_identity"] or row["trace_identity"] in identities: fail(f"trace identity/alias {row['source_case_ref']}")
        identities.add(row["trace_identity"])
    if len(identities) != 236 or len(positive_hashes) != 10: fail(f"trace execution closure {len(identities)}/236 positives={len(positive_hashes)}/10")
    attack = copy.deepcopy(registry["records"][0]); attack["realized_mutation"]["value"] = "fully-resealed-wrong-mutation"; attack["trace_identity"] = digest({"base_input_content_identity": attack["base_input_content_identity"], "realized_mutation": attack["realized_mutation"], "linked_operations": attack["linked_operations"], "lane": attack["lane"]})
    source = source_by_ref[attack["source_case_ref"]]
    if attack["realized_mutation"] == independent_inherited_reject_adapter(source["stage_oracle_contract"]["rule_id"], source["contract"])[1]: fail("fully resealed wrong trace mutation accepted")
    forced = copy.deepcopy(registry["records"]); forced[1]["trace_identity"] = forced[0]["trace_identity"]
    if len({row["trace_identity"] for row in forced}) == len(forced): fail("forced alias probe inactive")
    positive_records = {row["source_case_ref"]: row for row in registry["records"] if row["expected_disposition"] == "accept"}
    for label, case_id, mutate_record in (
        ("delete_required_linked", "R5C-110", lambda item: item["linked_operations"].pop()),
        ("add_false_linked", "R5C-109", lambda item: item["linked_operations"].append({**copy.deepcopy(item["realized_mutation"]), "sequence": 2, "pre_value": copy.deepcopy(item["realized_mutation"]["post_value"]), "post_value": copy.deepcopy(item["realized_mutation"]["post_value"])})),
        ("hide_second_diff", "R5C-116", lambda item: item["linked_operations"].clear()),
    ):
        attacked = copy.deepcopy(positive_records[case_id]); mutate_record(attacked); attacked["operation_count"] = 1 + len(attacked["linked_operations"])
        attacked_base = bases[attacked["base_input_ref"]]; attacked_expected = runtime["positive_bundles"][attacked["source_rule_id"]]
        attack_issues = trace_operation_completeness_issues(attacked_base, attacked_expected, attacked["realized_mutation"], attacked["linked_operations"], attacked["operation_count"])
        if not attack_issues: fail(f"trace operation completeness attack {label}")


def mutate(packet: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    changed = copy.deepcopy(packet); pointer_replace(changed, path, value); return changed


def fully_resealed_unused_locator_probe(subject: dict[str, Any]) -> dict[str, Any]:
    changed = copy.deepcopy(subject)
    projection = changed["projection"]
    receipt = changed["receipt"]
    template = projection["source_locators"][0]
    extra_ref = "locator::unused::fully-resealed-probe"
    extra = copy.deepcopy(template)
    extra["locator_ref"] = extra_ref
    extra["record_ref"] = "probe-row::unused"
    extra["column_or_anchor"] = "unused_probe"
    extra["raw_payload_hash"] = digest({"record": extra["record_ref"], "anchor": extra["column_or_anchor"]})
    extra["locator_content_hash"] = digest({key: value for key, value in extra.items() if key != "locator_content_hash"})
    projection["source_locators"] = sorted([*projection["source_locators"], extra], key=lambda row: row["locator_ref"])
    pair = next(row for row in receipt["source_revision_content_pairs"] if row["revision_id"] == extra["source_revision_ref"])
    pair["locator_refs"] = sorted([*pair["locator_refs"], extra_ref])
    pair["pair_content_hash"] = digest({key: value for key, value in pair.items() if key != "pair_content_hash"})
    membership = projection["membership_index"]
    membership["source_locator_refs"] = sorted([*membership["source_locator_refs"], extra_ref])
    membership["membership_content_hash"] = digest({key: value for key, value in membership.items() if key != "membership_content_hash"})
    projection["projection_id"] = digest({"contract_id": projection["contract_id"], "schema_version": projection["schema_version"], "scope_identity_hash": projection["scope_identity"]["identity_content_hash"], "membership_index_hash": membership["membership_content_hash"], "axis_basis_hash": projection["axis_basis"]["axis_content_hash"]})
    receipt["public_projection_id"] = projection["projection_id"]
    receipt["receipt_id"] = digest({"receipt_variant": receipt["receipt_variant"], "authority_contract_id": receipt["authority_contract_id"], "scope_identity_hash": receipt["scope_identity"]["identity_content_hash"], "public_projection_id": receipt["public_projection_id"]})
    projection["receipt_ref"] = receipt["receipt_id"]
    projection["projection_content_hash"] = digest({key: value for key, value in projection.items() if key != "projection_content_hash"})
    receipt["public_projection_content_hash"] = projection["projection_content_hash"]
    receipt["evaluation_content_identities"] = IndependentExecutor.subject_evaluation(projection, [row["accepted_content_hash"] for row in receipt["source_revision_content_pairs"]])
    receipt["receipt_content_hash"] = digest({key: value for key, value in receipt.items() if key != "receipt_content_hash"})
    changed["packet_content_hash"] = digest({"receipt_content_hash": receipt["receipt_content_hash"], "projection_content_hash": projection["projection_content_hash"]})
    return changed


def verify_parent_error_probes(runtime: dict[str, Any]) -> None:
    subject = runtime["subject"]
    subject_probes = [
        ("PUB_SCHEMA_EXACT_KEYS", "/projection/domain_tracks/0", {key: value for key, value in subject["projection"]["domain_tracks"][0].items() if key != "domain"}),
        ("PUB_DOMAIN_UNKNOWN", "/projection/domain_tracks/0/domain", "other"),
        ("PUB_DUPLICATE_REF", "/projection/events", [subject["projection"]["events"][0], subject["projection"]["events"][0]]),
        ("PUB_SOURCE_LOCATOR_UNRESOLVED", "/projection/events/0/source_locator_refs", ["locator::unknown"]),
        ("PUB_SOURCE_PARTITION_MISMATCH", "/receipt/source_revision_content_pairs/0/locator_refs", []),
        ("PUB_IDENTITY_CUTOFF_MISMATCH", "/projection/axis_basis/cutoff_endpoint/exact_date", "2026-08-18"),
        ("PUB_VISIBILITY_NOT_PROJECTABLE", "/receipt/visibility_closure/subject_visibility_state", "hidden"),
        ("PUB_MEMBERSHIP_MISMATCH", "/projection/membership_index/event_refs", []),
        ("PUB_PENDING_COVERAGE_MISMATCH", "/projection/pending_date_items", []),
        ("PUB_STUDY_DAY_VALUE_MISMATCH", "/projection/events/0/start_endpoint/study_day", 99),
        ("PUB_REFERENCE_DOMAIN_MISMATCH", "/projection/risk_anchors/0/domain", "mh"),
        ("PUB_AUDIENCE_CONTRACT_MISMATCH", "/receipt/audience_contract_id", "wrong"),
        ("PUB_CONTRACT_VERSION_MISMATCH", "/projection/schema_version", "wrong"),
        ("PUB_HASH_MISMATCH", "/packet_content_hash", "0" * 64),
    ]
    for code, path, value in subject_probes:
        errors = validate_parent(SUBJECT, mutate(subject, path, value))
        if code not in errors: fail(f"subject probe {code}: {errors}")
    unused_errors = validate_parent(SUBJECT, fully_resealed_unused_locator_probe(subject))
    if unused_errors != ["PUB_SOURCE_LOCATOR_UNUSED"]:
        fail(f"subject probe PUB_SOURCE_LOCATOR_UNUSED: {unused_errors}")
    previous, current = runtime["aemh_previous"], runtime["aemh_current"]
    aemh_probes = [
        ("AEMH_THREAD_REMINDER_MISSING", "/projection/threads/0/history_entries", current["projection"]["threads"][0]["history_entries"][1:]),
        ("AEMH_THREAD_REMINDER_REWRITTEN", "/projection/threads/0/history_entries/0/event_kind", "withdrawn"),
        ("AEMH_ORIGINAL_REMINDER_REF_MISMATCH", "/projection/threads/0/original_reminder_ref", "missing"),
        ("AEMH_HISTORY_SEQ_GAP", "/projection/threads/0/history_entries/1/seq", 9),
        ("AEMH_HISTORY_PRIOR_HASH_MISMATCH", "/projection/threads/0/history_entries/1/prior_entry_hash", "0" * 64),
        ("AEMH_MATCH_STATE_INVALID", "/projection/threads/0/history_entries/1/match_state", None),
        ("AEMH_MATCH_EVIDENCE_MISSING", "/projection/threads/0/history_entries/1/retained_evidence_locator_refs", []),
        ("AEMH_IDENTITY_EVIDENCE_MISMATCH", "/projection/threads/0/history_entries/1/identity_evidence/0/entity_ref", "wrong"),
        ("AEMH_EVIDENCE_RETENTION_VIOLATION", "/projection/threads/0/history_entries/2/retained_evidence_locator_refs", []),
        ("AEMH_PREFIX_CONTENT_MISMATCH", "/projection/threads/0/history_entries/0/reason_code", "rewritten"),
        ("AEMH_PREVIOUS_PROJECTION_MISMATCH", "/projection/previous_projection_ref", "wrong"),
        ("AEMH_THREAD_SET_MISMATCH", "/projection/threads", current["projection"]["threads"][:1]),
        ("AEMH_LIFECYCLE_TRANSITION_INVALID", "/projection/threads/0/history_entries/2/event_kind", "reappeared"),
    ]
    for code, path, value in aemh_probes:
        errors = validate_parent(AEMH, mutate(current, path, value), previous)
        if code not in errors: fail(f"aemh probe {code}: {errors}")


def medical_writing_inventory(contract: dict[str, Any]) -> tuple[int, str]:
    rows: list[tuple[str, str]] = []
    for root_name in contract["roots"]:
        base = ROOT / root_name
        if not base.exists(): continue
        for path in base.rglob("*"):
            if not path.is_file() or path.is_symlink(): continue
            relative = path.relative_to(ROOT).as_posix(); normalized = relative.lower().replace("-", "_")
            if "medical_writing" in normalized: rows.append((relative, raw_sha(path)))
    rows.sort(key=lambda row: row[0].encode())
    material = b"".join(path.encode() + b"\0" + sha.encode() + b"\n" for path, sha in rows)
    return len(rows), hashlib.sha256(material).hexdigest()


def verify_governance(manifest: dict[str, Any], schema: dict[str, Any], emitters: dict[str, Any], fixtures: dict[str, Any], traces: dict[str, Any], runtime: dict[str, Any]) -> None:
    subject = runtime["subject"]
    domain_mutations = [
        subject["projection"]["domain_tracks"][:-1],
        [*subject["projection"]["domain_tracks"], subject["projection"]["domain_tracks"][-1]],
        list(reversed(subject["projection"]["domain_tracks"])),
        [{**subject["projection"]["domain_tracks"][0], "domain": "unknown"}, *subject["projection"]["domain_tracks"][1:]],
    ]
    for index, tracks in enumerate(domain_mutations):
        if "PUB_DOMAIN_UNKNOWN" not in validate_parent(SUBJECT, mutate(subject, "/projection/domain_tracks", tracks)):
            fail(f"domain omit/dup/order/unknown probe {index}")
    root_constants = (subject["receipt"]["audience_contract_id"], subject["receipt"]["authority_contract_version"], subject["receipt"]["authority_contract_id"], subject["projection"]["contract_id"])
    if root_constants != (AUDIENCE, PARENT_VERSION, SUBJECT, SUBJECT): fail("root constants")
    for forbidden in schema["forbidden_candidate_keys"]:
        contaminated = copy.deepcopy(fixtures["baselines"][0]["authority_input"]); contaminated[forbidden] = "forbidden"
        if forbidden_candidate_key(contaminated) != forbidden: fail(f"candidate contamination {forbidden}")
    packet_contaminants = {
        "candidate_packet_payload": {"receipt": {}, "projection": {}},
        "parent_packet_hash": "0" * 64,
        "expected_packet_fixture_ref": "fixture.parent.packet",
        "packet_copy_source": "accepted-parent-fixture",
    }
    for key, value in packet_contaminants.items():
        contaminated = copy.deepcopy(fixtures["baselines"][0]["authority_input"])
        contaminated[key] = value
        contaminated["bundle_content_identity"] = digest({name: item for name, item in contaminated.items() if name != "bundle_content_identity"})
        if forbidden_candidate_key(contaminated) != key: fail(f"fully resealed packet contamination {key}")
    for row in fixtures["baselines"]:
        if forbidden_candidate_key(row["authority_input"]) is not None: fail("authority-only fixture contamination")
    extra_schema = copy.deepcopy(schema); extra_schema["objects"]["AuthorityBundleV02"]["fields"]["unexpected"] = "string"
    if digest({"objects": extra_schema["objects"], "enums": extra_schema["enums"]}) == schema["baseline_content_hash"]: fail("schema extra-key probe")
    overridden = copy.deepcopy(emitters); overridden["executable_v02_recipes"][0]["nodes"][0]["op"] = "read"
    if digest({key: value for key, value in overridden.items() if key != "registry_content_hash"}) == emitters["registry_content_hash"]: fail("emitter override probe")
    try: pointer_get(runtime["subject_bundle"], "/source/path/does/not/exist")
    except (KeyError, IndexError, TypeError): pass
    else: fail("missing trace path probe")
    wrong = copy.deepcopy(traces["records"][0]); wrong["instance_selector"] = {"source_contract": "wrong"}
    if wrong["instance_selector"] == traces["records"][0]["instance_selector"]: fail("wrong instance probe")
    any_pin = next(iter(manifest["external_pins"])); drifted_pin = "0" * 64
    if raw_sha(ROOT / any_pin) == drifted_pin: fail("pin drift probe")
    typed_pin_attack = copy.deepcopy(manifest)
    typed_pin_attack["typed_source_pins"][next(iter(TYPED_SOURCE_PINS))] = drifted_pin
    typed_pin_attack["manifest_content_hash"] = digest({key: value for key, value in typed_pin_attack.items() if key != "manifest_content_hash"})
    if not pin_surface_issues(typed_pin_attack): fail("fully resealed typed source pin drift")
    duplicate_pin_attack = copy.deepcopy(manifest)
    duplicate_pin_attack["accepted_parent_pins"]["source_file_sha256"] = copy.deepcopy(duplicate_pin_attack["typed_source_pins"])
    duplicate_pin_attack["manifest_content_hash"] = digest({key: value for key, value in duplicate_pin_attack.items() if key != "manifest_content_hash"})
    if pin_surface_issues(duplicate_pin_attack) != ["TPA_V02_DUPLICATE_TYPED_SOURCE_PIN_SURFACE"]: fail("duplicate typed source pin surface attack")
    protected = manifest["protected_accepted_pins"]
    for rel, expected in protected["protected_path_sha256"].items():
        if raw_sha(ROOT / rel) != expected: fail(f"protected path {rel}")
    count, aggregate = medical_writing_inventory(protected["medical_writing_inventory_contract"])
    if (count, aggregate) != (protected["medical_writing_protected_file_count"], protected["medical_writing_protected_inventory_sha256"]): fail(f"medical writing aggregate {count} {aggregate}")
    if {path.name for path in OUT.iterdir() if path.is_file()} != {"manifest.json", "schema.json", "emitter_recipe_registry.json", "full_graph_fixture_registry.json", "trace_realization_registry.json"}: fail("artifact directory exact files")
    if has_parent_packet_copy_entry(GENERATOR) or has_parent_packet_copy_entry(VERIFIER): fail("parent base packet copy entry")
    forbidden_parent_artifact = "base_" + "inputs.json"
    if any(path.endswith("/" + forbidden_parent_artifact) for path in manifest["accepted_parent_pins"]["artifact_raw_sha256"]): fail("parent base packet artifact pin")
    r5_root = ROOT / "poc/medical_monitoring_ai_native_r5"; forbidden_paths = []
    for path in r5_root.rglob("*"):
        if not (path.is_file() or path.is_symlink()): continue
        name = path.name.lower(); rel = path.relative_to(ROOT).as_posix().lower()
        producer = any(token in name for token in ("subject_temporal_public", "aemh_match_history_public", "public_authority_common"))
        s5 = "/src/mm_r5/s5_" in rel or "/tests/test_s5_" in rel or "/tests/s5_" in rel or "/evidence/r4_r5_s5" in rel
        bytecode = name.endswith((".pyc", ".pyo")) and (producer or "s5" in name)
        if producer or s5 or bytecode: forbidden_paths.append(rel)
    if forbidden_paths: fail("S5/producer/bytecode surface: " + ",".join(sorted(forbidden_paths)))
    caches = list((ROOT / "tools").glob("__pycache__/*temporal_projection_authority_delta_v0_2*.pyc"))
    if caches: fail("v0.2 bytecode cache")
    with socket.socket() as sock:
        sock.settimeout(0.15)
        if sock.connect_ex(("127.0.0.1", 8911)) == 0: fail("port 8911 listening")


def verify_determinism_and_ruff() -> None:
    env = dict(os.environ); env["PYTHONDONTWRITEBYTECODE"] = "1"
    bundle_shas = []
    for _ in range(2):
        result = subprocess.run([sys.executable, "-B", str(GENERATOR), "--print-bundle-sha"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120, check=False)
        if result.returncode != 0: fail(f"determinism generation: {result.stderr.strip()}")
        bundle_shas.append(result.stdout.strip())
    if len(set(bundle_shas)) != 1: fail("byte-identical generation")
    check = subprocess.run([sys.executable, "-B", str(GENERATOR), "--check"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120, check=False)
    if check.returncode != 0: fail(f"generator --check: {check.stderr.strip()} {check.stdout.strip()}")
    ruff = subprocess.run(["/Users/smkzw/.local/bin/uvx", "--offline", "ruff", "check", "--no-cache", str(GENERATOR), str(VERIFIER)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120, check=False)
    if ruff.returncode != 0: fail("offline Ruff: " + ruff.stdout.strip() + ruff.stderr.strip())


def main() -> int:
    sys.dont_write_bytecode = True
    verify_no_asserts()
    manifest, schema, emitters, fixtures, traces = load(MANIFEST), load(SCHEMA), load(EMITTERS), load(FIXTURES), load(TRACES)
    verify_manifest(manifest); verify_schema(schema, manifest); verify_emitters(emitters, manifest, schema, fixtures)
    runtime = verify_fixtures(fixtures, manifest, emitters); verify_traces(traces, manifest, runtime)
    verify_parent_error_probes(runtime); verify_governance(manifest, schema, emitters, fixtures, traces, runtime)
    verify_determinism_and_ruff()
    print(json.dumps({"status": "PASS", "optimize": sys.flags.optimize, "baselines": "2/2", "baseline_errors": "0/0", "positives": "10/10", "positive_errors": 0, "traces": "236/236/0", "subject_parent_probes": "15/15", "aemh_parent_probes": "13/13", "port_8911": "stopped", "self_acceptance": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
