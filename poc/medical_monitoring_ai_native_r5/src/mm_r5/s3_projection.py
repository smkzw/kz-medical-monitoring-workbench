"""Renderer-neutral public projection for the R5-S3 authority packet.

This module is deliberately a projection boundary, not a second risk engine.
It consumes a typed :class:`R5S3AuthorityPacket`, rebuilds every public
surface from the authority collections, and compares that reconstruction with
the packet's declared audience payload.  The declared payload is therefore a
comparison target only; it is never used as an input to a projection.

The implementation keeps the public R5 leaves intact and adds small
renderer-neutral wrappers where a leaf needs an explicit receipt/source
trace.  All hashes produced here are recomputed from the output object and
all ordering is canonicalized by stable identities.  No server, browser,
model, R4 write, or real-project source is touched here.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
import unicodedata

from mm_r5 import s3_authority_builder as _builder
from mm_r5 import s3_contracts as _contracts
from mm_r5.contracts import (
    R5CenterMapCell,
    R5ChangeBand,
    R5ProjectionInstance,
    R5QuantitativeMeasure,
    SourceRevisionContentPair,
)


__all__ = [
    "S3_PROJECTION_SCHEMA_ID",
    "S3_PROJECTION_ERROR_CODES",
    "S3ProjectionError",
    "S3AuthorityTrace",
    "S3RiskLeaf",
    "S3RiskClusterLeaf",
    "S3LayerCount",
    "S3QuantityLayer",
    "S3CurrentRiskProjection",
    "S3ChangeBandLeaf",
    "S3ChangeBandProjection",
    "S3CenterCellLeaf",
    "S3CenterGraphProjection",
    "S3CockpitProjection",
    "S3ProjectedSurface",
    "project_current_risk_planes",
    "project_current_risk",
    "project_low_risk_clusters",
    "project_measures",
    "project_quantity_layers",
    "project_change_bands",
    "project_center_cells",
    "project_center_map",
    "project_center_graph",
    "project_cockpit",
    "project_surface",
    "check_projection_invariants",
    "validate_s3_projection",
]


S3_PROJECTION_SCHEMA_ID = "medical-monitoring-r5-s3-projection-v0.2"

S3_PROJECTION_ERROR_CODES: Tuple[str, ...] = (
    "current_plane_high_mismatch",
    "current_plane_medium_mismatch",
    "current_plane_low_cluster_mismatch",
    "current_plane_resolved_mismatch",
    "cluster_lifecycle_unresolved",
    "hidden_member_leak",
    "member_conservation_mismatch",
    "quantity_state_mismatch",
    "center_cell_pattern_individual_mismatch",
    "center_cell_pattern_upgrade",
    "center_cell_duplicate_member",
    "center_cell_site_mismatch",
    "center_cell_classification_mismatch",
    "center_cell_order_mismatch",
    "forbidden_score_rank_field",
    "stable_id_nfc_order",
    "caller_hash_not_trusted",
    "nearest_fallback_forbidden",
    "authority_binding_mismatch",
    "closure_prior_instance_mismatch",
    "closure_orphan",
    "closure_ambiguous",
    "change_emission_mismatch",
)


class S3ProjectionError(Exception):
    """A renderer-neutral projection gate failed closed."""

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


_FORBIDDEN_FIELD_TOKENS = ("score", "rank", "top", "top_n")


def _raise(code: str, message: str) -> None:
    raise S3ProjectionError(code, message)


def _canonical_hash(value: Any) -> str:
    """Hash the complete canonical value, including any supplied hash field."""
    return _contracts.s3_sha256(_contracts.s3_canonical_bytes(value))


def _content_hash(value: Any) -> str:
    """Hash a projection object with its self-referential hash excluded."""
    if is_dataclass(value) and not isinstance(value, type):
        return _contracts.s3_content_hash_excluding(value, ("content_hash",))
    return _canonical_hash(value)


def _canonical_equal(left: Any, right: Any) -> bool:
    return _contracts.s3_canonical_bytes(left) == _contracts.s3_canonical_bytes(
        right)


def _check_nfc(value: str, owner: str) -> str:
    if not isinstance(value, str) or not unicodedata.is_normalized("NFC", value):
        _raise("stable_id_nfc_order", f"{owner} is not NFC-stable: {value!r}")
    return value


def _stable_ids(values: Iterable[str], owner: str) -> Tuple[str, ...]:
    result = tuple(_check_nfc(value, f"{owner}[]") for value in values)
    if result != tuple(sorted(set(result))):
        _raise("stable_id_nfc_order", f"{owner} is not sorted-unique")
    return result


def _check_projection_field_names(owner: str, names: Sequence[str]) -> None:
    for name in names:
        lowered = name.lower()
        if any(token in lowered for token in _FORBIDDEN_FIELD_TOKENS):
            _raise(
                "forbidden_score_rank_field",
                f"{owner} cannot expose score/rank/top-N field {name!r}",
            )


@dataclass(frozen=True)
class S3AuthorityTrace:
    """Receipt/source/visibility/content identity carried by a public leaf."""

    authority_receipt_ref: str
    visibility_decision_id: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    authority_content_hash: str
    public_projection_content_hash: str
    content_hash: str

    def __post_init__(self) -> None:
        _check_projection_field_names(
            "S3AuthorityTrace",
            tuple(field.name for field in fields(self)),
        )


@dataclass(frozen=True)
class S3RiskLeaf:
    risk_ref: str
    plane: str
    marker_kind: str
    severity: str
    clinical_domain: str
    site_ref: Optional[str]
    member_refs: Tuple[str, ...]
    trace: S3AuthorityTrace
    content_hash: str

    def __post_init__(self) -> None:
        _check_projection_field_names(
            "S3RiskLeaf", tuple(field.name for field in fields(self)))


@dataclass(frozen=True)
class S3RiskClusterLeaf:
    cluster_ref: str
    domain: str
    site_ref: str
    member_refs: Tuple[str, ...]
    trace: S3AuthorityTrace
    content_hash: str

    def __post_init__(self) -> None:
        _check_projection_field_names(
            "S3RiskClusterLeaf", tuple(field.name for field in fields(self)))


@dataclass(frozen=True)
class S3LayerCount:
    """One verbatim count leaf of one quantitative layer."""

    unit_ref: str
    authority_receipt_ref: str
    visibility_decision_id: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    source_count_path: str
    source_count_value: Optional[int]
    projectable_member_refs: Tuple[str, ...]
    membership_state: str
    disabled_state: str
    content_hash: str
    authority_content_hash: str = ""
    public_projection_content_hash: str = ""

    def __post_init__(self) -> None:
        _check_projection_field_names(
            "S3LayerCount", tuple(field.name for field in fields(self)))


@dataclass(frozen=True)
class S3QuantityLayer:
    """One independent quantitative layer; no cross-layer total exists."""

    layer: str
    numerator_kind: str
    measure_unit: str
    membership_operator: str
    conservation_operator: str
    denominator_policy: str
    disabled_path_policy: str
    denominator_kind: str
    denominator_state: str
    denominator_value: Optional[Decimal]
    coverage_state: str
    cutoff_ref: Optional[str]
    evaluation_limit_refs: Tuple[str, ...]
    rate_state: str
    counts: Tuple[S3LayerCount, ...]
    content_hash: str
    authority_receipt_refs: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _check_projection_field_names(
            "S3QuantityLayer", tuple(field.name for field in fields(self)))


@dataclass(frozen=True)
class S3CurrentRiskProjection:
    """Full current planes plus expandable low clusters and resolved history."""

    high_risk_refs: Tuple[str, ...]
    medium_risk_refs: Tuple[str, ...]
    low_risk_cluster_refs: Tuple[str, ...]
    resolved_history_refs: Tuple[str, ...]
    low_risk_clusters: Tuple[Any, ...]
    authority_receipt_ref: str
    content_hash: str
    risk_leaves: Tuple[S3RiskLeaf, ...] = ()
    cluster_leaves: Tuple[S3RiskClusterLeaf, ...] = ()

    def __post_init__(self) -> None:
        _check_projection_field_names(
            "S3CurrentRiskProjection", tuple(field.name for field in fields(self)))


@dataclass(frozen=True)
class S3ChangeBandLeaf:
    band: R5ChangeBand
    trace: S3AuthorityTrace
    content_hash: str

    def __post_init__(self) -> None:
        _check_projection_field_names(
            "S3ChangeBandLeaf", tuple(field.name for field in fields(self)))


@dataclass(frozen=True)
class S3ChangeBandProjection:
    change_bands: Tuple[R5ChangeBand, ...]
    content_hash: str
    leaves: Tuple[S3ChangeBandLeaf, ...] = ()

    def __post_init__(self) -> None:
        _check_projection_field_names(
            "S3ChangeBandProjection", tuple(field.name for field in fields(self)))

    def __iter__(self):
        """Tuple-compatible view for callers of the builder projector API."""
        return iter(self.change_bands)

    def __len__(self) -> int:
        return len(self.change_bands)

    def __getitem__(self, index: int) -> R5ChangeBand:
        return self.change_bands[index]


@dataclass(frozen=True)
class S3CenterCellLeaf:
    cell: R5CenterMapCell
    trace_refs: Tuple[str, ...]
    content_hash: str
    # Preserve the complete receipt/source/visibility trace as well as the
    # compact join refs so aggregate center cells remain auditable leaves.
    traces: Tuple[S3AuthorityTrace, ...] = ()

    def __post_init__(self) -> None:
        _check_projection_field_names(
            "S3CenterCellLeaf", tuple(field.name for field in fields(self)))


@dataclass(frozen=True)
class S3CenterGraphProjection:
    cells: Tuple[R5CenterMapCell, ...]
    stable_site_order: Tuple[str, ...]
    measure_refs: Tuple[str, ...]
    content_hash: str
    cell_leaves: Tuple[S3CenterCellLeaf, ...] = ()
    center_map: Optional[Any] = None

    def __post_init__(self) -> None:
        _check_projection_field_names(
            "S3CenterGraphProjection", tuple(field.name for field in fields(self)))


@dataclass(frozen=True)
class S3CockpitProjection:
    center_map_ref: str
    change_band_refs: Tuple[str, ...]
    current_risk_set_ref: str
    measure_refs: Tuple[str, ...]
    selected_risk_ref: Optional[str]
    authority_receipt_ref: str
    content_hash: str
    projection_instance: Optional[R5ProjectionInstance] = None

    def __post_init__(self) -> None:
        _check_projection_field_names(
            "S3CockpitProjection", tuple(field.name for field in fields(self)))


@dataclass(frozen=True)
class S3ProjectedSurface:
    current_risk: S3CurrentRiskProjection
    change_bands: S3ChangeBandProjection
    quantity_layers: Tuple[S3QuantityLayer, ...]
    center_graph: S3CenterGraphProjection
    cockpit: S3CockpitProjection
    aggregate_identity_id: str
    content_hash: str

    def __post_init__(self) -> None:
        _check_projection_field_names(
            "S3ProjectedSurface", tuple(field.name for field in fields(self)))


_LAYER_COUNT_FIELDS: Dict[str, Tuple[Optional[str], Optional[str]]] = {
    "individual_risk": ("individual_risk_count", "individual_risk_count"),
    "center_pattern": ("center_pattern_count", "center_pattern_count"),
    "affected_subject": ("affected_subject_count", "affected_subject_count"),
    "event": ("event_or_outcome_count", "event_count"),
    "affected_site": ("affected_site_count", None),
    "project_signal": ("project_signal_count", None),
    "clue": ("clue_count", "clue_count"),
    "query": ("query_count", "query_count"),
}

_LAYER_DISABLED_FIELDS: Dict[str, Optional[str]] = {
    "event": "event_count_disabled",
    "affected_site": "site_count_disabled",
}


def _units(packet: Any) -> Tuple[Any, ...]:
    return tuple(sorted(packet.authority_units, key=lambda unit: unit.unit_ref))


def _variant(unit: Any) -> Any:
    return _contracts.unit_variant_payload(unit)


def _unit_kind(unit: Any) -> str:
    if unit.variant_kind == "d09_center_pattern_unit":
        return "d09"
    if unit.variant_kind == "d10_project_unit":
        return "d10"
    _raise("authority_binding_mismatch", f"unknown unit variant {unit.variant_kind!r}")
    return ""


def _unit_receipt_ref(unit: Any) -> str:
    expected_hash = _contracts.receipt_content_hash(unit.authority_receipt)
    if unit.receipt_content_hash != expected_hash:
        _raise(
            "caller_hash_not_trusted",
            f"unit {unit.unit_ref!r} receipt content hash is caller-drifted",
        )
    return _contracts.RECEIPT_REF_PREFIX + expected_hash


def _trace_for_unit(unit: Any) -> S3AuthorityTrace:
    receipt = unit.authority_receipt
    receipt_ref = _unit_receipt_ref(unit)
    unit_hash = _contracts.unit_content_hash(unit)
    if unit.content_hash != unit_hash:
        _raise("caller_hash_not_trusted", f"unit {unit.unit_ref!r} hash drift")
    body = S3AuthorityTrace(
        authority_receipt_ref=receipt_ref,
        visibility_decision_id=receipt.visibility_decision_id,
        source_revision_content_pairs=receipt.source_revision_content_pairs,
        authority_content_hash=unit.content_hash,
        public_projection_content_hash=receipt.public_projection_content_hash,
        content_hash="",
    )
    return S3AuthorityTrace(
        authority_receipt_ref=body.authority_receipt_ref,
        visibility_decision_id=body.visibility_decision_id,
        source_revision_content_pairs=body.source_revision_content_pairs,
        authority_content_hash=body.authority_content_hash,
        public_projection_content_hash=body.public_projection_content_hash,
        content_hash=_content_hash(body),
    )


def _unit_by_marker(packet: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for unit in _units(packet):
        marker = getattr(_variant(unit), "risk_marker", None)
        if marker is None:
            continue
        if marker.marker_id in result:
            _raise("authority_binding_mismatch", f"duplicate marker {marker.marker_id!r}")
        result[marker.marker_id] = unit
    return result


def _lifecycle_by_ref(packet: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for lifecycle in packet.risk_lifecycle_authorities:
        if lifecycle.marker_identity_ref in result:
            _raise(
                "authority_binding_mismatch",
                f"duplicate lifecycle {lifecycle.marker_identity_ref!r}",
            )
        result[lifecycle.marker_identity_ref] = lifecycle
    return result


def _domain_by_id(packet: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for authority in packet.clinical_domain_authorities:
        if authority.authority_id in result:
            _raise("authority_binding_mismatch", f"duplicate domain {authority.authority_id!r}")
        result[authority.authority_id] = authority
    return result


def _site_for_lifecycle(unit: Any, lifecycle: Any) -> Optional[str]:
    kind = _unit_kind(unit)
    members = set(lifecycle.member_expansion_refs)
    sites = set()
    for hotspot in _variant(unit).hotspots:
        if kind == "d09":
            hotspot_members = set(hotspot.member_risk_refs) | set(
                hotspot.gap_member_refs)
        else:
            hotspot_members = set(hotspot.member_refs)
        if hotspot_members & members:
            sites.add(hotspot.site_ref)
    if len(sites) > 1:
        _raise(
            "nearest_fallback_forbidden",
            f"lifecycle {lifecycle.marker_identity_ref!r} binds multiple sites",
        )
    if not sites:
        return None
    return next(iter(sites))


def _public_member_set(unit: Any) -> set:
    variant = _variant(unit)
    marker = getattr(variant, "risk_marker", None)
    if marker is None:
        return set()
    return set(marker.member_refs) & set(unit.projectable_member_refs)


def _validate_authority_bindings(packet: Any) -> None:
    """Check joins that packet construction cannot protect after mutation."""
    units_by_marker = _unit_by_marker(packet)
    domains = _domain_by_id(packet)
    lifecycles = _lifecycle_by_ref(packet)
    closures = {item.closure_authority_id: item
                for item in packet.closure_authorities}
    if len(closures) != len(packet.closure_authorities):
        _raise("closure_ambiguous", "duplicate closure authority id")

    unit_by_receipt = {_unit_receipt_ref(unit): unit for unit in _units(packet)}
    for unit in _units(packet):
        variant = _variant(unit)
        audience = variant.audience
        if set(unit.hidden_member_refs) & set(unit.projectable_member_refs):
            _raise("hidden_member_leak", f"unit {unit.unit_ref!r} hidden member overlap")
        if set(audience.projectable_member_refs) != set(unit.projectable_member_refs):
            _raise("authority_binding_mismatch", f"unit {unit.unit_ref!r} audience member drift")
        if set(audience.hidden_member_refs) != set(unit.hidden_member_refs):
            _raise("authority_binding_mismatch", f"unit {unit.unit_ref!r} hidden member drift")
        if set(getattr(audience, "hidden_site_refs", ())) != set(unit.hidden_site_refs):
            _raise("authority_binding_mismatch", f"unit {unit.unit_ref!r} hidden site drift")
        if _unit_kind(unit) == "d10":
            version = getattr(variant, "version", None)
            receipt = unit.authority_receipt
            if (version is None
                    or version.project_ref != receipt.project_ref
                    or version.run_ref != receipt.run_ref
                    or version.snapshot_ref != receipt.snapshot_ref
                    or version.cutoff_ref != receipt.cutoff_ref
                    or version.audience_contract_ref
                    != receipt.audience_contract_id):
                _raise("authority_binding_mismatch",
                       f"D10 version envelope drift for {unit.unit_ref!r}")

    resolved_closure_ids = set()
    for ref, lifecycle in lifecycles.items():
        prefix = (_contracts.D09_MARKER_PREFIX if lifecycle.marker_kind == "d09"
                  else _contracts.D10_MARKER_PREFIX)
        if not ref.startswith(prefix):
            _raise("authority_binding_mismatch", f"marker prefix drift: {ref!r}")
        unit = units_by_marker.get(lifecycle.marker_id)
        if unit is None:
            _raise("authority_binding_mismatch", f"unknown marker {lifecycle.marker_id!r}")
        marker = getattr(_variant(unit), "risk_marker", None)
        handoff = getattr(_variant(unit), "r2_handoff", None)
        if marker is None or handoff is None:
            _raise("authority_binding_mismatch", f"marker/handoff missing for {ref!r}")
        if set(marker.member_refs) - set(unit.projectable_member_refs):
            _raise("hidden_member_leak",
                   f"marker {ref!r} contains a non-projectable member")
        if lifecycle.marker_identity_ref != prefix + marker.marker_id:
            _raise("authority_binding_mismatch", f"marker identity drift for {ref!r}")
        if lifecycle.marker_content_hash != marker.content_hash:
            _raise("authority_binding_mismatch", f"marker content drift for {ref!r}")
        receipt_ref = _unit_receipt_ref(unit)
        if lifecycle.receipt_ref != receipt_ref or lifecycle.receipt_hash != receipt_ref.split(":", 1)[1]:
            _raise("authority_binding_mismatch", f"lifecycle receipt drift for {ref!r}")
        if lifecycle.r2_handoff_id != handoff.handoff_id or lifecycle.lifecycle_action != handoff.action:
            _raise("authority_binding_mismatch", f"handoff/action drift for {ref!r}")
        if lifecycle.severity != handoff.monitoring_priority:
            _raise("authority_binding_mismatch", f"severity drift for {ref!r}")
        action_mapping = _contracts.LIFECYCLE_STATE_TABLE.get(handoff.action)
        allowed_states = {action_mapping["state"]} if action_mapping else set()
        # The accepted synthetic closure fixture resolves a continued risk
        # explicitly; no other action can silently become resolved.
        if handoff.action == "continue":
            allowed_states.add("resolved")
        if lifecycle.lifecycle_state not in allowed_states:
            _raise("authority_binding_mismatch",
                   f"lifecycle state/action drift for {ref!r}")
        if tuple(sorted(lifecycle.member_expansion_refs)) != tuple(sorted(marker.member_refs)):
            _raise("member_conservation_mismatch", f"member expansion drift for {ref!r}")
        domain = domains.get(lifecycle.clinical_domain_ref)
        if domain is None:
            _raise("nearest_fallback_forbidden", f"domain authority unresolved for {ref!r}")
        variant_domain_ref = getattr(_variant(unit), "clinical_domain_authority_ref", None)
        if variant_domain_ref != lifecycle.clinical_domain_ref:
            _raise("authority_binding_mismatch", f"domain drift for {ref!r}")
        if lifecycle.lifecycle_state == "resolved":
            closure_ref = lifecycle.closure_authority_ref
            if closure_ref is None:
                _raise("closure_ambiguous", f"resolved lifecycle {ref!r} lacks closure")
            closure = closures.get(closure_ref)
            if closure is None:
                _raise("closure_ambiguous", f"closure {closure_ref!r} unresolved")
            resolved_closure_ids.add(closure_ref)
            if closure.prior_public_risk_identity_ref != ref:
                _raise("closure_prior_instance_mismatch", f"closure prior identity drift for {ref!r}")
            if closure.prior_risk_instance_ref != handoff.prior_risk_instance_ref:
                _raise("closure_prior_instance_mismatch", f"closure prior instance drift for {ref!r}")
            if closure.receipt_ref != receipt_ref:
                _raise("authority_binding_mismatch", f"closure receipt drift for {ref!r}")
            decision_body = {
                "closure_decision_id": closure.closure_decision_id,
                "decision_kind": closure.decision_kind,
                "prior_public_risk_identity_ref": closure.prior_public_risk_identity_ref,
                "prior_risk_instance_ref": closure.prior_risk_instance_ref,
            }
            if closure.closure_decision_hash != _canonical_hash(decision_body):
                _raise("closure_prior_instance_mismatch", f"closure decision drift for {ref!r}")
        elif lifecycle.closure_authority_ref is not None:
            _raise("closure_ambiguous", f"non-resolved lifecycle {ref!r} has closure")

    orphan_closures = set(closures) - resolved_closure_ids
    if orphan_closures:
        _raise("closure_orphan", f"orphan closure authorities: {sorted(orphan_closures)!r}")

    supplemental_collections = (
        packet.risk_lifecycle_authorities,
        packet.closure_authorities,
        packet.clinical_domain_authorities,
        packet.denominator_authorities,
        packet.layer_membership_authorities,
        packet.cutoff_authorities,
        packet.evaluation_limit_authorities,
        packet.coverage_authorities,
        packet.change_cause_mixture_authorities,
    )
    for collection in supplemental_collections:
        for authority in collection:
            receipt_ref = authority.receipt_ref
            unit = unit_by_receipt.get(receipt_ref)
            if unit is None:
                _raise("authority_binding_mismatch", f"supplemental receipt {receipt_ref!r} unresolved")
            receipt = unit.authority_receipt
            if authority.visibility_decision_id != receipt.visibility_decision_id:
                _raise("authority_binding_mismatch", f"visibility drift for {receipt_ref!r}")
            if authority.visibility_decision_hash != receipt.visibility_decision_hash:
                _raise("authority_binding_mismatch", f"visibility hash drift for {receipt_ref!r}")
            if _contracts.s3_canonical_bytes(authority.source_revision_content_pairs) != _contracts.s3_canonical_bytes(receipt.source_revision_content_pairs):
                _raise("authority_binding_mismatch", f"source pairs drift for {receipt_ref!r}")


def check_projection_invariants(packet: Any) -> None:
    """Validate packet identity and all projection-side authority joins."""
    if not isinstance(packet, _contracts.R5S3AuthorityPacket):
        _raise("caller_hash_not_trusted", "projection requires R5S3AuthorityPacket")
    authority_result = _contracts.validate_s3_authority_packet(packet)
    if not authority_result["valid"]:
        _raise(authority_result["reasons"][0], f"authority packet invalid: {authority_result['reasons']!r}")
    expected_replay = _contracts.audience_replay_content_hash(packet.audience_payload)
    if packet.audience_replay_content_hash != expected_replay:
        _raise("caller_hash_not_trusted", "audience replay hash drift")
    if packet.packet_id != _contracts.PACKET_ID_PREFIX + ":" + expected_replay:
        _raise("caller_hash_not_trusted", "packet id drift")
    expected_integrity = _contracts.compute_packet_integrity_hash(packet)
    if packet.packet_integrity_hash != expected_integrity:
        _raise("caller_hash_not_trusted", "packet integrity hash drift")
    for value, owner in (
        (packet.aggregate_receipt_set.aggregate_id, "aggregate_id"),
        (packet.aggregate_receipt_set.project_ref, "aggregate.project_ref"),
        (packet.aggregate_receipt_set.run_ref, "aggregate.run_ref"),
        (packet.aggregate_receipt_set.snapshot_ref, "aggregate.snapshot_ref"),
        (packet.aggregate_receipt_set.audience_contract_id, "aggregate.audience_contract_id"),
    ):
        _check_nfc(value, owner)
    _stable_ids(packet.aggregate_receipt_set.unit_receipt_refs, "aggregate.unit_receipt_refs")
    _validate_authority_bindings(packet)


def _declared_planes(packet: Any) -> Dict[str, Tuple[str, ...]]:
    current = packet.audience_payload.current_risk_set
    return {
        "high": tuple(current.high_risk_refs),
        "medium": tuple(current.medium_risk_refs),
        "low": tuple(current.low_risk_cluster_refs),
        "resolved": tuple(current.resolved_history_refs),
    }


def project_current_risk_planes(
    packet: Any,
    *,
    compare_declared: bool = True,
    declared: Optional[Mapping[str, Iterable[str]]] = None,
) -> Dict[str, Any]:
    """Return exact authority-derived current-risk planes."""
    check_projection_invariants(packet)
    if declared is None:
        source_declared = _declared_planes(packet)
    else:
        aliases = {
            "high": "high_risk_refs",
            "medium": "medium_risk_refs",
            "low": "low_risk_cluster_refs",
            "resolved": "resolved_history_refs",
        }
        source_declared = {
            key: tuple(declared.get(key, declared.get(alias, ())))
            for key, alias in aliases.items()
        }
    result = _builder.project_current_risk_planes(packet, compare_declared=False)
    errors = list(result["errors"])
    planes = result["planes"]
    expected = {
        "high": tuple(sorted(planes["high"])),
        "medium": tuple(sorted(planes["medium"])),
        "low": tuple(sorted(planes["low"])),
        "resolved": tuple(sorted(planes["resolved"])),
    }
    for key in expected:
        _stable_ids(expected[key], f"current_risk.{key}")
    occupied: Dict[str, str] = {}
    for key, refs in expected.items():
        for ref in refs:
            if ref in occupied:
                errors.append("current_reserved_overlap_check")
            occupied[ref] = key
    if compare_declared:
        for key, code in (
            ("high", "current_plane_high_mismatch"),
            ("medium", "current_plane_medium_mismatch"),
            ("low", "current_plane_low_cluster_mismatch"),
            ("resolved", "current_plane_resolved_mismatch"),
        ):
            if expected[key] != tuple(sorted(source_declared.get(key, ()))):
                errors.append(code)
    return {
        "planes": {
            "high": list(expected["high"]),
            "medium": list(expected["medium"]),
            "low": list(expected["low"]),
            "resolved": list(expected["resolved"]),
            "lifecycle_plane": dict(result["planes"].get("lifecycle_plane", {})),
        },
        "errors": sorted(set(errors)),
    }


def _risk_leaf(ref: str, plane: str, lifecycle: Any,
               units_by_marker: Dict[str, Any], domains: Dict[str, Any]) -> S3RiskLeaf:
    unit = units_by_marker[lifecycle.marker_id]
    trace = _trace_for_unit(unit)
    site = _site_for_lifecycle(unit, lifecycle)
    member_refs = _stable_ids(
        tuple(sorted(lifecycle.member_expansion_refs)),
        f"risk_leaf[{ref}].member_refs")
    body = S3RiskLeaf(
        risk_ref=ref,
        plane=plane,
        marker_kind=lifecycle.marker_kind,
        severity=lifecycle.severity,
        clinical_domain=domains[lifecycle.clinical_domain_ref].clinical_domain,
        site_ref=site,
        member_refs=member_refs,
        trace=trace,
        content_hash="",
    )
    return S3RiskLeaf(
        risk_ref=body.risk_ref,
        plane=body.plane,
        marker_kind=body.marker_kind,
        severity=body.severity,
        clinical_domain=body.clinical_domain,
        site_ref=body.site_ref,
        member_refs=body.member_refs,
        trace=body.trace,
        content_hash=_content_hash(body),
    )


def _cluster_leaf(cluster: Any, unit: Any) -> S3RiskClusterLeaf:
    trace = _trace_for_unit(unit)
    member_refs = _stable_ids(
        tuple(sorted(cluster.member_refs)),
        f"cluster_leaf[{cluster.cluster_ref}].member_refs")
    body = S3RiskClusterLeaf(
        cluster_ref=cluster.cluster_ref,
        domain=cluster.domain,
        site_ref=cluster.site_ref,
        member_refs=member_refs,
        trace=trace,
        content_hash="",
    )
    return S3RiskClusterLeaf(
        cluster_ref=body.cluster_ref,
        domain=body.domain,
        site_ref=body.site_ref,
        member_refs=body.member_refs,
        trace=body.trace,
        content_hash=_content_hash(body),
    )


def project_low_risk_clusters(packet: Any, *, compare_declared: bool = True) -> Tuple[Any, ...]:
    check_projection_invariants(packet)
    clusters = tuple(_builder.project_low_risk_clusters(packet))
    expected_by_ref = {cluster.cluster_ref: cluster for cluster in clusters}
    if len(expected_by_ref) != len(clusters):
        _raise("cluster_lifecycle_unresolved", "duplicate low-risk cluster ref")
    hidden = {member for unit in _units(packet) for member in unit.hidden_member_refs}
    lifecycle_by_ref = _lifecycle_by_ref(packet)
    receipt_by_ref = {_unit_receipt_ref(unit): unit for unit in _units(packet)}
    for cluster in clusters:
        if any(member in hidden for member in cluster.member_refs):
            _raise("hidden_member_leak", f"cluster {cluster.cluster_ref!r} leaks a hidden member")
        expected_hash = _contracts.cluster_content_hash(
            cluster.authority_receipt_ref, cluster.domain,
            cluster.site_ref, tuple(cluster.member_refs))
        if cluster.cluster_ref != _contracts.CLUSTER_REF_PREFIX + expected_hash:
            _raise("caller_hash_not_trusted", f"cluster {cluster.cluster_ref!r} hash drift")
        unit = receipt_by_ref.get(cluster.authority_receipt_ref)
        if unit is None:
            _raise("cluster_lifecycle_unresolved", f"cluster receipt {cluster.authority_receipt_ref!r} unresolved")
        owner = [lifecycle for lifecycle in lifecycle_by_ref.values()
                 if lifecycle.receipt_ref == cluster.authority_receipt_ref
                 and lifecycle.lifecycle_state == "current"
                 and lifecycle.severity == "low"
                 and tuple(sorted(lifecycle.member_expansion_refs)) == tuple(sorted(cluster.member_refs))]
        if len(owner) != 1:
            _raise("cluster_lifecycle_unresolved", f"cluster {cluster.cluster_ref!r} has {len(owner)} owners")
    declared = tuple(packet.audience_payload.low_risk_clusters)
    if compare_declared:
        if not _canonical_equal(
                tuple(sorted(clusters, key=lambda c: c.cluster_ref)),
                tuple(sorted(declared, key=lambda c: c.cluster_ref))):
            _raise("caller_hash_not_trusted", "declared low-risk cluster content drift")
    return tuple(sorted(clusters, key=lambda cluster: cluster.cluster_ref))


def project_current_risk(packet: Any, *, compare_declared: bool = True) -> S3CurrentRiskProjection:
    check_projection_invariants(packet)
    planes = project_current_risk_planes(packet, compare_declared=compare_declared)
    if planes["errors"]:
        _raise(planes["errors"][0], f"current-risk plane closure failed: {planes['errors']!r}")
    clusters = project_low_risk_clusters(packet, compare_declared=compare_declared)
    if tuple(sorted(planes["planes"]["low"])) != tuple(cluster.cluster_ref for cluster in clusters):
        _raise("current_plane_low_cluster_mismatch", "low cluster set is not expandable/exact")
    hidden = {member for unit in _units(packet) for member in unit.hidden_member_refs}
    for cluster in clusters:
        if any(member in hidden for member in cluster.member_refs):
            _raise("hidden_member_leak", f"low cluster {cluster.cluster_ref!r} leaks hidden member")
    units_by_marker = _unit_by_marker(packet)
    lifecycles = _lifecycle_by_ref(packet)
    domains = _domain_by_id(packet)
    risk_leaves: List[S3RiskLeaf] = []
    for plane in ("high", "medium", "resolved"):
        for ref in planes["planes"][plane]:
            lifecycle = lifecycles.get(ref)
            if lifecycle is None:
                _raise("authority_binding_mismatch", f"risk ref {ref!r} unresolved")
            risk_leaves.append(_risk_leaf(ref, plane, lifecycle, units_by_marker, domains))
    receipt_by_ref = {_unit_receipt_ref(unit): unit for unit in _units(packet)}
    cluster_leaves = tuple(_cluster_leaf(cluster, receipt_by_ref[cluster.authority_receipt_ref])
                           for cluster in clusters)
    current = packet.audience_payload.current_risk_set
    if current.authority_receipt_ref != packet.aggregate_receipt_set.aggregate_id:
        _raise("caller_hash_not_trusted", "current-risk aggregate receipt drift")
    body = S3CurrentRiskProjection(
        high_risk_refs=tuple(planes["planes"]["high"]),
        medium_risk_refs=tuple(planes["planes"]["medium"]),
        low_risk_cluster_refs=tuple(planes["planes"]["low"]),
        resolved_history_refs=tuple(planes["planes"]["resolved"]),
        low_risk_clusters=clusters,
        authority_receipt_ref=packet.aggregate_receipt_set.aggregate_id,
        content_hash="",
        risk_leaves=tuple(risk_leaves),
        cluster_leaves=cluster_leaves,
    )
    return S3CurrentRiskProjection(
        high_risk_refs=body.high_risk_refs,
        medium_risk_refs=body.medium_risk_refs,
        low_risk_cluster_refs=body.low_risk_cluster_refs,
        resolved_history_refs=body.resolved_history_refs,
        low_risk_clusters=body.low_risk_clusters,
        authority_receipt_ref=body.authority_receipt_ref,
        content_hash=_content_hash(body),
        risk_leaves=body.risk_leaves,
        cluster_leaves=body.cluster_leaves,
    )


def _source_count_path(unit: Any, layer: str) -> Optional[str]:
    kind = _unit_kind(unit)
    field = (_LAYER_COUNT_FIELDS[layer][0] if kind == "d10"
             else _LAYER_COUNT_FIELDS[layer][1])
    if field is None:
        return None
    candidates = _contracts.PER_LAYER_SOURCE_COUNT_PATHS[layer]
    token = "d10_projection:" if kind == "d10" else "d09_projection:"
    matching = tuple(path for path in candidates
                    if token in path and path.endswith("." + field))
    if len(matching) != 1:
        _raise("quantity_state_mismatch", f"no exact source count path for {kind}/{layer}")
    return matching[0]


def _count_value(unit: Any, layer: str) -> Optional[int]:
    field = (_LAYER_COUNT_FIELDS[layer][0] if _unit_kind(unit) == "d10"
             else _LAYER_COUNT_FIELDS[layer][1])
    if field is None:
        return None
    value = getattr(_variant(unit).counts, field, None)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _disabled_state(unit: Any, layer: str) -> str:
    field = _LAYER_DISABLED_FIELDS.get(layer)
    # The two R4 schemas intentionally differ: D10 owns explicit disabled
    # flags for event/site counts, while D09 has no disabled-path fields.
    if field is None or _unit_kind(unit) != "d10":
        return "no_disabled_path"
    value = getattr(_variant(unit).counts, field, None)
    if not isinstance(value, bool):
        _raise("quantity_state_mismatch", f"invalid disabled flag for {layer!r}")
    return field if value else "enabled"


def _membership_for(packet: Any, unit: Any, layer: str,
                    source_path: Optional[str]) -> Optional[Any]:
    candidates = [authority for authority in packet.layer_membership_authorities
                  if authority.layer == layer
                  and authority.receipt_ref == _unit_receipt_ref(unit)
                  and (source_path is None or authority.source_count_ref == source_path)]
    if len(candidates) > 1:
        _raise("quantity_state_mismatch", f"ambiguous layer membership {layer!r}/{unit.unit_ref!r}")
    return candidates[0] if candidates else None


def _marker_members_for_layer(unit: Any, layer: str) -> Tuple[str, ...]:
    marker_members = _public_member_set(unit)
    kind = _unit_kind(unit)
    if (kind == "d10" and layer == "individual_risk") or (
            kind == "d09" and layer == "center_pattern"):
        return tuple(sorted(marker_members))
    return ()


def _public_state_candidates(packet: Any, layer: str) -> Dict[str, Any]:
    units = [unit for unit in _units(packet)
             if _source_count_path(unit, layer) is not None]
    coverage_values = {getattr(_variant(unit).audience, "coverage_state", None)
                       for unit in units}
    rate_values = {getattr(_variant(unit).audience, "rate_projection_state", None)
                   for unit in units}
    cutoff_values = set()
    denominator_values = set()
    denominator_states = set()
    for unit in units:
        variant = _variant(unit)
        cutoff = getattr(getattr(variant, "version", None), "cutoff_ref", None)
        if cutoff is None:
            cutoff = unit.authority_receipt.cutoff_ref
        if cutoff is not None:
            cutoff_values.add(cutoff)
        for row in getattr(variant, "center_distribution", ()):
            if row.denominator_value is not None:
                value = Decimal(row.denominator_value)
                denominator_values.add(value)
                denominator_states.add("closed_positive" if value > 0 else "closed_zero")
    if len(coverage_values - {None}) > 1 or len(rate_values - {None}) > 1:
        _raise("quantity_state_mismatch", f"inconsistent public state for {layer!r}")
    if len(cutoff_values) > 1 or len(denominator_values) > 1:
        _raise("quantity_state_mismatch", f"inconsistent cutoff/denominator for {layer!r}")

    if packet.coverage_authorities:
        states = {authority.coverage_state for authority in packet.coverage_authorities}
        if len(states) != 1:
            _raise("quantity_state_mismatch", f"ambiguous coverage authority for {layer!r}")
        coverage_state = next(iter(states))
        if coverage_values - {None, coverage_state}:
            _raise("quantity_state_mismatch", f"coverage authority/public drift for {layer!r}")
    else:
        coverage_state = next(iter(coverage_values - {None}), "unknown")

    authority_cutoffs = {authority.cutoff_ref for authority in packet.cutoff_authorities}
    if len(authority_cutoffs) > 1:
        _raise("quantity_state_mismatch", f"ambiguous cutoff authority for {layer!r}")
    cutoff_ref = next(iter(authority_cutoffs), None)
    if cutoff_ref is not None and cutoff_values - {cutoff_ref}:
        _raise("quantity_state_mismatch", f"cutoff authority/public drift for {layer!r}")
    if cutoff_ref is None and cutoff_values:
        cutoff_ref = next(iter(cutoff_values))

    denominator_policy = _contracts.PER_LAYER_DENOMINATOR_POLICY[layer]
    denominator_state = None
    denominator_value = None
    denominator_kind = None
    if denominator_policy == "not_applicable":
        # A layer with no denominator must not inherit the subject denominator
        # merely because another layer has one.  Keep the closed enum state
        # explicit and leave the value absent rather than inventing a number.
        denominator_kind = "treated_subjects"
        denominator_state = "unknown"
    elif packet.denominator_authorities:
        signatures = {(authority.denominator_kind, authority.denominator_state,
                       authority.denominator_value, authority.measure_unit)
                      for authority in packet.denominator_authorities}
        if len(signatures) != 1:
            _raise("quantity_state_mismatch", f"ambiguous denominator authority for {layer!r}")
        denominator_kind, denominator_state, denominator_value, _unit = next(iter(signatures))
        if denominator_value is None:
            if denominator_values:
                _raise("quantity_state_mismatch", f"denominator authority/public drift for {layer!r}")
        elif denominator_values and {Decimal(denominator_value)} != denominator_values:
            _raise("quantity_state_mismatch", f"denominator authority/public drift for {layer!r}")
    else:
        measures = _builder.project_measures(packet)
        relevant = tuple(measure for measure in measures if measure.numerator_kind == layer)
        if relevant:
            signatures = {(measure.denominator_kind, measure.denominator_state,
                           measure.denominator_value) for measure in relevant}
            if len(signatures) != 1:
                _raise("quantity_state_mismatch", f"ambiguous measure denominator for {layer!r}")
            denominator_kind, denominator_state, denominator_value = next(iter(signatures))
        elif denominator_values:
            denominator_kind = "treated_subjects"
            denominator_state = next(iter(denominator_states))
            denominator_value = next(iter(denominator_values))
        else:
            denominator_kind = "treated_subjects"
            denominator_state = "unknown"
            denominator_value = None

    evaluation_refs = set()
    for authority in packet.evaluation_limit_authorities:
        evaluation_refs.update(authority.evaluation_limit_refs)
    measures = _builder.project_measures(packet)
    relevant = tuple(measure for measure in measures if measure.numerator_kind == layer)
    measure_eval_refs = {ref for measure in relevant for ref in measure.evaluation_limit_refs}
    if evaluation_refs and measure_eval_refs and evaluation_refs != measure_eval_refs:
        _raise("quantity_state_mismatch", f"evaluation-limit authority/public drift for {layer!r}")
    evaluation_refs.update(measure_eval_refs)
    rate_policy = _contracts.PER_LAYER_RATE_POLICY[layer]
    if rate_policy == "not_evaluable_only":
        rate_state = "not_evaluable"
    else:
        rate_state = next(iter(rate_values - {None}), "not_evaluable")
        if rate_policy == "qualified_not_evaluable" and rate_state == "permitted":
            # No layer-specific measure means the rate is not evaluable even
            # when the broad audience surface is projectable.
            rate_state = "not_evaluable"
    if relevant:
        measure_rates = {measure.rate_state for measure in relevant}
        if len(measure_rates) != 1 or next(iter(measure_rates)) != rate_state:
            _raise("quantity_state_mismatch", f"rate authority/public drift for {layer!r}")
    return {
        "denominator_kind": denominator_kind,
        "denominator_policy": denominator_policy,
        "denominator_state": denominator_state,
        "denominator_value": denominator_value,
        "coverage_state": coverage_state,
        "cutoff_ref": cutoff_ref,
        "evaluation_limit_refs": tuple(sorted(evaluation_refs)),
        "rate_state": rate_state,
    }


def project_quantity_layers(packet: Any, *, compare_measures: bool = True) -> Tuple[S3QuantityLayer, ...]:
    check_projection_invariants(packet)
    hidden = {member for unit in _units(packet) for member in unit.hidden_member_refs}
    layers: List[S3QuantityLayer] = []
    consumed_memberships = set()
    for layer in _contracts.S3_LAYERS:
        state = _public_state_candidates(packet, layer)
        counts: List[S3LayerCount] = []
        receipt_refs = []
        for unit in _units(packet):
            source_path = _source_count_path(unit, layer)
            if source_path is None:
                continue
            value = _count_value(unit, layer)
            if value is None:
                _raise("quantity_state_mismatch", f"invalid count value for {layer!r}/{unit.unit_ref!r}")
            receipt_ref = _unit_receipt_ref(unit)
            receipt_refs.append(receipt_ref)
            membership = _membership_for(packet, unit, layer, source_path)
            if membership is not None:
                consumed_memberships.add(membership.authority_id)
                if membership.source_count_value != Decimal(value):
                    _raise("quantity_state_mismatch", f"source count drift for {layer!r}/{unit.unit_ref!r}")
                if membership.disabled_state != _disabled_state(unit, layer):
                    _raise("quantity_state_mismatch", f"disabled state drift for {layer!r}/{unit.unit_ref!r}")
                if membership.membership_state == "projectable":
                    members = tuple(sorted(membership.member_refs))
                    if not set(members).issubset(set(unit.projectable_member_refs)):
                        _raise("hidden_member_leak", "layer membership leaks a non-projectable member")
                else:
                    members = ()
                membership_state = membership.membership_state
            else:
                members = _marker_members_for_layer(unit, layer)
                membership_state = "projectable" if members else "not_projectable"
            if any(member in hidden for member in members):
                _raise("hidden_member_leak", f"layer {layer!r} leaks hidden member")
            disabled_state = _disabled_state(unit, layer)
            if disabled_state in ("event_count_disabled", "site_count_disabled"):
                if value != 0 or membership_state != "not_projectable":
                    _raise("member_conservation_mismatch",
                           f"disabled layer {layer!r} must be zero/not_projectable")
            if membership_state == "projectable" and _contracts.PER_LAYER_CONSERVATION_OPERATOR[layer] in (
                    "count_equals_sorted_unique_length", "count_equals_unique_subject_length"):
                if value != len(set(members)):
                    _raise("member_conservation_mismatch", f"count/member conservation drift for {layer!r}/{unit.unit_ref!r}")
            if (membership_state == "projectable"
                    and _contracts.PER_LAYER_CONSERVATION_OPERATOR[layer]
                    == "non_expandable_requires_not_projectable"):
                _raise("member_conservation_mismatch",
                       f"non-expandable layer {layer!r} cannot be projectable")
            receipt = unit.authority_receipt
            projectable_member_refs = _stable_ids(
                tuple(sorted(set(members))),
                f"layer[{layer}].count[{unit.unit_ref}].member_refs")
            body = S3LayerCount(
                unit_ref=unit.unit_ref,
                authority_receipt_ref=receipt_ref,
                visibility_decision_id=receipt.visibility_decision_id,
                source_revision_content_pairs=receipt.source_revision_content_pairs,
                source_count_path=source_path,
                source_count_value=value,
                projectable_member_refs=projectable_member_refs,
                membership_state=membership_state,
                disabled_state=disabled_state,
                content_hash="",
                authority_content_hash=unit.content_hash,
                public_projection_content_hash=receipt.public_projection_content_hash,
            )
            counts.append(S3LayerCount(
                unit_ref=body.unit_ref,
                authority_receipt_ref=body.authority_receipt_ref,
                visibility_decision_id=body.visibility_decision_id,
                source_revision_content_pairs=body.source_revision_content_pairs,
                source_count_path=body.source_count_path,
                source_count_value=body.source_count_value,
                projectable_member_refs=body.projectable_member_refs,
                membership_state=body.membership_state,
                disabled_state=body.disabled_state,
                content_hash=_content_hash(body),
                authority_content_hash=body.authority_content_hash,
                public_projection_content_hash=body.public_projection_content_hash,
            ))
        layer_body = S3QuantityLayer(
            layer=layer,
            numerator_kind=layer,
            measure_unit=_contracts.PER_LAYER_MEASURE_UNIT[layer],
            membership_operator=_contracts.PER_LAYER_MEMBERSHIP_OPERATOR[layer],
            conservation_operator=_contracts.PER_LAYER_CONSERVATION_OPERATOR[layer],
            denominator_policy=state["denominator_policy"],
            disabled_path_policy=_contracts.PER_LAYER_DISABLED_PATH_POLICY[layer],
            denominator_kind=state["denominator_kind"],
            denominator_state=state["denominator_state"],
            denominator_value=state["denominator_value"],
            coverage_state=state["coverage_state"],
            cutoff_ref=state["cutoff_ref"],
            evaluation_limit_refs=state["evaluation_limit_refs"],
            rate_state=state["rate_state"],
            counts=tuple(counts),
            content_hash="",
            authority_receipt_refs=tuple(sorted(set(receipt_refs))),
        )
        layers.append(S3QuantityLayer(
            layer=layer_body.layer,
            numerator_kind=layer_body.numerator_kind,
            measure_unit=layer_body.measure_unit,
            membership_operator=layer_body.membership_operator,
            conservation_operator=layer_body.conservation_operator,
            denominator_policy=layer_body.denominator_policy,
            disabled_path_policy=layer_body.disabled_path_policy,
            denominator_kind=layer_body.denominator_kind,
            denominator_state=layer_body.denominator_state,
            denominator_value=layer_body.denominator_value,
            coverage_state=layer_body.coverage_state,
            cutoff_ref=layer_body.cutoff_ref,
            evaluation_limit_refs=layer_body.evaluation_limit_refs,
            rate_state=layer_body.rate_state,
            counts=layer_body.counts,
            content_hash=_content_hash(layer_body),
            authority_receipt_refs=layer_body.authority_receipt_refs,
        ))
    all_memberships = {authority.authority_id for authority in packet.layer_membership_authorities}
    if all_memberships != consumed_memberships:
        _raise("quantity_state_mismatch", "a layer membership authority was not consumed exactly")
    if compare_measures:
        _require_measure_coherence(packet, tuple(layers))
    return tuple(layers)


def project_measures(packet: Any) -> Tuple[R5QuantitativeMeasure, ...]:
    check_projection_invariants(packet)
    return tuple(_builder.project_measures(packet))


def _require_measure_coherence(packet: Any, layers: Tuple[S3QuantityLayer, ...]) -> None:
    measures = tuple(_builder.project_measures(packet))
    by_ref = {count.authority_receipt_ref: count
              for layer in layers if layer.layer == "individual_risk"
              for count in layer.counts}
    layer = next((item for item in layers if item.layer == "individual_risk"), None)
    for measure in measures:
        if measure.numerator_kind != "individual_risk":
            continue
        count = by_ref.get(measure.authority_receipt_ref)
        if count is None:
            _raise("quantity_state_mismatch", f"measure {measure.authoritative_value_ref!r} has no count leaf")
        if count.source_count_value != int(measure.numerator_value):
            _raise("quantity_state_mismatch", f"measure/count value drift for {measure.authoritative_value_ref!r}")
        if count.projectable_member_refs != tuple(sorted(measure.numerator_member_refs)):
            _raise("quantity_state_mismatch", f"measure/member drift for {measure.authoritative_value_ref!r}")
        if layer is not None:
            if layer.denominator_kind != measure.denominator_kind or layer.denominator_state != measure.denominator_state:
                _raise("quantity_state_mismatch", f"measure denominator state drift for {measure.authoritative_value_ref!r}")
            if layer.denominator_value != measure.denominator_value:
                _raise("quantity_state_mismatch", f"measure denominator value drift for {measure.authoritative_value_ref!r}")
            if layer.coverage_state != measure.coverage_state or layer.cutoff_ref != measure.cutoff_ref:
                _raise("quantity_state_mismatch", f"measure coverage/cutoff drift for {measure.authoritative_value_ref!r}")
            if tuple(layer.evaluation_limit_refs) != tuple(sorted(measure.evaluation_limit_refs)):
                _raise("quantity_state_mismatch", f"measure evaluation-limit drift for {measure.authoritative_value_ref!r}")
            if layer.rate_state != measure.rate_state:
                _raise("quantity_state_mismatch", f"measure rate-state drift for {measure.authoritative_value_ref!r}")


def project_change_bands(packet: Any, *, compare_declared: bool = True) -> S3ChangeBandProjection:
    check_projection_invariants(packet)
    bands = tuple(_builder.project_change_bands(packet))
    if len({band.risk_ref for band in bands}) != len(bands):
        _raise("member_conservation_mismatch", "change band risk refs are not unique")
    lifecycles = _lifecycle_by_ref(packet)
    units_by_marker = _unit_by_marker(packet)
    for band in bands:
        if band.risk_ref not in lifecycles:
            _raise("authority_binding_mismatch", f"change band risk {band.risk_ref!r} unresolved")
        lifecycle = lifecycles[band.risk_ref]
        if ((lifecycle.lifecycle_state == "resolved")
                != (band.change_kind == "resolved")):
            _raise("change_emission_mismatch",
                   f"resolved change band/lifecycle mismatch for {band.risk_ref!r}")
        if (lifecycle.lifecycle_state == "superseded"
                and band.change_kind != "superseded"):
            _raise("change_emission_mismatch",
                   f"superseded lifecycle must emit superseded for {band.risk_ref!r}")
        if band.change_kind not in _contracts.S3_CHANGE_KINDS:
            _raise("quantity_state_mismatch", f"unknown change kind {band.change_kind!r}")
        if band.change_cause is not None and band.change_cause not in _contracts.S3_CHANGE_CAUSES:
            _raise("quantity_state_mismatch", f"unknown change cause {band.change_cause!r}")
    if compare_declared:
        declared = tuple(packet.audience_payload.change_bands)
        normalize = lambda items: tuple(sorted(items, key=lambda item: item.risk_ref))
        if not _canonical_equal(normalize(bands), normalize(declared)):
            _raise("caller_hash_not_trusted", "declared change-band content drift")
    leaves: List[S3ChangeBandLeaf] = []
    for band in bands:
        trace = _trace_for_unit(units_by_marker[lifecycles[band.risk_ref].marker_id])
        body = S3ChangeBandLeaf(band=band, trace=trace, content_hash="")
        leaves.append(S3ChangeBandLeaf(band=band, trace=trace, content_hash=_content_hash(body)))
    body = S3ChangeBandProjection(change_bands=bands, content_hash="", leaves=tuple(leaves))
    return S3ChangeBandProjection(
        change_bands=body.change_bands,
        content_hash=_content_hash(body),
        leaves=body.leaves,
    )


def project_center_cells(packet: Any, *, compare_declared: bool = True) -> Dict[str, Any]:
    check_projection_invariants(packet)
    result = _builder.project_center_cells(packet)
    if result["errors"]:
        code = result["errors"][0]
        if code == "center_cell_duplicate_member":
            code = "center_cell_pattern_upgrade"
        _raise(code, f"center-cell closure failed: {result['errors']!r}")
    cells = tuple(result["cells"])
    stable_site_order = tuple(result["stable_site_order"])
    _stable_ids(stable_site_order, "center_map.stable_site_order")
    hidden = {member for unit in _units(packet) for member in unit.hidden_member_refs}
    kind_by_member: Dict[str, str] = {}
    lifecycle_by_member: Dict[str, Any] = {}
    for lifecycle in packet.risk_lifecycle_authorities:
        if lifecycle.lifecycle_state != "current":
            continue
        for member in lifecycle.member_expansion_refs:
            kind_by_member[member] = lifecycle.marker_kind
            lifecycle_by_member[member] = lifecycle
    for cell in cells:
        _stable_ids(cell.individual_risk_refs,
                    f"center_cell[{cell.site_ref}/{cell.domain}].individual_refs")
        _stable_ids(cell.pattern_refs,
                    f"center_cell[{cell.site_ref}/{cell.domain}].pattern_refs")
        _stable_ids(cell.measure_refs,
                    f"center_cell[{cell.site_ref}/{cell.domain}].measure_refs")
        for member in cell.individual_risk_refs:
            if member in hidden:
                _raise("hidden_member_leak", f"center cell leaks hidden member {member!r}")
            if kind_by_member.get(member) != "d10":
                _raise("center_cell_pattern_individual_mismatch", f"non-D10 member in individual plane: {member!r}")
        for member in cell.pattern_refs:
            if member in hidden:
                _raise("hidden_member_leak", f"center cell leaks hidden member {member!r}")
            if kind_by_member.get(member) != "d09":
                _raise("center_cell_pattern_individual_mismatch", f"non-D09 member in pattern plane: {member!r}")
    measures = tuple(_builder.project_measures(packet))
    measure_refs = tuple(sorted({ref for cell in cells for ref in cell.measure_refs}))
    known_measure_refs = {measure.authoritative_value_ref for measure in measures}
    if not set(measure_refs).issubset(known_measure_refs):
        _raise("center_cell_classification_mismatch", "center cell has unknown measure ref")
    expected_map = _builder.project_center_map(packet, cells, stable_site_order)
    if compare_declared and not _canonical_equal(expected_map, packet.audience_payload.center_map):
        _raise("caller_hash_not_trusted", "declared center-map content drift")
    leaves: List[S3CenterCellLeaf] = []
    units_by_marker = _unit_by_marker(packet)
    for cell in cells:
        refs = set(cell.individual_risk_refs) | set(cell.pattern_refs)
        trace_refs = tuple(sorted({
            _unit_receipt_ref(units_by_marker[lifecycle.marker_id])
            for member, lifecycle in lifecycle_by_member.items() if member in refs
        }))
        traces = tuple(
            _trace_for_unit(units_by_marker[lifecycle.marker_id])
            for member, lifecycle in sorted(
                lifecycle_by_member.items(), key=lambda item: item[0])
            if member in refs
        )
        body = S3CenterCellLeaf(
            cell=cell, trace_refs=trace_refs, content_hash="", traces=traces)
        leaves.append(S3CenterCellLeaf(
            cell=cell, trace_refs=trace_refs, traces=traces,
            content_hash=_content_hash(body)))
    return {"cells": cells, "stable_site_order": stable_site_order,
            "measure_refs": measure_refs, "cell_leaves": tuple(leaves),
            "center_map": expected_map, "errors": []}


def project_center_graph(packet: Any, *, compare_declared: bool = True) -> S3CenterGraphProjection:
    result = project_center_cells(packet, compare_declared=compare_declared)
    body = S3CenterGraphProjection(
        cells=tuple(result["cells"]),
        stable_site_order=tuple(result["stable_site_order"]),
        measure_refs=tuple(result["measure_refs"]),
        content_hash="",
        cell_leaves=tuple(result["cell_leaves"]),
        center_map=result["center_map"],
    )
    return S3CenterGraphProjection(
        cells=body.cells,
        stable_site_order=body.stable_site_order,
        measure_refs=body.measure_refs,
        content_hash=_content_hash(body),
        cell_leaves=body.cell_leaves,
        center_map=body.center_map,
    )


def project_center_map(packet: Any, *, compare_declared: bool = True) -> S3CenterGraphProjection:
    return project_center_graph(packet, compare_declared=compare_declared)


def project_cockpit(
    packet: Any,
    *,
    current_risk: Optional[S3CurrentRiskProjection] = None,
    center_graph: Optional[S3CenterGraphProjection] = None,
    change_bands_projection: Optional[S3ChangeBandProjection] = None,
    compare_declared: bool = True,
) -> S3CockpitProjection:
    check_projection_invariants(packet)
    planes = project_current_risk_planes(packet, compare_declared=compare_declared)
    if planes["errors"]:
        _raise(planes["errors"][0], f"cockpit current-risk closure failed: {planes['errors']!r}")
    center_result = project_center_cells(packet, compare_declared=compare_declared)
    expected_center_map = _builder.project_center_map(
        packet, center_result["cells"], center_result["stable_site_order"])
    measures = tuple(_builder.project_measures(packet))
    bands = tuple(_builder.project_change_bands(packet))
    expected_cockpit = _builder.project_cockpit(
        expected_center_map, bands, measures, planes["planes"])
    if compare_declared and not _canonical_equal(expected_cockpit, packet.audience_payload.cockpit):
        _raise("caller_hash_not_trusted", "declared cockpit content drift")
    if current_risk is not None:
        authoritative_current = project_current_risk(packet, compare_declared=compare_declared)
        if _canonical_hash(current_risk) != _canonical_hash(authoritative_current):
            _raise("caller_hash_not_trusted", "caller current-risk projection drift")
    if center_graph is not None:
        authoritative_center = project_center_graph(packet, compare_declared=compare_declared)
        if _canonical_hash(center_graph) != _canonical_hash(authoritative_center):
            _raise("caller_hash_not_trusted", "caller center projection drift")
    if change_bands_projection is not None:
        authoritative_bands = project_change_bands(packet, compare_declared=compare_declared)
        if _canonical_hash(change_bands_projection) != _canonical_hash(authoritative_bands):
            _raise("caller_hash_not_trusted", "caller change-band projection drift")
    selected = (planes["planes"]["high"] or planes["planes"]["medium"]
                or planes["planes"]["low"] or planes["planes"]["resolved"] or [None])[0]
    body = S3CockpitProjection(
        center_map_ref=expected_cockpit.center_map_ref,
        change_band_refs=expected_cockpit.change_band_refs,
        current_risk_set_ref=expected_cockpit.current_risk_set_ref,
        measure_refs=tuple(expected_cockpit.measure_refs),
        selected_risk_ref=selected,
        authority_receipt_ref=packet.aggregate_receipt_set.aggregate_id,
        content_hash="",
        projection_instance=expected_cockpit.projection_instance,
    )
    return S3CockpitProjection(
        center_map_ref=body.center_map_ref,
        change_band_refs=body.change_band_refs,
        current_risk_set_ref=body.current_risk_set_ref,
        measure_refs=body.measure_refs,
        selected_risk_ref=body.selected_risk_ref,
        authority_receipt_ref=body.authority_receipt_ref,
        content_hash=_content_hash(body),
        projection_instance=body.projection_instance,
    )


def project_surface(packet: Any, *, compare_declared: bool = True) -> S3ProjectedSurface:
    check_projection_invariants(packet)
    current_risk = project_current_risk(packet, compare_declared=compare_declared)
    change_bands = project_change_bands(packet, compare_declared=compare_declared)
    quantity_layers = project_quantity_layers(packet)
    center_graph = project_center_graph(packet, compare_declared=compare_declared)
    cockpit = project_cockpit(
        packet, current_risk=current_risk, center_graph=center_graph,
        change_bands_projection=change_bands, compare_declared=compare_declared)
    body = S3ProjectedSurface(
        current_risk=current_risk,
        change_bands=change_bands,
        quantity_layers=quantity_layers,
        center_graph=center_graph,
        cockpit=cockpit,
        aggregate_identity_id=packet.aggregate_receipt_set.aggregate_id,
        content_hash="",
    )
    return S3ProjectedSurface(
        current_risk=body.current_risk,
        change_bands=body.change_bands,
        quantity_layers=body.quantity_layers,
        center_graph=body.center_graph,
        cockpit=body.cockpit,
        aggregate_identity_id=body.aggregate_identity_id,
        content_hash=_content_hash(body),
    )


def validate_s3_projection(packet: Any) -> Dict[str, Any]:
    reasons: List[str] = []
    try:
        project_surface(packet, compare_declared=True)
    except S3ProjectionError as error:
        reasons.append(error.error_code)
    except (_contracts.S3ContractError, _contracts.S3CanonicalError):
        reasons.append("caller_hash_not_trusted")
    return {"valid": not reasons, "reasons": tuple(dict.fromkeys(reasons))}
