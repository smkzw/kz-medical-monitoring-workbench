"""Strict request parsing for read-only R7 public-result routes."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional, Union

from fastapi import Request
from fastapi.responses import JSONResponse

from ..run_entry import chinese_message_for
from ...runtime import run_setup as rs
from .errors import _error_response


async def _reject_public_result_body(request: Request) -> Optional[JSONResponse]:
    if await request.body():
        return _error_response(
            422,
            "request_validation_failed",
            chinese_message_for("request_validation_failed"),
        )
    return None


def _parse_public_result_query(
    request: Request,
    *,
    allowed: frozenset[str],
    required: frozenset[str] = frozenset(),
) -> Union[dict[str, str], JSONResponse]:
    values: dict[str, str] = {}
    for key, raw_value in request.query_params.multi_items():
        if key not in allowed or key in values:
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        value = str(raw_value or "").strip()
        if not value:
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        values[key] = value
    if not required.issubset(values):
        return _error_response(
            422,
            "request_validation_failed",
            chinese_message_for("request_validation_failed"),
        )
    return values


def _canonical_public_result_value(
    value: Any, *, field_name: str
) -> Union[str, JSONResponse]:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        return _error_response(
            422,
            "request_validation_failed",
            chinese_message_for("request_validation_failed"),
        )
    return value


def _parse_public_result_date(value: str) -> Union[date, JSONResponse]:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return _error_response(
            422,
            "request_validation_failed",
            chinese_message_for("request_validation_failed"),
        )
    if parsed.isoformat() != value:
        return _error_response(
            422,
            "request_validation_failed",
            chinese_message_for("request_validation_failed"),
        )
    return parsed


def _comparison_range_text(
    mode: str,
    execution_basis: str,
    baseline: Optional[rs.PublishedBaseline],
) -> str:
    if baseline is not None:
        return f"{baseline.scope_description}（数据截止 {baseline.data_cutoff}）"
    if mode == rs.MODE_POST_LOCK_PRE_CFDI:
        return "当前固定总量完整数据（不使用比较基线）"
    if execution_basis == rs.BASIS_INCREMENTAL:
        return "同项目已发布数据基线"
    return "当前完整数据（不使用比较基线）"


__all__ = [
    "_reject_public_result_body",
    "_parse_public_result_query",
    "_canonical_public_result_value",
    "_parse_public_result_date",
    "_comparison_range_text",
]
