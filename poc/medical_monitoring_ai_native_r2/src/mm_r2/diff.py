"""Full and incremental snapshot diff for the R2 kernel (Design v1.1 section
6.2; plan R2 step 5).

VETO 2 repairs:
* Requires exact AcceptanceService and BaselineService types.
* Incremental diff verifies the DataBaseline is registered in the supplied
  BaselineService.
* Derives canonical field map and mapping IDs from the accepted snapshot
  binding's MappingDefinitions — caller no longer supplies mapping authority.
* Unmapped changed fields emit explicit ``UNMAPPED`` provenance marker with
  ``is_unknown_field=True``.
* Rejects empty record_key_fields; case-insensitive UN/UNK key rejection.
* Partial date covers YYYY, YYYY-MM, and case-insensitive UN/UNK components.
* ``diff_hash`` binds full DiffEntry hashes and full ConfigChange semantics.
"""

from __future__ import annotations

import re as _re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .domain import (
    DomainValidationError,
    ListingSnapshot,
    MmR2Error,
    content_hash,
    deep_freeze_json,
    now_iso,
    validate_sha256_hex,
)

__all__ = [
    "DiffError",
    "DiffEntryKind",
    "DiffEntry",
    "FieldChange",
    "ConfigChangeKind",
    "ConfigChange",
    "ConfigChangeSet",
    "SnapshotDiff",
    "DiffService",
]


class DiffError(MmR2Error):
    """Snapshot diff violation."""


class DiffEntryKind:
    ADD = "add"
    CHANGE = "change"
    DISAPPEAR = "disappear"
    SCOPE_CHANGE = "scope_change"

    @classmethod
    def all_kinds(cls) -> Tuple[str, ...]:
        return (cls.ADD, cls.CHANGE, cls.DISAPPEAR, cls.SCOPE_CHANGE)


class ConfigChangeKind:
    KNOWLEDGE = "knowledge_change"
    RULE = "rule_change"
    MAPPING = "mapping_change"
    MODE = "mode_change"
    IDENTITY_ALGORITHM = "identity_algorithm_change"

    @classmethod
    def all_kinds(cls) -> Tuple[str, ...]:
        return (cls.KNOWLEDGE, cls.RULE, cls.MAPPING, cls.MODE,
                cls.IDENTITY_ALGORITHM)


@dataclass(frozen=True)
class FieldChange:
    canonical_field: str
    old_value: Any = None
    new_value: Any = None
    mapping_id: str = ""
    is_partial_date: bool = False
    is_unknown_field: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "old_value", deep_freeze_json(self.old_value))
        object.__setattr__(self, "new_value", deep_freeze_json(self.new_value))

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "canonical_field": self.canonical_field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "mapping_id": self.mapping_id,
            "is_partial_date": self.is_partial_date,
            "is_unknown_field": self.is_unknown_field,
        }


@dataclass(frozen=True)
class DiffEntry:
    schema_name: str = "diff_entry"
    schema_version: str = "1"
    entry_id: str = ""
    kind: str = ""
    record_key: str = ""
    subject_ref: str = ""
    domain: str = ""
    field_changes: Tuple[FieldChange, ...] = ()
    needs_scope_check: bool = False
    scope_dimension: str = ""
    impact_domains: Tuple[str, ...] = ()
    created_at: str = ""
    entry_hash: str = ""

    def __post_init__(self) -> None:
        if not self.entry_id:
            raise DomainValidationError("DiffEntry.entry_id is required")
        if self.kind not in DiffEntryKind.all_kinds():
            raise DomainValidationError(f"DiffEntry.kind {self.kind!r} invalid")
        if not self.record_key and self.kind != DiffEntryKind.SCOPE_CHANGE:
            raise DomainValidationError("record_key required for non-scope-change")
        field_changes = tuple(self.field_changes)
        if any(type(change) is not FieldChange for change in field_changes):
            raise DomainValidationError(
                "DiffEntry.field_changes must be FieldChange records"
            )
        object.__setattr__(self, "field_changes", tuple(sorted(
            field_changes,
            key=lambda change: content_hash(change.canonical_payload()),
        )))
        object.__setattr__(self, "impact_domains", tuple(sorted(set(
            self.impact_domains
        ))))
        if self.kind == DiffEntryKind.DISAPPEAR and not self.needs_scope_check:
            object.__setattr__(self, "needs_scope_check", True)
        expected = self.compute_hash()
        if self.entry_hash and self.entry_hash != expected:
            raise DomainValidationError("DiffEntry.entry_hash mismatch")
        object.__setattr__(self, "entry_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "entry_id": self.entry_id,
            "kind": self.kind,
            "record_key": self.record_key,
            "subject_ref": self.subject_ref,
            "domain": self.domain,
            "field_changes": [fc.canonical_payload() for fc in self.field_changes],
            "needs_scope_check": self.needs_scope_check,
            "scope_dimension": self.scope_dimension,
            "impact_domains": list(self.impact_domains),
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


@dataclass(frozen=True)
class ConfigChange:
    kind: str = ""
    ref_id: str = ""
    old_version: str = ""
    new_version: str = ""
    old_digest: str = ""
    new_digest: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        if self.kind not in ConfigChangeKind.all_kinds():
            raise DomainValidationError(f"ConfigChange.kind {self.kind!r} invalid")
        if not self.ref_id:
            raise DomainValidationError("ConfigChange.ref_id is required")
        if not self.detail:
            raise DomainValidationError("ConfigChange.detail is required")
        if self.old_digest:
            validate_sha256_hex(self.old_digest, "ConfigChange.old_digest")
        if self.new_digest:
            validate_sha256_hex(self.new_digest, "ConfigChange.new_digest")

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "kind": self.kind, "ref_id": self.ref_id,
            "old_version": self.old_version, "new_version": self.new_version,
            "old_digest": self.old_digest, "new_digest": self.new_digest,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ConfigChangeSet:
    changes: Tuple[ConfigChange, ...] = ()

    def __post_init__(self) -> None:
        changes = tuple(self.changes)
        if any(type(change) is not ConfigChange for change in changes):
            raise DomainValidationError("ConfigChangeSet requires ConfigChange records")
        changes = tuple(sorted(
            changes,
            key=lambda change: content_hash(change.canonical_payload()),
        ))
        object.__setattr__(self, "changes", changes)

    @property
    def is_empty(self) -> bool:
        return len(self.changes) == 0

    def kinds(self) -> Tuple[str, ...]:
        return tuple(sorted({c.kind for c in self.changes}))

    def canonical_payload(self) -> List[Dict[str, Any]]:
        return [c.canonical_payload() for c in self.changes]


@dataclass(frozen=True)
class SnapshotDiff:
    schema_name: str = "snapshot_diff"
    schema_version: str = "1"
    diff_id: str = ""
    project_id: str = ""
    baseline_snapshot_id: str = ""
    current_snapshot_id: str = ""
    execution_basis: str = ""
    data_changes: Tuple[DiffEntry, ...] = ()
    config_changes: ConfigChangeSet = field(default_factory=ConfigChangeSet)
    impact_inputs: Tuple[Tuple[str, ...], ...] = ()
    n_added: int = 0
    n_changed: int = 0
    n_disappeared: int = 0
    n_scope_changed: int = 0
    created_at: str = ""
    diff_hash: str = ""

    def __post_init__(self) -> None:
        if not self.diff_id:
            raise DomainValidationError("SnapshotDiff.diff_id is required")
        if not self.project_id:
            raise DomainValidationError("project_id is required")
        if self.execution_basis not in ("full", "incremental"):
            raise DomainValidationError(
                f"execution_basis {self.execution_basis!r} invalid")
        data_changes = tuple(self.data_changes)
        if any(type(entry) is not DiffEntry for entry in data_changes):
            raise DomainValidationError("SnapshotDiff requires DiffEntry records")
        data_changes = tuple(sorted(
            data_changes,
            key=lambda entry: (entry.kind, entry.entry_id, entry.entry_hash),
        ))
        if type(self.config_changes) is not ConfigChangeSet:
            raise DomainValidationError("SnapshotDiff.config_changes must be ConfigChangeSet")
        impact_inputs = tuple(sorted(tuple(item) for item in self.impact_inputs))
        object.__setattr__(self, "data_changes", data_changes)
        object.__setattr__(self, "impact_inputs", impact_inputs)
        n_added = sum(1 for e in self.data_changes if e.kind == DiffEntryKind.ADD)
        n_changed = sum(1 for e in self.data_changes if e.kind == DiffEntryKind.CHANGE)
        n_disappeared = sum(1 for e in self.data_changes if e.kind == DiffEntryKind.DISAPPEAR)
        n_scope_changed = sum(1 for e in self.data_changes if e.kind == DiffEntryKind.SCOPE_CHANGE)
        object.__setattr__(self, "n_added", n_added)
        object.__setattr__(self, "n_changed", n_changed)
        object.__setattr__(self, "n_disappeared", n_disappeared)
        object.__setattr__(self, "n_scope_changed", n_scope_changed)
        expected = self.compute_hash()
        if self.diff_hash and self.diff_hash != expected:
            raise DomainValidationError("diff_hash mismatch")
        object.__setattr__(self, "diff_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "diff_id": self.diff_id,
            "project_id": self.project_id,
            "baseline_snapshot_id": self.baseline_snapshot_id,
            "current_snapshot_id": self.current_snapshot_id,
            "execution_basis": self.execution_basis,
            "data_change_hashes": [e.entry_hash for e in self.data_changes],
            "config_changes": self.config_changes.canonical_payload(),
            "impact_inputs": [list(t) for t in self.impact_inputs],
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())

    @property
    def has_data_changes(self) -> bool:
        return len(self.data_changes) > 0

    @property
    def has_config_changes(self) -> bool:
        return not self.config_changes.is_empty

    @property
    def has_disappearances_needing_scope_check(self) -> bool:
        return any(e.kind == DiffEntryKind.DISAPPEAR and e.needs_scope_check
                    for e in self.data_changes)


# ---------------------------------------------------------------------------
# Partial date / unknown value detection
# ---------------------------------------------------------------------------

_UNKNOWN_VALUES = frozenset({"", "UNK", "UNKNOWN", "N/A", "NOT DONE", None})
_DATE_YYYY = _re.compile(r"^\d{4}$")
_DATE_YYYY_MM = _re.compile(r"^\d{4}-\d{2}$")


def _is_partial_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if _DATE_YYYY.match(value):
        return True
    if _DATE_YYYY_MM.match(value):
        return True
    parts = value.split("-")
    if len(parts) >= 2:
        return any(p.upper() in ("UN", "UNK") for p in parts)
    return False


def _is_unknown_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.upper() in _UNKNOWN_VALUES:
        return True
    return False


def _is_unknown_key(value: Any) -> bool:
    """Case-insensitive check for unknown/empty key values."""
    if value is None:
        return True
    if isinstance(value, str):
        upper = value.upper()
        return upper in ("", "UN", "UNK", "UNKNOWN")
    return False


class DiffService:
    """Computes full and incremental diffs.

    VETO 2: requires real AcceptanceService and BaselineService; derives
    mapping provenance from the accepted binding; rejects empty key fields.
    """

    def diff_full(
        self, project_id: str,
        baseline_snapshot: ListingSnapshot, current_snapshot: ListingSnapshot,
        baseline_rows: List[Dict[str, Any]], current_rows: List[Dict[str, Any]],
        acceptance_service, *,
        record_key_fields: Tuple[str, ...] = ("subject",),
        config_changes: Optional[ConfigChangeSet] = None,
    ) -> SnapshotDiff:
        return self._compute_diff(
            project_id=project_id,
            baseline_snapshot=baseline_snapshot,
            current_snapshot=current_snapshot,
            baseline_rows=baseline_rows, current_rows=current_rows,
            execution_basis="full",
            acceptance_service=acceptance_service,
            baseline_service=None, data_baseline=None,
            record_key_fields=record_key_fields,
            config_changes=config_changes,
        )

    def diff_incremental(
        self, project_id: str,
        data_baseline, current_snapshot: ListingSnapshot,
        baseline_rows: List[Dict[str, Any]], current_rows: List[Dict[str, Any]],
        acceptance_service, baseline_service, *,
        record_key_fields: Tuple[str, ...] = ("subject",),
        config_changes: Optional[ConfigChangeSet] = None,
    ) -> SnapshotDiff:
        return self._compute_diff(
            project_id=project_id,
            baseline_snapshot=None,
            current_snapshot=current_snapshot,
            baseline_rows=baseline_rows, current_rows=current_rows,
            execution_basis="incremental",
            acceptance_service=acceptance_service,
            baseline_service=baseline_service, data_baseline=data_baseline,
            record_key_fields=record_key_fields,
            config_changes=config_changes,
        )

    def _compute_diff(
        self, project_id: str,
        baseline_snapshot: Optional[ListingSnapshot],
        current_snapshot: ListingSnapshot,
        baseline_rows: List[Dict[str, Any]],
        current_rows: List[Dict[str, Any]],
        execution_basis: str,
        acceptance_service, baseline_service, data_baseline,
        record_key_fields: Tuple[str, ...],
        config_changes: Optional[ConfigChangeSet],
    ) -> SnapshotDiff:
        from .acceptance import AcceptanceService, SnapshotAcceptanceState
        from .baselines import BaselineService, DataBaseline
        if type(acceptance_service) is not AcceptanceService:
            raise DiffError(
                "diff requires a real AcceptanceService instance; "
                "duck-typed substitutes are rejected"
            )
        if not record_key_fields:
            raise DiffError(
                "record_key_fields must be non-empty"
            )

        # Resolve baseline identity and rows.
        if execution_basis == "incremental":
            if type(baseline_service) is not BaselineService:
                raise DiffError(
                    "incremental diff requires a real BaselineService instance"
                )
            if data_baseline is None:
                raise DiffError("incremental diff requires a real DataBaseline")
            if type(data_baseline) is not DataBaseline:
                raise DiffError(
                    "incremental diff requires a service-issued DataBaseline"
                )
            # VETO 2: verify the baseline is registered in this BaselineService.
            if not baseline_service.has_baseline(data_baseline.baseline_id):
                raise DiffError(
                    f"DataBaseline {data_baseline.baseline_id!r} is not "
                    f"registered in the supplied BaselineService; fabricated "
                    f"or cross-service baselines are rejected"
                )
            # Verify the registered baseline matches.
            registered = baseline_service.get_baseline(data_baseline.baseline_id)
            if registered.baseline_hash != data_baseline.baseline_hash:
                raise DiffError(
                    f"DataBaseline baseline_hash mismatch; the supplied "
                    f"baseline does not match the registered one"
                )
            if registered != data_baseline:
                raise DiffError(
                    "the supplied DataBaseline does not exactly match the "
                    "registered service-issued baseline"
                )
            data_baseline = registered
            if registered.project_id != project_id:
                raise DiffError(
                    f"DataBaseline project_id {registered.project_id!r} does "
                    f"not match diff project_id {project_id!r}"
                )
            try:
                baseline_rec = acceptance_service.get(registered.snapshot_id)
                baseline_binding = acceptance_service.binding(registered.snapshot_id)
            except Exception as exc:
                raise DiffError(
                    "the registered DataBaseline snapshot is not present in "
                    "the live AcceptanceService"
                ) from exc
            if baseline_rec.blocked:
                raise DiffError("the registered DataBaseline snapshot is blocked")
            if baseline_rec.state != SnapshotAcceptanceState.BASELINE_ELIGIBLE:
                raise DiffError(
                    "the registered DataBaseline snapshot is no longer "
                    "baseline_eligible"
                )
            bound_baseline_snapshot = baseline_binding.snapshot
            if (
                bound_baseline_snapshot.project_id != registered.project_id
                or bound_baseline_snapshot.snapshot_id != registered.snapshot_id
                or bound_baseline_snapshot.content_hash != registered.snapshot_content_hash
                or bound_baseline_snapshot.content_digest != registered.snapshot_content_digest
                or bound_baseline_snapshot.revision_id != registered.source_revision_id
                or baseline_binding.identity_algorithm.digest
                != registered.identity_algorithm_digest
                or baseline_binding.mapping_version != registered.mapping_version
                or baseline_rec.evidence is None
                or baseline_rec.evidence.evidence_hash
                != registered.acceptance_evidence_hash
            ):
                raise DiffError(
                    "DataBaseline does not match the live acceptance binding"
                )
            baseline_snapshot_id = data_baseline.snapshot_id
            baseline_content_digest = data_baseline.snapshot_content_digest
            baseline_content_hash = data_baseline.snapshot_content_hash
        else:
            if baseline_snapshot is None:
                raise DiffError("full diff requires a baseline ListingSnapshot")
            self._verify_accepted(acceptance_service, baseline_snapshot, project_id)
            baseline_snapshot_id = baseline_snapshot.snapshot_id
            baseline_content_digest = baseline_snapshot.content_digest
            baseline_content_hash = baseline_snapshot.content_hash

        self._verify_accepted(acceptance_service, current_snapshot, project_id)

        # VETO 2-9: compare baseline snapshot content against the registered
        # binding for incremental; or against the baseline_snapshot for full.
        if execution_basis == "incremental":
            baseline_digest = content_hash(deep_freeze_json(baseline_rows))
            if baseline_digest != baseline_content_digest:
                raise DiffError(
                    "baseline_rows content digest does not match the data "
                    f"baseline content_digest"
                )
        else:
            if baseline_snapshot.project_id != project_id:
                raise DiffError("baseline snapshot project_id mismatch")
            baseline_digest = content_hash(deep_freeze_json(baseline_rows))
            if baseline_digest != baseline_content_digest:
                raise DiffError(
                    "baseline_rows content digest does not match the baseline "
                    f"snapshot content_digest"
                )
        if current_snapshot.project_id != project_id:
            raise DiffError("current snapshot project_id mismatch")
        current_digest = content_hash(deep_freeze_json(current_rows))
        if current_digest != current_snapshot.content_digest:
            raise DiffError(
                "current_rows content digest does not match the current "
                f"snapshot content_digest"
            )

        # VETO 2: derive canonical_field_map and mapping_ids from the accepted
        # snapshot binding's MappingDefinitions.
        binding = acceptance_service.binding(current_snapshot.snapshot_id)
        canonical_field_map: Dict[str, str] = {}
        mapping_ids: Dict[str, str] = {}
        for md in binding.mapping_definitions:
            canonical_field_map[md.source_field] = md.canonical_field
            mapping_ids[md.source_field] = md.mapping_id
            mapping_ids[md.canonical_field] = md.mapping_id

        # Scope change detection.
        baseline_fields = self._extract_field_set(baseline_rows)
        current_fields = self._extract_field_set(current_rows)
        entries: List[DiffEntry] = []
        if baseline_fields != current_fields:
            added_cols = current_fields - baseline_fields
            removed_cols = baseline_fields - current_fields
            dim_parts = []
            if added_cols:
                dim_parts.append(f"added:{sorted(added_cols)}")
            if removed_cols:
                dim_parts.append(f"removed:{sorted(removed_cols)}")
            entries.append(DiffEntry(
                entry_id=f"de-scope-{len(entries)}",
                kind=DiffEntryKind.SCOPE_CHANGE,
                record_key="",
                scope_dimension="; ".join(dim_parts),
                impact_domains=tuple(self._infer_impact_domains(
                    added_cols | removed_cols, canonical_field_map)),
                created_at=now_iso(),
            ))

        baseline_by_key = self._index_rows(baseline_rows, record_key_fields)
        current_by_key = self._index_rows(current_rows, record_key_fields)
        baseline_keys = set(baseline_by_key.keys())
        current_keys = set(current_by_key.keys())

        for key in sorted(current_keys - baseline_keys):
            row = current_by_key[key]
            entries.append(DiffEntry(
                entry_id=f"de-add-{key}", kind=DiffEntryKind.ADD,
                record_key=key, subject_ref=self._extract_subject(row),
                impact_domains=tuple(self._infer_impact_domains(
                    set(row.keys()), canonical_field_map)),
                created_at=now_iso(),
            ))
        for key in sorted(baseline_keys - current_keys):
            row = baseline_by_key[key]
            entries.append(DiffEntry(
                entry_id=f"de-dis-{key}", kind=DiffEntryKind.DISAPPEAR,
                record_key=key, subject_ref=self._extract_subject(row),
                needs_scope_check=True,
                impact_domains=tuple(self._infer_impact_domains(
                    set(row.keys()), canonical_field_map)),
                created_at=now_iso(),
            ))
        for key in sorted(baseline_keys & current_keys):
            old_row = baseline_by_key[key]
            new_row = current_by_key[key]
            field_changes = self._compute_field_changes(
                old_row, new_row, canonical_field_map, mapping_ids)
            if field_changes:
                entries.append(DiffEntry(
                    entry_id=f"de-chg-{key}", kind=DiffEntryKind.CHANGE,
                    record_key=key, subject_ref=self._extract_subject(new_row),
                    field_changes=tuple(field_changes),
                    impact_domains=tuple(self._infer_impact_domains(
                        {fc.canonical_field for fc in field_changes},
                        canonical_field_map)),
                    created_at=now_iso(),
                ))
        impact_inputs = self._compute_impact_inputs(entries, canonical_field_map)
        effective_config_changes = config_changes or ConfigChangeSet()
        diff_identity_payload = {
            "baseline": baseline_snapshot_id,
            "current": current_snapshot.snapshot_id,
            "basis": execution_basis,
            "entries": [entry.entry_hash for entry in entries],
            "config": effective_config_changes.canonical_payload(),
        }
        return SnapshotDiff(
            diff_id=f"diff-{content_hash(diff_identity_payload)[:16]}",
            project_id=project_id,
            baseline_snapshot_id=baseline_snapshot_id,
            current_snapshot_id=current_snapshot.snapshot_id,
            execution_basis=execution_basis,
            data_changes=tuple(entries),
            config_changes=effective_config_changes,
            impact_inputs=tuple(impact_inputs),
            created_at=now_iso(),
        )

    @staticmethod
    def _verify_accepted(acceptance_service, snapshot: ListingSnapshot, project_id: str) -> None:
        from .acceptance import SnapshotAcceptanceState
        if type(snapshot) is not ListingSnapshot:
            raise DiffError("diff requires a verified ListingSnapshot")
        try:
            rec = acceptance_service.get(snapshot.snapshot_id)
        except Exception as exc:
            raise DiffError(
                f"snapshot {snapshot.snapshot_id!r} is not registered in the "
                f"acceptance service: {exc}"
            ) from exc
        if rec.project_id != project_id:
            raise DiffError(
                f"acceptance record project_id mismatch for snapshot "
                f"{snapshot.snapshot_id!r}"
            )
        if rec.blocked:
            raise DiffError(
                f"snapshot {snapshot.snapshot_id!r} is blocked in the "
                f"acceptance service"
            )
        # VETO 2: compare content against binding.
        binding = acceptance_service.binding(snapshot.snapshot_id)
        bound_snap = binding.snapshot
        if snapshot.content_hash != bound_snap.content_hash:
            raise DiffError(
                f"snapshot content_hash does not match the registered "
                f"binding snapshot"
            )
        accepted_states = {
            SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
            SnapshotAcceptanceState.BASELINE_ELIGIBLE,
        }
        if rec.state not in accepted_states:
            raise DiffError(
                f"snapshot {snapshot.snapshot_id!r} is not accepted "
                f"(state={rec.state.value})"
            )

    @staticmethod
    def _extract_field_set(rows: List[Dict[str, Any]]) -> set:
        fields: set = set()
        for row in rows:
            fields.update(row.keys())
        return fields

    @staticmethod
    def _index_rows(rows: List[Dict[str, Any]], key_fields: Tuple[str, ...]) -> Dict[str, Dict[str, Any]]:
        indexed: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            key_parts = []
            for kf in key_fields:
                if kf not in row:
                    raise DiffError(
                        f"record key field {kf!r} is missing from a row"
                    )
                val = row[kf]
                if _is_unknown_key(val):
                    raise DiffError(
                        f"record key field {kf!r} has an unknown/empty value"
                    )
                key_parts.append(f"{kf}={val}")
            key = "|".join(key_parts)
            if key in indexed:
                raise DiffError(f"duplicate record key {key!r}")
            indexed[key] = row
        return indexed

    @staticmethod
    def _extract_subject(row: Dict[str, Any]) -> str:
        for key in ("subject", "subject_ref", "sub", "USUBJID"):
            if key in row:
                return str(row[key])
        return ""

    def _compute_field_changes(
        self, old_row: Dict[str, Any], new_row: Dict[str, Any],
        canonical_field_map: Dict[str, str], mapping_ids: Dict[str, str],
    ) -> List[FieldChange]:
        changes: List[FieldChange] = []
        all_fields = sorted(set(old_row.keys()) | set(new_row.keys()))
        for field_name in all_fields:
            old_val = old_row.get(field_name)
            new_val = new_row.get(field_name)
            if old_val == new_val:
                continue
            # VETO 2: derive canonical field and mapping_id from the accepted
            # binding.  Unmapped fields get an explicit UNMAPPED marker and
            # is_unknown_field=True.
            canonical = canonical_field_map.get(field_name)
            mid = mapping_ids.get(field_name, "")
            if canonical is None:
                canonical = f"UNMAPPED:{field_name}"
                mid = "UNMAPPED"
            is_partial = _is_partial_date(old_val) or _is_partial_date(new_val)
            is_unknown = _is_unknown_value(old_val) or _is_unknown_value(new_val)
            if mid == "UNMAPPED":
                is_unknown = True
            changes.append(FieldChange(
                canonical_field=canonical, old_value=old_val, new_value=new_val,
                mapping_id=mid, is_partial_date=is_partial,
                is_unknown_field=is_unknown,
            ))
        return changes

    @staticmethod
    def _infer_impact_domains(field_names: set, canonical_field_map: Dict[str, str]) -> List[str]:
        domains: set = set()
        domain_hints = {
            "ae": {"ae", "aeterm", "ae_term", "aesev", "aeser"},
            "mh": {"mh", "mhterm", "mh_term"},
            "cm": {"cm", "cmdecod", "cm_indication", "cmindc"},
            "lab": {"lab", "lbtest", "lbstresn", "lab_value"},
            "visit": {"visit", "visitday", "svstdtc"},
            "efficacy": {"efficacy", "response", "outcome"},
        }
        for field_name in field_names:
            canonical = canonical_field_map.get(field_name, field_name)
            lower = canonical.lower()
            for domain, hints in domain_hints.items():
                if lower in hints or any(h in lower for h in hints):
                    domains.add(domain)
                    break
        return sorted(domains) if domains else ["unspecified"]

    def _compute_impact_inputs(
        self, entries: List[DiffEntry], canonical_field_map: Dict[str, str],
    ) -> List[Tuple[str, ...]]:
        inputs: set = set()
        for entry in entries:
            if entry.kind == DiffEntryKind.SCOPE_CHANGE:
                continue
            for domain in entry.impact_domains:
                if entry.field_changes:
                    for fc in entry.field_changes:
                        inputs.add((entry.subject_ref, domain, fc.canonical_field))
                else:
                    inputs.add((entry.subject_ref, domain, ""))
        return sorted(inputs)
