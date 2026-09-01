#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent synthetic G6 filesystem/process/network observer.

This module never imports or mutates ``actual_app`` state.  It collects OS
command output, runtime-tree snapshots, and the two app ledgers, then compares
those observations with the frozen execution boundary.  Any unavailable,
ambiguous, foreign, non-synthetic, or out-of-root observation blocks the
reconciliation instead of inferring success.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    from canonical_evidence import digest_ref
    from g6_manifests import (
        APP_SCHEMA,
        ManifestError,
        load_all_manifests,
        validate_entry_manifest,
        validate_execution_boundary_manifest,
    )
    import synthetic_ego as _synthetic_ego
except ImportError:  # pragma: no cover - package-style import support
    from .canonical_evidence import digest_ref
    from .g6_manifests import (
        APP_SCHEMA,
        ManifestError,
        load_all_manifests,
        validate_entry_manifest,
        validate_execution_boundary_manifest,
    )
    from . import synthetic_ego as _synthetic_ego


OBSERVER_SCHEMA = "mm-monitoring-r8-g6-independent-observer-ledger-v1"
OBSERVER_VERSION = "1"
RECONCILIATION_SCHEMA = "mm-monitoring-r8-g6-independent-reconciliation-v1"
PROCESS_LEDGER_SCHEMA = "mm-monitoring-r8-g6-process-observer-ledger-v1"
NETWORK_LEDGER_SCHEMA = "mm-monitoring-r8-g6-network-observer-ledger-v1"
OPEN_FILES_LEDGER_SCHEMA = "mm-monitoring-r8-g6-open-files-observer-ledger-v1"
FILESYSTEM_LEDGER_SCHEMA = "mm-monitoring-r8-g6-filesystem-observer-ledger-v1"


class ObserverBlocked(RuntimeError):
    """Raised when independent evidence is unavailable or cannot reconcile."""


class FrozenCommandRunner:
    """Deterministic command seam for focused tests."""

    def __init__(self, outputs: Mapping[Any, Any]) -> None:
        self.outputs = dict(outputs)
        self.calls: List[Tuple[str, ...]] = []

    def __call__(self, command: Sequence[str]) -> str:
        key = tuple(str(item) for item in command)
        self.calls.append(key)
        if key in self.outputs:
            value = self.outputs[key]
        elif key[0] in self.outputs:
            value = self.outputs[key[0]]
        else:
            raise ObserverBlocked("observer_command_output_missing")
        if isinstance(value, Exception):
            raise ObserverBlocked("observer_command_unavailable") from value
        if not isinstance(value, str) or not value.strip():
            raise ObserverBlocked("observer_command_output_incomplete")
        return value



def _canonical_digest(value: Mapping[str, Any], field: str) -> None:
    expected = value.get(field)
    if not isinstance(expected, str) or digest_ref({key: item for key, item in value.items() if key != field}) != expected:
        raise ObserverBlocked(f"{field}_mismatch")



def _root(value: Path) -> Path:
    try:
        return Path(value).expanduser().resolve()
    except OSError as exc:
        raise ObserverBlocked("observer_root_unavailable") from exc



def _under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True



def _relative_to_allowed(path_text: str, roots: Mapping[str, Path]) -> Tuple[str, str]:
    if not isinstance(path_text, str) or not path_text.strip():
        raise ObserverBlocked("observed_path_missing")
    raw = path_text.strip()
    if not raw.startswith("/"):
        raise ObserverBlocked("observed_path_not_absolute")
    path = _root(Path(raw))
    for name, root in roots.items():
        if _under(path, root):
            return name, path.relative_to(root).as_posix() or "."
    raise ObserverBlocked("observed_path_outside_allowed_roots")



def _parse_int(value: str, field: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ObserverBlocked(f"{field}_invalid") from exc
    if result <= 0:
        raise ObserverBlocked(f"{field}_invalid")
    return result



def observe_process_tree(
    output: str,
    *,
    boundary: Mapping[str, Any],
    entry: Mapping[str, Any],
) -> Dict[str, Any]:
    """Parse a frozen ``ps`` ledger and enforce owned-process identity."""

    if not isinstance(output, str) or not output.strip():
        raise ObserverBlocked("process_observer_unavailable")
    process_boundary = boundary.get("owned_process_tree")
    if not isinstance(process_boundary, Mapping):
        raise ObserverBlocked("process_boundary_missing")
    allowed_names = process_boundary.get("allowed_process_names")
    root_name = process_boundary.get("root")
    if not isinstance(allowed_names, list) or not allowed_names or not isinstance(root_name, str):
        raise ObserverBlocked("process_boundary_incomplete")
    rows: List[Dict[str, Any]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("pid "):
            continue
        parts = line.split(None, 3)
        if len(parts) != 4:
            raise ObserverBlocked("process_observer_row_incomplete")
        pid = _parse_int(parts[0], "process.pid")
        ppid = _parse_int(parts[1], "process.ppid") if parts[1] != "0" else 0
        command = parts[2]
        argv = parts[3]
        rows.append({"pid": pid, "ppid": ppid, "name": command, "argv": argv})
    if not rows:
        raise ObserverBlocked("process_observer_empty")
    if any(row["name"] not in set(allowed_names) for row in rows):
        raise ObserverBlocked("unknown_process_observed")
    roots = [row for row in rows if row["name"] == root_name]
    if len(roots) != 1 or len(rows) != 1:
        raise ObserverBlocked("owned_process_tree_count_mismatch")
    expected_processes = entry.get("owned_process_tree", {}).get("processes", [])
    if not isinstance(expected_processes, list) or len(expected_processes) != 1:
        raise ObserverBlocked("entry_process_identity_missing")
    expected = expected_processes[0]
    if expected.get("name") != roots[0]["name"]:
        raise ObserverBlocked("entry_process_name_mismatch")
    argv_contains = expected.get("argv_contains")
    if not isinstance(argv_contains, str) or argv_contains not in roots[0]["argv"]:
        raise ObserverBlocked("entry_process_argv_mismatch")
    body: Dict[str, Any] = {
        "schema": PROCESS_LEDGER_SCHEMA,
        "version": OBSERVER_VERSION,
        "rows": rows,
        "owned_process_count": len(rows),
        "unknown_process_count": 0,
        "synthetic_only": True,
        "offline": True,
    }
    body["ledger_digest"] = digest_ref(body)
    return body



def _endpoint_from_lsof_name(name: str) -> Optional[Tuple[str, int]]:
    match = re.search(r"(?P<host>[^\s:]+):(?P<port>[0-9]+)(?:\s+\(LISTEN\))?$", name)
    if not match:
        return None
    return match.group("host"), int(match.group("port"))



def observe_network(output: str, *, boundary: Mapping[str, Any]) -> Dict[str, Any]:
    """Parse listening sockets and require the exact frozen loopback set."""

    if not isinstance(output, str) or not output.strip():
        raise ObserverBlocked("network_observer_unavailable")
    endpoints = boundary.get("network", {}).get("allowed_endpoints", [])
    if not isinstance(endpoints, list) or not endpoints:
        raise ObserverBlocked("network_boundary_missing")
    expected = {(row.get("host"), row.get("port")) for row in endpoints if isinstance(row, Mapping)}
    rows: List[Dict[str, Any]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("command "):
            continue
        parts = line.split()
        if len(parts) < 2:
            raise ObserverBlocked("network_observer_row_incomplete")
        try:
            pid = _parse_int(parts[1], "network.pid")
        except ObserverBlocked:
            raise
        listen_index = next((index for index, token in enumerate(parts) if token == "(LISTEN)"), None)
        if listen_index is None or listen_index == 0:
            raise ObserverBlocked("network_listener_state_missing")
        endpoint_token = parts[listen_index - 1]
        endpoint = _endpoint_from_lsof_name(endpoint_token)
        if endpoint is None:
            raise ObserverBlocked("network_endpoint_invalid")
        host, port = endpoint
        rows.append({"command": parts[0], "pid": pid, "host": host, "port": port, "state": "LISTEN"})
    if not rows:
        raise ObserverBlocked("network_observer_empty")
    observed = {(row["host"], row["port"]) for row in rows}
    if observed != expected:
        raise ObserverBlocked("foreign_or_missing_listener")
    if any(row["host"] != "127.0.0.1" for row in rows):
        raise ObserverBlocked("non_loopback_listener")
    body: Dict[str, Any] = {
        "schema": NETWORK_LEDGER_SCHEMA,
        "version": OBSERVER_VERSION,
        "rows": rows,
        "listener_count": len(rows),
        "synthetic_only": True,
        "offline": True,
    }
    body["ledger_digest"] = digest_ref(body)
    return body



def observe_open_files(output: str, *, allowed_roots: Mapping[str, Path]) -> Dict[str, Any]:
    """Parse an ``lsof -p`` ledger and reject every out-of-root reference."""

    if not isinstance(output, str) or not output.strip():
        raise ObserverBlocked("open_files_observer_unavailable")
    rows: List[Dict[str, Any]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("command "):
            continue
        parts = line.split(None, 8)
        if len(parts) < 9:
            raise ObserverBlocked("open_files_observer_row_incomplete")
        path_text = parts[-1]
        root_name, relative = _relative_to_allowed(path_text, allowed_roots)
        rows.append(
            {
                "command": parts[0],
                "pid": _parse_int(parts[1], "open_file.pid"),
                "fd": parts[3],
                "type": parts[4],
                "root": root_name,
                "relative_path": relative,
            }
        )
    if not rows:
        raise ObserverBlocked("open_files_observer_empty")
    body: Dict[str, Any] = {
        "schema": OPEN_FILES_LEDGER_SCHEMA,
        "version": OBSERVER_VERSION,
        "rows": rows,
        "reference_count": len(rows),
        "synthetic_only": True,
        "offline": True,
    }
    body["ledger_digest"] = digest_ref(body)
    return body



def snapshot_runtime_tree(runtime_root: Path) -> Dict[str, Any]:
    """Hash a runtime tree without following an escaping symlink."""

    root = _root(runtime_root)
    rows: List[Dict[str, Any]] = []
    if root.exists():
        if not root.is_dir():
            raise ObserverBlocked("runtime_tree_not_directory")
        try:
            paths = sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
            for path in paths:
                resolved = _root(path)
                if not _under(resolved, root):
                    raise ObserverBlocked("runtime_tree_symlink_escape")
                if path.is_symlink():
                    raise ObserverBlocked("runtime_tree_symlink_observed")
                if not path.is_file():
                    continue
                data = path.read_bytes()
                rows.append(
                    {
                        "relative_path": path.relative_to(root).as_posix(),
                        "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
                        "bytes": len(data),
                    }
                )
        except OSError as exc:
            raise ObserverBlocked("filesystem_observer_unavailable") from exc
    body: Dict[str, Any] = {
        "schema": FILESYSTEM_LEDGER_SCHEMA,
        "version": OBSERVER_VERSION,
        "root": "runtime_root",
        "rows": rows,
        "file_count": len(rows),
        "synthetic_only": True,
        "offline": True,
    }
    body["ledger_digest"] = digest_ref(body)
    return body



def _read_ledger(path: Path, schema: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ObserverBlocked("app_ledger_unavailable") from exc
    if not isinstance(value, dict) or value.get("schema") != schema or value.get("version") != OBSERVER_VERSION:
        raise ObserverBlocked("app_ledger_schema_mismatch")
    if not isinstance(value.get("events"), list):
        raise ObserverBlocked("app_ledger_events_missing")
    _canonical_digest(value, "ledger_digest")
    return value



def read_app_ledgers(runtime_root: Path) -> Dict[str, Any]:
    root = _root(runtime_root)
    return {
        "write": _read_ledger(root / "app_write_ledger.json", "mm-monitoring-r8-g6-app-write-ledger-v1"),
        "adapter": _read_ledger(root / "adapter_call_ledger.json", "mm-monitoring-r8-g6-adapter-call-ledger-v1"),
    }



def _validate_app_ledgers(ledgers: Mapping[str, Any]) -> None:
    write = ledgers.get("write")
    adapter = ledgers.get("adapter")
    if not isinstance(write, Mapping) or not isinstance(adapter, Mapping):
        raise ObserverBlocked("app_ledgers_incomplete")
    for event in write.get("events", []):
        if not isinstance(event, Mapping):
            raise ObserverBlocked("write_ledger_row_invalid")
        path = event.get("path")
        if not isinstance(path, str) or path.startswith("/") or any(part in {"", ".", ".."} for part in path.split("/")):
            raise ObserverBlocked("write_ledger_path_invalid")
        identity = event.get("identity")
        if not isinstance(identity, Mapping):
            raise ObserverBlocked("write_ledger_identity_missing")
        for key in ("project_ref", "admission_id", "run_ref", "analysis_mode", "binding_digest"):
            if not isinstance(identity.get(key), str):
                raise ObserverBlocked("write_ledger_identity_missing")
            if key == "binding_digest":
                if not re.fullmatch(r"sha256:[0-9a-f]{64}", identity[key]):
                    raise ObserverBlocked("write_ledger_binding_invalid")
            elif key == "analysis_mode":
                if identity[key] not in {*_synthetic_ego.ANALYSIS_MODES, "task"}:
                    raise ObserverBlocked("write_ledger_analysis_mode_invalid")
            elif not identity[key].startswith("synthetic"):
                raise ObserverBlocked("write_ledger_identity_non_synthetic")
    for event in adapter.get("events", []):
        if not isinstance(event, Mapping):
            raise ObserverBlocked("adapter_ledger_row_invalid")
        if (
            event.get("provider") != _synthetic_ego.SYNTHETIC_PROVIDER
            or event.get("model") != _synthetic_ego.SYNTHETIC_MODEL
            or event.get("adapter_id") != _synthetic_ego.RECORDED_ADAPTER_ID
            or event.get("adapter_kind") != _synthetic_ego.RECORDED_ADAPTER_KIND
            or event.get("synthetic_only") is not True
            or event.get("offline") is not True
            or event.get("fallback_attempt") is not False
            or event.get("real_model_call") is not False
        ):
            raise ObserverBlocked("non_synthetic_or_fallback_adapter")



def _changed_paths(before: Mapping[str, Any], after: Mapping[str, Any]) -> List[str]:
    before_rows = {row["relative_path"]: row for row in before.get("rows", [])}
    after_rows = {row["relative_path"]: row for row in after.get("rows", [])}
    return sorted(
        path
        for path in set(before_rows) | set(after_rows)
        if before_rows.get(path) != after_rows.get(path)
    )



def _ledger_paths(ledgers: Mapping[str, Any]) -> set[str]:
    paths = {"app_write_ledger.json", "adapter_call_ledger.json", "app_state.json", "app.lock"}
    for event in ledgers["write"]["events"]:
        paths.add(str(event["path"]))
        if str(event["path"]).endswith("/state.json"):
            paths.add(str(event["path"]).replace("/state.json", "/files.json"))
    return paths



def reconcile_observation(
    observation: Mapping[str, Any],
    *,
    boundary: Mapping[str, Any],
    ledgers: Mapping[str, Any],
    before_snapshot: Optional[Mapping[str, Any]] = None,
    after_snapshot: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Reconcile independent ledgers with the frozen boundary and app ledgers."""

    try:
        validate_execution_boundary_manifest(boundary)
    except (ManifestError, TypeError) as exc:
        raise ObserverBlocked("execution_boundary_invalid") from exc
    _validate_app_ledgers(ledgers)
    process = observation.get("process_tree")
    network = observation.get("network")
    files = observation.get("open_files")
    if not isinstance(process, Mapping) or not isinstance(network, Mapping) or not isinstance(files, Mapping):
        raise ObserverBlocked("independent_observation_incomplete")
    if process.get("owned_process_count") != 1 or process.get("unknown_process_count") != 0:
        raise ObserverBlocked("process_observation_not_reconciled")
    expected_listener_count = len(boundary["network"]["allowed_endpoints"])
    if network.get("listener_count") != expected_listener_count:
        raise ObserverBlocked("network_observation_not_reconciled")
    if not files.get("reference_count"):
        raise ObserverBlocked("open_files_observation_empty")
    if before_snapshot is not None or after_snapshot is not None:
        if not isinstance(before_snapshot, Mapping) or not isinstance(after_snapshot, Mapping):
            raise ObserverBlocked("filesystem_observation_incomplete")
        observed_changes = _changed_paths(before_snapshot, after_snapshot)
        unknown_changes = sorted(set(observed_changes) - _ledger_paths(ledgers))
        if unknown_changes:
            raise ObserverBlocked("filesystem_write_ledger_mismatch")
    result: Dict[str, Any] = {
        "schema": RECONCILIATION_SCHEMA,
        "version": OBSERVER_VERSION,
        "status": "reconciled",
        "boundary_manifest_digest": boundary.get("manifest_digest"),
        "process_ledger_digest": process.get("ledger_digest"),
        "network_ledger_digest": network.get("ledger_digest"),
        "open_files_ledger_digest": files.get("ledger_digest"),
        "write_ledger_digest": ledgers["write"].get("ledger_digest"),
        "adapter_ledger_digest": ledgers["adapter"].get("ledger_digest"),
        "observed_change_count": len(_changed_paths(before_snapshot, after_snapshot)) if before_snapshot is not None and after_snapshot is not None else None,
        "unknown_change_count": 0,
        "synthetic_only": True,
        "offline": True,
    }
    result["reconciliation_digest"] = digest_ref(result)
    return result



def _default_command_runner(command: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            list(command),
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ObserverBlocked("observer_command_unavailable") from exc
    if completed.returncode != 0 or not completed.stdout.strip():
        raise ObserverBlocked("observer_command_failed")
    return completed.stdout



def observe_and_reconcile(
    *,
    boundary: Mapping[str, Any],
    entry: Mapping[str, Any],
    runtime_root: Path,
    release_root: Optional[Path] = None,
    command_runner: Optional[Callable[[Sequence[str]], str]] = None,
    process_output: Optional[str] = None,
    network_output: Optional[str] = None,
    open_files_output: Optional[str] = None,
    before_snapshot: Optional[Mapping[str, Any]] = None,
    after_snapshot: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Collect all independent ledgers and return canonical reconciliation."""

    validate_entry_manifest(entry)
    validate_execution_boundary_manifest(boundary)
    run_command = command_runner or _default_command_runner
    process_text = process_output or run_command(("ps", "-axo", "pid=,ppid=,comm=,args="))
    process_ledger = observe_process_tree(process_text, boundary=boundary, entry=entry)
    pid = process_ledger["rows"][0]["pid"]
    network_text = network_output or run_command(("lsof", "-nP", "-iTCP", "-sTCP:LISTEN"))
    network_ledger = observe_network(network_text, boundary=boundary)
    open_text = open_files_output or run_command(("lsof", "-nP", "-p", str(pid)))
    resolved_release = _root(release_root) if release_root is not None else _root(Path.cwd())
    runtime = _root(runtime_root)
    allowed_roots = {"runtime_root": runtime, "release_root": resolved_release}
    open_files_ledger = observe_open_files(open_text, allowed_roots=allowed_roots)
    ledgers = read_app_ledgers(runtime)
    observation: Dict[str, Any] = {
        "schema": OBSERVER_SCHEMA,
        "version": OBSERVER_VERSION,
        "process_tree": process_ledger,
        "network": network_ledger,
        "open_files": open_files_ledger,
        "filesystem": {
            "before": _clone_snapshot(before_snapshot) if before_snapshot is not None else None,
            "after": _clone_snapshot(after_snapshot) if after_snapshot is not None else snapshot_runtime_tree(runtime),
        },
        "synthetic_only": True,
        "offline": True,
    }
    observation["observation_digest"] = digest_ref(observation)
    reconciliation = reconcile_observation(
        observation,
        boundary=boundary,
        ledgers=ledgers,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
    )
    observation["reconciliation"] = reconciliation
    observation["observation_digest"] = digest_ref({key: value for key, value in observation.items() if key != "observation_digest"})
    return observation



def _clone_snapshot(value: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    try:
        return json.loads(json.dumps(dict(value), ensure_ascii=False))
    except (TypeError, ValueError) as exc:
        raise ObserverBlocked("filesystem_snapshot_invalid") from exc



def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Independent synthetic G6 observer")
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        release_root = _root(args.release_root)
        manifests = load_all_manifests(base_dir=release_root, release_root=release_root)
        evidence = observe_and_reconcile(
            boundary=manifests["execution_boundary"],
            entry=manifests["entry"],
            runtime_root=args.runtime_root,
            release_root=release_root,
        )
    except (ObserverBlocked, ManifestError, OSError, ValueError) as exc:
        if args.json:
            print(json.dumps({"schema": RECONCILIATION_SCHEMA, "version": OBSERVER_VERSION, "status": "blocked", "reason": str(exc), "synthetic_only": True, "offline": True}, ensure_ascii=False, sort_keys=True))
        else:
            print("独立边界观察未完成，当前证据已阻止。")
        return 2
    if args.json:
        print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
    else:
        print("独立边界观察已完成。")
    return 0


__all__ = [
    "APP_SCHEMA",
    "FILESYSTEM_LEDGER_SCHEMA",
    "FrozenCommandRunner",
    "NETWORK_LEDGER_SCHEMA",
    "OBSERVER_SCHEMA",
    "OBSERVER_VERSION",
    "OPEN_FILES_LEDGER_SCHEMA",
    "ObserverBlocked",
    "PROCESS_LEDGER_SCHEMA",
    "RECONCILIATION_SCHEMA",
    "main",
    "observe_and_reconcile",
    "observe_network",
    "observe_open_files",
    "observe_process_tree",
    "read_app_ledgers",
    "reconcile_observation",
    "snapshot_runtime_tree",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
