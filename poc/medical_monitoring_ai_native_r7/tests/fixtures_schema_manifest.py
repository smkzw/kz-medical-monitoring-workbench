"""Synthetic/offline project schema fixtures for Slice-09B tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from mm_r1.store import Store
from mm_r7.launch_registry import LaunchRegistry
from mm_r7.profile_store import ProfileStore
from mm_r7.run_binding import RunBindingStore
from mm_r7.run_setup import RiskRuleRegistry
from mm_r7.schema_manifest import (
    LAUNCH_V1,
    LAUNCH_V2,
    LAUNCH_V3,
    RUNTIME_V4,
    RUNTIME_V5,
)


def _connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(str(path))


def make_runtime(path: Path, version: str = "6", *, control: bool = False) -> Path:
    """Create a current R1 runtime and downgrade only its synthetic shape."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Store(path, path.parent / "artifacts").close()
    if version not in {RUNTIME_V4, RUNTIME_V5, "6"}:
        raise ValueError(version)
    if version == "6" and not control:
        return path
    connection = _connect(path)
    try:
        if version != "6":
            connection.execute("DROP TABLE work_unit_capability_attempts")
            if version == RUNTIME_V4:
                connection.execute("ALTER TABLE node_runs DROP COLUMN manifest_revision")
                connection.execute("ALTER TABLE node_attempts DROP COLUMN manifest_revision")
            connection.execute("UPDATE meta SET value=? WHERE key='schema_version'", (version,))
        if control:
            connection.execute(
                """CREATE TABLE r7_execution_control (
                    run_id TEXT PRIMARY KEY NOT NULL REFERENCES monitoring_runs(run_id),
                    manifest_revision INTEGER NOT NULL,
                    generation INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    owner_token TEXT NOT NULL DEFAULT '',
                    lease_expires_at REAL,
                    cancel_requested INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )
        connection.commit()
    finally:
        connection.close()
    return path


def make_profile(path: Path, marker: Optional[str] = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    ProfileStore(path).close()
    if marker is not None:
        connection = _connect(path)
        try:
            connection.execute(
                "UPDATE profile_store_meta SET value=? WHERE key='schema_version'",
                (marker,),
            )
            connection.commit()
        finally:
            connection.close()
    return path


def make_binding(path: Path, *, malformed: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    RunBindingStore(path).close()
    if malformed:
        connection = _connect(path)
        try:
            connection.execute("ALTER TABLE monitoring_run_bindings ADD COLUMN drift TEXT")
            connection.commit()
        finally:
            connection.close()
    return path


def make_launch(path: Path, version: str = "mm-r7-slice08b-launch-registry-v4") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    registry = LaunchRegistry(path, project_id="synthetic-schema-project")
    registry.close()
    if version == "mm-r7-slice08b-launch-registry-v4":
        return path
    if version not in {LAUNCH_V1, LAUNCH_V2, LAUNCH_V3}:
        raise ValueError(version)
    connection = _connect(path)
    try:
        if version == LAUNCH_V1:
            connection.execute("DROP TABLE r7_continuity_items")
            connection.execute("DROP TABLE r7_continuity_plans")
            connection.execute("DROP TABLE r7_result_publications")
        elif version == LAUNCH_V2:
            connection.execute("DROP TABLE r7_continuity_items")
            connection.execute("DROP TABLE r7_continuity_plans")
        else:
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
            "UPDATE r7_launch_registry_meta SET value=? WHERE key='schema_version'",
            (version,),
        )
        connection.commit()
    finally:
        connection.close()
    return path


def make_risk(path: Path, *, malformed: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    RiskRuleRegistry(path).close()
    if malformed:
        connection = _connect(path)
        try:
            connection.execute("ALTER TABLE r7_risk_rule_revisions ADD COLUMN drift TEXT")
            connection.commit()
        finally:
            connection.close()
    return path


def make_project(
    root: Path,
    *,
    runtime_version: str = "6",
    profile_marker: Optional[str] = None,
    launch_version: Optional[str] = None,
    include_risk: bool = False,
    include_control: bool = False,
) -> Path:
    """Build the minimum synthetic project plus optional registry members."""
    root.mkdir(parents=True, exist_ok=True)
    make_profile(root / "execution_profiles.sqlite3", marker=profile_marker)
    make_binding(root / "monitoring_run_bindings.sqlite3")
    make_runtime(
        root / "runtime" / "monitoring_runtime.sqlite3",
        runtime_version,
        control=include_control,
    )
    if launch_version is not None:
        make_launch(root / "launch_registry.sqlite3", launch_version)
    if include_risk:
        make_risk(root / "risk_rules.sqlite3")
    return root


__all__ = [
    "make_binding",
    "make_launch",
    "make_profile",
    "make_project",
    "make_risk",
    "make_runtime",
]
