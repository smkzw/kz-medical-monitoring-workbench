"""Shared Batch C test helpers: build verified domain objects and a synthetic
R1 legacy SQLite fixture for the read-only adapter."""

import json
import sqlite3
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mm_r2.domain import (
    CanonicalFact,
    IdentityAlgorithm,
    ListingSnapshot,
    MappingDefinition,
    MappingResult,
    SourceRevision,
    StudyProject,
    deep_freeze_json,
    content_hash,
    sha256_hex,
)
from mm_r2.identity import make_record_identity


def make_project(pid="p1"):
    return StudyProject(project_id=pid, name=f"Project {pid}")


def make_source(pid="p1", rid="rev-1", content=b"synthetic-source-bytes"):
    return SourceRevision.from_bytes(
        revision_id=rid, project_id=pid, source_type="listing",
        version="v1", source_bytes=content,
    )


def make_snapshot(pid="p1", rid="rev-1", sid="s1",
                  rows=None):
    rows = rows if rows is not None else [{"subject": "S01", "ae": "Nausea"}]
    return ListingSnapshot.from_content(
        snapshot_id=sid, project_id=pid, revision_id=rid,
        snapshot_version=f"cutoff-{sid}", rows=rows,
    )


def make_algo(algo_id="alg-1"):
    return IdentityAlgorithm(algorithm_id=algo_id, name="record-id", version="1")


def make_mapping(pid="p1", rid="rev-1", mid="m1"):
    return MappingDefinition(
        mapping_id=mid, project_id=pid, source_revision_id=rid,
        identity_algorithm_id="alg-1", source_field="AETERM",
        canonical_field="ae_term", fact_type="ae", version="1",
        confidence=1.0, is_critical=True,
    )


def make_mapping_result(pid="p1", snap=None, mapping=None, algo=None,
                        rid="mr1"):
    snap = snap or make_snapshot(pid=pid)
    mapping = mapping or make_mapping(pid=pid)
    algo = algo or make_algo()
    return MappingResult.from_verified(
        result_id=rid, project_id=pid, snapshot=snap,
        mapping=mapping, identity_algorithm=algo,
        record_count=snap.row_count,
    )


def make_record_id(pid="p1", algo=None, subject="S01"):
    algo = algo or make_algo()
    return make_record_identity(pid, algo, {"subject": subject})


def make_fact(pid="p1", project=None, source=None, snap=None,
              mapping=None, result=None, algo=None, record=None,
              payload=None, fact_type="ae"):
    project = project or make_project(pid)
    source = source or make_source(pid=pid)
    snap = snap or make_snapshot(pid=pid)
    algo = algo or make_algo()
    mapping = mapping or make_mapping(pid=pid)
    result = result or make_mapping_result(
        pid=pid, snap=snap, mapping=mapping, algo=algo,
    )
    record = record or make_record_id(pid=pid, algo=algo)
    return CanonicalFact.from_bundle(
        project=project, source=source, snapshot=snap,
        record_identity=record, identity_algorithm=algo,
        mapping_definition=mapping, mapping_result=result,
        fact_type=fact_type,
        payload=tuple(sorted((payload or {"term": "Nausea"}).items())),
    )


# ---------------------------------------------------------------------------
# Synthetic R1 legacy SQLite fixture
# ---------------------------------------------------------------------------

R1_LEGACY_SCHEMA = """
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_synthetic INTEGER NOT NULL,
    config_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE source_revisions (
    revision_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    valid_from TEXT,
    scope_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE listing_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    revision_id TEXT NOT NULL,
    snapshot_version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    structure_json TEXT NOT NULL,
    is_synthetic INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE monitoring_runs (
    run_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    data_cutoff TEXT NOT NULL,
    source_revision_id TEXT NOT NULL,
    execution_basis TEXT NOT NULL,
    analysis_state TEXT NOT NULL,
    evidence_state TEXT NOT NULL,
    review_state TEXT NOT NULL,
    output_state TEXT NOT NULL,
    user_disposition TEXT,
    manifest_revision INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE canonical_facts (
    run_id TEXT NOT NULL,
    fact_hash TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    fact_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, fact_hash)
);
CREATE TABLE domain_objects (
    kind TEXT NOT NULL,
    object_id TEXT NOT NULL,
    run_id TEXT,
    version INTEGER NOT NULL,
    object_json TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (kind, object_id, version)
);
"""


def build_legacy_fixture(db_path, *, project_id="legacy-p1"):
    """Build a synthetic R1 SQLite fixture with one project, source, snapshot,
    fact, and risk identity.  Returns the path."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    conn.executescript(R1_LEGACY_SCHEMA)
    source_hash = sha256_hex(b"legacy-source-content")
    snap_hash = sha256_hex(b"legacy-snapshot-rows")
    fact_hash = sha256_hex(b"legacy-fact-body")
    risk_hash = sha256_hex(b"legacy-risk-identity")
    run_id = "legacy-run-1"
    conn.execute(
        "INSERT INTO projects(project_id, name, is_synthetic, config_json, created_at)"
        " VALUES (?,?,?,?,?)",
        (project_id, "Legacy Project", 1, "{}", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO source_revisions(revision_id, project_id, source_type, version,"
        " content_hash, valid_from, scope_json, created_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        ("legacy-rev-1", project_id, "listing", "v1", source_hash,
         None, "{}", "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO listing_snapshots(snapshot_id, project_id, revision_id,"
        " snapshot_version, content_hash, row_count, structure_json,"
        " is_synthetic, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        ("legacy-snap-1", project_id, "legacy-rev-1", "cutoff-1", snap_hash,
         1, "{}", 1, "2026-01-01T00:00:00"),
    )
    conn.execute(
        "INSERT INTO monitoring_runs(run_id, project_id, mode, data_cutoff,"
        " source_revision_id, execution_basis, analysis_state, evidence_state,"
        " review_state, output_state, manifest_revision, created_at, updated_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id, project_id, "daily", "cutoff-1", "legacy-rev-1", "full",
         "complete", "complete", "not_required", "dashboard_visible", 1,
         "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
    )
    fact_payload = {
        "fact_type": "ae",
        "subject_id": "S01",
        "site_id": None,
        "body": {"term": "Nausea"},
        "source_refs": ["legacy-snap-1"],
    }
    conn.execute(
        "INSERT INTO canonical_facts(run_id, fact_hash, fact_id, node_id,"
        " fact_json, created_at) VALUES (?,?,?,?,?,?)",
        (run_id, fact_hash, "legacy-fact-1", "ae_mh",
         json.dumps(fact_payload), "2026-01-01T00:00:00"),
    )
    risk_payload = {
        "project_id": project_id,
        "scope": "subject",
        "subject_id": "S01",
        "risk_domain": "ae",
        "event_identity": "Nausea",
    }
    conn.execute(
        "INSERT INTO domain_objects(kind, object_id, version, object_json,"
        " content_hash, created_at) VALUES (?,?,?,?,?,?)",
        ("risk_identity", "legacy-risk-1", 1, json.dumps(risk_payload),
         risk_hash, "2026-01-01T00:00:00"),
    )
    conn.commit()
    conn.close()
    return db_path
