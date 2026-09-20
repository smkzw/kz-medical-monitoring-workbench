"""Focused tests for the isolated monitoring visual transport harness.

All HTTP is faked by patching the shared gateway's ``urlopen`` binding
(``services.api.app.ai_gateway.urllib.request.urlopen``): since the strict
transport unification, the visual provider delegates POST/retry/read/parse
entirely to the shared gateway pipeline.  No real API calls, no network,
no model calls.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.api.app import monitoring_visual_transport as visual_transport  # noqa: E402
from services.api.app.ai_gateway import (  # noqa: E402
    AiPromptEnvelope,
    AiProviderRuntimeError,
    AiTaskType,
)
from services.api.app.monitoring_visual_transport import (  # noqa: E402
    MonitoringVisualImage,
    MonitoringVisualOpenAIProvider,
    MonitoringVisualPromptEnvelope,
    MonitoringVisualValidationError,
    build_monitoring_visual_envelope,
)


def _png_bytes(seed: bytes = b"harness-png") -> bytes:
    return b"\x89PNG\r\n\x1a\n" + seed + bytes(64)


def _jpeg_bytes(seed: bytes = b"harness-jpeg") -> bytes:
    return b"\xff\xd8\xff\xe0" + seed + bytes(64)


def _webp_bytes(seed: bytes = b"harness-webp") -> bytes:
    return b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + seed + bytes(64)


def _make_image(
    data: bytes | None = None,
    *,
    media_type: str = "image/png",
    locator: str = "harness:page:1",
) -> MonitoringVisualImage:
    payload = _png_bytes() if data is None else data
    return MonitoringVisualImage(
        data=payload,
        media_type=media_type,
        sha256=hashlib.sha256(payload).hexdigest(),
        locator=locator,
    )


def _make_envelope(
    images: list | None = None,
    *,
    thinking: str | None = None,
    payload: dict | None = None,
) -> MonitoringVisualPromptEnvelope:
    return build_monitoring_visual_envelope(
        task_id="task_visual_001",
        task_type=AiTaskType.MONITORING_RISK_INTERPRETATION,
        prompt_version="monitoring_visual_harness_v0_1",
        system_prompt="Return JSON.",
        payload=(
            payload
            if payload is not None
            else {"task_id": "task_visual_001", "probe": "vision-harness"}
        ),
        images=images if images is not None else [_make_image()],
        thinking=thinking,
    )


def _make_provider(**overrides) -> MonitoringVisualOpenAIProvider:
    options = {
        "base_url": "https://ai.example.test/v1",
        "api_key": "test-key",
        "model_name": "vision-harness-model",
        "timeout_seconds": 1,
    }
    options.update(overrides)
    return MonitoringVisualOpenAIProvider(**options)


def _completion_payload(model: str = "vision-harness-model") -> dict:
    return {
        "model": model,
        "choices": [{"message": {"content": json.dumps({"passed": True})}}],
    }


class _FakeResponse:
    def __init__(self, payload: dict, status: int = 200):
        self.payload = payload
        self.status = status
        self.headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __iter__(self):
        # 共享网关流式读取路径按行迭代响应。
        yield self.read()


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://ai.example.test/v1/chat/completions",
        code,
        f"HTTP {code}",
        {},
        None,
    )


class MonitoringVisualTransportTests(unittest.TestCase):
    def test_post_sends_original_image_bytes_as_content_blocks(self):
        image = _make_image(_png_bytes(b"original-bytes"))
        envelope = _make_envelope(images=[image])
        provider = _make_provider()

        with patch(
            "services.api.app.ai_gateway.urllib.request.urlopen",
            return_value=_FakeResponse(_completion_payload()),
        ) as urlopen:
            result = provider.run(envelope)

        self.assertEqual({"passed": True}, result)
        request = urlopen.call_args.args[0]
        self.assertEqual(
            "https://ai.example.test/v1/chat/completions", request.full_url
        )
        self.assertEqual("Bearer test-key", request.headers["Authorization"])
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual("vision-harness-model", body["model"])
        self.assertEqual({"type": "json_object"}, body["response_format"])
        self.assertEqual(0, body["temperature"])
        self.assertEqual("Return JSON.", body["messages"][0]["content"])
        content = body["messages"][1]["content"]
        self.assertIsInstance(content, list)
        self.assertEqual("text", content[0]["type"])
        self.assertEqual(
            json.dumps(envelope.payload, ensure_ascii=False), content[0]["text"]
        )
        self.assertEqual("image_url", content[1]["type"])
        data_url = content[1]["image_url"]["url"]
        self.assertTrue(data_url.startswith("data:image/png;base64,"))
        decoded = base64.b64decode(data_url.split(",", 1)[1])
        self.assertEqual(image.data, decoded)

    def test_text_protocol_and_thinking_params_unchanged(self):
        envelope = _make_envelope(
            images=[_make_image(_jpeg_bytes(), media_type="image/jpeg")],
            thinking="disabled",
            payload={"task_id": "task_visual_001"},
        )
        provider = _make_provider(default_reasoning_effort="xhigh")

        with patch(
            "services.api.app.ai_gateway.urllib.request.urlopen",
            return_value=_FakeResponse(_completion_payload()),
        ):
            provider.run(envelope)
            request = (
                __import__("services.api.app.ai_gateway", fromlist=["urllib"])
                .urllib.request.urlopen.call_args.args[0]
            )

        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual({"type": "disabled"}, body["thinking"])
        self.assertEqual("xhigh", body["reasoning_effort"])

    def test_model_identity_mismatch_matches_gateway_contract(self):
        provider = _make_provider(expected_response_model="vision-expected")
        envelope = _make_envelope()

        with patch(
            "services.api.app.ai_gateway.urllib.request.urlopen",
            return_value=_FakeResponse(_completion_payload(model="vision-other")),
        ):
            with self.assertRaisesRegex(
                AiProviderRuntimeError, "does not match"
            ) as raised:
                provider.run(envelope)
        self.assertEqual("vision-other", provider.response_model)
        # Same contract as the shared gateway: the failure_code travels on the
        # exception diagnostics, not on the persisted response_diagnostics.
        self.assertEqual(
            "provider_response_model_mismatch",
            raised.exception.diagnostics["failure_code"],
        )

    def test_missing_response_model_matches_gateway_contract(self):
        provider = _make_provider(expected_response_model="vision-expected")
        envelope = _make_envelope()

        with patch(
            "services.api.app.ai_gateway.urllib.request.urlopen",
            return_value=_FakeResponse(
                {"choices": [{"message": {"content": '{"ok":true}'}}]}
            ),
        ):
            with self.assertRaisesRegex(
                AiProviderRuntimeError, "did not include"
            ) as raised:
                provider.run(envelope)
        self.assertEqual(
            "provider_response_model_missing",
            raised.exception.diagnostics["failure_code"],
        )

    def test_http_error_surfaces_without_leaking_image_or_key(self):
        provider = _make_provider()
        envelope = _make_envelope()

        with patch(
            "services.api.app.ai_gateway.urllib.request.urlopen",
            side_effect=_http_error(400),
        ) as urlopen:
            with self.assertRaisesRegex(AiProviderRuntimeError, "HTTP 400"):
                provider.run(envelope)

        self.assertEqual(1, urlopen.call_count)
        image_b64 = base64.b64encode(envelope.images[0].data).decode("ascii")
        for value in provider.response_diagnostics.values():
            self.assertNotIn(image_b64, json.dumps(value, ensure_ascii=False))
        self.assertNotIn("test-key", json.dumps(provider.response_diagnostics))

    def test_retryable_http_error_retries_within_shared_budget(self):
        provider = _make_provider()
        envelope = _make_envelope()

        with (
            patch(
                "services.api.app.ai_gateway.urllib.request.urlopen",
                side_effect=[
                    _http_error(500),
                    _FakeResponse(_completion_payload()),
                ],
            ) as urlopen,
            patch("services.api.app.ai_gateway.time.sleep") as sleep,
            patch(
                "services.api.app.ai_gateway.random.uniform", return_value=0.0
            ),
        ):
            result = provider.run(envelope)

        self.assertEqual({"passed": True}, result)
        self.assertEqual(2, urlopen.call_count)
        sleep.assert_called_once_with(0.5)

    def test_image_count_budget_raises_without_http(self):
        images = [
            _make_image(_png_bytes(bytes([index])), locator=f"harness:page:{index}")
            for index in range(visual_transport.MONITORING_VISUAL_MAX_IMAGES + 1)
        ]
        with self.assertRaisesRegex(
            MonitoringVisualValidationError, "count_budget_exceeded"
        ):
            build_monitoring_visual_envelope(
                task_id="task_visual_001",
                task_type=AiTaskType.MONITORING_RISK_INTERPRETATION,
                prompt_version="monitoring_visual_harness_v0_1",
                system_prompt="Return JSON.",
                payload={},
                images=images,
            )

    def test_total_byte_budget_raises_without_silent_truncation(self):
        big = _png_bytes(b"x") + bytes(128)
        images = [
            _make_image(big, locator="harness:page:1"),
            _make_image(_png_bytes(b"y"), locator="harness:page:2"),
        ]
        with patch.object(
            visual_transport, "MONITORING_VISUAL_MAX_TOTAL_IMAGE_BYTES", 10
        ):
            with self.assertRaisesRegex(
                MonitoringVisualValidationError, "total_byte_budget_exceeded"
            ):
                _make_envelope(images=images)

    def test_digest_mismatch_rejected(self):
        payload = _png_bytes()
        with self.assertRaisesRegex(
            MonitoringVisualValidationError, "digest_mismatch"
        ):
            MonitoringVisualImage(
                data=payload,
                media_type="image/png",
                sha256="0" * 64,
                locator="harness:page:1",
            )

    def test_magic_mismatch_rejected(self):
        payload = _jpeg_bytes()
        with self.assertRaisesRegex(
            MonitoringVisualValidationError, "magic_mismatch"
        ):
            _make_image(payload, media_type="image/png")

    def test_word_emf_explicitly_unsupported_not_forged(self):
        with self.assertRaisesRegex(
            MonitoringVisualValidationError, "emf_unsupported"
        ):
            MonitoringVisualImage(
                data=b"\x01\x00\x00\x00" + bytes(64),
                media_type="image/emf",
                sha256=hashlib.sha256(b"\x01\x00\x00\x00" + bytes(64)).hexdigest(),
                locator="harness:word:ole:1",
            )
        emf_bytes = b"\x01\x00\x00\x00" + bytes(64)
        with self.assertRaisesRegex(
            MonitoringVisualValidationError, "emf_unsupported"
        ):
            MonitoringVisualImage(
                data=emf_bytes,
                media_type="image/png",
                sha256=hashlib.sha256(emf_bytes).hexdigest(),
                locator="harness:word:ole:2",
            )

    def test_bytes_never_enter_repr_log_or_summary(self):
        image = _make_image()
        envelope = _make_envelope(images=[image])
        image_b64 = base64.b64encode(image.data).decode("ascii")
        self.assertNotIn(image_b64, repr(image))
        self.assertNotIn(image_b64, repr(envelope))
        summary = visual_transport.monitoring_visual_envelope_summary(envelope)
        self.assertNotIn(image_b64, json.dumps(summary))
        self.assertEqual(image.sha256, summary["images"][0]["sha256"])

    def test_plain_text_envelope_fully_delegates_to_shared_run(self):
        envelope = AiPromptEnvelope(
            task_id="task_text_001",
            task_type=AiTaskType.PROTOCOL_RULE_EXTRACTION,
            prompt_version="protocol_rule_extraction_v0_1",
            system_prompt="Return JSON.",
            payload={"task_id": "task_text_001"},
        )
        provider = _make_provider()
        sent = {"passed": True}

        with patch(
            "services.api.app.ai_gateway.urllib.request.urlopen",
            return_value=_FakeResponse(
                {"choices": [{"message": {"content": json.dumps(sent)}}]}
            ),
        ) as urlopen:
            result = provider.run(envelope)

        self.assertEqual(sent, result)
        body = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertIsInstance(body["messages"][1]["content"], str)
        self.assertEqual(
            json.dumps(envelope.payload, ensure_ascii=False),
            body["messages"][1]["content"],
        )


if __name__ == "__main__":
    unittest.main()
