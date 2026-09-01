"""Generate the contract-spec-only R5-S5 public authority contract v0.4.1."""

from __future__ import annotations

import argparse
import ast
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
CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-implementation-contract-v0.4.1"
SCHEMA_VERSION = "2026-08-21.4.1"
SUBJECT = "subject-temporal-public-v1"
AEMH = "aemh-match-history-public-v1"
PARENT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
SEMANTIC_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1"
TEMPORAL_V01_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1"
TEMPORAL_V02_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2"
ERROR_DELTA_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1"
OUT_REL = pathlib.Path("artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1")
GENERATOR_REL = "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1.py"
VERIFIER_REL = "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1.py"

EXACT_PATHS = (
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1_20260821_context.md",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1_20260821.md",
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

ERROR_DELTA_PINS = {
    "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/base_input_registry.json": "68998bc935680db3c72be5dfb5f47b7695c0a02be929cc2eb8822a12064d071e",
    "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/challenge_registry.json": "e3f76a41618ff1aa1ecaf09c97ed2cf79e7227e517e6b19e5af9721b31990fe2",
    "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/gate_registry.json": "d8d73fdee73c13bcbf044c34831e8eb8bbc452f658529a9e07e7c3dfb39fd44c",
    "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/manifest.json": "0dbc0763b9c282c5e2363707a1f6ea99ae8e730e00acb716dcfc61bf9cd3186b",
    "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/schema.json": "2d7edec89b1b17dc4cadcb5e9e7c73d9d0647f7cde8fa5ff9cdbb91d26413733",
    "context/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1_20260821_context.md": "0fc4089e1b91778d1969301c824781e9bc1173b99d5379b52bac596321d6db86",
    "reviews/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1_20260821.md": "14a64edd3a3ee58e6b274e1ba8a38c5660417b1b9c1f0492d77c0ef6bfb406fe",
    "tools/generate_medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1.py": "9bf1e2bf674d743e381e0d732ec91a12a9fef6c0414ca6dcebc5559e6f082d46",
    "tools/verify_medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1.py": "9b30c56fd7b8f189f7b4e750a9d71923b0d1772ea544e1ca15010244419b5bf9",
}

ERROR_DELTA_ACCEPTANCE = {
    "context/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1_acceptance_record_20260821.md": "814f3e7b36aade049e9a5267a3b247ec23089a0ec0696f9d07b82133ca6b42e9",
}

BLOCKED_V04_PINS = {
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/invariant_error_matrix.json": "83064fbc0935b59510cc2fd463b7946165d86bec315b67ca3eda624efe1ed0d9",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/manifest.json": "c363811be037a107a369523c47f43a7e589ddc9f8e608ca87309e1f15b6f7a94",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/public_api.json": "d27523ec4a85218136f2640160a99ef85b9418a9224fdf24f290fac2fecc7d18",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/source_join_matrix.json": "ea825e18733611a69c354a93d555a555a76fa0b35df914bb1915c526cab0de59",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/test_matrix.json": "86061b6609a75d2b576d76c6b8b8bf13324322d396e79facb66dd09c22b63e46",
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_20260821_context.md": "dd6c803175a37bb8ee573c7d13f5b213b51734fd0470bd7deb988050b756bf65",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_20260821.md": "3928e8069ef68e0dc19f2ada18b5fa24943e795c170362a095975cfe67fc384e",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4.py": "be0fa7f6aa8c91767c35d2842116bd7c36cca1f19eb58ef01ae592f339129a6b",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4.py": "a4df9626112e3fa5ee45d0ad538a298b29dab98cf122e912211cbe21d307a2fe",
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
    for relative, expected in {**AUTHORITY_PINS, **ERROR_DELTA_PINS, **ERROR_DELTA_ACCEPTANCE, **BLOCKED_V04_PINS}.items():
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
    delta = read_json(ERROR_DELTA_DIR / "manifest.json")
    if delta["typed_source_pins"] != typed or delta["temporal_v02_nine_file_pins"] != {
        **temporal["file_raw_sha256"],
        str(TEMPORAL_V02_DIR.relative_to(ROOT) / "manifest.json"): AUTHORITY_PINS[str(TEMPORAL_V02_DIR.relative_to(ROOT) / "manifest.json")],
    }:
        raise SystemExit("STOP accepted delta duplicate pin disagreement")
    if delta["blocked_v04_nine_file_pins"] != BLOCKED_V04_PINS:
        raise SystemExit("STOP blocked v0.4 pin disagreement")
    if delta["authority_chain_pins"] != AUTHORITY_PINS:
        raise SystemExit("STOP accepted authority root pin disagreement")
    return typed, temporal


def v02_generator() -> Any:
    return load_module(
        ROOT / "tools/generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
        "accepted_temporal_v02_generator_for_implementation_v041",
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
            raise SystemExit(f"STOP v0.4.1 baseline closure: {target}:{issues}")
        baseline_results[target] = {"bundle": bundle, "result": result, "outputs": outputs}
    executed = []
    identities = set()
    positive_count = 0
    reject_count = 0
    for record in traces["records"]:
        base = copy.deepcopy(bases[record["base_input_ref"]])
        target = record["contract"]
        previous = None
        primary = copy.deepcopy(record["realized_mutation"])
        linked = copy.deepcopy(record["linked_operations"])
        source_transform = isinstance(primary.get("sequence"), int) and all(
            isinstance(item.get("sequence"), int) for item in linked
        )
        if source_transform:
            operations = [primary, *linked]
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
            positive_count += int(not issues)
        else:
            built = engine.execute_recipe_dag(base, recipes)
            if target == SUBJECT:
                graph = copy.deepcopy(built)
            else:
                previous, current = built
                graph = copy.deepcopy(current)
            parent.apply_mutation(graph, primary)
            if record["reseal_mode"] != "none":
                preserve = any("EVALUATION_IDENTITY" in code for code in record["observed_ordered_issues"])
                if target == SUBJECT:
                    parent.reseal_subject_packet(graph, subject_schema, preserve_evaluation=preserve)
                else:
                    parent.reseal_aemh_packet(graph, aemh_schema, preserve_evaluation=preserve)
            issues = parent.validate_subject(graph, subject_schema) if target == SUBJECT else parent.validate_aemh(graph, aemh_schema, previous)
            outputs = {}
            reject_count += int(bool(issues))
        pre_identities = {
            "authority_bundle": record["base_input_content_identity"],
            "previous_packet": previous["packet_content_hash"] if previous is not None else None,
            "pre_packet": output_packet(target, engine.execute_recipe_dag(copy.deepcopy(bases[record["base_input_ref"]]), recipes))["packet_content_hash"],
        }
        preserve_fields = ["/receipt/evaluation_content_identities"] if any("EVALUATION_IDENTITY" in code for code in record["observed_ordered_issues"]) and record["reseal_mode"] != "none" else []
        if source_transform:
            ordered_targets = ["authority_bundle", "accepted_v02_recipe_dag", "parent_validator"]
        elif record["reseal_mode"] == "none":
            ordered_targets = ["candidate_packet", "parent_validator"]
        else:
            ordered_targets = ["candidate_packet", "parent_hash_dag", "parent_validator"]
        reseal_plan = {"mode": record["reseal_mode"], "ordered_targets": ordered_targets, "preserve_fields": preserve_fields}
        identity = digest({
            "pre_authority_identities": pre_identities,
            "instance_selector": record["instance_selector"],
            "primary_operation": primary,
            "linked_operations": linked,
            "lane": record["lane"],
            "reseal_mode": record["reseal_mode"],
            "reseal_order": record["reseal_order"],
            "reseal_plan": reseal_plan,
        })
        disposition = "accept" if not issues else "reject"
        if identity in identities:
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
            "pre_authority_identities": pre_identities,
            "instance_selector": record["instance_selector"],
            "primary_operation": primary,
            "linked_operations": linked,
            "reseal_mode": record["reseal_mode"],
            "reseal_order": record["reseal_order"],
            "reseal_plan": reseal_plan,
            "actual_ordered_issues": issues,
            "future_validator_expected": {
                "ok": not issues,
                "primary_code": issues[0] if issues else None,
                "ordered_issue_codes": issues,
                "packet_emitted": not issues,
            },
            "post_packet_content_hash": graph["packet_content_hash"],
            "post_projection_content_hash": graph["projection"]["projection_content_hash"],
            "identity_contract": {
                "includes": ["pre_authority_identities", "instance_selector", "primary_operation", "linked_operations", "lane", "reseal_mode", "reseal_order", "reseal_plan"],
                "excludes": ["source_case_ref", "label", "sentinel", "expected_code", "expected_output", "observed_result", "observed_hash"],
            },
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
        "schema": "medical-monitoring-r5-s5-public-authority-api-v0.4.1", "schema_version": SCHEMA_VERSION, "contract_id": CONTRACT_ID,
        "python": {"minimum": "3.9", "frozen_dataclasses": True, "dynamic_attributes": False, "reflection": False, "mutable_fields": False, "free_mapping_fields": False, "untyped_fields": False},
        "internal_authority_pins": {"caller_may_supply": False, "manifest_refs_are_module_internal": True},
        "authority_bundle_contract": {"authority_scope": "synthetic_test_only", "execution_profile": "full_parent_graph", "temporal_v01_manifest_sha256": AUTHORITY_PINS[str(TEMPORAL_V01_DIR.relative_to(ROOT) / "manifest.json")], "temporal_v02_manifest_sha256": AUTHORITY_PINS[str(TEMPORAL_V02_DIR.relative_to(ROOT) / "manifest.json")], "exact_target_contracts": [SUBJECT, AEMH], "candidate_backfill_forbidden": True, "dual_plane_exact_cross_check": True},
        "internal_construction_graph_contract": {
            "type_name": "ConstructionGraph",
            "public": False,
            "fields": ["authority_bundle", "typed_source_instances", "recipe_outputs", "common_objects", "final_packet", "construction_graph_content_hash"],
            "subject_common_object_key": "PublicCutoffEndpoint::subject-cutoff-binding",
            "generator_and_validator_build_independently": True,
            "public_build_return": "packet_only",
            "trace_access": "module_internal_validation_only",
        },
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


TYPED_RECIPE_BINDINGS: dict[str, dict[str, str]] = {
    "recipe.v02.subject_identity_cutoff": {"path": "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "class": "MonitoringRun", "field": "project_id", "v02_pointer": "/source/scope/project_ref"},
    "recipe.v02.subject_locators_revisions": {"path": "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "class": "SourceRevision", "field": "revision_id", "v02_pointer": "/source/revision_specs/0/revision_ref"},
    "recipe.v02.subject_temporal_members": {"path": "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "class": "TemporalEvent", "field": "event_id", "v02_pointer": "/source/events/0/event_ref"},
    "recipe.v02.subject_domains_pending_membership": {"path": "poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py", "class": "SemanticRecord", "field": "role", "v02_pointer": "/source/domain_applicability/0/domain"},
    "recipe.v02.subject_axis": {"path": "poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule.py", "class": "VisitJourneyProjection", "field": "subject_ref", "v02_pointer": "/source/scope/subject_ref"},
    "recipe.v02.subject_projection": {"path": "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py", "class": "S4AcceptedAuthorityAnchor", "field": "spine_ref", "v02_pointer": "/source/scope/spine_ref"},
    "recipe.v02.subject_receipt": {"path": "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "class": "MonitoringRun", "field": "run_id", "v02_pointer": "/source/scope/run_ref"},
    "recipe.v02.subject_packet": {"path": "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "class": "ListingSnapshot", "field": "snapshot_version", "v02_pointer": "/source/scope/snapshot_ref"},
    "recipe.v02.aemh_identity_locators_revisions": {"path": "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "class": "MonitoringRun", "field": "project_id", "v02_pointer": "/source/current_scope/project_ref"},
    "recipe.v02.aemh_previous_threads": {"path": "poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py", "class": "AEMHResult", "field": "project_id", "v02_pointer": "/source/previous_scope/project_ref"},
    "recipe.v02.aemh_previous_packet": {"path": "poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py", "class": "AEMHResult", "field": "snapshot_version", "v02_pointer": "/source/previous_scope/snapshot_ref"},
    "recipe.v02.aemh_current_threads": {"path": "poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py", "class": "AEMHSliceResult", "field": "subject_ref", "v02_pointer": "/source/current_scope/subject_ref"},
    "recipe.v02.aemh_current_membership_prefix_cutoff": {"path": "poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py", "class": "RiskCandidate", "field": "domain", "v02_pointer": "/source/thread_specs/0/domain"},
    "recipe.v02.aemh_projection": {"path": "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py", "class": "S4AcceptedAuthorityAnchor", "field": "spine_ref", "v02_pointer": "/source/current_scope/spine_ref"},
    "recipe.v02.aemh_receipt": {"path": "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "class": "MonitoringRun", "field": "run_id", "v02_pointer": "/source/current_scope/run_ref"},
    "recipe.v02.aemh_packet": {"path": "poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py", "class": "AEMHResult", "field": "snapshot_version", "v02_pointer": "/source/current_scope/snapshot_ref"},
}

ROOT_PACKET_OBJECTS = {
    (SUBJECT, "SubjectTemporalAuthorityPacket"),
    (AEMH, "AEMHMatchHistoryAuthorityPacket"),
}
CONTRACT_SHARED_INTERMEDIATE_OBJECTS = {
    (SUBJECT, "PublicCutoffEndpoint"),
}
PACKET_REACHABLE_OBJECTS = {
    (SUBJECT, "PublicAuthorityReceipt"),
    (SUBJECT, "PublicScopeIdentity"),
    (SUBJECT, "PublicSourceLocator"),
    (SUBJECT, "SourceRevisionContentPair"),
    (SUBJECT, "SubjectTemporalPublicProjection"),
    (SUBJECT, "TemporalAxisBasis"),
    (SUBJECT, "TemporalDateEndpoint"),
    (SUBJECT, "TemporalDomainTrack"),
    (SUBJECT, "TemporalEvent"),
    (SUBJECT, "TemporalMembershipIndex"),
    (SUBJECT, "TemporalPendingDateItem"),
    (SUBJECT, "TemporalPhaseBand"),
    (SUBJECT, "TemporalRiskAnchor"),
    (SUBJECT, "TemporalVisit"),
    (SUBJECT, "VisibilityClosure"),
    (AEMH, "AEMHHistoryMembershipIndex"),
    (AEMH, "AEMHIdentityEvidence"),
    (AEMH, "AEMHMatchHistoryEntry"),
    (AEMH, "AEMHMatchHistoryPublicProjection"),
    (AEMH, "AEMHMatchThread"),
    (AEMH, "AEMHThreadPrefixAnchor"),
    (AEMH, "PublicAuthorityReceipt"),
    (AEMH, "PublicCutoffEndpoint"),
    (AEMH, "PublicScopeIdentity"),
    (AEMH, "PublicSourceLocator"),
    (AEMH, "SourceRevisionContentPair"),
    (AEMH, "VisibilityClosure"),
}

# Frozen from the parent dataclass containment graph and the accepted v0.2 node
# output contracts.  These are selectors, never equality-search results.
EXACT_PACKET_STAGE_SELECTORS = {
    (SUBJECT, "PublicAuthorityReceipt"): ("/receipt", "/"),
    (SUBJECT, "PublicScopeIdentity"): ("/projection/scope_identity", "/identity"),
    (SUBJECT, "PublicSourceLocator"): ("/projection/source_locators/0", "/locators/0"),
    (SUBJECT, "SourceRevisionContentPair"): ("/receipt/source_revision_content_pairs/0", "/pairs/0"),
    (SUBJECT, "SubjectTemporalPublicProjection"): ("/projection", "/"),
    (SUBJECT, "TemporalAxisBasis"): ("/projection/axis_basis", "/"),
    (SUBJECT, "TemporalDateEndpoint"): ("/projection/events/0/start_endpoint", "/events/0/start_endpoint"),
    (SUBJECT, "TemporalDomainTrack"): ("/projection/domain_tracks/0", "/tracks/0"),
    (SUBJECT, "TemporalEvent"): ("/projection/events/0", "/events/0"),
    (SUBJECT, "TemporalMembershipIndex"): ("/projection/membership_index", "/membership"),
    (SUBJECT, "TemporalPendingDateItem"): ("/projection/pending_date_items/0", "/pending/0"),
    (SUBJECT, "TemporalPhaseBand"): ("/projection/phase_bands/0", "/phase"),
    (SUBJECT, "TemporalRiskAnchor"): ("/projection/risk_anchors/0", "/risk"),
    (SUBJECT, "TemporalVisit"): ("/projection/visits/0", "/visit"),
    (SUBJECT, "VisibilityClosure"): ("/receipt/visibility_closure", "/visibility"),
    (AEMH, "AEMHHistoryMembershipIndex"): ("/projection/membership_index", "/membership"),
    (AEMH, "AEMHIdentityEvidence"): ("/projection/threads/0/history_entries/0/identity_evidence/0", "/0/history_entries/0/identity_evidence/0"),
    (AEMH, "AEMHMatchHistoryEntry"): ("/projection/threads/0/history_entries/0", "/0/history_entries/0"),
    (AEMH, "AEMHMatchHistoryPublicProjection"): ("/projection", "/"),
    (AEMH, "AEMHMatchThread"): ("/projection/threads/0", "/0"),
    (AEMH, "AEMHThreadPrefixAnchor"): ("/projection/accepted_thread_prefixes/0", "/prefixes/0"),
    (AEMH, "PublicAuthorityReceipt"): ("/receipt", "/"),
    (AEMH, "PublicCutoffEndpoint"): ("/projection/cutoff_endpoint", "/cutoff"),
    (AEMH, "PublicScopeIdentity"): ("/projection/scope_identity", "/current_identity"),
    (AEMH, "PublicSourceLocator"): ("/projection/source_locators/0", "/current_locators/0"),
    (AEMH, "SourceRevisionContentPair"): ("/receipt/source_revision_content_pairs/1", "/current_pairs/1"),
    (AEMH, "VisibilityClosure"): ("/receipt/visibility_closure", "/visibility_closure"),
}

STABLE_IDENTITY_FIELDS = {
    "PublicAuthorityReceipt": "receipt_id",
    "PublicScopeIdentity": "identity_content_hash",
    "PublicSourceLocator": "locator_ref",
    "SourceRevisionContentPair": "revision_id",
    "SubjectTemporalPublicProjection": "projection_id",
    "TemporalAxisBasis": "axis_ref",
    "TemporalDateEndpoint": "endpoint_content_hash",
    "TemporalDomainTrack": "domain",
    "TemporalEvent": "event_ref",
    "TemporalMembershipIndex": "membership_content_hash",
    "TemporalPendingDateItem": "pending_ref",
    "TemporalPhaseBand": "phase_ref",
    "TemporalRiskAnchor": "risk_anchor_ref",
    "TemporalVisit": "visit_ref",
    "VisibilityClosure": "visibility_decision_id",
    "AEMHHistoryMembershipIndex": "membership_content_hash",
    "AEMHIdentityEvidence": "evidence_content_hash",
    "AEMHMatchHistoryEntry": "entry_id",
    "AEMHMatchHistoryPublicProjection": "projection_id",
    "AEMHMatchThread": "thread_ref",
    "AEMHThreadPrefixAnchor": "thread_ref",
    "PublicCutoffEndpoint": "cutoff_content_hash",
    "SubjectTemporalAuthorityPacket": "packet_content_hash",
    "AEMHMatchHistoryAuthorityPacket": "packet_content_hash",
}


def exact_target_kind(target: str, object_type: str) -> str:
    key = (target, object_type)
    memberships = [
        name
        for name, values in (
            ("root_packet", ROOT_PACKET_OBJECTS),
            ("packet_reachable", PACKET_REACHABLE_OBJECTS),
            ("contract_shared_intermediate", CONTRACT_SHARED_INTERMEDIATE_OBJECTS),
        )
        if key in values
    ]
    if len(memberships) != 1:
        raise SystemExit(f"STOP target-kind classification: {target}:{object_type}:{memberships}")
    return memberships[0]


def typed_field_exists(binding: dict[str, str]) -> bool:
    tree = ast.parse((ROOT / binding["path"]).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == binding["class"]:
            return any(
                isinstance(item, ast.AnnAssign)
                and isinstance(item.target, ast.Name)
                and item.target.id == binding["field"]
                for item in node.body
            )
    return False


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


def locate_all_exact_objects(value: Any, keys: set[str], pointer: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        if set(value) == keys:
            found.append(pointer or "/")
        for key, item in value.items():
            found.extend(locate_all_exact_objects(item, keys, f"{pointer}/{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(locate_all_exact_objects(item, keys, f"{pointer}/{index}"))
    return found


def construction_graph(target: str, baseline: dict[str, Any], recipes: dict[str, Any]) -> dict[str, Any]:
    packet = output_packet(target, baseline["result"])
    bundle = baseline["bundle"]
    outputs = baseline["outputs"]
    typed_instances: dict[str, Any] = {}
    for recipe in recipes["executable_v02_recipes"]:
        recipe_id = recipe["recipe_id"]
        if recipe["target_contract"] != target:
            continue
        binding = TYPED_RECIPE_BINDINGS[recipe_id]
        if not typed_field_exists(binding):
            raise SystemExit(f"STOP typed field missing: {recipe_id}")
        value = copy.deepcopy(json_get(bundle, binding["v02_pointer"]))
        typed_instances[recipe_id] = {
            "module_path": binding["path"],
            "class_name": binding["class"],
            "instance_key": recipe_id,
            "fields": {binding["field"]: value},
            "instance_content_hash": digest({
                "module_path": binding["path"],
                "class_name": binding["class"],
                "instance_key": recipe_id,
                "fields": {binding["field"]: value},
            }),
        }
    common_objects: dict[str, Any] = {}
    if target == SUBJECT:
        binding = copy.deepcopy(bundle["source"]["cutoff_binding"])
        required = {"state", "exact_date", "source_locator_refs"}
        if set(binding) != required:
            missing = sorted(required - set(binding))
            raise SystemExit(f"STOP subject PublicCutoffEndpoint source leaves: {missing}")
        if binding["state"] not in {"present", "absent"}:
            raise SystemExit("STOP subject PublicCutoffEndpoint state authority")
        cutoff_core = {
            "state": binding["state"],
            "exact_date": binding["exact_date"],
            "source_locator_refs": sorted(set(binding["source_locator_refs"])),
        }
        if (cutoff_core["state"] == "present") != (cutoff_core["exact_date"] is not None):
            raise SystemExit("STOP subject PublicCutoffEndpoint state/date closure")
        if cutoff_core["state"] == "absent" and cutoff_core["source_locator_refs"]:
            raise SystemExit("STOP subject PublicCutoffEndpoint absent locator closure")
        cutoff = {**cutoff_core, "cutoff_content_hash": digest(cutoff_core)}
        common_objects = {
            "PublicCutoffEndpoint": {
                "subject-cutoff-binding": cutoff,
            }
        }
    graph = {
        "target_contract": target,
        "authority_bundle": bundle,
        "typed_source_instances": typed_instances,
        "recipe_outputs": outputs,
        "common_objects": common_objects,
        "final_packet": packet,
    }
    graph["construction_graph_content_hash"] = digest(graph)
    return graph


def source_join_matrix(runtime: dict[str, Any], accepted: dict[str, Any]) -> dict[str, Any]:
    recipes = accepted["recipes"]
    by_id = {row["recipe_id"]: row for row in recipes["executable_v02_recipes"]}
    rows: list[dict[str, Any]] = []
    containment_rows: list[dict[str, Any]] = []
    ordinal = 0
    schema_memberships = {
        (target, object_type)
        for target, schema_name in ((SUBJECT, "subject_temporal_schema.json"), (AEMH, "aemh_match_history_schema.json"))
        for object_type in read_json(PARENT_DIR / schema_name)["objects"]
    }
    classified = ROOT_PACKET_OBJECTS | PACKET_REACHABLE_OBJECTS | CONTRACT_SHARED_INTERMEDIATE_OBJECTS
    if len(schema_memberships) != 30 or classified != schema_memberships:
        raise SystemExit(f"STOP target-kind 30-object coverage: missing={sorted(schema_memberships - classified)} extra={sorted(classified - schema_memberships)}")
    if (ROOT_PACKET_OBJECTS & PACKET_REACHABLE_OBJECTS) or (ROOT_PACKET_OBJECTS & CONTRACT_SHARED_INTERMEDIATE_OBJECTS) or (PACKET_REACHABLE_OBJECTS & CONTRACT_SHARED_INTERMEDIATE_OBJECTS):
        raise SystemExit("STOP target-kind overlap")
    for target, schema_name in ((SUBJECT, "subject_temporal_schema.json"), (AEMH, "aemh_match_history_schema.json")):
        schema = read_json(PARENT_DIR / schema_name)
        baseline = runtime["baselines"][target]
        graph = construction_graph(target, baseline, recipes)
        wrapped = {"contracts": {target: graph}}
        packet = graph["final_packet"]
        local_count = 0
        for object_type, fields in schema["objects"].items():
            frozen_target_kind = exact_target_kind(target, object_type)
            recipe_id = recipe_for_object(target, object_type)
            recipe = by_id[recipe_id]
            binding = TYPED_RECIPE_BINDINGS[recipe_id]
            output_ref = recipe["nodes"][1]["outputs"][0]
            stage_value = graph["recipe_outputs"][output_ref]["value"]
            stage_paths = locate_all_exact_objects(stage_value, set(fields))
            packet_paths = locate_all_exact_objects(packet, set(fields))
            if frozen_target_kind == "root_packet":
                if target == AEMH:
                    if set(stage_value) != {"previous", "current"}:
                        raise SystemExit(f"STOP AEMH packet wrapper exact keys: {sorted(stage_value)}")
                    selected_stage = "/current"
                    stage_paths = [selected_stage]
                    stage_object = json_get(stage_value, selected_stage)
                    construction_base = f"/contracts/{target}/recipe_outputs/{output_ref}/value/current"
                else:
                    stage_paths = ["/"]
                    selected_stage = "/"
                    stage_object = stage_value
                    construction_base = f"/contracts/{target}/recipe_outputs/{output_ref}/value"
                common_instance = False
                if stage_object != packet:
                    raise SystemExit(f"STOP root packet equality: {target}:{object_type}")
                packet_base = "/"
                target_kind = "root_packet"
            elif frozen_target_kind == "contract_shared_intermediate":
                stage_paths = ["/common_objects/PublicCutoffEndpoint/subject-cutoff-binding"]
                selected_stage = "/common_objects/PublicCutoffEndpoint/subject-cutoff-binding"
                construction_base = f"/contracts/{target}/common_objects/PublicCutoffEndpoint/subject-cutoff-binding"
                common_instance = True
                stage_object = json_get(wrapped, construction_base)
                packet_base = None
                target_kind = "contract_shared_intermediate"
            else:
                selector_key = (target, object_type)
                if selector_key not in EXACT_PACKET_STAGE_SELECTORS:
                    raise SystemExit(f"STOP exact containment selector missing: {target}:{object_type}")
                packet_base, selected_stage = EXACT_PACKET_STAGE_SELECTORS[selector_key]
                stage_paths = [selected_stage]
                construction_base = f"/contracts/{target}/recipe_outputs/{output_ref}/value{selected_stage if selected_stage != '/' else ''}"
                common_instance = False
                stage_object = json_get(stage_value, selected_stage)
                packet_object = json_get(packet, packet_base)
                if set(packet_object) != set(fields) or set(stage_object) != set(fields):
                    raise SystemExit(f"STOP exact containment type: {target}:{object_type}")
                if packet_object != stage_object:
                    raise SystemExit(f"STOP exact containment leaf equality: {target}:{object_type}")
                target_kind = "packet_reachable"
            if target_kind != frozen_target_kind:
                raise SystemExit(f"STOP target-kind dispatch drift: {target}:{object_type}")
            if frozen_target_kind == "root_packet":
                contained = [("/", packet)]
            elif frozen_target_kind == "contract_shared_intermediate":
                contained = [(construction_base, stage_object)]
            else:
                contained = [(pointer, json_get(packet, pointer)) for pointer in packet_paths]
            identity_field = STABLE_IDENTITY_FIELDS.get(object_type)
            if identity_field is None:
                raise SystemExit(f"STOP parent stable identity missing: {target}:{object_type}")
            for contained_pointer, contained_value in contained:
                if set(contained_value) != set(fields):
                    raise SystemExit(f"STOP containment target type: {target}:{object_type}:{contained_pointer}")
                identity_value = contained_value[identity_field]
                containment_rows.append({
                    "contract": target,
                    "object_type": object_type,
                    "instance_key": f"{identity_field}={identity_value}@{contained_pointer}",
                    "stable_identity_field": identity_field,
                    "stable_identity_value": identity_value,
                    "exact_json_pointer": contained_pointer if frozen_target_kind == "contract_shared_intermediate" else f"/contracts/{target}/final_packet{'' if contained_pointer == '/' else contained_pointer}",
                    "target_kind": frozen_target_kind,
                    "selected_for_schema_leaf_rows": contained_pointer == packet_base if frozen_target_kind != "contract_shared_intermediate" else True,
                })
            typed_pointer = f"/contracts/{target}/typed_source_instances/{recipe_id}/fields/{binding['field']}"
            v02_pointer = f"/contracts/{target}/authority_bundle{binding['v02_pointer']}"
            typed_value = json_get(wrapped, typed_pointer)
            authority_value = json_get(wrapped, v02_pointer)
            if typed_value != authority_value:
                raise SystemExit(f"STOP dual selector cross-check: {target}:{object_type}")
            prior_nodes = recipe["nodes"][0]["params"]["prior_recipe_output_refs"]
            for field, spec in fields.items():
                ordinal += 1
                local_count += 1
                qualified = f"{target}::{object_type}.{field}"
                construction_pointer = f"{construction_base}/{field}"
                packet_pointer = None if packet_base is None else f"/contracts/{target}/final_packet{packet_base if packet_base != '/' else ''}/{field}"
                recipe_pointer = f"{selected_stage if selected_stage != '/' else ''}/{field}"
                construction_value = json_get(wrapped, construction_pointer)
                if common_instance:
                    source_leaf = "state" if field == "state" else "exact_date" if field == "exact_date" else "source_locator_refs" if field == "source_locator_refs" else None
                    if source_leaf is not None:
                        source_value = copy.deepcopy(baseline["bundle"]["source"]["cutoff_binding"][source_leaf])
                        if source_leaf == "source_locator_refs":
                            source_value = sorted(set(source_value))
                        if construction_value != source_value:
                            raise SystemExit(f"STOP subject common source cross-check: {qualified}")
                    elif field == "cutoff_content_hash":
                        core = {key: stage_object[key] for key in ("state", "exact_date", "source_locator_refs")}
                        if construction_value != digest(core):
                            raise SystemExit(f"STOP subject common canonical hash: {qualified}")
                    else:
                        raise SystemExit(f"STOP subject PublicCutoffEndpoint unknown leaf: {field}")
                else:
                    packet_value = json_get(wrapped, packet_pointer)
                    recipe_value = json_get(stage_value, recipe_pointer)
                    if construction_value != recipe_value or packet_value != recipe_value:
                        raise SystemExit(f"STOP resolved join value drift: {qualified}")
                value_hash = digest(construction_value)
                row = {
                    "ordinal": ordinal,
                    "contract": target,
                    "object_type": object_type,
                    "leaf": field,
                    "qualified_leaf": qualified,
                    "output_json_pointer": construction_pointer if packet_pointer is None else packet_pointer,
                    "output_type": spec["type"],
                    "nullable": spec["nullable"],
                    "cardinality": spec["cardinality"],
                    "ordering_rule": "canonical sorted unique" if spec["cardinality"] == "many" else "scalar exact",
                    "key_selector": {
                        "strategy": "exact_construction_path",
                        "object_type": object_type,
                        "instance_key": "subject-cutoff-binding" if common_instance else f"{STABLE_IDENTITY_FIELDS[object_type]}={stage_object[STABLE_IDENTITY_FIELDS[object_type]]}@{packet_base}",
                        "selected_instance_count": 1,
                        "available_instance_count": len(stage_paths),
                    },
                    "instance_selector": {
                        "graph_root": f"/contracts/{target}",
                        "instance_key": "subject-cutoff-binding" if common_instance else f"{STABLE_IDENTITY_FIELDS[object_type]}={stage_object[STABLE_IDENTITY_FIELDS[object_type]]}@{packet_base}",
                        "cardinality": "exact-one",
                        "zero_policy": "fail_closed",
                        "many_policy": "fail_closed",
                    },
                    "authority_source_kind": "dual_typed_and_accepted_v02",
                    "typed_source_selector": {
                        "module_path": binding["path"],
                        "class_name": binding["class"],
                        "field_path": binding["field"],
                        "instance_key": recipe_id,
                        "json_pointer": typed_pointer,
                        "cardinality": "exact-one",
                    },
                    "v02_authority_selector": {
                        "root_type": "AuthorityBundleV02",
                        "source_variant": "SubjectFullGraphInputV02" if target == SUBJECT else "AEMHFullGraphInputV02",
                        "instance_key": baseline["bundle"]["bundle_content_identity"],
                        "json_pointer": v02_pointer,
                        "cardinality": "exact-one",
                    },
                    "selector_cardinality": "exact-one",
                    "selector_zero_policy": "fail_closed",
                    "selector_many_policy": "fail_closed",
                    "selector_cross_check_content_hash": digest({"typed": typed_value, "v02": authority_value}),
                    "reducer_id": recipe["nodes"][0]["op"],
                    "accepted_reducer_op": recipe["nodes"][0]["op"],
                    "recipe_id": recipe_id,
                    "recipe_content_hash": recipe["recipe_content_hash"],
                    "recipe_node_id": recipe["nodes"][1]["node_id"],
                    "recipe_node_output_ref": output_ref,
                    "recipe_output_json_pointer": recipe_pointer,
                    "recipe_registry_content_hash": recipes["registry_content_hash"],
                    "dependency_output_leaves": [],
                    "dependency_recipe_nodes": [ref.removesuffix(".sealed") + ".n02" for ref in prior_nodes],
                    "construction_phase": recipe["nodes"][0]["params"]["phase"],
                    "construction_target": {
                        "graph_type": "ConstructionGraph",
                        "json_pointer": construction_pointer,
                        "instance_key": "subject-cutoff-binding" if common_instance else selected_stage,
                        "common_object": common_instance,
                        "resolved_value_content_hash": value_hash,
                        "target_kind": target_kind,
                    },
                    "packet_target": None if packet_pointer is None else {"json_pointer": packet_pointer, "target_kind": target_kind},
                    "parent_schema_ref": f"artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/{schema_name}#/objects/{object_type}/{field}",
                    "semantic_ref": None,
                    "expected_plane_ref": f"artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json#/baselines/{0 if target == SUBJECT else 1}/authority_input",
                    "expected_plane_kind": "accepted_v02_source_authority_and_parent_constructor" if common_instance else "accepted_v02_full_parent_graph",
                    "fail_closed_codes": ["PUB_COMMON_TARGET_MISBOUND", "PUB_TYPE_MISMATCH", "PUB_HASH_MISMATCH"] if common_instance else ["PUB_TYPE_MISMATCH", "PUB_HASH_MISMATCH"],
                    "resolved_value_content_hash": value_hash,
                    "generator_join_executed": True,
                    "candidate_backfill_forbidden": True,
                    "mirror_forbidden": True,
                }
                rows.append(row)
        expected_local = 156 if target == SUBJECT else 116
        if local_count != expected_local:
            raise SystemExit(f"STOP join contract count: {target}:{local_count}")
    target_pointers = {row["construction_target"]["json_pointer"] for row in rows}
    if len(rows) != 272 or len({row["qualified_leaf"] for row in rows}) != 272 or len(target_pointers) != 272:
        raise SystemExit("STOP 272 join bijection")
    containment_keys = {(item["contract"], item["object_type"], item["instance_key"]) for item in containment_rows}
    if len(containment_keys) != len(containment_rows):
        raise SystemExit("STOP duplicate containment instance")
    for item in containment_rows:
        json_get({"contracts": {target: construction_graph(target, runtime["baselines"][target], recipes) for target in (SUBJECT, AEMH)}}, item["exact_json_pointer"])
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-source-join-matrix-v0.4.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "construction_graph_contract": {
            "type": "ConstructionGraph",
            "internal_only": True,
            "contains": ["authority_bundle", "typed_source_instances", "recipe_outputs", "common_objects", "final_packet"],
            "builder_public_return": "packet_only",
            "generator_and_verifier_construct_independently": True,
            "subject_common_cutoff_instance_pointer": f"/contracts/{SUBJECT}/common_objects/PublicCutoffEndpoint/subject-cutoff-binding",
            "cross_aemh_mirror_forbidden": True,
        },
        "target_kind_contract": {
            "membership_count": 30,
            "mutually_exclusive": True,
            "fully_covered": True,
            "root_packet": [f"{target}::{object_type}" for target, object_type in sorted(ROOT_PACKET_OBJECTS)],
            "packet_reachable": [f"{target}::{object_type}" for target, object_type in sorted(PACKET_REACHABLE_OBJECTS)],
            "contract_shared_intermediate": [f"{target}::{object_type}" for target, object_type in sorted(CONTRACT_SHARED_INTERMEDIATE_OBJECTS)],
            "positive_controls": [
                {"object": f"{SUBJECT}::SubjectTemporalAuthorityPacket", "comparison": "whole accepted packet root"},
                {"object": f"{AEMH}::AEMHMatchHistoryAuthorityPacket", "comparison": "whole accepted packet root"},
                {"object": f"{SUBJECT}::PublicCutoffEndpoint", "resolved_leaf_count": 4, "comparison": "subject source authority plus independent parent constructor"},
                {"object": f"{AEMH}::AEMHMatchHistoryAuthorityPacket", "exact_recipe_output_selector": "/current", "wrapper_exact_keys": ["current", "previous"], "selector_cardinality": "exact-one", "previous_role": "independent source dependency only"},
            ],
            "negative_controls": [
                {"object_kind": "root_packet", "forged_kind": "packet_reachable", "expected_issue": "JOIN_ROOT_PACKET_MISCLASSIFIED"},
                {"object_kind": "root_packet", "forged_kind": "contract_shared_intermediate", "expected_issue": "JOIN_ROOT_PACKET_MISCLASSIFIED"},
                {"object_kind": "contract_shared_intermediate", "forged_kind": "root_packet", "expected_issue": "JOIN_SHARED_INTERMEDIATE_MISCLASSIFIED"},
                {"control": "aemh_current_previous_swap", "mutation": {"op": "replace", "path": "/selector", "value": "/previous"}, "expected_issue": "JOIN_CURRENT_PACKET_SELECTOR_MISMATCH"},
                {"control": "aemh_current_deleted", "mutation": {"op": "remove", "path": "/current"}, "expected_issue": "JOIN_CURRENT_PACKET_SELECTOR_CARDINALITY"},
                {"control": "aemh_double_current", "mutation": {"op": "add", "path": "/current_duplicate", "value": "current"}, "expected_issue": "JOIN_CURRENT_PACKET_WRAPPER_KEYS"},
                {"control": "aemh_generic_search", "mutation": {"op": "replace", "path": "/selector", "value": "recursive-equality-search"}, "expected_issue": "JOIN_CURRENT_PACKET_SELECTOR_NOT_EXACT"},
            ],
        },
        "exact_containment_map": {
            "instance_count": len(containment_rows),
            "all_instances_mapped": True,
            "identity_policy": "parent frozen stable identity plus exact containment role; no first/nearest/equality search",
            "rows": containment_rows,
            "negative_controls": [
                {"mutation": "wrong exact pointer", "expected_issue": "JOIN_CONTAINMENT_POINTER"},
                {"mutation": "nearest or first selector", "expected_issue": "JOIN_SELECTOR_NOT_EXACT"},
                {"mutation": "duplicate stable instance", "expected_issue": "JOIN_INSTANCE_CARDINALITY"},
                {"mutation": "previous/current swap", "expected_issue": "JOIN_CURRENT_PACKET_SELECTOR_MISMATCH"},
                {"mutation": "missing stable instance", "expected_issue": "JOIN_INSTANCE_MISSING"},
            ],
        },
        "row_count": 272,
        "subject_count": 156,
        "aemh_count": 116,
        "alias_count": 0,
        "unexplained_count": 0,
        "resolved_pointer_count": 272,
        "rows": rows,
        "dag_contract": {"independent_per_contract": True, "acyclic": True, "self_or_future_edges": False, "recipe_count": 16, "recipe_node_count": 32},
        "forbidden": ["target_output_path", "candidate output mirror", "example output mirror", "fixture output mirror", "prose resolver", "class-wide closure", "nearest fallback", "temporal constant override", "D07 OTHER", "S4 value transfer", "broad D08TypedInput.scope_binding", "bare /source", "$common"],
    }

def parent_case_issues(row: dict[str, Any], parent: Any, parent_exact: dict[str, Any], subject_schema: dict[str, Any], aemh_schema: dict[str, Any], inputs: dict[str, Any]) -> list[str]:
    contract = row["contract"]
    if contract == SUBJECT:
        candidate = copy.deepcopy(inputs[row["base_input_key"]])
        parent.apply_mutation(candidate, row["single_mutation"])
        if row["fully_reseal_after_mutation"]:
            parent.reseal_subject_packet(candidate, subject_schema, preserve_evaluation=row["category"].startswith("subject_evaluation_identity_"))
        return parent.validate_subject(candidate, subject_schema)
    if contract == AEMH:
        candidate = copy.deepcopy(inputs[row["base_input_key"]])
        parent.apply_mutation(candidate, row["single_mutation"])
        if row["fully_reseal_after_mutation"]:
            parent.reseal_aemh_packet(candidate, aemh_schema, preserve_evaluation=row["category"].startswith("aemh_evaluation_identity_"))
        return parent.validate_aemh(candidate, aemh_schema, inputs["aemh_match_history_previous_base"])
    if contract == "exact-overlay-v0.1":
        candidate = read_json(PARENT_DIR / "exact_overlay.json")
        parent.apply_mutation(candidate, row["single_mutation"])
        return parent.overlay_validation_issues(candidate, parent_exact)
    if contract == "source-matrix-v0.1":
        candidate = read_json(PARENT_DIR / "source_matrix.json")
        parent.apply_mutation(candidate, row["single_mutation"])
        return parent.source_matrix_validation_issues(candidate)
    if contract == "manifest-v0.1":
        candidate = read_json(PARENT_DIR / "manifest.json")
        parent.apply_mutation(candidate, row["single_mutation"])
        if row["fully_reseal_after_mutation"]:
            candidate["manifest_content_hash"] = parent.canonical_hash({key: value for key, value in candidate.items() if key != "manifest_content_hash"})
        return parent.manifest_contract_validation_issues(candidate)
    raise SystemExit(f"STOP unknown accepted parent gate: {contract}")


def pre_delta_error_replays() -> tuple[dict[str, dict[str, Any]], dict[str, int], dict[str, str]]:
    subject = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    semantic_schema = read_json(SEMANTIC_DIR / "schema.json")
    temporal_registry = read_json(TEMPORAL_V01_DIR / "challenge_registry.json")
    parent_codes = list(dict.fromkeys(subject["error_codes"] + aemh["error_codes"]))
    semantic_codes = list(semantic_schema["typed_error_priority"])
    temporal_codes = sorted({row["expected_error"] for row in temporal_registry["cases"]})
    ordered = parent_codes + semantic_codes + temporal_codes
    priorities = {code: index for index, code in enumerate(ordered, 1)}
    origins = {code: "parent" for code in parent_codes}
    origins.update({code: "semantic_delta" for code in semantic_codes})
    origins.update({code: "temporal_delta" for code in temporal_codes})
    if len(ordered) != 192 or len(set(ordered)) != 192:
        raise SystemExit("STOP accepted error priority closure")

    carriers: dict[str, dict[str, Any]] = {}
    parent = load_module(ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py", "accepted_parent_error_replay_v041")
    parent_registry = read_json(PARENT_DIR / "challenge_registry.json")
    parent_exact = read_json(ROOT / "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json")
    parent_inputs = read_json(PARENT_DIR / "base_inputs.json")
    for index, row in enumerate(parent_registry["public_authority_specific_cases"]):
        issues = parent_case_issues(row, parent, parent_exact, subject, aemh, parent_inputs)
        for code in issues:
            carriers.setdefault(code, {
                "replay_plane": "accepted_pre_delta",
                "source_challenge_ref": f"artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/challenge_registry.json#/public_authority_specific_cases/{index}",
                "gate_entrypoint": {SUBJECT: "validate_subject", AEMH: "validate_aemh", "exact-overlay-v0.1": "overlay_validation_issues", "source-matrix-v0.1": "source_matrix_validation_issues", "manifest-v0.1": "manifest_contract_validation_issues"}[row["contract"]],
                "base_input_ref": row.get("base_input_key"),
                "mutation": copy.deepcopy(row["single_mutation"]),
                "reseal": {"enabled": row["fully_reseal_after_mutation"], "mode": "accepted_parent_full_reseal" if row["fully_reseal_after_mutation"] else "none"},
                "observed_ordered_issue_codes": list(issues),
                "contract": row["contract"],
                "invariant": row["stage_oracle_contract"]["rule_id"],
            })

    semantic = load_module(ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py", "accepted_semantic_error_replay_v041")
    semantic_registry = read_json(SEMANTIC_DIR / "challenge_registry.json")
    semantic_manifest = read_json(SEMANTIC_DIR / "manifest.json")
    source_registry = semantic_manifest["synthetic_typed_source_record_registry"]
    acceptance_registry = semantic_manifest["synthetic_policy_acceptance_registry"]
    source_records = semantic.validate_source_registry(source_registry)
    accepted_records = semantic.validate_acceptance_registry(acceptance_registry)
    semantic_result = semantic.run_challenges(semantic_registry, source_registry, source_records, acceptance_registry, accepted_records)
    actual_by_case = {row["case_id"]: row["outcome"] for row in semantic_result["outcomes"]}
    for index, row in enumerate(semantic_registry["cases"]):
        code = actual_by_case[row["case_id"]]
        if code == "success":
            continue
        carriers.setdefault(code, {
            "replay_plane": "accepted_pre_delta",
            "source_challenge_ref": f"artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/challenge_registry.json#/cases/{index}",
            "gate_entrypoint": {"event": "evaluate_event", "risk": "evaluate_risk", "risk_authority": "evaluate_risk+candidate_compare", "governance": "evaluate_governance"}[row["evaluation_kind"]],
            "base_input_ref": row["baseline_ref"],
            "mutation": copy.deepcopy(row["mutation"]),
            "reseal": {"enabled": bool(row["mutation"]["mechanical_reseal"]), "mode": list(row["mutation"]["mechanical_reseal"])},
            "observed_ordered_issue_codes": [code],
            "contract": [SUBJECT, AEMH],
            "invariant": row["non_llm_oracle"],
        })

    temporal = load_module(ROOT / "tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1.py", "accepted_temporal_error_replay_v041")
    temporal_manifest = read_json(TEMPORAL_V01_DIR / "manifest.json")
    temporal_schema = read_json(TEMPORAL_V01_DIR / "schema.json")
    temporal_matrix = read_json(TEMPORAL_V01_DIR / "source_matrix_delta.json")
    temporal_recipes = read_json(TEMPORAL_V01_DIR / "recipe_registry.json")
    temporal.verify_schema(temporal_schema, temporal_manifest)
    temporal.verify_source_matrix(temporal_matrix, temporal_manifest)
    temporal.verify_typed_source_paths(temporal_matrix, temporal_manifest)
    recipe_map = temporal.verify_recipes(temporal_recipes, temporal_schema, temporal_manifest)
    temporal.verify_challenges(temporal_registry, temporal_recipes, temporal_manifest, temporal_schema, recipe_map)
    for index, row in enumerate(temporal_registry["cases"]):
        code = row["expected_error"]
        carriers.setdefault(code, {
            "replay_plane": "accepted_pre_delta",
            "source_challenge_ref": f"artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/challenge_registry.json#/cases/{index}",
            "gate_entrypoint": f"verify_challenges::{row['probe_kind']}",
            "base_input_ref": row.get("fixture_id"),
            "mutation": copy.deepcopy(row["mutation"]),
            "reseal": {"enabled": False, "mode": "accepted_temporal_probe"},
            "observed_ordered_issue_codes": [code],
            "contract": [row["covered_leaf"].split("::", 1)[0]] if row.get("covered_leaf") else [SUBJECT, AEMH],
            "invariant": row["required_non_llm_anchor"],
        })
    missing_delta = set(read_json(ERROR_DELTA_DIR / "manifest.json")["missing_error_codes"])
    pre = {code: carrier for code, carrier in carriers.items() if code not in missing_delta}
    if len(pre) != 170 or set(pre) != set(ordered) - missing_delta:
        raise SystemExit(f"STOP pre-delta replay closure: {len(pre)}")
    return pre, priorities, origins


def invariant_error_matrix() -> dict[str, Any]:
    pre, priorities, origins = pre_delta_error_replays()
    delta_generator = load_module(ROOT / "tools/generate_medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1.py", "accepted_error_delta_generator_v041")
    rendered = delta_generator.render()
    delta_challenges_rel = "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/challenge_registry.json"
    if hashlib.sha256(rendered[delta_challenges_rel]).hexdigest() != ERROR_DELTA_PINS[delta_challenges_rel]:
        raise SystemExit("STOP accepted delta gate replay drift")
    delta_registry = read_json(ERROR_DELTA_DIR / "challenge_registry.json")
    delta = {row["error_code"]: row for row in delta_registry["rows"]}
    if len(delta) != 22 or set(pre) & set(delta) or len(set(pre) | set(delta)) != 192:
        raise SystemExit("STOP 170+22 error union closure")
    carrier_by_code: dict[str, dict[str, Any]] = dict(pre)
    for code, row in delta.items():
        carrier_by_code[code] = {
            "replay_plane": "accepted_error_replay_delta",
            "source_challenge_ref": f"artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/challenge_registry.json#/rows/{row['case_id']}",
            "gate_entrypoint": row["gate_id"],
            "base_input_ref": row["base_input_ref"],
            "mutation": copy.deepcopy(row["single_mutation"]),
            "reseal": {"enabled": bool(row["ordered_reseal"]), "mode": copy.deepcopy(row["ordered_reseal"])},
            "observed_ordered_issue_codes": [item["code"] for item in row["observed_ordered_issues"]],
            "observed_ordered_issues": copy.deepcopy(row["observed_ordered_issues"]),
            "contract": [SUBJECT, AEMH],
            "invariant": row["surface"],
            "accepted_delta_trace_identity": row["trace_identity"],
        }
    path_by_code: dict[str, str] = {}
    for code, carrier in carrier_by_code.items():
        if "observed_ordered_issues" in carrier:
            path_by_code[code] = carrier["observed_ordered_issues"][0]["path"]
        else:
            mutation = carrier["mutation"]
            path_by_code[code] = str(mutation.get("path", mutation.get("json_pointer", mutation.get("target", "/"))))
    records = []
    for code in sorted(carrier_by_code, key=lambda item: priorities[item]):
        carrier = carrier_by_code[code]
        issue_objects = carrier.get("observed_ordered_issues") or [
            {"code": item, "path": path_by_code[item], "message": f"{origins[item]}:{item}:fail_closed", "origin": origins[item], "priority": priorities[item]}
            for item in carrier["observed_ordered_issue_codes"]
        ]
        record = {
            "code": code,
            "priority": priorities[code],
            "origin": origins[code],
            "contract": carrier["contract"],
            "invariant": carrier["invariant"],
            "path": path_by_code[code],
            "message": f"{origins[code]}:{code}:fail_closed",
            "replay_plane": carrier["replay_plane"],
            "source_challenge_ref": carrier["source_challenge_ref"],
            "coverage_replay_ref": carrier["source_challenge_ref"],
            "gate_entrypoint": carrier["gate_entrypoint"],
            "base_input_ref": carrier["base_input_ref"],
            "mutation": carrier["mutation"],
            "reseal": carrier["reseal"],
            "observed_ordered_issues": issue_objects,
            "accepted_delta_trace_identity": carrier.get("accepted_delta_trace_identity"),
            "generator_replay_executed": True,
        }
        records.append(record)
    if sum(row["replay_plane"] == "accepted_pre_delta" for row in records) != 170 or sum(row["replay_plane"] == "accepted_error_replay_delta" for row in records) != 22:
        raise SystemExit("STOP error replay plane counts")
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-invariant-error-matrix-v0.4.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "counts": {
            "authority_inventory": {"parent": 81, "semantic_delta": 49, "temporal_delta": 62, "union": 192},
            "executable_coverage": {"pre_delta_unique": 170, "error_replay_delta": 22, "post_union_unique": 192},
            "executed_cases": {"parent": 194, "semantic": 66, "temporal_v01": 418, "temporal_v02": 236, "error_replay_delta": 22},
        },
        "dedup_key": ["code", "path", "origin", "message"],
        "total_order": ["priority", "path", "code", "origin", "message"],
        "primary_code": "first ordered issue code",
        "any_issue_forbids_packet": True,
        "errors": records,
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
    parent = load_module(ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py", "accepted_parent_governance_for_v041")
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
        result.append({
            "probe_identity": digest({"base": base, "mutation": row["single_mutation"]}),
            "base_object": base,
            "base_artifact": base,
            "mutation": row["single_mutation"],
            "reseal": {"mode": "accepted_manifest_content_hash" if base == "manifest_artifact" else "none"},
            "gate_entrypoint": {"exact_overlay_artifact": "overlay_validation_issues", "source_matrix_artifact": "source_matrix_validation_issues", "manifest_artifact": "manifest_contract_validation_issues"}[base],
            "actual_ordered_issues": issues,
            "expected_exact_issue": expected,
            "required_issue": expected,
            "generator_executed": True,
        })
    if len(result) != 22:
        raise SystemExit("STOP governance probe count")
    return result


def future_producer_gate_spec(api: dict[str, Any]) -> dict[str, Any]:
    modules = {
        PRODUCER_ALLOWLIST[0]: "mm_r5.public_authority_common",
        PRODUCER_ALLOWLIST[1]: "mm_r5.subject_temporal_public",
        PRODUCER_ALLOWLIST[2]: "mm_r5.aemh_match_history_public",
        PRODUCER_ALLOWLIST[3]: "public_authority_runtime_fixtures",
        PRODUCER_ALLOWLIST[4]: "test_public_authority_common",
        PRODUCER_ALLOWLIST[5]: "test_subject_temporal_public",
        PRODUCER_ALLOWLIST[6]: "test_aemh_match_history_public",
        PRODUCER_ALLOWLIST[7]: "test_public_authority_source_joins",
        PRODUCER_ALLOWLIST[8]: "test_public_authority_readonly_gate",
        PRODUCER_ALLOWLIST[9]: "challenges.test_public_authority_runtime_challenges",
        PRODUCER_ALLOWLIST[10]: None,
    }
    path_specs = [
        {
            "path": path,
            "absolute_path": str((ROOT / path).resolve()),
            "module": modules[path],
            "kind": "source" if path.startswith("poc/medical_monitoring_ai_native_r5/src/") else "evidence" if path.endswith(".json") else "test",
            "create_only": True,
        }
        for path in PRODUCER_ALLOWLIST
    ]
    signatures = [
        {"module": module_name, "signature": signature}
        for module_name, surface in api["modules"].items()
        for signature in surface["functions"]
    ]
    constructors = []
    for module_name, surface in api["modules"].items():
        for group in ("input_classes", "result_classes", "output_classes"):
            for row in surface.get(group, []):
                constructors.append({
                    "module": module_name,
                    "class_name": row["name"],
                    "decorator": row["decorator"],
                    "field_order": [item[0] for item in row["fields"]],
                    "signature": f"{row['name']}(" + ", ".join(f"{name}: {type_name}" for name, type_name in row["fields"]) + ")",
                })
    pytest_nodes = [
        f"{PRODUCER_ALLOWLIST[4]}::test_canonical_json_bytes_exact",
        f"{PRODUCER_ALLOWLIST[4]}::test_validation_result_total_order",
        f"{PRODUCER_ALLOWLIST[5]}::test_subject_builder_returns_packet_only",
        f"{PRODUCER_ALLOWLIST[5]}::test_subject_validator_rebuilds_construction_graph",
        f"{PRODUCER_ALLOWLIST[6]}::test_aemh_builder_returns_packet_only",
        f"{PRODUCER_ALLOWLIST[6]}::test_aemh_validator_preserves_history",
        f"{PRODUCER_ALLOWLIST[7]}::test_all_272_exact_joins",
        f"{PRODUCER_ALLOWLIST[7]}::test_subject_common_cutoff_instance",
        f"{PRODUCER_ALLOWLIST[8]}::test_all_authority_pins",
        f"{PRODUCER_ALLOWLIST[8]}::test_no_side_effects",
        f"{PRODUCER_ALLOWLIST[9]}::test_all_236_runtime_specs",
        f"{PRODUCER_ALLOWLIST[9]}::test_all_192_error_replays",
    ]
    commands = [
        {"mode": "normal", "argv": ["python3", "-B", "-m", "pytest", *pytest_nodes]},
        {"mode": "O", "argv": ["python3", "-O", "-B", "-m", "pytest", *pytest_nodes]},
        {"mode": "OO", "argv": ["python3", "-OO", "-B", "-m", "pytest", *pytest_nodes]},
    ]
    sensitivity = [
        {"vector_id": "SENS-01", "api": "build_subject_temporal_authority", "source_path": "/monitoring_run/project_id", "candidate_path": "/receipt/scope_identity/project_ref", "previous_path": None, "mutation": {"op": "replace", "value": "project-drift"}, "expected_changed_issue": "PUB_IDENTITY_PROJECT_MISMATCH", "expected_changed_hash": "/packet_content_hash"},
        {"vector_id": "SENS-02", "api": "build_subject_temporal_authority", "source_path": "/temporal_authority/source/scope/run_ref", "candidate_path": "/projection/scope_identity/run_ref", "previous_path": None, "mutation": {"op": "replace", "value": "run-drift"}, "expected_changed_issue": "PUB_IDENTITY_RUN_MISMATCH", "expected_changed_hash": "/packet_content_hash"},
        {"vector_id": "SENS-03", "api": "build_subject_temporal_authority", "source_path": "/temporal_authority/source/cutoff_binding/exact_date", "candidate_path": "/projection/axis_basis/cutoff_endpoint/exact_date", "previous_path": None, "mutation": {"op": "replace", "value": "2026-08-22"}, "expected_changed_issue": "PUB_IDENTITY_CUTOFF_MISMATCH", "expected_changed_hash": "/projection/projection_content_hash"},
        {"vector_id": "SENS-04", "api": "build_subject_temporal_authority", "source_path": "/visit_projection/actual_encounter_markers/0", "candidate_path": "/projection/visits/0/actual_endpoint", "previous_path": None, "mutation": {"op": "replace", "value": "different-encounter"}, "expected_changed_issue": "PUB_DATE_CANDIDATE_RANGE_MISMATCH", "expected_changed_hash": "/projection/projection_content_hash"},
        {"vector_id": "SENS-05", "api": "validate_subject_temporal_authority", "source_path": "/risk_candidates/0/severity_hint", "candidate_path": "/projection/risk_anchors/0/severity", "previous_path": None, "mutation": {"op": "replace", "value": "high"}, "expected_changed_issue": "SEM_AUTHORITY_MISMATCH", "expected_changed_hash": "/packet_content_hash"},
        {"vector_id": "SENS-06", "api": "build_aemh_match_history_authority", "source_path": "/current_result/snapshot_version", "candidate_path": "/receipt/scope_identity/snapshot_ref", "previous_path": "/projection/scope_identity/snapshot_ref", "mutation": {"op": "replace", "value": "snapshot-drift"}, "expected_changed_issue": "PUB_IDENTITY_SNAPSHOT_MISMATCH", "expected_changed_hash": "/packet_content_hash"},
        {"vector_id": "SENS-07", "api": "build_aemh_match_history_authority", "source_path": "/current_slice/subject_ref", "candidate_path": "/projection/scope_identity/subject_ref", "previous_path": "/projection/scope_identity/subject_ref", "mutation": {"op": "replace", "value": "subject-drift"}, "expected_changed_issue": "PUB_IDENTITY_SUBJECT_MISMATCH", "expected_changed_hash": "/projection/projection_content_hash"},
        {"vector_id": "SENS-08", "api": "build_aemh_match_history_authority", "source_path": "/temporal_authority/source/decision_records/0/match_state", "candidate_path": "/projection/threads/0/history_entries/1/match_state", "previous_path": "/projection/threads/0/history_entries/0/match_state", "mutation": {"op": "replace", "value": "ambiguous"}, "expected_changed_issue": "AEMH_MATCH_DECISION_DUPLICATE", "expected_changed_hash": "/projection/projection_content_hash"},
        {"vector_id": "SENS-09", "api": "validate_aemh_match_history_authority", "source_path": "/temporal_authority/source/decision_records", "candidate_path": "/projection/threads/0/history_entries", "previous_path": "/projection/threads/0/history_entries", "mutation": {"op": "remove", "index": 1}, "expected_changed_issue": "AEMH_HISTORY_NOT_APPEND_ONLY", "expected_changed_hash": "/packet_content_hash"},
        {"vector_id": "SENS-10", "api": "validate_subject_temporal_authority", "source_path": "/temporal_authority/bundle_content_identity", "candidate_path": "/receipt/receipt_content_hash", "previous_path": None, "mutation": {"op": "replace", "value": "0" * 64}, "expected_changed_issue": "PUB_HASH_MISMATCH", "expected_changed_hash": "/packet_content_hash"},
    ]
    isolation_entry = str((ROOT / PRODUCER_ALLOWLIST[8]).resolve())
    isolation = {
        "test_entry_relative": PRODUCER_ALLOWLIST[8],
        "test_entry_absolute": isolation_entry,
        "argv": ["python3", "-I", "-B", isolation_entry, "--isolation-probe"],
        "entry_cli_contract": {"main_signature": "main(argv: list[str]) -> int", "probe_flag": "--isolation-probe", "unknown_arg_policy": "exit_nonzero", "normal_pytest_import_safe": True},
        "bootstrap_paths": {"src": str((ROOT / "poc/medical_monitoring_ai_native_r5/src").resolve()), "tests": str((ROOT / "poc/medical_monitoring_ai_native_r5/tests").resolve())},
        "bootstrap_sequence": ["bootstrap_exact_local_src_tests_paths", "import_exact_candidate_modules_and_support", "construct_synthetic_inputs", "install_denial_hooks", "execute_four_public_api_call_windows", "remove_denial_hooks", "emit_probe_result"],
        "import_before_hook_forbidden": False,
        "hook_install_precedes_candidate_import": False,
        "hook_scope": "only_four_public_api_call_windows",
        "deny_families": {
            "filesystem": ["builtins.open", "pathlib.Path.open", "pathlib.Path.read_bytes", "pathlib.Path.write_bytes", "os.open"],
            "network": ["socket.socket", "urllib.request.urlopen", "http.client.HTTPConnection", "asyncio.open_connection"],
            "subprocess": ["subprocess.Popen", "subprocess.run", "os.system", "os.spawnv"],
            "dynamic_code": ["builtins.eval", "builtins.exec", "builtins.compile", "importlib.import_module"],
        },
        "api_call_windows": [
            {"window_id": "subject_build", "call": "build_subject_temporal_authority(valid_subject_source)", "positive_control": "returns SubjectTemporalAuthorityPacket", "negative_control": "filesystem sentinel raises IsolationViolation"},
            {"window_id": "subject_validate", "call": "validate_subject_temporal_authority(candidate, valid_subject_source)", "positive_control": "returns PublicAuthorityValidationResult", "negative_control": "network sentinel raises IsolationViolation"},
            {"window_id": "aemh_build", "call": "build_aemh_match_history_authority(valid_aemh_source, previous_packet)", "positive_control": "returns AEMHMatchHistoryAuthorityPacket", "negative_control": "subprocess sentinel raises IsolationViolation"},
            {"window_id": "aemh_validate", "call": "validate_aemh_match_history_authority(candidate, valid_aemh_source, previous_packet)", "positive_control": "returns PublicAuthorityValidationResult", "negative_control": "dynamic-code sentinel raises IsolationViolation"},
        ],
    }
    return {
        "schema": "future-public-authority-producer-gates-v0.4.1",
        "path_specs": path_specs,
        "module_count": 10,
        "public_signatures": signatures,
        "dataclass_constructors": constructors,
        "ast": {
            "allowed_node_types": ["Module", "Import", "ImportFrom", "ClassDef", "FunctionDef", "arguments", "arg", "Return", "Assign", "AnnAssign", "Expr", "If", "For", "comprehension", "Call", "Name", "Attribute", "Constant", "List", "Tuple", "Dict", "Set", "Subscript", "Slice", "BinOp", "BoolOp", "Compare", "UnaryOp", "keyword", "Raise", "Try", "ExceptHandler", "With", "withitem"],
            "denied_node_types": ["AsyncFunctionDef", "Await", "Yield", "YieldFrom", "Global", "Nonlocal", "Assert", "Lambda", "NamedExpr"],
            "unknown_node_policy": "fail_closed",
            "mutation_controls": [
                {"node_type": "Assert", "mutation": "inject assert True", "expected_issue": "FUTURE_AST_NODE_DENIED"},
                {"node_type": "Lambda", "mutation": "inject lambda: None", "expected_issue": "FUTURE_AST_NODE_DENIED"},
                {"node_type": "NamedExpr", "mutation": "inject walrus expression", "expected_issue": "FUTURE_AST_NODE_DENIED"},
            ],
            "allowed_import_roots": ["dataclasses", "hashlib", "json", "typing", "pytest", "mm_r1", "mm_r2", "mm_r4", "mm_r5"],
            "denied_import_roots": ["socket", "subprocess", "urllib", "http", "requests", "importlib"],
            "allowed_call_symbols": ["dataclasses.dataclass", "hashlib.sha256", "json.dumps", "tuple", "sorted", "len", "isinstance", "enumerate", "zip", "range", "PublicAuthorityConstructionError"],
            "denied_call_symbols": ["open", "eval", "exec", "compile", "__import__", "getattr", "setattr", "delattr", "globals", "locals", "vars", "subprocess.run", "subprocess.Popen", "socket.socket", "importlib.import_module"],
            "reachable_call_rules": {"roots": [item["signature"].split("(", 1)[0] for item in signatures], "closure": "same-module named functions plus explicitly allowed imported symbols", "unreachable_public_symbol_forbidden": True, "dynamic_dispatch_forbidden": True},
        },
        "pytest_node_ids": pytest_nodes,
        "commands": commands,
        "sensitivity_vectors": sensitivity,
        "isolation": isolation,
        "executed": False,
    }


def active_gate_specs(governance: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {"attack_id": f"ACTIVE-GOV-{index:03d}", "family": "accepted_parent_governance", "base_object": item["base_object"], "mutation": item["mutation"], "reseal": item["reseal"], "gate_entrypoint": item["gate_entrypoint"], "expected_exact_issue": item["expected_exact_issue"]}
        for index, item in enumerate(governance, 1)
    ]
    delta = read_json(ERROR_DELTA_DIR / "challenge_registry.json")
    rows.extend(
        {"attack_id": f"ACTIVE-DELTA-{index:03d}", "family": "accepted_error_delta", "base_object": item["base_input_ref"], "mutation": item["single_mutation"], "reseal": item["ordered_reseal"], "gate_entrypoint": item["gate_id"], "expected_exact_issue": item["error_code"]}
        for index, item in enumerate(delta["rows"], 1)
    )
    contract_attacks = [
        ("join_reducer", "/rows/0/reducer_id", "unknown_op", "join_gate", "JOIN_REDUCER_MISMATCH"),
        ("join_recipe_hash", "/rows/0/recipe_content_hash", "0" * 64, "join_gate", "JOIN_RECIPE_HASH_MISMATCH"),
        ("join_node", "/rows/0/recipe_node_id", "wrong.node", "join_gate", "JOIN_NODE_MISMATCH"),
        ("join_cross_target", "/rows/0/dependency_recipe_nodes", ["recipe.v02.aemh_packet.n02"], "join_gate", "JOIN_CROSS_TARGET_DEPENDENCY"),
        ("join_expected_plane", "/rows/0/expected_plane_ref", "blocked-v0.4", "join_gate", "JOIN_EXPECTED_PLANE_MISMATCH"),
        ("join_fail_codes", "/rows/0/fail_closed_codes", ["consumer.fake"], "join_gate", "JOIN_FAIL_CODES_MISMATCH"),
        ("join_generic_selector", "/rows/0/v02_authority_selector/json_pointer", "/source", "join_gate", "JOIN_SELECTOR_NOT_EXACT"),
        ("join_target", "/rows/0/construction_target/json_pointer", "/contracts/wrong", "join_gate", "JOIN_TARGET_UNRESOLVED"),
        ("spec_primary", "/runtime_specifications/0/primary_operation/value", "poison", "runtime_spec_replay_gate", "SPEC_PRIMARY_MISMATCH"),
        ("spec_linked", "/runtime_specifications/1/linked_operations", [], "runtime_spec_replay_gate", "SPEC_LINKED_OPERATION_MISMATCH"),
        ("spec_reseal", "/runtime_specifications/2/reseal_mode", "none", "runtime_spec_replay_gate", "SPEC_RESEAL_MISMATCH"),
        ("spec_instance", "/runtime_specifications/3/instance_selector/base_variant", "wrong", "runtime_spec_replay_gate", "SPEC_INSTANCE_SELECTOR_MISMATCH"),
        ("spec_order", "/runtime_specifications/4/reseal_order", [], "runtime_spec_replay_gate", "SPEC_ORDER_MISMATCH"),
        ("error_fabrication", "/errors/0/origin", "consumer", "error_replay_gate", "ERROR_REPLAY_FABRICATION"),
    ]
    rows.extend(
        {"attack_id": f"ACTIVE-CONTRACT-{index:03d}", "family": family, "base_object": "v0.4.1 candidate artifact", "mutation": {"op": "replace", "path": path, "value": value}, "reseal": {"mode": "full_candidate_reseal"}, "gate_entrypoint": gate, "expected_exact_issue": issue}
        for index, (family, path, value, gate, issue) in enumerate(contract_attacks, 1)
    )
    if len(rows) != 58:
        raise SystemExit(f"STOP active gate spec count: {len(rows)}")
    return rows


def test_matrix(runtime: dict[str, Any], governance: list[dict[str, Any]], errors: dict[str, Any], api: dict[str, Any]) -> dict[str, Any]:
    error_by_code = {row["code"]: row for row in errors["errors"]}
    specs = copy.deepcopy(runtime["runtime_specs"])
    for spec in specs:
        issue_objects = [
            {"code": code, "path": error_by_code[code]["path"], "message": error_by_code[code]["message"], "origin": error_by_code[code]["origin"], "priority": error_by_code[code]["priority"]}
            for code in spec["actual_ordered_issues"]
        ]
        spec["actual_ordered_issue_objects"] = issue_objects
        spec["future_validator_expected"]["ordered_issues"] = issue_objects
    future = future_producer_gate_spec(api)
    attacks = active_gate_specs(governance)
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-test-matrix-v0.4.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "current_contract_verification": {
            "spec_count": 236,
            "unique_trace_count": 236,
            "alias_count": 0,
            "subject_count": 143,
            "aemh_count": 93,
            "positive_count": 10,
            "reject_count": 226,
            "artifact_governance_probe_count": 22,
            "active_gate_check_count": 58,
            "runtime_specifications": specs,
            "artifact_governance_probes": governance,
            "active_gate_specs": attacks,
            "all_rejects_compare_complete_ordered_issue_sequence": True,
            "spec_replay_consumes_frozen_fields_only": ["base_input_ref", "pre_authority_identities", "instance_selector", "primary_operation", "linked_operations", "lane", "reseal_mode", "reseal_order", "reseal_plan"],
        },
        "future_producer_acceptance": {
            "create_only_allowlist": list(PRODUCER_ALLOWLIST),
            "files_present": False,
            "producer_executed": False,
            "runtime_tests_executed": False,
            "ast_executed": False,
            "sensitivity_executed": False,
            "isolation_executed": False,
            "machine_executable_spec": future,
        },
        "contract_spec_only": True,
        "producer_executed": False,
        "evidence_created": False,
    }

def context_markdown() -> bytes:
    return b"""# R5-S5 public authority implementation contract v0.4.1 context\n\nState: `CANDIDATE_UNACCEPTED`\n\nThis append-only nine-file contract consumes only the accepted public parent v0.1, semantic delta v0.1, temporal v0.1 primitives, temporal v0.2 full-parent-graph and accepted error-replay coverage delta v0.1. Blocked v0.4 and rejected v0.1-v0.3 remain immutable negative evidence and supply no expected plane, selector, runtime value or acceptance implication.\n\nGeneration executes 272 exact typed/v0.2/recipe/construction-target joins through an internal ConstructionGraph while the future public builders remain packet-only. It replays 236 frozen specs from their own base, selector, primary and linked operations, lane and reseal program; executes 170 accepted pre-delta error codes plus 22 accepted delta gates; and freezes 58 real active-gate specifications.\n\nThe future eleven producer paths remain absent. Their exact path/module/signature/dataclass/AST/pytest/sensitivity/isolation specification is machine-readable but unexecuted. No producer, runtime test, evidence, S5, UI/browser, real project/model, clinical authority, product, production, medical-writing state or port 8911 is accepted.\n"""


def review_markdown() -> bytes:
    return b"""# R5-S5 public authority implementation contract v0.4.1 author review\n\nDisposition: `CANDIDATE_FOR_FRESH_ISOLATED_REVIEW`. This author does not accept the candidate.\n\nThe candidate replaces blocked-v0.4 generic selectors with exact typed-instance and AuthorityBundle pointers, accepted reducer/node bindings and independently resolvable ConstructionGraph targets. Subject PublicCutoffEndpoint resolves only through the subject cutoff-binding common object produced by the subject identity/cutoff recipe.\n\nAll 236 specifications are spec-driven: identity covers pre-authority identities, instance selector, primary and linked operations, lane and reseal mode/order, while excluding labels and outcomes. Error authority is split into executed accepted pre-delta 170 and accepted delta 22. The future producer gate is exact and machine-readable but remains unexecuted because all eleven producer paths are absent.\n\nOnly a later fresh isolated reviewer may accept one immutable v0.4.1 manifest. Such acceptance can unlock only the exact eleven-file create-only producer stage.\n"""


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
        "schema": "medical-monitoring-r5-s5-public-authority-implementation-contract-manifest-v0.4.1", "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID, "status": "candidate_unaccepted", "contract_spec_only": True, "non_clinical": True,
        "authority_scope": "synthetic_test_only", "execution_profile": "full_parent_graph",
        "exact_nine_paths": list(EXACT_PATHS),
        "file_raw_sha256": {path: hashlib.sha256(outputs[path]).hexdigest() for path in EXACT_PATHS if path != f"{OUT_REL}/manifest.json"},
        "manifest_self_raw_sha256": "external_fresh_review_pin_required",
        "authority_chain_pins": AUTHORITY_PINS,
        "accepted_error_replay_delta_pins": {**ERROR_DELTA_PINS, **ERROR_DELTA_ACCEPTANCE},
        "blocked_v04_nine_file_pins_negative_evidence_only": BLOCKED_V04_PINS,
        "typed_source_pins": typed,
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
            "leaf_count": joins["row_count"], "resolved_join_count": joins["resolved_pointer_count"], "recipe_count": 16, "recipe_node_count": 32,
            "artifact_governance_probe_count": 22, "active_gate_check_count": 58,
            "pre_delta_error_replay_count": 170, "accepted_delta_error_replay_count": 22, "error_union_count": 192,
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
    tests = test_matrix(runtime, governance, errors, api)
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
