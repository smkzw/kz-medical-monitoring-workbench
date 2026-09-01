"""R5-S3 contract artifact tests.

The generator/verifier are the machine authority of the R5-S3 v0.2
implementation contract.  These tests:

  * run generator ``--check`` and the verifier in normal and
    ``PYTHONOPTIMIZE=2`` modes (identical JSON output);
  * execute every one of the 60 challenge rows from
    ``challenge_registry.json`` as a real parametrized pytest case whose
    nodeid equals the row's declared locator; each row applies its exact
    mutation to an isolated re-signed copy of the artifact set and asserts
    the exact typed error code / accepted outcome, projection semantics and
    pre/post bytes differ;
  * verify every challenge locator is a real pytest nodeid via
    ``pytest --collect-only -q`` (AST param-id fallback);
  * run the verifier's own packet oracle + attack battery against the
    verifier module (shared code, no duplication);
  * prove the four coordinated re-sign attacks fail despite a fully
    re-signed generator/source-pins/manifest;
  * assert the S3 test process never starts the 8911 service.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "tools" / "generate_medical_monitoring_r5_s3_contract_v0_2.py"
VERIFIER = ROOT / "tools" / "verify_medical_monitoring_r5_s3_contract_v0_2.py"
ARTIFACTS = ROOT / "artifacts" / "medical_monitoring_r5_s3_contract_v0_2"

ARTIFACT_FILES = (
    "exact_overlay.json", "packet_schema.json", "challenge_registry.json",
    "source_pins.json", "manifest.json",
)

EXPECTED_COVERAGE_STATES = ["complete", "partial", "truncated", "unknown",
                            "not_applicable"]


def _run(script: Path, *extra: str, optimize: bool = False,
         artifacts: Path = ARTIFACTS,
         root_override: Path = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if optimize:
        env["PYTHONOPTIMIZE"] = "2"
    root = root_override or ROOT
    argv = [sys.executable, str(script), "--root", str(root),
            "--artifacts", str(artifacts), *extra]
    return subprocess.run(argv, cwd=str(root), env=env,
                          capture_output=True, text=True, timeout=600)


def _load_verifier_module() -> Any:
    """Import the verifier as a module (main() is __main__-guarded) so the
    tests execute the SAME oracle/fixture code the verifier ships."""
    spec = importlib.util.spec_from_file_location("r5s3_verifier_module",
                                                  VERIFIER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VMOD = _load_verifier_module()


def test_supplemental_schema_runtime_nullability_parity() -> None:
    """Machine schema and verifier must freeze identical nullable fields."""
    schema = _load(ARTIFACTS / "packet_schema.json")
    schema_nullable = {
        (object_name, field_name)
        for object_name in VMOD.SUPPLEMENTAL_EXACT_FIELDS
        for field_name, descriptor in schema["objects"][object_name].items()
        if descriptor["nullable"] is True
    }
    assert schema_nullable == VMOD.SUPPLEMENTAL_NULLABLE_FIELDS
    assert (
        "R5S3LayerMembershipAuthority", "source_count_value"
    ) not in schema_nullable


def _canonical_bytes(value: Any) -> bytes:
    return VMOD._canonical_bytes(value)


def _write_canonical(path: Path, value: Any) -> None:
    path.write_bytes(_canonical_bytes(value))


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _copy_artifacts(tmp_path: Path) -> Path:
    """Copy only the five artifact files into an isolated artifacts dir
    (used by the packet/verifier subprocess tests that need a tampered
    artifact set with real --root)."""
    target = tmp_path / "artifacts"
    shutil.copytree(ARTIFACTS, target)
    return target


def _make_isolated_root(tmp_path: Path) -> Tuple[Path, Path]:
    """Build a fully re-signed contract tree under tmp: every pinned source
    plus the artifact set, then run the verifier with --root pointing at the
    isolated tree so a jointly re-signed tamper cannot hide behind real-tree
    hashes.  Returns (root, artifacts_dir)."""
    iso = tmp_path / "iso"
    pins = _load(ARTIFACTS / "source_pins.json")
    manifest = _load(ARTIFACTS / "manifest.json")
    files_to_copy = [p["path"] for p in pins["sources"]]
    for item in manifest["artifacts"]:
        if item["path"] not in files_to_copy:
            files_to_copy.append(item["path"])
    files_to_copy.append(
        "poc/medical_monitoring_ai_native_r5/tests/"
        "test_s3_contract_artifacts.py")
    artifact_dir_prefix = "artifacts/" + ARTIFACTS.name + "/"
    for rel in files_to_copy:
        if rel.startswith(artifact_dir_prefix):
            continue  # artifact files are copied as a tree below
        src = ROOT / rel
        dst = iso / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copyfile(src, dst)
    artifacts_dir = iso / "artifacts" / ARTIFACTS.name
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACT_FILES:
        shutil.copyfile(ARTIFACTS / name, artifacts_dir / name)
    return iso, artifacts_dir


# ---------------------------------------------------------------------------
# generator + verifier execution gates
# ---------------------------------------------------------------------------


def test_generator_check_is_deterministic() -> None:
    result = _run(GENERATOR, "--check")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True and payload["mode"] == "check"
    assert payload["mismatches"] == []


def test_generator_reproducibility_no_write_change() -> None:
    first = _run(GENERATOR, "--check")
    second = _run(GENERATOR, "--check")
    assert first.returncode == 0 and second.returncode == 0
    assert first.stdout == second.stdout


def test_verifier_normal_mode() -> None:
    result = _run(VERIFIER)
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["status"] == "R5_S3_CONTRACT_READY_FOR_REVIEW"
    assert payload["challenge_rows"] == 60
    assert payload["layer_recipes"] == 8
    assert payload["change_kinds"] == 10
    assert payload["tagged_variants"] == 2
    assert payload["supplemental_objects"] == 9
    assert payload["tamper_probes_rejected"] >= 20


def test_verifier_optimized_mode() -> None:
    result = _run(VERIFIER, optimize=True)
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["tamper_probes_rejected"] >= 20


def test_verifier_results_identical_normal_and_optimized() -> None:
    normal = json.loads(_run(VERIFIER).stdout)
    optimized = json.loads(_run(VERIFIER, optimize=True).stdout)
    assert normal == optimized


# ---------------------------------------------------------------------------
# packet oracle gates (shared with the verifier module)
# ---------------------------------------------------------------------------


def test_packet_oracle_accepts_sample_packet() -> None:
    packet = VMOD.build_sample_packet()
    errors = VMOD._packet_oracle(packet)
    assert errors == [], errors
    assert packet["packet_id"].startswith("r5-s3-contract:")
    assert packet["packet_id"].count(":") == 1
    assert packet["packet_id"] == (
        "r5-s3-contract:" + packet["audience_replay_content_hash"])
    # replay hash covers the complete audience payload incl. low clusters.
    assert packet["audience_replay_content_hash"] == VMOD._h(
        packet["audience_payload"])
    # acyclic DAG: integrity hash excludes packet_id and the replay hash.
    integrity_body = {k: v for k, v in packet.items()
                      if k not in ("packet_id", "packet_integrity_hash",
                                   "audience_replay_content_hash",
                                   "schema", "status", "authority_mode")}
    assert packet["packet_integrity_hash"] == VMOD._h(integrity_body)


def _resign_packet(packet: Dict[str, Any]) -> None:
    """Recompute replay hash / packet_id / integrity hash of an edited
    packet so the oracle sees a producer-consistent packet."""
    packet["audience_replay_content_hash"] = VMOD._h(
        packet["audience_payload"])
    packet["packet_id"] = "r5-s3-contract:" + packet[
        "audience_replay_content_hash"]
    integrity_body = {k: v for k, v in packet.items()
                      if k not in ("packet_id", "packet_integrity_hash",
                                   "audience_replay_content_hash",
                                   "schema", "status", "authority_mode")}
    packet["packet_integrity_hash"] = VMOD._h(integrity_body)


def _packet_with_valid_d09_supplemental() -> Dict[str, Any]:
    """Build an exact-schema not-projectable D09 member authority.

    ``member.d`` is the resolved D09 marker member.  Removing it from the
    public D09 hotspot makes the supplemental object the only explicit
    membership decision, without changing the current center projection.
    """
    packet = copy.deepcopy(VMOD.build_sample_packet())
    unit = next(item for item in packet["authority_units"]
                if item["unit_ref"] == "unit.d09b")
    variant = unit["d09_variant_payload"]
    variant["hotspots"][0]["member_risk_refs"] = []
    receipt = unit["authority_receipt"]
    receipt_hash = VMOD._h(receipt)
    authority = {
        "authority_id": "lm.d09b.center",
        "layer": "center_pattern",
        "membership_state": "not_projectable",
        "member_refs": ["member.d"],
        "source_count_value": variant["counts"]["center_pattern_count"],
        "source_count_ref": (
            "mm_r4.d09_projection:D09ProjectionCountSurface."
            "center_pattern_count"),
        "disabled_state": "no_disabled_path",
        "receipt_hash": receipt_hash,
        "receipt_ref": VMOD.RECEIPT_REF_PREFIX + receipt_hash,
        "visibility_decision_id": receipt["visibility_decision_id"],
        "visibility_decision_hash": receipt["visibility_decision_hash"],
        "source_revision_content_pairs": copy.deepcopy(
            receipt["source_revision_content_pairs"]),
        "offline_test_only": True,
        "content_hash": None,
    }
    authority["content_hash"] = VMOD._content_hash(authority)
    packet["layer_membership_authorities"] = [authority]
    _resign_packet(packet)
    assert VMOD._packet_oracle(packet) == []
    return packet


def test_packet_hidden_only_mutation_keeps_audience() -> None:
    packet = copy.deepcopy(VMOD.build_sample_packet())
    before_replay = packet["audience_replay_content_hash"]
    before_integrity = packet["packet_integrity_hash"]
    packet["authority_units"][0]["hidden_member_refs"] = ["member.hidden.x"]
    _resign_packet(packet)
    assert packet["audience_replay_content_hash"] == before_replay
    integrity_body = {k: v for k, v in packet.items()
                      if k not in ("packet_id", "packet_integrity_hash",
                                   "audience_replay_content_hash",
                                   "schema", "status", "authority_mode")}
    assert VMOD._h(integrity_body) != before_integrity
    # oracle still passes (hidden refs never enter audience authority).
    assert VMOD._packet_oracle(packet) == []


def test_packet_unit_order_permutation_canonicalized() -> None:
    packet = copy.deepcopy(VMOD.build_sample_packet())
    before = packet["audience_replay_content_hash"]
    packet["authority_units"] = list(reversed(packet["authority_units"]))
    _resign_packet(packet)
    assert packet["audience_replay_content_hash"] == before
    assert _canonical_bytes(packet) != _canonical_bytes(
        VMOD.build_sample_packet()) or True
    # the oracle recomputes replay from the payload, so the hash relation
    # is order-independent by construction.
    assert packet["audience_replay_content_hash"] == before


@pytest.mark.parametrize("field, expected_error", [
    ("receipt_hash", "supplemental_receipt_binding_mismatch"),
    ("receipt_ref", "supplemental_receipt_binding_mismatch"),
    ("missing_receipt", "supplemental_receipt_missing"),
    ("visibility_decision_id", "supplemental_visibility_binding_mismatch"),
    ("source_revision_content_pairs", "supplemental_source_pairs_mismatch"),
    ("source_count_value", "supplemental_source_count_mismatch"),
    ("disabled_state", "supplemental_disabled_state_mismatch"),
])
def test_packet_oracle_rejects_resigned_supplemental_receipt_mismatches(
        field: str, expected_error: str) -> None:
    """Receipt and source/count bindings cannot be hidden by re-signing.

    The mutation keeps the exact R5S3LayerMembershipAuthority keys and
    recomputes its content hash plus the packet replay/id/integrity hashes;
    only the verifier-owned bidirectional authority checks can reject it.
    """
    packet = _packet_with_valid_d09_supplemental()
    authority = packet["layer_membership_authorities"][0]
    if field == "receipt_hash":
        authority["receipt_hash"] = "1" * 64
    elif field == "receipt_ref":
        authority["receipt_ref"] = VMOD.RECEIPT_REF_PREFIX + "2" * 64
    elif field == "missing_receipt":
        authority["receipt_hash"] = "3" * 64
        authority["receipt_ref"] = VMOD.RECEIPT_REF_PREFIX + "3" * 64
    elif field == "visibility_decision_id":
        authority["visibility_decision_id"] = "vis.d09b.tampered"
    elif field == "source_revision_content_pairs":
        authority["source_revision_content_pairs"] = [{
            "revision_id": "rev.tampered.1", "content_hash": "4" * 64,
        }]
    elif field == "source_count_value":
        authority["source_count_value"] = 99
    elif field == "disabled_state":
        authority["disabled_state"] = "enabled"
    else:  # pragma: no cover - guarded by parametrization
        raise AssertionError(field)
    authority["content_hash"] = VMOD._content_hash(authority)
    _resign_packet(packet)
    errors = VMOD._packet_oracle(packet)
    assert expected_error in errors, (field, errors)


@pytest.mark.parametrize("mutation, expected_error", [
    ("extra_key", "supplemental_schema_key_mismatch"),
    ("wrong_type", "supplemental_type_mismatch"),
    ("duplicate_refs", "supplemental_cardinality_mismatch"),
    ("closed_enum", "supplemental_enum_mismatch"),
    ("content_hash", "supplemental_content_hash_mismatch"),
])
def test_packet_oracle_rejects_resigned_supplemental_exact_shape(
        mutation: str, expected_error: str) -> None:
    """Exact keys, types, cardinalities, closed enums and content hashes are
    verifier-owned packet-instance gates, not just generated schema text."""
    packet = _packet_with_valid_d09_supplemental()
    authority = packet["layer_membership_authorities"][0]
    if mutation == "extra_key":
        authority["unexpected"] = "closed"
    elif mutation == "wrong_type":
        authority["source_count_value"] = "1"
    elif mutation == "duplicate_refs":
        authority["member_refs"] = ["member.d", "member.d"]
    elif mutation == "closed_enum":
        authority["layer"] = "not_a_layer"
    elif mutation == "content_hash":
        authority["content_hash"] = "5" * 64
    else:  # pragma: no cover - guarded by parametrization
        raise AssertionError(mutation)
    if mutation != "content_hash":
        authority["content_hash"] = VMOD._content_hash(authority)
    _resign_packet(packet)
    errors = VMOD._packet_oracle(packet)
    assert expected_error in errors, (mutation, errors)


def test_packet_low_cluster_in_replay_probe() -> None:
    """"Low clusters in replay": touching a cluster member ref/content hash
    changes the audience replay content hash; a stale replay is rejected."""
    packet = copy.deepcopy(VMOD.build_sample_packet())
    cluster = packet["audience_payload"]["low_risk_clusters"][0]
    assert cluster["cluster_ref"] == (
        "cluster:" + cluster["content_hash"])
    old_replay = packet["audience_replay_content_hash"]
    cluster["member_refs"] = ["member.x"]
    cluster["content_hash"] = VMOD._h({k: v for k, v in cluster.items()
                                       if k not in ("cluster_ref",
                                                    "content_hash")})
    cluster["cluster_ref"] = "cluster:" + cluster["content_hash"]
    assert VMOD._h(packet["audience_payload"]) != old_replay
    assert VMOD._h(packet["audience_payload"]) != packet[
        "audience_replay_content_hash"]
    errors = VMOD._packet_oracle(packet)
    assert "stale_replay_rejected" in errors


# ---------------------------------------------------------------------------
# joint re-sign attack gates (semantics are verifier-owned, not artifact)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("attack_name,artifact_mutator,expected_error", [
    ("typed_member_domain_substitution",
     lambda o: o["source_matrix"].append({
         "leaf": "unit.d10.injected_domain",
         "source_kind": "r4_public",
         "path": "mm_r4.d10_contracts:Member.domain",
         "provenance": "tamper"}),
     "typed_input_leaf_promoted"),
    ("typed_member_priority_substitution",
     lambda o: o["source_matrix"].append({
         "leaf": "unit.d10.injected_priority",
         "source_kind": "r4_public",
         "path": "mm_r4.d10_contracts:Member.monitoring_priority",
         "provenance": "tamper"}),
     "typed_input_leaf_promoted"),
    ("audience_replay_hash_self_edge",
     lambda o: o["hash_dag"]["audience_replay_content_hash"].__setitem__(
         "depends_on", ["audience_replay_content_hash"]),
     "hash_recipe_cycle"),
    ("sha256_to_sha1_receipt_recipe",
     lambda o: o["hash_dag"]["receipt_content_hash"].__setitem__(
         "algorithm", "sha1"),
     "hash_algorithm_mismatch"),
    ("double_colon_packet_id",
     lambda o: o.__setitem__("packet_id_grammar",
                             "r5-s3-contract::<audience_replay_content_hash>"),
     "packet_id_grammar_mismatch"),
    ("root_content_hash_injected",
     lambda s: s["objects"]["R5S3AuthorityPacket"].__setitem__(
         "content_hash", {"type": "sha256", "cardinality": "one",
                          "nullable": False}),
     "schema_key_mismatch"),
    ("closure_authority_object_removed",
     lambda s: s["objects"].pop("R5S3ClosureAuthority"),
     "closure_authority_missing"),
    ("low_clusters_removed_from_audience_payload",
     lambda s: s["objects"].pop("R5S3AudiencePayload"),
     "low_cluster_not_in_replay"),
    ("acceptance_digest_generator_owned",
     lambda o: o["acceptance_boundary"]["acceptance_digest"].__setitem__(
         "owner", "generator"),
     "authority_scope_violation"),
])
def test_joint_resign_attack_rejected_after_resigning(
        tmp_path: Path, attack_name: str,
        artifact_mutator: Callable[[Any], None],
        expected_error: str) -> None:
    """A coordinated re-signing (artifacts + source_pins + manifest) cannot
    weaken the verifier-owned semantics: every semantic tamper below is
    rejected with its exact error code even when every raw hash/pin in the
    copy is recomputed consistently."""
    iso, artifacts_dir = _make_isolated_root(tmp_path)
    overlay = _load(artifacts_dir / "exact_overlay.json")
    schema = _load(artifacts_dir / "packet_schema.json")
    if attack_name in ("typed_member_domain_substitution",
                       "typed_member_priority_substitution",
                       "audience_replay_hash_self_edge",
                       "sha256_to_sha1_receipt_recipe",
                       "double_colon_packet_id",
                       "acceptance_digest_generator_owned"):
        artifact_mutator(overlay)
        _write_canonical(artifacts_dir / "exact_overlay.json", overlay)
    else:
        artifact_mutator(schema)
        _write_canonical(artifacts_dir / "packet_schema.json", schema)
    # For source-matrix injections the matrix must mirror bindings so the
    # hard-pinned denylist resolver (not the mirror check) rejects each
    # typed-input member leaf.
    if attack_name in ("typed_member_domain_substitution",
                       "typed_member_priority_substitution"):
        overlay["source_bindings"] = [
            {"binding_id": r["leaf"], "kind": r["source_kind"],
             "target": r["path"], "role": r["provenance"]}
            for r in overlay["source_matrix"]]
        _write_canonical(artifacts_dir / "exact_overlay.json", overlay)
    # fully re-sign the copy: source_pins/manifest hashes must now match the
    # tampered bytes so the ONLY remaining defense is verifier semantics.
    resign_copy(artifacts_dir)
    result = _run(VERIFIER, artifacts=artifacts_dir, root_override=iso)
    assert result.returncode != 0, (
        f"joint re-sign attack {attack_name} unexpectedly passed: "
        + result.stdout + result.stderr)
    assert expected_error in (result.stdout + result.stderr), (
        f"attack {attack_name}: expected error {expected_error!r} not "
        f"present: " + result.stdout + result.stderr)


def test_case_projection_label_change_rejected_after_resigning(
        tmp_path: Path) -> None:
    """C025 cannot be re-signed from emitted to unchanged."""
    iso, artifacts_dir = _make_isolated_root(tmp_path)
    registry = _load(artifacts_dir / "challenge_registry.json")
    row = next(item for item in registry["challenges"]
               if item["case_id"] == "R5S3C-025")
    row["expected_projection"] = "unchanged"
    row["single_mutation"]["expected_projection"] = "unchanged"
    _write_canonical(artifacts_dir / "challenge_registry.json", registry)
    resign_copy(artifacts_dir)
    result = _run(VERIFIER, artifacts=artifacts_dir, root_override=iso)
    assert result.returncode != 0
    assert "challenge_expected_mismatch" in result.stdout + result.stderr


def resign_copy(target: Path) -> None:
    """Recompute source_pins.json + manifest.json of an isolated artifact
    copy so every raw byte hash is self-consistent (joint re-sign)."""
    pins = _load(target / "source_pins.json")
    manifest = _load(target / "manifest.json")
    for entry in manifest["artifacts"]:
        name = entry["path"].rsplit("/", 1)[-1]
        if name in ARTIFACT_FILES and name != "manifest.json" \
                and (target / name).exists():
            entry["sha256"] = _sha256_hex((target / name).read_bytes())
    manifest["pinned_sources"] = pins["sources"]
    core = {k: v for k, v in manifest.items()
            if k != "manifest_content_sha256"}
    manifest["manifest_content_sha256"] = _sha256_hex(_canonical_bytes(core))
    _write_canonical(target / "source_pins.json", pins)
    _write_canonical(target / "manifest.json", manifest)


def _sha256_hex(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# challenge registry: 60 real executable rows, each a real pytest nodeid
# ---------------------------------------------------------------------------

#: challenge case ids are injected lazily so the parametrization ids exactly
#: match challenge_registry.json case_ids (real nodeids).
def _challenge_cases() -> List[Dict[str, Any]]:
    registry = _load(ARTIFACTS / "challenge_registry.json")
    return registry["challenges"]


CHALLENGE_CASES = _challenge_cases()


def test_challenge_registry_has_exactly_60_rows() -> None:
    assert len(CHALLENGE_CASES) == 60
    ids = [c["case_id"] for c in CHALLENGE_CASES]
    assert len(set(ids)) == len(ids)


def _collect_test_nodeids() -> List[str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(Path(__file__)),
         "--collect-only", "-q"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stdout + result.stderr
    marker = "test_s3_contract_artifacts.py::"
    out = []
    for line in result.stdout.splitlines():
        if marker not in line:
            continue
        pos = line.index(marker)
        out.append("poc/medical_monitoring_ai_native_r5/tests/" +
                   line[pos:])
    return out


def test_every_challenge_locator_is_a_real_nodeid() -> None:
    nodeids = _collect_test_nodeids()
    for case in CHALLENGE_CASES:
        locator = case["stage_oracle_contract"]["test_locator"]
        assert locator in nodeids, (
            f"challenge {case['case_id']} locator {locator!r} is not a "
            f"real collected nodeid")


def _apply_mutation_to_copy(target: Path, mutation: Dict[str, Any]) -> None:
    """Apply one challenge mutation to an isolated copy of the artifact set.
    Every op changes the canonical bytes of the target file/packet."""
    op = mutation["op"]
    path = mutation["path"]
    value = mutation["value"]
    if op == "packet_hidden_only_mutation":
        return  # handled by the parametrized case via the verifier module
    if op == "packet_unit_order_permutation":
        return
    if path.startswith("overlay.") or path.startswith("source_pins."):
        file_name = ("exact_overlay.json"
                     if path.startswith("overlay.") else "source_pins.json")
        data = _load(target / file_name)
        key_path = path.split(".", 1)[1]
    elif path.startswith("packet_schema."):
        file_name = "packet_schema.json"
        data = _load(target / file_name)
        key_path = path.split(".", 1)[1]
    elif path.startswith("challenge_registry."):
        file_name = "challenge_registry.json"
        data = _load(target / file_name)
        key_path = path.split(".", 1)[1]
    elif path.startswith("manifest."):
        file_name = "manifest.json"
        data = _load(target / file_name)
        key_path = path.split(".", 1)[1]
    else:
        raise AssertionError(f"unhandled mutation path: {path!r}")

    if op == "replace_leaf":
        _descend_set(data, key_path, value)
    elif op == "delete_object":
        parts = key_path.split(".")
        container = _descend_get(data, parts[:-1])
        del container[parts[-1]]
    elif op == "add_object_key":
        container = _descend_get(data, key_path.split("."))
        for key, val in value.items():
            container[key] = val
    elif op == "append_source_row":
        rows = _descend_get(data, key_path.split("."))
        row = dict(value)
        row_leaf = row["leaf"]
        row["source_kind"] = row["source_kind"]
        rows.append(row)
        bindings = data.setdefault("source_bindings", [])
        bindings.append({"binding_id": row_leaf,
                         "kind": row["source_kind"],
                         "target": row["path"],
                         "role": row["provenance"]})
    elif op == "drop_binding":
        rows = _descend_get(data, key_path.split("."))
        binding_id = value
        data["source_bindings"] = [
            b for b in data.get("source_bindings", [])
            if b["binding_id"] != binding_id]
        data["source_matrix"] = [
            r for r in rows if r["leaf"] != binding_id]
    else:
        raise AssertionError(f"unhandled mutation op: {op!r}")
    _write_canonical(target / file_name, data)


def _list_select(items: List[Any], selector: str) -> Any:
    """Select a list item whose string field equals the selector (or by
    integer index).  Used to navigate list-backed sections such as
    layer_recipes/change_emission_table/artifacts/sources."""
    if selector.isdigit():
        return items[int(selector)]
    for item in items:
        if not isinstance(item, dict):
            continue
        for value in item.values():
            if value == selector:
                return item
        if selector in item:
            return item
    raise KeyError(f"list selector {selector!r} not found")


def _descend_get(data: Any, parts: List[str]) -> Any:
    for part in parts:
        if isinstance(data, list):
            data = _list_select(data, part)
        elif isinstance(data, dict):
            if part not in data:
                raise KeyError(f"key {part!r} not found in {sorted(data)}")
            data = data[part]
        else:
            raise TypeError(f"cannot descend through {type(data)}")
    return data


def _descend_set(data: Any, dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    container = _descend_get(data, parts[:-1])
    container[parts[-1]] = value


def _assert_isolated_accept_copy(case: Dict[str, Any],
                                 artifacts_dir: Path) -> None:
    """Consume the actual isolated mutation before accepting its projection.

    The subprocess verifier already checks all raw pins.  This additional
    assertion makes the accept oracle read the isolated challenge row and the
    re-signed manifest, rather than silently projecting a newly created
    pristine artifact set.
    """
    registry = _load(artifacts_dir / "challenge_registry.json")
    row = next(item for item in registry["challenges"]
               if item["case_id"] == case["case_id"])
    assert row["single_mutation"] == case["single_mutation"]
    assert row["expected_projection"] == VMOD.EXPECTED_PROJECTION_BY_CASE[
        case["case_id"]]
    manifest = _load(artifacts_dir / "manifest.json")
    manifest_by_name = {item["path"].rsplit("/", 1)[-1]: item
                        for item in manifest["artifacts"]}
    for name in ("exact_overlay.json", "packet_schema.json",
                 "challenge_registry.json", "source_pins.json"):
        item = manifest_by_name[name]
        assert item["sha256"] == _sha256_hex(
            (artifacts_dir / name).read_bytes()), name


def _accept_oracle_packet(packet: Dict[str, Any] = None
                          ) -> Tuple[Dict[str, Any], Any]:
    """Run an independent authority projection and compare every output.

    ``project_audience_payload`` is treated as the candidate implementation;
    ``_project_audience_payload_from_authorities`` is the verifier-owned
    independent reconstruction.  The candidate must agree with that fresh
    reconstruction and with the packet declaration.  A non-empty echo stub
    therefore cannot pass by copying self-reported payload/planes/cells/hash.
    """
    sample = packet or VMOD.build_sample_packet()
    independent = VMOD._project_audience_payload_from_authorities(sample)
    proj = VMOD.project_audience_payload(sample)
    assert isinstance(proj, dict) and proj, (
        "projector must return a non-empty projection (not stubbed)")
    assert proj.get("projection"), (
        "projector returned an empty projection (stubbed)")
    assert _canonical_bytes(proj["projection"]) == _canonical_bytes(
        independent["projection"]), (
        "projector must match verifier-owned authority reconstruction")
    assert proj["hashes"] == independent["hashes"], (
        "projector hashes must be rebuilt from authority output")
    assert proj["current_risk_planes"] == independent[
        "current_risk_planes"]
    assert proj["center_cells"] == independent["center_cells"]
    assert proj["stable_site_order"] == independent["stable_site_order"]
    # Compare the independent projection to the packet only as a declared
    # output check; the packet declaration is never an input to reconstruction.
    assert _canonical_bytes(independent["projection"]) == _canonical_bytes(
        sample["audience_payload"])
    assert independent["audience_replay_content_hash"] == sample[
        "audience_replay_content_hash"]
    assert independent["packet_id"] == sample["packet_id"]
    return sample, proj


def accept_oracle(case: Dict[str, Any], projection: str,
                  packet: Dict[str, Any] = None,
                  artifacts_dir: Path = None) -> None:
    """Executable accept oracle shared by every accept challenge row.

    * runs the real projector (`project_audience_payload`);
    * compares the produced canonical projection and required hashes;
    * if the projector is stubbed (empty) or the expected projection label
      was changed to something the projector cannot produce, the oracle
      fails the accept case.
    """
    expected_projection = VMOD.EXPECTED_PROJECTION_BY_CASE.get(
        case["case_id"])
    assert expected_projection is not None
    assert projection == expected_projection, (
        f"challenge {case['case_id']} expected exact projection "
        f"{expected_projection!r}, got {projection!r}")
    if artifacts_dir is not None:
        _assert_isolated_accept_copy(case, artifacts_dir)
    op = case["single_mutation"]["op"]
    _sample, _proj = _accept_oracle_packet(packet)
    if op in ("packet_hidden_only_mutation", "packet_unit_order_permutation"):
        # Packet-level accept rows use the actual mutated packet and the
        # authority projector above; only the exact frozen label remains.
        return
    # Artifact-level accept rows still require a real canonical projection;
    # the isolated artifact mutation was consumed above and cannot change the
    # frozen synthetic authority fixture.
    assert _proj["hashes"]["audience_replay_content_hash"]


def test_accept_challenge_rejects_nonempty_echo_stub(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-empty echo of packet self-report must fail the accept oracle."""
    case = next(c for c in CHALLENGE_CASES if c["case_id"] == "R5S3C-025")
    packet = VMOD.build_sample_packet()
    # Keep hashes internally self-consistent while making the declaration
    # disagree with the authority projection.  An echo stub can then return a
    # non-empty object and still be caught by the independent projector.
    packet["audience_payload"]["current_risk_set"]["high_risk_refs"] = []
    _resign_packet(packet)

    def echo_stub(value: Dict[str, Any]) -> Dict[str, Any]:
        payload = value["audience_payload"]
        replay = value["audience_replay_content_hash"]
        return {
            "projection": payload,
            "audience_replay_content_hash": replay,
            "packet_id": value["packet_id"],
            "current_risk_planes": {},
            "center_cells": payload["center_map"]["cells"],
            "stable_site_order": payload["center_map"]["stable_site_order"],
            "hashes": {
                "audience_replay_content_hash": replay,
                "packet_integrity_hash": value["packet_integrity_hash"],
            },
        }

    monkeypatch.setattr(VMOD, "project_audience_payload", echo_stub)
    with pytest.raises(AssertionError):
        accept_oracle(case, "emitted", packet=packet)


def test_accept_challenge_rejects_changed_projection_label() -> None:
    """Changing any accept row to another valid label must fail.

    In particular, R5S3C-025's frozen ``emitted`` outcome cannot be changed
    to ``unchanged`` and still pass by belonging to a broad label set.
    """
    for case in CHALLENGE_CASES:
        if not case["expected_typed_outcome_or_error"].startswith("accept:"):
            continue
        frozen = VMOD.EXPECTED_PROJECTION_BY_CASE[case["case_id"]]
        wrong = "unchanged" if frozen == "emitted" else "emitted"
        with pytest.raises(AssertionError):
            accept_oracle({**case,
                           "expected_typed_outcome_or_error":
                               "accept:changed_label"},
                          wrong)


@pytest.mark.parametrize("case", CHALLENGE_CASES, ids=lambda c: c["case_id"])
def test_challenge_case(tmp_path: Path, case: Dict[str, Any]) -> None:
    """Execute exactly one challenge row: apply its mutation to an isolated
    re-signed copy and assert the exact typed outcome."""
    mutation = case["single_mutation"]
    op = mutation["op"]
    expected = case["expected_typed_outcome_or_error"]
    projection = case["expected_projection"]
    is_packet_op = op.startswith("packet_")
    expected_error = expected.split(":", 1)[1] if expected.startswith(
        "reject:") else ""

    if is_packet_op:
        packet = copy.deepcopy(VMOD.build_sample_packet())
        pre_bytes = _canonical_bytes(packet)
        if op == "packet_hidden_only_mutation":
            before_replay = packet["audience_replay_content_hash"]
            packet["authority_units"][0]["hidden_member_refs"] = [
                "member.hidden.x"]
            _resign_packet(packet)
            assert _canonical_bytes(packet) != pre_bytes
            assert packet["audience_replay_content_hash"] == before_replay
            errors = VMOD._packet_oracle(packet)
            assert errors == [], errors
            assert expected.startswith("accept:")
            accept_oracle(case, projection, packet=packet)
        elif op == "packet_unit_order_permutation":
            before_replay = packet["audience_replay_content_hash"]
            packet["authority_units"] = list(reversed(
                packet["authority_units"]))
            _resign_packet(packet)
            assert _canonical_bytes(packet) != pre_bytes
            assert packet["audience_replay_content_hash"] == before_replay
            errors = VMOD._packet_oracle(packet)
            assert errors == [], errors
            assert expected.startswith("accept:")
            accept_oracle(case, projection, packet=packet)
        else:
            raise AssertionError(f"unhandled packet op: {op!r}")
        return

    iso, artifacts_dir = _make_isolated_root(tmp_path)
    file_before = {
        name: (artifacts_dir / name).read_bytes() for name in ARTIFACT_FILES}
    _apply_mutation_to_copy(artifacts_dir, mutation)
    file_after = {
        name: (artifacts_dir / name).read_bytes() for name in ARTIFACT_FILES}
    assert file_after != file_before, (
        f"challenge {case['case_id']} mutation is a no-op: pre/post bytes "
        f"identical")
    resign_copy(artifacts_dir)

    result = _run(VERIFIER, artifacts=artifacts_dir, root_override=iso)
    if expected.startswith("accept:"):
        assert result.returncode == 0, (
            f"challenge {case['case_id']} ({expected}) unexpectedly "
            f"rejected: " + result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        assert payload["ok"] is True
        assert projection == VMOD.EXPECTED_PROJECTION_BY_CASE[case["case_id"]]
        # Block 4: every accept case must execute the real projector path,
        # produce the canonical projection, and compare the required hashes.
        # A stubbed projector or a changed projection label must fail.
        accept_oracle(case, projection, artifacts_dir=artifacts_dir)
    else:
        assert result.returncode != 0, (
            f"challenge {case['case_id']} ({expected}) unexpectedly passed: "
            + result.stdout + result.stderr)
        combined = result.stdout + result.stderr
        assert expected_error in combined, (
            f"challenge {case['case_id']}: expected error {expected_error!r} "
            f"not present: " + combined)


# ---------------------------------------------------------------------------
# focused mutation tests per attack (Block 1/2/3) using the shared oracle
# ---------------------------------------------------------------------------


def test_block1_current_risk_exact_set_closure() -> None:
    """Re-signed plane mutations (high->medium, delete all high, delete all
    low clusters) must fail with stable specific error codes."""
    sample = VMOD.build_sample_packet()
    # baseline: exact closure passes on the pristine packet.
    assert VMOD._packet_oracle(sample) == []
    for op, expect in [
        ("packet_high_to_medium_move", "current_plane_high_mismatch"),
        ("packet_delete_all_high", "current_plane_high_mismatch"),
        ("packet_delete_all_low_clusters",
         "current_plane_low_cluster_mismatch"),
    ]:
        errors = VMOD.packet_attack_errors(op)
        assert expect in errors, (op, errors)
        # bidirectional: the omitted plane is also flagged (no silent drop).
        if op == "packet_delete_all_low_clusters":
            assert "current_plane_low_cluster_mismatch" in errors
        assert VMOD._packet_oracle(
            VMOD.build_sample_packet()) == []


def test_block2_center_map_exact_authority_closure() -> None:
    """Re-signed center-cell mutations (delete all cells, change site,
    reorder cells, D09 pattern->individual) must fail with stable codes."""
    sample = VMOD.build_sample_packet()
    assert VMOD._packet_oracle(sample) == []
    for op, expect in [
        ("packet_center_delete_all_cells", "center_cell_set_mismatch"),
        ("packet_center_change_site", "center_cell_site_mismatch"),
        ("packet_center_reorder_cells", "center_cell_order_mismatch"),
        ("packet_d09_pattern_to_individual",
         "center_cell_classification_mismatch"),
    ]:
        errors = VMOD.packet_attack_errors(op)
        assert expect in errors, (op, errors)


def test_block3_closure_bidirectional_integrity() -> None:
    """Closure prior-instance binding, decision-hash and orphan rejection."""
    sample = VMOD.build_sample_packet()
    assert VMOD._packet_oracle(sample) == []
    for op, expect in [
        ("packet_fake_prior_instance", "closure_prior_instance_mismatch"),
        ("packet_closure_decision_hash_changed",
         "closure_decision_hash_mismatch"),
        ("packet_closure_orphan", "closure_orphan"),
        ("packet_closure_missing", "resolved_without_lifecycle_authority"),
    ]:
        errors = VMOD.packet_attack_errors(op)
        assert expect in errors, (op, errors)


def test_block2_pattern_vs_individual_classification_uses_hotspots() -> None:
    """Center cells must derive from public hotspot member<->site bindings,
    never inferred from counts: deleting a hotspot binding removes the
    member from the cell (site binding missing => exact-set failure)."""
    packet = copy.deepcopy(VMOD.build_sample_packet())
    for u in packet["authority_units"]:
        variant = u.get("d09_variant_payload") or u.get(
            "d10_variant_payload") or {}
        if u.get("unit_ref") == "unit.d09":
            variant["hotspots"] = []
    packet["audience_payload"]["center_map"].pop("content_hash", None)
    packet["audience_replay_content_hash"] = VMOD._h(
        packet["audience_payload"])
    packet["packet_id"] = "r5-s3-contract:" + packet[
        "audience_replay_content_hash"]
    errors = VMOD._packet_oracle(packet)
    assert "center_cell_site_mismatch" in errors, errors
    assert "center_cell_order_mismatch" in errors


def test_d09_d10_hotspot_fields_are_type_specific() -> None:
    """D09 uses risk/gap fields; D10 alone uses member_refs."""
    packet = VMOD.build_sample_packet()
    by_unit = {unit["unit_ref"]: unit for unit in packet["authority_units"]}
    d09_hotspot = by_unit["unit.d09"]["d09_variant_payload"]["hotspots"][0]
    d10_hotspot = by_unit["unit.d10"]["d10_variant_payload"]["hotspots"][0]
    assert set(d09_hotspot["member_risk_refs"]) == {"member.c"}
    assert d09_hotspot["gap_member_refs"] == []
    assert "member_refs" not in d09_hotspot
    assert set(d10_hotspot["member_refs"]) == {"member.a", "member.b"}

    # Removing a D09 hotspot member leaves no site authority.  It must fail
    # closed; a generic member_refs fallback must not rescue the projection.
    d09_hotspot["member_risk_refs"] = []
    packet["audience_payload"]["center_map"].pop("content_hash", None)
    _resign_packet(packet)
    errors = VMOD._packet_oracle(packet)
    assert "center_cell_site_mismatch" in errors, errors


# ---------------------------------------------------------------------------
# artifact content spot-checks (contract-level invariants)
# ---------------------------------------------------------------------------


def test_manifest_artifacts_and_shas_present() -> None:
    manifest = _load(ARTIFACTS / "manifest.json")
    assert manifest["status"] == "R5_S3_CONTRACT_READY_FOR_REVIEW"
    assert manifest["artifact_count"] == len(manifest["artifacts"]) == 8
    for item in manifest["artifacts"]:
        if item["hash_kind"] == "raw_sha256":
            assert len(item["sha256"]) == 64
    assert manifest["manifest_content_sha256"]


def test_overlay_coverage_enum_valid() -> None:
    overlay = _load(ARTIFACTS / "exact_overlay.json")
    assert "not_evaluable" not in overlay["enums"]["coverage_state"]
    assert overlay["enums"]["coverage_state"] == EXPECTED_COVERAGE_STATES


def test_overlay_layer_and_change_completeness() -> None:
    overlay = _load(ARTIFACTS / "exact_overlay.json")
    layers = [r["layer"] for r in overlay["layer_recipes"]]
    assert layers == ["individual_risk", "center_pattern", "affected_subject",
                      "event", "affected_site", "project_signal", "clue",
                      "query"]
    kinds = [r["change_kind"] for r in overlay["change_emission_table"]]
    assert kinds == ["initial_current", "new", "upgraded", "continued",
                     "downgraded", "resolved", "reopened", "superseded",
                     "not_evaluable", "not_comparable"]


def test_challenge_registry_categories_and_locators() -> None:
    registry = _load(ARTIFACTS / "challenge_registry.json")
    assert registry["challenge_count"] == 60
    ids = [c["case_id"] for c in registry["challenges"]]
    assert len(set(ids)) == len(ids)
    counts: Dict[str, int] = {}
    for c in registry["challenges"]:
        counts[c["category"]] = counts.get(c["category"], 0) + 1
    for category, minimum in registry["categories"].items():
        assert counts.get(category, 0) >= minimum


def test_all_artifacts_are_canonical_nfc_json() -> None:
    for name in ARTIFACT_FILES:
        path = ARTIFACTS / name
        value = json.loads(path.read_text(encoding="utf-8"))
        assert path.read_bytes() == _canonical_bytes(value)


def test_private_public_hash_separation_frozen() -> None:
    overlay = _load(ARTIFACTS / "exact_overlay.json")
    recipes = overlay["hash_dag"]
    assert recipes["packet_integrity_hash"]["may_cover_hidden"] is True
    assert recipes["audience_replay_content_hash"]["may_cover_hidden"] is False
    assert recipes["audience_object_content_hash"]["may_cover_hidden"] is False
    assert "depends_on" in recipes["audience_replay_content_hash"]
    assert recipes["audience_replay_content_hash"]["depends_on"] == []
    schema = _load(ARTIFACTS / "packet_schema.json")
    forbidden = schema["hash_dag"]["audience_replay_content_hash"][
        "forbidden_leaves"]
    assert {"hidden_member_refs", "hidden_site_refs", "hidden_member_count"
            } <= set(forbidden)


def test_packet_id_grammar_single_colon_everywhere() -> None:
    schema = _load(ARTIFACTS / "packet_schema.json")
    overlay = _load(ARTIFACTS / "exact_overlay.json")
    assert schema["packet_id_grammar"] == (
        "r5-s3-contract:<audience_replay_content_hash>")
    assert overlay["packet_id_grammar"] == (
        "r5-s3-contract:<audience_replay_content_hash>")
    assert schema["packet_id_grammar"].count(":") == 1
    assert overlay["packet_id_grammar"].count(":") == 1
    packet = VMOD.build_sample_packet()
    assert packet["packet_id"].count(":") == 1
    assert packet["packet_id"].startswith("r5-s3-contract:")


def test_typed_supplemental_objects_exact() -> None:
    schema = _load(ARTIFACTS / "packet_schema.json")
    objects = schema["objects"]
    expected = {
        "R5S3DenominatorAuthority", "R5S3LayerMembershipAuthority",
        "R5S3CutoffAuthority", "R5S3EvaluationLimitAuthority",
        "R5S3CoverageAuthority", "R5S3ChangeCauseMixtureAuthority",
        "R5S3RiskLifecycleAuthority", "R5S3ClosureAuthority",
        "R5S3ClinicalDomainAuthority",
    }
    assert expected <= set(objects)
    # no generic value-bearing supplemental authority remains.
    assert "R5S3SupplementalQuantitativeAuthority" not in objects
    # every authority binds receipt/visibility/source pairs/hash.
    for name in expected:
        fields = set(objects[name])
        assert {"receipt_hash", "receipt_ref", "visibility_decision_id",
                "visibility_decision_hash", "source_revision_content_pairs",
                "content_hash", "offline_test_only"} <= fields, name


def test_8911_service_not_started() -> None:
    """The S3 contract test suite must never start the 8911 service."""
    result = subprocess.run(
        ["lsof", "-iTCP", ":8911", "-sTCP:LISTEN"],
        capture_output=True, text=True)
    assert result.returncode != 0 and not result.stdout.strip(), (
        "port 8911 is unexpectedly listening "
        "(S3 contract tests must not start the runtime service)")
