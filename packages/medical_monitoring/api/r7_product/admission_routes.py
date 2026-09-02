"""Project-scoped C1 data-admission routes for the R7 product API.

Phase C C1 exposes the deterministic real-file admission contract as three
thin product endpoints: create an admission attempt from a read-only source
directory, read its status, and preview its structure profile.  This module
owns resolution, authorization, request validation, Chinese error envelopes
and the public-projection boundary only.  The admission pipeline itself
(isolated staging copy with streaming SHA-256 and atomic completion, the
format-neutral structure profile, and persistence of ``SourceRevision`` /
``ListingSnapshot`` through the existing ``graph.Store``) is injected as an
``admission_pipeline`` capability, mirroring how publication providers and
harness adapters are bound.  Without a bound pipeline every admission route
fails closed with a stable Chinese error and performs zero workspace I/O.

Candidate/fact boundary: admission ends at an imported full snapshot plus a
candidate structure profile.  No mapping candidate, mapping definition or
canonical fact is created, confirmed or projected here, and no route in this
module can generate one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol, Union

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, ValidationError

from ...runtime import project_backup as pb
from ...admission.pipeline import AdmissionPipelineError
from .errors import _error_response, _run_entry_error_response, _validation_error_response


ADMISSION_SCHEMA_VERSION = "mm-c1-data-admission-v1"

_ATTEMPT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SOURCE_DIR_MAX_LENGTH = 4096

# Public-projection boundary (PRD: paths, hashes and internal object ids live
# only in the collapsed technical-details view).  A pipeline payload carrying
# any of these keys outside ``technical_details`` is rejected fail-closed.
_ADMISSION_PUBLIC_FORBIDDEN_KEYS = frozenset(
    {
        "source_dir",
        "staging_dir",
        "staging_root",
        "workspace_dir",
        "workspace",
        "db_path",
        "content_hash",
        "content_digest",
        "sha256",
        "source_sha256",
        "copy_sha256",
        "manifest_path",
        "revision_id",
        "snapshot_id",
        "traceback",
        "sqlite",
    }
)
_TECHNICAL_CONTAINER_KEY = "technical_details"

_ADMISSION_STATUS_CODES = {
    "admission_source_invalid": 422,
    "admission_copy_rejected": 409,
    "admission_profile_unavailable": 409,
    "admission_project_identity_conflict": 409,
    "admission_attempt_not_found": 404,
    "admission_attempt_id_invalid": 422,
    "admission_pipeline_unconfigured": 503,
    "admission_pipeline_failed": 500,
    "admission_projection_violation": 500,
}

_ADMISSION_MESSAGES = {
    "admission_source_invalid": "未找到可导入的数据目录。请确认所选数据位置存在且包含数据文件后重试。",
    "admission_copy_rejected": "数据复制校验未通过，系统已拒绝本次导入，原始数据未受影响。请重新发起导入；如再次失败，请检查数据来源是否完整。",
    "admission_profile_unavailable": "系统暂时无法识别这批数据的结构，本次导入未完成。请确认文件格式受支持后重新导入。",
    "admission_project_identity_conflict": "当前为演示项目，不能接入本机数据。请在实际研究项目中使用数据接入。",
    "admission_attempt_not_found": "未找到对应的数据导入记录。请返回上一步重新选择，或重新发起导入。",
    "admission_pipeline_unconfigured": "数据接入服务尚未配置，暂时无法导入新的数据版本。请联系管理员完成配置后再试。",
    "admission_pipeline_failed": "数据导入过程中出现问题，本次操作未生效，原始数据未受影响。请重试；如再次失败请联系管理员。",
    "admission_projection_violation": "系统生成的数据识别结果格式异常，本次结果未展示，原始数据未受影响。请重试；如再次失败，请查看技术详情。",
    "admission_attempt_id_invalid": "数据导入记录标识无效。请返回上一步重新进入。",
}


class AdmissionPipeline(Protocol):
    """Contract the C1 admission pipeline must satisfy.

    Implementations (staging copier + structure profiler + Store persistence)
    are owned by the C1 contract slices; this seam only fixes the three
    integration calls.  Every method is synchronous and returns a
    JSON-ready public mapping:

    * ``create_attempt`` returns at least ``attempt_id`` and ``state``.
    * ``attempt_status`` returns at least ``state``.
    * ``profile_preview`` returns at least ``tables`` (a list).

    Paths, hashes and internal object ids may only appear inside
    ``technical_details``; anything else is rejected before it reaches the
    client.  Implementations raise ``AdmissionPipelineError`` for expected
    product failures.
    """

    def create_attempt(
        self, *, project_id: str, source_dir: Path, workspace_dir: Path
    ) -> Mapping[str, Any]: ...

    def create_uploaded_attempt(
        self,
        *,
        project_id: str,
        uploads: list[tuple[str, Any]],
        workspace_dir: Path,
    ) -> Mapping[str, Any]: ...

    def attempt_status(
        self, *, project_id: str, attempt_id: str, workspace_dir: Path
    ) -> Mapping[str, Any]: ...

    def profile_preview(
        self, *, project_id: str, attempt_id: str, workspace_dir: Path
    ) -> Mapping[str, Any]: ...


class ProductDataAdmissionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_dir: str


@dataclass(frozen=True)
class AdmissionRouteContext:
    root: Path
    resolve_project: Any
    authorize: Any
    read_json_object: Any
    acquire_product_write_gate: Any
    workspace_dir: Any
    monitoring_action: Any
    admission_pipeline: Any


def _admission_error(code: str) -> JSONResponse:
    return _error_response(
        _ADMISSION_STATUS_CODES[code], code, _ADMISSION_MESSAGES[code]
    )


def _validated_attempt_id(attempt_id: str) -> Optional[str]:
    if not isinstance(attempt_id, str) or not _ATTEMPT_ID_RE.match(attempt_id or ""):
        return None
    return attempt_id


def _validated_source_dir(value: Any) -> Optional[str]:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > _SOURCE_DIR_MAX_LENGTH
        or "\x00" in value
    ):
        return None
    return value


def _public_admission_projection(
    payload: Mapping[str, Any], *, required_keys: tuple[str, ...]
) -> Union[dict[str, Any], JSONResponse]:
    if not isinstance(payload, Mapping):
        return _admission_error("admission_projection_violation")
    for key in required_keys:
        value = payload.get(key)
        if not isinstance(value, (str, int, list)) or (
            isinstance(value, str) and not value.strip()
        ):
            return _admission_error("admission_projection_violation")
    attempt_id = payload.get("attempt_id")
    if attempt_id is not None and _validated_attempt_id(str(attempt_id)) is None:
        return _admission_error("admission_projection_violation")
    public: dict[str, Any] = {}
    technical: Any = payload.get(_TECHNICAL_CONTAINER_KEY)
    for key, value in payload.items():
        if key == _TECHNICAL_CONTAINER_KEY:
            continue
        if key in _ADMISSION_PUBLIC_FORBIDDEN_KEYS:
            return _admission_error("admission_projection_violation")
        public[key] = value
    if technical is not None:
        if not isinstance(technical, Mapping):
            return _admission_error("admission_projection_violation")
        public[_TECHNICAL_CONTAINER_KEY] = dict(technical)
    return public


def register_admission_routes(router: APIRouter, context: AdmissionRouteContext) -> None:
    resolve_project = context.resolve_project
    authorize = context.authorize
    _read_json_object = context.read_json_object
    acquire_product_write_gate = context.acquire_product_write_gate
    _workspace_dir = context.workspace_dir
    MonitoringAction = context.monitoring_action
    admission_pipeline = context.admission_pipeline

    def _pipeline_or_error() -> Union[Any, JSONResponse]:
        if admission_pipeline is None:
            return _admission_error("admission_pipeline_unconfigured")
        return admission_pipeline

    @router.post("/data-admissions")
    async def create_data_admission(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.INTAKE_BATCH,
        )
        if isinstance(auth, JSONResponse):
            return auth
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductDataAdmissionCreateRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        source_dir = _validated_source_dir(parsed.source_dir)
        if source_dir is None:
            return _admission_error("admission_source_invalid")
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            result = pipeline.create_attempt(
                project_id=canonical,
                source_dir=Path(source_dir),
                workspace_dir=_workspace_dir(context.root, canonical),
            )
            public = _public_admission_projection(result, required_keys=("attempt_id", "state"))
            if isinstance(public, JSONResponse):
                return public
            return {
                "schema_version": ADMISSION_SCHEMA_VERSION,
                "project_id": canonical,
                **public,
            }
        except AdmissionPipelineError as exc:
            return _admission_error(exc.code)
        except Exception:
            return _admission_error("admission_pipeline_failed")
        finally:
            write_permit.release()

    @router.post("/data-admissions/upload")
    async def upload_data_admission(
        project_id: str,
        request: Request,
        files: list[UploadFile] = File(...),
        relative_paths: list[str] = Form(...),
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.INTAKE_BATCH,
        )
        if isinstance(auth, JSONResponse):
            return auth
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        if not files or len(files) != len(relative_paths):
            return _admission_error("admission_source_invalid")
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            result = pipeline.create_uploaded_attempt(
                project_id=canonical,
                uploads=[
                    (relative_path, upload.file)
                    for relative_path, upload in zip(relative_paths, files)
                ],
                workspace_dir=_workspace_dir(context.root, canonical),
            )
            public = _public_admission_projection(
                result, required_keys=("attempt_id", "state")
            )
            if isinstance(public, JSONResponse):
                return public
            return {
                "schema_version": ADMISSION_SCHEMA_VERSION,
                "project_id": canonical,
                **public,
            }
        except AdmissionPipelineError as exc:
            return _admission_error(exc.code)
        except Exception:
            return _admission_error("admission_pipeline_failed")
        finally:
            write_permit.release()

    def _read_admission(
        project_id: str,
        request: Request,
        attempt_id: str,
        *,
        handler_name: str,
        required_keys: tuple[str, ...],
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_SOURCE_EVIDENCE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _admission_error("admission_attempt_id_invalid")
        handler = getattr(pipeline, handler_name)
        try:
            result = handler(
                project_id=canonical,
                attempt_id=validated_attempt,
                workspace_dir=_workspace_dir(context.root, canonical),
            )
            public = _public_admission_projection(result, required_keys=required_keys)
            if isinstance(public, JSONResponse):
                return public
            return {
                "schema_version": ADMISSION_SCHEMA_VERSION,
                "project_id": canonical,
                "attempt_id": validated_attempt,
                **public,
            }
        except AdmissionPipelineError as exc:
            return _admission_error(exc.code)
        except Exception:
            return _admission_error("admission_pipeline_failed")

    @router.get("/data-admissions/{attempt_id}")
    async def get_data_admission_status(
        project_id: str, attempt_id: str, request: Request
    ) -> Any:
        return _read_admission(
            project_id,
            request,
            attempt_id,
            handler_name="attempt_status",
            required_keys=("state",),
        )

    @router.get("/data-admissions/{attempt_id}/profile")
    async def get_data_admission_profile(
        project_id: str, attempt_id: str, request: Request
    ) -> Any:
        return _read_admission(
            project_id,
            request,
            attempt_id,
            handler_name="profile_preview",
            required_keys=("tables",),
        )


__all__ = [
    "ADMISSION_SCHEMA_VERSION",
    "AdmissionPipeline",
    "AdmissionPipelineError",
    "AdmissionRouteContext",
    "ProductDataAdmissionCreateRequest",
    "register_admission_routes",
]
