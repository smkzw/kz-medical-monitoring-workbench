"""Strict response-shape mode for the monitoring visual transport harness.

Synthetic HTTP stubs only: no real model, network, OCR, or local-model
calls.  Covers truncated outer objects (an inner dict must never masquerade
as the whole output), complete bare/fenced objects, text+image wire format in
strict mode, identity refusal, retry budget, bounded secret-free diagnostics,
and default lenient-mode compatibility.
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
    MONITORING_VISUAL_STRICT_PROMPT_VERSION,
    MONITORING_VISUAL_STRICT_RAW_MAX_CHARS,
    MonitoringVisualImage,
    MonitoringVisualOpenAIProvider,
    MonitoringVisualStrictContentError,
    build_monitoring_visual_envelope,
    is_monitoring_visual_strict_envelope,
    parse_monitoring_visual_strict_content,
)

MODEL = "vision-harness-model"

# Broken outer object containing a complete inner dict: the lenient gateway
# salvage path recovers ``{"passed": True}`` from this; strict mode must
# return the raw string instead.
TRUNCATED_NESTED = (
    '{"task_id": "task_visual_001", "nested": {"passed": true}, "tail": [1, 2'
)
COMPLETE_OBJECT = (
    '{"task_id": "task_visual_001", "passed": true, '
    '"unexpected_future_key": [1, 2, 3]}'
)
FENCED_OBJECT = '```json\n{"task_id": "task_visual_001", "passed": true}\n```'
TRUNCATED_FENCE = '```json\n{"task_id": "task_visual_001", "passed": true}\n'
NON_OBJECT = "[1, 2, 3]"


def _png_bytes(seed: bytes = b"shape-png") -> bytes:
    return b"\x89PNG\r\n\x1a\n" + seed + bytes(64)


def _make_image(
    data: bytes | None = None,
    *,
    locator: str = "harness:page:1",
) -> MonitoringVisualImage:
    payload = _png_bytes() if data is None else data
    return MonitoringVisualImage(
        data=payload,
        media_type="image/png",
        sha256=hashlib.sha256(payload).hexdigest(),
        locator=locator,
    )


def _make_envelope(
    images: list | None = None,
    *,
    prompt_version: str = "monitoring_visual_harness_v0_1",
) -> object:
    return build_monitoring_visual_envelope(
        task_id="task_visual_001",
        task_type=AiTaskType.MONITORING_RISK_INTERPRETATION,
        prompt_version=prompt_version,
        system_prompt="Return JSON.",
        payload={"task_id": "task_visual_001", "probe": "shape-harness"},
        images=images if images is not None else [_make_image()],
    )


def _make_plain_envelope() -> AiPromptEnvelope:
    return AiPromptEnvelope(
        task_id="task_text_001",
        task_type=AiTaskType.PROTOCOL_RULE_EXTRACTION,
        prompt_version="protocol_rule_extraction_v0_1",
        system_prompt="Return JSON.",
        payload={"task_id": "task_text_001"},
    )


def _make_provider(**overrides) -> MonitoringVisualOpenAIProvider:
    options = {
        "base_url": "https://ai.example.test/v1",
        "api_key": "test-key",
        "model_name": MODEL,
        "timeout_seconds": 1,
    }
    options.update(overrides)
    return MonitoringVisualOpenAIProvider(**options)


def _completion_payload(
    content: str,
    *,
    model: str = MODEL,
    finish_reason: str = "stop",
) -> dict:
    return {
        "model": model,
        "choices": [{"message": {"content": content}, "finish_reason": finish_reason}],
    }


class _FakeShapeResponse:
    def __init__(self, payload: dict, status: int = 200):
        self.payload = payload
        self.status = status
        self.headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def __iter__(self):
        yield self.read()

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://ai.example.test/v1/chat/completions",
        code,
        f"HTTP {code}",
        {},
        None,
    )


def _run_strict(provider, envelope, payload, **patches):
    # WP0A传输统一后，provider经共享网关_post_and_parse发请求：
    # patch目标是ai_gateway的urlopen，不再是visual_transport模块绑定。
    with patch(
        "services.api.app.ai_gateway.urllib.request.urlopen",
        return_value=_FakeShapeResponse(payload),
    ) as urlopen:
        result = provider.run(envelope)
    return result, urlopen


class MonitoringStrictResponseShapeTests(unittest.TestCase):
    def test_truncated_outer_returns_raw_not_inner_dict(self):
        provider = _make_provider(strict_response_shape=True)
        envelope = _make_envelope()
        payload = _completion_payload(TRUNCATED_NESTED, finish_reason="length")

        result, _ = _run_strict(provider, envelope, payload)

        # Fidelity core: the inner fragment must not masquerade as the output.
        self.assertIsInstance(result, str)
        self.assertEqual(TRUNCATED_NESTED, result)
        diag = provider.strict_response_diagnostics
        self.assertEqual("invalid_json", diag["strict_parse_status"])
        self.assertEqual("strict_response_invalid_json", diag["strict_failure_code"])
        self.assertEqual(len(TRUNCATED_NESTED), diag["strict_raw_chars"])
        self.assertEqual(
            hashlib.sha256(TRUNCATED_NESTED.encode("utf-8")).hexdigest(),
            diag["strict_raw_sha256"],
        )
        self.assertEqual(["length"], diag["strict_finish_reasons"])
        self.assertEqual(MODEL, provider.response_model)

    def test_lenient_default_still_salvages_inner_dict(self):
        provider = _make_provider()
        self.assertFalse(provider.strict_response_shape)
        envelope = _make_envelope()
        payload = _completion_payload(TRUNCATED_NESTED, finish_reason="length")

        result, _ = _run_strict(provider, envelope, payload)

        # Old behavior pinned: lenient mode keeps the gateway salvage path.
        self.assertEqual({"passed": True}, result)
        self.assertEqual({}, provider.strict_response_diagnostics)

    def test_envelope_version_opt_in_without_provider_flag(self):
        provider = _make_provider()
        envelope = _make_envelope(
            prompt_version=MONITORING_VISUAL_STRICT_PROMPT_VERSION
        )
        self.assertTrue(is_monitoring_visual_strict_envelope(envelope))
        payload = _completion_payload(TRUNCATED_NESTED)

        result, _ = _run_strict(provider, envelope, payload)

        self.assertIsInstance(result, str)
        self.assertEqual(TRUNCATED_NESTED, result)

    def test_complete_object_returns_dict_with_unexpected_keys(self):
        provider = _make_provider(strict_response_shape=True)
        envelope = _make_envelope()
        payload = _completion_payload(COMPLETE_OBJECT)

        result, _ = _run_strict(provider, envelope, payload)

        # Complete structure passes through untouched for upstream validation,
        # even with schema-unknown keys.
        self.assertEqual(json.loads(COMPLETE_OBJECT), result)
        diag = provider.strict_response_diagnostics
        self.assertEqual("ok", diag["strict_parse_status"])
        self.assertFalse(diag["strict_fenced"])
        self.assertNotIn("strict_failure_code", diag)

    def test_complete_fenced_object_returns_dict(self):
        provider = _make_provider(strict_response_shape=True)
        envelope = _make_envelope()
        payload = _completion_payload(FENCED_OBJECT)

        result, _ = _run_strict(provider, envelope, payload)

        self.assertEqual({"task_id": "task_visual_001", "passed": True}, result)
        diag = provider.strict_response_diagnostics
        self.assertEqual("ok_fenced", diag["strict_parse_status"])
        self.assertTrue(diag["strict_fenced"])

    def test_truncated_fence_returns_raw(self):
        provider = _make_provider(strict_response_shape=True)
        envelope = _make_envelope()
        payload = _completion_payload(TRUNCATED_FENCE)

        result, _ = _run_strict(provider, envelope, payload)

        self.assertIsInstance(result, str)
        self.assertEqual(TRUNCATED_FENCE, result)
        self.assertEqual(
            "truncated_fence", provider.strict_response_diagnostics["strict_parse_status"]
        )

    def test_non_object_json_returns_raw(self):
        provider = _make_provider(strict_response_shape=True)
        envelope = _make_envelope()
        payload = _completion_payload(NON_OBJECT)

        result, _ = _run_strict(provider, envelope, payload)

        self.assertIsInstance(result, str)
        self.assertEqual(NON_OBJECT, result)
        self.assertEqual(
            "non_object", provider.strict_response_diagnostics["strict_parse_status"]
        )

    def test_strict_preserves_text_and_image_wire_format(self):
        image = _make_image(_png_bytes(b"strict-wire-bytes"))
        provider = _make_provider(strict_response_shape=True)
        envelope = _make_envelope(images=[image])
        payload = _completion_payload(COMPLETE_OBJECT)

        result, urlopen = _run_strict(provider, envelope, payload)

        self.assertEqual(json.loads(COMPLETE_OBJECT), result)
        body = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        content = body["messages"][1]["content"]
        self.assertEqual(
            json.dumps(envelope.payload, ensure_ascii=False), content[0]["text"]
        )
        data_url = content[1]["image_url"]["url"]
        self.assertTrue(data_url.startswith("data:image/png;base64,"))
        self.assertEqual(
            image.data, base64.b64decode(data_url.split(",", 1)[1])
        )

    def test_strict_plain_text_envelope_supported(self):
        provider = _make_provider(strict_response_shape=True)
        envelope = _make_plain_envelope()
        payload = _completion_payload(TRUNCATED_NESTED)

        result, urlopen = _run_strict(provider, envelope, payload)

        self.assertIsInstance(result, str)
        self.assertEqual(TRUNCATED_NESTED, result)
        body = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertIsInstance(body["messages"][1]["content"], str)

    def test_strict_identity_mismatch_still_refused(self):
        provider = _make_provider(
            strict_response_shape=True, expected_response_model="vision-expected"
        )
        envelope = _make_envelope()
        payload = _completion_payload(COMPLETE_OBJECT, model="vision-other")

        with patch(
            "services.api.app.ai_gateway.urllib.request.urlopen",
            return_value=_FakeShapeResponse(payload),
        ):
            with self.assertRaisesRegex(
                AiProviderRuntimeError, "does not match"
            ) as raised:
                provider.run(envelope)

        self.assertEqual("vision-other", provider.response_model)
        self.assertEqual(
            "provider_response_model_mismatch",
            raised.exception.diagnostics["failure_code"],
        )

    def test_strict_retry_budget_unchanged_single_post_on_success(self):
        provider = _make_provider(strict_response_shape=True)
        envelope = _make_envelope()
        payload = _completion_payload(COMPLETE_OBJECT)

        with (
            patch(
                "services.api.app.ai_gateway.urllib.request.urlopen",
                side_effect=[
                    _http_error(500),
                    _FakeShapeResponse(payload),
                ],
            ) as urlopen,
            patch("services.api.app.ai_gateway.time.sleep") as sleep,
            patch(
                "services.api.app.ai_gateway.random.uniform", return_value=0.0
            ),
        ):
            result = provider.run(envelope)

        self.assertEqual(json.loads(COMPLETE_OBJECT), result)
        self.assertEqual(2, urlopen.call_count)
        sleep.assert_called_once_with(0.5)

    def test_strict_diagnostics_bounded_without_secrets(self):
        long_object = '{"blob": "' + "x" * (MONITORING_VISUAL_STRICT_RAW_MAX_CHARS + 1000) + '"}'
        self.assertGreater(len(long_object), MONITORING_VISUAL_STRICT_RAW_MAX_CHARS)
        image = _make_image()
        provider = _make_provider(strict_response_shape=True)
        envelope = _make_envelope(images=[image])
        payload = _completion_payload(long_object)

        result, _ = _run_strict(provider, envelope, payload)

        self.assertEqual(json.loads(long_object), result)
        diag = provider.strict_response_diagnostics
        self.assertEqual(len(long_object), diag["strict_raw_chars"])
        self.assertEqual(
            hashlib.sha256(long_object.encode("utf-8")).hexdigest(),
            diag["strict_raw_sha256"],
        )
        self.assertEqual(
            MONITORING_VISUAL_STRICT_RAW_MAX_CHARS, len(diag["strict_raw_preview"])
        )
        self.assertTrue(diag["strict_raw_truncated"])
        image_b64 = base64.b64encode(image.data).decode("ascii")
        for name, scope in (
            ("strict", provider.strict_response_diagnostics),
            ("response", provider.response_diagnostics),
        ):
            rendered = json.dumps(scope, ensure_ascii=False)
            self.assertNotIn("test-key", rendered, name)
            self.assertNotIn(image_b64, rendered, name)
            self.assertNotIn("Authorization", rendered, name)


class MonitoringStrictParseUnitTests(unittest.TestCase):
    def test_empty_content_reports_empty(self):
        with self.assertRaises(MonitoringVisualStrictContentError) as raised:
            parse_monitoring_visual_strict_content("   ")
        self.assertEqual("empty", raised.exception.code)

    def test_prose_wrapped_fence_is_not_salvaged(self):
        with self.assertRaises(MonitoringVisualStrictContentError) as raised:
            parse_monitoring_visual_strict_content(
                'Here you go:\n```json\n{"a": 1}\n```'
            )
        self.assertEqual("invalid_json", raised.exception.code)

    def test_non_string_content_rejected(self):
        with self.assertRaises(MonitoringVisualStrictContentError):
            parse_monitoring_visual_strict_content({"a": 1})

    def test_envelope_predicate_exact_match_only(self):
        self.assertTrue(
            is_monitoring_visual_strict_envelope(
                _make_envelope(
                    prompt_version=MONITORING_VISUAL_STRICT_PROMPT_VERSION
                )
            )
        )
        self.assertFalse(is_monitoring_visual_strict_envelope(_make_envelope()))
        self.assertFalse(
            is_monitoring_visual_strict_envelope(
                _make_envelope(
                    prompt_version=MONITORING_VISUAL_STRICT_PROMPT_VERSION + "_x"
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
