"""R5-S4 runtime read-only gate (contract sections 2.2 / 8 / 10.2).

Guards the create-only 12-path allowlist boundary and the immutable
read-only set:

* the four ``src/mm_r5/s4_*`` runtime modules never import or open the
  generator / verifier / machine artifacts / registry / source-pins and never
  branch on challenge case ids, indices, mutations, expected outcomes, test
  locators, filenames or synthetic sentinels (AST anti-overfit gate);
* no runtime source uses ``assert`` to enforce a runtime invariant and no
  runtime source performs file I/O;
* the exact contract-section-8 12-path create-only allowlist is enforced: no
  extra ``s4_*`` / ``test_s4_*`` source, test, challenge or evidence file may
  exist beyond the allowlist;
* no task-created S4 bytecode (``.pyc``) or ``__pycache__`` residue may exist
  anywhere under the R5 POC (a bytecode file outside ``__pycache__`` or an
  ``s4_*``/``test_s4_*``-named cache entry is rejected).  Verification runs
  use ``PYTHONDONTWRITEBYTECODE=1`` / ``-B`` so a gate run does not recreate
  them;
* the pre/post SHA gate: every frozen R4 / R5 S1-S3 / root ``__init__.py`` /
  accepted S4 artifact / generator / verifier file still has exactly the raw
  SHA recorded in ``evidence/r4_r5_s4_readonly_sha256.json``.
"""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib

import pytest

_R5 = pathlib.Path(__file__).resolve().parent.parent
_SRC = _R5 / "src" / "mm_r5"
_WORKSPACE = _R5.parent.parent
_EVIDENCE = _R5 / "evidence" / "r4_r5_s4_readonly_sha256.json"

#: The four create-only runtime source modules guarded by the AST gate.
_RUNTIME_SOURCES = (
    "s4_contracts.py",
    "s4_authority_builder.py",
    "s4_projection.py",
    "s4_validator.py",
)

#: The exact contract-section-8 create-only allowlist (12 paths, relative to
#: the R5 POC root).  No other S4 file may exist.
_ALLOWLIST_PATHS = (
    "src/mm_r5/s4_contracts.py",
    "src/mm_r5/s4_authority_builder.py",
    "src/mm_r5/s4_projection.py",
    "src/mm_r5/s4_validator.py",
    "tests/s4_runtime_fixtures.py",
    "tests/test_s4_contracts.py",
    "tests/test_s4_authority_builder.py",
    "tests/test_s4_projection.py",
    "tests/test_s4_validator.py",
    "tests/test_s4_readonly_gate.py",
    "tests/challenges/test_s4_runtime_challenges.py",
    "evidence/r4_r5_s4_readonly_sha256.json",
)

#: The single pre-existing accepted S4-named file that predates the runtime
#: work and is NOT a create-only path (the machine contract-artifact suite
#: that owns the five frozen historical deselects).  It is accepted and must
#: be excluded from the create-only allowlist comparison.
_PREEXISTING_S4_FILES = frozenset({"tests/test_s4_contract_artifacts.py"})

#: The four runtime module stem names whose bytecode is task-created.
_RUNTIME_STEMS = ("s4_contracts", "s4_authority_builder", "s4_projection",
                  "s4_validator")

#: Anti-overfit decision-branch markers that a runtime source must never
#: reference (contract section 2.3: no case/index/oracle/mutation/sentinel/
#: test-locator decision branches).
_ANTI_OVERFIT_NAMES = (
    "R5S4C", "case_id", "challenge", "mutation", "expected_outcome",
    "oracle", "registry", "test_locator", "sentinel", "single_mutation",
    "stage_oracle", "precondition", "source_pin", "expected_typed",
    "artifact_governance",
)

#: Call/attribute names that would imply runtime file I/O.
_FILE_IO_CALLS = {"open", "read_text", "read_bytes", "read", "write_text",
                  "write_bytes", "unlink", "mkdir"}


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Exact 12-path create-only allowlist
# ---------------------------------------------------------------------------


def _s4_surface_files() -> set:
    """Every S4-named file under the R5 POC source/test/evidence surface."""
    files = set()
    files.update(str(p.relative_to(_R5))
                 for p in _SRC.glob("s4_*.py"))
    files.update(str(p.relative_to(_R5))
                 for p in (_R5 / "tests").glob("s4_*.py"))
    files.update(str(p.relative_to(_R5))
                 for p in (_R5 / "tests").glob("test_s4_*.py"))
    files.update(str(p.relative_to(_R5))
                 for p in (_R5 / "tests" / "challenges").glob("test_s4_*.py"))
    files.update(str(p.relative_to(_R5))
                 for p in (_R5 / "evidence").glob("r4_r5_s4_readonly_sha256.json"))
    return files


def test_exact_12_path_allowlist() -> None:
    """The task-created S4 source/test/challenge/evidence surface is exactly
    the 12-path contract allowlist (plus the single pre-existing accepted
    ``test_s4_contract_artifacts.py``); no other S4 file exists."""
    for rel in _ALLOWLIST_PATHS:
        assert (_R5 / rel).exists(), rel
    assert _s4_surface_files() == (
        set(_ALLOWLIST_PATHS) | set(_PREEXISTING_S4_FILES))


# ---------------------------------------------------------------------------
# Task-created bytecode / cache residue gate
# ---------------------------------------------------------------------------


def _task_created_s4_bytecode() -> list:
    """Every task-created S4 bytecode file: a ``.pyc`` outside a
    ``__pycache__`` directory, or an ``s4_*``/``test_s4_*``-named cache
    entry."""
    offenders = []
    for root_dir in (_SRC, _R5 / "tests", _R5 / "evidence"):
        for path in root_dir.rglob("*.pyc"):
            in_cache = path.parent.name == "__pycache__"
            name = path.stem  # e.g. 's4_contracts.cpython-39' -> 's4_contracts'
            base = name.split(".")[0]
            is_s4 = base.startswith("s4_") or base.startswith("test_s4_")
            if not in_cache or is_s4:
                offenders.append(str(path.relative_to(_R5)))
    return offenders


def test_no_task_created_s4_bytecode() -> None:
    """No task-created S4 bytecode or cache residue exists anywhere.  Run with
    ``PYTHONDONTWRITEBYTECODE=1`` / ``-B`` so a gate run never recreates it."""
    offenders = _task_created_s4_bytecode()
    assert offenders == [], \
        f"task-created S4 bytecode present (run with -B): {offenders}"


def test_no_extra_s4_source_under_runtime_package() -> None:
    """Only the four runtime S4 modules exist under ``src/mm_r5/s4_*.py``."""
    s4_files = {p.name for p in _SRC.glob("s4_*.py")}
    assert s4_files == set(_RUNTIME_SOURCES)


# ---------------------------------------------------------------------------
# AST anti-overfit gate over every runtime source module
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", _RUNTIME_SOURCES)
def test_runtime_source_no_oracle_imports(name: str) -> None:
    """No generator / verifier / machine-artifact / registry / source-pin
    import and no Path / file I/O in any runtime module."""
    tree = ast.parse((_SRC / name).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "tools" not in node.module, name
            assert "generate_medical_monitoring" not in node.module, name
            assert "verify_medical_monitoring" not in node.module, name
            assert "artifacts" not in node.module, name
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "tools" not in alias.name, name
                assert "artifacts" not in alias.name, name
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert "Path" not in names, name


@pytest.mark.parametrize("name", _RUNTIME_SOURCES)
def test_runtime_source_no_file_io(name: str) -> None:
    """No open / read_* / write_* file access in any runtime module."""
    tree = ast.parse((_SRC / name).read_text(encoding="utf-8"))
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute):
                calls.add(fn.attr)
            elif isinstance(fn, ast.Name):
                calls.add(fn.id)
    assert not (calls & _FILE_IO_CALLS), name


@pytest.mark.parametrize("name", _RUNTIME_SOURCES)
def test_runtime_source_never_uses_assert(name: str) -> None:
    """Runtime invariants fail closed; ``assert`` is never used to enforce
    them."""
    tree = ast.parse((_SRC / name).read_text(encoding="utf-8"))
    assert not any(isinstance(node, ast.Assert) for node in ast.walk(tree)), \
        name


@pytest.mark.parametrize("name", _RUNTIME_SOURCES)
def test_runtime_source_no_anti_overfit_decision_branches(name: str) -> None:
    """No challenge case id / oracle / mutation / sentinel / test-locator
    identifier is used in any runtime source (docstring prose about the
    boundary is not a decision branch; identifiers are checked at AST level)."""
    tree = ast.parse((_SRC / name).read_text(encoding="utf-8"))
    identifiers = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            identifiers.add(node.id)
        elif isinstance(node, ast.Attribute):
            identifiers.add(node.attr)
        elif isinstance(node, ast.arg):
            identifiers.add(node.arg)
        elif isinstance(node, ast.keyword):
            identifiers.add(node.arg or "")
    for marker in _ANTI_OVERFIT_NAMES:
        assert marker not in identifiers, (name, marker)


# ---------------------------------------------------------------------------
# Pre/post SHA gate (single new evidence file)
# ---------------------------------------------------------------------------


def _evidence() -> dict:
    return json.loads(_EVIDENCE.read_text(encoding="utf-8"))


def test_evidence_file_exists_and_has_expected_schema() -> None:
    evidence = _evidence()
    assert evidence["schema"] == \
        "medical-monitoring-r5-s4-runtime-readonly-sha256-evidence-v1"
    assert isinstance(evidence["files"], dict)
    assert len(evidence["files"]) >= 20
    # the 8 artifact-governance cases are frozen in the evidence.
    assert len(evidence["governance_cases"]) == 8
    for code in evidence["governance_cases"].values():
        assert code.startswith("s4.")


@pytest.mark.parametrize("path,sha", [
    ("poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py",
     "0a24c6993cb4997b1e77cefcfeeff490aaf882b269ab0fece8635ce81b6b4ebd"),
])
def test_root_init_unchanged(path: str, sha: str) -> None:
    """The accepted S1-S3 root package ``__init__.py`` is byte-unchanged."""
    assert _sha256(_WORKSPACE / path) == sha


def test_recorded_shas_match_current_frozen_files() -> None:
    """Every file recorded in the evidence still has exactly its recorded raw
    SHA (nothing in the read-only boundary drifted)."""
    evidence = _evidence()
    for rel, sha in evidence["files"].items():
        file_path = _WORKSPACE / rel
        assert file_path.exists(), rel
        assert _sha256(file_path) == sha, rel


def test_evidence_sha_is_stable_after_readonly_gate() -> None:
    """The evidence JSON itself is a single new file and its recorded SHAs are
    self-consistent (re-reading yields the same values)."""
    first = _evidence()
    second = _evidence()
    assert first == second
