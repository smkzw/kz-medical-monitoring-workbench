"""Generate the append-only R5-S5 semantic-authority delta.

The embedded registries are deliberately synthetic_test_only.  A candidate
receipt is only a projection of an independently pinned accepted record; it is
never an acceptance act.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1"
CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-semantic-delta-v0.1"
SCHEMA_VERSION = "2026-08-20.2"

CONTEXT_PATH = "context/medical_monitoring_r5_s5_semantic_authority_delta_20260820_context.md"
REVIEW_PATH = "reviews/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1_20260820.md"
SCHEMA_PATH = f"{ARTIFACT_DIR.relative_to(ROOT)}/schema.json"
SOURCE_MATRIX_PATH = f"{ARTIFACT_DIR.relative_to(ROOT)}/source_matrix_delta.json"
CHALLENGE_PATH = f"{ARTIFACT_DIR.relative_to(ROOT)}/challenge_registry.json"
MANIFEST_PATH = f"{ARTIFACT_DIR.relative_to(ROOT)}/manifest.json"
GENERATOR_PATH = "tools/generate_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py"
VERIFIER_PATH = "tools/verify_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py"
EXACT_DELTA_PATHS = (
    CONTEXT_PATH, REVIEW_PATH, SCHEMA_PATH, SOURCE_MATRIX_PATH, CHALLENGE_PATH,
    MANIFEST_PATH, GENERATOR_PATH, VERIFIER_PATH,
)

PARENT_MANIFEST_PATH = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json"
PARENT_MANIFEST_SHA256 = "92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270"
PARENT_ACCEPTANCE_PATH = "context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md"
PARENT_ACCEPTANCE_SHA256 = "23fed5b186057a79cd0ec43a7718e43934ebafdc8f62fd251077d4fb6891639d"

NEGATIVE_SNAPSHOT_PINS = {
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

DOMAINS = ("ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure", "symptom_efficacy", "protocol_compliance")
SUBTYPE_TO_DOMAIN = {
    "ae": "ae", "mh": "mh", "concomitant_medication": "cm",
    "ip_dose": "ip", "ip_pause": "ip", "ip_resume": "ip",
    "lab": "lab_exam", "exam": "lab_exam",
    "hospitalization": "hospital_procedure", "procedure": "hospital_procedure",
    "symptom": "symptom_efficacy", "efficacy": "symptom_efficacy",
    "scale": "symptom_efficacy", "outcome": "symptom_efficacy",
    "trend": "symptom_efficacy", "protocol_deviation": "protocol_compliance",
}
EVENT_TOKEN_RULES = (
    ("AE", "ae"), ("MH", "mh"), ("CM", "concomitant_medication"),
    ("LAB", "lab"), ("EXAM", "exam"), ("HOSPITALIZATION", "hospitalization"),
    ("PROCEDURE", "procedure"), ("SYMPTOM", "symptom"),
    ("EFFICACY", "efficacy"), ("SCALE", "scale"), ("OUTCOME", "outcome"),
    ("TREND", "trend"), ("PROTOCOL_DEVIATION", "protocol_deviation"),
)
COMPOUND_RULES = (("DOSE", "ip_dose"), ("PAUSE", "ip_pause"), ("RESUME", "ip_resume"))
RISK_RULES = (
    ("RISK_TYPE_POTENTIAL_UNREPORTED_AE", "potential_unreported_ae", "潜在未报告AE"),
    ("RISK_TYPE_POTENTIAL_UNREPORTED_MH", "potential_unreported_mh", "潜在未报告既往史"),
    ("RISK_TYPE_CONCOMITANT_MEDICATION", "concomitant_medication_risk", "合并用药风险"),
    ("RISK_TYPE_PROTOCOL_COMPLIANCE", "protocol_compliance_risk", "方案依从性风险"),
)
SEVERITY_RULES = (
    ("critical", "critical"), ("high", "high"), ("medium", "medium"),
    ("low", "low"), ("severe", "high"), ("moderate", "medium"), ("mild", "low"),
)
SEVERITIES = ("critical", "high", "medium", "low")
IDENTITY = {
    "project_ref": "project-sem-001", "run_ref": "run-sem-001",
    "snapshot_ref": "snapshot-sem-001", "cutoff_ref": "cutoff-sem-001",
    "site_ref": "site-sem-001", "subject_ref": "subject-sem-001",
    "risk_ref": "risk-sem-001", "spine_ref": "spine-sem-001",
}
SOURCE_REGISTRY_ID = "registry:r5-s5:synthetic-typed-source-records:20260820"
ACCEPTANCE_REGISTRY_ID = "registry:r5-s5:synthetic-policy-acceptance:20260820"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else canonical_bytes(value)).hexdigest()


def raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal(value: dict[str, Any], hash_field: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(hash_field, None)
    result[hash_field] = sha(result)
    return result


def fld(type_name: str, cardinality: str = "one", nullable: bool = False) -> dict[str, Any]:
    return {"type": type_name, "cardinality": cardinality, "nullable": nullable}


def exact_object(fields: dict[str, Any]) -> dict[str, Any]:
    return {"additional_properties": False, "exact_keys": sorted(fields), "fields": fields}


def source_pair(source_path: str) -> dict[str, str]:
    return {"source_ref": source_path, "source_content_hash": raw_sha(ROOT / source_path)}


def typed_record(ref: str, source_type: str, owner_field: str, owner_ref: str,
                 field_path: str, value: Any, source_path: str, locator: str) -> dict[str, Any]:
    record = {
        "source_record_ref": ref,
        "source_type_path": source_type,
        "owner_field_path": owner_field,
        "owner_ref": owner_ref,
        "field_path": field_path,
        "field_value": value,
        "identity_join": copy.deepcopy(IDENTITY),
        "source_revision_content_pairs": [source_pair(source_path)],
        "source_locator_refs": [locator],
    }
    return seal(record, "source_record_content_hash")


def build_source_registry() -> dict[str, Any]:
    r1 = "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py"
    r2 = "poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py"
    records: list[dict[str, Any]] = []
    event_values = [token for token, _ in EVENT_TOKEN_RULES] + ["IP", "AE ", "ae", "UNKNOWN_EVENT"]
    for token in event_values:
        if token == "ae":
            slug = "ae-lower"
        elif token == "AE ":
            slug = "ae-space"
        else:
            slug = token.lower().replace("_", "-")
        records.append(typed_record(
            f"src:event-type:{slug}", "mm_r1.domain.TemporalEvent", "event_id",
            f"event-{slug}", "event_type", token, r1, "TemporalEvent.event_type",
        ))
    for phase, _ in COMPOUND_RULES:
        records.append(typed_record(
            f"src:event-phase:{phase.lower()}", "mm_r1.domain.TemporalEvent", "event_id",
            "event-ip", "phase", phase, r1, "TemporalEvent.phase",
        ))
    for raw, _, _ in RISK_RULES:
        slug = raw.lower().replace("_", "-")
        records.append(typed_record(
            f"src:risk-type:{slug}", "mm_r1.domain.RiskCandidate", "candidate_id",
            "risk-sem-001", "risk_type", raw, r1, "RiskCandidate.risk_type",
        ))
    records.append(typed_record(
        "src:risk-type:unknown", "mm_r1.domain.RiskCandidate", "candidate_id",
        "risk-sem-001", "risk_type", "RISK_TYPE_UNKNOWN", r1, "RiskCandidate.risk_type",
    ))
    for token in [item[0] for item in SEVERITY_RULES] + ["catastrophic", "HIGH"]:
        records.append(typed_record(
            f"src:severity:{token}", "mm_r1.domain.RiskCandidate", "candidate_id",
            "risk-sem-001", "severity", token, r1, "RiskCandidate.severity",
        ))
    records.append(typed_record(
        "src:clinical-flags:sae-aesi", "mm_r2.risk.RiskInstance", "risk_instance_id",
        "risk-sem-001", "clinical_risk_flags", ["sae", "aesi"], r2,
        "RiskInstance.clinical_risk_flags",
    ))
    records.sort(key=lambda x: x["source_record_ref"])
    registry = {
        "registry_id": SOURCE_REGISTRY_ID,
        "authority_scope": "synthetic_test_only",
        "non_clinical": True,
        "records": records,
    }
    return seal(registry, "registry_content_hash")


def code_hash(package_id: str, package_version: str, code: str) -> str:
    return sha({"package_id": package_id, "package_version": package_version, "risk_type_code": code})


def build_packages() -> dict[str, dict[str, Any]]:
    event_package = seal({
        "package_id": "synthetic:event-classification:20260820",
        "package_version": "1.0.0", "package_state": "synthetic_test_only",
        "matching_policy": "exact_utf8_v1",
        "exact_rules": [
            {"rule_id": f"event:{token.lower()}", "owner_type": "TemporalEvent",
             "field_path": "event_type", "exact_raw_token": token, "output_subtype": subtype}
            for token, subtype in EVENT_TOKEN_RULES
        ],
        "compound_rules": [
            {"rule_id": f"event:ip:{phase.lower()}", "owner_type": "TemporalEvent",
             "components": [
                 {"field_path": "event_type", "exact_raw_token": "IP"},
                 {"field_path": "phase", "exact_raw_token": phase},
             ], "output_subtype": subtype}
            for phase, subtype in COMPOUND_RULES
        ],
        "subtype_to_domain": dict(SUBTYPE_TO_DOMAIN),
    }, "package_content_hash")
    taxonomy_id = "synthetic:risk-taxonomy:20260820"
    taxonomy_version = "1.0.0"
    taxonomy = seal({
        "package_id": taxonomy_id, "package_version": taxonomy_version,
        "package_state": "synthetic_test_only", "matching_policy": "exact_utf8_v1",
        "rules": [
            {"rule_id": f"risk:{code}", "owner_type": "RiskCandidate", "field_path": "risk_type",
             "exact_raw_token": raw, "risk_type_code": code,
             "risk_type_code_content_hash": code_hash(taxonomy_id, taxonomy_version, code)}
            for raw, code, _ in RISK_RULES
        ],
    }, "package_content_hash")
    severity = seal({
        "package_id": "synthetic:severity-policy:20260820", "package_version": "1.0.0",
        "package_state": "synthetic_test_only", "matching_policy": "exact_utf8_v1",
        "flag_policy": "clinical_risk_flags_do_not_promote_severity",
        "rules": [
            {"rule_id": f"severity:{raw}", "owner_type": "RiskCandidate", "field_path": "severity",
             "exact_raw_token": raw, "severity": output}
            for raw, output in SEVERITY_RULES
        ],
    }, "package_content_hash")
    lexicon = seal({
        "package_id": "synthetic:risk-lexicon-zh-cn:20260820", "package_version": "1.0.0",
        "package_state": "synthetic_test_only", "locale": "zh-CN",
        "matching_policy": "exact_utf8_v1",
        "taxonomy_package_id": taxonomy_id, "taxonomy_package_version": taxonomy_version,
        "items": [
            {"risk_type_code": code, "risk_type_code_content_hash": code_hash(taxonomy_id, taxonomy_version, code),
             "label": label}
            for _, code, label in RISK_RULES
        ],
    }, "package_content_hash")
    return {"event_classification": event_package, "risk_taxonomy": taxonomy,
            "severity_policy": severity, "risk_presentation_lexicon": lexicon}


def accepted_record(kind: str, package: dict[str, Any]) -> dict[str, Any]:
    ref = f"synthetic-accepted:{kind}:{package['package_content_hash'][:20]}"
    return seal({
        "accepted_record_ref": ref, "package_kind": kind,
        "package_id": package["package_id"], "package_version": package["package_version"],
        "package_content_hash": package["package_content_hash"],
        "authority_scope": "synthetic_test_only", "non_clinical": True,
        "acceptance_basis": "frozen_contract_fixture_only",
    }, "accepted_record_content_hash")


def build_acceptance_registry(packages: dict[str, dict[str, Any]]) -> dict[str, Any]:
    records = [accepted_record(kind, packages[kind]) for kind in sorted(packages)]
    return seal({
        "registry_id": ACCEPTANCE_REGISTRY_ID, "authority_scope": "synthetic_test_only",
        "non_clinical": True, "records": records,
    }, "registry_content_hash")


def receipt(kind: str, package: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    record = next(item for item in registry["records"] if item["package_kind"] == kind)
    body = {
        "receipt_id": "receipt:" + sha({"registry": registry["registry_id"], "record": record["accepted_record_ref"]})[:24],
        "registry_id": registry["registry_id"], "registry_content_hash": registry["registry_content_hash"],
        "accepted_record_ref": record["accepted_record_ref"],
        "accepted_record_content_hash": record["accepted_record_content_hash"],
        "package_kind": kind, "package_id": package["package_id"],
        "package_version": package["package_version"], "package_content_hash": package["package_content_hash"],
        "authority_scope": "synthetic_test_only", "audience_contract_id": "contract.s4.1",
    }
    return seal(body, "receipt_content_hash")


def evidence(record_ref: str, registry: dict[str, Any]) -> dict[str, Any]:
    record = next(item for item in registry["records"] if item["source_record_ref"] == record_ref)
    if not isinstance(record["field_value"], str):
        raise TypeError("token evidence requires string source field")
    return seal({
        "evidence_ref": "evidence:" + record["source_record_content_hash"][:24],
        "source_registry_id": registry["registry_id"],
        "source_registry_content_hash": registry["registry_content_hash"],
        "source_record_ref": record["source_record_ref"],
        "source_record_content_hash": record["source_record_content_hash"],
        "owner_type": record["source_type_path"].rsplit(".", 1)[1],
        "owner_ref": record["owner_ref"], "field_path": record["field_path"],
        "raw_token": record["field_value"],
        "snapshot_ref": record["identity_join"]["snapshot_ref"],
        "source_content_identity": record["source_record_content_hash"],
        "source_revision_content_pairs": copy.deepcopy(record["source_revision_content_pairs"]),
        "source_locator_refs": copy.deepcopy(record["source_locator_refs"]),
    }, "evidence_content_hash")


def flag_evidence(record_ref: str, registry: dict[str, Any]) -> dict[str, Any]:
    record = next(item for item in registry["records"] if item["source_record_ref"] == record_ref)
    return seal({
        "evidence_ref": "flag-evidence:" + record["source_record_content_hash"][:24],
        "source_registry_id": registry["registry_id"],
        "source_registry_content_hash": registry["registry_content_hash"],
        "source_record_ref": record["source_record_ref"],
        "source_record_content_hash": record["source_record_content_hash"],
        "owner_type": "RiskInstance", "owner_ref": record["owner_ref"],
        "field_path": record["field_path"], "flags": record["field_value"],
        "snapshot_ref": record["identity_join"]["snapshot_ref"],
        "source_content_identity": record["source_record_content_hash"],
        "source_revision_content_pairs": copy.deepcopy(record["source_revision_content_pairs"]),
        "source_locator_refs": copy.deepcopy(record["source_locator_refs"]),
    }, "evidence_content_hash")


def event_input(packages: dict[str, dict[str, Any]], acceptance: dict[str, Any], source: dict[str, Any],
                record_ref: str, phase_ref: str | None = None, use_context: str = "synthetic_test") -> dict[str, Any]:
    package = packages["event_classification"]
    ev = [evidence(record_ref, source)]
    if phase_ref:
        ev.append(evidence(phase_ref, source))
    return {"use_context": use_context, "identity_join": copy.deepcopy(IDENTITY), "evidence": ev,
            "package": copy.deepcopy(package), "receipt": receipt("event_classification", package, acceptance)}


def risk_input(packages: dict[str, dict[str, Any]], acceptance: dict[str, Any], source: dict[str, Any],
               severity_ref: str, flag: bool = False, use_context: str = "synthetic_test") -> dict[str, Any]:
    taxonomy, severity, lexicon = packages["risk_taxonomy"], packages["severity_policy"], packages["risk_presentation_lexicon"]
    result = {
        "use_context": use_context, "identity_join": copy.deepcopy(IDENTITY),
        "taxonomy_evidence": evidence("src:risk-type:risk-type-potential-unreported-ae", source),
        "severity_evidence": [evidence(severity_ref, source)], "flag_evidence": None,
        "taxonomy_package": copy.deepcopy(taxonomy), "taxonomy_receipt": receipt("risk_taxonomy", taxonomy, acceptance),
        "severity_package": copy.deepcopy(severity), "severity_receipt": receipt("severity_policy", severity, acceptance),
        "lexicon": copy.deepcopy(lexicon), "lexicon_receipt": receipt("risk_presentation_lexicon", lexicon, acceptance),
    }
    if flag:
        result["flag_evidence"] = flag_evidence("src:clinical-flags:sae-aesi", source)
    return result


def event_authority(input_value: dict[str, Any], subtype: str) -> dict[str, Any]:
    package, receipt_value = input_value["package"], input_value["receipt"]
    body = {
        "authority_ref": "event-authority:" + sha({"evidence": [x["evidence_ref"] for x in input_value["evidence"]], "package": package["package_content_hash"]})[:24],
        "identity_join": copy.deepcopy(input_value["identity_join"]),
        "evidence_refs": [x["evidence_ref"] for x in input_value["evidence"]],
        "package_ref": package["package_id"], "package_content_hash": package["package_content_hash"],
        "receipt_ref": receipt_value["receipt_id"], "receipt_content_hash": receipt_value["receipt_content_hash"],
        "subtype": subtype, "domain": SUBTYPE_TO_DOMAIN[subtype],
    }
    return seal(body, "authority_content_hash")


def risk_authority(input_value: dict[str, Any], severity: str) -> dict[str, Any]:
    taxonomy, lexicon = input_value["taxonomy_package"], input_value["lexicon"]
    rule = next(x for x in taxonomy["rules"] if x["exact_raw_token"] == input_value["taxonomy_evidence"]["raw_token"])
    item = next(x for x in lexicon["items"] if x["risk_type_code"] == rule["risk_type_code"])
    body = {
        "authority_ref": "risk-authority:" + sha({"taxonomy": input_value["taxonomy_evidence"]["evidence_ref"], "severity": [x["evidence_ref"] for x in input_value["severity_evidence"]]})[:24],
        "identity_join": copy.deepcopy(input_value["identity_join"]),
        "taxonomy_evidence_ref": input_value["taxonomy_evidence"]["evidence_ref"],
        "severity_evidence_refs": [x["evidence_ref"] for x in input_value["severity_evidence"]],
        "flag_evidence_ref": input_value["flag_evidence"]["evidence_ref"] if input_value["flag_evidence"] else None,
        "risk_type_code": rule["risk_type_code"], "risk_type_code_content_hash": rule["risk_type_code_content_hash"],
        "risk_type_zh": item["label"], "severity": severity,
        "taxonomy_package_ref": taxonomy["package_id"], "taxonomy_package_content_hash": taxonomy["package_content_hash"],
        "taxonomy_receipt_ref": input_value["taxonomy_receipt"]["receipt_id"], "taxonomy_receipt_content_hash": input_value["taxonomy_receipt"]["receipt_content_hash"],
        "severity_package_ref": input_value["severity_package"]["package_id"], "severity_package_content_hash": input_value["severity_package"]["package_content_hash"],
        "severity_receipt_ref": input_value["severity_receipt"]["receipt_id"], "severity_receipt_content_hash": input_value["severity_receipt"]["receipt_content_hash"],
        "lexicon_package_ref": lexicon["package_id"], "lexicon_package_content_hash": lexicon["package_content_hash"],
        "lexicon_receipt_ref": input_value["lexicon_receipt"]["receipt_id"], "lexicon_receipt_content_hash": input_value["lexicon_receipt"]["receipt_content_hash"],
    }
    return seal(body, "authority_content_hash")


def mutation(target: str, pointer: str, operation: str, value: Any = None,
             mechanical_reseal: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {"target": target, "json_pointer": pointer, "operation": operation,
            "value": value, "mechanical_reseal": mechanical_reseal or []}


def reseal(pointer: str, field: str) -> dict[str, Any]:
    return {"json_pointer": pointer, "hash_field": field, "bind_package_pointer": None}


def build_challenges(packages: dict[str, dict[str, Any]], acceptance: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    baselines: dict[str, Any] = {
        "event_mh": event_input(packages, acceptance, source, "src:event-type:mh"),
        "event_ae": event_input(packages, acceptance, source, "src:event-type:ae"),
        "event_ip_dose": event_input(packages, acceptance, source, "src:event-type:ip", "src:event-phase:dose"),
        "event_ip_pause": event_input(packages, acceptance, source, "src:event-type:ip", "src:event-phase:pause"),
        "risk_high": risk_input(packages, acceptance, source, "src:severity:high"),
        "risk_low": risk_input(packages, acceptance, source, "src:severity:low"),
        "governance": {
            "parent_pin_status": "exact", "target_path": CONTEXT_PATH,
            "authority_source_kind": "frozen_registry", "transport_text": "no verdict token",
            "s4_payload": copy.deepcopy(IDENTITY),
        },
    }
    cases: list[dict[str, Any]] = []

    def add(case_id: str, kind: str, baseline: str, mut: dict[str, Any], output: dict[str, Any] | None = None,
            code: str | None = None, note: str = "") -> None:
        cases.append({"case_id": case_id, "evaluation_kind": kind, "baseline_ref": baseline,
                      "mutation": mut, "expected_output": output, "expected_typed_error": code,
                      "forbidden_output": None if code is None else "any_semantic_authority",
                      "non_llm_oracle": "exact_authority_equality" if code is None else "exact_typed_error_and_no_authority",
                      "note": note})

    # Every positive mutation replaces a complete source-registry-resolved evidence object.
    for index, (token, subtype) in enumerate(EVENT_TOKEN_RULES, 1):
        base = "event_ae" if token == "MH" else "event_mh"
        mutated = copy.deepcopy(baselines[base])
        ev = evidence("src:event-type:" + token.lower().replace("_", "-"), source)
        mutated["evidence"][0] = ev
        add(f"SEM-EVT-{index:03d}", "event", base, mutation("input", "/evidence/0", "replace", ev), event_authority(mutated, subtype))
    for offset, (phase, subtype) in enumerate(COMPOUND_RULES, 14):
        base = "event_ip_pause" if phase == "DOSE" else "event_ip_dose"
        mutated = copy.deepcopy(baselines[base])
        ev = evidence(f"src:event-phase:{phase.lower()}", source)
        mutated["evidence"][1] = ev
        add(f"SEM-EVT-{offset:03d}", "event", base, mutation("input", "/evidence/1", "replace", ev), event_authority(mutated, subtype))

    for index, (raw, output) in enumerate(SEVERITY_RULES[:4], 1):
        base = "risk_low" if raw == "high" else "risk_high"
        mutated = copy.deepcopy(baselines[base])
        ev = evidence(f"src:severity:{raw}", source)
        mutated["severity_evidence"][0] = ev
        add(f"SEM-RISK-POS-{index:03d}", "risk", base,
            mutation("input", "/severity_evidence/0", "replace", ev), risk_authority(mutated, output))
    risk_flag = copy.deepcopy(baselines["risk_high"])
    flags = flag_evidence("src:clinical-flags:sae-aesi", source)
    risk_flag["flag_evidence"] = flags
    add("SEM-RISK-POS-005", "risk", "risk_high", mutation("input", "/flag_evidence", "replace", flags),
        risk_authority(risk_flag, "high"), note="real mm_r2.risk.RiskInstance.clinical_risk_flags does not promote severity")

    # Decisive active adversarial probes.
    swapped_rules = copy.deepcopy(baselines["event_mh"]["package"]["exact_rules"])
    ae_rule = next(item for item in swapped_rules if item["exact_raw_token"] == "AE")
    mh_rule = next(item for item in swapped_rules if item["exact_raw_token"] == "MH")
    ae_rule["output_subtype"], mh_rule["output_subtype"] = "mh", "ae"
    bind_receipt = reseal("/receipt", "receipt_content_hash")
    bind_receipt["bind_package_pointer"] = "/package"
    add("SEM-AUTH-001", "event", "event_mh",
        mutation("input", "/package/exact_rules", "replace", swapped_rules, [
            reseal("/package", "package_content_hash"), bind_receipt,
        ]), code="SEM_ACCEPTED_RECORD_PACKAGE_MISMATCH",
        note="fully resealed MH to ae candidate cannot change frozen accepted record")
    risk_out = risk_authority(baselines["risk_high"], "high")
    baselines["risk_authority"] = {"source_input": copy.deepcopy(baselines["risk_high"]), "candidate_authority": risk_out}
    add("SEM-AUTH-002", "risk_authority", "risk_authority",
        mutation("candidate_authority", "/risk_type_zh", "replace", "伪造标签", [reseal("", "authority_content_hash")]),
        code="SEM_LEXICON_LABEL_MISMATCH")
    catastrophic = evidence("src:severity:catastrophic", source)
    add("SEM-AUTH-003", "risk", "risk_high", mutation("input", "/severity_evidence/0", "replace", catastrophic),
        code="SEM_SEVERITY_TOKEN_UNMAPPED")
    add("SEM-AUTH-004", "event", "event_mh",
        mutation("input", "/receipt/example", "add", True, [reseal("/receipt", "receipt_content_hash")]),
        code="SEM_SCHEMA_EXACT_KEYS")
    add("SEM-AUTH-005", "risk", "risk_high",
        mutation("input", "/severity_package/rules/4", "remove", mechanical_reseal=[
            reseal("/severity_package", "package_content_hash"), reseal("/severity_receipt", "receipt_content_hash")]),
        code="SEM_LEGACY_SEVERITY_RULE_MISSING")
    add("SEM-AUTH-006", "event", "event_mh",
        mutation("input", "/package/matching_policy", "replace", "fuzzy", [
            reseal("/package", "package_content_hash"), reseal("/receipt", "receipt_content_hash")]),
        code="SEM_MATCHING_POLICY_FORBIDDEN")
    add("SEM-AUTH-007", "event", "event_mh",
        mutation("input", "/evidence/0/owner_ref", "replace", "event-cross-owner", [reseal("/evidence/0", "evidence_content_hash")]),
        code="SEM_SOURCE_RECORD_OWNER_MISMATCH")
    add("SEM-AUTH-008", "event", "event_mh",
        mutation("input", "/receipt/accepted_record_ref", "replace", "synthetic-accepted:forged", [reseal("/receipt", "receipt_content_hash")]),
        code="SEM_ACCEPTED_RECORD_UNRESOLVED")

    # Additional global/shape/provenance and fail-closed cases.
    add("SEM-NEG-001", "event", "event_mh", mutation("input", "/evidence/0/raw_token", "replace", "AE", [reseal("/evidence/0", "evidence_content_hash")]), code="SEM_SOURCE_RECORD_VALUE_MISMATCH")
    add("SEM-NEG-002", "event", "event_mh", mutation("input", "/evidence/0/source_record_content_hash", "replace", "0" * 64, [reseal("/evidence/0", "evidence_content_hash")]), code="SEM_SOURCE_RECORD_HASH_MISMATCH")
    add("SEM-NEG-003", "event", "event_mh", mutation("input", "/evidence/0/source_revision_content_pairs/0/source_content_hash", "replace", "0" * 64, [reseal("/evidence/0", "evidence_content_hash")]), code="SEM_SOURCE_RECORD_REVISION_MISMATCH")
    add("SEM-NEG-004", "event", "event_mh", mutation("input", "/identity_join/event_ref", "add", "event-phantom"), code="SEM_SCHEMA_EXACT_KEYS")
    add("SEM-NEG-005", "event", "event_mh", mutation("input", "/evidence/0/raw_token", "replace", "MH ", [reseal("/evidence/0", "evidence_content_hash")]), code="SEM_SOURCE_RECORD_VALUE_MISMATCH")
    lower = evidence("src:event-type:ae-lower", source)
    add("SEM-NEG-006", "event", "event_mh", mutation("input", "/evidence/0", "replace", lower), code="SEM_EVENT_TOKEN_UNMAPPED")
    unknown = evidence("src:event-type:unknown-event", source)
    add("SEM-NEG-007", "event", "event_mh", mutation("input", "/evidence/0", "replace", unknown), code="SEM_EVENT_TOKEN_UNMAPPED")
    add("SEM-NEG-008", "event", "event_mh", mutation("input", "/package/exact_rules/0", "remove", mechanical_reseal=[reseal("/package", "package_content_hash"), reseal("/receipt", "receipt_content_hash")]), code="SEM_EVENT_RELATION_INCOMPLETE")
    add("SEM-NEG-009", "event", "event_mh", mutation("input", "/package/subtype_to_domain/ae", "replace", "ninth_domain", [reseal("/package", "package_content_hash"), reseal("/receipt", "receipt_content_hash")]), code="SEM_EVENT_RELATION_INCOMPLETE")
    add("SEM-NEG-010", "event", "event_mh", mutation("input", "/package/exact_rules/0/extra", "add", True, [reseal("/package", "package_content_hash"), reseal("/receipt", "receipt_content_hash")]), code="SEM_SCHEMA_EXACT_KEYS")
    add("SEM-NEG-011", "event", "event_mh", mutation("input", "/use_context", "replace", "clinical"), code="SEM_SYNTHETIC_CLINICAL_AUTHORITY_FORBIDDEN")
    add("SEM-NEG-012", "event", "event_mh", mutation("input", "/receipt/package_content_hash", "replace", "0" * 64, [reseal("/receipt", "receipt_content_hash")]), code="SEM_RECEIPT_PACKAGE_MISMATCH")
    add("SEM-NEG-013", "event", "event_mh", mutation("input", "/package/package_content_hash", "replace", "0" * 64), code="SEM_PACKAGE_HASH_MISMATCH")
    add("SEM-NEG-014", "event", "event_mh", mutation("input", "/evidence/0/evidence_content_hash", "replace", "0" * 64), code="SEM_EVIDENCE_HASH_MISMATCH")
    add("SEM-NEG-015", "event", "event_mh", mutation("input", "/evidence/0/source_registry_content_hash", "replace", "0" * 64, [reseal("/evidence/0", "evidence_content_hash")]), code="SEM_SOURCE_REGISTRY_PIN_MISMATCH")
    add("SEM-NEG-016", "risk", "risk_high", mutation("input", "/taxonomy_evidence", "replace", evidence("src:risk-type:unknown", source)), code="SEM_RISK_TOKEN_UNMAPPED")
    add("SEM-NEG-017", "risk", "risk_high", mutation("input", "/taxonomy_package/rules/0/risk_type_code", "replace", "BAD-CODE", [reseal("/taxonomy_package", "package_content_hash"), reseal("/taxonomy_receipt", "receipt_content_hash")]), code="SEM_RISK_TYPE_CODE_INVALID")
    add("SEM-NEG-018", "risk", "risk_high", mutation("input", "/lexicon/locale", "replace", "en-US", [reseal("/lexicon", "package_content_hash"), reseal("/lexicon_receipt", "receipt_content_hash")]), code="SEM_LEXICON_LOCALE_MISMATCH")
    add("SEM-NEG-019", "risk", "risk_high", mutation("input", "/lexicon/items/0/label", "replace", "通用风险", [reseal("/lexicon", "package_content_hash"), reseal("/lexicon_receipt", "receipt_content_hash")]), code="SEM_GENERIC_RISK_LABEL_FORBIDDEN")
    add("SEM-NEG-020", "risk", "risk_high", mutation("input", "/severity_evidence/1", "add", evidence("src:severity:low", source)), code="SEM_SEVERITY_CONFLICT")
    add("SEM-NEG-021", "risk", "risk_high", mutation("input", "/severity_package/rules/1/severity", "replace", "catastrophic", [reseal("/severity_package", "package_content_hash"), reseal("/severity_receipt", "receipt_content_hash")]), code="SEM_SEVERITY_ENUM_INVALID")
    add("SEM-NEG-022", "risk", "risk_high", mutation("input", "/severity_package/rules/1/severity", "replace", "critical", [reseal("/severity_package", "package_content_hash"), reseal("/severity_receipt", "receipt_content_hash")]), code="SEM_SEVERITY_PROMOTION_FORBIDDEN")
    add("SEM-NEG-023", "risk", "risk_high", mutation("input", "/severity_package/flag_policy", "replace", "sae_promotes_critical", [reseal("/severity_package", "package_content_hash"), reseal("/severity_receipt", "receipt_content_hash")]), code="SEM_SAE_AESI_PROMOTION_FORBIDDEN")
    add("SEM-NEG-024", "risk", "risk_high", mutation("input", "/taxonomy_package/rules/0/risk_type_code_content_hash", "replace", "0" * 64, [reseal("/taxonomy_package", "package_content_hash"), reseal("/taxonomy_receipt", "receipt_content_hash")]), code="SEM_RISK_TYPE_CODE_HASH_MISMATCH")
    add("SEM-NEG-025", "risk", "risk_high", mutation("input", "/lexicon/items/0", "remove", mechanical_reseal=[reseal("/lexicon", "package_content_hash"), reseal("/lexicon_receipt", "receipt_content_hash")]), code="SEM_LEXICON_CODE_MISSING")
    add("SEM-NEG-026", "event", "event_mh", mutation("input", "/evidence/0/source_locator_refs/0", "replace", "forged.locator", [reseal("/evidence/0", "evidence_content_hash")]), code="SEM_SOURCE_RECORD_LOCATOR_MISMATCH")
    add("SEM-NEG-027", "event", "event_mh", mutation("input", "/receipt/registry_content_hash", "replace", "0" * 64, [reseal("/receipt", "receipt_content_hash")]), code="SEM_ACCEPTANCE_REGISTRY_PIN_MISMATCH")
    add("SEM-NEG-028", "event", "event_mh", mutation("input", "/receipt/authority_scope", "replace", "clinical_authority", [reseal("/receipt", "receipt_content_hash")]), code="SEM_SYNTHETIC_CLINICAL_AUTHORITY_FORBIDDEN")
    duplicate_rule = copy.deepcopy(baselines["event_mh"]["package"]["exact_rules"][1])
    add("SEM-NEG-029", "event", "event_mh", mutation("input", "/package/exact_rules/13", "add", duplicate_rule, [reseal("/package", "package_content_hash"), reseal("/receipt", "receipt_content_hash")]), code="SEM_RULE_DUPLICATE_OR_AMBIGUOUS")
    version_bind = reseal("/receipt", "receipt_content_hash")
    version_bind["bind_package_pointer"] = "/package"
    add("SEM-NEG-030", "event", "event_mh", mutation("input", "/package/package_version", "replace", "2.0.0", [reseal("/package", "package_content_hash"), version_bind]), code="SEM_ACCEPTED_RECORD_PACKAGE_MISMATCH")
    add("SEM-NEG-031", "event", "event_mh", mutation("input", "/identity_join/subject_ref", "replace", "subject-cross-identity"), code="SEM_IDENTITY_JOIN_MISMATCH")
    add("SEM-NEG-032", "risk", "risk_high", mutation("input", "/lexicon/taxonomy_package_id", "replace", "forged-taxonomy", [reseal("/lexicon", "package_content_hash"), reseal("/lexicon_receipt", "receipt_content_hash")]), code="SEM_LEXICON_TAXONOMY_MISMATCH")
    add("SEM-GOV-001", "governance", "governance", mutation("input", "/parent_pin_status", "replace", "drift"), code="SEM_PARENT_PIN_DRIFT")
    add("SEM-GOV-002", "governance", "governance", mutation("input", "/target_path", "replace", PARENT_MANIFEST_PATH), code="SEM_ORIGINAL_PATH_OVERWRITE_FORBIDDEN")
    add("SEM-GOV-003", "governance", "governance", mutation("input", "/authority_source_kind", "replace", "example"), code="SEM_EXAMPLE_AS_AUTHORITY_FORBIDDEN")
    add("SEM-GOV-004", "governance", "governance", mutation("input", "/transport_text", "replace", "ACCEPT_R5_S5_PUBLIC_AUTHORITY_SEMANTIC_DELTA_V0_1"), code="SEM_ACCEPTANCE_TOKEN_LEAKAGE")
    add("SEM-GOV-005", "governance", "governance", mutation("input", "/s4_payload/domain", "add", "ae"), code="SEM_S4_VALUE_TRANSFER_FORBIDDEN")

    return {
        "schema": "medical-monitoring-r5-s5-semantic-challenge-registry-v0.1",
        "contract_id": CONTRACT_ID,
        "evaluation_contract": {
            "mutation_count_per_case": 1,
            "verifier_must_not_branch_on": ["case_id", "expected_typed_error", "note"],
            "mechanical_reseal_semantics": "rehash exact object only; never changes frozen registries",
            "success_requires": "exactly one nonempty event match or one taxonomy, one severity and one lexicon match",
        },
        "baselines": baselines, "cases": cases,
    }


def build_schema() -> dict[str, Any]:
    objects = {
        "SourceRevisionContentPair": exact_object({"source_ref": fld("string"), "source_content_hash": fld("sha256")}),
        "SemanticIdentityJoin": exact_object({key: fld("string") for key in IDENTITY}),
        "TypedSemanticSourceRecord": exact_object({
            "source_record_ref": fld("string"), "source_type_path": fld("typed_python_path"),
            "owner_field_path": fld("string"), "owner_ref": fld("string"), "field_path": fld("string"),
            "field_value": fld("json_scalar_or_string_array"), "identity_join": fld("SemanticIdentityJoin"),
            "source_revision_content_pairs": fld("SourceRevisionContentPair", "one_or_more"),
            "source_locator_refs": fld("string", "one_or_more"), "source_record_content_hash": fld("sha256"),
        }),
        "SyntheticTypedSourceRecordRegistry": exact_object({
            "registry_id": fld("string"), "authority_scope": fld("synthetic_test_only"), "non_clinical": fld("true"),
            "records": fld("TypedSemanticSourceRecord", "one_or_more"), "registry_content_hash": fld("sha256"),
        }),
        "SyntheticAcceptedPolicyRecord": exact_object({
            "accepted_record_ref": fld("string"), "package_kind": fld("package_kind"),
            "package_id": fld("string"), "package_version": fld("semver"), "package_content_hash": fld("sha256"),
            "authority_scope": fld("synthetic_test_only"), "non_clinical": fld("true"),
            "acceptance_basis": fld("frozen_contract_fixture_only"), "accepted_record_content_hash": fld("sha256"),
        }),
        "SyntheticPolicyAcceptanceRegistry": exact_object({
            "registry_id": fld("string"), "authority_scope": fld("synthetic_test_only"), "non_clinical": fld("true"),
            "records": fld("SyntheticAcceptedPolicyRecord", "exactly_four"), "registry_content_hash": fld("sha256"),
        }),
        "SemanticPolicyAcceptanceReceipt": exact_object({
            "receipt_id": fld("string"), "registry_id": fld("string"), "registry_content_hash": fld("sha256"),
            "accepted_record_ref": fld("string"), "accepted_record_content_hash": fld("sha256"),
            "package_kind": fld("package_kind"), "package_id": fld("string"), "package_version": fld("semver"),
            "package_content_hash": fld("sha256"), "authority_scope": fld("synthetic_test_only"),
            "audience_contract_id": fld("contract.s4.1"), "receipt_content_hash": fld("sha256"),
        }),
        "RawSemanticTokenEvidence": exact_object({
            "evidence_ref": fld("string"), "source_registry_id": fld("string"),
            "source_registry_content_hash": fld("sha256"), "source_record_ref": fld("string"),
            "source_record_content_hash": fld("sha256"), "owner_type": fld("owner_type"),
            "owner_ref": fld("string"), "field_path": fld("string"), "raw_token": fld("string"),
            "snapshot_ref": fld("string"),
            "source_content_identity": fld("sha256"),
            "source_revision_content_pairs": fld("SourceRevisionContentPair", "one_or_more"),
            "source_locator_refs": fld("string", "one_or_more"), "evidence_content_hash": fld("sha256"),
        }),
        "RawSemanticFlagEvidence": exact_object({
            "evidence_ref": fld("string"), "source_registry_id": fld("string"),
            "source_registry_content_hash": fld("sha256"), "source_record_ref": fld("string"),
            "source_record_content_hash": fld("sha256"), "owner_type": fld("RiskInstance"),
            "owner_ref": fld("string"), "field_path": fld("clinical_risk_flags"), "flags": fld("sae_aesi_array"),
            "snapshot_ref": fld("string"),
            "source_content_identity": fld("sha256"),
            "source_revision_content_pairs": fld("SourceRevisionContentPair", "one_or_more"),
            "source_locator_refs": fld("string", "one_or_more"), "evidence_content_hash": fld("sha256"),
        }),
        "ExactRuleComponent": exact_object({"field_path": fld("event_field"), "exact_raw_token": fld("string")}),
        "SubtypeToDomainRelation": exact_object({subtype: fld("domain_literal") for subtype in SUBTYPE_TO_DOMAIN}),
        "ExactEventTokenRule": exact_object({"rule_id": fld("string"), "owner_type": fld("TemporalEvent"), "field_path": fld("event_type"), "exact_raw_token": fld("string"), "output_subtype": fld("journey_subtype")}),
        "CompoundEventClassificationRule": exact_object({"rule_id": fld("string"), "owner_type": fld("TemporalEvent"), "components": fld("ExactRuleComponent", "exactly_two"), "output_subtype": fld("journey_subtype")}),
        "EventClassificationRulePackage": exact_object({"package_id": fld("string"), "package_version": fld("semver"), "package_state": fld("synthetic_test_only"), "matching_policy": fld("exact_utf8_v1"), "exact_rules": fld("ExactEventTokenRule", "exactly_thirteen"), "compound_rules": fld("CompoundEventClassificationRule", "exactly_three"), "subtype_to_domain": fld("SubtypeToDomainRelation"), "package_content_hash": fld("sha256")}),
        "RiskTaxonomyRule": exact_object({"rule_id": fld("string"), "owner_type": fld("RiskCandidate"), "field_path": fld("risk_type"), "exact_raw_token": fld("string"), "risk_type_code": fld("risk_type_code"), "risk_type_code_content_hash": fld("sha256")}),
        "RiskTaxonomyPackage": exact_object({"package_id": fld("string"), "package_version": fld("semver"), "package_state": fld("synthetic_test_only"), "matching_policy": fld("exact_utf8_v1"), "rules": fld("RiskTaxonomyRule", "one_or_more"), "package_content_hash": fld("sha256")}),
        "SeverityPolicyRule": exact_object({"rule_id": fld("string"), "owner_type": fld("RiskCandidate"), "field_path": fld("severity"), "exact_raw_token": fld("string"), "severity": fld("severity")}),
        "SeverityPolicyPackage": exact_object({"package_id": fld("string"), "package_version": fld("semver"), "package_state": fld("synthetic_test_only"), "matching_policy": fld("exact_utf8_v1"), "flag_policy": fld("clinical_risk_flags_do_not_promote_severity"), "rules": fld("SeverityPolicyRule", "exactly_seven"), "package_content_hash": fld("sha256")}),
        "RiskPresentationLexiconItem": exact_object({"risk_type_code": fld("risk_type_code"), "risk_type_code_content_hash": fld("sha256"), "label": fld("non_generic_zh_cn_string")}),
        "RiskPresentationLexicon": exact_object({"package_id": fld("string"), "package_version": fld("semver"), "package_state": fld("synthetic_test_only"), "locale": fld("zh-CN"), "matching_policy": fld("exact_utf8_v1"), "taxonomy_package_id": fld("string"), "taxonomy_package_version": fld("semver"), "items": fld("RiskPresentationLexiconItem", "one_or_more"), "package_content_hash": fld("sha256")}),
        "SemanticAuthorityError": exact_object({"code": fld("typed_error_code"), "path": fld("json_pointer"), "authority_ref": fld("string", nullable=True)}),
        "EventClassificationAuthority": exact_object({"authority_ref": fld("string"), "identity_join": fld("SemanticIdentityJoin"), "evidence_refs": fld("string", "one_or_more"), "package_ref": fld("string"), "package_content_hash": fld("sha256"), "receipt_ref": fld("string"), "receipt_content_hash": fld("sha256"), "subtype": fld("journey_subtype"), "domain": fld("domain"), "authority_content_hash": fld("sha256")}),
        "RiskClassificationAuthority": exact_object({"authority_ref": fld("string"), "identity_join": fld("SemanticIdentityJoin"), "taxonomy_evidence_ref": fld("string"), "severity_evidence_refs": fld("string", "one_or_more"), "flag_evidence_ref": fld("string", nullable=True), "risk_type_code": fld("risk_type_code"), "risk_type_code_content_hash": fld("sha256"), "risk_type_zh": fld("non_generic_zh_cn_string"), "severity": fld("severity"), "taxonomy_package_ref": fld("string"), "taxonomy_package_content_hash": fld("sha256"), "taxonomy_receipt_ref": fld("string"), "taxonomy_receipt_content_hash": fld("sha256"), "severity_package_ref": fld("string"), "severity_package_content_hash": fld("sha256"), "severity_receipt_ref": fld("string"), "severity_receipt_content_hash": fld("sha256"), "lexicon_package_ref": fld("string"), "lexicon_package_content_hash": fld("sha256"), "lexicon_receipt_ref": fld("string"), "lexicon_receipt_content_hash": fld("sha256"), "authority_content_hash": fld("sha256")}),
        "EventClassificationSuccess": exact_object({"ok": fld("true"), "authority": fld("EventClassificationAuthority"), "errors": fld("SemanticAuthorityError", "empty")}),
        "EventClassificationFailure": exact_object({"ok": fld("false"), "authority": fld("null"), "errors": fld("SemanticAuthorityError", "one_or_more")}),
        "RiskClassificationSuccess": exact_object({"ok": fld("true"), "authority": fld("RiskClassificationAuthority"), "errors": fld("SemanticAuthorityError", "empty")}),
        "RiskClassificationFailure": exact_object({"ok": fld("false"), "authority": fld("null"), "errors": fld("SemanticAuthorityError", "one_or_more")}),
        "EventClassificationInput": exact_object({"use_context": fld("synthetic_test"), "identity_join": fld("SemanticIdentityJoin"), "evidence": fld("RawSemanticTokenEvidence", "one_or_more"), "package": fld("EventClassificationRulePackage"), "receipt": fld("SemanticPolicyAcceptanceReceipt")}),
        "RiskClassificationInput": exact_object({"use_context": fld("synthetic_test"), "identity_join": fld("SemanticIdentityJoin"), "taxonomy_evidence": fld("RawSemanticTokenEvidence"), "severity_evidence": fld("RawSemanticTokenEvidence", "one_or_more"), "flag_evidence": fld("RawSemanticFlagEvidence", nullable=True), "taxonomy_package": fld("RiskTaxonomyPackage"), "taxonomy_receipt": fld("SemanticPolicyAcceptanceReceipt"), "severity_package": fld("SeverityPolicyPackage"), "severity_receipt": fld("SemanticPolicyAcceptanceReceipt"), "lexicon": fld("RiskPresentationLexicon"), "lexicon_receipt": fld("SemanticPolicyAcceptanceReceipt")}),
        "RiskAuthorityValidationInput": exact_object({"source_input": fld("RiskClassificationInput"), "candidate_authority": fld("RiskClassificationAuthority")}),
        "GovernanceProbeInput": exact_object({"parent_pin_status": fld("exact"), "target_path": fld("allowed_delta_path"), "authority_source_kind": fld("frozen_registry"), "transport_text": fld("non_acceptance_token_string"), "s4_payload": fld("SemanticIdentityJoin")}),
        "MechanicalResealAction": exact_object({"json_pointer": fld("json_pointer"), "hash_field": fld("content_hash_field"), "bind_package_pointer": fld("json_pointer", nullable=True)}),
        "SemanticMutation": exact_object({"target": fld("mutation_target"), "json_pointer": fld("json_pointer"), "operation": fld("add_replace_remove"), "value": fld("json_value", nullable=True), "mechanical_reseal": fld("MechanicalResealAction", "many")}),
        "SemanticChallengeCase": exact_object({"case_id": fld("string"), "evaluation_kind": fld("event_risk_authority_governance"), "baseline_ref": fld("string"), "mutation": fld("SemanticMutation"), "expected_output": fld("semantic_authority", nullable=True), "expected_typed_error": fld("typed_error_code", nullable=True), "forbidden_output": fld("string", nullable=True), "non_llm_oracle": fld("oracle_name"), "note": fld("string")}),
    }
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-semantic-delta-schema-v0.1",
        "schema_version": SCHEMA_VERSION, "contract_id": CONTRACT_ID,
        "delta_mode": "append_only_semantic_authority_delta", "rewrites_parent": False,
        "invalidates_parent_acceptance": False,
        "enums": {"domain": list(DOMAINS), "journey_subtype": list(SUBTYPE_TO_DOMAIN),
                  "severity": list(SEVERITIES), "matching_policy": ["exact_utf8_v1"],
                  "authority_scope": ["synthetic_test_only"],
                  "package_kind": ["event_classification", "risk_taxonomy", "severity_policy", "risk_presentation_lexicon"]},
        "risk_type_code_contract": {"regex": "^[a-z][a-z0-9_]{2,63}$", "content_hash_recipe": "sha256(canonical_json({package_id,package_version,risk_type_code}))"},
        "exact_event_relation": {"subtype_to_domain": SUBTYPE_TO_DOMAIN, "subtype_count": 16, "domain_count": 8},
        "legacy_severity_mapping": {"severe": "high", "moderate": "medium", "mild": "low"},
        "objects": objects,
        "canonical_hash_recipes": {
            "canonical_json": "UTF-8 JSON; sorted keys; separators comma/colon; ensure_ascii=false; arrays retain order; strings receive no trim, casefold, Unicode normalization, fuzzy matching or catastrophic fallback",
            "object_content_hash": "sha256(canonical_json(exact object excluding its own hash field))",
            "source_record_content_hash": "sha256(canonical_json(exact TypedSemanticSourceRecord excluding source_record_content_hash))",
            "registry_content_hash": "sha256(canonical_json(exact registry excluding registry_content_hash))",
            "accepted_record_content_hash": "sha256(canonical_json(exact accepted record excluding accepted_record_content_hash))",
            "receipt_content_hash": "sha256(canonical_json(exact receipt excluding receipt_content_hash))",
            "authority_content_hash": "sha256(canonical_json(exact authority excluding authority_content_hash))",
        },
        "canonical_id_recipes": {
            "exact_event_rule_id": "event:{lowercase(exact_raw_token)}",
            "compound_event_rule_id": "event:ip:{lowercase(phase_exact_raw_token)}",
            "risk_rule_id": "risk:{risk_type_code}",
            "severity_rule_id": "severity:{exact_raw_token}",
            "accepted_record_ref": "synthetic-accepted:{package_kind}:{first20(package_content_hash)}",
            "receipt_id": "receipt:{first24(sha256(canonical_json({registry:registry_id,record:accepted_record_ref})))}",
            "token_evidence_ref": "evidence:{first24(source_record_content_hash)}",
            "flag_evidence_ref": "flag-evidence:{first24(source_record_content_hash)}",
            "event_authority_ref": "event-authority:{first24(sha256(canonical_json({evidence:evidence_refs,package:package_content_hash})))}",
            "risk_authority_ref": "risk-authority:{first24(sha256(canonical_json({taxonomy:taxonomy_evidence_ref,severity:severity_evidence_refs})))}",
        },
        "authorization_boundary": {
            "candidate_receipt_is_authority": False,
            "resolution": "receipt registry pin and accepted_record_ref must resolve to exact independently frozen registry object and exact accepted record",
            "synthetic_limit": "embedded registry is synthetic_test_only and non_clinical; no clinical producer authority is created",
            "status_string_inference": "forbidden",
        },
        "s4_join_surface": {"exact_keys": list(IDENTITY), "field_count": 8, "forbidden": ["event_ref", "visit_ref", "source_ref", "identity_content_hash"]},
        "real_flag_source": {"source_type_path": "mm_r2.risk.RiskInstance", "field_path": "clinical_risk_flags", "allowed_flags": ["sae", "aesi"], "severity_effect": "none"},
        "package_lifecycle": {
            "ai_proposal": "proposed content has no authority and no receipt may infer acceptance from a status string",
            "synthetic_resolution": "only exact records in the externally pinned synthetic_test_only non-clinical registry resolve in this delta",
            "clinical_resolution": "requires a separately governed external clinical registry outside this delta",
            "candidate_reseal": "cannot alter either frozen registry root",
        },
        "public_api_signatures": [
            "evaluate_event(input: EventClassificationInput) -> EventClassificationSuccess | EventClassificationFailure",
            "evaluate_risk(input: RiskClassificationInput) -> RiskClassificationSuccess | RiskClassificationFailure",
            "validate_risk_authority(input: RiskAuthorityValidationInput) -> RiskClassificationSuccess | RiskClassificationFailure",
        ],
        "future_bundle_integration": {
            "SubjectTemporalSourceBundle_additions": ["event_classification_authorities: tuple[EventClassificationAuthority, ...]", "risk_classification_authorities: tuple[RiskClassificationAuthority, ...]"],
            "leaf_projection": {"TemporalEvent.subtype": "EventClassificationAuthority.subtype", "TemporalEvent.domain": "EventClassificationAuthority.domain", "TemporalRiskAnchor.risk_type_zh": "RiskClassificationAuthority.risk_type_zh", "TemporalRiskAnchor.severity": "RiskClassificationAuthority.severity"},
            "unlock_state": "not unlocked by this delta",
        },
        "typed_error_priority": [
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
            "SEM_SEVERITY_RULESET_INCOMPLETE",
            "SEM_PACKAGE_HASH_MISMATCH", "SEM_EVIDENCE_HASH_MISMATCH",
            "SEM_SOURCE_REGISTRY_PIN_MISMATCH", "SEM_SOURCE_RECORD_UNRESOLVED",
            "SEM_SOURCE_RECORD_HASH_MISMATCH", "SEM_SOURCE_RECORD_OWNER_MISMATCH",
            "SEM_SOURCE_RECORD_VALUE_MISMATCH", "SEM_SOURCE_RECORD_REVISION_MISMATCH",
            "SEM_SOURCE_RECORD_LOCATOR_MISMATCH", "SEM_IDENTITY_JOIN_MISMATCH",
            "SEM_SYNTHETIC_CLINICAL_AUTHORITY_FORBIDDEN", "SEM_RECEIPT_HASH_MISMATCH",
            "SEM_ACCEPTANCE_REGISTRY_PIN_MISMATCH", "SEM_ACCEPTED_RECORD_UNRESOLVED",
            "SEM_ACCEPTED_RECORD_HASH_MISMATCH", "SEM_RECEIPT_PACKAGE_KIND_MISMATCH",
            "SEM_RECEIPT_PACKAGE_MISMATCH", "SEM_ACCEPTED_RECORD_PACKAGE_MISMATCH",
            "SEM_RULE_DUPLICATE_OR_AMBIGUOUS", "SEM_EVENT_TOKEN_UNMAPPED",
            "SEM_RISK_TOKEN_UNMAPPED", "SEM_SEVERITY_TOKEN_UNMAPPED",
            "SEM_SEVERITY_CONFLICT", "SEM_AUTHORITY_HASH_MISMATCH", "SEM_AUTHORITY_MISMATCH",
            "SEM_MANIFEST_HASH_MISMATCH",
        ],
    }


def build_source_matrix(source_registry: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "medical-monitoring-r5-s5-semantic-source-matrix-delta-v0.1",
        "contract_id": CONTRACT_ID,
        "rows": [
            {"row_id": "SRC-001", "source_type_path": "mm_r1.domain.TemporalEvent", "owner_field": "event_id", "semantic_fields": ["event_type", "phase"], "role": "raw event token authority through frozen typed source registry"},
            {"row_id": "SRC-002", "source_type_path": "mm_r1.domain.RiskCandidate", "owner_field": "candidate_id", "semantic_fields": ["risk_type", "severity"], "role": "raw risk and severity token authority through frozen typed source registry"},
            {"row_id": "SRC-003", "source_type_path": "mm_r2.risk.RiskCandidate", "owner_field": "candidate_id", "semantic_fields": ["signal_type", "severity_hint"], "role": "typed compatible future source, not present synthetic records"},
            {"row_id": "SRC-004", "source_type_path": "mm_r1.domain.RiskInstance", "owner_field": "instance_id", "semantic_fields": ["current_severity"], "role": "typed compatible future severity source"},
            {"row_id": "SRC-005", "source_type_path": "mm_r2.risk.RiskInstance", "owner_field": "risk_instance_id", "semantic_fields": ["severity", "clinical_risk_flags"], "role": "real SAE/AESI non-promotion input path"},
            {"row_id": "SRC-006", "source_type_path": "mm_r4.aemh.MedicalGrading", "owner_field": None, "semantic_fields": ["intensity", "seriousness_criteria", "monitoring_priority"], "role": "three independent dimensions; not used as invented RiskCandidate flags"},
            {"row_id": "SRC-007", "source_type_path": "S4JourneyTargetIdentity", "owner_field": None, "semantic_fields": list(IDENTITY), "role": "join-only exact eight-field surface; transfers no semantic values"},
            {"row_id": "SRC-008", "source_type_path": "D07DictionaryProjection", "owner_field": None, "semantic_fields": ["display_value"], "role": "negative-only fallback/OTHER; never semantic authority"},
            {"row_id": "SRC-009", "source_type_path": "rejected_public_authority_implementation_snapshot", "owner_field": None, "semantic_fields": [], "role": "negative evidence only"},
        ],
        "synthetic_source_registry_pin": {"registry_id": source_registry["registry_id"], "registry_content_hash": source_registry["registry_content_hash"], "non_clinical": True},
        "forbidden_value_transfer": ["S4 identity fields as semantic labels", "D07 fallback labels", "rejected implementation snapshot mappings"],
    }


def build_parent_pins() -> tuple[dict[str, str], dict[str, Any]]:
    parent_path = ROOT / PARENT_MANIFEST_PATH
    if raw_sha(parent_path) != PARENT_MANIFEST_SHA256:
        raise RuntimeError("accepted parent manifest drift")
    parent = json.loads(parent_path.read_text(encoding="utf-8"))
    pins = dict(parent["protected_accepted_pins"]["protected_path_sha256"])
    pins.update(parent["artifact_raw_sha256"])
    pins[PARENT_MANIFEST_PATH] = PARENT_MANIFEST_SHA256
    pins[PARENT_ACCEPTANCE_PATH] = PARENT_ACCEPTANCE_SHA256
    return dict(sorted(pins.items())), parent["protected_accepted_pins"]


def build_context(acceptance: dict[str, Any], source: dict[str, Any], challenge_count: int) -> str:
    records = "\n".join(
        f"- `{x['accepted_record_ref']}` / accepted-record SHA-256 `{x['accepted_record_content_hash']}` / package SHA-256 `{x['package_content_hash']}`"
        for x in acceptance["records"]
    )
    return f"""# R5-S5 semantic authority delta context (2026-08-20)

## Goal and boundary

This append-only delta freezes deterministic semantic authority shapes and adversarial probes without changing the accepted parent, any producer/runtime/S5/UI surface, or port 8911. It does not create clinical authority and does not self-accept.

## External synthetic authority pins

The candidate `SemanticPolicyAcceptanceReceipt` is not authority. It must resolve through exact `registry_id + registry_content_hash + accepted_record_ref + accepted_record_content_hash` to the frozen registry below. A changed package and fully resealed receipt still fail when the frozen record remains unchanged. No status string is consulted.

- acceptance registry: `{acceptance['registry_id']}`
- acceptance registry SHA-256: `{acceptance['registry_content_hash']}`
- authority scope: `synthetic_test_only`
- non-clinical: `true`
{records}

The typed source registry is independently pinned as `{source['registry_id']}` / `{source['registry_content_hash']}`. Every raw token or flag evidence object resolves to an exact typed record, owner, record content hash, field, value, source revision, locator and eight-field identity join. Candidate evidence resealing cannot change that record.

## Exact contracts

- S4 join is exactly eight keys: `{', '.join(IDENTITY)}`. Event, visit, source and join hash fields are forbidden.
- event relation is exactly 16 subtypes to 8 domains; every successful event classification has exactly one nonempty match.
- matching policy is only `exact_utf8_v1`; trim, casefold, fuzzy and fallback are forbidden.
- severity is exactly `{', '.join(SEVERITIES)}`; legacy severe/moderate/mild map to high/medium/low.
- SAE/AESI inputs use the real typed path `mm_r2.risk.RiskInstance.clinical_risk_flags` and never promote severity.
- package, rule, receipt, authority, API success/error and every nested object use exact key sets and content hashes.

## Challenge and done evidence

There are {challenge_count} active one-mutation cases. The verifier applies mutations mechanically, validates global packages and external registries, then evaluates semantics without importing the generator and without branching on case id, expected code or expected label. Codex remains the acceptance authority; this worker returns evidence only.
"""


def build_review(acceptance: dict[str, Any], source: dict[str, Any], challenge_count: int) -> str:
    return f"""# R5-S5 public semantic-authority delta v0.1

## Disposition

`IMPLEMENTED_FOR_INDEPENDENT_REVIEW` — not ACCEPTED. This delta is append-only and synthetic/non-clinical.

## Root-cause repair

The previous candidate let a receipt repeat `accepted` and a package hash, which made a fully resealed changed package capable of authorizing itself. Raw token evidence had the same defect: it could change token/owner and recompute its own hash. Nested exact schemas and global coverage were incomplete, the S4 join exceeded eight fields, and SAE/AESI paths were invented on `RiskCandidate`.

This revision pins a frozen synthetic acceptance registry (`{acceptance['registry_content_hash']}`) and a frozen typed-source registry (`{source['registry_content_hash']}`). Receipts and evidence are projections that must independently resolve to those roots. Both registries are `synthetic_test_only`, `non_clinical=true`; clinical acceptance remains outside this delta.

## Contract changes

- all nested schemas deny additional properties, including `ExactRuleComponent` and `SourceRevisionContentPair`;
- exact UTF-8 matching only; severity enum and risk-code regex/content hash are closed;
- global validation enforces 13 exact + 3 compound event rules, the full 16→8 relation, exact-one match, complete taxonomy/lexicon and all legacy severity mappings;
- S4 join has exactly eight fields;
- SAE/AESI non-promotion resolves from `mm_r2.risk.RiskInstance.clinical_risk_flags`;
- {challenge_count} active cases include fully resealed MH→ae, forged Chinese label, catastrophic, receipt extra field, missing legacy, fuzzy, cross-owner raw token and accepted-record mismatch attacks.

## Verification contract

Run the independent verifier normally, under `python3 -O`, with multiple `PYTHONHASHSEED` values, and Ruff. It also verifies parent pins, the 542-file inventory aggregate, negative-only rejected snapshot pins, allow/deny scope, producer absence, port 8911 stopped, deterministic regeneration and stable raw SHA-256. The worker does not produce an acceptance record.
"""


def inventory_aggregate() -> tuple[int, str]:
    paths: list[str] = []
    for root_name in ("deploy", "frontend", "packages", "runtime", "services"):
        base = ROOT / root_name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and ("medical-writing" in path.as_posix().lower() or "medical_writing" in path.as_posix().lower()):
                paths.append(path.relative_to(ROOT).as_posix())
    paths.sort(key=lambda x: x.encode("utf-8"))
    payload = b"".join(p.encode("utf-8") + b"\0" + raw_sha(ROOT / p).encode("ascii") + b"\n" for p in paths)
    return len(paths), hashlib.sha256(payload).hexdigest()


def build_all() -> dict[str, bytes]:
    packages = build_packages()
    source_registry = build_source_registry()
    acceptance_registry = build_acceptance_registry(packages)
    challenges = build_challenges(packages, acceptance_registry, source_registry)
    schema = build_schema()
    source_matrix = build_source_matrix(source_registry)
    parent_pins, accepted = build_parent_pins()
    count, aggregate = inventory_aggregate()
    if count != 542 or aggregate != "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca":
        raise RuntimeError("protected 542-file aggregate drift")
    content: dict[str, bytes] = {
        CONTEXT_PATH: build_context(acceptance_registry, source_registry, len(challenges["cases"])).encode("utf-8"),
        REVIEW_PATH: build_review(acceptance_registry, source_registry, len(challenges["cases"])).encode("utf-8"),
        SCHEMA_PATH: json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n",
        SOURCE_MATRIX_PATH: json.dumps(source_matrix, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n",
        CHALLENGE_PATH: json.dumps(challenges, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n",
    }
    artifact_hashes = {path: hashlib.sha256(data).hexdigest() for path, data in content.items()}
    artifact_hashes[GENERATOR_PATH] = raw_sha(ROOT / GENERATOR_PATH)
    artifact_hashes[VERIFIER_PATH] = raw_sha(ROOT / VERIFIER_PATH)
    manifest = {
        "schema": "medical-monitoring-r5-s5-public-authority-semantic-delta-manifest-v0.1",
        "schema_version": SCHEMA_VERSION, "contract_id": CONTRACT_ID,
        "delta_mode": "append_only_semantic_authority_delta", "rewrites_parent": False,
        "invalidates_parent_acceptance": False, "exact_delta_paths": list(EXACT_DELTA_PATHS),
        "artifact_raw_sha256": dict(sorted(artifact_hashes.items())),
        "protected_parent_pins": parent_pins,
        "protected_aggregate_pins": {"file_count": count, "aggregate_sha256": aggregate,
            "aggregate_recipe": accepted["medical_writing_inventory_contract"]["aggregate_recipe"],
            "roots": accepted["medical_writing_inventory_contract"]["roots"],
            "relative_path_regex": accepted["medical_writing_inventory_contract"]["relative_path_regex"]},
        "rejected_implementation_contract_snapshot_negative_evidence_only": {"authority": False, "pins": NEGATIVE_SNAPSHOT_PINS, "use": "negative evidence only"},
        "synthetic_policy_acceptance_registry": acceptance_registry,
        "synthetic_typed_source_record_registry": source_registry,
        "registry_pins_immutable_under_candidate_reseal": True,
        "challenge_count": len(challenges["cases"]),
        "acceptance_boundary": {"worker_may_accept": False, "clinical_authority_created": False, "independent_verifier_required": True},
        "no_producer_surface": {"forbidden_path_regex": "(^|/)(src|runtime|frontend|services|packages|deploy|poc)/", "allowed_paths": list(EXACT_DELTA_PATHS)},
        "port_8911_must_be_stopped": True, "python_assert_statements_allowed": False,
        "manifest_hash_recipe": "sha256(canonical_json(all exact fields except manifest_content_hash))",
    }
    manifest = seal(manifest, "manifest_content_hash")
    content[MANIFEST_PATH] = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    return content


def write_or_check(check: bool) -> int:
    content = build_all()
    mismatches: list[str] = []
    for relative, data in content.items():
        path = ROOT / relative
        if check:
            if not path.exists() or path.read_bytes() != data:
                mismatches.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if mismatches:
        print("generated artifact drift:")
        for item in mismatches:
            print(f"- {item}")
        return 1
    print(("checked" if check else "generated") + f" {len(content)} delta artifacts")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    return write_or_check(parser.parse_args().check)


if __name__ == "__main__":
    raise SystemExit(main())
