"""Explicit schema manifest and read-only project schema inspection.

This module is intentionally stdlib-only.  The manifest is built from the
frozen synthetic/offline DDL below in an in-memory SQLite connection; inspecting
a project always uses a read-only URI and only PRAGMA/SELECT statements.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple
from ..domain.schema_shape import connection_shape, quote_identifier, shape_from_ddl
from urllib.parse import quote
from .launch_schema import LAUNCH_DDL

MANIFEST_VERSION = "mm-r7-slice09b-schema-manifest-v1"
RUNTIME_MEMBER = "runtime"
EXECUTION_CONTROL_MEMBER = "execution_control"
PROFILE_MEMBER = "profile_store"
BINDING_MEMBER = "run_binding"
LAUNCH_MEMBER = "launch_registry"
RISK_MEMBER = "risk_rules"
MEMBER_ORDER = (RUNTIME_MEMBER, EXECUTION_CONTROL_MEMBER, PROFILE_MEMBER,
                BINDING_MEMBER, LAUNCH_MEMBER, RISK_MEMBER)
REQUIRED_PROJECT_MEMBERS = (RUNTIME_MEMBER, PROFILE_MEMBER, BINDING_MEMBER)
OPTIONAL_PROJECT_MEMBERS = (LAUNCH_MEMBER, RISK_MEMBER)

RUNTIME_DB_RELATIVE_PATH = "runtime/monitoring_runtime.sqlite3"
PROFILE_DB_RELATIVE_PATH = "execution_profiles.sqlite3"
BINDING_DB_RELATIVE_PATH = "monitoring_run_bindings.sqlite3"
LAUNCH_DB_RELATIVE_PATH = "launch_registry.sqlite3"
RISK_DB_RELATIVE_PATH = "risk_rules.sqlite3"

RUNTIME_V4 = "4"
RUNTIME_V5 = "5"
RUNTIME_V6 = "6"
LAUNCH_V1 = "mm-r7-slice07c2-launch-registry-v1"
LAUNCH_V2 = "mm-r7-slice07c3-launch-registry-v2"
LAUNCH_V3 = "mm-r7-slice08a-launch-registry-v3"
LAUNCH_V4 = "mm-r7-slice08b-launch-registry-v4"
PROFILE_V1 = "mm-r7-profile-store-v1"
BINDING_V1 = "r7-slice01-run-binding-v1"
RISK_V1 = "mm-r7-risk-rule-v1"


class SchemaClassification(str, Enum):
    CURRENT = "current"
    LEGACY = "legacy"
    UNKNOWN = "unknown"
    CORRUPT = "corrupt"
    # A readable alias for callers that use the contract's malformed wording.
    MALFORMED = "corrupt"


class SchemaInspectionError(RuntimeError):
    """Raised only by ``require_current``; inspection itself is fail-closed."""

    def __init__(self, report: "MemberInspection") -> None:
        self.report = report
        super().__init__(f"{report.member}: {report.reason_code}")


@dataclass(frozen=True)
class MemberInspection:
    member: str
    path: str
    classification: SchemaClassification
    schema_version: Optional[str]
    reason_code: str
    present: bool
    read_only: bool = True
    quick_check: Optional[str] = None
    foreign_key_violations: int = 0
    shape_digest: Optional[str] = None
    marker_value: Optional[str] = None
    optional: bool = False
    details: Tuple[str, ...] = ()

    @property
    def category(self) -> str:
        return self.classification.value

    @property
    def state(self) -> str:
        return self.classification.value

    @property
    def version(self) -> Optional[str]:
        return self.schema_version

    @property
    def is_current(self) -> bool:
        return self.classification is SchemaClassification.CURRENT

    @property
    def is_legacy(self) -> bool:
        return self.classification is SchemaClassification.LEGACY

    @property
    def is_blocked(self) -> bool:
        return self.classification in (SchemaClassification.UNKNOWN, SchemaClassification.CORRUPT)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "member": self.member,
            "path": self.path,
            "classification": self.classification.value,
            "schema_version": self.schema_version,
            "reason_code": self.reason_code,
            "present": self.present,
            "read_only": self.read_only,
            "quick_check": self.quick_check,
            "foreign_key_violations": self.foreign_key_violations,
            "shape_digest": self.shape_digest,
            "marker_value": self.marker_value,
            "optional": self.optional,
            "details": list(self.details),
        }


@dataclass(frozen=True)
class ProjectSchemaInspection:
    workspace: str
    classification: SchemaClassification
    reason_code: str
    members: Mapping[str, MemberInspection]
    read_only: bool = True
    can_view: bool = False
    can_upgrade: bool = False

    @property
    def category(self) -> str:
        return self.classification.value

    @property
    def state(self) -> str:
        return self.classification.value

    @property
    def complete_readable(self) -> bool:
        return self.classification in (SchemaClassification.CURRENT, SchemaClassification.LEGACY)

    @property
    def legacy_readonly(self) -> bool:
        return self.classification is SchemaClassification.LEGACY

    def member(self, name: str) -> MemberInspection:
        try:
            return self.members[name]
        except KeyError as exc:
            raise KeyError(f"unknown schema member: {name}") from exc

    def as_dict(self) -> Dict[str, Any]:
        return {
            "workspace": self.workspace,
            "classification": self.classification.value,
            "reason_code": self.reason_code,
            "read_only": self.read_only,
            "can_view": self.can_view,
            "can_upgrade": self.can_upgrade,
            "members": {
                key: self.members[key].as_dict()
                for key in sorted(self.members, key=lambda value: value.encode("utf-8"))
            },
        }


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def schema_manifest_digest(manifest: Optional[Mapping[str, Any]] = None) -> str:
    """Hash canonical manifest content without its self-referential digest."""
    value = copy.deepcopy(SCHEMA_MANIFEST if manifest is None else dict(manifest))
    if isinstance(value, dict) and "schema_manifest_digest" in value:
        value["schema_manifest_digest"] = ""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


_connection_shape = connection_shape
_quote_identifier = quote_identifier
_shape_from_ddl = shape_from_ddl

# Current launch DDL is centralized in ``launch_schema`` so constructor,
# staging-migration, and manifest expectations cannot drift.
_R1_DDL = "\nPRAGMA foreign_keys=ON;\nCREATE TABLE IF NOT EXISTS meta (\n    key TEXT PRIMARY KEY,\n    value TEXT NOT NULL\n);\nCREATE TABLE IF NOT EXISTS projects (\n    project_id TEXT PRIMARY KEY,\n    name TEXT NOT NULL,\n    is_synthetic INTEGER NOT NULL,\n    config_json TEXT NOT NULL,\n    created_at TEXT NOT NULL\n);\nCREATE TABLE IF NOT EXISTS source_revisions (\n    revision_id TEXT PRIMARY KEY,\n    project_id TEXT NOT NULL REFERENCES projects(project_id),\n    source_type TEXT NOT NULL,\n    version TEXT NOT NULL,\n    content_hash TEXT NOT NULL,\n    valid_from TEXT,\n    scope_json TEXT NOT NULL,\n    created_at TEXT NOT NULL\n);\nCREATE TABLE IF NOT EXISTS listing_snapshots (\n    snapshot_id TEXT PRIMARY KEY,\n    project_id TEXT NOT NULL REFERENCES projects(project_id),\n    revision_id TEXT NOT NULL REFERENCES source_revisions(revision_id),\n    snapshot_version TEXT NOT NULL,\n    content_hash TEXT NOT NULL,\n    row_count INTEGER NOT NULL DEFAULT 0,\n    structure_json TEXT NOT NULL,\n    is_synthetic INTEGER NOT NULL,\n    created_at TEXT NOT NULL\n);\nCREATE INDEX IF NOT EXISTS idx_snapshot_hash ON listing_snapshots(content_hash);\nCREATE TABLE IF NOT EXISTS snapshot_acceptance (\n    snapshot_id TEXT PRIMARY KEY REFERENCES listing_snapshots(snapshot_id),\n    state TEXT NOT NULL,\n    accepted_by TEXT,\n    ambiguity_json TEXT,\n    blocked INTEGER NOT NULL DEFAULT 0,\n    reason TEXT NOT NULL DEFAULT '',\n    updated_at TEXT NOT NULL\n);\nCREATE TABLE IF NOT EXISTS monitoring_runs (\n    run_id TEXT PRIMARY KEY,\n    project_id TEXT NOT NULL REFERENCES projects(project_id),\n    mode TEXT NOT NULL,\n    data_cutoff TEXT NOT NULL,\n    source_revision_id TEXT NOT NULL REFERENCES source_revisions(revision_id),\n    execution_basis TEXT NOT NULL,\n    analysis_state TEXT NOT NULL,\n    evidence_state TEXT NOT NULL,\n    review_state TEXT NOT NULL,\n    output_state TEXT NOT NULL,\n    user_disposition TEXT,\n    manifest_revision INTEGER NOT NULL DEFAULT 0,\n    created_at TEXT NOT NULL,\n    updated_at TEXT NOT NULL\n);\nCREATE TABLE IF NOT EXISTS run_manifests (\n    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),\n    revision INTEGER NOT NULL,\n    manifest_json TEXT NOT NULL,\n    created_at TEXT NOT NULL,\n    PRIMARY KEY (run_id, revision)\n);\nCREATE TABLE IF NOT EXISTS work_unit_runs (\n    run_id TEXT NOT NULL,\n    manifest_revision INTEGER NOT NULL,\n    work_unit_id TEXT NOT NULL,\n    node_id TEXT NOT NULL,\n    status TEXT NOT NULL,\n    idempotency_key TEXT NOT NULL DEFAULT '',\n    begin_hash TEXT NOT NULL DEFAULT '',\n    detail TEXT NOT NULL DEFAULT '',\n    execution_identity_json TEXT NOT NULL DEFAULT '{}',\n    evidence_count INTEGER NOT NULL DEFAULT 0,\n    completion_hash TEXT NOT NULL DEFAULT '',\n    started_at TEXT,\n    finished_at TEXT,\n    updated_at TEXT NOT NULL,\n    PRIMARY KEY (run_id, manifest_revision, work_unit_id),\n    FOREIGN KEY (run_id, manifest_revision)\n        REFERENCES run_manifests(run_id, revision)\n);\nCREATE INDEX IF NOT EXISTS idx_work_unit_runs_revision\n    ON work_unit_runs(run_id, manifest_revision, status);\nCREATE TABLE IF NOT EXISTS manifest_node_progress (\n    run_id TEXT NOT NULL,\n    manifest_revision INTEGER NOT NULL,\n    node_id TEXT NOT NULL,\n    status TEXT NOT NULL,\n    updated_at TEXT NOT NULL,\n    PRIMARY KEY (run_id, manifest_revision, node_id),\n    FOREIGN KEY (run_id, manifest_revision)\n        REFERENCES run_manifests(run_id, revision)\n);\nCREATE INDEX IF NOT EXISTS idx_manifest_node_progress_revision\n    ON manifest_node_progress(run_id, manifest_revision, status);\nCREATE TABLE IF NOT EXISTS node_runs (\n    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),\n    node_id TEXT NOT NULL,\n    node_type TEXT NOT NULL,\n    manifest_revision INTEGER NOT NULL DEFAULT 0,\n    status TEXT NOT NULL,\n    idempotency_key TEXT NOT NULL,\n    attempts INTEGER NOT NULL DEFAULT 0,\n    artifact_id TEXT,\n    output_json TEXT NOT NULL DEFAULT '{}',\n    error TEXT,\n    reason TEXT,\n    started_at TEXT,\n    finished_at TEXT,\n    PRIMARY KEY (run_id, node_id)\n);\nCREATE TABLE IF NOT EXISTS node_attempts (\n    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),\n    node_id TEXT NOT NULL,\n    attempt_seq INTEGER NOT NULL,\n    idempotency_key TEXT NOT NULL,\n    logical_key TEXT NOT NULL,\n    manifest_revision INTEGER NOT NULL DEFAULT 0,\n    status TEXT NOT NULL,\n    payload_hash TEXT,\n    created_at TEXT NOT NULL,\n    PRIMARY KEY (run_id, node_id, attempt_seq),\n    UNIQUE (idempotency_key)\n);\nCREATE INDEX IF NOT EXISTS idx_attempts_logical ON node_attempts(logical_key);\nCREATE TABLE IF NOT EXISTS capability_attempt_journal (\n    attempt_id TEXT PRIMARY KEY,\n    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),\n    node_id TEXT NOT NULL,\n    request_hash TEXT NOT NULL,\n    request_json TEXT NOT NULL,\n    profile_fingerprint TEXT NOT NULL,\n    manifest_revision INTEGER NOT NULL,\n    input_hash TEXT NOT NULL,\n    status TEXT NOT NULL,\n    terminal INTEGER NOT NULL DEFAULT 0,\n    owner_token TEXT,\n    lease_expires_at REAL,\n    result_json TEXT,\n    result_hash TEXT,\n    continued_from TEXT NOT NULL DEFAULT '',\n    created_at TEXT NOT NULL,\n    updated_at TEXT NOT NULL,\n    terminal_at TEXT\n);\nCREATE INDEX IF NOT EXISTS idx_capability_attempt_run\n    ON capability_attempt_journal(run_id, node_id, created_at);\nCREATE INDEX IF NOT EXISTS idx_capability_attempt_lease\n    ON capability_attempt_journal(status, lease_expires_at);\nCREATE TABLE IF NOT EXISTS work_unit_capability_attempts (\n    run_id TEXT NOT NULL,\n    manifest_revision INTEGER NOT NULL,\n    work_unit_id TEXT NOT NULL,\n    attempt_ordinal INTEGER NOT NULL CHECK (attempt_ordinal >= 1),\n    attempt_id TEXT NOT NULL UNIQUE REFERENCES capability_attempt_journal(attempt_id),\n    detail TEXT NOT NULL,\n    execution_identity_json TEXT NOT NULL,\n    identity_hash TEXT NOT NULL,\n    bound_at TEXT NOT NULL,\n    PRIMARY KEY (run_id, manifest_revision, work_unit_id, attempt_ordinal),\n    UNIQUE (run_id, manifest_revision, work_unit_id, attempt_id),\n    FOREIGN KEY (run_id, manifest_revision, work_unit_id)\n        REFERENCES work_unit_runs(run_id, manifest_revision, work_unit_id)\n);\nCREATE INDEX IF NOT EXISTS idx_work_unit_capability_attempts_unit\n    ON work_unit_capability_attempts(run_id, manifest_revision, work_unit_id);\nCREATE TABLE IF NOT EXISTS artifacts (\n    artifact_id TEXT PRIMARY KEY,\n    content_hash TEXT NOT NULL UNIQUE,\n    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),\n    node_id TEXT NOT NULL,\n    artifact_type TEXT NOT NULL,\n    completeness TEXT NOT NULL,\n    envelope_json TEXT NOT NULL,\n    created_at TEXT NOT NULL\n);\nCREATE TABLE IF NOT EXISTS audit_events (\n    seq INTEGER PRIMARY KEY AUTOINCREMENT,\n    run_id TEXT REFERENCES monitoring_runs(run_id),\n    event_type TEXT NOT NULL,\n    payload_json TEXT NOT NULL,\n    payload_hash TEXT NOT NULL,\n    prev_hash TEXT NOT NULL,\n    chain_hash TEXT NOT NULL,\n    created_at TEXT NOT NULL\n);\nCREATE TABLE IF NOT EXISTS audit_chain_head (\n    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),\n    last_seq INTEGER NOT NULL,\n    last_chain_hash TEXT NOT NULL\n);\nCREATE TABLE IF NOT EXISTS checkpoints (\n    checkpoint_id TEXT PRIMARY KEY,\n    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),\n    node_id TEXT NOT NULL,\n    state_json TEXT NOT NULL,\n    content_hash TEXT NOT NULL,\n    created_at TEXT NOT NULL\n);\nCREATE TABLE IF NOT EXISTS domain_objects (\n    kind TEXT NOT NULL,\n    object_id TEXT NOT NULL,\n    run_id TEXT REFERENCES monitoring_runs(run_id),\n    version INTEGER NOT NULL,\n    object_json TEXT NOT NULL,\n    content_hash TEXT NOT NULL,\n    created_at TEXT NOT NULL,\n    PRIMARY KEY (kind, object_id, version)\n);\nCREATE TABLE IF NOT EXISTS canonical_facts (\n    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),\n    fact_hash TEXT NOT NULL,\n    fact_id TEXT NOT NULL,\n    node_id TEXT NOT NULL,\n    fact_json TEXT NOT NULL,\n    created_at TEXT NOT NULL,\n    PRIMARY KEY (run_id, fact_hash)\n);\nCREATE TABLE IF NOT EXISTS idempotency_ledger (\n    idempotency_key TEXT PRIMARY KEY,\n    scope TEXT NOT NULL,\n    request_hash TEXT NOT NULL,\n    result_json TEXT NOT NULL,\n    created_at TEXT NOT NULL\n);\nCREATE INDEX IF NOT EXISTS idx_audit_run ON audit_events(run_id);\nCREATE INDEX IF NOT EXISTS idx_node_runs_run ON node_runs(run_id);\nCREATE INDEX IF NOT EXISTS idx_attempts_run ON node_attempts(run_id);\nCREATE INDEX IF NOT EXISTS idx_domain_run ON domain_objects(run_id);\n"
_CONTROL_DDL = "\nCREATE TABLE IF NOT EXISTS r7_execution_control (\n    run_id TEXT PRIMARY KEY NOT NULL REFERENCES monitoring_runs(run_id),\n    manifest_revision INTEGER NOT NULL,\n    generation INTEGER NOT NULL,\n    state TEXT NOT NULL,\n    owner_token TEXT NOT NULL DEFAULT '',\n    lease_expires_at REAL,\n    cancel_requested INTEGER NOT NULL DEFAULT 0,\n    created_at TEXT NOT NULL,\n    updated_at TEXT NOT NULL\n);\n"
_PROFILE_DDL = '\nCREATE TABLE IF NOT EXISTS profile_store_meta (\n    key TEXT PRIMARY KEY NOT NULL,\n    value TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS profile_layer_versions (\n    layer_kind TEXT NOT NULL,\n    scope_key TEXT NOT NULL,\n    revision INTEGER NOT NULL,\n    record_id TEXT NOT NULL UNIQUE,\n    payload_json TEXT NOT NULL,\n    content_digest TEXT NOT NULL,\n    PRIMARY KEY (layer_kind, scope_key, revision)\n);\n\nCREATE INDEX IF NOT EXISTS idx_profile_layer_latest\n    ON profile_layer_versions (layer_kind, scope_key, revision);\n'
_BINDING_DDL = '\nCREATE TABLE IF NOT EXISTS monitoring_run_bindings (\n    run_id TEXT PRIMARY KEY NOT NULL,\n    binding_digest TEXT NOT NULL,\n    project_id TEXT NOT NULL,\n    mode TEXT NOT NULL,\n    execution_basis TEXT NOT NULL,\n    data_cutoff TEXT NOT NULL,\n    source_revision_id TEXT NOT NULL,\n    prior_accepted_snapshot_ref TEXT,\n    execution_profile_id TEXT NOT NULL,\n    execution_profile_digest TEXT NOT NULL,\n    profile_id TEXT NOT NULL,\n    user_config_name TEXT NOT NULL,\n    effective_selector TEXT NOT NULL,\n    adapter_id TEXT NOT NULL,\n    adapter_version TEXT NOT NULL,\n    fallback_profile_ids_json TEXT NOT NULL,\n    schema_version TEXT NOT NULL,\n    frozen_profile_json TEXT NOT NULL,\n    record_json TEXT NOT NULL\n);\n'
_LAUNCH_DDL = LAUNCH_DDL
_RISK_DDL = 'CREATE TABLE IF NOT EXISTS r7_risk_rule_revisions (\n    project_id TEXT NOT NULL,\n    revision INTEGER NOT NULL,\n    revision_token TEXT NOT NULL,\n    candidate_id TEXT NOT NULL,\n    subject TEXT NOT NULL,\n    condition TEXT NOT NULL,\n    applicable_scope TEXT NOT NULL,\n    starting_run TEXT NOT NULL,\n    summary TEXT NOT NULL,\n    created_at TEXT NOT NULL,\n    rule_digest TEXT NOT NULL,\n    selectable INTEGER NOT NULL,\n    idempotency_key TEXT,\n    idempotency_fingerprint TEXT,\n    PRIMARY KEY(project_id, revision),\n    UNIQUE(project_id, revision_token),\n    UNIQUE(project_id, idempotency_key)\n)'

_RUNTIME_VARIANT_TRANSFORMS = {
    RUNTIME_V4: (
        "DROP TABLE work_unit_capability_attempts",
        "ALTER TABLE node_runs DROP COLUMN manifest_revision",
        "ALTER TABLE node_attempts DROP COLUMN manifest_revision",
    ),
    RUNTIME_V5: ("DROP TABLE work_unit_capability_attempts",),
    RUNTIME_V6: (),
}
_LAUNCH_VARIANT_TRANSFORMS = {
    LAUNCH_V1: (
        "DROP TABLE r7_continuity_items",
        "DROP TABLE r7_continuity_plans",
        "DROP TABLE r7_result_publications",
    ),
    LAUNCH_V2: (
        "DROP TABLE r7_continuity_items",
        "DROP TABLE r7_continuity_plans",
    ),
    LAUNCH_V3: (
        "ALTER TABLE r7_result_publications DROP COLUMN r6_output_set_digest",
        "ALTER TABLE r7_result_publications DROP COLUMN artifact_member_ids_json",
        "ALTER TABLE r7_result_publications DROP COLUMN artifact_member_set_digest",
        "ALTER TABLE r7_continuity_plans DROP COLUMN r6_output_set_digest",
    ),
    LAUNCH_V4: (),
}


def _variant(member: str, version: str, classification: str, ddl: str,
             transforms: Sequence[str] = ()) -> Dict[str, Any]:
    shape = _shape_from_ddl(ddl, transforms)
    return {
        "member": member,
        "schema_version": version,
        "classification": classification,
        "upgrade_supported": classification == SchemaClassification.LEGACY.value,
        "shape": shape,
        "shape_digest": hashlib.sha256(canonical_json_bytes(shape)).hexdigest(),
    }


def _build_manifest() -> Dict[str, Any]:
    runtime_variants = {
        version: _variant(RUNTIME_MEMBER, version,
                          "current" if version == RUNTIME_V6 else "legacy",
                          _R1_DDL, transforms)
        for version, transforms in _RUNTIME_VARIANT_TRANSFORMS.items()
    }
    launch_variants = {
        version: _variant(LAUNCH_MEMBER, version,
                          "current" if version == LAUNCH_V4 else "legacy",
                          _LAUNCH_DDL, transforms)
        for version, transforms in _LAUNCH_VARIANT_TRANSFORMS.items()
    }
    runtime_control = _shape_from_ddl(_CONTROL_DDL)
    profile_shape = _shape_from_ddl(_PROFILE_DDL)
    binding_shape = _shape_from_ddl(_BINDING_DDL)
    risk_shape = _shape_from_ddl(_RISK_DDL)
    return {
        "manifest_version": MANIFEST_VERSION,
        "members": {
            RUNTIME_MEMBER: {
                "relative_path": RUNTIME_DB_RELATIVE_PATH,
                "required": True,
                "marker": {"kind": "table_value", "table": "meta", "key": "schema_version",
                            "value_column": "value", "required": True},
                "user_version": [0],
                "versions": runtime_variants,
                "optional_tables": ["r7_execution_control"],
            },
            EXECUTION_CONTROL_MEMBER: {
                "relative_path": RUNTIME_DB_RELATIVE_PATH,
                "required": False,
                "default_if_absent": True,
                "marker": {"kind": "none", "reason": "same_runtime_file"},
                "user_version": [0],
                "versions": {"current": {
                    "member": EXECUTION_CONTROL_MEMBER,
                    "schema_version": None,
                    "classification": "current",
                    "upgrade_supported": False,
                    "shape": runtime_control,
                    "shape_digest": hashlib.sha256(canonical_json_bytes(runtime_control)).hexdigest(),
                }},
            },
            PROFILE_MEMBER: {
                "relative_path": PROFILE_DB_RELATIVE_PATH,
                "required": True,
                "marker": {"kind": "table_value", "table": "profile_store_meta", "key": "schema_version",
                            "value_column": "value", "required": True},
                "user_version": [0],
                "versions": {PROFILE_V1: _variant(PROFILE_MEMBER, PROFILE_V1, "current", _PROFILE_DDL)},
            },
            BINDING_MEMBER: {
                "relative_path": BINDING_DB_RELATIVE_PATH,
                "required": True,
                "marker": {"kind": "row_values", "table": "monitoring_run_bindings",
                            "column": "schema_version", "empty_is_current": True},
                "user_version": [0],
                "versions": {BINDING_V1: _variant(BINDING_MEMBER, BINDING_V1, "current", _BINDING_DDL)},
            },
            LAUNCH_MEMBER: {
                "relative_path": LAUNCH_DB_RELATIVE_PATH,
                "required": False,
                "default_if_absent": True,
                "marker": {"kind": "table_value", "table": "r7_launch_registry_meta",
                            "key": "schema_version", "value_column": "value", "required": True},
                "user_version": [0],
                "versions": launch_variants,
            },
            RISK_MEMBER: {
                "relative_path": RISK_DB_RELATIVE_PATH,
                "required": False,
                "default_if_absent": True,
                "marker": {"kind": "none", "reason": "structural-v1"},
                "user_version": [0],
                "versions": {RISK_V1: {
                    "member": RISK_MEMBER,
                    "schema_version": RISK_V1,
                    "classification": "current",
                    "upgrade_supported": False,
                    "shape": risk_shape,
                    "shape_digest": hashlib.sha256(canonical_json_bytes(risk_shape)).hexdigest(),
                }},
            },
        },
        "schema_manifest_digest": "",
    }


SCHEMA_MANIFEST = _build_manifest()
SCHEMA_MANIFEST["schema_manifest_digest"] = schema_manifest_digest(SCHEMA_MANIFEST)
SCHEMA_MANIFEST_DIGEST = SCHEMA_MANIFEST["schema_manifest_digest"]
SCHEMA_MANIFEST_JSON = canonical_json_bytes(SCHEMA_MANIFEST).decode("utf-8")


def get_schema_manifest() -> Dict[str, Any]:
    """Return an isolated copy of the explicit manifest."""
    return copy.deepcopy(SCHEMA_MANIFEST)


def _member_definition(member: str) -> Mapping[str, Any]:
    try:
        return SCHEMA_MANIFEST["members"][member]
    except KeyError as exc:
        raise ValueError(f"unknown schema member: {member}") from exc


def _member_from_path(path: Path) -> str:
    name = path.name
    if name == "monitoring_runtime.sqlite3":
        return RUNTIME_MEMBER
    if name == "execution_profiles.sqlite3":
        return PROFILE_MEMBER
    if name == "monitoring_run_bindings.sqlite3":
        return BINDING_MEMBER
    if name == "launch_registry.sqlite3":
        return LAUNCH_MEMBER
    if name == "risk_rules.sqlite3":
        return RISK_MEMBER
    raise ValueError(f"cannot infer schema member from path: {path}")


def _failure(member: str, path: Path, classification: SchemaClassification,
             reason_code: str, *, present: bool = True, optional: bool = False,
             schema_version: Optional[str] = None, marker_value: Optional[str] = None,
             quick_check: Optional[str] = None, foreign_key_violations: int = 0,
             shape_digest: Optional[str] = None,
             details: Iterable[str] = ()) -> MemberInspection:
    return MemberInspection(
        member=member, path=str(path), classification=classification,
        schema_version=schema_version, reason_code=reason_code, present=present,
        quick_check=quick_check, foreign_key_violations=foreign_key_violations,
        shape_digest=shape_digest, marker_value=marker_value, optional=optional,
        details=tuple(str(item) for item in details),
    )


def _uri_for_readonly(path: Path) -> str:
    # quote keeps spaces, non-ASCII project paths, '?' and '#' data-safe while
    # retaining '/' separators required by SQLite's URI parser.
    return "file:" + quote(str(path), safe="/") + "?mode=ro"


def _open_readonly(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(_uri_for_readonly(path), uri=True,
                                  isolation_level=None, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    value = connection.execute("PRAGMA query_only").fetchone()[0]
    if int(value) != 1:
        connection.close()
        raise sqlite3.DatabaseError("query_only was not enabled")
    return connection


def _quick_check(connection: sqlite3.Connection) -> Tuple[str, int]:
    quick_rows = connection.execute("PRAGMA quick_check").fetchall()
    if quick_rows and all(str(row[0]).lower() == "ok" for row in quick_rows):
        quick = "ok"
    else:
        quick = ";".join(str(row[0]) for row in quick_rows) or "empty"
    foreign_rows = connection.execute("PRAGMA foreign_key_check").fetchall()
    return quick, len(foreign_rows)


def _read_marker(connection: sqlite3.Connection, marker: Mapping[str, Any]) -> Optional[str]:
    kind = marker.get("kind")
    if kind == "table_value":
        table = _quote_identifier(str(marker["table"]))
        key_column = _quote_identifier("key")
        value_column = _quote_identifier(str(marker.get("value_column", "value")))
        row = connection.execute(
            f"SELECT {value_column} FROM {table} WHERE {key_column} = ?",
            (str(marker["key"]),),
        ).fetchone()
        return None if row is None else str(row[0])
    if kind == "row_values":
        table = _quote_identifier(str(marker["table"]))
        column = _quote_identifier(str(marker["column"]))
        rows = connection.execute(f"SELECT {column} FROM {table}").fetchall()
        if not rows:
            return "__EMPTY__"
        if any(row[0] is None for row in rows):
            return "__NULL__"
        values = {str(row[0]) for row in rows}
        if len(values) != 1:
            return "__MIXED__"
        return next(iter(values))
    return None


def _classify_open_connection(member: str, path: Path,
                              connection: sqlite3.Connection) -> MemberInspection:
    definition = _member_definition(member)
    try:
        quick, foreign_count = _quick_check(connection)
        actual_shape = _connection_shape(connection)
    except (sqlite3.DatabaseError, sqlite3.Error) as exc:
        return _failure(member, path, SchemaClassification.CORRUPT, "sqlite_malformed",
                        details=(type(exc).__name__, str(exc)))
    if quick != "ok":
        return _failure(member, path, SchemaClassification.CORRUPT, "quick_check_failed",
                        quick_check=quick, foreign_key_violations=foreign_count)
    if foreign_count:
        return _failure(member, path, SchemaClassification.CORRUPT,
                        "foreign_key_check_failed", quick_check=quick,
                        foreign_key_violations=foreign_count)
    allowed_user_versions = {int(value) for value in definition.get("user_version", (0,))}
    if int(actual_shape["user_version"]) not in allowed_user_versions:
        return _failure(member, path, SchemaClassification.UNKNOWN, "user_version_mismatch",
                        quick_check=quick, shape_digest=hashlib.sha256(canonical_json_bytes(actual_shape)).hexdigest())
    marker = definition.get("marker", {"kind": "none"})
    marker_value = _read_marker(connection, marker)
    if member == BINDING_MEMBER and marker_value == "__EMPTY__":
        marker_value = BINDING_V1
    if marker.get("kind") == "table_value" and marker_value is None:
        return _failure(member, path, SchemaClassification.UNKNOWN, "marker_missing",
                        quick_check=quick, foreign_key_violations=foreign_count)
    if marker.get("kind") == "row_values" and marker_value in {"__MIXED__", "__NULL__"}:
        reason = (
            "mixed_row_schema_version"
            if marker_value == "__MIXED__"
            else "null_row_schema_version"
        )
        return _failure(member, path, SchemaClassification.CORRUPT,
                        reason, quick_check=quick,
                        foreign_key_violations=foreign_count, marker_value=marker_value)
    variants = definition.get("versions", {})
    if marker.get("kind") == "none":
        matching = [
            candidate for candidate in variants.values()
            if candidate["shape"] == actual_shape
        ]
        variant = matching[0] if len(matching) == 1 else None
    else:
        variant = variants.get(marker_value)
    if variant is None:
        if marker.get("kind") == "none":
            reason = "shape_mismatch"
            classification = SchemaClassification.CORRUPT
        else:
            reason = (
                "unsupported_legacy_marker"
                if marker_value == "3"
                else "unsupported_schema_version"
            )
            classification = SchemaClassification.UNKNOWN
        return _failure(member, path, classification, reason,
                        quick_check=quick, foreign_key_violations=foreign_count,
                        marker_value=marker_value, schema_version=marker_value)
    expected_shape = variant["shape"]
    actual_for_compare = actual_shape
    if member == RUNTIME_MEMBER:
        # The execution-control table is created lazily by the R7 runner and
        # is a true default when absent; it is validated separately below.
        actual_for_compare = copy.deepcopy(actual_shape)
        actual_for_compare["tables"].pop("r7_execution_control", None)
    if actual_for_compare != expected_shape:
        actual_digest = hashlib.sha256(canonical_json_bytes(actual_for_compare)).hexdigest()
        return _failure(member, path, SchemaClassification.CORRUPT, "shape_mismatch",
                        quick_check=quick, foreign_key_violations=foreign_count,
                        marker_value=marker_value, schema_version=marker_value,
                        shape_digest=actual_digest)
    return MemberInspection(
        member=member, path=str(path),
        classification=SchemaClassification(variant["classification"]),
        schema_version=variant.get("schema_version"),
        reason_code="current_shape" if variant["classification"] == "current" else "supported_legacy_shape",
        present=True, quick_check=quick, foreign_key_violations=foreign_count,
        shape_digest=variant["shape_digest"], marker_value=marker_value,
        optional=not bool(definition.get("required", False)),
    )


def _inspect_runtime(path: Path) -> Tuple[MemberInspection, MemberInspection]:
    if not path.is_file():
        missing = _failure(RUNTIME_MEMBER, path, SchemaClassification.UNKNOWN,
                           "member_missing", present=False)
        control = _failure(EXECUTION_CONTROL_MEMBER, path, SchemaClassification.CURRENT,
                           "default_absent", present=False, optional=True)
        return missing, control
    connection: Optional[sqlite3.Connection] = None
    try:
        connection = _open_readonly(path)
        runtime = _classify_open_connection(RUNTIME_MEMBER, path, connection)
        try:
            quick, foreign_count = _quick_check(connection)
            actual_shape = _connection_shape(connection)
        except sqlite3.Error:
            quick, foreign_count, actual_shape = None, 0, {"tables": {}}
        control_table = actual_shape.get("tables", {}).get("r7_execution_control")
        control_definition = _member_definition(EXECUTION_CONTROL_MEMBER)
        control_variant = control_definition["versions"]["current"]
        if control_table is None:
            control = _failure(EXECUTION_CONTROL_MEMBER, path, SchemaClassification.CURRENT,
                               "default_absent", present=False, optional=True,
                               quick_check=quick, foreign_key_violations=foreign_count)
        elif runtime.classification is SchemaClassification.CORRUPT and runtime.reason_code == "sqlite_malformed":
            control = _failure(EXECUTION_CONTROL_MEMBER, path, SchemaClassification.CORRUPT,
                               "sqlite_malformed", quick_check=quick)
        else:
            actual_control = {"user_version": actual_shape["user_version"],
                               "tables": {"r7_execution_control": control_table}}
            expected_control = control_variant["shape"]
            # expected control shape has a table named r7_execution_control.
            if actual_control != expected_control:
                control = _failure(EXECUTION_CONTROL_MEMBER, path, SchemaClassification.CORRUPT,
                                   "shape_mismatch", present=True, optional=True,
                                   quick_check=quick,
                                   shape_digest=hashlib.sha256(canonical_json_bytes(actual_control)).hexdigest())
            else:
                control = MemberInspection(
                    member=EXECUTION_CONTROL_MEMBER, path=str(path),
                    classification=SchemaClassification.CURRENT,
                    schema_version=None, reason_code="current_shape", present=True,
                    quick_check=quick, foreign_key_violations=foreign_count,
                    shape_digest=control_variant["shape_digest"], optional=True,
                )
        return runtime, control
    except (OSError, sqlite3.Error) as exc:
        corrupt = _failure(RUNTIME_MEMBER, path, SchemaClassification.CORRUPT,
                           "sqlite_malformed", details=(type(exc).__name__, str(exc)))
        control = _failure(EXECUTION_CONTROL_MEMBER, path, SchemaClassification.CORRUPT,
                           "sqlite_malformed", present=True, optional=True)
        return corrupt, control
    finally:
        if connection is not None:
            connection.close()


def inspect_member(path: Any, member: Optional[str] = None) -> MemberInspection:
    target = Path(path)
    selected = member or _member_from_path(target)
    if selected == EXECUTION_CONTROL_MEMBER:
        runtime, control = _inspect_runtime(target)
        return control
    definition = _member_definition(selected)
    optional = not bool(definition.get("required", False))
    if not target.is_file():
        return _failure(selected, target, SchemaClassification.UNKNOWN, "member_missing",
                        present=False, optional=optional)
    connection: Optional[sqlite3.Connection] = None
    try:
        connection = _open_readonly(target)
        return _classify_open_connection(selected, target, connection)
    except (OSError, sqlite3.Error) as exc:
        return _failure(selected, target, SchemaClassification.CORRUPT,
                        "sqlite_malformed", details=(type(exc).__name__, str(exc)),
                        optional=optional)
    finally:
        if connection is not None:
            connection.close()


def require_current(path: Any, member: Optional[str] = None) -> MemberInspection:
    report = inspect_member(path, member)
    if report.classification is not SchemaClassification.CURRENT:
        raise SchemaInspectionError(report)
    return report


class ProjectSchemaInspector:
    """Synchronous, read-only schema preflight for a synthetic project."""

    def __init__(self, workspace: Any) -> None:
        self.workspace = Path(workspace)

    def inspect(self) -> ProjectSchemaInspection:
        root = self.workspace
        member_reports: Dict[str, MemberInspection] = {}
        runtime, control = _inspect_runtime(root / RUNTIME_DB_RELATIVE_PATH)
        member_reports[RUNTIME_MEMBER] = runtime
        member_reports[EXECUTION_CONTROL_MEMBER] = control
        for member in (PROFILE_MEMBER, BINDING_MEMBER, LAUNCH_MEMBER, RISK_MEMBER):
            definition = _member_definition(member)
            report = inspect_member(root / definition["relative_path"], member)
            if not report.present and definition.get("default_if_absent", False):
                report = _failure(
                    member,
                    root / definition["relative_path"],
                    SchemaClassification.CURRENT,
                    "default_absent",
                    present=False,
                    optional=True,
                )
            member_reports[member] = report
        required_missing = [
            member for member in REQUIRED_PROJECT_MEMBERS
            if not member_reports[member].present
        ]
        corrupt = [
            member for member, report in member_reports.items()
            if report.classification is SchemaClassification.CORRUPT
        ]
        unknown = [
            member for member, report in member_reports.items()
            if report.present and report.classification is SchemaClassification.UNKNOWN
        ]
        legacy = [
            member for member, report in member_reports.items()
            if report.present and report.classification is SchemaClassification.LEGACY
        ]
        if required_missing:
            classification = SchemaClassification.CORRUPT
            reason = "required_member_missing"
        elif corrupt:
            classification = SchemaClassification.CORRUPT
            reason = "member_corrupt"
        elif unknown:
            classification = SchemaClassification.UNKNOWN
            reason = "member_unknown"
        elif legacy:
            classification = SchemaClassification.LEGACY
            reason = "supported_legacy_project"
        else:
            classification = SchemaClassification.CURRENT
            reason = "current_project"
        return ProjectSchemaInspection(
            workspace=str(root), classification=classification, reason_code=reason,
            members={key: member_reports[key] for key in MEMBER_ORDER},
            can_view=classification in (SchemaClassification.CURRENT, SchemaClassification.LEGACY),
            can_upgrade=classification is SchemaClassification.LEGACY,
        )

    @classmethod
    def inspect_project(cls, workspace: Any) -> ProjectSchemaInspection:
        return cls(workspace).inspect()

    @staticmethod
    def inspect_member(path: Any, member: Optional[str] = None) -> MemberInspection:
        return inspect_member(path, member)


# Explicit function names make the read-only seam easy to use without
# constructing a product router or mutable store.
def inspect_project_schema(workspace: Any) -> ProjectSchemaInspection:
    return ProjectSchemaInspector(workspace).inspect()


__all__ = [
    "BINDING_MEMBER", "BINDING_V1", "EXECUTION_CONTROL_MEMBER",
    "LAUNCH_MEMBER", "LAUNCH_V1", "LAUNCH_V2", "LAUNCH_V3", "LAUNCH_V4",
    "MANIFEST_VERSION", "MEMBER_ORDER", "PROFILE_MEMBER", "PROFILE_V1",
    "ProjectSchemaInspection", "ProjectSchemaInspector", "REQUIRED_PROJECT_MEMBERS",
    "RISK_MEMBER", "RISK_V1", "RUNTIME_MEMBER", "RUNTIME_V4", "RUNTIME_V5", "RUNTIME_V6",
    "SCHEMA_MANIFEST", "SCHEMA_MANIFEST_DIGEST", "SCHEMA_MANIFEST_JSON",
    "SchemaClassification", "SchemaInspectionError", "MemberInspection",
    "canonical_json_bytes", "get_schema_manifest", "inspect_member", "inspect_project_schema",
    "require_current", "schema_manifest_digest",
]
