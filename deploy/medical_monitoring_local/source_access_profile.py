#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R8 G2 synthetic macOS ``source_access_profile`` evidence.

This module exercises a temporary locked macOS filesystem shadow root by
default and retains an explicit in-memory fixture for negative tests.  It never
accepts or probes a real project path, so the real-project gate remains closed.

The evidence contract proves four independent facts on a synthetic target:

* a declared source file can be read;
* a write operation is denied without mutating the source tree;
* the denied write produces an observable write event when monitoring is
  available and its scope is complete; and
* an unavailable/incomplete/indeterminate monitor is ``not_evaluable`` rather
  than a pass based only on before/after tree digests.
"""

from __future__ import annotations

import copy
import errno
import json
import os
import platform
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from canonical_evidence import bytes_digest_ref as _bytes_digest_ref
from canonical_evidence import canonical_json_bytes, digest_ref


SOURCE_ACCESS_PROFILE_SCHEMA = "mm-monitoring-r8-g2-source-access-profile-v1"
SOURCE_ACCESS_PROFILE_ID = "macos-synthetic-shadow-root-read-only-v1"
SOURCE_ACCESS_PROFILE_VERSION = "1"
TARGET_SYSTEM = "macOS"
ADAPTER_ID = "synthetic-shadow-root"
POLICY_VERSION = "macos-read-only-policy-v1"
MONITOR_TOOL_ID = "synthetic-write-event-monitor"
MONITOR_TOOL_VERSION = "1"
DEFAULT_ROOT_REF = "opaque-shadow-root:synthetic-g2"
DEFAULT_STARTED_AT = "2026-08-31T00:00:00Z"
DEFAULT_ENDED_AT = "2026-08-31T00:00:01Z"

_SHA256_REF_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_OPAQUE_ROOT_REF_RE = re.compile(r"^opaque-shadow-root:[A-Za-z0-9][A-Za-z0-9._:-]*$")
_ALLOWED_PROFILE_STATUS = frozenset({"evaluable", "not_evaluable"})
_ALLOWED_MONITOR_EXIT = frozenset({"complete", "failed", "unknown", "not_started"})


class SourceAccessProfileError(ValueError):
    """Synthetic source-access profile or evidence is invalid."""


class SourceWriteDenied(SourceAccessProfileError):
    """The synthetic read-only policy rejected a write attempt."""


def _copy_json(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise SourceAccessProfileError("value_must_be_json") from exc


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SourceAccessProfileError("%s_must_be_object" % field)
    return value


def _require_string(value: Any, field: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str):
        raise SourceAccessProfileError("%s_must_be_string" % field)
    normalized = unicodedata.normalize("NFC", value)
    if nonempty and not normalized:
        raise SourceAccessProfileError("%s_must_be_nonempty" % field)
    if "\x00" in normalized:
        raise SourceAccessProfileError("%s_contains_nul" % field)
    return normalized


def _require_enum(value: Any, field: str, allowed: Iterable[str]) -> str:
    normalized = _require_string(value, field)
    if normalized not in set(allowed):
        raise SourceAccessProfileError("%s_invalid" % field)
    return normalized


def _require_sha256_ref(value: Any, field: str) -> str:
    normalized = _require_string(value, field)
    if _SHA256_REF_RE.fullmatch(normalized) is None:
        raise SourceAccessProfileError("%s_must_be_sha256" % field)
    return normalized


def _require_root_ref(value: Any, field: str = "root_ref") -> str:
    normalized = _require_string(value, field)
    if _OPAQUE_ROOT_REF_RE.fullmatch(normalized) is None:
        raise SourceAccessProfileError("%s_must_be_opaque_shadow_root_ref" % field)
    return normalized


def _relative_path(value: Any, field: str = "path") -> str:
    """Validate a relative POSIX path without accepting filesystem paths."""

    path = _require_string(value, field)
    if path.startswith("/") or "\\" in path:
        raise SourceAccessProfileError("%s_must_be_relative_posix" % field)
    if path in {".", ".."} or path.startswith("../") or "/../" in path or path.endswith("/.."):
        raise SourceAccessProfileError("%s_escapes_shadow_root" % field)
    if "//" in path or path.startswith("./") or "/./" in path or path.endswith("/."):
        raise SourceAccessProfileError("%s_not_normalized" % field)
    parts = path.split("/")
    if not parts or any(not part or part in {".", ".."} for part in parts):
        raise SourceAccessProfileError("%s_not_normalized" % field)
    return path


class SyntheticShadowRoot:
    """In-memory source tree used by the macOS synthetic adapter.

    The class intentionally has no path-like API.  ``read_bytes`` reads from
    an immutable copy, while ``write_bytes`` records a policy event and raises
    ``SourceWriteDenied`` without changing the copy.
    """

    def __init__(
        self,
        files: Mapping[str, Union[bytes, bytearray, str]],
        *,
        root_ref: str = DEFAULT_ROOT_REF,
    ) -> None:
        self.implementation = "memory"
        self.root_ref = _require_root_ref(root_ref)
        if not isinstance(files, Mapping) or not files:
            raise SourceAccessProfileError("synthetic_shadow_root_requires_files")
        normalized: Dict[str, bytes] = {}
        for raw_path, raw_payload in files.items():
            path = _relative_path(raw_path, "files.path")
            if isinstance(raw_payload, str):
                payload = raw_payload.encode("utf-8")
            elif isinstance(raw_payload, (bytes, bytearray)):
                payload = bytes(raw_payload)
            else:
                raise SourceAccessProfileError("files.payload_must_be_bytes_or_string")
            if path in normalized:
                raise SourceAccessProfileError("duplicate_shadow_root_path:%s" % path)
            normalized[path] = payload
        self._files = dict(normalized)
        self._write_attempts: List[Dict[str, Any]] = []

    @classmethod
    def default(cls) -> "SyntheticShadowRoot":
        return cls(
            {
                "documents/allowed.txt": "synthetic read-only source",
                "documents/unchanged.txt": "stable synthetic content",
            }
        )

    def read_bytes(self, path: str) -> bytes:
        relative = _relative_path(path)
        try:
            return bytes(self._files[relative])
        except KeyError as exc:
            raise FileNotFoundError(relative) from exc

    def write_bytes(self, path: str, payload: Union[bytes, bytearray, str]) -> None:
        relative = _relative_path(path)
        if isinstance(payload, str):
            raw_payload = payload.encode("utf-8")
        elif isinstance(payload, (bytes, bytearray)):
            raw_payload = bytes(payload)
        else:
            raise SourceAccessProfileError("write_payload_must_be_bytes_or_string")
        event = {
            "event_id": "synthetic-write-%d" % (len(self._write_attempts) + 1),
            "kind": "write_attempt",
            "operation": "write",
            "path": relative,
            "target": "source_root",
            "decision": "denied",
            "outcome": "denied",
            "observed": True,
            "mutation_applied": False,
            "payload_sha256": _bytes_digest_ref(raw_payload),
        }
        self._write_attempts.append(event)
        raise SourceWriteDenied("synthetic_source_write_denied:%s" % relative)

    def tree(self) -> Dict[str, Any]:
        entries = [
            {
                "path": path,
                "kind": "regular_file",
                "length_bytes": len(payload),
                "sha256": _bytes_digest_ref(payload),
            }
            for path, payload in sorted(self._files.items())
        ]
        body: Dict[str, Any] = {"root_ref": self.root_ref, "entries": entries}
        body["tree_digest"] = digest_ref({"root_ref": self.root_ref, "entries": entries})
        return body

    @property
    def write_attempts(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(copy.deepcopy(self._write_attempts))


class MacOSSyntheticShadowRoot(SyntheticShadowRoot):
    """Temporary macOS filesystem root used only for the G2 denial drill."""

    def __init__(
        self,
        files: Mapping[str, Union[bytes, bytearray, str]],
        *,
        root_ref: str = DEFAULT_ROOT_REF,
    ) -> None:
        if platform.system() != "Darwin":
            raise SourceAccessProfileError("target_macos_unavailable")
        super().__init__(files, root_ref=root_ref)
        self.implementation = "macos_filesystem"
        self._temporary = tempfile.TemporaryDirectory(prefix="mm-r8-g2-shadow-")
        self._root_path = Path(self._temporary.name)
        for directory_name in ("cache", "probe"):
            (self._root_path / directory_name).mkdir()
        for relative, payload in self._files.items():
            target = self._root_path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            target.chmod(0o444)
        directories = [self._root_path, *(p for p in self._root_path.rglob("*") if p.is_dir())]
        for directory in sorted(directories, key=lambda p: len(p.parts), reverse=True):
            directory.chmod(0o555)

    @classmethod
    def default(cls) -> "MacOSSyntheticShadowRoot":
        return cls(
            {
                "documents/allowed.txt": "synthetic read-only source",
                "documents/unchanged.txt": "stable synthetic content",
            }
        )

    def _target(self, path: str) -> Path:
        return self._root_path / _relative_path(path)

    def read_bytes(self, path: str) -> bytes:
        return self._target(path).read_bytes()

    def write_bytes(self, path: str, payload: Union[bytes, bytearray, str]) -> None:
        relative = _relative_path(path)
        if isinstance(payload, str):
            raw_payload = payload.encode("utf-8")
        elif isinstance(payload, (bytes, bytearray)):
            raw_payload = bytes(payload)
        else:
            raise SourceAccessProfileError("write_payload_must_be_bytes_or_string")
        event = {
            "event_id": "synthetic-write-%d" % (len(self._write_attempts) + 1),
            "kind": "write_attempt",
            "operation": "write",
            "path": relative,
            "target": "source_root",
            "decision": "denied",
            "outcome": "denied",
            "observed": True,
            "mutation_applied": False,
            "payload_sha256": _bytes_digest_ref(raw_payload),
        }
        try:
            fd = os.open(self._target(relative), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except OSError as exc:
            if exc.errno not in {errno.EACCES, errno.EPERM, errno.EROFS}:
                raise
            self._write_attempts.append(event)
            raise SourceWriteDenied("macos_synthetic_source_write_denied:%s" % relative) from exc
        else:
            os.close(fd)
            event.update(decision="allowed", outcome="allowed", mutation_applied=True)
            self._write_attempts.append(event)
            raise SourceAccessProfileError("macos_synthetic_write_unexpectedly_allowed")

    def tree(self) -> Dict[str, Any]:
        entries = []
        for path in sorted(self._root_path.rglob("*"), key=lambda p: p.as_posix().encode("utf-8")):
            if path.is_file():
                payload = path.read_bytes()
                entries.append(
                    {
                        "path": path.relative_to(self._root_path).as_posix(),
                        "kind": "regular_file",
                        "length_bytes": len(payload),
                        "sha256": _bytes_digest_ref(payload),
                    }
                )
        body: Dict[str, Any] = {"root_ref": self.root_ref, "entries": entries}
        body["tree_digest"] = digest_ref(body)
        return body

    def close(self) -> None:
        if not hasattr(self, "_temporary"):
            return
        for path in [self._root_path, *self._root_path.rglob("*")]:
            try:
                path.chmod(0o700 if path.is_dir() else 0o600)
            except OSError:
                pass
        self._temporary.cleanup()
        del self._temporary


class SyntheticWriteEventMonitor:
    """Synthetic stand-in for the target-system write-event monitor."""

    def __init__(
        self,
        *,
        available: bool = True,
        scope_complete: bool = True,
        terminal_status: str = "complete",
        started_at: str = DEFAULT_STARTED_AT,
        ended_at: str = DEFAULT_ENDED_AT,
        tool_version: str = MONITOR_TOOL_VERSION,
        policy_version: str = POLICY_VERSION,
    ) -> None:
        self.available = bool(available)
        self.scope_complete = bool(scope_complete)
        self.terminal_status = _require_enum(
            terminal_status, "terminal_status", _ALLOWED_MONITOR_EXIT
        )
        self.started_at = _require_string(started_at, "started_at")
        self.ended_at = _require_string(ended_at, "ended_at")
        self.tool_version = _require_string(tool_version, "tool_version")
        self.policy_version = _require_string(policy_version, "policy_version")
        self.started = False
        self.finished = False
        self.events: List[Dict[str, Any]] = []
        self.dropped_event_count = 0

    def start(self) -> None:
        self.started = True

    def observe(self, event: Mapping[str, Any]) -> None:
        if not self.started or not self.available:
            self.dropped_event_count += 1
            return
        self.events.append(_copy_json(dict(event)))

    def finish(self) -> None:
        self.finished = True

    def as_dict(self) -> Dict[str, Any]:
        observed_write_event = any(
            event.get("kind") == "write_attempt"
            and event.get("decision") == "denied"
            and event.get("mutation_applied") is False
            for event in self.events
        )
        if not self.available:
            coverage = "unavailable"
        elif not self.scope_complete:
            coverage = "incomplete"
        else:
            coverage = "complete"
        return {
            "scope": ["synthetic_shadow_root"],
            "scope_complete": self.scope_complete,
            "started_at": self.started_at if self.started else None,
            "ended_at": self.ended_at if self.finished else None,
            "tool": MONITOR_TOOL_ID,
            "tool_version": self.tool_version,
            "policy_version": self.policy_version,
            "available": self.available,
            "exit_status": self.terminal_status if self.finished else "not_started",
            "terminal_status_known": self.finished and self.terminal_status != "unknown",
            "coverage": coverage,
            "events": _copy_json(self.events),
            "events_observed": len(self.events),
            "events_dropped": self.dropped_event_count,
            "write_event_observed": observed_write_event,
            "leak_conditions": [],
        }


def _profile_header(root: SyntheticShadowRoot, available: bool) -> Dict[str, Any]:
    return {
        "id": SOURCE_ACCESS_PROFILE_ID,
        "version": SOURCE_ACCESS_PROFILE_VERSION,
        "target_system": TARGET_SYSTEM,
        "adapter": ADAPTER_ID,
        "source_kind": "synthetic_shadow_root",
        "root_ref": root.root_ref,
        "implementation": root.implementation,
        "access_mode": "read_only",
        "available": bool(available),
    }


def _normalise_leak_conditions(value: Optional[Iterable[str]]) -> List[str]:
    if value is None:
        return []
    values: List[str] = []
    for index, item in enumerate(value):
        text = _require_string(item, "leak_conditions[%d]" % index)
        if text not in values:
            values.append(text)
    return sorted(values)


def _evidence_status(
    *,
    profile_available: bool,
    read_result: Mapping[str, Any],
    write_result: Mapping[str, Any],
    monitoring: Mapping[str, Any],
    tree_unchanged: bool,
    tree_hash_only: bool,
    leak_conditions: Sequence[str],
    implementation: str,
) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    if not profile_available:
        reasons.append("profile_unavailable")
    if read_result.get("status") != "allowed":
        reasons.append("read_not_allowed")
    if write_result.get("status") != "denied":
        reasons.append("write_not_denied")
    if write_result.get("mutation_applied") is not False:
        reasons.append("source_mutation_observed")
    if not monitoring.get("available"):
        reasons.append("monitor_unavailable")
    if monitoring.get("scope_complete") is not True:
        reasons.append("monitor_scope_incomplete")
    if monitoring.get("terminal_status_known") is not True:
        reasons.append("monitor_terminal_status_unknown")
    if monitoring.get("exit_status") != "complete":
        reasons.append("monitor_exit_not_complete")
    if monitoring.get("write_event_observed") is not True:
        reasons.append("write_event_not_observed")
    if not tree_unchanged:
        reasons.append("source_tree_changed")
    if tree_hash_only:
        reasons.append("tree_hash_only_insufficient")
    if leak_conditions:
        reasons.append("leak_conditions_present")
    if monitoring.get("events_dropped", 0) != 0:
        reasons.append("monitor_events_dropped")
    if implementation != "macos_filesystem":
        reasons.append("target_filesystem_not_exercised")
    return ("evaluable" if not reasons else "not_evaluable"), sorted(set(reasons))


def run_synthetic_source_access_profile(
    *,
    shadow_root: Optional[SyntheticShadowRoot] = None,
    read_path: str = "documents/allowed.txt",
    write_path: str = "probe/forbidden.txt",
    write_payload: Union[bytes, bytearray, str] = b"synthetic write probe",
    profile_available: bool = True,
    monitor_available: bool = True,
    monitor_scope_complete: bool = True,
    terminal_status: str = "complete",
    leak_conditions: Optional[Iterable[str]] = None,
    tree_hash_only: bool = False,
    started_at: str = DEFAULT_STARTED_AT,
    ended_at: str = DEFAULT_ENDED_AT,
    tool_version: str = MONITOR_TOOL_VERSION,
    policy_version: str = POLICY_VERSION,
) -> Dict[str, Any]:
    """Run the synthetic profile without accepting or touching a real path.

    ``shadow_root`` must be a controlled ``SyntheticShadowRoot``.  The default
    uses a temporary locked macOS shadow directory; the explicit in-memory
    implementation remains a fail-closed negative-test fixture.  A caller
    cannot pass a path, and no real project root is accepted or probed.
    """

    created_root = shadow_root is None
    try:
        root = MacOSSyntheticShadowRoot.default() if shadow_root is None else shadow_root
    except SourceAccessProfileError:
        root = SyntheticShadowRoot.default() if shadow_root is None else shadow_root
        profile_available = False
    if not isinstance(root, SyntheticShadowRoot):
        raise SourceAccessProfileError("shadow_root_must_be_synthetic")
    read_relative = _relative_path(read_path, "read_path")
    write_relative = _relative_path(write_path, "write_path")
    normalized_leaks = _normalise_leak_conditions(leak_conditions)
    monitor = SyntheticWriteEventMonitor(
        available=monitor_available,
        scope_complete=monitor_scope_complete,
        terminal_status=terminal_status,
        started_at=started_at,
        ended_at=ended_at,
        tool_version=tool_version,
        policy_version=policy_version,
    )
    before = root.tree()

    read_result: Dict[str, Any]
    write_result: Dict[str, Any]
    if not profile_available:
        read_result = {
            "path": read_relative,
            "status": "not_attempted",
            "observed": False,
        }
        write_result = {
            "path": write_relative,
            "status": "not_attempted",
            "synthetic_only": True,
            "mutation_applied": False,
            "observed": False,
        }
        monitor.finish()
    else:
        monitor.start()
        try:
            payload = root.read_bytes(read_relative)
        except (FileNotFoundError, SourceAccessProfileError) as exc:
            read_result = {
                "path": read_relative,
                "status": "failed",
                "observed": True,
                "error": type(exc).__name__,
            }
        else:
            read_result = {
                "path": read_relative,
                "status": "allowed",
                "observed": True,
                "length_bytes": len(payload),
                "content_sha256": _bytes_digest_ref(payload),
            }
        try:
            root.write_bytes(write_relative, write_payload)
        except SourceWriteDenied as exc:
            event = root.write_attempts[-1]
            monitor.observe(event)
            write_result = {
                "path": write_relative,
                "status": "denied",
                "decision": "deny",
                "synthetic_only": True,
                "mutation_applied": False,
                "observed": True,
                "error": type(exc).__name__,
            }
        except SourceAccessProfileError as exc:
            write_result = {
                "path": write_relative,
                "status": "failed",
                "decision": "unknown",
                "synthetic_only": True,
                "mutation_applied": None,
                "observed": True,
                "error": type(exc).__name__,
            }
        monitor.finish()

    after = root.tree()
    if normalized_leaks:
        monitor_payload = monitor.as_dict()
        monitor_payload["leak_conditions"] = list(normalized_leaks)
    else:
        monitor_payload = monitor.as_dict()
    tree_unchanged = before == after
    profile = _profile_header(root, profile_available)
    status, reasons = _evidence_status(
        profile_available=profile_available,
        read_result=read_result,
        write_result=write_result,
        monitoring=monitor_payload,
        tree_unchanged=tree_unchanged,
        tree_hash_only=bool(tree_hash_only),
        leak_conditions=normalized_leaks,
        implementation=root.implementation,
    )
    evidence: Dict[str, Any] = {
        "schema": SOURCE_ACCESS_PROFILE_SCHEMA,
        "profile": profile,
        "policy": {
            "read": "allow",
            "write": "deny",
            "write_probe_scope": "synthetic_only",
            "policy_version": policy_version,
        },
        "source": {
            "root_ref": root.root_ref,
            "synthetic": True,
            "before": before,
            "after": after,
            "unchanged": tree_unchanged,
            "tree_hash_only": bool(tree_hash_only),
        },
        "read": read_result,
        "write": write_result,
        "monitoring": monitor_payload,
        "status": status,
        "not_evaluable_reasons": reasons,
        "profile_digest": "",
    }
    evidence["profile_digest"] = digest_ref(evidence)
    try:
        return validate_source_access_evidence(evidence)
    finally:
        if created_root and isinstance(root, MacOSSyntheticShadowRoot):
            root.close()


# Explicit descriptive alias for callers that name the result as evidence.
build_source_access_evidence = run_synthetic_source_access_profile
build_macos_synthetic_source_access_evidence = run_synthetic_source_access_profile


@dataclass(frozen=True)
class SourceAccessReplayResult:
    valid: bool
    errors: Tuple[str, ...] = ()
    status: Optional[str] = None

    def __bool__(self) -> bool:
        return self.valid


def _validate_tree(value: Any, field: str, root_ref: str) -> Dict[str, Any]:
    body = dict(_require_mapping(value, field))
    if set(body) != {"root_ref", "entries", "tree_digest"}:
        raise SourceAccessProfileError("%s_fields_mismatch" % field)
    if _require_root_ref(body["root_ref"], field + ".root_ref") != root_ref:
        raise SourceAccessProfileError("%s_root_ref_mismatch" % field)
    entries_raw = body["entries"]
    if not isinstance(entries_raw, list):
        raise SourceAccessProfileError("%s.entries_must_be_array" % field)
    entries: List[Dict[str, Any]] = []
    prior_path: Optional[str] = None
    for index, raw in enumerate(entries_raw):
        entry = dict(_require_mapping(raw, "%s.entries[%d]" % (field, index)))
        if set(entry) != {"path", "kind", "length_bytes", "sha256"}:
            raise SourceAccessProfileError("%s.entries[%d]_fields_mismatch" % (field, index))
        path = _relative_path(entry["path"], "%s.entries[%d].path" % (field, index))
        if prior_path is not None and path <= prior_path:
            raise SourceAccessProfileError("%s.entries_not_sorted_or_duplicate" % field)
        prior_path = path
        if entry["kind"] != "regular_file":
            raise SourceAccessProfileError("%s.entries[%d].kind_invalid" % (field, index))
        length = entry["length_bytes"]
        if isinstance(length, bool) or not isinstance(length, int) or length < 0:
            raise SourceAccessProfileError("%s.entries[%d].length_invalid" % (field, index))
        digest = _require_sha256_ref(entry["sha256"], "%s.entries[%d].sha256" % (field, index))
        entries.append(
            {"path": path, "kind": "regular_file", "length_bytes": int(length), "sha256": digest}
        )
    tree_digest = _require_sha256_ref(body["tree_digest"], field + ".tree_digest")
    expected = digest_ref({"root_ref": root_ref, "entries": entries})
    if tree_digest != expected:
        raise SourceAccessProfileError("%s_digest_mismatch" % field)
    return {"root_ref": root_ref, "entries": entries, "tree_digest": tree_digest}


def validate_source_access_evidence(value: Mapping[str, Any]) -> Dict[str, Any]:
    """Strictly validate and replay one serialized profile evidence object."""

    raw = dict(_require_mapping(value, "evidence"))
    required = {
        "schema",
        "profile",
        "policy",
        "source",
        "read",
        "write",
        "monitoring",
        "status",
        "not_evaluable_reasons",
        "profile_digest",
    }
    if set(raw) != required:
        raise SourceAccessProfileError("evidence_fields_mismatch")
    if raw["schema"] != SOURCE_ACCESS_PROFILE_SCHEMA:
        raise SourceAccessProfileError("schema_mismatch")
    profile = dict(_require_mapping(raw["profile"], "profile"))
    if set(profile) != {
        "id",
        "version",
        "target_system",
        "adapter",
        "source_kind",
        "root_ref",
        "implementation",
        "access_mode",
        "available",
    }:
        raise SourceAccessProfileError("profile_fields_mismatch")
    if profile["id"] != SOURCE_ACCESS_PROFILE_ID:
        raise SourceAccessProfileError("profile_id_mismatch")
    if profile["version"] != SOURCE_ACCESS_PROFILE_VERSION:
        raise SourceAccessProfileError("profile_version_mismatch")
    if profile["target_system"] != TARGET_SYSTEM:
        raise SourceAccessProfileError("target_system_mismatch")
    if profile["adapter"] != ADAPTER_ID or profile["source_kind"] != "synthetic_shadow_root":
        raise SourceAccessProfileError("profile_adapter_mismatch")
    implementation = _require_enum(
        profile["implementation"],
        "profile.implementation",
        {"memory", "macos_filesystem"},
    )
    root_ref = _require_root_ref(profile["root_ref"], "profile.root_ref")
    if profile["access_mode"] != "read_only":
        raise SourceAccessProfileError("profile_access_mode_mismatch")
    if not isinstance(profile["available"], bool):
        raise SourceAccessProfileError("profile.available_must_be_bool")
    profile_available = profile["available"]

    policy = dict(_require_mapping(raw["policy"], "policy"))
    if set(policy) != {"read", "write", "write_probe_scope", "policy_version"}:
        raise SourceAccessProfileError("policy_fields_mismatch")
    if policy["read"] != "allow" or policy["write"] != "deny":
        raise SourceAccessProfileError("policy_not_read_only")
    if policy["write_probe_scope"] != "synthetic_only":
        raise SourceAccessProfileError("write_probe_scope_not_synthetic")
    _require_string(policy["policy_version"], "policy.policy_version")

    source = dict(_require_mapping(raw["source"], "source"))
    if set(source) != {"root_ref", "synthetic", "before", "after", "unchanged", "tree_hash_only"}:
        raise SourceAccessProfileError("source_fields_mismatch")
    if source["synthetic"] is not True:
        raise SourceAccessProfileError("source_must_be_synthetic")
    if _require_root_ref(source["root_ref"], "source.root_ref") != root_ref:
        raise SourceAccessProfileError("source_root_ref_mismatch")
    before = _validate_tree(source["before"], "source.before", root_ref)
    after = _validate_tree(source["after"], "source.after", root_ref)
    unchanged = source["unchanged"]
    if not isinstance(unchanged, bool):
        raise SourceAccessProfileError("source.unchanged_must_be_bool")
    if unchanged != (before == after):
        raise SourceAccessProfileError("source.unchanged_mismatch")
    tree_hash_only = source["tree_hash_only"]
    if not isinstance(tree_hash_only, bool):
        raise SourceAccessProfileError("source.tree_hash_only_must_be_bool")

    read = dict(_require_mapping(raw["read"], "read"))
    read_required = {"path", "status", "observed"}
    if not read_required.issubset(read):
        raise SourceAccessProfileError("read_fields_missing")
    read_path = _relative_path(read["path"], "read.path")
    read_status = _require_enum(read["status"], "read.status", {"allowed", "failed", "not_attempted"})
    if not isinstance(read["observed"], bool):
        raise SourceAccessProfileError("read.observed_must_be_bool")
    if read_status == "allowed":
        if read["observed"] is not True:
            raise SourceAccessProfileError("allowed_read_not_observed")
        if set(read) != {"path", "status", "observed", "length_bytes", "content_sha256"}:
            raise SourceAccessProfileError("read_allowed_fields_mismatch")
        length = read["length_bytes"]
        if isinstance(length, bool) or not isinstance(length, int) or length < 0:
            raise SourceAccessProfileError("read.length_invalid")
        _require_sha256_ref(read["content_sha256"], "read.content_sha256")
    elif set(read) not in (
        {"path", "status", "observed"},
        {"path", "status", "observed", "error"},
    ):
        raise SourceAccessProfileError("read_non_allowed_fields_mismatch")
    if not read_path:
        raise SourceAccessProfileError("read.path_empty")

    write = dict(_require_mapping(raw["write"], "write"))
    write_required = {"path", "status", "synthetic_only", "mutation_applied", "observed"}
    if not write_required.issubset(write):
        raise SourceAccessProfileError("write_fields_missing")
    _relative_path(write["path"], "write.path")
    write_status = _require_enum(write["status"], "write.status", {"denied", "failed", "not_attempted"})
    if write["synthetic_only"] is not True:
        raise SourceAccessProfileError("write_probe_not_synthetic")
    if write["mutation_applied"] is not False and write["mutation_applied"] is not None:
        raise SourceAccessProfileError("write_mutation_applied")
    if not isinstance(write["observed"], bool):
        raise SourceAccessProfileError("write.observed_must_be_bool")
    if write_status == "denied":
        if write["mutation_applied"] is not False or write["observed"] is not True:
            raise SourceAccessProfileError("denied_write_fields_invalid")
        if set(write) != {
            "path",
            "status",
            "decision",
            "synthetic_only",
            "mutation_applied",
            "observed",
            "error",
        }:
            raise SourceAccessProfileError("write_denied_fields_mismatch")
        if write["decision"] != "deny" or write["error"] != "SourceWriteDenied":
            raise SourceAccessProfileError("write_denial_evidence_invalid")
    elif set(write) not in (
        write_required,
        write_required | {"decision", "error"},
    ):
        raise SourceAccessProfileError("write_non_denied_fields_mismatch")

    monitoring = dict(_require_mapping(raw["monitoring"], "monitoring"))
    monitor_required = {
        "scope",
        "scope_complete",
        "started_at",
        "ended_at",
        "tool",
        "tool_version",
        "policy_version",
        "available",
        "exit_status",
        "terminal_status_known",
        "coverage",
        "events",
        "events_observed",
        "events_dropped",
        "write_event_observed",
        "leak_conditions",
    }
    if set(monitoring) != monitor_required:
        raise SourceAccessProfileError("monitoring_fields_mismatch")
    if monitoring["scope"] != ["synthetic_shadow_root"]:
        raise SourceAccessProfileError("monitoring_scope_mismatch")
    for field in ("scope_complete", "available", "terminal_status_known", "write_event_observed"):
        if not isinstance(monitoring[field], bool):
            raise SourceAccessProfileError("monitoring.%s_must_be_bool" % field)
    if monitoring["started_at"] is not None:
        _require_string(monitoring["started_at"], "monitoring.started_at")
    if monitoring["ended_at"] is not None:
        _require_string(monitoring["ended_at"], "monitoring.ended_at")
    _require_string(monitoring["tool"], "monitoring.tool")
    _require_string(monitoring["tool_version"], "monitoring.tool_version")
    _require_string(monitoring["policy_version"], "monitoring.policy_version")
    _require_enum(monitoring["exit_status"], "monitoring.exit_status", _ALLOWED_MONITOR_EXIT)
    _require_enum(monitoring["coverage"], "monitoring.coverage", {"complete", "incomplete", "unavailable"})
    expected_coverage = (
        "unavailable"
        if monitoring["available"] is False
        else "incomplete"
        if monitoring["scope_complete"] is False
        else "complete"
    )
    if monitoring["coverage"] != expected_coverage:
        raise SourceAccessProfileError("monitoring.coverage_mismatch")
    expected_terminal_known = monitoring["exit_status"] not in {"unknown", "not_started"}
    if monitoring["terminal_status_known"] != expected_terminal_known:
        raise SourceAccessProfileError("monitoring.terminal_status_known_mismatch")
    events = monitoring["events"]
    if not isinstance(events, list):
        raise SourceAccessProfileError("monitoring.events_must_be_array")
    for index, event_raw in enumerate(events):
        event = dict(_require_mapping(event_raw, "monitoring.events[%d]" % index))
        expected_event_fields = {
            "event_id",
            "kind",
            "operation",
            "path",
            "target",
            "decision",
            "outcome",
            "observed",
            "mutation_applied",
            "payload_sha256",
        }
        if set(event) != expected_event_fields:
            raise SourceAccessProfileError("monitoring.events[%d]_fields_mismatch" % index)
        _require_string(event["event_id"], "monitoring.events[%d].event_id" % index)
        if event["kind"] != "write_attempt" or event["operation"] != "write":
            raise SourceAccessProfileError("monitoring.events[%d]_kind_invalid" % index)
        _relative_path(event["path"], "monitoring.events[%d].path" % index)
        if event["target"] != "source_root" or event["decision"] != "denied" or event["outcome"] != "denied":
            raise SourceAccessProfileError("monitoring.events[%d]_denial_invalid" % index)
        if event["observed"] is not True or event["mutation_applied"] is not False:
            raise SourceAccessProfileError("monitoring.events[%d]_observation_invalid" % index)
        _require_sha256_ref(event["payload_sha256"], "monitoring.events[%d].payload_sha256" % index)
    if monitoring["events_observed"] != len(events) or monitoring["events_observed"] < 0:
        raise SourceAccessProfileError("monitoring.events_observed_mismatch")
    if (
        isinstance(monitoring["events_dropped"], bool)
        or not isinstance(monitoring["events_dropped"], int)
        or monitoring["events_dropped"] < 0
    ):
        raise SourceAccessProfileError("monitoring.events_dropped_invalid")
    expected_observed = any(
        event.get("kind") == "write_attempt"
        and event.get("decision") == "denied"
        and event.get("mutation_applied") is False
        for event in events
    )
    if monitoring["write_event_observed"] != expected_observed:
        raise SourceAccessProfileError("monitoring.write_event_observed_mismatch")
    if not isinstance(monitoring["leak_conditions"], list):
        raise SourceAccessProfileError("monitoring.leak_conditions_must_be_array")
    leak_conditions = []
    for index, condition in enumerate(monitoring["leak_conditions"]):
        leak_conditions.append(_require_string(condition, "monitoring.leak_conditions[%d]" % index))
    if leak_conditions != sorted(set(leak_conditions)):
        raise SourceAccessProfileError("monitoring.leak_conditions_not_sorted")

    status = _require_enum(raw["status"], "status", _ALLOWED_PROFILE_STATUS)
    reasons_raw = raw["not_evaluable_reasons"]
    if not isinstance(reasons_raw, list) or any(not isinstance(reason, str) or not reason for reason in reasons_raw):
        raise SourceAccessProfileError("not_evaluable_reasons_invalid")
    reasons = list(reasons_raw)
    if reasons != sorted(set(reasons)):
        raise SourceAccessProfileError("not_evaluable_reasons_not_sorted")
    if status == "evaluable" and reasons:
        raise SourceAccessProfileError("evaluable_has_not_evaluable_reasons")
    if status == "not_evaluable" and not reasons:
        raise SourceAccessProfileError("not_evaluable_requires_reason")
    expected_status, expected_reasons = _evidence_status(
        profile_available=profile_available,
        read_result=read,
        write_result=write,
        monitoring=monitoring,
        tree_unchanged=unchanged,
        tree_hash_only=tree_hash_only,
        leak_conditions=leak_conditions,
        implementation=implementation,
    )
    if status != expected_status or reasons != expected_reasons:
        raise SourceAccessProfileError("status_inconsistent")
    digest = _require_sha256_ref(raw["profile_digest"], "profile_digest")
    digest_body = _copy_json(raw)
    digest_body["profile_digest"] = ""
    if digest != digest_ref(digest_body):
        raise SourceAccessProfileError("profile_digest_mismatch")
    return _copy_json(raw)


def replay_source_access_evidence(
    value: Mapping[str, Any], *, strict: bool = False
) -> SourceAccessReplayResult:
    """Independently validate serialized profile evidence and its digest."""

    try:
        validated = validate_source_access_evidence(value)
    except SourceAccessProfileError as exc:
        if strict:
            raise
        return SourceAccessReplayResult(False, (str(exc),), None)
    return SourceAccessReplayResult(True, (), str(validated["status"]))


__all__ = [
    "ADAPTER_ID",
    "DEFAULT_ENDED_AT",
    "DEFAULT_ROOT_REF",
    "DEFAULT_STARTED_AT",
    "MONITOR_TOOL_ID",
    "MONITOR_TOOL_VERSION",
    "POLICY_VERSION",
    "SOURCE_ACCESS_PROFILE_ID",
    "SOURCE_ACCESS_PROFILE_SCHEMA",
    "SOURCE_ACCESS_PROFILE_VERSION",
    "SourceAccessProfileError",
    "SourceAccessReplayResult",
    "SourceWriteDenied",
    "MacOSSyntheticShadowRoot",
    "SyntheticShadowRoot",
    "SyntheticWriteEventMonitor",
    "build_macos_synthetic_source_access_evidence",
    "build_source_access_evidence",
    "canonical_json_bytes",
    "digest_ref",
    "replay_source_access_evidence",
    "run_synthetic_source_access_profile",
    "validate_source_access_evidence",
]
