"""Synthetic/offline tests for the R7 Slice-09C project audit ledger."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from mm_r7.project_audit import (
    EVENT_KIND_ALLOWLIST,
    PROJECT_AUDIT_GENESIS,
    ProjectAuditError,
    ProjectAuditEventKind,
    ProjectAuditLedger,
    canonical_digest,
    canonical_json,
)
from mm_r7.project_backup import OP_BACKUP, OperationLedger


NOW = "2026-08-30T04:00:00Z"
PRINCIPAL = "p" * 64
AUTHORIZATION = "a" * 64


def _ledger(tmp_path: Path, *, ids=("event-1", "event-2")) -> ProjectAuditLedger:
    event_ids = iter(ids)
    return ProjectAuditLedger(
        tmp_path,
        clock=lambda: NOW,
        event_id_factory=lambda: next(event_ids),
    )


def _payload(kind: str, *, operation: str = "operation-1", token: str = "boundary-1") -> dict:
    required = {
        "boundary_intent": {
            "operation": operation,
            "boundary_token": token,
            "expected_state": "requested",
            "before_digest": "before",
        },
        "boundary_committed": {
            "operation": operation,
            "boundary_token": token,
            "observed_durable_phase": "committed",
            "after_digest": "after",
        },
        "boundary_verified": {
            "operation": operation,
            "boundary_token": token,
            "verifier_outcome": "record_complete",
            "after_digest": "after",
        },
        "verification_started": {
            "verifier_version": "verifier-v1",
            "snapshot_fingerprint": "snapshot-1",
            "before_digest": "before",
        },
        "verification_completed": {
            "verifier_version": "verifier-v1",
            "snapshot_fingerprint": "snapshot-1",
            "verification_result": "record_complete",
        },
        "recovery_classified": {
            "operation": operation,
            "observed_durable_phase": "intent",
            "classification": "resume",
        },
        "recovery_completed": {
            "operation": operation,
            "terminal_outcome": "completed",
            "after_digest": "after",
        },
        "triage_retained": {
            "operation": operation,
            "observed_durable_phase": "rollback",
            "reason_enum": "ambiguous_boundary",
        },
        "rollback_release_intent": {
            "operation": operation,
            "verified_event_id": "event-verified",
            "rollback_digest": "rollback-digest",
        },
        "rollback_evidence_released": {
            "operation": operation,
            "release_intent_id": "event-release-intent",
            "outcome": "released",
        },
        "rollback_evidence_release_failed": {
            "operation": operation,
            "release_intent_id": "event-release-intent",
            "outcome": "retained",
        },
    }
    return required[kind]


def test_project_chains_have_independent_heads_and_canonical_bytes(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path, ids=("a-1", "b-1", "a-2"))
    try:
        first = ledger.append_event(
            "project-a",
            ProjectAuditEventKind.VERIFICATION_STARTED,
            {"snapshot_fingerprint": "snapshot-1", "verifier_version": "v1", "before_digest": "b"},
            principal_snapshot_hash=PRINCIPAL,
            authorization_decision_hash=AUTHORIZATION,
        )
        other = ledger.append_event(
            "project-b",
            "verification_started",
            {"before_digest": "b", "verifier_version": "v1", "snapshot_fingerprint": "snapshot-1"},
            principal_snapshot_hash=PRINCIPAL,
            authorization_decision_hash=AUTHORIZATION,
        )
        second = ledger.append_event(
            "project-a",
            "verification_completed",
            {"verifier_version": "v1", "snapshot_fingerprint": "snapshot-1", "verification_result": "record_complete"},
            principal_snapshot_hash=PRINCIPAL,
            authorization_decision_hash=AUTHORIZATION,
        )
        assert first.project_seq == other.project_seq == 1
        assert second.project_seq == 2
        assert first.previous_hash == PROJECT_AUDIT_GENESIS
        assert ledger.head("project-a").head_hash == second.chain_hash
        assert ledger.head("project-b").head_hash == other.chain_hash
        assert ledger.verify_chain("project-a") == (True, None, 2)
        assert ledger.verify_chain("project-b") == (True, None, 1)
        assert ledger.verify_chain() == (True, None, 3)
        assert canonical_json({"z": ["合成", 1], "a": {"b": True, "a": None}}) == '{"a":{"a":null,"b":true},"z":["合成",1]}'
        assert canonical_digest({"a": 1, "b": 2}) == canonical_digest({"b": 2, "a": 1})
    finally:
        ledger.close()


def test_fixed_per_kind_allowlist_rejects_missing_and_extra_fields(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    try:
        for kind, allowed in EVENT_KIND_ALLOWLIST.items():
            assert _payload(kind).keys() <= allowed
        with pytest.raises(ProjectAuditError) as missing:
            ledger.append_event(
                "project-a",
                "boundary_intent",
                {"operation": "op", "boundary_token": "bt", "expected_state": "requested"},
                principal_snapshot_hash=PRINCIPAL,
                authorization_decision_hash=AUTHORIZATION,
            )
        assert missing.value.code == "missing_payload_field"
        with pytest.raises(ProjectAuditError) as extra:
            ledger.append_event(
                "project-a",
                "verification_started",
                {**_payload("verification_started"), "actor": "client"},
                principal_snapshot_hash=PRINCIPAL,
                authorization_decision_hash=AUTHORIZATION,
            )
        assert extra.value.code == "unknown_payload_field"
        with pytest.raises(ProjectAuditError):
            ledger.append_event(
                "project-a",
                "verification_started",
                _payload("verification_started"),
                principal_snapshot_hash=PRINCIPAL,
                authorization_decision_hash=AUTHORIZATION,
                occurred_at="2026-08-30T04:00:00",
            )
    finally:
        ledger.close()


def test_boundary_and_event_id_replay_are_idempotent_but_conflicts_fail(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path, ids=("event-1", "event-2", "event-3"))
    try:
        payload = _payload("boundary_intent")
        first = ledger.append_event(
            "project-a", "boundary_intent", payload,
            principal_snapshot_hash=PRINCIPAL,
            authorization_decision_hash=AUTHORIZATION,
        )
        replay = ledger.append_event(
            "project-a", "boundary_intent", payload,
            principal_snapshot_hash=PRINCIPAL,
            authorization_decision_hash=AUTHORIZATION,
        )
        assert replay.replayed is True
        assert replay.event_id == first.event_id
        assert ledger.head("project-a").head_seq == 1
        with pytest.raises(ProjectAuditError) as conflict:
            ledger.append_event(
                "project-a", "boundary_intent",
                {**payload, "expected_state": "different"},
                principal_snapshot_hash=PRINCIPAL,
                authorization_decision_hash=AUTHORIZATION,
            )
        assert conflict.value.code == "project_audit_event_conflict"
        with pytest.raises(ProjectAuditError):
            ledger.append_event(
                "project-a", "verification_started", _payload("verification_started"),
                event_id=first.event_id,
                principal_snapshot_hash=PRINCIPAL,
                authorization_decision_hash=AUTHORIZATION,
            )
    finally:
        ledger.close()


def test_head_cas_and_direct_tamper_detection_fail_closed(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path, ids=("event-1", "event-2"))
    try:
        first = ledger.append_event(
            "project-a", "verification_started", _payload("verification_started"),
            principal_snapshot_hash=PRINCIPAL,
            authorization_decision_hash=AUTHORIZATION,
        )
        with pytest.raises(ProjectAuditError) as cas:
            ledger.append_event(
                "project-a", "verification_completed", _payload("verification_completed"),
                principal_snapshot_hash=PRINCIPAL,
                authorization_decision_hash=AUTHORIZATION,
                expected_head_seq=0,
                expected_head_hash=PROJECT_AUDIT_GENESIS,
            )
        assert cas.value.code == "project_audit_head_conflict"
        assert ledger.verify_chain("project-a") == (True, None, 1)
        with pytest.raises(sqlite3.IntegrityError):
            ledger.connection.execute(
                "UPDATE project_audit_events SET payload_json=? WHERE event_id=?",
                (json.dumps(_payload("verification_started")), first.event_id),
            )
        with pytest.raises(sqlite3.IntegrityError):
            ledger.connection.execute(
                "DELETE FROM project_audit_events WHERE event_id=?",
                (first.event_id,),
            )
        # Fault injection models an out-of-band copy whose append-only
        # triggers were removed; the verifier must still detect corruption.
        ledger.connection.execute("DROP TRIGGER project_audit_events_no_update")
        ledger.connection.execute(
            "UPDATE project_audit_events SET payload_json=? WHERE event_id=?",
            (json.dumps(_payload("verification_started")), first.event_id),
        )
        assert ledger.verify_chain("project-a")[0] is False
        ledger.connection.execute(
            "UPDATE project_audit_events SET payload_json=? WHERE event_id=?",
            (canonical_json(_payload("verification_started")), first.event_id),
        )
        ledger.connection.execute(
            "UPDATE project_audit_heads SET head_hash=? WHERE canonical_project_id=?",
            ("0" * 64, "project-a"),
        )
        assert ledger.verify_chain("project-a")[0] is False
    finally:
        ledger.close()


def test_operation_projection_and_event_append_share_one_transaction(tmp_path: Path) -> None:
    operations = OperationLedger(tmp_path)
    reserved = operations.create_or_replay(OP_BACKUP, "same-key", "project-a")
    operations.close()
    failures = {"enabled": True}

    def failure_hook(point: str) -> None:
        if failures["enabled"] and point == "event_insert.before":
            raise RuntimeError("synthetic event write failure")

    ledger = ProjectAuditLedger(tmp_path, clock=lambda: NOW, event_id_factory=lambda: "event-1", failure_hook=failure_hook)
    payload = _payload("boundary_intent", operation=reserved.operation_id)
    try:
        with pytest.raises(RuntimeError):
            ledger.append_event_with_operation(
                "project-a", "boundary_intent", payload,
                operation_id=reserved.operation_id,
                operation_update={"status": "collecting", "progress_percent": 20, "current_step": "collecting"},
                principal_snapshot_hash=PRINCIPAL,
                authorization_decision_hash=AUTHORIZATION,
            )
        assert ledger.head("project-a").head_seq == 0
        assert ledger.operation_projection(reserved.operation_id)["status"] == "requested"
        failures["enabled"] = False
        event = ledger.append_event_with_operation(
            "project-a", "boundary_intent", payload,
            operation_id=reserved.operation_id,
            operation_update={"status": "collecting", "progress_percent": 20, "current_step": "collecting"},
            principal_snapshot_hash=PRINCIPAL,
            authorization_decision_hash=AUTHORIZATION,
        )
        assert event.project_seq == 1
        projection = ledger.operation_projection(reserved.operation_id)
        assert projection["status"] == "collecting"
        assert projection["progress_percent"] == 20
        assert ledger.verify_chain("project-a") == (True, None, 1)
    finally:
        ledger.close()


def test_operation_projection_rejects_cross_project_and_immutable_identity(tmp_path: Path) -> None:
    operations = OperationLedger(tmp_path)
    reserved = operations.create_or_replay(OP_BACKUP, "same-key", "project-a")
    operations.close()
    ledger = _ledger(tmp_path)
    try:
        payload = _payload("boundary_intent", operation=reserved.operation_id)
        with pytest.raises(ProjectAuditError) as cross_project:
            ledger.append_event_with_operation(
                "project-b", "boundary_intent", payload,
                operation_id=reserved.operation_id,
                operation_update={"status": "collecting"},
                principal_snapshot_hash=PRINCIPAL,
                authorization_decision_hash=AUTHORIZATION,
            )
        assert cross_project.value.code == "operation_project_mismatch"
        with pytest.raises(ProjectAuditError) as immutable:
            ledger.append_event_with_operation(
                "project-a", "boundary_intent", payload,
                operation_id=reserved.operation_id,
                operation_update={"canonical_project_id": "project-b"},
                principal_snapshot_hash=PRINCIPAL,
                authorization_decision_hash=AUTHORIZATION,
            )
        assert immutable.value.code == "operation_identity_immutable"
        assert ledger.verify_chain() == (True, None, 0)
    finally:
        ledger.close()


def test_project_audit_ledger_rejects_r1_store_and_forbidden_file_target(tmp_path: Path) -> None:
    wrong_root = tmp_path / "wrong"
    wrong_root.mkdir()
    wrong_db = wrong_root / "backup_operations.sqlite3"
    connection = sqlite3.connect(wrong_db)
    connection.executescript(
        "CREATE TABLE audit_events(seq INTEGER); CREATE TABLE audit_chain_head(singleton INTEGER);"
    )
    connection.close()
    with pytest.raises(ProjectAuditError) as wrong_store:
        ProjectAuditLedger(wrong_root)
    assert wrong_store.value.code == "wrong_audit_store"
    with pytest.raises(ProjectAuditError) as wrong_path:
        ProjectAuditLedger(tmp_path / "monitoring_runtime.sqlite3")
    assert wrong_path.value.code == "invalid_root_ledger_path"


def test_all_frozen_event_kinds_and_nonfinite_payloads_are_checked(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path, ids=tuple("event-%02d" % index for index in range(20)))
    try:
        for index, kind in enumerate(EVENT_KIND_ALLOWLIST):
            event = ledger.append_event(
                "project-a",
                kind,
                _payload(kind, operation="operation-%d" % index, token="boundary-%d" % index),
                principal_snapshot_hash=PRINCIPAL,
                authorization_decision_hash=AUTHORIZATION,
            )
            assert event.event_kind == kind
        assert ledger.verify_chain("project-a") == (True, None, len(EVENT_KIND_ALLOWLIST))
        with pytest.raises(ProjectAuditError) as nonfinite:
            ledger.append_event(
                "project-b",
                "boundary_intent",
                {**_payload("boundary_intent"), "package_digest": float("nan")},
                principal_snapshot_hash=PRINCIPAL,
                authorization_decision_hash=AUTHORIZATION,
            )
        assert nonfinite.value.code == "payload_not_canonical"
    finally:
        ledger.close()
