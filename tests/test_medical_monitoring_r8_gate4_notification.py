"""R8 G4 synthetic notification focused tests (synthetic/offline).

Contract: reviews/medical_monitoring_r8_gate3_notification_decision_contract_v0_3_20260831.md
Covers terminal projection, idempotent outbox, four capability states, persistent
degradation, navigation-only intent, and fail-closed gates.

Does not start 8911/5174/8984, call models, read real project roots, or modify
deploy/medical_writing_local.
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path

import pytest

WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = WORKBENCH_ROOT / "deploy" / "medical_monitoring_local"

if str(DEPLOY_DIR) not in sys.path:
    sys.path.insert(0, str(DEPLOY_DIR))

import synthetic_notification as notify  # noqa: E402

PROJECT = "opaque-project:synth-notify-001"
ADMISSION = "opaque-admission:synth-adm-001"
RUN = "opaque-run:synth-run-001"
REVISION = "rev-synth-001"
BINDING_DIGEST = "sha256:0000000000000000000000000000000000000000000000000000000000000001"
SOURCE_MANIFEST_DIGEST = "sha256:" + "2" * 64
OUTPUT_MANIFEST_DIGEST = "sha256:" + "3" * 64
APP_VERSION = "synth-app-1"


def _binding(**overrides):
    base = {
        "project_ref": PROJECT,
        "admission_id": ADMISSION,
        "admission_status": "accepted",
        "binding_digest": BINDING_DIGEST,
        "contract_version": notify.CONTRACT_VERSION,
        "app_version": APP_VERSION,
        "registered_project_display_name": "合成演示项目",
        "binding_valid": True,
    }
    base.update(overrides)
    return notify.AdmissionBinding(**base)


def _event(**overrides):
    base = {
        "project_ref": PROJECT,
        "admission_id": ADMISSION,
        "run_id": RUN,
        "terminal_status": "complete",
        "terminal_revision": REVISION,
    }
    base.update(overrides)
    return notify.TerminalEvent(**base)


def _accessibility(**overrides):
    base = {
        "current_terminal_revision": REVISION,
        "binding_digest": BINDING_DIGEST,
        "source_manifest_digest": SOURCE_MANIFEST_DIGEST,
        "output_manifest_digest": OUTPUT_MANIFEST_DIGEST,
        "target_exists": True,
        "result_accessible": True,
        "explanation_accessible": True,
    }
    base.update(overrides)
    return notify.TargetAccessibility(**base)


def _adapter(capability: str = "authorized", **overrides):
    return notify.SyntheticNotificationAdapter(
        capability_by_admission={ADMISSION: capability},
        default_capability=capability,
        **overrides,
    )


def _process(capability: str = "authorized", **event_overrides):
    store = notify.NotificationStore()
    adapter = _adapter(capability)
    event = _event(**event_overrides)
    return notify.process_terminal_event(
        event,
        _binding(),
        _accessibility(),
        store,
        adapter,
    ), store, adapter, event


def _port_connect_ex(port: int) -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.2)
    try:
        return sock.connect_ex(("127.0.0.1", port))
    finally:
        sock.close()


def test_ports_stopped() -> None:
    for port in (8911, 5174, 8984):
        assert _port_connect_ex(port) != 0


def test_non_terminal_statuses_fail_closed_without_fact() -> None:
    for status in ("streaming", "checkpoint", "queued", "running"):
        result, store, _, _ = _process(terminal_status=status)
        assert result.status == "fail_closed"
        assert result.reason == "non_terminal_status"
        assert result.fact is None
        assert store.save_count == 0


def test_complete_projects_to_analysis_complete_when_result_accessible() -> None:
    result, _, _, event = _process()
    assert result.status == "ok"
    assert result.created is True
    assert result.fact is not None
    assert event.terminal_status == "complete"
    assert result.fact["notification_status"] == "analysis_complete"
    assert result.fact["user_copy"] == notify.USER_COPY["analysis_complete"]


def test_complete_without_result_access_fails_closed() -> None:
    store = notify.NotificationStore()
    result = notify.process_terminal_event(
        _event(),
        _binding(),
        _accessibility(result_accessible=False),
        store,
        _adapter(),
    )
    assert result.status == "fail_closed"
    assert result.reason == "target_not_accessible"
    assert store.get_fact(_event().identity_key) is None


@pytest.mark.parametrize(
    ("upstream", "notification_key"),
    [
        ("failed", "failed"),
        ("partial", "partial"),
        ("final_partial", "final_partial"),
        ("truncated", "truncated"),
        ("timed_out", "timed_out"),
        ("cancelled", "cancelled"),
        ("interrupted", "interrupted"),
        ("blocked", "blocked"),
    ],
)
def test_frozen_terminal_statuses_use_g3_chinese_templates(
    upstream: str, notification_key: str
) -> None:
    accessibility = _accessibility(
        result_accessible=upstream == "partial",
        explanation_accessible=True,
    )
    store = notify.NotificationStore()
    result = notify.process_terminal_event(
        _event(terminal_status=upstream),
        _binding(),
        accessibility,
        store,
        _adapter(),
    )
    assert result.status == "ok"
    assert result.fact is not None
    assert result.fact["notification_status"] == notification_key
    assert result.fact["user_copy"] == notify.USER_COPY[notification_key]


def test_idempotent_outbox_and_in_app_on_replay() -> None:
    result1, store, adapter, event = _process()
    assert result1.created is True
    outbox1 = store.get_outbox(event.identity_key)
    in_app1 = store.get_in_app(event.identity_key)
    assert outbox1 is not None
    assert in_app1 is not None
    assert in_app1["persistent"] is True

    result2 = notify.process_terminal_event(
        event,
        _binding(),
        _accessibility(),
        store,
        adapter,
    )
    assert result2.status == "ok"
    assert result2.created is False
    assert result2.fact["fact_digest"] == result1.fact["fact_digest"]
    outbox2 = store.get_outbox(event.identity_key)
    assert outbox2 == outbox1
    assert store.save_count == 2
    assert len(adapter.system_attempts) == 1
    assert outbox2["attempts"] == 1


@pytest.mark.parametrize("capability", notify.CAPABILITY_STATES)
def test_four_capability_states_persist_in_app_record(capability: str) -> None:
    result, store, adapter, event = _process(capability)
    assert result.status == "ok"
    in_app = store.get_in_app(event.identity_key)
    assert in_app is not None
    assert in_app["persistent"] is True
    assert result.fact["capability_state"] == capability
    if capability == "authorized":
        assert len(adapter.system_attempts) == 1
        assert result.fact["channel_evidence"] == "queued"
    else:
        assert len(adapter.system_attempts) == 0
        assert result.fact["channel_evidence"] == "unknown"


def test_persistent_degradation_keeps_in_app_when_denied() -> None:
    result, store, _, event = _process("denied", terminal_status="failed")
    assert result.status == "ok"
    assert store.get_in_app(event.identity_key) is not None
    assert result.fact["channel_evidence"] == "unknown"


def test_navigation_intent_is_navigate_only_and_repeatable() -> None:
    result, store, adapter, _ = _process()
    fact = result.fact
    nav1 = notify.build_navigation_intent(
        fact, _binding(), _accessibility(), store, adapter, click_count=3
    )
    assert nav1.status == "ok"
    assert nav1.intent is not None
    assert nav1.intent["action"] == "navigate_only"
    assert nav1.intent["run_id"] == RUN
    assert len(adapter.navigation_side_effects) == 3
    for effect in adapter.navigation_side_effects:
        assert effect["kind"] == "navigation_click"
        assert effect["intent"]["action"] == "navigate_only"

    nav2 = notify.build_navigation_intent(
        fact, _binding(), _accessibility(), store, adapter, click_count=1
    )
    assert nav2.intent == nav1.intent


def test_navigation_blocked_on_binding_mismatch() -> None:
    result, store, adapter, _ = _process()
    nav = notify.build_navigation_intent(
        result.fact,
        _binding(binding_digest="sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
        _accessibility(),
        store,
        adapter,
    )
    assert nav.status == "blocked"
    assert nav.user_message == notify.NAVIGATION_BLOCKED_MESSAGE


def test_invalid_binding_never_creates_fact_or_navigation() -> None:
    store = notify.NotificationStore()
    adapter = _adapter()
    result = notify.process_terminal_event(
        _event(), _binding(binding_valid=False), _accessibility(), store, adapter
    )
    assert result.status == "fail_closed"
    assert result.reason == "binding_invalid"
    assert store.save_count == 0


@pytest.mark.parametrize("field", ("authoritative", "frozen"))
def test_non_authoritative_or_unfrozen_terminal_never_creates_fact(field: str) -> None:
    result, store, _, _ = _process(**{field: False})
    assert result.status == "fail_closed"
    assert result.reason == "terminal_not_authoritative_frozen"
    assert store.save_count == 0


def test_invalid_capability_fails_closed_without_fact() -> None:
    store = notify.NotificationStore()
    adapter = notify.SyntheticNotificationAdapter(default_capability="authorized")
    adapter._capabilities[ADMISSION] = "invalid"
    result = notify.process_terminal_event(
        _event(), _binding(), _accessibility(), store, adapter
    )
    assert result.status == "fail_closed"
    assert result.reason == "capability_invalid"
    assert store.save_count == 0


@pytest.mark.parametrize("evidence", ("queued", "accepted_by_platform", "presented", "unknown"))
def test_authorized_channel_evidence_is_preserved_without_claim_upgrade(evidence: str) -> None:
    store = notify.NotificationStore()
    adapter = notify.SyntheticNotificationAdapter(
        capability_by_admission={ADMISSION: "authorized"},
        channel_evidence_by_capability={"authorized": evidence},
    )
    result = notify.process_terminal_event(
        _event(), _binding(), _accessibility(), store, adapter
    )
    assert result.fact["channel_evidence"] == evidence
    assert len(adapter.system_attempts) == 1


@pytest.mark.parametrize("admission_status", ("revoked", "re_admission_required"))
def test_revoked_admission_blocks_new_fact_and_navigation(admission_status: str) -> None:
    result, store, adapter, event = _process()
    blocked_binding = _binding(admission_status=admission_status)
    blocked_result = notify.process_terminal_event(
        _event(terminal_revision="rev-blocked"),
        blocked_binding,
        _accessibility(current_terminal_revision="rev-blocked"),
        notify.NotificationStore(),
        _adapter(),
    )
    assert blocked_result.status == "fail_closed"
    assert blocked_result.reason == "admission_blocked"

    nav = notify.build_navigation_intent(
        result.fact, blocked_binding, _accessibility(), store, adapter
    )
    assert nav.status == "blocked"


def test_conflicting_terminal_status_is_fail_closed() -> None:
    result1, store, adapter, event = _process(terminal_status="failed")
    assert result1.status == "ok"
    conflict = notify.process_terminal_event(
        _event(terminal_status="complete"),
        _binding(),
        _accessibility(),
        store,
        adapter,
    )
    assert conflict.status == "fail_closed"
    assert conflict.reason == "terminal_status_conflict"
    assert len(store.conflicts) == 1


def test_out_of_order_terminal_revision_fails_closed() -> None:
    store = notify.NotificationStore()
    adapter = _adapter()
    latest_revision = "rev-synth-002"
    latest = notify.process_terminal_event(
        _event(terminal_revision=latest_revision),
        _binding(),
        _accessibility(current_terminal_revision=latest_revision),
        store,
        adapter,
    )
    assert latest.status == "ok"

    stale = notify.process_terminal_event(
        _event(terminal_revision=REVISION),
        _binding(),
        _accessibility(current_terminal_revision=latest_revision),
        store,
        adapter,
    )
    assert stale.status == "fail_closed"
    assert stale.reason == "terminal_revision_stale"

    conflicting = notify.process_terminal_event(
        _event(terminal_revision=REVISION),
        _binding(),
        _accessibility(current_terminal_revision=REVISION),
        store,
        adapter,
    )
    assert conflicting.status == "fail_closed"
    assert conflicting.reason == "terminal_revision_conflict"
    assert len(store.conflicts) == 1


@pytest.mark.parametrize(
    "accessibility",
    [
        _accessibility(current_terminal_revision="rev-synth-next"),
        _accessibility(target_exists=False),
        _accessibility(source_manifest_digest="sha256:" + "4" * 64),
        _accessibility(output_manifest_digest="sha256:" + "5" * 64),
    ],
)
def test_navigation_blocks_when_current_target_changed(accessibility) -> None:
    result, store, adapter, _ = _process()
    nav = notify.build_navigation_intent(
        result.fact, _binding(), accessibility, store, adapter
    )
    assert nav.status == "blocked"
    assert nav.user_message == notify.NAVIGATION_BLOCKED_MESSAGE
    assert not adapter.navigation_side_effects


def test_system_copy_has_no_forbidden_tokens() -> None:
    result, _, _, _ = _process()
    system_copy = result.fact["system_copy"]
    combined = system_copy["title"] + system_copy["body"]
    for token in ("opaque-project:", "opaque-admission:", "sha256:", "8911"):
        assert token not in combined


def test_validate_notification_fact_accepts_canonical_fact() -> None:
    result, _, _, _ = _process()
    validated = notify.validate_notification_fact(result.fact)
    assert validated["fact_digest"] == result.fact["fact_digest"]


def test_validate_notification_fact_rejects_forged_projection() -> None:
    result, _, _, _ = _process()
    forged = dict(result.fact)
    forged["notification_status"] = "failed"
    forged["fact_digest"] = notify.digest_ref(
        {key: value for key, value in forged.items() if key != "fact_digest"}
    )
    with pytest.raises(notify.NotificationError, match="terminal_projection_mismatch"):
        notify.validate_notification_fact(forged)


def test_channel_failure_does_not_change_upstream_terminal_status() -> None:
    event = _event(terminal_status="failed")
    store = notify.NotificationStore()
    adapter = notify.SyntheticNotificationAdapter(
        capability_by_admission={ADMISSION: "authorized"},
        channel_evidence_by_capability={"authorized": "unknown"},
    )
    result = notify.process_terminal_event(
        event,
        _binding(),
        _accessibility(),
        store,
        adapter,
    )
    assert result.status == "ok"
    assert result.fact["terminal_status"] == "failed"
    assert result.fact["channel_evidence"] == "unknown"


def test_channel_exception_is_contained_and_replay_does_not_retry() -> None:
    class RaisingAdapter(notify.SyntheticNotificationAdapter):
        def attempt_system_notification(self, fact, capability_state):
            self._system_attempts.append({"attempted": True})
            raise RuntimeError("synthetic-channel-down")

    store = notify.NotificationStore()
    adapter = RaisingAdapter(
        capability_by_admission={ADMISSION: "authorized"},
        default_capability="authorized",
    )
    first = notify.process_terminal_event(
        _event(), _binding(), _accessibility(), store, adapter
    )
    second = notify.process_terminal_event(
        _event(), _binding(), _accessibility(), store, adapter
    )
    assert first.status == second.status == "ok"
    assert first.fact["terminal_status"] == "complete"
    assert first.fact["channel_evidence"] == "unknown"
    assert len(adapter.system_attempts) == 1
    assert store.get_outbox(_event().identity_key)["attempts"] == 1
