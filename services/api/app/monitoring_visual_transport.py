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
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import json
import random
import time
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
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
    "MonitoringVisualOpenAIProvider",
    "build_monitoring_visual_envelope",
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
    """

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

    def run_visual(
        self, envelope: MonitoringVisualPromptEnvelope
    ) -> Dict[str, Any]:
        total = _check_monitoring_visual_budget(envelope.images)
        if total <= 0:
            raise MonitoringVisualValidationError("visual_image_empty")
        request_payload = self.build_request_payload(envelope)
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(request_payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        response_body = ""
        response_status: Optional[int] = None
        response_content_type = ""
        for attempt in range(self.max_attempts):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    response_status = _gateway._response_status(response)
                    response_content_type = _gateway._response_content_type(response)
                    response_body = response.read().decode("utf-8")
                break
            except urllib.error.HTTPError as exc:
                if (
                    exc.code not in AI_PROVIDER_RETRYABLE_HTTP_CODES
                    or attempt == self.max_attempts - 1
                ):
                    suffix = (
                        " after bounded retries"
                        if exc.code in AI_PROVIDER_RETRYABLE_HTTP_CODES
                        and attempt > 0
                        else ""
                    )
                    raise AiProviderRuntimeError(
                        f"AI provider request failed{suffix}: HTTP {exc.code}",
                        diagnostics={
                            "failure_code": "provider_http_error",
                            "http_status": int(exc.code),
                            **self._visual_diagnostics_extra(envelope),
                        },
                    ) from exc
            except (
                urllib.error.URLError,
                http.client.IncompleteRead,
                http.client.RemoteDisconnected,
                ConnectionResetError,
                TimeoutError,
            ) as exc:
                if attempt == self.max_attempts - 1:
                    prefix = (
                        "AI provider request failed after bounded retries"
                        if attempt > 0
                        else "AI provider request failed"
                    )
                    raise AiProviderRuntimeError(
                        f"{prefix}: {type(exc).__name__}",
                        diagnostics={
                            "failure_code": "provider_transport_error",
                            "exception_type": type(exc).__name__,
                            **self._visual_diagnostics_extra(envelope),
                        },
                    ) from exc
            backoff_seconds = (0.5 * (2**attempt)) + random.uniform(0.0, 0.25)
            time.sleep(backoff_seconds)
        # Same model-identity verification contract as the shared gateway.
        verified_response_model = _gateway._completion_response_model(response_body)
        self.response_diagnostics = {
            **_gateway._completion_response_diagnostics(
                response_body,
                http_status=response_status,
                content_type=response_content_type,
            ),
            **self._visual_diagnostics_extra(envelope),
        }
        self.response_model = verified_response_model
        if self.expected_response_model and not verified_response_model:
            raise AiProviderRuntimeError(
                "AI provider response did not include the configured model name",
                diagnostics={
                    **self.response_diagnostics,
                    "failure_code": "provider_response_model_missing",
                },
            )
        if (
            self.expected_response_model
            and verified_response_model != self.expected_response_model
        ):
            raise AiProviderRuntimeError(
                "AI provider response model identity does not match the configured model "
                f"(actual={verified_response_model or 'missing'}, "
                f"expected={self.expected_response_model})",
                diagnostics={
                    **self.response_diagnostics,
                    "failure_code": "provider_response_model_mismatch",
                },
            )
        try:
            content = _gateway._chat_completion_content(response_body)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as exc:
            failure_code = (
                "provider_response_empty"
                if "empty" in str(exc).lower() or "no content" in str(exc).lower()
                else "provider_response_invalid"
            )
            raise AiProviderRuntimeError(
                "AI provider response is not valid JSON completion or SSE stream "
                f"({failure_code})",
                diagnostics={
                    **self.response_diagnostics,
                    "failure_code": failure_code,
                },
            ) from exc
        try:
            parsed = _gateway._parse_json_content(content)
        except AiProviderRuntimeError as exc:
            raise AiProviderRuntimeError(
                str(exc),
                diagnostics={
                    **self.response_diagnostics,
                    "failure_code": "provider_response_invalid_json",
                },
            ) from exc
        return parsed

    def run(self, envelope: AiPromptEnvelope) -> Dict[str, Any]:  # type: ignore[override]
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
        )
    except AiGatewayConfigurationError:
        raise
