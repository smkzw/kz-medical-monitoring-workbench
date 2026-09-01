"""Generate the immutable R5-S5 public-authority implementation contract v0.3.

The contract consumes three already accepted authority surfaces.  It never
creates a producer, runtime, test, evidence, acceptance record, or a fourth
authority registry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-implementation-contract-v0.3"
SCHEMA_VERSION = "2026-08-20.4"
PUBLIC_SCHEMA_VERSION = "2026-08-19.1"
AUDIENCE_CONTRACT_ID = "contract.s4.1"
SUBJECT = "subject-temporal-public-v1"
AEMH = "aemh-match-history-public-v1"

PARENT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
SEMANTIC_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1"
TEMPORAL_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1"
ARTIFACT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3"
CONTEXT_PATH = ROOT / "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_20260820_context.md"
REVIEW_PATH = ROOT / "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_20260820.md"
GENERATOR_PATH = Path(__file__).resolve()
VERIFIER_PATH = ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py"

PARENT_MANIFEST_SHA = "92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270"
PARENT_ACCEPTANCE_SHA = "23fed5b186057a79cd0ec43a7718e43934ebafdc8f62fd251077d4fb6891639d"
SEMANTIC_MANIFEST_SHA = "66605a46c10e2aa4d36b06e566158666a08cdc92ec0e630364aad5b9ffb2385d"
SEMANTIC_ACCEPTANCE_SHA = "bf50156fa82d825309fce72115ddf971fc4e0bdbd60936ea45e2362a6aa3eb4c"
TEMPORAL_MANIFEST_SHA = "e606e517c07dcb499657b418dbd16e4dacd98c7e7010770845dbccb91af59f97"
TEMPORAL_ACCEPTANCE_SHA = "523351f1b5536b12c1a5be9251ad01f4e8b7a70f5088073a2333aefc241d1b79"

EXACT_PATHS = [
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_20260820_context.md",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_20260820.md",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/public_api.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/source_join_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/invariant_error_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/test_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/manifest.json",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py",
]

PRODUCER_ALLOWLIST = [
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
]

S5_LOCKS = [
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_contracts.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_authority_builder.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_projection.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_validator.py",
    "poc/medical_monitoring_ai_native_r5/tests/s5_runtime_fixtures.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_contracts.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_authority_builder.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_projection.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_validator.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_readonly_gate.py",
    "poc/medical_monitoring_ai_native_r5/tests/challenges/test_s5_runtime_challenges.py",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_readonly_sha256.json",
]

REJECTED_V0_2_PINS = {
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_20260820_context.md": "7e16dd10f580f6dc7dcc49a771bd62ac553e5a8bd52b1a409967815ce20f144b",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_20260820.md": "7f9e9efa935d6d6c8112cc645c84ba72fbd5670626f097e04a67d1b73aedcd9b",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/public_api.json": "5ba41225cb76b91a69e634a728fe0af83a9062f08a39a2cafadd6643de111141",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/source_join_matrix.json": "0e35d32e7d39ca2994ae1e58c8d547e170dc2cdeeb44a417210744d7f021a970",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/invariant_error_matrix.json": "7caf087038b15222abb7526f69424627d957f3b61ee4ad2fb8e15a6b4ebc2bcb",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/test_matrix.json": "f7af7ca0cf4a4567397ff0587a857f25fd9e6af80ca71689f84242f1eb906c9c",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/manifest.json": "cf805305e927caee07464061e95ac894a866b3a5a444d29f012e26ea92893e6f",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py": "aa4266cef074b8afb76d7d57993a767fdbae1dc02aba3586eccccb4d7e3110c1",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py": "e5384b6c3404288352bf8540634b4761f61a39a4e37fd133136cd17e09916104",
}

ALIASES = {
    "PA-007": ["R5C-103"],
    "PA-034": ["PA-120"],
    "PA-035": ["PA-121"],
    "PA-118": ["R5C-108"],
    "PA-129": ["R5C-111"],
}

POSITIVE_CASES = {
    "R5C-109",
    "R5C-110",
    "R5C-116",
    "R5C-157",
    "R5C-158",
    "R5C-159",
    "R5C-160",
    "R5C-161",
    "R5C-162",
    "R5C-163",
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _surface_refs() -> dict[str, Any]:
    parent_manifest = read_json(PARENT_DIR / "manifest.json")
    semantic_manifest = read_json(SEMANTIC_DIR / "manifest.json")
    temporal_manifest = read_json(TEMPORAL_DIR / "manifest.json")
    return {
        "accepted_parent": {
            "manifest_path": str((PARENT_DIR / "manifest.json").relative_to(ROOT)),
            "manifest_raw_sha256": PARENT_MANIFEST_SHA,
            "acceptance_path": "context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md",
            "acceptance_raw_sha256": PARENT_ACCEPTANCE_SHA,
            "artifact_raw_sha256": parent_manifest["artifact_raw_sha256"],
        },
        "accepted_semantic_delta": {
            "manifest_path": str((SEMANTIC_DIR / "manifest.json").relative_to(ROOT)),
            "manifest_raw_sha256": SEMANTIC_MANIFEST_SHA,
            "acceptance_path": "context/medical_monitoring_r5_s5_semantic_authority_delta_acceptance_record_20260820.md",
            "acceptance_raw_sha256": SEMANTIC_ACCEPTANCE_SHA,
            "artifact_raw_sha256": semantic_manifest["artifact_raw_sha256"],
            "policy_registry_id": semantic_manifest["synthetic_policy_acceptance_registry"]["registry_id"],
            "policy_registry_content_hash": semantic_manifest["synthetic_policy_acceptance_registry"]["registry_content_hash"],
            "typed_source_registry_id": semantic_manifest["synthetic_typed_source_record_registry"]["registry_id"],
            "typed_source_registry_content_hash": semantic_manifest["synthetic_typed_source_record_registry"]["registry_content_hash"],
        },
        "accepted_temporal_delta": {
            "manifest_path": str((TEMPORAL_DIR / "manifest.json").relative_to(ROOT)),
            "manifest_raw_sha256": TEMPORAL_MANIFEST_SHA,
            "acceptance_path": "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_acceptance_record_20260820.md",
            "acceptance_raw_sha256": TEMPORAL_ACCEPTANCE_SHA,
            "artifact_raw_sha256": temporal_manifest["artifact_raw_sha256"],
            "external_registry_root_content_hash": temporal_manifest["external_registry_root_content_hash_pin"],
            "accepted_record_content_hash_pins": temporal_manifest["accepted_record_content_hash_pins"],
            "accepted_recipe_registry_content_hash": temporal_manifest["accepted_recipe_registry_content_hash_pin"],
            "accepted_authority_output_registry_content_hash": temporal_manifest["accepted_authority_output_registry_content_hash_pin"],
            "accepted_recipe_authority_binding_registry_content_hash": temporal_manifest["accepted_recipe_authority_binding_registry_content_hash_pin"],
        },
    }


def _output_classes(schema: dict[str, Any], module: str) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "decorator": "dataclasses.dataclass(frozen=True)",
            "module": module,
            "exact_serialized_fields": [
                {"name": field, **spec} for field, spec in fields.items()
            ],
            "extra_serialized_fields_forbidden": True,
        }
        for name, fields in schema["objects"].items()
    ]


def _accepted_exact_signatures(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Freeze an accepted schema as signatures without becoming a new authority."""
    signatures: list[dict[str, Any]] = []
    for name, definition in sorted(schema["objects"].items()):
        properties = definition.get("properties", definition.get("fields", {}))
        order = definition.get("required", definition.get("exact_keys", list(properties)))
        signatures.append(
            {
                "name": name,
                "decorator": "dataclasses.dataclass(frozen=True)",
                "fields_in_exact_order": [
                    {"name": field, **properties[field]} for field in order
                ],
                "additional_properties": definition.get("additional_properties", False),
                "accepted_definition_content_hash": digest(definition),
            }
        )
    return signatures


def public_api() -> dict[str, Any]:
    subject_schema = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh_schema = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    temporal_schema = read_json(TEMPORAL_DIR / "schema.json")
    semantic_schema = read_json(SEMANTIC_DIR / "schema.json")
    common_inputs = [
        {
            "name": "AcceptedAuthoritySurfaceRef",
            "decorator": "dataclasses.dataclass(frozen=True)",
            "fields": [
                ["manifest_path", "str"],
                ["manifest_raw_sha256", "str"],
                ["acceptance_record_path", "str"],
                ["acceptance_record_raw_sha256", "str"],
                ["registry_ref", "str"],
                ["registry_content_hash", "str"],
            ],
            "authority_rule": "reference-only pointer to an accepted immutable surface; it carries no candidate-selected policy or output value",
        },
        {
            "name": "PublicAuthorityCommonSourceBundle",
            "decorator": "dataclasses.dataclass(frozen=True)",
            "fields": [
                ["source_revisions", "tuple[mm_r1.domain.SourceRevision, ...]"],
                ["listing_snapshot", "mm_r1.domain.ListingSnapshot"],
                ["monitoring_run", "mm_r1.domain.MonitoringRun"],
                ["temporal_spine", "mm_r1.domain.SubjectTemporalSpine"],
                ["scope_binding", "mm_r4.d08_contracts.ScopeBinding"],
                ["shared_spine_binding", "mm_r4.d08_contracts.SharedSpineBinding"],
                ["visibility_decision", "mm_r4.d08_contracts.VisibilityDecision"],
                ["r4_source_locators", "tuple[mm_r4.contracts.SourceLocator, ...]"],
                ["d08_source_locators", "tuple[mm_r4.d08_contracts.SourceLocator, ...]"],
                ["d08_record_nodes", "tuple[mm_r4.d08_contracts.RecordNode, ...]"],
                ["d08_time_refs", "tuple[mm_r4.d08_contracts.TimeRef, ...]"],
                ["accepted_s4_anchors", "tuple[mm_r5.s4_contracts.S4AcceptedAuthorityAnchor, ...]"],
                ["r5_authority_receipt", "mm_r5.contracts.R5AuthorityReceipt"],
                ["parent_authority", "AcceptedAuthoritySurfaceRef"],
                ["semantic_authority", "AcceptedAuthoritySurfaceRef"],
                ["temporal_authority", "AcceptedAuthoritySurfaceRef"],
            ],
        },
    ]
    subject_inputs = [
        {
            "name": "SubjectTemporalSourceBundle",
            "decorator": "dataclasses.dataclass(frozen=True)",
            "fields": [
                ["common", "PublicAuthorityCommonSourceBundle"],
                ["planned_visits", "tuple[mm_r4.visit_schedule.PlannedVisitDefinition, ...]"],
                ["actual_encounters", "tuple[mm_r4.visit_schedule.ActualEncounterRecord, ...]"],
                ["actual_activities", "tuple[mm_r4.visit_schedule.ActualActivityRecord, ...]"],
                ["visit_assignments", "tuple[mm_r4.visit_schedule.VisitAssignmentDecision, ...]"],
                ["schedule_anchors", "tuple[mm_r4.visit_schedule.TypedScheduleAnchorRef, ...]"],
                ["semantic_records", "tuple[mm_r4.aemh.SemanticRecord, ...]"],
                ["risk_candidates", "tuple[mm_r2.risk.RiskCandidate, ...]"],
                ["risk_instances", "tuple[mm_r2.risk.RiskInstance, ...]"],
                ["semantic_bundle", "AcceptedSemanticAuthorityBundle"],
                ["temporal_bundle", "AcceptedTemporalProjectionAuthorityBundle"],
            ],
            "forbidden_fields": ["expected_output", "target_output", "fixture_authority", "independent_expected_authority_registry"],
        }
    ]
    aemh_inputs = [
        {
            "name": "AEMHMatchHistorySourceBundle",
            "decorator": "dataclasses.dataclass(frozen=True)",
            "fields": [
                ["common", "PublicAuthorityCommonSourceBundle"],
                ["current_result", "mm_r1.ae_mh.AEMHResult"],
                ["current_slice", "mm_r4.aemh.AEMHSliceResult"],
                ["semantic_records", "tuple[mm_r4.aemh.SemanticRecord, ...]"],
                ["risk_candidates", "tuple[mm_r2.risk.RiskCandidate, ...]"],
                ["risk_instances", "tuple[mm_r2.risk.RiskInstance, ...]"],
                ["risk_transitions", "tuple[mm_r2.risk.RiskTransition, ...]"],
                ["temporal_bundle", "AcceptedTemporalProjectionAuthorityBundle"],
            ],
            "forbidden_fields": ["expected_output", "target_output", "fixture_authority", "owner_authored_decision_policy"],
        }
    ]
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-api-v0.3",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "python": {
            "minimum": "3.9",
            "frozen_dataclasses": True,
            "pep604_union_forbidden": True,
            "root_init_frozen": True,
            "imports": "full module path only",
        },
        "constants": {
            "public_schema_version": PUBLIC_SCHEMA_VERSION,
            "audience_contract_id": AUDIENCE_CONTRACT_ID,
            "subject_contract_id": SUBJECT,
            "aemh_contract_id": AEMH,
        },
        "accepted_bundle_types": {
            "AcceptedSemanticAuthorityBundle": {
                "definition_source": "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/schema.json",
                "definition_pointer": "/objects",
                "definition_content_hash": digest(semantic_schema["objects"]),
                "exact_dataclass_signatures": _accepted_exact_signatures(semantic_schema),
                "runtime_rule": "typed values plus references to accepted policy and source registries; candidate cannot supply policy, expected output, receipt acceptance or registry records",
            },
            "AcceptedTemporalProjectionAuthorityBundle": {
                "definition_source": "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/schema.json",
                "definition_pointer": "/objects",
                "object_names": sorted(temporal_schema["objects"]),
                "definition_content_hash": digest(temporal_schema["objects"]),
                "exact_dataclass_signatures": _accepted_exact_signatures(temporal_schema),
                "runtime_rule": "typed source, previous and controlled values reference accepted registry entries and immutable recipes; definitions and expected targets are never candidate fields",
            },
        },
        "modules": {
            "mm_r5.public_authority_common": {
                "input_classes": common_inputs,
                "result_classes": [
                    {
                        "name": "PublicAuthorityValidationIssue",
                        "decorator": "dataclasses.dataclass(frozen=True)",
                        "fields": [
                            ["code", "str"],
                            ["path", "str"],
                            ["message", "str"],
                            ["origin", "Literal['parent', 'semantic_delta', 'temporal_delta', 'consumer']"],
                            ["priority", "int"],
                        ],
                    },
                    {
                        "name": "PublicAuthorityValidationResult",
                        "decorator": "dataclasses.dataclass(frozen=True)",
                        "fields": [
                            ["ok", "bool"],
                            ["primary_code", "Optional[str]"],
                            ["issues", "tuple[PublicAuthorityValidationIssue, ...]"],
                            ["packet_emitted", "bool"],
                        ],
                        "success_invariant": "ok=true, primary_code=null, issues=(), packet_emitted=true",
                        "error_invariant": "ok=false, primary_code=issues[0].code, issues sorted by deterministic_priority, packet_emitted=false",
                    },
                ],
                "output_classes": [
                    item for item in _output_classes(subject_schema, "mm_r5.public_authority_common")
                    if item["name"] in {"PublicAuthorityReceipt", "PublicCutoffEndpoint", "PublicScopeIdentity", "PublicSourceLocator", "SourceRevisionContentPair", "VisibilityClosure"}
                ],
                "functions": [
                    "canonical_json_bytes(value: object) -> bytes",
                    "canonical_sha256(value: object) -> str",
                    "validation_result(issues: Iterable[PublicAuthorityValidationIssue]) -> PublicAuthorityValidationResult",
                ],
            },
            "mm_r5.subject_temporal_public": {
                "input_classes": subject_inputs,
                "output_classes": [
                    item for item in _output_classes(subject_schema, "mm_r5.subject_temporal_public")
                    if item["name"] not in {"PublicAuthorityReceipt", "PublicCutoffEndpoint", "PublicScopeIdentity", "PublicSourceLocator", "SourceRevisionContentPair", "VisibilityClosure"}
                ],
                "functions": [
                    "build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket",
                    "validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle) -> PublicAuthorityValidationResult",
                ],
            },
            "mm_r5.aemh_match_history_public": {
                "input_classes": aemh_inputs,
                "output_classes": [
                    item for item in _output_classes(aemh_schema, "mm_r5.aemh_match_history_public")
                    if item["name"] not in {"PublicAuthorityReceipt", "PublicCutoffEndpoint", "PublicScopeIdentity", "PublicSourceLocator", "SourceRevisionContentPair", "VisibilityClosure"}
                ],
                "functions": [
                    "build_aemh_match_history_authority(source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> AEMHMatchHistoryAuthorityPacket",
                    "validate_aemh_match_history_authority(candidate: AEMHMatchHistoryAuthorityPacket, source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> PublicAuthorityValidationResult",
                ],
            },
        },
        "output_object_contract": {
            "subject_exact_object_count": len(subject_schema["objects"]),
            "aemh_exact_object_count": len(aemh_schema["objects"]),
            "subject_schema_raw_sha256": raw_sha(PARENT_DIR / "subject_temporal_schema.json"),
            "aemh_schema_raw_sha256": raw_sha(PARENT_DIR / "aemh_match_history_schema.json"),
            "recursive_extra_add_remove_change_forbidden": True,
        },
        "accepted_canonical_semantics": {
            "subject_hash_recipes": {
                "definition_source": "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json",
                "definition_pointer": "/hash_recipes",
                "definition_content_hash": digest(subject_schema["hash_recipes"]),
            },
            "subject_invariants": {
                "definition_source": "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json",
                "definition_pointer": "/invariants",
                "definition_content_hash": digest(subject_schema["invariants"]),
            },
            "aemh_hash_recipes": {
                "definition_source": "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json",
                "definition_pointer": "/hash_recipes",
                "definition_content_hash": digest(aemh_schema["hash_recipes"]),
            },
            "aemh_invariants": {
                "definition_source": "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json",
                "definition_pointer": "/invariants",
                "definition_content_hash": digest(aemh_schema["invariants"]),
            },
            "semantic_hash_and_id_recipes": {
                "definition_source": "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/schema.json",
                "definition_pointers": ["/canonical_hash_recipes", "/canonical_id_recipes"],
                "definition_content_hash": digest({
                    "canonical_hash_recipes": semantic_schema["canonical_hash_recipes"],
                    "canonical_id_recipes": semantic_schema["canonical_id_recipes"],
                }),
            },
            "temporal_hash_contract": {
                "definition_source": "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/schema.json",
                "definition_pointer": "/hash_contract",
                "definition_content_hash": digest(temporal_schema["hash_contract"]),
            },
            "consumer_rule": "execute the pinned accepted definitions by pointer; never copy them into a fourth mutable registry",
        },
        "construction_contract": {
            "execute_all_exact_authority_emitters": 119,
            "execute_all_exact_accepted_recipes": 18,
            "output_leaf_bijection": 272,
            "semantic_leaf_count": 4,
            "s4_identity_join_count": 8,
            "candidate_output_backfill_forbidden": True,
            "baseline_output_patch_forbidden": True,
            "hash_order": "authorities -> members/endpoints -> memberships -> inner hashes -> projections -> receipts -> packets",
        },
        "side_effect_contract": {
            "file_io": "forbidden",
            "network": "forbidden",
            "subprocess": "forbidden",
            "dynamic_import": "forbidden",
            "eval_exec_compile": "forbidden",
            "artifact_reads": "forbidden",
            "typed_objects_only": True,
        },
    }


def source_join_matrix() -> dict[str, Any]:
    registry = read_json(TEMPORAL_DIR / "recipe_registry.json")
    semantic_schema = read_json(SEMANTIC_DIR / "schema.json")
    mappings = {
        row["qualified_leaf"]: row
        for row in registry["authority_output_registry"]["mappings"]
    }
    semantic_projection = semantic_schema["future_bundle_integration"]["leaf_projection"]
    rows: list[dict[str, Any]] = []
    for ordinal, coverage in enumerate(registry["coverage_ledger"], 1):
        qualified = f"{coverage['contract']}::{coverage['leaf']}"
        resolver: dict[str, Any]
        if coverage["before_status"] == "C_accepted_semantic":
            resolver = {
                "surface": "accepted_semantic_delta",
                "operation": "execute accepted semantic evaluator",
                "source_path": semantic_projection[coverage["leaf"]],
                "manifest_raw_sha256": SEMANTIC_MANIFEST_SHA,
            }
        elif coverage["closure_kind"] == "authority_root":
            mapping = mappings[qualified]
            resolver = {
                "surface": "accepted_parent_plus_temporal_delta",
                "operation": "execute accepted authority emitter",
                "mapping_id": mapping["mapping_id"],
                "mapping_content_hash": mapping["mapping_content_hash"],
                "authority_root": mapping["authority_root"],
                "emitter_op": mapping["op"],
                "minimal_dependency_fixture_refs": mapping["source_fixture_refs"],
                "minimal_dependency_field_paths": mapping["source_field_paths"],
                "dependency_refs": mapping["dependency_refs"],
            }
        elif coverage["closure_kind"] == "recipe":
            resolver = {
                "surface": "accepted_parent_plus_temporal_delta",
                "operation": "execute accepted recipe IR",
                "recipe_id": coverage["closure_ref"],
                "recipe_registry_content_hash": registry["accepted_recipe_registry_reference"]["registry_content_hash"],
                "dependency_chain": coverage["dependency_chain"],
            }
        else:
            resolver = {
                "surface": "accepted_parent_plus_temporal_delta",
                "operation": "consume accepted parent leaf or parent deterministic recipe through temporal coverage ledger",
                "parent_closure_ref": coverage["closure_ref"],
                "dependency_chain": coverage["dependency_chain"],
            }
        rows.append(
            {
                "ordinal": ordinal,
                "contract": coverage["contract"],
                "leaf": coverage["leaf"],
                "qualified_leaf": qualified,
                "before_status": coverage["before_status"],
                "post_delta_status": coverage["post_delta_status"],
                "target_output_path": coverage["target_output_path"],
                "resolver": resolver,
                "runtime_candidate_may_supply": ["typed source values", "typed previous packet", "typed controlled operational values", "accepted registry entry references"],
                "runtime_candidate_forbidden_to_supply": ["policy", "recipe definition", "emitter definition", "expected output", "acceptance record", "authority registry record"],
                "output_backfill_forbidden": True,
                "unexplained": coverage["unexplained"],
            }
        )
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-source-join-matrix-v0.3",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "row_count": len(rows),
        "rows": rows,
        "coverage": {
            "subject": sum(row["contract"] == SUBJECT for row in rows),
            "aemh": sum(row["contract"] == AEMH for row in rows),
            "semantic": sum(row["before_status"] == "C_accepted_semantic" for row in rows),
            "authority_emitters": sum(row["resolver"]["operation"] == "execute accepted authority emitter" for row in rows),
            "accepted_recipes": registry["recipe_count"],
            "unexplained": sum(row["unexplained"] for row in rows),
        },
        "accepted_registry_pins": {
            "authority_output_registry_content_hash": registry["authority_output_registry_content_hash"],
            "recipe_registry_content_hash": registry["accepted_recipe_registry_reference"]["registry_content_hash"],
            "recipe_authority_binding_registry_content_hash": registry["recipe_authority_binding_registry_content_hash"],
        },
        "forbidden": [
            "candidate-target-example-fixture mirroring",
            "class-wide value closure",
            "nearest fallback",
            "nominal-to-actual inference",
            "D07 OTHER",
            "S4 value transfer",
            "free-form Any or Mapping authority",
            "case, fixture, sentinel or label branching",
            "model-role escalation",
        ],
    }


def invariant_error_matrix() -> dict[str, Any]:
    subject = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    semantic = read_json(SEMANTIC_DIR / "schema.json")
    temporal_challenges = read_json(TEMPORAL_DIR / "challenge_registry.json")
    parent_codes = list(dict.fromkeys(subject["error_codes"] + aemh["error_codes"]))
    semantic_codes = semantic["typed_error_priority"]
    temporal_codes = sorted({row["expected_error"] for row in temporal_challenges["cases"]})
    priority = parent_codes + semantic_codes + temporal_codes
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-invariant-error-matrix-v0.3",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "accepted_parent_error_codes": parent_codes,
        "accepted_semantic_delta_error_codes": semantic_codes,
        "accepted_temporal_delta_error_codes": temporal_codes,
        "deterministic_priority": [
            {"priority": index, "code": code, "origin": "parent" if code in parent_codes else "semantic_delta" if code in semantic_codes else "temporal_delta"}
            for index, code in enumerate(priority, 1)
        ],
        "error_union_count": len(priority),
        "priority_algorithm": "collect exact namespaced codes, deduplicate within each accepted surface, then sort by this total integer priority; any issue forbids packet emission",
        "optimized_python_identical": True,
        "cross_contract_invariants": [
            "all 272 leaves are constructed from the three accepted surfaces with no fourth authority",
            "four semantic leaves resolve only through the semantic delta",
            "all former-D leaves execute the temporal delta emitter or recipe declared for that exact leaf",
            "S4 transfers exactly eight identity joins and no semantic value",
            "AE/MH previous prefix is byte-identical and suffix lifecycle is valid",
            "CanonicalFact.fact_hash is the later-fact identity authority",
            "all source locator revisions are consumed exactly and visibility/membership closure is exact",
        ],
    }


def _all_parent_cases() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    registry = read_json(PARENT_DIR / "challenge_registry.json")
    all_rows = registry["inherited_cases"] + registry["public_authority_specific_cases"]
    governance = [row for row in all_rows if str(row.get("base_input_key", "")).endswith("_artifact")]
    runtime = [row for row in all_rows if row not in governance]
    return runtime, governance


def _fixture_key(row: dict[str, Any]) -> str:
    if row.get("base_input_key"):
        return str(row["base_input_key"])
    return "subject_temporal_valid_base" if row["contract"] == SUBJECT else "aemh_match_history_valid_base"


def _select_join(row: dict[str, Any], joins: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [item for item in joins if item["contract"] == row["contract"]]
    tokens = [token for token in str(row["single_mutation"]["path"]).lower().replace("/", "_").split("_") if token]
    scored = []
    for item in candidates:
        haystack = item["leaf"].lower()
        scored.append((sum(token in haystack for token in tokens), item["ordinal"], item))
    return max(scored, key=lambda value: (value[0], -value[1]))[2]


def _expected_error(row: dict[str, Any]) -> str | None:
    outcome = row["expected_typed_outcome_or_error"]
    if not outcome.startswith("reject:"):
        return None
    code = outcome.split("reject:", 1)[1]
    if code.startswith(("PUB_", "AEMH_", "SEM_", "TPA_")):
        return code
    category = row["category"]
    path = row["single_mutation"]["path"].lower()
    if category == "visit_semantics":
        return "PUB_UNSCHEDULED_PLANNED_BINDING_FORBIDDEN" if "unscheduled" in path else "PUB_REFERENCE_UNRESOLVED"
    if category == "axis_conversion":
        return "PUB_STUDY_DAY_VALUE_MISMATCH"
    if category == "uncertain_dates":
        return "PUB_DATE_STATE_INVALID"
    if category in {"eight_domain_adaptation", "encoding_registry"}:
        return "SEM_AUTHORITY_MISMATCH" if any(token in path for token in ("domain", "severity", "encoding")) else "PUB_DOMAIN_APPLICABILITY_MISMATCH"
    if category == "aemh_projection":
        return "AEMH_IDENTITY_EVIDENCE_MISMATCH"
    if category == "aemh_match_history":
        return "AEMH_LIFECYCLE_TRANSITION_INVALID"
    return "PUB_REFERENCE_UNRESOLVED"


def _linked_operations(case_id: str, selected: dict[str, Any]) -> list[dict[str, Any]]:
    if case_id == "R5C-109":
        return [
            {"selector": "MonitoringRun.data_cutoff", "op": "replace_exact_typed_source"},
            {"selector": "ScopeBinding.clinical_event_cutoff", "op": "replace_exact_typed_source"},
            {"selector": "TimeRef.value", "op": "replace_exact_typed_source"},
            {"selector": "CutoffEndpointBindingAuthority.cutoff_ref", "op": "replace_exact_typed_authority"},
            {"selector": "S4AcceptedAuthorityAnchor.cutoff_ref", "op": "replace_exact_identity_join"},
        ]
    resolver = selected["resolver"]
    selector = resolver.get("mapping_id") or resolver.get("recipe_id") or selected["qualified_leaf"]
    return [{"selector": selector, "op": "mutate_one_actual_typed_instance_then_execute_full_construction_plan"}]


def test_matrix(joins_doc: dict[str, Any]) -> dict[str, Any]:
    runtime_rows, governance_rows = _all_parent_cases()
    by_id = {row["case_id"]: row for row in runtime_rows}
    alias_ids = {alias for values in ALIASES.values() for alias in values}
    base_inputs = read_json(PARENT_DIR / "base_inputs.json")
    surface_refs = _surface_refs()
    contract_plans: dict[str, Any] = {}
    for contract in (SUBJECT, AEMH):
        rows = [row for row in joins_doc["rows"] if row["contract"] == contract]
        contract_plans[contract] = {
            "exact_leaf_count": len(rows),
            "qualified_leaves": [row["qualified_leaf"] for row in rows],
            "authority_mapping_ids": [row["resolver"]["mapping_id"] for row in rows if "mapping_id" in row["resolver"]],
            "recipe_ids": sorted({row["resolver"]["recipe_id"] for row in rows if "recipe_id" in row["resolver"]}),
            "semantic_leafs": [row["qualified_leaf"] for row in rows if row["before_status"] == "C_accepted_semantic"],
            "complete_packet_required": True,
            "baseline_output_patch_forbidden": True,
        }
    specs: list[dict[str, Any]] = []
    identities: set[str] = set()
    for row in runtime_rows:
        case_id = row["case_id"]
        if case_id in alias_ids:
            continue
        covered = [case_id] + ALIASES.get(case_id, [])
        accepted_rows = [by_id[item] for item in covered]
        selected = _select_join(row, joins_doc["rows"])
        fixture_key = _fixture_key(row)
        fixture_value = base_inputs[fixture_key]
        lane = "typed_source_to_builder" if case_id in POSITIVE_CASES else "typed_candidate_to_validator"
        linked = _linked_operations(case_id, selected)
        reseal_targets = []
        if row.get("fully_reseal_after_mutation") is True:
            schema_path = PARENT_DIR / (
                "subject_temporal_schema.json" if row["contract"] == SUBJECT else "aemh_match_history_schema.json"
            )
            accepted_schema = read_json(schema_path)
            reseal_targets = sorted(accepted_schema["hash_recipes"])
        identity_payload = {
            "contract": row["contract"],
            "lane": lane,
            "typed_candidate_fixture_content_hash": digest(fixture_value),
            "exact_mutation": row["single_mutation"],
            "selected_authority_resolver": selected["resolver"],
            "linked_operations": linked,
            "canonical_reseal_targets": reseal_targets,
            "construction_plan_hash": digest(contract_plans[row["contract"]]),
        }
        identity = digest(identity_payload)
        if identity in identities:
            raise RuntimeError(f"unexpected non-alias future input collision: {case_id}")
        identities.add(identity)
        expected_code = _expected_error(row)
        specs.append(
            {
                "spec_id": f"future-spec::{identity[:20]}",
                "covered_trace_case_ids": covered,
                "contract": row["contract"],
                "harness_lane": lane,
                "typed_fixture_reference_packet": {
                    "candidate_fixture_source": "accepted parent base_inputs candidate example; never authority",
                    "candidate_fixture_key": fixture_key,
                    "candidate_fixture_content_hash": digest(fixture_value),
                    "accepted_surface_refs": surface_refs,
                    "selected_exact_leaf": selected["qualified_leaf"],
                    "selected_authority_resolver": selected["resolver"],
                    "construction_plan_ref": row["contract"],
                },
                "one_exact_mutation": row["single_mutation"],
                "linked_source_operations": linked,
                "canonical_reseal_targets": reseal_targets,
                "expected_typed_result_or_error": {
                    "disposition": "accept" if expected_code is None else "reject",
                    "packet_type": "SubjectTemporalAuthorityPacket" if row["contract"] == SUBJECT else "AEMHMatchHistoryAuthorityPacket",
                    "primary_code": expected_code,
                    "accepted_trace_outcomes": [item["expected_typed_outcome_or_error"] for item in accepted_rows],
                },
                "forbidden_audience_output": sorted({value for item in accepted_rows for value in item["forbidden_audience_output"]}),
                "future_pytest_node": (
                    "poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py::"
                    f"test_future_spec[{identity[:20]}]"
                ),
                "non_llm_oracle": {
                    "execute_parent_schema_validator": True,
                    "execute_semantic_evaluator_for_four_subject_leaves": row["contract"] == SUBJECT,
                    "execute_temporal_emitters_and_recipes": True,
                    "recompute_all_dependent_ids_hashes_containers_receipts_packets": True,
                    "exact_primary_code": expected_code,
                    "no_case_id_label_fixture_name_or_sentinel_branch": True,
                },
                "future_spec_input_identity": identity,
                "input_identity_payload_sha256": digest(identity_payload),
                "producer_executed": False,
                "contract_spec_only": True,
            }
        )
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-test-matrix-v0.3",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "counts": {
            "accepted_case_trace_total": len(runtime_rows),
            "future_executable_spec_total": len(specs),
            "alias_group_count": len(ALIASES),
            "alias_trace_delta": sum(len(value) for value in ALIASES.values()),
            "artifact_governance_probe_total": len(governance_rows),
            "positive_spec_total": sum(spec["expected_typed_result_or_error"]["disposition"] == "accept" for spec in specs),
        },
        "aliases": [
            {"canonical_case_id": key, "alias_case_ids": value, "covered_case_ids": [key] + value}
            for key, value in ALIASES.items()
        ],
        "identity_contract": {
            "included_fields": ["contract", "harness_lane", "typed candidate fixture bytes", "exact mutation", "accepted authority resolver", "linked operations", "canonical reseal target set", "construction plan hash"],
            "excluded_fields": ["case_id", "rule_id", "labels", "fixture names", "oracle fields", "expected code", "sentinels"],
            "independently_recomputed": True,
            "distinct_identity_count": len(identities),
        },
        "contract_construction_plans": contract_plans,
        "future_runtime_specs": specs,
        "artifact_governance_probes": [
            {
                "case_id": row["case_id"],
                "contract": row["contract"],
                "base_input_key": row["base_input_key"],
                "mutation": row["single_mutation"],
                "expected_exact_error": row["expected_typed_outcome_or_error"].split("reject:", 1)[1],
                "execute_now": True,
            }
            for row in governance_rows
        ],
        "future_runtime_static_and_isolation_gates": {
            "exact_source_targets": PRODUCER_ALLOWLIST[:3],
            "forbidden_ast_nodes": ["Assert", "Lambda", "NamedExpr"],
            "forbidden_import_roots": ["artifacts", "importlib", "io", "os", "pathlib", "subprocess", "tests", "tools"],
            "forbidden_calls": ["__import__", "compile", "eval", "exec", "getattr", "open", "read", "write"],
            "forbidden_runtime_identifiers": ["adapter_id", "case_id", "fixture_id", "sentinel"],
            "isolation_probe": "python3 -I -B; import before audit hook, then deny file/network/subprocess/dynamic import/eval/exec/compile during all four public API calls",
            "sensitivity_vectors": "future producer tests mutate candidate/source and AE-MH previous independently; issues/ok/primary_code must change as specified",
            "contract_stage_execution": False,
        },
    }


def _rejected_v0_1_pins() -> dict[str, str]:
    semantic_manifest = read_json(SEMANTIC_DIR / "manifest.json")
    return semantic_manifest["rejected_implementation_contract_snapshot_negative_evidence_only"]["pins"]


def manifest(bundle: dict[Path, bytes]) -> dict[str, Any]:
    temporal_matrix = read_json(TEMPORAL_DIR / "source_matrix_delta.json")
    parent_manifest = read_json(PARENT_DIR / "manifest.json")
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-implementation-manifest-v0.3",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "exact_implementation_contract_paths": EXACT_PATHS,
        "artifact_raw_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(data).hexdigest()
            for path, data in bundle.items()
            if path.parent == ARTIFACT_DIR and path.name != "manifest.json"
        },
        "accepted_authority_surfaces": _surface_refs(),
        "source_file_sha256": temporal_matrix["accepted_source_file_sha256"],
        "protected_accepted_pins": parent_manifest["protected_accepted_pins"],
        "rejected_snapshots_negative_evidence_only": {
            "v0_1": _rejected_v0_1_pins(),
            "v0_2": REJECTED_V0_2_PINS,
            "authority": False,
        },
        "authority_consumption": {
            "leaf_bijection": 272,
            "authority_emitters": 119,
            "accepted_recipe_definitions": 18,
            "semantic_leaves": 4,
            "fourth_local_authority_layer_created": False,
        },
        "future_runtime_spec_counts": {"distinct_specs": 231, "accepted_traces": 236, "aliases": 5, "governance_probes": 22},
        "producer_create_only_allowlist": PRODUCER_ALLOWLIST,
        "producer_surface_must_be_absent_before_acceptance": True,
        "producer_bytecode_and_cache_must_be_absent": True,
        "s5_runtime_locked_paths": S5_LOCKS,
        "root_init_frozen": True,
        "medical_writing_file_count": 542,
        "medical_writing_inventory_sha256": "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca",
        "port_8911_must_be_stopped": True,
        "acceptance_checks": {
            "generator_check": "PYTHONDONTWRITEBYTECODE=1 python3 -B tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py --check",
            "verifier_normal": "PYTHONDONTWRITEBYTECODE=1 python3 -B tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py",
            "verifier_o": "PYTHONOPTIMIZE=1 PYTHONDONTWRITEBYTECODE=1 python3 -O -B tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py",
            "verifier_oo": "PYTHONOPTIMIZE=2 PYTHONDONTWRITEBYTECODE=1 python3 -OO -B tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py",
            "hash_seeds": ["0", "1", "8675309"],
            "byte_identical_generations": 2,
            "ruff": "/Users/smkzw/.local/bin/uvx --offline ruff check --no-cache tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py",
        },
        "python_assert_statements_allowed": False,
        "unlock": {
            "only_later_exact_token": "ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_3",
            "unlocks_only": PRODUCER_ALLOWLIST,
            "does_not_accept": ["either producer", "S5", "UI/browser", "real project/model", "clinical authority", "product", "production", "medical writing"],
            "self_acceptance_forbidden": True,
        },
        "manifest_hash_recipe": "sha256(canonical JSON of all keys except manifest_content_hash)",
    }


def context_markdown() -> bytes:
    text = f"""# Task Context: public authority implementation contract v0.3

Date: 2026-08-20  
State: `FROZEN_FOR_FRESH_INDEPENDENT_REVIEW`  
Objective: freeze the exact future implementation contract for `{SUBJECT}` and `{AEMH}` without creating a producer.

## Authority boundary

This contract consumes exactly three immutable accepted surfaces: parent `{PARENT_MANIFEST_SHA}`, semantic delta `{SEMANTIC_MANIFEST_SHA}`, and temporal delta `{TEMPORAL_MANIFEST_SHA}`. It creates no local authority mirror, expected-value registry, owner-authored decision policy, or acceptance receipt. Candidate data may carry typed source/previous/controlled values and accepted registry references only.

The accepted output schemas remain exactly 17 subject objects and 13 AE/MH objects. Four semantic leaves resolve only through the semantic delta. The other 268 leaves resolve through the parent plus the temporal delta; the temporal delta supplies the exact 272-leaf ledger, 119 operation-specific emitters, 18 accepted recipe definitions, minimal dependency slices, registry pins, typed fixtures and construction DAG. S4 remains exactly eight identity joins.

## Write and unlock boundary

Only the nine v0.3 paths named in the task are writable. Producer, test, evidence, S5, UI, browser, services, runtime, real projects/models, clinical authority, product, production and medical writing remain locked. Port 8911 remains stopped. This worker does not issue acceptance.

## Frozen inventories

- 272 exact output leaves: subject 156, AE/MH 116; unexplained 0.
- 119 accepted authority emitters across six operation branches; 18 accepted recipes.
- 231 distinct future executable input specs cover 236 accepted traces through exactly five aliases.
- 22 artifact-governance probes execute now and remain outside runtime inventory.
- Future producers receive typed objects and cannot read artifacts or use file/network/subprocess/dynamic import/eval/exec.

## Next action

A fresh isolated reviewer must run the exact normal/O/OO, cross-seed, double-generation, Ruff, pin, absence and 8911 gates. Only the exact token `ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_3` may unlock the eleven producer paths; it accepts no producer or downstream stage.
"""
    return text.encode("utf-8")


def review_markdown() -> bytes:
    text = """# R5-S5 public authority implementation contract v0.3

Status: `FROZEN_FOR_FRESH_INDEPENDENT_REVIEW`

## Result

The v0.3 contract replaces the rejected v0.1/v0.2 local expected-authority design with direct consumption of the three accepted authority surfaces. No candidate or target output is an oracle. The future builder must execute accepted operation-specific emitters and recipe IR, then rebuild identifiers, hashes, memberships, projections, receipts and packets upstream-first.

The Python floor is 3.9. Exact dataclass and function signatures are frozen in `public_api.json`; imports use full module paths and root `mm_r5/__init__.py` remains unchanged. Serialized output schemas are byte-pinned to the accepted 17/13 schemas.

## Source and invariant closure

`source_join_matrix.json` contains the accepted temporal delta's exact 272-row bijection. It binds 119 leaves to accepted authority emitters, 50 former-D dependent leaves to accepted recipe IR, four leaves to the accepted semantic delta, and the remaining accepted parent/derived leaves to the parent-plus-temporal closure. No row permits output backfill, class-wide value closure, nearest fallback, nominal-to-actual inference, D07 OTHER, S4 semantic transfer, `Any`/`Mapping` authority, sentinel branching or model escalation.

`invariant_error_matrix.json` creates one deterministic total priority across the accepted parent codes and namespaced `SEM_*` and `TPA_*` delta errors. Any issue forbids packet emission. AE/MH prefix bytes, membership, evidence identity, reachable `CanonicalFact.fact_hash`, append lifecycle and packet hashes remain fail-closed.

## Test inventory

Exactly 231 executable future specs cover 236 accepted traces through five exact aliases. Identity is recomputed without case IDs, labels, fixture names, oracle fields, expected codes or sentinels. Each spec freezes a typed candidate/reference packet, one accepted trace mutation, actual-instance selector/linked operations, typed result/error, forbidden output, exact future pytest node and non-LLM oracle. Ten positive specs require full packet construction from transformed typed sources; baseline output patching is forbidden.

The 22 parent artifact-governance cases are separate and execute during contract verification. The accepted temporal verifier's 418 challenges and this verifier's exact emitter/recipe execution cover fully resealed self-authorization, simultaneous candidate/target drift, cyclic fixtures, same-type swaps, cross-scope joins, membership changes, forged endpoints/counts/locators/visibility/pending/phase/risk/AE-MH evidence, prefix rewrite and wrong fact identity.

## Non-transfer

This document is not an acceptance record and does not accept a producer, S5, UI/browser, real project/model, clinical authority, product, production or medical writing. A later independent reviewer alone may return `ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_3`.
"""
    return text.encode("utf-8")


def check_source_pins() -> None:
    exact = {
        PARENT_DIR / "manifest.json": PARENT_MANIFEST_SHA,
        ROOT / "context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md": PARENT_ACCEPTANCE_SHA,
        SEMANTIC_DIR / "manifest.json": SEMANTIC_MANIFEST_SHA,
        ROOT / "context/medical_monitoring_r5_s5_semantic_authority_delta_acceptance_record_20260820.md": SEMANTIC_ACCEPTANCE_SHA,
        TEMPORAL_DIR / "manifest.json": TEMPORAL_MANIFEST_SHA,
        ROOT / "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_acceptance_record_20260820.md": TEMPORAL_ACCEPTANCE_SHA,
    }
    for path, expected in exact.items():
        actual = raw_sha(path)
        if actual != expected:
            raise RuntimeError(f"accepted authority pin drift: {path}: {actual}")
    for relative, expected in {**_rejected_v0_1_pins(), **REJECTED_V0_2_PINS}.items():
        actual = raw_sha(ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"rejected snapshot byte drift: {relative}: {actual}")


def build_bundle() -> dict[Path, bytes]:
    check_source_pins()
    api = public_api()
    joins = source_join_matrix()
    errors = invariant_error_matrix()
    tests = test_matrix(joins)
    bundle = {
        ARTIFACT_DIR / "public_api.json": json_bytes(api),
        ARTIFACT_DIR / "source_join_matrix.json": json_bytes(joins),
        ARTIFACT_DIR / "invariant_error_matrix.json": json_bytes(errors),
        ARTIFACT_DIR / "test_matrix.json": json_bytes(tests),
        CONTEXT_PATH: context_markdown(),
        REVIEW_PATH: review_markdown(),
    }
    manifest_value = manifest(bundle)
    manifest_value["manifest_content_hash"] = digest(manifest_value)
    bundle[ARTIFACT_DIR / "manifest.json"] = json_bytes(manifest_value)
    return bundle


def write_or_check(bundle: dict[Path, bytes], check: bool) -> None:
    mismatches: list[str] = []
    for path, data in bundle.items():
        if check:
            if not path.is_file() or path.read_bytes() != data:
                mismatches.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if mismatches:
        raise RuntimeError("generated snapshot mismatch: " + ", ".join(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    bundle = build_bundle()
    write_or_check(bundle, args.check)
    print(
        "PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_3_GENERATION_OK "
        "files=7 leaves=272 emitters=119 recipes=18 specs=231 traces=236 aliases=5 governance=22"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
