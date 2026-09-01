"""Generate the synthetic-only public-authority error replay coverage delta v0.1."""

from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import sys
import tempfile
import unicodedata
from collections.abc import Callable
from typing import Any, NoReturn

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-error-replay-coverage-delta-v0.1"
SCHEMA_VERSION = "2026-08-21.1"
SUBJECT = "subject-temporal-public-v1"
AEMH = "aemh-match-history-public-v1"
OUT_REL = pathlib.Path("artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1")
GENERATOR_REL = "tools/generate_medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1.py"
VERIFIER_REL = "tools/verify_medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1.py"
CONTEXT_REL = "context/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1_20260821_context.md"
REVIEW_REL = "reviews/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1_20260821.md"
PARENT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
SEMANTIC_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1"
TEMPORAL_V01_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1"
TEMPORAL_V02_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2"
SUBJECT_SCHEMA_REL = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json"
AEMH_SCHEMA_REL = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json"
PARENT_VERIFIER_REL = "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py"

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

EXACT_PATHS = (
    CONTEXT_REL,
    REVIEW_REL,
    f"{OUT_REL}/schema.json",
    f"{OUT_REL}/base_input_registry.json",
    f"{OUT_REL}/gate_registry.json",
    f"{OUT_REL}/challenge_registry.json",
    f"{OUT_REL}/manifest.json",
    GENERATOR_REL,
    VERIFIER_REL,
)

BLOCKED_V04_PINS = {
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_20260821_context.md": "dd6c803175a37bb8ee573c7d13f5b213b51734fd0470bd7deb988050b756bf65",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_20260821.md": "3928e8069ef68e0dc19f2ada18b5fa24943e795c170362a095975cfe67fc384e",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/public_api.json": "d27523ec4a85218136f2640160a99ef85b9418a9224fdf24f290fac2fecc7d18",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/source_join_matrix.json": "ea825e18733611a69c354a93d555a555a76fa0b35df914bb1915c526cab0de59",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/invariant_error_matrix.json": "83064fbc0935b59510cc2fd463b7946165d86bec315b67ca3eda624efe1ed0d9",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/test_matrix.json": "86061b6609a75d2b576d76c6b8b8bf13324322d396e79facb66dd09c22b63e46",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/manifest.json": "c363811be037a107a369523c47f43a7e589ddc9f8e608ca87309e1f15b6f7a94",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4.py": "be0fa7f6aa8c91767c35d2842116bd7c36cca1f19eb58ef01ae592f339129a6b",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4.py": "a4df9626112e3fa5ee45d0ad538a298b29dab98cf122e912211cbe21d307a2fe",
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

MISSING_CODES = (
    "PUB_SCHEMA_EXACT_KEYS",
    "PUB_TYPE_BOOL_REQUIRED",
    "PUB_TYPE_MISMATCH",
    "PUB_IDENTITY_PROJECT_MISMATCH",
    "PUB_IDENTITY_RUN_MISMATCH",
    "PUB_IDENTITY_SNAPSHOT_MISMATCH",
    "PUB_IDENTITY_SITE_MISMATCH",
    "PUB_IDENTITY_SPINE_MISMATCH",
    "PUB_VISIBILITY_DEEP_LINK_INELIGIBLE",
    "PUB_RUNTIME_TEST_SURFACE_FORBIDDEN",
    "AEMH_WITHDRAW_REAPPEAR_HISTORY_LOSS",
    "SEM_TYPE_MISMATCH",
    "SEM_RISK_TAXONOMY_INCOMPLETE",
    "SEM_RISK_TAXONOMY_AMBIGUOUS",
    "SEM_SEVERITY_RULESET_INCOMPLETE",
    "SEM_SOURCE_RECORD_UNRESOLVED",
    "SEM_RECEIPT_HASH_MISMATCH",
    "SEM_ACCEPTED_RECORD_HASH_MISMATCH",
    "SEM_RECEIPT_PACKAGE_KIND_MISMATCH",
    "SEM_AUTHORITY_HASH_MISMATCH",
    "SEM_AUTHORITY_MISMATCH",
    "SEM_MANIFEST_HASH_MISMATCH",
)

GATE_KEYS = {
    "gate_id", "entrypoint_class", "accepted_source_path", "accepted_source_raw_sha256",
    "accepted_ast_selector", "accepted_ast_normalized_sha256", "input_type", "output_type",
    "permitted_error_codes", "algorithm_contract", "constructor_precondition", "mutation_phase",
    "reseal_handler", "issue_order_source", "side_effect_boundary",
}
BASE_KEYS = {
    "base_input_ref", "accepted_source_path", "accepted_source_raw_sha256",
    "accepted_source_json_pointer", "raw_input_identity", "canonical_input_identity",
    "constructor_id", "constructor_recipe",
}
CHALLENGE_KEYS = {
    "case_id", "surface", "error_code", "accepted_priority", "entrypoint_class", "gate_id",
    "base_input_ref", "base_input_content_identity", "constructor_id", "instance_selector",
    "single_mutation", "ordered_reseal", "observed_ordered_issues", "forbidden_output", "trace_identity",
}


def stop(message: str) -> NoReturn:
    raise SystemExit(f"STOP {message}")


def read_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def load_module(relative: str, name: str) -> Any:
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        stop(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pointer_get(document: Any, pointer: str) -> Any:
    current = document
    if pointer in ("", "/"):
        return current
    for token in pointer.strip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def pointer_parent(document: Any, pointer: str) -> tuple[Any, str]:
    parts = pointer.strip("/").split("/")
    current = document
    for token in parts[:-1]:
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current, parts[-1]


def ast_hash(path: pathlib.Path, selector: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    matches = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == selector]
    if len(matches) != 1:
        stop(f"AST selector unresolved: {path}:{selector}")
    return hashlib.sha256(ast.dump(matches[0], annotate_fields=True, include_attributes=False).encode()).hexdigest()


def accepted_append_only_bindings(priorities: dict[str, int]) -> dict[str, Any]:
    subject_path = ROOT / SUBJECT_SCHEMA_REL
    aemh_path = ROOT / AEMH_SCHEMA_REL
    parent_path = ROOT / PARENT_VERIFIER_REL
    if raw_sha(subject_path) != APPEND_ONLY_AUTHORITY_HARD_PINS["subject_schema_raw_sha256"]:
        stop("accepted subject schema pin drift")
    if raw_sha(aemh_path) != APPEND_ONLY_AUTHORITY_HARD_PINS["aemh_schema_raw_sha256"]:
        stop("accepted AEMH schema pin drift")
    if ast_hash(parent_path, "validate_subject") != APPEND_ONLY_AUTHORITY_HARD_PINS["subject_validator_ast_sha256"]:
        stop("accepted subject validator AST drift")
    if ast_hash(parent_path, "validate_aemh") != APPEND_ONLY_AUTHORITY_HARD_PINS["aemh_validator_ast_sha256"]:
        stop("accepted AEMH validator AST drift")
    subject = read_json(subject_path)
    aemh = read_json(aemh_path)

    subject_pointer, subject_hash = APPEND_ONLY_AUTHORITY_HARD_PINS["subject_identity_invariant"]
    subject_invariant = pointer_get(subject, subject_pointer)
    if digest(subject_invariant) != subject_hash:
        stop("accepted subject identity invariant drift")
    match = re.fullmatch(r"receipt, projection, visibility and every member join the same ([a-z/]+) identity", subject_invariant)
    if match is None:
        stop("accepted subject identity invariant grammar")
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
        stop("accepted identity dimension/error binding closure")

    history_pointer, history_hash = APPEND_ONLY_AUTHORITY_HARD_PINS["aemh_history_invariant"]
    history_ordinal = int(history_pointer.rsplit("/", 1)[1])
    history_value = pointer_get(aemh, history_pointer)
    matching_ordinals = [index for index, value in enumerate(aemh["invariants"]) if digest(value) == history_hash]
    if matching_ordinals != [history_ordinal] or digest(history_value) != history_hash:
        stop("accepted history selector must resolve exact one invariant")
    history_invariant = {
        "invariant_id": f"{aemh['schema']}#{history_pointer}",
        "ordinal": history_ordinal,
        "json_pointer": history_pointer,
        "value": history_value,
        "normalized_content_hash": history_hash,
    }
    event_kinds = [kind for kind in aemh["enums"]["history_event_kind"] if kind in history_value]
    if len(event_kinds) != 2:
        stop("accepted history event-kind binding")
    supporting_rows = []
    for pointer, expected_hash in APPEND_ONLY_AUTHORITY_HARD_PINS["aemh_supporting_invariants"]:
        value = pointer_get(aemh, pointer)
        if digest(value) != expected_hash:
            stop(f"accepted AEMH supporting invariant drift: {pointer}")
        supporting_rows.append({"invariant_id": f"{aemh['schema']}#{pointer}", "ordinal": int(pointer.rsplit("/", 1)[1]), "json_pointer": pointer, "value": value, "normalized_content_hash": expected_hash})
    stable_text = supporting_rows[-1]["value"]
    stable_terms_match = re.search(r"; ([a-z/]+) identity is stable across versions$", stable_text)
    if stable_terms_match is None:
        stop("accepted stable-thread invariant grammar")
    stable_terms = stable_terms_match.group(1).split("/")
    thread_fields = list(aemh["objects"]["AEMHMatchThread"])
    stable_fields = sorted({field for field in thread_fields if field == "thread_ref" or any(term in field for term in stable_terms)})
    event_stems = [kind.removesuffix("n").removesuffix("ed").upper() for kind in event_kinds]
    history_codes = [
        code for code in aemh["error_codes"]
        if code.startswith("AEMH_") and all(stem in code for stem in event_stems) and "HISTORY" in code and "LOSS" in code
    ]
    if len(history_codes) != 1 or history_codes[0] not in MISSING_CODES:
        stop("accepted history invariant/error binding closure")
    history_code = history_codes[0]

    return {
        "subject_identity": {
            "schema_path": SUBJECT_SCHEMA_REL,
            "schema_raw_sha256": raw_sha(subject_path),
            "invariant": {"json_pointer": subject_pointer, "value": subject_invariant, "content_hash": subject_hash},
            "error_registry": {"json_pointer": "/error_codes", "content_hash": digest(subject["error_codes"])},
            "validator": {"source_path": PARENT_VERIFIER_REL, "selector": "validate_subject", "ast_normalized_sha256": ast_hash(parent_path, "validate_subject")},
            "dimension_bindings": dimension_bindings,
        },
        "aemh_history": {
            "schema_path": AEMH_SCHEMA_REL,
            "schema_raw_sha256": raw_sha(aemh_path),
            "history_invariant": history_invariant,
            "supporting_invariants": supporting_rows,
            "event_registry": {"json_pointer": "/enums/history_event_kind", "content_hash": digest(aemh["enums"]["history_event_kind"])},
            "error_registry": {"json_pointer": "/error_codes", "content_hash": digest(aemh["error_codes"])},
            "validator": {"source_path": PARENT_VERIFIER_REL, "selector": "validate_aemh", "ast_normalized_sha256": ast_hash(parent_path, "validate_aemh")},
            "event_kinds": event_kinds,
            "stable_thread_fields": stable_fields,
            "error_code": history_code,
            "accepted_priority": priorities[history_code],
        },
    }


def accepted_priority() -> tuple[list[str], dict[str, int], dict[str, str]]:
    subject = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    semantic = read_json(SEMANTIC_DIR / "schema.json")
    temporal = read_json(TEMPORAL_V01_DIR / "challenge_registry.json")
    parent_codes = list(dict.fromkeys(subject["error_codes"] + aemh["error_codes"]))
    semantic_codes = list(semantic["typed_error_priority"])
    temporal_codes = sorted({row["expected_error"] for row in temporal["cases"]})
    order = parent_codes + semantic_codes + temporal_codes
    if len(order) != 192 or len(set(order)) != 192:
        stop("accepted 192-code priority closure")
    origin = {code: "parent" for code in parent_codes}
    origin.update({code: "semantic_delta" for code in semantic_codes})
    origin.update({code: "temporal_delta" for code in temporal_codes})
    return order, {code: index for index, code in enumerate(order, 1)}, origin


def verify_pin_map(pin_map: dict[str, str], label: str) -> None:
    for relative, expected in pin_map.items():
        path = ROOT / relative
        if not path.is_file() or raw_sha(path) != expected:
            stop(f"{label} drift: {relative}")


def load_pinned_temporal_v02() -> dict[str, Any]:
    verify_pin_map(dict(EXTERNAL_ROOT_PIN_ITEMS), "external authority root")
    temporal = read_json(TEMPORAL_V02_DIR / "manifest.json")
    protected = temporal.get("protected_accepted_pins")
    if not isinstance(protected, dict) or not isinstance(protected.get("protected_path_sha256"), dict):
        stop("accepted protected scalar binding shape")
    protected_paths = protected["protected_path_sha256"]
    for scalar, relative, expected in PROTECTED_SCALAR_BINDINGS:
        if raw_sha(ROOT / relative) != expected:
            stop(f"accepted protected scalar actual raw: {scalar}")
        if protected.get(scalar) != expected or protected_paths.get(relative) != expected:
            stop(f"accepted temporal protected scalar binding: {scalar}")
    return temporal


def verify_negative_history(value: dict[str, Any], v03: dict[str, str]) -> None:
    exact_keys = {"authority", "v0_1", "v0_2", "rejection_record_path", "rejection_record_raw_sha256"}
    if set(value) != exact_keys or value["authority"] is not False:
        stop("negative history exact keys/authority")
    if value["v0_1"] != NEGATIVE_V01_PINS or value["v0_2"] != NEGATIVE_V02_PINS:
        stop("negative history frozen snapshot pin map")
    if (value["rejection_record_path"], value["rejection_record_raw_sha256"]) != NEGATIVE_V02_RECORD:
        stop("negative history rejection record path/hash")
    if v03 != NEGATIVE_V03_PINS:
        stop("negative history v0.3 frozen snapshot pin map")
    verify_pin_map(NEGATIVE_V01_PINS, "negative v0.1")
    verify_pin_map(NEGATIVE_V02_PINS, "negative v0.2")
    verify_pin_map(NEGATIVE_V03_PINS, "negative v0.3")
    verify_pin_map({NEGATIVE_V02_RECORD[0]: NEGATIVE_V02_RECORD[1]}, "negative v0.2 rejection record")


def pre_delta_execution() -> tuple[dict[str, Any], set[str], list[str], dict[str, int], dict[str, str]]:
    order, priorities, origins = accepted_priority()
    parent = load_module("tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py", "coverage_parent_generator")
    parent_registry = read_json(PARENT_DIR / "challenge_registry.json")
    parent_exact = read_json(ROOT / "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json")
    subject_schema = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh_schema = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    parent_inputs = read_json(PARENT_DIR / "base_inputs.json")
    actual_parent: list[str] = []
    for name in ("validate_subject", "validate_aemh", "overlay_validation_issues", "source_matrix_validation_issues", "manifest_contract_validation_issues"):
        original = getattr(parent, name)

        def wrapper(*args: Any, _original: Callable[..., list[str]] = original, **kwargs: Any) -> list[str]:
            result = _original(*args, **kwargs)
            actual_parent.extend(result)
            return result

        setattr(parent, name, wrapper)
    with contextlib.redirect_stdout(io.StringIO()):
        parent_count = parent.verify_challenges(parent_registry, parent_exact, subject_schema, aemh_schema, parent_inputs)

    semantic = load_module("tools/verify_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py", "coverage_semantic_generator")
    semantic_manifest = read_json(SEMANTIC_DIR / "manifest.json")
    semantic_challenges = read_json(SEMANTIC_DIR / "challenge_registry.json")
    source_registry = semantic_manifest["synthetic_typed_source_record_registry"]
    acceptance_registry = semantic_manifest["synthetic_policy_acceptance_registry"]
    source_records = semantic.validate_source_registry(source_registry)
    accepted_records = semantic.validate_acceptance_registry(acceptance_registry)
    semantic_result = semantic.run_challenges(semantic_challenges, source_registry, source_records, acceptance_registry, accepted_records)
    actual_semantic = {item["outcome"] for item in semantic_result["outcomes"] if item["outcome"] != "success"}

    temporal_v01 = load_module("tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1.py", "coverage_temporal_v01_generator")
    temporal_manifest = read_json(TEMPORAL_V01_DIR / "manifest.json")
    temporal_schema = read_json(TEMPORAL_V01_DIR / "schema.json")
    temporal_matrix = read_json(TEMPORAL_V01_DIR / "source_matrix_delta.json")
    temporal_recipes = read_json(TEMPORAL_V01_DIR / "recipe_registry.json")
    temporal_challenges = read_json(TEMPORAL_V01_DIR / "challenge_registry.json")
    temporal_v01.verify_schema(temporal_schema, temporal_manifest)
    temporal_v01.verify_source_matrix(temporal_matrix, temporal_manifest)
    temporal_v01.verify_typed_source_paths(temporal_matrix, temporal_manifest)
    recipe_map = temporal_v01.verify_recipes(temporal_recipes, temporal_schema, temporal_manifest)
    temporal_v01.verify_challenges(temporal_challenges, temporal_recipes, temporal_manifest, temporal_schema, recipe_map)
    actual_temporal_v01 = {row["expected_error"] for row in temporal_challenges["cases"]}

    temporal_v02 = load_module("tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py", "coverage_temporal_v02_generator")
    manifest_v02 = temporal_v02.load(temporal_v02.MANIFEST)
    schema_v02 = temporal_v02.load(temporal_v02.SCHEMA)
    emitters_v02 = temporal_v02.load(temporal_v02.EMITTERS)
    fixtures_v02 = temporal_v02.load(temporal_v02.FIXTURES)
    traces_v02 = temporal_v02.load(temporal_v02.TRACES)
    temporal_v02.verify_manifest(manifest_v02)
    temporal_v02.verify_schema(schema_v02, manifest_v02)
    temporal_v02.verify_emitters(emitters_v02, manifest_v02, schema_v02, fixtures_v02)
    runtime_v02 = temporal_v02.verify_fixtures(fixtures_v02, manifest_v02, emitters_v02)
    temporal_v02.verify_traces(traces_v02, manifest_v02, runtime_v02)
    temporal_v02.verify_parent_error_probes(runtime_v02)
    actual_temporal_v02 = {code for row in traces_v02["records"] for code in row["observed_ordered_issues"]}

    emitted = set(actual_parent) | actual_semantic | actual_temporal_v01 | actual_temporal_v02
    missing = [code for code in order if code not in emitted]
    if len(emitted) != 170 or tuple(missing) != MISSING_CODES:
        stop(f"pre-delta executable union={len(emitted)} missing={missing}")
    evidence = {
        "accepted_entrypoints": {
            "parent": {"executed": parent_count, "unique_actual_codes": len(set(actual_parent))},
            "semantic": {"executed": semantic_result["count"], "unique_actual_codes": len(actual_semantic)},
            "temporal_v01": {"executed": len(temporal_challenges["cases"]), "unique_actual_codes": len(actual_temporal_v01)},
            "temporal_v02": {"executed": len(traces_v02["records"]), "unique_actual_codes": len(actual_temporal_v02)},
        },
        "error_universe_count": len(order),
        "pre_delta_emitted_union_count": len(emitted),
        "missing_codes": missing,
    }
    return evidence, emitted, order, priorities, origins


def source_value(path: pathlib.Path, pointer: str) -> Any:
    return pointer_get(read_json(path), pointer)


def raw_input_identity(value: Any) -> str:
    raw_order_bytes = json.dumps(value, ensure_ascii=False, sort_keys=False, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw_order_bytes).hexdigest()


def base_input_registry() -> dict[str, Any]:
    fixture_path = TEMPORAL_V02_DIR / "full_graph_fixture_registry.json"
    semantic_challenge_path = SEMANTIC_DIR / "challenge_registry.json"
    semantic_manifest_path = SEMANTIC_DIR / "manifest.json"
    parent_manifest_path = PARENT_DIR / "manifest.json"
    specs = [
        ("base.parent.subject", fixture_path, "/baselines/0/authority_input", "temporal_v02.closed_16_recipe_32_node.subject", {"entrypoint": "execute_independent_recipe_dag", "target_contract": SUBJECT, "packet_mirror_forbidden": True}),
        ("base.parent.aemh", fixture_path, "/baselines/1/authority_input", "temporal_v02.closed_16_recipe_32_node.aemh", {"entrypoint": "execute_independent_recipe_dag", "target_contract": AEMH, "returns": ["previous_packet", "current_packet"], "packet_mirror_forbidden": True}),
        ("base.semantic.risk_high", semantic_challenge_path, "/baselines/risk_high", "semantic.accepted_baseline.risk_high", {"entrypoint": "copy_accepted_semantic_baseline", "registry_roots": ["synthetic_typed_source_record_registry", "synthetic_policy_acceptance_registry"]}),
        ("base.semantic.risk_authority", semantic_challenge_path, "/baselines/risk_authority", "semantic.accepted_baseline.risk_authority", {"entrypoint": "copy_accepted_semantic_baseline", "candidate_expected_independent": True}),
        ("base.semantic.manifest", semantic_manifest_path, "/", "semantic.accepted_manifest", {"entrypoint": "copy_accepted_manifest", "manifest_hash_recomputed_by_gate": True}),
        ("base.governance.runtime", parent_manifest_path, "/no_runtime_test_surface", "parent.accepted_runtime_surface_contract", {"entrypoint": "parameterized_ast_equivalent_no_runtime_surface_scan", "filesystem_root": "TemporaryDirectory"}),
    ]
    rows = []
    for ref, path, pointer, constructor_id, recipe in specs:
        value = source_value(path, pointer)
        rows.append({
            "base_input_ref": ref,
            "accepted_source_path": path.relative_to(ROOT).as_posix(),
            "accepted_source_raw_sha256": raw_sha(path),
            "accepted_source_json_pointer": pointer,
            "raw_input_identity": raw_input_identity(value),
            "canonical_input_identity": digest(value),
            "constructor_id": constructor_id,
            "constructor_recipe": recipe,
        })
    return {"schema": "error-replay-base-input-registry-v0.1", "schema_version": SCHEMA_VERSION, "rows": rows}


def gate_row(gate_id: str, entrypoint_class: str, path: str, selector: str, input_type: str, permitted: list[str], algorithm: Any, precondition: str, phase: str, reseal: str, order_source: str, boundary: str) -> dict[str, Any]:
    source = ROOT / path
    return {
        "gate_id": gate_id,
        "entrypoint_class": entrypoint_class,
        "accepted_source_path": path,
        "accepted_source_raw_sha256": raw_sha(source),
        "accepted_ast_selector": selector,
        "accepted_ast_normalized_sha256": ast_hash(source, selector),
        "input_type": input_type,
        "output_type": "ordered ValidationIssue tuple; no packet/authority on any issue",
        "permitted_error_codes": permitted,
        "algorithm_contract": algorithm,
        "constructor_precondition": precondition,
        "mutation_phase": phase,
        "reseal_handler": reseal,
        "issue_order_source": order_source,
        "side_effect_boundary": boundary,
    }


def gate_registry() -> dict[str, Any]:
    parent_path = "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py"
    semantic_path = "tools/verify_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py"
    parent_order = "accepted parent subject/aemh error_codes arrays, stable first occurrence"
    semantic_order = "accepted semantic schema typed_error_priority array"
    _ordered, priorities, _origins = accepted_priority()
    bindings = accepted_append_only_bindings(priorities)
    identity_codes = [row["error_code"] for row in bindings["subject_identity"]["dimension_bindings"]]
    history_code = bindings["aemh_history"]["error_code"]
    rows = [
        gate_row("gate.parent.untrusted_exact_parser", "untrusted_schema_parser", parent_path, "validate_exact_object", "untrusted Mapping plus accepted exact object schema", ["PUB_SCHEMA_EXACT_KEYS", "PUB_TYPE_BOOL_REQUIRED", "PUB_TYPE_MISMATCH"], "parse the selected raw Mapping directly; exact keys and scalar types are checked before any dataclass construction", "real temporal-v0.2 constructor has produced a parent-valid Subject packet", "after primary malformed Mapping mutation and declared dependent reseal", "closed selected exact-object reseal only", parent_order, "pure memory; malformed input is never normalized"),
        gate_row("gate.parent.identity_dimension", "typed_validator", parent_path, "validate_subject", "constructed SubjectTemporalAuthorityPacket", identity_codes, {"summary": "append-only narrowed replay gate compares receipt/projection/visibility/every-member identity on one accepted dimension", "accepted_authority_binding": bindings["subject_identity"]}, "parent-valid Subject packet and accepted invariant/error binding", "after receipt-scope primary mutation and scope/receipt/packet reseal", "reseal_receipt_scope_receipt_packet", parent_order, "pure memory; emits only the accepted registry dimension code"),
        gate_row("gate.parent.visibility_source", "typed_validator", parent_path, "validate_visibility_and_sources", "constructed Subject receipt and projection", ["PUB_VISIBILITY_DEEP_LINK_INELIGIBLE"], "invoke accepted visibility/source validator without filtering its complete returned list", "parent-valid Subject packet", "after visibility boolean mutation and closure/receipt/packet reseal", "reseal_visibility_receipt_packet", parent_order, "pure memory"),
        gate_row("gate.parent.runtime_surface", "artifact_governance", parent_path, "verify_no_runtime_test_surface", "accepted no-runtime-surface contract plus isolated filesystem root", ["PUB_RUNTIME_TEST_SURFACE_FORBIDDEN"], "AST-equivalent parameterized accepted path-name scan executes against one actual forbidden file", "accepted manifest no_runtime_test_surface object", "during isolated TemporaryDirectory mutation", "none", parent_order, "TemporaryDirectory only; no workspace path is writable"),
        gate_row("gate.parent.aemh_history_preservation", "typed_validator", parent_path, "validate_aemh", "constructed previous/current AEMH packets plus pre-mutation current packet", [history_code], {"summary": "append-only narrowed replay gate preserves the accepted event subset byte-identically in the same stable thread", "accepted_authority_binding": bindings["aemh_history"]}, "real temporal-v0.2 AEMH previous/current constructor pair and accepted invariant/error binding", "after one accepted history-event deletion and ordered parent reseal", "reseal_aemh_current_full", parent_order, "pure memory; emits only the accepted registry history-loss code"),
        gate_row("gate.semantic.common_parser", "untrusted_schema_parser", semantic_path, "validate_common_package", "accepted risk taxonomy package Mapping", ["SEM_TYPE_MISMATCH"], "invoke accepted common package parser on raw Mapping", "accepted semantic risk_high baseline", "immediately after primary malformed type mutation", "none", semantic_order, "pure memory"),
        gate_row("gate.semantic.risk_validator", "typed_validator", semantic_path, "validate_risk_package", "accepted risk taxonomy package Mapping", ["SEM_RISK_TAXONOMY_INCOMPLETE", "SEM_RISK_TAXONOMY_AMBIGUOUS"], "invoke accepted risk taxonomy validator", "accepted semantic risk_high baseline", "after one rule-set mutation and package reseal", "reseal_taxonomy_package", semantic_order, "pure memory"),
        gate_row("gate.semantic.severity_validator", "typed_validator", semantic_path, "validate_severity_package", "accepted severity package Mapping", ["SEM_SEVERITY_RULESET_INCOMPLETE"], "invoke accepted severity validator", "accepted semantic risk_high baseline", "after critical-rule deletion and package reseal", "reseal_severity_package", semantic_order, "pure memory"),
        gate_row("gate.semantic.token_evidence", "typed_validator", semantic_path, "validate_token_evidence", "accepted taxonomy token evidence plus accepted registries", ["SEM_SOURCE_RECORD_UNRESOLVED"], "invoke accepted token-evidence validator against immutable source registry", "accepted semantic risk_high baseline and pinned registry roots", "after source ref mutation and evidence reseal", "reseal_taxonomy_evidence", semantic_order, "pure memory"),
        gate_row("gate.semantic.receipt", "typed_validator", semantic_path, "validate_receipt", "accepted taxonomy receipt/package plus acceptance registry", ["SEM_RECEIPT_HASH_MISMATCH", "SEM_ACCEPTED_RECORD_HASH_MISMATCH", "SEM_RECEIPT_PACKAGE_KIND_MISMATCH"], "invoke accepted receipt validator without filtering", "accepted semantic risk_high baseline and pinned acceptance registry", "after one receipt mutation and declared receipt reseal", "closed receipt reseal or none", semantic_order, "pure memory"),
        gate_row("gate.semantic.candidate_comparison", "constructor_candidate_comparison", semantic_path, "risk_authority", "accepted risk_authority baseline", ["SEM_AUTHORITY_HASH_MISMATCH", "SEM_AUTHORITY_MISMATCH"], "accepted evaluate_risk constructs expected independently; candidate exact/hash gate runs before equality comparison", "accepted risk_authority source_input and candidate", "after one candidate mutation and declared candidate reseal", "reseal_candidate_authority or none", semantic_order, "pure memory; expected cannot be derived from candidate"),
        gate_row("gate.semantic.manifest", "artifact_governance", semantic_path, "validate_parent_and_manifest", "accepted semantic manifest Mapping", ["SEM_MANIFEST_HASH_MISMATCH"], "invoke accepted semantic manifest hash gate", "accepted semantic manifest bytes", "immediately after manifest content hash mutation", "none", semantic_order, "pure memory; no manifest write"),
    ]
    return {"schema": "error-replay-gate-registry-v0.1", "schema_version": SCHEMA_VERSION, "rows": rows}


def challenge_specs() -> list[dict[str, Any]]:
    return [
        {"case_id": "ERD-001", "surface": "subject_packet_root", "error_code": "PUB_SCHEMA_EXACT_KEYS", "gate_id": "gate.parent.untrusted_exact_parser", "base": "base.parent.subject", "selector": {"object_type": "SubjectTemporalAuthorityPacket", "json_pointer": "/"}, "mutation": {"op": "add", "path": "/unexpected_root_key", "value": True}, "reseal": [], "forbidden": "any_public_authority_packet"},
        {"case_id": "ERD-002", "surface": "subject_visibility", "error_code": "PUB_TYPE_BOOL_REQUIRED", "gate_id": "gate.parent.untrusted_exact_parser", "base": "base.parent.subject", "selector": {"object_type": "VisibilityClosure", "json_pointer": "/receipt/visibility_closure"}, "mutation": {"op": "replace", "path": "/receipt/visibility_closure/deep_link_eligible", "value": 1}, "reseal": ["reseal_visibility_receipt_packet"], "forbidden": "any_public_authority_packet"},
        {"case_id": "ERD-003", "surface": "subject_projection", "error_code": "PUB_TYPE_MISMATCH", "gate_id": "gate.parent.untrusted_exact_parser", "base": "base.parent.subject", "selector": {"object_type": "SubjectTemporalPublicProjection", "json_pointer": "/projection"}, "mutation": {"op": "replace", "path": "/projection/receipt_ref", "value": 7}, "reseal": ["reseal_subject_projection_packet"], "forbidden": "any_public_authority_packet"},
        {"case_id": "ERD-004", "surface": "subject_identity_project", "error_code": "PUB_IDENTITY_PROJECT_MISMATCH", "gate_id": "gate.parent.identity_dimension", "base": "base.parent.subject", "selector": {"dimension": "project_ref"}, "mutation": {"op": "replace", "path": "/receipt/scope_identity/project_ref", "value": "project::replay-mismatch"}, "reseal": ["reseal_receipt_scope_receipt_packet"], "forbidden": "any_public_authority_packet"},
        {"case_id": "ERD-005", "surface": "subject_identity_run", "error_code": "PUB_IDENTITY_RUN_MISMATCH", "gate_id": "gate.parent.identity_dimension", "base": "base.parent.subject", "selector": {"dimension": "run_ref"}, "mutation": {"op": "replace", "path": "/receipt/scope_identity/run_ref", "value": "run::replay-mismatch"}, "reseal": ["reseal_receipt_scope_receipt_packet"], "forbidden": "any_public_authority_packet"},
        {"case_id": "ERD-006", "surface": "subject_identity_snapshot", "error_code": "PUB_IDENTITY_SNAPSHOT_MISMATCH", "gate_id": "gate.parent.identity_dimension", "base": "base.parent.subject", "selector": {"dimension": "snapshot_ref"}, "mutation": {"op": "replace", "path": "/receipt/scope_identity/snapshot_ref", "value": "snapshot::replay-mismatch"}, "reseal": ["reseal_receipt_scope_receipt_packet"], "forbidden": "any_public_authority_packet"},
        {"case_id": "ERD-007", "surface": "subject_identity_site", "error_code": "PUB_IDENTITY_SITE_MISMATCH", "gate_id": "gate.parent.identity_dimension", "base": "base.parent.subject", "selector": {"dimension": "site_ref"}, "mutation": {"op": "replace", "path": "/receipt/scope_identity/site_ref", "value": "site::replay-mismatch"}, "reseal": ["reseal_receipt_scope_receipt_packet"], "forbidden": "any_public_authority_packet"},
        {"case_id": "ERD-008", "surface": "subject_identity_spine", "error_code": "PUB_IDENTITY_SPINE_MISMATCH", "gate_id": "gate.parent.identity_dimension", "base": "base.parent.subject", "selector": {"dimension": "spine_ref"}, "mutation": {"op": "replace", "path": "/receipt/scope_identity/spine_ref", "value": "spine::replay-mismatch"}, "reseal": ["reseal_receipt_scope_receipt_packet"], "forbidden": "any_public_authority_packet"},
        {"case_id": "ERD-009", "surface": "subject_visibility", "error_code": "PUB_VISIBILITY_DEEP_LINK_INELIGIBLE", "gate_id": "gate.parent.visibility_source", "base": "base.parent.subject", "selector": {"json_pointer": "/receipt/visibility_closure"}, "mutation": {"op": "replace", "path": "/receipt/visibility_closure/deep_link_eligible", "value": False}, "reseal": ["reseal_visibility_receipt_packet"], "forbidden": "any_public_authority_packet"},
        {"case_id": "ERD-010", "surface": "isolated_runtime_surface", "error_code": "PUB_RUNTIME_TEST_SURFACE_FORBIDDEN", "gate_id": "gate.parent.runtime_surface", "base": "base.governance.runtime", "selector": {"scan_mode": "path_names_only"}, "mutation": {"op": "create_temp_file", "path": "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py", "value": "synthetic replay probe"}, "reseal": [], "forbidden": "workspace_write_or_declaration_only"},
        {"case_id": "ERD-011", "surface": "aemh_history", "error_code": "AEMH_WITHDRAW_REAPPEAR_HISTORY_LOSS", "gate_id": "gate.parent.aemh_history_preservation", "base": "base.parent.aemh", "selector": {"thread_ref": "aemh-thread::ae::1", "event_kind": "reappeared"}, "mutation": {"op": "remove", "path": "/current_packet/projection/threads/0/history_entries/3"}, "reseal": ["reseal_aemh_current_full"], "forbidden": "any_public_authority_packet"},
        {"case_id": "ERD-012", "surface": "risk_taxonomy_package", "error_code": "SEM_TYPE_MISMATCH", "gate_id": "gate.semantic.common_parser", "base": "base.semantic.risk_high", "selector": {"json_pointer": "/taxonomy_package"}, "mutation": {"op": "replace", "path": "/taxonomy_package/package_id", "value": 7}, "reseal": [], "forbidden": "any_semantic_authority"},
        {"case_id": "ERD-013", "surface": "risk_taxonomy_rules", "error_code": "SEM_RISK_TAXONOMY_INCOMPLETE", "gate_id": "gate.semantic.risk_validator", "base": "base.semantic.risk_high", "selector": {"json_pointer": "/taxonomy_package"}, "mutation": {"op": "replace", "path": "/taxonomy_package/rules", "value": []}, "reseal": ["reseal_taxonomy_package"], "forbidden": "any_semantic_authority"},
        {"case_id": "ERD-014", "surface": "risk_taxonomy_rules", "error_code": "SEM_RISK_TAXONOMY_AMBIGUOUS", "gate_id": "gate.semantic.risk_validator", "base": "base.semantic.risk_high", "selector": {"json_pointer": "/taxonomy_package"}, "mutation": {"op": "append_copy", "path": "/taxonomy_package/rules", "value_from": "/taxonomy_package/rules/0"}, "reseal": ["reseal_taxonomy_package"], "forbidden": "any_semantic_authority"},
        {"case_id": "ERD-015", "surface": "severity_rules", "error_code": "SEM_SEVERITY_RULESET_INCOMPLETE", "gate_id": "gate.semantic.severity_validator", "base": "base.semantic.risk_high", "selector": {"json_pointer": "/severity_package"}, "mutation": {"op": "remove", "path": "/severity_package/rules/0"}, "reseal": ["reseal_severity_package"], "forbidden": "any_semantic_authority"},
        {"case_id": "ERD-016", "surface": "taxonomy_evidence", "error_code": "SEM_SOURCE_RECORD_UNRESOLVED", "gate_id": "gate.semantic.token_evidence", "base": "base.semantic.risk_high", "selector": {"json_pointer": "/taxonomy_evidence"}, "mutation": {"op": "replace", "path": "/taxonomy_evidence/source_record_ref", "value": "source-record::missing"}, "reseal": ["reseal_taxonomy_evidence"], "forbidden": "any_semantic_authority"},
        {"case_id": "ERD-017", "surface": "taxonomy_receipt", "error_code": "SEM_RECEIPT_HASH_MISMATCH", "gate_id": "gate.semantic.receipt", "base": "base.semantic.risk_high", "selector": {"package_key": "taxonomy_package", "receipt_key": "taxonomy_receipt", "package_kind": "risk_taxonomy"}, "mutation": {"op": "replace", "path": "/taxonomy_receipt/receipt_content_hash", "value": "0000000000000000000000000000000000000000000000000000000000000000"}, "reseal": [], "forbidden": "any_semantic_authority"},
        {"case_id": "ERD-018", "surface": "taxonomy_receipt", "error_code": "SEM_ACCEPTED_RECORD_HASH_MISMATCH", "gate_id": "gate.semantic.receipt", "base": "base.semantic.risk_high", "selector": {"package_key": "taxonomy_package", "receipt_key": "taxonomy_receipt", "package_kind": "risk_taxonomy"}, "mutation": {"op": "replace", "path": "/taxonomy_receipt/accepted_record_content_hash", "value": "0000000000000000000000000000000000000000000000000000000000000000"}, "reseal": ["reseal_taxonomy_receipt"], "forbidden": "any_semantic_authority"},
        {"case_id": "ERD-019", "surface": "taxonomy_receipt", "error_code": "SEM_RECEIPT_PACKAGE_KIND_MISMATCH", "gate_id": "gate.semantic.receipt", "base": "base.semantic.risk_high", "selector": {"package_key": "taxonomy_package", "receipt_key": "taxonomy_receipt", "package_kind": "risk_taxonomy"}, "mutation": {"op": "replace", "path": "/taxonomy_receipt/package_kind", "value": "severity_policy"}, "reseal": ["reseal_taxonomy_receipt"], "forbidden": "any_semantic_authority"},
        {"case_id": "ERD-020", "surface": "candidate_authority", "error_code": "SEM_AUTHORITY_HASH_MISMATCH", "gate_id": "gate.semantic.candidate_comparison", "base": "base.semantic.risk_authority", "selector": {"candidate_key": "candidate_authority", "source_key": "source_input"}, "mutation": {"op": "replace", "path": "/candidate_authority/authority_content_hash", "value": "0000000000000000000000000000000000000000000000000000000000000000"}, "reseal": [], "forbidden": "any_semantic_authority"},
        {"case_id": "ERD-021", "surface": "candidate_authority", "error_code": "SEM_AUTHORITY_MISMATCH", "gate_id": "gate.semantic.candidate_comparison", "base": "base.semantic.risk_authority", "selector": {"candidate_key": "candidate_authority", "source_key": "source_input"}, "mutation": {"op": "replace", "path": "/candidate_authority/authority_ref", "value": "risk-authority::replay-mismatch"}, "reseal": ["reseal_candidate_authority"], "forbidden": "any_semantic_authority"},
        {"case_id": "ERD-022", "surface": "semantic_manifest", "error_code": "SEM_MANIFEST_HASH_MISMATCH", "gate_id": "gate.semantic.manifest", "base": "base.semantic.manifest", "selector": {"json_pointer": "/"}, "mutation": {"op": "replace", "path": "/manifest_content_hash", "value": "0000000000000000000000000000000000000000000000000000000000000000"}, "reseal": [], "forbidden": "any_semantic_authority"},
    ]


def construct_bases() -> tuple[dict[str, Any], dict[str, Any]]:
    temporal = load_module("tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py", "delta_constructor_generator")
    fixture_registry = temporal.load(temporal.FIXTURES)
    recipes = temporal.load(temporal.EMITTERS)
    constructed: dict[str, Any] = {}
    authority_inputs: dict[str, Any] = {}
    for row in fixture_registry["baselines"]:
        bundle = copy.deepcopy(row["authority_input"])
        target = bundle["target_contract"]
        if temporal.authority_issues(bundle, temporal.load(temporal.SCHEMA)):
            stop(f"base authority input invalid: {target}")
        built, _ = temporal.execute_independent_recipe_dag(bundle, recipes)
        if target == SUBJECT:
            issues = temporal.validate_parent(target, built)
            constructed["base.parent.subject"] = built
        else:
            previous, current = built
            issues = [*temporal.validate_parent(target, previous, None), *temporal.validate_parent(target, current, previous)]
            constructed["base.parent.aemh"] = {"previous_packet": previous, "current_packet": current}
        if issues:
            stop(f"real constructor parent baseline issues: {target}:{issues}")
        authority_inputs[target] = bundle
    semantic_challenges = read_json(SEMANTIC_DIR / "challenge_registry.json")
    constructed["base.semantic.risk_high"] = copy.deepcopy(semantic_challenges["baselines"]["risk_high"])
    constructed["base.semantic.risk_authority"] = copy.deepcopy(semantic_challenges["baselines"]["risk_authority"])
    constructed["base.semantic.manifest"] = read_json(SEMANTIC_DIR / "manifest.json")
    constructed["base.governance.runtime"] = read_json(PARENT_DIR / "manifest.json")["no_runtime_test_surface"]
    return constructed, authority_inputs


def apply_primary(document: Any, mutation: dict[str, Any]) -> None:
    operation = mutation["op"]
    if operation == "create_temp_file":
        return
    parent, key = pointer_parent(document, mutation["path"])
    if operation == "replace":
        if isinstance(parent, list):
            parent[int(key)] = copy.deepcopy(mutation["value"])
        else:
            parent[key] = copy.deepcopy(mutation["value"])
    elif operation == "add":
        parent[key] = copy.deepcopy(mutation["value"])
    elif operation == "remove":
        if isinstance(parent, list):
            parent.pop(int(key))
        else:
            del parent[key]
    elif operation == "append_copy":
        target = pointer_get(document, mutation["path"])
        target.append(copy.deepcopy(pointer_get(document, mutation["value_from"])))
    else:
        stop(f"unknown primary mutation: {operation}")


def structural_patches(before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
    if type(before) is not type(after):
        return [{"op": "replace", "path": path or "/", "before": before, "after": after}]
    if isinstance(before, dict):
        changes = []
        for key in sorted(set(before) | set(after)):
            child = f"{path}/{key}"
            if key not in before:
                changes.append({"op": "add", "path": child, "after": after[key]})
            elif key not in after:
                changes.append({"op": "remove", "path": child, "before": before[key]})
            else:
                changes.extend(structural_patches(before[key], after[key], child))
        return changes
    if isinstance(before, list):
        if len(after) == len(before) + 1:
            for index in range(len(after)):
                if before == after[:index] + after[index + 1 :]:
                    return [{"op": "add", "path": f"{path}/{index}", "after": after[index]}]
        if len(before) == len(after) + 1:
            for index in range(len(before)):
                if after == before[:index] + before[index + 1 :]:
                    return [{"op": "remove", "path": f"{path}/{index}", "before": before[index]}]
        if len(before) != len(after):
            return [{"op": "replace", "path": path or "/", "before": before, "after": after}]
        changes = []
        for index, (left, right) in enumerate(zip(before, after)):
            changes.extend(structural_patches(left, right, f"{path}/{index}"))
        return changes
    return [] if before == after else [{"op": "replace", "path": path or "/", "before": before, "after": after}]


def apply_reseal(document: Any, handler: str, parent: Any, semantic: Any, subject_schema: dict[str, Any], aemh_schema: dict[str, Any]) -> None:
    if handler == "reseal_visibility_receipt_packet":
        packet = document
        parent.reseal_exact_object("VisibilityClosure", packet["receipt"]["visibility_closure"], subject_schema)
        parent.reseal_exact_object("PublicAuthorityReceipt", packet["receipt"], subject_schema)
        packet["packet_content_hash"] = parent.canonical_hash({"receipt_content_hash": packet["receipt"]["receipt_content_hash"], "projection_content_hash": packet["projection"]["projection_content_hash"]})
    elif handler == "reseal_subject_projection_packet":
        packet = document
        parent.reseal_exact_object("SubjectTemporalPublicProjection", packet["projection"], subject_schema)
        packet["packet_content_hash"] = parent.canonical_hash({"receipt_content_hash": packet["receipt"]["receipt_content_hash"], "projection_content_hash": packet["projection"]["projection_content_hash"]})
    elif handler == "reseal_receipt_scope_receipt_packet":
        packet = document
        parent.reseal_exact_object("PublicScopeIdentity", packet["receipt"]["scope_identity"], subject_schema)
        parent.reseal_exact_object("PublicAuthorityReceipt", packet["receipt"], subject_schema)
        packet["packet_content_hash"] = parent.canonical_hash({"receipt_content_hash": packet["receipt"]["receipt_content_hash"], "projection_content_hash": packet["projection"]["projection_content_hash"]})
    elif handler == "reseal_aemh_current_full":
        parent.reseal_aemh_packet(document["current_packet"], aemh_schema, preserve_evaluation=False)
    elif handler == "reseal_taxonomy_package":
        document["taxonomy_package"]["package_content_hash"] = semantic.object_hash(document["taxonomy_package"], "package_content_hash")
    elif handler == "reseal_severity_package":
        document["severity_package"]["package_content_hash"] = semantic.object_hash(document["severity_package"], "package_content_hash")
    elif handler == "reseal_taxonomy_evidence":
        document["taxonomy_evidence"]["evidence_content_hash"] = semantic.object_hash(document["taxonomy_evidence"], "evidence_content_hash")
    elif handler == "reseal_taxonomy_receipt":
        document["taxonomy_receipt"]["receipt_content_hash"] = semantic.object_hash(document["taxonomy_receipt"], "receipt_content_hash")
    elif handler == "reseal_candidate_authority":
        candidate = document["candidate_authority"]
        candidate["authority_content_hash"] = semantic.object_hash(candidate, "authority_content_hash")
    else:
        stop(f"unknown reseal handler: {handler}")


def parent_parser_gate(candidate: Any, spec: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    issues: list[str] = []
    selector = spec["selector"]
    env["parent"].validate_exact_object(selector["object_type"], pointer_get(candidate, selector["json_pointer"]), env["subject_schema"], selector["json_pointer"], issues)
    return [(code, spec["mutation"]["path"]) for code in issues]


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


def identity_gate(candidate: Any, spec: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    dimension = spec["selector"]["dimension"]
    bindings = {row["dimension"]: row for row in env["append_only_bindings"]["subject_identity"]["dimension_bindings"]}
    if dimension not in bindings:
        stop(f"identity selector outside accepted invariant: {dimension}")
    receipt_value = candidate["receipt"]["scope_identity"][dimension]
    projection_value = candidate["projection"]["scope_identity"][dimension]
    visibility = candidate["receipt"]["visibility_closure"]
    visibility_values = collect_identity_values(visibility, dimension, "/receipt/visibility_closure")
    if dimension == "snapshot_ref" and receipt_value not in visibility["visibility_decision_id"]:
        visibility_values.append(("/receipt/visibility_closure/visibility_decision_id", visibility["visibility_decision_id"]))
    member_values = collect_identity_values(candidate["projection"], dimension, "/projection")
    observed = [("/receipt/scope_identity", receipt_value), ("/projection/scope_identity", projection_value), *visibility_values, *member_values]
    mismatch = any(value != receipt_value for _path, value in observed[1:])
    return [(bindings[dimension]["error_code"], spec["mutation"]["path"])] if mismatch else []


def visibility_gate(candidate: Any, spec: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    issues: list[str] = []
    env["parent"].validate_visibility_and_sources(candidate["receipt"], candidate["projection"], issues)
    return [(code, spec["mutation"]["path"]) for code in issues]


def runtime_surface_gate(candidate: Any, spec: dict[str, Any], _env: dict[str, Any]) -> list[tuple[str, str]]:
    contract = candidate
    relative = spec["mutation"]["path"]
    with tempfile.TemporaryDirectory(prefix="error-replay-runtime-surface-") as directory:
        target = pathlib.Path(directory) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(spec["mutation"]["value"], encoding="utf-8")
        exact = relative in set(contract["forbidden_exact_paths"])
        pattern = any(re.fullmatch(pattern, relative) for pattern in contract["forbidden_relative_path_regexes"])
        if not target.is_file() or not (exact or pattern):
            return []
        return [("PUB_RUNTIME_TEST_SURFACE_FORBIDDEN", relative)]


def history_gate(candidate: Any, spec: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    before_packet = env["before_candidate"]["current_packet"]
    current_packet = candidate["current_packet"]
    binding = env["append_only_bindings"]["aemh_history"]
    selector = spec["selector"]
    before_threads = {thread["thread_ref"]: thread for thread in before_packet["projection"]["threads"]}
    current_threads = {thread["thread_ref"]: thread for thread in current_packet["projection"]["threads"]}
    thread_ref = selector["thread_ref"]
    eligible_threads = [
        ref for ref, thread in before_threads.items()
        if set(binding["event_kinds"]) <= {entry["event_kind"] for entry in thread["history_entries"]}
    ]
    if len(eligible_threads) != 1 or thread_ref != eligible_threads[0] or selector.get("event_kind") not in binding["event_kinds"]:
        stop("history selector outside accepted invariant/base binding")
    if thread_ref not in before_threads or thread_ref not in current_threads:
        return [(binding["error_code"], "/current_packet/projection/threads")]
    stable_fields = binding["stable_thread_fields"]
    if any(before_threads[thread_ref][field] != current_threads[thread_ref][field] for field in stable_fields):
        return [(binding["error_code"], "/current_packet/projection/threads")]
    required = [entry for entry in before_threads[thread_ref]["history_entries"] if entry["event_kind"] in binding["event_kinds"]]
    if {entry["event_kind"] for entry in required} != set(binding["event_kinds"]):
        stop("accepted base does not close the bound history event set")
    available = current_threads[thread_ref]["history_entries"]
    cursor = 0
    for expected in required:
        while cursor < len(available) and canonical_bytes(available[cursor]) != canonical_bytes(expected):
            cursor += 1
        if cursor == len(available):
            return [(binding["error_code"], "/current_packet/projection/threads/0/history_entries")]
        cursor += 1
    return []


def semantic_common_gate(candidate: Any, spec: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    package = pointer_get(candidate, spec["selector"]["json_pointer"])
    try:
        env["semantic"].validate_common_package(package, env["semantic"].RISK_PACKAGE_KEYS, "/taxonomy_package")
    except env["semantic"].SemanticError as exc:
        return [(exc.code, exc.path)]
    return []


def semantic_validator_gate(candidate: Any, spec: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    pointer = spec["selector"]["json_pointer"]
    value = pointer_get(candidate, pointer)
    gate_id = spec["gate_id"]
    functions = {
        "gate.semantic.risk_validator": env["semantic"].validate_risk_package,
        "gate.semantic.severity_validator": env["semantic"].validate_severity_package,
    }
    try:
        functions[gate_id](value)
    except env["semantic"].SemanticError as exc:
        return [(exc.code, exc.path)]
    return []


def token_evidence_gate(candidate: Any, _spec: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    try:
        env["semantic"].validate_token_evidence(candidate["taxonomy_evidence"], env["source_registry"], env["source_records"], candidate["identity_join"], "/taxonomy_evidence")
    except env["semantic"].SemanticError as exc:
        return [(exc.code, exc.path)]
    return []


def receipt_gate(candidate: Any, spec: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    selector = spec["selector"]
    try:
        env["semantic"].validate_receipt(candidate[selector["receipt_key"]], candidate[selector["package_key"]], selector["package_kind"], candidate["use_context"], env["acceptance_registry"], env["accepted_records"], "/" + selector["receipt_key"])
    except env["semantic"].SemanticError as exc:
        return [(exc.code, exc.path)]
    return []


def candidate_comparison_gate(candidate: Any, spec: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    selector = spec["selector"]
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


def manifest_gate(candidate: Any, _spec: dict[str, Any], env: dict[str, Any]) -> list[tuple[str, str]]:
    try:
        env["semantic"].validate_parent_and_manifest(candidate)
    except env["semantic"].SemanticError as exc:
        return [(exc.code, exc.path)]
    return []


GATE_DISPATCH: dict[str, Callable[[Any, dict[str, Any], dict[str, Any]], list[tuple[str, str]]]] = {
    "gate.parent.untrusted_exact_parser": parent_parser_gate,
    "gate.parent.identity_dimension": identity_gate,
    "gate.parent.visibility_source": visibility_gate,
    "gate.parent.runtime_surface": runtime_surface_gate,
    "gate.parent.aemh_history_preservation": history_gate,
    "gate.semantic.common_parser": semantic_common_gate,
    "gate.semantic.risk_validator": semantic_validator_gate,
    "gate.semantic.severity_validator": semantic_validator_gate,
    "gate.semantic.token_evidence": token_evidence_gate,
    "gate.semantic.receipt": receipt_gate,
    "gate.semantic.candidate_comparison": candidate_comparison_gate,
    "gate.semantic.manifest": manifest_gate,
}


def replay_delta(base_registry: dict[str, Any], gates: dict[str, Any], priorities: dict[str, int], origins: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    parent = load_module("tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py", "delta_parent_gate_generator")
    semantic = load_module("tools/verify_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py", "delta_semantic_gate_generator")
    subject_schema = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh_schema = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    semantic_manifest = read_json(SEMANTIC_DIR / "manifest.json")
    source_registry = semantic_manifest["synthetic_typed_source_record_registry"]
    acceptance_registry = semantic_manifest["synthetic_policy_acceptance_registry"]
    env = {
        "parent": parent,
        "semantic": semantic,
        "subject_schema": subject_schema,
        "aemh_schema": aemh_schema,
        "source_registry": source_registry,
        "acceptance_registry": acceptance_registry,
        "source_records": semantic.validate_source_registry(source_registry),
        "accepted_records": semantic.validate_acceptance_registry(acceptance_registry),
        "append_only_bindings": accepted_append_only_bindings(priorities),
    }
    bases, _authority_inputs = construct_bases()
    base_rows = {row["base_input_ref"]: row for row in base_registry["rows"]}
    gate_rows = {row["gate_id"]: row for row in gates["rows"]}
    rows = []
    gate_observations = []
    for spec in challenge_specs():
        candidate = copy.deepcopy(bases[spec["base"]])
        before = copy.deepcopy(candidate)
        apply_primary(candidate, spec["mutation"])
        primary_patches = [{"op": "create_temp_file", "path": spec["mutation"]["path"]}] if spec["mutation"]["op"] == "create_temp_file" else structural_patches(before, candidate)
        if len(primary_patches) != 1:
            stop(f"primary structural diff is not one operation: {spec['case_id']}:{primary_patches}")
        after_primary = copy.deepcopy(candidate)
        for handler in spec["reseal"]:
            apply_reseal(candidate, handler, parent, semantic, subject_schema, aemh_schema)
        reseal_patches = structural_patches(after_primary, candidate)
        env["before_candidate"] = before
        gate = gate_rows[spec["gate_id"]]
        actual = GATE_DISPATCH[spec["gate_id"]](candidate, spec, env)
        if len(actual) != 1:
            stop(f"delta gate must emit exactly one issue: {spec['case_id']}:{actual}")
        actual_code, actual_path = actual[0]
        mismatches = [actual_code != spec["error_code"], actual_code not in gate["permitted_error_codes"]]
        if any(mismatches):
            stop(f"delta gate wrong code: {spec['case_id']}:{actual_code}")
        issue = {
            "code": actual_code,
            "path": actual_path,
            "message": f"{origins[actual_code]}:{actual_code}:fail_closed",
            "origin": origins[actual_code],
            "priority": priorities[actual_code],
        }
        base_row = base_rows[spec["base"]]
        identity_payload = {
            "base_input_content_identity": base_row["canonical_input_identity"],
            "gate_id": spec["gate_id"],
            "instance_selector": spec["selector"],
            "single_mutation": spec["mutation"],
            "ordered_reseal": spec["reseal"],
        }
        rows.append({
            "case_id": spec["case_id"],
            "surface": spec["surface"],
            "error_code": spec["error_code"],
            "accepted_priority": priorities[spec["error_code"]],
            "entrypoint_class": gate["entrypoint_class"],
            "gate_id": spec["gate_id"],
            "base_input_ref": spec["base"],
            "base_input_content_identity": base_row["canonical_input_identity"],
            "constructor_id": base_row["constructor_id"],
            "instance_selector": spec["selector"],
            "single_mutation": spec["mutation"],
            "ordered_reseal": spec["reseal"],
            "observed_ordered_issues": [issue],
            "forbidden_output": spec["forbidden"],
            "trace_identity": digest(identity_payload),
        })
        gate_observations.append({"gate_id": spec["gate_id"], "actual_code": actual_code, "primary_patch": primary_patches[0], "reseal_patch_count": len(reseal_patches), "packet_or_authority_emitted": False})
    if len(rows) != 22 or len({row["error_code"] for row in rows}) != 22 or len({row["trace_identity"] for row in rows}) != 22:
        stop("22/22/22 delta registry closure")
    return {"schema": "error-replay-challenge-registry-v0.1", "schema_version": SCHEMA_VERSION, "rows": rows}, {"challenge_count": 22, "gate_observations": gate_observations}


def schema_artifact() -> dict[str, Any]:
    return {
        "schema": "public-authority-error-replay-coverage-delta-schema-v0.1",
        "schema_version": SCHEMA_VERSION,
        "authority_scope": "synthetic_test_only",
        "exact_root_keys": {
            "base_input_registry": ["schema", "schema_version", "rows"],
            "gate_registry": ["schema", "schema_version", "rows"],
            "challenge_registry": ["schema", "schema_version", "rows"],
        },
        "exact_row_keys": {
            "base_input": sorted(BASE_KEYS),
            "gate": sorted(GATE_KEYS),
            "challenge": sorted(CHALLENGE_KEYS),
        },
        "entrypoint_classes": ["untrusted_schema_parser", "typed_validator", "constructor_candidate_comparison", "artifact_governance"],
        "trace_identity_includes": ["base_input_content_identity", "gate_id", "instance_selector", "single_mutation", "ordered_reseal"],
        "trace_identity_excludes": ["case_id", "surface", "error_code", "accepted_priority", "observed_ordered_issues", "forbidden_output", "labels"],
        "actual_issue_order": ["accepted_priority", "path", "code", "origin", "message"],
        "single_primary_mutation_required": True,
        "candidate_packet_or_authority_forbidden_on_issue": True,
    }


def context_markdown(pre: dict[str, Any], delta: dict[str, Any]) -> bytes:
    text = f"""# R5-S5 public authority error replay coverage delta v0.1 context

Date: 2026-08-21
Status: `candidate_unaccepted`
Authority scope: `synthetic_test_only`

This append-only delta executed the accepted parent, semantic, temporal-v0.1 and temporal-v0.2 challenge entrypoints before authoring. Their actual emitted union is {pre['pre_delta_emitted_union_count']}/{pre['error_universe_count']}; the exact missing set is the 22 rows in the challenge registry. The delta executed {delta['challenge_count']} real parser, validator, constructor-comparison or isolated filesystem gates and emitted one existing code per row. No code, priority, invariant, clinical rule, fallback or production behavior was added or changed.

The identity and AEMH history replay gates derive dimensions, event kinds, stable-thread selectors, existing codes and priorities from raw-pinned accepted schema invariants, parent error registries and normalized parent-validator ASTs. Every accepted authority root is independently raw-pinned before nested fields are read, and each protected scalar is bound four ways to its immutable SHA, actual path bytes, accepted temporal field and delta duplicate. Negative implementation histories use exact frozen path/SHA maps and an exact rejection-record path/hash gate; candidate content hashes cannot replace those raw-byte checks.

The blocked implementation-contract v0.4 remains immutable negative evidence. No producer, runtime, test, evidence, acceptance, S5, frontend, medical-writing, real-project, model, service or port-8911 action is authorized. Only a fresh isolated reviewer may accept this exact manifest SHA.
"""
    return text.encode()


def review_markdown(pre: dict[str, Any], delta: dict[str, Any]) -> bytes:
    text = f"""# R5-S5 public authority error replay coverage delta v0.1 author review

Disposition: `CANDIDATE_FOR_FRESH_ISOLATED_REVIEW` — this worker does not accept it.

- Accepted entrypoints executed: parent {pre['accepted_entrypoints']['parent']['executed']}, semantic {pre['accepted_entrypoints']['semantic']['executed']}, temporal v0.1 {pre['accepted_entrypoints']['temporal_v01']['executed']}, temporal v0.2 {pre['accepted_entrypoints']['temporal_v02']['executed']}.
- Pre-delta actual union: {pre['pre_delta_emitted_union_count']}/{pre['error_universe_count']}.
- Delta replay: {delta['challenge_count']}/22 gates, aliases 0, new/renamed/reordered codes 0.
- Post-union: 192/192.
- Parent, semantic and both temporal authority roots plus their acceptance records are independently raw-pinned before nested fields are read; protected scalars also match their actual-path raw bytes and both duplicate planes.
- Subject identity and AEMH append-only gates are reconstructed from accepted invariant/error/AST bindings; no gate-local dimension/event-to-code map is authoritative.
- Every v0.1/v0.2/v0.3 negative snapshot path and the v0.2 rejection record are checked against frozen hard maps and actual raw bytes.
- Runtime governance uses an actual forbidden path in `TemporaryDirectory`; no workspace producer/runtime/test/evidence path is created.

Next action: a fresh isolated reviewer must independently rerun all accepted entrypoints, all 22 gates, structural/reseal and poisoning attacks, optimization/hash-seed/determinism/Ruff/pin/absence/8911 checks against one immutable manifest SHA. Only that reviewer may return the acceptance token named in the task contract.
"""
    return text.encode()


def manifest_artifact(outputs: dict[str, bytes], pre: dict[str, Any], delta: dict[str, Any], base_registry: dict[str, Any], gates: dict[str, Any], challenges: dict[str, Any]) -> dict[str, Any]:
    temporal_v02 = load_pinned_temporal_v02()
    temporal_v02_pins = dict(temporal_v02["file_raw_sha256"])
    temporal_v02_pins[f"{TEMPORAL_V02_DIR.relative_to(ROOT)}/manifest.json"] = raw_sha(TEMPORAL_V02_DIR / "manifest.json")
    protected = temporal_v02["protected_accepted_pins"]
    manifest = {
        "schema": "public-authority-error-replay-coverage-delta-manifest-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "status": "candidate_unaccepted",
        "authority_scope": "synthetic_test_only",
        "pre_delta_executable_error_count": 170,
        "delta_challenge_count": 22,
        "post_union_error_count": 192,
        "new_error_code_count": 0,
        "renamed_error_code_count": 0,
        "reordered_error_code_count": 0,
        "clinical_truth_changed": False,
        "parent_bytes_changed": False,
        "semantic_bytes_changed": False,
        "temporal_bytes_changed": False,
        "implementation_v04_changed": False,
        "producer_executed": False,
        "port_8911_must_be_stopped": True,
        "self_acceptance": False,
        "exact_nine_paths": list(EXACT_PATHS),
        "exact_artifact_paths": [f"{OUT_REL}/{name}" for name in ("schema.json", "base_input_registry.json", "gate_registry.json", "challenge_registry.json", "manifest.json")],
        "file_raw_sha256": {relative: hashlib.sha256(content).hexdigest() for relative, content in sorted(outputs.items()) if relative != f"{OUT_REL}/manifest.json"},
        "authority_chain_pins": dict(EXTERNAL_ROOT_PIN_ITEMS),
        "temporal_v02_nine_file_pins": dict(sorted(temporal_v02_pins.items())),
        "typed_source_pins": temporal_v02["typed_source_pins"],
        "protected_accepted_pins": protected,
        "rejected_v01_v02_negative_evidence_only": temporal_v02["rejected_v01_v02_negative_evidence_only"],
        "rejected_v03_negative_evidence_only": temporal_v02["rejected_v03_negative_evidence_only"],
        "blocked_v04_nine_file_pins": BLOCKED_V04_PINS,
        "accepted_append_only_gate_bindings": accepted_append_only_bindings({code: index for index, code in enumerate(accepted_priority()[0], 1)}),
        "pre_delta_execution_evidence": pre,
        "delta_execution_evidence": delta,
        "base_input_registry_content_hash": digest(base_registry),
        "gate_registry_content_hash": digest(gates),
        "challenge_registry_content_hash": digest(challenges),
        "missing_error_codes": list(MISSING_CODES),
        "required_attack_families": [
            "expected_poisoning", "case_error_sentinel_branching", "gate_substitution", "parser_normalization",
            "multi_mutation_smuggling", "stale_reseal", "excess_reseal", "local_mirror_oracle", "dead_code_replay",
            "identity_history_overreach", "candidate_self_equality", "fake_governance", "priority_drift",
            "accepted_negative_protection_pin_drift", "duplicate_pin_disagreement", "nine_path_scope",
            "producer_s5_bytecode_absence", "port_8911_stopped",
        ],
        "manifest_hash_recipe": "sha256(canonical JSON of all fields except manifest_content_hash)",
    }
    manifest["manifest_content_hash"] = digest(manifest)
    return manifest


def render() -> dict[str, bytes]:
    temporal_v02 = load_pinned_temporal_v02()
    verify_pin_map(BLOCKED_V04_PINS, "blocked v0.4")
    verify_negative_history(temporal_v02["rejected_v01_v02_negative_evidence_only"], temporal_v02["rejected_v03_negative_evidence_only"])
    pre, emitted, _order, priorities, origins = pre_delta_execution()
    base_registry = base_input_registry()
    gates = gate_registry()
    challenges, delta = replay_delta(base_registry, gates, priorities, origins)
    delta_codes = {row["error_code"] for row in challenges["rows"]}
    if delta_codes != set(MISSING_CODES) or len(emitted | delta_codes) != 192:
        stop("170+22=192 executable union")
    if [row["error_code"] for row in sorted(challenges["rows"], key=lambda item: item["accepted_priority"])] != list(MISSING_CODES):
        stop("accepted priority order for missing codes")
    schema = schema_artifact()
    preliminary = {
        CONTEXT_REL: context_markdown(pre, delta),
        REVIEW_REL: review_markdown(pre, delta),
        f"{OUT_REL}/schema.json": pretty(schema),
        f"{OUT_REL}/base_input_registry.json": pretty(base_registry),
        f"{OUT_REL}/gate_registry.json": pretty(gates),
        f"{OUT_REL}/challenge_registry.json": pretty(challenges),
        GENERATOR_REL: (ROOT / GENERATOR_REL).read_bytes(),
        VERIFIER_REL: (ROOT / VERIFIER_REL).read_bytes(),
    }
    manifest = manifest_artifact(preliminary, pre, delta, base_registry, gates, challenges)
    preliminary[f"{OUT_REL}/manifest.json"] = pretty(manifest)
    outputs = {relative: preliminary[relative] for relative in EXACT_PATHS}
    if tuple(outputs) != tuple(EXACT_PATHS):
        stop("exact nine output order/scope")
    return outputs


def write_or_check(outputs: dict[str, bytes], output_root: pathlib.Path, check: bool) -> None:
    isolated = output_root.resolve() != ROOT.resolve()
    for relative, content in outputs.items():
        target = output_root / relative
        if check:
            if not target.is_file() or target.read_bytes() != content:
                stop(f"generated drift: {relative}")
            continue
        if not isolated and relative in {GENERATOR_REL, VERIFIER_REL}:
            if target.read_bytes() != content:
                stop(f"tool self-byte drift: {relative}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output-root", type=pathlib.Path, default=ROOT)
    args = parser.parse_args()
    outputs = render()
    write_or_check(outputs, args.output_root, args.check)
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write", "pre_delta": "170/192", "delta": "22/22", "post_union": "192/192", "paths": 9, "producer_executed": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
