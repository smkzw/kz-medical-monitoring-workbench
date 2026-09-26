"""Accepted publication-context reconstruction for public R7 results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional

from fastapi.responses import JSONResponse

from ...graph.store import Store
from ...projections.product_adapter import R5ProductAdapter, R5ProductAdapterError
from ...runtime import launch_registry as lr
from ...runtime.run_entry import MonitoringRunEntry
from ...runtime.runtime_progress import ARTIFACT_DIR_NAME, RUNTIME_DB_NAME, RUNTIME_DIR_NAME
from .contracts import ProductPublicationError
from .frozen_read_model import (
    load_frozen_read_model_document,
    restore_frozen_packet,
)
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


@dataclass(frozen=True)
class ResolvedResultContext:
    """One request-scoped, publication-bound result context.

    The mode outputs are copied from the four immutable artifacts recorded on
    the publication row.  Consumers therefore never reopen an active findings
    pointer after resolving a historical result token.
    """

    registry: lr.LaunchRegistry
    entry: MonitoringRunEntry
    launch: lr.LaunchRecord
    publication: lr.ResultPublication
    adapter: Optional[R5ProductAdapter]
    mode_outputs: Mapping[str, Mapping[str, Any]]
    mode_output_artifacts: Mapping[str, str]

    def __iter__(self) -> Iterator[Any]:
        return iter(
            (
                self.registry,
                self.entry,
                self.launch,
                self.publication,
                self.adapter,
            )
        )

    def __getitem__(self, index: int) -> Any:
        return tuple(self)[index]

    def close(self) -> None:
        self.entry.close()
        self.registry.close()

    def public_findings_envelope(self) -> dict[str, Any]:
        """公开findings信封（W01-R26 A12/A13）。

        - 新形态载荷（携带平行``findings``数组，Finding冻结DTO）：findings
          即Finding DTO行，QueryDraft保留自身ID随meta携带；
        - 旧形态载荷（pre-S3，仅query_drafts）：不伪造Finding DTO——
          findings为空数组，drafts以自身身份随meta如实携带，并在
          payload_shape标注来源形态（S2冻结read model读出的旧token）；
        - 既无findings也无query_drafts的载荷：明确result_context_unavailable
          （删除旧的query_drafts换名findings回退）。
        content_sha256为实际载荷内容的确定性哈希，不再是artifact_id。
        """
        output = self.mode_outputs.get("affected_query_draft")
        artifact_id = self.mode_output_artifacts.get("affected_query_draft")
        if output is None:
            return {
                "findings": [],
                "query_drafts": [],
                "meta": {
                    "state": "not_applicable",
                    "artifact": None,
                    "content_sha256": None,
                    "payload_shape": "not_applicable",
                    "total": 0,
                    "gaps": 0,
                    "error": None,
                },
            }
        output_payload = output.get("payload")
        if not isinstance(output_payload, Mapping):
            raise ProductPublicationError("result_context_unavailable")
        if "findings" in output_payload:
            finding_rows = output_payload.get("findings")
            if not isinstance(finding_rows, list):
                raise ProductPublicationError("result_context_unavailable")
            draft_rows = output_payload.get("query_drafts")
            draft_rows = draft_rows if isinstance(draft_rows, list) else []
            rows = [
                dict(item) for item in finding_rows if isinstance(item, Mapping)
            ]
            if len(rows) != len(finding_rows):
                raise ProductPublicationError("result_context_unavailable")
            drafts = [
                dict(item) for item in draft_rows if isinstance(item, Mapping)
            ]
            payload_shape = "finding_dto_v1"
        elif "query_drafts" in output_payload:
            draft_rows = output_payload.get("query_drafts")
            if not isinstance(draft_rows, list):
                raise ProductPublicationError("result_context_unavailable")
            rows = []
            drafts = [
                dict(item) for item in draft_rows if isinstance(item, Mapping)
            ]
            payload_shape = "legacy_query_drafts"
        else:
            raise ProductPublicationError("result_context_unavailable")
        served_rows = rows if payload_shape == "finding_dto_v1" else drafts
        return {
            "findings": rows,
            "query_drafts": drafts,
            "meta": {
                "state": (
                    "completed_with_findings"
                    if rows
                    else "completed_no_findings"
                ),
                "artifact": artifact_id,
                "content_sha256": (
                    lr.content_digest(served_rows) if served_rows else None
                ),
                "payload_shape": payload_shape,
                "total": len(rows),
                "gaps": sum(
                    1 for item in rows if item.get("kind") == "coverage_gap"
                ),
                "error": None,
            },
        }


def load_public_result_context(
    dependencies: ResultContextDependencies,
    canonical_project_id: str,
    result_context_token: str,
    *,
    site_ref: Optional[str] = None,
    require_product_adapter: bool = True,
    continuity_context: bool = False,
) -> ResolvedResultContext:
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

        if (
            site_ref is not None
            and site_ref not in publication.site_coverage
        ):
            raise ProductPublicationError("result_center_out_of_scope")
        # The result token resolves the persisted publication.  Reading a
        # historical result must not re-select the project's current active
        # snapshot or setup manifest; those are launch-time inputs already
        # frozen on ResultPublication and verified below through the run gate
        # and authority packet digests.
        if (
            launch.current_snapshot_token != publication.snapshot_token
            or not publication.snapshot_ref
            or not publication.source_revision_id
            or not publication.data_cutoff
            or not publication.setup_manifest_digest
            or not publication.setup_manifest_identity
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
        runtime_dir = _workspace_dir(root, canonical_project_id) / RUNTIME_DIR_NAME
        r1_store = Store(
            runtime_dir / RUNTIME_DB_NAME,
            runtime_dir / ARTIFACT_DIR_NAME,
        )
        mode_outputs: dict[str, Mapping[str, Any]] = {}
        mode_output_artifacts: dict[str, str] = {}
        try:
            if (
                publication.frozen_read_model_artifact_id
                and publication.frozen_read_model_sha256
            ):
                # W01-R26（20260926）：冻结read model优先。digest校验对象
                # 从"当下重算"换成"发布时快照"，校验强度不降：CAS完整性、
                # 文档sha256、版本与锚点仍逐一核对；投影代码升级不再导致
                # 旧token不可读。
                document = load_frozen_read_model_document(
                    r1_store, publication
                )
                packet = restore_frozen_packet(document)
                if packet.product_packet is None:
                    # 发布包本身无product视图（product-less发布，连续性
                    # 合成通道）：公开视图只能来自读取侧重建，保持既有
                    # 行为；锚点仍以下方冻结快照比对为准。
                    packet = _build_r5_publication_packet(
                        publication_provider,
                        authority_identity,
                        attempts=gate["receipt_attempts"],
                        bridge=publication_bridge,
                        product_packet_factory=r5_product_packet_factory,
                    )
            else:
                # 存量发布行无冻结引用：保持既有重建比对路径。
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
            for member_id in publication.artifact_member_ids:
                if not r1_store.verify_artifact(member_id):
                    raise ProductPublicationError("result_context_unavailable")
                envelope = r1_store.get_artifact(member_id)
                payload = envelope.payload
                output_kind = str(payload.get("output_kind") or "")
                if (
                    envelope.run_id != launch.run_id
                    or not output_kind
                    or output_kind in mode_outputs
                    or str(payload.get("project_id") or "")
                    != canonical_project_id
                    or str(payload.get("run_id") or "") != launch.run_id
                    or str(payload.get("data_cutoff") or "")
                    != publication.data_cutoff
                    or str(
                        (payload.get("authority_refs") or {}).get(
                            "authority_digest"
                        )
                    )
                    != packet.packet_digest
                ):
                    raise ProductPublicationError("result_context_unavailable")
                mode_outputs[output_kind] = dict(payload)
                mode_output_artifacts[output_kind] = member_id
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
        return ResolvedResultContext(
            registry=registry,
            entry=entry,
            launch=launch,
            publication=publication,
            adapter=adapter if require_product_adapter else None,
            mode_outputs=mode_outputs,
            mode_output_artifacts=mode_output_artifacts,
        )
    except Exception:
        if entry is not None:
            entry.close()
        registry.close()
        raise

__all__ = [
    "ResolvedResultContext",
    "ResultContextDependencies",
    "load_public_result_context",
]
