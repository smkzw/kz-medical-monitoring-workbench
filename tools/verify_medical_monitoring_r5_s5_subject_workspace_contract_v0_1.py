#!/usr/bin/env python3
"""Independently verify the frozen renderer-neutral R5-S5 contract.

This verifier deliberately does not import a producer or an S5 runtime.  It
reconstructs the typed object descriptors, authority paths, parent replacements,
challenge rows, hashes, and boundary values from accepted input documents and
hard-pinned semantic constants.  The challenge registry is contract metadata at
this stage: no S5 runtime exists to execute medical projections.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import unicodedata
from typing import Any


sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1"
EXACT = ARTIFACT_DIR / "exact_contract.json"
MATRIX = ARTIFACT_DIR / "source_leaf_matrix.json"
CHALLENGE = ARTIFACT_DIR / "challenge_registry.json"
MANIFEST = ARTIFACT_DIR / "manifest.json"
GENERATOR = ROOT / "tools/generate_medical_monitoring_r5_s5_subject_workspace_contract_v0_1.py"
VERIFIER = pathlib.Path(__file__).resolve()
GENERATOR_REL = GENERATOR.relative_to(ROOT).as_posix()

CONTRACT_ID = "medical-monitoring-r5-s5-subject-workspace-contract-v0.1"
SCHEMA_VERSION = "2026-08-26.1"
ACCEPTANCE_TOKEN = "ACCEPT_R5_S5_CONTRACT"
PARENT_CONTRACT_ID = "medical-monitoring-r5-exact-contract-v0.3.1"
PARENT_SOURCE_ROOT_TYPE = "R5ExactContract"
STAGE_CONTRACT_ID = "accepted-r5-stage-contract-v0.3"
STAGE_SOURCE_ROOT_TYPE = "AcceptedR5StageContract"
PARENT_EXACT = "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json"
PARENT_CHALLENGES = "artifacts/medical_monitoring_r5_contract_v0_3/challenge_registry.json"
PARENT_QUOTA = "artifacts/medical_monitoring_r5_contract_v0_3/quota_ledger.json"
SUBJECT_SCHEMA = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json"
AEMH_SCHEMA = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json"
TEMPORAL_SCHEMA = "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/schema.json"
TEMPORAL_RECIPES = "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/emitter_recipe_registry.json"
TEMPORAL_FIXTURES = "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json"
TYPED_AUTHORITY = "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1/authority_contract.json"
TYPED_MANIFEST = "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1/manifest.json"
PUBLIC_IMPL_MANIFEST = "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2/manifest.json"
PUBLIC_IMPL_FUTURE = "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2/future_producer_contract.json"
PUBLIC_EVIDENCE = "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_public_authority_readonly_sha256.json"
PRODUCER_ACCEPTANCE = "context/medical_monitoring_r5_s5_public_authority_producers_v0_1_acceptance_record_20260826.md"
STAGE_REVIEW = "reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md"

OWNED_PATHS = (
    "context/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_20260826_context.md",
    "reviews/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_20260826.md",
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/exact_contract.json",
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/source_leaf_matrix.json",
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/challenge_registry.json",
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/manifest.json",
    "tools/generate_medical_monitoring_r5_s5_subject_workspace_contract_v0_1.py",
)
EXPECTED_COMPLETE_PATHS = (*OWNED_PATHS, "tools/verify_medical_monitoring_r5_s5_subject_workspace_contract_v0_1.py")

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

# These are independent constants, not values read from the candidate
# manifest.  The public evidence document below is itself pinned here; its
# 29 source-file hashes are then replayed independently.
EXPECTED_INPUT_PINS = {
    "context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md": "2868e1977250532e6bc51fc426f224e4f28b8556cf8ce9ad5d8a0392ccb404a8",
    "reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md": "1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6",
    "context/medical_monitoring_r5_s4_acceptance_record_20260819.md": "1d17297c44b371aefecf28cfc2388181b7be35d9e5cc830b148a0b3a9da1971e",
    "context/medical_monitoring_r5_s5_public_authority_producers_v0_1_acceptance_record_20260826.md": "76ec09525bc37a3efc4112bae5b5d1e11b9b9fc46a0b9c04c5a19ba0902364c2",
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2_acceptance_record_20260825.md": "d6d9b4dad6a8b9c8501d6c8ccfcd71cf1f3f682b40be3ecd3cf10efea7364981",
    "context/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1_acceptance_record_20260825.md": "b509de3edb6111da19977cc8aa7741160aa04366dbd5565bb746fe633ffd46e6",
    "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2_acceptance_record_20260821.md": "d08b4ed27f9829db4cdcab0837f3623c244ee8c888cce699c55580621bd68ef4",
    "context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md": "23fed5b186057a79cd0ec43a7718e43934ebafdc8f62fd251077d4fb6891639d",
    PARENT_EXACT: "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949",
    PARENT_CHALLENGES: "ef459f58ad6997a823c3ff57d51256cdf531b806d9033df636ab2912085b0887",
    PARENT_QUOTA: "aeec1482b1c374d175a89660dd11cc312b6ba2612cf6c5a709379f2b05163b37",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json": "92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270",
    SUBJECT_SCHEMA: "d2f56f21dc7b228736b2efbdc4c1db3a28185e25895563c0b59a812cd126a0f4",
    AEMH_SCHEMA: "479dc2759833d698fd761247f4ec504069880717ec9c64631242ad2554b19840",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/manifest.json": "466b0ae605b83a57f0e184446db311beb05ff5e4e1998a7dc5be9bb44d2b7de8",
    TEMPORAL_SCHEMA: "74617b858f961f3af615b3d96a51625427faeecfac8c5a4011ecac4fd79dabbc",
    TEMPORAL_RECIPES: "e7a8d5246d71e7b2baece0d21909518426da6d3799bfd6913d4fefa81729bf39",
    TEMPORAL_FIXTURES: "f9bf0c8031d3acba615b5ac147c27866c8a7430154a0bb98fc24314619009ae7",
    TYPED_AUTHORITY: "bc0c60db30721401315605f69b1d6e3c0e26b39161ea3135f1fcc547828c09cc",
    TYPED_MANIFEST: "a71f0937dd5d0a0fc77de98b41f6308b5caed0ae7d460f0282884c56127cd22c",
    PUBLIC_IMPL_MANIFEST: "f3fcb4172dd74d9c8c1fff16fbda1a516caf41447d08b6c5637fde0fd403ecc8",
    PUBLIC_IMPL_FUTURE: "09ead56dc8989c469fc9aa4912c40e0c9bf8e896063a340b2dd209a851571124",
    PUBLIC_EVIDENCE: "8a0d0935a21e569cef078a08ff084367aa401c2e188f50d9ada7e77c9b734058",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s4_readonly_sha256.json": "53a927a08451b426edb9ac9578a6ea3b658ff8df1d5dd2b33f94fb0446647822",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_readonly_sha256.json": "d5fe8b44edaf86f8a5aa611cc23011526479c87d24c47efd347e6b20525b6d89",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_s2_readonly_sha256.json": "6cec5b39fe325bf644e2ae31174a5175b2ad94e190d98cb43b00b33636ff21af",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_s3_readonly_sha256.json": "f217f66a0ffbeb5e5b37d85e056aad6c218d1979e023e4a55dc13b33354e3a77",
}

EXPECTED_OUTPUT_SHA = {
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/challenge_registry.json": "e5143edda759685fccedd9c696429454f2e1924175171d89f7c3948e5d61f00c",
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/exact_contract.json": "5b674b16159295052afb56a0736dc8fc87a6070a0ea5524a2b8bfc7850d29cac",
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/source_leaf_matrix.json": "551a9c34a6c99f468d80a4dec3c5ee508d354167b06d92c9c02e0d654534d8d3",
    "context/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_20260826_context.md": "3d5410c85d3ab2426bd599c228f5d58b910ec719ea9970f4bb51bed0a6ae6327",
    "reviews/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_20260826.md": "edd6b0e0f686c7842a8fe20bd3efb1baaac098842f0f0b3576d00c06eafed22a",
    GENERATOR_REL: "bb7aec3b9a5efe80dc83fe45ea95f650d44dbaf0566fcd4d8f7f33bbffe6a74f",
}
EXPECTED_EVIDENCE_CONTENT_HASH = "858df4875324543d81cf048a332ef7bf1d642177805da59a2694c69e73848dff"
EXPECTED_MEDICAL_WRITING_COUNT = 542
EXPECTED_MEDICAL_WRITING_INVENTORY = "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca"

EXPECTED_ACCEPTED_PUBLIC_PINS = {
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py": "4767e28ab7e54a4fbc89e3e30a12448467597cdadfc06833f11158bc2aa54b4c",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py": "0a519d6b93dee9bc06930707eed7f6b7f2be180fe2b35dc25d23ccf8ce918be7",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py": "3463eedf0bad35596f9b1f28c9479c76fb0cffaf5977766e812839e342bd3243",
    "poc/medical_monitoring_ai_native_r5/tests/public_authority_runtime_fixtures.py": "a4b9a2d681ca280ea344d36591eb7875e032dcf7e4b9209be34ba7bf5972c794",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py": "eeffbcf0c07c130e3cb05f3ac19ba3f2698de6461344812c18c1c083234b0aa3",
    "poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py": "2aa3b626cfd0feda9a70a7416f564955a9c7378e66e26a8c2b2682bd9a20bb8c",
    "poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py": "c8b3afefc49d3fc62eecf072f23b7a82d9bab2c5ae35852f482a19b9b618702d",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py": "15a3de48c22e7417dd0b1159f5d696d90730c080856b3dda04a8ea552ef99e64",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_readonly_gate.py": "e5c9cdb5ff9989b1e8057a1624c618a4cdc93715275f3fd51a992ae395ef6299",
    "poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py": "f6bee54e92820e48cd8a3b3111261308e639a3f61609b1c4b24073f8ef6e61b2",
    PUBLIC_EVIDENCE: "8a0d0935a21e569cef078a08ff084367aa401c2e188f50d9ada7e77c9b734058",
}

RUNTIME_SURFACE_ROOTS = (
    "poc/medical_monitoring_ai_native_r5/src/mm_r5",
    "poc/medical_monitoring_ai_native_r5/tests",
    "poc/medical_monitoring_ai_native_r5/evidence",
)
RUNTIME_SURFACE_BASELINE_HASH = "d94c9e7203572519f9db92c219d4f18a9b76fdd3af0fd8a60b98b85120ecb915"
RUNTIME_SURFACE_IGNORED_CACHE_RULES = ("*/__pycache__/*", "*.pyc", "*.pyo")

SUBJECT_MAP = {
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
AEMH_MAP = {
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
CORE_OBJECTS = {
    "S5AuthorityReceipt", "S5CutoffEndpoint", "S5ScopeIdentity", "S5SourceLocator",
    "S5SourceRevisionContentPair", "S5VisibilityClosure", "S5DateEndpoint", "S5AxisBasis",
    "S5DomainTrack", "S5JourneyEvent", "S5MembershipIndex", "S5PendingDateItem",
    "S5PhaseBand", "S5RiskAnchor", "S5VisitNode", "S5SubjectTemporalProjection",
    "S5SubjectTemporalPacket", "S5AEMHMembershipIndex", "S5AEMHIdentityEvidence",
    "S5AEMHHistoryEntry", "S5AEMHPrefixAnchor", "S5AEMHThread", "S5AEMHProjection",
    "S5AEMHPacket",
}
PRESENTATION_OBJECTS = {
    "S5DomainEncodingItem", "S5SeverityEncoding", "S5LegacyTreatmentMapping",
    "S5AudienceLexicon", "S5AudienceEncodingRegistry",
}
NAVIGATION_OBJECTS = ["S5SelectionAnchor", "S5SharedTemporalContext", "S5ViewBinding", "S5SubjectWorkspaceContract"]
DOMAINS = ["ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure", "symptom_efficacy", "protocol_compliance"]
JOURNEY_SUBTYPES = [
    "ae", "mh", "concomitant_medication", "ip_dose", "ip_pause", "ip_resume", "lab", "exam",
    "hospitalization", "procedure", "symptom", "efficacy", "scale", "outcome", "trend", "protocol_deviation",
]
SYMPTOM_SUBTYPES = ["symptom", "efficacy", "scale", "outcome", "trend"]
DOMAIN_SUBTYPE_MATRIX = {
    "ae": ["ae"],
    "mh": ["mh"],
    "cm": ["concomitant_medication"],
    "ip": ["ip_dose", "ip_pause", "ip_resume"],
    "lab_exam": ["lab", "exam"],
    "hospital_procedure": ["hospitalization", "procedure"],
    "symptom_efficacy": SYMPTOM_SUBTYPES,
    "protocol_compliance": ["protocol_deviation"],
}
LEGACY_SEVERITY_MAPPING = [
    {"legacy_value": "severe", "severity": "high"},
    {"legacy_value": "moderate", "severity": "medium"},
    {"legacy_value": "mild", "severity": "low"},
]
FORBIDDEN_TERMS = ["已记录事项", "正式事实", "候选信号", "通用风险点", "只读xx", "Checklist", "待行动", "未读"]
COMMON_FORBIDDEN = ["fixture_text", "fixture_count", "case_id", "filename", "unbound_hash", "nearest_record", "ui_state", "candidate_output"]
DOMAIN_ENCODING = [
    {"domain": "ae", "short_label_zh": "AE", "event_shape": "rounded_rect", "line_style": "solid"},
    {"domain": "mh", "short_label_zh": "MH", "event_shape": "bookmark", "line_style": "dot_dash"},
    {"domain": "cm", "short_label_zh": "合并用药", "event_shape": "capsule", "line_style": "solid"},
    {"domain": "ip", "short_label_zh": "试验药", "event_shape": "hexagon", "line_style": "step"},
    {"domain": "lab_exam", "short_label_zh": "检验/检查", "event_shape": "square", "line_style": "trend"},
    {"domain": "hospital_procedure", "short_label_zh": "住院/操作", "event_shape": "doorframe", "line_style": "solid"},
    {"domain": "symptom_efficacy", "short_label_zh": "症状/疗效", "event_shape": "circle", "line_style": "trend"},
    {"domain": "protocol_compliance", "short_label_zh": "方案符合", "event_shape": "single_flag", "line_style": "bracket"},
]
SEVERITY_ENCODING = [
    {"severity": "critical", "label_zh": "紧急", "line_weight": None},
    {"severity": "high", "label_zh": "高", "line_weight": None},
    {"severity": "medium", "label_zh": "中", "line_weight": None},
    {"severity": "low", "label_zh": "低", "line_weight": None},
]
PRODUCER_VALIDATORS = {
    "subject-temporal-public-v1": [
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py:build_subject_temporal_authority",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py:validate_subject_temporal_authority",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py:authority_issues",
    ],
    "aemh-match-history-public-v1": [
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py:build_aemh_match_history_authority",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py:validate_aemh_match_history_authority",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py:authority_issues",
    ],
}

EXPECTED_ENUMS = {
    "domain": DOMAINS,
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
    "severity": ["critical", "high", "medium", "low"],
    "match_state": ["exact", "ambiguous", "rejected"],
    "journey_subtype": JOURNEY_SUBTYPES,
    "symptom_efficacy_subtype": SYMPTOM_SUBTYPES,
    "event_shape": ["rounded_rect", "bookmark", "capsule", "hexagon", "square", "doorframe", "circle", "triangle", "single_flag"],
    "line_style": ["solid", "dashed", "dot_dash", "step", "trend", "bracket"],
    "legacy_treatment_kind": ["background_treatment", "non_drug_treatment"],
    "legacy_mapping_state": ["mapped", "unmapped_fail_closed"],
    "source_locator_variant": ["r4_source_locator", "d08_source_locator"],
    "visibility_state": ["projectable", "hidden", "not_evaluable"],
    "s5_anchor_kind": ["none", "event", "risk_anchor", "visit", "source_locator"],
    "s5_view": ["journey", "profile", "timeline"],
    "s5_projection_kind": ["subject_temporal", "aemh_history"],
}

STAGE_DOMAIN_LABELS = {
    "AE": "ae", "MH": "mh", "CM": "cm", "IP 给药": "ip",
    "检验与检查": "lab_exam", "住院与操作": "hospital_procedure",
    "症状与疗效": "symptom_efficacy", "方案符合性": "protocol_compliance",
}
STAGE_SHAPE_TOKENS = (
    ("圆角矩形", "rounded_rect"), ("书签形", "bookmark"), ("胶囊形", "capsule"),
    ("六边形", "hexagon"), ("方形", "square"), ("门框形", "doorframe"),
    ("圆点", "circle"), ("旗标形", "single_flag"),
)
STAGE_LINE_TOKENS = (
    ("阶梯线", "step"), ("括号区间", "bracket"), ("趋势线", "trend"),
    ("折线", "trend"), ("粗区间", "solid"), ("细实线", "solid"),
    ("点划", "dot_dash"), ("实线", "solid"),
)
SUBTYPE_STAGE_TOKENS = {
    "ae": "AE", "mh": "MH", "concomitant_medication": "合并用药",
    "ip_dose": "给药", "ip_pause": "暂停", "ip_resume": "恢复",
    "lab": "检验", "exam": "检查", "hospitalization": "住院",
    "procedure": "操作", "protocol_deviation": "方案符合",
}
STAGE_SYMPTOM_SUBTYPE_LABELS = {
    "症状": "symptom", "疗效": "efficacy", "量表": "scale", "结局": "outcome", "趋势": "trend",
}
FUTURE_RUNTIME_VALIDATION_CONTRACT = {
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

PARENT_REPLACEMENTS = {
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
    "R5AuthorityReceipt": {"public_projection_kind": ["S5AuthorityReceipt.receipt_variant"]},
}

S5_CHALLENGE_SPECS = (
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
REPLAY_CASES = ("R5C-109", "R5C-110", "R5C-116", "R5C-157", "R5C-158", "R5C-159", "R5C-160", "R5C-161", "R5C-162", "R5C-163")
CHALLENGE_MUTATION_OPS = {"replace", "remove", "replay"}
CHALLENGE_ORACLE_KEYS = {
    "rule_id", "expected_outcome", "expected_error", "expected_projection",
    "required_non_llm_anchor", "test_locator",
}
CHALLENGE_PLACEHOLDER_MARKERS = ("alias", "placeholder", "todo", "tbd", "<path>", "<value>")


class VerificationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise VerificationError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def canonicalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized = unicodedata.normalize("NFC", str(key))
            require(normalized not in result, f"canonical duplicate key:{normalized}")
            result[normalized] = canonicalize(item)
        return result
    fail(f"unsupported canonical type:{type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel_path(path: pathlib.Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_json(relative: str) -> Any:
    path = ROOT / relative
    require(path.is_file(), f"missing input:{relative}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"invalid json:{relative}:{exc}")


def verify_pins(evidence: dict[str, Any]) -> dict[str, str]:
    for relative, expected in sorted(EXPECTED_INPUT_PINS.items()):
        path = ROOT / relative
        require(path.is_file(), f"missing pinned input:{relative}")
        require(raw_sha(path) == expected, f"pinned input drift:{relative}")
    require(evidence.get("schema") == "medical-monitoring-r5-s5-public-authority-readonly-sha256-evidence-v1", "public evidence schema")
    evidence_files = evidence.get("files")
    require(isinstance(evidence_files, dict) and len(evidence_files) == 29, "public evidence file count")
    for relative, expected in sorted(evidence_files.items()):
        require(isinstance(relative, str) and isinstance(expected, str), "public evidence entry type")
        path = ROOT / relative
        require(path.is_file(), f"missing public evidence source:{relative}")
        require(raw_sha(path) == expected, f"public evidence source drift:{relative}")
    for relative, expected in sorted(EXPECTED_ACCEPTED_PUBLIC_PINS.items()):
        path = ROOT / relative
        require(path.is_file(), f"missing accepted public-authority pin:{relative}")
        require(raw_sha(path) == expected, f"accepted public-authority pin drift:{relative}")
    combined = dict(EXPECTED_INPUT_PINS)
    combined.update(evidence_files)
    combined.update(EXPECTED_ACCEPTED_PUBLIC_PINS)
    return dict(sorted(combined.items()))


def descriptor(type_name: str, cardinality: str = "one", nullable: bool = False) -> dict[str, Any]:
    return {"cardinality": cardinality, "nullable": nullable, "type": type_name}


def remap_type(value: str, object_map: dict[str, str]) -> str:
    if value in object_map:
        return object_map[value]
    return {"string": "str", "boolean": "bool", "integer": "int"}.get(value, value)


def clone_source_object(schema: dict[str, Any], name: str, object_map: dict[str, str]) -> dict[str, Any]:
    source = schema["objects"].get(name)
    require(isinstance(source, dict), f"missing source object:{name}")
    return {
        key: descriptor(remap_type(spec["type"], object_map), spec["cardinality"], spec["nullable"])
        for key, spec in source.items()
    }


def expected_objects(subject: dict[str, Any], aemh: dict[str, Any]) -> dict[str, dict[str, Any]]:
    objects: dict[str, dict[str, Any]] = {}
    for source, target in SUBJECT_MAP.items():
        objects[target] = clone_source_object(subject, source, SUBJECT_MAP)
    for source, target in AEMH_MAP.items():
        objects[target] = clone_source_object(aemh, source, AEMH_MAP)
    objects.update({
        "S5SelectionAnchor": {
            "anchor_kind": descriptor("enum:s5_anchor_kind"), "anchor_ref": descriptor("str", nullable=True),
            "source_locator_ref": descriptor("str", nullable=True), "content_hash": descriptor("sha256"),
        },
        "S5SharedTemporalContext": {
            "context_ref": descriptor("str"), "authority_receipt_ref": descriptor("str"), "spine_ref": descriptor("str"),
            "axis_mode": descriptor("enum:axis_mode"), "window_start": descriptor("date", nullable=True),
            "window_end": descriptor("date", nullable=True), "selection_anchor": descriptor("S5SelectionAnchor"),
            "selected_event_ref": descriptor("str", nullable=True), "selected_risk_anchor_ref": descriptor("str", nullable=True),
            "selected_visit_ref": descriptor("str", nullable=True), "content_hash": descriptor("sha256"),
        },
        "S5ViewBinding": {
            "view": descriptor("enum:s5_view"), "shared_context_ref": descriptor("str"), "spine_ref": descriptor("str"),
            "authority_projection_id": descriptor("str"), "anchor_ref": descriptor("str", nullable=True), "content_hash": descriptor("sha256"),
        },
        "S5SubjectWorkspaceContract": {
            "subject_ref": descriptor("str"), "spine_ref": descriptor("str"), "authority_receipt_refs": descriptor("str", "many"),
            "shared_context": descriptor("S5SharedTemporalContext"), "view_bindings": descriptor("S5ViewBinding", "many"),
            "content_hash": descriptor("sha256"),
        },
        "S5DomainEncodingItem": {
            "domain": descriptor("enum:domain"), "short_label_zh": descriptor("str"),
            "event_shape": descriptor("enum:event_shape"), "line_style": descriptor("enum:line_style"),
        },
        "S5SeverityEncoding": {
            "severity": descriptor("enum:severity"), "label_zh": descriptor("str"), "line_weight": descriptor("int", nullable=True),
        },
        "S5LegacyTreatmentMapping": {
            "legacy_kind": descriptor("enum:legacy_treatment_kind"), "mapping_state": descriptor("enum:legacy_mapping_state"),
            "mapping_authority_ref": descriptor("str", nullable=True), "target_domain": descriptor("enum:domain", nullable=True),
            "target_subtype": descriptor("enum:journey_subtype", nullable=True),
        },
        "S5AudienceLexicon": {
            "content_hash": descriptor("sha256"), "forbidden_terms": descriptor("str", "many"),
            "domain_items": descriptor("S5DomainEncodingItem", "many"), "severity_items": descriptor("S5SeverityEncoding", "many"),
            "symptom_efficacy_subtypes": descriptor("enum:symptom_efficacy_subtype", "many"),
        },
        "S5AudienceEncodingRegistry": {
            "domain_items": descriptor("S5DomainEncodingItem", "many"), "severity_items": descriptor("S5SeverityEncoding", "many"),
            "risk_overlay_shape": descriptor("str"), "symptom_efficacy_subtypes": descriptor("enum:symptom_efficacy_subtype", "many"),
            "legacy_treatment_mapping": descriptor("S5LegacyTreatmentMapping", "many"),
        },
    })
    return objects


def source_pointer(base: str, leaf: str) -> str:
    return "/" + leaf if base == "/" else base + "/" + leaf


def producer_source_paths(object_name: str, leaf: str) -> tuple[dict[str, str], ...]:
    common = {
        "S5ScopeIdentity": ("/projection/scope_identity", "PublicScopeIdentity"),
        "S5SourceLocator": ("/projection/source_locators[*]", "PublicSourceLocator"),
        "S5SourceRevisionContentPair": ("/receipt/source_revision_content_pairs[*]", "SourceRevisionContentPair"),
        "S5VisibilityClosure": ("/receipt/visibility_closure", "VisibilityClosure"),
        "S5AuthorityReceipt": ("/receipt", "PublicAuthorityReceipt"),
    }
    endpoint_bases = (
        "/projection/axis_basis/cutoff_endpoint", "/projection/events[*]/start_endpoint", "/projection/events[*]/end_endpoint",
        "/projection/pending_date_items[*]/start_endpoint", "/projection/pending_date_items[*]/end_endpoint",
        "/projection/phase_bands[*]/start_endpoint", "/projection/phase_bands[*]/end_endpoint",
        "/projection/risk_anchors[*]/start_endpoint", "/projection/risk_anchors[*]/end_endpoint",
        "/projection/visits[*]/actual_endpoint", "/projection/visits[*]/nominal_endpoint",
    )
    subject = {
        "S5AxisBasis": ("/projection/axis_basis", "TemporalAxisBasis"), "S5DomainTrack": ("/projection/domain_tracks[*]", "TemporalDomainTrack"),
        "S5JourneyEvent": ("/projection/events[*]", "TemporalEvent"), "S5MembershipIndex": ("/projection/membership_index", "TemporalMembershipIndex"),
        "S5PendingDateItem": ("/projection/pending_date_items[*]", "TemporalPendingDateItem"), "S5PhaseBand": ("/projection/phase_bands[*]", "TemporalPhaseBand"),
        "S5RiskAnchor": ("/projection/risk_anchors[*]", "TemporalRiskAnchor"), "S5VisitNode": ("/projection/visits[*]", "TemporalVisit"),
        "S5SubjectTemporalProjection": ("/projection", "SubjectTemporalPublicProjection"), "S5SubjectTemporalPacket": ("/", "SubjectTemporalAuthorityPacket"),
    }
    aemh = {
        "S5AEMHMembershipIndex": ("/projection/membership_index", "AEMHHistoryMembershipIndex"),
        "S5AEMHIdentityEvidence": ("/projection/threads[*]/history_entries[*]/identity_evidence[*]", "AEMHIdentityEvidence"),
        "S5AEMHHistoryEntry": ("/projection/threads[*]/history_entries[*]", "AEMHMatchHistoryEntry"),
        "S5AEMHPrefixAnchor": ("/projection/accepted_thread_prefixes[*]", "AEMHThreadPrefixAnchor"),
        "S5AEMHThread": ("/projection/threads[*]", "AEMHMatchThread"), "S5AEMHProjection": ("/projection", "AEMHMatchHistoryPublicProjection"),
        "S5AEMHPacket": ("/", "AEMHMatchHistoryAuthorityPacket"),
    }
    if object_name == "S5CutoffEndpoint":
        bases = (("aemh-match-history-public-v1", "/projection/cutoff_endpoint", "PublicCutoffEndpoint"),)
    elif object_name == "S5DateEndpoint":
        bases = tuple(("subject-temporal-public-v1", base, "TemporalDateEndpoint") for base in endpoint_bases)
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
    result = []
    for contract, base, source_type in bases:
        root = "SubjectTemporalAuthorityPacket" if contract == "subject-temporal-public-v1" else "AEMHMatchHistoryAuthorityPacket"
        result.append({"authority_contract": contract, "source_root_type": root, "source_type": source_type, "json_pointer": source_pointer(base, leaf)})
    return tuple(result)


def expected_producer_row(object_name: str, leaf: str, spec: dict[str, Any]) -> dict[str, Any]:
    sources = producer_source_paths(object_name, leaf)
    contracts = sorted({row["authority_contract"] for row in sources})
    validators = sorted({item for contract in contracts for item in PRODUCER_VALIDATORS[contract]})
    derived = spec["type"] == "sha256" or leaf.endswith("_hash") or leaf.endswith("_identity")
    return {
        "leaf_id": f"{object_name}.{leaf}", "target_object": object_name, "target_field": leaf, "target_spec": spec,
        "core_authority_leaf": object_name in CORE_OBJECTS, "authority_plane": "accepted_public_packet",
        "source_kind": "accepted_public_packet_derived" if derived else "accepted_public_packet_direct",
        "source_contracts": contracts, "source_paths": list(sources), "validator_refs": validators,
        "identity_recipe": "producer_pinned_canonical_sha256_recipe" if derived else "accepted_public_packet_field_with_exact_selector",
        "forbidden_authority_sources": COMMON_FORBIDDEN, "deferred_contract": None, "placeholder": False, "self_signed": False, "executable": True,
    }


def _clean_stage_cell(value: str) -> str:
    return value.strip().replace("`", "")


def _stage_span(line_number: int, row_key: str, line_text: str) -> dict[str, Any]:
    return {"line_start": line_number, "line_end": line_number, "row_key": row_key, "line_text": line_text}


def _stage_table_rows(stage_text: str) -> tuple[dict[str, Any], ...]:
    rows = []
    for line_number, line in enumerate(stage_text.splitlines(), 1):
        if not line.lstrip().startswith("|"):
            continue
        cells = [_clean_stage_cell(cell) for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] not in STAGE_DOMAIN_LABELS:
            continue
        domain = STAGE_DOMAIN_LABELS[cells[0]]
        shapes = [value for token, value in STAGE_SHAPE_TOKENS if token in cells[2]]
        lines = [value for token, value in STAGE_LINE_TOKENS if token in cells[2]]
        require(len(set(shapes)) == 1 and len(set(lines)) == 1, f"stage encoding not singular:{cells[0]}")
        rows.append({"domain": domain, "stage_label": cells[0], "short_label_zh": cells[1], "event_shape": shapes[0], "line_style": lines[0], "cells": cells, "source_span": _stage_span(line_number, domain, line)})
    require(len(rows) == 8 and {row["domain"] for row in rows} == set(DOMAINS), "stage domain table coverage")
    return tuple(rows)


def _stage_line(stage_text: str, predicate: Any, row_key: str) -> dict[str, Any]:
    for line_number, line in enumerate(stage_text.splitlines(), 1):
        if predicate(line):
            return {"line": line, "source_span": _stage_span(line_number, row_key, line)}
    fail(f"stage source span missing:{row_key}")


def _legacy_severity_from_parent(parent: dict[str, Any]) -> tuple[list[dict[str, str]], str]:
    invariant = next((item for item in parent["invariants"] if item.get("invariant_id") == "legacy_severity_mapping"), None)
    require(invariant is not None, "accepted parent legacy severity invariant missing")
    pairs = [{"legacy_value": legacy, "severity": severity} for legacy, severity in re.findall(r"([a-z][a-z_]*)\s*->\s*([a-z][a-z_]*)", invariant.get("predicate", ""))]
    require(pairs == LEGACY_SEVERITY_MAPPING and "fails closed" in invariant.get("predicate", ""), "accepted parent legacy severity predicate")
    return pairs, "fail_closed"


def expected_audience_constants(parent: dict[str, Any], stage_text: str) -> dict[str, Any]:
    rows = _stage_table_rows(stage_text)
    domain_order = list(resolve_json_pointer(parent, "/enums/domain"))
    require(domain_order == DOMAINS, "parent domain enum drift")
    subtype_order = list(resolve_json_pointer(parent, "/enums/journey_subtype"))
    symptom_line = _stage_line(stage_text, lambda line: "症状与疗效" in line and "症状/疗效/量表/结局/趋势" in line, "symptom_efficacy_subtypes")
    match = re.search(r"`([^`]*症状/疗效/量表/结局/趋势[^`]*)`", symptom_line["line"])
    require(match is not None, "stage symptom subtype list")
    symptom_subtypes = [STAGE_SYMPTOM_SUBTYPE_LABELS[label] for label in match.group(1).split("/")]
    require(symptom_subtypes == list(resolve_json_pointer(parent, "/enums/symptom_efficacy_subtype")), "parent symptom subtype drift")
    domain_line = _stage_line(stage_text, lambda line: "八个主轨道" in line and all(label in line for label in STAGE_DOMAIN_LABELS), "domain_list")
    severity_line = _stage_line(stage_text, lambda line: "普通受众层风险等级" in line and all(label in line for label in parent["enums"]["severity_zh"]), "severity_lexicon")
    forbidden_line = _stage_line(stage_text, lambda line: "不得使用" in line and "已记录事项" in line, "forbidden_terms")
    overlay_line = _stage_line(stage_text, lambda line: "双折角徽标" in line, "risk_overlay")
    forbidden_terms = re.findall(r"[“\"]([^”\"]+)[”\"]", forbidden_line["line"])
    require(forbidden_terms, "stage forbidden-term list")
    legacy_pairs, legacy_policy = _legacy_severity_from_parent(parent)
    legacy_domain_policy = copy.deepcopy(resolve_json_pointer(parent, "/legacy_domain_policy"))
    treatment_mapping = [{"legacy_kind": kind, "mapping_state": "unmapped_fail_closed", "mapping_authority_ref": None, "target_domain": None, "target_subtype": None} for kind in parent["enums"]["legacy_treatment_kind"]]
    matrix_lists = {domain: [] for domain in domain_order}
    for subtype in subtype_order:
        if subtype in symptom_subtypes:
            matrix_lists["symptom_efficacy"].append(subtype)
            continue
        token = SUBTYPE_STAGE_TOKENS.get(subtype)
        require(token is not None, f"stage subtype token:{subtype}")
        matched = []
        for row in rows:
            haystack = " ".join(row["cells"] if subtype == "protocol_deviation" else row["cells"][:3])
            if token in haystack:
                matched.append(row["domain"])
        require(len(matched) == 1, f"stage subtype relation:{subtype}:{matched}")
        matrix_lists[matched[0]].append(subtype)
    require([subtype for values in matrix_lists.values() for subtype in values] == subtype_order, "stage subtype coverage")
    parent_forbidden_shapes = list(resolve_json_pointer(parent, "/event_forbidden_shapes"))
    return {
        "domain_order": domain_order,
        "journey_subtype_order": subtype_order,
        "domains_exactly_eight": [{key: row[key] for key in ("domain", "short_label_zh", "event_shape", "line_style")} for row in rows],
        "severity_exactly_four": [{"severity": severity, "label_zh": label, "line_weight": None} for severity, label in zip(parent["enums"]["severity"], parent["enums"]["severity_zh"])],
        "domain_subtype_matrix": matrix_lists,
        "legacy_severity_mapping": legacy_pairs,
        "legacy_severity_unknown_policy": legacy_policy,
        "risk_overlay_shape": resolve_json_pointer(parent, "/risk_overlay_shape"),
        "event_shapes_forbidden": parent_forbidden_shapes,
        "symptom_efficacy_subtypes": symptom_subtypes,
        "forbidden_terms": forbidden_terms,
        "legacy_treatment_mapping": treatment_mapping,
        "legacy_treatment_policy": legacy_domain_policy,
        "source_spans": {
            "domain_list": domain_line["source_span"],
            "domain_rows": {row["domain"]: row["source_span"] for row in rows},
            "symptom_efficacy_subtypes": symptom_line["source_span"],
            "severity_lexicon": severity_line["source_span"],
            "forbidden_terms": forbidden_line["source_span"],
            "risk_overlay": overlay_line["source_span"],
        },
        "stage_raw_sha256": raw_sha(ROOT / STAGE_REVIEW),
        "parent_raw_sha256": raw_sha(ROOT / PARENT_EXACT),
        "parent_content_sha256": parent["contract_sha256"],
    }


def expected_presentation_row(parent: dict[str, Any], object_name: str, leaf: str, spec: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    def stage_path(span: dict[str, Any], source_type: str = "AcceptedR5StageParagraph") -> dict[str, Any]:
        return {"authority_contract": STAGE_CONTRACT_ID, "source_root_type": STAGE_SOURCE_ROOT_TYPE, "source_type": source_type, "source_span": copy.deepcopy(span), "raw_sha256": expected["stage_raw_sha256"], "parent_contract_id": PARENT_CONTRACT_ID, "parent_raw_sha256": expected["parent_raw_sha256"], "parent_content_sha256": expected["parent_content_sha256"]}
    def parent_path(pointer: str) -> dict[str, Any]:
        return {"authority_contract": PARENT_CONTRACT_ID, "source_root_type": PARENT_SOURCE_ROOT_TYPE, "source_type": PARENT_SOURCE_ROOT_TYPE, "json_pointer": pointer, "raw_sha256": expected["parent_raw_sha256"], "content_sha256": expected["parent_content_sha256"], "concrete_object": True}
    if (object_name, leaf) in {("S5SeverityEncoding", "line_weight"), ("S5AudienceLexicon", "content_hash")}:
        source_paths, source_kind, contracts, future_parameter, executable = [], "future_renderer_parameter", [], True, False
        derivation_sources = ["not_frozen_by_accepted_r5_sources", "acceptance_claim_false"]
    elif object_name == "S5DomainEncodingItem":
        source_paths, source_kind, contracts, future_parameter, executable = [stage_path(row, "MarkdownTableRow") for row in expected["source_spans"]["domain_rows"].values()], "accepted_stage_review_concrete", [STAGE_CONTRACT_ID], False, True
        derivation_sources = [f"{STAGE_REVIEW}:exact_source_spans_and_rows", f"{PARENT_EXACT}:raw_sha256={expected['parent_raw_sha256']}", f"{PARENT_EXACT}:content_sha256={expected['parent_content_sha256']}"]
    elif object_name == "S5SeverityEncoding":
        source_paths, source_kind, contracts, future_parameter, executable = [stage_path(expected["source_spans"]["severity_lexicon"])], "accepted_stage_review_concrete", [STAGE_CONTRACT_ID], False, True
        derivation_sources = [f"{STAGE_REVIEW}:exact_source_spans_and_rows", f"{PARENT_EXACT}:raw_sha256={expected['parent_raw_sha256']}", f"{PARENT_EXACT}:content_sha256={expected['parent_content_sha256']}"]
    elif object_name == "S5LegacyTreatmentMapping":
        source_paths, source_kind, contracts, future_parameter, executable = [parent_path(f"/legacy_domain_policy/{item['legacy_kind']}") for item in expected["legacy_treatment_mapping"]], "accepted_parent_policy_concrete", [PARENT_CONTRACT_ID], False, True
        derivation_sources = [f"{STAGE_REVIEW}:exact_source_spans_and_rows", f"{PARENT_EXACT}:raw_sha256={expected['parent_raw_sha256']}", f"{PARENT_EXACT}:content_sha256={expected['parent_content_sha256']}"]
    elif object_name == "S5AudienceLexicon":
        source = {"forbidden_terms": [stage_path(expected["source_spans"]["forbidden_terms"])], "domain_items": [stage_path(row, "MarkdownTableRow") for row in expected["source_spans"]["domain_rows"].values()], "severity_items": [stage_path(expected["source_spans"]["severity_lexicon"])], "symptom_efficacy_subtypes": [stage_path(expected["source_spans"]["symptom_efficacy_subtypes"])]}[leaf]
        source_paths, source_kind, contracts, future_parameter, executable = source, "accepted_stage_review_concrete", [STAGE_CONTRACT_ID], False, True
        derivation_sources = [f"{STAGE_REVIEW}:exact_source_spans_and_rows", f"{PARENT_EXACT}:raw_sha256={expected['parent_raw_sha256']}", f"{PARENT_EXACT}:content_sha256={expected['parent_content_sha256']}"]
    else:
        if leaf == "domain_items": source_paths = [stage_path(row, "MarkdownTableRow") for row in expected["source_spans"]["domain_rows"].values()]
        elif leaf == "severity_items": source_paths = [stage_path(expected["source_spans"]["severity_lexicon"])]
        elif leaf == "symptom_efficacy_subtypes": source_paths = [stage_path(expected["source_spans"]["symptom_efficacy_subtypes"])]
        elif leaf == "risk_overlay_shape": source_paths = [parent_path("/risk_overlay_shape"), parent_path("/event_forbidden_shapes")]
        else: source_paths = [parent_path(f"/legacy_domain_policy/{item['legacy_kind']}") for item in expected["legacy_treatment_mapping"]]
        source_kind, contracts, future_parameter, executable = ("accepted_parent_policy_concrete" if leaf in {"risk_overlay_shape", "legacy_treatment_mapping"} else "accepted_stage_review_concrete"), ([PARENT_CONTRACT_ID] if leaf in {"risk_overlay_shape", "legacy_treatment_mapping"} else [STAGE_CONTRACT_ID]), False, True
        derivation_sources = [f"{STAGE_REVIEW}:exact_source_spans_and_rows", f"{PARENT_EXACT}:raw_sha256={expected['parent_raw_sha256']}", f"{PARENT_EXACT}:content_sha256={expected['parent_content_sha256']}"]
    return {
        "leaf_id": f"{object_name}.{leaf}", "target_object": object_name, "target_field": leaf, "target_spec": spec,
        "core_authority_leaf": False, "authority_plane": "s5_owned_presentation_non_core", "source_kind": source_kind,
        "source_contracts": contracts, "source_paths": source_paths,
        "validator_refs": [f"{GENERATOR_REL}:extract_stage_audience_constants", f"{GENERATOR_REL}:validate_parent_derived_constants"] + ([f"{GENERATOR_REL}:resolve_json_pointer"] if source_kind == "accepted_parent_policy_concrete" else []),
        "identity_recipe": "future_renderer_parameter_not_acceptance_authority" if future_parameter else "accepted_stage_row_or_parent_policy_with_raw_and_content_hash_binding",
        "derivation_sources": derivation_sources, "forbidden_authority_sources": COMMON_FORBIDDEN,
        "deferred_contract": None, "placeholder": False, "self_signed": False, "executable": executable,
        "acceptance_claim": False, "future_renderer_parameter": future_parameter,
    }


def expected_navigation_row(object_name: str, leaf: str, spec: dict[str, Any]) -> dict[str, Any]:
    bound = leaf in {"spine_ref", "subject_ref", "authority_receipt_ref", "authority_receipt_refs", "authority_projection_id"}
    if leaf in {"authority_receipt_ref", "authority_receipt_refs"}:
        pointer = "/receipt/receipt_id"
    elif leaf == "authority_projection_id":
        pointer = "/projection/projection_id"
    else:
        pointer = "/projection/scope_identity/" + leaf
    if leaf in {"authority_receipt_ref", "authority_receipt_refs"}:
        paths = [
            {"authority_contract": "subject-temporal-public-v1", "source_root_type": "SubjectTemporalAuthorityPacket", "source_type": "PublicAuthorityReceipt", "json_pointer": pointer},
            {"authority_contract": "aemh-match-history-public-v1", "source_root_type": "AEMHMatchHistoryAuthorityPacket", "source_type": "PublicAuthorityReceipt", "json_pointer": pointer},
        ]
        contracts = ["subject-temporal-public-v1", "aemh-match-history-public-v1"]
    elif bound:
        paths = [{"authority_contract": "subject-temporal-public-v1", "source_root_type": "SubjectTemporalAuthorityPacket", "source_type": "SubjectTemporalPublicProjection", "json_pointer": pointer}]
        contracts = ["subject-temporal-public-v1"]
    else:
        paths = []
        contracts = []
    return {
        "leaf_id": f"{object_name}.{leaf}", "target_object": object_name, "target_field": leaf, "target_spec": spec,
        "core_authority_leaf": False, "authority_plane": "navigation_contract",
        "source_kind": "accepted_public_packet_binding" if bound else "runtime_navigation_state",
        "source_contracts": contracts, "source_paths": paths,
        "validator_refs": ["s5.navigation_context_membership_validator", "s5.navigation_state_is_not_medical_authority"],
        "identity_recipe": "canonical_navigation_state_hash" if "hash" in leaf else "navigation_state_not_authority",
        "forbidden_authority_sources": COMMON_FORBIDDEN, "deferred_contract": None, "placeholder": False, "self_signed": False, "executable": True,
    }


def expected_replaced_targets(target: str) -> list[str]:
    object_name, leaf = target.split(".", 1)
    return PARENT_REPLACEMENTS.get(object_name, {}).get(leaf, [])


def expected_parent_rows(parent: dict[str, Any]) -> list[dict[str, Any]]:
    replacement_contracts = {"subject-temporal-public-v1", "aemh-match-history-public-v1", "r5-authority-receipt-kind-v1"}
    rows = []
    for original in parent["field_mappings"]:
        source = copy.deepcopy(original)
        deferred = source.get("deferred_contract")
        if source["source_kind"] == "deferred" and deferred in replacement_contracts:
            replacements = expected_replaced_targets(source["target"])
            require(replacements, f"missing replacement map:{source['target']}")
            source.update({
                "source_kind": "s5_canonical_replacement", "deferred_contract": None, "core_authority_leaf": False,
                "status": "replaced_by_s5_typed_leaf", "replacement_leaf_ids": replacements,
                "authority_source_forbidden": COMMON_FORBIDDEN, "placeholder": False, "self_signed": False,
            })
        elif source["source_kind"] == "deferred":
            source.update({"core_authority_leaf": False, "status": "deferred_out_of_scope_preserved", "authority_source_forbidden": COMMON_FORBIDDEN, "placeholder": False, "self_signed": False})
        else:
            source.update({"core_authority_leaf": False, "status": "inherited_parent_mapping", "authority_source_forbidden": COMMON_FORBIDDEN, "placeholder": False, "self_signed": False})
        rows.append(source)
    return sorted(rows, key=lambda row: row["target"])


def expected_matrix(parent: dict[str, Any], objects: dict[str, Any], audience_expected: dict[str, Any] | None = None) -> dict[str, Any]:
    audience_expected = audience_expected or expected_audience_constants(parent, (ROOT / STAGE_REVIEW).read_text(encoding="utf-8"))
    rows = []
    for object_name, fields in objects.items():
        if object_name in PRESENTATION_OBJECTS:
            rows.extend(expected_presentation_row(parent, object_name, leaf, spec, audience_expected) for leaf, spec in fields.items())
        elif object_name in {"S5SelectionAnchor", "S5SharedTemporalContext", "S5ViewBinding", "S5SubjectWorkspaceContract"}:
            rows.extend(expected_navigation_row(object_name, leaf, spec) for leaf, spec in fields.items())
        else:
            rows.extend(expected_producer_row(object_name, leaf, spec) for leaf, spec in fields.items())
    rows.sort(key=lambda row: row["leaf_id"])
    parent_rows = expected_parent_rows(parent)
    core = [row["leaf_id"] for row in rows if row["core_authority_leaf"]]
    deferred = [row["leaf_id"] for row in rows if row["core_authority_leaf"] and (row.get("deferred_contract") or row["source_kind"] in {"deferred", "placeholder", "self_signed"})]
    result = {
        "schema": "medical-monitoring-r5-s5-subject-workspace-source-leaf-matrix-v0.1", "schema_version": SCHEMA_VERSION, "contract_id": CONTRACT_ID,
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
        "canonical_leaf_rows": rows, "parent_leaf_rows": parent_rows, "core_leaf_ids": core, "deferred_core_leaf_ids": deferred,
        "counts": {
            "canonical_leaf_count": len(rows), "core_leaf_count": len(core), "presentation_leaf_count": sum(row["authority_plane"] == "s5_owned_presentation_non_core" for row in rows), "deferred_core_leaf_count": len(deferred),
            "parent_leaf_count": len(parent_rows), "parent_replaced_leaf_count": sum(row["status"] == "replaced_by_s5_typed_leaf" for row in parent_rows),
            "parent_deferred_out_of_scope_count": sum(row["status"] == "deferred_out_of_scope_preserved" for row in parent_rows),
        },
        "matrix_content_hash": None,
    }
    result["matrix_content_hash"] = digest({key: value for key, value in result.items() if key != "matrix_content_hash"})
    return result


def json_pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def s5_mutation_definition(target: str) -> dict[str, Any]:
    zero_hash = "0" * 64
    definitions = {
        "parent_exact_contract": {"op": "replace", "path": f"/manifest/input_raw_sha256/{json_pointer_token(PARENT_EXACT)}", "value": zero_hash, "valid_value": EXPECTED_INPUT_PINS[PARENT_EXACT]},
        "public_producer_module": {"op": "replace", "path": "/manifest/input_raw_sha256/poc~1medical_monitoring_ai_native_r5~1src~1mm_r5~1public_authority_common.py", "value": zero_hash, "valid_value": EXPECTED_ACCEPTED_PUBLIC_PINS["poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py"]},
        "public_producer_test": {"op": "replace", "path": "/manifest/input_raw_sha256/poc~1medical_monitoring_ai_native_r5~1tests~1test_public_authority_common.py", "value": zero_hash, "valid_value": EXPECTED_ACCEPTED_PUBLIC_PINS["poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py"]},
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
    require(target in definitions, f"missing executable S5 mutation:{target}")
    return definitions[target]


def oracle_with_error(oracle: dict[str, Any]) -> dict[str, Any]:
    result = dict(oracle)
    outcome = result.get("expected_outcome")
    result["expected_error"] = outcome.split(":", 1)[1] if isinstance(outcome, str) and outcome.startswith("reject:") else None
    return result


def expected_challenges(parent: dict[str, Any], parent_registry: dict[str, Any], parent_quota: dict[str, Any]) -> dict[str, Any]:
    inherited = []
    rules = {row["rule_id"]: row for row in parent["challenge_rules"]}
    for row in parent_registry["rows"]:
        oracle = row["stage_oracle_contract"]
        rule_id = oracle["rule_id"]
        require(rule_id in rules, f"parent challenge rule missing:{rule_id}")
        rule = rules[rule_id]
        structured_oracle = oracle_with_error(oracle)
        inherited.append({
            "challenge_id": f"parent::{rule_id}", "category": row["category"], "origin": "accepted_parent_r5_v0.3",
            "target": rule_id.split(".", 1)[1] if "." in rule_id else rule_id, "mutation": row["single_mutation"]["value"],
            "single_mutation": dict(row["single_mutation"]),
            "valid_value": rule["valid_value"], "expected_outcome": oracle["expected_outcome"], "expected_projection": oracle["expected_projection"],
            "oracle_contract": structured_oracle, "stage_oracle_contract": dict(structured_oracle),
            "severity": row["severity"], "precondition": row["precondition"], "test_metadata_only": True, "authority_source_forbidden": COMMON_FORBIDDEN,
        })
    s5 = []
    for index, (category, target, expected) in enumerate(S5_CHALLENGE_SPECS, 1):
        mutation = s5_mutation_definition(target)
        oracle = oracle_with_error({
            "rule_id": f"s5.{target}", "expected_outcome": expected,
            "expected_projection": "not_emitted", "required_non_llm_anchor": "deterministic generator semantic validator plus exact contract content hash",
            "test_locator": f"poc/medical_monitoring_ai_native_r5/tests/challenges/test_s5_runtime_challenges.py::test_{target}",
            "kind": "planned_pytest", "planned_stage": "S5",
        })
        s5.append({
            "challenge_id": f"s5::{index:03d}", "category": category, "origin": "s5_contract_specific", "target": target,
            "mutation": mutation["value"], "single_mutation": {key: value for key, value in mutation.items() if key != "valid_value"},
            "valid_value": mutation["valid_value"], "expected_outcome": expected, "expected_projection": "not_emitted",
            "oracle_contract": oracle, "stage_oracle_contract": dict(oracle), "test_metadata_only": True, "authority_source_forbidden": COMMON_FORBIDDEN,
        })
    replay = []
    for index, reference in enumerate(REPLAY_CASES, 1):
        oracle = oracle_with_error({
            "rule_id": f"accepted_public_replay.{reference}", "expected_outcome": "accept_replay_only", "expected_projection": "packet_emitted",
            "required_non_llm_anchor": "accepted producer graph replay record and packet content hash",
            "test_locator": "poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py::test_exact_graph_replay",
            "kind": "accepted_replay", "planned_stage": "S5",
        })
        replay.append({
            "challenge_id": f"accepted-public-replay::{index:03d}", "category": "accepted_public_authority_replay", "origin": "accepted_public_authority_producer_record",
            "source_case_ref": reference, "target": "public_packet_graph", "mutation": reference,
            "single_mutation": {"op": "replay", "path": "/accepted_public_packet_graph", "value": reference}, "valid_value": "accepted_public_packet_graph",
            "expected_outcome": "accept_replay_only", "expected_projection": "packet_emitted", "oracle_contract": oracle, "stage_oracle_contract": dict(oracle),
            "test_metadata_only": True, "authority_source_forbidden": COMMON_FORBIDDEN,
        })
    rows = inherited + s5 + replay
    category_counts: dict[str, int] = {}
    for row in rows:
        category_counts[row["category"]] = category_counts.get(row["category"], 0) + 1
    result = {
        "schema": "medical-monitoring-r5-s5-subject-workspace-challenge-registry-v0.1", "schema_version": SCHEMA_VERSION, "contract_id": CONTRACT_ID,
        "parent_contract_sha256": parent["contract_sha256"], "parent_quota_ledger_sha256": raw_sha(ROOT / PARENT_QUOTA), "rows": rows,
        "row_count": len(rows), "counts": {"inherited_parent_rows": len(inherited), "s5_contract_specific_rows": len(s5), "accepted_public_replay_rows": len(replay), "total": len(rows)},
        "category_counts": dict(sorted(category_counts.items())),
        "quota": {"parent_quota_is_immutable": True, "parent_expected_total": parent_quota["expected_total"], "s5_additional_rows_have_no_medical_quota_authority": True},
        "authority_forbidden": COMMON_FORBIDDEN,
        "future_runtime_validation_contract": copy.deepcopy(FUTURE_RUNTIME_VALIDATION_CONTRACT),
        "row_contract": {"single_mutation_required": ["op", "path", "value"], "oracle_contract_required": ["rule_id", "expected_outcome", "expected_error", "expected_projection", "required_non_llm_anchor", "test_locator"], "placeholder_mutations_forbidden": True, "test_metadata_only": True},
        "structured_mutation_row_count": len(rows), "structured_oracle_row_count": len(rows),
        "unique_single_mutation_tuple_count": len({(row["single_mutation"]["op"], row["single_mutation"]["path"], digest(row["single_mutation"]["value"])) for row in rows}),
        "registry_content_hash": None,
    }
    result["registry_content_hash"] = digest({key: value for key, value in result.items() if key != "registry_content_hash"})
    return result


def check_exact_schema_paths(value: Any, schema: dict[str, Any], root_type: str, pointer: str) -> str:
    """Resolve the producer's ``[*]`` pointer notation and return node type."""
    node_type = root_type
    parts = [part for part in pointer.strip("/").split("/") if part]
    require(parts, f"empty source pointer:{pointer}")
    for index, part in enumerate(parts):
        wildcard = part.endswith("[*]")
        field_name = part[:-3] if wildcard else part
        require(node_type in schema["objects"], f"source path unknown object:{node_type}:{pointer}")
        fields = schema["objects"][node_type]
        require(field_name in fields, f"source path unknown field:{node_type}.{field_name}:{pointer}")
        spec = fields[field_name]
        if wildcard:
            require(spec["cardinality"] == "many", f"source path wildcard on scalar:{pointer}")
        parent_type = node_type
        node_type = spec["type"]
        if index == len(parts) - 1:
            return parent_type
    fail(f"unresolved source pointer:{pointer}")


def validate_source_paths(matrix: dict[str, Any], parent: dict[str, Any], subject: dict[str, Any], aemh: dict[str, Any]) -> None:
    schemas = {"subject-temporal-public-v1": subject, "aemh-match-history-public-v1": aemh}
    stage_text = (ROOT / STAGE_REVIEW).read_text(encoding="utf-8")
    stage_lines = stage_text.splitlines()
    audience_spans = expected_audience_constants(parent, stage_text)["source_spans"]
    accepted_stage_spans = {
        canonical_bytes(span)
        for span in audience_spans.values()
        if isinstance(span, dict)
    }
    for span in audience_spans["domain_rows"].values():
        accepted_stage_spans.add(canonical_bytes(span))
    accepted_parent_pointers = {
        "/risk_overlay_shape", "/event_forbidden_shapes",
        *(f"/legacy_domain_policy/{kind}" for kind in parent["enums"]["legacy_treatment_kind"]),
    }
    stage_raw = raw_sha(ROOT / STAGE_REVIEW)
    parent_raw = raw_sha(ROOT / PARENT_EXACT)
    parent_content = parent["contract_sha256"]
    for row in matrix["canonical_leaf_rows"]:
        if row["authority_plane"] == "s5_owned_presentation_non_core":
            require(row["acceptance_claim"] is False, f"presentation acceptance claim:{row['leaf_id']}")
            if row["future_renderer_parameter"]:
                require(not row["source_paths"] and row["executable"] is False, f"future renderer source binding:{row['leaf_id']}")
            else:
                require(row["source_paths"] and row["source_kind"] in {"accepted_stage_review_concrete", "accepted_parent_policy_concrete"}, f"presentation concrete source binding:{row['leaf_id']}")
            for source in row["source_paths"]:
                require(source["raw_sha256"] == stage_raw if source["authority_contract"] == STAGE_CONTRACT_ID else source["raw_sha256"] == parent_raw, f"source raw hash:{row['leaf_id']}")
                if source["authority_contract"] == STAGE_CONTRACT_ID:
                    require(source["source_root_type"] == STAGE_SOURCE_ROOT_TYPE and source["source_type"] in {"MarkdownTableRow", "AcceptedR5StageParagraph"} and source["source_span"]["line_start"] == source["source_span"]["line_end"], f"stage source span:{row['leaf_id']}")
                    span = source["source_span"]
                    index = span["line_start"] - 1
                    require(0 <= index < len(stage_lines) and stage_lines[index] == span["line_text"], f"stage source text drift:{row['leaf_id']}")
                    require(canonical_bytes(span) in accepted_stage_spans, f"stage source row not accepted:{row['leaf_id']}")
                else:
                    require(source["authority_contract"] == PARENT_CONTRACT_ID and source["source_root_type"] == PARENT_SOURCE_ROOT_TYPE and source["source_type"] == PARENT_SOURCE_ROOT_TYPE, f"presentation parent source:{row['leaf_id']}")
                    require(source["content_sha256"] == parent_content and source["concrete_object"] is True, f"presentation parent binding:{row['leaf_id']}")
                    require(source["json_pointer"] in accepted_parent_pointers and not source["json_pointer"].startswith(("/objects/", "/invariants/")), f"parent scalar pseudo-selector:{row['leaf_id']}")
                    resolve_json_pointer(parent, source["json_pointer"])
            continue
        for source in row["source_paths"]:
            contract = source["authority_contract"]
            require(contract in schemas, f"unknown source contract:{contract}")
            if row["authority_plane"] == "accepted_public_packet":
                node_type = check_exact_schema_paths(schemas[contract], schemas[contract], source["source_root_type"], source["json_pointer"])
                require(node_type == source["source_type"], f"source type mismatch:{row['leaf_id']}:{source['json_pointer']}:{node_type}!={source['source_type']}")
                require(row["target_field"] in schemas[contract]["objects"][node_type], f"source leaf missing:{row['leaf_id']}")
            else:
                require(source["json_pointer"].startswith("/"), f"navigation pointer:{row['leaf_id']}")


def resolve_json_pointer(document: Any, pointer: str) -> Any:
    require(pointer.startswith("/"), f"invalid JSON pointer:{pointer}")
    current = document
    if pointer == "/":
        return current
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        try:
            current = current[int(token)] if isinstance(current, list) else current[token]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            fail(f"unresolved JSON pointer:{pointer}")
    return current


def expected_exact_contract(parent: dict[str, Any], subject: dict[str, Any], aemh: dict[str, Any], temporal: dict[str, Any], recipes: dict[str, Any], fixtures: dict[str, Any], typed: dict[str, Any], matrix: dict[str, Any], challenges: dict[str, Any], audience_expected: dict[str, Any] | None = None) -> dict[str, Any]:
    audience_expected = audience_expected or expected_audience_constants(parent, (ROOT / STAGE_REVIEW).read_text(encoding="utf-8"))
    parent_meta = {
        "schema": parent["schema"], "raw_sha256": raw_sha(ROOT / PARENT_EXACT), "content_sha256": parent["contract_sha256"],
        "field_mapping_count": len(parent["field_mappings"]), "challenge_count": len(parent["challenge_rules"]),
    }
    accepted = {
        "subject_temporal": {"contract_id": "subject-temporal-public-v1", "schema_version": subject["schema_version"], "schema_raw_sha256": raw_sha(ROOT / SUBJECT_SCHEMA), "validator_refs": list(PRODUCER_VALIDATORS["subject-temporal-public-v1"])},
        "aemh_match_history": {"contract_id": "aemh-match-history-public-v1", "schema_version": aemh["schema_version"], "schema_raw_sha256": raw_sha(ROOT / AEMH_SCHEMA), "validator_refs": list(PRODUCER_VALIDATORS["aemh-match-history-public-v1"])},
    }
    authority = {
        "serialized_input_authority": "AuthorityBundleV02", "typed_decoder_is_lossless_not_independent_authority": True,
        "public_packet_is_output_authority": True, "candidate_output_as_input_forbidden": True,
        "accepted_producer_builders": ["subject_temporal_public.build_subject_temporal_authority", "aemh_match_history_public.build_aemh_match_history_authority"],
        "accepted_producer_validators": ["subject_temporal_public.validate_subject_temporal_authority", "aemh_match_history_public.validate_aemh_match_history_authority"],
        "fallback_policy": "fail_closed_no_nearest",
    }
    audience = {
        "domain_order": copy.deepcopy(audience_expected["domain_order"]),
        "journey_subtype_order": copy.deepcopy(audience_expected["journey_subtype_order"]),
        "domains_exactly_eight": copy.deepcopy(audience_expected["domains_exactly_eight"]),
        "severity_exactly_four": copy.deepcopy(audience_expected["severity_exactly_four"]),
        "domain_subtype_matrix": copy.deepcopy(audience_expected["domain_subtype_matrix"]),
        "legacy_severity_mapping": copy.deepcopy(audience_expected["legacy_severity_mapping"]),
        "legacy_severity_unknown_policy": audience_expected["legacy_severity_unknown_policy"],
        "risk_overlay_shape": audience_expected["risk_overlay_shape"],
        "event_shapes_forbidden": copy.deepcopy(audience_expected["event_shapes_forbidden"]),
        "symptom_efficacy_subtypes": copy.deepcopy(audience_expected["symptom_efficacy_subtypes"]),
        "forbidden_terms": copy.deepcopy(audience_expected["forbidden_terms"]),
        "legacy_treatment_mapping": copy.deepcopy(audience_expected["legacy_treatment_mapping"]),
        "legacy_treatment_policy": copy.deepcopy(audience_expected["legacy_treatment_policy"]),
        "authority_scope": "s5_owned_presentation_non_core",
        "acceptance_claim": False,
        "source_binding": {
            "stage_contract": STAGE_REVIEW,
            "stage_raw_sha256": audience_expected["stage_raw_sha256"],
            "parent_contract": PARENT_EXACT,
            "parent_raw_sha256": audience_expected["parent_raw_sha256"],
            "parent_content_sha256": audience_expected["parent_content_sha256"],
            "source_spans": copy.deepcopy(audience_expected["source_spans"]),
        },
        "future_renderer_parameters": [
            {"parameter": "S5SeverityEncoding.line_weight", "value": None, "acceptance_claim": False, "reason": "numeric line weight is not concretely frozen by accepted R5 sources"},
            {"parameter": "S5AudienceLexicon.content_hash", "value": None, "acceptance_claim": False, "reason": "renderer content hash is not frozen before a future renderer exists"},
        ],
        "domain_subtype_unknown_pair_policy": "fail_closed",
        "other_domain_policy": "forbidden",
        "unknown_domain_policy": "fail_closed_to_domain_confirmation_surface",
        "not_applicable_vs_not_provided_distinct": True,
        "constant_derivation": {
            "source_contracts": [STAGE_CONTRACT_ID, PARENT_CONTRACT_ID],
            "concrete_stage_rows_and_parent_policy_only": True,
            "schema_descriptors_and_invariant_predicates_are_not_scalar_authority": True,
            "source_spans_and_parent_hashes_are_frozen": True,
            "validator_ref": f"{GENERATOR_REL}:validate_parent_derived_constants",
        },
    }
    shared = {
        "one_spine_across_views": True, "views": ["journey", "profile", "timeline"],
        "shared_fields": ["spine_ref", "axis_mode", "window_start", "window_end", "selection_anchor", "selected_event_ref", "selected_risk_anchor_ref", "selected_visit_ref"],
        "view_bindings_must_share_context_ref": True, "actual_calendar_axis_default": True, "study_day_is_explicit_projection": True,
        "nominal_actual_unscheduled_visit_axes_not_absorbed": True, "date_state_preservation": ["exact", "partial", "conflicted", "missing"],
        "missing_or_conflicted_date_not_fabricated": True, "partial_or_conflicted_range_preserved": True, "ui_state_is_not_identity_authority": True,
    }
    aemh_contract = {
        "original_reminder_retained": True, "later_recorded_fact_retained": True, "history_order": "seq_and_prior_entry_hash",
        "previous_prefix_retained": True, "identity_evidence_retained": True, "automatic_closure_forbidden": True,
        "identity_rewrite_forbidden": True, "match_states": ["exact", "ambiguous", "rejected"],
    }
    hash_recipes = {
        "canonical_json": "UTF-8 JSON; NFC strings; sorted object keys; no insignificant whitespace; declared array order preserved",
        "producer_identity": "accepted producer packet and receipt hash recipes pinned by the accepted public schemas",
        "s5_navigation_content_hash": "sha256(canonical_json(all exact object fields except content_hash))",
        "s5_context_ref": "sha256(canonical_json({authority_receipt_ref,spine_ref,axis_mode,window_start,window_end,selection_anchor,selected_event_ref,selected_risk_anchor_ref,selected_visit_ref}))",
        "s5_view_binding_hash": "sha256(canonical_json(all exact S5ViewBinding fields except content_hash))",
        "s5_workspace_hash": "sha256(canonical_json(all exact S5SubjectWorkspaceContract fields except content_hash; view_bindings sorted by view))",
    }
    validator = f"{GENERATOR_REL}:validate_parent_derived_constants"
    invariants = [
        {"id": "accepted_packet_only", "predicate": "only accepted AuthorityBundleV02 builder output may populate core S5 leaves"},
        {"id": "receipt_projection_exact", "predicate": "receipt scope, projection id/content hash and packet content hash bind exactly"},
        {"id": "scope_identity_exact", "predicate": "project/run/site/snapshot/spine/subject/cutoff state stay within one packet scope"},
        {"id": "shared_spine_exact", "predicate": "journey/profile/timeline share one spine/window/selection/anchor context"},
        {"id": "date_geometry_exact", "predicate": "exact, partial, conflicted and missing endpoint states are retained without fabrication"},
        {"id": "domain_bijection", "predicate": "exactly eight domains; unknown and OTHER fail closed", "validator_ref": validator},
        {"id": "domain_subtype_matrix_exact", "predicate": "domain/subtype pairs must be in the exact eight-domain matrix; ae/ip_dose and every unlisted pair fail closed", "validator_ref": f"{GENERATOR_REL}:validate_domain_subtype_pair"},
        {"id": "future_s5_cross_domain_validator", "predicate": "future S5 validator rejects domain=ae, subtype=ip_dose with DOMAIN_SUBTYPE_MISMATCH before projection acceptance", "validator_ref": FUTURE_RUNTIME_VALIDATION_CONTRACT["validator_path"] + ":" + FUTURE_RUNTIME_VALIDATION_CONTRACT["validator_function"], "test_locator": FUTURE_RUNTIME_VALIDATION_CONTRACT["test_path"], "required": True, "runtime_absent_until_fresh_acceptance": True},
        {"id": "non_color_encoding", "predicate": "event/risk distinction and domain shape/label/line style are explicit; risk overlay never an event shape"},
        {"id": "severity_no_promotion", "predicate": "high never becomes critical without accepted upstream critical", "validator_ref": validator},
        {"id": "legacy_severity_mapping_exact", "predicate": "severe maps to high, moderate to medium, mild to low; unknown legacy severity fails closed", "validator_ref": f"{GENERATOR_REL}:validate_legacy_severity"},
        {"id": "legacy_treatment_fail_closed", "predicate": "background/non-drug treatment requires an accepted mapping or remains unmapped_fail_closed"},
        {"id": "parent_derived_constant_closure", "predicate": "presentation constants are non-core; concrete labels/shapes/line styles/terms bind exact accepted stage rows and parent policy objects with raw/content hashes; schema descriptors and predicates are not scalar authority", "validator_ref": validator},
        {"id": "clinical_public_leaf_authority", "predicate": "clinical, identity, date, domain-event and history leaves remain core and resolve to accepted executable public packet paths and producer validators"},
        {"id": "aemh_append_only", "predicate": "original reminder, later facts, identity evidence and prefix history are retained"},
        {"id": "no_automatic_closure", "predicate": "AEMH matching never closes or rewrites the source risk/identity"},
        {"id": "no_nearest_fallback", "predicate": "identity or source mismatch emits no adjacent subject/site/event"},
        {"id": "navigation_non_authority", "predicate": "window/selection/UI state can bind only to verified packet members and cannot rewrite medical authority"},
        {"id": "unlock_boundary", "predicate": "contract acceptance unlocks only the exact future synthetic/offline runtime allowlist"},
    ]
    counts = typed["counts"]
    return {
        "schema": "medical-monitoring-r5-s5-subject-workspace-exact-contract-v0.1", "schema_version": SCHEMA_VERSION, "contract_id": CONTRACT_ID,
        "parent_contract": parent_meta, "accepted_public_packet_contracts": accepted, "authority_model": authority, "objects": expected_objects(subject, aemh),
        "exact_keys_recursive": True, "additional_properties": False, "enums": EXPECTED_ENUMS, "core_object_names": sorted(CORE_OBJECTS), "navigation_object_names": NAVIGATION_OBJECTS,
        "audience_constants": audience, "shared_temporal_spine_contract": shared, "aemh_append_only_contract": aemh_contract, "hash_recipes": hash_recipes,
        "source_leaf_matrix_content_hash": matrix["matrix_content_hash"], "challenge_registry_content_hash": challenges["registry_content_hash"],
        "typed_authority_upstream": {"typed_contract_content_hash": counts["contract_content_hash"], "typed_leaf_derivation_count": counts["leaf_derivations"], "typed_record_count": counts["typed_records"], "temporal_schema_version": temporal["schema_version"], "temporal_recipe_count": len(recipes["executable_v02_recipes"]), "temporal_positive_path_count": fixtures["positive_valid_count"]},
        "parent_compatibility_policy": {"lossy_shallow_parent_objects_not_emitted_as_s5_authority": ["R5AEMHMatchHistory", "R5JourneyEvent", "R5PendingDateItem", "R5RiskAnchor", "R5TemporalSpineProjection", "R5VisitNode"], "reason": "accepted public packet retains endpoint ranges, cutoff state, append-only entries and source identities that shallow parent fields cannot represent", "replacement": "S5 canonical typed objects in source_leaf_matrix.canonical_leaf_rows", "no_lossy_null_or_date_collapse": True},
        "invariants": invariants,
        "performance_profile_for_future_runtime_only": {"synthetic_dataset": {"events": 1000, "metrics": 40, "risk_anchors": 300}, "shared_selection_update_p95_ms": 100, "browser_and_8911_acceptance": "not_in_scope_at_contract_stage"},
        "future_runtime_allowlist_ref": "manifest.future_runtime_allowlist", "future_runtime_surface_scan_ref": "manifest.runtime_surface_scan", "future_runtime_validation_contract": copy.deepcopy(FUTURE_RUNTIME_VALIDATION_CONTRACT),
        "acceptance": {"required_token": ACCEPTANCE_TOKEN, "eligible_only_when": ["deferred_core_leaf_count == 0", "placeholder_core_leaf_count == 0", "self_signed_core_leaf_count == 0", "independent_verifier_passes_normal_O_O_and_replay_gates", "fresh_isolated_review_or_conference_decision_bound_to_frozen_hashes", "8911_stopped", "medical_writing_boundary_unchanged"], "fresh_isolated_acceptance_record": {"required": True, "decision": ACCEPTANCE_TOKEN, "must_bind_exactly": ["contract_content_hash", "manifest_content_hash", "generator_raw_sha256", "verifier_raw_sha256", "generated_artifact_raw_sha256", "acceptance_token"], "external_record_only": True, "verifier_self_hash_inside_own_source_forbidden": True}, "worker_self_acceptance": False, "acceptance_token_emitted": False, "does_not_accept": ["S5 runtime", "UI", "browser", "real projects", "real models", "clinical truth", "product or production", "medical-writing subsystem", "security design or testing"]},
        "contract_content_hash": None,
    }


def verify_exact_contract(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    require(set(actual) == set(expected), "exact contract top-level keys")
    for key, value in expected.items():
        if key != "contract_content_hash":
            require(actual.get(key) == value, f"exact contract semantic drift:{key}")
    require(isinstance(actual.get("contract_content_hash"), str), "missing contract content hash")
    require(actual["contract_content_hash"] == digest({key: value for key, value in actual.items() if key != "contract_content_hash"}), "contract content hash")


def verify_matrix(actual: dict[str, Any], expected: dict[str, Any], parent: dict[str, Any], subject: dict[str, Any], aemh: dict[str, Any]) -> None:
    require(actual == expected, "source leaf matrix independent reconstruction")
    require(actual["counts"] == {"canonical_leaf_count": 265, "core_leaf_count": 216, "presentation_leaf_count": 22, "deferred_core_leaf_count": 0, "parent_leaf_count": 195, "parent_replaced_leaf_count": 53, "parent_deferred_out_of_scope_count": 33}, "source leaf counts")
    require(len(actual["canonical_leaf_rows"]) == len({row["leaf_id"] for row in actual["canonical_leaf_rows"]}), "duplicate canonical leaves")
    require(len(actual["core_leaf_ids"]) == 216 and not actual["deferred_core_leaf_ids"], "core leaf gate")
    validate_source_paths(actual, parent, subject, aemh)
    for row in actual["canonical_leaf_rows"]:
        if row["core_authority_leaf"]:
            require(row["executable"] and row["deferred_contract"] is None and not row["placeholder"] and not row["self_signed"], f"non-executable core leaf:{row['leaf_id']}")
        if row["authority_plane"] == "s5_owned_presentation_non_core":
            require(row["acceptance_claim"] is False and row["core_authority_leaf"] is False, f"presentation core claim:{row['leaf_id']}")


def verify_challenges(actual: dict[str, Any], expected: dict[str, Any], parent: dict[str, Any], parent_registry: dict[str, Any]) -> None:
    require(actual["row_count"] == 250 and len(actual["rows"]) == 250, "challenge row count")
    require(len({row["challenge_id"] for row in actual["rows"]}) == 250, "duplicate challenge ids")
    require(actual["counts"] == {"inherited_parent_rows": 204, "s5_contract_specific_rows": 36, "accepted_public_replay_rows": 10, "total": 250}, "challenge counts")
    require(actual["future_runtime_validation_contract"] == FUTURE_RUNTIME_VALIDATION_CONTRACT, "future runtime validation contract")
    require(actual["unique_single_mutation_tuple_count"] == 250, "unique challenge mutation tuples")
    require(actual["quota"]["parent_expected_total"] == 204, "parent quota metadata")
    require(actual["parent_quota_ledger_sha256"] == EXPECTED_INPUT_PINS[PARENT_QUOTA], "parent quota pin")
    rule_ids = {row["rule_id"] for row in parent["challenge_rules"]}
    for row in actual["rows"]:
        mutation = row.get("single_mutation")
        require(isinstance(mutation, dict) and set(mutation) == {"op", "path", "value"}, f"concrete mutation shape:{row.get('challenge_id')}")
        require(mutation["op"] in CHALLENGE_MUTATION_OPS, f"unknown mutation op:{row.get('challenge_id')}")
        require(isinstance(mutation["path"], str) and mutation["path"].startswith("/"), f"mutation path:{row.get('challenge_id')}")
        oracle = row.get("oracle_contract")
        stage_oracle = row.get("stage_oracle_contract")
        require(isinstance(oracle, dict) and CHALLENGE_ORACLE_KEYS.issubset(oracle), f"oracle shape:{row.get('challenge_id')}")
        require(stage_oracle == oracle, f"stage oracle binding:{row.get('challenge_id')}")
        outcome = oracle["expected_outcome"]
        expected_error = outcome.split(":", 1)[1] if isinstance(outcome, str) and outcome.startswith("reject:") else None
        require(oracle["expected_error"] == expected_error, f"oracle error binding:{row.get('challenge_id')}")
        require(isinstance(oracle["required_non_llm_anchor"], str) and oracle["required_non_llm_anchor"], f"oracle anchor:{row.get('challenge_id')}")
        require(isinstance(oracle["test_locator"], str) and "::test_" in oracle["test_locator"], f"oracle test locator:{row.get('challenge_id')}")
        challenge_text = json.dumps({key: row.get(key) for key in ("category", "target", "source_case_ref", "mutation", "valid_value", "single_mutation", "oracle_contract", "stage_oracle_contract")}, ensure_ascii=False, sort_keys=True).lower()
        require(not any(marker in challenge_text for marker in CHALLENGE_PLACEHOLDER_MARKERS) and re.search(r"<[^>]+>", challenge_text) is None, f"placeholder or alias challenge:{row.get('challenge_id')}")
        require(row["test_metadata_only"] is True and row["authority_source_forbidden"] == COMMON_FORBIDDEN, f"challenge metadata gate:{row['challenge_id']}")
        if row["origin"] in {"accepted_parent_r5_v0.3", "s5_contract_specific"}:
            if mutation["op"] == "remove":
                require(row["mutation"] == mutation["value"], f"negative remove mutation:{row['challenge_id']}")
            else:
                require(row["mutation"] == mutation["value"] and mutation["value"] != row["valid_value"], f"negative mutation is null:{row['challenge_id']}")
            if row["origin"] == "s5_contract_specific":
                require(row["expected_outcome"].startswith("reject:"), f"negative outcome not reject:{row['challenge_id']}")
                require(row["expected_projection"] == "not_emitted", f"negative projection emitted:{row['challenge_id']}")
        else:
            require(row["origin"] == "accepted_public_authority_producer_record" and row["source_case_ref"] in REPLAY_CASES, f"replay origin:{row['challenge_id']}")
            require(row["single_mutation"]["op"] == "replay" and row["single_mutation"]["value"] == row["source_case_ref"], f"replay mutation:{row['challenge_id']}")
            require(row["expected_outcome"] == "accept_replay_only" and row["expected_projection"] == "packet_emitted", f"replay gate:{row['challenge_id']}")
    mutation_tuples = {(row["single_mutation"]["op"], row["single_mutation"]["path"], digest(row["single_mutation"]["value"])) for row in actual["rows"]}
    require(len(mutation_tuples) == 250 and actual["unique_single_mutation_tuple_count"] == len(mutation_tuples), "single mutation uniqueness")
    s5_rows = [row for row in actual["rows"] if row["origin"] == "s5_contract_specific"]
    for row, spec in zip(s5_rows, S5_CHALLENGE_SPECS):
        category, target, outcome = spec
        require((row["category"], row["target"], row["expected_outcome"]) == (category, target, outcome), f"S5 negative specification:{row['challenge_id']}")
    replay = [row["source_case_ref"] for row in actual["rows"] if row["origin"] == "accepted_public_authority_producer_record"]
    require(replay == list(REPLAY_CASES), "accepted replay case coverage")
    require(all(row["challenge_id"].startswith("parent::") for row in actual["rows"][:204]), "parent challenge ordering")
    require(all(row["target"] in {rule.split(".", 1)[1] if "." in rule else rule for rule in rule_ids} for row in actual["rows"][:204]), "parent challenge target coverage")
    require(actual == expected, "challenge registry independent reconstruction")


def verify_future_cross_domain_leaf(exact: dict[str, Any], challenge: dict[str, Any], manifest: dict[str, Any]) -> None:
    contract = FUTURE_RUNTIME_VALIDATION_CONTRACT
    require(exact.get("future_runtime_validation_contract") == contract, "exact future cross-domain contract")
    require(challenge.get("future_runtime_validation_contract") == contract, "challenge future cross-domain contract")
    require(manifest.get("future_runtime_validation_contract") == contract, "manifest future cross-domain contract")
    invariant = next((item for item in exact["invariants"] if item.get("id") == "future_s5_cross_domain_validator"), None)
    require(invariant is not None and invariant["required"] is True and invariant["runtime_absent_until_fresh_acceptance"] is True, "required future cross-domain invariant")
    require(invariant["validator_ref"] == contract["validator_path"] + ":" + contract["validator_function"], "future validator leaf binding")
    require(invariant["test_locator"] == contract["test_path"], "future validator test binding")
    require(contract["validator_path"] in FUTURE_RUNTIME_ALLOWLIST and contract["test_path"].split("::", 1)[0] in FUTURE_RUNTIME_ALLOWLIST and contract["challenge_test_path"].split("::", 1)[0] in FUTURE_RUNTIME_ALLOWLIST, "future cross-domain path allowlist")
    require(not (ROOT / contract["validator_path"]).exists() and not (ROOT / contract["test_path"].split("::", 1)[0]).exists() and not (ROOT / contract["challenge_test_path"].split("::", 1)[0]).exists(), "future cross-domain runtime absence")
    matrix = exact["audience_constants"]["domain_subtype_matrix"]
    require("ip_dose" not in matrix["ae"] and "ip_dose" in matrix["ip"], "cross-domain fail-closed leaf")


def verify_public_inputs(exact: dict[str, Any], manifest: dict[str, Any], evidence: dict[str, Any], temporal: dict[str, Any], recipes: dict[str, Any], fixtures: dict[str, Any], typed_manifest: dict[str, Any], public_impl_manifest: dict[str, Any]) -> dict[str, str]:
    combined = verify_pins(evidence)
    require(manifest["input_raw_sha256"] == combined, "manifest input raw pin map")
    require(digest(evidence) == EXPECTED_EVIDENCE_CONTENT_HASH, "public evidence content identity")
    require(evidence["protected_boundaries"] == {"medical_writing_file_count": EXPECTED_MEDICAL_WRITING_COUNT, "medical_writing_inventory_sha256": EXPECTED_MEDICAL_WRITING_INVENTORY, "port_8911": "stopped"}, "public protected boundary aggregate")
    require(manifest["protected_boundaries"] == {"accepted_inputs_immutable": True, "medical_writing_file_count": EXPECTED_MEDICAL_WRITING_COUNT, "medical_writing_inventory_sha256": EXPECTED_MEDICAL_WRITING_INVENTORY, "port_8911": "stopped_required", "producer_runtime_not_created_by_worker_01": True}, "manifest protected boundaries")
    require(manifest["protected_boundaries"]["port_8911"] == "stopped_required", "manifest stopped-port boundary")
    require(public_impl_manifest["manifest_content_hash"] == "5483374f9d4600bc9dd302069249d80599cb281fb5ce05f06e25a65232c83c1e", "public implementation manifest identity")
    require(public_impl_manifest["manifest_content_hash"] == digest({key: value for key, value in public_impl_manifest.items() if key != "manifest_content_hash"}), "public implementation manifest hash")
    require(typed_manifest["manifest_content_hash"] == "38a8cadee3bcac6dd74a5ce9d522c9f744e82592f87089423e7783be7f6be976", "typed manifest identity")
    require(typed_manifest["manifest_content_hash"] == digest({**typed_manifest, "manifest_content_hash": ""}), "typed manifest hash")
    require(load_json(PARENT_EXACT)["contract_sha256"] == "1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6", "parent contract content identity")
    identity_checks = {
        SUBJECT_SCHEMA: "57b1560848c6265702263273d97ad5ead3c2137a22b999a5f2841692697e24bf",
        AEMH_SCHEMA: "0423ab019f9864ea070e33bc11dc1167fe39be9c09c9ab142f2c99c53cbf4648",
        TEMPORAL_SCHEMA: "e18e6a3dd9fe5e641cc8faa3f397319c306311e0a6dadc2bb8aec764ddff0395",
        TEMPORAL_RECIPES: "b8dfc691dee6148308aeeaa1a38e56bb927a6bae64ec710cd2051ec7fd727274",
        TEMPORAL_FIXTURES: "a7e8799c5bf38658e6a6da03a72e8c2cfda3ff11d597c98d240a3f4244cc0923",
    }
    for relative, expected in identity_checks.items():
        require(digest(load_json(relative)) == expected, f"input content identity:{relative}")
    require(load_json(TYPED_AUTHORITY)["counts"]["contract_content_hash"] == "c7096021f0486a7bca8d7eddfded56f4721ba4e794cbd2930a26da308300d064", "typed authority content identity")
    require(manifest["input_content_identities"] == {
        PARENT_EXACT: "1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6",
        AEMH_SCHEMA: "0423ab019f9864ea070e33bc11dc1167fe39be9c09c9ab142f2c99c53cbf4648",
        SUBJECT_SCHEMA: "57b1560848c6265702263273d97ad5ead3c2137a22b999a5f2841692697e24bf",
        PUBLIC_IMPL_MANIFEST: "5483374f9d4600bc9dd302069249d80599cb281fb5ce05f06e25a65232c83c1e",
        TEMPORAL_RECIPES: "b8dfc691dee6148308aeeaa1a38e56bb927a6bae64ec710cd2051ec7fd727274",
        TEMPORAL_FIXTURES: "a7e8799c5bf38658e6a6da03a72e8c2cfda3ff11d597c98d240a3f4244cc0923",
        TEMPORAL_SCHEMA: "e18e6a3dd9fe5e641cc8faa3f397319c306311e0a6dadc2bb8aec764ddff0395",
        TYPED_AUTHORITY: "c7096021f0486a7bca8d7eddfded56f4721ba4e794cbd2930a26da308300d064",
    }, "manifest input content identities")
    require(manifest["accepted_authority_pins"] == {
        "parent_r5_v0_3": exact["parent_contract"],
        "public_authority_producer_acceptance_record": EXPECTED_INPUT_PINS[PRODUCER_ACCEPTANCE],
        "public_authority_implementation_manifest_content_hash": public_impl_manifest["manifest_content_hash"],
        "typed_authority_manifest_content_hash": typed_manifest["manifest_content_hash"],
        "public_authority_evidence_content_hash": digest(evidence),
        "accepted_public_authority_producer_raw_sha256": dict(sorted(EXPECTED_ACCEPTED_PUBLIC_PINS.items())),
    }, "accepted authority pins")
    require(manifest["accepted_public_authority_producer_raw_sha256"] == dict(sorted(EXPECTED_ACCEPTED_PUBLIC_PINS.items())), "accepted public-authority raw pin map")
    require(temporal["schema_version"] == "2026-08-21.1" and len(recipes["executable_v02_recipes"]) == 16 and fixtures["positive_valid_count"] == 10, "typed temporal upstream facts")
    return combined


def verify_manifest(actual: dict[str, Any], exact: dict[str, Any], matrix: dict[str, Any], challenges: dict[str, Any], evidence: dict[str, Any], source_pins: dict[str, str]) -> None:
    expected_keys = {"acceptance_token", "acceptance_token_emitted", "accepted_authority_pins", "accepted_public_authority_producer_raw_sha256", "contract_id", "core_leaf_gate", "counts", "exact_owned_paths", "expected_complete_paths", "file_raw_sha256", "future_runtime_allowlist", "future_runtime_validation_contract", "input_content_identities", "input_raw_sha256", "manifest_content_hash", "manifest_hash_recipe", "protected_boundaries", "public_authority_producer_allowlist", "runtime_surface_scan", "schema", "schema_version", "self_acceptance", "status", "unlock", "verifier_raw_sha256", "worker_verifier_path"}
    require(set(actual) == expected_keys, "manifest top-level keys")
    require(actual["schema"] == "medical-monitoring-r5-s5-subject-workspace-contract-manifest-v0.1" and actual["schema_version"] == SCHEMA_VERSION and actual["contract_id"] == CONTRACT_ID, "manifest identity")
    require(actual["status"] == "candidate_unaccepted" and actual["self_acceptance"] is False and actual["acceptance_token_emitted"] is False and actual["acceptance_token"] == ACCEPTANCE_TOKEN, "manifest candidate state")
    require(actual["exact_owned_paths"] == list(OWNED_PATHS) and actual["expected_complete_paths"] == list(EXPECTED_COMPLETE_PATHS), "manifest path surface")
    require(actual["worker_verifier_path"] == EXPECTED_COMPLETE_PATHS[-1], "manifest verifier path")
    expected_file_hashes = dict(EXPECTED_OUTPUT_SHA)
    expected_file_hashes[EXPECTED_COMPLETE_PATHS[-1]] = actual["verifier_raw_sha256"]
    require(actual["file_raw_sha256"] == expected_file_hashes, "manifest frozen output hashes")
    for relative, expected in EXPECTED_OUTPUT_SHA.items():
        require(raw_sha(ROOT / relative) == expected, f"output hash:{relative}")
    require(raw_sha(VERIFIER) == actual["verifier_raw_sha256"], f"verifier raw hash binding:manifest={actual['verifier_raw_sha256']} observed={raw_sha(VERIFIER)}")
    counts = {"canonical_leaf_count": 265, "core_leaf_count": 216, "deferred_core_leaf_count": 0, "placeholder_core_leaf_count": 0, "self_signed_core_leaf_count": 0, "parent_leaf_count": 195, "parent_replaced_leaf_count": 53, "challenge_row_count": 250, "unique_single_mutation_tuple_count": 250, "domain_count": 8, "presentation_leaf_count": 22, "future_runtime_allowlist_count": 11}
    require(actual["counts"] == counts, "manifest counts")
    require(actual["core_leaf_gate"] == {"deferred": [], "placeholder": [], "self_signed": [], "eligible_for_independent_review": True}, "manifest core gate")
    require(actual["public_authority_producer_allowlist"] == sorted(EXPECTED_ACCEPTED_PUBLIC_PINS), "manifest public source allowlist")
    require(actual["accepted_public_authority_producer_raw_sha256"] == dict(sorted(EXPECTED_ACCEPTED_PUBLIC_PINS.items())), "manifest accepted producer pin map")
    expected_future = [{"path": path, "create_only": True, "present": False, "kind": "synthetic_offline_runtime_or_test", "allowed_only_after": ACCEPTANCE_TOKEN, "real_project_or_model": False, "starts_8911": False, "medical_writing": False} for path in FUTURE_RUNTIME_ALLOWLIST]
    require(actual["future_runtime_allowlist"] == expected_future, "manifest future runtime allowlist")
    require(actual["future_runtime_validation_contract"] == FUTURE_RUNTIME_VALIDATION_CONTRACT, "manifest future runtime validation contract")
    require(actual["manifest_hash_recipe"] == "sha256(canonical_json(all manifest fields except manifest_content_hash))", "manifest hash recipe")
    require(actual["manifest_content_hash"] == digest({key: value for key, value in actual.items() if key != "manifest_content_hash"}), "manifest content hash")
    require(actual["unlock"] == {"on_fresh_acceptance": "only future_runtime_allowlist create-only synthetic/offline paths", "requires_all": [ACCEPTANCE_TOKEN, "independent verifier normal/O/OO", "negative and replay gates", "fresh isolated review or conference decision", "decision binds exact.contract_content_hash", "decision binds manifest.manifest_content_hash", "decision binds manifest.file_raw_sha256[tools/generate_medical_monitoring_r5_s5_subject_workspace_contract_v0_1.py]", "decision binds manifest.file_raw_sha256[tools/verify_medical_monitoring_r5_s5_subject_workspace_contract_v0_1.py]", "decision binds all generated artifact raw hashes", "stopped port 8911", "unchanged medical-writing boundary"], "fresh_isolated_acceptance_record": {"required": True, "decision": ACCEPTANCE_TOKEN, "binds": ["exact.contract_content_hash", "manifest.manifest_content_hash", "manifest.file_raw_sha256[generator]", "manifest.file_raw_sha256[verifier]", "manifest.file_raw_sha256[all_owned_generated_artifacts]", "acceptance_token"], "external_record_only": True, "verifier_self_hash_inside_own_source_forbidden": True}, "does_not_unlock": ["8911", "UI or browser", "real projects or models", "product or production", "medical-writing", "accepted producer mutation", "security work"]}, "manifest unlock boundary")
    require(source_pins == actual["input_raw_sha256"], "manifest source pin identity")


def runtime_surface_snapshot() -> dict[str, Any]:
    files: dict[str, str] = {}
    for root_relative in RUNTIME_SURFACE_ROOTS:
        root = ROOT / root_relative
        require(root.is_dir(), f"missing runtime surface root:{root_relative}")
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(ROOT).as_posix()
            require(not path.is_symlink(), f"runtime surface symlink:{relative}")
            if not path.is_file() or "/__pycache__/" in f"/{relative}/" or path.suffix in {".pyc", ".pyo"}:
                continue
            files[relative] = raw_sha(path)
    return {
        "mode": "exact_frozen_non_cache_file_inventory",
        "roots": list(RUNTIME_SURFACE_ROOTS),
        "ignored_cache_rules": list(RUNTIME_SURFACE_IGNORED_CACHE_RULES),
        "frozen_file_count": len(files),
        "frozen_file_raw_sha256": dict(sorted(files.items())),
        "frozen_inventory_content_hash": digest(files),
        "future_allowlist_absence_required": True,
        "unexpected_new_path_policy": "fail_closed_before_generation",
    }


def verify_runtime_boundaries(manifest: dict[str, Any]) -> None:
    for item in manifest["future_runtime_allowlist"]:
        path = ROOT / item["path"]
        require(not path.exists() and item["present"] is False, f"future runtime path present:{item['path']}")
    snapshot = runtime_surface_snapshot()
    require(snapshot["frozen_inventory_content_hash"] == RUNTIME_SURFACE_BASELINE_HASH, f"runtime surface baseline drift:{snapshot['frozen_inventory_content_hash']}")
    require(manifest["runtime_surface_scan"] == snapshot, "manifest runtime surface scan")
    require(snapshot["frozen_file_count"] == 51, "runtime surface file count")
    require(all(not (ROOT / item["path"]).exists() and item["present"] is False for item in manifest["future_runtime_allowlist"]), "future runtime absence")
    for path in ARTIFACT_DIR.rglob("*"):
        if path.name in {"__pycache__", ".pytest_cache"} or path.suffix in {".pyc", ".pyo"}:
            fail(f"contract artifact cache path:{rel_path(path)}")


def verify_no_asserts() -> None:
    for path in (GENERATOR, VERIFIER):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)), f"assert statement:{rel_path(path)}")


def run_command(command: list[str], label: str) -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
    require(result.returncode == 0, f"{label}:rc={result.returncode}:stdout={result.stdout[-800:]}:stderr={result.stderr[-800:]}")


def run_generator_semantic_mutation_gates() -> None:
    script = r'''
import copy
import importlib.util
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("s5_generator", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
parent = module.load_json(module.PARENT_EXACT_REL)
stage_text = (module.ROOT / module.STAGE_REL).read_text(encoding="utf-8")

def mutated_constants(name):
    if name == "severity_line_weight_99":
        return {"SEVERITY_ENCODING": tuple(dict(item, line_weight=99) if index == 1 else dict(item) for index, item in enumerate(module.SEVERITY_ENCODING))}
    if name == "legacy_severe_to_critical":
        return {"LEGACY_SEVERITY_MAPPING": tuple(dict(item, severity="critical") if index == 0 else dict(item) for index, item in enumerate(module.LEGACY_SEVERITY_MAPPING))}
    if name == "domain_matrix_cm_ip_swap":
        return {"DOMAIN_SUBTYPE_MATRIX": {**module.DOMAIN_SUBTYPE_MATRIX, "cm": ["ip_dose"]}}
    if name == "domain_shape_protocol_triangle":
        return {"DOMAIN_ENCODING": tuple(dict(item, event_shape="triangle") if index == 7 else dict(item) for index, item in enumerate(module.DOMAIN_ENCODING))}
    if name == "forbidden_term_remove_unread":
        return {"FORBIDDEN_TERMS": tuple(item for item in module.FORBIDDEN_TERMS if item != "未读")}
    raise SystemExit("UNKNOWN_SEMANTIC_MUTATION:" + name)

for name in ("severity_line_weight_99", "legacy_severe_to_critical", "domain_matrix_cm_ip_swap", "domain_shape_protocol_triangle", "forbidden_term_remove_unread"):
    names = ("SEVERITY_ENCODING", "LEGACY_SEVERITY_MAPPING", "DOMAIN_SUBTYPE_MATRIX", "DOMAIN_ENCODING", "FORBIDDEN_TERMS")
    originals = {key: copy.deepcopy(getattr(module, key)) for key in names}
    try:
        for key, value in mutated_constants(name).items():
            setattr(module, key, value)
        try:
            module.validate_parent_derived_constants(parent, stage_text)
        except SystemExit:
            continue
        raise SystemExit("ACCEPTED_UNEXPECTEDLY:" + name)
    finally:
        for key, value in originals.items():
            setattr(module, key, value)
print("GENERATOR_SEMANTIC_MUTATIONS_OK")
'''
    for optimization, label in ((None, "normal"), ("-O", "O"), ("-OO", "OO")):
        command = [sys.executable]
        if optimization:
            command.append(optimization)
        command.extend(["-B", "-c", script, str(GENERATOR)])
        run_command(command, f"generator-semantic-mutations-{label}")


def run_generator_gates() -> None:
    for optimization, label in ((None, "generator-normal"), ("-O", "generator-O"), ("-OO", "generator-OO")):
        command = [sys.executable]
        if optimization:
            command.append(optimization)
        command.extend([str(GENERATOR), "--check"])
        run_command(command, label)
    module = str(GENERATOR).replace("\\", "\\\\")
    script = (
        "import importlib.util; p=" + repr(module) + "; s=importlib.util.spec_from_file_location('s5_generator',p); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); a=m.build_all(); b=m.build_all()\n"
        "if a != b:\n    raise SystemExit('NONDETERMINISTIC')\n"
        "print('DOUBLE_GENERATION_OK')"
    )
    run_command([sys.executable, "-B", "-c", script], "generator-double-generation")
    run_generator_semantic_mutation_gates()


def verify_negative_and_replay_gate(challenge: dict[str, Any], acceptance_record: str) -> None:
    for category, target, expected in S5_CHALLENGE_SPECS:
        needle = f"s5::{S5_CHALLENGE_SPECS.index((category, target, expected)) + 1:03d}"
        rows = [row for row in challenge["rows"] if row["challenge_id"] == needle]
        require(len(rows) == 1, f"negative gate row missing:{needle}")
        row = rows[0]
        mutation = row["single_mutation"]
        baseline_valid = "valid_value" in row and "value" in mutation
        mutated = mutation["op"] == "remove" or mutation["value"] != row["valid_value"]
        require(baseline_valid and mutated, f"negative mutation not isolated:{needle}")
        require(row["expected_outcome"] == expected and row["expected_projection"] == "not_emitted", f"negative oracle:{needle}")
    for reference in REPLAY_CASES[:3]:
        require(reference in acceptance_record, f"accepted replay reference missing:{reference}")
    require("R5C-157" in acceptance_record and "R5C-163" in acceptance_record, "accepted replay range missing:R5C-157..R5C-163")
    require("exact accepted graph replay: `10/10`" in acceptance_record, "accepted replay count evidence")


def verify_port_stopped() -> None:
    addresses = []
    for host in ("localhost", "127.0.0.1", "::1"):
        try:
            addresses.extend(socket.getaddrinfo(host, 8911, type=socket.SOCK_STREAM))
        except socket.gaierror:
            continue
    seen = set()
    for family, socktype, proto, _, sockaddr in addresses:
        key = (family, sockaddr)
        if key in seen:
            continue
        seen.add(key)
        sock = socket.socket(family, socktype, proto)
        sock.settimeout(0.25)
        try:
            result = sock.connect_ex(sockaddr)
        finally:
            sock.close()
        require(result != 0, f"port 8911 listener:{sockaddr}")
    lsof = shutil.which("lsof")
    require(lsof is not None, "broad 8911 listener check unavailable:lsof")
    result = subprocess.run([lsof, "-nP", "-a", "-iTCP:8911", "-sTCP:LISTEN"], capture_output=True, text=True)
    require(result.returncode in {0, 1}, f"broad 8911 listener check rc={result.returncode}:{result.stderr[-400:]}")
    require(not result.stdout.strip(), f"broad 8911 listener:{result.stdout[-800:]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        verify_no_asserts()
        parent = load_json(PARENT_EXACT)
        parent_registry = load_json(PARENT_CHALLENGES)
        parent_quota = load_json(PARENT_QUOTA)
        subject = load_json(SUBJECT_SCHEMA)
        aemh = load_json(AEMH_SCHEMA)
        temporal = load_json(TEMPORAL_SCHEMA)
        recipes = load_json(TEMPORAL_RECIPES)
        fixtures = load_json(TEMPORAL_FIXTURES)
        typed = load_json(TYPED_AUTHORITY)
        typed_manifest = load_json(TYPED_MANIFEST)
        public_impl_manifest = load_json(PUBLIC_IMPL_MANIFEST)
        public_impl_future = load_json(PUBLIC_IMPL_FUTURE)
        evidence = load_json(PUBLIC_EVIDENCE)
        acceptance_record = (ROOT / PRODUCER_ACCEPTANCE).read_text(encoding="utf-8")
        actual_exact = load_json(rel_path(EXACT))
        actual_matrix = load_json(rel_path(MATRIX))
        actual_challenge = load_json(rel_path(CHALLENGE))
        actual_manifest = load_json(rel_path(MANIFEST))
        audience_expected = expected_audience_constants(parent, (ROOT / STAGE_REVIEW).read_text(encoding="utf-8"))
        objects = expected_objects(subject, aemh)
        expected_matrix_doc = expected_matrix(parent, objects, audience_expected)
        expected_challenge_doc = expected_challenges(parent, parent_registry, parent_quota)
        expected_exact_doc = expected_exact_contract(parent, subject, aemh, temporal, recipes, fixtures, typed, expected_matrix_doc, expected_challenge_doc, audience_expected)
        verify_exact_contract(actual_exact, expected_exact_doc)
        verify_matrix(actual_matrix, expected_matrix_doc, parent, subject, aemh)
        verify_challenges(actual_challenge, expected_challenge_doc, parent, parent_registry)
        verify_future_cross_domain_leaf(actual_exact, actual_challenge, actual_manifest)
        source_pins = verify_public_inputs(actual_exact, actual_manifest, evidence, temporal, recipes, fixtures, typed_manifest, public_impl_manifest)
        verify_manifest(actual_manifest, actual_exact, actual_matrix, actual_challenge, evidence, source_pins)
        require(public_impl_future["create_only_path_count"] == 11 and public_impl_future["files_present"] is False and public_impl_future["producer_executed"] is False, "accepted producer future surface")
        require(sorted(public_impl_future["create_only_paths"]) == sorted(["poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py", "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py", "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py", "poc/medical_monitoring_ai_native_r5/tests/public_authority_runtime_fixtures.py", "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py", "poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py", "poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py", "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py", "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_readonly_gate.py", "poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py", PUBLIC_EVIDENCE]), "accepted producer path surface")
        verify_negative_and_replay_gate(actual_challenge, acceptance_record)
        verify_runtime_boundaries(actual_manifest)
        verify_port_stopped()
        run_generator_gates()
        print(f"VERIFY_OK contract={CONTRACT_ID} canonical_leaves=265 core_leaves=216 presentation_leaves=22 challenges=250 source_pins={len(source_pins)} future_runtime_paths=11 port_8911=stopped medical_writing_files={EXPECTED_MEDICAL_WRITING_COUNT}")
    except VerificationError as exc:
        print(f"VERIFY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
