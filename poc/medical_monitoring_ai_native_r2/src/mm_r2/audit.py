"""Hash-chained tamper-evident audit log for the R2 kernel (Batch C).

The audit chain is append-only and hash-chained: every event's
``chain_hash`` is SHA-256 over ``(seq, event_type, payload_hash, prev_hash,
created_at)``.  A genesis hash anchors the chain head.  Verification walks
the chain and recomputes every link.

This is a functional data-integrity / recovery mechanism, not a security
control.  Adversarial tamper resistance is explicitly out of scope for this
batch per user directive; hashes make corruption and accidental edits
detectable and recoverable.

The chain is SQLite-backed.  The :class:`AuditChain` is opened with a
sqlite3 connection and shares the store's transaction (all audit appends
happen inside the store's single explicit transaction so state and audit
commit atomically).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .domain import (
    MmR2Error,
    canonical_json,
    content_hash,
    new_id,
    now_iso,
    sha256_hex,
    to_dictable,
)

__all__ = [
    "AuditError",
    "AuditEvent",
    "AuditChain",
    "AUDIT_GENESIS_SEED",
]

AUDIT_GENESIS_SEED = b"mm_r2:audit:genesis:v1"


def _genesis_hash() -> str:
    return sha256_hex(AUDIT_GENESIS_SEED)


class AuditError(MmR2Error):
    """Audit-chain violation (corruption, tail/head mismatch, bad append)."""


# ---------------------------------------------------------------------------
# Event value object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuditEvent:
    """One append-only audit event in the hash chain."""

    seq: int
    event_type: str
    payload: Dict[str, Any]
    payload_hash: str
    prev_hash: str
    chain_hash: str
    run_id: Optional[str]
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "AuditEvent":
        import json
        return cls(
            seq=int(row["seq"]),
            event_type=row["event_type"],
            payload=json.loads(row["payload_json"]),
            payload_hash=row["payload_hash"],
            prev_hash=row["prev_hash"],
            chain_hash=row["chain_hash"],
            run_id=row["run_id"],
            created_at=row["created_at"],
        )


# ---------------------------------------------------------------------------
# Schema (applied by the store on init; declared here as the single source)
# ---------------------------------------------------------------------------

AUDIT_SCHEMA = """
CREATE TABLE IF NOT EXISTS r2_audit_events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    chain_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_r2_audit_run ON r2_audit_events(run_id);
CREATE TABLE IF NOT EXISTS r2_audit_chain_head (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    last_seq INTEGER NOT NULL,
    last_chain_hash TEXT NOT NULL
);
"""


# ---------------------------------------------------------------------------
# Chain
# ---------------------------------------------------------------------------

class AuditChain:
    """Append-only hash-chained audit log.

    The chain is anchored by a genesis hash.  Every append:
      1. reads the durable chain head (``r2_audit_chain_head`` singleton),
      2. verifies it matches the actual last event row (tail check),
      3. computes the new chain hash over
         ``(seq, event_type, payload_hash, prev_hash, created_at)``,
      4. inserts the event and advances the head -- all inside the caller's
         transaction.

    A tail/head mismatch raises :class:`AuditError` (the chain was edited
    out of band).  Verification (:meth:`verify_chain`) recomputes every link.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # -- init --------------------------------------------------------------

    def ensure_schema(self) -> None:
        """Create the audit tables if absent and seed the genesis head."""
        self._conn.executescript(AUDIT_SCHEMA)
        self._conn.execute(
            "INSERT OR IGNORE INTO r2_audit_chain_head(singleton, last_seq, last_chain_hash)"
            " VALUES (1, 0, ?)",
            (_genesis_hash(),),
        )

    # -- append ------------------------------------------------------------

    def _read_head(self, conn: sqlite3.Connection) -> tuple:
        head = conn.execute(
            "SELECT last_seq, last_chain_hash FROM r2_audit_chain_head WHERE singleton=1"
        ).fetchone()
        if head is None:
            raise AuditError("audit chain head is missing")
        return int(head[0]), head[1]

    def _read_tail(self, conn: sqlite3.Connection) -> tuple:
        last = conn.execute(
            "SELECT seq, chain_hash FROM r2_audit_events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        if last is None:
            return 0, _genesis_hash()
        return int(last[0]), last[1]

    def append(
        self,
        event_type: str,
        payload: Dict[str, Any],
        *,
        run_id: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> AuditEvent:
        """Append one event inside the caller's transaction.

        ``conn`` defaults to this chain's connection.  Callers that run a
        custom transaction should pass their own connection so the append
        participates in it.
        """
        if not event_type or not isinstance(event_type, str):
            raise AuditError("audit event_type must be a non-empty string")
        c = conn if conn is not None else self._conn
        created = now_iso()
        payload_json = canonical_json(to_dictable(dict(payload)))
        payload_hash = sha256_hex(payload_json.encode("utf-8"))
        head = self._read_head(c)
        tail = self._read_tail(c)
        if tail != head:
            raise AuditError(
                "audit chain tail does not match its durable head "
                f"(tail={tail!r}, head={head!r})"
            )
        seq, prev = head[0] + 1, head[1]
        chain_hash = sha256_hex(canonical_json({
            "seq": seq,
            "event_type": event_type,
            "payload_hash": payload_hash,
            "prev_hash": prev,
            "created_at": created,
        }).encode("utf-8"))
        c.execute(
            "INSERT INTO r2_audit_events"
            "(seq, run_id, event_type, payload_json, payload_hash, prev_hash, chain_hash, created_at)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (seq, run_id, event_type, payload_json, payload_hash, prev, chain_hash, created),
        )
        c.execute(
            "UPDATE r2_audit_chain_head SET last_seq=?, last_chain_hash=? WHERE singleton=1",
            (seq, chain_hash),
        )
        return AuditEvent(
            seq=seq, event_type=event_type, payload=dict(payload),
            payload_hash=payload_hash, prev_hash=prev, chain_hash=chain_hash,
            run_id=run_id, created_at=created,
        )


    # -- read --------------------------------------------------------------

    def events(self, *, run_id: Optional[str] = None,
               limit: Optional[int] = None) -> List[AuditEvent]:
        if run_id is not None:
            stmt = (
                "SELECT * FROM r2_audit_events WHERE run_id=? ORDER BY seq"
            )
            params: tuple = (run_id,)
        else:
            stmt = "SELECT * FROM r2_audit_events ORDER BY seq"
            params = ()
        if limit is not None:
            stmt += " LIMIT ?"
            params = params + (int(limit),)
        rows = self._conn.execute(stmt, params).fetchall()
        return [AuditEvent.from_row(r) for r in rows]

    def head(self) -> tuple:
        return self._read_head(self._conn)

    # -- verify ------------------------------------------------------------

    def verify_chain(self) -> bool:
        """Recompute every link; return True iff the chain is intact."""
        prev = _genesis_hash()
        expected_seq = 0
        for row in self._conn.execute(
            "SELECT seq, event_type, payload_json, payload_hash, prev_hash,"
            " chain_hash, created_at FROM r2_audit_events ORDER BY seq"
        ).fetchall():
            seq = int(row[0])
            if seq != expected_seq + 1:
                return False
            if row[4] != prev:  # prev_hash must equal the prior chain_hash
                return False
            # Recompute payload_hash from the stored payload_json.
            recomputed_payload_hash = sha256_hex(
                row[2].encode("utf-8") if isinstance(row[2], str)
                else row[2]
            )
            if recomputed_payload_hash != row[3]:  # payload_hash
                return False
            recomputed = sha256_hex(canonical_json({
                "seq": seq,
                "event_type": row[1],
                "payload_hash": row[3],
                "prev_hash": row[4],
                "created_at": row[6],
            }).encode("utf-8"))
            if recomputed != row[5]:  # chain_hash
                return False
            prev = row[5]
            expected_seq = seq
        # Head must match the last computed link.
        head = self._read_head(self._conn)
        if head != (expected_seq, prev):
            return False
        return True
