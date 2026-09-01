"""R8 G2 synthetic macOS source_access_profile contract tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = WORKBENCH_ROOT / "deploy" / "medical_monitoring_local"
if str(DEPLOY_DIR) not in sys.path:
    sys.path.insert(0, str(DEPLOY_DIR))

import source_access_profile as sap  # noqa: E402


def test_macos_synthetic_profile_proves_read_only_and_observable_denial() -> None:
    evidence = sap.run_synthetic_source_access_profile(
        read_path="documents/allowed.txt",
        write_path="cache/forbidden.txt",
        started_at="2026-08-31T01:00:00Z",
        ended_at="2026-08-31T01:00:01Z",
    )

    assert evidence["profile"] == {
        "id": sap.SOURCE_ACCESS_PROFILE_ID,
        "version": "1",
        "target_system": "macOS",
        "adapter": "synthetic-shadow-root",
        "source_kind": "synthetic_shadow_root",
        "root_ref": sap.DEFAULT_ROOT_REF,
        "implementation": "macos_filesystem",
        "access_mode": "read_only",
        "available": True,
    }
    assert evidence["policy"] == {
        "read": "allow",
        "write": "deny",
        "write_probe_scope": "synthetic_only",
        "policy_version": sap.POLICY_VERSION,
    }
    assert evidence["read"]["status"] == "allowed"
    assert evidence["read"]["observed"] is True
    assert evidence["write"]["status"] == "denied"
    assert evidence["write"]["synthetic_only"] is True
    assert evidence["write"]["mutation_applied"] is False
    assert evidence["monitoring"]["write_event_observed"] is True
    assert evidence["monitoring"]["events_observed"] == 1
    assert evidence["monitoring"]["events"][0]["decision"] == "denied"
    assert evidence["source"]["before"] == evidence["source"]["after"]
    assert evidence["source"]["unchanged"] is True
    assert evidence["status"] == "evaluable"
    assert evidence["not_evaluable_reasons"] == []
    assert sap.validate_source_access_evidence(evidence) == evidence


def test_synthetic_write_denial_cannot_mutate_or_probe_a_real_path() -> None:
    root = sap.SyntheticShadowRoot({"documents/allowed.txt": b"source"})
    before = root.tree()

    with pytest.raises(sap.SourceWriteDenied):
        root.write_bytes("documents/new.txt", b"must not appear")

    assert root.tree() == before
    assert root.write_attempts[0]["decision"] == "denied"
    assert root.write_attempts[0]["mutation_applied"] is False
    with pytest.raises(sap.SourceAccessProfileError, match="shadow_root_must_be_synthetic"):
        sap.run_synthetic_source_access_profile(shadow_root=Path("/tmp/not-a-source"))  # type: ignore[arg-type]


def test_write_event_requires_complete_monitoring_not_tree_hash_only() -> None:
    evidence = sap.run_synthetic_source_access_profile(tree_hash_only=True)

    assert evidence["source"]["unchanged"] is True
    assert evidence["monitoring"]["write_event_observed"] is True
    assert evidence["status"] == "not_evaluable"
    assert evidence["not_evaluable_reasons"] == ["tree_hash_only_insufficient"]


def test_memory_fixture_cannot_masquerade_as_target_macos_profile() -> None:
    evidence = sap.run_synthetic_source_access_profile(
        shadow_root=sap.SyntheticShadowRoot.default()
    )
    assert evidence["profile"]["implementation"] == "memory"
    assert evidence["status"] == "not_evaluable"
    assert "target_filesystem_not_exercised" in evidence["not_evaluable_reasons"]


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"profile_available": False}, "profile_unavailable"),
        ({"monitor_available": False}, "monitor_unavailable"),
        ({"monitor_scope_complete": False}, "monitor_scope_incomplete"),
        ({"terminal_status": "unknown"}, "monitor_terminal_status_unknown"),
        ({"terminal_status": "failed"}, "monitor_exit_not_complete"),
        ({"leak_conditions": ["unmonitored_metadata_path"]}, "leak_conditions_present"),
    ],
)
def test_monitoring_failure_is_fail_closed_not_evaluable(kwargs: dict[str, object], reason: str) -> None:
    evidence = sap.run_synthetic_source_access_profile(**kwargs)

    assert evidence["status"] == "not_evaluable"
    assert reason in evidence["not_evaluable_reasons"]
    assert sap.replay_source_access_evidence(evidence).valid is True
    assert sap.replay_source_access_evidence(evidence).status == "not_evaluable"


def test_profile_digest_replay_rejects_tampering() -> None:
    evidence = sap.run_synthetic_source_access_profile()
    tampered = json.loads(json.dumps(evidence, ensure_ascii=False))
    tampered["monitoring"]["events"][0]["path"] = "other/path.txt"

    replay = sap.replay_source_access_evidence(tampered)
    assert replay.valid is False
    assert "profile_digest_mismatch" in replay.errors
    with pytest.raises(sap.SourceAccessProfileError, match="profile_digest_mismatch"):
        sap.replay_source_access_evidence(tampered, strict=True)

def test_validator_rejects_relabeling_incomplete_monitoring_as_evaluable() -> None:
    evidence = sap.run_synthetic_source_access_profile(monitor_available=False)
    tampered = json.loads(json.dumps(evidence, ensure_ascii=False))
    tampered["status"] = "evaluable"
    tampered["not_evaluable_reasons"] = []
    digest_body = json.loads(json.dumps(tampered, ensure_ascii=False))
    digest_body["profile_digest"] = ""
    tampered["profile_digest"] = sap.digest_ref(digest_body)

    with pytest.raises(sap.SourceAccessProfileError, match="status_inconsistent"):
        sap.validate_source_access_evidence(tampered)


def test_validator_rejects_absolute_or_escape_paths() -> None:
    with pytest.raises(sap.SourceAccessProfileError, match="relative_posix"):
        sap.SyntheticShadowRoot({"/absolute.txt": b"x"})
    with pytest.raises(sap.SourceAccessProfileError, match="escapes_shadow_root"):
        sap.SyntheticShadowRoot({"../outside.txt": b"x"})
    with pytest.raises(sap.SourceAccessProfileError, match="shadow_root_must_be_synthetic"):
        sap.run_synthetic_source_access_profile(shadow_root="/real/source")  # type: ignore[arg-type]


def test_profile_digest_is_deterministic_for_fixed_synthetic_inputs() -> None:
    kwargs = {
        "started_at": "2026-08-31T02:00:00Z",
        "ended_at": "2026-08-31T02:00:01Z",
    }
    first = sap.run_synthetic_source_access_profile(**kwargs)
    second = sap.run_synthetic_source_access_profile(**kwargs)

    assert first == second
    assert first["profile_digest"].startswith("sha256:")
    assert sap.replay_source_access_evidence(first, strict=True).valid is True
