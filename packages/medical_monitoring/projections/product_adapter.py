"""Read-only R5 product adapter facade."""
from __future__ import annotations

from datetime import date
from typing import Any, Callable, Mapping, Optional, Sequence

from .product_fixtures import (
    R5AuthorityProvider,
    SyntheticR5AuthorityProvider,
    build_synthetic_r5_authority_packet,
    build_synthetic_r5_authority_provider,
)
from .product_projection_helpers import (
    _change_band_records,
    _event_payload,
    _indicator_payloads,
    _public_source,
    _risk_payload,
    _subject_flow_projection,
    _subject_rows,
    _with_content_hash,
    response_snapshot_sha256,
)
from .product_types import (
    CHANGE_CAUSES,
    CHANGE_KINDS,
    DOMAINS,
    DOMAIN_ENCODING,
    FLOW_COVERAGE_BUCKETS,
    FLOW_MAX_COLUMNS,
    FLOW_NOT_PROVIDED_REASON_ZH,
    FLOW_PATH_STATES,
    FLOW_SEVERITY_ZH,
    FLOW_STAGE_CHANGE_KINDS,
    FLOW_STAGE_KINDS,
    MID_HIGH_SEVERITIES,
    PRODUCT_READ_SCHEMA,
    R5AuthorityPacket,
    R5EventRecord,
    R5FlowStageRecord,
    R5HistoryRecord,
    R5ProductAdapterError,
    R5RiskRecord,
    R5SiteAudienceRecord,
    R5SiteRecord,
    R5SourceRecord,
    R5SourceRevisionPair,
    R5SubjectFlowPathRecord,
    R5SubjectFlowStep,
    R5SubjectRecord,
    R5VisitRecord,
    R5_CONTRACT_SCHEMA,
    R5_CONTRACT_SHA256,
    R5_FLOW_AUTHORITY_CONTRACT_VERSION,
    SEVERITIES,
    SYNTHETIC_CUTOFF_REF,
    SYNTHETIC_FIXTURE_MODE,
    SYNTHETIC_PROJECT_REF,
    SYNTHETIC_RUN_REF,
    _iso,
    _required,
    _sha,
    canonical_json,
    canonical_sha256,
)

# Overview scale boundary: cohorts larger than this project aggregate risk
# rows (plus medium-or-higher exemplars) instead of one row per risk.
_OVERVIEW_AGGREGATION_THRESHOLD = 500
_OVERVIEW_EXEMPLAR_LIMIT = 50


class R5ProductAdapter:
    """Project typed authority into the three closed R5 read surfaces."""

    def __init__(self, authority_provider: Optional[Any], *, synthetic_fixture_mode: bool = False) -> None:
        if synthetic_fixture_mode:
            if authority_provider is not None and not getattr(authority_provider, "fixture_mode", False):
                raise R5ProductAdapterError("SYNTHETIC_PROVIDER_MISMATCH")
            authority_provider = authority_provider or build_synthetic_r5_authority_provider()
        self.authority_provider = authority_provider
        self.synthetic_fixture_mode = synthetic_fixture_mode

    def _packet(
        self,
        project_ref: str,
        run_ref: Optional[str],
        snapshot_ref: Optional[str],
        cutoff_ref: Optional[str],
    ) -> R5AuthorityPacket:
        if self.authority_provider is None:
            raise R5ProductAdapterError("AUTHORITY_PACKET_UNAVAILABLE")
        provider = self.authority_provider
        try:
            if hasattr(provider, "get_packet"):
                packet = provider.get_packet(project_ref, run_ref, snapshot_ref, cutoff_ref)
            elif callable(provider):
                packet = provider(project_ref, run_ref, snapshot_ref, cutoff_ref)
            else:
                raise R5ProductAdapterError("AUTHORITY_PROVIDER_INVALID")
        except R5ProductAdapterError:
            raise
        except Exception as exc:
            raise R5ProductAdapterError("AUTHORITY_PACKET_UNAVAILABLE") from exc
        if type(packet) is not R5AuthorityPacket:
            raise R5ProductAdapterError("TYPED_AUTHORITY_REQUIRED")
        if self.synthetic_fixture_mode and not packet.synthetic:
            raise R5ProductAdapterError("SYNTHETIC_AUTHORITY_REQUIRED")
        if packet.project_ref != project_ref:
            raise R5ProductAdapterError("PROJECT_IDENTITY_MISMATCH")
        for name, expected in (("run_ref", run_ref), ("snapshot_ref", snapshot_ref), ("cutoff_ref", cutoff_ref)):
            if expected is not None and getattr(packet, name) != expected:
                raise R5ProductAdapterError("AUTHORITY_IDENTITY_MISMATCH", name)
        return packet

    def get_authority_packet(
        self,
        *,
        project_ref: str,
        run_ref: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        cutoff_ref: Optional[str] = None,
    ) -> R5AuthorityPacket:
        """Expose the validated packet for one route-level identity handoff."""

        return self._packet(project_ref, run_ref, snapshot_ref, cutoff_ref)

    def overview(
        self,
        *,
        project_ref: str,
        run_ref: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        cutoff_ref: Optional[str] = None,
        site_ref: Optional[str] = None,
    ) -> dict[str, Any]:
        packet = self._packet(project_ref, run_ref, snapshot_ref, cutoff_ref)
        if site_ref is not None:
            site_ref = _required(site_ref, "site_ref")
        selected_sites = tuple(item for item in packet.sites if site_ref is None or item.site_ref == site_ref)
        if site_ref is not None and not selected_sites:
            raise R5ProductAdapterError("TARGET_NOT_PROJECTABLE")
        selected_site_refs = {item.site_ref for item in selected_sites}
        selected_subjects = tuple(item for item in packet.subjects if item.site_ref in selected_site_refs)
        selected_events = tuple(item for item in packet.events if item.site_ref in selected_site_refs)
        selected_visits = tuple(item for item in packet.visits if item.site_ref in selected_site_refs)
        selected_risks = tuple(item for item in packet.risks if item.site_ref in selected_site_refs)
        receipt_ref = packet.receipt_id
        subject_labels = {item.subject_ref: item.subject_label for item in packet.subjects}
        high = tuple(item for item in selected_risks if item.severity in {"critical", "high"})
        medium = tuple(item for item in selected_risks if item.severity == "medium")
        low = tuple(item for item in selected_risks if item.severity == "low")
        # Scale-aware overview: real cohorts carry five-to-six-digit risk
        # anchors; a project cockpit projects aggregates (plus medium-or-higher
        # exemplars for drill-in), never one row per risk. Small packets (the
        # fixture lane, single-site scopes) keep the per-risk shape.
        aggregated_overview = len(selected_risks) > _OVERVIEW_AGGREGATION_THRESHOLD
        if aggregated_overview:
            type_severity_counts: dict[tuple[str, str], int] = {}
            site_severity_counts: dict[tuple[str, str], int] = {}
            exemplar_pool = sorted(
                (*high, *medium),
                key=lambda item: SEVERITIES.index(item.severity),
            )
            for item in selected_risks:
                type_key = (item.risk_type_zh, item.severity)
                type_severity_counts[type_key] = type_severity_counts.get(type_key, 0) + 1
                site_key = (item.site_ref, item.severity)
                site_severity_counts[site_key] = site_severity_counts.get(site_key, 0) + 1
            current_risks = [
                {
                    "aggregate": True,
                    "risk_type": risk_type,
                    "severity": severity,
                    "count": count,
                }
                for (risk_type, severity), count in sorted(type_severity_counts.items())
            ]
            current_risks.extend(
                _risk_payload(item, receipt_ref, subject_label=subject_labels.get(item.subject_ref))
                for item in exemplar_pool[:_OVERVIEW_EXEMPLAR_LIMIT]
            )
            current_risk_set = _with_content_hash({
                "aggregated": True,
                "risk_count": len(selected_risks),
                "high_risk_count": len(high),
                "medium_risk_count": len(medium),
                "low_risk_count": len(low),
                "resolved_history_refs": [],
                "authority_receipt_ref": receipt_ref,
            })
        else:
            current_risks = [
                _risk_payload(item, receipt_ref, subject_label=subject_labels.get(item.subject_ref))
                for item in selected_risks
            ]
            current_risk_set = _with_content_hash({
                "high_risk_refs": [item.risk_ref for item in high],
                "medium_risk_refs": [item.risk_ref for item in medium],
                "low_risk_cluster_refs": [item.risk_ref for item in low],
                "resolved_history_refs": [],
                "authority_receipt_ref": receipt_ref,
            })
        center_cells = []
        for site in selected_sites:
            for domain in DOMAINS:
                site_risks = tuple(item for item in selected_risks if item.site_ref == site.site_ref and item.domain == domain)
                if not site_risks and domain != site.domain:
                    continue
                if aggregated_overview:
                    cell_severity_counts = {
                        severity: sum(1 for item in site_risks if item.severity == severity)
                        for severity in SEVERITIES
                        if any(item.severity == severity for item in site_risks)
                    }
                    center_cells.append({
                        "site_ref": site.site_ref,
                        "domain": domain,
                        "severity": max((item.severity for item in site_risks), default=site.severity, key=SEVERITIES.index),
                        "pattern_refs": list(site.pattern_refs),
                        "individual_risk_count": len(site_risks),
                        "severity_counts": cell_severity_counts,
                        "measure_refs": list(site.measure_refs),
                    })
                else:
                    center_cells.append({
                        "site_ref": site.site_ref,
                        "domain": domain,
                        "severity": max((item.severity for item in site_risks), default=site.severity, key=SEVERITIES.index),
                        "pattern_refs": list(site.pattern_refs),
                        "individual_risk_refs": [item.risk_ref for item in site_risks],
                        "measure_refs": list(site.measure_refs),
                    })
        # Canonical center_map shape is an object, never a bare cell array:
        # {stable_site_order, cells, projection_instance, content_hash}; every
        # cell carries site/domain/severity/pattern/risk/measure references.
        center_map = _with_content_hash({
            "stable_site_order": [site.site_ref for site in selected_sites],
            "cells": center_cells,
            "projection_instance": {
                "opaque_run_ref": packet.run_ref,
                "opaque_snapshot_ref": packet.snapshot_ref,
                "replay_content_identity": canonical_sha256({"packet": packet.source_snapshot_sha256, "surface": "overview"}),
                "authority_receipt_ref": receipt_ref,
            },
        })
        change_band_records = _change_band_records(selected_risks)
        if aggregated_overview:
            change_kind_counts: dict[str, int] = {}
            for item in change_band_records:
                change_kind_counts[item.change_kind] = change_kind_counts.get(item.change_kind, 0) + 1
            changes = [
                {
                    "aggregate": True,
                    "change_kind": change_kind,
                    "count": count,
                    "current_snapshot_ref": packet.snapshot_ref,
                    "authority_receipt_ref": receipt_ref,
                }
                for change_kind, count in sorted(change_kind_counts.items())
            ]
        else:
            changes = [
                {
                    "risk_ref": item.risk_ref,
                    "change_kind": item.change_kind,
                    "change_cause": item.change_cause,
                    "prior_snapshot_ref": item.prior_snapshot_ref,
                    "current_snapshot_ref": packet.snapshot_ref,
                    "authority_receipt_ref": receipt_ref,
                }
                for item in change_band_records
            ]
        measures = [
            {
                "measure_ref": measure_ref,
                "site_ref": site.site_ref,
                "numerator": site.numerator,
                "denominator": site.denominator,
                "denominator_state": "closed_positive" if site.denominator else "closed_zero",
                "rate_state": "closed" if site.denominator else "not_evaluable",
                "coverage_state": site.coverage_state,
                "cutoff_ref": packet.cutoff_ref,
                "authority_receipt_ref": receipt_ref,
            }
            for site in selected_sites
            for measure_ref in site.measure_refs
        ]
        coverage_numerator = sum(site.numerator for site in selected_sites)
        coverage_denominator = sum(site.denominator or 0 for site in selected_sites)
        coverage_state = "complete" if all(site.coverage_state == "complete" for site in selected_sites) else "partial"
        subject_flow = _subject_flow_projection(
            packet,
            selected_site_refs=selected_site_refs,
            site_ref=site_ref,
        )
        # Surface-specific contract: evidence binds one risk to one source.
        # The eight-domain registry belongs to overview/subject projections;
        # it is intentionally absent here and must not be added generically.
        projection = _with_content_hash({
            "kind": "project_cockpit",
            "projection_instance": {
                "opaque_run_ref": packet.run_ref,
                "opaque_snapshot_ref": packet.snapshot_ref,
                "replay_content_identity": canonical_sha256({"packet": packet.source_snapshot_sha256, "surface": "overview"}),
                "authority_receipt_ref": receipt_ref,
            },
            "project": {"project_ref": packet.project_ref, "project_label": packet.project_label},
            "subjects": _subject_rows(packet, subjects=selected_subjects),
            "current_risks": current_risks,
            "current_risk_set": current_risk_set,
            "center_map": center_map,
            "change_bands": changes,
            "measures": measures,
            "coverage": {
                "numerator": coverage_numerator,
                "denominator": coverage_denominator,
                "coverage_state": coverage_state,
                "label": "当前范围覆盖",
                "authority_receipt_ref": receipt_ref,
            },
            "subject_flow": subject_flow,
            "domain_encoding": [dict({"domain": domain}, **DOMAIN_ENCODING[domain]) for domain in DOMAINS],
            "risk_overlay_shape": "double_chevron_badge",
            **(
                {
                    "aggregation": {
                        "mode": "aggregate",
                        "risk_count": len(selected_risks),
                        "threshold": _OVERVIEW_AGGREGATION_THRESHOLD,
                        "exemplar_limit": _OVERVIEW_EXEMPLAR_LIMIT,
                    }
                }
                if aggregated_overview
                else {}
            ),
        })
        selected_source_refs = {
            locator_ref
            for item in (*selected_events, *selected_visits, *selected_risks)
            for locator_ref in item.source_locator_refs
        }
        source_refs = [
            _public_source(item)
            for item in packet.sources
            if site_ref is None or item.locator_ref in selected_source_refs
        ]
        counts = self._counts(
            packet,
            events=selected_events,
            risks=selected_risks,
            change_band_records=change_band_records,
        )
        return_context_key = f"r5:return:overview:{packet.snapshot_ref}"
        if site_ref is not None:
            return_context_key = f"{return_context_key}:{site_ref}"
        identity_overrides = {"site_ref": site_ref} if site_ref is not None else None
        return self._result(
            packet,
            projection,
            counts,
            source_refs,
            view="overview",
            return_context_key=return_context_key,
            identity_overrides=identity_overrides,
        )

    def subject_workspace(
        self,
        *,
        project_ref: str,
        subject_ref: str,
        run_ref: str,
        snapshot_ref: str,
        cutoff_ref: str,
        site_ref: str,
        spine_ref: str,
        window_start: date,
        window_end: date,
        risk_instance_ref: Optional[str] = None,
        risk_anchor_ref: Optional[str] = None,
        visit_ref: Optional[str] = None,
        event_ref: Optional[str] = None,
    ) -> dict[str, Any]:
        packet = self._packet(project_ref, run_ref, snapshot_ref, cutoff_ref)
        if window_start > window_end:
            raise R5ProductAdapterError("WINDOW_INVALID")
        subject = next((item for item in packet.subjects if item.subject_ref == subject_ref), None)
        if subject is None or subject.site_ref != site_ref or subject.spine_ref != spine_ref:
            raise R5ProductAdapterError("TARGET_NOT_PROJECTABLE")
        events = tuple(item for item in packet.events if item.subject_ref == subject_ref and item.spine_ref == spine_ref)
        visits = tuple(item for item in packet.visits if item.subject_ref == subject_ref and item.spine_ref == spine_ref)
        risks = tuple(item for item in packet.risks if item.subject_ref == subject_ref and item.spine_ref == spine_ref)
        if risk_instance_ref is not None:
            if not any(item.risk_instance_ref == risk_instance_ref for item in risks):
                raise R5ProductAdapterError("TARGET_NOT_PROJECTABLE")
        if risk_anchor_ref is not None:
            if not any(item.risk_anchor_ref == risk_anchor_ref for item in risks):
                raise R5ProductAdapterError("TARGET_NOT_PROJECTABLE")
        if visit_ref is not None and not any(item.visit_ref == visit_ref for item in visits):
            raise R5ProductAdapterError("TARGET_NOT_PROJECTABLE")
        if event_ref is not None and not any(item.event_ref == event_ref for item in events):
            raise R5ProductAdapterError("TARGET_NOT_PROJECTABLE")
        receipt_ref = packet.receipt_id
        subject_labels = {item.subject_ref: item.subject_label for item in packet.subjects}
        event_payloads = [_event_payload(item) for item in events]
        risk_payloads = [
            _risk_payload(item, receipt_ref, subject_label=subject_labels.get(item.subject_ref))
            for item in risks
        ]
        visit_payloads = [
            {
                "visit_ref": item.visit_ref,
                "subject_ref": item.subject_ref,
                "site_ref": item.site_ref,
                "spine_ref": item.spine_ref,
                "visit_kind": item.visit_kind,
                "date_state": item.date_state,
                "actual_date": _iso(item.actual_date),
                "nominal_date": _iso(item.nominal_date),
                "phase_ref": item.phase_ref,
                "source_locator_refs": list(item.source_locator_refs),
            }
            for item in visits
        ]
        pending_date_payloads = [
            {
                "item_ref": item.event_ref,
                "event_ref": item.event_ref,
                "domain": item.domain,
                "date_state": item.date_state,
                "source_locator_refs": list(item.source_locator_refs),
                "authority_receipt_ref": receipt_ref,
            }
            for item in events
            if item.date_state != "exact"
        ]
        domain_tracks = [
            {
                "domain": domain,
                "event_refs": [item.event_ref for item in events if item.domain == domain],
                "risk_anchor_refs": [item.risk_anchor_ref for item in risks if item.domain == domain],
                "encoding": dict(DOMAIN_ENCODING[domain]),
            }
            for domain in DOMAINS
        ]
        pending_date_refs = [item.event_ref for item in events if item.date_state != "exact"]
        spine = _with_content_hash({
            "spine_ref": subject.spine_ref,
            "subject_ref": subject.subject_ref,
            "cutoff_ref": packet.cutoff_ref,
            "axis_mode": "calendar",
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "event_refs": [item.event_ref for item in events],
            "visit_refs": [item.visit_ref for item in visits],
            "pending_date_refs": pending_date_refs,
            "phase_band_refs": [],
            "events": event_payloads,
            "visits": visit_payloads,
            "risk_anchors": risk_payloads,
            "pending_dates": pending_date_payloads,
        })
        workspace = _with_content_hash({
            "subject_ref": subject.subject_ref,
            "spine_ref": subject.spine_ref,
            "active_view": "journey",
            "axis_mode": "calendar",
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "selected_event_ref": event_ref,
            "selected_risk_ref": risk_instance_ref,
            "selected_visit_ref": visit_ref,
        })
        history = [
            {
                "candidate_ref": item.candidate_ref,
                "later_fact_ref": item.later_fact_ref,
                "event_kind": item.event_kind,
                "match_state": item.match_state,
                "from_snapshot_ref": item.from_snapshot_ref,
                "to_snapshot_ref": item.to_snapshot_ref,
                "identity_evidence_refs": list(item.identity_evidence_refs),
            }
            for item in packet.histories
            if item.subject_ref == subject_ref
        ]
        projection = _with_content_hash({
            "kind": "subject_workspace",
            "subject": {
                "subject_ref": subject.subject_ref,
                "site_ref": subject.site_ref,
                "spine_ref": subject.spine_ref,
                "subject_label": subject.subject_label,
            },
            "temporal_spine": spine,
            "workspace_state": workspace,
            "events": event_payloads,
            "visits": visit_payloads,
            "current_risks": risk_payloads,
            "risk_anchors": risk_payloads,
            "domain_tracks": domain_tracks,
            "indicators": _indicator_payloads(packet, events=events, risks=risks),
            "aemh_match_history": history,
            "pending_dates": pending_date_payloads,
            "date_pending_refs": pending_date_refs,
            "risk_overlay_shape": "double_chevron_badge",
        })
        source_locator_refs = set()
        for item in events:
            source_locator_refs.update(item.source_locator_refs)
        for item in risks:
            source_locator_refs.update(item.source_locator_refs)
        for item in visits:
            source_locator_refs.update(item.source_locator_refs)
        # Diagnostic: capture the unbound refs before failing closed.
        bound_refs = {item.locator_ref for item in packet.sources}
        unbound_refs = sorted(source_locator_refs - bound_refs)
        source_refs = [_public_source(item) for item in packet.sources if item.locator_ref in source_locator_refs]
        if unbound_refs:
            raise R5ProductAdapterError(
                f"SOURCE_LOCATOR_NOT_BOUND:{unbound_refs[0]}:{len(unbound_refs)}"
            )
        counts = self._counts(
            packet,
            events=events,
            risks=risks,
            indicators=projection["indicators"],
        )
        target_risk = next((item for item in risks if item.risk_instance_ref == risk_instance_ref or item.risk_anchor_ref == risk_anchor_ref), None)
        identity = {
            "site_ref": site_ref,
            "subject_ref": subject_ref,
            "spine_ref": spine_ref,
            "risk_ref": target_risk.risk_ref if target_risk else None,
            "risk_instance_ref": target_risk.risk_instance_ref if target_risk else risk_instance_ref,
            "risk_anchor_ref": target_risk.risk_anchor_ref if target_risk else risk_anchor_ref,
            "visit_ref": visit_ref,
            "event_ref": event_ref,
            "source_locator_ref": None,
        }
        return self._result(packet, projection, counts, source_refs, view="journey", return_context_key=f"r5:return:subject:{subject_ref}:{spine_ref}", identity_overrides=identity, window_start=window_start, window_end=window_end)

    def source_evidence(
        self,
        *,
        project_ref: str,
        run_ref: str,
        snapshot_ref: str,
        cutoff_ref: str,
        risk_instance_ref: str,
        source_locator_ref: str,
    ) -> dict[str, Any]:
        packet = self._packet(project_ref, run_ref, snapshot_ref, cutoff_ref)
        risk = next((item for item in packet.risks if item.risk_instance_ref == risk_instance_ref), None)
        if risk is None or source_locator_ref not in risk.source_locator_refs:
            raise R5ProductAdapterError("SOURCE_LOCATOR_NOT_BOUND")
        source = next((item for item in packet.sources if item.locator_ref == source_locator_ref and item.snapshot_ref == snapshot_ref), None)
        if source is None:
            raise R5ProductAdapterError("SOURCE_LOCATOR_NOT_BOUND")
        projection = _with_content_hash({
            "kind": "source_evidence",
            "risk_ref": risk.risk_ref,
            "risk_instance_ref": risk.risk_instance_ref,
            "source_locator_ref": source.locator_ref,
            "evidence": {
                "excerpt": source.excerpt,
                "record_ref": source.record_ref,
                "canonical_location": source.canonical_location,
                "lineage": list(source.lineage),
                "source_revision_ref": source.source_revision_ref,
                "source_revision_content_hash": source.source_revision_content_hash,
            },
            "authority_receipt_ref": packet.receipt_id,
        })
        counts = self._counts(packet, events=(), risks=(risk,))
        return self._result(
            packet,
            projection,
            counts,
            [_public_source(source, include_excerpt=True)],
            view="evidence",
            return_context_key=f"r5:return:evidence:{risk.risk_instance_ref}:{source.locator_ref}",
            identity_overrides={
                "site_ref": risk.site_ref,
                "subject_ref": risk.subject_ref,
                "spine_ref": risk.spine_ref,
                "risk_ref": risk.risk_ref,
                "risk_instance_ref": risk.risk_instance_ref,
                "risk_anchor_ref": risk.risk_anchor_ref,
                "source_locator_ref": source.locator_ref,
            },
        )

    def _counts(
        self,
        packet: R5AuthorityPacket,
        *,
        events: Sequence[R5EventRecord],
        risks: Sequence[R5RiskRecord],
        indicators: Sequence[Mapping[str, Any]] = (),
        change_band_records: Optional[Sequence[R5RiskRecord]] = None,
    ) -> dict[str, Any]:
        current_risk = {
            "critical": sum(item.severity == "critical" for item in risks),
            "high": sum(item.severity == "high" for item in risks),
            "medium": sum(item.severity == "medium" for item in risks),
            "low": sum(item.severity == "low" for item in risks),
            "total": len(risks),
        }
        result = {
            "query": len(risks),
            "clue": len(events),
            "center_pattern": len(packet.sites),
            "individual_risk": len(risks),
            "affected_subject": len({item.subject_ref for item in risks} or {item.subject_ref for item in events}),
            "event": len(events),
            "affected_site": len({item.site_ref for item in risks} or {item.site_ref for item in events}),
            "project_signal": len(tuple(item for item in risks if item.severity in {"critical", "high", "medium"})),
            "indicator": len(indicators),
            "risk_anchor": len(risks),
            # Each severity remains a separate authority count; there is no
            # frontend-derived scalar that conflates current risk levels.
            "current_risk": current_risk,
        }
        if change_band_records is not None:
            # This is a closed count of rows emitted from the same authority
            # packet; the frontend must not count projection rows.
            result["change_band_count"] = len(change_band_records)
        return result

    def _result(
        self,
        packet: R5AuthorityPacket,
        projection: Mapping[str, Any],
        counts: Mapping[str, Any],
        source_refs: Sequence[Mapping[str, Any]],
        *,
        view: str,
        return_context_key: str,
        identity_overrides: Optional[Mapping[str, Any]] = None,
        window_start: Optional[date] = None,
        window_end: Optional[date] = None,
    ) -> dict[str, Any]:
        identity = {
            "tenant_id": None,
            "project_ref": packet.project_ref,
            "run_ref": packet.run_ref,
            "snapshot_ref": packet.snapshot_ref,
            "cutoff_state": packet.cutoff_state,
            "cutoff_ref": packet.cutoff_ref,
            "site_ref": None,
            "subject_ref": None,
            "risk_ref": None,
            "risk_instance_ref": None,
            "spine_ref": None,
            "view": view,
            "axis_mode": "calendar",
            "window_start": _iso(window_start),
            "window_end": _iso(window_end),
            "visit_ref": None,
            "event_ref": None,
            "risk_anchor_ref": None,
            "source_locator_ref": None,
            "target_projection_content_hash": projection["content_hash"],
            "return_context_key": return_context_key,
            "authority_hash": packet.authority_hash,
            "source_snapshot_sha256": packet.source_snapshot_sha256,
            "response_snapshot_sha256": "",
            "principal_identity_hash": "",
            "authorization_decision_sha256": "",
            "audit_id": "",
        }
        if identity_overrides:
            identity.update(identity_overrides)
        return {
            "packet": packet,
            "projection": dict(projection),
            "counts": dict(counts),
            "source_refs": [dict(item) for item in source_refs],
            "identity": identity,
            "authority_receipt": packet.authority_receipt(),
        }


def build_response_envelope(
    result: Mapping[str, Any],
    *,
    read_handoff: Mapping[str, Any],
    read_handoff_builder: Optional[Callable[[str], Mapping[str, Any]]] = None,
    tenant_id: str,
    principal_identity_hash: str,
    authorization_decision_sha256: str,
    audit_id: str,
) -> dict[str, Any]:
    """Bind route identity and read handoff into the exact response envelope."""

    packet = result.get("packet")
    if type(packet) is not R5AuthorityPacket:
        raise R5ProductAdapterError("TYPED_AUTHORITY_REQUIRED")
    identity = dict(result["identity"])
    identity.update(
        {
            "tenant_id": _required(tenant_id, "tenant_id"),
            "principal_identity_hash": _sha(principal_identity_hash, "principal_identity_hash"),
            "authorization_decision_sha256": _sha(authorization_decision_sha256, "authorization_decision_sha256"),
            "audit_id": _required(audit_id, "audit_id"),
        }
    )
    handoff = dict(read_handoff)
    handoff["response_snapshot_sha256"] = ""
    envelope: dict[str, Any] = {
        "schema": PRODUCT_READ_SCHEMA,
        "contract_schema": R5_CONTRACT_SCHEMA,
        "contract_sha256": R5_CONTRACT_SHA256,
        "authority_receipt": dict(result["authority_receipt"]),
        "identity": identity,
        "projection": dict(result["projection"]),
        "counts": dict(result["counts"]),
        "source_refs": [dict(item) for item in result["source_refs"]],
        "response_snapshot_sha256": "",
        "read_handoff": handoff,
        "read_only": True,
        "mutation_applied": False,
        "persisted": False,
        "aggregate_version_before": packet.aggregate_version,
        "aggregate_version_after": packet.aggregate_version,
    }
    digest = response_snapshot_sha256(envelope)
    if read_handoff_builder is not None:
        envelope["read_handoff"] = dict(read_handoff_builder(digest))
        if response_snapshot_sha256(envelope) != digest:
            raise R5ProductAdapterError("RESPONSE_DIGEST_UNSTABLE")
    envelope["response_snapshot_sha256"] = digest
    envelope["identity"]["response_snapshot_sha256"] = digest
    envelope["read_handoff"]["response_snapshot_sha256"] = digest
    return envelope


__all__ = [
    "CHANGE_CAUSES",
    "CHANGE_KINDS",
    "DOMAINS",
    "DOMAIN_ENCODING",
    "FLOW_COVERAGE_BUCKETS",
    "FLOW_MAX_COLUMNS",
    "FLOW_NOT_PROVIDED_REASON_ZH",
    "FLOW_PATH_STATES",
    "FLOW_SEVERITY_ZH",
    "FLOW_STAGE_CHANGE_KINDS",
    "FLOW_STAGE_KINDS",
    "MID_HIGH_SEVERITIES",
    "PRODUCT_READ_SCHEMA",
    "R5AuthorityPacket",
    "R5AuthorityProvider",
    "R5_FLOW_AUTHORITY_CONTRACT_VERSION",
    "R5_CONTRACT_SCHEMA",
    "R5_CONTRACT_SHA256",
    "R5EventRecord",
    "R5FlowStageRecord",
    "R5HistoryRecord",
    "R5ProductAdapter",
    "R5ProductAdapterError",
    "R5RiskRecord",
    "R5SiteAudienceRecord",
    "R5SiteRecord",
    "R5SourceRecord",
    "R5SourceRevisionPair",
    "R5SubjectFlowPathRecord",
    "R5SubjectFlowStep",
    "R5SubjectRecord",
    "R5VisitRecord",
    "SEVERITIES",
    "SYNTHETIC_CUTOFF_REF",
    "SYNTHETIC_FIXTURE_MODE",
    "SYNTHETIC_PROJECT_REF",
    "SYNTHETIC_RUN_REF",
    "SyntheticR5AuthorityProvider",
    "build_response_envelope",
    "build_synthetic_r5_authority_packet",
    "build_synthetic_r5_authority_provider",
    "canonical_json",
    "canonical_sha256",
    "response_snapshot_sha256",
]
