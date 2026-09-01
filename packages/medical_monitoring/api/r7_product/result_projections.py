"""Launch, publication and public-result projections for the R7 product API."""

from __future__ import annotations

from typing import Any, Mapping

from ...runtime import launch_registry as lr
from .contracts import ProductPublicationError
from .public_text import _projection

_PUBLICATION_MESSAGES = {
    "publication_not_available": "结果尚未整理完成",
    "publication_publishing": "结果正在整理，请稍候。",
    "publication_available": "结果已整理完成。",
    "publication_recoverable_failed": "结果整理暂时失败，可重试。",
    "publication_blocked": "结果尚未整理完成",
    "authority_provider_unavailable": "结果权威暂不可用，结果整理未完成。",
    "authority_provider_invalid": "结果权威接口无效，结果整理未完成。",
    "authority_identity_mismatch": "本次结果权威身份不一致，结果入口已关闭。",
    "manifest_identity_mismatch": "本次监查范围身份不一致，结果整理已阻断。",
    "receipt_gate_blocked": "本次结果材料未完整通过核对，结果整理已阻断。",
    "deterministic_gate_blocked": "本次监查的确定性工作项未完整完成，结果整理已阻断。",
    "runtime_read_failed": "本次监查运行记录暂时无法读取，结果整理可重试。",
    "result_context_not_found": "本次结果暂不可查看，请返回进度页",
    "result_context_unavailable": "本次结果暂不可查看，请返回进度页",
    "result_center_out_of_scope": "该中心不在本次监查范围",
    "continuity_unavailable": "连续性比较结果暂不可查看，请返回结果页",
}


def _launch_projection(record: lr.LaunchRecord, *, replayed: bool) -> dict[str, Any]:
    body = record.public_projection()
    body["replayed"] = bool(replayed)
    return _projection(body)

def _publication_status_text(state: str, *, run_state: str = "") -> str:
    if (
        run_state == lr.STATE_COMPLETED
        and state != lr.PUBLICATION_STATE_AVAILABLE
    ):
        return "分析已结束，结果整理未完成"
    if state == lr.PUBLICATION_STATE_AVAILABLE:
        return _PUBLICATION_MESSAGES["publication_available"]
    if state == lr.PUBLICATION_STATE_PUBLISHING:
        return _PUBLICATION_MESSAGES["publication_publishing"]
    if state == lr.PUBLICATION_STATE_RECOVERABLE_FAILED:
        return _PUBLICATION_MESSAGES["publication_recoverable_failed"]
    if state == lr.PUBLICATION_STATE_BLOCKED:
        return _PUBLICATION_MESSAGES["publication_blocked"]
    return _PUBLICATION_MESSAGES["publication_not_available"]


def _publication_projection(
    public_run_token: str,
    state: str,
    *,
    replayed: bool = False,
    run_state: str = "",
) -> dict[str, Any]:
    if state not in lr.PUBLICATION_STATE_VALUES and state != "not_started":
        raise ProductPublicationError("internal_error")
    return {
        "public_run_token": public_run_token,
        "publication_state": state,
        "result_available": state == lr.PUBLICATION_STATE_AVAILABLE,
        "publication_status_text": _publication_status_text(
            state, run_state=run_state
        ),
        "replayed": bool(replayed),
    }

_PUBLIC_RESULT_LOCATOR_KEYS = (
    "site_ref",
    "subject_ref",
    "spine_ref",
    "window_start",
    "window_end",
    "risk_instance_ref",
    "risk_anchor_ref",
    "visit_ref",
    "event_ref",
    "source_locator_ref",
)
_PUBLIC_RESULT_FORBIDDEN_KEYS = frozenset(
    {
        "run_id",
        "run_ref",
        "snapshot_ref",
        "cutoff_ref",
        "cutoff_state",
        "opaque_run_ref",
        "opaque_snapshot_ref",
        "authority_hash",
        "authority_receipt",
        "authority_receipt_ref",
        "receipt_id",
        "receipt_ref",
        "receipt_set_digest",
        "packet_identity",
        "packet_digest",
        "r5_authority_packet_id",
        "r5_authority_packet_digest",
        "s4_authority_packet_identities",
        "s4_authority_packet_digests",
        "source_snapshot_sha256",
        "source_revision_content_hash",
        "response_snapshot_sha256",
        "return_context_key",
        "r6_output_set_digest",
        "artifact_member_ids",
        "artifact_member_ids_json",
        "artifact_member_set_digest",
        "r6_publication_digest",
        "r6_receipt_digest",
    }
)


def _public_result_projection(value: Any) -> Any:
    """Strip internal authority identity while retaining the R5 audience shape."""
    if isinstance(value, Mapping):
        projected: dict[str, Any] = {}
        for raw_key, item in value.items():
            key = str(raw_key)
            lowered = key.casefold()
            if (
                lowered in _PUBLIC_RESULT_FORBIDDEN_KEYS
                or lowered.startswith(("authority_", "receipt_", "s4_", "r5_"))
                or lowered.endswith("_snapshot_ref")
                or lowered.endswith("_cutoff_ref")
            ):
                continue
            projected[key] = _public_result_projection(item)
        if "content_hash" in projected:
            projected["content_hash"] = lr.content_digest(
                {**projected, "content_hash": ""}
            )
        return projected
    if isinstance(value, list):
        return [_public_result_projection(item) for item in value]
    if isinstance(value, tuple):
        return [_public_result_projection(item) for item in value]
    return value

__all__ = [
    "_PUBLICATION_MESSAGES",
    "_launch_projection",
    "_publication_status_text",
    "_publication_projection",
    "_PUBLIC_RESULT_LOCATOR_KEYS",
    "_PUBLIC_RESULT_FORBIDDEN_KEYS",
    "_public_result_projection",
]

