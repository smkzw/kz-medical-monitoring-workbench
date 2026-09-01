#!/usr/bin/env python3
"""Generate the renderer-neutral R5-S5 Subject Workspace contract.

This generator is intentionally contract-only.  It reads pinned accepted R5
and public-authority inputs, emits the seven worker-01 artifacts, and never
imports or executes a producer/runtime module.  Public packets are the only
authority for temporal and AEMH leaves; fixture text, counts, case ids,
filenames, nearest records and client state are never authority inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import unicodedata
from typing import Any


sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_ID = "medical-monitoring-r5-s5-subject-workspace-contract-v0.1"
SCHEMA_VERSION = "2026-08-26.1"
ACCEPTANCE_TOKEN = "ACCEPT_R5_S5_CONTRACT"

ARTIFACT_DIR = pathlib.Path("artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1")
CONTEXT_REL = pathlib.Path(
    "context/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_20260826_context.md"
)
REVIEW_REL = pathlib.Path("reviews/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_20260826.md")
GENERATOR_REL = pathlib.Path("tools/generate_medical_monitoring_r5_s5_subject_workspace_contract_v0_1.py")
VERIFIER_REL = pathlib.Path("tools/verify_medical_monitoring_r5_s5_subject_workspace_contract_v0_1.py")
PARENT_CONTRACT_ID = "medical-monitoring-r5-exact-contract-v0.3.1"
PARENT_SOURCE_ROOT_TYPE = "R5ExactContract"
STAGE_CONTRACT_ID = "accepted-r5-stage-contract-v0.3"
STAGE_SOURCE_ROOT_TYPE = "AcceptedR5StageContract"

EXACT_REL = ARTIFACT_DIR / "exact_contract.json"
MATRIX_REL = ARTIFACT_DIR / "source_leaf_matrix.json"
CHALLENGE_REL = ARTIFACT_DIR / "challenge_registry.json"
MANIFEST_REL = ARTIFACT_DIR / "manifest.json"

OWNED_REL = (CONTEXT_REL, REVIEW_REL, EXACT_REL, MATRIX_REL, CHALLENGE_REL, MANIFEST_REL, GENERATOR_REL)
EXPECTED_REL = (*OWNED_REL, VERIFIER_REL)

PARENT_EXACT_REL = pathlib.Path("artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json")
PARENT_CHALLENGE_REL = pathlib.Path("artifacts/medical_monitoring_r5_contract_v0_3/challenge_registry.json")
PARENT_QUOTA_REL = pathlib.Path("artifacts/medical_monitoring_r5_contract_v0_3/quota_ledger.json")
SUBJECT_SCHEMA_REL = pathlib.Path(
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json"
)
AEMH_SCHEMA_REL = pathlib.Path(
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json"
)
TEMPORAL_SCHEMA_REL = pathlib.Path(
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/schema.json"
)
TEMPORAL_RECIPES_REL = pathlib.Path(
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/emitter_recipe_registry.json"
)
TEMPORAL_FIXTURES_REL = pathlib.Path(
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json"
)
TYPED_AUTHORITY_REL = pathlib.Path(
    "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1/authority_contract.json"
)
TYPED_MANIFEST_REL = pathlib.Path(
    "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1/manifest.json"
)
PUBLIC_IMPL_MANIFEST_REL = pathlib.Path(
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2/manifest.json"
)
PUBLIC_IMPL_FUTURE_REL = pathlib.Path(
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2/future_producer_contract.json"
)
PUBLIC_EVIDENCE_REL = pathlib.Path(
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_public_authority_readonly_sha256.json"
)
STAGE_REL = pathlib.Path("reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md")

UPSTREAM_PINS = {
    "context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md":
        "2868e1977250532e6bc51fc426f224e4f28b8556cf8ce9ad5d8a0392ccb404a8",
    "reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md":
        "1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6",
    "context/medical_monitoring_r5_s4_acceptance_record_20260819.md":
        "1d17297c44b371aefecf28cfc2388181b7be35d9e5cc830b148a0b3a9da1971e",
    "context/medical_monitoring_r5_s5_public_authority_producers_v0_1_acceptance_record_20260826.md":
        "76ec09525bc37a3efc4112bae5b5d1e11b9b9fc46a0b9c04c5a19ba0902364c2",
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2_acceptance_record_20260825.md":
        "d6d9b4dad6a8b9c8501d6c8ccfcd71cf1f3f682b40be3ecd3cf10efea7364981",
    "context/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1_acceptance_record_20260825.md":
        "b509de3edb6111da19977cc8aa7741160aa04366dbd5565bb746fe633ffd46e6",
    "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2_acceptance_record_20260821.md":
        "d08b4ed27f9829db4cdcab0837f3623c244ee8c888cce699c55580621bd68ef4",
    "context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md":
        "23fed5b186057a79cd0ec43a7718e43934ebafdc8f62fd251077d4fb6891639d",
    "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json":
        "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949",
    "artifacts/medical_monitoring_r5_contract_v0_3/challenge_registry.json":
        "ef459f58ad6997a823c3ff57d51256cdf531b806d9033df636ab2912085b0887",
    "artifacts/medical_monitoring_r5_contract_v0_3/quota_ledger.json":
        "aeec1482b1c374d175a89660dd11cc312b6ba2612cf6c5a709379f2b05163b37",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json":
        "92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json":
        "d2f56f21dc7b228736b2efbdc4c1db3a28185e25895563c0b59a812cd126a0f4",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json":
        "479dc2759833d698fd761247f4ec504069880717ec9c64631242ad2554b19840",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/manifest.json":
        "466b0ae605b83a57f0e184446db311beb05ff5e4e1998a7dc5be9bb44d2b7de8",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/schema.json":
        "74617b858f961f3af615b3d96a51625427faeecfac8c5a4011ecac4fd79dabbc",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/emitter_recipe_registry.json":
        "e7a8d5246d71e7b2baece0d21909518426da6d3799bfd6913d4fefa81729bf39",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json":
        "f9bf0c8031d3acba615b5ac147c27866c8a7430154a0bb98fc24314619009ae7",
    "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1/authority_contract.json":
        "bc0c60db30721401315605f69b1d6e3c0e26b39161ea3135f1fcc547828c09cc",
    "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1/manifest.json":
        "a71f0937dd5d0a0fc77de98b41f6308b5caed0ae7d460f0282884c56127cd22c",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2/manifest.json":
        "f3fcb4172dd74d9c8c1fff16fbda1a516caf41447d08b6c5637fde0fd403ecc8",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2/future_producer_contract.json":
        "09ead56dc8989c469fc9aa4912c40e0c9bf8e896063a340b2dd209a851571124",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_public_authority_readonly_sha256.json":
        "8a0d0935a21e569cef078a08ff084367aa401c2e188f50d9ada7e77c9b734058",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s4_readonly_sha256.json":
        "53a927a08451b426edb9ac9578a6ea3b658ff8df1d5dd2b33f94fb0446647822",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_readonly_sha256.json":
        "d5fe8b44edaf86f8a5aa611cc23011526479c87d24c47efd347e6b20525b6d89",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_s2_readonly_sha256.json":
        "6cec5b39fe325bf644e2ae31174a5175b2ad94e190d98cb43b00b33636ff21af",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_s3_readonly_sha256.json":
        "f217f66a0ffbeb5e5b37d85e056aad6c218d1979e023e4a55dc13b33354e3a77",
}

ACCEPTED_PUBLIC_AUTHORITY_PINS = {
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py":
        "4767e28ab7e54a4fbc89e3e30a12448467597cdadfc06833f11158bc2aa54b4c",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py":
        "0a519d6b93dee9bc06930707eed7f6b7f2be180fe2b35dc25d23ccf8ce918be7",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py":
        "3463eedf0bad35596f9b1f28c9479c76fb0cffaf5977766e812839e342bd3243",
    "poc/medical_monitoring_ai_native_r5/tests/public_authority_runtime_fixtures.py":
        "a4b9a2d681ca280ea344d36591eb7875e032dcf7e4b9209be34ba7bf5972c794",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py":
        "eeffbcf0c07c130e3cb05f3ac19ba3f2698de6461344812c18c1c083234b0aa3",
    "poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py":
        "2aa3b626cfd0feda9a70a7416f564955a9c7378e66e26a8c2b2682bd9a20bb8c",
    "poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py":
        "c8b3afefc49d3fc62eecf072f23b7a82d9bab2c5ae35852f482a19b9b618702d",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py":
        "15a3de48c22e7417dd0b1159f5d696d90730c080856b3dda04a8ea552ef99e64",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_readonly_gate.py":
        "e5c9cdb5ff9989b1e8057a1624c618a4cdc93715275f3fd51a992ae395ef6299",
    "poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py":
        "f6bee54e92820e48cd8a3b3111261308e639a3f61609b1c4b24073f8ef6e61b2",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_public_authority_readonly_sha256.json":
        "8a0d0935a21e569cef078a08ff084367aa401c2e188f50d9ada7e77c9b734058",
}

RUNTIME_SURFACE_ROOTS = (
    "poc/medical_monitoring_ai_native_r5/src/mm_r5",
    "poc/medical_monitoring_ai_native_r5/tests",
    "poc/medical_monitoring_ai_native_r5/evidence",
)
RUNTIME_SURFACE_BASELINE_HASH = "d94c9e7203572519f9db92c219d4f18a9b76fdd3af0fd8a60b98b85120ecb915"
RUNTIME_SURFACE_IGNORED_CACHE_RULES = ("*/__pycache__/*", "*.pyc", "*.pyo")

FUTURE_RUNTIME_ALLOWLIST = (
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_contracts.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_authority_adapter.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_projection.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_validator.py",
    "poc/medical_monitoring_ai_native_r5/tests/s5_runtime_fixtures.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_contracts.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_authority_adapter.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_projection.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_validator.py",
    "poc/medical_monitoring_ai_native_r5/tests/challenges/test_s5_runtime_challenges.py",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_subject_workspace_readonly_sha256.json",
)

PRODUCER_VALIDATORS = {
    "subject-temporal-public-v1": (
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py:"
        "build_subject_temporal_authority",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py:"
        "validate_subject_temporal_authority",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py:authority_issues",
    ),
    "aemh-match-history-public-v1": (
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py:"
        "build_aemh_match_history_authority",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py:"
        "validate_aemh_match_history_authority",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py:authority_issues",
    ),
}

DOMAINS = (
    "ae",
    "mh",
    "cm",
    "ip",
    "lab_exam",
    "hospital_procedure",
    "symptom_efficacy",
    "protocol_compliance",
)

DOMAIN_ENCODING = (
    {"domain": "ae", "short_label_zh": "AE", "event_shape": "rounded_rect", "line_style": "solid"},
    {"domain": "mh", "short_label_zh": "MH", "event_shape": "bookmark", "line_style": "dot_dash"},
    {"domain": "cm", "short_label_zh": "合并用药", "event_shape": "capsule", "line_style": "solid"},
    {"domain": "ip", "short_label_zh": "试验药", "event_shape": "hexagon", "line_style": "step"},
    {"domain": "lab_exam", "short_label_zh": "检验/检查", "event_shape": "square", "line_style": "trend"},
    {"domain": "hospital_procedure", "short_label_zh": "住院/操作", "event_shape": "doorframe", "line_style": "solid"},
    {"domain": "symptom_efficacy", "short_label_zh": "症状/疗效", "event_shape": "circle", "line_style": "trend"},
    {"domain": "protocol_compliance", "short_label_zh": "方案符合", "event_shape": "single_flag", "line_style": "bracket"},
)

SEVERITY_ENCODING = (
    {"severity": "critical", "label_zh": "紧急", "line_weight": None},
    {"severity": "high", "label_zh": "高", "line_weight": None},
    {"severity": "medium", "label_zh": "中", "line_weight": None},
    {"severity": "low", "label_zh": "低", "line_weight": None},
)

FORBIDDEN_TERMS = (
    "已记录事项",
    "正式事实",
    "候选信号",
    "通用风险点",
    "只读xx",
    "Checklist",
    "待行动",
    "未读",
)

SYMPTOM_EFFICACY_SUBTYPES = ("symptom", "efficacy", "scale", "outcome", "trend")
DOMAIN_SUBTYPE_MATRIX = {
    "ae": ("ae",),
    "mh": ("mh",),
    "cm": ("concomitant_medication",),
    "ip": ("ip_dose", "ip_pause", "ip_resume"),
    "lab_exam": ("lab", "exam"),
    "hospital_procedure": ("hospitalization", "procedure"),
    "symptom_efficacy": SYMPTOM_EFFICACY_SUBTYPES,
    "protocol_compliance": ("protocol_deviation",),
}
LEGACY_SEVERITY_MAPPING = (
    {"legacy_value": "severe", "severity": "high"},
    {"legacy_value": "moderate", "severity": "medium"},
    {"legacy_value": "mild", "severity": "low"},
)
UNKNOWN_LEGACY_SEVERITY_POLICY = "fail_closed"
LEGACY_TREATMENT_MAPPING = (
    {
        "legacy_kind": "background_treatment",
        "mapping_state": "unmapped_fail_closed",
        "mapping_authority_ref": None,
        "target_domain": None,
        "target_subtype": None,
    },
    {
        "legacy_kind": "non_drug_treatment",
        "mapping_state": "unmapped_fail_closed",
        "mapping_authority_ref": None,
        "target_domain": None,
        "target_subtype": None,
    },
)
RISK_OVERLAY_SHAPE = "double_chevron_badge"
EVENT_FORBIDDEN_SHAPES = ("double_chevron_badge",)
JOURNEY_SUBTYPES = (
    "ae",
    "mh",
    "concomitant_medication",
    "ip_dose",
    "ip_pause",
    "ip_resume",
    "lab",
    "exam",
    "hospitalization",
    "procedure",
    "symptom",
    "efficacy",
    "scale",
    "outcome",
    "trend",
    "protocol_deviation",
)

COMMON_FORBIDDEN_AUTHORITY_SOURCES = (
    "fixture_text",
    "fixture_count",
    "case_id",
    "filename",
    "unbound_hash",
    "nearest_record",
    "ui_state",
    "candidate_output",
)

STAGE_DOMAIN_LABELS = {
    "AE": "ae",
    "MH": "mh",
    "CM": "cm",
    "IP 给药": "ip",
    "检验与检查": "lab_exam",
    "住院与操作": "hospital_procedure",
    "症状与疗效": "symptom_efficacy",
    "方案符合性": "protocol_compliance",
}
STAGE_SHAPE_TOKENS = (
    ("圆角矩形", "rounded_rect"),
    ("书签形", "bookmark"),
    ("胶囊形", "capsule"),
    ("六边形", "hexagon"),
    ("方形", "square"),
    ("门框形", "doorframe"),
    ("圆点", "circle"),
    ("旗标形", "single_flag"),
)
STAGE_LINE_TOKENS = (
    ("阶梯线", "step"),
    ("括号区间", "bracket"),
    ("趋势线", "trend"),
    ("折线", "trend"),
    ("粗区间", "solid"),
    ("细实线", "solid"),
    ("点划", "dot_dash"),
    ("实线", "solid"),
)
SUBTYPE_STAGE_TOKENS = {
    "ae": "AE",
    "mh": "MH",
    "concomitant_medication": "合并用药",
    "ip_dose": "给药",
    "ip_pause": "暂停",
    "ip_resume": "恢复",
    "lab": "检验",
    "exam": "检查",
    "hospitalization": "住院",
    "procedure": "操作",
    "protocol_deviation": "方案符合",
}
STAGE_SYMPTOM_SUBTYPE_LABELS = {
    "症状": "symptom",
    "疗效": "efficacy",
    "量表": "scale",
    "结局": "outcome",
    "趋势": "trend",
}


def json_pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def s5_mutation_definition(target: str) -> dict[str, Any]:
    zero_hash = "0" * 64
    definitions = {
        "parent_exact_contract": {
            "op": "replace",
            "path": f"/manifest/input_raw_sha256/{json_pointer_token(PARENT_EXACT_REL.as_posix())}",
            "value": zero_hash,
            "valid_value": UPSTREAM_PINS[PARENT_EXACT_REL.as_posix()],
        },
        "public_producer_module": {
            "op": "replace",
            "path": f"/manifest/input_raw_sha256/{json_pointer_token('poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py')}",
            "value": zero_hash,
            "valid_value": ACCEPTED_PUBLIC_AUTHORITY_PINS["poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py"],
        },
        "public_producer_test": {
            "op": "replace",
            "path": f"/manifest/input_raw_sha256/{json_pointer_token('poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py')}",
            "value": zero_hash,
            "valid_value": ACCEPTED_PUBLIC_AUTHORITY_PINS["poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py"],
        },
        "candidate_packet_as_authority": {"op": "replace", "path": "/authority_model/serialized_input_authority", "value": "candidate_packet", "valid_value": "AuthorityBundleV02"},
        "missing_receipt_binding": {"op": "replace", "path": "/receipt/receipt_id", "value": "unbound-receipt", "valid_value": "bound-receipt"},
        "projection_hash": {"op": "replace", "path": "/receipt/public_projection_content_hash", "value": zero_hash, "valid_value": "accepted-projection-content-hash"},
        "scope_subject_ref": {"op": "replace", "path": "/receipt/scope_identity/subject_ref", "value": "subject-cross-scope", "valid_value": "subject-bound"},
        "scope_spine_ref": {"op": "replace", "path": "/receipt/scope_identity/spine_ref", "value": "spine-cross-scope", "valid_value": "spine-bound"},
        "date_state_exact_without_date": {"op": "replace", "path": "/projection/events/0/start_endpoint/state", "value": "exact", "valid_value": "partial"},
        "partial_date_range_dropped": {"op": "remove", "path": "/projection/events/0/start_endpoint/range_start", "value": "2026-01-01", "valid_value": "2026-01-02"},
        "conflicted_date_collapsed": {"op": "replace", "path": "/projection/events/0/start_endpoint/state", "value": "partial", "valid_value": "conflicted"},
        "missing_date_fabricated": {"op": "replace", "path": "/projection/events/0/start_endpoint/exact_date", "value": "2026-01-01", "valid_value": None},
        "visit_event_absorption": {"op": "replace", "path": "/projection/events/0/event_ref", "value": "visit-0", "valid_value": "event-0"},
        "second_spine": {"op": "replace", "path": "/projection/scope_identity/spine_ref", "value": "spine-second", "valid_value": "spine-bound"},
        "unknown_domain_to_other": {"op": "replace", "path": "/projection/events/0/domain", "value": "OTHER", "valid_value": "ae"},
        "eight_domain_duplicate": {"op": "replace", "path": "/audience_constants/domains_exactly_eight/7/domain", "value": "ae", "valid_value": "protocol_compliance"},
        "symptom_efficacy_second_shape": {"op": "replace", "path": "/audience_constants/domains_exactly_eight/6/event_shape", "value": "triangle", "valid_value": "circle"},
        "not_applicable_to_not_provided": {"op": "replace", "path": "/projection/domain_tracks/0/applicability_state", "value": "not_provided", "valid_value": "not_applicable"},
        "risk_overlay_as_event_shape": {"op": "replace", "path": "/audience_constants/domains_exactly_eight/0/event_shape", "value": "double_chevron_badge", "valid_value": "rounded_rect"},
        "high_promoted_to_critical": {"op": "replace", "path": "/audience_constants/severity_exactly_four/1/severity", "value": "critical", "valid_value": "high"},
        "legacy_severity_unmapped": {"op": "replace", "path": "/audience_constants/legacy_severity_mapping/0/legacy_value", "value": "unknown", "valid_value": "severe"},
        "forbidden_audience_term": {"op": "replace", "path": "/audience_constants/forbidden_terms/0", "value": "已记录事项", "valid_value": "受试者"},
        "background_treatment_without_mapping": {"op": "replace", "path": "/audience_constants/legacy_treatment_mapping/0/mapping_state", "value": "mapped", "valid_value": "unmapped_fail_closed"},
        "non_drug_treatment_without_mapping": {"op": "replace", "path": "/audience_constants/legacy_treatment_mapping/1/mapping_state", "value": "mapped", "valid_value": "unmapped_fail_closed"},
        "original_reminder_deleted": {"op": "remove", "path": "/projection/threads/0/history_entries/0", "value": {"event_kind": "reminder_created"}, "valid_value": {"event_kind": "reminder_created"}},
        "later_fact_identity_rewritten": {"op": "replace", "path": "/projection/threads/0/history_entries/1/later_fact_content_identities/0", "value": zero_hash, "valid_value": "accepted-later-fact-content-hash"},
        "match_decision_auto_closes_risk": {"op": "replace", "path": "/projection/threads/0/history_entries/1/risk_lifecycle_effect", "value": "closed", "valid_value": "none"},
        "previous_prefix_dropped": {"op": "remove", "path": "/projection/accepted_thread_prefixes/0", "value": {"prefix_seq": 0}, "valid_value": {"prefix_seq": 0}},
        "journey_profile_spine_mismatch": {"op": "replace", "path": "/workspace/view_bindings/1/spine_ref", "value": "spine-other", "valid_value": "spine-shared"},
        "profile_timeline_window_mismatch": {"op": "replace", "path": "/workspace/shared_context/window_end", "value": "2099-12-31", "valid_value": "2026-12-31"},
        "selection_anchor_not_member": {"op": "replace", "path": "/workspace/shared_context/selection_anchor/anchor_ref", "value": "event-unbound", "valid_value": "event-member"},
        "ui_state_rewrites_authority": {"op": "replace", "path": "/workspace/view_bindings/0/authority_projection_id", "value": "projection-ui", "valid_value": "projection-accepted"},
        "contract_acceptance_starts_8911": {"op": "replace", "path": "/manifest/unlock/does_not_unlock/0", "value": "allow-8911", "valid_value": "8911"},
        "contract_acceptance_allows_real_project": {"op": "replace", "path": "/manifest/unlock/does_not_unlock/2", "value": "allow-real-project", "valid_value": "real projects or models"},
        "contract_acceptance_allows_product": {"op": "replace", "path": "/manifest/unlock/does_not_unlock/3", "value": "allow-product", "valid_value": "product or production"},
        "contract_acceptance_allows_medical_writing": {"op": "replace", "path": "/manifest/unlock/does_not_unlock/4", "value": "allow-medical-writing", "valid_value": "medical-writing"},
    }
    if target not in definitions:
        raise SystemExit(f"STOP missing executable S5 mutation definition: {target}")
    mutation = dict(definitions[target])
    if isinstance(mutation["value"], str) and mutation["value"] in {f"mutated::{target}", f"valid::{target}"}:
        raise SystemExit(f"STOP placeholder S5 mutation definition: {target}")
    return mutation


def canonicalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", str(key)): canonicalize(item) for key, item in value.items()}
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def load_json(rel: pathlib.Path) -> Any:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def resolve_json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "/":
        return document
    if not pointer.startswith("/"):
        raise SystemExit(f"STOP invalid JSON pointer: {pointer}")
    current = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        try:
            if isinstance(current, list):
                current = current[int(token)]
            elif isinstance(current, dict):
                current = current[token]
            else:
                raise KeyError(token)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise SystemExit(f"STOP unresolved accepted JSON pointer: {pointer}") from exc
    return current


def runtime_surface_snapshot() -> dict[str, Any]:
    files: dict[str, str] = {}
    for root_rel in RUNTIME_SURFACE_ROOTS:
        base = ROOT / root_rel
        if not base.is_dir():
            raise SystemExit(f"STOP missing runtime surface root: {root_rel}")
        for path in sorted(base.rglob("*")):
            relative = path.relative_to(ROOT).as_posix()
            if path.is_symlink():
                raise SystemExit(f"STOP symlink in runtime surface: {relative}")
            if not path.is_file():
                continue
            if "/__pycache__/" in f"/{relative}/" or relative.endswith((".pyc", ".pyo")):
                continue
            files[relative] = raw_sha(path)
    observed_hash = digest(files)
    if observed_hash != RUNTIME_SURFACE_BASELINE_HASH:
        raise SystemExit(
            "STOP runtime surface drift: "
            f"expected={RUNTIME_SURFACE_BASELINE_HASH} observed={observed_hash}"
        )
    present_allowlist = [relative for relative in FUTURE_RUNTIME_ALLOWLIST if (ROOT / relative).exists()]
    if present_allowlist:
        raise SystemExit(f"STOP future S5 runtime surface present: {present_allowlist}")
    return {
        "mode": "exact_frozen_non_cache_file_inventory",
        "roots": list(RUNTIME_SURFACE_ROOTS),
        "ignored_cache_rules": list(RUNTIME_SURFACE_IGNORED_CACHE_RULES),
        "frozen_file_count": len(files),
        "frozen_file_raw_sha256": dict(sorted(files.items())),
        "frozen_inventory_content_hash": observed_hash,
        "future_allowlist_absence_required": True,
        "unexpected_new_path_policy": "fail_closed_before_generation",
    }


def pin_inputs() -> dict[str, Any]:
    actual = {}
    for rel, expected in sorted(UPSTREAM_PINS.items()):
        path = ROOT / rel
        if not path.exists():
            raise SystemExit(f"STOP missing accepted input: {rel}")
        observed = raw_sha(path)
        if observed != expected:
            raise SystemExit(f"STOP accepted input pin drift: {rel}:{observed}")
        actual[rel] = observed

    evidence = load_json(PUBLIC_EVIDENCE_REL)
    if evidence.get("schema") != "medical-monitoring-r5-s5-public-authority-readonly-sha256-evidence-v1":
        raise SystemExit("STOP public-authority evidence schema")
    evidence_files = dict(sorted(evidence["files"].items()))
    for rel, expected in evidence_files.items():
        observed = raw_sha(ROOT / rel)
        if observed != expected:
            raise SystemExit(f"STOP public-authority source pin drift: {rel}:{observed}")
        actual[rel] = observed

    for rel, expected in sorted(ACCEPTED_PUBLIC_AUTHORITY_PINS.items()):
        path = ROOT / rel
        if not path.exists():
            raise SystemExit(f"STOP missing accepted public-authority producer path: {rel}")
        observed = raw_sha(path)
        if observed != expected:
            raise SystemExit(f"STOP accepted public-authority producer pin drift: {rel}:{observed}")
        actual[rel] = observed

    return {
        "raw_sha256": dict(sorted(actual.items())),
        "public_evidence_files": evidence_files,
        "public_evidence_protected_boundaries": evidence["protected_boundaries"],
        "accepted_public_authority_pins": dict(sorted(ACCEPTED_PUBLIC_AUTHORITY_PINS.items())),
        "runtime_surface_scan": runtime_surface_snapshot(),
    }


def field(type_name: str, cardinality: str = "one", nullable: bool = False) -> dict[str, Any]:
    return {"cardinality": cardinality, "nullable": nullable, "type": type_name}


def type_name(value: str, object_map: dict[str, str] | None = None) -> str:
    object_map = object_map or {}
    if value in object_map:
        return object_map[value]
    return {
        "string": "str",
        "boolean": "bool",
        "integer": "int",
    }.get(value, value)


def clone_object(source: dict[str, Any], name: str, object_map: dict[str, str]) -> dict[str, Any]:
    return {
        key: field(type_name(spec["type"], object_map), spec["cardinality"], spec["nullable"])
        for key, spec in source["objects"][name].items()
    }


def build_objects(subject_schema: dict[str, Any], aemh_schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    subject_map = {
        "PublicAuthorityReceipt": "S5AuthorityReceipt",
        "PublicCutoffEndpoint": "S5CutoffEndpoint",
        "PublicScopeIdentity": "S5ScopeIdentity",
        "PublicSourceLocator": "S5SourceLocator",
        "SourceRevisionContentPair": "S5SourceRevisionContentPair",
        "VisibilityClosure": "S5VisibilityClosure",
        "TemporalAxisBasis": "S5AxisBasis",
        "TemporalDateEndpoint": "S5DateEndpoint",
        "TemporalDomainTrack": "S5DomainTrack",
        "TemporalEvent": "S5JourneyEvent",
        "TemporalMembershipIndex": "S5MembershipIndex",
        "TemporalPendingDateItem": "S5PendingDateItem",
        "TemporalPhaseBand": "S5PhaseBand",
        "TemporalRiskAnchor": "S5RiskAnchor",
        "TemporalVisit": "S5VisitNode",
        "SubjectTemporalAuthorityPacket": "S5SubjectTemporalPacket",
        "SubjectTemporalPublicProjection": "S5SubjectTemporalProjection",
    }
    aemh_map = {
        "PublicAuthorityReceipt": "S5AuthorityReceipt",
        "PublicCutoffEndpoint": "S5CutoffEndpoint",
        "PublicScopeIdentity": "S5ScopeIdentity",
        "PublicSourceLocator": "S5SourceLocator",
        "SourceRevisionContentPair": "S5SourceRevisionContentPair",
        "VisibilityClosure": "S5VisibilityClosure",
        "AEMHHistoryMembershipIndex": "S5AEMHMembershipIndex",
        "AEMHIdentityEvidence": "S5AEMHIdentityEvidence",
        "AEMHMatchHistoryEntry": "S5AEMHHistoryEntry",
        "AEMHThreadPrefixAnchor": "S5AEMHPrefixAnchor",
        "AEMHMatchThread": "S5AEMHThread",
        "AEMHMatchHistoryPublicProjection": "S5AEMHProjection",
        "AEMHMatchHistoryAuthorityPacket": "S5AEMHPacket",
    }
    objects: dict[str, dict[str, Any]] = {}
    for source_name, target_name in subject_map.items():
        objects[target_name] = clone_object(subject_schema, source_name, subject_map)
    for source_name, target_name in aemh_map.items():
        objects[target_name] = clone_object(aemh_schema, source_name, aemh_map)

    objects.update(
        {
            "S5SelectionAnchor": {
                "anchor_kind": field("enum:s5_anchor_kind"),
                "anchor_ref": field("str", nullable=True),
                "source_locator_ref": field("str", nullable=True),
                "content_hash": field("sha256"),
            },
            "S5SharedTemporalContext": {
                "context_ref": field("str"),
                "authority_receipt_ref": field("str"),
                "spine_ref": field("str"),
                "axis_mode": field("enum:axis_mode"),
                "window_start": field("date", nullable=True),
                "window_end": field("date", nullable=True),
                "selection_anchor": field("S5SelectionAnchor"),
                "selected_event_ref": field("str", nullable=True),
                "selected_risk_anchor_ref": field("str", nullable=True),
                "selected_visit_ref": field("str", nullable=True),
                "content_hash": field("sha256"),
            },
            "S5ViewBinding": {
                "view": field("enum:s5_view"),
                "shared_context_ref": field("str"),
                "spine_ref": field("str"),
                "authority_projection_id": field("str"),
                "anchor_ref": field("str", nullable=True),
                "content_hash": field("sha256"),
            },
            "S5SubjectWorkspaceContract": {
                "subject_ref": field("str"),
                "spine_ref": field("str"),
                "authority_receipt_refs": field("str", "many"),
                "shared_context": field("S5SharedTemporalContext"),
                "view_bindings": field("S5ViewBinding", "many"),
                "content_hash": field("sha256"),
            },
            "S5DomainEncodingItem": {
                "domain": field("enum:domain"),
                "short_label_zh": field("str"),
                "event_shape": field("enum:event_shape"),
                "line_style": field("enum:line_style"),
            },
            "S5SeverityEncoding": {
                "severity": field("enum:severity"),
                "label_zh": field("str"),
                "line_weight": field("int", nullable=True),
            },
            "S5LegacyTreatmentMapping": {
                "legacy_kind": field("enum:legacy_treatment_kind"),
                "mapping_state": field("enum:legacy_mapping_state"),
                "mapping_authority_ref": field("str", nullable=True),
                "target_domain": field("enum:domain", nullable=True),
                "target_subtype": field("enum:journey_subtype", nullable=True),
            },
            "S5AudienceLexicon": {
                "content_hash": field("sha256"),
                "forbidden_terms": field("str", "many"),
                "domain_items": field("S5DomainEncodingItem", "many"),
                "severity_items": field("S5SeverityEncoding", "many"),
                "symptom_efficacy_subtypes": field("enum:symptom_efficacy_subtype", "many"),
            },
            "S5AudienceEncodingRegistry": {
                "domain_items": field("S5DomainEncodingItem", "many"),
                "severity_items": field("S5SeverityEncoding", "many"),
                "risk_overlay_shape": field("str"),
                "symptom_efficacy_subtypes": field("enum:symptom_efficacy_subtype", "many"),
                "legacy_treatment_mapping": field("S5LegacyTreatmentMapping", "many"),
            },
        }
    )
    return objects


CORE_OBJECTS = {
    "S5AuthorityReceipt",
    "S5CutoffEndpoint",
    "S5ScopeIdentity",
    "S5SourceLocator",
    "S5SourceRevisionContentPair",
    "S5VisibilityClosure",
    "S5DateEndpoint",
    "S5AxisBasis",
    "S5DomainTrack",
    "S5JourneyEvent",
    "S5MembershipIndex",
    "S5PendingDateItem",
    "S5PhaseBand",
    "S5RiskAnchor",
    "S5VisitNode",
    "S5SubjectTemporalProjection",
    "S5SubjectTemporalPacket",
    "S5AEMHMembershipIndex",
    "S5AEMHIdentityEvidence",
    "S5AEMHHistoryEntry",
    "S5AEMHPrefixAnchor",
    "S5AEMHThread",
    "S5AEMHProjection",
    "S5AEMHPacket",
}

PRESENTATION_OBJECTS = {
    "S5DomainEncodingItem",
    "S5SeverityEncoding",
    "S5LegacyTreatmentMapping",
    "S5AudienceLexicon",
    "S5AudienceEncodingRegistry",
}


def source_pointer(base: str, leaf: str) -> str:
    return ("/" + leaf) if base == "/" else (base + "/" + leaf)


def source_root_type(contract: str, object_name: str) -> str:
    del object_name
    return (
        "SubjectTemporalAuthorityPacket"
        if contract == "subject-temporal-public-v1"
        else "AEMHMatchHistoryAuthorityPacket"
    )


def producer_sources(object_name: str, leaf: str) -> tuple[dict[str, str], ...]:
    common = {
        "S5ScopeIdentity": ("/projection/scope_identity", "PublicScopeIdentity"),
        "S5SourceLocator": ("/projection/source_locators[*]", "PublicSourceLocator"),
        "S5SourceRevisionContentPair": ("/receipt/source_revision_content_pairs[*]", "SourceRevisionContentPair"),
        "S5VisibilityClosure": ("/receipt/visibility_closure", "VisibilityClosure"),
        "S5AuthorityReceipt": ("/receipt", "PublicAuthorityReceipt"),
    }
    date_endpoint_bases = (
        "/projection/axis_basis/cutoff_endpoint",
        "/projection/events[*]/start_endpoint",
        "/projection/events[*]/end_endpoint",
        "/projection/pending_date_items[*]/start_endpoint",
        "/projection/pending_date_items[*]/end_endpoint",
        "/projection/phase_bands[*]/start_endpoint",
        "/projection/phase_bands[*]/end_endpoint",
        "/projection/risk_anchors[*]/start_endpoint",
        "/projection/risk_anchors[*]/end_endpoint",
        "/projection/visits[*]/actual_endpoint",
        "/projection/visits[*]/nominal_endpoint",
    )
    subject = {
        "S5AxisBasis": ("/projection/axis_basis", "TemporalAxisBasis"),
        "S5DomainTrack": ("/projection/domain_tracks[*]", "TemporalDomainTrack"),
        "S5JourneyEvent": ("/projection/events[*]", "TemporalEvent"),
        "S5MembershipIndex": ("/projection/membership_index", "TemporalMembershipIndex"),
        "S5PendingDateItem": ("/projection/pending_date_items[*]", "TemporalPendingDateItem"),
        "S5PhaseBand": ("/projection/phase_bands[*]", "TemporalPhaseBand"),
        "S5RiskAnchor": ("/projection/risk_anchors[*]", "TemporalRiskAnchor"),
        "S5VisitNode": ("/projection/visits[*]", "TemporalVisit"),
        "S5SubjectTemporalProjection": ("/projection", "SubjectTemporalPublicProjection"),
        "S5SubjectTemporalPacket": ("/", "SubjectTemporalAuthorityPacket"),
    }
    aemh = {
        "S5AEMHMembershipIndex": ("/projection/membership_index", "AEMHHistoryMembershipIndex"),
        "S5AEMHIdentityEvidence": (
            "/projection/threads[*]/history_entries[*]/identity_evidence[*]",
            "AEMHIdentityEvidence",
        ),
        "S5AEMHHistoryEntry": ("/projection/threads[*]/history_entries[*]", "AEMHMatchHistoryEntry"),
        "S5AEMHPrefixAnchor": ("/projection/accepted_thread_prefixes[*]", "AEMHThreadPrefixAnchor"),
        "S5AEMHThread": ("/projection/threads[*]", "AEMHMatchThread"),
        "S5AEMHProjection": ("/projection", "AEMHMatchHistoryPublicProjection"),
        "S5AEMHPacket": ("/", "AEMHMatchHistoryAuthorityPacket"),
    }
    if object_name == "S5CutoffEndpoint":
        bases = (("aemh-match-history-public-v1", "/projection/cutoff_endpoint", "PublicCutoffEndpoint"),)
    elif object_name == "S5DateEndpoint":
        bases = tuple(
            ("subject-temporal-public-v1", base, "TemporalDateEndpoint")
            for base in date_endpoint_bases
        )
    elif object_name in common:
        base, source_type = common[object_name]
        bases = (("subject-temporal-public-v1", base, source_type), ("aemh-match-history-public-v1", base, source_type))
    elif object_name in subject:
        base, source_type = subject[object_name]
        bases = (("subject-temporal-public-v1", base, source_type),)
    elif object_name in aemh:
        base, source_type = aemh[object_name]
        bases = (("aemh-match-history-public-v1", base, source_type),)
    else:
        return ()
    return tuple(
        {
            "authority_contract": contract,
            "source_root_type": source_root_type(contract, object_name),
            "source_type": source_type,
            "json_pointer": source_pointer(base, leaf),
        }
        for contract, base, source_type in bases
    )


def producer_leaf_row(object_name: str, leaf: str, spec: dict[str, Any]) -> dict[str, Any]:
    sources = producer_sources(object_name, leaf)
    contracts = sorted({row["authority_contract"] for row in sources})
    validators = sorted({item for contract in contracts for item in PRODUCER_VALIDATORS[contract]})
    hash_leaf = spec["type"] == "sha256" or leaf.endswith("_hash") or leaf.endswith("_identity")
    return {
        "leaf_id": f"{object_name}.{leaf}",
        "target_object": object_name,
        "target_field": leaf,
        "target_spec": spec,
        "core_authority_leaf": object_name in CORE_OBJECTS,
        "authority_plane": "accepted_public_packet",
        "source_kind": "accepted_public_packet_derived" if hash_leaf else "accepted_public_packet_direct",
        "source_contracts": contracts,
        "source_paths": list(sources),
        "validator_refs": validators,
        "identity_recipe": (
            "producer_pinned_canonical_sha256_recipe"
            if hash_leaf
            else "accepted_public_packet_field_with_exact_selector"
        ),
        "forbidden_authority_sources": list(COMMON_FORBIDDEN_AUTHORITY_SOURCES),
        "deferred_contract": None,
        "placeholder": False,
        "self_signed": False,
        "executable": True,
    }


def parent_invariant_pointer(parent: dict[str, Any], invariant_id: str) -> str:
    for index, invariant in enumerate(parent["invariants"]):
        if invariant["invariant_id"] == invariant_id:
            return f"/invariants/{index}"
    raise SystemExit(f"STOP accepted parent invariant missing: {invariant_id}")


def _stage_span(line_number: int, row_key: str, line_text: str) -> dict[str, Any]:
    return {
        "line_start": line_number,
        "line_end": line_number,
        "row_key": row_key,
        "line_text": line_text,
    }


def _clean_markdown_cell(value: str) -> str:
    return value.strip().replace("`", "")


def _stage_table_rows(stage_text: str) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(stage_text.splitlines(), 1):
        if not line.lstrip().startswith("|"):
            continue
        cells = [_clean_markdown_cell(cell) for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] not in STAGE_DOMAIN_LABELS:
            continue
        domain = STAGE_DOMAIN_LABELS[cells[0]]
        shape_matches = [value for token, value in STAGE_SHAPE_TOKENS if token in cells[2]]
        line_matches = [value for token, value in STAGE_LINE_TOKENS if token in cells[2]]
        if len(set(shape_matches)) != 1 or len(set(line_matches)) != 1:
            raise SystemExit(f"STOP stage domain row encoding is not singular: {cells[0]}")
        rows.append(
            {
                "domain": domain,
                "stage_label": cells[0],
                "short_label_zh": cells[1],
                "event_shape": shape_matches[0],
                "line_style": line_matches[0],
                "cells": cells,
                "source_span": _stage_span(line_number, domain, line),
            }
        )
    if len(rows) != len(STAGE_DOMAIN_LABELS) or {row["domain"] for row in rows} != set(STAGE_DOMAIN_LABELS.values()):
        raise SystemExit("STOP accepted stage domain table is incomplete or duplicated")
    return tuple(rows)


def _stage_line(stage_text: str, predicate: Any, row_key: str) -> dict[str, Any]:
    for line_number, line in enumerate(stage_text.splitlines(), 1):
        if predicate(line):
            return {"line": line, "source_span": _stage_span(line_number, row_key, line)}
    raise SystemExit(f"STOP accepted stage source span missing: {row_key}")


def _legacy_severity_from_parent(parent: dict[str, Any]) -> tuple[tuple[dict[str, str], ...], str]:
    invariant = next(
        (item for item in parent["invariants"] if item["invariant_id"] == "legacy_severity_mapping"),
        None,
    )
    if invariant is None:
        raise SystemExit("STOP accepted parent legacy severity invariant missing")
    predicate = invariant.get("predicate", "")
    pairs = tuple(
        {"legacy_value": legacy, "severity": severity}
        for legacy, severity in re.findall(r"([a-z][a-z_]*)\s*->\s*([a-z][a-z_]*)", predicate)
    )
    if not pairs or "fails closed" not in predicate:
        raise SystemExit("STOP accepted parent legacy severity predicate is not executable")
    return pairs, "fail_closed"


def extract_stage_audience_constants(parent: dict[str, Any], stage_text: str) -> dict[str, Any]:
    """Extract concrete audience values from the accepted parent and stage review.

    The parser deliberately returns source spans and parent hashes alongside
    values.  It does not copy a second expected audience registry into the
    validator: the stage table/list and parent predicates are the expected set.
    """
    rows = _stage_table_rows(stage_text)
    domain_enum = tuple(parent["enums"]["domain"])
    if domain_enum != tuple(STAGE_DOMAIN_LABELS.values()):
        raise SystemExit("STOP parent domain enum does not match accepted stage domain order")
    domain_encoding = tuple(
        {
            "domain": row["domain"],
            "short_label_zh": row["short_label_zh"],
            "event_shape": row["event_shape"],
            "line_style": row["line_style"],
        }
        for row in rows
    )

    domain_list_line = _stage_line(
        stage_text,
        lambda line: "八个主轨道" in line and all(label in line for label in STAGE_DOMAIN_LABELS),
        "domain_list",
    )
    subtype_line = _stage_line(
        stage_text,
        lambda line: "症状与疗效" in line and "症状/疗效/量表/结局/趋势" in line,
        "symptom_efficacy_subtypes",
    )
    subtype_match = re.search(r"`([^`]*症状/疗效/量表/结局/趋势[^`]*)`", subtype_line["line"])
    if subtype_match is None:
        raise SystemExit("STOP accepted stage symptom subtype list missing")
    symptom_labels = tuple(subtype_match.group(1).split("/"))
    try:
        symptom_subtypes = tuple(STAGE_SYMPTOM_SUBTYPE_LABELS[label] for label in symptom_labels)
    except KeyError as exc:
        raise SystemExit("STOP accepted stage symptom subtype label drift") from exc
    if symptom_subtypes != tuple(parent["enums"]["symptom_efficacy_subtype"]):
        raise SystemExit("STOP accepted stage symptom subtype order drift")

    severity_line = _stage_line(
        stage_text,
        lambda line: "普通受众层风险等级" in line and all(label in line for label in parent["enums"]["severity_zh"]),
        "severity_lexicon",
    )
    severity_encoding = tuple(
        {
            "severity": severity,
            "label_zh": label,
            # The accepted parent only freezes the field type, not a number.
            "line_weight": None,
        }
        for severity, label in zip(parent["enums"]["severity"], parent["enums"]["severity_zh"])
    )

    forbidden_line = _stage_line(
        stage_text,
        lambda line: "不得使用" in line and "已记录事项" in line,
        "forbidden_terms",
    )
    forbidden_terms = tuple(re.findall(r"[“\"]([^”\"]+)[”\"]", forbidden_line["line"]))
    if not forbidden_terms:
        raise SystemExit("STOP accepted stage forbidden-term list missing")

    overlay_line = _stage_line(
        stage_text,
        lambda line: "双折角徽标" in line,
        "risk_overlay",
    )
    parent_risk_overlay = resolve_json_pointer(parent, "/risk_overlay_shape")
    parent_forbidden_shapes = tuple(resolve_json_pointer(parent, "/event_forbidden_shapes"))
    if "双折角徽标" not in overlay_line["line"]:
        raise SystemExit("STOP accepted stage risk overlay source missing")

    legacy_pairs, legacy_unknown_policy = _legacy_severity_from_parent(parent)
    parent_policy = dict(resolve_json_pointer(parent, "/legacy_domain_policy"))
    treatment_mapping = []
    for legacy_kind in parent["enums"]["legacy_treatment_kind"]:
        policy = parent_policy.get(legacy_kind)
        if policy != "frozen_mapping_or_fail_closed":
            raise SystemExit(f"STOP accepted parent legacy treatment policy drift: {legacy_kind}")
        treatment_mapping.append(
            {
                "legacy_kind": legacy_kind,
                "mapping_state": "unmapped_fail_closed",
                "mapping_authority_ref": None,
                "target_domain": None,
                "target_subtype": None,
            }
        )

    matrix_lists = {domain: [] for domain in domain_enum}
    for subtype in parent["enums"]["journey_subtype"]:
        if subtype in symptom_subtypes:
            matrix_lists["symptom_efficacy"].append(subtype)
            continue
        token = SUBTYPE_STAGE_TOKENS.get(subtype)
        if token is None:
            raise SystemExit(f"STOP no accepted stage token for subtype: {subtype}")
        matched_domains = []
        for row in rows:
            cells = row["cells"]
            haystack = " ".join(cells[:3])
            if subtype == "protocol_deviation":
                haystack = " ".join(cells)
            if token in haystack:
                matched_domains.append(row["domain"])
        if len(matched_domains) != 1:
            raise SystemExit(f"STOP stage subtype relation is not singular: {subtype}:{matched_domains}")
        matrix_lists[matched_domains[0]].append(subtype)
    domain_subtype_matrix = {domain: tuple(values) for domain, values in matrix_lists.items()}
    flattened = [subtype for values in domain_subtype_matrix.values() for subtype in values]
    if tuple(flattened) != tuple(parent["enums"]["journey_subtype"]):
        raise SystemExit("STOP accepted stage domain/subtype relation does not cover parent enum")

    invariant_map = {item["invariant_id"]: item for item in parent["invariants"]}
    domain_predicate = invariant_map.get("domain_subtype_matrix", {}).get("predicate", "")
    if not all(token in domain_predicate for token in symptom_subtypes):
        raise SystemExit("STOP accepted parent domain/subtype predicate drift")

    return {
        "domain_order": list(domain_enum),
        "journey_subtype_order": list(parent["enums"]["journey_subtype"]),
        "domains_exactly_eight": [dict(item) for item in domain_encoding],
        "severity_exactly_four": [dict(item) for item in severity_encoding],
        "domain_subtype_matrix": {domain: list(values) for domain, values in domain_subtype_matrix.items()},
        "legacy_severity_mapping": [dict(item) for item in legacy_pairs],
        "legacy_severity_unknown_policy": legacy_unknown_policy,
        "risk_overlay_shape": parent_risk_overlay,
        "event_shapes_forbidden": list(parent_forbidden_shapes),
        "symptom_efficacy_subtypes": list(symptom_subtypes),
        "forbidden_terms": list(forbidden_terms),
        "legacy_treatment_mapping": treatment_mapping,
        "legacy_treatment_policy": parent_policy,
        "source_spans": {
            "domain_list": domain_list_line["source_span"],
            "domain_rows": {row["domain"]: row["source_span"] for row in rows},
            "symptom_efficacy_subtypes": subtype_line["source_span"],
            "severity_lexicon": severity_line["source_span"],
            "forbidden_terms": forbidden_line["source_span"],
            "risk_overlay": overlay_line["source_span"],
        },
        "stage_raw_sha256": raw_sha(ROOT / STAGE_REL),
        "parent_raw_sha256": raw_sha(ROOT / PARENT_EXACT_REL),
        "parent_content_sha256": parent["contract_sha256"],
    }


def candidate_audience_constants() -> dict[str, Any]:
    return {
        "domain_order": list(DOMAINS),
        "journey_subtype_order": list(JOURNEY_SUBTYPES),
        "domains_exactly_eight": [dict(item) for item in DOMAIN_ENCODING],
        "severity_exactly_four": [dict(item) for item in SEVERITY_ENCODING],
        "domain_subtype_matrix": {domain: list(values) for domain, values in DOMAIN_SUBTYPE_MATRIX.items()},
        "legacy_severity_mapping": [dict(item) for item in LEGACY_SEVERITY_MAPPING],
        "legacy_severity_unknown_policy": UNKNOWN_LEGACY_SEVERITY_POLICY,
        "risk_overlay_shape": RISK_OVERLAY_SHAPE,
        "event_shapes_forbidden": list(EVENT_FORBIDDEN_SHAPES),
        "symptom_efficacy_subtypes": list(SYMPTOM_EFFICACY_SUBTYPES),
        "forbidden_terms": list(FORBIDDEN_TERMS),
        "legacy_treatment_mapping": [dict(item) for item in LEGACY_TREATMENT_MAPPING],
    }


def validate_domain_subtype_pair(domain: str, subtype: str) -> bool:
    return domain in DOMAIN_SUBTYPE_MATRIX and subtype in DOMAIN_SUBTYPE_MATRIX[domain]


def validate_legacy_severity(value: str) -> str | None:
    for item in LEGACY_SEVERITY_MAPPING:
        if item["legacy_value"] == value:
            return item["severity"]
    return None


def oracle_with_error(oracle: dict[str, Any]) -> dict[str, Any]:
    result = dict(oracle)
    outcome = result.get("expected_outcome")
    result["expected_error"] = outcome.split(":", 1)[1] if isinstance(outcome, str) and outcome.startswith("reject:") else None
    return result


def future_runtime_validation_contract() -> dict[str, Any]:
    return {
        "required": True,
        "validator_path": "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_validator.py",
        "validator_function": "validate_domain_subtype_pair",
        "test_path": "poc/medical_monitoring_ai_native_r5/tests/test_s5_validator.py::test_rejects_ae_ip_dose_before_projection_acceptance",
        "challenge_test_path": "poc/medical_monitoring_ai_native_r5/tests/challenges/test_s5_runtime_challenges.py::test_cross_domain_ae_ip_dose",
        "input": {"domain": "ae", "subtype": "ip_dose"},
        "expected_error": "DOMAIN_SUBTYPE_MISMATCH",
        "expected_projection": "not_emitted",
        "must_run_before_projection_acceptance": True,
        "runtime_absent_until_fresh_acceptance": True,
    }


def validate_future_runtime_contract() -> None:
    contract = future_runtime_validation_contract()
    allowlist = set(FUTURE_RUNTIME_ALLOWLIST)
    for key in ("validator_path", "test_path", "challenge_test_path"):
        path = contract[key].split("::", 1)[0]
        if path not in allowlist:
            raise SystemExit(f"STOP future cross-domain contract path outside allowlist: {path}")
        if (ROOT / path).exists():
            raise SystemExit(f"STOP future S5 runtime/test path already present: {path}")
    if validate_domain_subtype_pair(**contract["input"]):
        raise SystemExit("STOP future cross-domain validator contract is not fail-closed")


def validate_parent_derived_constants(
    parent: dict[str, Any], stage_text: str, expected: dict[str, Any] | None = None
) -> None:
    if parent.get("schema") != PARENT_CONTRACT_ID:
        raise SystemExit("STOP accepted parent contract schema")
    expected = expected or extract_stage_audience_constants(parent, stage_text)
    if expected["parent_raw_sha256"] != raw_sha(ROOT / PARENT_EXACT_REL):
        raise SystemExit("STOP parent raw hash changed during audience validation")
    if expected["stage_raw_sha256"] != raw_sha(ROOT / STAGE_REL):
        raise SystemExit("STOP stage raw hash changed during audience validation")

    # Resolve only concrete accepted parent data paths.  Object descriptors and
    # invariant predicates are validated below, never used as scalar values.
    for pointer in (
        "/enums/domain",
        "/enums/journey_subtype",
        "/enums/symptom_efficacy_subtype",
        "/enums/severity",
        "/enums/severity_zh",
        "/enums/event_shape",
        "/enums/line_style",
        "/enums/legacy_treatment_kind",
        "/enums/legacy_mapping_state",
        "/risk_overlay_shape",
        "/event_forbidden_shapes",
        "/legacy_domain_policy",
    ):
        resolve_json_pointer(parent, pointer)

    parent_enums = parent["enums"]
    candidate = candidate_audience_constants()
    for key in (
        "domain_order",
        "journey_subtype_order",
        "domains_exactly_eight",
        "severity_exactly_four",
        "domain_subtype_matrix",
        "legacy_severity_mapping",
        "legacy_severity_unknown_policy",
        "risk_overlay_shape",
        "event_shapes_forbidden",
        "symptom_efficacy_subtypes",
        "forbidden_terms",
        "legacy_treatment_mapping",
    ):
        if candidate[key] != expected[key]:
            raise SystemExit(f"STOP audience constant drift: {key}")

    if tuple(parent_enums["domain"]) != tuple(item["domain"] for item in expected["domains_exactly_eight"]):
        raise SystemExit("STOP parent domain enum drift")
    if tuple(parent_enums["journey_subtype"]) != tuple(
        subtype for values in expected["domain_subtype_matrix"].values() for subtype in values
    ):
        raise SystemExit("STOP parent journey subtype enum drift")
    if tuple(parent_enums["symptom_efficacy_subtype"]) != tuple(expected["symptom_efficacy_subtypes"]):
        raise SystemExit("STOP parent symptom/efficacy subtype enum drift")
    if tuple(parent_enums["severity"]) != tuple(item["severity"] for item in expected["severity_exactly_four"]):
        raise SystemExit("STOP parent severity enum drift")
    if tuple(parent_enums["severity_zh"]) != tuple(item["label_zh"] for item in expected["severity_exactly_four"]):
        raise SystemExit("STOP parent severity lexicon drift")
    if tuple(resolve_json_pointer(parent, "/legacy_domain_policy").keys()) != tuple(
        [item["legacy_kind"] for item in expected["legacy_treatment_mapping"]] + ["OTHER"]
    ) and set(resolve_json_pointer(parent, "/legacy_domain_policy")) != set(expected["legacy_treatment_policy"]):
        raise SystemExit("STOP parent legacy treatment policy keys drift")
    if resolve_json_pointer(parent, "/legacy_domain_policy") != expected["legacy_treatment_policy"]:
        raise SystemExit("STOP parent legacy treatment policy drift")

    invariant_map = {item["invariant_id"]: item for item in parent["invariants"]}
    required_invariants = {
        "domain_subtype_matrix",
        "severity_lexicon_bijection",
        "legacy_severity_mapping",
        "risk_overlay_unique",
        "domain_encoding_complete_unique",
        "legacy_treatment_fail_closed",
    }
    if not required_invariants.issubset(invariant_map):
        raise SystemExit("STOP parent audience invariant missing")
    domain_predicate = invariant_map["domain_subtype_matrix"].get("predicate", "")
    if not all(subtype in domain_predicate for subtype in expected["symptom_efficacy_subtypes"]):
        raise SystemExit("STOP parent domain/subtype invariant drift")
    parent_legacy_pairs, parent_legacy_policy = _legacy_severity_from_parent(parent)
    if list(parent_legacy_pairs) != expected["legacy_severity_mapping"] or parent_legacy_policy != expected["legacy_severity_unknown_policy"]:
        raise SystemExit("STOP parent legacy-severity invariant drift")

    # Schema objects must exist, but their scalar descriptors are not authority.
    for object_name in (
        "R5DomainEncodingItem",
        "R5SeverityLexiconItem",
        "R5LegacyTreatmentMappingItem",
        "R5AudienceLexicon",
        "R5AudienceEncodingRegistry",
    ):
        if not parent.get("objects", {}).get(object_name):
            raise SystemExit(f"STOP parent encoding object empty: {object_name}")

    if not set(DOMAIN_SUBTYPE_MATRIX) == set(expected["domain_subtype_matrix"]):
        raise SystemExit("STOP S5 domain subtype matrix domain set")
    flattened = [subtype for values in DOMAIN_SUBTYPE_MATRIX.values() for subtype in values]
    if len(flattened) != len(set(flattened)) or set(flattened) != set(parent_enums["journey_subtype"]):
        raise SystemExit("STOP S5 domain subtype matrix subtype coverage")
    if validate_domain_subtype_pair("ae", "ip_dose") or validate_domain_subtype_pair("unknown", "ae"):
        raise SystemExit("STOP S5 domain subtype fail-closed rule")
    for domain in parent_enums["domain"]:
        for subtype in parent_enums["journey_subtype"]:
            expected_pair = subtype in expected["domain_subtype_matrix"][domain]
            if validate_domain_subtype_pair(domain, subtype) != expected_pair:
                raise SystemExit(f"STOP S5 domain subtype validator drift: {domain}/{subtype}")
    if any(validate_legacy_severity(item["legacy_value"]) != item["severity"] for item in expected["legacy_severity_mapping"]):
        raise SystemExit("STOP S5 legacy severity mapping")
    if validate_legacy_severity("unknown") is not None:
        raise SystemExit("STOP S5 unknown legacy severity policy")


def constant_rows(
    parent: dict[str, Any],
    object_name: str,
    fields: dict[str, dict[str, Any]],
    expected: dict[str, Any],
) -> list[dict[str, Any]]:
    del parent

    def stage_path(span: dict[str, Any], source_type: str = "AcceptedR5StageParagraph") -> dict[str, Any]:
        return {
            "authority_contract": STAGE_CONTRACT_ID,
            "source_root_type": STAGE_SOURCE_ROOT_TYPE,
            "source_type": source_type,
            "source_span": dict(span),
            "raw_sha256": expected["stage_raw_sha256"],
            "parent_contract_id": PARENT_CONTRACT_ID,
            "parent_raw_sha256": expected["parent_raw_sha256"],
            "parent_content_sha256": expected["parent_content_sha256"],
        }

    def parent_path(pointer: str) -> dict[str, Any]:
        return {
            "authority_contract": PARENT_CONTRACT_ID,
            "source_root_type": PARENT_SOURCE_ROOT_TYPE,
            "source_type": PARENT_SOURCE_ROOT_TYPE,
            "json_pointer": pointer,
            "raw_sha256": expected["parent_raw_sha256"],
            "content_sha256": expected["parent_content_sha256"],
            "concrete_object": True,
        }

    domain_spans = [
        stage_path(span, "MarkdownTableRow")
        for span in expected["source_spans"]["domain_rows"].values()
    ]
    severity_spans = [stage_path(expected["source_spans"]["severity_lexicon"])]
    symptom_spans = [stage_path(expected["source_spans"]["symptom_efficacy_subtypes"])]
    forbidden_spans = [stage_path(expected["source_spans"]["forbidden_terms"])]
    legacy_policy_paths = [
        parent_path(f"/legacy_domain_policy/{item['legacy_kind']}")
        for item in expected["legacy_treatment_mapping"]
    ]
    risk_paths = [parent_path("/risk_overlay_shape"), parent_path("/event_forbidden_shapes")]

    def source_paths_for(leaf: str) -> tuple[list[dict[str, Any]], str, list[str], bool, bool]:
        if (object_name, leaf) in {
            ("S5SeverityEncoding", "line_weight"),
            ("S5AudienceLexicon", "content_hash"),
        }:
            return [], "future_renderer_parameter", [], True, False
        if object_name == "S5DomainEncodingItem":
            return list(domain_spans), "accepted_stage_review_concrete", [STAGE_CONTRACT_ID], False, True
        if object_name == "S5SeverityEncoding":
            return list(severity_spans), "accepted_stage_review_concrete", [STAGE_CONTRACT_ID], False, True
        if object_name == "S5LegacyTreatmentMapping":
            return list(legacy_policy_paths), "accepted_parent_policy_concrete", [PARENT_CONTRACT_ID], False, True
        if object_name == "S5AudienceLexicon":
            source = {
                "forbidden_terms": forbidden_spans,
                "domain_items": domain_spans,
                "severity_items": severity_spans,
                "symptom_efficacy_subtypes": symptom_spans,
            }[leaf]
            return list(source), "accepted_stage_review_concrete", [STAGE_CONTRACT_ID], False, True
        if object_name == "S5AudienceEncodingRegistry":
            if leaf == "domain_items":
                return list(domain_spans), "accepted_stage_review_concrete", [STAGE_CONTRACT_ID], False, True
            if leaf == "severity_items":
                return list(severity_spans), "accepted_stage_review_concrete", [STAGE_CONTRACT_ID], False, True
            if leaf == "symptom_efficacy_subtypes":
                return list(symptom_spans), "accepted_stage_review_concrete", [STAGE_CONTRACT_ID], False, True
            if leaf == "risk_overlay_shape":
                return list(risk_paths), "accepted_parent_policy_concrete", [PARENT_CONTRACT_ID], False, True
            if leaf == "legacy_treatment_mapping":
                return list(legacy_policy_paths), "accepted_parent_policy_concrete", [PARENT_CONTRACT_ID], False, True
        raise SystemExit(f"STOP missing S5 presentation source mapping: {object_name}.{leaf}")

    rows = []
    for leaf, spec in fields.items():
        source_paths, source_kind, source_contracts, future_parameter, executable = source_paths_for(leaf)
        rows.append(
            {
                "leaf_id": f"{object_name}.{leaf}",
                "target_object": object_name,
                "target_field": leaf,
                "target_spec": spec,
                "core_authority_leaf": False,
                "authority_plane": "s5_owned_presentation_non_core",
                "source_kind": source_kind,
                "source_contracts": source_contracts,
                "source_paths": source_paths,
                "validator_refs": [
                    f"{GENERATOR_REL.as_posix()}:extract_stage_audience_constants",
                    f"{GENERATOR_REL.as_posix()}:validate_parent_derived_constants",
                ] + ([f"{GENERATOR_REL.as_posix()}:resolve_json_pointer"] if source_kind == "accepted_parent_policy_concrete" else []),
                "identity_recipe": (
                    "future_renderer_parameter_not_acceptance_authority"
                    if future_parameter
                    else "accepted_stage_row_or_parent_policy_with_raw_and_content_hash_binding"
                ),
                "derivation_sources": (
                    ["not_frozen_by_accepted_r5_sources", "acceptance_claim_false"]
                    if future_parameter
                    else [
                        f"{STAGE_REL.as_posix()}:exact_source_spans_and_rows",
                        f"{PARENT_EXACT_REL.as_posix()}:raw_sha256={expected['parent_raw_sha256']}",
                        f"{PARENT_EXACT_REL.as_posix()}:content_sha256={expected['parent_content_sha256']}",
                    ]
                ),
                "forbidden_authority_sources": list(COMMON_FORBIDDEN_AUTHORITY_SOURCES),
                "deferred_contract": None,
                "placeholder": False,
                "self_signed": False,
                "executable": executable,
                "acceptance_claim": False,
                "future_renderer_parameter": future_parameter,
            }
        )
    return rows


def navigation_rows(object_name: str, fields: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for leaf, spec in fields.items():
        binding = "accepted_public_packet_binding" if leaf in {
            "spine_ref",
            "subject_ref",
            "authority_receipt_ref",
            "authority_receipt_refs",
            "authority_projection_id",
        } else "runtime_navigation_state"
        if leaf in {"authority_receipt_ref", "authority_receipt_refs"}:
            source_pointer_value = "/receipt/receipt_id"
        elif leaf == "authority_projection_id":
            source_pointer_value = "/projection/projection_id"
        else:
            source_pointer_value = "/projection/scope_identity/" + leaf
        if leaf in {"authority_receipt_ref", "authority_receipt_refs"}:
            navigation_sources = [
                {
                    "authority_contract": "subject-temporal-public-v1",
                    "source_root_type": "SubjectTemporalAuthorityPacket",
                    "source_type": "PublicAuthorityReceipt",
                    "json_pointer": source_pointer_value,
                },
                {
                    "authority_contract": "aemh-match-history-public-v1",
                    "source_root_type": "AEMHMatchHistoryAuthorityPacket",
                    "source_type": "PublicAuthorityReceipt",
                    "json_pointer": source_pointer_value,
                },
            ]
        else:
            navigation_sources = [
                {
                    "authority_contract": "subject-temporal-public-v1",
                    "source_root_type": "SubjectTemporalAuthorityPacket",
                    "source_type": "SubjectTemporalPublicProjection",
                    "json_pointer": source_pointer_value,
                }
            ] if binding != "runtime_navigation_state" else []
        rows.append(
            {
                "leaf_id": f"{object_name}.{leaf}",
                "target_object": object_name,
                "target_field": leaf,
                "target_spec": spec,
                "core_authority_leaf": False,
                "authority_plane": "navigation_contract",
                "source_kind": binding,
                "source_contracts": (
                    ["subject-temporal-public-v1", "aemh-match-history-public-v1"]
                    if leaf in {"authority_receipt_ref", "authority_receipt_refs"}
                    else (["subject-temporal-public-v1"] if binding != "runtime_navigation_state" else [])
                ),
                "source_paths": navigation_sources,
                "validator_refs": [
                    "s5.navigation_context_membership_validator",
                    "s5.navigation_state_is_not_medical_authority",
                ],
                "identity_recipe": "canonical_navigation_state_hash" if "hash" in leaf else "navigation_state_not_authority",
                "forbidden_authority_sources": list(COMMON_FORBIDDEN_AUTHORITY_SOURCES),
                "deferred_contract": None,
                "placeholder": False,
                "self_signed": False,
                "executable": True,
            }
        )
    return rows


def replacement_for_parent_target(target: str) -> list[str]:
    object_name, leaf = target.split(".", 1)
    mapping = {
        "R5AEMHMatchHistory": {
            "candidate_ref": ["S5AEMHThread.original_candidate_ref"],
            "from_snapshot_ref": ["S5AEMHProjection.previous_projection_ref", "S5AEMHPrefixAnchor.previous_thread_content_hash"],
            "history_content_hash": ["S5AEMHHistoryEntry.entry_hash", "S5AEMHThread.thread_content_hash"],
            "identity_evidence_refs": ["S5AEMHHistoryEntry.identity_evidence_refs"],
            "later_fact_ref": ["S5AEMHHistoryEntry.later_fact_refs"],
            "match_state": ["S5AEMHHistoryEntry.match_state"],
            "to_snapshot_ref": ["S5AEMHHistoryEntry.snapshot_ref"],
        },
        "R5DeepLinkState": {
            "event_ref": ["S5SharedTemporalContext.selected_event_ref"],
            "risk_anchor_ref": ["S5SharedTemporalContext.selected_risk_anchor_ref"],
            "spine_ref": ["S5SharedTemporalContext.spine_ref"],
            "visit_ref": ["S5SharedTemporalContext.selected_visit_ref"],
        },
        "R5JourneyEvent": {
            "date_state": ["S5JourneyEvent.start_endpoint.state", "S5JourneyEvent.end_endpoint.state"],
            "domain": ["S5JourneyEvent.domain"],
            "end": ["S5JourneyEvent.end_endpoint"],
            "event_ref": ["S5JourneyEvent.event_ref"],
            "risk_anchor_refs": ["S5JourneyEvent.risk_anchor_refs"],
            "source_locator_refs": ["S5JourneyEvent.source_locator_refs"],
            "start": ["S5JourneyEvent.start_endpoint"],
            "subtype": ["S5JourneyEvent.subtype"],
        },
        "R5JourneyTrack": {
            "applicability_state": ["S5DomainTrack.applicability_state"],
            "content_hash": ["S5DomainTrack.track_content_hash"],
            "domain": ["S5DomainTrack.domain"],
            "event_refs": ["S5DomainTrack.event_refs"],
            "risk_anchor_refs": ["S5DomainTrack.risk_anchor_refs"],
        },
        "R5PendingDateItem": {
            "candidate_date_refs": ["S5PendingDateItem.start_endpoint.source_locator_refs", "S5PendingDateItem.end_endpoint.source_locator_refs"],
            "date_state": ["S5PendingDateItem.start_endpoint.state", "S5PendingDateItem.end_endpoint.state"],
            "domain": ["S5PendingDateItem.domain"],
            "item_kind": ["S5PendingDateItem.item_kind"],
            "item_ref": ["S5PendingDateItem.item_ref"],
            "source_locator_refs": ["S5PendingDateItem.source_locator_refs"],
        },
        "R5RiskAnchor": {
            "date_state": ["S5RiskAnchor.start_endpoint.state", "S5RiskAnchor.end_endpoint.state"],
            "domain": ["S5RiskAnchor.domain"],
            "event_ref": ["S5RiskAnchor.event_ref"],
            "risk_ref": ["S5RiskAnchor.risk_ref"],
            "risk_type_zh": ["S5RiskAnchor.risk_type_zh"],
            "severity": ["S5RiskAnchor.severity"],
            "visit_ref": ["S5RiskAnchor.visit_ref"],
        },
        "R5TemporalSpineProjection": {
            "content_hash": ["S5SubjectTemporalProjection.projection_content_hash"],
            "cutoff_ref": ["S5AxisBasis.cutoff_endpoint.exact_date", "S5AxisBasis.cutoff_endpoint.state"],
            "event_refs": ["S5MembershipIndex.event_refs"],
            "pending_date_refs": ["S5MembershipIndex.pending_date_refs"],
            "phase_band_refs": ["S5MembershipIndex.phase_refs"],
            "spine_ref": ["S5ScopeIdentity.spine_ref"],
            "subject_ref": ["S5ScopeIdentity.subject_ref"],
            "visit_refs": ["S5MembershipIndex.visit_refs"],
        },
        "R5VisitNode": {
            "actual_date": ["S5VisitNode.actual_endpoint"],
            "date_state": ["S5VisitNode.actual_endpoint.state", "S5VisitNode.nominal_endpoint.state"],
            "nominal_date": ["S5VisitNode.nominal_endpoint"],
            "phase_ref": ["S5VisitNode.phase_ref"],
            "source_locator_refs": ["S5VisitNode.source_locator_refs"],
            "visit_kind": ["S5VisitNode.visit_kind"],
            "visit_ref": ["S5VisitNode.visit_ref"],
        },
        "R5AuthorityReceipt": {
            "public_projection_kind": ["S5AuthorityReceipt.receipt_variant"],
        },
    }
    return mapping.get(object_name, {}).get(leaf, [])


def parent_leaf_rows(parent: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    replacement_contracts = {"subject-temporal-public-v1", "aemh-match-history-public-v1", "r5-authority-receipt-kind-v1"}
    for source in parent["field_mappings"]:
        deferred = source.get("deferred_contract")
        if source["source_kind"] == "deferred" and deferred in replacement_contracts:
            status = "replaced_by_s5_typed_leaf"
            replacement = replacement_for_parent_target(source["target"])
            if not replacement:
                raise SystemExit(f"STOP missing S5 replacement: {source['target']}")
            row = {
                **source,
                "source_kind": "s5_canonical_replacement",
                "deferred_contract": None,
                "core_authority_leaf": False,
                "status": status,
                "replacement_leaf_ids": replacement,
                "authority_source_forbidden": list(COMMON_FORBIDDEN_AUTHORITY_SOURCES),
                "placeholder": False,
                "self_signed": False,
            }
        elif source["source_kind"] == "deferred":
            row = {
                **source,
                "core_authority_leaf": False,
                "status": "deferred_out_of_scope_preserved",
                "authority_source_forbidden": list(COMMON_FORBIDDEN_AUTHORITY_SOURCES),
                "placeholder": False,
                "self_signed": False,
            }
        else:
            row = {
                **source,
                "core_authority_leaf": False,
                "status": "inherited_parent_mapping",
                "authority_source_forbidden": list(COMMON_FORBIDDEN_AUTHORITY_SOURCES),
                "placeholder": False,
                "self_signed": False,
            }
        rows.append(row)
    return rows


def build_matrix(
    parent: dict[str, Any], objects: dict[str, dict[str, Any]], audience_expected: dict[str, Any]
) -> dict[str, Any]:
    canonical_rows: list[dict[str, Any]] = []
    for object_name, fields in objects.items():
        if object_name in {"S5AudienceLexicon", "S5AudienceEncodingRegistry"}:
            canonical_rows.extend(constant_rows(parent, object_name, fields, audience_expected))
        elif object_name in {"S5DomainEncodingItem", "S5SeverityEncoding", "S5LegacyTreatmentMapping"}:
            canonical_rows.extend(constant_rows(parent, object_name, fields, audience_expected))
        elif object_name in {"S5SelectionAnchor", "S5SharedTemporalContext", "S5ViewBinding", "S5SubjectWorkspaceContract"}:
            canonical_rows.extend(navigation_rows(object_name, fields))
        else:
            canonical_rows.extend(
                producer_leaf_row(object_name, leaf, spec) for leaf, spec in fields.items()
            )
    canonical_rows.sort(key=lambda row: row["leaf_id"])
    legacy_rows = parent_leaf_rows(parent)
    legacy_rows.sort(key=lambda row: row["target"])
    core_rows = [row for row in canonical_rows if row["core_authority_leaf"]]
    presentation_rows = [
        row for row in canonical_rows if row["authority_plane"] == "s5_owned_presentation_non_core"
    ]
    deferred_core = [
        row["leaf_id"]
        for row in canonical_rows
        if row["core_authority_leaf"]
        and (row.get("deferred_contract") or row["source_kind"] in {"deferred", "placeholder", "self_signed"})
    ]
    if deferred_core:
        raise SystemExit(f"STOP deferred S5 core leaves: {deferred_core[:5]}")
    return {
        "schema": "medical-monitoring-r5-s5-subject-workspace-source-leaf-matrix-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "authority_rule": {
            "serialized_input_authority": "accepted AuthorityBundleV02 only at producer boundary",
            "public_output_authority": "accepted subject_temporal_public and aemh_match_history_public packets",
            "candidate_output_as_input_forbidden": True,
            "fixture_text_count_case_id_filename_hash_nearest_ui_authority_forbidden": True,
            "unknown_domain": "fail_closed_to_domain_confirmation_surface",
            "clinical_identity_temporal_history_core_public_only": True,
            "presentation_constants_non_core": True,
            "accepted_stage_source_span_and_parent_sha_binding_required": True,
            "future_renderer_parameter_has_no_acceptance_claim": True,
            "pseudo_constant_selectors_forbidden": True,
            "runtime_surface_scan_required": True,
        },
        "canonical_leaf_rows": canonical_rows,
        "parent_leaf_rows": legacy_rows,
        "core_leaf_ids": [row["leaf_id"] for row in core_rows],
        "deferred_core_leaf_ids": deferred_core,
        "counts": {
            "canonical_leaf_count": len(canonical_rows),
            "core_leaf_count": len(core_rows),
            "presentation_leaf_count": len(presentation_rows),
            "deferred_core_leaf_count": len(deferred_core),
            "parent_leaf_count": len(legacy_rows),
            "parent_replaced_leaf_count": sum(row["status"] == "replaced_by_s5_typed_leaf" for row in legacy_rows),
            "parent_deferred_out_of_scope_count": sum(
                row["status"] == "deferred_out_of_scope_preserved" for row in legacy_rows
            ),
        },
        "matrix_content_hash": None,
    }


def resolve_schema_pointer(schema: dict[str, Any], root_type: str, pointer: str) -> dict[str, Any]:
    if pointer == "/":
        raise SystemExit("STOP source leaf pointer cannot be root")
    current_type = root_type
    parts = [part for part in pointer.split("/") if part]
    for index, raw_part in enumerate(parts):
        is_array = raw_part.endswith("[*]")
        field_name = raw_part[:-3] if is_array else raw_part
        current_object = schema["objects"].get(current_type)
        if current_object is None or field_name not in current_object:
            raise SystemExit(f"STOP unresolved public source pointer: {pointer}")
        field_spec = current_object[field_name]
        if index < len(parts) - 1:
            if is_array and field_spec["cardinality"] != "many":
                raise SystemExit(f"STOP array selector on one-valued source field: {pointer}")
            if not is_array and field_spec["cardinality"] == "many":
                raise SystemExit(f"STOP missing array selector on source field: {pointer}")
            next_type = field_spec["type"]
            if next_type.startswith("enum:") or next_type not in schema["objects"]:
                raise SystemExit(f"STOP non-object source traversal: {pointer}")
            current_type = next_type
    return field_spec


def validate_source_leaf_matrix(
    matrix: dict[str, Any],
    parent: dict[str, Any],
    subject_schema: dict[str, Any],
    aemh_schema: dict[str, Any],
    stage_text: str,
) -> None:
    schemas = {
        "subject-temporal-public-v1": subject_schema,
        "aemh-match-history-public-v1": aemh_schema,
    }
    stage_lines = stage_text.splitlines()
    stage_sha256 = raw_sha(ROOT / STAGE_REL)
    parent_raw_sha256 = raw_sha(ROOT / PARENT_EXACT_REL)
    parent_content_sha256 = parent["contract_sha256"]
    for row in matrix["canonical_leaf_rows"]:
        for source in row["source_paths"]:
            contract = source["authority_contract"]
            if contract == STAGE_CONTRACT_ID:
                if source.get("source_root_type") != STAGE_SOURCE_ROOT_TYPE:
                    raise SystemExit(f"STOP stage source root/type mismatch: {row['leaf_id']}")
                span = source.get("source_span")
                if not isinstance(span, dict) or span.get("line_start") != span.get("line_end"):
                    raise SystemExit(f"STOP stage source span missing: {row['leaf_id']}")
                line_number = span.get("line_start")
                if not isinstance(line_number, int) or not 1 <= line_number <= len(stage_lines):
                    raise SystemExit(f"STOP stage source line out of range: {row['leaf_id']}")
                if stage_lines[line_number - 1] != span.get("line_text"):
                    raise SystemExit(f"STOP stage source line drift: {row['leaf_id']}")
                if source.get("raw_sha256") != stage_sha256:
                    raise SystemExit(f"STOP stage source raw hash mismatch: {row['leaf_id']}")
                if source.get("parent_contract_id") != PARENT_CONTRACT_ID:
                    raise SystemExit(f"STOP stage source parent contract binding missing: {row['leaf_id']}")
                if source.get("parent_raw_sha256") != parent_raw_sha256 or source.get("parent_content_sha256") != parent_content_sha256:
                    raise SystemExit(f"STOP stage source parent hash binding mismatch: {row['leaf_id']}")
                continue
            if contract == PARENT_CONTRACT_ID:
                if source["source_root_type"] != PARENT_SOURCE_ROOT_TYPE or source["source_type"] != PARENT_SOURCE_ROOT_TYPE:
                    raise SystemExit(f"STOP parent source root/type mismatch: {row['leaf_id']}")
                resolve_json_pointer(parent, source["json_pointer"])
                if source.get("raw_sha256") not in {None, parent_raw_sha256}:
                    raise SystemExit(f"STOP parent source raw hash mismatch: {row['leaf_id']}")
                if source.get("content_sha256") not in {None, parent_content_sha256}:
                    raise SystemExit(f"STOP parent source content hash mismatch: {row['leaf_id']}")
                if source.get("json_pointer", "").startswith("/contract_constants/"):
                    raise SystemExit(f"STOP pseudo constant selector: {row['leaf_id']}")
                continue
            if contract not in schemas:
                raise SystemExit(f"STOP unknown source contract: {contract}")
            field_spec = resolve_schema_pointer(schemas[contract], source["source_root_type"], source["json_pointer"])
            if row["core_authority_leaf"] and row["authority_plane"] == "accepted_public_packet":
                terminal = source["json_pointer"].split("/")[-1].removesuffix("[*]")
                if terminal != row["target_field"]:
                    raise SystemExit(f"STOP public source leaf mismatch: {row['leaf_id']}")
        if row["core_authority_leaf"]:
            if not row["source_paths"] or not row["validator_refs"]:
                raise SystemExit(f"STOP core authority mapping incomplete: {row['leaf_id']}")
            if row["source_kind"] in {"accepted_contract_constant", "placeholder", "self_signed", "deferred"}:
                raise SystemExit(f"STOP pseudo or deferred core authority mapping: {row['leaf_id']}")
        elif row["authority_plane"] == "s5_owned_presentation_non_core":
            if row.get("acceptance_claim") is not False:
                raise SystemExit(f"STOP presentation leaf acceptance claim: {row['leaf_id']}")
            if row.get("future_renderer_parameter") and row["source_paths"]:
                raise SystemExit(f"STOP unbound future renderer parameter has source path: {row['leaf_id']}")


def build_challenges(parent: dict[str, Any], parent_challenge: dict[str, Any], parent_quota: dict[str, Any]) -> dict[str, Any]:
    inherited = []
    for row in parent_challenge["rows"]:
        oracle = row["stage_oracle_contract"]
        structured_oracle = oracle_with_error(oracle)
        rule_id = oracle["rule_id"]
        exact_rule = next((item for item in parent["challenge_rules"] if item["rule_id"] == rule_id), None)
        if exact_rule is None:
            raise SystemExit(f"STOP parent challenge rule missing: {rule_id}")
        inherited.append(
            {
                "challenge_id": f"parent::{rule_id}",
                "category": row["category"],
                "origin": "accepted_parent_r5_v0.3",
                "target": rule_id.split(".", 1)[1] if "." in rule_id else rule_id,
                "mutation": row["single_mutation"]["value"],
                "single_mutation": dict(row["single_mutation"]),
                "valid_value": exact_rule["valid_value"],
                "expected_outcome": oracle["expected_outcome"],
                "expected_projection": oracle["expected_projection"],
                "oracle_contract": structured_oracle,
                "stage_oracle_contract": dict(structured_oracle),
                "severity": row["severity"],
                "precondition": row["precondition"],
                "test_metadata_only": True,
                "authority_source_forbidden": list(COMMON_FORBIDDEN_AUTHORITY_SOURCES),
            }
        )
    specs = (
        ("source_pin", "parent_exact_contract", "reject:SOURCE_PIN_MISMATCH"),
        ("source_pin", "public_producer_module", "reject:SOURCE_PIN_MISMATCH"),
        ("source_pin", "public_producer_test", "reject:SOURCE_PIN_MISMATCH"),
        ("typed_packet", "candidate_packet_as_authority", "reject:CANDIDATE_OUTPUT_AS_AUTHORITY"),
        ("typed_packet", "missing_receipt_binding", "reject:RECEIPT_BINDING_MISMATCH"),
        ("typed_packet", "projection_hash", "reject:PROJECTION_HASH_MISMATCH"),
        ("identity", "scope_subject_ref", "reject:SCOPE_IDENTITY_MISMATCH"),
        ("identity", "scope_spine_ref", "reject:SCOPE_IDENTITY_MISMATCH"),
        ("temporal", "date_state_exact_without_date", "reject:DATE_GEOMETRY_MISMATCH"),
        ("temporal", "partial_date_range_dropped", "reject:DATE_STATE_LOSS"),
        ("temporal", "conflicted_date_collapsed", "reject:DATE_STATE_LOSS"),
        ("temporal", "missing_date_fabricated", "reject:DATE_STATE_LOSS"),
        ("temporal", "visit_event_absorption", "reject:VISIT_EVENT_AXIS_MISMATCH"),
        ("temporal", "second_spine", "reject:SECOND_TEMPORAL_SPINE"),
        ("domain", "unknown_domain_to_other", "reject:UNKNOWN_DOMAIN_FAIL_CLOSED"),
        ("domain", "eight_domain_duplicate", "reject:DOMAIN_REGISTRY_NOT_BIJECTIVE"),
        ("domain", "symptom_efficacy_second_shape", "reject:SYMPTOM_EFFICACY_SHAPE_COLLISION"),
        ("domain", "not_applicable_to_not_provided", "reject:APPLICABILITY_STATE_DRIFT"),
        ("encoding", "risk_overlay_as_event_shape", "reject:RISK_EVENT_SHAPE_COLLISION"),
        ("encoding", "high_promoted_to_critical", "reject:SEVERITY_PROMOTION"),
        ("encoding", "legacy_severity_unmapped", "reject:LEGACY_SEVERITY_FAIL_CLOSED"),
        ("encoding", "forbidden_audience_term", "reject:FORBIDDEN_AUDIENCE_TERM"),
        ("legacy", "background_treatment_without_mapping", "reject:LEGACY_TREATMENT_FAIL_CLOSED"),
        ("legacy", "non_drug_treatment_without_mapping", "reject:LEGACY_TREATMENT_FAIL_CLOSED"),
        ("aemh", "original_reminder_deleted", "reject:AEMH_HISTORY_NOT_APPEND_ONLY"),
        ("aemh", "later_fact_identity_rewritten", "reject:AEMH_IDENTITY_REWRITE"),
        ("aemh", "match_decision_auto_closes_risk", "reject:AEMH_AUTOMATIC_CLOSURE"),
        ("aemh", "previous_prefix_dropped", "reject:AEMH_PREFIX_NOT_RETAINED"),
        ("workspace", "journey_profile_spine_mismatch", "reject:SHARED_SPINE_MISMATCH"),
        ("workspace", "profile_timeline_window_mismatch", "reject:SHARED_WINDOW_MISMATCH"),
        ("workspace", "selection_anchor_not_member", "reject:SELECTION_ANCHOR_NOT_MEMBER"),
        ("workspace", "ui_state_rewrites_authority", "reject:UI_STATE_AS_AUTHORITY"),
        ("unlock", "contract_acceptance_starts_8911", "reject:UNLOCK_BOUNDARY"),
        ("unlock", "contract_acceptance_allows_real_project", "reject:UNLOCK_BOUNDARY"),
        ("unlock", "contract_acceptance_allows_product", "reject:UNLOCK_BOUNDARY"),
        ("unlock", "contract_acceptance_allows_medical_writing", "reject:UNLOCK_BOUNDARY"),
    )
    s5_rows = []
    for index, (category, target, expected) in enumerate(specs, 1):
        mutation = s5_mutation_definition(target)
        structured_oracle = oracle_with_error(
            {
                "rule_id": f"s5.{target}",
                "expected_outcome": expected,
                "expected_projection": "not_emitted" if expected.startswith("reject:") else "none",
                "required_non_llm_anchor": "deterministic generator semantic validator plus exact contract content hash",
                "test_locator": f"poc/medical_monitoring_ai_native_r5/tests/challenges/test_s5_runtime_challenges.py::test_{target}",
                "kind": "planned_pytest",
                "planned_stage": "S5",
            }
        )
        s5_rows.append(
            {
                "challenge_id": f"s5::{index:03d}",
                "category": category,
                "origin": "s5_contract_specific",
                "target": target,
                "mutation": mutation["value"],
                "single_mutation": {
                    key: value for key, value in mutation.items() if key != "valid_value"
                },
                "valid_value": mutation["valid_value"],
                "expected_outcome": expected,
                "expected_projection": "not_emitted" if expected.startswith("reject:") else "none",
                "oracle_contract": structured_oracle,
                "stage_oracle_contract": dict(structured_oracle),
                "test_metadata_only": True,
                "authority_source_forbidden": list(COMMON_FORBIDDEN_AUTHORITY_SOURCES),
            }
        )
    replay_refs = (
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
    )
    replay_rows = [
        {
            "challenge_id": f"accepted-public-replay::{index:03d}",
            "category": "accepted_public_authority_replay",
            "origin": "accepted_public_authority_producer_record",
            "source_case_ref": ref,
            "target": "public_packet_graph",
            "mutation": ref,
            "single_mutation": {"op": "replay", "path": "/accepted_public_packet_graph", "value": ref},
            "valid_value": "accepted_public_packet_graph",
            "expected_outcome": "accept_replay_only",
            "expected_projection": "packet_emitted",
            "oracle_contract": oracle_with_error({
                "rule_id": f"accepted_public_replay.{ref}",
                "expected_outcome": "accept_replay_only",
                "expected_projection": "packet_emitted",
                "required_non_llm_anchor": "accepted producer graph replay record and packet content hash",
                "test_locator": "poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py::test_exact_graph_replay",
                "kind": "accepted_replay",
                "planned_stage": "S5",
            }),
            "stage_oracle_contract": oracle_with_error({
                "rule_id": f"accepted_public_replay.{ref}",
                "expected_outcome": "accept_replay_only",
                "expected_projection": "packet_emitted",
                "required_non_llm_anchor": "accepted producer graph replay record and packet content hash",
                "test_locator": "poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py::test_exact_graph_replay",
                "kind": "accepted_replay",
                "planned_stage": "S5",
            }),
            "test_metadata_only": True,
            "authority_source_forbidden": list(COMMON_FORBIDDEN_AUTHORITY_SOURCES),
        }
        for index, ref in enumerate(replay_refs, 1)
    ]
    rows = inherited + s5_rows + replay_rows
    required_oracle_keys = {
        "rule_id",
        "expected_outcome",
        "expected_error",
        "expected_projection",
        "required_non_llm_anchor",
        "test_locator",
    }
    for row in rows:
        mutation = row.get("single_mutation")
        oracle = row.get("oracle_contract")
        if not isinstance(mutation, dict) or set(("op", "path", "value")) - set(mutation):
            raise SystemExit(f"STOP non-executable challenge mutation: {row['challenge_id']}")
        if not isinstance(oracle, dict) or not required_oracle_keys.issubset(oracle):
            raise SystemExit(f"STOP incomplete challenge oracle: {row['challenge_id']}")
        if row["origin"] == "s5_contract_specific" and isinstance(mutation["value"], str) and mutation["value"].startswith(("mutated::", "valid::")):
            raise SystemExit(f"STOP placeholder challenge mutation: {row['challenge_id']}")
    mutation_keys: dict[tuple[str, str, str], str] = {}
    for row in rows:
        mutation = row["single_mutation"]
        key = (mutation["op"], mutation["path"], digest(mutation["value"]))
        previous = mutation_keys.get(key)
        if previous is not None:
            raise SystemExit(
                f"STOP duplicate single_mutation tuple: {previous} and {row['challenge_id']}"
            )
        mutation_keys[key] = row["challenge_id"]
    categories: dict[str, int] = {}
    for row in rows:
        categories[row["category"]] = categories.get(row["category"], 0) + 1
    result = {
        "schema": "medical-monitoring-r5-s5-subject-workspace-challenge-registry-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "parent_contract_sha256": parent["contract_sha256"],
        "parent_quota_ledger_sha256": raw_sha(ROOT / PARENT_QUOTA_REL),
        "rows": rows,
        "row_count": len(rows),
        "counts": {
            "inherited_parent_rows": len(inherited),
            "s5_contract_specific_rows": len(s5_rows),
            "accepted_public_replay_rows": len(replay_rows),
            "total": len(rows),
        },
        "category_counts": dict(sorted(categories.items())),
        "quota": {
            "parent_quota_is_immutable": True,
            "parent_expected_total": parent_quota["expected_total"],
            "s5_additional_rows_have_no_medical_quota_authority": True,
        },
        "authority_forbidden": list(COMMON_FORBIDDEN_AUTHORITY_SOURCES),
        "future_runtime_validation_contract": future_runtime_validation_contract(),
        "row_contract": {
            "single_mutation_required": ["op", "path", "value"],
            "oracle_contract_required": ["rule_id", "expected_outcome", "expected_error", "expected_projection", "required_non_llm_anchor", "test_locator"],
            "placeholder_mutations_forbidden": True,
            "test_metadata_only": True,
        },
        "structured_mutation_row_count": len(rows),
        "structured_oracle_row_count": len(rows),
        "unique_single_mutation_tuple_count": len(mutation_keys),
        "registry_content_hash": None,
    }
    return result


def build_exact(
    parent: dict[str, Any],
    subject_schema: dict[str, Any],
    aemh_schema: dict[str, Any],
    temporal_schema: dict[str, Any],
    temporal_recipes: dict[str, Any],
    temporal_fixtures: dict[str, Any],
    typed_authority: dict[str, Any],
    matrix: dict[str, Any],
    challenges: dict[str, Any],
    audience_expected: dict[str, Any],
) -> dict[str, Any]:
    objects = build_objects(subject_schema, aemh_schema)
    audience = candidate_audience_constants()
    audience["legacy_treatment_policy"] = audience_expected["legacy_treatment_policy"]
    audience.update(
        {
            "authority_scope": "s5_owned_presentation_non_core",
            "acceptance_claim": False,
            "source_binding": {
                "stage_contract": STAGE_REL.as_posix(),
                "stage_raw_sha256": audience_expected["stage_raw_sha256"],
                "parent_contract": PARENT_EXACT_REL.as_posix(),
                "parent_raw_sha256": audience_expected["parent_raw_sha256"],
                "parent_content_sha256": audience_expected["parent_content_sha256"],
                "source_spans": audience_expected["source_spans"],
            },
            "future_renderer_parameters": [
                {
                    "parameter": "S5SeverityEncoding.line_weight",
                    "value": None,
                    "acceptance_claim": False,
                    "reason": "numeric line weight is not concretely frozen by accepted R5 sources",
                },
                {
                    "parameter": "S5AudienceLexicon.content_hash",
                    "value": None,
                    "acceptance_claim": False,
                    "reason": "renderer content hash is not frozen before a future renderer exists",
                },
            ],
        }
    )
    enums = {
        "domain": list(audience_expected["domain_order"]),
        "aemh_domain": ["ae", "mh"],
        "axis_mode": ["calendar", "study_day"],
        "cutoff_state": ["present", "absent"],
        "cutoff_endpoint_state": ["present", "absent"],
        "date_state": ["exact", "partial", "conflicted", "missing"],
        "date_geometry": ["point", "closed_interval", "open_start", "open_end"],
        "applicability_state": ["applicable", "not_applicable", "not_provided"],
        "fallback_policy": ["fail_closed_no_nearest"],
        "history_event_kind": ["reminder_created", "match_decided", "withdrawn", "reappeared"],
        "identity_evidence_kind": ["candidate", "later_fact", "considered_fact"],
        "pending_item_kind": ["event", "risk", "visit", "phase"],
        "visit_kind": ["nominal", "actual", "unscheduled"],
        "receipt_variant": ["subject_temporal", "aemh_match_history"],
        "risk_lifecycle_effect": ["none"],
        "severity": [item["severity"] for item in audience_expected["severity_exactly_four"]],
        "match_state": ["exact", "ambiguous", "rejected"],
        "journey_subtype": list(audience_expected["journey_subtype_order"]),
        "symptom_efficacy_subtype": list(audience_expected["symptom_efficacy_subtypes"]),
        "event_shape": list(resolve_json_pointer(parent, "/enums/event_shape")),
        "line_style": list(resolve_json_pointer(parent, "/enums/line_style")),
        "legacy_treatment_kind": list(resolve_json_pointer(parent, "/enums/legacy_treatment_kind")),
        "legacy_mapping_state": list(resolve_json_pointer(parent, "/enums/legacy_mapping_state")),
        "source_locator_variant": ["r4_source_locator", "d08_source_locator"],
        "visibility_state": ["projectable", "hidden", "not_evaluable"],
        "s5_anchor_kind": ["none", "event", "risk_anchor", "visit", "source_locator"],
        "s5_view": ["journey", "profile", "timeline"],
        "s5_projection_kind": ["subject_temporal", "aemh_history"],
    }
    exact = {
        "schema": "medical-monitoring-r5-s5-subject-workspace-exact-contract-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "parent_contract": {
            "schema": parent["schema"],
            "raw_sha256": raw_sha(ROOT / PARENT_EXACT_REL),
            "content_sha256": parent["contract_sha256"],
            "field_mapping_count": len(parent["field_mappings"]),
            "challenge_count": len(parent["challenge_rules"]),
        },
        "accepted_public_packet_contracts": {
            "subject_temporal": {
                "contract_id": "subject-temporal-public-v1",
                "schema_version": subject_schema["schema_version"],
                "schema_raw_sha256": raw_sha(ROOT / SUBJECT_SCHEMA_REL),
                "validator_refs": list(PRODUCER_VALIDATORS["subject-temporal-public-v1"]),
            },
            "aemh_match_history": {
                "contract_id": "aemh-match-history-public-v1",
                "schema_version": aemh_schema["schema_version"],
                "schema_raw_sha256": raw_sha(ROOT / AEMH_SCHEMA_REL),
                "validator_refs": list(PRODUCER_VALIDATORS["aemh-match-history-public-v1"]),
            },
        },
        "authority_model": {
            "serialized_input_authority": "AuthorityBundleV02",
            "typed_decoder_is_lossless_not_independent_authority": True,
            "public_packet_is_output_authority": True,
            "candidate_output_as_input_forbidden": True,
            "accepted_producer_builders": [
                "subject_temporal_public.build_subject_temporal_authority",
                "aemh_match_history_public.build_aemh_match_history_authority",
            ],
            "accepted_producer_validators": [
                "subject_temporal_public.validate_subject_temporal_authority",
                "aemh_match_history_public.validate_aemh_match_history_authority",
            ],
            "fallback_policy": "fail_closed_no_nearest",
        },
        "objects": objects,
        "exact_keys_recursive": True,
        "additional_properties": False,
        "enums": enums,
        "core_object_names": sorted(CORE_OBJECTS),
        "navigation_object_names": [
            "S5SelectionAnchor",
            "S5SharedTemporalContext",
            "S5ViewBinding",
            "S5SubjectWorkspaceContract",
        ],
        "audience_constants": {
            **audience,
            "domain_subtype_unknown_pair_policy": "fail_closed",
            "other_domain_policy": "forbidden",
            "unknown_domain_policy": "fail_closed_to_domain_confirmation_surface",
            "not_applicable_vs_not_provided_distinct": True,
            "constant_derivation": {
                "source_contracts": [STAGE_CONTRACT_ID, PARENT_CONTRACT_ID],
                "concrete_stage_rows_and_parent_policy_only": True,
                "schema_descriptors_and_invariant_predicates_are_not_scalar_authority": True,
                "source_spans_and_parent_hashes_are_frozen": True,
                "validator_ref": f"{GENERATOR_REL.as_posix()}:validate_parent_derived_constants",
            },
        },
        "shared_temporal_spine_contract": {
            "one_spine_across_views": True,
            "views": ["journey", "profile", "timeline"],
            "shared_fields": [
                "spine_ref",
                "axis_mode",
                "window_start",
                "window_end",
                "selection_anchor",
                "selected_event_ref",
                "selected_risk_anchor_ref",
                "selected_visit_ref",
            ],
            "view_bindings_must_share_context_ref": True,
            "actual_calendar_axis_default": True,
            "study_day_is_explicit_projection": True,
            "nominal_actual_unscheduled_visit_axes_not_absorbed": True,
            "date_state_preservation": ["exact", "partial", "conflicted", "missing"],
            "missing_or_conflicted_date_not_fabricated": True,
            "partial_or_conflicted_range_preserved": True,
            "ui_state_is_not_identity_authority": True,
        },
        "aemh_append_only_contract": {
            "original_reminder_retained": True,
            "later_recorded_fact_retained": True,
            "history_order": "seq_and_prior_entry_hash",
            "previous_prefix_retained": True,
            "identity_evidence_retained": True,
            "automatic_closure_forbidden": True,
            "identity_rewrite_forbidden": True,
            "match_states": ["exact", "ambiguous", "rejected"],
        },
        "hash_recipes": {
            "canonical_json": "UTF-8 JSON; NFC strings; sorted object keys; no insignificant whitespace; declared array order preserved",
            "producer_identity": "accepted producer packet and receipt hash recipes pinned by the accepted public schemas",
            "s5_navigation_content_hash": "sha256(canonical_json(all exact object fields except content_hash))",
            "s5_context_ref": "sha256(canonical_json({authority_receipt_ref,spine_ref,axis_mode,window_start,window_end,selection_anchor,selected_event_ref,selected_risk_anchor_ref,selected_visit_ref}))",
            "s5_view_binding_hash": "sha256(canonical_json(all exact S5ViewBinding fields except content_hash))",
            "s5_workspace_hash": "sha256(canonical_json(all exact S5SubjectWorkspaceContract fields except content_hash; view_bindings sorted by view))",
        },
        "source_leaf_matrix_content_hash": matrix["matrix_content_hash"],
        "challenge_registry_content_hash": challenges["registry_content_hash"],
        "typed_authority_upstream": {
            "typed_contract_content_hash": typed_authority["counts"]["contract_content_hash"],
            "typed_leaf_derivation_count": typed_authority["counts"]["leaf_derivations"],
            "typed_record_count": typed_authority["counts"]["typed_records"],
            "temporal_schema_version": temporal_schema["schema_version"],
            "temporal_recipe_count": len(temporal_recipes["executable_v02_recipes"]),
            "temporal_positive_path_count": temporal_fixtures["positive_valid_count"],
        },
        "parent_compatibility_policy": {
            "lossy_shallow_parent_objects_not_emitted_as_s5_authority": [
                "R5AEMHMatchHistory",
                "R5JourneyEvent",
                "R5PendingDateItem",
                "R5RiskAnchor",
                "R5TemporalSpineProjection",
                "R5VisitNode",
            ],
            "reason": "accepted public packet retains endpoint ranges, cutoff state, append-only entries and source identities that shallow parent fields cannot represent",
            "replacement": "S5 canonical typed objects in source_leaf_matrix.canonical_leaf_rows",
            "no_lossy_null_or_date_collapse": True,
        },
        "invariants": [
            {"id": "accepted_packet_only", "predicate": "only accepted AuthorityBundleV02 builder output may populate core S5 leaves"},
            {"id": "receipt_projection_exact", "predicate": "receipt scope, projection id/content hash and packet content hash bind exactly"},
            {"id": "scope_identity_exact", "predicate": "project/run/site/snapshot/spine/subject/cutoff state stay within one packet scope"},
            {"id": "shared_spine_exact", "predicate": "journey/profile/timeline share one spine/window/selection/anchor context"},
            {"id": "date_geometry_exact", "predicate": "exact, partial, conflicted and missing endpoint states are retained without fabrication"},
            {
                "id": "domain_bijection",
                "predicate": "exactly eight domains; unknown and OTHER fail closed",
                "validator_ref": f"{GENERATOR_REL.as_posix()}:validate_parent_derived_constants",
            },
            {
                "id": "domain_subtype_matrix_exact",
                "predicate": "domain/subtype pairs must be in the exact eight-domain matrix; ae/ip_dose and every unlisted pair fail closed",
                "validator_ref": f"{GENERATOR_REL.as_posix()}:validate_domain_subtype_pair",
            },
            {
                "id": "future_s5_cross_domain_validator",
                "predicate": "future S5 validator rejects domain=ae, subtype=ip_dose with DOMAIN_SUBTYPE_MISMATCH before projection acceptance",
                "validator_ref": future_runtime_validation_contract()["validator_path"] + ":" + future_runtime_validation_contract()["validator_function"],
                "test_locator": future_runtime_validation_contract()["test_path"],
                "required": True,
                "runtime_absent_until_fresh_acceptance": True,
            },
            {"id": "non_color_encoding", "predicate": "event/risk distinction and domain shape/label/line style are explicit; risk overlay never an event shape"},
            {
                "id": "severity_no_promotion",
                "predicate": "high never becomes critical without accepted upstream critical",
                "validator_ref": f"{GENERATOR_REL.as_posix()}:validate_parent_derived_constants",
            },
            {
                "id": "legacy_severity_mapping_exact",
                "predicate": "severe maps to high, moderate to medium, mild to low; unknown legacy severity fails closed",
                "validator_ref": f"{GENERATOR_REL.as_posix()}:validate_legacy_severity",
            },
            {"id": "legacy_treatment_fail_closed", "predicate": "background/non-drug treatment requires an accepted mapping or remains unmapped_fail_closed"},
            {
                "id": "parent_derived_constant_closure",
                "predicate": "presentation constants are non-core; concrete labels/shapes/line styles/terms bind exact accepted stage rows and parent policy objects with raw/content hashes; schema descriptors and predicates are not scalar authority",
                "validator_ref": f"{GENERATOR_REL.as_posix()}:validate_parent_derived_constants",
            },
            {
                "id": "clinical_public_leaf_authority",
                "predicate": "clinical, identity, date, domain-event and history leaves remain core and resolve to accepted executable public packet paths and producer validators",
            },
            {"id": "aemh_append_only", "predicate": "original reminder, later facts, identity evidence and prefix history are retained"},
            {"id": "no_automatic_closure", "predicate": "AEMH matching never closes or rewrites the source risk/identity"},
            {"id": "no_nearest_fallback", "predicate": "identity or source mismatch emits no adjacent subject/site/event"},
            {"id": "navigation_non_authority", "predicate": "window/selection/UI state can bind only to verified packet members and cannot rewrite medical authority"},
            {"id": "unlock_boundary", "predicate": "contract acceptance unlocks only the exact future synthetic/offline runtime allowlist"},
        ],
        "performance_profile_for_future_runtime_only": {
            "synthetic_dataset": {"events": 1000, "metrics": 40, "risk_anchors": 300},
            "shared_selection_update_p95_ms": 100,
            "browser_and_8911_acceptance": "not_in_scope_at_contract_stage",
        },
        "future_runtime_allowlist_ref": "manifest.future_runtime_allowlist",
        "future_runtime_surface_scan_ref": "manifest.runtime_surface_scan",
        "future_runtime_validation_contract": future_runtime_validation_contract(),
        "acceptance": {
            "required_token": ACCEPTANCE_TOKEN,
            "eligible_only_when": [
                "deferred_core_leaf_count == 0",
                "placeholder_core_leaf_count == 0",
                "self_signed_core_leaf_count == 0",
                "independent_verifier_passes_normal_O_O_and_replay_gates",
                "fresh_isolated_review_or_conference_decision_bound_to_frozen_hashes",
                "8911_stopped",
                "medical_writing_boundary_unchanged",
            ],
            "fresh_isolated_acceptance_record": {
                "required": True,
                "decision": ACCEPTANCE_TOKEN,
                "must_bind_exactly": [
                    "contract_content_hash",
                    "manifest_content_hash",
                    "generator_raw_sha256",
                    "verifier_raw_sha256",
                    "generated_artifact_raw_sha256",
                    "acceptance_token",
                ],
                "external_record_only": True,
                "verifier_self_hash_inside_own_source_forbidden": True,
            },
            "worker_self_acceptance": False,
            "acceptance_token_emitted": False,
            "does_not_accept": [
                "S5 runtime",
                "UI",
                "browser",
                "real projects",
                "real models",
                "clinical truth",
                "product or production",
                "medical-writing subsystem",
                "security design or testing",
            ],
        },
        "contract_content_hash": None,
    }
    return exact


def make_manifest(
    exact: dict[str, Any],
    matrix: dict[str, Any],
    challenges: dict[str, Any],
    upstream: dict[str, Any],
    verifier_raw_sha256: str,
) -> dict[str, Any]:
    future = [
        {
            "path": rel,
            "create_only": True,
            "present": (ROOT / rel).exists(),
            "kind": "synthetic_offline_runtime_or_test",
            "allowed_only_after": ACCEPTANCE_TOKEN,
            "real_project_or_model": False,
            "starts_8911": False,
            "medical_writing": False,
        }
        for rel in FUTURE_RUNTIME_ALLOWLIST
    ]
    return {
        "schema": "medical-monitoring-r5-s5-subject-workspace-contract-manifest-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "status": "candidate_unaccepted",
        "self_acceptance": False,
        "acceptance_token_emitted": False,
        "acceptance_token": ACCEPTANCE_TOKEN,
        "exact_owned_paths": [p.as_posix() for p in OWNED_REL],
        "expected_complete_paths": [p.as_posix() for p in EXPECTED_REL],
        "worker_verifier_path": VERIFIER_REL.as_posix(),
        "file_raw_sha256": None,
        "input_raw_sha256": upstream["raw_sha256"],
        "input_content_identities": {
            PARENT_EXACT_REL.as_posix(): exact["parent_contract"]["content_sha256"],
            SUBJECT_SCHEMA_REL.as_posix(): digest(load_json(SUBJECT_SCHEMA_REL)),
            AEMH_SCHEMA_REL.as_posix(): digest(load_json(AEMH_SCHEMA_REL)),
            TEMPORAL_SCHEMA_REL.as_posix(): digest(load_json(TEMPORAL_SCHEMA_REL)),
            TEMPORAL_RECIPES_REL.as_posix(): digest(load_json(TEMPORAL_RECIPES_REL)),
            TEMPORAL_FIXTURES_REL.as_posix(): digest(load_json(TEMPORAL_FIXTURES_REL)),
            TYPED_AUTHORITY_REL.as_posix(): exact["typed_authority_upstream"]["typed_contract_content_hash"],
            PUBLIC_IMPL_MANIFEST_REL.as_posix(): load_json(PUBLIC_IMPL_MANIFEST_REL)["manifest_content_hash"],
        },
        "accepted_authority_pins": {
            "parent_r5_v0_3": exact["parent_contract"],
            "public_authority_producer_acceptance_record": upstream["raw_sha256"][
                "context/medical_monitoring_r5_s5_public_authority_producers_v0_1_acceptance_record_20260826.md"
            ],
            "public_authority_implementation_manifest_content_hash": load_json(PUBLIC_IMPL_MANIFEST_REL)["manifest_content_hash"],
            "typed_authority_manifest_content_hash": load_json(TYPED_MANIFEST_REL)["manifest_content_hash"],
            "public_authority_evidence_content_hash": digest(load_json(PUBLIC_EVIDENCE_REL)),
            "accepted_public_authority_producer_raw_sha256": upstream["accepted_public_authority_pins"],
        },
        "accepted_public_authority_producer_raw_sha256": upstream["accepted_public_authority_pins"],
        "runtime_surface_scan": upstream["runtime_surface_scan"],
        "counts": {
            "canonical_leaf_count": matrix["counts"]["canonical_leaf_count"],
            "core_leaf_count": matrix["counts"]["core_leaf_count"],
            "deferred_core_leaf_count": matrix["counts"]["deferred_core_leaf_count"],
            "placeholder_core_leaf_count": 0,
            "self_signed_core_leaf_count": 0,
            "parent_leaf_count": matrix["counts"]["parent_leaf_count"],
            "parent_replaced_leaf_count": matrix["counts"]["parent_replaced_leaf_count"],
            "challenge_row_count": challenges["row_count"],
            "unique_single_mutation_tuple_count": challenges["unique_single_mutation_tuple_count"],
            "domain_count": len(exact["enums"]["domain"]),
            "presentation_leaf_count": matrix["counts"]["presentation_leaf_count"],
            "future_runtime_allowlist_count": len(future),
        },
        "core_leaf_gate": {
            "deferred": matrix["deferred_core_leaf_ids"],
            "placeholder": [],
            "self_signed": [],
            "eligible_for_independent_review": True,
        },
        "future_runtime_allowlist": future,
        "future_runtime_validation_contract": future_runtime_validation_contract(),
        "public_authority_producer_allowlist": sorted(ACCEPTED_PUBLIC_AUTHORITY_PINS),
        "protected_boundaries": {
            "port_8911": "stopped_required",
            "medical_writing_file_count": upstream["public_evidence_protected_boundaries"]["medical_writing_file_count"],
            "medical_writing_inventory_sha256": upstream["public_evidence_protected_boundaries"]["medical_writing_inventory_sha256"],
            "accepted_inputs_immutable": True,
            "producer_runtime_not_created_by_worker_01": True,
        },
        "unlock": {
            "on_fresh_acceptance": "only future_runtime_allowlist create-only synthetic/offline paths",
            "requires_all": [
                ACCEPTANCE_TOKEN,
                "independent verifier normal/O/OO",
                "negative and replay gates",
                "fresh isolated review or conference decision",
                "decision binds exact.contract_content_hash",
                "decision binds manifest.manifest_content_hash",
                "decision binds manifest.file_raw_sha256[tools/generate_medical_monitoring_r5_s5_subject_workspace_contract_v0_1.py]",
                "decision binds manifest.file_raw_sha256[tools/verify_medical_monitoring_r5_s5_subject_workspace_contract_v0_1.py]",
                "decision binds all generated artifact raw hashes",
                "stopped port 8911",
                "unchanged medical-writing boundary",
            ],
            "fresh_isolated_acceptance_record": {
                "required": True,
                "decision": ACCEPTANCE_TOKEN,
                "binds": [
                    "exact.contract_content_hash",
                    "manifest.manifest_content_hash",
                    "manifest.file_raw_sha256[generator]",
                    "manifest.file_raw_sha256[verifier]",
                    "manifest.file_raw_sha256[all_owned_generated_artifacts]",
                    "acceptance_token",
                ],
                "external_record_only": True,
                "verifier_self_hash_inside_own_source_forbidden": True,
            },
            "does_not_unlock": [
                "8911",
                "UI or browser",
                "real projects or models",
                "product or production",
                "medical-writing",
                "accepted producer mutation",
                "security work",
            ],
        },
        "manifest_hash_recipe": "sha256(canonical_json(all manifest fields except manifest_content_hash))",
        "verifier_raw_sha256": verifier_raw_sha256,
        "manifest_content_hash": None,
    }


def context_text(exact: dict[str, Any], matrix: dict[str, Any], challenges: dict[str, Any], manifest: dict[str, Any]) -> str:
    return f"""# R5-S5 Subject Workspace / Patient Journey Contract v0.1 Context

日期：2026-08-26

## 当前状态

本批次只冻结 renderer-neutral 的 R5-S5 Subject Workspace / Patient Journey
typed contract；不创建 S5 runtime、test、UI、browser、service 或产品文件。
当前文件是候选快照，worker-01 不发出 `{ACCEPTANCE_TOKEN}`，最终接受仍需
独立 verifier 和 fresh isolated review。

## 权威链

- R5 v0.3 exact contract：`{PARENT_EXACT_REL.as_posix()}`，父合同 raw/content SHA
  由 manifest 固定。
- Subject temporal 公共包：`subject-temporal-public-v1`。
- AE/MH match-history 公共包：`aemh-match-history-public-v1`。
- 两个公共包只接受冻结 `AuthorityBundleV02` 输入；candidate packet、fixture
  文本/计数、case id、文件名、未绑定 hash、nearest record 和 UI state 均不是医学或
  身份权威。

## S5 contract closure

- canonical leaves：{matrix['counts']['canonical_leaf_count']}；core authority leaves：{matrix['counts']['core_leaf_count']}。
- deferred core：{matrix['counts']['deferred_core_leaf_count']}；placeholder core：0；self-signed core：0。
- parent v0.3 leaves：{matrix['counts']['parent_leaf_count']}，其中 {matrix['counts']['parent_replaced_leaf_count']} 个
  S5 deferred/shallow leaves 被明确替换为完整 typed packet leaves；不能表达 cutoff absent、日期范围或
  append-only history 的浅对象不会被误当成 S5 authority。
- challenge rows：{challenges['row_count']}（父合同 204 行、S5 专项 {challenges['counts']['s5_contract_specific_rows']} 行、
  accepted public replay {challenges['counts']['accepted_public_replay_rows']} 行）。这些行仅是测试元数据。
- 每一行都冻结 executable `single_mutation(op/path/value)` 与 `oracle_contract(rule_id/expected_outcome/expected_error/expected_projection/required_non_llm_anchor/test_locator)`；
  structured mutation/oracle rows：{challenges['structured_mutation_row_count']}/{challenges['structured_oracle_row_count']}，S5 专项不使用 alias 或 placeholder mutation。
- presentation leaves：{matrix['counts']['presentation_leaf_count']}；它们是 S5-owned non-core renderer vocabulary，均明确
  `acceptance_claim=false`。域标签/形状/线型、禁词和 subtype 列表绑定 accepted R5 stage review 的精确 Markdown 行/段落，
  同时冻结 stage raw SHA、parent raw SHA 和 parent content SHA；legacy treatment 只绑定 parent 的实际
  `/legacy_domain_policy/<kind>` 对象。不存在 `/contract_constants/*` pseudo-selector，也不把 schema descriptor/predicate 当标量权威。
- `S5SeverityEncoding.line_weight` 的数值及 `S5AudienceLexicon.content_hash` 未被已接受来源具体冻结，均保留为
  future-renderer parameter，值为 null 且不构成 acceptance claim；clinical/identity/date/domain-event/history leaves
  仍是 core 并只来自 accepted executable public packets。
- 已接受 public-authority producer/test/evidence 的显式 path+SHA pin：{len(manifest['accepted_authority_pins']['accepted_public_authority_producer_raw_sha256'])}；
  manifest input raw pin map：{len(manifest['input_raw_sha256'])}。

## Frozen semantics

一个 shared temporal context 绑定 Journey、Profile 和 Timeline 的同一 spine、axis、window、selection
和 anchor。实际日期轴为默认；study day 是显式投影。exact/partial/conflicted/missing 日期保留完整
endpoint state、candidate values、range 和 projectability，不吸附到名义访视或伪造日期。

域闭集恰好八类：AE、MH、CM、IP 给药、检验与检查、住院与操作、症状与疗效、方案符合性；unknown
和 OTHER fail-closed。不依赖颜色区分 event/risk，risk overlay 与事件形状严格分离。AEMH 保留
原始 reminder、后续 fact、identity evidence、previous prefix 和 append-only sequence；不自动关闭风险，
不重写 identity。
- domain/subtype matrix 是 exact 八域闭集：`ae=ae`、`mh=mh`、`cm=concomitant_medication`、
  `ip=(ip_dose,ip_pause,ip_resume)`、`lab_exam=(lab,exam)`、`hospital_procedure=(hospitalization,procedure)`、
  `symptom_efficacy=(symptom,efficacy,scale,outcome,trend)`、`protocol_compliance=protocol_deviation`；
  `ae/ip_dose` 及所有未列 pair 均 fail-closed。
- legacy severity 只允许 `severe→high`、`moderate→medium`、`mild→low`；unknown value fail-closed。
- future S5 runtime 必须在 projection acceptance 前由 `s5_validator.py::validate_domain_subtype_pair` 拒绝
  `domain=ae, subtype=ip_dose`，错误为 `DOMAIN_SUBTYPE_MISMATCH`、projection 为 `not_emitted`；对应 validator/test/challenge
  仅作为 exact 11-path future allowlist contract 冻结，当前均 absent。

## Boundaries and unlock

8911 必须保持 stopped；medical-writing 的既有保护聚合为 {manifest['protected_boundaries']['medical_writing_file_count']}
文件及其冻结 inventory SHA。即便未来 fresh review 接受本合同，也只允许 manifest 中 exact
`future_runtime_allowlist` 的 synthetic/offline create-only 路径；不解锁 8911、UI/browser、真实项目/模型、
产品/生产、medical-writing、producer mutation 或 security work。
runtime surface scan 覆盖 `{", ".join(manifest['runtime_surface_scan']['roots'])}` 的全部非 cache 文件（冻结
{manifest['runtime_surface_scan']['frozen_file_count']} 个，inventory SHA `{manifest['runtime_surface_scan']['frozen_inventory_content_hash']}`）；
任意新增或改名文件在生成前 fail-closed，future allowlist 恰为 {len(manifest['future_runtime_allowlist'])} 个路径且当前全部 absent。
unlock 还必须由 fresh isolated 外部 review/conference record 绑定 exact contract hash、manifest hash、generator raw SHA、
verifier raw SHA、全部 generated artifact raw SHA 及 exact acceptance token；worker 不自签，verifier 不在自身 source 内自哈希。
"""


def review_text(exact: dict[str, Any], matrix: dict[str, Any], challenges: dict[str, Any], manifest: dict[str, Any]) -> str:
    return f"""# R5-S5 Subject Workspace / Patient Journey Contract v0.1 Review

## Review scope

本文件由 worker-01 generator 生成，供 Codex 和独立 verifier 复核；不是接受记录，
不包含 `{ACCEPTANCE_TOKEN}` verdict。

## Mechanical contract facts

- contract：`{CONTRACT_ID}` / schema `{SCHEMA_VERSION}`。
- canonical typed leaves：{matrix['counts']['canonical_leaf_count']}；core accepted leaves：{matrix['counts']['core_leaf_count']}。
- deferred/placeholder/self-signed core leaves：{matrix['counts']['deferred_core_leaf_count']}/0/0。
- parent mapping rows：{matrix['counts']['parent_leaf_count']}；replaced S5 parent rows：{matrix['counts']['parent_replaced_leaf_count']}。
- challenge registry rows：{challenges['row_count']}；future runtime paths：{len(manifest['future_runtime_allowlist'])}。
- structured executable challenge rows：mutation {challenges['structured_mutation_row_count']} / oracle {challenges['structured_oracle_row_count']}；
  every row has one concrete `op/path/value` mutation and a rule/outcome/error/projection/non-LLM-anchor/test-locator oracle.
- accepted public-authority producer/test/evidence explicit pins：{len(manifest['accepted_authority_pins']['accepted_public_authority_producer_raw_sha256'])}；
  input raw pin map count：{len(manifest['input_raw_sha256'])}。
- presentation leaves：{matrix['counts']['presentation_leaf_count']}，均为 S5-owned non-core renderer vocabulary，
  `acceptance_claim=false`。Concrete domain labels/shapes/line styles, forbidden terms and subtype list bind exact accepted
  stage Markdown rows/spans plus stage raw SHA and parent raw/content SHA；legacy treatment binds actual
  `/legacy_domain_policy/<kind>` objects。Schema descriptors and invariant predicates are never scalar authority，且
  `/contract_constants/*` pseudo-selectors are forbidden。
- `S5SeverityEncoding.line_weight` numeric value and `S5AudienceLexicon.content_hash` remain null future-renderer parameters
  without acceptance claims；clinical/identity/date/domain-event/history leaves remain core accepted public-packet leaves。
- runtime surface：{manifest['runtime_surface_scan']['frozen_file_count']} frozen non-cache files across
  `{", ".join(manifest['runtime_surface_scan']['roots'])}`; inventory SHA `{manifest['runtime_surface_scan']['frozen_inventory_content_hash']}`;
  exact 11 future allowlist paths are absent and arbitrary new paths fail closed.

## Authority review points

1. Core temporal and AEMH fields point to accepted public packet types and named producer validators.
2. Lossy parent objects are marked as compatibility replacements; no cutoff/date/history information is
   silently dropped.
3. Navigation state is typed and hashable but explicitly non-authoritative; selections must be verified
   against the same packet membership and cannot rewrite source identity.
4. Exact eight-domain subtype matrix rejects `ae/ip_dose` and every unlisted pair; legacy severity is exactly
   `severe→high`, `moderate→medium`, `mild→low`, with unknown values fail-closed.
5. Domain, date, severity, lexicon, legacy mapping and non-color encoding are closed and fail-closed.
6. Future exact-allowlist `s5_validator.py::validate_domain_subtype_pair` plus its test/challenge contract must reject
   `domain=ae, subtype=ip_dose` with `DOMAIN_SUBTYPE_MISMATCH` before projection acceptance; all such runtime/test paths remain absent.
7. Acceptance unlock text is exact and excludes 8911, UI/browser, real projects/models, production,
   medical-writing, accepted producer mutation and security work.
8. Fresh isolated acceptance must bind exact/manifest/generator/verifier/all-generated-artifact hashes and the exact token;
   the worker does not emit the token and the verifier cannot self-hash inside its own source.

## Required independent checks

The verifier must rerun generator `--check`, normal/`-O`/`-OO`, deterministic replay, source/path hash
tamper gates, core-leaf zero-deferred gates, challenge realization, protected medical-writing boundary and
stopped-port check. A verifier result is required before any downstream S5 runtime path is created.
"""


def build_all() -> dict[str, bytes]:
    upstream = pin_inputs()
    verifier_path = ROOT / VERIFIER_REL
    if not verifier_path.exists():
        raise SystemExit(f"STOP verifier required for external acceptance binding: {VERIFIER_REL.as_posix()}")
    verifier_raw_sha256 = raw_sha(verifier_path)
    parent = load_json(PARENT_EXACT_REL)
    parent_challenge = load_json(PARENT_CHALLENGE_REL)
    parent_quota = load_json(PARENT_QUOTA_REL)
    subject_schema = load_json(SUBJECT_SCHEMA_REL)
    aemh_schema = load_json(AEMH_SCHEMA_REL)
    temporal_schema = load_json(TEMPORAL_SCHEMA_REL)
    temporal_recipes = load_json(TEMPORAL_RECIPES_REL)
    temporal_fixtures = load_json(TEMPORAL_FIXTURES_REL)
    typed_authority = load_json(TYPED_AUTHORITY_REL)
    stage_text = (ROOT / STAGE_REL).read_text(encoding="utf-8")
    audience_expected = extract_stage_audience_constants(parent, stage_text)
    validate_parent_derived_constants(parent, stage_text, audience_expected)
    validate_future_runtime_contract()

    objects = build_objects(subject_schema, aemh_schema)
    matrix = build_matrix(parent, objects, audience_expected)
    validate_source_leaf_matrix(matrix, parent, subject_schema, aemh_schema, stage_text)
    matrix["matrix_content_hash"] = digest({key: value for key, value in matrix.items() if key != "matrix_content_hash"})
    challenges = build_challenges(parent, parent_challenge, parent_quota)
    challenges["registry_content_hash"] = digest(
        {key: value for key, value in challenges.items() if key != "registry_content_hash"}
    )
    exact = build_exact(
        parent,
        subject_schema,
        aemh_schema,
        temporal_schema,
        temporal_recipes,
        temporal_fixtures,
        typed_authority,
        matrix,
        challenges,
        audience_expected,
    )
    exact["contract_content_hash"] = digest({key: value for key, value in exact.items() if key != "contract_content_hash"})

    manifest = make_manifest(exact, matrix, challenges, upstream, verifier_raw_sha256)
    context = context_text(exact, matrix, challenges, manifest)
    review = review_text(exact, matrix, challenges, manifest)

    output_bytes = {
        EXACT_REL.as_posix(): pretty(exact),
        MATRIX_REL.as_posix(): pretty(matrix),
        CHALLENGE_REL.as_posix(): pretty(challenges),
        CONTEXT_REL.as_posix(): context.encode("utf-8"),
        REVIEW_REL.as_posix(): review.encode("utf-8"),
    }
    output_hashes = {
        rel: hashlib.sha256(data).hexdigest() for rel, data in sorted(output_bytes.items())
    }
    output_hashes[GENERATOR_REL.as_posix()] = raw_sha(ROOT / GENERATOR_REL)
    output_hashes[VERIFIER_REL.as_posix()] = verifier_raw_sha256
    manifest["file_raw_sha256"] = dict(sorted(output_hashes.items()))
    manifest["manifest_content_hash"] = digest(
        {key: value for key, value in manifest.items() if key != "manifest_content_hash"}
    )
    output_bytes[MANIFEST_REL.as_posix()] = pretty(manifest)
    return output_bytes


def write_or_check(expected: dict[str, bytes], check: bool) -> None:
    if check:
        problems = []
        for rel, data in expected.items():
            path = ROOT / rel
            if not path.exists():
                problems.append(f"missing:{rel}")
            elif path.read_bytes() != data:
                problems.append(f"drift:{rel}")
        extra = sorted(
            p.relative_to(ROOT).as_posix()
            for p in ((ROOT / ARTIFACT_DIR).glob("*") if (ROOT / ARTIFACT_DIR).exists() else ())
            if p.is_file() and p.relative_to(ROOT).as_posix() not in expected
        )
        if extra:
            problems.extend(f"extra:{rel}" for rel in extra)
        if problems:
            raise SystemExit("CHECK_FAILED " + ",".join(problems))
        print(f"CHECK_OK files={len(expected)} contract={CONTRACT_ID}")
        return
    for rel, data in expected.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(f"GENERATED files={len(expected)} contract={CONTRACT_ID}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify owned bytes without writing")
    args = parser.parse_args()
    expected = build_all()
    write_or_check(expected, args.check)


if __name__ == "__main__":
    main()
