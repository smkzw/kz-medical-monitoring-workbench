"""Synthetic S6 fixtures built on the accepted typed S5 packets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from mm_r5.s5_authority_adapter import (
    adapt_aemh_match_history_authority,
    adapt_subject_temporal_authority,
)
from mm_r5.s6_accessibility import build_keyboard_contract
from mm_r5.s6_contracts import (
    DOMAINS,
    S6PerformanceCorpusIdentity,
    S6PerformanceProfile,
    build_performance_corpus_identity as build_s6_performance_corpus_identity,
    build_performance_profile as build_s6_performance_profile,
    s6_as_mapping,
)
from mm_r5.s6_navigation import (
    build_canonical_return_state,
    build_deep_link_identity,
    build_ephemeral_return_state,
    build_return_context as build_s6_return_context,
    build_semantic_zoom_state,
    project_density_and_zoom,
)

try:
    from s5_runtime_fixtures import (
        build_aemh_authority_bundle,
        build_subject_authority_bundle,
        build_subject_workspace as build_s5_subject_workspace,
    )
except ImportError:  # pragma: no cover - package import fallback
    from .s5_runtime_fixtures import (
        build_aemh_authority_bundle,
        build_subject_authority_bundle,
        build_subject_workspace as build_s5_subject_workspace,
    )


@dataclass(frozen=True)
class S6PerformanceRecord:
    record_kind: Literal["event", "indicator", "risk_anchor"]
    ordinal: int
    domain: str
    source_locator_ref: str


def build_subject_packet():
    return adapt_subject_temporal_authority(build_subject_authority_bundle())


def build_aemh_packet():
    return adapt_aemh_match_history_authority(build_aemh_authority_bundle())


def build_subject_workspace_packet():
    """Return the accepted typed S5 workspace bound to the subject packet."""
    return build_s5_subject_workspace()


def build_subject_workspace():
    return build_subject_workspace_packet()


def build_deep_link():
    subject = build_subject_packet()
    workspace = build_subject_workspace_packet()
    anchor = subject.projection.risk_anchors[0]
    event = subject.projection.events[0]
    return build_deep_link_identity(
        subject,
        workspace,
        target_kind="subject_workspace",
        view="journey",
        axis_mode="calendar",
        window_start=date(2026, 1, 1),
        window_end=date(2026, 3, 31),
        risk_ref=anchor.risk_ref,
        event_ref=event.event_ref,
        risk_anchor_ref=anchor.risk_anchor_ref,
        visit_ref=anchor.visit_ref,
        source_locator_ref=anchor.source_locator_refs[0],
        return_context_key="return::s6::fixture",
    )


def build_valid_deep_link():
    return build_deep_link()


def build_canonical():
    link = build_deep_link()
    subject = build_subject_packet()
    event = subject.projection.events[0]
    anchor = subject.projection.risk_anchors[0]
    from mm_r5.s6_contracts import S6FilterState, S6PageState, S6SelectionAnchor, S6SortState

    return build_canonical_return_state(
        link,
        filter_state=S6FilterState(
            change_kind=("new",), domain=(event.domain,), severity=(anchor.severity,),
            site_refs=(subject.projection.scope_identity.site_ref,), include_low=False,
        ),
        sort_state=S6SortState(key="priority", direction="desc"),
        page_state=S6PageState(page_index=0, page_size=25),
        selection_anchor=S6SelectionAnchor(
            selected_event_ref=event.event_ref,
            selected_risk_ref=anchor.risk_ref,
            selected_visit_ref=anchor.visit_ref,
            risk_anchor_ref=anchor.risk_anchor_ref,
            source_locator_ref=anchor.source_locator_refs[0],
        ),
        semantic_zoom_state=build_semantic_zoom_state("overview", "standard"),
    )


def build_valid_canonical():
    return build_canonical()


def build_ephemeral():
    return build_ephemeral_return_state(
        scroll_refs=("risk-list", "center-map"),
        inspector_width=360,
        inspector_expanded=True,
        temporary_expansion_refs=("risk-anchor::ae::1",),
        focus_ref="risk-list",
    )


def build_return_context_fixture():
    return build_s6_return_context(build_canonical(), build_ephemeral())


def build_return_context_value():
    return build_return_context_fixture()


def build_performance_corpus() -> tuple[S6PerformanceRecord, ...]:
    records = []
    for kind, count in (("event", 1000), ("indicator", 40), ("risk_anchor", 300)):
        for ordinal in range(count):
            records.append(S6PerformanceRecord(
                record_kind=kind,
                ordinal=ordinal,
                domain=DOMAINS[ordinal % len(DOMAINS)],
                source_locator_ref=f"locator::s6::{kind}::{ordinal:04d}",
            ))
    return tuple(records)


def build_corpus_records():
    return build_performance_corpus()


def build_performance_identity() -> S6PerformanceCorpusIdentity:
    return build_s6_performance_corpus_identity()


def build_performance_profile_fixture() -> S6PerformanceProfile:
    return build_s6_performance_profile()


def build_zoom_projection(level: str = "overview", density: str = "standard"):
    subject = build_subject_packet()
    return project_density_and_zoom(
        subject, build_semantic_zoom_state(level, density), build_subject_workspace_packet()
    )


def build_keyboard():
    return build_keyboard_contract()


def as_mapping(value):
    return s6_as_mapping(value)


build_deep_link_identity_fixture = build_deep_link
build_canonical_return_state_fixture = build_canonical
build_return_context = build_return_context_fixture
build_performance_corpus_identity = build_performance_identity
build_performance_profile = build_performance_profile_fixture


__all__ = [
    "S6PerformanceRecord", "build_subject_packet", "build_aemh_packet", "build_subject_workspace_packet",
    "build_subject_workspace",
    "build_deep_link", "build_valid_deep_link", "build_deep_link_identity_fixture", "build_canonical",
    "build_valid_canonical", "build_canonical_return_state_fixture", "build_ephemeral",
    "build_return_context_fixture", "build_return_context_value", "build_return_context", "build_performance_corpus",
    "build_corpus_records", "build_performance_identity", "build_performance_corpus_identity",
    "build_performance_profile_fixture", "build_performance_profile", "build_zoom_projection", "build_keyboard", "as_mapping",
]
