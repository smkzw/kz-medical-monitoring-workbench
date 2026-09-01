"""Provider-neutral API/harness execution boundary for the isolated R1 POC.

This module does not choose a provider or model.  A user-selected
``ExecutionProfile`` freezes that choice, an opaque credential reference and
the permitted execution surface.  API and harness transports exchange the
same JSON-RPC-shaped request/result envelope and finish through the existing
candidate-only :mod:`mm_r1.adapters` contract.

The implementation intentionally contains no real provider client.  API
transport is injected; the harness transport uses an explicit argv tuple,
``shell=False`` and JSON on stdin/stdout.  Tests therefore exercise real
process boundaries without contacting a service, provider or real project.
"""

from __future__ import annotations

import json
import hashlib
import os
import signal
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Protocol, Sequence, Tuple, Union
from urllib.parse import urlsplit

from .adapters import (
    AdapterPersistenceReceipt,
    AdapterRun,
    AdapterState,
    ImmutableAdapterBinding,
    ScriptedOutput,
    _coerce_coverage_unit,
    _make_candidate_artifact,
    _make_coverage,
    _make_raw_provenance,
    _resolve_status,
    freeze_binding,
    persist_adapter_run,
)
from .domain import (
    CoverageUnit,
    CoverageUnitStatus,
    ModelAnalysis,
    canonical_json,
    content_hash,
    from_jsonable,
    now_iso,
    to_jsonable,
)


class TransportKind(str, Enum):
    API = "api"
    HARNESS = "harness"


class HarnessIsolationBackend(str, Enum):
    """Actually enforced harness backends accepted by this isolated R1 slice."""

    MACOS_SEATBELT_R1 = "macos_seatbelt_r1"


_SANDBOX_EXEC_PATH = Path("/usr/bin/sandbox-exec")
_SEATBELT_DENIED_READ_ROOTS = (
    "/Users",
    "/private/tmp",
    "/private/var/folders",
    "/Volumes",
    "/Network",
)


def _resolved_directory(value: str, field_name: str) -> str:
    path = Path(value)
    if not value or not path.is_absolute() or not path.is_dir():
        raise ValueError("%s must contain existing absolute directories" % field_name)
    return str(path.resolve())


def _normalized_executable(value: str) -> str:
    path = Path(value)
    if not value or not path.is_absolute() or not path.is_file() or not os.access(str(path), os.X_OK):
        raise ValueError("allowed_executables must contain existing absolute executable files")
    return str(path)


def _path_within(path: Path, roots: Sequence[str]) -> bool:
    resolved = path.resolve()
    for root_value in roots:
        try:
            resolved.relative_to(Path(root_value))
            return True
        except ValueError:
            continue
    return False


@dataclass(frozen=True)
class HarnessIsolationPolicy:
    """Frozen macOS Seatbelt POC contract; not a production sandbox claim.

    The policy blocks direct network access, hides broad user/temp/volume roots
    except explicitly readable roots, permits writes only below explicit roots,
    and permits process execution only for an exact executable closure.  The
    backend is deprecated by macOS and therefore remains an R1-only adapter.
    """

    backend: HarnessIsolationBackend = HarnessIsolationBackend.MACOS_SEATBELT_R1
    readable_roots: Tuple[str, ...] = ()
    writable_roots: Tuple[str, ...] = ()
    allowed_executables: Tuple[str, ...] = ()
    deny_network: bool = True
    terminate_process_group: bool = True

    def __post_init__(self) -> None:
        backend = self.backend if isinstance(self.backend, HarnessIsolationBackend) \
            else HarnessIsolationBackend(str(self.backend))
        readable = tuple(dict.fromkeys(
            _resolved_directory(str(value), "readable_roots") for value in self.readable_roots
        ))
        writable = tuple(dict.fromkeys(
            _resolved_directory(str(value), "writable_roots") for value in self.writable_roots
        ))
        executable_values = []  # type: list[str]
        for value in self.allowed_executables:
            executable = _normalized_executable(str(value))
            executable_values.append(executable)
            resolved = str(Path(executable).resolve())
            if resolved != executable:
                executable_values.append(resolved)
        executables = tuple(dict.fromkeys(executable_values))
        if backend != HarnessIsolationBackend.MACOS_SEATBELT_R1:
            raise ValueError("unsupported harness isolation backend")
        if not readable or not executables:
            raise ValueError("Seatbelt isolation requires readable_roots and allowed_executables")
        if not self.deny_network or not self.terminate_process_group:
            raise ValueError("R1 Seatbelt policy requires network denial and process-group cleanup")
        unsafe_roots = {"/", "/Users", "/private", "/Volumes", "/Network"}
        if any(value in unsafe_roots for value in readable + writable):
            raise ValueError("isolation roots are too broad")
        object.__setattr__(self, "backend", backend)
        object.__setattr__(self, "readable_roots", readable)
        object.__setattr__(self, "writable_roots", writable)
        object.__setattr__(self, "allowed_executables", executables)

    def public_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend.value,
            "readable_roots": list(self.readable_roots),
            "writable_roots": list(self.writable_roots),
            "allowed_executables": list(self.allowed_executables),
            "deny_network": self.deny_network,
            "terminate_process_group": self.terminate_process_group,
        }

    @property
    def fingerprint(self) -> str:
        return content_hash(self.public_dict())

    def verify_effective(self) -> None:
        if sys.platform != "darwin":
            raise CapabilityRuntimeError("macOS Seatbelt isolation is unavailable on this platform")
        if not _SANDBOX_EXEC_PATH.is_file() or not os.access(str(_SANDBOX_EXEC_PATH), os.X_OK):
            raise CapabilityRuntimeError("macOS Seatbelt isolation backend is unavailable")
        for value in self.readable_roots + self.writable_roots:
            path = Path(value)
            if not path.is_dir() or str(path.resolve()) != value:
                raise CapabilityRuntimeError("isolation root changed after profile freeze")
        for value in self.allowed_executables:
            path = Path(value)
            if not path.is_file() or not os.access(str(path), os.X_OK):
                raise CapabilityRuntimeError("isolation executable changed after profile freeze")


def _seatbelt_profile(policy: HarnessIsolationPolicy) -> str:
    """Build a parameterized SBPL profile without interpolating path values."""

    lines = [
        "(version 1)",
        "(deny default)",
        "(allow process-fork)",
        "(allow signal (target same-sandbox))",
        "(allow process-info* (target same-sandbox))",
        "(allow sysctl-read)",
        "(allow ipc-posix-sem)",
        "(allow ipc-posix-shm)",
        "(allow mach-lookup (global-name \"com.apple.system.opendirectoryd.libinfo\"))",
        "(allow file-read-metadata)",
        "(allow file-read* (require-all %s))" % " ".join(
            "(require-not (subpath (param \"DENY_READ_%d\")))" % index
            for index, _ in enumerate(_SEATBELT_DENIED_READ_ROOTS)
        ),
        "(allow file-write-data (literal \"/dev/null\"))",
    ]
    lines.extend(
        "(allow process-exec (literal (param \"EXEC_%d\")))" % index
        for index, _ in enumerate(policy.allowed_executables)
    )
    lines.extend(
        "(allow file-read* (subpath (param \"READ_%d\")))" % index
        for index, _ in enumerate(policy.readable_roots)
    )
    lines.extend(
        "(allow file-read* (subpath (param \"WRITE_%d\")))" % index
        for index, _ in enumerate(policy.writable_roots)
    )
    lines.extend(
        "(allow file-write* (subpath (param \"WRITE_%d\")))" % index
        for index, _ in enumerate(policy.writable_roots)
    )
    lines.append("(deny network*)")
    return "\n".join(lines)


def _seatbelt_argv(policy: HarnessIsolationPolicy, argv: Sequence[str]) -> Tuple[str, ...]:
    parameters = []  # type: list[Tuple[str, str]]
    parameters.extend(
        ("DENY_READ_%d" % index, value)
        for index, value in enumerate(_SEATBELT_DENIED_READ_ROOTS)
    )
    parameters.extend(
        ("EXEC_%d" % index, value)
        for index, value in enumerate(policy.allowed_executables)
    )
    parameters.extend(
        ("READ_%d" % index, value)
        for index, value in enumerate(policy.readable_roots)
    )
    parameters.extend(
        ("WRITE_%d" % index, value)
        for index, value in enumerate(policy.writable_roots)
    )
    command = [str(_SANDBOX_EXEC_PATH)]
    for key, value in parameters:
        command.extend(("-D", "%s=%s" % (key, value)))
    command.extend(("-p", _seatbelt_profile(policy)))
    command.extend(str(value) for value in argv)
    return tuple(command)


def _terminate_process_group(process: subprocess.Popen, grace_seconds: float = 0.25) -> None:
    """Terminate the setsid-created group, then force-kill surviving descendants."""

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


class AttemptStage(str, Enum):
    DECLARED = "attempt_declared"
    STARTED = "execution_started"
    RAW_SEALED = "raw_output_sealed"
    PARSE_CLASSIFIED = "parse_classified"
    CANDIDATE_REGISTERED = "candidate_registered"
    TERMINAL = "attempt_terminal"


class CapabilityRuntimeError(RuntimeError):
    """Base fail-closed error for execution-profile or attempt mismatches."""


class StaleAttemptError(CapabilityRuntimeError):
    """Raised before dispatch when a request is bound to a stale manifest."""


class AttemptIdentityError(CapabilityRuntimeError):
    """Raised when an attempt id is reused for a different frozen request."""


class ApiTransport(Protocol):
    def __call__(
        self,
        request: Mapping[str, Any],
        profile: "ExecutionProfile",
    ) -> Mapping[str, Any]:
        ...


class AttemptJournal(Protocol):
    """Application-owned durable attempt boundary used before transport."""

    def declare_capability_attempt(self, **kwargs: Any) -> Mapping[str, Any]:
        ...

    def claim_capability_attempt(
        self,
        attempt_id: str,
        request_hash: str,
        owner_token: str,
        *,
        lease_seconds: float,
    ) -> Mapping[str, Any]:
        ...

    def interrupt_capability_attempt(
        self,
        attempt_id: str,
        request_hash: str,
        owner_token: str,
        *,
        reason: str,
    ) -> Mapping[str, Any]:
        ...

    def complete_capability_attempt(
        self,
        attempt_id: str,
        request_hash: str,
        owner_token: str,
        *,
        status: str,
        result: Mapping[str, Any],
        now_epoch: Optional[float] = None,
    ) -> Mapping[str, Any]:
        ...

    def get_capability_attempt(self, attempt_id: str) -> Optional[Mapping[str, Any]]:
        ...


class AttemptLifecycleObserver(Protocol):
    """Application-owned bridge from one durable attempt to its work unit.

    The runtime owns provider-neutral execution and the attempt journal.  The
    application controller owns user-visible progress and persistence.  These
    callbacks deliberately expose immutable request/result contracts instead
    of transport internals.
    """

    def on_attempt_prepared(
        self,
        request: "CapabilityRequest",
        *,
        replaying: bool,
    ) -> None:
        ...

    def on_attempt_terminal(self, result: "CapabilityAttemptResult") -> None:
        ...

    def on_attempt_interrupted(
        self,
        request: "CapabilityRequest",
        *,
        reason: str,
    ) -> None:
        ...


def _tuple(values: Optional[Iterable[str]]) -> Tuple[str, ...]:
    return tuple(str(value) for value in (values or ()))


def _file_sha256(path: Union[str, Path]) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class ExecutionProfile:
    """Frozen, user-selected execution configuration without secret values."""

    profile_id: str
    transport: TransportKind
    binding: ImmutableAdapterBinding
    api_route: str = ""
    argv: Tuple[str, ...] = ()
    working_directory: str = ""
    credential_ref: str = ""
    runtime_revision: str = ""
    environment_keys: Tuple[str, ...] = ()
    harness_isolation: Optional[HarnessIsolationPolicy] = None
    timeout_seconds: Optional[int] = None
    output_limit_chars: int = 120000
    schema_version: str = "mm-capability-r1"
    credential_ref_hash: str = field(init=False, repr=False)
    environment_values: Tuple[Tuple[str, str], ...] = field(init=False, repr=False)
    environment_value_hashes: Tuple[Tuple[str, str], ...] = field(init=False, repr=False)
    execution_file_hashes: Tuple[Tuple[str, str], ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise ValueError("execution profile_id is required")
        transport = self.transport if isinstance(self.transport, TransportKind) else TransportKind(str(self.transport))
        binding = freeze_binding(self.binding)
        argv = _tuple(self.argv)
        env_keys = _tuple(self.environment_keys)
        isolation = self.harness_isolation
        if isolation is not None and not isinstance(isolation, HarnessIsolationPolicy):
            raise ValueError("harness_isolation must be a HarnessIsolationPolicy")
        object.__setattr__(self, "transport", transport)
        object.__setattr__(self, "binding", binding)
        object.__setattr__(self, "argv", argv)
        object.__setattr__(self, "environment_keys", env_keys)
        object.__setattr__(self, "harness_isolation", isolation)
        object.__setattr__(
            self,
            "credential_ref_hash",
            content_hash({"credential_ref": self.credential_ref}) if self.credential_ref else "",
        )
        object.__setattr__(
            self,
            "environment_values",
            tuple((key, os.environ.get(key, "")) for key in env_keys),
        )
        object.__setattr__(
            self,
            "environment_value_hashes",
            tuple(
                (key, content_hash({"environment_value": os.environ.get(key, "<missing>")}))
                for key in env_keys
            ),
        )
        timeout = self.timeout_seconds or binding.timeout_seconds
        if timeout is not None and timeout <= 0:
            raise ValueError("execution timeout must be positive")
        object.__setattr__(self, "timeout_seconds", timeout)
        if self.output_limit_chars <= 0:
            raise ValueError("output_limit_chars must be positive")
        if not self.schema_version:
            raise ValueError("schema_version is required")
        if len(set(env_keys)) != len(env_keys):
            raise ValueError("environment_keys must be unique")
        if any(not key or "=" in key or "\x00" in key for key in env_keys):
            raise ValueError("environment_keys must be names, not assignments")
        if transport == TransportKind.API:
            if not self.api_route or argv:
                raise ValueError("API profile requires api_route and forbids argv")
            if isolation is not None:
                raise ValueError("API profile forbids harness_isolation")
            if binding.endpoint != "external":
                raise ValueError("API profile binding endpoint must be external")
            route = urlsplit(self.api_route)
            if route.query or route.fragment or route.username or route.password:
                raise ValueError("api_route may not contain query, fragment or user credentials")
            if not self.runtime_revision:
                raise ValueError("API profile requires an explicit runtime_revision")
        else:
            if self.api_route or not argv:
                raise ValueError("harness profile requires argv and forbids api_route")
            executable = Path(argv[0])
            if not executable.is_absolute():
                raise ValueError("harness executable must be an absolute path")
            if any("\x00" in arg for arg in argv):
                raise ValueError("harness argv may not contain NUL")
            working_directory = Path(self.working_directory)
            if not self.working_directory or not working_directory.is_absolute():
                raise ValueError("harness working_directory must be a non-empty absolute directory")
            if not working_directory.is_dir():
                raise ValueError("harness working_directory must exist and be a directory")
            object.__setattr__(self, "working_directory", str(working_directory.resolve()))
            if binding.endpoint != "local":
                raise ValueError("harness profile binding endpoint must be local")
            if isolation is not None:
                isolation.verify_effective()
                allowed_roots = isolation.readable_roots + isolation.writable_roots
                if not _path_within(working_directory, allowed_roots):
                    raise ValueError(
                        "isolated harness working_directory must be inside a declared root"
                    )
                executable_values = set(isolation.allowed_executables)
                executable = str(Path(argv[0]))
                if executable not in executable_values \
                        and str(Path(executable).resolve()) not in executable_values:
                    raise ValueError(
                        "isolated harness executable must be in allowed_executables"
                    )
                for argument in argv[1:]:
                    argument_path = Path(argument)
                    if argument_path.is_absolute() \
                            and not _path_within(argument_path, allowed_roots) \
                            and str(argument_path) not in executable_values \
                            and str(argument_path.resolve()) not in executable_values:
                        raise ValueError(
                            "isolated harness absolute argv paths must be inside declared roots"
                        )

        execution_files = [
            arg for arg in argv if Path(arg).is_absolute() and Path(arg).is_file()
        ]
        if isolation is not None:
            execution_files.extend(isolation.allowed_executables)
            execution_files.append(str(_SANDBOX_EXEC_PATH))
        object.__setattr__(
            self,
            "execution_file_hashes",
            tuple(
                (path, _file_sha256(path))
                for path in dict.fromkeys(execution_files)
            ),
        )

    @property
    def fingerprint(self) -> str:
        return content_hash(self.public_dict())

    def public_dict(self) -> Dict[str, Any]:
        """Persistable profile view; credential reference value is excluded."""

        return {
            "profile_id": self.profile_id,
            "transport": self.transport.value,
            "binding": self.binding.to_dict(),
            "api_route": self.api_route,
            "argv_executable": self.argv[0] if self.argv else "",
            "argv_argument_hashes": [content_hash({"argument": item}) for item in self.argv[1:]],
            "argv_argument_count": max(0, len(self.argv) - 1),
            "working_directory": self.working_directory,
            "credential_ref_present": bool(self.credential_ref),
            "credential_ref_hash": self.credential_ref_hash,
            "runtime_revision": self.runtime_revision,
            "environment_keys": list(self.environment_keys),
            "environment_value_hashes": dict(self.environment_value_hashes),
            "execution_file_hashes": dict(self.execution_file_hashes),
            "harness_isolation": (
                self.harness_isolation.public_dict() if self.harness_isolation else None
            ),
            "timeout_seconds": self.timeout_seconds,
            "output_limit_chars": self.output_limit_chars,
            "schema_version": self.schema_version,
        }

    def verify_effective_identity(self) -> None:
        if self.transport == TransportKind.HARNESS:
            working_directory = Path(self.working_directory)
            if not working_directory.is_absolute() or not working_directory.is_dir():
                raise CapabilityRuntimeError(
                    "harness working_directory is no longer an existing absolute directory"
                )
            if self.harness_isolation is not None:
                self.harness_isolation.verify_effective()
        current_environment = tuple(
            (key, content_hash({"environment_value": os.environ.get(key, "<missing>")}))
            for key in self.environment_keys
        )
        if current_environment != self.environment_value_hashes:
            raise CapabilityRuntimeError("allowlisted environment values changed after profile freeze")
        for path, expected in self.execution_file_hashes:
            if not Path(path).is_file() or _file_sha256(path) != expected:
                raise CapabilityRuntimeError("harness execution file changed after profile freeze")

    def response_identity(self) -> Dict[str, str]:
        return {
            "profile_fingerprint": self.fingerprint,
            "binding_id": self.binding.binding_id,
            "provider": self.binding.provider,
            "model": self.binding.model,
            "selector": self.binding.selector,
            "adapter_version": self.binding.adapter_version,
        }

    def execution_environment(self) -> Dict[str, str]:
        """Return the in-memory frozen allowlist; values are never persisted."""

        return dict(self.environment_values)


@dataclass(frozen=True)
class InvocationVersions:
    source_revision_id: str
    rule_version: str
    knowledge_version: str
    graph_version: str
    schema_version: str
    mapping_version: str = ""

    def __post_init__(self) -> None:
        required = (
            self.source_revision_id,
            self.rule_version,
            self.knowledge_version,
            self.graph_version,
            self.schema_version,
        )
        if any(not value for value in required):
            raise ValueError("source/rule/knowledge/graph/schema versions are required")

    def to_dict(self) -> Dict[str, str]:
        return {
            "source_revision_id": self.source_revision_id,
            "rule_version": self.rule_version,
            "knowledge_version": self.knowledge_version,
            "graph_version": self.graph_version,
            "schema_version": self.schema_version,
            "mapping_version": self.mapping_version,
        }


@dataclass(frozen=True)
class CapabilityRequest:
    attempt_id: str
    monitoring_run_id: str
    node_id: str
    manifest_revision: int
    profile_fingerprint: str
    binding: ImmutableAdapterBinding
    versions: InvocationVersions
    input_hash: str
    payload: Any
    expected_units: Tuple[CoverageUnit, ...]
    continued_from: str = ""

    @classmethod
    def build(
        cls,
        *,
        attempt_id: str,
        monitoring_run_id: str,
        node_id: str,
        manifest_revision: int,
        profile: ExecutionProfile,
        versions: InvocationVersions,
        payload: Any,
        expected_units: Sequence[Union[CoverageUnit, Mapping[str, Any], str]],
        continued_from: str = "",
    ) -> "CapabilityRequest":
        if not attempt_id or not monitoring_run_id or not node_id:
            raise ValueError("attempt_id, monitoring_run_id and node_id are required")
        if manifest_revision < 1:
            raise ValueError("manifest_revision must be at least 1")
        units = tuple(_coerce_coverage_unit(item) for item in expected_units)
        if not units:
            raise ValueError("expected coverage denominator is required")
        if any(
            not unit.expected or unit.status is not None or unit.reason is not None
            for unit in units
        ):
            raise ValueError(
                "expected coverage denominator may contain only scope/key; status and reason belong to produced coverage"
            )
        detached_payload = json.loads(canonical_json(payload))
        input_hash = content_hash(
            {
                "monitoring_run_id": monitoring_run_id,
                "node_id": node_id,
                "manifest_revision": manifest_revision,
                "profile_fingerprint": profile.fingerprint,
                "versions": versions.to_dict(),
                "payload": detached_payload,
                "expected_units": [unit.__dict__ for unit in units],
            }
        )
        return cls(
            attempt_id=attempt_id,
            monitoring_run_id=monitoring_run_id,
            node_id=node_id,
            manifest_revision=manifest_revision,
            profile_fingerprint=profile.fingerprint,
            binding=profile.binding.with_input_hash(input_hash),
            versions=versions,
            input_hash=input_hash,
            payload=detached_payload,
            expected_units=units,
            continued_from=continued_from,
        )

    @property
    def request_hash(self) -> str:
        return content_hash(self.to_jsonrpc())

    def identity_dict(self) -> Dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "monitoring_run_id": self.monitoring_run_id,
            "node_id": self.node_id,
            "manifest_revision": self.manifest_revision,
            "profile_fingerprint": self.profile_fingerprint,
            "binding_id": self.binding.binding_id,
            "input_hash": self.input_hash,
            "versions": self.versions.to_dict(),
            "expected_units": [unit.__dict__.copy() for unit in self.expected_units],
            "continued_from": self.continued_from,
            "request_hash": self.request_hash,
        }

    def to_jsonrpc(self) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": self.attempt_id,
            "method": "medical_monitoring.analyze",
            "params": {
                "monitoring_run_id": self.monitoring_run_id,
                "node_id": self.node_id,
                "manifest_revision": self.manifest_revision,
                "profile_fingerprint": self.profile_fingerprint,
                "binding": self.binding.to_dict(),
                "execution_identity": {
                    "profile_fingerprint": self.profile_fingerprint,
                    "binding_id": self.binding.binding_id,
                    "provider": self.binding.provider,
                    "model": self.binding.model,
                    "selector": self.binding.selector,
                    "adapter_version": self.binding.adapter_version,
                },
                "versions": self.versions.to_dict(),
                "input_hash": self.input_hash,
                "input": self.payload,
                "expected_coverage": [unit.__dict__.copy() for unit in self.expected_units],
                "continued_from": self.continued_from or None,
            },
        }


@dataclass(frozen=True)
class AdapterWorkEvent:
    sequence: int
    attempt_id: str
    stage: AttemptStage
    status: str
    detail: str
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.sequence < 1 or not self.attempt_id:
            raise ValueError("work event requires positive sequence and attempt_id")
        stage = self.stage if isinstance(self.stage, AttemptStage) else AttemptStage(str(self.stage))
        object.__setattr__(self, "stage", stage)
        if not self.created_at:
            object.__setattr__(self, "created_at", now_iso())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence": self.sequence,
            "attempt_id": self.attempt_id,
            "stage": self.stage.value,
            "status": self.status,
            "detail": self.detail,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class TransportExecution:
    raw_output: Any = None
    stdout: str = ""
    stderr: str = ""
    return_code: Optional[int] = None
    timed_out: bool = False
    cancelled: bool = False
    output_truncated: bool = False
    execution_id: str = ""
    failure_reason: str = ""
    isolation_backend: str = ""
    isolation_policy_fingerprint: str = ""


@dataclass(frozen=True)
class CapabilityAttemptResult:
    profile: ExecutionProfile
    request: CapabilityRequest
    adapter_run: AdapterRun
    work_events: Tuple[AdapterWorkEvent, ...]
    transport_execution: TransportExecution

    @property
    def status(self) -> AdapterState:
        return self.adapter_run.status


@dataclass(frozen=True)
class CapabilityPersistenceReceipt:
    adapter: AdapterPersistenceReceipt
    profile_version: int
    request_version: int
    work_event_versions: Tuple[int, ...]


def _attempt_result_payload(result: CapabilityAttemptResult) -> Dict[str, Any]:
    """Canonical JSON payload for immutable cross-process replay."""

    return {
        "adapter_run": to_jsonable(result.adapter_run),
        "work_events": [item.to_dict() for item in result.work_events],
        "transport_execution": to_jsonable(result.transport_execution),
    }


def _attempt_result_from_payload(
    profile: ExecutionProfile,
    request: CapabilityRequest,
    payload: Mapping[str, Any],
) -> CapabilityAttemptResult:
    adapter_run = from_jsonable(AdapterRun, payload.get("adapter_run"))
    if not isinstance(adapter_run, AdapterRun):
        raise CapabilityRuntimeError("journaled adapter result is not reconstructable")
    events = tuple(
        AdapterWorkEvent(
            sequence=int(item["sequence"]),
            attempt_id=str(item["attempt_id"]),
            stage=AttemptStage(str(item["stage"])),
            status=str(item.get("status", "")),
            detail=str(item.get("detail", "")),
            created_at=str(item.get("created_at", "")),
        )
        for item in payload.get("work_events", ())
    )
    transport = from_jsonable(TransportExecution, payload.get("transport_execution", {}))
    if not isinstance(transport, TransportExecution):
        raise CapabilityRuntimeError("journaled transport result is not reconstructable")
    if adapter_run.run_id != request.attempt_id:
        raise CapabilityRuntimeError("journaled result attempt identity mismatch")
    return CapabilityAttemptResult(
        profile=profile,
        request=request,
        adapter_run=adapter_run,
        work_events=events,
        transport_execution=transport,
    )


class CapabilityRuntime:
    """Shared lifecycle; subclasses provide only the transport execution."""

    raw_source = "capability_transport"

    def __init__(
        self,
        profile: ExecutionProfile,
        *,
        manifest_revision_reader: Optional[Callable[[str], int]] = None,
        attempt_journal: Optional[AttemptJournal] = None,
        journal_owner_token: str = "",
        journal_lease_seconds: Optional[float] = None,
    ) -> None:
        if manifest_revision_reader is None:
            raise ValueError("authoritative manifest_revision_reader is required")
        self.profile = profile
        self._manifest_revision_reader = manifest_revision_reader
        runtime_journal_factory = (
            getattr(attempt_journal, "_runtime_attempt_journal", None)
            if attempt_journal is not None else None
        )
        self._attempt_journal = (
            runtime_journal_factory()
            if callable(runtime_journal_factory) else attempt_journal
        )
        self._journal_owner_token = journal_owner_token or uuid.uuid4().hex
        derived_lease = max(float(profile.timeout_seconds or 300) + 10.0, 30.0)
        self._journal_lease_seconds = float(journal_lease_seconds or derived_lease)
        if self._journal_lease_seconds <= 0:
            raise ValueError("journal lease must be positive")
        self._attempts: Dict[str, CapabilityAttemptResult] = {}
        self._request_hashes: Dict[str, str] = {}
        self._inflight = set()  # type: set[str]
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)

    @property
    def attempts(self) -> Tuple[CapabilityAttemptResult, ...]:
        with self._lock:
            return tuple(self._attempts.values())

    def _manifest_revision(self, run_id: str, declared: int) -> int:
        return int(self._manifest_revision_reader(run_id))

    def _execute(self, request: CapabilityRequest) -> TransportExecution:
        raise NotImplementedError

    def cancel(self, attempt_id: str) -> bool:
        """Common lifecycle surface; transport runtimes override when active."""

        return False

    def _prepare_durable_attempt(
        self,
        request: CapabilityRequest,
    ) -> Optional[CapabilityAttemptResult]:
        if self._attempt_journal is None:
            return None
        entry = self._attempt_journal.declare_capability_attempt(
            attempt_id=request.attempt_id,
            run_id=request.monitoring_run_id,
            node_id=request.node_id,
            request_hash=request.request_hash,
            request=request.to_jsonrpc(),
            profile_fingerprint=request.profile_fingerprint,
            manifest_revision=request.manifest_revision,
            input_hash=request.input_hash,
            continued_from=request.continued_from,
        )
        if bool(entry.get("terminal")):
            result_payload = entry.get("result")
            if not isinstance(result_payload, Mapping):
                raise CapabilityRuntimeError("terminal journal entry has no immutable result")
            return _attempt_result_from_payload(self.profile, request, result_payload)
        claimed = self._attempt_journal.claim_capability_attempt(
            request.attempt_id,
            request.request_hash,
            self._journal_owner_token,
            lease_seconds=self._journal_lease_seconds,
        )
        if bool(claimed.get("terminal")):
            result_payload = claimed.get("result")
            if not isinstance(result_payload, Mapping):
                raise CapabilityRuntimeError("terminal journal entry has no immutable result")
            return _attempt_result_from_payload(self.profile, request, result_payload)
        if claimed.get("status") == "interrupted":
            raise CapabilityRuntimeError(
                "interrupted attempt cannot be redispatched under the same id; resume with a new attempt id"
            )
        if claimed.get("status") != "running" \
                or claimed.get("owner_token") != self._journal_owner_token:
            raise CapabilityRuntimeError("durable attempt was not claimed by this runtime")
        return None

    def _complete_durable_attempt(
        self,
        request: CapabilityRequest,
        result: CapabilityAttemptResult,
    ) -> None:
        if self._attempt_journal is None:
            return
        self._attempt_journal.complete_capability_attempt(
            request.attempt_id,
            request.request_hash,
            self._journal_owner_token,
            status=result.status.value,
            result=_attempt_result_payload(result),
        )

    def _interrupt_durable_attempt(self, request: CapabilityRequest, reason: str) -> None:
        if self._attempt_journal is None:
            return
        try:
            self._attempt_journal.interrupt_capability_attempt(
                request.attempt_id,
                request.request_hash,
                self._journal_owner_token,
                reason=reason,
            )
        except Exception:
            pass

    def invoke(
        self,
        *,
        attempt_id: str,
        monitoring_run_id: str,
        node_id: str,
        manifest_revision: int,
        versions: InvocationVersions,
        payload: Any,
        expected_units: Sequence[Union[CoverageUnit, Mapping[str, Any], str]],
        continued_from: str = "",
        lifecycle_observer: Optional[AttemptLifecycleObserver] = None,
    ) -> CapabilityAttemptResult:
        self.profile.verify_effective_identity()
        request = CapabilityRequest.build(
            attempt_id=attempt_id,
            monitoring_run_id=monitoring_run_id,
            node_id=node_id,
            manifest_revision=manifest_revision,
            profile=self.profile,
            versions=versions,
            payload=payload,
            expected_units=expected_units,
            continued_from=continued_from,
        )
        cached_result = None  # type: Optional[CapabilityAttemptResult]
        with self._condition:
            prior_hash = self._request_hashes.get(attempt_id)
            if prior_hash is not None:
                if prior_hash != request.request_hash:
                    raise AttemptIdentityError("attempt_id already belongs to a different frozen request")
                while attempt_id in self._inflight:
                    self._condition.wait()
                if attempt_id not in self._attempts:
                    raise CapabilityRuntimeError("prior execution failed before producing an immutable result")
                cached_result = self._attempts[attempt_id]
            else:
                current_revision = self._manifest_revision(monitoring_run_id, manifest_revision)
                if current_revision != manifest_revision:
                    raise StaleAttemptError("manifest revision changed before adapter dispatch")
                self._request_hashes[attempt_id] = request.request_hash
                self._inflight.add(attempt_id)

        if cached_result is not None:
            if lifecycle_observer is not None:
                lifecycle_observer.on_attempt_prepared(request, replaying=True)
                lifecycle_observer.on_attempt_terminal(cached_result)
            return cached_result

        try:
            replay = self._prepare_durable_attempt(request)
            if lifecycle_observer is not None:
                lifecycle_observer.on_attempt_prepared(
                    request,
                    replaying=replay is not None,
                )
            result = replay if replay is not None else self._invoke_new(request)
            if replay is None:
                self._complete_durable_attempt(request, result)
            if lifecycle_observer is not None:
                lifecycle_observer.on_attempt_terminal(result)
        except Exception as exc:
            reason = "runtime exception: %s" % exc
            self._interrupt_durable_attempt(request, reason)
            if lifecycle_observer is not None:
                try:
                    lifecycle_observer.on_attempt_interrupted(request, reason=reason)
                except Exception:
                    # Preserve the initiating failure.  A durable assignment
                    # can be reconciled by the application after restart.
                    pass
            with self._condition:
                self._inflight.discard(attempt_id)
                self._request_hashes.pop(attempt_id, None)
                self._condition.notify_all()
            raise
        with self._condition:
            self._attempts[attempt_id] = result
            self._inflight.discard(attempt_id)
            self._condition.notify_all()
        return result

    def _invoke_new(self, request: CapabilityRequest) -> CapabilityAttemptResult:
        attempt_id = request.attempt_id
        monitoring_run_id = request.monitoring_run_id
        manifest_revision = request.manifest_revision

        events = []  # type: list[AdapterWorkEvent]

        def event(stage: AttemptStage, status: str, detail: str) -> None:
            events.append(AdapterWorkEvent(len(events) + 1, attempt_id, stage, status, detail))

        event(AttemptStage.DECLARED, "ready", "执行档案、输入版本与覆盖分母已冻结")
        started = _start_adapter_run(request)
        event(AttemptStage.STARTED, "running", "执行端已启动")
        try:
            execution = self._execute(request)
        except Exception as exc:  # transport failures are classified, never promoted
            execution = TransportExecution(failure_reason="transport error: %s" % exc)

        if execution.raw_output is None:
            # Terminal journal/work-unit validation requires sealed evidence
            # even when a provider returns no body.  Persist a bounded
            # transport outcome rather than leaving a successful-looking gap.
            execution = replace(
                execution,
                raw_output={
                    "execution_id": execution.execution_id,
                    "return_code": execution.return_code,
                    "timed_out": execution.timed_out,
                    "cancelled": execution.cancelled,
                    "output_truncated": execution.output_truncated,
                    "failure_reason": execution.failure_reason
                    or "transport returned no response body",
                    "isolation_backend": execution.isolation_backend,
                    "isolation_policy_fingerprint": (
                        execution.isolation_policy_fingerprint
                    ),
                },
            )

        if execution.raw_output is not None:
            event(AttemptStage.RAW_SEALED, "sealed", "原始输出已内容寻址封存")
        normalized = _normalize_transport_result(request, execution)

        post_revision = self._manifest_revision(monitoring_run_id, manifest_revision)
        if post_revision != manifest_revision:
            normalized = ScriptedOutput(
                status=AdapterState.FAILED,
                raw_output=normalized.raw_output,
                failure_reason="stale manifest revision after transport completion",
                expected_units=request.expected_units,
                produced_units=(),
            )
        event(AttemptStage.PARSE_CLASSIFIED, normalized.status.value, normalized.failure_reason or "输出已分类")
        completed = _finish_adapter_run(started, normalized, source=self.raw_source)
        if completed.candidate_artifact is not None:
            event(AttemptStage.CANDIDATE_REGISTERED, "candidate_only", "候选结果已登记；未晋升医学事实")
        event(AttemptStage.TERMINAL, completed.status.value, completed.failure_reason or "执行已结束")
        result = CapabilityAttemptResult(
            profile=self.profile,
            request=request,
            adapter_run=completed,
            work_events=tuple(events),
            transport_execution=execution,
        )
        return result

    def resume(
        self,
        previous_attempt_id: str,
        *,
        attempt_id: str,
        manifest_revision: int,
        lifecycle_observer: Optional[AttemptLifecycleObserver] = None,
    ) -> CapabilityAttemptResult:
        with self._lock:
            previous = self._attempts.get(previous_attempt_id)
        journal_entry = None
        if self._attempt_journal is not None:
            journal_entry = self._attempt_journal.get_capability_attempt(previous_attempt_id)
            if journal_entry is None and previous is not None:
                raise CapabilityRuntimeError(
                    "cached attempt is missing from the configured durable journal"
                )
        if previous is None and journal_entry is None:
            raise KeyError("unknown adapter attempt: %s" % previous_attempt_id)
        if journal_entry is None and previous is not None:
            previous_status = previous.status.value
            req = previous.request
            versions = req.versions
            payload = req.payload
            expected_units = req.expected_units
            stored_input_hash = req.input_hash
            monitoring_run_id = req.monitoring_run_id
            node_id = req.node_id
            stored_manifest_revision = req.manifest_revision
        else:
            previous_status = str(journal_entry.get("status", ""))
            if journal_entry.get("profile_fingerprint") != self.profile.fingerprint:
                raise AttemptIdentityError("resume profile fingerprint changed")
            rpc = journal_entry.get("request")
            if not isinstance(rpc, Mapping) or rpc.get("id") != previous_attempt_id:
                raise CapabilityRuntimeError("journaled resume request is invalid")
            params = rpc.get("params")
            if not isinstance(params, Mapping):
                raise CapabilityRuntimeError("journaled resume params are invalid")
            versions = InvocationVersions(**dict(params.get("versions", {})))
            payload = params.get("input")
            expected_units = tuple(
                _coerce_coverage_unit(item) for item in params.get("expected_coverage", ())
            )
            stored_input_hash = str(journal_entry.get("input_hash", ""))
            monitoring_run_id = str(journal_entry.get("run_id", ""))
            node_id = str(journal_entry.get("node_id", ""))
            stored_manifest_revision = int(journal_entry.get("manifest_revision", 0))
        if previous_status not in (
            AdapterState.TIMEOUT.value,
            AdapterState.PARTIAL.value,
            AdapterState.TRUNCATED.value,
            "interrupted",
        ):
            raise CapabilityRuntimeError("only timeout, partial or truncated attempts may resume")
        if manifest_revision != stored_manifest_revision:
            raise AttemptIdentityError("resume must use the original manifest revision")
        if self._manifest_revision(monitoring_run_id, manifest_revision) != manifest_revision:
            raise StaleAttemptError("manifest revision changed before resume")
        prospective = CapabilityRequest.build(
            attempt_id=attempt_id,
            monitoring_run_id=monitoring_run_id,
            node_id=node_id,
            manifest_revision=manifest_revision,
            profile=self.profile,
            versions=versions,
            payload=payload,
            expected_units=expected_units,
            continued_from=previous_attempt_id,
        )
        if prospective.input_hash != stored_input_hash:
            raise AttemptIdentityError("resume input/version/profile identity changed")
        return self.invoke(
            attempt_id=attempt_id,
            monitoring_run_id=monitoring_run_id,
            node_id=node_id,
            manifest_revision=manifest_revision,
            versions=versions,
            payload=payload,
            expected_units=expected_units,
            continued_from=previous_attempt_id,
            lifecycle_observer=lifecycle_observer,
        )


class ApiCapabilityRuntime(CapabilityRuntime):
    raw_source = "api_transport"

    def __init__(
        self,
        profile: ExecutionProfile,
        transport: ApiTransport,
        *,
        manifest_revision_reader: Optional[Callable[[str], int]] = None,
        attempt_journal: Optional[AttemptJournal] = None,
        journal_owner_token: str = "",
        journal_lease_seconds: Optional[float] = None,
    ) -> None:
        if profile.transport != TransportKind.API:
            raise ValueError("ApiCapabilityRuntime requires an API profile")
        super().__init__(
            profile,
            manifest_revision_reader=manifest_revision_reader,
            attempt_journal=attempt_journal,
            journal_owner_token=journal_owner_token,
            journal_lease_seconds=journal_lease_seconds,
        )
        self._transport = transport
        self._active_api = {}  # type: Dict[str, Tuple[threading.Event, threading.Event]]
        self._api_cancelled = set()  # type: set[str]

    def _cancel_transport(self, attempt_id: str) -> None:
        cancel = getattr(self._transport, "cancel", None)
        if callable(cancel):
            try:
                cancel(attempt_id)
            except Exception:
                pass

    def cancel(self, attempt_id: str) -> bool:
        with self._lock:
            active = self._active_api.get(attempt_id)
            if active is None:
                return False
            wake, cancel_event = active
            self._api_cancelled.add(attempt_id)
            cancel_event.set()
            wake.set()
        self._cancel_transport(attempt_id)
        return True

    def _execute(self, request: CapabilityRequest) -> TransportExecution:
        wake = threading.Event()
        cancel_event = threading.Event()
        box = {}  # type: Dict[str, Any]

        def run_transport() -> None:
            try:
                box["response"] = self._transport(request.to_jsonrpc(), self.profile)
            except Exception as exc:
                box["error"] = exc
            finally:
                box["done"] = True
                wake.set()

        with self._lock:
            self._active_api[request.attempt_id] = (wake, cancel_event)
        thread = threading.Thread(target=run_transport, daemon=True)
        thread.start()
        timeout = self.profile.timeout_seconds
        completed = wake.wait(timeout=timeout)
        with self._lock:
            cancelled = request.attempt_id in self._api_cancelled or cancel_event.is_set()
            self._active_api.pop(request.attempt_id, None)
        if cancelled:
            return TransportExecution(cancelled=True, failure_reason="API execution cancelled")
        if not completed or not box.get("done"):
            self._cancel_transport(request.attempt_id)
            return TransportExecution(timed_out=True, failure_reason="API execution timeout")
        if "error" in box:
            return TransportExecution(failure_reason="transport error: %s" % box["error"])
        detached = json.loads(canonical_json(box.get("response")))
        return TransportExecution(raw_output=detached, execution_id=str(detached.get("execution_id", "")))


class HarnessCapabilityRuntime(CapabilityRuntime):
    raw_source = "harness_process"

    def __init__(
        self,
        profile: ExecutionProfile,
        *,
        manifest_revision_reader: Optional[Callable[[str], int]] = None,
        attempt_journal: Optional[AttemptJournal] = None,
        journal_owner_token: str = "",
        journal_lease_seconds: Optional[float] = None,
    ) -> None:
        if profile.transport != TransportKind.HARNESS:
            raise ValueError("HarnessCapabilityRuntime requires a harness profile")
        super().__init__(
            profile,
            manifest_revision_reader=manifest_revision_reader,
            attempt_journal=attempt_journal,
            journal_owner_token=journal_owner_token,
            journal_lease_seconds=journal_lease_seconds,
        )
        self._active: Dict[str, subprocess.Popen] = {}
        self._cancelled = set()  # type: set[str]

    def cancel(self, attempt_id: str) -> bool:
        with self._lock:
            process = self._active.get(attempt_id)
        if process is None or process.poll() is not None:
            return False
        with self._lock:
            self._cancelled.add(attempt_id)
        _terminate_process_group(process)
        return True

    def _execute(self, request: CapabilityRequest) -> TransportExecution:
        environment = self.profile.execution_environment()
        isolation = self.profile.harness_isolation
        command = (
            _seatbelt_argv(isolation, self.profile.argv)
            if isolation is not None else self.profile.argv
        )
        process = subprocess.Popen(
            list(command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            cwd=self.profile.working_directory,
            env=environment,
            shell=False,
            close_fds=True,
            start_new_session=True,
        )
        with self._lock:
            self._active[request.attempt_id] = process
        timed_out = False
        try:
            stdout, stderr = process.communicate(
                canonical_json(request.to_jsonrpc()),
                timeout=self.profile.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_process_group(process)
            stdout, stderr = process.communicate()
        finally:
            with self._lock:
                self._active.pop(request.attempt_id, None)
                cancelled = request.attempt_id in self._cancelled
        output_truncated = len(stdout) > self.profile.output_limit_chars
        bounded_stdout = stdout[: self.profile.output_limit_chars]
        bounded_stderr = stderr[: self.profile.output_limit_chars]
        raw = {
            "stdout": stdout,
            "stderr": stderr,
            "return_code": process.returncode,
            "timed_out": timed_out,
            "cancelled": cancelled,
            "output_truncated": output_truncated,
            "stdout_chars": len(stdout),
            "stderr_chars": len(stderr),
            "isolation_backend": isolation.backend.value if isolation else "",
            "isolation_policy_fingerprint": isolation.fingerprint if isolation else "",
        }
        return TransportExecution(
            raw_output=raw,
            stdout=bounded_stdout,
            stderr=bounded_stderr,
            return_code=process.returncode,
            timed_out=timed_out,
            cancelled=cancelled,
            output_truncated=output_truncated,
            failure_reason=("harness timeout" if timed_out else "harness cancelled" if cancelled else ""),
            isolation_backend=isolation.backend.value if isolation else "",
            isolation_policy_fingerprint=isolation.fingerprint if isolation else "",
        )


def _start_adapter_run(request: CapabilityRequest) -> AdapterRun:
    analysis = ModelAnalysis(
        analysis_id=request.attempt_id,
        binding_id=request.binding.binding_id,
        run_id=request.monitoring_run_id,
        node_id=request.node_id,
        input_hash=request.input_hash,
        parse_state=AdapterState.RUNNING.value,
        created_at=now_iso(),
    )
    return AdapterRun(
        run_id=request.attempt_id,
        binding=request.binding,
        status=AdapterState.RUNNING,
        analysis=analysis,
        monitoring_run_id=request.monitoring_run_id,
        node_id=request.node_id,
        independent=True,
        continued_from=request.continued_from or None,
        created_at=analysis.created_at,
    )


def _finish_adapter_run(current: AdapterRun, output: ScriptedOutput, *, source: str) -> AdapterRun:
    raw = _make_raw_provenance(current, output.raw_output, source=source)
    coverage = _make_coverage(output.expected_units, output.produced_units)
    status = _resolve_status(output.status, coverage, raw)
    candidate = None
    if output.payload is not None:
        candidate = _make_candidate_artifact(current, output, raw, coverage, status)
    analysis = replace(
        current.analysis,
        raw_output_ref=raw.raw_output_ref if raw is not None else "",
        parse_state=status.value,
        coverage=coverage,
        failure_reason=output.failure_reason,
    )
    return replace(
        current,
        status=status,
        analysis=analysis,
        raw_output=raw,
        coverage=coverage,
        candidate_artifact=candidate,
        failure_reason=output.failure_reason,
        finished_at=now_iso(),
    )


def _decode_response(execution: TransportExecution) -> Tuple[Optional[Mapping[str, Any]], str]:
    if execution.stdout:
        try:
            parsed = json.loads(execution.stdout)
        except Exception as exc:
            return None, "harness stdout is not valid JSON: %s" % exc
        if not isinstance(parsed, Mapping):
            return None, "harness response must be a JSON object"
        return parsed, ""
    if isinstance(execution.raw_output, Mapping):
        return execution.raw_output, ""
    return None, execution.failure_reason or "transport returned no response"


def _normalize_transport_result(request: CapabilityRequest, execution: TransportExecution) -> ScriptedOutput:
    raw = execution.raw_output
    if execution.cancelled:
        return ScriptedOutput(
            status=AdapterState.CANCELLED,
            raw_output=raw,
            failure_reason=execution.failure_reason or "harness cancelled",
            expected_units=request.expected_units,
        )
    if execution.timed_out:
        return ScriptedOutput(
            status=AdapterState.TIMEOUT,
            raw_output=raw,
            failure_reason=execution.failure_reason or "adapter timeout",
            expected_units=request.expected_units,
        )
    if execution.output_truncated:
        return ScriptedOutput(
            status=AdapterState.TRUNCATED,
            raw_output=raw,
            failure_reason="transport output exceeded configured limit",
            expected_units=request.expected_units,
        )
    if execution.return_code not in (None, 0):
        return ScriptedOutput(
            status=AdapterState.FAILED,
            raw_output=raw,
            failure_reason="harness exited with code %s" % execution.return_code,
            expected_units=request.expected_units,
        )
    response, error = _decode_response(execution)
    if response is None:
        return ScriptedOutput(
            status=AdapterState.FAILED,
            raw_output=raw,
            failure_reason=error,
            expected_units=request.expected_units,
        )
    if response.get("jsonrpc") != "2.0" or response.get("id") != request.attempt_id:
        return ScriptedOutput(
            status=AdapterState.FAILED,
            raw_output=raw,
            failure_reason="response id or JSON-RPC version does not match request",
            expected_units=request.expected_units,
        )
    if response.get("error") is not None:
        err = response.get("error")
        reason = err.get("message", "transport error") if isinstance(err, Mapping) else str(err)
        return ScriptedOutput(
            status=AdapterState.FAILED,
            raw_output=raw,
            failure_reason=reason,
            expected_units=request.expected_units,
        )
    result = response.get("result")
    if not isinstance(result, Mapping):
        return ScriptedOutput(
            status=AdapterState.FAILED,
            raw_output=raw,
            failure_reason="response result must be an object",
            expected_units=request.expected_units,
        )
    expected_identity = {
        "profile_fingerprint": request.profile_fingerprint,
        "binding_id": request.binding.binding_id,
        "provider": request.binding.provider,
        "model": request.binding.model,
        "selector": request.binding.selector,
        "adapter_version": request.binding.adapter_version,
    }
    if result.get("execution_identity") != expected_identity:
        return ScriptedOutput(
            status=AdapterState.FAILED,
            raw_output=raw,
            failure_reason="response execution identity does not match frozen profile",
            expected_units=request.expected_units,
        )
    try:
        status = AdapterState(str(result.get("status", AdapterState.COMPLETE.value)))
        if status in (AdapterState.CONFIGURED, AdapterState.RUNNING):
            raise ValueError("transport response must be terminal")
        produced_raw = tuple(result.get("produced_units", ()))
        if any(not isinstance(item, Mapping) or not item.get("status") for item in produced_raw):
            raise ValueError("every produced coverage unit requires an explicit status")
        produced = tuple(_coerce_coverage_unit(item) for item in produced_raw)
    except Exception as exc:
        return ScriptedOutput(
            status=AdapterState.FAILED,
            raw_output=raw,
            failure_reason="response classification failed: %s" % exc,
            expected_units=request.expected_units,
        )
    if status == AdapterState.COMPLETE:
        expected_keys = {(unit.scope, unit.key) for unit in request.expected_units}
        produced_keys = [(unit.scope, unit.key) for unit in produced]
        statuses = {unit.status for unit in produced}
        if set(produced_keys) != expected_keys or len(produced_keys) != len(expected_keys):
            status = AdapterState.PARTIAL
        elif statuses != {CoverageUnitStatus.COVERED}:
            if CoverageUnitStatus.TRUNCATED in statuses:
                status = AdapterState.TRUNCATED
            elif CoverageUnitStatus.FAILED in statuses:
                status = AdapterState.FAILED
            else:
                status = AdapterState.PARTIAL
    return ScriptedOutput(
        status=status,
        payload=result.get("candidate_payload", result.get("payload")),
        raw_output=raw,
        expected_units=request.expected_units,
        produced_units=produced,
        failure_reason=result.get("failure_reason"),
    )


def persist_capability_attempt(store: Any, result: CapabilityAttemptResult) -> CapabilityPersistenceReceipt:
    """Persist candidate/provenance through Store without creating authority."""

    adapter_receipt = persist_adapter_run(store, result.adapter_run)
    run_id = result.request.monitoring_run_id or None
    profile_version = store.put_domain_object(
        "execution_profile",
        "execution-profile:%s" % result.profile.fingerprint,
        result.profile.public_dict(),
        run_id=run_id,
        idempotency_key="capability-profile:%s" % result.profile.fingerprint,
    )
    request_version = store.put_domain_object(
        "adapter_attempt_request",
        "adapter-attempt-request:%s" % result.request.attempt_id,
        result.request.identity_dict(),
        run_id=run_id,
        idempotency_key="capability-request:%s:%s" % (
            result.request.attempt_id,
            result.request.request_hash,
        ),
    )
    event_versions = []
    for item in result.work_events:
        version = store.put_domain_object(
            "adapter_work_event",
            "adapter-work-event:%s:%03d" % (item.attempt_id, item.sequence),
            item.to_dict(),
            run_id=run_id,
            idempotency_key="capability-event:%s:%03d" % (item.attempt_id, item.sequence),
        )
        event_versions.append(int(version))
    return CapabilityPersistenceReceipt(
        adapter=adapter_receipt,
        profile_version=int(profile_version),
        request_version=int(request_version),
        work_event_versions=tuple(event_versions),
    )


__all__ = [
    "AdapterWorkEvent",
    "ApiCapabilityRuntime",
    "ApiTransport",
    "AttemptJournal",
    "AttemptLifecycleObserver",
    "AttemptIdentityError",
    "AttemptStage",
    "CapabilityAttemptResult",
    "CapabilityPersistenceReceipt",
    "CapabilityRequest",
    "CapabilityRuntime",
    "CapabilityRuntimeError",
    "ExecutionProfile",
    "HarnessCapabilityRuntime",
    "HarnessIsolationBackend",
    "HarnessIsolationPolicy",
    "InvocationVersions",
    "StaleAttemptError",
    "TransportExecution",
    "TransportKind",
    "persist_capability_attempt",
]
