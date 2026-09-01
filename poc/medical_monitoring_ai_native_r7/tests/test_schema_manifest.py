"""Slice-09B schema manifest, inspector, and constructor-boundary tests."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from fixtures_schema_manifest import (
    make_binding,
    make_launch,
    make_profile,
    make_project,
    make_risk,
    make_runtime,
)
import mm_r1.store as store_module
from mm_r1.store import Store, StoreError
from mm_r1.schema_shape import connection_shape, shape_from_ddl
from mm_r1.store import _runtime_schema_shape
from mm_r7 import launch_registry as launch_module
from mm_r7 import migration as migration_module
from mm_r7 import schema_manifest as schema_module
from mm_r7 import launch_schema as launch_schema_module
from mm_r7.launch_schema import (
    BASE_DDL,
    CONTINUITY_INDEX_DDL,
    CONTINUITY_ITEMS_DDL,
    CONTINUITY_PLANS_DDL,
    LAUNCH_DDL,
    PUBLICATION_DDL,
    RESULT_CONTEXT_INDEX_DDL,
)
from mm_r7.launch_registry import LaunchRegistry, LaunchRegistryError
from mm_r7.profile_store import ProfileStore, ProfileStoreError
from mm_r7.run_binding import RunBindingError, RunBindingStore
from mm_r7.run_setup import RiskRuleRegistry, RunSetupError
from mm_r7.schema_manifest import (
    BINDING_MEMBER,
    BINDING_V1,
    LAUNCH_MEMBER,
    LAUNCH_V1,
    LAUNCH_V2,
    LAUNCH_V3,
    LAUNCH_V4,
    PROFILE_MEMBER,
    RISK_MEMBER,
    RUNTIME_MEMBER,
    RUNTIME_V4,
    RUNTIME_V5,
    RUNTIME_V6,
    SCHEMA_MANIFEST_DIGEST,
    SchemaClassification,
    ProjectSchemaInspector,
    canonical_json_bytes,
    get_schema_manifest,
    inspect_member,
    schema_manifest_digest,
)




def test_manifest_is_explicit_deterministic_and_structural() -> None:
    manifest = get_schema_manifest()
    assert schema_manifest_digest(manifest) == SCHEMA_MANIFEST_DIGEST
    assert hashlib.sha256(canonical_json_bytes(manifest)).hexdigest() != ""
    assert set(manifest["members"]) == {
        RUNTIME_MEMBER,
        "execution_control",
        PROFILE_MEMBER,
        BINDING_MEMBER,
        LAUNCH_MEMBER,
        RISK_MEMBER,
    }
    assert manifest["members"][RUNTIME_MEMBER]["versions"].keys() == {
        RUNTIME_V4,
        RUNTIME_V5,
        RUNTIME_V6,
    }
    assert manifest["members"][LAUNCH_MEMBER]["versions"].keys() == {
        LAUNCH_V1,
        LAUNCH_V2,
        LAUNCH_V3,
        LAUNCH_V4,
    }
    for member in (RUNTIME_MEMBER, PROFILE_MEMBER, BINDING_MEMBER, LAUNCH_MEMBER, RISK_MEMBER):
        versions = manifest["members"][member]["versions"]
        for variant in versions.values():
            shape = variant["shape"]
            assert isinstance(shape["user_version"], int)
            assert shape["tables"]
            for table in shape["tables"].values():
                assert table["columns"]
                assert all("declared_type" in column for column in table["columns"])
                assert "foreign_keys" in table
                assert "indexes" in table



def test_shared_shape_and_launch_ddl_sources_preserve_frozen_contract(
    tmp_path: Path,
) -> None:
    manifest = get_schema_manifest()
    assert SCHEMA_MANIFEST_DIGEST == (
        "32f081a61730001e9cc69482b958de7a8b3af6e226b14bf445caad398a7c6a8a"
    )
    assert schema_module._connection_shape is connection_shape
    assert schema_module._shape_from_ddl is shape_from_ddl
    assert _runtime_schema_shape is connection_shape
    assert schema_module._LAUNCH_DDL is LAUNCH_DDL
    assert launch_module._DDL is LAUNCH_DDL
    assert launch_module._BASE_DDL is BASE_DDL
    assert launch_module._PUBLICATION_DDL is PUBLICATION_DDL
    assert launch_module._RESULT_CONTEXT_INDEX_DDL is RESULT_CONTEXT_INDEX_DDL
    assert launch_module._CONTINUITY_PLANS_DDL is CONTINUITY_PLANS_DDL
    assert launch_module._CONTINUITY_ITEMS_DDL is CONTINUITY_ITEMS_DDL
    assert launch_module._CONTINUITY_INDEX_DDL is CONTINUITY_INDEX_DDL
    assert migration_module._PUBLICATION_DDL is PUBLICATION_DDL
    assert migration_module._RESULT_CONTEXT_INDEX_DDL is RESULT_CONTEXT_INDEX_DDL
    assert migration_module._CONTINUITY_PLANS_DDL is CONTINUITY_PLANS_DDL
    assert migration_module._CONTINUITY_ITEMS_DDL is CONTINUITY_ITEMS_DDL
    assert migration_module._CONTINUITY_INDEX_DDL is CONTINUITY_INDEX_DDL
    r1_source = Path(store_module.__file__).read_text(encoding="utf-8")
    manifest_source = Path(schema_module.__file__).read_text(encoding="utf-8")
    launch_registry_source = Path(launch_module.__file__).read_text(encoding="utf-8")
    migration_source = Path(migration_module.__file__).read_text(encoding="utf-8")
    launch_schema_source = Path(launch_schema_module.__file__).read_text(
        encoding="utf-8"
    )
    for source in (r1_source, manifest_source):
        for helper_name in (
            "_normalise_sql",
            "_quote_identifier",
            "_connection_shape",
            "_shape_from_ddl",
            "_runtime_schema_shape",
        ):
            assert "def " + helper_name not in source
    assert "from mm_r7" not in r1_source
    launch_markers = (
        "CREATE TABLE IF NOT EXISTS r7_launch_registry_meta",
        "CREATE TABLE IF NOT EXISTS r7_result_publications",
        "CREATE TABLE IF NOT EXISTS r7_continuity_plans",
        "CREATE TABLE IF NOT EXISTS r7_continuity_items",
    )
    for marker in launch_markers:
        assert marker in launch_schema_source
        assert marker not in manifest_source
        assert marker not in launch_registry_source
        assert marker not in migration_source
    for private_call in (
        "._fingerprint(",
        "._current_snapshot(",
        "._member_bytes(",
        "._verify_artifact_closure(",
        "._snapshot_workspace(",
    ):
        assert private_call not in migration_source
    runtime = make_runtime(tmp_path / "runtime.sqlite3", RUNTIME_V6)
    with sqlite3.connect(runtime) as connection:
        actual = connection_shape(connection)
    expected = manifest["members"][RUNTIME_MEMBER]["versions"][RUNTIME_V6]["shape"]
    assert actual == expected

def test_current_project_with_default_optional_members_is_current(tmp_path: Path) -> None:
    project = make_project(tmp_path / "project-current")
    tracked = (
        project / "runtime" / "monitoring_runtime.sqlite3",
        project / "execution_profiles.sqlite3",
        project / "monitoring_run_bindings.sqlite3",
    )
    before = {path: path.read_bytes() for path in tracked}
    result = ProjectSchemaInspector(project).inspect()
    assert result.classification is SchemaClassification.CURRENT
    assert result.can_view is True
    assert result.can_upgrade is False
    assert result.members["execution_control"].present is False
    assert result.members[LAUNCH_MEMBER].present is False
    assert result.members[RISK_MEMBER].present is False
    assert result.members[LAUNCH_MEMBER].classification is SchemaClassification.CURRENT
    assert result.members[RISK_MEMBER].classification is SchemaClassification.CURRENT
    assert {path: path.read_bytes() for path in tracked} == before


def test_current_control_and_risk_members_match_exact_shapes(tmp_path: Path) -> None:
    project = make_project(
        tmp_path / "project-with-optional-members",
        include_control=True,
        include_risk=True,
    )
    result = ProjectSchemaInspector(project).inspect()
    assert result.classification is SchemaClassification.CURRENT
    assert result.members["execution_control"].classification is SchemaClassification.CURRENT
    assert result.members["execution_control"].present is True
    assert result.members[RISK_MEMBER].classification is SchemaClassification.CURRENT
    assert result.members[RISK_MEMBER].present is True


def test_supported_runtime_legacy_is_readable_and_upgradeable(tmp_path: Path) -> None:
    for version in (RUNTIME_V4, RUNTIME_V5):
        project = make_project(tmp_path / f"project-runtime-{version}", runtime_version=version)
        result = ProjectSchemaInspector(project).inspect()
        assert result.classification is SchemaClassification.LEGACY
        assert result.can_view is True
        assert result.can_upgrade is True
        assert result.members[RUNTIME_MEMBER].schema_version == version
        assert result.members[RUNTIME_MEMBER].reason_code == "supported_legacy_shape"


def test_supported_launch_legacy_is_readable_and_upgradeable(tmp_path: Path) -> None:
    for version in (LAUNCH_V1, LAUNCH_V2, LAUNCH_V3):
        project = make_project(
            tmp_path / f"project-launch-{version[-2:]}",
            launch_version=version,
        )
        result = ProjectSchemaInspector(project).inspect()
        assert result.classification is SchemaClassification.LEGACY
        assert result.members[LAUNCH_MEMBER].schema_version == version


def test_marker_three_and_future_marker_are_unknown_not_legacy(tmp_path: Path) -> None:
    runtime = make_runtime(tmp_path / "runtime.sqlite3", RUNTIME_V5)
    connection = sqlite3.connect(runtime)
    try:
        connection.execute("UPDATE meta SET value='3' WHERE key='schema_version'")
        connection.commit()
    finally:
        connection.close()
    marker3 = inspect_member(runtime, RUNTIME_MEMBER)
    assert marker3.classification is SchemaClassification.UNKNOWN
    assert marker3.reason_code == "unsupported_legacy_marker"
    assert marker3.schema_version == "3"

    future = tmp_path / "future.sqlite3"
    make_runtime(future, RUNTIME_V6)
    connection = sqlite3.connect(future)
    try:
        connection.execute("UPDATE meta SET value='9' WHERE key='schema_version'")
        connection.commit()
    finally:
        connection.close()
    future_result = inspect_member(future, RUNTIME_MEMBER)
    assert future_result.classification is SchemaClassification.UNKNOWN
    assert future_result.reason_code == "unsupported_schema_version"
    assert future_result.schema_version == "9"


def test_missing_marker_and_structural_corruption_are_distinct(tmp_path: Path) -> None:
    profile = make_profile(tmp_path / "profile.sqlite3")
    connection = sqlite3.connect(profile)
    try:
        connection.execute("DELETE FROM profile_store_meta WHERE key='schema_version'")
        connection.commit()
    finally:
        connection.close()
    missing_marker = inspect_member(profile, PROFILE_MEMBER)
    assert missing_marker.classification is SchemaClassification.UNKNOWN
    assert missing_marker.reason_code == "marker_missing"

    binding = make_binding(tmp_path / "binding.sqlite3", malformed=True)
    malformed = inspect_member(binding, BINDING_MEMBER)
    assert malformed.classification is SchemaClassification.CORRUPT
    assert malformed.reason_code == "shape_mismatch"


def test_binding_empty_table_is_current_and_mixed_rows_are_corrupt(tmp_path: Path) -> None:
    binding = make_binding(tmp_path / "binding.sqlite3")
    empty = inspect_member(binding, BINDING_MEMBER)
    assert empty.classification is SchemaClassification.CURRENT
    assert empty.schema_version == BINDING_V1

    connection = sqlite3.connect(binding)
    try:
        connection.execute(
            "INSERT INTO monitoring_run_bindings "
            "(run_id,binding_digest,project_id,mode,execution_basis,data_cutoff,"
            "source_revision_id,execution_profile_id,execution_profile_digest,profile_id,"
            "user_config_name,effective_selector,adapter_id,adapter_version,"
            "fallback_profile_ids_json,schema_version,frozen_profile_json,record_json) "
            "VALUES ('a','d','p','daily','full','2026-08-30','r','ep','ed','p','cfg',"
            "'selector','adapter','v','[]','r7-slice01-run-binding-v1','{}','{}')"
        )
        connection.execute(
            "INSERT INTO monitoring_run_bindings "
            "(run_id,binding_digest,project_id,mode,execution_basis,data_cutoff,"
            "source_revision_id,execution_profile_id,execution_profile_digest,profile_id,"
            "user_config_name,effective_selector,adapter_id,adapter_version,"
            "fallback_profile_ids_json,schema_version,frozen_profile_json,record_json) "
            "VALUES ('b','d','p','daily','full','2026-08-30','r','ep','ed','p','cfg',"
            "'selector','adapter','v','[]','future-v9','{}','{}')"
        )
        connection.commit()
    finally:
        connection.close()
    mixed = inspect_member(binding, BINDING_MEMBER)
    assert mixed.classification is SchemaClassification.CORRUPT
    assert mixed.reason_code == "mixed_row_schema_version"


def test_corrupt_sqlite_is_classified_without_writes(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.sqlite3"
    path.write_bytes(b"not a sqlite database")
    before = path.read_bytes()
    result = inspect_member(path, PROFILE_MEMBER)
    assert result.classification is SchemaClassification.CORRUPT
    assert result.reason_code == "sqlite_malformed"
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    ("member", "builder", "constructor", "error_type"),
    (
        (
            RUNTIME_MEMBER,
            lambda root: make_runtime(root / "runtime.sqlite3", RUNTIME_V5),
            Store,
            StoreError,
        ),
        (
            PROFILE_MEMBER,
            lambda root: make_profile(root / "profile.sqlite3", marker="legacy-v0"),
            ProfileStore,
            ProfileStoreError,
        ),
        (
            BINDING_MEMBER,
            lambda root: make_binding(root / "binding.sqlite3", malformed=True),
            RunBindingStore,
            RunBindingError,
        ),
        (
            LAUNCH_MEMBER,
            lambda root: make_launch(root / "launch.sqlite3", LAUNCH_V2),
            LaunchRegistry,
            LaunchRegistryError,
        ),
        (
            RISK_MEMBER,
            lambda root: make_risk(root / "risk.sqlite3", malformed=True),
            RiskRuleRegistry,
            RunSetupError,
        ),
    ),
)
def test_mutable_constructors_fail_closed_and_preserve_source_bytes(
    tmp_path: Path,
    member: str,
    builder,
    constructor,
    error_type,
) -> None:
    root = tmp_path / member
    root.mkdir()
    path = builder(root)
    before = path.read_bytes()
    if member == RUNTIME_MEMBER:
        with pytest.raises(error_type):
            constructor(path, root / "artifacts")
    elif member == LAUNCH_MEMBER:
        with pytest.raises(error_type):
            constructor(path, project_id="synthetic-schema-project")
    else:
        with pytest.raises(error_type):
            constructor(path)
    assert path.read_bytes() == before


def test_project_unknown_and_corrupt_states_fail_closed(tmp_path: Path) -> None:
    project_unknown = make_project(tmp_path / "project-unknown")
    profile = project_unknown / "execution_profiles.sqlite3"
    connection = sqlite3.connect(profile)
    try:
        connection.execute(
            "UPDATE profile_store_meta SET value='future-v9' WHERE key='schema_version'"
        )
        connection.commit()
    finally:
        connection.close()
    unknown = ProjectSchemaInspector(project_unknown).inspect()
    assert unknown.classification is SchemaClassification.UNKNOWN
    assert unknown.can_view is False
    assert unknown.can_upgrade is False

    project_corrupt = make_project(tmp_path / "project-corrupt")
    binding = project_corrupt / "monitoring_run_bindings.sqlite3"
    connection = sqlite3.connect(binding)
    try:
        connection.execute("ALTER TABLE monitoring_run_bindings ADD COLUMN drift TEXT")
        connection.commit()
    finally:
        connection.close()
    corrupt = ProjectSchemaInspector(project_corrupt).inspect()
    assert corrupt.classification is SchemaClassification.CORRUPT
    assert corrupt.can_view is False
    assert corrupt.can_upgrade is False
