"""Accepted publication-context reconstruction for public R7 results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from fastapi.responses import JSONResponse

from ...graph.store import Store
from ...projections.product_adapter import R5ProductAdapter, R5ProductAdapterError
from ...runtime import launch_registry as lr
from ...runtime.run_entry import MonitoringRunEntry
from ...runtime.runtime_progress import ARTIFACT_DIR_NAME, RUNTIME_DB_NAME, RUNTIME_DIR_NAME
from .contracts import ProductPublicationError
from .publication_providers import _r5_publication_types
from .route_utils import _workspace_dir


@dataclass(frozen=True)
class ResultContextDependencies:
    root: Path
    open_legacy_view: Any
    open_launch_registry: Any
    open_entry: Any
    publication_setup_inputs: Any
    publication_bridge: Any
    publication_provider: Any
    r5_product_packet_factory: Any
    harness_r1_profile: Any
    build_r5_publication_packet: Any
    read_publication_gate: Any


def load_public_result_context(
    dependencies: ResultContextDependencies,
    canonical_project_id: str,
    result_context_token: str,
    *,
    site_ref: Optional[str] = None,
    require_product_adapter: bool = True,
    continuity_context: bool = False,
) -> tuple[
    lr.LaunchRegistry,
    MonitoringRunEntry,
    lr.LaunchRecord,
    lr.ResultPublication,
    Optional[R5ProductAdapter],
]:
    """Resolve one persisted context and rebuild the accepted R5 view."""
    root = dependencies.root
    open_legacy_view = dependencies.open_legacy_view
    open_launch_registry = dependencies.open_launch_registry
    _open_entry = dependencies.open_entry
    _publication_setup_inputs = dependencies.publication_setup_inputs
    publication_bridge = dependencies.publication_bridge
    publication_provider = dependencies.publication_provider
    r5_product_packet_factory = dependencies.r5_product_packet_factory
    harness_r1_profile = dependencies.harness_r1_profile
    _build_r5_publication_packet = dependencies.build_r5_publication_packet
    _read_publication_gate = dependencies.read_publication_gate
    legacy_view = open_legacy_view(canonical_project_id)
    if legacy_view is not None:
        # Legacy result data is readable only through the bounded facade;
        # this R5 adapter requires mutable current-schema stores.
        legacy_view.close()
        raise ProductPublicationError("result_context_unavailable")
    registry = open_launch_registry(canonical_project_id)
    if isinstance(registry, JSONResponse):
        raise ProductPublicationError("result_context_unavailable")
    entry: Optional[MonitoringRunEntry] = None
    try:
        try:
            publication = registry.get_publication_by_result_context_token(
                result_context_token,
                project_id=canonical_project_id,
            )
        except lr.LaunchRegistryError as exc:
            raise ProductPublicationError(
                "result_context_unavailable"
            ) from exc
        if (
            publication.publication_state
            != lr.PUBLICATION_STATE_AVAILABLE
            or publication.result_context_token != result_context_token
        ):
            raise ProductPublicationError("result_context_unavailable")
        try:
            launch = registry.get_by_public_token(
                publication.public_run_token,
                project_id=canonical_project_id,
            )
        except lr.LaunchRegistryError as exc:
            raise ProductPublicationError(
                "result_context_unavailable"
            ) from exc
        if (
            launch.run_id != publication.run_id
            or launch.public_run_token != publication.public_run_token
            or launch.run_state != lr.STATE_COMPLETED
            or not launch.result_available
        ):
            raise ProductPublicationError("result_context_unavailable")

        (
            current,
            _setup_manifest,
            coverage,
            setup_identity,
            setup_digest,
        ) = _publication_setup_inputs(canonical_project_id, launch)
        current_source_revision = (
            current.source_revision_id or current.snapshot_ref
        )
        if (
            site_ref is not None
            and site_ref not in publication.site_coverage
        ):
            raise ProductPublicationError("result_center_out_of_scope")
        if (
            launch.current_snapshot_token != publication.snapshot_token
            or current.snapshot_token != publication.snapshot_token
            or current.snapshot_ref != publication.snapshot_ref
            or current.data_cutoff != publication.data_cutoff
            or current_source_revision != publication.source_revision_id
            or tuple(coverage) != tuple(publication.site_coverage)
            or setup_digest != publication.setup_manifest_digest
            or setup_identity != dict(publication.setup_manifest_identity)
        ):
            raise ProductPublicationError("result_context_unavailable")

        entry_candidate = _open_entry(
            _workspace_dir(root, canonical_project_id),
            allow_create=False,
        )
        if isinstance(entry_candidate, JSONResponse):
            raise ProductPublicationError("result_context_unavailable")
        entry = entry_candidate
        gate = _read_publication_gate(
            _workspace_dir(root, canonical_project_id),
            launch.run_id,
            entry=entry,
            harness_r1_profile=harness_r1_profile,
        )
        if (
            gate["revision"] != publication.manifest_revision
            or gate["digest"] != publication.manifest_digest
            or gate["identity"]
            != dict(publication.runtime_manifest_identity)
            or tuple(gate["receipt_ids"])
            != tuple(publication.receipt_identities)
            or gate["receipt_set_digest"]
            != publication.receipt_set_digest
        ):
            raise ProductPublicationError("result_context_unavailable")

        (
            _packet_type,
            _bridge_type,
            _bridge_error_type,
            _input_type,
            identity_type,
        ) = _r5_publication_types()
        authority_identity = identity_type(
            project_ref=canonical_project_id,
            run_ref=launch.run_id,
            public_run_token=launch.public_run_token,
            snapshot_ref=publication.snapshot_ref or publication.snapshot_token,
            cutoff_ref=publication.data_cutoff,
            site_refs=publication.site_coverage,
            snapshot_token=publication.snapshot_token,
        )
        packet = _build_r5_publication_packet(
            publication_provider,
            authority_identity,
            attempts=gate["receipt_attempts"],
            bridge=publication_bridge,
            product_packet_factory=r5_product_packet_factory,
        )
        if (
            packet.packet_identity != publication.r5_authority_packet_id
            or packet.packet_digest != publication.r5_authority_packet_digest
            or tuple(packet.site_refs) != tuple(publication.site_coverage)
        ):
            raise ProductPublicationError("result_context_unavailable")
        if (
            not publication.r6_output_set_digest
            or len(publication.artifact_member_ids) != 4
            or publication.artifact_member_set_digest
            != lr.content_digest(list(publication.artifact_member_ids))
        ):
            raise ProductPublicationError(
                "continuity_unavailable"
                if continuity_context
                else "result_context_unavailable"
            )
        runtime_dir = _workspace_dir(root, canonical_project_id) / RUNTIME_DIR_NAME
        r1_store = Store(
            runtime_dir / RUNTIME_DB_NAME,
            runtime_dir / ARTIFACT_DIR_NAME,
        )
        try:
            if any(
                not r1_store.verify_artifact(member_id)
                for member_id in publication.artifact_member_ids
            ):
                raise ProductPublicationError("result_context_unavailable")
        finally:
            r1_store.close()
        product_packet = getattr(packet, "product_packet", None)
        if product_packet is None:
            raise ProductPublicationError("authority_provider_invalid")
        if (
            getattr(product_packet, "project_ref", canonical_project_id)
            != canonical_project_id
            or getattr(product_packet, "run_ref", launch.run_id)
            != launch.run_id
            or getattr(
                product_packet,
                "snapshot_ref",
                publication.snapshot_ref or publication.snapshot_token,
            )
            != (publication.snapshot_ref or publication.snapshot_token)
            or getattr(product_packet, "cutoff_ref", publication.data_cutoff)
            != publication.data_cutoff
        ):
            raise ProductPublicationError("result_context_unavailable")
        for collection_name, reference_name in (
                ("sites", "site_ref"),
                ("subjects", "subject_ref"),
                ("events", "event_ref"),
                ("visits", "visit_ref"),
                ("risks", "risk_ref"),
                ("sources", "locator_ref"),
        ):
            if not hasattr(packet, collection_name):
                continue
            bridge_refs = {
                getattr(item, reference_name, None)
                for item in getattr(packet, collection_name, ())
            }
            product_refs = {
                getattr(item, reference_name, None)
                for item in getattr(product_packet, collection_name, ())
            }
            if bridge_refs != product_refs:
                raise ProductPublicationError("result_context_unavailable")

        def product_packet_provider(
            project_ref: str,
            run_ref: Optional[str] = None,
            snapshot_ref: Optional[str] = None,
            cutoff_ref: Optional[str] = None,
        ) -> Any:
            if (
                project_ref != canonical_project_id
                or run_ref is not None
                and run_ref != launch.run_id
                or snapshot_ref is not None
                and snapshot_ref != (
                    publication.snapshot_ref or publication.snapshot_token
                )
                or cutoff_ref is not None
                and cutoff_ref != publication.data_cutoff
            ):
                raise R5ProductAdapterError(
                    "AUTHORITY_IDENTITY_MISMATCH"
                )
            return product_packet

        adapter = R5ProductAdapter(product_packet_provider)
        return (
            registry,
            entry,
            launch,
            publication,
            adapter if require_product_adapter else None,
        )
    except Exception:
        if entry is not None:
            entry.close()
        registry.close()
        raise

__all__ = ["ResultContextDependencies", "load_public_result_context"]
