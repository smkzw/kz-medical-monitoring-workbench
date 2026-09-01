"""Read-only, isolation and exact-path gates for the producer stage."""

from __future__ import annotations

import ast
import hashlib
import json
import socket
from pathlib import Path

import pytest

from mm_r5.aemh_match_history_public import build_aemh_match_history_authority
from mm_r5.subject_temporal_public import build_subject_temporal_authority
from public_authority_runtime_fixtures import (
    build_aemh_authority_bundle,
    build_subject_authority_bundle,
)


_R5 = Path(__file__).resolve().parent.parent
_WORKSPACE = _R5.parent.parent
_V042 = _WORKSPACE / "artifacts" / (
    "medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2"
)
_EVIDENCE = _R5 / "evidence" / "r4_r5_s5_public_authority_readonly_sha256.json"

_EXPECTED_RELATIVE = {
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
}
_RUNTIME_SOURCES = (
    "public_authority_common.py",
    "subject_temporal_public.py",
    "aemh_match_history_public.py",
)
_FORBIDDEN_CALLS = {
    "open",
    "read",
    "read_text",
    "read_bytes",
    "write",
    "write_text",
    "write_bytes",
    "unlink",
    "mkdir",
    "connect",
    "create_connection",
    "run",
    "Popen",
}
_FORBIDDEN_IMPORTS = {
    "os",
    "pathlib",
    "socket",
    "subprocess",
    "requests",
    "urllib",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence() -> dict:
    return json.loads(_EVIDENCE.read_text(encoding="utf-8"))


def _surface_paths() -> set[str]:
    paths = set(
        path for path in (_R5 / "src/mm_r5").glob("*.py")
        if path.name in {"public_authority_common.py", "subject_temporal_public.py", "aemh_match_history_public.py"}
    )
    paths.update(
        path for path in (_R5 / "tests").glob("*.py")
        if "public_authority" in path.name
        or path.name in {"test_subject_temporal_public.py", "test_aemh_match_history_public.py"}
    )
    paths.update((_R5 / "tests" / "challenges").glob("*public_authority*.py"))
    paths.add(_EVIDENCE)
    return {str(path.relative_to(_WORKSPACE)) for path in paths if path.exists()}


def test_exact_eleven_path_allowlist_matches_accepted_contract() -> None:
    contract = json.loads(
        (_V042 / "future_producer_contract.json").read_text(encoding="utf-8")
    )
    expected = set(contract["create_only_paths"])
    assert expected == _EXPECTED_RELATIVE
    assert all((_WORKSPACE / path).exists() for path in expected)
    assert _surface_paths() == expected


@pytest.mark.parametrize("name", _RUNTIME_SOURCES)
def test_runtime_source_is_stdlib_first_and_side_effect_free(name: str) -> None:
    tree = ast.parse(
        (_R5 / "src/mm_r5" / name).read_text(encoding="utf-8"),
        filename=name,
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".", 1)[0] not in _FORBIDDEN_IMPORTS for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".", 1)[0] not in _FORBIDDEN_IMPORTS
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            calls.add(node.func.id if isinstance(node.func, ast.Name) else node.func.attr)
    assert not calls & _FORBIDDEN_CALLS
    assert not any(isinstance(node, ast.Assert) for node in ast.walk(tree))


def test_runtime_sources_do_not_expose_a_previous_packet_builder_input() -> None:
    for name in _RUNTIME_SOURCES[1:]:
        source = (_R5 / "src/mm_r5" / name).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=name)
        builders = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("build_")
        ]
        assert builders, name
        for builder in builders:
            assert len(builder.args.args) == 1, (name, builder.name)
            assert builder.args.args[0].arg == "source"


def test_pinned_readonly_files_and_protected_boundary() -> None:
    evidence = _evidence()
    assert evidence["schema"] == (
        "medical-monitoring-r5-s5-public-authority-readonly-sha256-evidence-v1"
    )
    assert evidence["accepted_manifest_content_hash"] == (
        "5483374f9d4600bc9dd302069249d80599cb281fb5ce05f06e25a65232c83c1e"
    )
    assert evidence["protected_boundaries"] == {
        "medical_writing_file_count": 542,
        "medical_writing_inventory_sha256": (
            "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca"
        ),
        "port_8911": "stopped",
    }
    for relative, expected_sha in evidence["files"].items():
        path = _WORKSPACE / relative
        assert path.exists(), relative
        assert _sha256(path) == expected_sha, relative


def test_builder_execution_has_no_pinned_file_side_effects() -> None:
    evidence = _evidence()
    paths = {
        _WORKSPACE / relative: expected_sha
        for relative, expected_sha in evidence["files"].items()
    }
    before = {path: (path.stat().st_mtime_ns, _sha256(path)) for path in paths}
    build_subject_temporal_authority(build_subject_authority_bundle())
    build_aemh_match_history_authority(build_aemh_authority_bundle())
    after = {path: (path.stat().st_mtime_ns, _sha256(path)) for path in paths}
    assert after == before


def test_port_8911_remains_stopped() -> None:
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.settimeout(0.2)
    try:
        assert connection.connect_ex(("127.0.0.1", 8911)) != 0
    finally:
        connection.close()
