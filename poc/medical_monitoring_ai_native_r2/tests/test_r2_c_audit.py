"""Batch C: hash-chained tamper-evident audit tests."""

import sqlite3

import pytest

from mm_r2.audit import AuditChain, AuditError, AuditEvent, AUDIT_GENESIS_SEED
from mm_r2.domain import sha256_hex


@pytest.fixture
def audit_chain(tmp_path):
    db = tmp_path / "audit.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    chain = AuditChain(conn)
    chain.ensure_schema()
    yield chain
    conn.close()


class TestAuditChain:
    def test_genesis_seed_is_stable(self):
        assert sha256_hex(AUDIT_GENESIS_SEED)

    def test_head_starts_at_genesis(self, audit_chain):
        seq, h = audit_chain.head()
        assert seq == 0
        assert h == sha256_hex(AUDIT_GENESIS_SEED)

    def test_append_advances_head(self, audit_chain):
        ev = audit_chain.append("test_event", {"key": "value"})
        assert ev.seq == 1
        assert ev.event_type == "test_event"
        seq, _ = audit_chain.head()
        assert seq == 1

    def test_chain_links_correctly(self, audit_chain):
        ev1 = audit_chain.append("e1", {"a": 1})
        ev2 = audit_chain.append("e2", {"b": 2})
        assert ev2.prev_hash == ev1.chain_hash
        assert ev2.seq == ev1.seq + 1

    def test_verify_clean_chain(self, audit_chain):
        audit_chain.append("e1", {"a": 1})
        audit_chain.append("e2", {"b": 2})
        assert audit_chain.verify_chain() is True

    def test_verify_detects_tampered_payload(self, audit_chain):
        audit_chain.append("e1", {"a": 1})
        # Tamper with the event payload directly (simulating out-of-band edit)
        audit_chain._conn.execute(
            "UPDATE r2_audit_events SET payload_json=? WHERE seq=1",
            ('{"a": "TAMPERED"}',),
        )
        assert audit_chain.verify_chain() is False

    def test_verify_detects_tampered_chain_hash(self, audit_chain):
        audit_chain.append("e1", {"a": 1})
        audit_chain._conn.execute(
            "UPDATE r2_audit_events SET chain_hash=? WHERE seq=1",
            ("0" * 64,),
        )
        assert audit_chain.verify_chain() is False

    def test_events_returns_in_order(self, audit_chain):
        audit_chain.append("e1", {"a": 1}, run_id="r1")
        audit_chain.append("e2", {"a": 2}, run_id="r1")
        audit_chain.append("e3", {"a": 3}, run_id="r2")
        all_events = audit_chain.events()
        assert len(all_events) == 3
        assert [e.seq for e in all_events] == [1, 2, 3]
        r1_events = audit_chain.events(run_id="r1")
        assert len(r1_events) == 2

    def test_rejects_empty_event_type(self, audit_chain):
        with pytest.raises(AuditError):
            audit_chain.append("", {"a": 1})

    def test_tail_head_mismatch_detected(self, audit_chain):
        audit_chain.append("e1", {"a": 1})
        # Tamper with the head to create a mismatch
        audit_chain._conn.execute(
            "UPDATE r2_audit_chain_head SET last_seq=999 WHERE singleton=1"
        )
        with pytest.raises(AuditError):
            audit_chain.append("e2", {"b": 2})
