"""Independent non-LLM verifier for error replay coverage delta v0.1."""

from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
import tempfile
import unicodedata
from collections.abc import Callable
from typing import Any, NoReturn

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1"
GENERATOR = ROOT / "tools/generate_medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1.py"
VERIFIER = pathlib.Path(__file__).resolve()
PARENT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
SEMANTIC_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1"
TEMPORAL_V01_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1"
TEMPORAL_V02_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2"
SUBJECT_SCHEMA_REL = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json"
AEMH_SCHEMA_REL = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json"
PARENT_VERIFIER_REL = "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py"
SUBJECT = "subject-temporal-public-v1"
AEMH = "aemh-match-history-public-v1"
CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-error-replay-coverage-delta-v0.1"
SCHEMA_VERSION = "2026-08-21.1"

APPEND_ONLY_AUTHORITY_HARD_PINS = {
    "subject_schema_raw_sha256": "d2f56f21dc7b228736b2efbdc4c1db3a28185e25895563c0b59a812cd126a0f4",
    "subject_identity_invariant": ("/invariants/1", "2c61e751e68fbd960b1cc144e6b5ca1bd488c8390f62485df7cdc3cf6d8c32b6"),
    "subject_validator_ast_sha256": "f4f287e127be90e7197c432fad04637819dff08c52c783cf4146f985e5ce8534",
    "aemh_schema_raw_sha256": "479dc2759833d698fd761247f4ec504069880717ec9c64631242ad2554b19840",
    "aemh_history_invariant": ("/invariants/12", "b46963815f03b3e3a5b2f799798685f9c8ab3abd9c9ef262f11b95a4d4360194"),
    "aemh_supporting_invariants": (
        ("/invariants/17", "5cad2074816dc7bef6df6e00d306a2efd6b3d9a8d1d9f8918a4506a0e565cf4b"),
        ("/invariants/18", "e25c514e74e1b10ee3cbe12722bc6286d8f31d38f04829587d736bcc7e32b664"),
    ),
    "aemh_validator_ast_sha256": "6eefe1e0689ea942cb90361d74b9228eb397043e7f15b7928c7946ddb9ab0dda",
}

NEGATIVE_V01_PINS = {
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/invariant_error_matrix.json": "36e3497f9993f631d3c62abb144cbaad4aca339d60053a13656c6f164fac9e20",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/manifest.json": "19d1769095d884f9bc5409a2af6795f24fce7f8c81c5132f2dce54b34303502a",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/public_api.json": "70dd9ffea90d84145b00cb058f32cb30a93220e79d23fcf17cbe64e26fb7a0bc",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/source_join_matrix.json": "b4c4504fdb616e76012d1ae57e71abc57ea384896f3d3aa784db85c696983213",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/test_matrix.json": "428bc85b806212e7ce4d03bffc6bd807aff2bfae9e7f288adeae0508fdb91c2e",
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_20260819_context.md": "74b61738458f5f564a19b9867cf59e232100467ab2bc15fc964c63b88b20be05",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1_20260819.md": "67aae3a80f928f6887d594bc9a1fbd53fb6e5a9eb0947853f263cd3294f0c745",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py": "6a02c5c65565d1ff7becad4b71f8413e695f8d556d97abbc1d5d9b2e2ff1b3b0",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py": "c20c7b2008c4c441b80c91ee0a5f6c2118bb9303ddfcfa025dda88e65a953d94",
}
NEGATIVE_V02_PINS = {
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/invariant_error_matrix.json": "7caf087038b15222abb7526f69424627d957f3b61ee4ad2fb8e15a6b4ebc2bcb",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/manifest.json": "cf805305e927caee07464061e95ac894a866b3a5a444d29f012e26ea92893e6f",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/public_api.json": "5ba41225cb76b91a69e634a728fe0af83a9062f08a39a2cafadd6643de111141",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/source_join_matrix.json": "0e35d32e7d39ca2994ae1e58c8d547e170dc2cdeeb44a417210744d7f021a970",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/test_matrix.json": "f7af7ca0cf4a4567397ff0587a857f25fd9e6af80ca71689f84242f1eb906c9c",
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_20260820_context.md": "7e16dd10f580f6dc7dcc49a771bd62ac553e5a8bd52b1a409967815ce20f144b",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_20260820.md": "7f9e9efa935d6d6c8112cc645c84ba72fbd5670626f097e04a67d1b73aedcd9b",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py": "aa4266cef074b8afb76d7d57993a767fdbae1dc02aba3586eccccb4d7e3110c1",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py": "e5384b6c3404288352bf8540634b4761f61a39a4e37fd133136cd17e09916104",
}
NEGATIVE_V03_PINS = {
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/invariant_error_matrix.json": "77780a7d95dc468ca64efda9a49bde28d701313c19c7a26440852dcb23aa9170",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/manifest.json": "c3c9e9d2ba6cb25bf9f73d4a4f685b2e8f8cb8bf4ba5707803d1a356061a4f35",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/public_api.json": "a10e30115c8351a30ed1987ed1eb6b230e5b2ab1a225887a4bda5d117c6aff0a",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/source_join_matrix.json": "85b5678debd1f99f2df07810a39a29aaf508d833e1f5a8afeda3f689480d08d8",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/test_matrix.json": "7937c0e2d71b1397ed4eddee22e7dd3343459ae4fa9a84fc49aa657983338466",
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_20260820_context.md": "a94f9c793c03339ce8c342e54db68f706693464e24208470d28d1a981160f448",
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_rejection_record_20260820.md": "11b2baf15c1c89cc22a0a052c2e591ba6ce88e79cf660535578f6ba07e98099a",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_20260820.md": "68e82a6e248a60f56e339f31f9416da2954e347b335d55abeb9e566300590a3c",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py": "5cad78d95fed0e83eb587bc3804859c84301b3771ba8cde56c443e119010c9ae",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py": "ebf426693566d6cee73aea8d62958219b846b7baca55b136fcd917be835049e5",
}
NEGATIVE_V02_RECORD = (
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_rejection_record_20260820.md",
    "3a8bad1ba05f0cbf8a551051140b68823f7b6dc8c450e0068c0f8b11046d5dd5",
)

EXTERNAL_ROOT_PIN_ITEMS = (
    ("artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json", "92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270"),
    ("context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md", "23fed5b186057a79cd0ec43a7718e43934ebafdc8f62fd251077d4fb6891639d"),
    ("artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/manifest.json", "66605a46c10e2aa4d36b06e566158666a08cdc92ec0e630364aad5b9ffb2385d"),
    ("context/medical_monitoring_r5_s5_semantic_authority_delta_acceptance_record_20260820.md", "bf50156fa82d825309fce72115ddf971fc4e0bdbd60936ea45e2362a6aa3eb4c"),
    ("artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/manifest.json", "e606e517c07dcb499657b418dbd16e4dacd98c7e7010770845dbccb91af59f97"),
    ("context/medical_monitoring_r5_s5_temporal_projection_authority_delta_acceptance_record_20260820.md", "523351f1b5536b12c1a5be9251ad01f4e8b7a70f5088073a2333aefc241d1b79"),
    ("artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/manifest.json", "466b0ae605b83a57f0e184446db311beb05ff5e4e1998a7dc5be9bb44d2b7de8"),
    ("context/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2_acceptance_record_20260821.md", "d08b4ed27f9829db4cdcab0837f3623c244ee8c888cce699c55580621bd68ef4"),
)

PROTECTED_SCALAR_BINDINGS = (
    ("accepted_r5_v0_3_exact_contract_sha256", "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json", "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949"),
    ("accepted_r4_r5_s4_readonly_manifest_sha256", "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s4_readonly_sha256.json", "53a927a08451b426edb9ac9578a6ea3b658ff8df1d5dd2b33f94fb0446647822"),
    ("r5_root_init_sha256", "poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py", "0a24c6993cb4997b1e77cefcfeeff490aaf882b269ab0fece8635ce81b6b4ebd"),
    ("s4_acceptance_record_sha256", "context/medical_monitoring_r5_s4_acceptance_record_20260819.md", "1d17297c44b371aefecf28cfc2388181b7be35d9e5cc830b148a0b3a9da1971e"),
)

EXACT_PATHS = {
    "context/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1_20260821_context.md",
    "reviews/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1_20260821.md",
    "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/schema.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/base_input_registry.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/gate_registry.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/challenge_registry.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/manifest.json",
    "tools/generate_medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1.py",
    "tools/verify_medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1.py",
}

MISSING_CODES = [
    "PUB_SCHEMA_EXACT_KEYS", "PUB_TYPE_BOOL_REQUIRED", "PUB_TYPE_MISMATCH",
    "PUB_IDENTITY_PROJECT_MISMATCH", "PUB_IDENTITY_RUN_MISMATCH", "PUB_IDENTITY_SNAPSHOT_MISMATCH",
    "PUB_IDENTITY_SITE_MISMATCH", "PUB_IDENTITY_SPINE_MISMATCH", "PUB_VISIBILITY_DEEP_LINK_INELIGIBLE",
    "PUB_RUNTIME_TEST_SURFACE_FORBIDDEN", "AEMH_WITHDRAW_REAPPEAR_HISTORY_LOSS", "SEM_TYPE_MISMATCH",
    "SEM_RISK_TAXONOMY_INCOMPLETE", "SEM_RISK_TAXONOMY_AMBIGUOUS", "SEM_SEVERITY_RULESET_INCOMPLETE",
    "SEM_SOURCE_RECORD_UNRESOLVED", "SEM_RECEIPT_HASH_MISMATCH", "SEM_ACCEPTED_RECORD_HASH_MISMATCH",
    "SEM_RECEIPT_PACKAGE_KIND_MISMATCH", "SEM_AUTHORITY_HASH_MISMATCH", "SEM_AUTHORITY_MISMATCH",
    "SEM_MANIFEST_HASH_MISMATCH",
]

GATE_KEYS = {
    "gate_id", "entrypoint_class", "accepted_source_path", "accepted_source_raw_sha256",
    "accepted_ast_selector", "accepted_ast_normalized_sha256", "input_type", "output_type",
    "permitted_error_codes", "algorithm_contract", "constructor_precondition", "mutation_phase",
    "reseal_handler", "issue_order_source", "side_effect_boundary",
}
BASE_KEYS = {
    "base_input_ref", "accepted_source_path", "accepted_source_raw_sha256", "accepted_source_json_pointer",
    "raw_input_identity", "canonical_input_identity", "constructor_id", "constructor_recipe",
}
CHALLENGE_KEYS = {
    "case_id", "surface", "error_code", "accepted_priority", "entrypoint_class", "gate_id", "base_input_ref",
    "base_input_content_identity", "constructor_id", "instance_selector", "single_mutation", "ordered_reseal",
    "observed_ordered_issues", "forbidden_output", "trace_identity",
}

BASE_EXPECTED_GATE_CODES = {
    "gate.parent.untrusted_exact_parser": {"PUB_SCHEMA_EXACT_KEYS", "PUB_TYPE_BOOL_REQUIRED", "PUB_TYPE_MISMATCH"},
    "gate.parent.visibility_source": {"PUB_VISIBILITY_DEEP_LINK_INELIGIBLE"},
    "gate.parent.runtime_surface": {"PUB_RUNTIME_TEST_SURFACE_FORBIDDEN"},
    "gate.semantic.common_parser": {"SEM_TYPE_MISMATCH"},
    "gate.semantic.risk_validator": {"SEM_RISK_TAXONOMY_INCOMPLETE", "SEM_RISK_TAXONOMY_AMBIGUOUS"},
    "gate.semantic.severity_validator": {"SEM_SEVERITY_RULESET_INCOMPLETE"},
    "gate.semantic.token_evidence": {"SEM_SOURCE_RECORD_UNRESOLVED"},
    "gate.semantic.receipt": {"SEM_RECEIPT_HASH_MISMATCH", "SEM_ACCEPTED_RECORD_HASH_MISMATCH", "SEM_RECEIPT_PACKAGE_KIND_MISMATCH"},
    "gate.semantic.candidate_comparison": {"SEM_AUTHORITY_HASH_MISMATCH", "SEM_AUTHORITY_MISMATCH"},
    "gate.semantic.manifest": {"SEM_MANIFEST_HASH_MISMATCH"},
}

EXPECTED_RESEAL = {
    ("gate.parent.untrusted_exact_parser", "/unexpected_root_key"): [],
    ("gate.parent.untrusted_exact_parser", "/receipt/visibility_closure/deep_link_eligible"): ["reseal_visibility_receipt_packet"],
    ("gate.parent.untrusted_exact_parser", "/projection/receipt_ref"): ["reseal_subject_projection_packet"],
    ("gate.parent.identity_dimension", "/receipt/scope_identity/project_ref"): ["reseal_receipt_scope_receipt_packet"],
    ("gate.parent.identity_dimension", "/receipt/scope_identity/run_ref"): ["reseal_receipt_scope_receipt_packet"],
    ("gate.parent.identity_dimension", "/receipt/scope_identity/snapshot_ref"): ["reseal_receipt_scope_receipt_packet"],
    ("gate.parent.identity_dimension", "/receipt/scope_identity/site_ref"): ["reseal_receipt_scope_receipt_packet"],
    ("gate.parent.identity_dimension", "/receipt/scope_identity/spine_ref"): ["reseal_receipt_scope_receipt_packet"],
    ("gate.parent.visibility_source", "/receipt/visibility_closure/deep_link_eligible"): ["reseal_visibility_receipt_packet"],
    ("gate.parent.runtime_surface", "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py"): [],
    ("gate.parent.aemh_history_preservation", "/current_packet/projection/threads/0/history_entries/3"): ["reseal_aemh_current_full"],
    ("gate.semantic.common_parser", "/taxonomy_package/package_id"): [],
    ("gate.semantic.risk_validator", "/taxonomy_package/rules"): ["reseal_taxonomy_package"],
    ("gate.semantic.severity_validator", "/severity_package/rules/0"): ["reseal_severity_package"],
    ("gate.semantic.token_evidence", "/taxonomy_evidence/source_record_ref"): ["reseal_taxonomy_evidence"],
    ("gate.semantic.receipt", "/taxonomy_receipt/receipt_content_hash"): [],
    ("gate.semantic.receipt", "/taxonomy_receipt/accepted_record_content_hash"): ["reseal_taxonomy_receipt"],
    ("gate.semantic.receipt", "/taxonomy_receipt/package_kind"): ["reseal_taxonomy_receipt"],
    ("gate.semantic.candidate_comparison", "/candidate_authority/authority_content_hash"): [],
    ("gate.semantic.candidate_comparison", "/candidate_authority/authority_ref"): ["reseal_candidate_authority"],
    ("gate.semantic.manifest", "/manifest_content_hash"): [],
}

RESEAL_ENV_KEYS = {
    "reseal_visibility_receipt_packet": frozenset({"parent", "subject_schema"}),
    "reseal_subject_projection_packet": frozenset({"parent", "subject_schema"}),
    "reseal_receipt_scope_receipt_packet": frozenset({"parent", "subject_schema"}),
    "reseal_aemh_current_full": frozenset({"parent", "aemh_schema"}),
    "reseal_taxonomy_package": frozenset({"semantic"}),
    "reseal_severity_package": frozenset({"semantic"}),
    "reseal_taxonomy_evidence": frozenset({"semantic"}),
    "reseal_taxonomy_receipt": frozenset({"semantic"}),
    "reseal_candidate_authority": frozenset({"semantic"}),
}

EXPECTED_BASES = {
    "base.parent.subject": ("artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json", "/baselines/0/authority_input", "temporal_v02.closed_16_recipe_32_node.subject"),
    "base.parent.aemh": ("artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json", "/baselines/1/authority_input", "temporal_v02.closed_16_recipe_32_node.aemh"),
    "base.semantic.risk_high": ("artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/challenge_registry.json", "/baselines/risk_high", "semantic.accepted_baseline.risk_high"),
    "base.semantic.risk_authority": ("artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/challenge_registry.json", "/baselines/risk_authority", "semantic.accepted_baseline.risk_authority"),
    "base.semantic.manifest": ("artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/manifest.json", "/", "semantic.accepted_manifest"),
    "base.governance.runtime": ("artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json", "/no_runtime_test_surface", "parent.accepted_runtime_surface_contract"),
}


def fail(message: str) -> NoReturn:
    raise SystemExit(f"STOP {message}")


def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def module(relative: str, name: str) -> Any:
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail(f"module load: {relative}")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def normalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", str(key)): normalize(item) for key, item in value.items()}
    return value


def canon(value: Any) -> bytes:
    return json.dumps(normalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canon(value)).hexdigest()


def raw(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def load_pinned_temporal_v02(candidate_raw: bytes | None = None) -> dict[str, Any]:
    external_roots = dict(EXTERNAL_ROOT_PIN_ITEMS)
    for relative, expected in EXTERNAL_ROOT_PIN_ITEMS:
        path = ROOT / relative
        if not path.is_file() or raw(path) != expected:
            fail(f"external authority root actual raw pin: {relative}")
    temporal_relative = (TEMPORAL_V02_DIR / "manifest.json").relative_to(ROOT).as_posix()
    temporal_raw = (TEMPORAL_V02_DIR / "manifest.json").read_bytes() if candidate_raw is None else candidate_raw
    if hashlib.sha256(temporal_raw).hexdigest() != external_roots[temporal_relative]:
        fail("external authority root raw pin: temporal v0.2 manifest")
    return json.loads(temporal_raw)


def get(document: Any, pointer: str) -> Any:
    current = document
    if pointer in ("", "/"):
        return current
    for part in pointer.strip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def contains_forbidden_mirror(value: Any) -> bool:
    if isinstance(value, dict):
        forbidden = {"packet_mirror", "output_mirror", "issue_mirror", "expected_mirror", "expected_output"}
        return any(key in forbidden or contains_forbidden_mirror(item) for key, item in value.items())
    if isinstance(value, list):
        return any(contains_forbidden_mirror(item) for item in value)
    return False


def parent_at(document: Any, pointer: str) -> tuple[Any, str]:
    parts = pointer.strip("/").split("/")
    current = document
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current, parts[-1]


def function_ast_hash(path: pathlib.Path, selector: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == selector]
    if len(found) != 1:
        fail(f"accepted AST selector: {path}:{selector}")
    payload = ast.dump(found[0], annotate_fields=True, include_attributes=False).encode()
    return hashlib.sha256(payload).hexdigest()


def priority_plane() -> tuple[list[str], dict[str, int], dict[str, str]]:
    subject = load(PARENT_DIR / "subject_temporal_schema.json")
    aemh = load(PARENT_DIR / "aemh_match_history_schema.json")
    semantic = load(SEMANTIC_DIR / "schema.json")
    temporal = load(TEMPORAL_V01_DIR / "challenge_registry.json")
    parent_codes = list(dict.fromkeys(subject["error_codes"] + aemh["error_codes"]))
    semantic_codes = list(semantic["typed_error_priority"])
    temporal_codes = sorted({item["expected_error"] for item in temporal["cases"]})
    ordered = parent_codes + semantic_codes + temporal_codes
    if len(ordered) != 192 or len(set(ordered)) != 192:
        fail("independent accepted error universe")
    origins = {item: "parent" for item in parent_codes}
    origins.update({item: "semantic_delta" for item in semantic_codes})
    origins.update({item: "temporal_delta" for item in temporal_codes})
    return ordered, {item: index for index, item in enumerate(ordered, 1)}, origins


def accepted_append_only_bindings(priorities: dict[str, int]) -> dict[str, Any]:
    subject_path = ROOT / SUBJECT_SCHEMA_REL
    aemh_path = ROOT / AEMH_SCHEMA_REL
    parent_path = ROOT / PARENT_VERIFIER_REL
    if raw(subject_path) != APPEND_ONLY_AUTHORITY_HARD_PINS["subject_schema_raw_sha256"]:
        fail("accepted subject schema pin drift")
    if raw(aemh_path) != APPEND_ONLY_AUTHORITY_HARD_PINS["aemh_schema_raw_sha256"]:
        fail("accepted AEMH schema pin drift")
    if function_ast_hash(parent_path, "validate_subject") != APPEND_ONLY_AUTHORITY_HARD_PINS["subject_validator_ast_sha256"]:
        fail("accepted subject validator AST drift")
    if function_ast_hash(parent_path, "validate_aemh") != APPEND_ONLY_AUTHORITY_HARD_PINS["aemh_validator_ast_sha256"]:
        fail("accepted AEMH validator AST drift")
    subject = load(subject_path)
    aemh = load(aemh_path)
    subject_pointer, subject_hash = APPEND_ONLY_AUTHORITY_HARD_PINS["subject_identity_invariant"]
    subject_invariant = get(subject, subject_pointer)
    if digest(subject_invariant) != subject_hash:
        fail("accepted subject identity invariant drift")
    match = re.fullmatch(r"receipt, projection, visibility and every member join the same ([a-z/]+) identity", subject_invariant)
    if match is None:
        fail("accepted subject identity invariant grammar")
    accepted_dimensions = [f"{token}_ref" for token in match.group(1).split("/")]
    target_identity_codes = {code for code in MISSING_CODES if code.startswith("PUB_IDENTITY_") and code.endswith("_MISMATCH")}
    dimension_bindings = []
    for dimension in accepted_dimensions:
        token = dimension.removesuffix("_ref").upper()
        matches = [code for code in subject["error_codes"] if re.fullmatch(rf"PUB_IDENTITY_{re.escape(token)}_MISMATCH", code) and code in target_identity_codes]
        if len(matches) == 1:
            code = matches[0]
            dimension_bindings.append({"dimension": dimension, "error_code": code, "accepted_priority": priorities[code]})
    if len(dimension_bindings) != 5 or {row["error_code"] for row in dimension_bindings} != target_identity_codes:
        fail("accepted identity dimension/error binding closure")
    history_pointer, history_hash = APPEND_ONLY_AUTHORITY_HARD_PINS["aemh_history_invariant"]
    history_ordinal = int(history_pointer.rsplit("/", 1)[1])
    history_value = get(aemh, history_pointer)
    matching_ordinals = [index for index, value in enumerate(aemh["invariants"]) if digest(value) == history_hash]
    if matching_ordinals != [history_ordinal] or digest(history_value) != history_hash:
        fail("accepted history selector must resolve exact one invariant")
    history_invariant = {
        "invariant_id": f"{aemh['schema']}#{history_pointer}",
        "ordinal": history_ordinal,
        "json_pointer": history_pointer,
        "value": history_value,
        "normalized_content_hash": history_hash,
    }
    event_kinds = [kind for kind in aemh["enums"]["history_event_kind"] if kind in history_value]
    if len(event_kinds) != 2:
        fail("accepted history event-kind binding")
    supporting_rows = []
    for pointer, expected_hash in APPEND_ONLY_AUTHORITY_HARD_PINS["aemh_supporting_invariants"]:
        value = get(aemh, pointer)
        if digest(value) != expected_hash:
            fail(f"accepted AEMH supporting invariant drift: {pointer}")
        supporting_rows.append({"invariant_id": f"{aemh['schema']}#{pointer}", "ordinal": int(pointer.rsplit("/", 1)[1]), "json_pointer": pointer, "value": value, "normalized_content_hash": expected_hash})
    stable_match = re.search(r"; ([a-z/]+) identity is stable across versions$", supporting_rows[-1]["value"])
    if stable_match is None:
        fail("accepted stable-thread invariant grammar")
    stable_terms = stable_match.group(1).split("/")
    thread_fields = list(aemh["objects"]["AEMHMatchThread"])
    stable_fields = sorted({field for field in thread_fields if field == "thread_ref" or any(term in field for term in stable_terms)})
    event_stems = [kind.removesuffix("n").removesuffix("ed").upper() for kind in event_kinds]
    history_codes = [code for code in aemh["error_codes"] if code.startswith("AEMH_") and all(stem in code for stem in event_stems) and "HISTORY" in code and "LOSS" in code]
    if len(history_codes) != 1 or history_codes[0] not in MISSING_CODES:
        fail("accepted history invariant/error binding closure")
    history_code = history_codes[0]
    return {
        "subject_identity": {
            "schema_path": SUBJECT_SCHEMA_REL,
            "schema_raw_sha256": raw(subject_path),
            "invariant": {"json_pointer": subject_pointer, "value": subject_invariant, "content_hash": subject_hash},
            "error_registry": {"json_pointer": "/error_codes", "content_hash": digest(subject["error_codes"])},
            "validator": {"source_path": PARENT_VERIFIER_REL, "selector": "validate_subject", "ast_normalized_sha256": function_ast_hash(parent_path, "validate_subject")},
            "dimension_bindings": dimension_bindings,
        },
        "aemh_history": {
            "schema_path": AEMH_SCHEMA_REL,
            "schema_raw_sha256": raw(aemh_path),
            "history_invariant": history_invariant,
            "supporting_invariants": supporting_rows,
            "event_registry": {"json_pointer": "/enums/history_event_kind", "content_hash": digest(aemh["enums"]["history_event_kind"])},
            "error_registry": {"json_pointer": "/error_codes", "content_hash": digest(aemh["error_codes"])},
            "validator": {"source_path": PARENT_VERIFIER_REL, "selector": "validate_aemh", "ast_normalized_sha256": function_ast_hash(parent_path, "validate_aemh")},
            "event_kinds": event_kinds,
            "stable_thread_fields": stable_fields,
            "error_code": history_code,
            "accepted_priority": priorities[history_code],
        },
    }


def expected_gate_codes(priorities: dict[str, int]) -> dict[str, set[str]]:
    result = copy.deepcopy(BASE_EXPECTED_GATE_CODES)
    bindings = accepted_append_only_bindings(priorities)
    result["gate.parent.identity_dimension"] = {row["error_code"] for row in bindings["subject_identity"]["dimension_bindings"]}
    result["gate.parent.aemh_history_preservation"] = {bindings["aemh_history"]["error_code"]}
    return result


def independent_pre_delta() -> tuple[dict[str, Any], set[str], list[str], dict[str, int], dict[str, str]]:
    ordered, priorities, origins = priority_plane()
    parent = module("tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py", "independent_parent_coverage_delta")
    registry = load(PARENT_DIR / "challenge_registry.json")
    exact = load(ROOT / "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json")
    subject_schema = load(PARENT_DIR / "subject_temporal_schema.json")
    aemh_schema = load(PARENT_DIR / "aemh_match_history_schema.json")
    inputs = load(PARENT_DIR / "base_inputs.json")
    parent_actual: list[str] = []
    for symbol in ("validate_subject", "validate_aemh", "overlay_validation_issues", "source_matrix_validation_issues", "manifest_contract_validation_issues"):
        original = getattr(parent, symbol)

        def capture(*args: Any, _call: Callable[..., list[str]] = original, **kwargs: Any) -> list[str]:
            issues = _call(*args, **kwargs)
            parent_actual.extend(issues)
            return issues

        setattr(parent, symbol, capture)
    with contextlib.redirect_stdout(io.StringIO()):
        parent_count = parent.verify_challenges(registry, exact, subject_schema, aemh_schema, inputs)

    semantic = module("tools/verify_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py", "independent_semantic_coverage_delta")
    semantic_manifest = load(SEMANTIC_DIR / "manifest.json")
    semantic_challenges = load(SEMANTIC_DIR / "challenge_registry.json")
    sr = semantic_manifest["synthetic_typed_source_record_registry"]
    ar = semantic_manifest["synthetic_policy_acceptance_registry"]
    sr_rows = semantic.validate_source_registry(sr)
    ar_rows = semantic.validate_acceptance_registry(ar)
    semantic_run = semantic.run_challenges(semantic_challenges, sr, sr_rows, ar, ar_rows)
    semantic_actual = {row["outcome"] for row in semantic_run["outcomes"] if row["outcome"] != "success"}

    temporal_v01 = module("tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1.py", "independent_temporal_v01_coverage_delta")
    manifest_01 = load(TEMPORAL_V01_DIR / "manifest.json")
    schema_01 = load(TEMPORAL_V01_DIR / "schema.json")
    matrix_01 = load(TEMPORAL_V01_DIR / "source_matrix_delta.json")
    recipes_01 = load(TEMPORAL_V01_DIR / "recipe_registry.json")
    challenges_01 = load(TEMPORAL_V01_DIR / "challenge_registry.json")
    temporal_v01.verify_schema(schema_01, manifest_01)
    temporal_v01.verify_source_matrix(matrix_01, manifest_01)
    temporal_v01.verify_typed_source_paths(matrix_01, manifest_01)
    recipe_map = temporal_v01.verify_recipes(recipes_01, schema_01, manifest_01)
    temporal_v01.verify_challenges(challenges_01, recipes_01, manifest_01, schema_01, recipe_map)
    temporal_01_actual = {row["expected_error"] for row in challenges_01["cases"]}

    temporal_v02 = module("tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py", "independent_temporal_v02_coverage_delta")
    manifest_02 = temporal_v02.load(temporal_v02.MANIFEST)
    schema_02 = temporal_v02.load(temporal_v02.SCHEMA)
    emitters_02 = temporal_v02.load(temporal_v02.EMITTERS)
    fixtures_02 = temporal_v02.load(temporal_v02.FIXTURES)
    traces_02 = temporal_v02.load(temporal_v02.TRACES)
    temporal_v02.verify_manifest(manifest_02)
    temporal_v02.verify_schema(schema_02, manifest_02)
    temporal_v02.verify_emitters(emitters_02, manifest_02, schema_02, fixtures_02)
    runtime = temporal_v02.verify_fixtures(fixtures_02, manifest_02, emitters_02)
    temporal_v02.verify_traces(traces_02, manifest_02, runtime)
    temporal_v02.verify_parent_error_probes(runtime)
    temporal_02_actual = {code for row in traces_02["records"] for code in row["observed_ordered_issues"]}

    emitted = set(parent_actual) | semantic_actual | temporal_01_actual | temporal_02_actual
    missing = [code for code in ordered if code not in emitted]
    if len(emitted) != 170 or missing != MISSING_CODES:
        fail(f"blocked v0.4 recomputed STOP boundary: {len(emitted)}:{missing}")
    evidence = {
        "accepted_entrypoints": {
            "parent": {"executed": parent_count, "unique_actual_codes": len(set(parent_actual))},
            "semantic": {"executed": semantic_run["count"], "unique_actual_codes": len(semantic_actual)},
            "temporal_v01": {"executed": len(challenges_01["cases"]), "unique_actual_codes": len(temporal_01_actual)},
            "temporal_v02": {"executed": len(traces_02["records"]), "unique_actual_codes": len(temporal_02_actual)},
        },
        "error_universe_count": 192,
        "pre_delta_emitted_union_count": 170,
        "missing_codes": missing,
    }
    return evidence, emitted, ordered, priorities, origins


def verify_static_independence() -> None:
    trees = [(path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path))) for path in (GENERATOR, VERIFIER)]
    for path, tree in trees:
        if any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
            fail(f"assert-only gate: {path.name}")
        imports = [alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names]
        if any("error_replay_coverage_delta_v0_1" in name for name in imports):
            fail("generator/verifier mutual import")
        behavior_functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and (
                node.name.endswith("_gate")
                or node.name in {"apply_primary", "apply_reseal", "mutate", "reseal"}
                or node.name.startswith("semantic_")
            )
        }
        for function_name, function_node in behavior_functions.items():
            for node in ast.walk(function_node):
                if function_name in {"identity_gate", "history_gate"} and isinstance(node, ast.Constant) and isinstance(node.value, str) and (node.value.startswith("PUB_IDENTITY_") or node.value.startswith("AEMH_WITHDRAW_REAPPEAR")):
                    fail(f"local append-only pseudo-code map: {path.name}:{function_name}")
                if isinstance(node, ast.If):
                    test = ast.unparse(node.test)
                    forbidden = ("case" + "_id", "error" + "_code", "senti" + "nel")
                    if any(token in test for token in forbidden):
                        fail(f"case/error/sentinel behavior branch: {path.name}:{function_name}:{test}")
    generator_tree = trees[0][1]
    for node in ast.walk(generator_tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "load_module" and node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str) and "error_replay_coverage_delta_v0_1" in first.value:
                fail("generator loads delta verifier expected plane")
    for _path, tree in trees:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                fail("dynamic local mirror import")


def verify_reseal_contract() -> None:
    declared = {handler for handlers in EXPECTED_RESEAL.values() for handler in handlers}
    if set(RESEAL_ENV_KEYS) != declared:
        fail("closed reseal/env-key handler set")
    parent_handlers = {name for name, keys in RESEAL_ENV_KEYS.items() if "parent" in keys}
    semantic_handlers = {name for name, keys in RESEAL_ENV_KEYS.items() if "semantic" in keys}
    if parent_handlers & semantic_handlers or parent_handlers | semantic_handlers != declared:
        fail("reseal branch authority partition")
    if any("semantic" in RESEAL_ENV_KEYS[name] for name in parent_handlers):
        fail("parent reseal accessed semantic")
    if any("parent" in RESEAL_ENV_KEYS[name] for name in semantic_handlers):
        fail("semantic reseal accessed parent")


def verify_negative_history_pins(manifest: dict[str, Any]) -> None:
    negative = manifest.get("rejected_v01_v02_negative_evidence_only")
    exact_keys = {"authority", "v0_1", "v0_2", "rejection_record_path", "rejection_record_raw_sha256"}
    if not isinstance(negative, dict) or set(negative) != exact_keys:
        fail("negative history exact keys")
    if negative["authority"] is not False:
        fail("negative history authority must be false")
    if negative["v0_1"] != NEGATIVE_V01_PINS:
        fail("negative history v0.1 frozen hard map")
    if negative["v0_2"] != NEGATIVE_V02_PINS:
        fail("negative history v0.2 frozen hard map")
    if (negative["rejection_record_path"], negative["rejection_record_raw_sha256"]) != NEGATIVE_V02_RECORD:
        fail("negative history rejection record path/hash")
    if manifest.get("rejected_v03_negative_evidence_only") != NEGATIVE_V03_PINS:
        fail("negative history v0.3 frozen hard map")
    for label, pins in (("v0.1", NEGATIVE_V01_PINS), ("v0.2", NEGATIVE_V02_PINS), ("v0.3", NEGATIVE_V03_PINS)):
        for relative, expected in pins.items():
            if not (ROOT / relative).is_file() or raw(ROOT / relative) != expected:
                fail(f"negative history {label} actual raw pin: {relative}")
    record_path, record_hash = NEGATIVE_V02_RECORD
    if not (ROOT / record_path).is_file() or raw(ROOT / record_path) != record_hash:
        fail("negative history rejection record actual raw pin")


def verify_manifest_and_pins(
    candidate: dict[str, Any] | None = None,
    duplicate_candidate: dict[str, Any] | None = None,
    accepted_temporal_raw: bytes | None = None,
) -> dict[str, Any]:
    pinned_temporal_manifest = load_pinned_temporal_v02(accepted_temporal_raw)
    manifest = load(OUT / "manifest.json") if candidate is None else candidate
    required = {
        "status": "candidate_unaccepted", "authority_scope": "synthetic_test_only",
        "pre_delta_executable_error_count": 170, "delta_challenge_count": 22, "post_union_error_count": 192,
        "new_error_code_count": 0, "renamed_error_code_count": 0, "reordered_error_code_count": 0,
        "clinical_truth_changed": False, "parent_bytes_changed": False, "semantic_bytes_changed": False,
        "temporal_bytes_changed": False, "implementation_v04_changed": False, "producer_executed": False,
        "port_8911_must_be_stopped": True, "self_acceptance": False,
    }
    if manifest.get("contract_id") != CONTRACT_ID or any(manifest.get(key) != value for key, value in required.items()):
        fail("manifest exact status/boundary")
    if set(manifest.get("exact_nine_paths", [])) != EXACT_PATHS or len(manifest.get("exact_nine_paths", [])) != 9:
        fail("manifest nine-path boundary")
    if manifest.get("manifest_content_hash") != digest({key: value for key, value in manifest.items() if key != "manifest_content_hash"}):
        fail("manifest content hash")
    verify_negative_history_pins(manifest)
    _ordered, priorities, _origins = priority_plane()
    if manifest.get("accepted_append_only_gate_bindings") != accepted_append_only_bindings(priorities):
        fail("accepted append-only manifest binding")
    expected_external = EXACT_PATHS - {"artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/manifest.json"}
    if set(manifest.get("file_raw_sha256", {})) != expected_external:
        fail("manifest eight external file pins")
    external_roots = dict(EXTERNAL_ROOT_PIN_ITEMS)
    if manifest.get("authority_chain_pins") != external_roots:
        fail("external authority root delta pin map")
    temporal_relative = (TEMPORAL_V02_DIR / "manifest.json").relative_to(ROOT).as_posix()
    if manifest.get("temporal_v02_nine_file_pins", {}).get(temporal_relative) != external_roots[temporal_relative]:
        fail("external authority root temporal nine-file pin")
    temporal_manifest = pinned_temporal_manifest if duplicate_candidate is None else duplicate_candidate
    temporal_protected = temporal_manifest.get("protected_accepted_pins")
    delta_protected = manifest.get("protected_accepted_pins")
    if not isinstance(temporal_protected, dict) or not isinstance(delta_protected, dict):
        fail("protected scalar binding shape")
    temporal_paths = temporal_protected.get("protected_path_sha256")
    delta_paths = delta_protected.get("protected_path_sha256")
    if not isinstance(temporal_paths, dict) or not isinstance(delta_paths, dict):
        fail("protected scalar path binding shape")
    for scalar, relative, expected in PROTECTED_SCALAR_BINDINGS:
        if raw(ROOT / relative) != expected:
            fail(f"protected scalar actual raw binding: {scalar}")
        if temporal_protected.get(scalar) != expected or temporal_paths.get(relative) != expected:
            fail(f"protected scalar accepted temporal binding: {scalar}")
        if delta_protected.get(scalar) != expected or delta_paths.get(relative) != expected:
            fail(f"protected scalar delta binding: {scalar}")
    if manifest["typed_source_pins"] != temporal_manifest["typed_source_pins"]:
        fail("duplicate typed-source pin disagreement")
    if manifest["protected_accepted_pins"] != temporal_manifest["protected_accepted_pins"]:
        fail("duplicate protected pin disagreement")
    pin_surfaces = [
        "file_raw_sha256", "authority_chain_pins", "temporal_v02_nine_file_pins", "typed_source_pins",
        "blocked_v04_nine_file_pins", "rejected_v03_negative_evidence_only",
    ]
    for surface in pin_surfaces:
        for relative, expected in manifest[surface].items():
            if not isinstance(expected, str) or len(expected) != 64 or raw(ROOT / relative) != expected:
                fail(f"pin drift: {surface}:{relative}")
    protected_paths = manifest["protected_accepted_pins"]["protected_path_sha256"]
    for relative, expected in protected_paths.items():
        if raw(ROOT / relative) != expected:
            fail(f"protected path drift: {relative}")
    if manifest.get("missing_error_codes") != MISSING_CODES:
        fail("manifest missing-code set")
    return manifest


def verify_schema_and_registries(manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    schema = load(OUT / "schema.json")
    bases = load(OUT / "base_input_registry.json")
    gates = load(OUT / "gate_registry.json")
    challenges = load(OUT / "challenge_registry.json")
    if schema.get("schema_version") != SCHEMA_VERSION or schema.get("authority_scope") != "synthetic_test_only":
        fail("delta schema identity")
    if set(bases) != {"schema", "schema_version", "rows"} or set(gates) != {"schema", "schema_version", "rows"} or set(challenges) != {"schema", "schema_version", "rows"}:
        fail("registry exact roots")
    if any(set(row) != BASE_KEYS for row in bases["rows"]) or any(set(row) != GATE_KEYS for row in gates["rows"]) or any(set(row) != CHALLENGE_KEYS for row in challenges["rows"]):
        fail("registry exact row keys")
    if manifest["base_input_registry_content_hash"] != digest(bases) or manifest["gate_registry_content_hash"] != digest(gates) or manifest["challenge_registry_content_hash"] != digest(challenges):
        fail("registry content pins")
    base_map = {row["base_input_ref"]: row for row in bases["rows"]}
    if set(base_map) != set(EXPECTED_BASES) or len(base_map) != len(bases["rows"]):
        fail("base registry identity set")
    for reference, (relative, pointer, constructor) in EXPECTED_BASES.items():
        row = base_map[reference]
        source = ROOT / relative
        value = get(load(source), pointer)
        raw_order = hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        if (row["accepted_source_path"], row["accepted_source_json_pointer"], row["constructor_id"]) != (relative, pointer, constructor):
            fail(f"base pointer/constructor: {reference}")
        if (row["accepted_source_raw_sha256"], row["raw_input_identity"], row["canonical_input_identity"]) != (raw(source), raw_order, digest(value)):
            fail(f"base identity: {reference}")
        if any(key in row for key in ("packet", "output", "issues", "expected")) or contains_forbidden_mirror(row["constructor_recipe"]):
            fail("base registry mirror plane")
    gate_map = {row["gate_id"]: row for row in gates["rows"]}
    _ordered, priorities, _origins = priority_plane()
    expected_codes = expected_gate_codes(priorities)
    append_bindings = accepted_append_only_bindings(priorities)
    if set(gate_map) != set(expected_codes) or len(gate_map) != len(gates["rows"]):
        fail("closed gate identity set")
    for gate_id, permitted in expected_codes.items():
        row = gate_map[gate_id]
        path = ROOT / row["accepted_source_path"]
        if set(row["permitted_error_codes"]) != permitted or row["accepted_source_raw_sha256"] != raw(path) or row["accepted_ast_normalized_sha256"] != function_ast_hash(path, row["accepted_ast_selector"]):
            fail(f"gate source/permit pin: {gate_id}")
    if gate_map["gate.parent.identity_dimension"]["algorithm_contract"].get("accepted_authority_binding") != append_bindings["subject_identity"]:
        fail("accepted subject invariant gate binding")
    if gate_map["gate.parent.aemh_history_preservation"]["algorithm_contract"].get("accepted_authority_binding") != append_bindings["aemh_history"]:
        fail("accepted AEMH invariant gate binding")
    return bases, gates, challenges


def build_runtime_bases() -> tuple[dict[str, Any], dict[str, Any]]:
    temporal = module("tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py", "independent_delta_constructor")
    fixtures = temporal.load(temporal.FIXTURES)
    recipes = temporal.load(temporal.EMITTERS)
    schema = temporal.load(temporal.SCHEMA)
    result: dict[str, Any] = {}
    for item in fixtures["baselines"]:
        authority = copy.deepcopy(item["authority_input"])
        target = authority["target_contract"]
        if temporal.authority_issues(authority, schema):
            fail(f"typed authority base invalid: {target}")
        built, _ = temporal.execute_independent_recipe_dag(authority, recipes)
        if target == SUBJECT:
            errors = temporal.validate_parent(target, built)
            result["base.parent.subject"] = built
        else:
            previous, current = built
            errors = [*temporal.validate_parent(target, previous), *temporal.validate_parent(target, current, previous)]
            result["base.parent.aemh"] = {"previous_packet": previous, "current_packet": current}
        if errors:
            fail(f"constructed base parent errors: {target}:{errors}")
    semantic_challenges = load(SEMANTIC_DIR / "challenge_registry.json")
    result["base.semantic.risk_high"] = copy.deepcopy(semantic_challenges["baselines"]["risk_high"])
    result["base.semantic.risk_authority"] = copy.deepcopy(semantic_challenges["baselines"]["risk_authority"])
    result["base.semantic.manifest"] = load(SEMANTIC_DIR / "manifest.json")
    result["base.governance.runtime"] = load(PARENT_DIR / "manifest.json")["no_runtime_test_surface"]
    return result, {"temporal": temporal}


def mutate(document: Any, operation: dict[str, Any]) -> None:
    kind = operation["op"]
    if kind == "create_temp_file":
        return
    container, key = parent_at(document, operation["path"])
    if kind == "replace":
        if isinstance(container, list):
            container[int(key)] = copy.deepcopy(operation["value"])
        else:
            container[key] = copy.deepcopy(operation["value"])
    elif kind == "add":
        container[key] = copy.deepcopy(operation["value"])
    elif kind == "remove":
        container.pop(int(key)) if isinstance(container, list) else container.pop(key)
    elif kind == "append_copy":
        get(document, operation["path"]).append(copy.deepcopy(get(document, operation["value_from"])))
    else:
        fail(f"unsupported mutation op: {kind}")


def patches(left: Any, right: Any, path: str = "") -> list[tuple[str, str]]:
    if type(left) is not type(right):
        return [("replace", path or "/")]
    if isinstance(left, dict):
        changes: list[tuple[str, str]] = []
        for key in sorted(set(left) | set(right)):
            child = f"{path}/{key}"
            if key not in left:
                changes.append(("add", child))
            elif key not in right:
                changes.append(("remove", child))
            else:
                changes.extend(patches(left[key], right[key], child))
        return changes
    if isinstance(left, list):
        if len(right) == len(left) + 1:
            for index in range(len(right)):
                if left == right[:index] + right[index + 1 :]:
                    return [("add", f"{path}/{index}")]
        if len(left) == len(right) + 1:
            for index in range(len(left)):
                if right == left[:index] + left[index + 1 :]:
                    return [("remove", f"{path}/{index}")]
        if len(left) != len(right):
            return [("replace", path or "/")]
        changes = []
        for index, (a, b) in enumerate(zip(left, right)):
            changes.extend(patches(a, b, f"{path}/{index}"))
        return changes
    return [] if left == right else [("replace", path or "/")]


def exact_reseal_env(name: str, env: dict[str, Any]) -> dict[str, Any]:
    if name not in RESEAL_ENV_KEYS:
        fail(f"unknown reseal handler: {name}")
    required = RESEAL_ENV_KEYS[name]
    missing = required - set(env)
    if missing:
        fail(f"reseal env missing keys: {name}:{sorted(missing)}")
    return {key: env[key] for key in required}


def reseal(document: Any, name: str, env: dict[str, Any]) -> None:
    if name not in RESEAL_ENV_KEYS:
        fail(f"unknown reseal handler: {name}")
    required = RESEAL_ENV_KEYS[name]
    missing = required - set(env)
    if missing:
        fail(f"reseal env missing keys: {name}:{sorted(missing)}")
    extra = set(env) - required
    if extra:
        fail(f"reseal env extra keys: {name}:{sorted(extra)}")
    if name == "reseal_visibility_receipt_packet":
        parent = env["parent"]
        subject_schema = env["subject_schema"]
        parent.reseal_exact_object("VisibilityClosure", document["receipt"]["visibility_closure"], subject_schema)
        parent.reseal_exact_object("PublicAuthorityReceipt", document["receipt"], subject_schema)
        document["packet_content_hash"] = parent.canonical_hash({"receipt_content_hash": document["receipt"]["receipt_content_hash"], "projection_content_hash": document["projection"]["projection_content_hash"]})
    elif name == "reseal_subject_projection_packet":
        parent = env["parent"]
        subject_schema = env["subject_schema"]
        parent.reseal_exact_object("SubjectTemporalPublicProjection", document["projection"], subject_schema)
        document["packet_content_hash"] = parent.canonical_hash({"receipt_content_hash": document["receipt"]["receipt_content_hash"], "projection_content_hash": document["projection"]["projection_content_hash"]})
    elif name == "reseal_receipt_scope_receipt_packet":
        parent = env["parent"]
        subject_schema = env["subject_schema"]
        parent.reseal_exact_object("PublicScopeIdentity", document["receipt"]["scope_identity"], subject_schema)
        parent.reseal_exact_object("PublicAuthorityReceipt", document["receipt"], subject_schema)
        document["packet_content_hash"] = parent.canonical_hash({"receipt_content_hash": document["receipt"]["receipt_content_hash"], "projection_content_hash": document["projection"]["projection_content_hash"]})
    elif name == "reseal_aemh_current_full":
        parent = env["parent"]
        parent.reseal_aemh_packet(document["current_packet"], env["aemh_schema"], preserve_evaluation=False)
    elif name == "reseal_taxonomy_package":
        semantic = env["semantic"]
        document["taxonomy_package"]["package_content_hash"] = semantic.object_hash(document["taxonomy_package"], "package_content_hash")
    elif name == "reseal_severity_package":
        semantic = env["semantic"]
        document["severity_package"]["package_content_hash"] = semantic.object_hash(document["severity_package"], "package_content_hash")
    elif name == "reseal_taxonomy_evidence":
        semantic = env["semantic"]
        document["taxonomy_evidence"]["evidence_content_hash"] = semantic.object_hash(document["taxonomy_evidence"], "evidence_content_hash")
    elif name == "reseal_taxonomy_receipt":
        semantic = env["semantic"]
        document["taxonomy_receipt"]["receipt_content_hash"] = semantic.object_hash(document["taxonomy_receipt"], "receipt_content_hash")
    elif name == "reseal_candidate_authority":
        semantic = env["semantic"]
        document["candidate_authority"]["authority_content_hash"] = semantic.object_hash(document["candidate_authority"], "authority_content_hash")


def parser_gate(candidate: Any, row: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    selector = row["instance_selector"]
    found: list[str] = []
    env["parent"].validate_exact_object(selector["object_type"], get(candidate, selector["json_pointer"]), env["subject_schema"], selector["json_pointer"], found)
    return [(item, row["single_mutation"]["path"]) for item in found]


def collect_identity_values(value: Any, dimension: str, path: str = "") -> list[tuple[str, Any]]:
    stem = dimension.removesuffix("_ref")
    rows: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}/{key}"
            if key == dimension and not child.startswith("/receipt/scope_identity") and not child.startswith("/projection/scope_identity"):
                rows.append((child, item))
            elif key.endswith(f"{stem}_refs") and isinstance(item, list):
                rows.extend((f"{child}/{index}", member) for index, member in enumerate(item))
            rows.extend(collect_identity_values(item, dimension, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            rows.extend(collect_identity_values(item, dimension, f"{path}/{index}"))
    return rows


def identity_gate(candidate: Any, row: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    dimension = row["instance_selector"]["dimension"]
    bindings = {item["dimension"]: item for item in env["append_only_bindings"]["subject_identity"]["dimension_bindings"]}
    if dimension not in bindings:
        fail(f"identity selector outside accepted invariant: {dimension}")
    receipt_value = candidate["receipt"]["scope_identity"][dimension]
    projection_value = candidate["projection"]["scope_identity"][dimension]
    visibility = candidate["receipt"]["visibility_closure"]
    visibility_values = collect_identity_values(visibility, dimension, "/receipt/visibility_closure")
    if dimension == "snapshot_ref" and receipt_value not in visibility["visibility_decision_id"]:
        visibility_values.append(("/receipt/visibility_closure/visibility_decision_id", visibility["visibility_decision_id"]))
    member_values = collect_identity_values(candidate["projection"], dimension, "/projection")
    observed = [("/receipt/scope_identity", receipt_value), ("/projection/scope_identity", projection_value), *visibility_values, *member_values]
    mismatch = any(value != receipt_value for _path, value in observed[1:])
    return [(bindings[dimension]["error_code"], row["single_mutation"]["path"])] if mismatch else []


def visibility_gate(candidate: Any, row: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    found: list[str] = []
    env["parent"].validate_visibility_and_sources(candidate["receipt"], candidate["projection"], found)
    return [(item, row["single_mutation"]["path"]) for item in found]


def governance_gate(candidate: Any, row: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    relative = row["single_mutation"]["path"]
    with tempfile.TemporaryDirectory(prefix="independent-error-replay-") as temporary:
        target = pathlib.Path(temporary) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(row["single_mutation"]["value"], encoding="utf-8")
        env["actual_governance_actions"] += 1
        matched = relative in set(candidate["forbidden_exact_paths"]) or any(re.fullmatch(pattern, relative) for pattern in candidate["forbidden_relative_path_regexes"])
        return [("PUB_RUNTIME_TEST_SURFACE_FORBIDDEN", relative)] if target.is_file() and matched else []


def history_gate(candidate: Any, row: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    baseline = env["before"]["current_packet"]
    current = candidate["current_packet"]
    binding = env["append_only_bindings"]["aemh_history"]
    selector = row["instance_selector"]
    thread_ref = selector["thread_ref"]
    old = {item["thread_ref"]: item for item in baseline["projection"]["threads"]}
    new = {item["thread_ref"]: item for item in current["projection"]["threads"]}
    eligible = [ref for ref, thread in old.items() if set(binding["event_kinds"]) <= {entry["event_kind"] for entry in thread["history_entries"]}]
    if len(eligible) != 1 or thread_ref != eligible[0] or selector.get("event_kind") not in binding["event_kinds"]:
        fail("history selector outside accepted invariant/base binding")
    if thread_ref not in old or thread_ref not in new:
        return [(binding["error_code"], "/current_packet/projection/threads")]
    if any(old[thread_ref][field] != new[thread_ref][field] for field in binding["stable_thread_fields"]):
        return [(binding["error_code"], "/current_packet/projection/threads")]
    required = [item for item in old[thread_ref]["history_entries"] if item["event_kind"] in binding["event_kinds"]]
    if {item["event_kind"] for item in required} != set(binding["event_kinds"]):
        fail("accepted base does not close the bound history event set")
    available = new[thread_ref]["history_entries"]
    position = 0
    for expected in required:
        while position < len(available) and canon(available[position]) != canon(expected):
            position += 1
        if position >= len(available):
            return [(binding["error_code"], "/current_packet/projection/threads/0/history_entries")]
        position += 1
    return []


def semantic_common(candidate: Any, row: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    try:
        env["semantic"].validate_common_package(get(candidate, row["instance_selector"]["json_pointer"]), env["semantic"].RISK_PACKAGE_KEYS, "/taxonomy_package")
    except env["semantic"].SemanticError as exc:
        return [(exc.code, exc.path)]
    return []


def semantic_package(candidate: Any, row: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    call_by_gate = {"gate.semantic.risk_validator": env["semantic"].validate_risk_package, "gate.semantic.severity_validator": env["semantic"].validate_severity_package}
    try:
        call_by_gate[row["gate_id"]](get(candidate, row["instance_selector"]["json_pointer"]))
    except env["semantic"].SemanticError as exc:
        return [(exc.code, exc.path)]
    return []


def semantic_evidence(candidate: Any, _row: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    try:
        env["semantic"].validate_token_evidence(candidate["taxonomy_evidence"], env["source_registry"], env["source_records"], candidate["identity_join"], "/taxonomy_evidence")
    except env["semantic"].SemanticError as exc:
        return [(exc.code, exc.path)]
    return []


def semantic_receipt(candidate: Any, row: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    selector = row["instance_selector"]
    try:
        env["semantic"].validate_receipt(candidate[selector["receipt_key"]], candidate[selector["package_key"]], selector["package_kind"], candidate["use_context"], env["acceptance_registry"], env["accepted_records"], "/" + selector["receipt_key"])
    except env["semantic"].SemanticError as exc:
        return [(exc.code, exc.path)]
    return []


def semantic_candidate(candidate: Any, row: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    selector = row["instance_selector"]
    expected = env["semantic"].evaluate_risk(candidate[selector["source_key"]], env["source_registry"], env["source_records"], env["acceptance_registry"], env["accepted_records"])
    proposed = candidate[selector["candidate_key"]]
    try:
        env["semantic"].exact_keys(proposed, env["semantic"].RISK_AUTHORITY_KEYS, "/candidate_authority")
        env["semantic"].require_hash(proposed, "authority_content_hash", "SEM_AUTHORITY_HASH_MISMATCH", "/candidate_authority")
        if proposed != expected:
            raise env["semantic"].SemanticError("SEM_AUTHORITY_MISMATCH", "/candidate_authority")
    except env["semantic"].SemanticError as exc:
        return [(exc.code, exc.path)]
    return []


def semantic_manifest(candidate: Any, _row: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    try:
        env["semantic"].validate_parent_and_manifest(candidate)
    except env["semantic"].SemanticError as exc:
        return [(exc.code, exc.path)]
    return []


DISPATCH: dict[str, Callable[[Any, dict[str, Any], dict[str, Any]], list[tuple[str, str]]]] = {
    "gate.parent.untrusted_exact_parser": parser_gate,
    "gate.parent.identity_dimension": identity_gate,
    "gate.parent.visibility_source": visibility_gate,
    "gate.parent.runtime_surface": governance_gate,
    "gate.parent.aemh_history_preservation": history_gate,
    "gate.semantic.common_parser": semantic_common,
    "gate.semantic.risk_validator": semantic_package,
    "gate.semantic.severity_validator": semantic_package,
    "gate.semantic.token_evidence": semantic_evidence,
    "gate.semantic.receipt": semantic_receipt,
    "gate.semantic.candidate_comparison": semantic_candidate,
    "gate.semantic.manifest": semantic_manifest,
}


def expected_trace(row: dict[str, Any]) -> str:
    return digest({
        "base_input_content_identity": row["base_input_content_identity"],
        "gate_id": row["gate_id"],
        "instance_selector": row["instance_selector"],
        "single_mutation": row["single_mutation"],
        "ordered_reseal": row["ordered_reseal"],
    })


def verify_challenges(bases_artifact: dict[str, Any], gates_artifact: dict[str, Any], challenges: dict[str, Any], priorities: dict[str, int], origins: dict[str, str]) -> tuple[set[str], dict[str, Any]]:
    expected_codes = expected_gate_codes(priorities)
    append_bindings = accepted_append_only_bindings(priorities)
    if set(bases_artifact) != {"schema", "schema_version", "rows"} or any(set(item) != BASE_KEYS for item in bases_artifact.get("rows", [])):
        fail("attack base registry shape")
    if any(contains_forbidden_mirror(item["constructor_recipe"]) for item in bases_artifact["rows"]):
        fail("attack local base mirror oracle")
    if set(gates_artifact) != {"schema", "schema_version", "rows"} or any(set(item) != GATE_KEYS for item in gates_artifact.get("rows", [])):
        fail("attack gate registry shape")
    if set(challenges) != {"schema", "schema_version", "rows"} or any(set(item) != CHALLENGE_KEYS for item in challenges.get("rows", [])):
        fail("attack challenge registry shape")
    base_rows = {item["base_input_ref"]: item for item in bases_artifact["rows"]}
    gate_rows = {item["gate_id"]: item for item in gates_artifact["rows"]}
    if set(base_rows) != set(EXPECTED_BASES) or len(base_rows) != len(bases_artifact["rows"]):
        fail("attack base identity set")
    if set(gate_rows) != set(expected_codes) or len(gate_rows) != len(gates_artifact["rows"]):
        fail("attack closed gate identity set")
    for gate_id, permitted_codes in expected_codes.items():
        if set(gate_rows[gate_id]["permitted_error_codes"]) != permitted_codes:
            fail(f"attack gate permitted-code drift: {gate_id}")
    identity_contract = gate_rows["gate.parent.identity_dimension"].get("algorithm_contract")
    history_contract = gate_rows["gate.parent.aemh_history_preservation"].get("algorithm_contract")
    if not isinstance(identity_contract, dict) or identity_contract.get("accepted_authority_binding") != append_bindings["subject_identity"]:
        fail("attack accepted subject invariant binding")
    if not isinstance(history_contract, dict) or history_contract.get("accepted_authority_binding") != append_bindings["aemh_history"]:
        fail("attack accepted AEMH invariant binding")
    runtime, _ = build_runtime_bases()
    parent = module("tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py", "independent_delta_parent_gate")
    semantic = module("tools/verify_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py", "independent_delta_semantic_gate")
    semantic_manifest_value = load(SEMANTIC_DIR / "manifest.json")
    sr = semantic_manifest_value["synthetic_typed_source_record_registry"]
    ar = semantic_manifest_value["synthetic_policy_acceptance_registry"]
    env = {
        "parent": parent, "semantic": semantic,
        "subject_schema": load(PARENT_DIR / "subject_temporal_schema.json"),
        "aemh_schema": load(PARENT_DIR / "aemh_match_history_schema.json"),
        "source_registry": sr, "acceptance_registry": ar,
        "source_records": semantic.validate_source_registry(sr), "accepted_records": semantic.validate_acceptance_registry(ar),
        "actual_governance_actions": 0,
        "append_only_bindings": append_bindings,
    }
    rows = challenges["rows"]
    if len(rows) != 22 or len({item["case_id"] for item in rows}) != 22 or len({item["trace_identity"] for item in rows}) != 22:
        fail("challenge cardinality/identity")
    if {item["error_code"] for item in rows} != set(MISSING_CODES):
        fail("exact 22 missing-code set")
    actual_codes: set[str] = set()
    used_gates: dict[str, int] = {gate: 0 for gate in DISPATCH}
    reseal_patch_count = 0
    for row in rows:
        if row["base_input_ref"] not in runtime or row["base_input_ref"] not in base_rows or row["gate_id"] not in gate_rows:
            fail("challenge closed reference")
        mutation_path = row["single_mutation"]["path"]
        mutation_keys = {
            "replace": {"op", "path", "value"},
            "add": {"op", "path", "value"},
            "remove": {"op", "path"},
            "append_copy": {"op", "path", "value_from"},
            "create_temp_file": {"op", "path", "value"},
        }
        operation = row["single_mutation"].get("op")
        if operation not in mutation_keys or set(row["single_mutation"]) != mutation_keys[operation]:
            fail(f"single-mutation exact shape: {row['case_id']}")
        expected_reseal = EXPECTED_RESEAL.get((row["gate_id"], mutation_path))
        if expected_reseal is None or row["ordered_reseal"] != expected_reseal:
            fail(f"stale/excess/wrong reseal: {row['gate_id']}:{mutation_path}")
        base_row = base_rows[row["base_input_ref"]]
        if row["base_input_content_identity"] != base_row["canonical_input_identity"] or row["constructor_id"] != base_row["constructor_id"]:
            fail("challenge base/constructor binding")
        if row["entrypoint_class"] != gate_rows[row["gate_id"]]["entrypoint_class"]:
            fail("challenge gate class binding")
        candidate = copy.deepcopy(runtime[row["base_input_ref"]])
        before = copy.deepcopy(candidate)
        mutate(candidate, row["single_mutation"])
        primary = [("create_temp_file", mutation_path)] if row["single_mutation"]["op"] == "create_temp_file" else patches(before, candidate)
        if len(primary) != 1:
            fail(f"multi-mutation smuggling: {row['gate_id']}:{primary}")
        after_primary = copy.deepcopy(candidate)
        for handler in row["ordered_reseal"]:
            reseal(candidate, handler, exact_reseal_env(handler, env))
        dependent = patches(after_primary, candidate)
        if row["ordered_reseal"] and not dependent:
            fail(f"stale reseal handler: {row['gate_id']}:{mutation_path}")
        reseal_patch_count += len(dependent)
        env["before"] = before
        actual = DISPATCH[row["gate_id"]](candidate, row, env)
        used_gates[row["gate_id"]] += 1
        if len(actual) != 1:
            fail(f"actual gate issue cardinality: {row['gate_id']}:{actual}")
        code, issue_path = actual[0]
        if code not in expected_codes[row["gate_id"]] or code not in gate_rows[row["gate_id"]]["permitted_error_codes"]:
            fail(f"gate overreach/substitution: {row['gate_id']}:{code}")
        actual_issue = {"code": code, "path": issue_path, "message": f"{origins[code]}:{code}:fail_closed", "origin": origins[code], "priority": priorities[code]}
        if row["error_code"] != code or row["accepted_priority"] != priorities[code] or row["observed_ordered_issues"] != [actual_issue]:
            fail(f"expected/priority/observation poisoning: {row['gate_id']}:{mutation_path}")
        if row["trace_identity"] != expected_trace(row):
            fail("trace identity poisoning")
        actual_codes.add(code)
    if any(count == 0 for count in used_gates.values()) or env["actual_governance_actions"] != 1:
        fail("dead-code replay or fake governance")
    if actual_codes != set(MISSING_CODES):
        fail("22 actual gate codes")
    return actual_codes, {"gate_execution_counts": used_gates, "governance_actions": env["actual_governance_actions"], "reseal_patch_count": reseal_patch_count}


def active_attack_checks(
    bases: dict[str, Any],
    gates: dict[str, Any],
    challenges: dict[str, Any],
    manifest: dict[str, Any],
    priorities: dict[str, int],
    origins: dict[str, str],
) -> int:
    count = 0

    def rejected(action: Callable[[], Any], label: str, expected: str | None = None) -> None:
        nonlocal count
        try:
            action()
        except SystemExit as exc:
            if not str(exc).startswith("STOP "):
                fail(f"non-fail-closed attack result: {label}:{exc}")
            if expected is not None and expected not in str(exc):
                fail(f"wrong fail-closed gate for attack: {label}:{exc}")
        else:
            fail(f"attack survived real verifier: {label}")
        count += 1

    def challenge_attack(label: str, index: int, mutate_row: Callable[[dict[str, Any]], None]) -> None:
        candidate = copy.deepcopy(challenges)
        mutate_row(candidate["rows"][index])
        rejected(lambda: verify_challenges(bases, gates, candidate, priorities, origins), label)

    def manifest_attack(
        label: str,
        mutate_manifest: Callable[[dict[str, Any]], None],
        expected: str,
        mutate_duplicate: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        candidate = copy.deepcopy(manifest)
        mutate_manifest(candidate)
        candidate["manifest_content_hash"] = digest({key: value for key, value in candidate.items() if key != "manifest_content_hash"})
        if mutate_duplicate is None:
            rejected(lambda: verify_manifest_and_pins(candidate), label, expected)
            return
        duplicate_candidate = load(TEMPORAL_V02_DIR / "manifest.json")
        mutate_duplicate(duplicate_candidate)
        duplicate_candidate["manifest_content_hash"] = digest(
            {key: value for key, value in duplicate_candidate.items() if key != "manifest_content_hash"}
        )
        rejected(lambda: verify_manifest_and_pins(candidate, duplicate_candidate), label, expected)

    def coordinated_protected_attack(scalar: str, relative: str) -> None:
        temporal_candidate = load(TEMPORAL_V02_DIR / "manifest.json")
        temporal_protected = temporal_candidate["protected_accepted_pins"]
        temporal_protected[scalar] = "0" * 64
        temporal_protected["protected_path_sha256"][relative] = "0" * 64
        temporal_candidate["manifest_content_hash"] = digest(
            {key: value for key, value in temporal_candidate.items() if key != "manifest_content_hash"}
        )
        temporal_raw = pretty_json(temporal_candidate)
        temporal_raw_sha256 = hashlib.sha256(temporal_raw).hexdigest()
        temporal_relative = (TEMPORAL_V02_DIR / "manifest.json").relative_to(ROOT).as_posix()
        candidate = copy.deepcopy(manifest)
        candidate["protected_accepted_pins"] = copy.deepcopy(temporal_protected)
        candidate["authority_chain_pins"][temporal_relative] = temporal_raw_sha256
        candidate["temporal_v02_nine_file_pins"][temporal_relative] = temporal_raw_sha256
        candidate["manifest_content_hash"] = digest(
            {key: value for key, value in candidate.items() if key != "manifest_content_hash"}
        )
        rejected(
            lambda: verify_manifest_and_pins(candidate, accepted_temporal_raw=temporal_raw),
            f"coordinated_protected_scalar_reseal_{scalar}",
            "external authority root raw pin: temporal v0.2 manifest",
        )

    for label, index, mutate_row in (
        ("expected_poison", 0, lambda item: item.__setitem__("error_code", "PUB_ENUM_UNKNOWN")),
        ("priority_drift", 0, lambda item: item.__setitem__("accepted_priority", 999)),
        ("observation_poison", 0, lambda item: item["observed_ordered_issues"].clear()),
        ("gate_substitution", 0, lambda item: item.__setitem__("gate_id", "gate.parent.identity_dimension")),
        ("parser_normalization", 1, lambda item: item["single_mutation"].__setitem__("value", True)),
        ("multi_mutation", 0, lambda item: item["single_mutation"].__setitem__("second_path", "/forbidden")),
        ("excess_reseal", 0, lambda item: item["ordered_reseal"].append("reseal_candidate_authority")),
        ("trace_alias", 0, lambda item: item.__setitem__("trace_identity", challenges["rows"][1]["trace_identity"])),
    ):
        challenge_attack(label, index, mutate_row)

    case_candidate = copy.deepcopy(challenges)
    case_candidate["rows"][0]["case_id"] = "POISONED_CASE_LABEL"
    case_codes, _ = verify_challenges(bases, gates, case_candidate, priorities, origins)
    if case_codes != set(MISSING_CODES):
        fail("case label changed real gate output")
    count += 1

    stale_index = next(index for index, item in enumerate(challenges["rows"]) if item["ordered_reseal"])
    challenge_attack("stale_reseal", stale_index, lambda item: item["ordered_reseal"].clear())

    base_candidate = copy.deepcopy(bases)
    base_candidate["rows"][0]["constructor_recipe"]["packet_mirror"] = {}
    rejected(lambda: verify_challenges(base_candidate, gates, challenges, priorities, origins), "local_mirror_oracle")
    gate_candidate = copy.deepcopy(gates)
    gate_candidate["rows"].append(copy.deepcopy(gate_candidate["rows"][0]))
    rejected(lambda: verify_challenges(bases, gate_candidate, challenges, priorities, origins), "dead_gate")
    gate_candidate = copy.deepcopy(gates)
    gate_candidate["rows"][1]["permitted_error_codes"].append("PUB_IDENTITY_SUBJECT_MISMATCH")
    rejected(lambda: verify_challenges(bases, gate_candidate, challenges, priorities, origins), "identity_overreach")
    gate_candidate = copy.deepcopy(gates)
    gate_candidate["rows"][4]["permitted_error_codes"].append("AEMH_PREFIX_HASH_MISMATCH")
    rejected(lambda: verify_challenges(bases, gate_candidate, challenges, priorities, origins), "history_overreach")
    gate_candidate = copy.deepcopy(gates)
    identity_row = next(item for item in gate_candidate["rows"] if item["gate_id"] == "gate.parent.identity_dimension")
    del identity_row["algorithm_contract"]["accepted_authority_binding"]["invariant"]
    rejected(lambda: verify_challenges(bases, gate_candidate, challenges, priorities, origins), "identity_invariant_binding_deleted", "accepted subject invariant binding")
    gate_candidate = copy.deepcopy(gates)
    identity_row = next(item for item in gate_candidate["rows"] if item["gate_id"] == "gate.parent.identity_dimension")
    identity_row["algorithm_contract"]["accepted_authority_binding"]["invariant"]["json_pointer"] = "/invariants/0"
    rejected(lambda: verify_challenges(bases, gate_candidate, challenges, priorities, origins), "identity_invariant_selector_changed", "accepted subject invariant binding")
    gate_candidate = copy.deepcopy(gates)
    identity_row = next(item for item in gate_candidate["rows"] if item["gate_id"] == "gate.parent.identity_dimension")
    identity_row["algorithm_contract"]["accepted_authority_binding"]["dimension_bindings"][0]["error_code"] = "PUB_IDENTITY_SUBJECT_MISMATCH"
    identity_row["permitted_error_codes"][0] = "PUB_IDENTITY_SUBJECT_MISMATCH"
    rejected(lambda: verify_challenges(bases, gate_candidate, challenges, priorities, origins), "identity_local_pseudo_code_map", "gate permitted-code drift")
    accepted_aemh = load(ROOT / AEMH_SCHEMA_REL)
    wrong_pointer = "/invariants/13"
    wrong_value = get(accepted_aemh, wrong_pointer)
    wrong_invariant = {
        "invariant_id": f"{accepted_aemh['schema']}#{wrong_pointer}",
        "ordinal": 13,
        "json_pointer": wrong_pointer,
        "value": wrong_value,
        "normalized_content_hash": digest(wrong_value),
    }
    gate_candidate = copy.deepcopy(gates)
    history_row = next(item for item in gate_candidate["rows"] if item["gate_id"] == "gate.parent.aemh_history_preservation")
    selected = history_row["algorithm_contract"]["accepted_authority_binding"]["history_invariant"]
    history_row["algorithm_contract"]["accepted_authority_binding"]["history_invariant"] = [selected, wrong_invariant]
    rejected(lambda: verify_challenges(bases, gate_candidate, challenges, priorities, origins), "history_selector_12_plus_13", "accepted AEMH invariant binding")
    gate_candidate = copy.deepcopy(gates)
    history_row = next(item for item in gate_candidate["rows"] if item["gate_id"] == "gate.parent.aemh_history_preservation")
    history_row["algorithm_contract"]["accepted_authority_binding"]["history_invariant"] = wrong_invariant
    rejected(lambda: verify_challenges(bases, gate_candidate, challenges, priorities, origins), "history_selector_only_13", "accepted AEMH invariant binding")
    for label, key, replacement in (
        ("history_selector_ordinal", "ordinal", 13),
        ("history_selector_id", "invariant_id", "poison#invariants/12"),
        ("history_selector_hash", "normalized_content_hash", "0" * 64),
    ):
        gate_candidate = copy.deepcopy(gates)
        history_row = next(item for item in gate_candidate["rows"] if item["gate_id"] == "gate.parent.aemh_history_preservation")
        history_row["algorithm_contract"]["accepted_authority_binding"]["history_invariant"][key] = replacement
        rejected(lambda gate_candidate=gate_candidate: verify_challenges(bases, gate_candidate, challenges, priorities, origins), label, "accepted AEMH invariant binding")
    gate_candidate = copy.deepcopy(gates)
    history_row = next(item for item in gate_candidate["rows"] if item["gate_id"] == "gate.parent.aemh_history_preservation")
    history_row["algorithm_contract"]["accepted_authority_binding"]["error_code"] = "AEMH_PREFIX_HASH_MISMATCH"
    history_row["permitted_error_codes"] = ["AEMH_PREFIX_HASH_MISMATCH"]
    rejected(lambda: verify_challenges(bases, gate_candidate, challenges, priorities, origins), "history_local_pseudo_code_map", "gate permitted-code drift")
    candidate_index = next(index for index, item in enumerate(challenges["rows"]) if item["gate_id"] == "gate.semantic.candidate_comparison" and item["error_code"] == "SEM_AUTHORITY_MISMATCH")
    challenge_attack("candidate_self_equality", candidate_index, lambda item: item["single_mutation"].__setitem__("source_mutation", "/source_input"))
    governance_index = next(index for index, item in enumerate(challenges["rows"]) if item["gate_id"] == "gate.parent.runtime_surface")
    challenge_attack("fake_governance", governance_index, lambda item: item["single_mutation"].__setitem__("path", "declaration-only"))
    history_index = next(index for index, item in enumerate(challenges["rows"]) if item["gate_id"] == "gate.parent.aemh_history_preservation")
    challenge_attack("history_selector_outside_invariant", history_index, lambda item: item["instance_selector"].__setitem__("event_kind", "match_decided"))

    runtime, _runtime_env = build_runtime_bases()
    parent = module(PARENT_VERIFIER_REL, "active_append_only_attack_parent")
    append_bindings = accepted_append_only_bindings(priorities)
    direct_env = {
        "parent": parent,
        "subject_schema": load(ROOT / SUBJECT_SCHEMA_REL),
        "aemh_schema": load(ROOT / AEMH_SCHEMA_REL),
        "append_only_bindings": append_bindings,
    }
    parent_positive = copy.deepcopy(runtime["base.parent.subject"])
    parent_minimal_env = {"parent": parent, "subject_schema": direct_env["subject_schema"]}
    reseal(parent_positive, "reseal_receipt_scope_receipt_packet", parent_minimal_env)
    count += 1
    semantic = module("tools/verify_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py", "active_reseal_semantic")
    semantic_positive = copy.deepcopy(runtime["base.semantic.risk_high"])
    reseal(semantic_positive, "reseal_taxonomy_package", {"semantic": semantic})
    count += 1
    rejected(lambda: reseal(copy.deepcopy(parent_positive), "reseal_receipt_scope_receipt_packet", {**parent_minimal_env, "semantic": semantic}), "parent_reseal_cross_branch_extra", "reseal env extra keys")
    rejected(lambda: reseal(copy.deepcopy(parent_positive), "reseal_receipt_scope_receipt_packet", {"subject_schema": direct_env["subject_schema"]}), "parent_reseal_missing_key", "reseal env missing keys")
    rejected(lambda: reseal(copy.deepcopy(semantic_positive), "reseal_taxonomy_package", {"semantic": semantic, "parent": parent}), "semantic_reseal_cross_branch_extra", "reseal env extra keys")
    rejected(lambda: reseal(copy.deepcopy(semantic_positive), "reseal_taxonomy_package", {}), "semantic_reseal_missing_key", "reseal env missing keys")
    rejected(lambda: reseal(copy.deepcopy(parent_positive), "reseal_unknown", {}), "unknown_reseal_id", "unknown reseal handler")
    identity_row = copy.deepcopy(next(item for item in challenges["rows"] if item["error_code"] == next(binding["error_code"] for binding in append_bindings["subject_identity"]["dimension_bindings"] if binding["dimension"] == "snapshot_ref")))
    identity_candidate = copy.deepcopy(runtime["base.parent.subject"])
    mutate(identity_candidate, identity_row["single_mutation"])
    reseal(identity_candidate, "reseal_receipt_scope_receipt_packet", exact_reseal_env("reseal_receipt_scope_receipt_packet", direct_env))
    identity_candidate["projection"]["scope_identity"]["snapshot_ref"] = identity_candidate["receipt"]["scope_identity"]["snapshot_ref"]
    parent.reseal_exact_object("PublicScopeIdentity", identity_candidate["projection"]["scope_identity"], direct_env["subject_schema"])
    parent.reseal_exact_object("SubjectTemporalPublicProjection", identity_candidate["projection"], direct_env["subject_schema"])
    identity_candidate["packet_content_hash"] = parent.canonical_hash({"receipt_content_hash": identity_candidate["receipt"]["receipt_content_hash"], "projection_content_hash": identity_candidate["projection"]["projection_content_hash"]})
    identity_actual = identity_gate(identity_candidate, identity_row, direct_env)
    identity_expected = next(binding["error_code"] for binding in append_bindings["subject_identity"]["dimension_bindings"] if binding["dimension"] == "snapshot_ref")
    if identity_actual != [(identity_expected, identity_row["single_mutation"]["path"])]:
        fail(f"fully resealed four-plane identity attack survived: {identity_actual}")
    count += 1

    history_row = copy.deepcopy(challenges["rows"][history_index])
    history_candidate = copy.deepcopy(runtime["base.parent.aemh"])
    history_before = copy.deepcopy(history_candidate)
    history_binding = append_bindings["aemh_history"]
    thread = next(item for item in history_candidate["current_packet"]["projection"]["threads"] if item["thread_ref"] == history_row["instance_selector"]["thread_ref"])
    remove_index = next(index for index, entry in enumerate(thread["history_entries"]) if entry["event_kind"] == history_binding["event_kinds"][0])
    thread["history_entries"].pop(remove_index)
    parent.reseal_aemh_packet(history_candidate["current_packet"], direct_env["aemh_schema"], preserve_evaluation=False)
    direct_env["before"] = history_before
    history_row["instance_selector"]["event_kind"] = history_binding["event_kinds"][0]
    history_actual = history_gate(history_candidate, history_row, direct_env)
    if history_actual != [(history_binding["error_code"], "/current_packet/projection/threads/0/history_entries")]:
        fail(f"fully resealed single-event history attack survived: {history_actual}")
    count += 1

    for surface in ("file_raw_sha256", "temporal_v02_nine_file_pins", "blocked_v04_nine_file_pins"):
        key = next(iter(manifest[surface]))
        manifest_attack(f"{surface}_drift", lambda item, surface=surface, key=key: item[surface].__setitem__(key, "0" * 64), "pin drift")
    authority_key = next(iter(manifest["authority_chain_pins"]))
    manifest_attack(
        "authority_chain_pins_drift",
        lambda item: item["authority_chain_pins"].__setitem__(authority_key, "0" * 64),
        "external authority root delta pin map",
    )
    typed_key = next(iter(manifest["typed_source_pins"]))
    manifest_attack(
        "typed_source_pins_drift",
        lambda item: item["typed_source_pins"].__setitem__(typed_key, "0" * 64),
        "duplicate typed-source pin disagreement",
    )
    manifest_attack(
        "typed_source_unique_synced_duplicate_actual_sha_drift",
        lambda item: item["typed_source_pins"].__setitem__(typed_key, "0" * 64),
        "pin drift: typed_source_pins:",
        lambda item: item["typed_source_pins"].__setitem__(typed_key, "0" * 64),
    )
    manifest_attack(
        "typed_source_duplicate_only_disagreement",
        lambda _item: None,
        "duplicate typed-source pin disagreement",
        lambda item: item["typed_source_pins"].__setitem__(typed_key, "0" * 64),
    )
    for scalar, relative, _expected in PROTECTED_SCALAR_BINDINGS:
        manifest_attack(
            f"protected_scalar_delta_only_{scalar}",
            lambda item, scalar=scalar: item["protected_accepted_pins"].__setitem__(scalar, "0" * 64),
            f"protected scalar delta binding: {scalar}",
        )
        coordinated_protected_attack(scalar, relative)
    for revision, hard_map in (("v0_1", NEGATIVE_V01_PINS), ("v0_2", NEGATIVE_V02_PINS)):
        for key in hard_map:
            manifest_attack(
                f"negative_{revision}_{key}",
                lambda item, revision=revision, key=key: item["rejected_v01_v02_negative_evidence_only"][revision].__setitem__(key, "0" * 64),
                f"negative history {revision.replace('_', '.')} frozen hard map",
            )
    manifest_attack("negative_exact_keys", lambda item: item["rejected_v01_v02_negative_evidence_only"].__setitem__("unexpected", None), "negative history exact keys")
    manifest_attack("negative_authority", lambda item: item["rejected_v01_v02_negative_evidence_only"].__setitem__("authority", True), "negative history authority must be false")
    manifest_attack("negative_record_path", lambda item: item["rejected_v01_v02_negative_evidence_only"].__setitem__("rejection_record_path", "context/poison.md"), "negative history rejection record path/hash")
    manifest_attack("negative_record_hash", lambda item: item["rejected_v01_v02_negative_evidence_only"].__setitem__("rejection_record_raw_sha256", "0" * 64), "negative history rejection record path/hash")
    for key in NEGATIVE_V03_PINS:
        manifest_attack("negative_v0_3_" + key, lambda item, key=key: item["rejected_v03_negative_evidence_only"].__setitem__(key, "0" * 64), "negative history v0.3 frozen hard map")
    manifest_attack("protected_accepted_pin_drift", lambda item: item["protected_accepted_pins"].__setitem__("medical_writing_protected_inventory_sha256", "0" * 64), "duplicate protected pin disagreement")
    manifest_attack("duplicate_typed_pin_disagreement", lambda item: item.__setitem__("typed_source_pins", copy.deepcopy(item["authority_chain_pins"])), "duplicate typed-source pin disagreement")
    manifest_attack("duplicate_protected_pin_disagreement", lambda item: item["protected_accepted_pins"].__setitem__("protected_path_sha256", {}), "protected scalar delta binding")
    manifest_attack("append_only_manifest_binding_drift", lambda item: item["accepted_append_only_gate_bindings"]["subject_identity"]["invariant"].__setitem__("json_pointer", "/invariants/0"), "accepted append-only manifest binding")
    for key, replacement in (
        ("exact_nine_paths", []), ("missing_error_codes", []), ("producer_executed", True),
        ("implementation_v04_changed", True), ("port_8911_must_be_stopped", False),
    ):
        manifest_attack(key, lambda item, key=key, replacement=replacement: item.__setitem__(key, replacement), "manifest exact status/boundary" if key in {"producer_executed", "implementation_v04_changed", "port_8911_must_be_stopped"} else "manifest nine-path boundary" if key == "exact_nine_paths" else "manifest missing-code set")
    rejected(lambda: enforce_boundary_observations(["forbidden_producer.py"], [], False), "producer_presence")
    rejected(lambda: enforce_boundary_observations([], ["forbidden_s5.pyc"], False), "s5_bytecode_presence")
    rejected(lambda: enforce_boundary_observations([], [], True), "port_8911_listener")
    if count < 25:
        fail("active attack minimum")
    return count


def enforce_boundary_observations(producer_or_s5_paths: list[str], cache_paths: list[str], port_listening: bool) -> None:
    if producer_or_s5_paths:
        fail(f"producer/S5 absence: {producer_or_s5_paths[:2]}")
    if cache_paths:
        fail(f"producer/S5 bytecode absence: {cache_paths[:2]}")
    if port_listening:
        fail("port 8911 listening")


def medical_writing_inventory(contract: dict[str, Any]) -> tuple[int, str]:
    regex = re.compile(contract["relative_path_regex"], re.IGNORECASE)
    rows = []
    for root_name in contract["roots"]:
        for path in (ROOT / root_name).rglob("*"):
            if path.is_file():
                relative = path.relative_to(ROOT).as_posix()
                if regex.search(relative):
                    rows.append((relative, raw(path)))
    rows.sort(key=lambda item: item[0].encode())
    payload = b"".join(path.encode() + b"\0" + sha.encode() + b"\n" for path, sha in rows)
    return len(rows), hashlib.sha256(payload).hexdigest()


def verify_absence_port_and_scope(manifest: dict[str, Any]) -> None:
    if {path.name for path in OUT.iterdir()} != {"schema.json", "base_input_registry.json", "gate_registry.json", "challenge_registry.json", "manifest.json"}:
        fail("exact five-artifact set")
    for relative in EXACT_PATHS:
        if not (ROOT / relative).is_file():
            fail(f"missing exact nine path: {relative}")
    protected = manifest["protected_accepted_pins"]
    if medical_writing_inventory(protected["medical_writing_inventory_contract"]) != (protected["medical_writing_protected_file_count"], protected["medical_writing_protected_inventory_sha256"]):
        fail("542 medical-writing aggregate")
    blocked = load(ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/manifest.json")
    future = set(blocked["future_producer_allowlist"])
    s5 = {
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_contracts.py", "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_authority_builder.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_projection.py", "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_validator.py",
        "poc/medical_monitoring_ai_native_r5/tests/s5_runtime_fixtures.py", "poc/medical_monitoring_ai_native_r5/tests/test_s5_contracts.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_s5_authority_builder.py", "poc/medical_monitoring_ai_native_r5/tests/test_s5_projection.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_s5_validator.py", "poc/medical_monitoring_ai_native_r5/tests/test_s5_readonly_gate.py",
        "poc/medical_monitoring_ai_native_r5/tests/challenges/test_s5_runtime_challenges.py", "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_readonly_sha256.json",
    }
    present = sorted(relative for relative in future | s5 if (ROOT / relative).exists())
    caches = [path for path in (ROOT / "poc/medical_monitoring_ai_native_r5").rglob("*") if path.is_file() and (path.suffix in {".pyc", ".pyo"}) and ("public_authority" in path.name or "s5_" in path.name)]
    with socket.socket() as connection:
        connection.settimeout(0.2)
        port_listening = connection.connect_ex(("127.0.0.1", 8911)) == 0
    enforce_boundary_observations(present, [str(path) for path in caches], port_listening)


def verify_generation_and_ruff() -> None:
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    run = subprocess.run([sys.executable, "-B", str(GENERATOR), "--check"], cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
    if run.returncode != 0:
        fail("generator --check: " + (run.stdout + run.stderr)[-2000:])
    with tempfile.TemporaryDirectory(prefix="error-delta-a-") as first, tempfile.TemporaryDirectory(prefix="error-delta-b-") as second:
        for destination in (first, second):
            execution = subprocess.run([sys.executable, "-B", str(GENERATOR), "--output-root", destination], cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
            if execution.returncode != 0:
                fail("isolated generation: " + (execution.stdout + execution.stderr)[-2000:])
        for relative in EXACT_PATHS:
            if (pathlib.Path(first) / relative).read_bytes() != (pathlib.Path(second) / relative).read_bytes():
                fail(f"double-generation drift: {relative}")
    lint = subprocess.run(["/Users/smkzw/.local/bin/uvx", "--offline", "ruff", "check", "--no-cache", str(GENERATOR.relative_to(ROOT)), str(VERIFIER.relative_to(ROOT))], cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
    if lint.returncode != 0:
        fail("offline Ruff: " + (lint.stdout + lint.stderr)[-3000:])


def main() -> int:
    verify_static_independence()
    verify_reseal_contract()
    manifest = verify_manifest_and_pins()
    bases, gates, challenges = verify_schema_and_registries(manifest)
    pre, emitted, _ordered, priorities, origins = independent_pre_delta()
    if manifest["pre_delta_execution_evidence"] != pre:
        fail("pre-delta execution evidence mismatch")
    delta_codes, replay = verify_challenges(bases, gates, challenges, priorities, origins)
    if len(emitted | delta_codes) != 192 or emitted & delta_codes:
        fail("actual 170+22=192 union")
    attacks = active_attack_checks(bases, gates, challenges, manifest, priorities, origins)
    verify_absence_port_and_scope(manifest)
    verify_generation_and_ruff()
    print(json.dumps({
        "status": "PASS", "optimize": sys.flags.optimize, "pre_delta": "170/192", "delta": "22/22",
        "post_union": "192/192", "accepted_entrypoints": pre["accepted_entrypoints"], "gate_execution_counts": replay["gate_execution_counts"],
        "governance_actions": replay["governance_actions"], "active_attacks": attacks, "double_generation": "byte_identical",
        "ruff": "offline_pass", "medical_writing": "542/542", "producer_s5_bytecode": "absent", "port_8911": "stopped",
        "self_acceptance": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
