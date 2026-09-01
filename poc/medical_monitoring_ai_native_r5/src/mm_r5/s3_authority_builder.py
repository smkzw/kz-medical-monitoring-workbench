"""R5 S3 -- synthetic/offline authority builder for the offline project
cockpit and center-graph runtime (authority side).

The builder consumes leaf-by-leaf read-only references to the R4/S1/S2 public
authority objects -- the D09/D10 public projections, the R5 authority
receipts and the named synthetic supplemental authorities -- and produces the
frozen ``R5S3AuthorityPacket`` typed authorities declared by the accepted
``medical-monitoring-r5-s3-packet-schema-v0.2`` contract.  It never imports
a D09/D10 typed-input object and never recomputes medical risk, chooses a
majority, infers members from counts or trusts a caller-supplied hash: every
S3-owned content hash, identity hash, cluster ref and aggregate identity is
recomputed from the real leaves and verified at construction.

The renderer-neutral projection side (current-risk exact planes, center-cell
closure, change-band emission, measure projection, center-map/cockpit
projection) is implemented here as pure functions of the typed packet so that
``build_s3_authority_packet`` closes end-to-end; worker_02 owns the
presentation of those projection functions and any fail-closed invariant
extensions.

Scope: synthetic/offline supplemental test authority only
(``authority_mode = synthetic_offline_test_only``).  Nothing here starts a
service, opens a browser, reads real project data or writes back to R4/S1/S2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from mm_r4.d09_projection import (
    D09AudienceProjection,
    D09HotspotProjection,
    D09ProjectionBundle,
    D09ProjectionCountSurface,
    D09R2RiskHandoff,
    D09RiskMarker,
)
from mm_r4.d10_projection import (
    D10AudienceProjection,
    D10CenterPatternRow,
    D10ChangeSection,
    D10HotspotProjection,
    D10ProjectionBundle,
    D10ProjectionCountSurface,
    D10ProjectionVersion,
    D10ProjectProjection,
    D10R2RiskHandoff,
    D10RiskMarker,
    D10TrendSurface,
)
from mm_r5.contracts import (
    R5AuthorityReceipt,
    R5CenterMapCell,
    R5CenterMapProjection,
    R5ChangeBand,
    R5CurrentRiskSet,
    R5ProjectCockpitProjection,
    R5ProjectionInstance,
    R5QuantitativeMeasure,
    SourceRevisionContentPair,
)
from mm_r5.s3_contracts import (
    AUTHORITY_MODE_S3,
    CLUSTER_REF_PREFIX,
    D09_MARKER_PREFIX,
    D10_MARKER_PREFIX,
    LIFECYCLE_STATE_TABLE,
    PACKET_ID_PREFIX,
    RECEIPT_REF_PREFIX,
    R5S3AggregateReceiptSetIdentity,
    R5S3AudiencePayload,
    R5S3AuthorityPacket,
    R5S3AuthorityUnitTagged,
    R5S3ChangeCauseMixtureAuthority,
    R5S3ClinicalDomainAuthority,
    R5S3ClosureAuthority,
    R5S3CoverageAuthority,
    R5S3CutoffAuthority,
    R5S3D09CenterPatternUnit,
    R5S3D10ProjectUnit,
    R5S3DenominatorAuthority,
    R5S3EvaluationLimitAuthority,
    R5S3LayerMembershipAuthority,
    R5S3LowRiskCluster,
    R5S3RiskLifecycleAuthority,
    S3ContractError,
    S3_MARKER_KINDS,
    S3_PACKET_SCHEMA_ID,
    S3_SEVERITIES,
    STAGE_STATUS_S3,
    authority_receipt_ref,
    cluster_content_hash,
    receipt_content_hash,
    s3_canonical_bytes,
    s3_content_hash_excluding,
    s3_sha256,
    unit_variant_payload,
)

# ---------------------------------------------------------------------------
# Builder identity / errors
# ---------------------------------------------------------------------------

#: Self-declared builder schema id.  This value is not pinned by an accepted
#: S3 artifact (like the S2 thin-slice schema id); it is a local module
#: identity so the builder source can be recognized on replay.
S3_BUILDER_SCHEMA_ID = "medical-monitoring-r5-s3-authority-builder-v0.1"


class S3AuthorityBuilderError(Exception):
    """A fail-closed builder gate failed: the R4/S1/S2 authority leaves did
    not yield the frozen S3 authority objects a packet requires (missing
    marker/handoff, non high/medium/low severity, unresolved domain ref, …).
    No packet is emitted."""


# ---------------------------------------------------------------------------
# Synthetic envelope identity (neutral, meaningful; never test/case ids)
# ---------------------------------------------------------------------------

SYNTHETIC_PROJECT_REF = "S3-PROJECT-001"
SYNTHETIC_RUN_REF = "S3-RUN-001"
SYNTHETIC_SNAPSHOT_REF = "S3-SNAPSHOT-001"
SYNTHETIC_CUTOFF_REF = "S3-CUTOFF-001"
SYNTHETIC_AUDIENCE_CONTRACT_ID = "S3-AUDIENCE-CONTRACT-001"
SYNTHETIC_SOURCE_REVISION = "S3-REV-SOURCE-001"
SYNTHETIC_SOURCE_FILE = "synthetic_source/s3_packet_source.json"

#: Three authority units: one high D10 project signal, one low D09 center
#: pattern, one resolved D09 center pattern (resolved history).
SYNTHETIC_UNIT_D10_REF = "S3-UNIT-D10-001"
SYNTHETIC_UNIT_D09_LOW_REF = "S3-UNIT-D09-001"
SYNTHETIC_UNIT_D09_RESOLVED_REF = "S3-UNIT-D09-002"

SYNTHETIC_MEMBERS_D10 = ("S3-MEMBER-D10-001", "S3-MEMBER-D10-002")
SYNTHETIC_MEMBERS_D09_LOW = ("S3-MEMBER-D09-001",)
SYNTHETIC_MEMBERS_D09_RESOLVED = ("S3-MEMBER-D09-002",)

SYNTHETIC_SITE_D10 = "S3-SITE-D10-001"
SYNTHETIC_SITE_D09_LOW = "S3-SITE-D09-001"
SYNTHETIC_SITE_D09_RESOLVED = "S3-SITE-D09-002"

#: Closed clinical domains (synthetic supplemental authorities; never typed
#: Member domain).
SYNTHETIC_DOMAIN_D10 = "mh"
SYNTHETIC_DOMAIN_D09_LOW = "ae"
SYNTHETIC_DOMAIN_D09_RESOLVED = "cm"

SYNTHETIC_PRIOR_INSTANCE_D10 = "S3-INSTANCE-PRIOR-D10-001"
SYNTHETIC_PRIOR_INSTANCE_D09_RESOLVED = "S3-INSTANCE-PRIOR-D09-002"
SYNTHETIC_EVALUATION_LIMIT_D10 = "S3-EVAL-LIMIT-D10-001"

SYNTHETIC_WINDOW_REF = "S3-WINDOW-001"


def _h(value: Any) -> str:
    """S3 canonical content hash of any value (the packet recipe)."""
    return s3_sha256(s3_canonical_bytes(value))


def _fixture_hash(label: str) -> str:
    """Deterministic 64-hex digest for a synthetic offline leaf (the public
    R4 projection objects carry opaque content hashes; the S3 builder never
    recomputes R4 hashes, it only mirrors them)."""
    return s3_sha256(("s3-fixture:" + label).encode("utf-8"))


def _content_hash_of(obj: Any) -> str:
    """Canonical content hash of ONE typed object excluding its own
    ``content_hash`` field (used by every builder to fill object hashes)."""
    return s3_content_hash_excluding(obj, ("content_hash",))


# ---------------------------------------------------------------------------
# Synthetic R4 public projection fixtures (packet_fixture source kind)
# ---------------------------------------------------------------------------

#: facets shared by every synthetic public receipt.
def _build_receipt(kind: str, projection_id: str) -> R5AuthorityReceipt:
    """One synthetic R5 authority receipt bound to the shared synthetic
    project/run/snapshot/cutoff/audience identities (public R4/S1 leaf)."""
    pair = SourceRevisionContentPair(
        revision_id=SYNTHETIC_SOURCE_REVISION,
        content_hash=_fixture_hash("revision." + projection_id))
    return R5AuthorityReceipt(
        audience_contract_id=SYNTHETIC_AUDIENCE_CONTRACT_ID,
        cutoff_ref=SYNTHETIC_CUTOFF_REF,
        evaluation_content_identities=(
            _fixture_hash("evaluation." + projection_id),),
        project_ref=SYNTHETIC_PROJECT_REF,
        public_projection_content_hash=_fixture_hash("projection." +
                                                     projection_id),
        public_projection_id=projection_id,
        public_projection_kind=("d10_project" if kind == "d10"
                                else "d09_audience"),
        run_ref=SYNTHETIC_RUN_REF,
        snapshot_ref=SYNTHETIC_SNAPSHOT_REF,
        source_revision_content_pairs=(pair,),
        visibility_decision_hash=_fixture_hash("visibility." + projection_id),
        visibility_decision_id=("S3-VIS-DECISION-" + projection_id),
    )


def _build_d09_marker(marker_label: str,
                      members: Tuple[str, ...]) -> D09RiskMarker:
    marker_id = _fixture_hash("d09-marker." + marker_label)
    return D09RiskMarker(
        marker_id=marker_id,
        public_risk_identity={"kind": "d09", "label": marker_label},
        stable_core=marker_id,
        risk_owner="D09",
        risk_kind="center_pattern",
        aggregation_level="site_pattern",
        member_refs=tuple(sorted(members)),
        source_locator_ids=(_fixture_hash("locator-d09." + marker_label),),
        content_hash=_fixture_hash("d09-marker-content." + marker_label),
    )


def _build_d10_marker(marker_label: str,
                      members: Tuple[str, ...]) -> D10RiskMarker:
    marker_id = _fixture_hash("d10-marker." + marker_label)
    return D10RiskMarker(
        marker_id=marker_id,
        public_risk_identity={"kind": "d10", "label": marker_label},
        stable_core=marker_id,
        risk_owner="D10",
        risk_kind="project_signal",
        aggregation_level="project_signal",
        member_refs=tuple(sorted(members)),
        source_locator_ids=(_fixture_hash("locator-d10." + marker_label),),
        content_hash=_fixture_hash("d10-marker-content." + marker_label),
    )


def _build_d09_handoff(label: str, action: str, priority: str,
                       members: Tuple[str, ...],
                       prior_instance: Optional[str],
                       prior_public: Optional[str]) -> D09R2RiskHandoff:
    handoff_id = _fixture_hash("d09-handoff." + label)
    return D09R2RiskHandoff(
        handoff_id=handoff_id,
        idempotency_key=handoff_id,
        public_d09_risk_identity={"kind": "d09", "label": label},
        stable_core_ref=handoff_id,
        current_evaluation_content_ref=_fixture_hash("eval." + label),
        run_snapshot_audit_refs=(SYNTHETIC_RUN_REF, SYNTHETIC_SNAPSHOT_REF),
        prior_risk_instance_ref=prior_instance,
        prior_public_risk_identity_ref=prior_public,
        action=action,
        lineage_relation=("initial_full_snapshot" if action == "create"
                          else "continued_from_data_revision"),
        pattern_definition_hash=_fixture_hash("pattern." + label),
        mode_contract_version="v0.3",
        member_refs=tuple(sorted(members)),
        measure_ledger_ref=_fixture_hash("measure." + label),
        completeness_decision_ref=_fixture_hash("completeness." + label),
        monitoring_priority=priority,
        no_auto_close_reasons=(),
    )


def _build_d10_handoff(label: str, action: str, priority: str,
                       members: Tuple[str, ...],
                       prior_instance: Optional[str]) -> D10R2RiskHandoff:
    handoff_id = _fixture_hash("d10-handoff." + label)
    return D10R2RiskHandoff(
        handoff_id=handoff_id,
        idempotency_key=handoff_id,
        public_d10_risk_identity={"kind": "d10", "label": label},
        stable_core_ref=handoff_id,
        current_evaluation_content_ref=_fixture_hash("eval." + label),
        run_snapshot_audit_refs=(SYNTHETIC_RUN_REF, SYNTHETIC_SNAPSHOT_REF),
        prior_risk_instance_ref=prior_instance,
        action=action,
        lineage_relation="continued_from_data_revision",
        change_decision_ref=_fixture_hash("change." + label),
        completeness_decision_ref=_fixture_hash("completeness." + label),
        member_refs=tuple(sorted(members)),
        measure_ledger_ref=_fixture_hash("measure." + label),
        monitoring_priority=priority,
        no_auto_close_reasons=(),
    )


def _build_d09_audience(scope: str, members: Tuple[str, ...],
                        site: str) -> D09AudienceProjection:
    return D09AudienceProjection(
        audience_scope_id=scope,
        projectable_member_refs=tuple(sorted(members)),
        evaluation_member_refs=tuple(sorted(members)),
        hidden_member_refs=(),
        hidden_member_count=0,
        audience_payload_present=True,
        risk_present=True,
        query_present=False,
        journey_marker_present=False,
        hotspot_present=True,
        rate_projection_state="permitted",
        visible_n=len(members),
        eligible_n=len(members),
        coverage_state="complete",
        coverage_zh=("\u5b8c\u6574"),
        disposition_zh=("\u9633\u6027"),
        primary_reason="synthetic",
        disclosure_leak_present=False,
    )


def _build_d09_counts(label: str, members: Tuple[str, ...],
                      ) -> D09ProjectionCountSurface:
    count = len(members)
    return D09ProjectionCountSurface(
        evaluation_window_instance_ref=SYNTHETIC_WINDOW_REF,
        individual_risk_count=count,
        affected_subject_count=count,
        event_count=count,
        gap_opportunity_count=0,
        center_pattern_count=count,
        clue_count=0,
        query_count=0,
        hidden_member_count=0,
        visible_individual_risk_count=count,
        visible_affected_subject_count=count,
        visible_event_count=count,
        visible_gap_opportunity_count=0,
        visible_n=count,
        eligible_n=count,
        rate_projection_state="permitted",
        individual_risk_zh="\u4e2a\u4f53\u98ce\u9669",
        affected_subjects_zh="\u53d7\u5f71\u54cd\u53d7\u8bd5\u8005",
        event_count_zh="\u4e8b\u4ef6\u6570",
        center_pattern_count_zh="\u4e2d\u5fc3\u89c4\u5f8b\u6570",
        query_count_zh=None,
        clue_count_zh=None,
        coverage_zh="\u5b8c\u6574",
        coverage_state_zh="\u8986\u76d6\u5b8c\u6574",
        denominator_zh="\u53d7\u8bd5\u8005",
        rate_zh="50%",
        disposition_zh="\u9633\u6027",
        lifecycle_zh=None,
    )


def _build_d09_hotspot(label: str, site: str, subject: str,
                       members: Tuple[str, ...],
                       priority: str) -> D09HotspotProjection:
    return D09HotspotProjection(
        projection_id=("S3-HOTSPOT-" + label),
        site_ref=site,
        evaluation_window_instance_ref=SYNTHETIC_WINDOW_REF,
        subject_ref=subject,
        member_risk_refs=tuple(sorted(members)),
        gap_member_refs=(),
        monitoring_priority=priority,
        priority_rule_ref="S3-PRIORITY-RULE-001",
        visit_or_time_anchor_refs=(),
        source_locator_refs=(),
        projectability_decision_ref=("S3-VIS-DECISION-" + label),
    )


def _build_d10_audience(scope: str, members: Tuple[str, ...],
                        site: str) -> D10AudienceProjection:
    return D10AudienceProjection(
        audience_scope_id=scope,
        projectable_member_refs=tuple(sorted(members)),
        evaluation_member_refs=tuple(sorted(members)),
        hidden_member_refs=(),
        projectable_site_refs=(site,),
        evaluation_site_refs=(site,),
        hidden_site_refs=(),
        hidden_member_count=0,
        hidden_site_count=0,
        audience_payload_present=True,
        risk_marker_present=True,
        query_present=False,
        hotspot_present=True,
        deep_link_present=False,
        rate_projection_state="permitted",
        visible_n=len(members),
        eligible_n=len(members),
        coverage_state="complete",
        coverage_zh="\u5b8c\u6574",
        disposition_zh="\u9633\u6027",
        reason_zh="\u5408\u6210\u79bb\u7ebf\u6d4b\u8bd5",
        disclosure_leak_present=False,
    )


def _build_d10_counts(label: str, members: Tuple[str, ...],
                      site: str) -> D10ProjectionCountSurface:
    count = len(members)
    return D10ProjectionCountSurface(
        evaluation_window_instance_ref=SYNTHETIC_WINDOW_REF,
        individual_risk_count=count,
        affected_subject_count=count,
        event_or_outcome_count=1,
        center_pattern_count=0,
        affected_site_count=1,
        project_signal_count=1,
        clue_count=0,
        query_count=0,
        numerator_member_count=count,
        hidden_member_count=0,
        hidden_site_count=0,
        visible_individual_risk_count=count,
        visible_affected_subject_count=count,
        visible_event_or_outcome_count=1,
        visible_center_pattern_count=0,
        visible_affected_site_count=1,
        event_count_disabled=False,
        site_count_disabled=False,
        visible_n=count,
        eligible_n=count,
        rate_projection_state="permitted",
        individual_risk_zh="\u4e2a\u4f53\u98ce\u9669",
        affected_subjects_zh="\u53d7\u5f71\u54cd\u53d7\u8bd5\u8005",
        event_or_outcome_zh="\u4e8b\u4ef6\u6570",
        center_pattern_zh="\u4e2d\u5fc3\u89c4\u5f8b\u6570",
        affected_site_zh="\u53d7\u5f71\u54cd\u5e16\u5757",
        project_signal_zh="\u9879\u76ee\u4fe1\u53f7",
        clue_zh=None,
        query_count_zh="\u67e5\u8be2\u6570",
        coverage_zh="\u5b8c\u6574",
        coverage_state_zh="\u8986\u76d6\u5b8c\u6574",
        denominator_zh="\u53d7\u8bd5\u8005",
        rate_zh="50%",
        disposition_zh="\u9633\u6027",
    )


def _build_d10_version(label: str) -> D10ProjectionVersion:
    return D10ProjectionVersion(
        projection_version_id=("S3-PROJ-VERSION-" + label),
        project_ref=SYNTHETIC_PROJECT_REF,
        run_ref=SYNTHETIC_RUN_REF,
        snapshot_ref=SYNTHETIC_SNAPSHOT_REF,
        cutoff_ref=SYNTHETIC_CUTOFF_REF,
        source_evaluation_content_identities=(
            _fixture_hash("evaluation." + label),),
        source_ledger_hashes=(_fixture_hash("ledger." + label),),
        source_risk_refs=(_fixture_hash("risk." + label),),
        visibility_decision_refs=("S3-VIS-DECISION-" + label,),
        audience_contract_ref=SYNTHETIC_AUDIENCE_CONTRACT_ID,
        supersedes_projection_ref=None,
        projection_content_hash=_fixture_hash("projection." + label),
        projection_version_content_hash=_fixture_hash("pid." + label),
    )


def _build_d10_change_section() -> D10ChangeSection:
    return D10ChangeSection(
        change_kind="continued",
        change_cause="data",
        lineage_relation="continued_from_data_revision",
        analysis_only=False,
        fresh_full=False,
        replay=False,
        change_kind_zh="\u6301\u7eed",
        change_cause_zh="\u6570\u636e\u53d8\u5316",
        lineage_zh="\u6570\u636e\u4fee\u8ba2\u7eed\u63a5",
        narrative_zh="\u672c\u7248\u76f8\u5bf9\u4e0a\u4e00\u53ef\u6bd4\u7248\u672c\u4e3a\u6301\u7eed\u72b6\u6001\u3002",
    )


def _build_d10_center_row(site: str, members: Tuple[str, ...],
                          ) -> D10CenterPatternRow:
    return D10CenterPatternRow(
        site_ref=site,
        site_activation_state="active",
        member_count=len(members),
        affected_subject_count=len(members),
        denominator_value=8,
        rate_zh="25%",
        warning_codes=(),
        coverage_state="complete",
    )


def _build_d10_hotspot(label: str, site: str, subject: str,
                       members: Tuple[str, ...],
                       priority: str) -> D10HotspotProjection:
    return D10HotspotProjection(
        projection_id=("S3-HOTSPOT-" + label),
        site_ref=site,
        evaluation_window_instance_ref=SYNTHETIC_WINDOW_REF,
        subject_ref=subject,
        member_refs=tuple(sorted(members)),
        monitoring_priority=priority,
        source_locator_refs=(),
        projectability_decision_ref=("S3-VIS-DECISION-" + label),
    )


def _build_d10_trend(label: str) -> D10TrendSurface:
    return D10TrendSurface(
        trend_surface_present=False,
        signal_kind="symptom",
        evaluation_window_instance_ref=SYNTHETIC_WINDOW_REF,
        window_text_zh="",
        analysis_population_ref=None,
        denominator_kind="treated_subjects",
        denominator_value=0,
        estimate_kind=None,
        exposure_definition_ref=None,
        coding_dictionary_ref=None,
        severity_scale_ref=None,
        endpoint_definition_ref=None,
        estimand_ref=None,
        missing_data_rule_ref=None,
        intercurrent_event_rule_ref=None,
        treatment_role_authority_ref=None,
        small_sample=False,
        limited_evidence=False,
        limited_reason=None,
        trend_note_zh="",
    )


@dataclass(frozen=True)
class S3SyntheticUnit:
    """One synthetic authority unit: the R4 public bundle (packet_fixture),
    the R5 receipt, the closed clinical domain and the unit identity."""

    kind: str  # "d09" | "d10"
    unit_ref: str
    bundle: Any
    receipt: R5AuthorityReceipt
    clinical_domain: str
    marker_kind: str


@dataclass(frozen=True)
class S3AuthorityView:
    """Lightweight, non-validating authority view of the packet collections.

    The renderer-neutral projectors read ONLY the authority collections, so
    they may run over a full ``R5S3AuthorityPacket`` or over this view during
    assembly (before the audience payload -- and therefore a valid packet --
    exists).  The view never carries a self-reported payload: the projected
    audience surface is rebuilt from the authorities, never echoed."""

    authority_units: Tuple[R5S3AuthorityUnitTagged, ...]
    aggregate_receipt_set: R5S3AggregateReceiptSetIdentity
    risk_lifecycle_authorities: Tuple[R5S3RiskLifecycleAuthority, ...]
    closure_authorities: Tuple[R5S3ClosureAuthority, ...]
    clinical_domain_authorities: Tuple[R5S3ClinicalDomainAuthority, ...]
    denominator_authorities: Tuple[R5S3DenominatorAuthority, ...]
    layer_membership_authorities: Tuple[R5S3LayerMembershipAuthority, ...]
    cutoff_authorities: Tuple[R5S3CutoffAuthority, ...]
    evaluation_limit_authorities: Tuple[R5S3EvaluationLimitAuthority, ...]
    coverage_authorities: Tuple[R5S3CoverageAuthority, ...]
    change_cause_mixture_authorities: Tuple[
        R5S3ChangeCauseMixtureAuthority, ...]

    @staticmethod
    def from_packet(packet: R5S3AuthorityPacket) -> "S3AuthorityView":
        """Build the authority view from a full typed packet (the view's only
        factory; the packet's payload is never read)."""
        return S3AuthorityView(
            authority_units=packet.authority_units,
            aggregate_receipt_set=packet.aggregate_receipt_set,
            risk_lifecycle_authorities=packet.risk_lifecycle_authorities,
            closure_authorities=packet.closure_authorities,
            clinical_domain_authorities=packet.clinical_domain_authorities,
            denominator_authorities=packet.denominator_authorities,
            layer_membership_authorities=packet.layer_membership_authorities,
            cutoff_authorities=packet.cutoff_authorities,
            evaluation_limit_authorities=packet.evaluation_limit_authorities,
            coverage_authorities=packet.coverage_authorities,
            change_cause_mixture_authorities=(
                packet.change_cause_mixture_authorities),
        )


def build_synthetic_units() -> Tuple[S3SyntheticUnit, ...]:
    """Deterministic synthetic S3 units (packet_fixture provenance): the
    public D09/D10 projection objects are constructed exactly and read-only;
    every S3-owned hash is recomputed by the builder, never echoed."""
    # --- D10 high project signal ------------------------------------------
    d10_marker = _build_d10_marker("d10-hi", SYNTHETIC_MEMBERS_D10)
    d10_handoff = _build_d10_handoff(
        "d10-hi", "continue", "high", SYNTHETIC_MEMBERS_D10,
        SYNTHETIC_PRIOR_INSTANCE_D10)
    d10_audience = _build_d10_audience("S3-SCOPE-D10-001",
                                       SYNTHETIC_MEMBERS_D10,
                                       SYNTHETIC_SITE_D10)
    d10_counts = _build_d10_counts("d10-hi", SYNTHETIC_MEMBERS_D10,
                                   SYNTHETIC_SITE_D10)
    d10_version = _build_d10_version("d10-hi")
    d10_center = _build_d10_center_row(SYNTHETIC_SITE_D10,
                                       SYNTHETIC_MEMBERS_D10)
    d10_hotspot = _build_d10_hotspot("D10-001", SYNTHETIC_SITE_D10,
                                     "S3-SUBJ-D10-001", SYNTHETIC_MEMBERS_D10,
                                     "high")
    d10_trend = _build_d10_trend("d10-hi")
    d10_proj = D10ProjectProjection(
        projection_id=("S3-PROJECTION-D10-001"),
        projection_version_ref=d10_version.projection_version_id,
        change_section=_build_d10_change_section(),
        center_distribution=(d10_center,),
        trend_surface=d10_trend,
        warning_markers=(),
        risk_marker_ref=d10_marker.marker_id,
        hotspot_site_refs=(SYNTHETIC_SITE_D10,),
        hotspot_subject_refs=("S3-SUBJ-D10-001",),
        count_surface_ref=_fixture_hash("count.d10-hi"),
        coverage_refs=(),
        deep_link_target_refs=(),
        query_draft_ref=None,
        r2_handoff_ref=d10_handoff.handoff_id,
        audience_text_ref=SYNTHETIC_AUDIENCE_CONTRACT_ID,
        projection_content_hash=_fixture_hash("projection.d10-hi"),
    )
    d10_bundle = D10ProjectionBundle(
        audience=d10_audience,
        counts=d10_counts,
        version=d10_version,
        change_section=d10_proj.change_section,
        center_distribution=(d10_center,),
        trend_surface=d10_trend,
        warning_markers=(),
        risk_marker=d10_marker,
        hotspots=(d10_hotspot,),
        deep_links=(),
        query_draft=None,
        r2_handoff=d10_handoff,
        project_projection=d10_proj,
    )

    # --- D09 low center pattern -------------------------------------------
    d09_low_marker = _build_d09_marker("d09-lo", SYNTHETIC_MEMBERS_D09_LOW)
    d09_low_handoff = _build_d09_handoff(
        "d09-lo", "create", "low", SYNTHETIC_MEMBERS_D09_LOW, None, None)
    d09_low_audience = _build_d09_audience("S3-SCOPE-D09-001",
                                           SYNTHETIC_MEMBERS_D09_LOW,
                                           SYNTHETIC_SITE_D09_LOW)
    d09_low_counts = _build_d09_counts("d09-lo", SYNTHETIC_MEMBERS_D09_LOW)
    d09_low_hotspot = _build_d09_hotspot("D09-LOW-001", SYNTHETIC_SITE_D09_LOW,
                                         "S3-SUBJ-D09-LOW-001",
                                         SYNTHETIC_MEMBERS_D09_LOW, "low")
    d09_low_bundle = D09ProjectionBundle(
        audience=d09_low_audience,
        counts=d09_low_counts,
        risk_marker=d09_low_marker,
        hotspots=(d09_low_hotspot,),
        deep_links=(),
        query_draft=None,
        r2_handoff=d09_low_handoff,
    )

    # --- D09 resolved center pattern --------------------------------------
    d09_res_marker = _build_d09_marker("d09-res", SYNTHETIC_MEMBERS_D09_RESOLVED)
    d09_res_prior = D09_MARKER_PREFIX + d09_res_marker.marker_id
    d09_res_handoff = _build_d09_handoff(
        "d09-res", "continue", "medium", SYNTHETIC_MEMBERS_D09_RESOLVED,
        SYNTHETIC_PRIOR_INSTANCE_D09_RESOLVED, d09_res_prior)
    d09_res_audience = _build_d09_audience("S3-SCOPE-D09-002",
                                           SYNTHETIC_MEMBERS_D09_RESOLVED,
                                           SYNTHETIC_SITE_D09_RESOLVED)
    d09_res_counts = _build_d09_counts("d09-res",
                                       SYNTHETIC_MEMBERS_D09_RESOLVED)
    d09_res_hotspot = _build_d09_hotspot(
        "D09-RES-001", SYNTHETIC_SITE_D09_RESOLVED,
        "S3-SUBJ-D09-RES-001", SYNTHETIC_MEMBERS_D09_RESOLVED, "medium")
    d09_res_bundle = D09ProjectionBundle(
        audience=d09_res_audience,
        counts=d09_res_counts,
        risk_marker=d09_res_marker,
        hotspots=(d09_res_hotspot,),
        deep_links=(),
        query_draft=None,
        r2_handoff=d09_res_handoff,
    )

    return (
        S3SyntheticUnit("d10", SYNTHETIC_UNIT_D10_REF, d10_bundle,
                        _build_receipt("d10", "S3-U-D10-001"),
                        SYNTHETIC_DOMAIN_D10, "d10"),
        S3SyntheticUnit("d09", SYNTHETIC_UNIT_D09_LOW_REF, d09_low_bundle,
                        _build_receipt("d09", "S3-U-D09-001"),
                        SYNTHETIC_DOMAIN_D09_LOW, "d09"),
        S3SyntheticUnit("d09", SYNTHETIC_UNIT_D09_RESOLVED_REF,
                        d09_res_bundle,
                        _build_receipt("d09", "S3-U-D09-002"),
                        SYNTHETIC_DOMAIN_D09_RESOLVED, "d09"),
    )


# ---------------------------------------------------------------------------
# Named supplemental authority builders (exact typed; hashes recomputed)
# ---------------------------------------------------------------------------


def build_clinical_domain_authority(
    authority_id: str, clinical_domain: str,
    receipt: R5AuthorityReceipt,
) -> R5S3ClinicalDomainAuthority:
    """Synthetic/offline clinical-domain authority bound to one complete
    receipt (visibility decision + source pairs exact, verbatim)."""
    obj = {
        "authority_id": authority_id,
        "clinical_domain": clinical_domain,
        "receipt_hash": receipt_content_hash(receipt),
        "receipt_ref": authority_receipt_ref(receipt),
        "visibility_decision_id": receipt.visibility_decision_id,
        "visibility_decision_hash": receipt.visibility_decision_hash,
        "source_revision_content_pairs":
            receipt.source_revision_content_pairs,
        "offline_test_only": True,
    }
    return R5S3ClinicalDomainAuthority(
        content_hash=s3_sha256(s3_canonical_bytes(obj)), **obj)


def build_denominator_authority(
    authority_id: str,
    denominator_kind: str, denominator_state: str,
    denominator_value: object,
    measure_unit: str,
    member_refs: Tuple[str, ...],
    exclusion_refs: Tuple[str, ...],
    receipt: R5AuthorityReceipt,
) -> R5S3DenominatorAuthority:
    """Quantified supplemental: exact kind/state/value/unit plus exact member
    and exclusion refs, hashes recomputed from the receipt."""
    obj = {
        "authority_id": authority_id,
        "denominator_kind": denominator_kind,
        "denominator_state": denominator_state,
        "denominator_value": denominator_value,
        "measure_unit": measure_unit,
        "member_refs": tuple(sorted(member_refs)),
        "exclusion_refs": tuple(sorted(exclusion_refs)),
        "receipt_hash": receipt_content_hash(receipt),
        "receipt_ref": authority_receipt_ref(receipt),
        "visibility_decision_id": receipt.visibility_decision_id,
        "visibility_decision_hash": receipt.visibility_decision_hash,
        "source_revision_content_pairs":
            receipt.source_revision_content_pairs,
        "offline_test_only": True,
    }
    return R5S3DenominatorAuthority(
        content_hash=s3_sha256(s3_canonical_bytes(obj)), **obj)


def build_layer_membership_authority(
    authority_id: str,
    layer: str, membership_state: str,
    member_refs: Tuple[str, ...],
    source_count_value: object,
    source_count_ref: str,
    disabled_state: str,
    receipt: R5AuthorityReceipt,
) -> R5S3LayerMembershipAuthority:
    """Quantified supplemental: exact layer / membership state / projectable
    member refs / non-null source count value and ref / disabled state.  The
    source-count value is the verbatim public count leaf (never inferred)."""
    obj = {
        "authority_id": authority_id,
        "layer": layer,
        "membership_state": membership_state,
        "member_refs": tuple(sorted(member_refs)),
        "source_count_value": source_count_value,
        "source_count_ref": source_count_ref,
        "disabled_state": disabled_state,
        "receipt_hash": receipt_content_hash(receipt),
        "receipt_ref": authority_receipt_ref(receipt),
        "visibility_decision_id": receipt.visibility_decision_id,
        "visibility_decision_hash": receipt.visibility_decision_hash,
        "source_revision_content_pairs":
            receipt.source_revision_content_pairs,
        "offline_test_only": True,
    }
    return R5S3LayerMembershipAuthority(
        content_hash=s3_sha256(s3_canonical_bytes(obj)), **obj)


def build_cutoff_authority(
    authority_id: str, cutoff_ref: Optional[str],
    receipt: R5AuthorityReceipt,
) -> R5S3CutoffAuthority:
    """Supplemental carrying the exact cutoff bound verbatim from the public
    projection version / receipt."""
    obj = {
        "authority_id": authority_id,
        "cutoff_ref": cutoff_ref,
        "receipt_hash": receipt_content_hash(receipt),
        "receipt_ref": authority_receipt_ref(receipt),
        "visibility_decision_id": receipt.visibility_decision_id,
        "visibility_decision_hash": receipt.visibility_decision_hash,
        "source_revision_content_pairs":
            receipt.source_revision_content_pairs,
        "offline_test_only": True,
    }
    return R5S3CutoffAuthority(
        content_hash=s3_sha256(s3_canonical_bytes(obj)), **obj)


def build_evaluation_limit_authority(
    authority_id: str,
    evaluation_limit_refs: Tuple[str, ...],
    evaluation_limit_values: Tuple[str, ...],
    receipt: R5AuthorityReceipt,
) -> R5S3EvaluationLimitAuthority:
    """Supplemental carrying closed evaluation-limit refs/values verbatim."""
    obj = {
        "authority_id": authority_id,
        "evaluation_limit_refs": tuple(sorted(evaluation_limit_refs)),
        "evaluation_limit_values": tuple(sorted(evaluation_limit_values)),
        "receipt_hash": receipt_content_hash(receipt),
        "receipt_ref": authority_receipt_ref(receipt),
        "visibility_decision_id": receipt.visibility_decision_id,
        "visibility_decision_hash": receipt.visibility_decision_hash,
        "source_revision_content_pairs":
            receipt.source_revision_content_pairs,
        "offline_test_only": True,
    }
    return R5S3EvaluationLimitAuthority(
        content_hash=s3_sha256(s3_canonical_bytes(obj)), **obj)


def build_coverage_authority(
    authority_id: str, coverage_state: str,
    receipt: R5AuthorityReceipt,
) -> R5S3CoverageAuthority:
    """Supplemental carrying the closed coverage state (never
    ``not_evaluable``)."""
    obj = {
        "authority_id": authority_id,
        "coverage_state": coverage_state,
        "receipt_hash": receipt_content_hash(receipt),
        "receipt_ref": authority_receipt_ref(receipt),
        "visibility_decision_id": receipt.visibility_decision_id,
        "visibility_decision_hash": receipt.visibility_decision_hash,
        "source_revision_content_pairs":
            receipt.source_revision_content_pairs,
        "offline_test_only": True,
    }
    return R5S3CoverageAuthority(
        content_hash=s3_sha256(s3_canonical_bytes(obj)), **obj)


def build_change_cause_mixture_authority(
    authority_id: str, causes: Tuple[str, ...],
    receipt: R5AuthorityReceipt,
) -> R5S3ChangeCauseMixtureAuthority:
    """Supplemental carrying a closed change-cause mixture (at least two
    sorted-unique causes; a single D10 cause never promotes to a mixture)."""
    obj = {
        "authority_id": authority_id,
        "causes": tuple(sorted(causes)),
        "receipt_hash": receipt_content_hash(receipt),
        "receipt_ref": authority_receipt_ref(receipt),
        "visibility_decision_id": receipt.visibility_decision_id,
        "visibility_decision_hash": receipt.visibility_decision_hash,
        "source_revision_content_pairs":
            receipt.source_revision_content_pairs,
        "offline_test_only": True,
    }
    return R5S3ChangeCauseMixtureAuthority(
        content_hash=s3_sha256(s3_canonical_bytes(obj)), **obj)


def build_closure_authority(
    closure_authority_id: str,
    closure_decision_id: str,
    prior_public_risk_identity_ref: str,
    prior_risk_instance_ref: str,
    receipt: R5AuthorityReceipt,
) -> R5S3ClosureAuthority:
    """Closure authority for one resolved lifecycle: the prior identity and
    prior instance refs are the public R2 handoff values verbatim; the
    closure decision hash is recomputed canonically (never caller-supplied)."""
    decision_body = {
        "closure_decision_id": closure_decision_id,
        "decision_kind": "resolved",
        "prior_public_risk_identity_ref": prior_public_risk_identity_ref,
        "prior_risk_instance_ref": prior_risk_instance_ref,
    }
    obj = {
        "closure_authority_id": closure_authority_id,
        "closure_decision_id": closure_decision_id,
        "closure_decision_hash": _h(decision_body),
        "prior_public_risk_identity_ref": prior_public_risk_identity_ref,
        "prior_risk_instance_ref": prior_risk_instance_ref,
        "receipt_hash": receipt_content_hash(receipt),
        "receipt_ref": authority_receipt_ref(receipt),
        "visibility_decision_id": receipt.visibility_decision_id,
        "visibility_decision_hash": receipt.visibility_decision_hash,
        "source_revision_content_pairs":
            receipt.source_revision_content_pairs,
        "decision_kind": "resolved",
        "offline_test_only": True,
    }
    return R5S3ClosureAuthority(
        content_hash=s3_sha256(s3_canonical_bytes(obj)), **obj)


def build_lifecycle_authority(
    authority_id: str,
    marker_kind: str,
    marker: Any,
    handoff: Any,
    clinical_domain_ref: str,
    receipt: R5AuthorityReceipt,
    lifecycle_state: Optional[str] = None,
    closure_authority_ref: Optional[str] = None,
    prior_marker_identity_ref: Optional[str] = None,
) -> R5S3RiskLifecycleAuthority:
    """Per-marker lifecycle authority derived from the public marker and R2
    handoff: severity EQUALS the public ``monitoring_priority`` (critical /
    unknown / unmapped fail closed), the lifecycle state comes from the
    action table (or ``resolved`` when a closure is supplied), member
    expansion equals the public marker member set, and the marker identity
    ref is the kind-prefixed public marker id."""
    priority = handoff.monitoring_priority
    if priority not in S3_SEVERITIES[1:]:
        raise S3AuthorityBuilderError(
            "lifecycle severity must be high/medium/low (critical/unknown/"
            f"unmapped fail closed), got {priority!r}")
    if marker_kind not in S3_MARKER_KINDS:
        raise S3AuthorityBuilderError(
            f"unknown marker_kind {marker_kind!r}")
    marker_identity_ref = (D09_MARKER_PREFIX if marker_kind == "d09"
                           else D10_MARKER_PREFIX) + marker.marker_id
    if closure_authority_ref is not None:
        state = "resolved"
    elif lifecycle_state is not None:
        state = lifecycle_state
    else:
        mapping = LIFECYCLE_STATE_TABLE.get(handoff.action)
        if mapping is None:
            raise S3AuthorityBuilderError(
                f"unknown handoff action {handoff.action!r}")
        state = mapping["state"]
    obj = {
        "authority_id": authority_id,
        "marker_kind": marker_kind,
        "marker_identity_ref": marker_identity_ref,
        "marker_id": marker.marker_id,
        "marker_content_hash": marker.content_hash,
        "receipt_hash": receipt_content_hash(receipt),
        "receipt_ref": authority_receipt_ref(receipt),
        "visibility_decision_id": receipt.visibility_decision_id,
        "visibility_decision_hash": receipt.visibility_decision_hash,
        "source_revision_content_pairs":
            receipt.source_revision_content_pairs,
        "clinical_domain_ref": clinical_domain_ref,
        "severity": priority,
        "lifecycle_state": state,
        "lifecycle_action": handoff.action,
        "r2_handoff_id": handoff.handoff_id,
        "r2_handoff_ref": "r2:" + handoff.handoff_id,
        "member_expansion_refs": tuple(sorted(marker.member_refs)),
        "closure_authority_ref": closure_authority_ref,
        "prior_marker_identity_ref": prior_marker_identity_ref,
        "offline_test_only": True,
    }
    return R5S3RiskLifecycleAuthority(
        content_hash=s3_sha256(s3_canonical_bytes(obj)), **obj)


# ---------------------------------------------------------------------------
# Unit builder
# ---------------------------------------------------------------------------


def build_authority_unit(
    unit: S3SyntheticUnit,
    clinical_domain_authority_ref: str,
) -> R5S3AuthorityUnitTagged:
    """Consume one R4 public projection bundle + receipt and build the tagged
    authority unit (variant payload, projectable/hidden planes, receipt and
    content hashes).  Neither the medical risk nor any member set is
    recomputed: the payload leaves are the R4 public objects verbatim."""
    receipt = unit.receipt
    if unit.kind == "d09":
        bundle = unit.bundle
        payload = R5S3D09CenterPatternUnit(
            audience=bundle.audience,
            counts=bundle.counts,
            risk_marker=bundle.risk_marker,
            r2_handoff=bundle.r2_handoff,
            hotspots=bundle.hotspots,
            clinical_domain_authority_ref=clinical_domain_authority_ref,
            source_revision_content_pairs=receipt.source_revision_content_pairs,
        )
        variant_kind = "d09_center_pattern_unit"
        projectable = tuple(sorted(bundle.audience.projectable_member_refs))
        hidden_member = tuple(sorted(bundle.audience.hidden_member_refs))
        hidden_site: Tuple[str, ...] = ()
    else:
        bundle = unit.bundle
        payload = R5S3D10ProjectUnit(
            audience=bundle.audience,
            counts=bundle.counts,
            version=bundle.version,
            change_section=bundle.change_section,
            center_distribution=bundle.center_distribution,
            risk_marker=bundle.risk_marker,
            r2_handoff=bundle.r2_handoff,
            hotspots=bundle.hotspots,
            project_projection=bundle.project_projection,
            clinical_domain_authority_ref=clinical_domain_authority_ref,
            source_revision_content_pairs=receipt.source_revision_content_pairs,
        )
        variant_kind = "d10_project_unit"
        projectable = tuple(sorted(bundle.audience.projectable_member_refs))
        hidden_member = tuple(sorted(bundle.audience.hidden_member_refs))
        hidden_site = tuple(sorted(bundle.audience.hidden_site_refs))

    base = {
        "unit_ref": unit.unit_ref,
        "variant_kind": variant_kind,
        "authority_receipt": receipt,
        "receipt_content_hash": receipt_content_hash(receipt),
        "projectable_member_refs": projectable,
        "hidden_member_refs": hidden_member,
        "hidden_site_refs": hidden_site,
        "source_unit_refs": (SYNTHETIC_SOURCE_FILE,),
        "d09_variant_payload": (payload if unit.kind == "d09" else None),
        "d10_variant_payload": (payload if unit.kind == "d10" else None),
    }
    content_hash = s3_sha256(s3_canonical_bytes(base))
    return R5S3AuthorityUnitTagged(content_hash=content_hash, **base)


# ---------------------------------------------------------------------------
# Aggregate receipt-set identity
# ---------------------------------------------------------------------------


def build_aggregate_receipt_set(
    units: Tuple[R5S3AuthorityUnitTagged, ...],
) -> R5S3AggregateReceiptSetIdentity:
    """Canonical aggregate receipt-set identity over the sorted unique unit
    receipt refs and risk marker identity hashes (hashes recomputed)."""
    receipt_refs = tuple(sorted({
        RECEIPT_REF_PREFIX + unit.receipt_content_hash
        for unit in units}))
    marker_hashes = tuple(sorted({
        unit_variant_payload(unit).risk_marker.content_hash
        for unit in units
        if unit_variant_payload(unit).risk_marker is not None}))
    receipts = [unit.authority_receipt for unit in units]
    identities = {(r.project_ref, r.run_ref, r.snapshot_ref, r.cutoff_ref,
                   r.audience_contract_id) for r in receipts}
    if len(identities) != 1:
        raise S3AuthorityBuilderError(
            "units do not share one project/run/snapshot/cutoff/audience "
            f"identity: {identities!r}")
    identity, = identities
    body = {
        "unit_receipt_refs": list(receipt_refs),
        "risk_marker_identity_hashes": list(marker_hashes),
        "project_ref": identity[0],
        "run_ref": identity[1],
        "snapshot_ref": identity[2],
        "cutoff_ref": identity[3],
        "audience_contract_id": identity[4],
    }
    aggregate_id = "aggregate:" + _h(body)
    full = dict(body)
    full["aggregate_id"] = aggregate_id
    return R5S3AggregateReceiptSetIdentity(
        content_hash=s3_sha256(s3_canonical_bytes(full)),
        aggregate_id=aggregate_id,
        unit_receipt_refs=receipt_refs,
        risk_marker_identity_hashes=marker_hashes,
        project_ref=identity[0],
        run_ref=identity[1],
        snapshot_ref=identity[2],
        cutoff_ref=identity[3],
        audience_contract_id=identity[4],
    )


# ---------------------------------------------------------------------------
# Low-risk cluster
# ---------------------------------------------------------------------------


def build_low_risk_cluster(
    lifecycle: R5S3RiskLifecycleAuthority,
    domain: str,
    site_ref: str,
) -> Optional[R5S3LowRiskCluster]:
    """One low-risk cluster from a current+low lifecycle's public member
    expansion/domain/site authorities (never inferred from counts)."""
    if lifecycle.lifecycle_state != "current" or lifecycle.severity != "low":
        return None
    members = tuple(sorted(lifecycle.member_expansion_refs))
    if not domain or site_ref is None or not members:
        return None
    content_hash = cluster_content_hash(lifecycle.receipt_ref, domain,
                                        site_ref, members)
    return R5S3LowRiskCluster(
        cluster_ref=CLUSTER_REF_PREFIX + content_hash,
        authority_receipt_ref=lifecycle.receipt_ref,
        domain=domain,
        site_ref=site_ref,
        member_refs=members,
        content_hash=content_hash,
    )


# ---------------------------------------------------------------------------
# Renderer-neutral projection helpers (typed-packet pure functions)
# ---------------------------------------------------------------------------


def _lifecycle_site(packet: R5S3AuthorityPacket,
                    lifecycle: R5S3RiskLifecycleAuthority) -> Optional[str]:
    """Resolve the site of a lifecycle from public hotspot member<->site
    bindings (never inferred from counts)."""
    unit = next((u for u in packet.authority_units
                 if unit_variant_payload(u).risk_marker is not None
                 and unit_variant_payload(u).risk_marker.marker_id
                 == lifecycle.marker_id), None)
    if unit is None:
        return None
    variant = unit_variant_payload(unit)
    kind = "d09" if unit.variant_kind == "d09_center_pattern_unit" else "d10"
    members = set(lifecycle.member_expansion_refs)
    sites: set = set()
    for hotspot in variant.hotspots:
        if set(_hotspot_member_refs(kind, hotspot)) & members:
            sites.add(hotspot.site_ref)
    if len(sites) == 1:
        return next(iter(sites))
    return None


def _hotspot_member_refs(kind: str, hotspot: Any) -> Tuple[str, ...]:
    """D09 uses separate risk/gap fields; D10 alone uses ``member_refs``
    (type-specific read -- never a fabricated unified field)."""
    if kind == "d09":
        return tuple(sorted(set(hotspot.member_risk_refs)
                            | set(hotspot.gap_member_refs)))
    return tuple(sorted(hotspot.member_refs))


def _member_explicitly_not_projectable(
    packet: R5S3AuthorityPacket, member: str,
) -> bool:
    """A member is excluded from the projectable center-cell closure only when
    a named layer-membership supplemental explicitly marks it
    ``membership_state=not_projectable`` (empty refs alone are insufficient)."""
    for authority in packet.layer_membership_authorities:
        if authority.membership_state == "not_projectable" \
                and member in authority.member_refs:
            return True
    return False


def project_current_risk_planes(
    packet: R5S3AuthorityPacket,
    compare_declared: bool = True,
    declared: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Exact current-risk plane closure (Block 1): every current lifecycle
    with severity high/medium/low projects its marker identity or cluster
    ref exactly once; resolved lifecycles project to the resolved plane;
    low-cluster planes are rebuilt and compared bidirectionally.

    ``declared`` optionally supplies the declared current-risk surface
    (``{"high_risk_refs": ..., "medium_risk_refs": ...,
    "low_risk_cluster_refs": ..., "resolved_history_refs": ...}``) so the
    projector can run over an ``S3AuthorityView`` (during assembly, before
    a packet exists) as well as over a full typed packet (which carries its
    own ``audience_payload``)."""
    errors: list = []
    payload = None
    if declared is None:
        payload = getattr(packet, "audience_payload", None)
        if payload is not None:
            declared = {
                "high_risk_refs": payload.current_risk_set.high_risk_refs,
                "medium_risk_refs": payload.current_risk_set.medium_risk_refs,
                "low_risk_cluster_refs":
                    payload.current_risk_set.low_risk_cluster_refs,
                "resolved_history_refs":
                    payload.current_risk_set.resolved_history_refs,
            }
    declared = declared or {}

    expected_high: list = []
    expected_medium: list = []
    expected_low_lifecycles: list = []
    expected_resolved: list = []
    seen: Dict[str, str] = {}
    for lifecycle in packet.risk_lifecycle_authorities:
        ref = lifecycle.marker_identity_ref
        state = lifecycle.lifecycle_state
        severity = lifecycle.severity
        if state == "current":
            if severity not in ("high", "medium", "low"):
                errors.append("severity_not_in_enum")
                continue
            if severity == "high":
                expected_high.append(ref)
            elif severity == "medium":
                expected_medium.append(ref)
            else:
                expected_low_lifecycles.append(ref)
        elif state == "resolved":
            expected_resolved.append(ref)
        else:
            continue  # superseded / proposed_close: never a current ref
        if ref in seen:
            errors.append("current_plane_duplicate_projection")
        seen[ref] = state
    expected_high = sorted(expected_high)
    expected_medium = sorted(expected_medium)
    expected_resolved = sorted(expected_resolved)

    projected_clusters = project_low_risk_clusters(packet)
    expected_low: list = []
    for ref in expected_low_lifecycles:
        lifecycle = _lifecycle_by_ref(packet, ref)
        domain = _domain_authority_domain(
            packet, lifecycle.clinical_domain_ref)
        site = _lifecycle_site(packet, lifecycle)
        members = tuple(sorted(lifecycle.member_expansion_refs))
        matches = [cluster.cluster_ref for cluster in projected_clusters
                   if tuple(sorted(cluster.member_refs)) == members
                   and cluster.domain == domain
                   and cluster.site_ref == site
                   and cluster.authority_receipt_ref == lifecycle.receipt_ref]
        if len(matches) == 0:
            errors.append("current_plane_low_cluster_mismatch")
        elif len(matches) > 1:
            errors.append("cluster_lifecycle_unresolved")
        else:
            expected_low.append(matches[0])
    expected_low = sorted(expected_low)

    declared_high = sorted(declared.get("high_risk_refs", []))
    declared_medium = sorted(declared.get("medium_risk_refs", []))
    declared_low = sorted(declared.get("low_risk_cluster_refs", []))
    declared_resolved = sorted(declared.get("resolved_history_refs", []))

    if compare_declared:
        if expected_high != declared_high:
            errors.append("current_plane_high_mismatch")
        if expected_medium != declared_medium:
            errors.append("current_plane_medium_mismatch")
        if expected_low != declared_low:
            errors.append("current_plane_low_cluster_mismatch")
        if expected_resolved != declared_resolved:
            errors.append("current_plane_resolved_mismatch")

    # every declared ref must resolve to an authority lifecycle/cluster.
    known_lifecycle_refs = {
        lifecycle.marker_identity_ref
        for lifecycle in packet.risk_lifecycle_authorities}
    for ref in declared_high + declared_medium + declared_resolved:
        if ref not in known_lifecycle_refs:
            errors.append("current_risk_lifecycle_unresolved")
    if compare_declared:
        projected_cluster_refs = {c.cluster_ref for c in projected_clusters}
        for ref in declared_low:
            if ref not in projected_cluster_refs:
                errors.append("cluster_lifecycle_unresolved")
    return {
        "planes": {
            "high": expected_high,
            "medium": expected_medium,
            "low": expected_low,
            "resolved": expected_resolved,
            "lifecycle_plane": seen,
        },
        "errors": errors,
    }


def _lifecycle_by_ref(
    packet: R5S3AuthorityPacket, marker_identity_ref: str,
) -> R5S3RiskLifecycleAuthority:
    for lifecycle in packet.risk_lifecycle_authorities:
        if lifecycle.marker_identity_ref == marker_identity_ref:
            return lifecycle
    raise S3ContractError(
        "unknown lifecycle authority for marker identity "
        f"{marker_identity_ref!r}")


def _domain_authority_domain(
    packet: R5S3AuthorityPacket, authority_ref: str,
) -> Optional[str]:
    for authority in packet.clinical_domain_authorities:
        if authority.authority_id == authority_ref:
            return authority.clinical_domain
    return None


def project_low_risk_clusters(
    packet: R5S3AuthorityPacket,
) -> Tuple[R5S3LowRiskCluster, ...]:
    """Rebuild low-risk clusters from current+low lifecycle authorities
    (cluster ref/content hash included; the audience surface is compared, not
    echoed)."""
    clusters: list = []
    for lifecycle in packet.risk_lifecycle_authorities:
        if lifecycle.lifecycle_state != "current" \
                or lifecycle.severity != "low":
            continue
        domain = _domain_authority_domain(packet, lifecycle.clinical_domain_ref)
        site = _lifecycle_site(packet, lifecycle)
        cluster = build_low_risk_cluster(lifecycle, domain or "",
                                         site or "")
        if cluster is not None:
            clusters.append(cluster)
    return tuple(sorted(clusters, key=lambda cluster: cluster.cluster_ref))


def project_measures(packet: R5S3AuthorityPacket) -> Tuple[
        R5QuantitativeMeasure, ...]:
    """Rebuild quantitative measures from public unit authorities (verbatim
    leaves; no numerator/denominator recomputation)."""
    measures: list = []
    serial = 1
    for unit in sorted(packet.authority_units, key=lambda u: u.unit_ref):
        variant = unit_variant_payload(unit)
        if unit.variant_kind != "d10_project_unit":
            continue
        audience = variant.audience
        marker = variant.risk_marker
        if marker is None:
            continue
        members = tuple(sorted(set(marker.member_refs)
                               & set(audience.projectable_member_refs)))
        if not members:
            continue
        rows = variant.center_distribution
        denominator_value = None
        if rows:
            values = [row.denominator_value for row in rows
                      if row.denominator_value is not None]
            if values:
                denominator_value = values[0]
        if denominator_value is None:
            denominator_value = len(members)
        denominator_state = ("closed_positive" if denominator_value > 0
                             else "closed_zero")
        from decimal import Decimal
        measures.append(R5QuantitativeMeasure(
            authoritative_value_ref=f"measure.ir.{serial}",
            authority_receipt_ref=RECEIPT_REF_PREFIX
            + unit.receipt_content_hash,
            coverage_state=audience.coverage_state if audience.coverage_state
            in ("complete", "partial", "truncated", "unknown",
                "not_applicable") else "unknown",
            cutoff_ref=variant.version.cutoff_ref
            if variant.version.cutoff_ref else SYNTHETIC_CUTOFF_REF,
            denominator_exclusion_refs=(),
            denominator_kind="treated_subjects",
            denominator_member_refs=members,
            denominator_state=denominator_state,
            denominator_value=Decimal(denominator_value),
            evaluation_limit_refs=(
                SYNTHETIC_EVALUATION_LIMIT_D10,),
            numerator_kind="individual_risk",
            numerator_member_refs=members,
            numerator_value=Decimal(variant.counts.individual_risk_count),
            rate_state=audience.rate_projection_state
            if audience.rate_projection_state in ("permitted", "qualified",
                                                  "not_evaluable")
            else "not_evaluable",
            unit="subject",
        ))
        serial += 1
    return tuple(measures)


def _measure_refs_for_cell(
    measures: Tuple[R5QuantitativeMeasure, ...], cell_members: set,
) -> Tuple[str, ...]:
    return tuple(sorted({
        measure.authoritative_value_ref for measure in measures
        if set(measure.numerator_member_refs) & cell_members}))


def project_center_cells(packet: R5S3AuthorityPacket) -> Dict[str, Any]:
    """Exact center-cell closure (Block 2): cells rebuilt from public hotspot
    member<->site bindings + lifecycle/marker/domain authorities.  D09 marker
    members are pattern refs, D10 marker members are individual refs; a single
    member is never promoted to a pattern (center-cell pattern upgrade gate
    is enforced at the packet-oracle level)."""
    errors: list = []
    measures = project_measures(packet)
    member_lifecycle: Dict[str, R5S3RiskLifecycleAuthority] = {}
    member_kind: Dict[str, str] = {}
    member_severity: Dict[str, str] = {}
    member_domain: Dict[str, str] = {}
    for lifecycle in packet.risk_lifecycle_authorities:
        if lifecycle.lifecycle_state != "current":
            continue
        for member in lifecycle.member_expansion_refs:
            if member in member_lifecycle:
                errors.append("center_cell_duplicate_member")
                continue
            member_lifecycle[member] = lifecycle
            member_kind[member] = lifecycle.marker_kind
            member_severity[member] = lifecycle.severity
            member_domain[member] = _domain_authority_domain(
                packet, lifecycle.clinical_domain_ref)

    member_site: Dict[str, str] = {}
    for unit in packet.authority_units:
        kind = ("d09" if unit.variant_kind == "d09_center_pattern_unit"
                else "d10")
        variant = unit_variant_payload(unit)
        for hotspot in variant.hotspots:
            for member in _hotspot_member_refs(kind, hotspot):
                if member in member_site and member_site[member] != \
                        hotspot.site_ref:
                    errors.append("center_cell_site_mismatch")
                member_site[member] = hotspot.site_ref

    for member in member_lifecycle:
        if member not in member_site \
                and not _member_explicitly_not_projectable(packet, member):
            errors.append("center_cell_site_mismatch")

    cells: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for member, lifecycle in member_lifecycle.items():
        site = member_site.get(member)
        domain = member_domain.get(member)
        if site is None or domain is None:
            continue
        key = (site, domain)
        cell = cells.setdefault(key, {
            "site_ref": site, "domain": domain,
            "individual_risk_refs": [], "pattern_refs": [],
            "member_severities": []})
        if member_kind.get(member) == "d10":
            cell["individual_risk_refs"].append(member)
        elif member_kind.get(member) == "d09":
            cell["pattern_refs"].append(member)
        else:
            errors.append("center_cell_classification_mismatch")
        sev = member_severity.get(member)
        if sev:
            cell["member_severities"].append(sev)

    expected_cells: list = []
    for (site, domain), cell in sorted(cells.items()):
        cell["individual_risk_refs"] = sorted(cell["individual_risk_refs"])
        cell["pattern_refs"] = sorted(cell["pattern_refs"])
        sevs = cell.pop("member_severities")
        cell["severity"] = ("high" if "high" in sevs
                            else "medium" if "medium" in sevs
                            else "low" if sevs else None)
        cell_members = set(cell["individual_risk_refs"]) | set(
            cell["pattern_refs"])
        cell["measure_refs"] = list(
            _measure_refs_for_cell(measures, cell_members))
        expected_cells.append((
            (site, domain),
            R5CenterMapCell(
                domain=domain,
                individual_risk_refs=tuple(cell["individual_risk_refs"]),
                measure_refs=tuple(cell["measure_refs"]),
                pattern_refs=tuple(cell["pattern_refs"]),
                severity=cell["severity"] if cell["severity"] else "low",
                site_ref=site,
            ),
        ))
    expected_cell_objects = [cell for _key, cell in expected_cells]
    # stable site order = NFC-stable projectable site identity ascending.
    projectable_sites = sorted({cell.site_ref
                                for cell in expected_cell_objects})
    return {
        "cells": tuple(expected_cell_objects),
        "stable_site_order": tuple(projectable_sites),
        "errors": errors,
    }


def project_change_bands(packet: R5S3AuthorityPacket) -> Tuple[
        R5ChangeBand, ...]:
    """Change-band rows from lifecycle, handoff and receipt inputs (closed
    kind emission: resolved never inferred from the change section alone)."""
    severity_order = {"high": 0, "medium": 1, "low": 2}
    rows: list = []
    for lifecycle in packet.risk_lifecycle_authorities:
        unit = next((u for u in packet.authority_units
                     if unit_variant_payload(u).risk_marker is not None
                     and unit_variant_payload(u).risk_marker.marker_id
                     == lifecycle.marker_id), None)
        if unit is None:
            continue
        receipt = unit.authority_receipt
        variant = unit_variant_payload(unit)
        section = getattr(variant, "change_section", None)
        if lifecycle.lifecycle_state == "resolved":
            change_kind = "resolved"
        elif section is not None and section.change_kind:
            change_kind = section.change_kind
        elif lifecycle.lifecycle_action == "create":
            change_kind = "initial_current"
        else:
            change_kind = "continued"
        change_cause = section.change_cause if section is not None else None
        row = R5ChangeBand(
            authority_receipt_ref=RECEIPT_REF_PREFIX
            + unit.receipt_content_hash,
            change_cause=change_cause,
            change_kind=change_kind,
            current_snapshot_ref=receipt.snapshot_ref,
            prior_snapshot_ref=None,
            risk_ref=lifecycle.marker_identity_ref,
        )
        rank = (0 if change_kind != "resolved" else 3,
                severity_order.get(lifecycle.severity, 9),
                lifecycle.marker_identity_ref)
        rows.append((rank, row))
    return tuple(row for _rank, row in sorted(rows, key=lambda item: item[0]))


def _source_receipt_ref(packet: R5S3AuthorityPacket,
                        prefer_d10: bool = True) -> str:
    d10_units = [u for u in packet.authority_units
                 if u.variant_kind == "d10_project_unit"]
    source = sorted(d10_units, key=lambda u: u.unit_ref)[0] if d10_units \
        else sorted(packet.authority_units, key=lambda u: u.unit_ref)[0]
    return RECEIPT_REF_PREFIX + source.receipt_content_hash


def _projection_instance(packet: R5S3AuthorityPacket) -> R5ProjectionInstance:
    d10_units = [u for u in packet.authority_units
                 if u.variant_kind == "d10_project_unit"]
    source = sorted(d10_units, key=lambda u: u.unit_ref)[0] if d10_units \
        else sorted(packet.authority_units, key=lambda u: u.unit_ref)[0]
    receipt = source.authority_receipt
    # The R5 projection-instance object pins its own canonical ``content_hash``
    # (empty-string sentinel); the S3 recipe never overrides an R5 hash.
    return R5ProjectionInstance(
        authority_receipt_ref=RECEIPT_REF_PREFIX
        + source.receipt_content_hash,
        content_hash="",
        opaque_run_ref=receipt.run_ref,
        opaque_snapshot_ref=receipt.snapshot_ref,
        replay_content_identity=_h({
            "authority_receipt_ref": RECEIPT_REF_PREFIX
            + source.receipt_content_hash,
            "stable_site_order": list(
                project_center_cells(packet)["stable_site_order"]),
        }),
    )


def project_center_map(
    packet: R5S3AuthorityPacket, cells: Tuple[R5CenterMapCell, ...],
    stable_site_order: Tuple[str, ...],
) -> R5CenterMapProjection:
    """Center-map metadata from a public receipt, not a payload echo."""
    instance = _projection_instance(packet)
    return R5CenterMapProjection(
        cells=cells,
        content_hash="",
        projection_instance=instance,
        stable_site_order=stable_site_order,
    )


def project_cockpit(
    center_map: R5CenterMapProjection,
    change_bands: Tuple[R5ChangeBand, ...],
    measures: Tuple[R5QuantitativeMeasure, ...],
    planes: Dict[str, Any],
) -> R5ProjectCockpitProjection:
    """Renderer-neutral cockpit surface bound to the replay instance."""
    selected = (
        planes.get("high") or planes.get("medium") or planes.get("low")
        or planes.get("resolved") or (None,))[0]
    return R5ProjectCockpitProjection(
        center_map_ref="center_map.v1",
        change_band_refs=tuple(
            f"band.{index}" for index in range(1, len(change_bands) + 1)),
        content_hash="",
        current_risk_set_ref="current_risk_set.v1",
        measure_refs=tuple(m.authoritative_value_ref for m in measures),
        projection_instance=center_map.projection_instance,
        selected_risk_ref=selected,
    )


def build_audience_payload(
    view: S3AuthorityView,
) -> R5S3AudiencePayload:
    """Project the complete audience payload from the authority collections
    (bidirectional closure with ``compare_declared=False``: the surface is
    derived from the authorities, never echoed from a declared payload)."""
    planes = project_current_risk_planes(view, compare_declared=False)
    if planes["errors"]:
        raise S3AuthorityBuilderError(
            "current-risk plane closure failed before payload projection: "
            f"{planes['errors']}")
    cells = project_center_cells(view)
    if cells["errors"]:
        raise S3AuthorityBuilderError(
            "center-cell closure failed before payload projection: "
            f"{cells['errors']}")
    clusters = project_low_risk_clusters(view)
    measures = project_measures(view)
    change_bands = project_change_bands(view)
    center_map = project_center_map(view, cells["cells"],
                                    cells["stable_site_order"])
    cockpit = project_cockpit(center_map, change_bands, measures,
                              planes["planes"])
    current_risk_set = R5CurrentRiskSet(
        authority_receipt_ref=view.aggregate_receipt_set.aggregate_id,
        high_risk_refs=tuple(planes["planes"]["high"]),
        low_risk_cluster_refs=tuple(planes["planes"]["low"]),
        medium_risk_refs=tuple(planes["planes"]["medium"]),
        resolved_history_refs=tuple(planes["planes"]["resolved"]),
    )
    return R5S3AudiencePayload(
        current_risk_set=current_risk_set,
        change_bands=change_bands,
        measures=measures,
        center_map=center_map,
        cockpit=cockpit,
        low_risk_clusters=clusters,
    )


def assemble_packet(
    units: Tuple[R5S3AuthorityUnitTagged, ...],
    aggregate_receipt_set: R5S3AggregateReceiptSetIdentity,
    lifecycles: Tuple[R5S3RiskLifecycleAuthority, ...],
    closures: Tuple[R5S3ClosureAuthority, ...],
    domain_authorities: Tuple[R5S3ClinicalDomainAuthority, ...],
    denominator_authorities: Tuple[R5S3DenominatorAuthority, ...],
    layer_membership_authorities: Tuple[R5S3LayerMembershipAuthority, ...],
    cutoff_authorities: Tuple[R5S3CutoffAuthority, ...],
    evaluation_limit_authorities: Tuple[R5S3EvaluationLimitAuthority, ...],
    coverage_authorities: Tuple[R5S3CoverageAuthority, ...],
    change_cause_mixture_authorities: Tuple[
        R5S3ChangeCauseMixtureAuthority, ...],
    payload: Optional[R5S3AudiencePayload] = None,
) -> R5S3AuthorityPacket:
    """Assemble the frozen typed packet.  When ``payload`` is ``None`` the
    audience payload is projected from the authority collections (never an
    echo); the replay/integrity hashes and the single-colon packet id are
    recomputed here and re-verified by the packet dataclass at construction.
    """
    if payload is None:
        view = S3AuthorityView(
            units, aggregate_receipt_set, lifecycles, closures,
            domain_authorities, denominator_authorities,
            layer_membership_authorities, cutoff_authorities,
            evaluation_limit_authorities, coverage_authorities,
            change_cause_mixture_authorities)
        payload = build_audience_payload(view)
    replay_hash = s3_sha256(s3_canonical_bytes(payload))
    return R5S3AuthorityPacket(
        packet_id=PACKET_ID_PREFIX + ":" + replay_hash,
        schema=S3_PACKET_SCHEMA_ID,
        status=STAGE_STATUS_S3,
        authority_mode=AUTHORITY_MODE_S3,
        authority_units=units,
        aggregate_receipt_set=aggregate_receipt_set,
        risk_lifecycle_authorities=lifecycles,
        closure_authorities=closures,
        clinical_domain_authorities=domain_authorities,
        denominator_authorities=denominator_authorities,
        layer_membership_authorities=layer_membership_authorities,
        cutoff_authorities=cutoff_authorities,
        evaluation_limit_authorities=evaluation_limit_authorities,
        coverage_authorities=coverage_authorities,
        change_cause_mixture_authorities=change_cause_mixture_authorities,
        audience_payload=payload,
        audience_replay_content_hash=replay_hash,
        packet_integrity_hash=None,
    )


def build_s3_authority_packet() -> R5S3AuthorityPacket:
    """Build one frozen synthetic/offline S3 authority packet end-to-end
    through the typed authority builder.  Deterministic on replay; the
    audience payload is projected from the authorities, never echoed."""
    units_in = build_synthetic_units()
    domain_ids = {
        unit.unit_ref: _domain_authority_id(unit)
        for unit in units_in}

    domain_authorities = tuple(
        build_clinical_domain_authority(domain_ids[unit.unit_ref],
                                        unit.clinical_domain, unit.receipt)
        for unit in units_in)

    units = tuple(
        build_authority_unit(unit, domain_ids[unit.unit_ref])
        for unit in units_in)

    aggregate = build_aggregate_receipt_set(units)

    lifecycles: list = []
    closures: list = []
    for unit, unit_in in zip(units, units_in):
        variant = unit_variant_payload(unit)
        marker = variant.risk_marker
        handoff = variant.r2_handoff
        if marker is None or handoff is None:
            raise S3AuthorityBuilderError(
                f"unit {unit.unit_ref} has no public marker/handoff: cannot "
                "derive a lifecycle authority")
        unit_domain_ref = domain_ids[unit.unit_ref]
        if unit_in.kind == "d09" and unit.unit_ref == \
                SYNTHETIC_UNIT_D09_RESOLVED_REF:
            closure = build_closure_authority(
                closure_authority_id="S3-CLOSURE-D09-002",
                closure_decision_id="S3-CLOSE-DECISION-D09-002",
                prior_public_risk_identity_ref=D09_MARKER_PREFIX
                + marker.marker_id,
                prior_risk_instance_ref=SYNTHETIC_PRIOR_INSTANCE_D09_RESOLVED,
                receipt=unit.authority_receipt,
            )
            closures.append(closure)
            lifecycle = build_lifecycle_authority(
                authority_id="S3-LIFECYCLE-" + unit.unit_ref,
                marker_kind="d09", marker=marker, handoff=handoff,
                clinical_domain_ref=unit_domain_ref,
                receipt=unit.authority_receipt,
                closure_authority_ref=closure.closure_authority_id,
                prior_marker_identity_ref=D09_MARKER_PREFIX + marker.marker_id,
            )
        else:
            prior_marker = (D10_MARKER_PREFIX + marker.marker_id
                            if unit_in.kind == "d10" else None)
            lifecycle = build_lifecycle_authority(
                authority_id="S3-LIFECYCLE-" + unit.unit_ref,
                marker_kind=unit_in.kind, marker=marker, handoff=handoff,
                clinical_domain_ref=unit_domain_ref,
                receipt=unit.authority_receipt,
                prior_marker_identity_ref=prior_marker,
            )
        lifecycles.append(lifecycle)

    # Named quantified supplementals (exact typed; the sample keeps most of
    # them empty -- the D10 numerator measure is covered by the public unit
    # authority).
    denominator_authorities: Tuple[R5S3DenominatorAuthority, ...] = ()
    layer_membership_authorities: Tuple[
        R5S3LayerMembershipAuthority, ...] = ()
    cutoff_authorities: Tuple[R5S3CutoffAuthority, ...] = (
        build_cutoff_authority("S3-CUTOFF-AUTHORITY-001",
                               SYNTHETIC_CUTOFF_REF,
                               units[0].authority_receipt),)
    evaluation_limit_authorities: tuple = (
        build_evaluation_limit_authority(
            "S3-EVALLIMIT-AUTHORITY-001",
            (SYNTHETIC_EVALUATION_LIMIT_D10,),
            (SYNTHETIC_EVALUATION_LIMIT_D10,),
            units[0].authority_receipt),)
    coverage_authorities: Tuple[R5S3CoverageAuthority, ...] = (
        build_coverage_authority("S3-COVERAGE-AUTHORITY-001", "complete",
                                 units[0].authority_receipt),)
    change_cause_mixture_authorities: Tuple[
        R5S3ChangeCauseMixtureAuthority, ...] = (
        build_change_cause_mixture_authority(
            "S3-CHANGE-CAUSE-MIXTURE-001",
            ("data", "coverage"), units[0].authority_receipt),)

    return assemble_packet(
        units, aggregate,
        tuple(sorted(lifecycles, key=lambda l: l.marker_identity_ref)),
        tuple(closures),
        tuple(sorted(domain_authorities, key=lambda d: d.authority_id)),
        denominator_authorities,
        layer_membership_authorities,
        cutoff_authorities,
        evaluation_limit_authorities,
        coverage_authorities,
        change_cause_mixture_authorities,
    )


def _domain_authority_id(unit: S3SyntheticUnit) -> str:
    """Stable synthetic domain-authority id derived from the unit/domain
    (identity leaf, never a hash)."""
    label = unit.kind.upper() + "-" + unit.unit_ref.split("-")[-1]
    return "S3-CDA-" + unit.kind + "-" + label




__all__ = [
    "S3_BUILDER_SCHEMA_ID",
    "S3AuthorityBuilderError",
    "SYNTHETIC_PROJECT_REF",
    "SYNTHETIC_RUN_REF",
    "SYNTHETIC_SNAPSHOT_REF",
    "SYNTHETIC_CUTOFF_REF",
    "SYNTHETIC_AUDIENCE_CONTRACT_ID",
    "SYNTHETIC_SOURCE_REVISION",
    "SYNTHETIC_SOURCE_FILE",
    "SYNTHETIC_UNIT_D10_REF",
    "SYNTHETIC_UNIT_D09_LOW_REF",
    "SYNTHETIC_UNIT_D09_RESOLVED_REF",
    "S3SyntheticUnit",
    "build_synthetic_units",
    "build_clinical_domain_authority",
    "build_denominator_authority",
    "build_layer_membership_authority",
    "build_cutoff_authority",
    "build_evaluation_limit_authority",
    "build_coverage_authority",
    "build_change_cause_mixture_authority",
    "build_closure_authority",
    "build_lifecycle_authority",
    "build_authority_unit",
    "build_aggregate_receipt_set",
    "build_low_risk_cluster",
    "project_current_risk_planes",
    "project_low_risk_clusters",
    "project_measures",
    "project_center_cells",
    "project_change_bands",
    "project_center_map",
    "project_cockpit",
    "build_audience_payload",
    "assemble_packet",
    "build_s3_authority_packet",
]
