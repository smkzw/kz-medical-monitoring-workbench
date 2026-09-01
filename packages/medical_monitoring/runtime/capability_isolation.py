"""Harness isolation and capability attempt vocabulary."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

from ..domain.execution import content_hash

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


def _seatbelt_argv(
    policy: HarnessIsolationPolicy,
    argv: Sequence[str],
    sandbox_exec_path: Path = _SANDBOX_EXEC_PATH,
) -> Tuple[str, ...]:
    if not sandbox_exec_path.is_file() or not os.access(str(sandbox_exec_path), os.X_OK):
        raise CapabilityRuntimeError(
            "macos_seatbelt_r1 backend is unavailable: /usr/bin/sandbox-exec "
            "is not executable"
        )
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
    command = [str(sandbox_exec_path)]
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


