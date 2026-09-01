"""Audience overlays, error responses and setup identity for R7 publication."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional

from fastapi.responses import JSONResponse

from ...runtime import launch_registry as lr
from ...runtime import run_setup as rs
from .contracts import ProductPrepareAndStartRequest, ProductPublicationError
from .errors import _error_response
from .public_text import _SECRET_VALUE
from .result_projections import (
    _PUBLICATION_MESSAGES,
    _PUBLIC_RESULT_LOCATOR_KEYS,
    _public_result_projection,
    _publication_projection,
    _publication_status_text,
)
from .route_utils import _workspace_dir
from .runtime_manifest import _publication_manifest_identity


def publication_overlay(
    root: Path,
    canonical_project_id: str,
    run_id: str,
    base: Mapping[str, Any],
) -> dict[str, Any]:
    """Overlay registry publication state without changing R1 progress."""
    public_token = lr.derive_public_run_token(canonical_project_id, run_id)
    state = "not_started"
    has_launch = False
    launch_path = (
        _workspace_dir(root, canonical_project_id) / lr.LAUNCH_REGISTRY_DB_NAME
    )
    registry: Optional[lr.LaunchRegistry] = None
    try:
        if launch_path.is_file():
            registry = lr.LaunchRegistry(
                launch_path, project_id=canonical_project_id
            )
            launch = registry.get(run_id, project_id=canonical_project_id)
            has_launch = True
            try:
                publication = registry.get_publication(
                    project_id=canonical_project_id,
                    run_id=run_id,
                )
                state = publication.publication_state
            except lr.LaunchRegistryError as exc:
                if exc.code != "publication_not_found":
                    raise
                state = "not_started"
            public_token = launch.public_run_token
        return {
            **dict(base),
            "publication_state": state,
            "result_available": state == lr.PUBLICATION_STATE_AVAILABLE,
            "publication_status_text": _publication_status_text(
                state, run_state=str(base.get("run_state", ""))
            ),
            "_publication_has_launch": has_launch,
            "_publication_public_token": public_token,
        }
    except lr.LaunchRegistryError as exc:
        if exc.code in {"run_not_found", "public_run_not_found"}:
            return {
                **dict(base),
                "publication_state": "not_started",
                "result_available": False,
                "publication_status_text": _publication_status_text(
                    "not_started",
                    run_state=str(base.get("run_state", "")),
                ),
                "_publication_has_launch": False,
                "_publication_public_token": public_token,
            }
        raise
    except Exception:
        return {
            **dict(base),
            "publication_state": lr.PUBLICATION_STATE_RECOVERABLE_FAILED,
            "result_available": False,
            "publication_status_text": _PUBLICATION_MESSAGES[
                "publication_recoverable_failed"
            ],
            "_publication_has_launch": has_launch,
            "_publication_public_token": public_token,
        }
    finally:
        if registry is not None:
            registry.close()


def publication_setup_inputs(
    resolve_launch_inputs: Any,
    canonical_project_id: str,
    launch: lr.LaunchRecord,
) -> tuple[rs.DataSnapshot, rs.WorkUnitManifest, tuple[str, ...], dict[str, Any], str]:
    parsed = ProductPrepareAndStartRequest(
        current_snapshot_token=launch.current_snapshot_token,
        mode=launch.mode,
        execution_basis=launch.execution_basis,
        baseline_token=launch.baseline_token,
        risk_rule_tokens=list(launch.rule_tokens),
        idempotency_key=launch.idempotency_key,
    )
    resolved = resolve_launch_inputs(canonical_project_id, parsed)
    if isinstance(resolved, JSONResponse):
        raise ProductPublicationError("manifest_identity_mismatch")
    current, _, _, manifest = resolved
    setup_identity = _publication_manifest_identity(manifest)
    setup_digest = manifest.manifest_digest
    if launch.manifest_digest is not None and launch.manifest_digest != setup_digest:
        raise ProductPublicationError("manifest_identity_mismatch")
    coverage = tuple(
        sorted(
            {
                str(row["site_ref"])
                for row in current.rows
                if isinstance(row, Mapping)
                and isinstance(row.get("site_ref"), str)
                and row.get("site_ref")
            }
        )
    )
    if not coverage:
        raise ProductPublicationError("authority_identity_mismatch")
    return current, manifest, coverage, setup_identity, setup_digest


def record_publication_failure(
    registry: lr.LaunchRegistry,
    publication: lr.ResultPublication,
    *,
    code: str,
    recoverable: bool,
) -> lr.ResultPublication:
    target = (
        lr.PUBLICATION_STATE_RECOVERABLE_FAILED
        if recoverable
        else lr.PUBLICATION_STATE_BLOCKED
    )
    message = _PUBLICATION_MESSAGES.get(
        code,
        _PUBLICATION_MESSAGES[
            "runtime_read_failed" if recoverable else "publication_blocked"
        ],
    )
    try:
        return registry.record_publication_failure(
            project_id=publication.project_id,
            run_id=publication.run_id,
            revision=publication.publication_revision,
            target_state=target,
            expected_state=publication.publication_state,
            error_code=code,
            error_message=message,
        )
    except lr.LaunchRegistryError:
        return registry.get_publication(
            project_id=publication.project_id,
            run_id=publication.run_id,
            revision=publication.publication_revision,
        )


def publication_failure_response(publication: lr.ResultPublication) -> JSONResponse:
    if publication.publication_state == lr.PUBLICATION_STATE_AVAILABLE:
        return _publication_projection(
            publication.public_run_token,
            publication.publication_state,
            replayed=True,
        )
    if publication.publication_state == lr.PUBLICATION_STATE_RECOVERABLE_FAILED:
        return _error_response(
            500,
            "publication_recoverable_failed",
            _PUBLICATION_MESSAGES["publication_recoverable_failed"],
        )
    if publication.publication_state == lr.PUBLICATION_STATE_BLOCKED:
        return _error_response(
            409,
            "publication_blocked",
            _PUBLICATION_MESSAGES["publication_blocked"],
        )
    return _error_response(
        422,
        "publication_not_available",
        _PUBLICATION_MESSAGES["publication_not_available"],
    )


def public_result_envelope(
    result: Mapping[str, Any],
    *,
    launch: lr.LaunchRecord,
    publication: lr.ResultPublication,
    result_context_token: str,
) -> dict[str, Any]:
    raw_identity = result.get("identity")
    if not isinstance(raw_identity, Mapping):
        raise ProductPublicationError("result_context_unavailable")
    projection = _public_result_projection(result.get("projection"))
    if not isinstance(projection, Mapping):
        raise ProductPublicationError("result_context_unavailable")
    identity: dict[str, Any] = {
        "project_ref": launch.project_id,
        "public_run_token": launch.public_run_token,
        "snapshot_token": publication.snapshot_token,
        "data_cutoff_text": publication.data_cutoff,
        "view": str(raw_identity.get("view") or ""),
        "mode_text": launch.mode_text,
        "site_scope_text": "、".join(
            f"中心 {site_ref}" for site_ref in publication.site_coverage
        ),
    }
    for key in _PUBLIC_RESULT_LOCATOR_KEYS:
        value = raw_identity.get(key)
        if value is not None:
            identity[key] = value
    if identity["view"] not in {"overview", "journey", "evidence"}:
        raise ProductPublicationError("result_context_unavailable")
    public_blob = json.dumps(
        {"identity": identity, "projection": projection}, ensure_ascii=False
    ).casefold()
    if _SECRET_VALUE.search(public_blob) or any(
        marker in public_blob
        for marker in (
            '"run_id"',
            '"run_ref"',
            '"snapshot_ref"',
            '"cutoff_ref"',
            '"authority_hash"',
            '"authority_receipt',
            '"packet_digest"',
            '"packet_identity"',
            '"s4_',
            '"r5_',
        )
    ):
        raise ProductPublicationError("result_context_unavailable")
    response_digest = lr.content_digest(
        {"identity": identity, "projection": projection}
    )
    return {
        "identity": identity,
        "projection": dict(projection),
        "result_context_token": result_context_token,
        "response_digest": response_digest,
    }


def public_result_error(exc: Exception) -> JSONResponse:
    if isinstance(exc, ProductPublicationError) and exc.code == (
        "result_center_out_of_scope"
    ):
        return _error_response(
            409,
            "result_center_out_of_scope",
            _PUBLICATION_MESSAGES["result_center_out_of_scope"],
        )
    if isinstance(exc, ProductPublicationError) and exc.code == (
        "continuity_unavailable"
    ):
        return _error_response(
            409,
            "continuity_unavailable",
            _PUBLICATION_MESSAGES["continuity_unavailable"],
        )
    return _error_response(
        409,
        "result_context_unavailable",
        _PUBLICATION_MESSAGES["result_context_unavailable"],
    )


__all__ = [
    "publication_overlay",
    "publication_setup_inputs",
    "record_publication_failure",
    "publication_failure_response",
    "public_result_envelope",
    "public_result_error",
]
