#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合成离线一键生命周期演练。

The adapter in this module is deliberately memory-only.  It models lifecycle
signals and ownership without importing a service runner, using operating-system
networking, spawning a process, reading a project, calling a model, or touching
the filesystem.  The CLI therefore exercises the one-click contract while never
starting the product runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from canonical_evidence import canonical_digest, canonical_json_bytes, digest_ref


LIFECYCLE_SCHEMA = "mm-monitoring-r8-g2-synthetic-lifecycle-v1"
LIFECYCLE_VERSION = "1"
ADAPTER_ID = "synthetic-runtime-adapter"
ADAPTER_VERSION = "1"

ENDPOINTS: Tuple[str, ...] = ("backend", "frontend", "auxiliary")
SCENARIOS: Tuple[str, ...] = (
    "start-stop-restart",
    "ready",
    "failure",
    "partial",
    "foreign-ownership",
)

# Public descriptive names kept alongside the concise constants.
SYNTHETIC_LIFECYCLE_SCHEMA = LIFECYCLE_SCHEMA
SYNTHETIC_LIFECYCLE_VERSION = LIFECYCLE_VERSION
SYNTHETIC_ADAPTER_ID = ADAPTER_ID
SCENARIO_ALIASES = {
    "start_stop_restart": "start-stop-restart",
    "foreign": "foreign-ownership",
    "foreign_ownership": "foreign-ownership",
}
SCENARIO_EXPECTATIONS = {
    "start-stop-restart": {
        "steps": (("start", "ready", "ready"), ("stop", "stopped", "stopped"), ("restart", "ready", "ready")),
        "events": (
            "operation_requested", "endpoint_starting", "endpoint_ready",
            "endpoint_starting", "endpoint_ready", "endpoint_starting", "endpoint_ready",
            "ready_signaled", "operation_requested", "endpoint_stopped", "endpoint_stopped",
            "endpoint_stopped", "stopped_signaled", "operation_requested",
            "operation_requested", "stopped_signaled", "operation_requested",
            "endpoint_starting", "endpoint_ready", "endpoint_starting", "endpoint_ready",
            "endpoint_starting", "endpoint_ready", "ready_signaled",
        ),
    },
    "ready": {
        "steps": (("start", "ready", "ready"),),
        "events": (
            "operation_requested", "endpoint_starting", "endpoint_ready",
            "endpoint_starting", "endpoint_ready", "endpoint_starting", "endpoint_ready",
            "ready_signaled",
        ),
    },
    "failure": {
        "steps": (("start", "failed", "stopped"),),
        "events": (
            "operation_requested", "endpoint_starting", "endpoint_ready",
            "endpoint_starting", "endpoint_start_failed", "endpoint_rollback_stopped",
            "rollback_complete",
        ),
    },
    "partial": {
        "steps": (("start", "partial", "partial"),),
        "events": ("operation_requested", "start_rejected"),
    },
    "foreign-ownership": {
        "steps": (
            ("start", "foreign_ownership", "foreign_ownership"),
            ("stop", "foreign_ownership", "foreign_ownership"),
            ("restart", "foreign_ownership", "foreign_ownership"),
        ),
        "events": (
            "operation_requested", "start_rejected", "operation_requested", "stop_rejected",
            "operation_requested", "operation_requested", "stop_rejected", "restart_rejected",
        ),
    },
}

_STOPPED = "stopped"
_READY = "ready"
_FOREIGN = "foreign"
_ALLOWED_INITIAL_STATES = frozenset({_STOPPED, _READY, _FOREIGN})


class SyntheticLifecycleError(ValueError):
    """合成生命周期输入、证据或回放无效。"""


@dataclass(frozen=True)
class ReplayResult:
    """独立回放结果；失败时保留可机器读取的错误标签。"""

    valid: bool
    scenario: Optional[str] = None
    status: Optional[str] = None
    errors: Tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.valid

    def as_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "scenario": self.scenario,
            "status": self.status,
            "errors": list(self.errors),
        }


def _copy_json(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SyntheticLifecycleError("%s_must_be_object" % field)
    return value


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SyntheticLifecycleError("%s_must_be_non_empty_string" % field)
    return value


def _check_endpoint(value: Any, field: str) -> str:
    endpoint = _require_string(value, field)
    if endpoint not in ENDPOINTS:
        raise SyntheticLifecycleError("%s_unknown_endpoint" % field)
    return endpoint


def _unique_endpoints(values: Iterable[str], field: str) -> Tuple[str, ...]:
    result: List[str] = []
    seen = set()
    for index, raw in enumerate(values):
        endpoint = _check_endpoint(raw, "%s[%d]" % (field, index))
        if endpoint in seen:
            raise SyntheticLifecycleError("%s_duplicate_endpoint" % field)
        seen.add(endpoint)
        result.append(endpoint)
    return tuple(result)


def _status_for_states(states: Mapping[str, str]) -> str:
    if any(states[endpoint] == _FOREIGN for endpoint in ENDPOINTS):
        return "foreign_ownership"
    ready_count = sum(states[endpoint] == _READY for endpoint in ENDPOINTS)
    if ready_count == len(ENDPOINTS):
        return "ready"
    if ready_count:
        return "partial"
    return "stopped"


def _signal_for_status(status: str) -> str:
    if status == "ready":
        return "ready"
    if status == "stopped":
        return "stopped"
    return "failure"


class SyntheticLifecycleAdapter:
    """In-memory adapter that drives all lifecycle outcomes.

    ``failure_endpoint`` injects a deterministic start failure.  ``initial_states``
    and ``foreign_endpoints`` model residual partial ownership and an external
    owner without creating a process or using an operating-system resource.
    """

    def __init__(
        self,
        *,
        initial_states: Optional[Mapping[str, str]] = None,
        failure_endpoint: Optional[str] = None,
        foreign_endpoints: Iterable[str] = (),
    ) -> None:
        states = {endpoint: _STOPPED for endpoint in ENDPOINTS}
        if initial_states is not None:
            for raw_endpoint, raw_state in initial_states.items():
                endpoint = _check_endpoint(raw_endpoint, "initial_states.endpoint")
                if raw_state not in _ALLOWED_INITIAL_STATES:
                    raise SyntheticLifecycleError("initial_states.%s_invalid" % endpoint)
                states[endpoint] = str(raw_state)

        foreign = _unique_endpoints(foreign_endpoints, "foreign_endpoints")
        for endpoint in foreign:
            if states[endpoint] == _READY:
                raise SyntheticLifecycleError("foreign_endpoint_already_owned")
            states[endpoint] = _FOREIGN

        if failure_endpoint is not None:
            failure_endpoint = _check_endpoint(failure_endpoint, "failure_endpoint")
            if states[failure_endpoint] != _STOPPED:
                raise SyntheticLifecycleError("failure_endpoint_must_start_stopped")

        self._states: Dict[str, str] = states
        self._failure_endpoint = failure_endpoint
        self._events: List[Dict[str, Any]] = []

    @property
    def events(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(_copy_json(self._events))

    @property
    def states(self) -> Dict[str, str]:
        return dict(self._states)

    @property
    def foreign_endpoints(self) -> Tuple[str, ...]:
        return tuple(endpoint for endpoint in ENDPOINTS if self._states[endpoint] == _FOREIGN)

    def _event(
        self,
        kind: str,
        *,
        operation: str,
        endpoint: Optional[str] = None,
        from_state: Optional[str] = None,
        to_state: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        event: Dict[str, Any] = {
            "sequence": len(self._events) + 1,
            "kind": kind,
            "operation": operation,
            "endpoint": endpoint,
            "from_state": from_state,
            "to_state": to_state,
            "reason": reason,
        }
        self._events.append(event)

    def _result(
        self,
        operation: str,
        status: str,
        *,
        reason: Optional[str] = None,
        before: Optional[Mapping[str, str]] = None,
        rollback_complete: bool = False,
    ) -> Dict[str, Any]:
        current = dict(self._states)
        current_status = _status_for_states(current)
        foreign = tuple(endpoint for endpoint in ENDPOINTS if current[endpoint] == _FOREIGN)
        return {
            "operation": operation,
            "status": status,
            "signal": _signal_for_status(status),
            "ready_signal": status == "ready",
            "failure_signal": status in {"failed", "partial", "foreign_ownership"},
            "reason": reason,
            "before": dict(before or current),
            "after": current,
            "postcondition_status": current_status,
            "foreign_endpoints": list(foreign),
            "foreign_preserved": bool(foreign),
            "changed": dict(before or current) != current,
            "rollback_complete": rollback_complete,
        }

    def status(self) -> Dict[str, Any]:
        current = dict(self._states)
        status = _status_for_states(current)
        self._event("status_observed", operation="status", reason=status)
        return self._result("status", status, before=current, rollback_complete=True)

    def start(self) -> Dict[str, Any]:
        before = dict(self._states)
        self._event("operation_requested", operation="start")

        foreign = self.foreign_endpoints
        if foreign:
            self._event(
                "start_rejected",
                operation="start",
                reason="foreign_ownership",
            )
            return self._result(
                "start",
                "foreign_ownership",
                reason="foreign_ownership",
                before=before,
                rollback_complete=True,
            )

        current_status = _status_for_states(self._states)
        if current_status == "ready":
            self._event("start_idempotent", operation="start", reason="already_ready")
            return self._result(
                "start",
                "ready",
                reason="already_ready",
                before=before,
                rollback_complete=True,
            )
        if current_status == "partial":
            self._event("start_rejected", operation="start", reason="partial_runtime")
            return self._result(
                "start",
                "partial",
                reason="partial_runtime",
                before=before,
                rollback_complete=True,
            )

        started: List[str] = []
        for endpoint in ENDPOINTS:
            self._event(
                "endpoint_starting",
                operation="start",
                endpoint=endpoint,
                from_state=self._states[endpoint],
                to_state="starting",
            )
            if endpoint == self._failure_endpoint:
                self._event(
                    "endpoint_start_failed",
                    operation="start",
                    endpoint=endpoint,
                    from_state=_STOPPED,
                    to_state=_STOPPED,
                    reason="synthetic_start_failure",
                )
                for rollback_endpoint in reversed(started):
                    previous = self._states[rollback_endpoint]
                    self._states[rollback_endpoint] = _STOPPED
                    self._event(
                        "endpoint_rollback_stopped",
                        operation="start",
                        endpoint=rollback_endpoint,
                        from_state=previous,
                        to_state=_STOPPED,
                        reason="synthetic_start_failure",
                    )
                self._event(
                    "rollback_complete",
                    operation="start",
                    reason="synthetic_start_failure",
                )
                return self._result(
                    "start",
                    "failed",
                    reason="synthetic_start_failure",
                    before=before,
                    rollback_complete=True,
                )

            self._states[endpoint] = _READY
            started.append(endpoint)
            self._event(
                "endpoint_ready",
                operation="start",
                endpoint=endpoint,
                from_state=_STOPPED,
                to_state=_READY,
            )

        self._event("ready_signaled", operation="start", reason="all_endpoints_ready")
        return self._result("start", "ready", before=before, rollback_complete=True)

    def stop(self) -> Dict[str, Any]:
        before = dict(self._states)
        self._event("operation_requested", operation="stop")

        foreign = self.foreign_endpoints
        if foreign:
            self._event(
                "stop_rejected",
                operation="stop",
                reason="foreign_ownership",
            )
            return self._result(
                "stop",
                "foreign_ownership",
                reason="foreign_ownership",
                before=before,
                rollback_complete=True,
            )

        for endpoint in reversed(ENDPOINTS):
            if self._states[endpoint] != _READY:
                continue
            self._states[endpoint] = _STOPPED
            self._event(
                "endpoint_stopped",
                operation="stop",
                endpoint=endpoint,
                from_state=_READY,
                to_state=_STOPPED,
            )
        self._event("stopped_signaled", operation="stop", reason="owned_endpoints_stopped")
        return self._result("stop", "stopped", before=before, rollback_complete=True)

    def restart(self) -> Dict[str, Any]:
        before = dict(self._states)
        self._event("operation_requested", operation="restart")
        stopped = self.stop()
        if stopped["status"] != "stopped":
            self._event(
                "restart_rejected",
                operation="restart",
                reason=str(stopped["reason"] or stopped["status"]),
            )
            result = self._result(
                "restart",
                str(stopped["status"]),
                reason=str(stopped["reason"] or stopped["status"]),
                before=before,
                rollback_complete=True,
            )
            result["restart_stop"] = stopped
            result["restart_start"] = None
            return result

        started = self.start()
        result = self._result(
            "restart",
            str(started["status"]),
            reason=started["reason"],
            before=before,
            rollback_complete=bool(started["rollback_complete"]),
        )
        result["restart_stop"] = stopped
        result["restart_start"] = started
        return result


# Descriptive aliases for callers that use either naming convention.
SyntheticRuntimeAdapter = SyntheticLifecycleAdapter
SyntheticAdapter = SyntheticLifecycleAdapter


def _canonical_scenario(value: Any) -> str:
    scenario = _require_string(value, "scenario")
    return SCENARIO_ALIASES.get(scenario, scenario)


def _scenario_adapter(scenario: str) -> Tuple[SyntheticLifecycleAdapter, Tuple[str, ...]]:
    if scenario == "start-stop-restart":
        return SyntheticLifecycleAdapter(), ("start", "stop", "restart")
    if scenario == "ready":
        return SyntheticLifecycleAdapter(), ("start",)
    if scenario == "failure":
        return SyntheticLifecycleAdapter(failure_endpoint="frontend"), ("start",)
    if scenario == "partial":
        return SyntheticLifecycleAdapter(initial_states={"backend": _READY}), ("start",)
    if scenario == "foreign-ownership":
        return SyntheticLifecycleAdapter(foreign_endpoints=("backend",)), (
            "start",
            "stop",
            "restart",
        )
    raise SyntheticLifecycleError("unknown_scenario")


def _run_operation(adapter: SyntheticLifecycleAdapter, operation: str) -> Dict[str, Any]:
    handler = getattr(adapter, operation, None)
    if not callable(handler):
        raise SyntheticLifecycleError("unsupported_operation")
    return handler()


def _build_synthetic_lifecycle(scenario: str) -> Dict[str, Any]:
    scenario = _canonical_scenario(scenario)
    if scenario not in SCENARIOS:
        raise SyntheticLifecycleError("unknown_scenario")

    adapter, operations = _scenario_adapter(scenario)
    steps: List[Dict[str, Any]] = []
    for index, operation in enumerate(operations, start=1):
        result = _run_operation(adapter, operation)
        result["step"] = index
        steps.append(result)

    final_step = steps[-1]
    final_status = str(final_step["status"])
    final_after = dict(final_step["after"])
    no_half_initialized = all(state in {_STOPPED, _READY, _FOREIGN} for state in final_after.values())
    failure_rolled_back = (
        scenario != "failure"
        or (
            final_status == "failed"
            and final_step["postcondition_status"] == "stopped"
            and final_step["rollback_complete"] is True
        )
    )
    foreign_preserved = (
        scenario != "foreign-ownership"
        or (
            final_step["status"] == "foreign_ownership"
            and final_step["foreign_preserved"] is True
            and final_after["backend"] == _FOREIGN
        )
    )
    checks = {
        "synthetic_only": True,
        "offline": True,
        "transport": "in_memory",
        "external_processes_started": 0,
        "network_calls": 0,
        "model_calls": 0,
        "filesystem_reads": 0,
        "filesystem_writes": 0,
        "manual_endpoint_configuration": False,
        "no_half_initialized_state": no_half_initialized,
        "failure_rolled_back": failure_rolled_back,
        "foreign_ownership_preserved": foreign_preserved,
    }
    body: Dict[str, Any] = {
        "schema": LIFECYCLE_SCHEMA,
        "version": LIFECYCLE_VERSION,
        "synthetic": True,
        "offline": True,
        "adapter": {
            "id": ADAPTER_ID,
            "version": ADAPTER_VERSION,
            "kind": "synthetic",
            "mode": "offline",
            "state_store": "memory",
        },
        "scenario": scenario,
        "steps": steps,
        "events": list(adapter.events),
        "final": {
            "status": final_status,
            "signal": final_step["signal"],
            "ready_signal": final_step["ready_signal"],
            "failure_signal": final_step["failure_signal"],
            "postcondition_status": final_step["postcondition_status"],
            "endpoint_states": final_after,
            "foreign_endpoints": list(adapter.foreign_endpoints),
        },
        "checks": checks,
        "lifecycle_digest": "",
    }
    body["lifecycle_digest"] = digest_ref(body)
    return body


def validate_synthetic_lifecycle(value: Mapping[str, Any]) -> Dict[str, Any]:
    """严格校验合成一键证据并重放固定 scenario。"""

    raw = dict(_require_mapping(value, "lifecycle"))
    required = {
        "schema",
        "version",
        "synthetic",
        "offline",
        "adapter",
        "scenario",
        "steps",
        "events",
        "final",
        "checks",
        "lifecycle_digest",
    }
    if set(raw) != required:
        raise SyntheticLifecycleError("lifecycle_fields_mismatch")
    if raw["schema"] != LIFECYCLE_SCHEMA:
        raise SyntheticLifecycleError("schema_mismatch")
    if raw["version"] != LIFECYCLE_VERSION:
        raise SyntheticLifecycleError("version_mismatch")
    if raw["synthetic"] is not True or raw["offline"] is not True:
        raise SyntheticLifecycleError("offline_synthetic_boundary_mismatch")
    adapter = dict(_require_mapping(raw["adapter"], "adapter"))
    expected_adapter = {
        "id": ADAPTER_ID,
        "version": ADAPTER_VERSION,
        "kind": "synthetic",
        "mode": "offline",
        "state_store": "memory",
    }
    if adapter != expected_adapter:
        raise SyntheticLifecycleError("adapter_mismatch")
    scenario = _require_string(raw["scenario"], "scenario")
    if scenario not in SCENARIOS:
        raise SyntheticLifecycleError("unknown_scenario")
    if not isinstance(raw["steps"], list) or not raw["steps"]:
        raise SyntheticLifecycleError("steps_must_be_non_empty_array")
    if not isinstance(raw["events"], list):
        raise SyntheticLifecycleError("events_must_be_array")
    _require_mapping(raw["final"], "final")
    checks = dict(_require_mapping(raw["checks"], "checks"))
    expected_check_keys = {
        "synthetic_only",
        "offline",
        "transport",
        "external_processes_started",
        "network_calls",
        "model_calls",
        "filesystem_reads",
        "filesystem_writes",
        "manual_endpoint_configuration",
        "no_half_initialized_state",
        "failure_rolled_back",
        "foreign_ownership_preserved",
    }
    if set(checks) != expected_check_keys:
        raise SyntheticLifecycleError("checks_fields_mismatch")
    if checks["synthetic_only"] is not True or checks["offline"] is not True:
        raise SyntheticLifecycleError("checks_boundary_mismatch")
    if checks["transport"] != "in_memory":
        raise SyntheticLifecycleError("transport_mismatch")
    for key in (
        "external_processes_started",
        "network_calls",
        "model_calls",
        "filesystem_reads",
        "filesystem_writes",
    ):
        if checks[key] != 0:
            raise SyntheticLifecycleError("%s_nonzero" % key)
    for key in (
        "manual_endpoint_configuration",
        "no_half_initialized_state",
        "failure_rolled_back",
        "foreign_ownership_preserved",
    ):
        if not isinstance(checks[key], bool):
            raise SyntheticLifecycleError("%s_must_be_bool" % key)
    lifecycle_digest = raw["lifecycle_digest"]
    if not isinstance(lifecycle_digest, str) or not lifecycle_digest.startswith("sha256:"):
        raise SyntheticLifecycleError("lifecycle_digest_invalid")
    body = dict(raw)
    body["lifecycle_digest"] = ""
    if digest_ref(body) != lifecycle_digest:
        raise SyntheticLifecycleError("lifecycle_digest_mismatch")

    expectation = SCENARIO_EXPECTATIONS[scenario]
    actual_steps = tuple(
        (
            _require_string(_require_mapping(step, "steps[]").get("operation"), "steps.operation"),
            _require_string(_require_mapping(step, "steps[]").get("status"), "steps.status"),
            _require_string(
                _require_mapping(step, "steps[]").get("postcondition_status"),
                "steps.postcondition_status",
            ),
        )
        for step in raw["steps"]
    )
    actual_events = tuple(
        _require_string(_require_mapping(event, "events[]").get("kind"), "events.kind")
        for event in raw["events"]
    )
    final = _require_mapping(raw["final"], "final")
    if (
        actual_steps != expectation["steps"]
        or actual_events != expectation["events"]
        or final.get("status") != expectation["steps"][-1][1]
        or final.get("postcondition_status") != expectation["steps"][-1][2]
        or checks["no_half_initialized_state"] is not True
        or checks["failure_rolled_back"] is not True
        or checks["foreign_ownership_preserved"] is not True
        or checks["manual_endpoint_configuration"] is not False
    ):
        raise SyntheticLifecycleError("scenario_replay_mismatch")
    return _copy_json(raw)


def run_synthetic_lifecycle(scenario: str = "start-stop-restart") -> Dict[str, Any]:
    """运行一个不依赖外部资源的一键生命周期 scenario。"""

    return validate_synthetic_lifecycle(_build_synthetic_lifecycle(scenario))


# Small descriptive aliases for offline callers.
run_synthetic_runtime = run_synthetic_lifecycle
build_synthetic_lifecycle_evidence = run_synthetic_lifecycle


def replay_synthetic_lifecycle(value: Any, *, strict: bool = False) -> ReplayResult:
    scenario: Optional[str] = None
    status: Optional[str] = None
    errors: List[str] = []
    try:
        if isinstance(value, Mapping):
            scenario_value = value.get("scenario")
            scenario = scenario_value if isinstance(scenario_value, str) else None
            final = value.get("final")
            if isinstance(final, Mapping) and isinstance(final.get("status"), str):
                status = str(final["status"])
        validate_synthetic_lifecycle(_require_mapping(value, "lifecycle"))
    except (SyntheticLifecycleError, TypeError, ValueError) as exc:
        errors.append(str(exc))
        if strict:
            raise SyntheticLifecycleError(str(exc)) from exc
    return ReplayResult(
        valid=not errors,
        scenario=scenario,
        status=status,
        errors=tuple(errors),
    )


independent_replay = replay_synthetic_lifecycle
replay_synthetic_runtime = replay_synthetic_lifecycle
validate_lifecycle_evidence = validate_synthetic_lifecycle
replay_lifecycle_evidence = replay_synthetic_lifecycle


def _load_json_input(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SyntheticLifecycleError("input_unreadable:%s" % type(exc).__name__) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="synthetic_lifecycle",
        description="医学监查工作台合成离线一键生命周期演练（仅内存，不启动服务）",
    )
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser("run", help="运行合成生命周期演练")
    run.add_argument("--scenario", choices=SCENARIOS, default="start-stop-restart")
    replay = sub.add_parser("replay", help="独立回放合成生命周期 JSON")
    replay.add_argument("input", help="证据 JSON 路径；使用 - 从标准输入读取")
    replay.add_argument("--strict", action="store_true", help="遇到不一致时以错误退出")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    except SystemExit as exc:
        code = int(exc.code or 0)
        return 0 if code == 0 else 2

    if args.command == "run":
        try:
            evidence = run_synthetic_lifecycle(args.scenario)
        except SyntheticLifecycleError as exc:
            sys.stderr.write("合成离线生命周期演练失败：%s\n" % exc)
            return 2
        sys.stdout.write(json.dumps(evidence, ensure_ascii=False, sort_keys=True) + "\n")
        return 0

    if args.command == "replay":
        try:
            result = replay_synthetic_lifecycle(_load_json_input(args.input), strict=bool(args.strict))
        except SyntheticLifecycleError as exc:
            sys.stderr.write("合成离线生命周期回放失败：%s\n" % exc)
            return 2
        sys.stdout.write(json.dumps(result.as_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return 0 if result.valid else 1

    parser.print_help(sys.stderr)
    sys.stderr.write("请指定操作：run 或 replay。\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
