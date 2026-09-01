"""R7 Slice-07C-3/4 synthetic/offline launch/publication registry tests.

The suite exercises only the project-scoped SQLite registry and its migration
boundary.  It never starts a service, invokes a provider, or reads a real
project.  Public history is checked as an exact Chinese-facing projection;
publication internals are exercised only through the durable store contract.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Optional
import pytest

from conftest import POC_ROOT, SRC_DIR
from fixtures_run_setup import (
    CURRENT_SNAPSHOT_REF,
    MODE_DAILY,
    MODE_POST_LOCK_PRE_CFDI,
    MODE_PRE_LOCK,
    OTHER_PROJECT_ID,
    PROJECT_ID,
    make_catalog,
)
from mm_r7.launch_registry import (
    BASIS_FULL,
    BASIS_INCREMENTAL,
    DEFAULT_HISTORY_LIMIT,
    PUBLICATION_REVISION,
    PUBLICATION_STATE_AVAILABLE,
    PUBLICATION_STATE_BLOCKED,
    PUBLICATION_STATE_PUBLISHING,
    PUBLICATION_STATE_RECOVERABLE_FAILED,
    SCHEMA_VERSION,
    SCHEMA_VERSION_V1,
    STATE_COMPLETED,
    STATE_RUNNING,
    STATE_WAITING_START,
    IdempotencyConflictError,
    LaunchRegistry,
    LaunchRegistryError,
    content_digest,
    compute_publication_fingerprint,
)

from mm_r7.migration import (
    MigrationError,
    migrate_launch_registry_staging,
)
from mm_r7.run_setup import RunSetupError


PUBLIC_HISTORY_KEYS = {
    "public_run_token",
    "mode_text",
    "data_cutoff_text",
    "comparison_range_text",
    "run_state",
    "result_available",
    "main_action",
    "status_text",
}
INTERNAL_OR_EXECUTION_KEYS = {
    "project_id",
    "idempotency_key",
    "run_id",
    "request_fingerprint",
    "current_snapshot_token",
    "baseline_token",
    "rule_tokens",
    "manifest_digest",
    "source_revision_id",
    "profile",
    "provider",
    "model",
    "database",
}


def _reserve(
    registry: LaunchRegistry,
    *,
    project_id: str = PROJECT_ID,
    idempotency_key: str,
    mode: str = MODE_DAILY,
    execution_basis: str = BASIS_FULL,
    current_snapshot_token: str = "snapshot:synthetic-current-v1",
    baseline_token: Optional[str] = None,
    rule_tokens: Iterable[str] = (),
    data_cutoff: str = "2026-08-28",
    comparison_range: str = "当前完整数据范围（合成）",
    manifest_digest: Optional[str] = None,
    enforce_in_flight: bool = False,
):
    return registry.reserve(
        project_id,
        idempotency_key=idempotency_key,
        mode=mode,
        execution_basis=execution_basis,
        current_snapshot_token=current_snapshot_token,
        baseline_token=baseline_token,
        rule_tokens=rule_tokens,
        data_cutoff=data_cutoff,
        comparison_range=comparison_range,
        manifest_digest=manifest_digest,
        enforce_in_flight=enforce_in_flight,
    )


def _stage_legacy_launch(
    tmp_path: Path,
    source: Path,
    operation_id: str = "explicit-launch",
) -> Path:
    workspace = tmp_path / ".migration-staging" / operation_id / "workspace"
    workspace.mkdir(parents=True, exist_ok=False)
    staged = workspace / source.name
    shutil.copy2(source, staged)
    return staged


def test_three_modes_create_public_history_without_internal_fields(tmp_path: Path) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        requests = (
            (MODE_DAILY, BASIS_INCREMENTAL, "baseline:synthetic-daily-v1"),
            (MODE_PRE_LOCK, BASIS_FULL, "baseline:synthetic-pre-lock-v1"),
            (MODE_POST_LOCK_PRE_CFDI, BASIS_FULL, None),
        )
        reservations = [
            _reserve(
                registry,
                idempotency_key=f"three-mode-{index}",
                mode=mode,
                execution_basis=basis,
                baseline_token=baseline,
                data_cutoff=f"2026-08-{28 - index:02d}",
            )
            for index, (mode, basis, baseline) in enumerate(requests)
        ]

        assert all(item.replayed is False for item in reservations)
        assert all(item.run_state == STATE_WAITING_START for item in reservations)
        for item in reservations:
            public = item.as_dict()
            assert set(public) == PUBLIC_HISTORY_KEYS | {"replayed"}
            assert set(item.record.public_projection()) == PUBLIC_HISTORY_KEYS
            assert item.record.mode_text in {"日常监查", "锁库前监查", "核查前监查"}
            assert item.record.result_available is False
            assert item.record.main_action == "查看本次进度"
            assert not INTERNAL_OR_EXECUTION_KEYS.intersection(public)

        history = registry.list_history(PROJECT_ID)
        assert len(history) == 3
        assert all(set(item) == PUBLIC_HISTORY_KEYS for item in history)
        assert [item["mode_text"] for item in history] == [
            "核查前监查",
            "锁库前监查",
            "日常监查",
        ]
    finally:
        registry.close()


def test_same_key_replay_normalizes_rule_order_and_conflicts_on_content_change(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        first = _reserve(
            registry,
            idempotency_key="idem-same-content",
            mode=MODE_DAILY,
            execution_basis=BASIS_INCREMENTAL,
            baseline_token="baseline:synthetic-daily-v1",
            rule_tokens=("rule-b", "rule-a", "rule-a"),
        )
        replay = _reserve(
            registry,
            idempotency_key="idem-same-content",
            mode=MODE_DAILY,
            execution_basis=BASIS_INCREMENTAL,
            baseline_token="baseline:synthetic-daily-v1",
            rule_tokens=("rule-a", "rule-b"),
        )
        assert replay.replayed is True
        assert replay.run_id == first.run_id
        assert replay.public_run_token == first.public_run_token
        assert len(registry.list_records(PROJECT_ID)) == 1

        with pytest.raises(IdempotencyConflictError) as error:
            _reserve(
                registry,
                idempotency_key="idem-same-content",
                mode=MODE_DAILY,
                execution_basis=BASIS_FULL,
                baseline_token=None,
                rule_tokens=("rule-a", "rule-b"),
            )
        assert error.value.code == "idempotency_conflict"
        assert error.value.as_error_body()["message"] == "同一幂等请求标识对应的请求内容冲突，拒绝覆盖。"
        assert len(registry.list_history(PROJECT_ID)) == 1
    finally:
        registry.close()


def test_project_namespace_isolation_for_same_key_and_public_token(tmp_path: Path) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3")
    try:
        project_a = _reserve(
            registry,
            project_id=PROJECT_ID,
            idempotency_key="same-key-different-project",
        )
        project_b = _reserve(
            registry,
            project_id=OTHER_PROJECT_ID,
            idempotency_key="same-key-different-project",
        )
        assert project_a.replayed is False
        assert project_b.replayed is False
        assert project_a.run_id != project_b.run_id
        assert project_a.public_run_token != project_b.public_run_token
        assert registry.get_by_idempotency(
            "same-key-different-project", project_id=PROJECT_ID
        ).run_id == project_a.run_id
        assert registry.get_by_idempotency(
            "same-key-different-project", project_id=OTHER_PROJECT_ID
        ).run_id == project_b.run_id

        with pytest.raises(LaunchRegistryError) as error:
            registry.get_by_public_token(
                project_a.public_run_token, project_id=OTHER_PROJECT_ID
            )
        assert error.value.code == "public_run_not_found"
        assert len(registry.list_history(PROJECT_ID)) == 1
        assert len(registry.list_history(OTHER_PROJECT_ID)) == 1
    finally:
        registry.close()


def test_busy_timeout_close_reopen_and_store_closed_boundary(tmp_path: Path) -> None:
    db_path = tmp_path / "launch.sqlite3"
    registry = LaunchRegistry(db_path, project_id=PROJECT_ID, busy_timeout_ms=1_234)
    first = _reserve(registry, idempotency_key="close-reopen")
    assert registry.busy_timeout_ms == 1_234
    assert registry._conn is not None
    assert registry._conn.execute("PRAGMA busy_timeout").fetchone()[0] == 1_234
    registry.close()

    with pytest.raises(LaunchRegistryError) as error:
        registry.list_history(PROJECT_ID)
    assert error.value.code == "store_closed"

    registry.reopen()
    try:
        replay = _reserve(registry, idempotency_key="close-reopen")
        assert replay.replayed is True
        assert replay.run_id == first.run_id
        assert registry.path == db_path
    finally:
        registry.close()


def test_history_limit_is_bounded_and_never_exposes_unbounded_rows(tmp_path: Path) -> None:
    registry = LaunchRegistry(
        tmp_path / "launch.sqlite3",
        project_id=PROJECT_ID,
        default_history_limit=2,
        max_history_limit=2,
    )
    try:
        for index in range(4):
            _reserve(
                registry,
                idempotency_key=f"bounded-{index}",
                data_cutoff=f"2026-08-{index + 1:02d}",
            )
        assert DEFAULT_HISTORY_LIMIT > 2
        assert len(registry.list_history(PROJECT_ID)) == 2
        assert len(registry.list_history(PROJECT_ID, limit=200)) == 2
        assert len(registry.list_records(PROJECT_ID, limit=0)) == 0
    finally:
        registry.close()


def test_start_failure_keeps_one_waiting_run_and_replay_recovers_same_public_token(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        first = _reserve(registry, idempotency_key="start-failure-recovery")
        running = registry.mark_running(first.public_run_token, project_id=PROJECT_ID)
        assert running.run_state == STATE_RUNNING

        waiting = registry.record_start_failure(
            running.public_run_token, project_id=PROJECT_ID
        )
        assert waiting.run_state == STATE_WAITING_START
        assert waiting.run_id == first.run_id
        assert waiting.public_run_token == first.public_run_token

        replay = _reserve(registry, idempotency_key="start-failure-recovery")
        assert replay.replayed is True
        assert replay.run_id == first.run_id
        assert replay.public_run_token == first.public_run_token
        assert replay.run_state == STATE_WAITING_START
        assert len(registry.list_records(PROJECT_ID)) == 1
        assert registry.list_history(PROJECT_ID)[0]["run_state"] == STATE_WAITING_START

        resumed = registry.mark_running(
            replay.public_run_token, project_id=PROJECT_ID
        )
        assert resumed.run_state == STATE_RUNNING
        assert resumed.run_id == first.run_id
    finally:
        registry.close()


def test_successful_start_replay_does_not_create_or_restart_a_second_run(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        first = _reserve(registry, idempotency_key="successful-start-replay")
        started = registry.mark_running(first.public_run_token, project_id=PROJECT_ID)
        replay = _reserve(registry, idempotency_key="successful-start-replay")
        assert started.run_state == STATE_RUNNING
        assert replay.replayed is True
        assert replay.run_id == started.run_id
        assert replay.run_state == STATE_RUNNING
        assert len(registry.list_records(PROJECT_ID)) == 1

        completed = registry.mark_completed(
            replay.public_run_token, project_id=PROJECT_ID, result_available=False
        )
        assert completed.run_state == STATE_COMPLETED
        assert completed.result_available is False
        assert completed.main_action == "查看本次进度"
        completed_replay = _reserve(
            registry, idempotency_key="successful-start-replay"
        )
        assert completed_replay.replayed is True
        assert completed_replay.run_id == completed.run_id
        assert completed_replay.run_state == STATE_COMPLETED
        with pytest.raises(LaunchRegistryError) as error:
            registry.mark_running(completed.public_run_token, project_id=PROJECT_ID)
        assert error.value.code == "illegal_state_transition"
    finally:
        registry.close()


def test_expired_snapshot_and_baseline_tokens_fail_closed_after_catalog_refresh() -> None:
    original = make_catalog()
    try:
        options = original.get_options(PROJECT_ID, current_snapshot_ref=CURRENT_SNAPSHOT_REF)
        current = options.current_data
        assert current is not None
        daily = next(item for item in options.modes if item.mode == MODE_DAILY)
        assert daily.published_baselines
        expired_snapshot_token = current.snapshot_token
        expired_baseline_token = daily.published_baselines[0].baseline_token
    finally:
        original.close()

    refreshed = make_catalog()
    try:
        refreshed.snapshots = tuple(
            item for item in refreshed.snapshots if item.snapshot_token != expired_snapshot_token
        )
        refreshed.published_baselines = tuple(
            item
            for item in refreshed.published_baselines
            if item.baseline_token != expired_baseline_token
        )
        with pytest.raises(RunSetupError) as error:
            refreshed.snapshot_for_token(PROJECT_ID, expired_snapshot_token)
        assert error.value.code == "invalid_snapshot"
        with pytest.raises(RunSetupError) as error:
            refreshed.baseline_for_token(
                PROJECT_ID, MODE_DAILY, expired_baseline_token
            )
        assert error.value.code == "baseline_not_published"
    finally:
        refreshed.close()


def test_launch_fingerprint_is_byte_stable_across_hash_seed_and_optimizer_matrix() -> None:
    script = r'''
import json
from mm_r7.launch_registry import normalize_request
request = normalize_request(
    project_id="synthetic-r7-07c2-project",
    idempotency_key="deterministic-key",
    mode="daily",
    execution_basis="incremental",
    current_snapshot_token="snapshot:synthetic-current-v1",
    baseline_token="baseline:synthetic-daily-v1",
    rule_tokens=("rule-z", "rule-a", "rule-z"),
)
print(json.dumps({
    "request": request.as_dict(),
    "fingerprint": request.request_fingerprint,
}, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
'''
    outputs = []
    base_env = os.environ.copy()
    existing = base_env.get("PYTHONPATH", "")
    base_env["PYTHONPATH"] = os.pathsep.join(
        item for item in (str(SRC_DIR), str(Path(__file__).parent), existing) if item
    )
    for seed in ("0", "1", "42"):
        for opt_flag in ((), ("-O",), ("-OO",)):
            env = base_env.copy()
            env["PYTHONHASHSEED"] = seed
            completed = subprocess.run(
                [sys.executable, *opt_flag, "-c", script],
                cwd=str(POC_ROOT),
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            outputs.append(completed.stdout)
    assert outputs[0] == outputs[1] == outputs[2] == outputs[3] == outputs[4] == outputs[5] == outputs[6] == outputs[7] == outputs[8]
    payload = json.loads(outputs[0])
    assert payload["request"]["rule_tokens"] == ["rule-a", "rule-z"]
    assert len(payload["fingerprint"]) == 64


def test_publication_fingerprint_normalizes_setup_manifest_shapes_and_detects_drift() -> None:
    common = {
        "project_id": PROJECT_ID,
        "run_id": "r7-run-fingerprint-shapes",
        "snapshot_token": "snapshot:synthetic-current-v1",
        "source_revision_id": "source-v1",
        "data_cutoff": "2026-08-28",
        "site_coverage": ("site-b", "site-a"),
    }
    identities = (
        {"risk-unit": True, "deterministic-unit": False},
        {
            "work_units": {
                "deterministic-unit": False,
                "risk-unit": True,
            },
            "denominator": 2,
        },
        {
            "units": [
                {"work_unit_id": "risk-unit", "mandatory": True, "ordinal": 1},
                {
                    "work_unit_id": "deterministic-unit",
                    "mandatory": False,
                    "ordinal": 2,
                },
            ],
            "denominator": 2,
        },
    )
    fingerprints = [
        compute_publication_fingerprint(
            **common,
            setup_manifest_identity=identity,
        )
        for identity in identities
    ]
    assert fingerprints[0] == fingerprints[1] == fingerprints[2]

    drifted = compute_publication_fingerprint(
        **common,
        setup_manifest_identity={
            "work_units": {
                "deterministic-unit": True,
                "risk-unit": True,
            }
        },
    )
    assert drifted != fingerprints[0]


def _reserve_publication(
    registry: LaunchRegistry,
    run_id: str,
    *,
    key: str = "publication-key",
    fingerprint: str = "publication-fingerprint",
    **kwargs,
):
    return registry.reserve_publication(
        PROJECT_ID,
        run_id,
        key,
        fingerprint,
        **kwargs,
    )


def _r6_finalize_args() -> dict[str, object]:
    members = ("artifact-a", "artifact-b", "artifact-c", "artifact-d")
    return {
        "r6_output_set_digest": "6" * 64,
        "artifact_member_ids": members,
        "artifact_member_set_digest": content_digest(list(members)),
    }


def test_reserve_publication_rejects_prebound_completion_metadata(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = _reserve(registry, idempotency_key="publication-prebound")
        invalid_metadata = (
            {"runtime_manifest_revision": 7},
            {"runtime_manifest_identity": {"work_units": {"risk-unit": True}}},
            {"runtime_manifest_digest": "runtime-digest"},
            {"manifest_revision": 7, "manifest_digest": "runtime-digest"},
            {"receipt_identities": ("receipt-1",)},
            {"receipt_set": ("receipt-1",), "receipt_set_digest": "receipts"},
            {"r5_authority_packet_id": "r5-packet"},
            {"r5_authority_packet_digest": "r5-digest"},
            {"s4_authority_packet_identities": ("s4-packet",)},
            {"s4_authority_packet_digests": ("s4-digest",)},
            {
                "runtime_manifest_revision": 7,
                "runtime_manifest_identity": {"work_units": {"risk-unit": True}},
                "runtime_manifest_digest": "runtime-digest",
                "receipt_identities": ("receipt-1",),
                "r5_authority_packet_id": "r5-packet",
                "s4_authority_packet_digests": ("s4-digest",),
            },
        )
        for metadata in invalid_metadata:
            with pytest.raises(LaunchRegistryError) as error:
                _reserve_publication(
                    registry,
                    launch.run_id,
                    key=f"prebound-{len(registry.list_publications(PROJECT_ID))}",
                    **metadata,
                )
            assert error.value.code == "invalid_publication_metadata"
        assert registry.list_publications(PROJECT_ID) == ()

        accepted = _reserve_publication(
            registry,
            launch.run_id,
            setup_manifest_identity={"risk-unit": True},
            mandatory_denominator=1,
        )
        assert accepted.publication_state == PUBLICATION_STATE_PUBLISHING
        assert accepted.manifest_revision is None
        assert accepted.runtime_manifest_identity == {}
        assert accepted.receipt_identities == ()
        assert accepted.r5_authority_packet_id is None
        assert accepted.s4_authority_packet_digests == ()
    finally:
        registry.close()


def test_publication_identity_is_one_per_run_and_replays_across_keys(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        first_run = _reserve(registry, idempotency_key="launch-one")
        first = _reserve_publication(
            registry,
            first_run.run_id,
            site_coverage=("site-b", "site-a", "site-a"),
            source_revision_id="source-v1",
            setup_manifest_digest="setup-digest",
            mandatory_denominator=3,
            setup_manifest_identity={"wu-a": True, "wu-b": True, "wu-c": True},
        )
        assert first.publication_revision == PUBLICATION_REVISION
        assert first.publication_state == PUBLICATION_STATE_PUBLISHING
        assert first.site_coverage == ("site-a", "site-b")
        assert first.source_revision_id == "source-v1"
        assert first.mandatory_denominator == 3

        replay = _reserve_publication(
            registry,
            first_run.run_id,
            key="publication-key-retry",
            fingerprint="publication-fingerprint",
        )
        assert replay.replayed is True
        assert replay.sequence == first.sequence
        assert replay.run_id == first_run.run_id
        assert len(registry.list_publications(PROJECT_ID)) == 1

        with pytest.raises(IdempotencyConflictError):
            _reserve_publication(
                registry,
                first_run.run_id,
                key="publication-key-retry",
                fingerprint="different-fingerprint",
            )

        second_run = _reserve(registry, idempotency_key="launch-two")
        with pytest.raises(IdempotencyConflictError):
            _reserve_publication(
                registry,
                second_run.run_id,
                key="publication-key",
                fingerprint="publication-fingerprint",
            )
    finally:
        registry.close()


def test_publication_failure_cas_and_terminal_state_machine(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = _reserve(registry, idempotency_key="publication-state")
        publication = _reserve_publication(registry, launch.run_id)
        failed = registry.record_publication_failure(
            project_id=PROJECT_ID,
            run_id=launch.run_id,
            state=PUBLICATION_STATE_BLOCKED,
            expected_state=PUBLICATION_STATE_PUBLISHING,
            error_code="authority_blocked",
            error_message="authority incomplete",
        )
        assert failed.publication_state == PUBLICATION_STATE_BLOCKED
        assert failed.failure_code == "authority_blocked"
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False

        with pytest.raises(LaunchRegistryError) as stale:
            registry.record_publication_failure(
                project_id=PROJECT_ID,
                run_id=launch.run_id,
                state=PUBLICATION_STATE_RECOVERABLE_FAILED,
                expected_state=PUBLICATION_STATE_PUBLISHING,
            )
        assert stale.value.code == "publication_cas_conflict"

        resumed = registry.retry_publication(
            project_id=PROJECT_ID,
            run_id=launch.run_id,
            expected_state=PUBLICATION_STATE_BLOCKED,
        )
        assert resumed.publication_state == PUBLICATION_STATE_PUBLISHING
        transient = registry.record_publication_failure(
            project_id=PROJECT_ID,
            run_id=launch.run_id,
            state=PUBLICATION_STATE_RECOVERABLE_FAILED,
        )
        assert transient.publication_state == PUBLICATION_STATE_RECOVERABLE_FAILED

        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)
        available = registry.finalize_publication(
            project_id=PROJECT_ID,
            run_id=launch.run_id,
            expected_state=PUBLICATION_STATE_RECOVERABLE_FAILED,
            receipt_identities=("receipt-b", "receipt-a", "receipt-a"),
            receipt_set_digest="receipts-digest",
            r5_authority_packet_id="r5-packet",
            r5_authority_packet_digest="r5-digest",
            s4_authority_packet_identities=("s4-b", "s4-a"),
            s4_authority_packet_digests=("s4-digest-b", "s4-digest-a"),
            **_r6_finalize_args(),
        )
        assert available.publication_state == PUBLICATION_STATE_AVAILABLE
        assert available.receipt_identities == ("receipt-a", "receipt-b")
        assert available.s4_authority_packet_identities == ("s4-a", "s4-b")
        assert available.s4_authority_packet_digests == (
            "s4-digest-a",
            "s4-digest-b",
        )
        launch_after = registry.get(launch.run_id, project_id=PROJECT_ID)
        assert launch_after.result_available is True
        assert launch_after.main_action == "查看本次结果"

        replay = registry.finalize_publication(PROJECT_ID, launch.run_id)
        assert replay.replayed is True
        with pytest.raises(LaunchRegistryError) as terminal:
            registry.record_publication_failure(
                PROJECT_ID,
                launch.run_id,
                state=PUBLICATION_STATE_BLOCKED,
            )
        assert terminal.value.code == "illegal_publication_transition"
        with pytest.raises(LaunchRegistryError) as terminal:
            registry.retry_publication(PROJECT_ID, launch.run_id)
        assert terminal.value.code == "illegal_publication_transition"
        assert publication.sequence == available.sequence
    finally:
        registry.close()


def test_finalize_requires_completed_run_and_binds_result_metadata_once(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = _reserve(registry, idempotency_key="publication-incomplete")
        _reserve_publication(registry, launch.run_id)
        with pytest.raises(LaunchRegistryError) as not_completed:
            registry.finalize_publication(PROJECT_ID, launch.run_id)
        assert not_completed.value.code == "run_not_completed"
        assert registry.get_publication(PROJECT_ID, launch.run_id).state == PUBLICATION_STATE_PUBLISHING
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False

        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)
        finalized = registry.finalize_publication(
            PROJECT_ID,
            launch.run_id,
            receipt_set=("r-2", "r-1"),
            receipt_digest="receipt-digest",
            **_r6_finalize_args(),
        )
        assert finalized.result_available is True
        with pytest.raises(LaunchRegistryError) as overwrite:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                fingerprint="different-fingerprint",
            )
        assert overwrite.value.code == "idempotency_conflict"
        assert registry.get_publication(PROJECT_ID, launch.run_id).receipt_set == (
            "r-1",
            "r-2",
        )
    finally:
        registry.close()


def test_launch_result_flag_can_only_be_opened_by_available_publication(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = _reserve(registry, idempotency_key="result-flag-guard")
        _reserve_publication(registry, launch.run_id)
        with pytest.raises(LaunchRegistryError) as error:
            registry.mark_completed(
                launch.run_id,
                project_id=PROJECT_ID,
                result_available=True,
            )
        assert error.value.code == "invalid_result_state"
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False
    finally:
        registry.close()


@pytest.mark.parametrize(
    "failure_point",
    ("finalize.after_publication_update", "finalize.after_launch_update"),
)
def test_finalize_fault_injection_rolls_back_both_sides(
    tmp_path: Path, failure_point: str
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = _reserve(registry, idempotency_key=f"publication-fault-{failure_point}")
        _reserve_publication(registry, launch.run_id)
        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)

        def fail(point: str) -> None:
            if point == failure_point:
                raise RuntimeError(point)

        registry._failure_injector = fail
        with pytest.raises(LaunchRegistryError) as error:
            registry.finalize_publication(
                PROJECT_ID, launch.run_id, **_r6_finalize_args()
            )
        assert error.value.code == "store_closed"
        assert registry.get_publication(PROJECT_ID, launch.run_id).state == PUBLICATION_STATE_PUBLISHING
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False

        registry._failure_injector = None
        finalized = registry.finalize_publication(
            PROJECT_ID, launch.run_id, **_r6_finalize_args()
        )
        assert finalized.state == PUBLICATION_STATE_AVAILABLE
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is True
    finally:
        registry.close()


def test_v1_to_v4_migration_is_additive_transactional_and_retryable(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "launch.sqlite3"
    registry = LaunchRegistry(db_path, project_id=PROJECT_ID)
    launch = _reserve(registry, idempotency_key="migration-history")
    registry.close()

    connection = sqlite3.connect(db_path)
    try:
        connection.execute("DROP INDEX IF EXISTS r7_result_publications_project_idx")
        connection.execute("DROP TABLE r7_result_publications")
        connection.execute(
            "UPDATE r7_launch_registry_meta SET value = ? WHERE key = ?",
            (SCHEMA_VERSION_V1, "schema_version"),
        )
        connection.commit()
    finally:
        connection.close()
    live_before = db_path.read_bytes()

    with pytest.raises(LaunchRegistryError) as boundary:
        LaunchRegistry(db_path, project_id=PROJECT_ID)
    assert boundary.value.code == "unsupported_schema_version"
    assert db_path.read_bytes() == live_before

    staged = _stage_legacy_launch(tmp_path, db_path)

    def fail(point: str) -> None:
        if point == "migration.launch_registry.ddl.after":
            raise RuntimeError(point)

    with pytest.raises(MigrationError) as migration_error:
        migrate_launch_registry_staging(
            staged,
            SCHEMA_VERSION_V1,
            failure_injector=fail,
        )
    assert migration_error.value.code == "injected_failure"
    check = sqlite3.connect(staged)
    try:
        assert check.execute(
            "SELECT value FROM r7_launch_registry_meta WHERE key = 'schema_version'"
        ).fetchone()[0] == SCHEMA_VERSION_V1
        assert check.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name = 'r7_result_publications'"
        ).fetchone() is None
        assert check.execute(
            "SELECT run_id FROM r7_launch_registry WHERE idempotency_key = ?",
            ("migration-history",),
        ).fetchone()[0] == launch.run_id
    finally:
        check.close()
    assert db_path.read_bytes() == live_before

    migrate_launch_registry_staging(staged, SCHEMA_VERSION_V1)
    migrated = LaunchRegistry(staged, project_id=PROJECT_ID)
    try:
        assert migrated._conn is not None
        assert migrated._conn.execute(
            "SELECT value FROM r7_launch_registry_meta WHERE key = 'schema_version'"
        ).fetchone()[0] == SCHEMA_VERSION
        replay = _reserve(migrated, idempotency_key="migration-history")
        assert replay.replayed is True
        assert migrated.list_publications(PROJECT_ID) == ()
    finally:
        migrated.close()


def test_unknown_registry_schema_fails_closed_without_publication_use(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "unknown.sqlite3"
    registry = LaunchRegistry(db_path, project_id=PROJECT_ID)
    registry.close()
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "UPDATE r7_launch_registry_meta SET value = ? WHERE key = ?",
            ("mm-r7-future-v9", "schema_version"),
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(LaunchRegistryError) as error:
        LaunchRegistry(db_path, project_id=PROJECT_ID)
    assert error.value.code == "unsupported_schema_version"


def _runtime_manifest_args() -> dict[str, object]:
    return {
        "runtime_manifest_revision": 7,
        "runtime_manifest_identity": {
            "work_units": {
                "deterministic-unit": False,
                "risk-unit": True,
            }
        },
        "runtime_manifest_digest": "runtime-manifest-digest-v7",
        "mandatory_denominator": 1,
    }


def test_runtime_manifest_bind_is_post_reservation_cas_and_exactly_replayable(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = _reserve(registry, idempotency_key="runtime-bind")
        publication = _reserve_publication(
            registry,
            launch.run_id,
            fingerprint="runtime-bind-fingerprint",
            setup_manifest_identity={
                "work_units": {
                    "deterministic-unit": False,
                    "risk-unit": True,
                }
            },
            mandatory_denominator=1,
        )

        bound = registry.bind_publication_runtime_manifest(
            PROJECT_ID,
            launch.run_id,
            expected_state=PUBLICATION_STATE_PUBLISHING,
            expected_fingerprint="runtime-bind-fingerprint",
            **_runtime_manifest_args(),
        )
        assert bound.replayed is False
        assert bound.publication_state == PUBLICATION_STATE_PUBLISHING
        assert bound.runtime_manifest_revision == 7
        assert bound.runtime_manifest_digest == "runtime-manifest-digest-v7"
        assert bound.runtime_manifest_identity == {
            "work_units": {
                "deterministic-unit": False,
                "risk-unit": True,
            }
        }
        assert bound.mandatory_denominator == 1
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False

        replay = registry.bind_publication_runtime_manifest(
            PROJECT_ID,
            launch.run_id,
            expected_state=PUBLICATION_STATE_PUBLISHING,
            expected_fingerprint="runtime-bind-fingerprint",
            **_runtime_manifest_args(),
        )
        assert replay.replayed is True
        assert replay.sequence == publication.sequence == bound.sequence
        assert registry.get_publication(PROJECT_ID, launch.run_id).manifest_revision == 7
    finally:
        registry.close()


def test_runtime_manifest_bind_rejects_partial_conflict_and_manifest_drift(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = _reserve(registry, idempotency_key="runtime-bind-conflict")
        _reserve_publication(
            registry,
            launch.run_id,
            fingerprint="runtime-bind-conflict-fingerprint",
            setup_manifest_identity={
                "work_units": {"risk-unit": True, "deterministic-unit": False}
            },
            mandatory_denominator=1,
        )
        with pytest.raises(LaunchRegistryError) as partial:
            registry.bind_publication_runtime_manifest(
                PROJECT_ID,
                launch.run_id,
                runtime_manifest_revision=7,
                runtime_manifest_identity={"work_units": {"risk-unit": True}},
                mandatory_denominator=1,
            )
        assert partial.value.code == "invalid_publication_metadata"

        with pytest.raises(LaunchRegistryError) as denominator:
            registry.bind_publication_runtime_manifest(
                PROJECT_ID,
                launch.run_id,
                expected_fingerprint="runtime-bind-conflict-fingerprint",
                runtime_manifest_revision=7,
                runtime_manifest_identity={
                    "work_units": {
                        "risk-unit": True,
                        "deterministic-unit": False,
                    }
                },
                runtime_manifest_digest="runtime-manifest-digest-v7",
                mandatory_denominator=2,
            )
        assert denominator.value.code == "publication_cas_conflict"

        with pytest.raises(LaunchRegistryError) as mismatch:
            registry.bind_publication_runtime_manifest(
                PROJECT_ID,
                launch.run_id,
                expected_fingerprint="runtime-bind-conflict-fingerprint",
                runtime_manifest_revision=7,
                runtime_manifest_identity={
                    "work_units": {
                        "risk-unit": True,
                        "deterministic-unit": False,
                        "new-unit": True,
                    }
                },
                runtime_manifest_digest="runtime-manifest-digest-v7",
                mandatory_denominator=2,
            )
        assert mismatch.value.code == "publication_cas_conflict"
        untouched = registry.get_publication(PROJECT_ID, launch.run_id)
        assert untouched.manifest_revision is None
        assert untouched.runtime_manifest_identity == {}

        first = registry.bind_publication_runtime_manifest(
            PROJECT_ID,
            launch.run_id,
            expected_fingerprint="runtime-bind-conflict-fingerprint",
            **_runtime_manifest_args(),
        )
        assert first.manifest_revision == 7
        with pytest.raises(LaunchRegistryError) as conflict:
            registry.bind_publication_runtime_manifest(
                PROJECT_ID,
                launch.run_id,
                expected_fingerprint="runtime-bind-conflict-fingerprint",
                runtime_manifest_revision=8,
                runtime_manifest_identity=_runtime_manifest_args()[
                    "runtime_manifest_identity"
                ],
                runtime_manifest_digest="runtime-manifest-digest-v8",
                mandatory_denominator=1,
            )
        assert conflict.value.code == "publication_cas_conflict"
        assert registry.get_publication(PROJECT_ID, launch.run_id).manifest_revision == 7
    finally:
        registry.close()


def test_runtime_manifest_bind_rejects_stale_state_and_rolls_back_injected_failure(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        stale_launch = _reserve(registry, idempotency_key="runtime-bind-stale")
        _reserve_publication(registry, stale_launch.run_id)
        registry.record_publication_failure(
            PROJECT_ID,
            stale_launch.run_id,
            state=PUBLICATION_STATE_BLOCKED,
        )
        with pytest.raises(LaunchRegistryError) as stale:
            registry.bind_publication_runtime_manifest(
                PROJECT_ID, stale_launch.run_id, **_runtime_manifest_args()
            )
        assert stale.value.code == "publication_cas_conflict"
        assert registry.get_publication(
            PROJECT_ID, stale_launch.run_id
        ).publication_state == PUBLICATION_STATE_BLOCKED

        launch = _reserve(registry, idempotency_key="runtime-bind-rollback")
        _reserve_publication(registry, launch.run_id, key="publication-key-rollback")

        def fail(point: str) -> None:
            if point == "bind_publication_runtime_manifest.after_update":
                raise RuntimeError(point)

        registry.set_failure_injector(fail)
        with pytest.raises(LaunchRegistryError) as injected:
            registry.bind_publication_runtime_manifest(
                PROJECT_ID,
                launch.run_id,
                **_runtime_manifest_args(),
            )
        assert injected.value.code == "store_closed"
        rolled_back = registry.get_publication(PROJECT_ID, launch.run_id)
        assert rolled_back.manifest_revision is None
        assert rolled_back.manifest_digest is None
        assert rolled_back.runtime_manifest_identity == {}
        assert rolled_back.mandatory_denominator == 0
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False

        registry.set_failure_injector(None)
        recovered = registry.bind_publication_runtime_manifest(
            PROJECT_ID,
            launch.run_id,
            **_runtime_manifest_args(),
        )
        assert recovered.manifest_revision == 7
    finally:
        registry.close()


def test_result_context_token_is_persisted_and_replayed_without_reminting(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = _reserve(registry, idempotency_key="context-token-launch")
        _reserve_publication(
            registry,
            launch.run_id,
            key="context-token-publication",
            site_coverage=("site-a",),
        )
        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)
        finalized = registry.finalize_publication(
            project_id=PROJECT_ID,
            run_id=launch.run_id,
            **_r6_finalize_args(),
        )
        assert finalized.result_context_token
        assert finalized.result_context_token.startswith("result-context:")
        persisted = registry._conn.execute(
            "SELECT result_context_token FROM r7_result_publications "
            "WHERE project_id = ? AND run_id = ?",
            (PROJECT_ID, launch.run_id),
        ).fetchone()
        assert persisted is not None
        assert persisted[0] == finalized.result_context_token

        replay = registry.finalize_publication(
            project_id=PROJECT_ID,
            run_id=launch.run_id,
        )
        assert replay.replayed is True
        assert replay.result_context_token == finalized.result_context_token
        looked_up = registry.get_publication_by_result_context_token(
            finalized.result_context_token,
            project_id=PROJECT_ID,
        )
        assert looked_up.publication_id == finalized.publication_id
    finally:
        registry.close()


def test_enforced_in_flight_gate_replays_same_key_and_allows_terminal_run(
    tmp_path: Path,
) -> None:
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        first = _reserve(
            registry,
            idempotency_key="in-flight-first",
        )
        registry.mark_running(first.public_run_token, project_id=PROJECT_ID)
        assert registry.has_in_flight(PROJECT_ID) is True

        with pytest.raises(LaunchRegistryError) as blocked:
            _reserve(
                registry,
                idempotency_key="in-flight-second",
                mode=MODE_PRE_LOCK,
                enforce_in_flight=True,
            )
        assert blocked.value.code == "in_flight_conflict"

        replay = _reserve(
            registry,
            idempotency_key="in-flight-first",
            enforce_in_flight=True,
        )
        assert replay.replayed is True
        registry.mark_failed(first.public_run_token, project_id=PROJECT_ID)
        assert registry.has_in_flight(PROJECT_ID) is False
        second = _reserve(
            registry,
            idempotency_key="in-flight-second",
            mode=MODE_PRE_LOCK,
            enforce_in_flight=True,
        )
        assert second.replayed is False
    finally:
        registry.close()
