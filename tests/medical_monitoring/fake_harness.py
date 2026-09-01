"""Deterministic harness catalog and transport fakes for product tests.

These fakes never start a process or contact a provider.  They expose the
small adapter surface consumed by ``HarnessCapabilityRuntime`` so the
product-router tests can inject catalog, receipt, blocking, and identity
failures without touching a real model transport.  Moved from the R7 POC
suite during B6; the adapter contract is the package-native authority in
``packages.medical_monitoring.runtime.agent_harness``.
"""

from __future__ import annotations

import hashlib
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from packages.medical_monitoring.runtime.agent_harness import (
    InvocationReceipt,
    PreflightResult,
)


@dataclass(frozen=True)
class FakeCatalog:
    """Minimal catalog marker consumed by ``FakeHarnessAdapter``."""

    name: str = "synthetic-catalog"
    valid: bool = True
    failure_reason: str = "catalog_unavailable"


class FakeHarnessAdapter:
    """Thread-safe fake adapter with deterministic fault injection."""

    def __init__(
        self,
        *,
        states: Sequence[str] = ("complete",),
        catalog_ok: bool = True,
        preflight_reason: str = "catalog_unavailable",
        block: bool = False,
        block_timeout_seconds: float = 5.0,
        receipt_overrides: Optional[Mapping[str, Any]] = None,
        raise_on_invoke: bool = False,
        preflight_exception: Optional[Exception] = None,
        invoke_exceptions: Sequence[Optional[Exception]] = (),
    ) -> None:
        self.states = tuple(str(value) for value in states) or ("complete",)
        self.catalog_ok = bool(catalog_ok)
        self.preflight_reason = str(preflight_reason)
        self.block = bool(block)
        self.block_timeout_seconds = float(block_timeout_seconds)
        self.receipt_overrides = dict(receipt_overrides or {})
        self.raise_on_invoke = bool(raise_on_invoke)
        self.preflight_exception = preflight_exception
        self.invoke_exceptions = tuple(invoke_exceptions)
        self.catalog_calls: list[Any] = []
        self.preflight_results: list[PreflightResult] = []
        self.invoke_preflight_results: list[PreflightResult] = []
        self.preflight_calls = 0
        self.invoke_calls: list[dict[str, Any]] = []
        self._state_index = 0
        self._lock = threading.Lock()
        self.entered = threading.Event()
        self.release = threading.Event()

    def preflight(
        self,
        profile: Any,
        *,
        catalog: Any = None,
        extra_allowed_tools: Optional[Sequence[str]] = None,
    ) -> PreflightResult:
        del extra_allowed_tools
        with self._lock:
            self.preflight_calls += 1
            self.catalog_calls.append(catalog)
        if self.preflight_exception is not None:
            raise self.preflight_exception
        valid_catalog = bool(getattr(catalog, "valid", True))
        ok = self.catalog_ok and valid_catalog
        reason = str(getattr(catalog, "failure_reason", "") or self.preflight_reason)
        result = PreflightResult(
            ok=ok,
            executable=sys.executable if ok else "",
            selector=profile.effective_selector,
            effort=profile.reasoning_effort,
            allowed_tools=tuple(profile.allowed_tools),
            timeout_seconds=int(profile.timeout_seconds),
            reasons=() if ok else (reason,),
        )
        with self._lock:
            self.preflight_results.append(result)
        return result

    def invoke(
        self,
        profile: Any,
        prompt: str,
        *,
        output_dir: Any,
        expected_units: Sequence[str],
        invocation_id: str,
        preflight_result: PreflightResult,
        **kwargs: Any,
    ) -> InvocationReceipt:
        if not preflight_result.ok:
            raise RuntimeError("fake transport received failed preflight")
        catalog = kwargs.get("catalog")
        with self._lock:
            self.invoke_preflight_results.append(preflight_result)
        with self._lock:
            index = len(self.invoke_calls)
            state = self.states[min(index, len(self.states) - 1)]
            self.invoke_calls.append(
                {
                    "invocation_id": invocation_id,
                    "prompt": prompt,
                    "expected_units": tuple(expected_units),
                    "catalog_name": str(getattr(catalog, "name", "") or ""),
                    "catalog_valid": bool(getattr(catalog, "valid", True)),
                    "preflight_ok": bool(preflight_result.ok),
                    "preflight_selector": preflight_result.selector,
                    "preflight_effort": preflight_result.effort,
                    "profile_digest": profile.execution_profile_digest,
                    "requested_provider": profile.requested_provider,
                    "requested_model": profile.requested_model,
                    "selector": profile.effective_selector,
                    "effort": profile.reasoning_effort,
                    "output_dir": str(output_dir),
                }
            )
        self.entered.set()
        fault = (
            self.invoke_exceptions[min(index, len(self.invoke_exceptions) - 1)]
            if self.invoke_exceptions else None
        )
        if fault is not None:
            raise fault
        if self.raise_on_invoke:
            raise RuntimeError("transport_unavailable: token=super-secret-value")
        if self.block and not self.release.wait(self.block_timeout_seconds):
            raise TimeoutError("fake transport release timeout")
        expected = tuple(str(value) for value in expected_units)
        if state == "complete" or state == "truncated":
            produced = expected
        elif state == "partial":
            produced = expected[: max(0, len(expected) - 1)]
        else:
            produced = ()
        missing = tuple(value for value in expected if value not in produced)
        now = float(index + 1)
        values: dict[str, Any] = {
            "invocation_id": invocation_id,
            "profile_digest": profile.execution_profile_digest,
            "adapter_id": profile.adapter_id,
            "adapter_version": profile.adapter_version,
            "input_digest": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "requested_selector": profile.effective_selector,
            "effective_selector": profile.effective_selector,
            "reasoning_effort": profile.reasoning_effort,
            "allowed_tools": tuple(profile.allowed_tools),
            "started_at": now,
            "ended_at": now + 0.001,
            "duration_seconds": 0.001,
            "state": state,
            "parse_state": "parsed" if state in {"complete", "partial", "truncated"} else "unparsed",
            "expected_units": expected,
            "produced_units": produced,
            "missing_units": missing,
            "stdout_path": str(Path(output_dir) / "super-secret-path.stdout.json"),
            "stdout_sha256": "f" * 64,
            "stderr_summary": "token=super-secret-value",
            "exit_code": 0,
            "failure_reason": "" if state == "complete" else "synthetic_%s" % state,
            "fallback_used": False,
            "analysis_complete": state == "complete",
            "unsupported_operation": "",
        }
        values.update(self.receipt_overrides)
        return InvocationReceipt(**values)


__all__ = ["FakeCatalog", "FakeHarnessAdapter"]
