"""Focused W1 tests: exact keys, closed enums, immutability, deterministic
canonical hash and tamper rejection of the R5 typed contract surface.

The frozen machine authority ``exact_contract.json`` is read-only input to
these tests (never loaded by the runtime package).  The artifact's pinned
SHA is verified first so a drifted authority cannot silently change the
coverage assertions.
"""

from __future__ import annotations

import hashlib
import json
import typing
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

import mm_r5
from mm_r5 import canonical
from mm_r5.contracts import (
    DOMAINS,
    DOMAIN_ENCODING_ITEMS,
    FORBIDDEN_TERMS,
    LEGACY_TREATMENT_MAPPING_ITEMS,
    LEXICON_ITEMS,
    R5AEMHMatchHistory,
    R5AudienceEncodingRegistry,
    R5AudienceLexicon,
    R5AuthorityReceipt,
    R5CenterMapCell,
    R5CenterMapProjection,
    R5ChangeBand,
    R5ContractError,
    R5CurrentRiskSet,
    R5DeepLinkState,
    R5DomainEncodingItem,
    R5FilterState,
    R5HashMismatchError,
    R5JourneyEvent,
    R5JourneyTrack,
    R5LegacyTreatmentMappingItem,
    R5LexiconItem,
    R5PageState,
    R5PendingDateItem,
    R5ProjectCockpitProjection,
    R5ProjectionInstance,
    R5QuantitativeMeasure,
    R5ReturnContext,
    R5RiskAnchor,
    R5RiskInspectorProjection,
    R5ScrollState,
    R5SeverityLexiconItem,
    R5SortState,
    R5SubjectWorkspaceState,
    R5TemporalSpineProjection,
    R5VisitNode,
    R5_CONTRACT_SHA256,
    R5_EXACT_CONTRACT_ARTIFACT_SHA256,
    SEVERITIES,
    SEVERITY_LEXICON_ITEMS,
    SYMPTOM_EFFICACY_SUBTYPES,
    SourceRevisionContentPair,
    build_audience_encoding_registry,
    build_audience_lexicon,
    deferred_contract,
    deferred_fields_for,
    deferred_leaf_objects,
    enum_values,
    is_deferred_field,
    is_r5_object,
    known_object_names,
    legacy_severity_to_r5,
    severity_to_zh,
    validate_object,
    validate_severity_authority,
    zh_to_severity,
)

ARTIFACT = (Path(__file__).resolve().parents[3]
            / "artifacts" / "medical_monitoring_r5_contract_v0_3"
            / "exact_contract.json")

H64 = "a" * 64  # valid 64-hex sha256 shape
BAD_ENUM = "::invalid::"


# ---------------------------------------------------------------------------
# Frozen authority loading
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def exact() -> dict:
    assert ARTIFACT.is_file(), f"missing frozen authority: {ARTIFACT}"
    raw = ARTIFACT.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == R5_EXACT_CONTRACT_ARTIFACT_SHA256, (
        "exact_contract.json drifted from the S0 freeze")
    data = json.loads(raw)
    assert data["contract_sha256"] == R5_CONTRACT_SHA256, (
        "embedded contract SHA drifted from the S0 freeze")
    return data


# ---------------------------------------------------------------------------
# One valid instance per object (covers every field incl. deferred leaves)
# ---------------------------------------------------------------------------


def _pair(revision: str = "sr-1") -> SourceRevisionContentPair:
    return SourceRevisionContentPair(revision_id=revision, content_hash=H64)


def _projection_instance() -> R5ProjectionInstance:
    return R5ProjectionInstance(
        authority_receipt_ref="rec-1", content_hash="",
        opaque_run_ref="run-1", opaque_snapshot_ref="snap-1",
        replay_content_identity=H64)


def make_valid(cls_name: str):
    """One deterministic valid instance of any R5 object (hash fields may
    be left blank and are auto-filled by the constructor)."""
    if cls_name == "SourceRevisionContentPair":
        return _pair()
    if cls_name == "R5AEMHMatchHistory":
        return R5AEMHMatchHistory(
            candidate_ref="cand-1", from_snapshot_ref="snap-a",
            history_content_hash="", identity_evidence_refs=("ev-1",),
            later_fact_ref=None, match_state="exact", to_snapshot_ref="snap-b")
    if cls_name == "R5AudienceEncodingRegistry":
        return build_audience_encoding_registry()
    if cls_name == "R5AudienceLexicon":
        return build_audience_lexicon()
    if cls_name == "R5AuthorityReceipt":
        return R5AuthorityReceipt(
            audience_contract_id="aud-1", cutoff_ref="cut-1",
            evaluation_content_identities=(H64,), project_ref="proj-1",
            public_projection_content_hash=H64, public_projection_id="pp-1",
            public_projection_kind="d10_project", run_ref="run-1",
            snapshot_ref="snap-1",
            source_revision_content_pairs=(_pair(),),
            visibility_decision_hash=H64, visibility_decision_id="vd-1")
    if cls_name == "R5CenterMapCell":
        return R5CenterMapCell(
            domain="ae", individual_risk_refs=("r-1",), measure_refs=(),
            pattern_refs=(), severity="high", site_ref="site-1")
    if cls_name == "R5CenterMapProjection":
        return R5CenterMapProjection(
            cells=(R5CenterMapCell(
                domain="ae", individual_risk_refs=("r-1",), measure_refs=(),
                pattern_refs=(), severity="high", site_ref="site-1"),),
            content_hash="", projection_instance=_projection_instance(),
            stable_site_order=("site-1",))
    if cls_name == "R5ChangeBand":
        return R5ChangeBand(
            authority_receipt_ref="rec-1", change_cause=None,
            change_kind="initial_current", current_snapshot_ref="snap-1",
            prior_snapshot_ref=None, risk_ref="r-1")
    if cls_name == "R5CurrentRiskSet":
        return R5CurrentRiskSet(
            authority_receipt_ref="rec-1", high_risk_refs=("r-1",),
            low_risk_cluster_refs=(), medium_risk_refs=(),
            resolved_history_refs=())
    if cls_name == "R5DeepLinkState":
        return R5DeepLinkState(
            axis_mode="calendar", cutoff_ref="cut-1", event_ref=None,
            project_ref="proj-1", return_context_key="k-1",
            risk_anchor_ref="ra-1", risk_ref="r-1", run_ref="run-1",
            site_ref="site-1", snapshot_ref="snap-1",
            source_locator_ref=None, spine_ref="spine-1", subject_ref="subj-1",
            view="journey", visit_ref=None, window_end=None,
            window_start=None)
    if cls_name == "R5DomainEncodingItem":
        return DOMAIN_ENCODING_ITEMS[0]
    if cls_name == "R5FilterState":
        return R5FilterState(
            change_kind=("new",), domain=("ae",), include_low=False,
            severity=("high",), site_refs=())
    if cls_name == "R5JourneyEvent":
        return R5JourneyEvent(
            date_state="exact", domain="ae", end=None, event_ref="e-1",
            risk_anchor_refs=(), source_locator_refs=(),
            start=date(2026, 1, 1), subtype="ae")
    if cls_name == "R5JourneyTrack":
        return R5JourneyTrack(
            applicability_state="applicable", content_hash="", domain="ae",
            event_refs=("e-1",), risk_anchor_refs=())
    if cls_name == "R5LegacyTreatmentMappingItem":
        return LEGACY_TREATMENT_MAPPING_ITEMS[0]
    if cls_name == "R5LexiconItem":
        return LEXICON_ITEMS[0]
    if cls_name == "R5PageState":
        return R5PageState(page_index=0, page_size=20)
    if cls_name == "R5PendingDateItem":
        return R5PendingDateItem(
            candidate_date_refs=("cd-1",), date_state="missing", domain="ae",
            item_kind="event", item_ref="e-1", source_locator_refs=())
    if cls_name == "R5ProjectCockpitProjection":
        return R5ProjectCockpitProjection(
            center_map_ref="cm-1", change_band_refs=(), content_hash="",
            current_risk_set_ref="crs-1", measure_refs=(),
            projection_instance=_projection_instance(), selected_risk_ref=None)
    if cls_name == "R5ProjectionInstance":
        return _projection_instance()
    if cls_name == "R5QuantitativeMeasure":
        return R5QuantitativeMeasure(
            authoritative_value_ref="av-1", authority_receipt_ref="rec-1",
            coverage_state="complete", cutoff_ref="cut-1",
            denominator_exclusion_refs=(),
            denominator_kind="enrolled_subjects",
            denominator_member_refs=("m-1", "m-2"),
            denominator_state="closed_positive", denominator_value=Decimal(10),
            evaluation_limit_refs=(), numerator_kind="individual_risk",
            numerator_member_refs=("m-1",), numerator_value=Decimal(2),
            rate_state="permitted", unit="subject")
    if cls_name == "R5ReturnContext":
        return R5ReturnContext(
            canonical_state_hash="", deep_link_state=make_valid("R5DeepLinkState"),
            filter_state=make_valid("R5FilterState"), inspector_width=0,
            page_state=make_valid("R5PageState"),
            scroll_state=make_valid("R5ScrollState"),
            sort_state=make_valid("R5SortState"), temporary_expansion_refs=())
    if cls_name == "R5RiskAnchor":
        return R5RiskAnchor(
            date_state="exact", domain="ae", event_ref="e-1", risk_ref="r-1",
            risk_type_zh="AE漏报", severity="high", visit_ref=None)
    if cls_name == "R5RiskInspectorProjection":
        return R5RiskInspectorProjection(
            adjudication_ref=None, analysis_attempt_refs=("a-1",),
            authority_receipt_ref="rec-1", baseline_assessment_refs=(),
            baseline_item_refs=("b-1",), conflict_refs=(),
            counterevidence_refs=(), domain="ae", query_draft_ref=None,
            risk_ref="r-1", severity="high", source_locator_refs=("sl-1",),
            support_evidence_refs=("se-1",), verification_refs=(),
            worker_output_refs=("w-1",))
    if cls_name == "R5ScrollState":
        return R5ScrollState(center_map_y=0, project_list_y=0, workspace_y=0)
    if cls_name == "R5SeverityLexiconItem":
        return SEVERITY_LEXICON_ITEMS[0]
    if cls_name == "R5SortState":
        return R5SortState(direction="asc", key="priority")
    if cls_name == "R5SubjectWorkspaceState":
        return R5SubjectWorkspaceState(
            active_view="journey", axis_mode="calendar", content_hash="",
            selected_event_ref=None, selected_risk_ref=None,
            selected_visit_ref=None, spine_ref="spine-1", subject_ref="subj-1",
            window_end=None, window_start=None)
    if cls_name == "R5TemporalSpineProjection":
        return R5TemporalSpineProjection(
            content_hash="", cutoff_ref="cut-1", event_refs=("e-1",),
            pending_date_refs=(), phase_band_refs=("ph-1",),
            spine_ref="spine-1", subject_ref="subj-1", visit_refs=("v-1",))
    if cls_name == "R5VisitNode":
        return R5VisitNode(
            actual_date=date(2026, 1, 1), date_state="exact",
            nominal_date=None, phase_ref="ph-1", source_locator_refs=(),
            visit_kind="actual", visit_ref="v-1")
    raise AssertionError(f"no valid-instance builder for {cls_name}")


_CLASS_BY_NAME = {cls.__name__: cls for cls in (
    SourceRevisionContentPair, R5AEMHMatchHistory, R5AudienceEncodingRegistry,
    R5AudienceLexicon, R5AuthorityReceipt, R5CenterMapCell,
    R5CenterMapProjection, R5ChangeBand, R5CurrentRiskSet, R5DeepLinkState,
    R5DomainEncodingItem, R5FilterState, R5JourneyEvent, R5JourneyTrack,
    R5LegacyTreatmentMappingItem, R5LexiconItem, R5PageState,
    R5PendingDateItem, R5ProjectCockpitProjection, R5ProjectionInstance,
    R5QuantitativeMeasure, R5ReturnContext, R5RiskAnchor,
    R5RiskInspectorProjection, R5ScrollState, R5SeverityLexiconItem,
    R5SortState, R5SubjectWorkspaceState, R5TemporalSpineProjection,
    R5VisitNode,
)}


# ---------------------------------------------------------------------------
# Exact keys and type conformance
# ---------------------------------------------------------------------------


def test_exact_object_coverage_bidirectional(exact):
    json_objects = set(exact["objects"])
    r5_names = set(known_object_names())
    assert json_objects == r5_names, (
        "typed surface must cover exactly the JSON objects")


@pytest.mark.parametrize("object_name", sorted(_CLASS_BY_NAME))
def test_exact_field_keys(object_name, exact):
    spec = exact["objects"][object_name]
    cls = _CLASS_BY_NAME[object_name]
    assert is_dataclass(cls), f"{object_name} must be a dataclass"
    actual = {f.name for f in fields(cls)}
    assert set(spec) == actual, (
        f"{object_name} field keys differ from exact_contract.json: "
        f"missing={sorted(set(spec) - actual)!r} "
        f"extra={sorted(actual - set(spec))!r}")


def _shape(hint):
    """(is_tuple, nullable, base) of a resolved type hint."""
    nullable = False
    if typing.get_origin(hint) is typing.Union:
        args = [a for a in typing.get_args(hint) if a is not type(None)]
        nullable = True
        hint = args[0]
    if typing.get_origin(hint) is tuple:
        base = typing.get_args(hint)[0]
        return True, nullable, base
    return False, nullable, hint


@pytest.mark.parametrize("object_name", sorted(_CLASS_BY_NAME))
def test_field_type_conformance(object_name, exact):
    cls = _CLASS_BY_NAME[object_name]
    hints = typing.get_type_hints(cls)
    for field_name, spec in exact["objects"][object_name].items():
        is_tuple, nullable, base = _shape(hints[field_name])
        assert is_tuple == (spec["cardinality"] == "many"), (
            f"{object_name}.{field_name} cardinality mismatch")
        assert nullable == spec["nullable"], (
            f"{object_name}.{field_name} nullability mismatch")
        spec_type = spec["type"]
        if spec_type.startswith("enum:"):
            assert base is str
        elif spec_type == "str":
            assert base is str
        elif spec_type == "sha256":
            assert base is str
        elif spec_type == "int":
            assert base is int
        elif spec_type == "bool":
            assert base is bool
        elif spec_type == "decimal":
            assert base is Decimal
        elif spec_type == "date":
            assert base is date
        else:  # nested object type
            assert base is _CLASS_BY_NAME[spec_type], (
                f"{object_name}.{field_name} nested type mismatch")


@pytest.mark.parametrize("object_name", sorted(_CLASS_BY_NAME))
def test_every_object_constructible(object_name):
    obj = make_valid(object_name)
    assert is_r5_object(obj)
    assert validate_object(obj) is True


# ---------------------------------------------------------------------------
# Closed enums
# ---------------------------------------------------------------------------


def test_exact_enum_vocabulary(exact):
    for name, values in exact["enums"].items():
        assert tuple(values) == enum_values(name), (
            f"enum {name!r} must match exact_contract.json exactly "
            "(value and order)")


@pytest.mark.parametrize("object_name", sorted(_CLASS_BY_NAME))
def test_enum_fields_reject_invalid_values(object_name, exact):
    """Every enum-typed field of every object fails closed on an invalid
    token (invalid construction is rejected, not coerced)."""
    obj = make_valid(object_name)
    for field_name, spec in exact["objects"][object_name].items():
        if not spec["type"].startswith("enum:"):
            continue
        bad = [BAD_ENUM] if spec["cardinality"] == "one" else (BAD_ENUM,)
        with pytest.raises(R5ContractError):
            replace(obj, **{field_name: bad})


def test_severity_zh_bijection_and_legacy_mapping():
    assert severity_to_zh("critical") == "紧急"
    assert zh_to_severity("低") == "low"
    assert [severity_to_zh(s) for s in SEVERITIES] == ["紧急", "高", "中", "低"]
    with pytest.raises(R5ContractError):
        severity_to_zh("urgent")
    with pytest.raises(R5ContractError):
        zh_to_severity("紧急升级")
    assert legacy_severity_to_r5("severe") == "high"
    assert legacy_severity_to_r5("moderate") == "medium"
    assert legacy_severity_to_r5("mild") == "low"
    with pytest.raises(R5ContractError):
        legacy_severity_to_r5("unknown-legacy")


def test_severity_no_promotion():
    assert validate_severity_authority("high", "high") == "high"
    assert validate_severity_authority("critical", "critical") == "critical"
    assert validate_severity_authority("low", "high") == "low"
    with pytest.raises(R5ContractError):
        validate_severity_authority("critical", "high")
    with pytest.raises(R5ContractError):
        validate_severity_authority("high", "medium")
    with pytest.raises(R5ContractError):
        validate_severity_authority("high", "unknown")
    with pytest.raises(R5ContractError):
        validate_severity_authority("high", "not-a-token")


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("object_name", sorted(_CLASS_BY_NAME))
def test_immutable_after_construction(object_name):
    obj = make_valid(object_name)
    first_field = next(iter(fields(_CLASS_BY_NAME[object_name]))).name
    with pytest.raises(FrozenInstanceError):
        setattr(obj, first_field, "mutated")
    for f in fields(_CLASS_BY_NAME[object_name]):
        value = getattr(obj, f.name)
        if isinstance(value, tuple):
            with pytest.raises(AttributeError):
                value.append  # noqa: B018  (tuples expose no mutators)


# ---------------------------------------------------------------------------
# Deterministic canonical hash
# ---------------------------------------------------------------------------


def test_unordered_refs_do_not_change_hash():
    track_a = R5JourneyTrack(
        applicability_state="applicable", content_hash="", domain="ae",
        event_refs=("e-1", "e-2", "e-3"), risk_anchor_refs=("ra-2", "ra-1"))
    track_b = R5JourneyTrack(
        applicability_state="applicable", content_hash="", domain="ae",
        event_refs=("e-3", "e-1", "e-2"), risk_anchor_refs=("ra-1", "ra-2"))
    assert track_a.content_hash == track_b.content_hash
    assert canonical.canonical_object_hash(track_a) == (
        canonical.canonical_object_hash(track_b))


def test_ordered_site_order_preserved_in_core():
    cell = make_valid("R5CenterMapCell")
    map_a = R5CenterMapProjection(
        cells=(cell,), content_hash="", projection_instance=_projection_instance(),
        stable_site_order=("s-1", "s-2"))
    map_b = R5CenterMapProjection(
        cells=(cell,), content_hash="", projection_instance=_projection_instance(),
        stable_site_order=("s-2", "s-1"))
    assert map_a.content_hash != map_b.content_hash
    core_a = canonical.object_to_core(map_a)
    assert core_a["stable_site_order"] == ["s-1", "s-2"]
    assert canonical.object_to_core(map_b)["stable_site_order"] == ["s-2", "s-1"]


def test_object_list_order_does_not_change_hash():
    """Object many-fields are hash-sorted: input ordering never changes the
    content hash (deterministic replay), while stable_site_order stays the
    display authority."""
    cell_a = R5CenterMapCell(
        domain="ae", individual_risk_refs=("r-1",), measure_refs=(),
        pattern_refs=(), severity="high", site_ref="site-a")
    cell_b = R5CenterMapCell(
        domain="mh", individual_risk_refs=("r-2",), measure_refs=(),
        pattern_refs=(), severity="medium", site_ref="site-b")
    proj_a = R5CenterMapProjection(
        cells=(cell_a, cell_b), content_hash="",
        projection_instance=_projection_instance(),
        stable_site_order=("site-a", "site-b"))
    proj_b = R5CenterMapProjection(
        cells=(cell_b, cell_a), content_hash="",
        projection_instance=_projection_instance(),
        stable_site_order=("site-a", "site-b"))
    assert proj_a.content_hash == proj_b.content_hash

    lex_a = build_audience_lexicon()
    lex_b = R5AudienceLexicon(
        content_hash="", forbidden_terms=lex_a.forbidden_terms,
        items=tuple(reversed(lex_a.items)))
    assert lex_a.content_hash == lex_b.content_hash


def test_return_context_hash_independent_implementation():
    ctx = make_valid("R5ReturnContext")
    expected = hashlib.sha256(
        canonical.canonical_json({
            "deep_link_state": {
                "axis_mode": "calendar", "cutoff_ref": "cut-1",
                "event_ref": None, "project_ref": "proj-1",
                "return_context_key": "k-1", "risk_anchor_ref": "ra-1",
                "risk_ref": "r-1", "run_ref": "run-1", "site_ref": "site-1",
                "snapshot_ref": "snap-1", "source_locator_ref": None,
                "spine_ref": "spine-1", "subject_ref": "subj-1",
                "view": "journey", "visit_ref": None, "window_end": None,
                "window_start": None,
            },
            "filter_state": {
                "change_kind": ["new"], "domain": ["ae"], "include_low": False,
                "severity": ["high"], "site_refs": [],
            },
            "inspector_width": 0,
            "page_state": {"page_index": 0, "page_size": 20},
            "scroll_state": {"center_map_y": 0, "project_list_y": 0,
                             "workspace_y": 0},
            "sort_state": {"direction": "asc", "key": "priority"},
            "temporary_expansion_refs": [],
        }).encode("utf-8")).hexdigest()
    assert ctx.canonical_state_hash == expected
    assert "canonical_state_hash" not in canonical.object_to_core(ctx)


def test_hash_changes_when_non_hash_field_changes():
    base = make_valid("R5SubjectWorkspaceState")
    other = replace(base, subject_ref="subj-2", content_hash="")
    assert base.content_hash != other.content_hash
    assert other.content_hash == canonical.canonical_object_hash(other)


def test_nfc_normalization_does_not_change_hash():
    composed = R5LexiconItem(token="t1", label_zh="é", audience_allowed=True)
    decomposed = R5LexiconItem(token="t1", label_zh="e\u0301",
                               audience_allowed=True)
    assert composed.label_zh == "é"
    assert canonical.canonical_object_hash(composed) == (
        canonical.canonical_object_hash(decomposed))


def test_decimal_canonicalization():
    m1 = R5QuantitativeMeasure(
        authoritative_value_ref="av-1", authority_receipt_ref="rec-1",
        coverage_state="complete", cutoff_ref="cut-1",
        denominator_exclusion_refs=(), denominator_kind="enrolled_subjects",
        denominator_member_refs=("m-1",), denominator_state="closed_positive",
        denominator_value=Decimal("10.0"), evaluation_limit_refs=(),
        numerator_kind="individual_risk", numerator_member_refs=("m-1",),
        numerator_value=Decimal("2.50"), rate_state="permitted",
        unit="subject")
    m2 = R5QuantitativeMeasure(
        authoritative_value_ref="av-1", authority_receipt_ref="rec-1",
        coverage_state="complete", cutoff_ref="cut-1",
        denominator_exclusion_refs=(), denominator_kind="enrolled_subjects",
        denominator_member_refs=("m-1",), denominator_state="closed_positive",
        denominator_value=10, evaluation_limit_refs=(),
        numerator_kind="individual_risk", numerator_member_refs=("m-1",),
        numerator_value=Decimal("2.5"), rate_state="permitted",
        unit="subject")
    assert m1.denominator_value == Decimal("10.0")
    assert canonical.canonical_object_hash(m1) == (
        canonical.canonical_object_hash(m2))
    core = canonical.object_to_core(m1)
    assert core["numerator_value"] == "2.5"
    assert core["denominator_value"] == "10"


# ---------------------------------------------------------------------------
# Tamper rejection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("object_name", [
    "R5ProjectionInstance", "R5ProjectCockpitProjection",
    "R5CenterMapProjection", "R5SubjectWorkspaceState", "R5ReturnContext",
    "R5JourneyTrack", "R5TemporalSpineProjection", "R5AEMHMatchHistory",
    "R5AudienceLexicon",
])
def test_supplied_mismatched_hash_rejected(object_name):
    valid = make_valid(object_name)
    hash_field = next(f.name for f in fields(_CLASS_BY_NAME[object_name])
                      if f.name in ("content_hash", "history_content_hash",
                                    "canonical_state_hash"))
    forged = "0" * 64
    assert forged != getattr(valid, hash_field)
    with pytest.raises(R5HashMismatchError):
        replace(valid, **{hash_field: forged})


@pytest.mark.parametrize("object_name", [
    "R5ProjectionInstance", "R5ProjectCockpitProjection",
    "R5CenterMapProjection", "R5SubjectWorkspaceState", "R5ReturnContext",
    "R5JourneyTrack", "R5TemporalSpineProjection", "R5AEMHMatchHistory",
    "R5AudienceLexicon",
])
def test_supplied_correct_hash_accepted(object_name):
    valid = make_valid(object_name)
    hash_field = next(f.name for f in fields(_CLASS_BY_NAME[object_name])
                      if f.name in ("content_hash", "history_content_hash",
                                    "canonical_state_hash"))
    computed = getattr(valid, hash_field)
    rebuilt = replace(valid, **{hash_field: computed})
    assert getattr(rebuilt, hash_field) == computed


def test_receipt_hashes_are_opaque_shape_only():
    """R4-authoritative receipt hashes are shape-checked, not locally
    recomputed (the W2 adapter verifies them against R4)."""
    receipt = make_valid("R5AuthorityReceipt")
    with pytest.raises(R5ContractError):
        replace(receipt, public_projection_content_hash="not-a-hash")
    with pytest.raises(R5ContractError):
        replace(receipt, visibility_decision_hash="xyz")
    with pytest.raises(R5ContractError):
        replace(receipt, evaluation_content_identities=("bad",))


# ---------------------------------------------------------------------------
# Unique reference sets and cross-field invariants
# ---------------------------------------------------------------------------


def test_duplicate_refs_rejected():
    with pytest.raises(R5ContractError):
        R5CurrentRiskSet(authority_receipt_ref="rec-1",
                         high_risk_refs=("r-1", "r-1"), medium_risk_refs=(),
                         low_risk_cluster_refs=(), resolved_history_refs=())
    with pytest.raises(R5ContractError):
        R5JourneyEvent(date_state="exact", domain="ae", end=None,
                       event_ref="e-1", risk_anchor_refs=("ra-1", "ra-1"),
                       source_locator_refs=(), start=date(2026, 1, 1),
                       subtype="ae")


def test_current_risk_set_planes_disjoint():
    with pytest.raises(R5ContractError):
        R5CurrentRiskSet(authority_receipt_ref="rec-1",
                         high_risk_refs=("r-1",), medium_risk_refs=("r-1",),
                         low_risk_cluster_refs=(), resolved_history_refs=())
    with pytest.raises(R5ContractError):
        R5CurrentRiskSet(authority_receipt_ref="rec-1", high_risk_refs=(),
                         medium_risk_refs=(), low_risk_cluster_refs=("r-1",),
                         resolved_history_refs=("r-1",))


def test_support_counterevidence_planes_exclusive():
    with pytest.raises(R5ContractError):
        R5RiskInspectorProjection(
            adjudication_ref=None, analysis_attempt_refs=("a-1",),
            authority_receipt_ref="rec-1", baseline_assessment_refs=(),
            baseline_item_refs=(), conflict_refs=(),
            counterevidence_refs=("ev-1",), domain="ae", query_draft_ref=None,
            risk_ref="r-1", severity="high", source_locator_refs=(),
            support_evidence_refs=("ev-1",), verification_refs=(),
            worker_output_refs=())


def test_denominator_rate_consistency():
    base = dict(
        authoritative_value_ref="av-1", authority_receipt_ref="rec-1",
        coverage_state="complete", cutoff_ref="cut-1",
        denominator_exclusion_refs=(), denominator_kind="enrolled_subjects",
        denominator_member_refs=("m-1",), evaluation_limit_refs=(),
        numerator_kind="individual_risk", numerator_member_refs=("m-1",),
        numerator_value=Decimal(1), unit="subject")
    # closed_zero requires value 0 + rate_state not_evaluable
    R5QuantitativeMeasure(
        denominator_state="closed_zero", denominator_value=Decimal(0),
        rate_state="not_evaluable", **base)
    with pytest.raises(R5ContractError):
        R5QuantitativeMeasure(
            denominator_state="closed_zero", denominator_value=Decimal(0),
            rate_state="permitted", **base)
    with pytest.raises(R5ContractError):
        R5QuantitativeMeasure(
            denominator_state="closed_zero", denominator_value=Decimal(1),
            rate_state="not_evaluable", **base)
    # unknown/unclosed require null value + not_evaluable
    R5QuantitativeMeasure(
        denominator_state="unknown", denominator_value=None,
        rate_state="not_evaluable", **base)
    with pytest.raises(R5ContractError):
        R5QuantitativeMeasure(
            denominator_state="unclosed", denominator_value=Decimal(5),
            rate_state="not_evaluable", **base)
    with pytest.raises(R5ContractError):
        R5QuantitativeMeasure(
            denominator_state="unknown", denominator_value=None,
            rate_state="qualified", **base)
    # closed_positive requires value > 0
    with pytest.raises(R5ContractError):
        R5QuantitativeMeasure(
            denominator_state="closed_positive", denominator_value=Decimal(0),
            rate_state="permitted", **base)


def test_date_geometry_consistency():
    with pytest.raises(R5ContractError):
        R5VisitNode(actual_date=date(2026, 1, 1), date_state="missing",
                    nominal_date=None, phase_ref=None, source_locator_refs=(),
                    visit_kind="actual", visit_ref="v-1")
    with pytest.raises(R5ContractError):
        R5VisitNode(actual_date=None, date_state="exact", nominal_date=None,
                    phase_ref=None, source_locator_refs=(),
                    visit_kind="nominal", visit_ref="v-1")
    R5VisitNode(actual_date=None, date_state="missing", nominal_date=None,
                phase_ref=None, source_locator_refs=(), visit_kind="actual",
                visit_ref="v-1")
    with pytest.raises(R5ContractError):
        R5JourneyEvent(date_state="missing", domain="ae", end=None,
                       event_ref="e-1", risk_anchor_refs=(),
                       source_locator_refs=(), start=date(2026, 1, 1),
                       subtype="ae")
    with pytest.raises(R5ContractError):
        R5JourneyEvent(date_state="exact", domain="ae", end=None,
                       event_ref="e-1", risk_anchor_refs=(),
                       source_locator_refs=(), start=None, subtype="ae")
    with pytest.raises(R5ContractError):
        R5PendingDateItem(candidate_date_refs=(), date_state="exact",
                          domain="ae", item_kind="event", item_ref="e-1",
                          source_locator_refs=())


def test_domain_subtype_matrix():
    with pytest.raises(R5ContractError):
        R5JourneyEvent(date_state="exact", domain="ae", end=None,
                       event_ref="e-1", risk_anchor_refs=(),
                       source_locator_refs=(), start=date(2026, 1, 1),
                       subtype="symptom")
    R5JourneyEvent(date_state="exact", domain="symptom_efficacy", end=None,
                   event_ref="e-1", risk_anchor_refs=(), source_locator_refs=(),
                   start=date(2026, 1, 1), subtype="trend")
    with pytest.raises(R5ContractError):
        R5JourneyEvent(date_state="exact", domain="cm", end=None,
                       event_ref="e-1", risk_anchor_refs=(),
                       source_locator_refs=(), start=date(2026, 1, 1),
                       subtype="ip_dose")


def test_legacy_treatment_fail_closed():
    with pytest.raises(R5ContractError):
        R5LegacyTreatmentMappingItem(
            legacy_kind="background_treatment", mapping_state="mapped",
            mapping_authority_ref=None, target_domain=None,
            target_subtype=None)
    with pytest.raises(R5ContractError):
        R5LegacyTreatmentMappingItem(
            legacy_kind="non_drug_treatment",
            mapping_state="unmapped_fail_closed",
            mapping_authority_ref="auth-1", target_domain="cm",
            target_subtype="concomitant_medication")


def test_encoding_registry_invariants():
    registry = build_audience_encoding_registry()
    assert registry.risk_overlay_shape == "double_chevron_badge"
    shapes = {item.event_shape for item in registry.domain_items}
    assert "double_chevron_badge" not in shapes
    severities = {item.severity for item in registry.severity_items}
    assert severities == set(SEVERITIES)
    assert {item.label_zh for item in registry.severity_items} == {
        "紧急", "高", "中", "低"}
    assert {item.domain for item in registry.domain_items} == set(DOMAINS)
    symptom = next(item for item in registry.domain_items
                   if item.domain == "symptom_efficacy")
    assert (symptom.event_shape, symptom.line_style) == ("circle", "trend")
    # duplicated severity rejected (severity_lexicon_bijection)
    with pytest.raises(R5ContractError):
        R5AudienceEncodingRegistry(
            domain_items=DOMAIN_ENCODING_ITEMS,
            legacy_treatment_mapping=LEGACY_TREATMENT_MAPPING_ITEMS,
            risk_overlay_shape="double_chevron_badge",
            severity_items=(SEVERITY_LEXICON_ITEMS[0],
                            SEVERITY_LEXICON_ITEMS[0],
                            SEVERITY_LEXICON_ITEMS[2],
                            SEVERITY_LEXICON_ITEMS[3]),
            symptom_efficacy_subtypes=("symptom", "efficacy", "scale",
                                       "outcome", "trend"))
    # wrong overlay shape rejected
    with pytest.raises(R5ContractError):
        R5AudienceEncodingRegistry(
            domain_items=DOMAIN_ENCODING_ITEMS,
            legacy_treatment_mapping=LEGACY_TREATMENT_MAPPING_ITEMS,
            risk_overlay_shape="chevron",
            severity_items=SEVERITY_LEXICON_ITEMS,
            symptom_efficacy_subtypes=("symptom", "efficacy", "scale",
                                       "outcome", "trend"))
    # forbidden event shape rejected (risk_overlay_unique)
    with pytest.raises(R5ContractError):
        R5DomainEncodingItem(domain="ae", short_label_zh="AE",
                             event_shape="double_chevron_badge",
                             line_style="solid")
    # every domain appears exactly once and all eight domains are required
    with pytest.raises(R5ContractError):
        R5AudienceEncodingRegistry(
            domain_items=DOMAIN_ENCODING_ITEMS[:-1],
            legacy_treatment_mapping=LEGACY_TREATMENT_MAPPING_ITEMS,
            risk_overlay_shape="double_chevron_badge",
            severity_items=SEVERITY_LEXICON_ITEMS,
            symptom_efficacy_subtypes=SYMPTOM_EFFICACY_SUBTYPES)
    with pytest.raises(R5ContractError):
        R5AudienceEncodingRegistry(
            domain_items=DOMAIN_ENCODING_ITEMS[:-1] +
            (DOMAIN_ENCODING_ITEMS[0],),
            legacy_treatment_mapping=LEGACY_TREATMENT_MAPPING_ITEMS,
            risk_overlay_shape="double_chevron_badge",
            severity_items=SEVERITY_LEXICON_ITEMS,
            symptom_efficacy_subtypes=SYMPTOM_EFFICACY_SUBTYPES)
    wrong_symptom = replace(
        symptom, event_shape="triangle", line_style="trend")
    with pytest.raises(R5ContractError):
        R5AudienceEncodingRegistry(
            domain_items=tuple(
                wrong_symptom if item.domain == "symptom_efficacy" else item
                for item in DOMAIN_ENCODING_ITEMS),
            legacy_treatment_mapping=LEGACY_TREATMENT_MAPPING_ITEMS,
            risk_overlay_shape="double_chevron_badge",
            severity_items=SEVERITY_LEXICON_ITEMS,
            symptom_efficacy_subtypes=SYMPTOM_EFFICACY_SUBTYPES)


def test_authority_receipt_preserves_absent_cutoff_as_null():
    receipt = make_valid("R5AuthorityReceipt")
    without_cutoff = replace(receipt, cutoff_ref=None)
    assert without_cutoff.cutoff_ref is None
    with pytest.raises(R5ContractError):
        replace(receipt, cutoff_ref="")


def test_audience_lexicon_consistency():
    lexicon = build_audience_lexicon()
    assert lexicon.content_hash == canonical.canonical_object_hash(lexicon)
    forbidden = set(lexicon.forbidden_terms)
    assert forbidden == {item.label_zh for item in lexicon.items
                         if not item.audience_allowed}
    assert forbidden and set(FORBIDDEN_TERMS) == forbidden
    assert "待行动" in forbidden and "Checklist" in forbidden
    allowed = {item.label_zh for item in lexicon.items
               if item.audience_allowed}
    assert {"紧急", "高", "中", "低"} <= allowed


# ---------------------------------------------------------------------------
# Deferred leaf registry
# ---------------------------------------------------------------------------


def test_deferred_registry_matches_authority(exact):
    json_deferred = {fm["deferred_contract"]
                     for fm in exact["field_mappings"]
                     if fm["source_kind"] == "deferred"}
    assert {spec.contract_id for spec in mm_r5.DEFERRED_CONTRACT_SPECS} == (
        json_deferred)
    # per-contract field targets
    for spec in mm_r5.DEFERRED_CONTRACT_SPECS:
        json_targets = sorted(
            fm["target"] for fm in exact["field_mappings"]
            if fm["source_kind"] == "deferred"
            and fm["deferred_contract"] == spec.contract_id)
        assert sorted(spec.deferred_fields) == json_targets, (
            f"deferred contract {spec.contract_id} field targets drift")


def test_deferred_field_lookup(exact):
    for object_name, fields_spec in exact["objects"].items():
        json_deferred = sorted(
            fm["target"].split(".", 1)[1]
            for fm in exact["field_mappings"]
            if fm["source_kind"] == "deferred"
            and fm["target"].startswith(object_name + "."))
        assert sorted(deferred_fields_for(object_name)) == json_deferred, (
            f"deferred fields of {object_name} drift")
        for field_name in json_deferred:
            assert is_deferred_field(object_name, field_name)
    with pytest.raises(R5ContractError):
        deferred_fields_for("NotAnR5Object")
    with pytest.raises(R5ContractError):
        deferred_contract("unknown-deferred-id")


def test_deferred_leaf_objects(exact):
    all_fields = {name: set(spec) for name, spec in exact["objects"].items()}
    json_leaves = set()
    for object_name, spec in exact["objects"].items():
        deferred = set(
            fm["target"].split(".", 1)[1]
            for fm in exact["field_mappings"]
            if fm["source_kind"] == "deferred"
            and fm["target"].startswith(object_name + "."))
        if deferred == all_fields[object_name]:
            json_leaves.add(object_name)
    assert set(deferred_leaf_objects()) == json_leaves
    # deferred leaves must still be fully constructible
    for leaf in json_leaves:
        make_valid(leaf)


def test_r4_direct_and_derived_fields_not_marked_deferred(exact):
    """Fields with a real R4 source path must NOT be deferred: only the
    JSON-declared deferred fields are."""
    for fm in exact["field_mappings"]:
        object_name, field_name = fm["target"].split(".", 1)
        assert is_deferred_field(object_name, field_name) == (
            fm["source_kind"] == "deferred"), (
            f"{fm['target']} deferred flag mismatch with source_kind")


# ---------------------------------------------------------------------------
# Packaging / surface sanity
# ---------------------------------------------------------------------------


def test_public_surface_imports():
    assert mm_r5.R5_CONTRACT_SCHEMA_ID == (
        "medical-monitoring-r5-exact-contract-v0.3.1")
    assert mm_r5.R5_CONTRACT_SHA256 == R5_CONTRACT_SHA256
    assert mm_r5.canonical_object_hash is canonical.canonical_object_hash
    assert mm_r5.build_authority_receipt.__module__ == "mm_r5.authority_adapter"
    assert mm_r5.verify_authority_receipt.__module__ == "mm_r5.authority_adapter"
    assert mm_r5.DEFAULT_D10_AUTHORITY_ADAPTER_VARIANT.projection_kind == (
        "d10_project")
    # every public class constructs (surface is complete and importable)
    for name in known_object_names():
        assert hasattr(mm_r5, name)


def test_canonical_rejects_unknown_types():
    with pytest.raises(canonical.R5CanonicalError):
        canonical.canonical_json(object())
    with pytest.raises(canonical.R5CanonicalError):
        canonical.canonical_json(float("nan"))
    with pytest.raises(canonical.R5CanonicalError):
        canonical.canonical_json({1, 2, 3})
