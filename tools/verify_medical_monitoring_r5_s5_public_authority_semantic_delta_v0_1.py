"""Independent verifier for the R5-S5 semantic-authority delta.

This module intentionally does not import the generator.  Candidate package and
evidence hashes are integrity checks only; authority is resolved against two
externally pinned, synthetic-only registry roots.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-semantic-delta-v0.1"
EXPECTED_SOURCE_REGISTRY_SHA256 = "28d536579be39b80bdb3dc1033845cae0eea27d362eef1375ac66eb3a34c5939"
EXPECTED_ACCEPTANCE_REGISTRY_SHA256 = "71dc168b99dd1ea2d768284fe69e0c0cdd013b9fa261e85132f0b334cf20e075"
PARENT_MANIFEST = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json"
PARENT_MANIFEST_SHA256 = "92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270"
PARENT_ACCEPTANCE = "context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md"
PARENT_ACCEPTANCE_SHA256 = "23fed5b186057a79cd0ec43a7718e43934ebafdc8f62fd251077d4fb6891639d"
MANIFEST_PATH = "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/manifest.json"
SCHEMA_PATH = "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/schema.json"
CHALLENGE_PATH = "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/challenge_registry.json"
SOURCE_MATRIX_PATH = "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/source_matrix_delta.json"
GENERATOR_PATH = "tools/generate_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py"
VERIFIER_PATH = "tools/verify_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py"

EXACT_PATHS = (
    "context/medical_monitoring_r5_s5_semantic_authority_delta_20260820_context.md",
    "reviews/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1_20260820.md",
    SCHEMA_PATH, SOURCE_MATRIX_PATH, CHALLENGE_PATH, MANIFEST_PATH,
    GENERATOR_PATH, VERIFIER_PATH,
)
IDENTITY_KEYS = {"project_ref", "run_ref", "snapshot_ref", "cutoff_ref", "site_ref", "subject_ref", "risk_ref", "spine_ref"}
DOMAINS = {"ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure", "symptom_efficacy", "protocol_compliance"}
SUBTYPE_TO_DOMAIN = {
    "ae": "ae", "mh": "mh", "concomitant_medication": "cm",
    "ip_dose": "ip", "ip_pause": "ip", "ip_resume": "ip",
    "lab": "lab_exam", "exam": "lab_exam", "hospitalization": "hospital_procedure",
    "procedure": "hospital_procedure", "symptom": "symptom_efficacy",
    "efficacy": "symptom_efficacy", "scale": "symptom_efficacy",
    "outcome": "symptom_efficacy", "trend": "symptom_efficacy",
    "protocol_deviation": "protocol_compliance",
}
EVENT_EXPECTED = {
    "AE": "ae", "MH": "mh", "CM": "concomitant_medication", "LAB": "lab",
    "EXAM": "exam", "HOSPITALIZATION": "hospitalization", "PROCEDURE": "procedure",
    "SYMPTOM": "symptom", "EFFICACY": "efficacy", "SCALE": "scale",
    "OUTCOME": "outcome", "TREND": "trend", "PROTOCOL_DEVIATION": "protocol_deviation",
}
COMPOUND_EXPECTED = {"DOSE": "ip_dose", "PAUSE": "ip_pause", "RESUME": "ip_resume"}
RISK_EXPECTED = {
    "RISK_TYPE_POTENTIAL_UNREPORTED_AE": "potential_unreported_ae",
    "RISK_TYPE_POTENTIAL_UNREPORTED_MH": "potential_unreported_mh",
    "RISK_TYPE_CONCOMITANT_MEDICATION": "concomitant_medication_risk",
    "RISK_TYPE_PROTOCOL_COMPLIANCE": "protocol_compliance_risk",
}
LABEL_EXPECTED = {
    "potential_unreported_ae": "潜在未报告AE", "potential_unreported_mh": "潜在未报告既往史",
    "concomitant_medication_risk": "合并用药风险", "protocol_compliance_risk": "方案依从性风险",
}
SEVERITY_EXPECTED = {"critical": "critical", "high": "high", "medium": "medium", "low": "low", "severe": "high", "moderate": "medium", "mild": "low"}
GENERIC_LABELS = {"AE风险", "MH风险", "CM风险", "IP风险", "检验检查风险", "住院操作风险", "症状疗效风险", "方案风险", "通用风险"}
RISK_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
TYPED_ERROR_PRIORITY = [
    "SEM_SCHEMA_EXACT_KEYS", "SEM_TYPE_MISMATCH", "SEM_PARENT_PIN_DRIFT",
    "SEM_ORIGINAL_PATH_OVERWRITE_FORBIDDEN", "SEM_ACCEPTANCE_TOKEN_LEAKAGE",
    "SEM_EXAMPLE_AS_AUTHORITY_FORBIDDEN", "SEM_S4_VALUE_TRANSFER_FORBIDDEN",
    "SEM_MATCHING_POLICY_FORBIDDEN", "SEM_SEVERITY_ENUM_INVALID",
    "SEM_LEGACY_SEVERITY_RULE_MISSING", "SEM_SAE_AESI_PROMOTION_FORBIDDEN",
    "SEM_SEVERITY_PROMOTION_FORBIDDEN", "SEM_EVENT_RELATION_INCOMPLETE",
    "SEM_RISK_TAXONOMY_INCOMPLETE", "SEM_RISK_TAXONOMY_AMBIGUOUS",
    "SEM_RISK_TYPE_CODE_INVALID", "SEM_RISK_TYPE_CODE_HASH_MISMATCH",
    "SEM_LEXICON_LOCALE_MISMATCH", "SEM_GENERIC_RISK_LABEL_FORBIDDEN",
    "SEM_LEXICON_TAXONOMY_MISMATCH", "SEM_LEXICON_CODE_MISSING", "SEM_LEXICON_LABEL_MISMATCH",
    "SEM_SEVERITY_RULESET_INCOMPLETE", "SEM_PACKAGE_HASH_MISMATCH",
    "SEM_EVIDENCE_HASH_MISMATCH", "SEM_SOURCE_REGISTRY_PIN_MISMATCH",
    "SEM_SOURCE_RECORD_UNRESOLVED", "SEM_SOURCE_RECORD_HASH_MISMATCH",
    "SEM_SOURCE_RECORD_OWNER_MISMATCH", "SEM_SOURCE_RECORD_VALUE_MISMATCH",
    "SEM_SOURCE_RECORD_REVISION_MISMATCH", "SEM_SOURCE_RECORD_LOCATOR_MISMATCH",
    "SEM_IDENTITY_JOIN_MISMATCH", "SEM_SYNTHETIC_CLINICAL_AUTHORITY_FORBIDDEN",
    "SEM_RECEIPT_HASH_MISMATCH", "SEM_ACCEPTANCE_REGISTRY_PIN_MISMATCH",
    "SEM_ACCEPTED_RECORD_UNRESOLVED", "SEM_ACCEPTED_RECORD_HASH_MISMATCH",
    "SEM_RECEIPT_PACKAGE_KIND_MISMATCH", "SEM_RECEIPT_PACKAGE_MISMATCH",
    "SEM_ACCEPTED_RECORD_PACKAGE_MISMATCH", "SEM_RULE_DUPLICATE_OR_AMBIGUOUS",
    "SEM_EVENT_TOKEN_UNMAPPED", "SEM_RISK_TOKEN_UNMAPPED",
    "SEM_SEVERITY_TOKEN_UNMAPPED", "SEM_SEVERITY_CONFLICT",
    "SEM_AUTHORITY_HASH_MISMATCH", "SEM_AUTHORITY_MISMATCH", "SEM_MANIFEST_HASH_MISMATCH",
]

NEGATIVE_PINS = {
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1_20260819.md": "67aae3a80f928f6887d594bc9a1fbd53fb6e5a9eb0947853f263cd3294f0c745",
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_20260819_context.md": "74b61738458f5f564a19b9867cf59e232100467ab2bc15fc964c63b88b20be05",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/public_api.json": "70dd9ffea90d84145b00cb058f32cb30a93220e79d23fcf17cbe64e26fb7a0bc",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/source_join_matrix.json": "b4c4504fdb616e76012d1ae57e71abc57ea384896f3d3aa784db85c696983213",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/invariant_error_matrix.json": "36e3497f9993f631d3c62abb144cbaad4aca339d60053a13656c6f164fac9e20",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/test_matrix.json": "428bc85b806212e7ce4d03bffc6bd807aff2bfae9e7f288adeae0508fdb91c2e",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/manifest.json": "19d1769095d884f9bc5409a2af6795f24fce7f8c81c5132f2dce54b34303502a",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py": "6a02c5c65565d1ff7becad4b71f8413e695f8d556d97abbc1d5d9b2e2ff1b3b0",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py": "c20c7b2008c4c441b80c91ee0a5f6c2118bb9303ddfcfa025dda88e65a953d94",
}


class SemanticError(Exception):
    def __init__(self, code: str, path: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.path = path


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else canonical_bytes(value)).hexdigest()


def raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_hash(value: dict[str, Any], hash_field: str) -> str:
    copy_value = copy.deepcopy(value)
    copy_value.pop(hash_field, None)
    return sha(copy_value)


def exact_keys(value: Any, required: set[str], path: str) -> None:
    if not isinstance(value, dict) or set(value) != required:
        raise SemanticError("SEM_SCHEMA_EXACT_KEYS", path)


def require_hash(value: dict[str, Any], field: str, code: str, path: str) -> None:
    if value.get(field) != object_hash(value, field):
        raise SemanticError(code, path)


SOURCE_PAIR_KEYS = {"source_ref", "source_content_hash"}
SOURCE_RECORD_KEYS = {"source_record_ref", "source_type_path", "owner_field_path", "owner_ref", "field_path", "field_value", "identity_join", "source_revision_content_pairs", "source_locator_refs", "source_record_content_hash"}
SOURCE_REGISTRY_KEYS = {"registry_id", "authority_scope", "non_clinical", "records", "registry_content_hash"}
ACCEPTED_RECORD_KEYS = {"accepted_record_ref", "package_kind", "package_id", "package_version", "package_content_hash", "authority_scope", "non_clinical", "acceptance_basis", "accepted_record_content_hash"}
ACCEPTANCE_REGISTRY_KEYS = {"registry_id", "authority_scope", "non_clinical", "records", "registry_content_hash"}
RECEIPT_KEYS = {"receipt_id", "registry_id", "registry_content_hash", "accepted_record_ref", "accepted_record_content_hash", "package_kind", "package_id", "package_version", "package_content_hash", "authority_scope", "audience_contract_id", "receipt_content_hash"}
TOKEN_EVIDENCE_KEYS = {"evidence_ref", "source_registry_id", "source_registry_content_hash", "source_record_ref", "source_record_content_hash", "owner_type", "owner_ref", "field_path", "raw_token", "snapshot_ref", "source_content_identity", "source_revision_content_pairs", "source_locator_refs", "evidence_content_hash"}
FLAG_EVIDENCE_KEYS = {"evidence_ref", "source_registry_id", "source_registry_content_hash", "source_record_ref", "source_record_content_hash", "owner_type", "owner_ref", "field_path", "flags", "snapshot_ref", "source_content_identity", "source_revision_content_pairs", "source_locator_refs", "evidence_content_hash"}
EXACT_COMPONENT_KEYS = {"field_path", "exact_raw_token"}
EVENT_RULE_KEYS = {"rule_id", "owner_type", "field_path", "exact_raw_token", "output_subtype"}
COMPOUND_RULE_KEYS = {"rule_id", "owner_type", "components", "output_subtype"}
EVENT_PACKAGE_KEYS = {"package_id", "package_version", "package_state", "matching_policy", "exact_rules", "compound_rules", "subtype_to_domain", "package_content_hash"}
RISK_RULE_KEYS = {"rule_id", "owner_type", "field_path", "exact_raw_token", "risk_type_code", "risk_type_code_content_hash"}
RISK_PACKAGE_KEYS = {"package_id", "package_version", "package_state", "matching_policy", "rules", "package_content_hash"}
SEVERITY_RULE_KEYS = {"rule_id", "owner_type", "field_path", "exact_raw_token", "severity"}
SEVERITY_PACKAGE_KEYS = {"package_id", "package_version", "package_state", "matching_policy", "flag_policy", "rules", "package_content_hash"}
LEXICON_ITEM_KEYS = {"risk_type_code", "risk_type_code_content_hash", "label"}
LEXICON_KEYS = {"package_id", "package_version", "package_state", "locale", "matching_policy", "taxonomy_package_id", "taxonomy_package_version", "items", "package_content_hash"}
EVENT_INPUT_KEYS = {"use_context", "identity_join", "evidence", "package", "receipt"}
RISK_INPUT_KEYS = {"use_context", "identity_join", "taxonomy_evidence", "severity_evidence", "flag_evidence", "taxonomy_package", "taxonomy_receipt", "severity_package", "severity_receipt", "lexicon", "lexicon_receipt"}
EVENT_AUTHORITY_KEYS = {"authority_ref", "identity_join", "evidence_refs", "package_ref", "package_content_hash", "receipt_ref", "receipt_content_hash", "subtype", "domain", "authority_content_hash"}
RISK_AUTHORITY_KEYS = {"authority_ref", "identity_join", "taxonomy_evidence_ref", "severity_evidence_refs", "flag_evidence_ref", "risk_type_code", "risk_type_code_content_hash", "risk_type_zh", "severity", "taxonomy_package_ref", "taxonomy_package_content_hash", "taxonomy_receipt_ref", "taxonomy_receipt_content_hash", "severity_package_ref", "severity_package_content_hash", "severity_receipt_ref", "severity_receipt_content_hash", "lexicon_package_ref", "lexicon_package_content_hash", "lexicon_receipt_ref", "lexicon_receipt_content_hash", "authority_content_hash"}
GOVERNANCE_INPUT_KEYS = {"parent_pin_status", "target_path", "authority_source_kind", "transport_text", "s4_payload"}
MECHANICAL_RESEAL_KEYS = {"json_pointer", "hash_field", "bind_package_pointer"}
MUTATION_KEYS = {"target", "json_pointer", "operation", "value", "mechanical_reseal"}
CHALLENGE_CASE_KEYS = {"case_id", "evaluation_kind", "baseline_ref", "mutation", "expected_output", "expected_typed_error", "forbidden_output", "non_llm_oracle", "note"}

OBJECT_KEYS = {
    "SourceRevisionContentPair": SOURCE_PAIR_KEYS,
    "SemanticIdentityJoin": IDENTITY_KEYS,
    "TypedSemanticSourceRecord": SOURCE_RECORD_KEYS,
    "SyntheticTypedSourceRecordRegistry": SOURCE_REGISTRY_KEYS,
    "SyntheticAcceptedPolicyRecord": ACCEPTED_RECORD_KEYS,
    "SyntheticPolicyAcceptanceRegistry": ACCEPTANCE_REGISTRY_KEYS,
    "SemanticPolicyAcceptanceReceipt": RECEIPT_KEYS,
    "RawSemanticTokenEvidence": TOKEN_EVIDENCE_KEYS,
    "RawSemanticFlagEvidence": FLAG_EVIDENCE_KEYS,
    "ExactRuleComponent": EXACT_COMPONENT_KEYS,
    "SubtypeToDomainRelation": set(SUBTYPE_TO_DOMAIN),
    "ExactEventTokenRule": EVENT_RULE_KEYS,
    "CompoundEventClassificationRule": COMPOUND_RULE_KEYS,
    "EventClassificationRulePackage": EVENT_PACKAGE_KEYS,
    "RiskTaxonomyRule": RISK_RULE_KEYS,
    "RiskTaxonomyPackage": RISK_PACKAGE_KEYS,
    "SeverityPolicyRule": SEVERITY_RULE_KEYS,
    "SeverityPolicyPackage": SEVERITY_PACKAGE_KEYS,
    "RiskPresentationLexiconItem": LEXICON_ITEM_KEYS,
    "RiskPresentationLexicon": LEXICON_KEYS,
    "SemanticAuthorityError": {"code", "path", "authority_ref"},
    "EventClassificationAuthority": EVENT_AUTHORITY_KEYS,
    "RiskClassificationAuthority": RISK_AUTHORITY_KEYS,
    "EventClassificationSuccess": {"ok", "authority", "errors"},
    "EventClassificationFailure": {"ok", "authority", "errors"},
    "RiskClassificationSuccess": {"ok", "authority", "errors"},
    "RiskClassificationFailure": {"ok", "authority", "errors"},
    "EventClassificationInput": EVENT_INPUT_KEYS,
    "RiskClassificationInput": RISK_INPUT_KEYS,
    "RiskAuthorityValidationInput": {"source_input", "candidate_authority"},
    "GovernanceProbeInput": GOVERNANCE_INPUT_KEYS,
    "MechanicalResealAction": MECHANICAL_RESEAL_KEYS,
    "SemanticMutation": MUTATION_KEYS,
    "SemanticChallengeCase": CHALLENGE_CASE_KEYS,
}


def validate_schema(schema: dict[str, Any]) -> None:
    if schema.get("contract_id") != CONTRACT_ID:
        raise RuntimeError("schema contract id mismatch")
    if schema.get("enums", {}).get("matching_policy") != ["exact_utf8_v1"]:
        raise RuntimeError("matching policy is not closed")
    if schema.get("enums", {}).get("severity") != ["critical", "high", "medium", "low"]:
        raise RuntimeError("severity enum is not exact")
    if schema.get("exact_event_relation", {}).get("subtype_to_domain") != SUBTYPE_TO_DOMAIN:
        raise RuntimeError("schema 16-to-8 relation mismatch")
    if set(schema.get("objects", {})) != set(OBJECT_KEYS):
        raise RuntimeError("schema object set mismatch")
    for name, keys in OBJECT_KEYS.items():
        obj = schema["objects"][name]
        if obj.get("additional_properties") is not False:
            raise RuntimeError(f"{name} permits unknown fields")
        if set(obj.get("exact_keys", [])) != keys or set(obj.get("fields", {})) != keys:
            raise RuntimeError(f"{name} exact keys mismatch")
    if schema.get("s4_join_surface", {}).get("field_count") != 8:
        raise RuntimeError("S4 join is not exactly eight fields")
    if set(schema["s4_join_surface"]["exact_keys"]) != IDENTITY_KEYS:
        raise RuntimeError("S4 join keys mismatch")
    source = schema.get("real_flag_source", {})
    if source != {"source_type_path": "mm_r2.risk.RiskInstance", "field_path": "clinical_risk_flags", "allowed_flags": ["sae", "aesi"], "severity_effect": "none"}:
        raise RuntimeError("real flag path contract mismatch")
    if schema.get("typed_error_priority") != TYPED_ERROR_PRIORITY:
        raise RuntimeError("typed error priority is not exact")
    if len(schema.get("public_api_signatures", [])) != 3:
        raise RuntimeError("public API signatures are incomplete")
    if schema.get("future_bundle_integration", {}).get("unlock_state") != "not unlocked by this delta":
        raise RuntimeError("future bundle integration boundary mismatch")


def validate_identity(value: Any, path: str = "/identity_join") -> None:
    exact_keys(value, IDENTITY_KEYS, path)
    if any(not isinstance(item, str) or not item for item in value.values()):
        raise SemanticError("SEM_IDENTITY_JOIN_MISMATCH", path)


def class_fields(source_path: Path, class_name: str) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {item.target.id for item in node.body if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)}
    return set()


def validate_source_registry(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    exact_keys(registry, SOURCE_REGISTRY_KEYS, "/synthetic_typed_source_record_registry")
    if registry.get("registry_content_hash") != EXPECTED_SOURCE_REGISTRY_SHA256:
        raise RuntimeError("externally pinned source registry root mismatch")
    require_hash(registry, "registry_content_hash", "SEM_SOURCE_REGISTRY_PIN_MISMATCH", "/synthetic_typed_source_record_registry")
    if registry.get("authority_scope") != "synthetic_test_only" or registry.get("non_clinical") is not True:
        raise RuntimeError("source registry is not synthetic/non-clinical")
    result: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(registry.get("records", [])):
        path = f"/synthetic_typed_source_record_registry/records/{index}"
        exact_keys(record, SOURCE_RECORD_KEYS, path)
        validate_identity(record["identity_join"], path + "/identity_join")
        require_hash(record, "source_record_content_hash", "SEM_SOURCE_RECORD_HASH_MISMATCH", path)
        ref = record["source_record_ref"]
        if not isinstance(ref, str) or not ref or ref in result:
            raise RuntimeError("source record refs must be nonempty and unique")
        pairs = record["source_revision_content_pairs"]
        if not isinstance(pairs, list) or not pairs:
            raise RuntimeError("source record revisions are empty")
        for pair_index, pair in enumerate(pairs):
            exact_keys(pair, SOURCE_PAIR_KEYS, f"{path}/source_revision_content_pairs/{pair_index}")
            source_path = ROOT / pair["source_ref"]
            if not source_path.is_file() or raw_sha(source_path) != pair["source_content_hash"]:
                raise RuntimeError("typed source revision does not resolve")
        if not isinstance(record["source_locator_refs"], list) or not record["source_locator_refs"]:
            raise RuntimeError("source locators are empty")
        module_class = record["source_type_path"].rsplit(".", 1)
        if len(module_class) != 2:
            raise RuntimeError("invalid source type path")
        fields = class_fields(ROOT / pairs[0]["source_ref"], module_class[1])
        if record["owner_field_path"] not in fields or record["field_path"] not in fields:
            raise RuntimeError(f"typed source field does not exist: {record['source_type_path']}")
        result[ref] = record
    if not result:
        raise RuntimeError("source registry is empty")
    return result


def validate_acceptance_registry(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    exact_keys(registry, ACCEPTANCE_REGISTRY_KEYS, "/synthetic_policy_acceptance_registry")
    if registry.get("registry_content_hash") != EXPECTED_ACCEPTANCE_REGISTRY_SHA256:
        raise RuntimeError("externally pinned acceptance registry root mismatch")
    require_hash(registry, "registry_content_hash", "SEM_ACCEPTANCE_REGISTRY_PIN_MISMATCH", "/synthetic_policy_acceptance_registry")
    if registry.get("authority_scope") != "synthetic_test_only" or registry.get("non_clinical") is not True:
        raise RuntimeError("acceptance registry is not synthetic/non-clinical")
    records = registry.get("records")
    if not isinstance(records, list) or len(records) != 4:
        raise RuntimeError("acceptance registry must contain exactly four records")
    result: dict[str, dict[str, Any]] = {}
    kinds: set[str] = set()
    for index, record in enumerate(records):
        path = f"/synthetic_policy_acceptance_registry/records/{index}"
        exact_keys(record, ACCEPTED_RECORD_KEYS, path)
        require_hash(record, "accepted_record_content_hash", "SEM_ACCEPTED_RECORD_HASH_MISMATCH", path)
        if record.get("authority_scope") != "synthetic_test_only" or record.get("non_clinical") is not True or record.get("acceptance_basis") != "frozen_contract_fixture_only":
            raise RuntimeError("accepted record escaped synthetic boundary")
        ref, kind = record["accepted_record_ref"], record["package_kind"]
        expected_ref = f"synthetic-accepted:{kind}:{record['package_content_hash'][:20]}"
        if ref != expected_ref:
            raise RuntimeError("accepted record ref recipe mismatch")
        if ref in result or kind in kinds:
            raise RuntimeError("accepted record refs/kinds are not unique")
        result[ref] = record
        kinds.add(kind)
    if kinds != {"event_classification", "risk_taxonomy", "severity_policy", "risk_presentation_lexicon"}:
        raise RuntimeError("accepted record kinds incomplete")
    return result


def validate_token_evidence(value: Any, source_registry: dict[str, Any], source_records: dict[str, dict[str, Any]], identity: dict[str, Any], path: str) -> None:
    exact_keys(value, TOKEN_EVIDENCE_KEYS, path)
    require_hash(value, "evidence_content_hash", "SEM_EVIDENCE_HASH_MISMATCH", path)
    if value["source_registry_id"] != source_registry["registry_id"] or value["source_registry_content_hash"] != EXPECTED_SOURCE_REGISTRY_SHA256:
        raise SemanticError("SEM_SOURCE_REGISTRY_PIN_MISMATCH", path)
    record = source_records.get(value["source_record_ref"])
    if record is None:
        raise SemanticError("SEM_SOURCE_RECORD_UNRESOLVED", path)
    if value["source_record_content_hash"] != record["source_record_content_hash"] or value["source_content_identity"] != record["source_record_content_hash"]:
        raise SemanticError("SEM_SOURCE_RECORD_HASH_MISMATCH", path)
    if value["evidence_ref"] != "evidence:" + record["source_record_content_hash"][:24]:
        raise SemanticError("SEM_SOURCE_RECORD_HASH_MISMATCH", path)
    expected_owner_type = record["source_type_path"].rsplit(".", 1)[1]
    if value["owner_type"] != expected_owner_type or value["owner_ref"] != record["owner_ref"]:
        raise SemanticError("SEM_SOURCE_RECORD_OWNER_MISMATCH", path)
    if value["field_path"] != record["field_path"] or value["raw_token"] != record["field_value"]:
        raise SemanticError("SEM_SOURCE_RECORD_VALUE_MISMATCH", path)
    if value["snapshot_ref"] != record["identity_join"]["snapshot_ref"]:
        raise SemanticError("SEM_IDENTITY_JOIN_MISMATCH", path)
    if value["source_revision_content_pairs"] != record["source_revision_content_pairs"]:
        raise SemanticError("SEM_SOURCE_RECORD_REVISION_MISMATCH", path)
    if value["source_locator_refs"] != record["source_locator_refs"]:
        raise SemanticError("SEM_SOURCE_RECORD_LOCATOR_MISMATCH", path)
    if record["identity_join"] != identity:
        raise SemanticError("SEM_IDENTITY_JOIN_MISMATCH", path)


def validate_flag_evidence(value: Any, source_registry: dict[str, Any], source_records: dict[str, dict[str, Any]], identity: dict[str, Any], path: str) -> None:
    exact_keys(value, FLAG_EVIDENCE_KEYS, path)
    require_hash(value, "evidence_content_hash", "SEM_EVIDENCE_HASH_MISMATCH", path)
    if value["source_registry_id"] != source_registry["registry_id"] or value["source_registry_content_hash"] != EXPECTED_SOURCE_REGISTRY_SHA256:
        raise SemanticError("SEM_SOURCE_REGISTRY_PIN_MISMATCH", path)
    record = source_records.get(value["source_record_ref"])
    if record is None:
        raise SemanticError("SEM_SOURCE_RECORD_UNRESOLVED", path)
    if value["source_record_content_hash"] != record["source_record_content_hash"] or value["source_content_identity"] != record["source_record_content_hash"]:
        raise SemanticError("SEM_SOURCE_RECORD_HASH_MISMATCH", path)
    if value["evidence_ref"] != "flag-evidence:" + record["source_record_content_hash"][:24]:
        raise SemanticError("SEM_SOURCE_RECORD_HASH_MISMATCH", path)
    if value["owner_type"] != "RiskInstance" or value["owner_ref"] != record["owner_ref"]:
        raise SemanticError("SEM_SOURCE_RECORD_OWNER_MISMATCH", path)
    if value["field_path"] != "clinical_risk_flags" or value["field_path"] != record["field_path"] or value["flags"] != record["field_value"]:
        raise SemanticError("SEM_SOURCE_RECORD_VALUE_MISMATCH", path)
    if value["snapshot_ref"] != record["identity_join"]["snapshot_ref"]:
        raise SemanticError("SEM_IDENTITY_JOIN_MISMATCH", path)
    if value["source_revision_content_pairs"] != record["source_revision_content_pairs"]:
        raise SemanticError("SEM_SOURCE_RECORD_REVISION_MISMATCH", path)
    if value["source_locator_refs"] != record["source_locator_refs"]:
        raise SemanticError("SEM_SOURCE_RECORD_LOCATOR_MISMATCH", path)
    if set(value["flags"]) - {"sae", "aesi"} or record["identity_join"] != identity:
        raise SemanticError("SEM_IDENTITY_JOIN_MISMATCH", path)


def validate_common_package(value: dict[str, Any], keys: set[str], path: str) -> None:
    exact_keys(value, keys, path)
    if value.get("matching_policy") != "exact_utf8_v1":
        raise SemanticError("SEM_MATCHING_POLICY_FORBIDDEN", path + "/matching_policy")
    if value.get("package_state") != "synthetic_test_only":
        raise SemanticError("SEM_SYNTHETIC_CLINICAL_AUTHORITY_FORBIDDEN", path + "/package_state")
    if not isinstance(value.get("package_id"), str) or not value["package_id"] or SEMVER_RE.fullmatch(value.get("package_version", "")) is None:
        raise SemanticError("SEM_TYPE_MISMATCH", path)


def validate_event_package(package: dict[str, Any]) -> None:
    validate_common_package(package, EVENT_PACKAGE_KEYS, "/package")
    exact_rules, compound_rules = package["exact_rules"], package["compound_rules"]
    if not isinstance(exact_rules, list) or not isinstance(compound_rules, list):
        raise SemanticError("SEM_TYPE_MISMATCH", "/package")
    ids: list[str] = []
    raw_tokens: list[str] = []
    outputs: list[str] = []
    for index, rule in enumerate(exact_rules):
        exact_keys(rule, EVENT_RULE_KEYS, f"/package/exact_rules/{index}")
        if rule["owner_type"] != "TemporalEvent" or rule["field_path"] != "event_type" or not rule["exact_raw_token"]:
            raise SemanticError("SEM_EVENT_RELATION_INCOMPLETE", f"/package/exact_rules/{index}")
        if rule["rule_id"] != "event:" + rule["exact_raw_token"].lower():
            raise SemanticError("SEM_EVENT_RELATION_INCOMPLETE", f"/package/exact_rules/{index}/rule_id")
        ids.append(rule["rule_id"]); raw_tokens.append(rule["exact_raw_token"]); outputs.append(rule["output_subtype"])
    compound_by_phase: dict[str, str] = {}
    for index, rule in enumerate(compound_rules):
        exact_keys(rule, COMPOUND_RULE_KEYS, f"/package/compound_rules/{index}")
        if rule["owner_type"] != "TemporalEvent" or not isinstance(rule["components"], list) or len(rule["components"]) != 2:
            raise SemanticError("SEM_EVENT_RELATION_INCOMPLETE", f"/package/compound_rules/{index}")
        component_map: dict[str, str] = {}
        for component_index, component in enumerate(rule["components"]):
            exact_keys(component, EXACT_COMPONENT_KEYS, f"/package/compound_rules/{index}/components/{component_index}")
            component_map[component["field_path"]] = component["exact_raw_token"]
        if set(component_map) != {"event_type", "phase"} or component_map["event_type"] != "IP" or not component_map["phase"]:
            raise SemanticError("SEM_EVENT_RELATION_INCOMPLETE", f"/package/compound_rules/{index}")
        if rule["rule_id"] != "event:ip:" + component_map["phase"].lower():
            raise SemanticError("SEM_EVENT_RELATION_INCOMPLETE", f"/package/compound_rules/{index}/rule_id")
        if component_map["phase"] in compound_by_phase:
            raise SemanticError("SEM_RULE_DUPLICATE_OR_AMBIGUOUS", f"/package/compound_rules/{index}")
        compound_by_phase[component_map["phase"]] = rule["output_subtype"]
        ids.append(rule["rule_id"]); outputs.append(rule["output_subtype"])
    if len(ids) != len(set(ids)) or len(raw_tokens) != len(set(raw_tokens)):
        raise SemanticError("SEM_RULE_DUPLICATE_OR_AMBIGUOUS", "/package")
    if len(exact_rules) != 13 or len(compound_rules) != 3 or set(outputs) != set(SUBTYPE_TO_DOMAIN):
        raise SemanticError("SEM_EVENT_RELATION_INCOMPLETE", "/package")
    if set(raw_tokens) != set(EVENT_EXPECTED) or compound_by_phase != COMPOUND_EXPECTED:
        raise SemanticError("SEM_EVENT_RELATION_INCOMPLETE", "/package")
    if package["subtype_to_domain"] != SUBTYPE_TO_DOMAIN or set(package["subtype_to_domain"].values()) != DOMAINS:
        raise SemanticError("SEM_EVENT_RELATION_INCOMPLETE", "/package/subtype_to_domain")
    require_hash(package, "package_content_hash", "SEM_PACKAGE_HASH_MISMATCH", "/package")


def risk_code_hash(package: dict[str, Any], code: str) -> str:
    return sha({"package_id": package["package_id"], "package_version": package["package_version"], "risk_type_code": code})


def validate_risk_package(package: dict[str, Any]) -> None:
    validate_common_package(package, RISK_PACKAGE_KEYS, "/taxonomy_package")
    rules = package["rules"]
    if not isinstance(rules, list) or not rules:
        raise SemanticError("SEM_RISK_TAXONOMY_INCOMPLETE", "/taxonomy_package/rules")
    ids, raws, codes = [], [], []
    for index, rule in enumerate(rules):
        exact_keys(rule, RISK_RULE_KEYS, f"/taxonomy_package/rules/{index}")
        code = rule["risk_type_code"]
        if not isinstance(code, str) or RISK_CODE_RE.fullmatch(code) is None:
            raise SemanticError("SEM_RISK_TYPE_CODE_INVALID", f"/taxonomy_package/rules/{index}/risk_type_code")
        if rule["risk_type_code_content_hash"] != risk_code_hash(package, code):
            raise SemanticError("SEM_RISK_TYPE_CODE_HASH_MISMATCH", f"/taxonomy_package/rules/{index}")
        if rule["owner_type"] != "RiskCandidate" or rule["field_path"] != "risk_type":
            raise SemanticError("SEM_RISK_TAXONOMY_INCOMPLETE", f"/taxonomy_package/rules/{index}")
        if rule["rule_id"] != "risk:" + code:
            raise SemanticError("SEM_RISK_TAXONOMY_INCOMPLETE", f"/taxonomy_package/rules/{index}/rule_id")
        ids.append(rule["rule_id"]); raws.append(rule["exact_raw_token"]); codes.append(code)
    if len(ids) != len(set(ids)) or len(raws) != len(set(raws)) or len(codes) != len(set(codes)):
        raise SemanticError("SEM_RISK_TAXONOMY_AMBIGUOUS", "/taxonomy_package/rules")
    if dict(zip(raws, codes)) != RISK_EXPECTED:
        raise SemanticError("SEM_RISK_TAXONOMY_INCOMPLETE", "/taxonomy_package/rules")
    require_hash(package, "package_content_hash", "SEM_PACKAGE_HASH_MISMATCH", "/taxonomy_package")


def validate_severity_package(package: dict[str, Any]) -> None:
    validate_common_package(package, SEVERITY_PACKAGE_KEYS, "/severity_package")
    if package["flag_policy"] != "clinical_risk_flags_do_not_promote_severity":
        raise SemanticError("SEM_SAE_AESI_PROMOTION_FORBIDDEN", "/severity_package/flag_policy")
    rules = package["rules"]
    if not isinstance(rules, list):
        raise SemanticError("SEM_TYPE_MISMATCH", "/severity_package/rules")
    mapping: dict[str, str] = {}
    ids: set[str] = set()
    for index, rule in enumerate(rules):
        exact_keys(rule, SEVERITY_RULE_KEYS, f"/severity_package/rules/{index}")
        if rule["severity"] not in {"critical", "high", "medium", "low"}:
            raise SemanticError("SEM_SEVERITY_ENUM_INVALID", f"/severity_package/rules/{index}/severity")
        if rule["owner_type"] != "RiskCandidate" or rule["field_path"] != "severity" or rule["rule_id"] in ids or rule["exact_raw_token"] in mapping:
            raise SemanticError("SEM_RULE_DUPLICATE_OR_AMBIGUOUS", f"/severity_package/rules/{index}")
        if rule["rule_id"] != "severity:" + rule["exact_raw_token"]:
            raise SemanticError("SEM_SEVERITY_RULESET_INCOMPLETE", f"/severity_package/rules/{index}/rule_id")
        ids.add(rule["rule_id"]); mapping[rule["exact_raw_token"]] = rule["severity"]
    missing_legacy = any(mapping.get(raw) != output for raw, output in {"severe": "high", "moderate": "medium", "mild": "low"}.items())
    if missing_legacy:
        raise SemanticError("SEM_LEGACY_SEVERITY_RULE_MISSING", "/severity_package/rules")
    if set(mapping) != set(SEVERITY_EXPECTED):
        raise SemanticError("SEM_SEVERITY_RULESET_INCOMPLETE", "/severity_package/rules")
    if any(mapping[raw] != output for raw, output in SEVERITY_EXPECTED.items()):
        raise SemanticError("SEM_SEVERITY_PROMOTION_FORBIDDEN", "/severity_package/rules")
    require_hash(package, "package_content_hash", "SEM_PACKAGE_HASH_MISMATCH", "/severity_package")


def validate_lexicon(lexicon: dict[str, Any], taxonomy: dict[str, Any]) -> None:
    validate_common_package(lexicon, LEXICON_KEYS, "/lexicon")
    if lexicon["locale"] != "zh-CN":
        raise SemanticError("SEM_LEXICON_LOCALE_MISMATCH", "/lexicon/locale")
    if lexicon["taxonomy_package_id"] != taxonomy["package_id"] or lexicon["taxonomy_package_version"] != taxonomy["package_version"]:
        raise SemanticError("SEM_LEXICON_TAXONOMY_MISMATCH", "/lexicon")
    expected_codes = {rule["risk_type_code"]: rule["risk_type_code_content_hash"] for rule in taxonomy["rules"]}
    actual: dict[str, tuple[str, str]] = {}
    for index, item in enumerate(lexicon["items"]):
        exact_keys(item, LEXICON_ITEM_KEYS, f"/lexicon/items/{index}")
        if item["label"] in GENERIC_LABELS:
            raise SemanticError("SEM_GENERIC_RISK_LABEL_FORBIDDEN", f"/lexicon/items/{index}/label")
        if item["risk_type_code"] in actual:
            raise SemanticError("SEM_RISK_TAXONOMY_AMBIGUOUS", f"/lexicon/items/{index}")
        actual[item["risk_type_code"]] = (item["risk_type_code_content_hash"], item["label"])
    if set(actual) != set(expected_codes):
        raise SemanticError("SEM_LEXICON_CODE_MISSING", "/lexicon/items")
    for code, code_hash_value in expected_codes.items():
        if actual[code][0] != code_hash_value:
            raise SemanticError("SEM_RISK_TYPE_CODE_HASH_MISMATCH", "/lexicon/items")
        if actual[code][1] != LABEL_EXPECTED[code]:
            raise SemanticError("SEM_LEXICON_LABEL_MISMATCH", "/lexicon/items")
    require_hash(lexicon, "package_content_hash", "SEM_PACKAGE_HASH_MISMATCH", "/lexicon")


def validate_receipt(receipt: dict[str, Any], package: dict[str, Any], kind: str,
                     use_context: str, acceptance_registry: dict[str, Any], accepted_records: dict[str, dict[str, Any]], path: str) -> None:
    exact_keys(receipt, RECEIPT_KEYS, path)
    require_hash(receipt, "receipt_content_hash", "SEM_RECEIPT_HASH_MISMATCH", path)
    if use_context != "synthetic_test" or receipt["authority_scope"] != "synthetic_test_only":
        raise SemanticError("SEM_SYNTHETIC_CLINICAL_AUTHORITY_FORBIDDEN", path)
    if receipt["registry_id"] != acceptance_registry["registry_id"] or receipt["registry_content_hash"] != EXPECTED_ACCEPTANCE_REGISTRY_SHA256:
        raise SemanticError("SEM_ACCEPTANCE_REGISTRY_PIN_MISMATCH", path)
    record = accepted_records.get(receipt["accepted_record_ref"])
    if record is None:
        raise SemanticError("SEM_ACCEPTED_RECORD_UNRESOLVED", path + "/accepted_record_ref")
    if receipt["accepted_record_content_hash"] != record["accepted_record_content_hash"]:
        raise SemanticError("SEM_ACCEPTED_RECORD_HASH_MISMATCH", path)
    expected_receipt_id = "receipt:" + sha({"registry": acceptance_registry["registry_id"], "record": record["accepted_record_ref"]})[:24]
    if receipt["receipt_id"] != expected_receipt_id:
        raise SemanticError("SEM_RECEIPT_HASH_MISMATCH", path + "/receipt_id")
    if receipt["package_kind"] != kind or receipt["audience_contract_id"] != "contract.s4.1":
        raise SemanticError("SEM_RECEIPT_PACKAGE_KIND_MISMATCH", path)
    package_tuple = (package["package_id"], package["package_version"], package["package_content_hash"])
    receipt_tuple = (receipt["package_id"], receipt["package_version"], receipt["package_content_hash"])
    if receipt_tuple != package_tuple:
        raise SemanticError("SEM_RECEIPT_PACKAGE_MISMATCH", path)
    record_tuple = (record["package_id"], record["package_version"], record["package_content_hash"])
    if record["package_kind"] != kind or record_tuple != package_tuple:
        raise SemanticError("SEM_ACCEPTED_RECORD_PACKAGE_MISMATCH", path)


def event_authority(input_value: dict[str, Any], subtype: str) -> dict[str, Any]:
    package, receipt = input_value["package"], input_value["receipt"]
    body = {
        "authority_ref": "event-authority:" + sha({"evidence": [x["evidence_ref"] for x in input_value["evidence"]], "package": package["package_content_hash"]})[:24],
        "identity_join": copy.deepcopy(input_value["identity_join"]),
        "evidence_refs": [x["evidence_ref"] for x in input_value["evidence"]],
        "package_ref": package["package_id"], "package_content_hash": package["package_content_hash"],
        "receipt_ref": receipt["receipt_id"], "receipt_content_hash": receipt["receipt_content_hash"],
        "subtype": subtype, "domain": SUBTYPE_TO_DOMAIN[subtype],
    }
    body["authority_content_hash"] = sha(body)
    return body


def risk_authority(input_value: dict[str, Any], code: str, code_hash_value: str, label: str, severity: str) -> dict[str, Any]:
    taxonomy, lexicon = input_value["taxonomy_package"], input_value["lexicon"]
    body = {
        "authority_ref": "risk-authority:" + sha({"taxonomy": input_value["taxonomy_evidence"]["evidence_ref"], "severity": [x["evidence_ref"] for x in input_value["severity_evidence"]]})[:24],
        "identity_join": copy.deepcopy(input_value["identity_join"]),
        "taxonomy_evidence_ref": input_value["taxonomy_evidence"]["evidence_ref"],
        "severity_evidence_refs": [x["evidence_ref"] for x in input_value["severity_evidence"]],
        "flag_evidence_ref": input_value["flag_evidence"]["evidence_ref"] if input_value["flag_evidence"] else None,
        "risk_type_code": code, "risk_type_code_content_hash": code_hash_value,
        "risk_type_zh": label, "severity": severity,
        "taxonomy_package_ref": taxonomy["package_id"], "taxonomy_package_content_hash": taxonomy["package_content_hash"],
        "taxonomy_receipt_ref": input_value["taxonomy_receipt"]["receipt_id"], "taxonomy_receipt_content_hash": input_value["taxonomy_receipt"]["receipt_content_hash"],
        "severity_package_ref": input_value["severity_package"]["package_id"], "severity_package_content_hash": input_value["severity_package"]["package_content_hash"],
        "severity_receipt_ref": input_value["severity_receipt"]["receipt_id"], "severity_receipt_content_hash": input_value["severity_receipt"]["receipt_content_hash"],
        "lexicon_package_ref": lexicon["package_id"], "lexicon_package_content_hash": lexicon["package_content_hash"],
        "lexicon_receipt_ref": input_value["lexicon_receipt"]["receipt_id"], "lexicon_receipt_content_hash": input_value["lexicon_receipt"]["receipt_content_hash"],
    }
    body["authority_content_hash"] = sha(body)
    return body


def evaluate_event(input_value: Any, source_registry: dict[str, Any], source_records: dict[str, dict[str, Any]], acceptance_registry: dict[str, Any], accepted_records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    exact_keys(input_value, EVENT_INPUT_KEYS, "")
    validate_identity(input_value["identity_join"])
    if not isinstance(input_value["evidence"], list) or not input_value["evidence"]:
        raise SemanticError("SEM_EVENT_TOKEN_UNMAPPED", "/evidence")
    for index, item in enumerate(input_value["evidence"]):
        validate_token_evidence(item, source_registry, source_records, input_value["identity_join"], f"/evidence/{index}")
    owners = {(x["owner_type"], x["owner_ref"]) for x in input_value["evidence"]}
    if len(owners) != 1:
        raise SemanticError("SEM_SOURCE_RECORD_OWNER_MISMATCH", "/evidence")
    validate_event_package(input_value["package"])
    validate_receipt(input_value["receipt"], input_value["package"], "event_classification", input_value["use_context"], acceptance_registry, accepted_records, "/receipt")
    token_map = {x["field_path"]: x["raw_token"] for x in input_value["evidence"]}
    matches: list[str] = []
    for rule in input_value["package"]["exact_rules"]:
        if token_map.get(rule["field_path"]) == rule["exact_raw_token"]:
            matches.append(rule["output_subtype"])
    for rule in input_value["package"]["compound_rules"]:
        if all(token_map.get(component["field_path"]) == component["exact_raw_token"] for component in rule["components"]):
            matches.append(rule["output_subtype"])
    if not matches:
        raise SemanticError("SEM_EVENT_TOKEN_UNMAPPED", "/evidence")
    if len(matches) != 1 or not matches[0]:
        raise SemanticError("SEM_RULE_DUPLICATE_OR_AMBIGUOUS", "/package")
    return event_authority(input_value, matches[0])


def evaluate_risk(input_value: Any, source_registry: dict[str, Any], source_records: dict[str, dict[str, Any]], acceptance_registry: dict[str, Any], accepted_records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    exact_keys(input_value, RISK_INPUT_KEYS, "")
    validate_identity(input_value["identity_join"])
    validate_token_evidence(input_value["taxonomy_evidence"], source_registry, source_records, input_value["identity_join"], "/taxonomy_evidence")
    if not isinstance(input_value["severity_evidence"], list) or not input_value["severity_evidence"]:
        raise SemanticError("SEM_SEVERITY_TOKEN_UNMAPPED", "/severity_evidence")
    for index, item in enumerate(input_value["severity_evidence"]):
        validate_token_evidence(item, source_registry, source_records, input_value["identity_join"], f"/severity_evidence/{index}")
    if input_value["flag_evidence"] is not None:
        validate_flag_evidence(input_value["flag_evidence"], source_registry, source_records, input_value["identity_join"], "/flag_evidence")
    validate_risk_package(input_value["taxonomy_package"])
    validate_severity_package(input_value["severity_package"])
    validate_lexicon(input_value["lexicon"], input_value["taxonomy_package"])
    for package_key, receipt_key, kind in (
        ("taxonomy_package", "taxonomy_receipt", "risk_taxonomy"),
        ("severity_package", "severity_receipt", "severity_policy"),
        ("lexicon", "lexicon_receipt", "risk_presentation_lexicon"),
    ):
        validate_receipt(input_value[receipt_key], input_value[package_key], kind, input_value["use_context"], acceptance_registry, accepted_records, "/" + receipt_key)
    risk_matches = [rule for rule in input_value["taxonomy_package"]["rules"] if rule["exact_raw_token"] == input_value["taxonomy_evidence"]["raw_token"]]
    if not risk_matches:
        raise SemanticError("SEM_RISK_TOKEN_UNMAPPED", "/taxonomy_evidence")
    if len(risk_matches) != 1:
        raise SemanticError("SEM_RISK_TAXONOMY_AMBIGUOUS", "/taxonomy_package/rules")
    severity_values: list[str] = []
    for evidence in input_value["severity_evidence"]:
        matches = [rule["severity"] for rule in input_value["severity_package"]["rules"] if rule["exact_raw_token"] == evidence["raw_token"]]
        if not matches:
            raise SemanticError("SEM_SEVERITY_TOKEN_UNMAPPED", "/severity_evidence")
        if len(matches) != 1:
            raise SemanticError("SEM_RULE_DUPLICATE_OR_AMBIGUOUS", "/severity_package/rules")
        severity_values.append(matches[0])
    if len(set(severity_values)) != 1:
        raise SemanticError("SEM_SEVERITY_CONFLICT", "/severity_evidence")
    risk_rule = risk_matches[0]
    lexicon_matches = [item for item in input_value["lexicon"]["items"] if item["risk_type_code"] == risk_rule["risk_type_code"]]
    if len(lexicon_matches) != 1:
        raise SemanticError("SEM_LEXICON_CODE_MISSING", "/lexicon/items")
    item = lexicon_matches[0]
    return risk_authority(input_value, risk_rule["risk_type_code"], risk_rule["risk_type_code_content_hash"], item["label"], severity_values[0])


def evaluate_governance(input_value: Any) -> None:
    exact_keys(input_value, GOVERNANCE_INPUT_KEYS, "")
    if input_value["parent_pin_status"] != "exact":
        raise SemanticError("SEM_PARENT_PIN_DRIFT", "/parent_pin_status")
    if input_value["target_path"] not in EXACT_PATHS:
        raise SemanticError("SEM_ORIGINAL_PATH_OVERWRITE_FORBIDDEN", "/target_path")
    if input_value["authority_source_kind"] != "frozen_registry":
        raise SemanticError("SEM_EXAMPLE_AS_AUTHORITY_FORBIDDEN", "/authority_source_kind")
    if "ACCEPT_R5_S5_PUBLIC_AUTHORITY_SEMANTIC_DELTA_V0_1" in input_value["transport_text"]:
        raise SemanticError("SEM_ACCEPTANCE_TOKEN_LEAKAGE", "/transport_text")
    try:
        validate_identity(input_value["s4_payload"], "/s4_payload")
    except SemanticError as exc:
        if exc.code == "SEM_SCHEMA_EXACT_KEYS":
            raise SemanticError("SEM_S4_VALUE_TRANSFER_FORBIDDEN", "/s4_payload") from None
        raise


def pointer_parent(root: Any, pointer: str) -> tuple[Any, str]:
    if pointer == "":
        return None, ""
    parts = pointer.lstrip("/").split("/")
    parts = [item.replace("~1", "/").replace("~0", "~") for item in parts]
    current = root
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current, parts[-1]


def pointer_get(root: Any, pointer: str) -> Any:
    if pointer == "":
        return root
    parent, key = pointer_parent(root, pointer)
    return parent[int(key)] if isinstance(parent, list) else parent[key]


def pointer_set(root: Any, pointer: str, operation: str, value: Any = None) -> None:
    parent, key = pointer_parent(root, pointer)
    if parent is None:
        raise RuntimeError("root mutation is not supported")
    if isinstance(parent, list):
        index = int(key)
        if operation == "remove":
            parent.pop(index)
        elif operation == "add" and index == len(parent):
            parent.append(copy.deepcopy(value))
        elif operation in {"add", "replace"}:
            parent[index] = copy.deepcopy(value)
        else:
            raise RuntimeError("unknown mutation operation")
    elif operation == "remove":
        del parent[key]
    elif operation in {"add", "replace"}:
        parent[key] = copy.deepcopy(value)
    else:
        raise RuntimeError("unknown mutation operation")


def apply_case(baseline: Any, mutation: dict[str, Any]) -> Any:
    result = copy.deepcopy(baseline)
    target = mutation["target"]
    target_value = result if target == "input" else result[target]
    pointer_set(target_value, mutation["json_pointer"], mutation["operation"], mutation.get("value"))
    for action in mutation.get("mechanical_reseal", []):
        exact_keys(action, MECHANICAL_RESEAL_KEYS, "/mutation/mechanical_reseal")
        object_value = pointer_get(target_value, action["json_pointer"])
        bind_pointer = action.get("bind_package_pointer")
        if bind_pointer:
            package = pointer_get(target_value, bind_pointer)
            object_value["package_id"] = package["package_id"]
            object_value["package_version"] = package["package_version"]
            object_value["package_content_hash"] = package["package_content_hash"]
        hash_field = action["hash_field"]
        object_value[hash_field] = object_hash(object_value, hash_field)
    return result


def run_challenges(challenges: dict[str, Any], source_registry: dict[str, Any], source_records: dict[str, dict[str, Any]], acceptance_registry: dict[str, Any], accepted_records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    baselines, cases = challenges["baselines"], challenges["cases"]
    outcomes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for case in cases:
        if set(case) != CHALLENGE_CASE_KEYS:
            raise RuntimeError("challenge case schema mismatch")
        case_identifier = case["case_id"]
        if case_identifier in seen:
            raise RuntimeError("duplicate challenge id")
        seen.add(case_identifier)
        mutation = case["mutation"]
        if set(mutation) != MUTATION_KEYS:
            raise RuntimeError("mutation schema mismatch")
        if case["expected_typed_error"] is None:
            if case["forbidden_output"] is not None or case["non_llm_oracle"] != "exact_authority_equality":
                raise RuntimeError("positive non-LLM oracle contract mismatch")
        elif case["forbidden_output"] != "any_semantic_authority" or case["non_llm_oracle"] != "exact_typed_error_and_no_authority":
            raise RuntimeError("negative non-LLM oracle contract mismatch")
        baseline = baselines[case["baseline_ref"]]
        candidate = apply_case(baseline, mutation)
        if candidate == baseline:
            raise RuntimeError(f"no-op mutation: {case_identifier}")
        actual_output = None
        actual_error = None
        try:
            if case["evaluation_kind"] == "event":
                actual_output = evaluate_event(candidate, source_registry, source_records, acceptance_registry, accepted_records)
            elif case["evaluation_kind"] == "risk":
                actual_output = evaluate_risk(candidate, source_registry, source_records, acceptance_registry, accepted_records)
            elif case["evaluation_kind"] == "risk_authority":
                expected = evaluate_risk(candidate["source_input"], source_registry, source_records, acceptance_registry, accepted_records)
                authority = candidate["candidate_authority"]
                exact_keys(authority, RISK_AUTHORITY_KEYS, "/candidate_authority")
                require_hash(authority, "authority_content_hash", "SEM_AUTHORITY_HASH_MISMATCH", "/candidate_authority")
                if authority["risk_type_zh"] != expected["risk_type_zh"]:
                    raise SemanticError("SEM_LEXICON_LABEL_MISMATCH", "/candidate_authority/risk_type_zh")
                if authority != expected:
                    raise SemanticError("SEM_AUTHORITY_MISMATCH", "/candidate_authority")
                actual_output = authority
            elif case["evaluation_kind"] == "governance":
                actual_output = evaluate_governance(candidate)
            else:
                raise RuntimeError("unknown evaluation kind")
        except SemanticError as exc:
            actual_error = exc.code
        if actual_error != case["expected_typed_error"] or actual_output != case["expected_output"]:
            raise RuntimeError(f"challenge mismatch {case_identifier}: error={actual_error!r} output_match={actual_output == case['expected_output']}")
        outcomes.append({"case_id": case_identifier, "outcome": "success" if actual_error is None else actual_error})
    if len(cases) < 45:
        raise RuntimeError("challenge registry is not broad enough")
    required = {"SEM-AUTH-001", "SEM-AUTH-002", "SEM-AUTH-003", "SEM-AUTH-004", "SEM-AUTH-005", "SEM-AUTH-006", "SEM-AUTH-007", "SEM-AUTH-008", "SEM-EVT-002", "SEM-EVT-015", "SEM-RISK-POS-004", "SEM-GOV-001", "SEM-GOV-002", "SEM-GOV-003", "SEM-GOV-004", "SEM-GOV-005"}
    if not required.issubset(seen):
        raise RuntimeError("decisive probes missing")
    return {"count": len(outcomes), "outcomes": outcomes}


def validate_parent_and_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("contract_id") != CONTRACT_ID or manifest.get("exact_delta_paths") != list(EXACT_PATHS):
        raise RuntimeError("manifest scope mismatch")
    if manifest.get("rewrites_parent") is not False or manifest.get("invalidates_parent_acceptance") is not False:
        raise RuntimeError("parent rewrite declared")
    if manifest.get("acceptance_boundary") != {"worker_may_accept": False, "clinical_authority_created": False, "independent_verifier_required": True}:
        raise RuntimeError("acceptance boundary mismatch")
    if manifest.get("registry_pins_immutable_under_candidate_reseal") is not True:
        raise RuntimeError("registry pin immutability missing")
    require_hash(manifest, "manifest_content_hash", "SEM_MANIFEST_HASH_MISMATCH", "/manifest")
    parent_path = ROOT / PARENT_MANIFEST
    if raw_sha(parent_path) != PARENT_MANIFEST_SHA256:
        raise RuntimeError("parent manifest drift")
    parent = json.loads(parent_path.read_text(encoding="utf-8"))
    expected_pins = dict(parent["protected_accepted_pins"]["protected_path_sha256"])
    expected_pins.update(parent["artifact_raw_sha256"])
    expected_pins[PARENT_MANIFEST] = PARENT_MANIFEST_SHA256
    expected_pins[PARENT_ACCEPTANCE] = PARENT_ACCEPTANCE_SHA256
    expected_pins = dict(sorted(expected_pins.items()))
    if manifest.get("protected_parent_pins") != expected_pins:
        raise RuntimeError("protected parent pin set mismatch")
    for relative, expected in expected_pins.items():
        if not (ROOT / relative).is_file() or raw_sha(ROOT / relative) != expected:
            raise RuntimeError(f"protected parent drift: {relative}")
    negative = manifest.get("rejected_implementation_contract_snapshot_negative_evidence_only", {})
    if negative.get("authority") is not False or negative.get("pins") != NEGATIVE_PINS:
        raise RuntimeError("negative-only snapshot boundary mismatch")
    for relative, expected in NEGATIVE_PINS.items():
        if not (ROOT / relative).is_file() or raw_sha(ROOT / relative) != expected:
            raise RuntimeError(f"negative snapshot drift: {relative}")
    artifact_pins = manifest.get("artifact_raw_sha256", {})
    if set(artifact_pins) != set(EXACT_PATHS) - {MANIFEST_PATH}:
        raise RuntimeError("delta artifact pin set mismatch")
    for relative, expected in artifact_pins.items():
        if raw_sha(ROOT / relative) != expected:
            raise RuntimeError(f"delta artifact drift: {relative}")


def inventory_aggregate() -> tuple[int, str]:
    paths: list[str] = []
    for root_name in ("deploy", "frontend", "packages", "runtime", "services"):
        base = ROOT / root_name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and ("medical-writing" in path.as_posix().lower() or "medical_writing" in path.as_posix().lower()):
                paths.append(path.relative_to(ROOT).as_posix())
    paths.sort(key=lambda item: item.encode("utf-8"))
    payload = b"".join(item.encode("utf-8") + b"\0" + raw_sha(ROOT / item).encode("ascii") + b"\n" for item in paths)
    return len(paths), hashlib.sha256(payload).hexdigest()


def validate_scope_and_environment(manifest: dict[str, Any]) -> None:
    count, aggregate = inventory_aggregate()
    pins = manifest.get("protected_aggregate_pins", {})
    if (count, aggregate) != (542, "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca"):
        raise RuntimeError("542-file protected inventory drift")
    if pins.get("file_count") != count or pins.get("aggregate_sha256") != aggregate:
        raise RuntimeError("manifest 542 aggregate mismatch")
    if set(manifest["no_producer_surface"]["allowed_paths"]) != set(EXACT_PATHS):
        raise RuntimeError("allowlist mismatch")
    for relative in EXACT_PATHS:
        if re.search(r"(^|/)(src|runtime|frontend|services|packages|deploy|poc)/", relative):
            raise RuntimeError("producer path entered delta allowlist")
    for script_path in (GENERATOR_PATH, VERIFIER_PATH):
        tree = ast.parse((ROOT / script_path).read_text(encoding="utf-8"))
        if any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
            raise RuntimeError("Python assert found")
        if script_path == VERIFIER_PATH:
            imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
            imports.update(node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom))
            if any("generate_medical_monitoring_r5_s5_public_authority_semantic_delta" in item for item in imports):
                raise RuntimeError("verifier imports generator")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(0.2)
        if client.connect_ex(("127.0.0.1", 8911)) == 0:
            raise RuntimeError("port 8911 is listening")


def stable_generation() -> dict[str, str]:
    command = [sys.executable, str(ROOT / GENERATOR_PATH), "--check"]
    first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if first.returncode != 0:
        raise RuntimeError("generator --check failed: " + (first.stdout + first.stderr)[-1000:])
    before = {path: raw_sha(ROOT / path) for path in EXACT_PATHS}
    second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if second.returncode != 0:
        raise RuntimeError("second generator --check failed")
    after = {path: raw_sha(ROOT / path) for path in EXACT_PATHS}
    if before != after:
        raise RuntimeError("delta SHA set is unstable")
    return before


def verify_once(run_ruff: bool = False) -> dict[str, Any]:
    schema = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
    challenges = json.loads((ROOT / CHALLENGE_PATH).read_text(encoding="utf-8"))
    source_matrix = json.loads((ROOT / SOURCE_MATRIX_PATH).read_text(encoding="utf-8"))
    validate_schema(schema)
    validate_parent_and_manifest(manifest)
    validate_scope_and_environment(manifest)
    if source_matrix.get("synthetic_source_registry_pin", {}).get("registry_content_hash") != EXPECTED_SOURCE_REGISTRY_SHA256:
        raise RuntimeError("source matrix registry pin mismatch")
    source_registry = manifest["synthetic_typed_source_record_registry"]
    acceptance_registry = manifest["synthetic_policy_acceptance_registry"]
    source_records = validate_source_registry(source_registry)
    accepted_records = validate_acceptance_registry(acceptance_registry)
    result = run_challenges(challenges, source_registry, source_records, acceptance_registry, accepted_records)
    if manifest.get("challenge_count") != result["count"]:
        raise RuntimeError("manifest challenge count mismatch")
    final_sha = stable_generation()
    if run_ruff:
        lint_env = dict(os.environ)
        lint_env.setdefault("UV_CACHE_DIR", "/tmp/r5_s5_semantic_delta_uv_cache")
        lint = subprocess.run([
            "/Users/smkzw/.local/bin/uvx", "--from", "ruff", "ruff", "check", "--no-cache",
            str(ROOT / GENERATOR_PATH), str(ROOT / VERIFIER_PATH),
        ], cwd=ROOT, env=lint_env, text=True, capture_output=True, check=False)
        if lint.returncode != 0:
            raise RuntimeError("Ruff failed: " + (lint.stdout + lint.stderr)[-2000:])
    decisive_ids = {f"SEM-AUTH-{index:03d}" for index in range(1, 9)}
    decisive = [item for item in result["outcomes"] if item["case_id"] in decisive_ids]
    return {"status": "VERIFIED_FOR_INDEPENDENT_ACCEPTANCE_NOT_ACCEPTED", "challenge_count": result["count"], "decisive_probe_outcomes": decisive, "final_sha256": final_sha, "optimization_level": sys.flags.optimize, "pythonhashseed": os.environ.get("PYTHONHASHSEED", "unset")}


def cross_seed_and_optimized() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for optimization_level, seed in ((0, "0"), (0, "271828"), (2, "0"), (2, "271828")):
        command = [sys.executable, "-B", str(ROOT / VERIFIER_PATH), "--probe-only", "--json"]
        env = dict(os.environ)
        env.pop("PYTHONOPTIMIZE", None)
        if optimization_level == 2:
            env["PYTHONOPTIMIZE"] = "2"
        env["PYTHONHASHSEED"] = seed
        run = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
        if run.returncode != 0:
            raise RuntimeError(f"cross-seed/O2 verifier failed optimization_level={optimization_level} seed={seed}: " + (run.stdout + run.stderr)[-2000:])
        probe_result = json.loads(run.stdout)
        if probe_result.get("optimization_level") != optimization_level:
            raise RuntimeError("cross-seed verifier optimization level mismatch")
        results.append(probe_result)
    sha_sets = {canonical_bytes(item["final_sha256"]) for item in results}
    if len(sha_sets) != 1:
        raise RuntimeError("cross-seed/O2 final SHA mismatch")
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = verify_once(run_ruff=not args.probe_only)
    if not args.probe_only:
        result["cross_seed_o2"] = [{"optimization_level": item["optimization_level"], "pythonhashseed": item["pythonhashseed"], "challenge_count": item["challenge_count"]} for item in cross_seed_and_optimized()]
    output = json.dumps(result, ensure_ascii=False, indent=None if args.json else 2, sort_keys=True)
    print(output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, SemanticError, KeyError, TypeError, ValueError) as exc:
        print(f"VERIFY_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
