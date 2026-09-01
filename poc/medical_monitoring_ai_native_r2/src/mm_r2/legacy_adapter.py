"""R1 read-only legacy adapter (Batch C; Design v1.1 section 15 / migration).

Opens a **synthetic** R1 SQLite fixture in **read-only** mode and exposes
proven source/fact/risk identity mappings into R2 projections.  The adapter:

* opens the legacy DB with ``mode=ro`` (SQLite URI read-only) -- no writes
  are possible through this connection;
* exposes **no write method** whatsoever;
* performs only proven identity mappings (source revision, listing snapshot,
  canonical fact, risk identity key -> R2 content hash);
* emits explicit matched / unmatched / ambiguous dual-read differences so a
  migration consumer knows exactly what carried over, what did not, and what
  was ambiguous.

The adapter never modifies any R1 file.  It reads only the R1 schema tables
(``projects``, ``source_revisions``, ``listing_snapshots``,
``canonical_facts``, ``domain_objects``) that the R1 store defines.

Dual-read differences (:class:`DualReadDiff`) let a migration compare the
R2 current state against the R1 legacy state for the same project: matched
entities (same identity, same content hash), unmatched (present in one side
only), and ambiguous (identity matched but content differs).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .domain import (
    DomainValidationError,
    MmR2Error,
    content_hash,
    sha256_hex,
)

__all__ = [
    "LegacyAdapterError",
    "LegacySourceRow",
    "LegacySnapshotRow",
    "LegacyFactRow",
    "LegacyRiskRow",
    "LegacyProjection",
    "DualReadDiff",
    "DiffEntry",
    "DiffStatus",
    "R1LegacyAdapter",
]


class LegacyAdapterError(MmR2Error):
    """Legacy-adapter violation (write attempt, unreadable fixture, etc)."""


# ---------------------------------------------------------------------------
# Projections (read-only views of R1 data)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LegacySourceRow:
    revision_id: str
    project_id: str
    source_type: str
    version: str
    content_hash: str
    valid_from: Optional[str]
    scope: Dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class LegacySnapshotRow:
    snapshot_id: str
    project_id: str
    revision_id: str
    snapshot_version: str
    content_hash: str
    row_count: int
    structure: Dict[str, Any]
    is_synthetic: bool
    created_at: str


@dataclass(frozen=True)
class LegacyFactRow:
    run_id: str
    fact_hash: str
    fact_id: str
    node_id: str
    fact_type: str
    subject_id: Optional[str]
    site_id: Optional[str]
    body: Dict[str, Any]
    source_refs: List[str]


@dataclass(frozen=True)
class LegacyRiskRow:
    kind: str
    object_id: str
    version: int
    content_hash: str
    payload: Dict[str, Any]


@dataclass(frozen=True)
class LegacyProjection:
    """All proven R1 identity-mapped projections for one project."""

    project_id: str
    sources: Tuple[LegacySourceRow, ...]
    snapshots: Tuple[LegacySnapshotRow, ...]
    facts: Tuple[LegacyFactRow, ...]
    risks: Tuple[LegacyRiskRow, ...]


# ---------------------------------------------------------------------------
# Dual-read diff
# ---------------------------------------------------------------------------

class DiffStatus:
    MATCHED = "matched"
    UNMATCHED_LEGACY_ONLY = "unmatched_legacy_only"
    UNMATCHED_R2_ONLY = "unmatched_r2_only"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class DiffEntry:
    """One dual-read difference entry."""

    entity_kind: str          # source | snapshot | fact | risk
    identity_key: str         # proven identity key (revision_id / snapshot_id / fact_hash / risk key)
    status: str               # DiffStatus.*
    legacy_hash: str = ""
    r2_hash: str = ""
    detail: str = ""


@dataclass(frozen=True)
class DualReadDiff:
    """The full dual-read difference between R1 legacy and R2 current."""

    project_id: str
    entries: Tuple[DiffEntry, ...]

    @property
    def matched(self) -> Tuple[DiffEntry, ...]:
        return tuple(e for e in self.entries if e.status == DiffStatus.MATCHED)

    @property
    def unmatched(self) -> Tuple[DiffEntry, ...]:
        return tuple(
            e for e in self.entries
            if e.status in (DiffStatus.UNMATCHED_LEGACY_ONLY, DiffStatus.UNMATCHED_R2_ONLY)
        )

    @property
    def ambiguous(self) -> Tuple[DiffEntry, ...]:
        return tuple(e for e in self.entries if e.status == DiffStatus.AMBIGUOUS)

    @property
    def is_clean(self) -> bool:
        return len(self.unmatched) == 0 and len(self.ambiguous) == 0


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class R1LegacyAdapter:
    """Read-only adapter over a synthetic R1 SQLite fixture.

    The connection is opened with ``mode=ro`` (immutable read-only URI).
    No write method exists on this class.  Attempting to execute a write
    statement through the underlying connection raises an SQLite
    ``OperationalError`` (read-only database).
    """

    # Proven identity mappings (R1 -> R2 content-hash key):
    #   source:   (project_id, revision_id)          -> R1 content_hash
    #   snapshot: (project_id, snapshot_id)          -> R1 content_hash
    #   fact:     (run_id, fact_hash)                -> R1 fact_hash (canonical)
    #   risk:     (project_id, risk_identity_key)    -> R1 identity stable_key

    def __init__(self, legacy_db_path: Path) -> None:
        self.legacy_db_path = Path(legacy_db_path)
        if not self.legacy_db_path.exists():
            raise LegacyAdapterError(
                f"legacy fixture not found: {self.legacy_db_path}"
            )
        # Open READ-ONLY via SQLite URI.  mode=ro forbids writes at the
        # sqlite3 level; the adapter adds no write method on top.
        uri = f"file:{self.legacy_db_path.resolve()}?mode=ro"
        self._conn = sqlite3.connect(uri, uri=True)
        self._conn.row_factory = sqlite3.Row
        self._verify_legacy_schema()

    def _verify_legacy_schema(self) -> None:
        """Verify the fixture has the R1 tables the adapter reads."""
        required = {
            "projects", "source_revisions", "listing_snapshots",
            "monitoring_runs", "canonical_facts", "domain_objects",
        }
        actual = set()
        for row in self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall():
            actual.add(row["name"])
        missing = required - actual
        if missing:
            raise LegacyAdapterError(
                f"legacy fixture is missing required R1 tables: {sorted(missing)}"
            )
        non_synthetic = self._conn.execute(
            "SELECT project_id FROM projects WHERE is_synthetic != 1"
            " OR is_synthetic IS NULL ORDER BY project_id"
        ).fetchall()
        if non_synthetic:
            raise LegacyAdapterError(
                "R1 legacy adapter accepts synthetic fixtures only; non-synthetic "
                f"projects found: {[row['project_id'] for row in non_synthetic]}"
            )
        non_synthetic_snapshots = self._conn.execute(
            "SELECT snapshot_id FROM listing_snapshots WHERE is_synthetic != 1"
            " OR is_synthetic IS NULL ORDER BY snapshot_id"
        ).fetchall()
        if non_synthetic_snapshots:
            raise LegacyAdapterError(
                "R1 legacy adapter accepts synthetic snapshots only; non-synthetic "
                "snapshots found: "
                f"{[row['snapshot_id'] for row in non_synthetic_snapshots]}"
            )

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "R1LegacyAdapter":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- read-only projections --------------------------------------------

    def project_ids(self) -> List[str]:
        return [
            r["project_id"] for r in self._conn.execute(
                "SELECT project_id FROM projects ORDER BY project_id"
            ).fetchall()
        ]

    def sources(self, project_id: str) -> Tuple[LegacySourceRow, ...]:
        rows = self._conn.execute(
            "SELECT revision_id, project_id, source_type, version, content_hash,"
            " valid_from, scope_json, created_at"
            " FROM source_revisions WHERE project_id=? ORDER BY revision_id",
            (project_id,),
        ).fetchall()
        return tuple(
            LegacySourceRow(
                revision_id=r["revision_id"],
                project_id=r["project_id"],
                source_type=r["source_type"],
                version=r["version"],
                content_hash=r["content_hash"],
                valid_from=r["valid_from"],
                scope=json.loads(r["scope_json"]),
                created_at=r["created_at"],
            )
            for r in rows
        )

    def snapshots(self, project_id: str) -> Tuple[LegacySnapshotRow, ...]:
        rows = self._conn.execute(
            "SELECT snapshot_id, project_id, revision_id, snapshot_version,"
            " content_hash, row_count, structure_json, is_synthetic, created_at"
            " FROM listing_snapshots WHERE project_id=? ORDER BY snapshot_id",
            (project_id,),
        ).fetchall()
        return tuple(
            LegacySnapshotRow(
                snapshot_id=r["snapshot_id"],
                project_id=r["project_id"],
                revision_id=r["revision_id"],
                snapshot_version=r["snapshot_version"],
                content_hash=r["content_hash"],
                row_count=int(r["row_count"]),
                structure=json.loads(r["structure_json"]),
                is_synthetic=bool(r["is_synthetic"]),
                created_at=r["created_at"],
            )
            for r in rows
        )

    def facts(self, project_id: str) -> Tuple[LegacyFactRow, ...]:
        # canonical_facts is keyed by (run_id, fact_hash); join through
        # monitoring_runs to scope by project_id.
        rows = self._conn.execute(
            "SELECT cf.run_id, cf.fact_hash, cf.fact_id, cf.node_id, cf.fact_json"
            " FROM canonical_facts cf"
            " JOIN monitoring_runs mr ON cf.run_id = mr.run_id"
            " WHERE mr.project_id=? ORDER BY cf.fact_hash",
            (project_id,),
        ).fetchall()
        out: List[LegacyFactRow] = []
        for r in rows:
            payload = json.loads(r["fact_json"])
            out.append(LegacyFactRow(
                run_id=r["run_id"],
                fact_hash=r["fact_hash"],
                fact_id=r["fact_id"],
                node_id=r["node_id"],
                fact_type=payload.get("fact_type", ""),
                subject_id=payload.get("subject_id"),
                site_id=payload.get("site_id"),
                body=payload.get("body", {}),
                source_refs=list(payload.get("source_refs", [])),
            ))
        return tuple(out)

    def risks(self, project_id: str) -> Tuple[LegacyRiskRow, ...]:
        # R1 stores risk objects in domain_objects (kind-based, versioned).
        rows = self._conn.execute(
            "SELECT kind, object_id, version, content_hash, object_json"
            " FROM domain_objects"
            " WHERE kind IN ('risk_identity','risk_candidate','risk_instance')"
            " ORDER BY kind, object_id, version",
        ).fetchall()
        # domain_objects is not project-scoped directly; filter by payload.
        out: List[LegacyRiskRow] = []
        for r in rows:
            payload = json.loads(r["object_json"])
            if payload.get("project_id") != project_id:
                continue
            out.append(LegacyRiskRow(
                kind=r["kind"],
                object_id=r["object_id"],
                version=int(r["version"]),
                content_hash=r["content_hash"],
                payload=payload,
            ))
        return tuple(out)

    def projection(self, project_id: str) -> LegacyProjection:
        """Return all proven R1 projections for one project."""
        if project_id not in set(self.project_ids()):
            raise LegacyAdapterError(
                f"project {project_id!r} not found in legacy fixture"
            )
        return LegacyProjection(
            project_id=project_id,
            sources=self.sources(project_id),
            snapshots=self.snapshots(project_id),
            facts=self.facts(project_id),
            risks=self.risks(project_id),
        )

    @staticmethod
    def fact_identity_key(run_id: str, fact_hash: str) -> str:
        """Return the proven composite key of one R1 canonical fact."""
        return json.dumps(
            ["fact", run_id, fact_hash],
            ensure_ascii=False, separators=(",", ":"),
        )

    @staticmethod
    def risk_identity_key(kind: str, object_id: str, version: int) -> str:
        """Return the proven composite key of one versioned R1 risk object."""
        return json.dumps(
            ["risk", kind, object_id, int(version)],
            ensure_ascii=False, separators=(",", ":"),
        )

    # -- dual-read diff ----------------------------------------------------

    def dual_read_diff(
        self,
        project_id: str,
        r2_state: "R2DualReadState",
    ) -> DualReadDiff:
        """Compare R1 legacy state against an R2 current state projection.

        ``r2_state`` is an :class:`R2DualReadState` carrying the R2-side
        content hashes keyed by the same proven identity keys the adapter
        uses.  Emits matched / unmatched / ambiguous entries.
        """
        legacy = self.projection(project_id)
        entries: List[DiffEntry] = []

        # Sources
        legacy_sources = {
            src.revision_id: src.content_hash for src in legacy.sources
        }
        entries.extend(_diff_entity(
            "source", legacy_sources, r2_state.sources,
        ))
        # Snapshots
        legacy_snaps = {
            s.snapshot_id: s.content_hash for s in legacy.snapshots
        }
        entries.extend(_diff_entity(
            "snapshot", legacy_snaps, r2_state.snapshots,
        ))
        # Facts
        legacy_facts = {
            self.fact_identity_key(f.run_id, f.fact_hash): f.fact_hash
            for f in legacy.facts
        }
        entries.extend(_diff_entity(
            "fact", legacy_facts, r2_state.facts,
        ))
        # Risks (identity key -> content_hash)
        legacy_risks = {
            self.risk_identity_key(r.kind, r.object_id, r.version): r.content_hash
            for r in legacy.risks
        }
        entries.extend(_diff_entity(
            "risk", legacy_risks, r2_state.risks,
        ))

        return DualReadDiff(project_id=project_id, entries=tuple(entries))


# ---------------------------------------------------------------------------
# R2-side dual-read input
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class R2DualReadState:
    """R2-side content-hash projection for a dual-read comparison.

    Each dict maps a proven identity key to the R2 content hash of that
    entity.  Build this from the live R2 store / services.
    """

    sources: Dict[str, str] = field(default_factory=dict)    # revision_id -> hash
    snapshots: Dict[str, str] = field(default_factory=dict)  # snapshot_id -> hash
    facts: Dict[str, str] = field(default_factory=dict)      # composite fact key -> hash
    risks: Dict[str, str] = field(default_factory=dict)      # composite risk key -> hash


# ---------------------------------------------------------------------------
# Diff helper
# ---------------------------------------------------------------------------

def _diff_entity(
    entity_kind: str,
    legacy: Dict[str, str],
    r2: Dict[str, str],
) -> List[DiffEntry]:
    """Compute matched / unmatched / ambiguous entries for one entity kind."""
    out: List[DiffEntry] = []
    all_keys = set(legacy) | set(r2)
    for key in sorted(all_keys):
        lh = legacy.get(key, "")
        rh = r2.get(key, "")
        if lh and rh:
            if lh == rh:
                out.append(DiffEntry(
                    entity_kind=entity_kind, identity_key=key,
                    status=DiffStatus.MATCHED, legacy_hash=lh, r2_hash=rh,
                ))
            else:
                out.append(DiffEntry(
                    entity_kind=entity_kind, identity_key=key,
                    status=DiffStatus.AMBIGUOUS, legacy_hash=lh, r2_hash=rh,
                    detail=f"identity matched but content differs",
                ))
        elif lh and not rh:
            out.append(DiffEntry(
                entity_kind=entity_kind, identity_key=key,
                status=DiffStatus.UNMATCHED_LEGACY_ONLY, legacy_hash=lh,
                detail="present in R1 legacy, absent in R2",
            ))
        else:
            out.append(DiffEntry(
                entity_kind=entity_kind, identity_key=key,
                status=DiffStatus.UNMATCHED_R2_ONLY, r2_hash=rh or "",
                detail="present in R2, absent in R1 legacy",
            ))
    return out
