"""Isolated monitoring harness: raw-API multimodal (text+image) transport.

Harness-only adapter.  It reuses the shared
:class:`services.api.app.ai_gateway.OpenAICompatibleAiProvider` configuration,
response parsing, actual-model verification, diagnostics and retry budget
without modifying the shared gateway.  Nothing here is wired into any product
factory or tool loop; the main thread owns that integration decision.

Wire format: OpenAI chat-completions ``content`` blocks
(``text`` + ``image_url`` data URLs carrying the original image bytes in the
actual POST body).  Image bytes only ever enter the outbound POST; they never
appear in ``repr``, logs, diagnostics, or exception payloads.

Strict response-shape mode (opt-in, default off): set
``provider.strict_response_shape = True`` (or pass
``strict_response_shape=True`` to the constructor) or send an envelope whose
``prompt_version`` exactly equals
``MONITORING_VISUAL_STRICT_PROMPT_VERSION``.  The strict path reuses the same
POST / retry / actual-model-identity contract and accepts only one complete
JSON object — bare or fully fenced.  A truncated outer object never yields an
inner dict.  Complete structures with an unexpected schema are still returned
for upstream validation.  When the model output is not a complete object the
run returns the raw string for upstream repair and records bounded,
secret-free diagnostics (bounded raw preview, sha256, lengths,
``finish_reason`` list) on ``provider.strict_response_diagnostics`` (also
merged into ``provider.response_diagnostics``) for attempt persistence.
Lenient (default) behavior is unchanged.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import json
import random
import re
import time
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.request import Request, urlopen

from . import ai_gateway as _gateway
from .ai_gateway import (
    AI_PROVIDER_MAX_ATTEMPTS,
    AI_PROVIDER_RETRYABLE_HTTP_CODES,
    AiGatewayConfigurationError,
    AiPromptEnvelope,
    AiProviderRuntimeError,
    AiTaskType,
    OpenAICompatibleAiProvider,
)

__all__ = [
    "MONITORING_VISUAL_MAX_IMAGES",
    "MONITORING_VISUAL_MAX_IMAGE_BYTES",
    "MONITORING_VISUAL_MAX_TOTAL_IMAGE_BYTES",
    "MONITORING_VISUAL_SUPPORTED_MEDIA_TYPES",
    "MonitoringVisualImage",
    "MonitoringVisualPromptEnvelope",
    "MonitoringVisualValidationError",
    "MONITORING_VISUAL_STRICT_PROMPT_VERSION",
    "MONITORING_VISUAL_STRICT_RAW_MAX_CHARS",
    "MonitoringVisualOpenAIProvider",
    "MonitoringVisualStrictContentError",
    "build_monitoring_visual_envelope",
    "is_monitoring_visual_strict_envelope",
    "parse_monitoring_visual_strict_content",
    "build_monitoring_visual_user_content",
    "monitoring_visual_envelope_summary",
]

#: Hard caps.  Exceeding any of them raises instead of silently truncating.
MONITORING_VISUAL_MAX_IMAGES = 4
MONITORING_VISUAL_MAX_IMAGE_BYTES = 4 * 1024 * 1024
MONITORING_VISUAL_MAX_TOTAL_IMAGE_BYTES = 8 * 1024 * 1024

#: Media types a real OpenAI-compatible vision endpoint accepts.  Word EMF
#: (``image/emf`` / ``image/x-emf`` / WMF variants) is explicitly unsupported:
#: it is rejected with a dedicated error, never forged into another format.
MONITORING_VISUAL_SUPPORTED_MEDIA_TYPES = frozenset(
    {"image/png", "image/jpeg", "image/webp"}
)
_MONITORING_VISUAL_EMF_MEDIA_TYPES = frozenset(
    {
        "image/emf",
        "image/x-emf",
        "image/x-ms-emf",
        "image/wmf",
        "image/x-wmf",
        "application/emf",
        "application/x-msmetafile",
    }
)

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"
_EMF_MAGIC = b"\x01\x00\x00\x00"
_WMF_MAGIC = b"\xd7\xcd\xc6\x9a"


class MonitoringVisualValidationError(ValueError):
    """Fail-closed envelope validation failure (budget/digest/format)."""


def _normalize_media_type(media_type: str) -> str:
    normalized = (media_type or "").strip().lower()
    if normalized == "image/jpg":
        return "image/jpeg"
    return normalized


def _sniff_media_type(data: bytes) -> Optional[str]:
    """Best-effort magic-byte sniff; ``None`` when unrecognized."""
    if data.startswith(_PNG_MAGIC):
        return "image/png"
    if data.startswith(_JPEG_MAGIC):
        return "image/jpeg"
    if (
        len(data) >= 12
        and data[0:4] == b"RIFF"
        and data[8:12] == b"WEBP"
    ):
        return "image/webp"
    return None


def _is_emf_or_wmf_bytes(data: bytes) -> bool:
    return data.startswith(_EMF_MAGIC) or data.startswith(_WMF_MAGIC)


#: Opt-in strict response-shape prompt version.  An envelope whose
#: ``prompt_version`` exactly equals this value takes the strict response path
#: even when the provider flag is off.  The main thread owns the wiring.
MONITORING_VISUAL_STRICT_PROMPT_VERSION = "monitoring_visual_strict_v1"

#: Bound on model-output raw text retained in strict diagnostics.  The full
#: hash and lengths are always recorded; only the preview is truncated.
MONITORING_VISUAL_STRICT_RAW_MAX_CHARS = 8000


class MonitoringVisualStrictContentError(ValueError):
    """Strict-shape parse failure; never raised for schema mismatches.

    ``code`` is one of ``empty`` / ``truncated_fence`` / ``invalid_json`` /
    ``non_object``.  ``raw_content`` is the exact model-output string so the
    caller can hand it upstream for repair.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str,
        fenced: bool = False,
        raw_content: str = "",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.fenced = fenced
        self.raw_content = raw_content


def parse_monitoring_visual_strict_content(
    content: Any,
) -> Tuple[Dict[str, Any], bool]:
    """Strictly parse one complete JSON object (bare or fully fenced).

    Returns ``(parsed, fenced)``.  A complete structure with an unexpected
    schema is still returned — schema validation stays upstream.  Anything
    else raises :class:`MonitoringVisualStrictContentError`; in particular a
    truncated outer object never yields an inner dict, and prose wrapped
    around a fence is rejected rather than salvaged.
    """
    if not isinstance(content, str):
        raise MonitoringVisualStrictContentError(
            "strict response content must be a string",
            code="invalid_json",
            raw_content="",
        )
    text = content.strip()
    if not text:
        raise MonitoringVisualStrictContentError(
            "strict response content is empty",
            code="empty",
            raw_content=content,
        )
    fenced_match = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE
    )
    if text.startswith("```") and fenced_match is None:
        raise MonitoringVisualStrictContentError(
            "strict response fenced block is truncated",
            code="truncated_fence",
            raw_content=content,
        )
    if fenced_match is not None:
        inner = fenced_match.group(1).strip()
        try:
            parsed = json.loads(inner)
        except json.JSONDecodeError as exc:
            raise MonitoringVisualStrictContentError(
                "strict response fenced block is not a complete JSON object",
                code="invalid_json",
                fenced=True,
                raw_content=content,
            ) from exc
        if not isinstance(parsed, dict):
            raise MonitoringVisualStrictContentError(
                "strict response fenced block must decode to a JSON object",
                code="non_object",
                fenced=True,
                raw_content=content,
            )
        return parsed, True
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MonitoringVisualStrictContentError(
            "strict response is not a complete JSON object",
            code="invalid_json",
            raw_content=content,
        ) from exc
    if not isinstance(parsed, dict):
        raise MonitoringVisualStrictContentError(
            "strict response must decode to a JSON object",
            code="non_object",
            raw_content=content,
        )
    return parsed, False


def is_monitoring_visual_strict_envelope(envelope: Any) -> bool:
    """True when the envelope opts into strict shape via exact prompt version."""
    return (
        getattr(envelope, "prompt_version", "")
        == MONITORING_VISUAL_STRICT_PROMPT_VERSION
    )


def _monitoring_visual_strict_diagnostics(
    *,
    content: Any,
    parse_status: str,
    fenced: bool,
    finish_reasons: List[str],
    failure_code: str = "",
) -> Dict[str, Any]:
    """Bounded, secret-free strict diagnostics for attempt persistence.

    Records the bounded raw preview plus full hash/lengths and the response
    ``finish_reason`` list.  Never includes API keys, request images, or
    headers — the preview is model-output text only.
    """
    text = content if isinstance(content, str) else ""
    encoded = text.encode("utf-8")
    diagnostics: Dict[str, Any] = {
        "strict_response_shape": True,
        "strict_parse_status": parse_status,
        "strict_fenced": bool(fenced),
        "strict_raw_chars": len(text),
        "strict_raw_bytes": len(encoded),
        "strict_raw_sha256": hashlib.sha256(encoded).hexdigest(),
        "strict_raw_preview": text[:MONITORING_VISUAL_STRICT_RAW_MAX_CHARS],
        "strict_raw_truncated": len(text) > MONITORING_VISUAL_STRICT_RAW_MAX_CHARS,
        "strict_finish_reasons": list(finish_reasons or []),
    }
    if failure_code:
        diagnostics["strict_failure_code"] = failure_code
    return diagnostics


@dataclass(frozen=True)
class MonitoringVisualImage:
    """One typed, frozen harness image.  Bytes never enter ``repr``."""

    data: bytes = field(repr=False)
    media_type: str = ""
    sha256: str = ""
    locator: str = ""

    def __post_init__(self) -> None:
        media_type = _normalize_media_type(self.media_type)
        object.__setattr__(self, "media_type", media_type)
        if not isinstance(self.data, (bytes, bytearray)) or not self.data:
            raise MonitoringVisualValidationError("visual_image_empty")
        data = bytes(self.data)
        object.__setattr__(self, "data", data)
        if not self.locator or not self.locator.strip():
            raise MonitoringVisualValidationError("visual_image_locator_required")
        expected_digest = hashlib.sha256(data).hexdigest()
        if self.sha256.strip().lower() != expected_digest:
            raise MonitoringVisualValidationError("visual_image_digest_mismatch")
        if media_type in _MONITORING_VISUAL_EMF_MEDIA_TYPES:
            raise MonitoringVisualValidationError(
                "visual_image_emf_unsupported: Word EMF/WMF metafiles are not "
                "accepted by vision endpoints and are never converted; supply "
                "a rendered png/jpeg/webp instead"
            )
        if _is_emf_or_wmf_bytes(data):
            raise MonitoringVisualValidationError(
                "visual_image_emf_unsupported: payload magic indicates EMF/WMF; "
                "Word metafiles are unsupported, supply png/jpeg/webp"
            )
        if media_type not in MONITORING_VISUAL_SUPPORTED_MEDIA_TYPES:
            raise MonitoringVisualValidationError(
                f"visual_image_media_type_unsupported: {media_type or 'missing'}"
            )
        sniffed = _sniff_media_type(data)
        if sniffed is None:
            raise MonitoringVisualValidationError(
                "visual_image_magic_unrecognized: bytes do not match png/jpeg/webp"
            )
        if sniffed != media_type:
            raise MonitoringVisualValidationError(
                f"visual_image_magic_mismatch: declared={media_type} sniffed={sniffed}"
            )
        if len(data) > MONITORING_VISUAL_MAX_IMAGE_BYTES:
            raise MonitoringVisualValidationError("visual_image_byte_budget_exceeded")

    def __repr__(self) -> str:  # bytes-free by construction
        return (
            "MonitoringVisualImage("
            f"media_type={self.media_type!r}, "
            f"bytes={len(self.data)}, "
            f"sha256={self.sha256!r}, "
            f"locator={self.locator!r})"
        )

    @property
    def data_url(self) -> str:
        """Original bytes as an ``image_url`` data URL (POST body only)."""
        encoded = base64.b64encode(self.data).decode("ascii")
        return f"data:{self.media_type};base64,{encoded}"


@dataclass(frozen=True)
class MonitoringVisualPromptEnvelope(AiPromptEnvelope):
    """Text envelope plus typed frozen images; bytes never enter ``repr``."""

    images: Tuple[MonitoringVisualImage, ...] = ()

    def __post_init__(self) -> None:
        images = tuple(self.images or ())
        object.__setattr__(self, "images", images)
        if not images:
            raise MonitoringVisualValidationError("visual_envelope_images_required")
        for image in images:
            if not isinstance(image, MonitoringVisualImage):
                raise MonitoringVisualValidationError("visual_envelope_image_typed")
        _check_monitoring_visual_budget(images)

    def __repr__(self) -> str:  # metadata only, no bytes, no base64
        return (
            "MonitoringVisualPromptEnvelope("
            f"task_id={self.task_id!r}, "
            f"task_type={self.task_type.value!r}, "
            f"prompt_version={self.prompt_version!r}, "
            f"images={monitoring_visual_envelope_summary(self)!r})"
        )


def _check_monitoring_visual_budget(
    images: Tuple[MonitoringVisualImage, ...],
) -> int:
    if len(images) > MONITORING_VISUAL_MAX_IMAGES:
        raise MonitoringVisualValidationError(
            f"visual_image_count_budget_exceeded: {len(images)} > "
            f"{MONITORING_VISUAL_MAX_IMAGES}"
        )
    total = sum(len(image.data) for image in images)
    if total > MONITORING_VISUAL_MAX_TOTAL_IMAGE_BYTES:
        raise MonitoringVisualValidationError(
            f"visual_image_total_byte_budget_exceeded: {total} > "
            f"{MONITORING_VISUAL_MAX_TOTAL_IMAGE_BYTES}"
        )
    return total


def monitoring_visual_envelope_summary(
    envelope: MonitoringVisualPromptEnvelope,
) -> Dict[str, Any]:
    """Safe log/telemetry summary: hashes and sizes only, never bytes."""
    return {
        "image_count": len(envelope.images),
        "total_bytes": sum(len(image.data) for image in envelope.images),
        "images": [
            {
                "media_type": image.media_type,
                "bytes": len(image.data),
                "sha256": image.sha256,
                "locator": image.locator,
            }
            for image in envelope.images
        ],
    }


def build_monitoring_visual_envelope(
    *,
    task_id: str,
    task_type: AiTaskType,
    prompt_version: str,
    system_prompt: str,
    payload: Dict[str, Any],
    images: List[MonitoringVisualImage],
    thinking: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
) -> MonitoringVisualPromptEnvelope:
    """Validate budgets/digests/formats and build the visual envelope.

    Raises :class:`MonitoringVisualValidationError` instead of truncating.
    """
    return MonitoringVisualPromptEnvelope(
        task_id=task_id,
        task_type=task_type,
        prompt_version=prompt_version,
        system_prompt=system_prompt,
        payload=dict(payload),
        thinking=thinking,
        reasoning_effort=reasoning_effort,
        max_output_tokens=max_output_tokens,
        images=tuple(images or ()),
    )


def build_monitoring_visual_user_content(
    envelope: MonitoringVisualPromptEnvelope,
) -> List[Dict[str, Any]]:
    """Text JSON protocol block plus one ``image_url`` block per image.

    The text block is byte-identical to the plain-text transport's user
    message (``json.dumps(payload, ensure_ascii=False)``); thinking /
    reasoning / output-JSON protocol handling is unchanged.
    """
    blocks: List[Dict[str, Any]] = [
        {
            "type": "text",
            "text": json.dumps(envelope.payload, ensure_ascii=False),
        }
    ]
    for image in envelope.images:
        blocks.append(
            {
                "type": "image_url",
                "image_url": {"url": image.data_url},
            }
        )
    return blocks


class MonitoringVisualOpenAIProvider(OpenAICompatibleAiProvider):
    """Monitoring-only OpenAI-compatible transport with vision support.

    Plain :class:`AiPromptEnvelope` inputs delegate entirely to the shared
    gateway ``run``; only :class:`MonitoringVisualPromptEnvelope` takes the
    multimodal content-block path below.  No global ``urllib`` state is
    touched: this module binds its own ``urlopen``/``Request`` names so tests
    can patch this module alone.

    Strict mode is opt-in only (default off); lenient behavior is unchanged
    unless :meth:`_strict_response_enabled` fires.  Main-thread API:
    ``strict_response_shape`` flag (constructor kwarg or plain attribute),
    exact-``prompt_version`` envelope opt-in, ``run`` returning ``dict`` for a
    complete object or the raw ``str`` for upstream repair, and
    ``strict_response_diagnostics`` for attempt persistence.
    """

    #: Opt-in strict response-shape mode.  Default False: every existing
    #: caller keeps the lenient gateway parse.
    strict_response_shape: bool

    #: Last strict-run diagnostics (bounded preview/hash/lengths/finish
    #: reasons/parse status).  Empty until the first strict run; never
    #: reassigned in lenient mode.
    strict_response_diagnostics: Dict[str, Any]

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        provider_name: str = "openai_compatible",
        timeout_seconds: float = 120.0,
        expected_response_model: str = "",
        max_attempts: Optional[int] = None,
        default_thinking: Optional[str] = None,
        default_reasoning_effort: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        stream_enabled: bool = True,
        total_deadline_seconds: float = 1200.0,
        max_response_bytes: int = 128 * 1024 * 1024,
        *,
        strict_response_shape: bool = False,
    ) -> None:
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
            provider_name=provider_name,
            timeout_seconds=timeout_seconds,
            expected_response_model=expected_response_model,
            max_attempts=max_attempts,
            default_thinking=default_thinking,
            default_reasoning_effort=default_reasoning_effort,
            extra_headers=extra_headers,
            stream_enabled=stream_enabled,
            total_deadline_seconds=total_deadline_seconds,
            max_response_bytes=max_response_bytes,
        )
        self.strict_response_shape = bool(strict_response_shape)
        self.strict_response_diagnostics = {}

    def _strict_response_enabled(self, envelope: AiPromptEnvelope) -> bool:
        if bool(getattr(self, "strict_response_shape", False)):
            return True
        return is_monitoring_visual_strict_envelope(envelope)

    def _build_plain_strict_request_payload(
        self, envelope: AiPromptEnvelope
    ) -> Dict[str, Any]:
        """Gateway-identical text payload for strict plain-envelope runs."""
        request_payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": envelope.system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(envelope.payload, ensure_ascii=False),
                },
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        thinking = self.default_thinking or envelope.thinking
        reasoning_effort = self.default_reasoning_effort or envelope.reasoning_effort
        if thinking in {"enabled", "disabled"}:
            request_payload["thinking"] = {"type": thinking}
        if reasoning_effort:
            request_payload["reasoning_effort"] = reasoning_effort
        if envelope.max_output_tokens is not None:
            request_payload["max_tokens"] = int(envelope.max_output_tokens)
        return request_payload

    def _run_completion(self, *, envelope, request_payload, visual_extra):
        """Shared monitoring POST; strict mode only changes response parsing.

        传输/解析完全复用网关``_post_and_parse``：流式开关、provider特俗头、
        产品UA、绝对deadline、字节上限、SSE终态合同与模型身份校验一次实现，
        视觉路径不再维护第二套发送逻辑。
        """
        if self.stream_enabled:
            request_payload = {**request_payload, "stream": True}
        request = self._build_request(request_payload)
        parsed, content = self._post_and_parse(request, extra_diagnostics=visual_extra)
        if self._strict_response_enabled(envelope):
            return self._parse_strict_response(content)
        return parsed

    def _parse_strict_response(self, content):
        finish_reasons = list(self.response_diagnostics.get("finish_reasons") or [])
        try:
            parsed, fenced = parse_monitoring_visual_strict_content(content)
        except MonitoringVisualStrictContentError as exc:
            strict_diagnostics = _monitoring_visual_strict_diagnostics(
                content=content,
                parse_status=exc.code,
                fenced=exc.fenced,
                finish_reasons=finish_reasons,
                failure_code=f"strict_response_{exc.code}",
            )
            self.strict_response_diagnostics = strict_diagnostics
            self.response_diagnostics = {
                **self.response_diagnostics,
                **strict_diagnostics,
            }
            return content
        strict_diagnostics = _monitoring_visual_strict_diagnostics(
            content=content,
            parse_status="ok_fenced" if fenced else "ok",
            fenced=fenced,
            finish_reasons=finish_reasons,
        )
        self.strict_response_diagnostics = strict_diagnostics
        self.response_diagnostics = {
            **self.response_diagnostics,
            **strict_diagnostics,
        }
        return parsed

    def build_request_payload(
        self, envelope: MonitoringVisualPromptEnvelope
    ) -> Dict[str, Any]:
        request_payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": envelope.system_prompt},
                {
                    "role": "user",
                    "content": build_monitoring_visual_user_content(envelope),
                },
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        thinking = self.default_thinking or envelope.thinking
        reasoning_effort = self.default_reasoning_effort or envelope.reasoning_effort
        if thinking in {"enabled", "disabled"}:
            request_payload["thinking"] = {"type": thinking}
        if reasoning_effort:
            request_payload["reasoning_effort"] = reasoning_effort
        if envelope.max_output_tokens is not None:
            request_payload["max_tokens"] = int(envelope.max_output_tokens)
        return request_payload

    def _visual_diagnostics_extra(
        self, envelope: MonitoringVisualPromptEnvelope
    ) -> Dict[str, Any]:
        return {
            "visual_image_count": len(envelope.images),
            "visual_total_bytes": sum(len(image.data) for image in envelope.images),
            "visual_image_sha256": [image.sha256 for image in envelope.images],
            "visual_media_types": [image.media_type for image in envelope.images],
        }

    def run_visual(self, envelope: MonitoringVisualPromptEnvelope) -> Union[Dict[str, Any], str]:
        total = _check_monitoring_visual_budget(envelope.images)
        if total <= 0:
            raise MonitoringVisualValidationError("visual_image_empty")
        return self._run_completion(
            envelope=envelope, request_payload=self.build_request_payload(envelope),
            visual_extra=self._visual_diagnostics_extra(envelope),
        )

    def run(self, envelope: AiPromptEnvelope) -> Union[Dict[str, Any], str]:  # type: ignore[override]
        if self._strict_response_enabled(envelope):
            if isinstance(envelope, MonitoringVisualPromptEnvelope):
                return self.run_visual(envelope)
            return self._run_completion(
                envelope=envelope,
                request_payload=self._build_plain_strict_request_payload(envelope),
                visual_extra={},
            )
        if not isinstance(envelope, MonitoringVisualPromptEnvelope):
            return super().run(envelope)
        return self.run_visual(envelope)


def provider_from_shared_config(
    *,
    base_url: str,
    api_key: str,
    model_name: str,
    provider_name: str = "openai_compatible",
    timeout_seconds: float = 120.0,
    expected_response_model: str = "",
    max_attempts: Optional[int] = None,
    default_thinking: Optional[str] = None,
    default_reasoning_effort: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    stream_enabled: bool = True,
    total_deadline_seconds: float = 1200.0,
    max_response_bytes: int = 128 * 1024 * 1024,
) -> MonitoringVisualOpenAIProvider:
    """Build the harness provider from existing gateway config values.

    Main-thread integration point: pass the already-resolved
    ``OpenAICompatibleAiProvider`` constructor arguments through unchanged.
    """
    if max_attempts is None:
        max_attempts = AI_PROVIDER_MAX_ATTEMPTS
    try:
        return MonitoringVisualOpenAIProvider(
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
            provider_name=provider_name,
            timeout_seconds=timeout_seconds,
            expected_response_model=expected_response_model,
            max_attempts=max_attempts,
            default_thinking=default_thinking,
            default_reasoning_effort=default_reasoning_effort,
            extra_headers=extra_headers,
            stream_enabled=stream_enabled,
            total_deadline_seconds=total_deadline_seconds,
            max_response_bytes=max_response_bytes,
        )
    except AiGatewayConfigurationError:
        raise
