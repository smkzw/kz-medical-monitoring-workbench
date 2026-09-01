"""R3-C snapshot diff and clinical impact propagation.

Computes deterministic diffs between two *full* listing snapshots using
stable record identities (R3-B ``identity``).  The input contract is
always full snapshots (Design §5.1: 输入始终是全量快照); there is no
incremental patch.  A diff classifies every record as added / removed /
unchanged / modified, and propagates *clinical impact* so that a record
that disappeared is never silently treated as resolved (Design §6.2:
旧记录在新快照消失时，先检查导出范围、结构、文件漏行和真实删除，
不能直接解除风险).

Design grounding: system design §§5,6,16 (deterministic_service: diff;
双基线; 增量传播; every derived result retains source locator/raw
value and explicit uncertainty); plan R3 step 7 (snapshot diff 与临床
影响传播).

Contracts
---------
* :class:`SnapshotFacts` -- an immutable, content-addressed set of
  canonical records keyed by stable :class:`RecordIdentity` digests.
  Carries its source revision and identity-algorithm lineage.
* :class:`ChangeKind` -- the four change kinds plus ``disappeared``.
* :class:`ChangeRecord` -- one diff entry: old/new identity, old/new
  payload, change kind, fields changed, and explicit uncertainty.
* :class:`SnapshotDiff` -- the full diff result with summary tallies.
* :class:`ImpactKind` / :class:`ImpactPropagation` -- clinical impact
  propagation that surfaces what downstream objects *may* be affected
  and which disappearances need scope/coverage review.

All classes are immutable and content-addressed; the same two snapshots
always yield the same diff.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .identity import (
    IdentityAlgorithm,
    IdentityResolution,
    RecordIdentity,
    resolve_rows as _resolve_rows_mod,
)
from .normalization import is_missing
from .primitives import (
    content_hash,
    deep_freeze_json,
    new_id,
    validate_nonempty_str,
    validate_sha256_hex,
)
from .schema_registry import default_registry

__all__ = [
    "SnapshotFacts",
    "ChangeKind",
    "CHANGE_KINDS",
    "ChangeRecord",
    "SnapshotDiff",
    "ImpactKind",
    "IMPACT_KINDS",
    "ImpactItem",
    "ImpactPropagation",
    "build_snapshot_facts",
    "diff_snapshots",
    "propagate_impact",
    "ScopeCoverageNote",
]


# ---------------------------------------------------------------------------
# Schema validation helper
# ---------------------------------------------------------------------------

def _validate_schema(obj: Any) -> None:
    default_registry().assert_writable(obj.schema_name, obj.schema_version)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class SnapshotDiffError(Exception):
    """Snapshot diff invariant violation."""


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ChangeKind:
    """How one record changed between baseline and current snapshot.

    * ``added`` -- record present in current but absent from baseline.
    * ``removed`` -- record present in baseline but absent from current
      *and* confirmed outside the current export scope (truly deleted).
    * ``disappeared`` -- record present in baseline but absent from
      current, but the current snapshot's scope does not confirm
      coverage (Design §6.2: cannot directly resolve risk).
    * ``unchanged`` -- same identity, same canonical payload.
    * ``modified`` -- same identity, different canonical payload.
    """
    ADDED = "added"
    REMOVED = "removed"
    DISAPPEARED = "disappeared"
    UNCHANGED = "unchanged"
    MODIFIED = "modified"


CHANGE_KINDS: Tuple[str, ...] = (
    ChangeKind.ADDED,
    ChangeKind.REMOVED,
    ChangeKind.DISAPPEARED,
    ChangeKind.UNCHANGED,
    ChangeKind.MODIFIED,
)


class ImpactKind:
    """Clinical impact classification for one change.

    * ``new_finding`` -- a new record may introduce new clinical findings.
    * ``data_correction`` -- a modified record is a data correction.
    * ``potential_loss`` -- a disappeared record may have been lost
      (scope/coverage gap); must not auto-resolve.
    * ``confirmed_removal`` -- a removed record is confirmed deleted.
    * ``none`` -- no clinical impact (unchanged).
    """
    NEW_FINDING = "new_finding"
    DATA_CORRECTION = "data_correction"
    POTENTIAL_LOSS = "potential_loss"
    CONFIRMED_REMOVAL = "confirmed_removal"
    NONE = "none"


IMPACT_KINDS: Tuple[str, ...] = (
    ImpactKind.NEW_FINDING,
    ImpactKind.DATA_CORRECTION,
    ImpactKind.POTENTIAL_LOSS,
    ImpactKind.CONFIRMED_REMOVAL,
    ImpactKind.NONE,
)


def _validate_enum(value: str, allowed: Tuple[str, ...], field_name: str) -> str:
    if value not in allowed:
        raise SnapshotDiffError(f"{field_name}={value!r} not in {allowed}")
    return value


# ---------------------------------------------------------------------------
# ScopeCoverageNote -- scope/coverage confirmation for disappearances
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScopeCoverageNote:
    """Documents whether the *current* snapshot's export scope covers the
    baseline record that is absent.

    Design §6.2: 旧记录在新快照消失时，先检查导出范围、结构、文件漏行
    和真实删除，不能直接解除风险.  A disappearance is only reclassified
    as ``removed`` when coverage is explicitly confirmed.
    """
    record_id: str
    covered: bool
    basis: str
    confirmed_by: str = ""

    def __post_init__(self) -> None:
        validate_nonempty_str(self.record_id, "ScopeCoverageNote.record_id")
        validate_nonempty_str(self.basis, "ScopeCoverageNote.basis")
        object.__setattr__(self, "covered", bool(self.covered))
        if self.covered:
            validate_nonempty_str(
                self.confirmed_by,
                "ScopeCoverageNote.confirmed_by when covered=True",
            )


# ---------------------------------------------------------------------------
# SnapshotFacts (immutable, content-addressed)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SnapshotFacts:
    """An immutable set of canonical records from one full snapshot.

    Each record is a ``Mapping[str, Any]`` (the canonical row payload)
    keyed by its stable :class:`RecordIdentity` digest.  The facts bind
    to a source revision and a frozen identity algorithm so the diff is
    reproducible.

    ``coverage_scope`` is the declared export scope of this snapshot
    (e.g. ``{"domain": "ae"}``).  It is used by impact propagation to
    decide whether absent baseline records *disappeared* (coverage gap)
    vs were *removed* (confirmed in scope).
    """
    schema_name: str = "r3_snapshot_facts"
    schema_version: str = "1"
    facts_id: str = ""
    project_id: str = ""
    source_revision_id: str = ""
    algorithm_digest: str = ""
    records: Tuple[Tuple[str, Mapping[str, Any]], ...] = ()
    coverage_scope: Tuple[Tuple[str, Any], ...] = ()
    n_records: int = 0
    content_hash: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.facts_id, "SnapshotFacts.facts_id")
        validate_nonempty_str(self.project_id, "SnapshotFacts.project_id")
        validate_nonempty_str(self.source_revision_id, "SnapshotFacts.source_revision_id")
        validate_sha256_hex(self.algorithm_digest, "SnapshotFacts.algorithm_digest")
        frozen_recs = deep_freeze_json(self.records)
        # validate uniqueness of digests (keys)
        keys = [k for k, _ in frozen_recs]
        for key in keys:
            validate_sha256_hex(key, "SnapshotFacts record digest")
        if len(set(keys)) != len(keys):
            raise SnapshotDiffError("SnapshotFacts record digests must be unique")
        object.__setattr__(self, "records", frozen_recs)
        object.__setattr__(self, "coverage_scope", deep_freeze_json(self.coverage_scope))
        object.__setattr__(self, "n_records", len(frozen_recs))
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise SnapshotDiffError(
                f"SnapshotFacts.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "facts_id": self.facts_id,
            "project_id": self.project_id,
            "source_revision_id": self.source_revision_id,
            "algorithm_digest": self.algorithm_digest,
            "records": [
                {"digest": k, "payload": dict(v)}
                for k, v in sorted(self.records, key=lambda r: r[0])
            ],
            "coverage_scope": dict(self.coverage_scope),
        }

    def content_fingerprint(self) -> Dict[str, Any]:
        """Structure-only payload (excludes the surrogate facts_id)."""
        return {
            "project_id": self.project_id,
            "source_revision_id": self.source_revision_id,
            "algorithm_digest": self.algorithm_digest,
            "records": [
                {"digest": k, "payload": dict(v)}
                for k, v in sorted(self.records, key=lambda r: r[0])
            ],
            "coverage_scope": dict(self.coverage_scope),
        }

    def compute_hash(self) -> str:
        return content_hash(self.content_fingerprint())

    def as_dict(self) -> Dict[str, Mapping[str, Any]]:
        """Return records as a plain dict keyed by digest."""
        return {k: v for k, v in self.records}

    def scope_get(self, key: str, default: Any = None) -> Any:
        for k, v in self.coverage_scope:
            if k == key:
                return v
        return default

    @property
    def scope_unspecified(self) -> bool:
        return len(self.coverage_scope) == 0


# ---------------------------------------------------------------------------
# ChangeRecord (one diff entry)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ChangeRecord:
    """One record-level change between baseline and current snapshots.

    ``record_id`` is the stable ``rec-<digest>`` id.  For ``added``
    records, ``old_payload`` is empty and ``new_payload`` carries the
    record.  For ``removed``/``disappeared``, the reverse.  For
    ``modified``, both carry payloads and ``fields_changed`` lists the
    field names that differ.
    """
    schema_name: str = "r3_change_record"
    schema_version: str = "1"
    record_id: str = ""
    change_kind: str = ChangeKind.UNCHANGED
    old_payload: Tuple[Tuple[str, Any], ...] = ()
    new_payload: Tuple[Tuple[str, Any], ...] = ()
    fields_changed: Tuple[str, ...] = ()
    uncertainty: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.record_id, "ChangeRecord.record_id")
        _validate_enum(self.change_kind, CHANGE_KINDS, "ChangeRecord.change_kind")
        object.__setattr__(self, "old_payload", deep_freeze_json(self.old_payload))
        object.__setattr__(self, "new_payload", deep_freeze_json(self.new_payload))
        object.__setattr__(self, "fields_changed", tuple(self.fields_changed))

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "change_kind": self.change_kind,
            "old_payload": dict(self.old_payload),
            "new_payload": dict(self.new_payload),
            "fields_changed": list(self.fields_changed),
            "uncertainty": self.uncertainty,
        }


# ---------------------------------------------------------------------------
# SnapshotDiff (the full diff result)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SnapshotDiff:
    """The deterministic diff between two :class:`SnapshotFacts`.

    Both snapshots must share the same ``project_id`` and
    ``algorithm_digest`` so record identities are comparable.

    Summary tallies are *derived* (never declared by the caller).
    ``changes`` is sorted by ``record_id`` for deterministic ordering.
    """
    schema_name: str = "r3_snapshot_diff"
    schema_version: str = "1"
    diff_id: str = ""
    project_id: str = ""
    baseline_source_revision_id: str = ""
    current_source_revision_id: str = ""
    algorithm_digest: str = ""
    changes: Tuple[ChangeRecord, ...] = ()
    n_added: int = 0
    n_removed: int = 0
    n_disappeared: int = 0
    n_unchanged: int = 0
    n_modified: int = 0
    content_hash: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.diff_id, "SnapshotDiff.diff_id")
        validate_nonempty_str(self.project_id, "SnapshotDiff.project_id")
        validate_nonempty_str(
            self.baseline_source_revision_id,
            "SnapshotDiff.baseline_source_revision_id",
        )
        validate_nonempty_str(
            self.current_source_revision_id,
            "SnapshotDiff.current_source_revision_id",
        )
        validate_sha256_hex(self.algorithm_digest, "SnapshotDiff.algorithm_digest")
        changes = tuple(sorted(self.changes, key=lambda c: c.record_id))
        record_ids = [c.record_id for c in changes]
        if len(set(record_ids)) != len(record_ids):
            raise SnapshotDiffError("SnapshotDiff change record_ids must be unique")
        object.__setattr__(self, "changes", changes)
        # derive tallies
        added = sum(1 for c in changes if c.change_kind == ChangeKind.ADDED)
        removed = sum(1 for c in changes if c.change_kind == ChangeKind.REMOVED)
        disappeared = sum(1 for c in changes if c.change_kind == ChangeKind.DISAPPEARED)
        unchanged = sum(1 for c in changes if c.change_kind == ChangeKind.UNCHANGED)
        modified = sum(1 for c in changes if c.change_kind == ChangeKind.MODIFIED)
        object.__setattr__(self, "n_added", added)
        object.__setattr__(self, "n_removed", removed)
        object.__setattr__(self, "n_disappeared", disappeared)
        object.__setattr__(self, "n_unchanged", unchanged)
        object.__setattr__(self, "n_modified", modified)
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise SnapshotDiffError(
                f"SnapshotDiff.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "diff_id": self.diff_id,
            "project_id": self.project_id,
            "baseline_source_revision_id": self.baseline_source_revision_id,
            "current_source_revision_id": self.current_source_revision_id,
            "algorithm_digest": self.algorithm_digest,
            "changes": [c.canonical_payload() for c in self.changes],
        }

    def content_fingerprint(self) -> Dict[str, Any]:
        """Excludes surrogate diff_id for stable content addressing."""
        return {
            "project_id": self.project_id,
            "baseline_source_revision_id": self.baseline_source_revision_id,
            "current_source_revision_id": self.current_source_revision_id,
            "algorithm_digest": self.algorithm_digest,
            "changes": [c.canonical_payload() for c in self.changes],
        }

    def compute_hash(self) -> str:
        return content_hash(self.content_fingerprint())

    def changes_of(self, kind: str) -> Tuple[ChangeRecord, ...]:
        """All change records of one kind, deterministically ordered."""
        _validate_enum(kind, CHANGE_KINDS, "kind")
        return tuple(c for c in self.changes if c.change_kind == kind)

    @property
    def has_changes(self) -> bool:
        """True iff any non-unchanged change exists."""
        return any(c.change_kind != ChangeKind.UNCHANGED for c in self.changes)

    @property
    def has_disappearances(self) -> bool:
        """True iff any disappeared (coverage-unconfirmed) record exists."""
        return self.n_disappeared > 0


# ---------------------------------------------------------------------------
# ImpactItem + ImpactPropagation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImpactItem:
    """One propagated clinical impact for one change record."""
    record_id: str
    change_kind: str
    impact_kind: str
    affected_domains: Tuple[str, ...] = ()
    affected_subjects: Tuple[str, ...] = ()
    requires_review: bool = False
    uncertainty: str = ""

    def __post_init__(self) -> None:
        validate_nonempty_str(self.record_id, "ImpactItem.record_id")
        _validate_enum(self.change_kind, CHANGE_KINDS, "ImpactItem.change_kind")
        _validate_enum(self.impact_kind, IMPACT_KINDS, "ImpactItem.impact_kind")
        if self.impact_kind == ImpactKind.POTENTIAL_LOSS and not self.requires_review:
            raise SnapshotDiffError(
                "potential_loss impact must require review"
            )
        object.__setattr__(self, "affected_domains", deep_freeze_json(self.affected_domains))
        object.__setattr__(self, "affected_subjects", deep_freeze_json(self.affected_subjects))


@dataclass(frozen=True)
class ImpactPropagation:
    """Clinical impact propagation result for one :class:`SnapshotDiff`.

    Design §6.2/§10.1: disappearances and rule/knowledge/mapping changes
    propagate as ``superseded`` or ``not_evaluable``, never as resolved;
    only confirmed data evidence of true removal uses ``resolved_by_data``.
    """
    schema_name: str = "r3_impact_propagation"
    schema_version: str = "1"
    propagation_id: str = ""
    project_id: str = ""
    diff_content_hash: str = ""
    items: Tuple[ImpactItem, ...] = ()
    n_new_finding: int = 0
    n_data_correction: int = 0
    n_potential_loss: int = 0
    n_confirmed_removal: int = 0
    n_none: int = 0
    content_hash: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.propagation_id, "ImpactPropagation.propagation_id")
        validate_nonempty_str(self.project_id, "ImpactPropagation.project_id")
        validate_sha256_hex(self.diff_content_hash, "ImpactPropagation.diff_content_hash")
        items = tuple(self.items)
        object.__setattr__(self, "items", items)
        nf = sum(1 for i in items if i.impact_kind == ImpactKind.NEW_FINDING)
        dc = sum(1 for i in items if i.impact_kind == ImpactKind.DATA_CORRECTION)
        pl = sum(1 for i in items if i.impact_kind == ImpactKind.POTENTIAL_LOSS)
        cr = sum(1 for i in items if i.impact_kind == ImpactKind.CONFIRMED_REMOVAL)
        no = sum(1 for i in items if i.impact_kind == ImpactKind.NONE)
        object.__setattr__(self, "n_new_finding", nf)
        object.__setattr__(self, "n_data_correction", dc)
        object.__setattr__(self, "n_potential_loss", pl)
        object.__setattr__(self, "n_confirmed_removal", cr)
        object.__setattr__(self, "n_none", no)
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise SnapshotDiffError(
                f"ImpactPropagation.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "propagation_id": self.propagation_id,
            "project_id": self.project_id,
            "diff_content_hash": self.diff_content_hash,
            "items": [
                {
                    "record_id": i.record_id,
                    "change_kind": i.change_kind,
                    "impact_kind": i.impact_kind,
                    "affected_domains": list(i.affected_domains),
                    "affected_subjects": list(i.affected_subjects),
                    "requires_review": i.requires_review,
                    "uncertainty": i.uncertainty,
                }
                for i in self.items
            ],
        }

    def content_fingerprint(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "diff_content_hash": self.diff_content_hash,
            "items": [
                {
                    "record_id": i.record_id,
                    "change_kind": i.change_kind,
                    "impact_kind": i.impact_kind,
                    "affected_domains": list(i.affected_domains),
                    "affected_subjects": list(i.affected_subjects),
                    "requires_review": i.requires_review,
                    "uncertainty": i.uncertainty,
                }
                for i in self.items
            ],
        }

    def compute_hash(self) -> str:
        return content_hash(self.content_fingerprint())

    @property
    def requires_review_count(self) -> int:
        return sum(1 for i in self.items if i.requires_review)


# ---------------------------------------------------------------------------
# Payload comparison helper
# ---------------------------------------------------------------------------

def _canonicalize_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Canonicalize a record payload for deterministic comparison.

    String values are trimmed; missing sentinels become None so that a
    blank and an explicit "UNK" do not invent a spurious diff.
    """
    out: Dict[str, Any] = {}
    for k in sorted(payload.keys()):
        v = payload[k]
        if is_missing(v):
            out[k] = None
        elif isinstance(v, str):
            out[k] = v.strip()
        else:
            out[k] = v
    return out


def _fields_changed(
    old: Mapping[str, Any],
    new: Mapping[str, Any],
) -> Tuple[str, ...]:
    """Return the sorted tuple of field names whose canonical values differ."""
    old_c = _canonicalize_payload(old)
    new_c = _canonicalize_payload(new)
    all_keys = sorted(set(old_c.keys()) | set(new_c.keys()))
    return tuple(k for k in all_keys if old_c.get(k) != new_c.get(k))


# ---------------------------------------------------------------------------
# build_snapshot_facts
# ---------------------------------------------------------------------------

def build_snapshot_facts(
    project_id: str,
    source_revision_id: str,
    algorithm: IdentityAlgorithm,
    rows: Sequence[Mapping[str, Any]],
    *,
    coverage_scope: Optional[Mapping[str, Any]] = None,
    facts_id: str = "",
) -> Tuple[SnapshotFacts, IdentityResolution]:
    """Build :class:`SnapshotFacts` from raw listing rows.

    Resolves each row under ``algorithm`` and stores the canonical payload
    keyed by the record identity digest.  Returns both the facts and the
    identity resolution (so the caller can inspect ambiguities).

    Identity ambiguity or duplicate keys block facts construction.  Building
    a partial snapshot by silently dropping ambiguous rows or keeping the
    first duplicate would corrupt downstream incremental comparison.
    """
    validate_nonempty_str(project_id, "build_snapshot_facts.project_id")
    validate_nonempty_str(source_revision_id, "build_snapshot_facts.source_revision_id")
    if algorithm is None:
        raise SnapshotDiffError("build_snapshot_facts requires an IdentityAlgorithm")

    resolution = _resolve_rows_mod(
        project_id=project_id,
        source_revision_id=source_revision_id,
        algorithm=algorithm,
        rows=list(rows),
    )
    if not resolution.is_clean:
        raise SnapshotDiffError(
            "identity ambiguity blocks snapshot facts construction"
        )
    if resolution.has_duplicates:
        raise SnapshotDiffError(
            "duplicate identity keys block snapshot facts construction"
        )

    row_by_index: Dict[int, Mapping[str, Any]] = {}
    for i, row in enumerate(rows):
        idx = row.get("_row_index", i)
        if idx in row_by_index:
            raise SnapshotDiffError(
                f"duplicate source row index {idx!r} blocks snapshot facts construction"
            )
        row_by_index[idx] = row

    records: List[Tuple[str, Mapping[str, Any]]] = []
    for ri in resolution.resolved:
        digest = ri.digest
        row_index = ri.row_index if ri.row_index is not None else 0
        if row_index not in row_by_index:
            raise SnapshotDiffError(
                f"resolved row index {row_index!r} has no source row"
            )
        row = row_by_index[row_index]
        # ``_row_index`` and ``_record_id`` are pipeline locators, not source
        # clinical values.  Keeping either in the canonical payload would let
        # regenerated internal identifiers create a false MODIFIED diff.
        payload = {
            k: v
            for k, v in row.items()
            if k not in ("_row_index", "_record_id")
        }
        records.append((digest, payload))

    scope_tuple = tuple(sorted((coverage_scope or {}).items()))
    facts = SnapshotFacts(
        facts_id=facts_id or new_id("facts-"),
        project_id=project_id,
        source_revision_id=source_revision_id,
        algorithm_digest=algorithm.digest,
        records=tuple(records),
        coverage_scope=scope_tuple,
    )
    return facts, resolution


# ---------------------------------------------------------------------------
# diff_snapshots
# ---------------------------------------------------------------------------

def diff_snapshots(
    baseline: SnapshotFacts,
    current: SnapshotFacts,
    *,
    coverage_notes: Optional[Sequence[ScopeCoverageNote]] = None,
    diff_id: str = "",
) -> SnapshotDiff:
    """Compute the deterministic diff between two full snapshots.

    Both snapshots must share ``project_id`` and ``algorithm_digest`` so
    record identities are comparable.

    ``coverage_notes`` documents whether the *current* snapshot's export
    scope covers each absent baseline record.  Without a confirming note,
    an absent record is ``disappeared`` (coverage gap, not auto-resolved).
    With a confirming note (``covered=True``), it is ``removed``.
    """
    if baseline.project_id != current.project_id:
        raise SnapshotDiffError(
            "baseline and current project_id must match for diff"
        )
    if baseline.algorithm_digest != current.algorithm_digest:
        raise SnapshotDiffError(
            "baseline and current algorithm_digest must match for diff; "
            "different identity algorithms make records incomparable"
        )

    note_map: Dict[str, ScopeCoverageNote] = {}
    for note in (coverage_notes or []):
        if note.record_id in note_map:
            raise SnapshotDiffError(
                f"duplicate coverage note for {note.record_id!r}"
            )
        note_map[note.record_id] = note

    baseline_recs = baseline.as_dict()
    current_recs = current.as_dict()
    all_digests = sorted(set(baseline_recs.keys()) | set(current_recs.keys()))
    absent_record_ids = {
        f"rec-{digest}"
        for digest in baseline_recs
        if digest not in current_recs
    }
    unknown_note_ids = set(note_map) - absent_record_ids
    if unknown_note_ids:
        raise SnapshotDiffError(
            "coverage notes may only refer to baseline records absent from the current snapshot"
        )

    changes: List[ChangeRecord] = []
    for digest in all_digests:
        record_id = f"rec-{digest}"
        in_base = digest in baseline_recs
        in_curr = digest in current_recs

        if in_base and in_curr:
            old_p = baseline_recs[digest]
            new_p = current_recs[digest]
            fc = _fields_changed(old_p, new_p)
            if fc:
                changes.append(ChangeRecord(
                    record_id=record_id,
                    change_kind=ChangeKind.MODIFIED,
                    old_payload=tuple(sorted(old_p.items())),
                    new_payload=tuple(sorted(new_p.items())),
                    fields_changed=fc,
                    uncertainty="",
                ))
            else:
                changes.append(ChangeRecord(
                    record_id=record_id,
                    change_kind=ChangeKind.UNCHANGED,
                ))
        elif in_curr and not in_base:
            new_p = current_recs[digest]
            changes.append(ChangeRecord(
                record_id=record_id,
                change_kind=ChangeKind.ADDED,
                new_payload=tuple(sorted(new_p.items())),
                uncertainty="",
            ))
        else:
            # in_base and not in_curr: removed or disappeared
            old_p = baseline_recs[digest]
            note = note_map.get(record_id)
            if note is not None and note.covered:
                changes.append(ChangeRecord(
                    record_id=record_id,
                    change_kind=ChangeKind.REMOVED,
                    old_payload=tuple(sorted(old_p.items())),
                    uncertainty=f"confirmed removal: {note.basis}",
                ))
            else:
                reason = (
                    f"coverage note: {note.basis}"
                    if note is not None
                    else "absent from current snapshot; coverage unconfirmed"
                )
                changes.append(ChangeRecord(
                    record_id=record_id,
                    change_kind=ChangeKind.DISAPPEARED,
                    old_payload=tuple(sorted(old_p.items())),
                    uncertainty=(
                        "record absent from current snapshot; export "
                        f"scope/coverage not confirmed ({reason})"
                    ),
                ))

    # deterministic sort by record_id
    changes.sort(key=lambda c: c.record_id)

    return SnapshotDiff(
        diff_id=diff_id or new_id("diff-"),
        project_id=baseline.project_id,
        baseline_source_revision_id=baseline.source_revision_id,
        current_source_revision_id=current.source_revision_id,
        algorithm_digest=baseline.algorithm_digest,
        changes=tuple(changes),
    )


# ---------------------------------------------------------------------------
# propagate_impact
# ---------------------------------------------------------------------------

def _payload_as_dict(payload: Any) -> Dict[str, Any]:
    """Coerce a ChangeRecord payload (tuple of pairs or mapping) to a dict."""
    if isinstance(payload, Mapping):
        return dict(payload)
    if isinstance(payload, (tuple, list)):
        return {k: v for k, v in payload}
    return {}


def _extract_domains(payload: Any) -> Tuple[str, ...]:
    """Extract domain hints from a record payload (heuristic, no hardcoding)."""
    d = _payload_as_dict(payload)
    domains: List[str] = []
    for key in ("domain", "DOMAIN", "dataset", "DATASET"):
        val = d.get(key)
        if isinstance(val, str) and val.strip():
            domains.append(val.strip().upper())
    return tuple(sorted(set(domains)))


def _extract_subjects(payload: Any) -> Tuple[str, ...]:
    """Extract subject identifiers from common and renamed listing fields."""
    d = _payload_as_dict(payload)
    subjects: List[str] = []
    explicit = {
        "subject", "usubjid", "subjid", "subj", "pt", "ptid",
        "patient", "patientid", "patientnum", "participantid",
        "受试者", "受试者编号", "参与者", "参与者编号",
    }
    for key, val in d.items():
        normalized_key = "".join(ch for ch in str(key).casefold() if ch.isalnum())
        looks_like_subject_id = (
            normalized_key in explicit
            or (
                any(token in normalized_key for token in ("subject", "subj", "patient", "participant"))
                and any(token in normalized_key for token in ("id", "num", "number", "no"))
            )
        )
        if looks_like_subject_id and isinstance(val, str) and val.strip():
            subjects.append(val.strip())
    return tuple(sorted(set(subjects)))


def propagate_impact(
    diff: SnapshotDiff,
    *,
    propagation_id: str = "",
) -> ImpactPropagation:
    """Propagate clinical impact for each change in a :class:`SnapshotDiff`.

    Mapping rules (Design §6.2, §10.1):

    * ``added`` -> :attr:`ImpactKind.NEW_FINDING`, requires review.
    * ``modified`` -> :attr:`ImpactKind.DATA_CORRECTION`, requires review.
    * ``removed`` (confirmed) -> :attr:`ImpactKind.CONFIRMED_REMOVAL`.
    * ``disappeared`` -> :attr:`ImpactKind.POTENTIAL_LOSS`, requires review
      (never auto-resolved).
    * ``unchanged`` -> :attr:`ImpactKind.NONE`.
    """
    items: List[ImpactItem] = []
    for c in diff.changes:
        domains: Tuple[str, ...] = ()
        subjects: Tuple[str, ...] = ()
        payload = c.new_payload if c.new_payload else c.old_payload
        if payload:
            domains = _extract_domains(payload)
            subjects = _extract_subjects(payload)

        if c.change_kind == ChangeKind.ADDED:
            items.append(ImpactItem(
                record_id=c.record_id,
                change_kind=c.change_kind,
                impact_kind=ImpactKind.NEW_FINDING,
                affected_domains=domains,
                affected_subjects=subjects,
                requires_review=True,
                uncertainty="new record; clinical significance unconfirmed",
            ))
        elif c.change_kind == ChangeKind.MODIFIED:
            items.append(ImpactItem(
                record_id=c.record_id,
                change_kind=c.change_kind,
                impact_kind=ImpactKind.DATA_CORRECTION,
                affected_domains=domains,
                affected_subjects=subjects,
                requires_review=True,
                uncertainty=f"fields changed: {list(c.fields_changed)}",
            ))
        elif c.change_kind == ChangeKind.REMOVED:
            items.append(ImpactItem(
                record_id=c.record_id,
                change_kind=c.change_kind,
                impact_kind=ImpactKind.CONFIRMED_REMOVAL,
                affected_domains=domains,
                affected_subjects=subjects,
                requires_review=False,
                uncertainty="confirmed in-scope removal",
            ))
        elif c.change_kind == ChangeKind.DISAPPEARED:
            items.append(ImpactItem(
                record_id=c.record_id,
                change_kind=c.change_kind,
                impact_kind=ImpactKind.POTENTIAL_LOSS,
                affected_domains=domains,
                affected_subjects=subjects,
                requires_review=True,
                uncertainty=(
                    "record absent from current snapshot; scope/coverage "
                    "unconfirmed; must not auto-resolve risk"
                ),
            ))
        else:  # unchanged
            items.append(ImpactItem(
                record_id=c.record_id,
                change_kind=c.change_kind,
                impact_kind=ImpactKind.NONE,
                affected_domains=domains,
                affected_subjects=subjects,
                requires_review=False,
                uncertainty="",
            ))

    return ImpactPropagation(
        propagation_id=propagation_id or new_id("impact-"),
        project_id=diff.project_id,
        diff_content_hash=diff.content_hash,
        items=tuple(items),
    )
