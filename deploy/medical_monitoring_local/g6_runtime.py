#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Persistent, synthetic-only runtime seams for the actual G6 application.

The module owns no server and imports no actual-app lifecycle code.  It stores
run identity, notification facts, task state, and the app write/call ledgers
only below the caller-provided runtime root.  Every identity is reconstructed
from the canonical synthetic bundle before a state transition is accepted.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    from canonical_evidence import canonical_json, canonical_json_bytes, digest_ref
    import synthetic_ego as _synthetic_ego
except ImportError:  # pragma: no cover - package-style import support
    from .canonical_evidence import canonical_json, canonical_json_bytes, digest_ref
    from . import synthetic_ego as _synthetic_ego


RUNTIME_API_SCHEMA = "mm-monitoring-r8-g6-actual-runtime-api-v1"
RUNTIME_API_VERSION = "1"
RUN_STORE_SCHEMA = "mm-monitoring-r8-g6-persistent-run-store-v1"
NOTIFICATION_STORE_SCHEMA = "mm-monitoring-r8-g6-persistent-notification-store-v1"
TASK_STATE_SCHEMA = "mm-monitoring-r8-g6-actual-task-state-v1"
TASK_ENGINE_SCHEMA = "mm-monitoring-r8-g6-actual-task-engine-v1"
WRITE_LEDGER_SCHEMA = "mm-monitoring-r8-g6-app-write-ledger-v1"
ADAPTER_LEDGER_SCHEMA = "mm-monitoring-r8-g6-adapter-call-ledger-v1"
RUN_STORE_VERSION = "1"
ENTRY_ROUTE = "/?g6=synthetic"
TASKS_DIRECTORY = "tasks"

TERMINAL_STATUSES = tuple(_synthetic_ego.TERMINAL_STATUSES)
CAPABILITY_STATES = tuple(_synthetic_ego.CAPABILITY_STATES)
TASK_KEYS = tuple(_synthetic_ego.TASK_KEYS)

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SAFE_TASK = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class RuntimeStoreError(ValueError):
    """Raised when persisted runtime data or a requested transition is invalid."""


class StaleRuntimeCallbackError(RuntimeStoreError):
    """Raised when a callback does not match the current immutable run identity."""


class NotificationRuntimeError(RuntimeStoreError):
    """Raised when a durable notification fact cannot be reconciled."""


class TaskRuntimeError(RuntimeStoreError):
    """Raised when a task action or task state is not contract-valid."""



def _clone(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False))
    except (TypeError, ValueError) as exc:
        raise RuntimeStoreError("runtime_value_not_json") from exc



def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RuntimeStoreError(f"{field}_must_be_object")
    return value



def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeStoreError(f"{field}_must_be_non_empty_string")
    return value.strip()



def _require_id(value: Any, field: str) -> str:
    text = _require_text(value, field)
    if not _SAFE_ID.fullmatch(text):
        raise RuntimeStoreError(f"{field}_must_be_safe_id")
    return text



def _require_digest(value: Any, field: str) -> str:
    text = _require_text(value, field)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", text):
        raise RuntimeStoreError(f"{field}_must_be_sha256")
    return text



def _digest_without(value: Mapping[str, Any], *fields: str) -> str:
    excluded = set(fields)
    return digest_ref({key: _clone(item) for key, item in value.items() if key not in excluded})
def _require_persisted_digest(value: Mapping[str, Any], field: str, error: str) -> None:
    expected = value.get(field)
    if not isinstance(expected, str) or _digest_without(value, field) != expected:
        raise RuntimeStoreError(error)





def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Optional[Path] = None
    try:
        handle = tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
            delete=False,
        )
        temporary = Path(handle.name)
        with handle:
            handle.write(canonical_json_bytes(dict(payload)) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary), str(path))
    except OSError as exc:
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass
        raise RuntimeStoreError(f"runtime_write_failed:{path.name}") from exc



def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeStoreError(f"runtime_read_failed:{path.name}") from exc
    if not isinstance(raw, dict):
        raise RuntimeStoreError(f"runtime_object_required:{path.name}")
    return raw



def _relative_runtime_path(path: str) -> str:
    value = path.replace("\\", "/").strip("/")
    if not value or any(part in {".", ".."} for part in value.split("/")):
        raise RuntimeStoreError("runtime_path_invalid")
    return value


class SyntheticRuntimeStore:
    """Atomic actual-app store for one synthetic runtime root."""

    def __init__(self, runtime_root: Path) -> None:
        self.runtime_root = Path(runtime_root).expanduser().resolve()
        try:
            self.runtime_root.mkdir(parents=True, exist_ok=True)
            os.chmod(self.runtime_root, 0o700)
        except OSError as exc:
            raise RuntimeStoreError("runtime_root_unwritable") from exc
        self.run_path = self.runtime_root / "g6_runs.json"
        self.notification_path = self.runtime_root / "g6_notifications.json"
        self.write_ledger_path = self.runtime_root / "app_write_ledger.json"
        self.adapter_ledger_path = self.runtime_root / "adapter_call_ledger.json"
        self.tasks_root = self.runtime_root / TASKS_DIRECTORY

    # ------------------------------------------------------------------
    # Canonical identity and persistence primitives
    # ------------------------------------------------------------------

    def _bundle_context(self, project_ref: str, analysis_mode: str, run_ref: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        project_ref = _require_id(project_ref, "project_ref")
        if analysis_mode not in _synthetic_ego.ANALYSIS_MODES:
            raise RuntimeStoreError("analysis_mode_invalid")
        bundle = _synthetic_ego.validate_synthetic_audience_bundle(
            _synthetic_ego.build_synthetic_audience_bundle()
        )
        fixture = bundle["fixture"]
        candidates = [
            row
            for row in bundle["run_bindings"]
            if row["project_ref"] == project_ref and row["analysis_mode"] == analysis_mode
        ]
        if len(candidates) != 1:
            raise RuntimeStoreError("run_binding_not_found")
        binding = candidates[0]
        if run_ref is not None and binding["run_ref"] != _require_id(run_ref, "run_ref"):
            raise RuntimeStoreError("run_binding_ref_mismatch")
        return _clone(fixture), _clone(binding), _clone(bundle)

    @staticmethod
    def _identity(binding: Mapping[str, Any]) -> Dict[str, str]:
        identity = {
            "project_ref": _require_id(binding.get("project_ref"), "identity.project_ref"),
            "admission_id": _require_id(binding.get("admission_id"), "identity.admission_id"),
            "run_ref": _require_id(binding.get("run_ref"), "identity.run_ref"),
            "analysis_mode": _require_text(binding.get("analysis_mode"), "identity.analysis_mode"),
            "binding_digest": _require_digest(binding.get("binding_digest"), "identity.binding_digest"),
        }
        return identity

    @staticmethod
    def identity_key(identity: Mapping[str, Any]) -> str:
        fields = {
            "project_ref": _require_id(identity.get("project_ref"), "identity.project_ref"),
            "admission_id": _require_id(identity.get("admission_id"), "identity.admission_id"),
            "run_ref": _require_id(identity.get("run_ref"), "identity.run_ref"),
            "analysis_mode": _require_text(identity.get("analysis_mode"), "identity.analysis_mode"),
            "binding_digest": _require_digest(identity.get("binding_digest"), "identity.binding_digest"),
        }
        return canonical_json(fields)

    @classmethod
    def _load_store(self, path: Path, schema: str) -> Dict[str, Any]:
        value = _read_json(path)
        if value is None:
            return self._new_store(schema)
        if value.get("schema") != schema or value.get("version") != RUN_STORE_VERSION:
            raise RuntimeStoreError(f"store_schema_mismatch:{path.name}")
        if not isinstance(value.get("records"), dict) or not isinstance(value.get("events"), list):
            raise RuntimeStoreError(f"store_shape_mismatch:{path.name}")
        _require_persisted_digest(value, "store_digest", f"store_digest_mismatch:{path.name}")
        return value
            return self._new_store(schema)
        if value.get("schema") != schema or value.get("version") != RUN_STORE_VERSION:
            raise RuntimeStoreError(f"store_schema_mismatch:{path.name}")
        if not isinstance(value.get("records"), dict) or not isinstance(value.get("events"), list):
            raise RuntimeStoreError(f"store_shape_mismatch:{path.name}")
        return value

    def _load_runs(self) -> Dict[str, Any]:
        value = _read_json(self.run_path)
        if value is None:
            return {"schema": RUN_STORE_SCHEMA, "version": RUN_STORE_VERSION, "current": None, "events": []}
        if value.get("schema") != RUN_STORE_SCHEMA or value.get("version") != RUN_STORE_VERSION:
            raise RuntimeStoreError("run_store_schema_mismatch")
        if value.get("current") is not None and not isinstance(value.get("current"), dict):
            raise RuntimeStoreError("run_store_current_mismatch")
        if not isinstance(value.get("events"), list):
            raise RuntimeStoreError("run_store_events_mismatch")
        return value

    def _load_ledger(self, path: Path, schema: str) -> Dict[str, Any]:
        value = _read_json(path)
        if value is None:
            return {"schema": schema, "version": RUN_STORE_VERSION, "events": []}
        if value.get("schema") != schema or value.get("version") != RUN_STORE_VERSION:
            raise RuntimeStoreError(f"ledger_schema_mismatch:{path.name}")
        if not isinstance(value.get("events"), list):
            raise RuntimeStoreError(f"ledger_events_mismatch:{path.name}")
        return value

    def _record_write(self, operation: str, relative_path: str, identity: Optional[Mapping[str, Any]] = None) -> None:
        relative_path = _relative_runtime_path(relative_path)
        ledger = self._load_ledger(self.write_ledger_path, WRITE_LEDGER_SCHEMA)
        event: Dict[str, Any] = {
            "sequence": len(ledger["events"]) + 1,
            "operation": _require_text(operation, "write.operation"),
            "path": relative_path,
            "synthetic_only": True,
            "offline": True,
        }
        if identity is not None:
            event["identity"] = _clone(dict(identity))
            event["run_key"] = self.identity_digest(identity)
        ledger["events"].append(event)
        ledger["ledger_digest"] = _digest_without(ledger, "ledger_digest")
        _atomic_write_json(self.write_ledger_path, ledger)

    def _record_adapter_call(
        self,
        kind: str,
        identity: Mapping[str, Any],
        *,
        outcome: str = "recorded",
        fallback_attempt: bool = False,
        real_model_call: bool = False,
    ) -> None:
        ledger = self._load_ledger(self.adapter_ledger_path, ADAPTER_LEDGER_SCHEMA)
        event = {
            "sequence": len(ledger["events"]) + 1,
            "kind": _require_text(kind, "adapter.kind"),
            "outcome": _require_text(outcome, "adapter.outcome"),
            "identity": _clone(dict(identity)),
            "run_key": self.identity_digest(identity),
            "provider": _synthetic_ego.SYNTHETIC_PROVIDER,
            "model": _synthetic_ego.SYNTHETIC_MODEL,
            "adapter_id": _synthetic_ego.RECORDED_ADAPTER_ID,
            "adapter_kind": _synthetic_ego.RECORDED_ADAPTER_KIND,
            "synthetic_only": True,
            "offline": True,
            "fallback_attempt": bool(fallback_attempt),
            "real_model_call": bool(real_model_call),
        }
        ledger["events"].append(event)
        ledger["ledger_digest"] = _digest_without(ledger, "ledger_digest")
        _atomic_write_json(self.adapter_ledger_path, ledger)

    def _write_runs(self, value: Mapping[str, Any]) -> None:
        _atomic_write_json(self.run_path, value)

    def _binding_for_identity(self, identity: Mapping[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        fixture, binding, _bundle = self._bundle_context(
            str(identity.get("project_ref")),
            str(identity.get("analysis_mode")),
            str(identity.get("run_ref")),
        )
        expected = self._identity(binding)
        supplied = {
            key: identity.get(key)
            for key in ("project_ref", "admission_id", "run_ref", "analysis_mode", "binding_digest")
        }
        if supplied != expected:
            raise StaleRuntimeCallbackError("run_identity_mismatch")
        if binding["fixture_digest"] != fixture["fixture_digest"]:
            raise StaleRuntimeCallbackError("run_fixture_digest_mismatch")
        return fixture, binding

    def _current_state(self) -> Optional[Dict[str, Any]]:
        runs = self._load_runs()
        current = runs.get("current")
        return _clone(current) if isinstance(current, dict) else None

    def _validate_state(self, state: Mapping[str, Any]) -> Dict[str, Any]:
        raw = _clone(dict(_require_mapping(state, "run_state")))
        if raw.get("schema") != RUN_STORE_SCHEMA or raw.get("version") != RUN_STORE_VERSION:
            raise RuntimeStoreError("run_state_schema_mismatch")
        state_digest = raw.get("state_digest")
        if not isinstance(state_digest, str) or _digest_without(raw, "state_digest") != state_digest:
            raise RuntimeStoreError("run_state_digest_mismatch")
        identity = _require_mapping(raw.get("identity"), "run_state.identity")
        self._binding_for_identity(identity)
        if raw.get("run_key") != self.identity_digest(identity):
            raise RuntimeStoreError("run_state_key_mismatch")
        if raw.get("status") not in {"prepared", "running", "complete", "failed", "partial", "final_partial", "truncated", "timed_out", "cancelled", "interrupted", "blocked"}:
            raise RuntimeStoreError("run_state_status_invalid")
        if not isinstance(raw.get("cursor"), int) or raw["cursor"] < 0:
            raise RuntimeStoreError("run_state_cursor_invalid")
        return raw

    def _assert_request_matches(self, state: Mapping[str, Any], request: Optional[Mapping[str, Any]]) -> None:
        if request is None:
            return
        supplied = _require_mapping(request, "run_request")
        if supplied.get("run_key") is not None and supplied.get("run_key") != state.get("run_key"):
            raise StaleRuntimeCallbackError("run_key_mismatch")
        identity = state["identity"]
        for key in ("project_ref", "admission_id", "run_ref", "analysis_mode", "binding_digest"):
            if supplied.get(key) is not None and supplied.get(key) != identity.get(key):
                raise StaleRuntimeCallbackError(f"run_{key}_mismatch")
        if supplied.get("profile_binding_digest") is not None and supplied.get("profile_binding_digest") != state.get("profile_binding_digest"):
            raise StaleRuntimeCallbackError("profile_binding_digest_mismatch")
        if supplied.get("fixture_digest") is not None and supplied.get("fixture_digest") != state.get("fixture_digest"):
            raise StaleRuntimeCallbackError("fixture_digest_mismatch")

    def _state_projection(self, state: Mapping[str, Any]) -> Dict[str, Any]:
        result = {
            "schema": RUNTIME_API_SCHEMA,
            "version": RUNTIME_API_VERSION,
            "ready": True,
            "synthetic_only": True,
            "offline": True,
            "run_key": state["run_key"],
            "identity": _clone(state["identity"]),
            "profile_binding_digest": state["profile_binding_digest"],
            "fixture_digest": state["fixture_digest"],
            "source_manifest_digest": state["source_manifest_digest"],
            "output_manifest_digest": state["output_manifest_digest"],
            "revision": state["revision"],
            "status": state["status"],
            "cursor": state["cursor"],
            "event_count": state["event_count"],
            "progress": state["progress"],
            "terminal_status": state["terminal_status"],
            "window_route": ENTRY_ROUTE,
        }
        if state.get("evidence") is not None:
            result["evidence"] = _clone(state["evidence"])
        return result

    def prepare_run(
        self,
        project_ref: str = "synthetic-project-alpha",
        analysis_mode: str = "full",
        *,
        run_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        fixture, binding, _bundle = self._bundle_context(project_ref, analysis_mode, run_ref)
        identity = self._identity(binding)
        run_key = self.identity_digest(identity)
        runs = self._load_runs()
        existing = runs.get("current")
        if isinstance(existing, dict):
            state = self._validate_state(existing)
            if state.get("run_key") != run_key:
                raise RuntimeStoreError("another_run_already_selected")
            return self._state_projection(state)
        analysis = next(
            row
            for row in fixture["analysis_inputs"]
            if row["project_ref"] == binding["project_ref"] and row["analysis_mode"] == binding["analysis_mode"]
        )
        state: Dict[str, Any] = {
            "schema": RUN_STORE_SCHEMA,
            "version": RUN_STORE_VERSION,
            "identity": identity,
            "run_key": run_key,
            "profile_binding_digest": binding["profile_binding_digest"],
            "fixture_digest": binding["fixture_digest"],
            "source_manifest_digest": binding["source_manifest_digest"],
            "output_manifest_digest": binding["output_manifest_digest"],
            "revision": "synthetic-revision-%s" % binding["run_ref"],
            "status": "prepared",
            "cursor": 0,
            "event_count": len(analysis["event_refs"]),
            "progress": 0,
            "terminal_status": analysis["terminal_status"],
            "binding": binding,
            "evidence": None,
        }
        state["state_digest"] = _digest_without(state, "state_digest")
        runs["current"] = state
        runs["events"].append({"sequence": len(runs["events"]) + 1, "operation": "prepare", "run_key": run_key, "identity": identity})
        runs["store_digest"] = _digest_without(runs, "store_digest")
        self._write_runs(runs)
        self._record_write("prepare_run", "g6_runs.json", identity)
        return self._state_projection(state)

    def start_run(self, request: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        state = self._current_state()
        if state is None:
            raise RuntimeStoreError("run_not_prepared")
        state = self._validate_state(state)
        self._assert_request_matches(state, request)
        if state["status"] == "prepared":
            state["status"] = "running"
            state["state_digest"] = _digest_without(state, "state_digest")
            runs = self._load_runs()
            runs["current"] = state
            runs["events"].append({"sequence": len(runs["events"]) + 1, "operation": "start", "run_key": state["run_key"], "identity": state["identity"]})
            runs["store_digest"] = _digest_without(runs, "store_digest")
            self._write_runs(runs)
            self._record_write("start_run", "g6_runs.json", state["identity"])
        return self._state_projection(state)

    def read_run(self, request: Optional[Mapping[str, Any]] = None, *, advance: bool = False) -> Dict[str, Any]:
        state = self._current_state()
        if state is None:
            raise RuntimeStoreError("run_not_prepared")
        state = self._validate_state(state)
        self._assert_request_matches(state, request)
        if advance and state["status"] == "running":
            if state["cursor"] < state["event_count"]:
                state["cursor"] += 1
                state["progress"] = int((state["cursor"] * 100) / max(1, state["event_count"]))
            if state["cursor"] >= state["event_count"]:
                state["progress"] = 100
                state["status"] = state["terminal_status"]
            state["state_digest"] = _digest_without(state, "state_digest")
            runs = self._load_runs()
            runs["current"] = state
            runs["events"].append({"sequence": len(runs["events"]) + 1, "operation": "read_advance", "run_key": state["run_key"], "cursor": state["cursor"], "identity": state["identity"]})
            runs["store_digest"] = _digest_without(runs, "store_digest")
            self._write_runs(runs)
            self._record_write("read_run", "g6_runs.json", state["identity"])
        return self._state_projection(state)

    def restore_run(self, request: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        state = self._current_state()
        if state is None:
            raise RuntimeStoreError("run_not_found")
        state = self._validate_state(state)
        self._assert_request_matches(state, request)
        return self._state_projection(state)

    def accept_callback(self, callback: Mapping[str, Any]) -> Dict[str, Any]:
        state = self._current_state()
        if state is None:
            raise StaleRuntimeCallbackError("callback_without_current_run")
        state = self._validate_state(state)
        callback = _require_mapping(callback, "callback")
        self._assert_request_matches(state, callback)
        if callback.get("revision") != state["revision"]:
            raise StaleRuntimeCallbackError("callback_revision_mismatch")
        if callback.get("profile_binding_digest") != state["profile_binding_digest"]:
            raise StaleRuntimeCallbackError("callback_profile_binding_mismatch")
        if callback.get("fixture_digest") != state["fixture_digest"]:
            raise StaleRuntimeCallbackError("callback_fixture_mismatch")
        if callback.get("status") is not None and callback["status"] not in {"running", *TERMINAL_STATUSES}:
            raise StaleRuntimeCallbackError("callback_status_invalid")
        if callback.get("cursor") is not None:
            cursor = callback["cursor"]
            if not isinstance(cursor, int) or cursor < state["cursor"] or cursor > state["event_count"]:
                raise StaleRuntimeCallbackError("callback_cursor_invalid")
        return self._state_projection(state)

    # ------------------------------------------------------------------
    # Durable notification facts and precise navigation
    # ------------------------------------------------------------------

    @staticmethod
    def _notification_key(identity: Mapping[str, Any], terminal_status: str, capability_state: str) -> str:
        return digest_ref(
            {
                "identity": _clone(dict(identity)),
                "terminal_status": terminal_status,
                "capability_state": capability_state,
            }
        )

    @staticmethod
    def _notification_target(identity: Mapping[str, Any], terminal_status: str, binding_digest: str) -> Dict[str, str]:
        target_kind = "result" if terminal_status in {"complete", "partial"} else "explanation"
        query = urllib.parse.urlencode(
            [
                ("g6", "synthetic"),
                ("view", target_kind),
                ("project_ref", identity["project_ref"]),
                ("admission_id", identity["admission_id"]),
                ("run_ref", identity["run_ref"]),
                ("analysis_mode", identity["analysis_mode"]),
                ("binding_digest", binding_digest),
            ]
        )
        return {"path": "/?" + query, "target_kind": target_kind, "action": "navigate_only"}

    def _binding_for_notification(self, request: Optional[Mapping[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        supplied = _require_mapping(request or {}, "notification_request")
        current = self._current_state()
        if current is not None and any(supplied.get(key) is not None for key in ("run_key", "project_ref", "admission_id", "run_ref", "analysis_mode", "binding_digest")):
            state = self._validate_state(current)
            self._assert_request_matches(state, supplied)
            return self._binding_for_identity(state["identity"])
        project_ref = str(supplied.get("project_ref") or (current or {}).get("identity", {}).get("project_ref") or "synthetic-project-alpha")
        analysis_mode = str(supplied.get("analysis_mode") or (current or {}).get("identity", {}).get("analysis_mode") or "full")
        run_ref = supplied.get("run_ref")
        fixture, binding, _bundle = self._bundle_context(project_ref, analysis_mode, str(run_ref) if run_ref is not None else None)
        return fixture, binding

    def _record_notification_for_binding(
        self,
        fixture: Mapping[str, Any],
        binding: Mapping[str, Any],
        terminal_status: str,
        capability_state: str,
        terminal_revision: Optional[str] = None,
    ) -> Dict[str, Any]:
        if terminal_status not in TERMINAL_STATUSES:
            raise NotificationRuntimeError("terminal_status_invalid")
        if capability_state not in CAPABILITY_STATES:
            raise NotificationRuntimeError("capability_state_invalid")
        identity = self._identity(binding)
        key = self._notification_key(identity, terminal_status, capability_state)
        revision = terminal_revision or "synthetic-terminal-revision-%s-%s" % (binding["run_ref"], terminal_status)
        _require_id(revision, "terminal_revision")
        target = self._notification_target(identity, terminal_status, binding["binding_digest"])
        body: Dict[str, Any] = {
            "schema": "mm-monitoring-r8-g6-actual-notification-fact-v1",
            "version": "1",
            "record_key": key,
            "identity": identity,
            "terminal_status": terminal_status,
            "notification_status": "analysis_complete" if terminal_status == "complete" else terminal_status,
            "capability_state": capability_state,
            "terminal_revision": revision,
            "fixture_digest": fixture["fixture_digest"],
            "profile_binding_digest": binding["profile_binding_digest"],
            "binding_digest": binding["binding_digest"],
            "source_manifest_digest": binding["source_manifest_digest"],
            "output_manifest_digest": binding["output_manifest_digest"],
            "application_record": {"persistent": True, "recorded": True},
            "system_record": {"attempted": False, "presented": False, "deferred_to_visual_packet": True},
            "channel_evidence": "unknown",
            "system_attempt_count": 0,
            "navigation": {"status": "ok", "intent": target},
            "synthetic_only": True,
            "offline": True,
        }
        body["fact_digest"] = _digest_without(body, "fact_digest")
        store = self._load_store(self.notification_path, NOTIFICATION_STORE_SCHEMA)
        existing = store["records"].get(key)
        if existing is not None:
            if existing != body:
                raise NotificationRuntimeError("notification_replay_identity_mismatch")
            return _clone(existing)
        store["records"][key] = body
        store["events"].append({"sequence": len(store["events"]) + 1, "operation": "record", "record_key": key, "identity": identity})
        store["store_digest"] = _digest_without(store, "store_digest")
        _atomic_write_json(self.notification_path, store)
        self._record_write("notification_record", "g6_notifications.json", identity)
        self._record_adapter_call("notification_fact", identity)
        return _clone(body)

    def record_notification(
        self,
        terminal_status: str,
        capability_state: str,
        request: Optional[Mapping[str, Any]] = None,
        *,
        terminal_revision: Optional[str] = None,
    ) -> Dict[str, Any]:
        fixture, binding = self._binding_for_notification(request)
        return self._record_notification_for_binding(
            fixture,
            binding,
            terminal_status,
            capability_state,
            terminal_revision,
        )

    def record_notification_matrix(self) -> Dict[str, Any]:
        bundle = _synthetic_ego.validate_synthetic_audience_bundle(
            _synthetic_ego.build_synthetic_audience_bundle()
        )
        rows: List[Dict[str, Any]] = []
        for index, (terminal_status, capability_state) in enumerate(
            (status, capability)
            for status in TERMINAL_STATUSES
            for capability in CAPABILITY_STATES
        ):
            binding = bundle["run_bindings"][index % len(bundle["run_bindings"])]
            row = self._record_notification_for_binding(
                bundle["fixture"],
                binding,
                terminal_status,
                capability_state,
                "synthetic-runtime-terminal-revision-%03d" % (index + 1),
            )
            rows.append(row)
        return {
            "schema": NOTIFICATION_STORE_SCHEMA,
            "version": RUN_STORE_VERSION,
            "status": "recorded",
            "row_count": len(rows),
            "rows": rows,
            "fixture_digest": bundle["fixture"]["fixture_digest"],
            "profile_binding_digest": bundle["fixture"]["profile_binding_digest"],
            "synthetic_only": True,
            "offline": True,
        }

    def list_notifications(self) -> Dict[str, Any]:
        store = self._load_store(self.notification_path, NOTIFICATION_STORE_SCHEMA)
        rows = [store["records"][key] for key in sorted(store["records"])]
        return {
            "schema": RUNTIME_API_SCHEMA,
            "version": RUNTIME_API_VERSION,
            "ready": True,
            "synthetic_only": True,
            "offline": True,
            "row_count": len(rows),
            "rows": _clone(rows),
        }

    def replay_notification(self, record: Mapping[str, Any]) -> Dict[str, Any]:
        value = _require_mapping(record, "notification")
        key = _require_text(value.get("record_key"), "notification.record_key")
        store = self._load_store(self.notification_path, NOTIFICATION_STORE_SCHEMA)
        existing = store["records"].get(key)
        if not isinstance(existing, dict) or existing != dict(value):
            raise NotificationRuntimeError("notification_replay_mismatch")
        if _digest_without(existing, "fact_digest") != existing.get("fact_digest"):
            raise NotificationRuntimeError("notification_fact_digest_mismatch")
        return _clone(existing)

    def navigate_notification(
        self,
        record: Mapping[str, Any],
        *,
        current_revision: Optional[str] = None,
        current_binding_digest: Optional[str] = None,
        target_exists: bool = True,
        target_accessible: bool = True,
    ) -> Dict[str, Any]:
        try:
            fact = self.replay_notification(record)
            state = self._current_state()
            if state is not None:
                state = self._validate_state(state)
                if fact["identity"] != state["identity"]:
                    raise NotificationRuntimeError("navigation_identity_mismatch")
                expected_revision = state["revision"] if current_revision is None else current_revision
                if fact["terminal_revision"] != expected_revision:
                    raise NotificationRuntimeError("navigation_revision_mismatch")
            elif current_revision is not None and fact["terminal_revision"] != current_revision:
                raise NotificationRuntimeError("navigation_revision_mismatch")
            if current_binding_digest is not None and fact["binding_digest"] != current_binding_digest:
                raise NotificationRuntimeError("navigation_binding_mismatch")
            if not target_exists:
                raise NotificationRuntimeError("navigation_target_missing")
            if not target_accessible:
                raise NotificationRuntimeError("navigation_target_inaccessible")
            return {
                "schema": RUNTIME_API_SCHEMA,
                "version": RUNTIME_API_VERSION,
                "status": "ok",
                "side_effect_count": 0,
                "identity": _clone(fact["identity"]),
                "fact_digest": fact["fact_digest"],
                "intent": _clone(fact["navigation"]["intent"]),
                "synthetic_only": True,
                "offline": True,
            }
        except NotificationRuntimeError as exc:
            return {
                "schema": RUNTIME_API_SCHEMA,
                "version": RUNTIME_API_VERSION,
                "status": "blocked",
                "message": "本次运行暂无法打开，请返回工作台查看项目运行记录。",
                "reason": str(exc),
                "side_effect_count": 0,
                "synthetic_only": True,
                "offline": True,
            }

    # ------------------------------------------------------------------
    # Disk-backed §15.4 task engine
    # ------------------------------------------------------------------

    @staticmethod
    def _task_spec(task_key: str) -> Dict[str, Any]:
        if not isinstance(task_key, str) or not _SAFE_TASK.fullmatch(task_key) or task_key not in TASK_KEYS:
            raise TaskRuntimeError("unknown_task_key")
        return next(_clone(item) for item in _synthetic_ego.TASK_SPECS if item["key"] == task_key)

    def _task_path(self, task_key: str) -> Path:
        self._task_spec(task_key)
        return self.tasks_root / task_key

    @staticmethod
    def _task_state_digest(state: Mapping[str, Any]) -> str:
        return _digest_without(state, "state_digest")

    def _load_task_state(self, task_key: str) -> Dict[str, Any]:
        path = self._task_path(task_key) / "state.json"
        value = _read_json(path)
        if value is None:
            raise TaskRuntimeError("task_not_prepared")
        if value.get("schema") != TASK_STATE_SCHEMA or value.get("version") != RUN_STORE_VERSION:
            raise TaskRuntimeError("task_state_schema_mismatch")
        if value.get("task_key") != task_key or value.get("task_spec_digest") != _synthetic_ego.TASK_SPEC_DIGEST:
            raise TaskRuntimeError("task_spec_identity_mismatch")
        if value.get("state_digest") != self._task_state_digest(value):
            raise TaskRuntimeError("task_state_digest_mismatch")
        if not isinstance(value.get("steps"), list) or not isinstance(value.get("current_state"), dict):
            raise TaskRuntimeError("task_state_shape_mismatch")
        return value

    def _write_task_state(self, state: Dict[str, Any], operation: str) -> None:
        state["state_digest"] = self._task_state_digest(state)
        task_key = state["task_key"]
        directory = self._task_path(task_key)
        _atomic_write_json(directory / "state.json", state)
        _atomic_write_json(
            directory / "files.json",
            {
                "schema": "mm-monitoring-r8-g6-task-files-v1",
                "version": RUN_STORE_VERSION,
                "task_key": task_key,
                "state": _clone(state["current_state"]),
                "state_digest": state["state_digest"],
                "synthetic_only": True,
                "offline": True,
            },
        )
        identity = {"project_ref": "synthetic-task", "admission_id": "synthetic-task", "run_ref": "synthetic-task-%s" % task_key, "analysis_mode": "task", "binding_digest": _synthetic_ego.build_synthetic_fixture()["profile_binding_digest"]}
        self._record_write(operation, f"{TASKS_DIRECTORY}/{task_key}/state.json", identity)

    @staticmethod
    def _task_projection(state: Mapping[str, Any]) -> Dict[str, Any]:
        result = {
            "schema": TASK_ENGINE_SCHEMA,
            "version": RUN_STORE_VERSION,
            "ready": True,
            "synthetic_only": True,
            "offline": True,
            "task_key": state["task_key"],
            "task_spec_digest": state["task_spec_digest"],
            "title": state["title"],
            "status": state["status"],
            "action_index": state["action_index"],
            "action_count": state["action_count"],
            "initial_state": _clone(state["initial_state"]),
            "current_state": _clone(state["current_state"]),
            "steps": _clone(state["steps"]),
            "restart_points": _clone(state["restart_points"]),
            "sandbox_relative_path": f"{TASKS_DIRECTORY}/{state['task_key']}",
        }
        if state.get("evidence") is not None:
            result["evidence"] = _clone(state["evidence"])
        return result

    def preview_task(self, task_key: str) -> Dict[str, Any]:
        spec = self._task_spec(task_key)
        try:
            state = self._load_task_state(task_key)
            return self._task_projection(state)
        except TaskRuntimeError as exc:
            if str(exc) != "task_not_prepared":
                raise
        state: Dict[str, Any] = {
            "schema": TASK_STATE_SCHEMA,
            "version": RUN_STORE_VERSION,
            "task_key": task_key,
            "task_spec_digest": _synthetic_ego.TASK_SPEC_DIGEST,
            "title": spec["title"],
            "status": "awaiting_user_actions",
            "action_index": 0,
            "action_count": len(spec["actions"]),
            "initial_state": _clone(spec["initial_state"]),
            "current_state": _clone(spec["initial_state"]),
            "steps": [],
            "restart_points": [],
            "restarted": False,
            "evidence": None,
        }
        self._write_task_state(state, "task_preview")
        return self._task_projection(state)

    @staticmethod
    def _apply_task_transition(task_key: str, state: Dict[str, Any], action_index: int) -> None:
        files = state["current_state"].setdefault("files", {})
        application = state["current_state"].setdefault("application", {})
        if task_key == "export_import":
            files["export_copy"] = "present"
            if action_index == 1:
                files["import_copy"] = "present"
                application["active_run"] = "present"
        elif task_key == "manifest_identity_lineage":
            files["backup_integrity"] = "verified"
            files["summary"] = "identity_lineage_verified"
        elif task_key == "backup_corruption":
            files["corrupt_backup"] = "blocked"
            files["import_attempt"] = "blocked"
        elif task_key == "clean_restore":
            if action_index == 0:
                files["restore_preview"] = "present"
            else:
                files["restore_target"] = "present"
                files["reopened"] = "present"
        elif task_key == "pre_upgrade_protection":
            files["protection_point"] = "present"
        elif task_key == "migration_success":
            files["new_version"] = "present"
            files["migration_marker"] = "complete"
        elif task_key == "critical_boundary_failure":
            files["switch_marker"] = "blocked"
            files["boundary_failure"] = "recorded"
        elif task_key == "original_version_usable":
            files["failed_new_version"] = "blocked"
            files["old_version"] = "usable"
        elif task_key == "actual_rollback":
            files["rollback_marker"] = "complete"
            files["new_version"] = "absent"
            files["old_version"] = "usable"
        elif task_key == "credentials_not_exported_plaintext":
            files["ordinary_export"] = "present"
            files["package_scan"] = "passed"
            files["credential_values"] = 0
            files["credential_field_names"] = 0
            files["environment_members"] = 0
        elif task_key == "default_uninstall_retains_data":
            files["application"] = "removed"
            files["reinstall_marker"] = "present"
            files["project_data"] = "present"
        elif task_key == "explicit_clear_preview_confirm_cancel":
            if action_index == 0:
                application["clear_confirmation"] = "cancelled"
                files["clear_preview"] = "present"
                files["clear_record"] = "absent"
                files["project_data"] = "present"
            else:
                application["clear_confirmation"] = "confirmed"
                files["clear_preview"] = "present"
                files["clear_record"] = "present"
                files["project_data"] = "absent"
        elif task_key == "mixed_version_late_callback_fence":
            application["late_callback"] = "blocked"
            files["late_callback_record"] = "blocked"
            files["output_record"] = "present"
        else:  # pragma: no cover - task keys are validated above
            raise TaskRuntimeError("task_transition_missing")

    def _finish_task_if_ready(self, state: Dict[str, Any], spec: Mapping[str, Any]) -> None:
        if state["action_index"] != state["action_count"]:
            return
        if spec["restart_points"] and not state.get("restarted"):
            state["status"] = "restart_required"
            return
        state["status"] = "passed"
        evidence = {
            "schema": "mm-monitoring-r8-g6-actual-task-evidence-v1",
            "version": RUN_STORE_VERSION,
            "evidence_kind": "actual_app_task_evidence",
            "task_key": state["task_key"],
            "task_spec_digest": state["task_spec_digest"],
            "initial_state": _clone(state["initial_state"]),
            "steps": _clone(state["steps"]),
            "file_state_summary": _clone(state["current_state"]),
            "restart_points": _clone(spec["restart_points"]),
            "negative_assertions": _clone(spec["negative_assertions"]),
            "cleanup": spec["cleanup"],
            "result": "passed",
            "identity_preserved": True,
            "synthetic_only": True,
            "offline": True,
        }
        evidence["task_digest"] = _digest_without(evidence, "task_digest")
        state["evidence"] = evidence

    def perform_task_action(
        self,
        task_key: str,
        action: Optional[str] = None,
        *,
        action_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        spec = self._task_spec(task_key)
        try:
            state = self._load_task_state(task_key)
        except TaskRuntimeError as exc:
            if str(exc) != "task_not_prepared":
                raise
            self.preview_task(task_key)
            state = self._load_task_state(task_key)
        if state["status"] == "passed":
            return self._task_projection(state)
        if state["status"] == "restart_required":
            raise TaskRuntimeError("task_restart_required")
        expected_index = state["action_index"]
        if action_index is not None and action_index != expected_index:
            raise TaskRuntimeError("task_action_index_mismatch")
        if expected_index >= len(spec["actions"]):
            raise TaskRuntimeError("task_actions_exhausted")
        expected = spec["actions"][expected_index]
        if action is not None and action != expected["action"]:
            raise TaskRuntimeError("task_action_mismatch")
        self._apply_task_transition(task_key, state, expected_index)
        state["steps"].append(
            {
                "action": expected["action"],
                "visible_result": expected["visible_result"],
                "restart_required": expected["restart_required"],
                "negative_assertions": _clone(spec["negative_assertions"]),
                "file_state": _clone(state["current_state"]),
            }
        )
        state["action_index"] += 1
        if expected["restart_required"]:
            state["restart_points"] = _clone(spec["restart_points"])
        self._finish_task_if_ready(state, spec)
        self._write_task_state(state, "task_action")
        return self._task_projection(state)

    def confirm_task(self, task_key: str, action: Optional[str] = None) -> Dict[str, Any]:
        return self.perform_task_action(task_key, action)

    def cancel_task(self, task_key: str) -> Dict[str, Any]:
        self._task_spec(task_key)
        try:
            state = self._load_task_state(task_key)
        except TaskRuntimeError as exc:
            if str(exc) != "task_not_prepared":
                raise
            self.preview_task(task_key)
            state = self._load_task_state(task_key)
        if state["status"] == "passed":
            return self._task_projection(state)
        state["status"] = "cancelled"
        state["cancelled"] = True
        self._write_task_state(state, "task_cancel")
        return self._task_projection(state)

    def restart_task(self, task_key: str) -> Dict[str, Any]:
        spec = self._task_spec(task_key)
        state = self._load_task_state(task_key)
        if state["status"] == "passed":
            return self._task_projection(state)
        if state["status"] != "restart_required":
            raise TaskRuntimeError("task_restart_not_required")
        state["restarted"] = True
        self._finish_task_if_ready(state, spec)
        self._write_task_state(state, "task_restart")
        return self._task_projection(state)

    def reset_task(self, task_key: str) -> Dict[str, Any]:
        task_dir = self._task_path(task_key)
        for child in (task_dir / "state.json", task_dir / "files.json"):
            try:
                child.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise TaskRuntimeError("task_reset_failed") from exc
        return self.preview_task(task_key)

    def status_task(self, task_key: str) -> Dict[str, Any]:
        return self._task_projection(self._load_task_state(task_key))

    def list_tasks(self) -> Dict[str, Any]:
        return {
            "schema": TASK_ENGINE_SCHEMA,
            "version": RUN_STORE_VERSION,
            "task_spec_digest": _synthetic_ego.TASK_SPEC_DIGEST,
            "task_count": len(TASK_KEYS),
            "tasks": [
                {"key": spec["key"], "title": spec["title"], "action_count": len(spec["actions"])}
                for spec in _synthetic_ego.TASK_SPECS
            ],
            "synthetic_only": True,
            "offline": True,
        }


# Stable descriptive alias for callers that prefer an app-specific name.
ActualAppRuntime = SyntheticRuntimeStore


def _error_response(exc: Exception) -> Tuple[int, Dict[str, Any]]:
    status = 409 if isinstance(exc, (StaleRuntimeCallbackError, NotificationRuntimeError, TaskRuntimeError)) else 503
    return (
        status,
        {
            "schema": RUNTIME_API_SCHEMA,
            "version": RUNTIME_API_VERSION,
            "ready": False,
            "synthetic_only": True,
            "offline": True,
            "status": "blocked",
            "message": "本次操作未完成，当前合成运行状态未改变。",
            "reason": str(exc),
        },
    )


def _request_mapping(body: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    return dict(_require_mapping(body or {}, "request"))


def runtime_api_request(
    method: str,
    path: str,
    body: Optional[Mapping[str, Any]] = None,
    *,
    runtime_root: Optional[Path] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Execute a deterministic API seam without opening a listener."""

    try:
        parsed = urllib.parse.urlsplit(path)
        route = parsed.path
        request = _request_mapping(body)
        if method.upper() == "GET":
            request.update({key: value for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)})
        store = SyntheticRuntimeStore(runtime_root or Path(tempfile.gettempdir()) / "mm-g6-synthetic-runtime")
        if route == "/api/g6/run/prepare" and method.upper() == "POST":
            return 200, store.prepare_run(
                request.get("project_ref", "synthetic-project-alpha"),
                request.get("analysis_mode", "full"),
                run_ref=request.get("run_ref"),
            )
        if route == "/api/g6/run/start" and method.upper() == "POST":
            return 200, store.start_run(request)
        if route in {"/api/g6/run", "/api/g6/run/read"} and method.upper() == "GET":
            advance = str(request.pop("advance", "false")).lower() in {"1", "true", "yes"}
            return 200, store.read_run(request, advance=advance)
        if route in {"/api/g6/run", "/api/g6/run/read"} and method.upper() == "POST":
            advance = bool(request.pop("advance", False))
            return 200, store.read_run(request, advance=advance)
        if route == "/api/g6/run/restore" and method.upper() == "POST":
            return 200, store.restore_run(request)
        if route == "/api/g6/run/callback" and method.upper() == "POST":
            return 200, store.accept_callback(request)
        if route == "/api/g6/notifications" and method.upper() == "GET":
            return 200, store.list_notifications()
        if route == "/api/g6/notifications" and method.upper() == "POST":
            return 200, store.record_notification(
                request.get("terminal_status"),
                request.get("capability_state"),
                request,
                terminal_revision=request.get("terminal_revision"),
            )
        if route == "/api/g6/notifications/matrix" and method.upper() == "POST":
            return 200, store.record_notification_matrix()
        if route == "/api/g6/notifications/replay" and method.upper() == "POST":
            return 200, store.replay_notification(request.get("notification", request))
        if route == "/api/g6/notifications/navigate" and method.upper() == "POST":
            return 200, store.navigate_notification(
                request.get("notification", request),
                current_revision=request.get("current_revision"),
                current_binding_digest=request.get("current_binding_digest"),
                target_exists=request.get("target_exists", True) is not False,
                target_accessible=request.get("target_accessible", True) is not False,
            )
        if route == "/api/g6/tasks" and method.upper() == "GET":
            return 200, store.list_tasks()
        task_prefix = "/api/g6/tasks/"
        if route.startswith(task_prefix):
            suffix = route[len(task_prefix):].strip("/").split("/")
            if len(suffix) != 2:
                raise TaskRuntimeError("task_route_invalid")
            task_key, action = urllib.parse.unquote(suffix[0]), suffix[1]
            if method.upper() != "POST":
                raise TaskRuntimeError("task_method_invalid")
            if action == "preview":
                return 200, store.preview_task(task_key)
            if action in {"action", "confirm"}:
                return 200, store.perform_task_action(task_key, request.get("action"), action_index=request.get("action_index"))
            if action == "cancel":
                return 200, store.cancel_task(task_key)
            if action == "restart":
                return 200, store.restart_task(task_key)
            if action == "reset":
                return 200, store.reset_task(task_key)
            if action == "status":
                return 200, store.status_task(task_key)
            raise TaskRuntimeError("task_action_route_invalid")
        raise RuntimeStoreError("runtime_route_not_found")
    except Exception as exc:
        return _error_response(exc)


def runtime_api_get(path: str, *, runtime_root: Optional[Path] = None) -> Tuple[int, Dict[str, Any]]:
    return runtime_api_request("GET", path, runtime_root=runtime_root)


def runtime_api_post(
    path: str,
    body: Optional[Mapping[str, Any]] = None,
    *,
    runtime_root: Optional[Path] = None,
) -> Tuple[int, Dict[str, Any]]:
    return runtime_api_request("POST", path, body, runtime_root=runtime_root)


__all__ = [
    "ACTUAL_ENTRY_ROUTE",
    "ActualAppRuntime",
    "ADAPTER_LEDGER_SCHEMA",
    "CAPABILITY_STATES",
    "ENTRY_ROUTE",
    "NOTIFICATION_STORE_SCHEMA",
    "NotificationRuntimeError",
    "RUNTIME_API_SCHEMA",
    "RUNTIME_API_VERSION",
    "RUN_STORE_SCHEMA",
    "StaleRuntimeCallbackError",
    "SyntheticRuntimeStore",
    "TASK_ENGINE_SCHEMA",
    "TASK_KEYS",
    "TASK_STATE_SCHEMA",
    "TERMINAL_STATUSES",
    "TaskRuntimeError",
    "WRITE_LEDGER_SCHEMA",
    "runtime_api_get",
    "runtime_api_post",
    "runtime_api_request",
]

ACTUAL_ENTRY_ROUTE = ENTRY_ROUTE


if __name__ == "__main__":  # pragma: no cover - the actual app owns the entry
    raise SystemExit("actual app runtime module is not a standalone entry")
