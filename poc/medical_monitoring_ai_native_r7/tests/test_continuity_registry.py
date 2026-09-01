"""Focused stdlib-only Slice-08A continuity registry tests."""
from __future__ import annotations

import re
import shutil
import sqlite3
from pathlib import Path
import pytest

from fixtures_run_setup import PROJECT_ID
from mm_r7.continuity import (
    CarryForwardItem,
    CarryForwardPlan,
    build_carry_forward_item,
    build_carry_forward_plan,
)

from mm_r7.migration import MigrationError, migrate_launch_registry_staging
from mm_r7.launch_registry import (
    BASIS_FULL,
    BUSY_TIMEOUT_MS,
    CONTINUITY_PLAN_STATE_BLOCKED,
    CONTINUITY_PLAN_STATE_PUBLISHED,
    CONTINUITY_PLAN_STATE_STAGING,
    CONTINUITY_PLAN_STATE_VERIFIED,
    LaunchRegistry,
    LaunchRegistryError,
    PUBLICATION_STATE_AVAILABLE,
    PUBLICATION_STATE_BLOCKED,
    PUBLICATION_STATE_PUBLISHING,
    PUBLICATION_STATE_RECOVERABLE_FAILED,
    ResultPublication,
    SCHEMA_VERSION,
    SCHEMA_VERSION_V2,
    SCHEMA_VERSION_V3,
    SCHEMA_VERSION_V4,
    content_digest,
    derive_continuity_plan_id,
)


NOW = "2026-08-29T04:00:00.000+00:00"


def _plan(target_run_id: str):
    item = build_carry_forward_item(
        {
            "object_type": "risk_instance",
            "object_ref": "risk-001",
            "data_change_kind": "revised",
            "reason": "本轮数据修订变化",
            "target_run_id": target_run_id,
            "target_project_id": PROJECT_ID,
            "target_mode": "daily",
        }
    )
    return build_carry_forward_plan(
        project_id=PROJECT_ID,
        mode="daily",
        execution_basis=BASIS_FULL,
        target_run_id=target_run_id,
        target_snapshot_id="snapshot-target",
        target_data_cutoff="2026-08-29",
        target_decision_version="decision-target",
        r5_authority_digest="r5-target",
        r6_publication_digest="r6-target",
        r6_receipt_digest="receipt-target",
        r6_output_set_digest="6" * 64,
        items=(item,),
        created_at=NOW,
    )


def _publication(registry: LaunchRegistry, run_id: str):
    return registry.reserve_publication(
        PROJECT_ID,
        run_id,
        idempotency_key="publication-" + run_id,
        request_fingerprint="r6-target",
        snapshot_token="snapshot-target",
        data_cutoff="2026-08-29",
    )


def _stage_legacy_launch(
    tmp_path: Path,
    source: Path,
    operation_id: str = "explicit-continuity",
) -> Path:
    workspace = tmp_path / ".migration-staging" / operation_id / "workspace"
    workspace.mkdir(parents=True, exist_ok=False)
    staged = workspace / source.name
    shutil.copy2(source, staged)
    return staged


def test_finalize_rejects_empty_r6_artifact_closure(tmp_path: Path):
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = registry.reserve(
            PROJECT_ID,
            idempotency_key="empty-r6-closure",
            mode="daily",
            execution_basis=BASIS_FULL,
            current_snapshot_token="snapshot-target",
            data_cutoff="2026-08-29",
        )
        _publication(registry, launch.run_id)
        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)

        with pytest.raises(LaunchRegistryError) as blocked:
            registry.finalize_publication(PROJECT_ID, launch.run_id)

        assert blocked.value.code == "invalid_publication_metadata"
        assert registry.get_publication(PROJECT_ID, launch.run_id).state == "publishing"
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False
    finally:
        registry.close()


def test_finalize_rejects_partial_r6_closure_and_read_detects_digest_tamper(
    tmp_path: Path,
):
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = registry.reserve(
            PROJECT_ID,
            idempotency_key="partial-r6-closure",
            mode="daily",
            execution_basis=BASIS_FULL,
            current_snapshot_token="snapshot-target",
            data_cutoff="2026-08-29",
        )
        _publication(registry, launch.run_id)
        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)
        with pytest.raises(LaunchRegistryError) as partial:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                r6_output_set_digest="6" * 64,
                artifact_member_ids=("artifact-only",),
                artifact_member_set_digest=content_digest(["artifact-only"]),
            )
        assert partial.value.code == "invalid_publication_metadata"

        members = ("artifact-a", "artifact-b", "artifact-c", "artifact-d")
        registry.finalize_publication(
            PROJECT_ID,
            launch.run_id,
            r6_output_set_digest="6" * 64,
            artifact_member_ids=members,
            artifact_member_set_digest=content_digest(list(members)),
        )
        assert registry._conn is not None
        registry._conn.execute(
            "UPDATE r7_result_publications SET artifact_member_ids_json = ? "
            "WHERE project_id = ? AND run_id = ?",
            ('["artifact-a","artifact-b","artifact-c","artifact-x"]', PROJECT_ID, launch.run_id),
        )
        registry._conn.commit()
        with pytest.raises(LaunchRegistryError) as tampered:
            registry.get_publication(PROJECT_ID, launch.run_id)
        assert tampered.value.code == "store_closed"
    finally:
        registry.close()


def test_continuity_plan_round_trip_status_gate_and_close_reopen(tmp_path: Path):
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = registry.reserve(
            PROJECT_ID,
            idempotency_key="continuity-round-trip",
            mode="daily",
            execution_basis=BASIS_FULL,
            current_snapshot_token="snapshot-target",
            data_cutoff="2026-08-29",
            comparison_range="合成完整范围",
        )
        plan = _plan(launch.run_id)
        staged = registry.save_continuity_plan(plan)
        assert staged.status == CONTINUITY_PLAN_STATE_STAGING
        assert staged.as_dict() == plan.as_dict()
        assert registry.get_continuity_plan(PROJECT_ID, launch.run_id) == plan
        assert registry.get_continuity_plan(
            derive_continuity_plan_id(plan)
        ) == plan
        assert registry.list_continuity_items(PROJECT_ID, launch.run_id) == plan.items

        verified = registry.verify_continuity_plan(
            PROJECT_ID, launch.run_id, expected_plan_digest=plan.plan_digest
        )
        assert verified.status == CONTINUITY_PLAN_STATE_VERIFIED
        assert verified.plan_digest == plan.plan_digest
        registry.close()
        registry.reopen()
        assert registry.get_continuity_plan(PROJECT_ID, launch.run_id).status == CONTINUITY_PLAN_STATE_VERIFIED
    finally:
        registry.close()


def test_continuity_status_fault_rolls_back_and_publication_is_atomic(
    tmp_path: Path,
):
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = registry.reserve(
            PROJECT_ID,
            idempotency_key="continuity-publish",
            mode="daily",
            execution_basis=BASIS_FULL,
            current_snapshot_token="snapshot-target",
            data_cutoff="2026-08-29",
            comparison_range="合成完整范围",
        )
        registry.save_continuity_plan(_plan(launch.run_id))
        publication = _publication(registry, launch.run_id)
        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)
        with pytest.raises(LaunchRegistryError) as blocked:
            registry.publish_continuity_plan(PROJECT_ID, launch.run_id)
        assert blocked.value.code == "continuity_plan_not_verified"
        assert registry.get_publication(PROJECT_ID, launch.run_id).state == "publishing"

        registry.verify_continuity_plan(PROJECT_ID, launch.run_id)

        def fail(point: str) -> None:
            if point == "finalize.after_continuity_update":
                raise RuntimeError(point)

        registry.set_failure_injector(fail)
        with pytest.raises(LaunchRegistryError) as rolled_back:
            registry.publish_continuity_plan(
                PROJECT_ID,
                launch.run_id,
                r5_authority_packet_digest="r5-target",
                receipt_set_digest="receipt-target",
                r6_output_set_digest="6" * 64,
                artifact_member_ids=("art-1", "art-2", "art-3", "art-4"),
            )
        assert registry.get_continuity_plan(PROJECT_ID, launch.run_id).status == CONTINUITY_PLAN_STATE_VERIFIED
        assert registry.get_publication(PROJECT_ID, launch.run_id).state == "publishing"
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False

        registry.set_failure_injector(None)
        finalized = registry.publish_continuity_plan(
            PROJECT_ID,
            launch.run_id,
            r5_authority_packet_digest="r5-target",
            receipt_set_digest="receipt-target",
            r6_output_set_digest="6" * 64,
            artifact_member_ids=("art-1", "art-2", "art-3", "art-4"),
        )
        assert finalized.publication_id == publication.publication_id
        assert finalized.state == "available"
        assert registry.get_continuity_plan(PROJECT_ID, launch.run_id).status == CONTINUITY_PLAN_STATE_PUBLISHED
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is True
    finally:
        registry.close()


def test_continuity_publication_digest_drift_stays_closed(tmp_path: Path):
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        launch = registry.reserve(
            PROJECT_ID,
            idempotency_key="continuity-digest-drift",
            mode="daily",
            execution_basis=BASIS_FULL,
            current_snapshot_token="snapshot-target",
            data_cutoff="2026-08-29",
            comparison_range="合成完整范围",
        )
        registry.save_continuity_plan(_plan(launch.run_id))
        registry.verify_continuity_plan(PROJECT_ID, launch.run_id)
        _publication(registry, launch.run_id)
        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)
        with pytest.raises(LaunchRegistryError) as conflict:
            registry.publish_continuity_plan(
                PROJECT_ID,
                launch.run_id,
                r5_authority_packet_digest="r5-drift",
                receipt_set_digest="receipt-target",
            )
        assert conflict.value.code == "continuity_publication_conflict"
        assert registry.get_publication(PROJECT_ID, launch.run_id).state == "publishing"
        assert registry.get_continuity_plan(PROJECT_ID, launch.run_id).status == CONTINUITY_PLAN_STATE_VERIFIED
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False
    finally:
        registry.close()


def test_continuity_save_fault_rolls_back_parent_and_items(tmp_path: Path):
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT_ID)
    try:
        plan = _plan("run-without-launch")

        def fail(point: str) -> None:
            if point == "continuity.save.after_plan":
                raise RuntimeError(point)

        registry.set_failure_injector(fail)
        with pytest.raises(LaunchRegistryError) as error:
            registry.save_continuity_plan(plan)
        assert error.value.code == "store_closed"
        assert registry.list_continuity_plans(PROJECT_ID) == ()

        registry.set_failure_injector(None)
        assert registry.save_continuity_plan(plan) == plan
    finally:
        registry.close()

@pytest.mark.parametrize(
    "failure_point",
    (
        "migration.launch_registry.ddl.before",
        "migration.launch_registry.ddl.after",
        "migration.launch_registry.oracle.before",
        "migration.launch_registry.oracle.after",
        "migration.launch_registry.marker.before",
        "migration.launch_registry.marker.after",
        "migration.launch_registry.commit.before",
    ),
)
def test_v2_to_v4_migration_is_additive_transactional_and_retryable(
    tmp_path: Path, failure_point: str
):
    db_path = tmp_path / "launch.sqlite3"
    registry = LaunchRegistry(db_path, project_id=PROJECT_ID)
    launch = registry.reserve(
        PROJECT_ID,
        idempotency_key="continuity-migration",
        mode="daily",
        execution_basis=BASIS_FULL,
        current_snapshot_token="snapshot-target",
        data_cutoff="2026-08-29",
        comparison_range="合成完整范围",
    )
    registry.close()

    connection = sqlite3.connect(db_path)
    try:
        connection.execute("DROP INDEX IF EXISTS r7_continuity_plans_project_idx")
        connection.execute("DROP INDEX IF EXISTS r7_continuity_items_plan_idx")
        connection.execute("DROP TABLE r7_continuity_items")
        connection.execute("DROP TABLE r7_continuity_plans")
        connection.execute(
            "UPDATE r7_launch_registry_meta SET value = ? WHERE key = ?",
            (SCHEMA_VERSION_V2, "schema_version"),
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
        if point == failure_point:
            raise RuntimeError(point)

    with pytest.raises(MigrationError) as error:
        migrate_launch_registry_staging(
            staged,
            SCHEMA_VERSION_V2,
            failure_injector=fail,
        )
    assert error.value.code == "injected_failure"

    check = sqlite3.connect(staged)
    try:
        assert check.execute(
            "SELECT value FROM r7_launch_registry_meta WHERE key = 'schema_version'"
        ).fetchone()[0] == SCHEMA_VERSION_V2
        assert check.execute(
            "SELECT run_id FROM r7_launch_registry WHERE idempotency_key = ?",
            ("continuity-migration",),
        ).fetchone()[0] == launch.run_id
        assert check.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name = 'r7_continuity_plans'"
        ).fetchone() is None
    finally:
        check.close()
    assert db_path.read_bytes() == live_before

    migrate_launch_registry_staging(staged, SCHEMA_VERSION_V2)
    migrated = LaunchRegistry(staged, project_id=PROJECT_ID)
    try:
        assert migrated.schema_version == SCHEMA_VERSION
        assert migrated.get_by_idempotency(
            "continuity-migration", project_id=PROJECT_ID
        ).run_id == launch.run_id
        assert migrated.list_continuity_plans(PROJECT_ID) == ()
    finally:
        migrated.close()


@pytest.mark.parametrize(
    "failure_point",
    (
        "migration.launch_registry.ddl.before",
        "migration.launch_registry.ddl.after",
        "migration.launch_registry.oracle.before",
        "migration.launch_registry.oracle.after",
        "migration.launch_registry.marker.before",
        "migration.launch_registry.marker.after",
        "migration.launch_registry.commit.before",
    ),
)
def test_v3_to_v4_migration_is_additive_retryable_and_transactional(
    tmp_path: Path, failure_point: str
):
    db_path = tmp_path / "launch_v3.sqlite3"
    registry = LaunchRegistry(db_path, project_id=PROJECT_ID)
    launch = registry.reserve(
        PROJECT_ID,
        idempotency_key="v3-migration-key",
        mode="daily",
        execution_basis=BASIS_FULL,
        current_snapshot_token="snapshot-target",
        data_cutoff="2026-08-29",
        comparison_range="合成完整范围",
    )
    pub = _publication(registry, launch.run_id)
    item = build_carry_forward_item(
        {
            "object_type": "risk_instance",
            "object_ref": "risk-001",
            "data_change_kind": "revised",
            "reason": "本轮数据修订变化",
            "target_run_id": launch.run_id,
            "target_project_id": PROJECT_ID,
            "target_mode": "daily",
        }
    )
    v3_initial_plan = build_carry_forward_plan(
        project_id=PROJECT_ID,
        mode="daily",
        execution_basis=BASIS_FULL,
        target_run_id=launch.run_id,
        target_snapshot_id="snapshot-target",
        target_data_cutoff="2026-08-29",
        target_decision_version="decision-target",
        r5_authority_digest="r5-target",
        r6_publication_digest="r6-target",
        r6_receipt_digest="receipt-target",
        r6_output_set_digest="",
        items=(item,),
        created_at=NOW,
    )
    plan = registry.save_continuity_plan(v3_initial_plan)
    registry.close()

    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "ALTER TABLE r7_result_publications DROP COLUMN r6_output_set_digest"
        )
        connection.execute(
            "ALTER TABLE r7_result_publications DROP COLUMN artifact_member_ids_json"
        )
        connection.execute(
            "ALTER TABLE r7_result_publications DROP COLUMN artifact_member_set_digest"
        )
        connection.execute(
            "ALTER TABLE r7_continuity_plans DROP COLUMN r6_output_set_digest"
        )
        connection.execute(
            "UPDATE r7_launch_registry_meta SET value = ? WHERE key = 'schema_version'",
            (SCHEMA_VERSION_V3,),
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
        if point == failure_point:
            raise RuntimeError(point)

    with pytest.raises(MigrationError) as error:
        migrate_launch_registry_staging(
            staged,
            SCHEMA_VERSION_V3,
            failure_injector=fail,
        )
    assert error.value.code == "injected_failure"

    check = sqlite3.connect(staged)
    try:
        assert check.execute(
            "SELECT value FROM r7_launch_registry_meta WHERE key = 'schema_version'"
        ).fetchone()[0] == SCHEMA_VERSION_V3
        assert check.execute(
            "SELECT run_id FROM r7_launch_registry WHERE idempotency_key = ?",
            ("v3-migration-key",),
        ).fetchone()[0] == launch.run_id
        assert check.execute(
            "SELECT run_id FROM r7_result_publications WHERE run_id = ?",
            (launch.run_id,),
        ).fetchone()[0] == launch.run_id
        assert check.execute(
            "SELECT target_run_id FROM r7_continuity_plans WHERE target_run_id = ?",
            (launch.run_id,),
        ).fetchone()[0] == launch.run_id
    finally:
        check.close()
    assert db_path.read_bytes() == live_before

    migrate_launch_registry_staging(staged, SCHEMA_VERSION_V3)
    migrated = LaunchRegistry(staged, project_id=PROJECT_ID)
    try:
        assert migrated.schema_version == SCHEMA_VERSION_V4
        assert migrated.schema_version == SCHEMA_VERSION
        assert migrated.get_by_idempotency(
            "v3-migration-key", project_id=PROJECT_ID
        ).run_id == launch.run_id
        loaded_pub = migrated.get_publication(PROJECT_ID, launch.run_id)
        assert loaded_pub.run_id == launch.run_id
        assert loaded_pub.r6_output_set_digest is None
        assert loaded_pub.artifact_member_ids == ()
        assert loaded_pub.artifact_member_set_digest is None
        loaded_plan = migrated.get_continuity_plan(PROJECT_ID, launch.run_id)
        assert loaded_plan.target_run_id == launch.run_id
        assert loaded_plan.r6_output_set_digest == ""
    finally:
        migrated.close()


def test_v3_legacy_plan_blocked_from_verification_without_r6_output_set_digest(
    tmp_path: Path,
):
    db_path = tmp_path / "legacy_v3_plan.sqlite3"
    registry = LaunchRegistry(db_path, project_id=PROJECT_ID)
    try:
        launch = registry.reserve(
            PROJECT_ID,
            idempotency_key="legacy-plan-key",
            mode="daily",
            execution_basis=BASIS_FULL,
            current_snapshot_token="snapshot-target",
            data_cutoff="2026-08-29",
            comparison_range="合成完整范围",
        )
        item = build_carry_forward_item(
            {
                "object_type": "risk_instance",
                "object_ref": "risk-001",
                "data_change_kind": "revised",
                "reason": "本轮数据修订变化",
                "target_run_id": launch.run_id,
                "target_project_id": PROJECT_ID,
                "target_mode": "daily",
            }
        )
        # Plan with empty r6_output_set_digest simulates a legacy v3 plan
        v3_plan = build_carry_forward_plan(
            project_id=PROJECT_ID,
            mode="daily",
            execution_basis=BASIS_FULL,
            target_run_id=launch.run_id,
            target_snapshot_id="snapshot-target",
            target_data_cutoff="2026-08-29",
            target_decision_version="decision-target",
            r5_authority_digest="r5-target",
            r6_publication_digest="r6-target",
            r6_receipt_digest="receipt-target",
            r6_output_set_digest="",
            items=(item,),
            created_at=NOW,
        )
        staged = registry.save_continuity_plan(v3_plan)
        assert staged.status == CONTINUITY_PLAN_STATE_STAGING
        assert staged.r6_output_set_digest == ""
        _publication(registry, launch.run_id)
        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)

        with pytest.raises(LaunchRegistryError) as blocked_verify:
            registry.verify_continuity_plan(PROJECT_ID, launch.run_id)
        assert blocked_verify.value.code == "continuity_plan_not_verified"

        with pytest.raises(LaunchRegistryError) as blocked_publish:
            registry.publish_continuity_plan(PROJECT_ID, launch.run_id)
        assert blocked_publish.value.code == "continuity_plan_not_verified"
    finally:
        registry.close()


def test_result_publication_and_carry_forward_plan_v4_serialization_and_digests(
    tmp_path: Path,
):
    db_path = tmp_path / "v4_serialization.sqlite3"
    registry = LaunchRegistry(db_path, project_id=PROJECT_ID)
    try:
        launch = registry.reserve(
            PROJECT_ID,
            idempotency_key="v4-serial-key",
            mode="daily",
            execution_basis=BASIS_FULL,
            current_snapshot_token="snapshot-target",
            data_cutoff="2026-08-29",
            comparison_range="合成完整范围",
        )
        pub = _publication(registry, launch.run_id)
        assert pub.r6_output_set_digest is None
        assert pub.artifact_member_ids == ()
        assert pub.artifact_member_set == ()
        assert pub.artifact_members == ()
        assert pub.artifact_member_set_digest is None

        pub_dict = pub.as_dict()
        assert "r6_output_set_digest" in pub_dict
        assert "artifact_member_ids" in pub_dict
        assert "artifact_member_set_digest" in pub_dict
        assert pub_dict["r6_output_set_digest"] is None
        assert pub_dict["artifact_member_ids"] == []
        assert pub_dict["artifact_member_set_digest"] is None

        out_digest = "e" * 64
        members = ("art-01", "art-02", "art-03", "art-04")
        member_set_digest = content_digest(list(members))

        item = build_carry_forward_item(
            {
                "object_type": "risk_instance",
                "object_ref": "risk-001",
                "data_change_kind": "revised",
                "reason": "本轮数据修订变化",
                "target_run_id": launch.run_id,
                "target_project_id": PROJECT_ID,
                "target_mode": "daily",
            }
        )
        plan = build_carry_forward_plan(
            project_id=PROJECT_ID,
            mode="daily",
            execution_basis=BASIS_FULL,
            target_run_id=launch.run_id,
            target_snapshot_id="snapshot-target",
            target_data_cutoff="2026-08-29",
            target_decision_version="decision-target",
            r5_authority_digest="r5-target",
            r6_publication_digest="r6-target",
            r6_receipt_digest="receipt-target",
            r6_output_set_digest=out_digest,
            items=(item,),
            created_at=NOW,
        )
        assert plan.r6_output_set_digest == out_digest
        assert "r6_output_set_digest" in plan.canonical_payload()
        assert plan.canonical_payload()["r6_output_set_digest"] == out_digest
        assert plan.compute_digest() == plan.plan_digest

        plan_dict = plan.as_dict()
        assert plan_dict["r6_output_set_digest"] == out_digest
        reconstituted = CarryForwardPlan.from_mapping(plan_dict)
        assert reconstituted.r6_output_set_digest == out_digest
        assert reconstituted.plan_digest == plan.plan_digest

        saved_plan = registry.save_continuity_plan(plan)
        assert saved_plan.r6_output_set_digest == out_digest
        verified_plan = registry.verify_continuity_plan(PROJECT_ID, launch.run_id)
        assert verified_plan.status == CONTINUITY_PLAN_STATE_VERIFIED
        assert verified_plan.r6_output_set_digest == out_digest

        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)
        finalized = registry.finalize_publication(
            PROJECT_ID,
            launch.run_id,
            r5_authority_packet_digest="r5-target",
            receipt_set_digest="receipt-target",
            r6_output_set_digest=out_digest,
            artifact_member_ids=members,
            artifact_member_set_digest=member_set_digest,
        )
        assert finalized.publication_state == PUBLICATION_STATE_AVAILABLE
        assert finalized.r6_output_set_digest == out_digest
        assert finalized.artifact_member_ids == members
        assert finalized.artifact_member_set == members
        assert finalized.artifact_members == members
        assert finalized.artifact_member_set_digest == member_set_digest

        reloaded_pub = registry.get_publication(PROJECT_ID, launch.run_id)
        assert reloaded_pub.r6_output_set_digest == out_digest
        assert reloaded_pub.artifact_member_ids == members
        assert reloaded_pub.artifact_member_set_digest == member_set_digest
    finally:
        registry.close()


def test_finalize_publication_cas_four_digests_and_replay_conflicts(
    tmp_path: Path,
):
    db_path = tmp_path / "finalize_cas.sqlite3"
    registry = LaunchRegistry(db_path, project_id=PROJECT_ID)
    try:
        launch = registry.reserve(
            PROJECT_ID,
            idempotency_key="finalize-cas-key",
            mode="daily",
            execution_basis=BASIS_FULL,
            current_snapshot_token="snapshot-target",
            data_cutoff="2026-08-29",
            comparison_range="合成完整范围",
        )
        out_digest = "f" * 64
        members = ("art-10", "art-20", "art-30", "art-40")
        member_set_digest = content_digest(list(members))

        item = build_carry_forward_item(
            {
                "object_type": "risk_instance",
                "object_ref": "risk-001",
                "data_change_kind": "revised",
                "reason": "本轮数据修订变化",
                "target_run_id": launch.run_id,
                "target_project_id": PROJECT_ID,
                "target_mode": "daily",
            }
        )
        plan = build_carry_forward_plan(
            project_id=PROJECT_ID,
            mode="daily",
            execution_basis=BASIS_FULL,
            target_run_id=launch.run_id,
            target_snapshot_id="snapshot-target",
            target_data_cutoff="2026-08-29",
            target_decision_version="decision-target",
            r5_authority_digest="r5-correct",
            r6_publication_digest="r6-target",
            r6_receipt_digest="receipt-correct",
            r6_output_set_digest=out_digest,
            items=(item,),
            created_at=NOW,
        )
        registry.save_continuity_plan(plan)
        registry.verify_continuity_plan(PROJECT_ID, launch.run_id)
        _publication(registry, launch.run_id)
        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)

        # 1. R5 digest drift
        with pytest.raises(LaunchRegistryError) as err1:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                r5_authority_packet_digest="r5-wrong",
                receipt_set_digest="receipt-correct",
                r6_output_set_digest=out_digest,
                artifact_member_ids=members,
                artifact_member_set_digest=member_set_digest,
            )
        assert err1.value.code == "continuity_publication_conflict"

        # 2. Receipt digest drift
        with pytest.raises(LaunchRegistryError) as err2:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                r5_authority_packet_digest="r5-correct",
                receipt_set_digest="receipt-wrong",
                r6_output_set_digest=out_digest,
                artifact_member_ids=members,
                artifact_member_set_digest=member_set_digest,
            )
        assert err2.value.code == "continuity_publication_conflict"

        # 3. Output-set digest drift
        with pytest.raises(LaunchRegistryError) as err3:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                r5_authority_packet_digest="r5-correct",
                receipt_set_digest="receipt-correct",
                r6_output_set_digest="0" * 64,
                artifact_member_ids=members,
                artifact_member_set_digest=member_set_digest,
            )
        assert err3.value.code == "continuity_publication_conflict"

        # 4. Invalid members (unsorted / duplicates)
        with pytest.raises(LaunchRegistryError) as err4:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                r5_authority_packet_digest="r5-correct",
                receipt_set_digest="receipt-correct",
                r6_output_set_digest=out_digest,
                artifact_member_ids=("art-20", "art-10", "art-30", "art-40"),
            )
        assert err4.value.code == "invalid_publication_metadata"

        # 5. Invalid member set digest
        with pytest.raises(LaunchRegistryError) as err5:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                r5_authority_packet_digest="r5-correct",
                receipt_set_digest="receipt-correct",
                r6_output_set_digest=out_digest,
                artifact_member_ids=members,
                artifact_member_set_digest="1" * 64,
            )
        assert err5.value.code == "invalid_publication_metadata"

        # 6. Successful finalize
        finalized = registry.finalize_publication(
            PROJECT_ID,
            launch.run_id,
            r5_authority_packet_digest="r5-correct",
            receipt_set_digest="receipt-correct",
            r6_output_set_digest=out_digest,
            artifact_member_ids=members,
            artifact_member_set_digest=member_set_digest,
        )
        assert finalized.publication_state == PUBLICATION_STATE_AVAILABLE
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is True
        assert registry.get_continuity_plan(PROJECT_ID, launch.run_id).status == CONTINUITY_PLAN_STATE_PUBLISHED

        # 7. Same values replay -> returns replayed=True
        replay = registry.finalize_publication(
            PROJECT_ID,
            launch.run_id,
            r5_authority_packet_digest="r5-correct",
            receipt_set_digest="receipt-correct",
            r6_output_set_digest=out_digest,
            artifact_member_ids=members,
            artifact_member_set_digest=member_set_digest,
        )
        assert replay.replayed is True
        assert replay.r6_output_set_digest == out_digest

        # 8. Replay conflict with different output-set digest
        with pytest.raises(LaunchRegistryError) as rep_err1:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                r6_output_set_digest="1" * 64,
            )
        assert rep_err1.value.code in ("publication_cas_conflict", "continuity_publication_conflict")

        # 9. Replay conflict with different members
        with pytest.raises(LaunchRegistryError) as rep_err2:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                artifact_member_ids=("art-90", "art-91", "art-92", "art-99"),
            )
        assert rep_err2.value.code in ("publication_cas_conflict", "continuity_publication_conflict")
    finally:
        registry.close()


@pytest.mark.parametrize(
    "failure_point",
    (
        "finalize.after_publication_update",
        "finalize.after_launch_update",
        "finalize.after_continuity_update",
        "finalize.before_commit",
    ),
)
def test_finalize_publication_fault_injection_rolls_back_atomically(
    tmp_path: Path, failure_point: str
):
    db_path = tmp_path / "finalize_fault.sqlite3"
    registry = LaunchRegistry(db_path, project_id=PROJECT_ID)
    try:
        launch = registry.reserve(
            PROJECT_ID,
            idempotency_key="finalize-fault-key",
            mode="daily",
            execution_basis=BASIS_FULL,
            current_snapshot_token="snapshot-target",
            data_cutoff="2026-08-29",
            comparison_range="合成完整范围",
        )
        out_digest = "c" * 64
        members = ("art-1", "art-2", "art-3", "art-4")
        item = build_carry_forward_item(
            {
                "object_type": "risk_instance",
                "object_ref": "risk-001",
                "data_change_kind": "revised",
                "reason": "本轮数据修订变化",
                "target_run_id": launch.run_id,
                "target_project_id": PROJECT_ID,
                "target_mode": "daily",
            }
        )
        plan = build_carry_forward_plan(
            project_id=PROJECT_ID,
            mode="daily",
            execution_basis=BASIS_FULL,
            target_run_id=launch.run_id,
            target_snapshot_id="snapshot-target",
            target_data_cutoff="2026-08-29",
            target_decision_version="decision-target",
            r5_authority_digest="r5-target",
            r6_publication_digest="r6-target",
            r6_receipt_digest="receipt-target",
            r6_output_set_digest=out_digest,
            items=(item,),
            created_at=NOW,
        )
        registry.save_continuity_plan(plan)
        registry.verify_continuity_plan(PROJECT_ID, launch.run_id)
        _publication(registry, launch.run_id)
        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)

        def fail(point: str) -> None:
            if point == failure_point:
                raise RuntimeError(point)

        registry.set_failure_injector(fail)
        with pytest.raises(LaunchRegistryError) as err:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                r5_authority_packet_digest="r5-target",
                receipt_set_digest="receipt-target",
                r6_output_set_digest=out_digest,
                artifact_member_ids=members,
            )
        assert err.value.code == "store_closed"

        # Verification: publication stays publishing, launch result flag remains False, plan remains verified
        assert registry.get_publication(PROJECT_ID, launch.run_id).publication_state == "publishing"
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False
        assert registry.get_continuity_plan(PROJECT_ID, launch.run_id).status == CONTINUITY_PLAN_STATE_VERIFIED

        # Clear failure injector and retry successfully
        registry.set_failure_injector(None)
        finalized = registry.finalize_publication(
            PROJECT_ID,
            launch.run_id,
            r5_authority_packet_digest="r5-target",
            receipt_set_digest="receipt-target",
            r6_output_set_digest=out_digest,
            artifact_member_ids=members,
        )
        assert finalized.publication_state == PUBLICATION_STATE_AVAILABLE
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is True
        assert registry.get_continuity_plan(PROJECT_ID, launch.run_id).status == CONTINUITY_PLAN_STATE_PUBLISHED
    finally:
        registry.close()



# --- Slice-08D §13/§14: busy_timeout, source-enumerated hooks, late callback ---

_LAUNCH_REGISTRY_SRC = Path(__file__).resolve().parents[1] / "src" / "mm_r7" / "launch_registry.py"


def _enumerate_source_failure_hooks() -> frozenset[str]:
    """Enumerate current LaunchRegistry failure hooks from source.

    Format-string hooks such as ``continuity.save.after_item_%d`` are expanded
    to the fixture ordinal ``0`` used by `_plan`. Prefixed
    ``failure_prefix + ".after_update"`` defaults to ``continuity.status``.
    """
    source = _LAUNCH_REGISTRY_SRC.read_text(encoding="utf-8")
    static = set(re.findall(r'_inject_failure\(\s*"([^"%]+)"\s*\)', source))
    for template in re.findall(
        r'_inject_failure\(\s*\n?\s*"([^"]*%[^"]*)"\s*%', source
    ):
        if template == "continuity.save.after_item_%d":
            static.add("continuity.save.after_item_0")
        else:
            raise AssertionError(f"unhandled failure-hook template: {template}")
    if 'failure_prefix + ".after_update"' in source:
        static.add("continuity.status.after_update")
    return frozenset(static)


def _prepare_verified_publication(registry: LaunchRegistry, *, key: str):
    launch = registry.reserve(
        PROJECT_ID,
        idempotency_key=key,
        mode="daily",
        execution_basis=BASIS_FULL,
        current_snapshot_token="snapshot-target",
        data_cutoff="2026-08-29",
        comparison_range="合成完整范围",
    )
    plan = _plan(launch.run_id)
    registry.save_continuity_plan(plan)
    registry.verify_continuity_plan(PROJECT_ID, launch.run_id)
    publication = _publication(registry, launch.run_id)
    registry.mark_completed(launch.run_id, project_id=PROJECT_ID)
    members = ("art-1", "art-2", "art-3", "art-4")
    return launch, plan, publication, members, content_digest(list(members))


def test_busy_timeout_pragma_10000_after_close_reopen(tmp_path: Path):
    """08D: reopen must assert real PRAGMA busy_timeout=10000, not the property alone."""
    db_path = tmp_path / "busy_timeout.sqlite3"
    registry = LaunchRegistry(db_path, project_id=PROJECT_ID)
    try:
        launch, plan, publication, members, member_digest = _prepare_verified_publication(
            registry, key="busy-timeout-reopen"
        )
        before = {
            "plan_digest": registry.get_continuity_plan(
                PROJECT_ID, launch.run_id
            ).plan_digest,
            "plan_status": registry.get_continuity_plan(
                PROJECT_ID, launch.run_id
            ).status,
            "publication_state": registry.get_publication(
                PROJECT_ID, launch.run_id
            ).publication_state,
            "history_count": len(registry.list_history(PROJECT_ID)),
        }
        assert BUSY_TIMEOUT_MS == 10_000
        # Execute the live connection PRAGMA (contract forbids property-only checks).
        pragma_before = registry._conn.execute("PRAGMA busy_timeout").fetchone()[0]
        assert pragma_before == 10_000
        registry.close()
        registry.reopen()
        pragma_after = registry._conn.execute("PRAGMA busy_timeout").fetchone()[0]
        assert pragma_after == 10_000
        after_plan = registry.get_continuity_plan(PROJECT_ID, launch.run_id)
        after_pub = registry.get_publication(PROJECT_ID, launch.run_id)
        assert after_plan.plan_digest == before["plan_digest"]
        assert after_plan.status == before["plan_status"]
        assert after_pub.publication_state == before["publication_state"]
        assert len(registry.list_history(PROJECT_ID)) == before["history_count"]
        finalized = registry.finalize_publication(
            PROJECT_ID,
            launch.run_id,
            r5_authority_packet_digest="r5-target",
            receipt_set_digest="receipt-target",
            r6_output_set_digest="6" * 64,
            artifact_member_ids=members,
            artifact_member_set_digest=member_digest,
        )
        assert finalized.publication_state == PUBLICATION_STATE_AVAILABLE
        assert registry._conn.execute("PRAGMA busy_timeout").fetchone()[0] == 10_000
    finally:
        registry.close()

@pytest.mark.parametrize("failure_point", sorted(_enumerate_source_failure_hooks()))
def test_each_source_failure_hook_rolls_back_without_half_publication(
    tmp_path: Path, failure_point: str
):
    """Hit every current source hook; miss => parametrize collection fails the suite."""
    db_path = tmp_path / "hook.sqlite3"
    hit = []

    def fail(point: str) -> None:
        hit.append(point)
        if point == failure_point:
            raise RuntimeError(point)

    registry = LaunchRegistry(db_path, project_id=PROJECT_ID)
    try:
        if failure_point.startswith(
            ("continuity.after_plan", "continuity.save.", "continuity.after_item")
        ) or failure_point in {
            "continuity.before_commit",
        }:
            # Save-path hooks (before_commit also fires on status; save covers it).
            if failure_point == "continuity.before_commit":
                # Prefer save path; status path also injects the same name.
                pass
            launch = registry.reserve(
                PROJECT_ID,
                idempotency_key="hook-save",
                mode="daily",
                execution_basis=BASIS_FULL,
                current_snapshot_token="snapshot-target",
                data_cutoff="2026-08-29",
                comparison_range="合成完整范围",
            )
            registry.set_failure_injector(fail)
            with pytest.raises(LaunchRegistryError) as err:
                registry.save_continuity_plan(_plan(launch.run_id))
            assert err.value.code == "store_closed"
            assert failure_point in hit
            assert registry.list_continuity_plans(PROJECT_ID) == ()
            registry.set_failure_injector(None)
            assert registry.save_continuity_plan(_plan(launch.run_id)).plan_digest
            return

        if failure_point in {
            "continuity.status.after_update",
            "continuity.after_status_update",
            "continuity.status.before_commit",
        }:
            launch = registry.reserve(
                PROJECT_ID,
                idempotency_key="hook-status",
                mode="daily",
                execution_basis=BASIS_FULL,
                current_snapshot_token="snapshot-target",
                data_cutoff="2026-08-29",
                comparison_range="合成完整范围",
            )
            registry.save_continuity_plan(_plan(launch.run_id))
            registry.set_failure_injector(fail)
            with pytest.raises(LaunchRegistryError) as err:
                registry.verify_continuity_plan(PROJECT_ID, launch.run_id)
            assert err.value.code == "store_closed"
            assert failure_point in hit
            assert (
                registry.get_continuity_plan(PROJECT_ID, launch.run_id).status
                == CONTINUITY_PLAN_STATE_STAGING
            )
            registry.set_failure_injector(None)
            assert (
                registry.verify_continuity_plan(PROJECT_ID, launch.run_id).status
                == CONTINUITY_PLAN_STATE_VERIFIED
            )
            return

        if failure_point == "bind_publication_runtime_manifest.after_update":
            launch = registry.reserve(
                PROJECT_ID,
                idempotency_key="hook-bind",
                mode="daily",
                execution_basis=BASIS_FULL,
                current_snapshot_token="snapshot-target",
                data_cutoff="2026-08-29",
                comparison_range="合成完整范围",
            )
            registry.reserve_publication(
                PROJECT_ID,
                launch.run_id,
                idempotency_key="publication-bind",
                request_fingerprint="runtime-bind-fingerprint",
                snapshot_token="snapshot-target",
                data_cutoff="2026-08-29",
                setup_manifest_identity={
                    "work_units": {
                        "deterministic-unit": False,
                        "risk-unit": True,
                    }
                },
                mandatory_denominator=1,
            )
            registry.set_failure_injector(fail)
            with pytest.raises(LaunchRegistryError) as err:
                registry.bind_publication_runtime_manifest(
                    PROJECT_ID,
                    launch.run_id,
                    expected_state=PUBLICATION_STATE_PUBLISHING,
                    expected_fingerprint="runtime-bind-fingerprint",
                    runtime_manifest_revision=7,
                    runtime_manifest_identity={
                        "work_units": {
                            "deterministic-unit": False,
                            "risk-unit": True,
                        }
                    },
                    runtime_manifest_digest="runtime-manifest-digest-v7",
                    mandatory_denominator=1,
                )
            assert err.value.code == "store_closed"
            assert failure_point in hit
            pub = registry.get_publication(PROJECT_ID, launch.run_id)
            assert pub.publication_state == PUBLICATION_STATE_PUBLISHING
            assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False
            registry.set_failure_injector(None)
            bound = registry.bind_publication_runtime_manifest(
                PROJECT_ID,
                launch.run_id,
                expected_state=PUBLICATION_STATE_PUBLISHING,
                expected_fingerprint="runtime-bind-fingerprint",
                runtime_manifest_revision=7,
                runtime_manifest_identity={
                    "work_units": {
                        "deterministic-unit": False,
                        "risk-unit": True,
                    }
                },
                runtime_manifest_digest="runtime-manifest-digest-v7",
                mandatory_denominator=1,
            )
            assert bound.publication_state == PUBLICATION_STATE_PUBLISHING
            assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False
            return

        # finalize / publish hooks
        launch, plan, publication, members, member_digest = _prepare_verified_publication(
            registry, key="hook-finalize"
        )
        registry.set_failure_injector(fail)
        with pytest.raises(LaunchRegistryError) as err:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                r5_authority_packet_digest="r5-target",
                receipt_set_digest="receipt-target",
                r6_output_set_digest="6" * 64,
                artifact_member_ids=members,
                artifact_member_set_digest=member_digest,
            )
        assert err.value.code == "store_closed"
        assert failure_point in hit
        assert (
            registry.get_publication(PROJECT_ID, launch.run_id).publication_state
            == PUBLICATION_STATE_PUBLISHING
        )
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False
        assert (
            registry.get_continuity_plan(PROJECT_ID, launch.run_id).status
            == CONTINUITY_PLAN_STATE_VERIFIED
        )
        registry.set_failure_injector(None)
        finalized = registry.finalize_publication(
            PROJECT_ID,
            launch.run_id,
            r5_authority_packet_digest="r5-target",
            receipt_set_digest="receipt-target",
            r6_output_set_digest="6" * 64,
            artifact_member_ids=members,
            artifact_member_set_digest=member_digest,
        )
        assert finalized.publication_state == PUBLICATION_STATE_AVAILABLE
        assert registry.get_continuity_plan(PROJECT_ID, launch.run_id).status == (
            CONTINUITY_PLAN_STATE_PUBLISHED
        )
    finally:
        registry.close()


def test_late_callback_after_reopen_same_digest_recovers_without_second_publication(
    tmp_path: Path,
):
    db_path = tmp_path / "late_callback.sqlite3"
    registry = LaunchRegistry(db_path, project_id=PROJECT_ID)
    try:
        launch, plan, publication, members, member_digest = _prepare_verified_publication(
            registry, key="late-callback"
        )
        plan_digest = plan.plan_digest
        registry.close()
        # Late callback after process-boundary reopen with same digests.
        registry.reopen()
        assert registry._conn.execute("PRAGMA busy_timeout").fetchone()[0] == 10_000
        first = registry.finalize_publication(
            PROJECT_ID,
            launch.run_id,
            r5_authority_packet_digest="r5-target",
            receipt_set_digest="receipt-target",
            r6_output_set_digest="6" * 64,
            artifact_member_ids=members,
            artifact_member_set_digest=member_digest,
        )
        assert first.publication_state == PUBLICATION_STATE_AVAILABLE
        assert first.replayed is False
        assert registry.get_continuity_plan(PROJECT_ID, launch.run_id).status == (
            CONTINUITY_PLAN_STATE_PUBLISHED
        )
        # Duplicate finalize / late same-digest callback replays original facts.
        replay = registry.finalize_publication(
            PROJECT_ID,
            launch.run_id,
            r5_authority_packet_digest="r5-target",
            receipt_set_digest="receipt-target",
            r6_output_set_digest="6" * 64,
            artifact_member_ids=members,
            artifact_member_set_digest=member_digest,
        )
        assert replay.replayed is True
        assert replay.publication_id == first.publication_id
        # Conflicting late callback must not create a second publication.
        with pytest.raises(LaunchRegistryError) as conflict:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                r6_output_set_digest="1" * 64,
            )
        assert conflict.value.code in (
            "publication_cas_conflict",
            "continuity_publication_conflict",
        )
        pubs = [
            row
            for row in registry.list_history(PROJECT_ID)
            if row.get("run_id") == launch.run_id
            or row.get("public_run_token") == launch.public_run_token
        ]
        # list_history is public projection; fall back to publication row count.
        assert len(registry.list_history(PROJECT_ID)) == 1
        assert (
            registry.get_publication(PROJECT_ID, launch.run_id).publication_id
            == first.publication_id
        )
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is True
        assert (
            registry.get_continuity_plan(PROJECT_ID, launch.run_id).plan_digest
            == plan_digest
            or registry.get_continuity_plan(PROJECT_ID, launch.run_id).status
            == CONTINUITY_PLAN_STATE_PUBLISHED
        )
    finally:
        registry.close()


def test_cas_conflict_keeps_verified_real_drift_blocks_no_half_publication(
    tmp_path: Path,
):
    registry = LaunchRegistry(tmp_path / "cas_drift.sqlite3", project_id=PROJECT_ID)
    try:
        launch = registry.reserve(
            PROJECT_ID,
            idempotency_key="cas-drift",
            mode="daily",
            execution_basis=BASIS_FULL,
            current_snapshot_token="snapshot-target",
            data_cutoff="2026-08-29",
            comparison_range="合成完整范围",
        )
        plan = _plan(launch.run_id)
        registry.save_continuity_plan(plan)
        # Retryable CAS on verify: wrong expected digest keeps staging closed.
        with pytest.raises(LaunchRegistryError) as cas:
            registry.verify_continuity_plan(
                PROJECT_ID,
                launch.run_id,
                expected_plan_digest="0" * 64,
            )
        assert cas.value.code == "continuity_plan_cas_conflict"
        assert (
            registry.get_continuity_plan(PROJECT_ID, launch.run_id).status
            == CONTINUITY_PLAN_STATE_STAGING
        )
        verified = registry.verify_continuity_plan(
            PROJECT_ID, launch.run_id, expected_plan_digest=plan.plan_digest
        )
        assert verified.status == CONTINUITY_PLAN_STATE_VERIFIED
        publication = _publication(registry, launch.run_id)
        registry.mark_completed(launch.run_id, project_id=PROJECT_ID)
        members = ("art-1", "art-2", "art-3", "art-4")
        member_digest = content_digest(list(members))
        # Real digest drift on finalize stays closed (no available publication).
        with pytest.raises(LaunchRegistryError) as drift:
            registry.finalize_publication(
                PROJECT_ID,
                launch.run_id,
                r5_authority_packet_digest="r5-drift",
                receipt_set_digest="receipt-target",
                r6_output_set_digest="6" * 64,
                artifact_member_ids=members,
                artifact_member_set_digest=member_digest,
            )
        assert drift.value.code == "continuity_publication_conflict"
        assert (
            registry.get_publication(PROJECT_ID, launch.run_id).publication_state
            == PUBLICATION_STATE_PUBLISHING
        )
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False
        # Recoverable publication failure then retry back to publishing, then succeed.
        failed = registry.record_publication_failure(
            project_id=PROJECT_ID,
            run_id=launch.run_id,
            state=PUBLICATION_STATE_RECOVERABLE_FAILED,
            expected_state=PUBLICATION_STATE_PUBLISHING,
            error_code="transient_backend",
            error_message="synthetic transient",
        )
        assert failed.publication_state == PUBLICATION_STATE_RECOVERABLE_FAILED
        resumed = registry.retry_publication(
            project_id=PROJECT_ID,
            run_id=launch.run_id,
            expected_state=PUBLICATION_STATE_RECOVERABLE_FAILED,
        )
        assert resumed.publication_state == PUBLICATION_STATE_PUBLISHING
        # Hard block path remains explainable and never opens result_available.
        blocked = registry.record_publication_failure(
            project_id=PROJECT_ID,
            run_id=launch.run_id,
            state=PUBLICATION_STATE_BLOCKED,
            expected_state=PUBLICATION_STATE_PUBLISHING,
            error_code="authority_blocked",
            error_message="synthetic block",
        )
        assert blocked.publication_state == PUBLICATION_STATE_BLOCKED
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False
        # Plan can be explicitly blocked on identity/digest drift without publishing.
        blocked_plan = registry.block_continuity_plan(PROJECT_ID, launch.run_id)
        assert blocked_plan.status == CONTINUITY_PLAN_STATE_BLOCKED
        assert registry.get(launch.run_id, project_id=PROJECT_ID).result_available is False
    finally:
        registry.close()
