"""R8 G2 synthetic canonical digest/manifest/replay tests.

These tests use only in-memory synthetic values and temporary JSON. They never
read a project root, call a model, start a service, or bind a product port.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest


WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = WORKBENCH_ROOT / "deploy" / "medical_monitoring_local"
if str(DEPLOY_DIR) not in sys.path:
    sys.path.insert(0, str(DEPLOY_DIR))

import synthetic_manifest as sm  # noqa: E402
import source_access_profile as sap  # noqa: E402
import synthetic_lifecycle as sl  # noqa: E402


REF_PROJECT = "opaque-project:synthetic-g2"
REF_ROOT = "opaque-root:synthetic-g2"
REF_OUTPUT = "opaque-output:synthetic-g2"
REF_ADMISSION = "opaque-admission:synthetic-g2"
REF_RUN = "opaque-run:synthetic-run"
BINDING = "sha256:" + hashlib.sha256(b"synthetic-binding").hexdigest()
SCOPE = "sha256:" + hashlib.sha256(b"synthetic-scope").hexdigest()


def _ref(seed: str) -> str:
    return "sha256:" + hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _entry(path: str, seed: str) -> Dict[str, Any]:
    return {
        "relative_path": path,
        "entry_kind": "regular_file",
        "size_bytes": len(seed),
        "mtime_ns": 1,
        "content_hash": _ref("content:" + seed),
        "snapshot_role": "supporting",
        "read_status": "read",
        "evidence_ids": ["evidence:" + seed],
    }


def _source_entries(order: str = "normal") -> Dict[str, Any]:
    entries = [_entry("docs/b.txt", "b"), _entry("docs/a.txt", "a")]
    if order == "reverse":
        entries.reverse()
    return {
        "A": {"snapshot_id": "A", "entries": entries},
        "B": {"snapshot_id": "B", "entries": list(entries)},
    }


def _source() -> Dict[str, Any]:
    access = sap.run_synthetic_source_access_profile()
    return sm.build_source_manifest(
        contract_ref={"id": "r8-g0-synthetic", "version": "0.1"},
        binding_digest=BINDING,
        project_ref=REF_PROJECT,
        source_root_ref=REF_ROOT,
        output_root_ref=REF_OUTPUT,
        admission_id=REF_ADMISSION,
        source_scope_spec_digest=SCOPE,
        snapshots=_source_entries(),
        policy={"read_only": True, "scope": "synthetic"},
        toolchain={"python": "stdlib"},
        role_availability={
            "supporting": {"required": True, "available": True},
            "protocol": {"required": False, "available": False},
        },
        duplicates_conflicts={"duplicates": [], "conflicts": []},
        stability={"status": "stable", "snapshot_compare": "equal"},
        zero_write={"status": access["status"], "evidence": access},
        independent_verification={"status": "verified", "replayed": True},
        status="evaluable",
    )


def _artifacts() -> List[Dict[str, Any]]:
    return [
        {
            "artifact_id": stage,
            "sha256": _ref("artifact:" + stage),
            "media_type": "application/json",
            "length_bytes": index + 1,
            "stage": stage,
            "trusted": True,
        }
        for index, stage in enumerate(
            ("raw_output", "envelope", "parsed_output", "validation", "adjudication", "disposition")
        )
    ]


def _lineage_nodes() -> List[Dict[str, str]]:
    return [
        {
            "stage": stage,
            "artifact_id": stage,
            "sha256": _ref("artifact:" + stage),
        }
        for stage in (
            "raw_output",
            "envelope",
            "parsed_output",
            "validation",
            "adjudication",
            "disposition",
        )
    ]


def _output_kwargs() -> Dict[str, Any]:
    source = _source()
    return {
        "contract_ref": {"id": "r8-g0-synthetic", "version": "0.1"},
        "project_ref": REF_PROJECT,
        "admission_id": REF_ADMISSION,
        "run_ref": REF_RUN,
        "binding_digest": BINDING,
        "source_manifest_digest": source["manifest_digest"],
        "source_access_profile_digest": source["zero_write"]["profile_digest"],
        "input_digest": _ref("input"),
        "prompt_frame_digest": _ref("prompt-frame"),
        "schema_digest": _ref("schema"),
        "execution_profile_digest": _ref("execution-profile"),
        "output_root_ref": REF_OUTPUT,
        "artifacts": _artifacts(),
        "lineage": _lineage_nodes(),
    }


def test_canonical_json_is_nfc_sorted_and_rejects_ambiguous_keys() -> None:
    composed = "é"
    decomposed = "e\u0301"
    assert sm.canonical_json_bytes({"b": 1, "a": composed}) == sm.canonical_json_bytes(
        {"a": decomposed, "b": 1}
    )
    with pytest.raises(TypeError, match="colliding"):
        sm.canonical_json_bytes({composed: 1, decomposed: 2})


def test_canonical_digest_matches_sha256_of_emitted_bytes() -> None:
    value = {"z": ["二", 1], "a": {"n": None}}
    expected = hashlib.sha256(sm.canonical_json_bytes(value)).hexdigest()
    assert sm.canonical_digest(value) == expected
    assert sm.digest_ref(value) == "sha256:" + expected


def test_all_g2_modules_share_identical_canonical_bytes() -> None:
    value = {"negative_zero": -0.0, "text": "e\u0301", "nested": [{"b": 2, "a": 1}]}
    expected = sm.canonical_json_bytes(value)
    assert expected == sap.canonical_json_bytes(value)
    assert expected == sl.canonical_json_bytes(value)
    assert b'"negative_zero":0.0' in expected

def test_named_digest_rejects_undeclared_fields() -> None:
    with pytest.raises(sm.ManifestError, match="unknown_fields"):
        sm.digest_named("raw", {"artifact_id": "raw", "unexpected": True})


def test_digest_spec_table_covers_contract_named_inputs() -> None:
    required = {
        "contract",
        "binding",
        "source_manifest",
        "input",
        "unit_set",
        "prompt_frame",
        "execution_profile",
        "raw",
        "parsed",
        "coverage",
        "source_anchors",
        "validation",
        "output_manifest",
    }
    names = {row["name"] for row in sm.DIGEST_SPEC_TABLE}
    assert names == required
    assert all(row["hash_algorithm"] == "sha256" for row in sm.DIGEST_SPEC_TABLE)
    assert all(row["serializer"]["version"] == "1" for row in sm.DIGEST_SPEC_TABLE)

def test_digest_specification_has_stable_self_digest() -> None:
    assert sm.CANONICAL_DIGEST_SPEC_DIGEST == sm.digest_ref(sm.CANONICAL_DIGEST_SPEC)
    assert sm.CANONICAL_DIGEST_SPEC_DIGEST.startswith("sha256:")


def test_named_unit_and_source_digests_sort_declared_arrays() -> None:
    units_a = {"unit_set_id": "u", "units": [{"unit_id": "b"}, {"unit_id": "a"}]}
    units_b = {"unit_set_id": "u", "units": [{"unit_id": "a"}, {"unit_id": "b"}]}
    assert sm.digest_named("unit_set", units_a) == sm.digest_named("unit_set", units_b)
    source_a = sm.build_source_manifest(
        **{
            **{
                "contract_ref": {"id": "r8-g0-synthetic", "version": "0.1"},
                "binding_digest": BINDING,
                "project_ref": REF_PROJECT,
                "source_root_ref": REF_ROOT,
                "output_root_ref": REF_OUTPUT,
                "admission_id": REF_ADMISSION,
                "source_scope_spec_digest": SCOPE,
            },
            "snapshots": _source_entries("normal"),
        }
    )
    source_b = sm.build_source_manifest(
        **{
            **{
                "contract_ref": {"id": "r8-g0-synthetic", "version": "0.1"},
                "binding_digest": BINDING,
                "project_ref": REF_PROJECT,
                "source_root_ref": REF_ROOT,
                "output_root_ref": REF_OUTPUT,
                "admission_id": REF_ADMISSION,
                "source_scope_spec_digest": SCOPE,
            },
            "snapshots": _source_entries("reverse"),
        }
    )
    assert source_a["manifest_digest"] == source_b["manifest_digest"]


def test_source_manifest_digest_and_validation_are_fail_closed() -> None:
    manifest = _source()
    assert manifest["manifest_digest"] == manifest["source_manifest_digest"]
    assert sm.validate_source_manifest(manifest) == manifest
    tampered = json.loads(json.dumps(manifest))
    tampered["snapshots"]["A"]["entries"][0]["size_bytes"] += 1
    with pytest.raises(sm.ManifestError, match="digest_mismatch"):
        sm.validate_source_manifest(tampered)


def test_source_manifest_rejects_unbound_or_mismatched_zero_write_evidence() -> None:
    access = sap.run_synthetic_source_access_profile()
    kwargs = {
        "contract_ref": {"id": "r8-g0-synthetic", "version": "0.1"},
        "binding_digest": BINDING,
        "project_ref": REF_PROJECT,
        "source_root_ref": REF_ROOT,
        "output_root_ref": REF_OUTPUT,
        "admission_id": REF_ADMISSION,
        "source_scope_spec_digest": SCOPE,
        "snapshots": _source_entries(),
    }
    with pytest.raises(sm.ManifestError, match="zero_write_fields_mismatch"):
        sm.build_source_manifest(**kwargs, zero_write={"status": "evaluable"})
    with pytest.raises(sm.ManifestError, match="zero_write_status_mismatch"):
        sm.build_source_manifest(
            **kwargs,
            zero_write={"status": "not_evaluable", "evidence": access},
        )


def test_source_manifest_rejects_absolute_or_escape_paths() -> None:
    entries = _source_entries()
    entries["A"]["entries"][0]["relative_path"] = "../outside"
    with pytest.raises(sm.ManifestError, match="escape"):
        sm.build_source_manifest(
            contract_ref="r8-g0-synthetic",
            binding_digest=BINDING,
            project_ref=REF_PROJECT,
            source_root_ref=REF_ROOT,
            output_root_ref=REF_OUTPUT,
            admission_id=REF_ADMISSION,
            source_scope_spec_digest=SCOPE,
            snapshots=entries,
        )


def test_output_manifest_binds_every_lineage_edge_to_artifact_hash() -> None:
    manifest = sm.build_output_manifest(**_output_kwargs())
    assert manifest["manifest_digest"] == manifest["output_manifest_digest"]
    assert len(manifest["lineage"]) == 5
    assert manifest["lineage"][0]["from_stage"] == "raw_output"
    assert manifest["lineage"][-1]["to_stage"] == "disposition"
    assert sm.validate_output_manifest(manifest) == manifest
    tampered = json.loads(json.dumps(manifest))
    tampered["lineage"][0]["from_sha256"] = _ref("different")
    with pytest.raises(sm.ManifestError, match="digest_mismatch"):
        sm.validate_output_manifest(tampered)


def test_output_manifest_digest_binds_source_access_profile_digest() -> None:
    manifest = sm.build_output_manifest(**_output_kwargs())
    tampered = json.loads(json.dumps(manifest))
    tampered["source_access_profile_digest"] = _ref("different-source-access-profile")
    with pytest.raises(sm.ManifestError, match="digest_mismatch"):
        sm.validate_output_manifest(tampered)


def test_output_manifest_rejects_revision_parent_invariants() -> None:
    with pytest.raises(sm.ManifestError, match="first_manifest"):
        sm.build_output_manifest(
            **_output_kwargs(), manifest_revision=1, parent_manifest_digest=_ref("parent")
        )
    with pytest.raises(sm.ManifestError, match="requires_parent"):
        sm.build_output_manifest(**_output_kwargs(), manifest_revision=2)


def test_revision_chain_is_monotonic_and_exposes_one_current_pointer() -> None:
    chain = sm.ManifestRevisionChain(admission_id=REF_ADMISSION, binding_digest=BINDING)
    first = chain.append_revision(**_output_kwargs())
    second = chain.append_revision(**{**_output_kwargs(), "publication_status": "candidate"})
    assert first["manifest_revision"] == 1
    assert second["manifest_revision"] == 2
    assert second["parent_manifest_digest"] == first["manifest_digest"]
    serialized = chain.as_dict()
    assert serialized["manifest_revision"] == 2
    assert serialized["current_manifest_digest"] == second["manifest_digest"]
    assert serialized["current_pointer"] == {
        "manifest_revision": 2,
        "manifest_digest": second["manifest_digest"],
    }
    assert chain.replay().valid


def test_independent_replay_detects_tampering_and_pointer_drift() -> None:
    chain = sm.ManifestRevisionChain(admission_id=REF_ADMISSION, binding_digest=BINDING)
    chain.append_revision(**_output_kwargs())
    chain.append_revision(**{**_output_kwargs(), "publication_status": "candidate"})
    tampered = chain.as_dict()
    tampered["manifest_revisions"][0]["artifacts"][0]["length_bytes"] += 100
    result = sm.independent_replay(tampered)
    assert not result.valid
    assert any("revision_1_invalid" in error for error in result.errors)
    pointer_drift = chain.as_dict()
    pointer_drift["current_pointer"]["manifest_revision"] = 1
    result = sm.replay_revision_chain(pointer_drift)
    assert not result.valid
    assert "current_pointer_mismatch" in result.errors


def test_revision_chain_rejects_cross_admission_and_cross_binding_reuse() -> None:
    chain = sm.ManifestRevisionChain(admission_id=REF_ADMISSION, binding_digest=BINDING)
    with pytest.raises(sm.ManifestError, match="cross_admission"):
        chain.append(sm.build_output_manifest(**{**_output_kwargs(), "admission_id": "opaque-admission:other"}))
    with pytest.raises(sm.ManifestError, match="cross_binding"):
        chain.append(
            sm.build_output_manifest(
                **{**_output_kwargs(), "binding_digest": _ref("other-binding"), "emitted_by_binding_digest": _ref("other-binding")}
            )
        )


def test_replay_cli_is_independent_and_offline(tmp_path: Path) -> None:
    chain = sm.ManifestRevisionChain(admission_id=REF_ADMISSION, binding_digest=BINDING)
    chain.append_revision(**_output_kwargs())
    path = tmp_path / "chain.json"
    path.write_text(json.dumps(chain.as_dict(), ensure_ascii=False), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(DEPLOY_DIR / "synthetic_manifest.py"), "replay", str(path), "--strict"],
        cwd=str(WORKBENCH_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert result["valid"] is True
    assert result["current_revision"] == 1
    assert completed.stderr == ""


def test_replay_strict_raises_for_malformed_chain() -> None:
    with pytest.raises(sm.ManifestError, match="schema_mismatch"):
        sm.replay_revision_chain({"schema": "wrong", "manifest_revisions": []}, strict=True)
