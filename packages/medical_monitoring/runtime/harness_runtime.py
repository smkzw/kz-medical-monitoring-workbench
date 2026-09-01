"""R7 Slice-06 bridge from the frozen R6 harness to the R1 runtime.

The R6 adapter and the R1 capability kernel intentionally use different
profile schemas.  This module keeps that distinction explicit:

* :class:`ProfileReceiptBridge` records both identities without persisting a
  credential value;
* :class:`HarnessCapabilityRuntime` is a thin ``CapabilityRuntime`` subclass;
* the R6 receipt is retained as raw evidence while a deterministic JSON-RPC
  envelope is fed through R1's existing classifier; and
* ``renew_inflight_lease`` is a separate run-level CAS from Slice-05's
  claim/heartbeat operation.

Only injected adapters/catalogs are used by the offline path.  No provider or
model is selected here and no R1/R6 source is modified.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple, Union

from .adapters import ImmutableAdapterBinding
from .capability import (
    CapabilityAttemptResult,
    CapabilityRequest,
    CapabilityRuntime,
    ExecutionProfile,
    StaleAttemptError,
    TransportExecution,
    TransportKind,
)
from ..domain.execution import CoverageUnit
from .agent_harness import (
    ADAPTER_ID as R6_ADAPTER_ID,
    ADAPTER_VERSION as R6_ADAPTER_VERSION,
    AgentHarnessError,
    FrozenExecutionProfile,
    InvocationReceipt,
    PreflightResult,
    sanitize_text,
    validate_frozen_profile,
)


BRIDGE_SCHEMA_VERSION = "mm-r7-profile-receipt-bridge-v1"
PREFLIGHT_DIAGNOSIS_SCHEMA_VERSION = "mm-r7-preflight-diagnosis-v1"
INFLIGHT_CONTROL_TABLE = "r7_execution_control"
INFLIGHT_LEASE_SECONDS = 15.0
INFLIGHT_RENEW_INTERVAL_SECONDS = 5.0

_ACTIVE_CONTROL_STATES = frozenset(("running", "cancelling"))
_SECRET_TEXT = re.compile(
    r"(?i)(sk-[a-z0-9]{8,}|bearer\s+\S+|(?:api[_-]?key|password|token|secret)\s*[:=]\s*\S+)"
)
_SAFE_REASON = re.compile(r"^[A-Za-z0-9_.-]+$")


class HarnessRuntimeError(RuntimeError):
    """Fail-closed R7 bridge/runtime error."""


class ProfileBridgeError(HarnessRuntimeError):
    """R6/R1 profile identities or mapping do not agree."""


class PreflightRequiredError(HarnessRuntimeError):
    """Execution was attempted before a frozen preflight result was supplied."""


class PreflightFailedError(HarnessRuntimeError):
    """The frozen preflight result is not executable."""


class InflightLeaseError(HarnessRuntimeError):
    """The R7 run owner no longer has a valid in-flight lease."""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _r6_invocation_id(attempt_id: str) -> str:
    """Map the R1 attempt identity to the frozen R6 adapter's ID grammar."""

    return "r7_%s" % _sha256_text(attempt_id)[:32]


def _canonical(value: Any) -> Any:
    """Detach a value through JSON, rejecting non-deterministic payloads."""

    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _claim_value(claim: Any, name: str, default: Any = None) -> Any:
    if claim is None:
        return default
    if isinstance(claim, Mapping):
        return claim.get(name, default)
    return getattr(claim, name, default)


def _safe_reason(value: Any) -> str:
    """Reduce adapter diagnostics to a non-sensitive stable code."""

    text = sanitize_text(str(value or ""), limit=240)
    text = _SECRET_TEXT.sub("[REDACTED]", text)
    # Catalog/credential/OS diagnostics may contain paths, provider response
    # bodies, or user input.  Keep only the stable leading code.
    code = text.split(":", 1)[0].strip().split(None, 1)[0] if text.strip() else "preflight_failed"
    return code if _SAFE_REASON.fullmatch(code) else "preflight_failed"


def _safe_text(value: Any, limit: int = 4000) -> str:
    return _SECRET_TEXT.sub("[REDACTED]", sanitize_text(str(value or ""), limit=limit))


def _r6_identity(profile: FrozenExecutionProfile) -> Dict[str, Any]:
    """Return the R6 identity needed for a bridge, without a credential ref."""

    return {
        "r6_execution_profile_id": profile.execution_profile_id,
        "r6_execution_profile_digest": profile.execution_profile_digest,
        "r6_profile_id": profile.profile_id,
        "r6_profile_revision": profile.profile_revision,
        "capability_id": profile.capability_id,
        "requested_provider": profile.requested_provider,
        "requested_model": profile.requested_model,
        "user_config_name": profile.user_config_name,
        "effective_selector": profile.effective_selector,
        "reasoning_effort": profile.reasoning_effort,
        "timeout_seconds": profile.timeout_seconds,
        "allowed_tools": list(profile.allowed_tools),
        "context_isolation": profile.context_isolation,
        "credential_ref_present": bool(profile.credential_ref),
        "credential_ref_hash": _sha256_text(profile.credential_ref) if profile.credential_ref else "",
        "adapter_id": profile.adapter_id,
        "adapter_version": profile.adapter_version,
        "fallback_profile_ids": list(profile.fallback_profile_ids),
    }


def _r1_identity(profile: ExecutionProfile) -> Dict[str, Any]:
    binding = profile.binding
    return {
        "r1_profile_id": profile.profile_id,
        "r1_profile_fingerprint": profile.fingerprint,
        "r1_transport": profile.transport.value,
        "r1_binding_id": binding.binding_id,
        "capability_id": binding.capability,
        "provider": binding.provider,
        "model": binding.model,
        "selector": binding.selector,
        "effort": binding.effort,
        "adapter_version": binding.adapter_version,
        "allowed_tools": list(binding.allowed_tools),
        "isolation": binding.isolation,
        "timeout_seconds": profile.timeout_seconds,
    }


@dataclass(frozen=True)
class ProfileReceiptBridge:
    """Content-addressed mapping between one R6 profile and one R1 profile.

    The two profile digests are deliberately separate fields.  The bridge
    digest is a third digest over the mapping and is never used as either
    profile's identity.
    """

    r6_profile: FrozenExecutionProfile
    r1_profile: ExecutionProfile
    r6_execution_profile_id: str
    r6_execution_profile_digest: str
    r1_profile_fingerprint: str
    r6_profile_id: str
    r6_profile_revision: str
    capability_id: str
    requested_provider: str
    requested_model: str
    user_config_name: str
    effective_selector: str
    reasoning_effort: str
    timeout_seconds: int
    allowed_tools: Tuple[str, ...]
    r6_adapter_id: str
    r6_adapter_version: str
    r1_binding_id: str
    bridge_digest: str
    schema_version: str = BRIDGE_SCHEMA_VERSION

    @classmethod
    def from_profiles(
        cls,
        r6_profile: FrozenExecutionProfile,
        r1_profile: ExecutionProfile,
    ) -> "ProfileReceiptBridge":
        if not isinstance(r6_profile, FrozenExecutionProfile):
            raise ProfileBridgeError("r6_profile_type_invalid")
        if not isinstance(r1_profile, ExecutionProfile):
            raise ProfileBridgeError("r1_profile_type_invalid")
        try:
            validate_frozen_profile(r6_profile)
        except AgentHarnessError as exc:
            raise ProfileBridgeError("r6_profile_invalid:%s" % _safe_reason(exc)) from exc
        _validate_profile_mapping(r6_profile, r1_profile)
        identity = _r6_identity(r6_profile)
        r1 = _r1_identity(r1_profile)
        body = {
            "schema_version": BRIDGE_SCHEMA_VERSION,
            "r6": identity,
            "r1": r1,
        }
        digest = _sha256_text(json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return cls(
            r6_profile=r6_profile,
            r1_profile=r1_profile,
            r6_execution_profile_id=r6_profile.execution_profile_id,
            r6_execution_profile_digest=r6_profile.execution_profile_digest,
            r1_profile_fingerprint=r1_profile.fingerprint,
            r6_profile_id=r6_profile.profile_id,
            r6_profile_revision=r6_profile.profile_revision,
            capability_id=r6_profile.capability_id,
            requested_provider=r6_profile.requested_provider,
            requested_model=r6_profile.requested_model,
            user_config_name=r6_profile.user_config_name,
            effective_selector=r6_profile.effective_selector,
            reasoning_effort=r6_profile.reasoning_effort,
            timeout_seconds=int(r6_profile.timeout_seconds),
            allowed_tools=tuple(r6_profile.allowed_tools),
            r6_adapter_id=r6_profile.adapter_id,
            r6_adapter_version=r6_profile.adapter_version,
            r1_binding_id=r1_profile.binding.binding_id,
            bridge_digest=digest,
        )

    def digest_body(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "r6": _r6_identity(self.r6_profile),
            "r1": _r1_identity(self.r1_profile),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Safe durable projection; never includes a credential reference value."""

        body = {
            "schema_version": self.schema_version,
            "bridge_digest": self.bridge_digest,
            "r6_execution_profile_id": self.r6_execution_profile_id,
            "r6_execution_profile_digest": self.r6_execution_profile_digest,
            "r6_profile_id": self.r6_profile_id,
            "r6_profile_revision": self.r6_profile_revision,
            "r1_profile_fingerprint": self.r1_profile_fingerprint,
            "r1_profile_id": self.r1_profile.profile_id,
            "r1_transport": self.r1_profile.transport.value,
            "r1_binding_id": self.r1_binding_id,
            "capability_id": self.capability_id,
            "requested_provider": self.requested_provider,
            "requested_model": self.requested_model,
            "user_config_name": self.user_config_name,
            "effective_selector": self.effective_selector,
            "reasoning_effort": self.reasoning_effort,
            "timeout_seconds": self.timeout_seconds,
            "allowed_tools": list(self.allowed_tools),
            "r6_adapter_id": self.r6_adapter_id,
            "r6_adapter_version": self.r6_adapter_version,
        }
        if any(key.lower() in {"credential", "credential_ref", "credential_value", "api_key", "token", "secret"} for key in body):
            raise ProfileBridgeError("bridge_projection_contains_credential_field")
        return {key: body[key] for key in sorted(body)}

    as_dict = to_dict

    def validate(self) -> None:
        try:
            validate_frozen_profile(self.r6_profile)
        except AgentHarnessError as exc:
            raise ProfileBridgeError("r6_profile_identity_mismatch:%s" % _safe_reason(exc)) from exc
        _validate_profile_mapping(self.r6_profile, self.r1_profile)
        if self.r6_execution_profile_id != self.r6_profile.execution_profile_id:
            raise ProfileBridgeError("r6_execution_profile_id_mismatch")
        if self.r6_execution_profile_digest != self.r6_profile.execution_profile_digest:
            raise ProfileBridgeError("r6_execution_profile_digest_mismatch")
        if self.r1_profile_fingerprint != self.r1_profile.fingerprint:
            raise ProfileBridgeError("r1_profile_fingerprint_mismatch")
        if self.r1_binding_id != self.r1_profile.binding.binding_id:
            raise ProfileBridgeError("r1_binding_id_mismatch")
        if _sha256_text(json.dumps(self.digest_body(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))) != self.bridge_digest:
            raise ProfileBridgeError("bridge_digest_mismatch")
        projection = json.dumps(self.to_dict(), ensure_ascii=False).lower()
        if "credential_value" in projection or "sk-" in projection:
            raise ProfileBridgeError("bridge_projection_leaked_credential_material")


def _validate_profile_mapping(
    r6_profile: FrozenExecutionProfile,
    r1_profile: ExecutionProfile,
) -> None:
    if r6_profile.adapter_id != R6_ADAPTER_ID or r6_profile.adapter_version != R6_ADAPTER_VERSION:
        raise ProfileBridgeError("unsupported_r6_adapter")
    if r6_profile.fallback_profile_ids:
        raise ProfileBridgeError("auto_fallback_forbidden")
    if r1_profile.transport is not TransportKind.HARNESS:
        raise ProfileBridgeError("r1_profile_must_be_harness_transport")
    binding = r1_profile.binding
    checks = (
        (binding.capability, r6_profile.capability_id, "capability_id"),
        (binding.provider, r6_profile.requested_provider, "provider"),
        (binding.model, r6_profile.requested_model, "model"),
        (binding.selector, r6_profile.effective_selector, "selector"),
        (binding.effort, r6_profile.reasoning_effort, "effort"),
        (binding.adapter_version, r6_profile.adapter_version, "adapter_version"),
        (tuple(binding.allowed_tools), tuple(r6_profile.allowed_tools), "allowed_tools"),
        (binding.isolation, r6_profile.context_isolation, "context_isolation"),
        (r1_profile.timeout_seconds, r6_profile.timeout_seconds, "timeout_seconds"),
    )
    for actual, expected, name in checks:
        if actual != expected:
            raise ProfileBridgeError("profile_mapping_mismatch:%s" % name)
    if binding.endpoint != "local":
        raise ProfileBridgeError("r1_harness_binding_must_be_local")


def build_r1_execution_profile(
    r6_profile: FrozenExecutionProfile,
    *,
    executable: Optional[Union[str, Path]] = None,
    working_directory: Optional[Union[str, Path]] = None,
    profile_id: Optional[str] = None,
    binding_id: Optional[str] = None,
    output_limit_chars: int = 120000,
) -> ExecutionProfile:
    """Build the R1 identity shell used by the R6-backed runtime.

    The executable/working directory are identity inputs only; the thin
    runtime invokes the injected R6 adapter.  Callers should pass the same
    offline executable and directory used by their test adapter.
    """

    if not isinstance(r6_profile, FrozenExecutionProfile):
        raise ProfileBridgeError("r6_profile_type_invalid")
    exe = Path(executable if executable is not None else sys.executable).resolve()
    work = Path(working_directory if working_directory is not None else Path.cwd()).resolve()
    if not exe.is_file() or not work.is_dir():
        raise ProfileBridgeError("r1_identity_paths_invalid")
    binding = ImmutableAdapterBinding(
        binding_id=binding_id or "r7-r6-binding:%s" % r6_profile.execution_profile_digest[:32],
        capability=r6_profile.capability_id,
        provider=r6_profile.requested_provider,
        model=r6_profile.requested_model,
        selector=r6_profile.effective_selector,
        effort=r6_profile.reasoning_effort,
        adapter_version=r6_profile.adapter_version,
        allowed_tools=tuple(r6_profile.allowed_tools),
        isolation=r6_profile.context_isolation,
        timeout_seconds=int(r6_profile.timeout_seconds),
        endpoint="local",
        # R7 reconstructs this identity shell on each explicit start or
        # continuation.  A wall-clock-created binding would change the R1
        # fingerprint between attempts even though the R6 profile is frozen.
        created_at="r7-slice06:%s" % r6_profile.execution_profile_digest[:32],
    )
    return ExecutionProfile(
        profile_id=profile_id or "r7-harness:%s" % r6_profile.execution_profile_id,
        transport=TransportKind.HARNESS,
        binding=binding,
        argv=(str(exe),),
        working_directory=str(work),
        credential_ref=r6_profile.credential_ref,
        runtime_revision="r7-slice06:%s" % r6_profile.adapter_version,
        timeout_seconds=int(r6_profile.timeout_seconds),
        output_limit_chars=output_limit_chars,
    )


def build_profile_receipt_bridge(
    r6_profile: FrozenExecutionProfile,
    r1_profile: Optional[ExecutionProfile] = None,
    *,
    executable: Optional[Union[str, Path]] = None,
    working_directory: Optional[Union[str, Path]] = None,
) -> ProfileReceiptBridge:
    """Create and validate one R6→R1 profile bridge."""

    r1 = r1_profile or build_r1_execution_profile(
        r6_profile,
        executable=executable,
        working_directory=working_directory,
    )
    bridge = ProfileReceiptBridge.from_profiles(r6_profile, r1)
    bridge.validate()
    return bridge


def bridge_from_run_binding(
    run_binding_store: Any,
    run_id: str,
    *,
    r1_profile: Optional[ExecutionProfile] = None,
    executable: Optional[Union[str, Path]] = None,
    working_directory: Optional[Union[str, Path]] = None,
) -> ProfileReceiptBridge:
    """Restore the frozen R6 profile from the immutable R7 Run binding."""

    getter = getattr(run_binding_store, "get_with_frozen", None)
    if not callable(getter):
        raise ProfileBridgeError("run_binding_store_missing_get_with_frozen")
    try:
        _, frozen = getter(run_id)
    except Exception as exc:
        raise ProfileBridgeError("run_binding_not_found") from exc
    return build_profile_receipt_bridge(
        frozen,
        r1_profile,
        executable=executable,
        working_directory=working_directory,
    )


@dataclass(frozen=True)
class PreflightDiagnosis:
    """De-sensitive, R1-domain-auditable preflight failure record."""

    run_id: str
    node_id: str
    manifest_revision: int
    bridge_digest: str
    r1_profile_fingerprint: str
    ok: bool
    reason_codes: Tuple[str, ...]
    schema_version: str = PREFLIGHT_DIAGNOSIS_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "node_id": self.node_id,
            "manifest_revision": int(self.manifest_revision),
            "bridge_digest": self.bridge_digest,
            "r1_profile_fingerprint": self.r1_profile_fingerprint,
            "ok": bool(self.ok),
            "reason_codes": list(self.reason_codes),
        }


def build_preflight_diagnosis(
    bridge: ProfileReceiptBridge,
    result: PreflightResult,
    *,
    run_id: str,
    node_id: str,
    manifest_revision: int,
) -> PreflightDiagnosis:
    bridge.validate()
    reasons = tuple(dict.fromkeys(_safe_reason(value) for value in result.reasons))
    return PreflightDiagnosis(
        run_id=str(run_id),
        node_id=str(node_id),
        manifest_revision=int(manifest_revision),
        bridge_digest=bridge.bridge_digest,
        r1_profile_fingerprint=bridge.r1_profile_fingerprint,
        ok=bool(result.ok),
        reason_codes=reasons,
    )


def persist_preflight_diagnosis(
    store: Any,
    diagnosis: PreflightDiagnosis,
) -> int:
    """Persist diagnosis through R1's public domain-object/audit seam."""

    if not hasattr(store, "put_domain_object"):
        raise HarnessRuntimeError("diagnosis_store_missing_domain_object_seam")
    payload = diagnosis.to_dict()
    digest = _sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    object_id = "r7-preflight:%s:%s:%s:%s" % (
        diagnosis.run_id,
        diagnosis.node_id,
        diagnosis.manifest_revision,
        digest[:24],
    )
    return int(store.put_domain_object(
        "r7_preflight_diagnosis",
        object_id,
        payload,
        run_id=diagnosis.run_id,
        idempotency_key="r7-preflight-diagnosis:%s" % digest,
    ))


def persist_profile_receipt_bridge(
    store: Any,
    bridge: ProfileReceiptBridge,
    *,
    run_id: Optional[str] = None,
) -> int:
    """Persist the safe bridge projection through R1's domain-object seam."""

    bridge.validate()
    if not hasattr(store, "put_domain_object"):
        raise HarnessRuntimeError("bridge_store_missing_domain_object_seam")
    payload = bridge.to_dict()
    scope = str(run_id or "")
    object_id = "r7-profile-receipt-bridge:%s:%s" % (scope or "profile", bridge.bridge_digest)
    return int(store.put_domain_object(
        "r7_profile_receipt_bridge",
        object_id,
        payload,
        run_id=scope or None,
        # The key must carry the run scope: two runs sharing one frozen
        # profile digest in the same project store each persist their own
        # bridge row, and a digest-only key would collide on the second run.
        idempotency_key="r7-profile-receipt-bridge:%s:%s" % (
            scope or "profile",
            bridge.bridge_digest,
        ),
    ))


def _control_row(
    db_path: Union[str, Path],
    *,
    run_id: str,
    manifest_revision: int,
    generation: int,
    owner_token: str,
    now_epoch: float,
) -> Optional[Tuple[str, int, int, str, float, int]]:
    """Read one control row without creating/migrating the R7 schema."""

    if not Path(db_path).is_file():
        return None
    connection: Optional[sqlite3.Connection] = None
    try:
        connection = sqlite3.connect(str(db_path), timeout=10.0, isolation_level=None)
        connection.execute("PRAGMA busy_timeout=10000")
    except (OSError, sqlite3.Error):
        if connection is not None:
            connection.close()
        return None
    try:
        row = connection.execute(
            "SELECT run_id, manifest_revision, generation, state, owner_token, "
            "lease_expires_at, cancel_requested FROM %s WHERE run_id=?" % INFLIGHT_CONTROL_TABLE,
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        if (
            row[0] != run_id
            or row[1] != manifest_revision
            or row[2] != generation
            or row[3] not in _ACTIVE_CONTROL_STATES
            or row[4] != owner_token
            or row[5] is None
            or float(row[5]) <= float(now_epoch)
            or (row[3] == "running" and row[6] != 0)
            or (row[3] == "cancelling" and row[6] != 1)
        ):
            return None
        return (str(row[0]), int(row[1]), int(row[2]), str(row[3]), float(row[5]), int(row[6]))
    except (sqlite3.Error, TypeError, ValueError):
        return None
    finally:
        if connection is not None:
            connection.close()


def inflight_lease_valid(
    db_path: Union[str, Path],
    run_id: str,
    manifest_revision: int,
    generation: int,
    owner_token: str,
    *,
    now_epoch: Optional[float] = None,
) -> bool:
    """Return whether a run owner may finish its current in-flight unit."""

    if not owner_token:
        return False
    return _control_row(
        db_path,
        run_id=run_id,
        manifest_revision=manifest_revision,
        generation=generation,
        owner_token=owner_token,
        now_epoch=float(time.time() if now_epoch is None else now_epoch),
    ) is not None


def renew_inflight_lease(
    db_path: Union[str, Path],
    run_id: str,
    manifest_revision: int,
    generation: int,
    owner_token: str,
    *,
    lease_seconds: float = INFLIGHT_LEASE_SECONDS,
    now_epoch: Optional[float] = None,
) -> bool:
    """CAS-renew a current R7 owner lease during a blocking transport.

    This is deliberately not ``BackgroundRecoveryAdapter.heartbeat``:
    cancelling owners may renew only this current unit, but must never claim a
    new unit through the Slice-05 scheduling path.
    """

    try:
        lease = float(lease_seconds)
        current = float(time.time() if now_epoch is None else now_epoch)
    except (TypeError, ValueError, OverflowError):
        return False
    if not owner_token or not math.isfinite(lease) or lease <= 0:
        return False
    if not math.isfinite(current):
        return False
    # sqlite3.connect() creates a file for a missing path.  A lease check must
    # never create runtime state or make a missing control database look like
    # an initialized run.
    if not Path(db_path).is_file():
        return False
    connection: Optional[sqlite3.Connection] = None
    try:
        connection = sqlite3.connect(str(db_path), timeout=10.0, isolation_level=None)
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("BEGIN IMMEDIATE")
    except (OSError, sqlite3.Error, ValueError, TypeError):
        if connection is not None:
            connection.close()
        return False
    try:
        row = connection.execute(
            "SELECT state, owner_token, lease_expires_at, cancel_requested "
            "FROM %s WHERE run_id=? AND manifest_revision=? AND generation=?" % INFLIGHT_CONTROL_TABLE,
            (run_id, manifest_revision, generation),
        ).fetchone()
        valid = bool(
            row is not None
            and row[0] in _ACTIVE_CONTROL_STATES
            and row[1] == owner_token
            and row[2] is not None
            and float(row[2]) > current
            and ((row[0] == "running" and row[3] == 0) or (row[0] == "cancelling" and row[3] == 1))
        )
        if not valid:
            connection.execute("ROLLBACK")
            return False
        updated = connection.execute(
            "UPDATE %s SET lease_expires_at=?, updated_at=? "
            "WHERE run_id=? AND manifest_revision=? AND generation=? AND owner_token=? "
            "AND state IN ('running','cancelling') AND lease_expires_at>?" % INFLIGHT_CONTROL_TABLE,
            (
                current + lease,
                _utc_now_text(current),
                run_id,
                manifest_revision,
                generation,
                owner_token,
                current,
            ),
        )
        ok = updated.rowcount == 1
        connection.execute("COMMIT" if ok else "ROLLBACK")
        return ok
    except (sqlite3.Error, TypeError, ValueError, OSError):
        try:
            connection.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        return False
    finally:
        if connection is not None:
            connection.close()


def _utc_now_text(epoch: float) -> str:
    import datetime

    return datetime.datetime.fromtimestamp(float(epoch), datetime.timezone.utc).isoformat()


def _receipt_value(receipt: Any, name: str, default: Any = None) -> Any:
    if isinstance(receipt, Mapping):
        return receipt.get(name, default)
    return getattr(receipt, name, default)


def _receipt_projection(receipt: Any) -> Dict[str, Any]:
    if isinstance(receipt, InvocationReceipt):
        body = receipt.to_public_dict()
    elif isinstance(receipt, Mapping):
        body = dict(receipt)
    elif hasattr(receipt, "to_public_dict"):
        body = dict(receipt.to_public_dict())
    else:
        raise HarnessRuntimeError("r6_receipt_type_invalid")
    safe = _canonical(body)
    # The path is not needed for the R7 raw receipt and would expose local
    # filesystem structure.  R6's content hash and timing remain evidence.
    safe["stdout_path"] = ""
    for key in ("stderr_summary", "failure_reason"):
        if key in safe:
            safe[key] = _safe_text(safe[key])
    for key in ("argv", "command", "raw_stderr", "stderr"):
        safe.pop(key, None)
    return safe


def _coverage_token(unit: CoverageUnit) -> str:
    return "%s:%s" % (unit.scope, unit.key)


def _expected_tokens(request: CapabilityRequest) -> Tuple[str, ...]:
    return tuple(_coverage_token(unit) for unit in request.expected_units)


def _r1_coverage_from_r6(
    request: CapabilityRequest,
    produced: Sequence[str],
    state: str,
) -> Tuple[Dict[str, Any], ...]:
    expected = {_coverage_token(unit): unit for unit in request.expected_units}
    if any(value not in expected for value in produced):
        raise HarnessRuntimeError("r6_receipt_produced_unknown_coverage")
    status = "covered" if state == "complete" else state
    if status == "timed_out":
        status = "failed"
    return tuple(
        {
            "scope": expected[value].scope,
            "key": expected[value].key,
            "expected": True,
            "status": status,
        }
        for value in produced
    )


def _classify_r6_receipt(
    request: CapabilityRequest,
    bridge: ProfileReceiptBridge,
    receipt: Any,
    prompt: str,
) -> Tuple[str, bool, Tuple[Dict[str, Any], ...], str]:
    """Map a validated R6 receipt to ``(R1 status, timed_out, coverage, reason)``."""

    state = str(_receipt_value(receipt, "state", ""))
    parse_state = str(_receipt_value(receipt, "parse_state", ""))
    expected = tuple(str(value) for value in (_receipt_value(receipt, "expected_units", ()) or ()))
    produced = tuple(str(value) for value in (_receipt_value(receipt, "produced_units", ()) or ()))
    missing = tuple(str(value) for value in (_receipt_value(receipt, "missing_units", ()) or ()))
    reasons = []
    if _receipt_value(receipt, "invocation_id", "") != _r6_invocation_id(request.attempt_id):
        reasons.append("invocation_id_mismatch")
    if _receipt_value(receipt, "profile_digest", "") != bridge.r6_execution_profile_digest:
        reasons.append("r6_profile_digest_mismatch")
    if _receipt_value(receipt, "adapter_id", "") != R6_ADAPTER_ID:
        reasons.append("r6_adapter_id_mismatch")
    if _receipt_value(receipt, "adapter_version", "") != R6_ADAPTER_VERSION:
        reasons.append("r6_adapter_version_mismatch")
    if _receipt_value(receipt, "requested_selector", "") != bridge.effective_selector:
        reasons.append("r6_requested_selector_mismatch")
    if _receipt_value(receipt, "effective_selector", "") != bridge.effective_selector:
        reasons.append("r6_effective_selector_mismatch")
    if _receipt_value(receipt, "reasoning_effort", "") != bridge.reasoning_effort:
        reasons.append("r6_effort_mismatch")
    try:
        receipt_tools = tuple(_receipt_value(receipt, "allowed_tools", ()) or ())
    except (TypeError, ValueError):
        receipt_tools = ()
        reasons.append("r6_tools_invalid")
    if receipt_tools != bridge.allowed_tools:
        reasons.append("r6_tools_mismatch")
    if _receipt_value(receipt, "input_digest", "") != _sha256_text(prompt):
        reasons.append("r6_input_digest_mismatch")
    if expected != _expected_tokens(request):
        reasons.append("r6_expected_coverage_mismatch")
    if len(produced) != len(set(produced)):
        reasons.append("r6_produced_coverage_duplicate")
    if any(not value or value not in expected for value in produced):
        reasons.append("r6_produced_coverage_invalid")
    expected_missing = tuple(value for value in expected if value not in set(produced))
    if missing != expected_missing:
        reasons.append("r6_missing_coverage_mismatch")
    if bool(_receipt_value(receipt, "fallback_used", False)):
        reasons.append("auto_fallback_used")
    if _receipt_value(receipt, "unsupported_operation", ""):
        reasons.append("unsupported_operation")
    if state not in {"complete", "partial", "truncated", "timed_out", "failed", "not_evaluable"}:
        reasons.append("r6_state_invalid")

    if state == "timed_out" and reasons:
        return "failed", False, _r1_coverage_from_r6(
            request, produced, "failed"
        ), _safe_reason(reasons[0])

    if state == "timed_out":
        # Timeout is represented by the R1 transport flag only.  Do not invent
        # an unsupported JSON-RPC "timeout" AdapterState.
        expected_set = set(_expected_tokens(request))
        safe_produced = tuple(dict.fromkeys(value for value in produced if value in expected_set))
        return "failed", True, _r1_coverage_from_r6(request, safe_produced, "failed"), _safe_reason("timed_out")

    if state in {"partial", "truncated"} and not reasons:
        return state, False, _r1_coverage_from_r6(request, produced, state), _safe_reason(state)

    complete = (
        state == "complete"
        and bool(_receipt_value(receipt, "analysis_complete", False))
        and parse_state == "parsed"
        and not expected_missing
        and not reasons
    )
    if complete:
        return "complete", False, _r1_coverage_from_r6(request, produced, "complete"), ""
    reason = reasons[0] if reasons else ("coverage_gap" if expected_missing else "r6_not_complete")
    return "failed", False, _r1_coverage_from_r6(request, produced, "failed"), _safe_reason(reason)

def build_r6_prompt(payload: Any, expected_units: Sequence[str]) -> str:
    """Public deterministic prompt builder paired with receipt classification."""

    return _prompt_from_payload(payload, expected_units)


build_receipt_prompt = build_r6_prompt
def classify_r6_receipt(
    request: CapabilityRequest,
    bridge: ProfileReceiptBridge,
    receipt: Any,
    prompt: str,
) -> Tuple[str, bool, Tuple[Dict[str, Any], ...], str]:
    """Public receipt-classification seam shared by R7 publication gates.

    The implementation deliberately delegates to the existing classifier so
    product publication never grows a second interpretation of R6 receipts.
    """

    return _classify_r6_receipt(request, bridge, receipt, prompt)


classify_receipt = classify_r6_receipt


def _r1_envelope(
    request: CapabilityRequest,
    profile: ExecutionProfile,
    *,
    status: str,
    produced_units: Sequence[Mapping[str, Any]],
    reason: str,
    candidate_payload: Any = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "status": status,
        "execution_identity": profile.response_identity(),
        "input_hash": request.input_hash,
        "produced_units": [dict(item) for item in produced_units],
    }
    if candidate_payload is not None:
        result["candidate_payload"] = _canonical(candidate_payload)
    if reason:
        result["failure_reason"] = _safe_text(reason, limit=240)
    return {
        "jsonrpc": "2.0",
        "id": request.attempt_id,
        "result": result,
    }


def _prompt_from_payload(payload: Any, expected_units: Sequence[str]) -> str:
    """Build the deterministic R6 output contract around one R1 payload."""

    source = payload if isinstance(payload, str) else json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    expected = json.dumps(
        [str(value) for value in expected_units],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return (
        "请完成下列医学监查工作单元。仅依据输入作答，不补造事实。\n"
        "完成时只输出一个JSON对象，不要输出Markdown或解释文字："
        '{"status":"complete","produced_units":%s,"result":{}}。\n'
        "produced_units必须逐字复制给定覆盖项且不得增删；无法完成时输出"
        '{"status":"failed","produced_units":[],"failure_reason":"简短原因"}。\n'
        "给定覆盖项：%s\n输入：%s" % (expected, expected, source)
    )


def _receipt_candidate_payload(
    *,
    status: str,
    produced_units: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Create candidate-only metadata when R6 returned a receipt without payload.

    R6's frozen receipt is execution evidence, not a medical fact payload.  R1
    still requires a candidate artifact for successful/partial AI attempts, so
    use a deterministic receipt-backed marker that contains no provider/model
    identity and no raw candidate text.  The receipt remains the authoritative
    raw evidence in ``TransportExecution.raw_output``.
    """

    return {
        "source": "r6_invocation_receipt",
        "status": status,
        "produced_units": [dict(item) for item in produced_units],
    }


class HarnessCapabilityRuntime(CapabilityRuntime):
    """Thin R7 runtime that delegates transport work to ``OmpPrintAdapter``."""

    raw_source = "r6_omp_print_adapter"

    def __init__(
        self,
        bridge: Optional[Union[ProfileReceiptBridge, FrozenExecutionProfile]] = None,
        adapter: Any = None,
        *,
        r1_profile: Optional[ExecutionProfile] = None,
        r6_profile: Optional[FrozenExecutionProfile] = None,
        transport: Any = None,
        manifest_revision_reader: Optional[Callable[[str], int]] = None,
        attempt_journal: Any = None,
        journal_owner_token: str = "",
        run_claim: Any = None,
        run_control: Any = None,
        control_db_path: Optional[Union[str, Path]] = None,
        run_lease_seconds: float = INFLIGHT_LEASE_SECONDS,
        renew_interval_seconds: float = INFLIGHT_RENEW_INTERVAL_SECONDS,
        output_dir: Optional[Union[str, Path]] = None,
        output_dir_factory: Optional[Callable[[str], Union[str, Path]]] = None,
        preflight_result: Optional[PreflightResult] = None,
        catalog: Any = None,
        require_run_cas: bool = False,
    ) -> None:
        if bridge is None and r6_profile is not None:
            bridge = r6_profile
        if isinstance(bridge, ProfileReceiptBridge):
            resolved_bridge = bridge
        elif isinstance(bridge, FrozenExecutionProfile):
            resolved_bridge = build_profile_receipt_bridge(bridge, r1_profile)
        else:
            raise ProfileBridgeError("bridge_type_invalid")
        resolved_bridge.validate()
        resolved_adapter = adapter if adapter is not None else transport
        if resolved_adapter is None or not callable(getattr(resolved_adapter, "invoke", None)):
            raise HarnessRuntimeError("r6_adapter_invoke_missing")
        if float(run_lease_seconds) <= 0 or float(renew_interval_seconds) <= 0:
            raise HarnessRuntimeError("lease_options_invalid")
        self.bridge = resolved_bridge
        self.r6_profile = resolved_bridge.r6_profile
        self.r6_adapter = resolved_adapter
        # Keep the caller-owned public journal/store reference for the
        # pre-terminal CAS check.  The inherited runtime may wrap a Store's
        # private journal hook internally; R7 never reaches through that hook.
        self._attempt_store = attempt_journal
        self._run_claim = run_claim
        self._run_control = run_control
        self._control_db_path = Path(control_db_path) if control_db_path is not None else self._path_from_store(attempt_journal)
        self._run_lease_seconds = float(run_lease_seconds)
        self._renew_interval_seconds = float(renew_interval_seconds)
        self._output_dir = Path(output_dir) if output_dir is not None else None
        self._output_dir_factory = output_dir_factory
        self._preflight_result = preflight_result
        self._catalog = catalog
        self._preflight_lock = threading.RLock()
        self._require_run_cas = bool(require_run_cas)
        if manifest_revision_reader is None and callable(getattr(attempt_journal, "get_run", None)):
            manifest_revision_reader = lambda run_id: int(attempt_journal.get_run(run_id).manifest_revision)
        if manifest_revision_reader is None:
            manifest_revision_reader = lambda _run_id: 1
        timeout = max(int(self.r6_profile.timeout_seconds) + 30, 60)
        super().__init__(
            resolved_bridge.r1_profile,
            manifest_revision_reader=manifest_revision_reader,
            attempt_journal=attempt_journal,
            journal_owner_token=journal_owner_token,
            journal_lease_seconds=timeout,
        )
        if self._preflight_result is not None:
            self._validate_preflight_result(self._preflight_result)

    @staticmethod
    def _path_from_store(store: Any) -> Optional[Path]:
        path = getattr(store, "db_path", None)
        return Path(path) if path else None

    @property
    def preflight_result(self) -> Optional[PreflightResult]:
        return self._preflight_result

    def _validate_preflight_result(self, result: PreflightResult) -> None:
        if not isinstance(result, PreflightResult):
            raise PreflightRequiredError("preflight_result_type_invalid")
        if result.selector != self.r6_profile.effective_selector:
            raise ProfileBridgeError("preflight_selector_mismatch")
        if result.effort != self.r6_profile.reasoning_effort:
            raise ProfileBridgeError("preflight_effort_mismatch")
        if tuple(result.allowed_tools) != tuple(self.r6_profile.allowed_tools):
            raise ProfileBridgeError("preflight_tools_mismatch")
        if int(result.timeout_seconds) != int(self.r6_profile.timeout_seconds):
            raise ProfileBridgeError("preflight_timeout_mismatch")

    def preflight(
        self,
        *,
        catalog: Any = None,
        extra_allowed_tools: Optional[Sequence[str]] = None,
    ) -> PreflightResult:
        """Run R6 preflight exactly once and retain that result for invoke."""

        with self._preflight_lock:
            self.bridge.validate()
            if self._preflight_result is not None:
                self._validate_preflight_result(self._preflight_result)
                return self._preflight_result
            selected_catalog = self._catalog if catalog is None else catalog
            preflight_kwargs: Dict[str, Any] = {}
            if selected_catalog is not None:
                preflight_kwargs["catalog"] = selected_catalog
            if extra_allowed_tools is not None:
                preflight_kwargs["extra_allowed_tools"] = extra_allowed_tools
            try:
                result = self.r6_adapter.preflight(self.r6_profile, **preflight_kwargs)
            except Exception as exc:
                result = PreflightResult(
                    ok=False,
                    executable="",
                    selector=self.r6_profile.effective_selector,
                    effort=self.r6_profile.reasoning_effort,
                    allowed_tools=tuple(self.r6_profile.allowed_tools),
                    timeout_seconds=int(self.r6_profile.timeout_seconds),
                    reasons=(_safe_reason(exc),),
                )
            self._validate_preflight_result(result)
            self._preflight_result = result
            return result

    prepare_preflight = preflight

    def require_preflight(self) -> PreflightResult:
        result = self._preflight_result
        if result is None:
            raise PreflightRequiredError("preflight_required_before_capability_invoke")
        self._validate_preflight_result(result)
        if not result.ok:
            raise PreflightFailedError("preflight_failed:%s" % ",".join(_safe_reason(value) for value in result.reasons))
        return result

    def invoke(self, **kwargs: Any) -> CapabilityAttemptResult:
        # This check runs before R1's declare/claim seam.  Callers must invoke
        # preflight before controller.register/execute to preserve zero-attempt
        # preflight failures.
        self.require_preflight()
        return super().invoke(**kwargs)

    invoke_preflighted = invoke

    def _output_path(self, attempt_id: str) -> Tuple[Path, Optional[tempfile.TemporaryDirectory[str]]]:
        if self._output_dir_factory is not None:
            return Path(self._output_dir_factory(attempt_id)), None
        if self._output_dir is not None:
            return self._output_dir, None
        temporary = tempfile.TemporaryDirectory(prefix="mm-r7-harness-")
        return Path(temporary.name), temporary

    def _claim_for_request(self, request: CapabilityRequest) -> Optional[Tuple[str, int, int, str]]:
        claim = self._run_claim
        if claim is None:
            return None
        run_id = str(_claim_value(claim, "run_id", ""))
        revision = int(_claim_value(claim, "manifest_revision", 0) or 0)
        generation = int(_claim_value(claim, "generation", -1) or -1)
        owner = str(_claim_value(claim, "owner_token", ""))
        if run_id != request.monitoring_run_id or revision != request.manifest_revision or not owner:
            return None
        return run_id, revision, generation, owner

    def _renew_claim(self, request: CapabilityRequest) -> bool:
        values = self._claim_for_request(request)
        if values is None:
            return False
        run_id, revision, generation, owner = values
        method = getattr(self._run_control, "renew_inflight_lease", None)
        if callable(method):
            try:
                return bool(method(
                    run_id,
                    revision,
                    generation,
                    owner,
                    lease_seconds=self._run_lease_seconds,
                ))
            except TypeError:
                try:
                    return bool(method(run_id, revision, generation, owner))
                except Exception:
                    return False
            except Exception:
                return False
        if self._control_db_path is None:
            return False
        return renew_inflight_lease(
            self._control_db_path,
            run_id,
            revision,
            generation,
            owner,
            lease_seconds=self._run_lease_seconds,
        )

    def renew_inflight_lease(
        self,
        run_id: str,
        manifest_revision: int,
        generation: int,
        owner_token: str,
        *,
        lease_seconds: Optional[float] = None,
        now_epoch: Optional[float] = None,
    ) -> bool:
        """Runtime convenience wrapper around the distinct run-level CAS."""

        if self._control_db_path is None:
            return False
        return renew_inflight_lease(
            self._control_db_path,
            run_id,
            manifest_revision,
            generation,
            owner_token,
            lease_seconds=self._run_lease_seconds if lease_seconds is None else lease_seconds,
            now_epoch=now_epoch,
        )

    def _start_renew_loop(
        self,
        request: CapabilityRequest,
    ) -> Tuple[threading.Event, threading.Event, Optional[threading.Thread]]:
        stop = threading.Event()
        lost = threading.Event()
        if self._run_claim is None:
            if self._require_run_cas:
                lost.set()
            return stop, lost, None

        if not self._renew_claim(request):
            lost.set()
            return stop, lost, None

        def renew() -> None:
            while not stop.wait(self._renew_interval_seconds):
                if not self._renew_claim(request):
                    lost.set()
                    return

        thread = threading.Thread(target=renew, name="mm-r7-inflight-lease", daemon=True)
        thread.start()
        return stop, lost, thread

    def _stop_renew_loop(
        self,
        stop: threading.Event,
        thread: Optional[threading.Thread],
    ) -> None:
        stop.set()
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=min(max(self._renew_interval_seconds * 2.0, 0.1), 2.0))

    def _execute(self, request: CapabilityRequest) -> TransportExecution:
        preflight = self.require_preflight()
        self.bridge.validate()
        expected = _expected_tokens(request)
        prompt = _prompt_from_payload(request.payload, expected)
        output_dir, temporary = self._output_path(request.attempt_id)
        stop, lost, renew_thread = self._start_renew_loop(request)
        try:
            if lost.is_set():
                return TransportExecution(
                    raw_output={"state": "failed", "failure_reason": "inflight_lease_unavailable"},
                    stdout="",
                    failure_reason="inflight lease unavailable before transport",
                )
            invoke_kwargs: Dict[str, Any] = {
                "output_dir": output_dir,
                "expected_units": expected,
                "invocation_id": _r6_invocation_id(request.attempt_id),
                "preflight_result": preflight,
            }
            if self._catalog is not None:
                invoke_kwargs["catalog"] = self._catalog
            # Exactly one adapter invocation is allowed.  A TypeError raised
            # by the adapter is a transport failure, not permission to retry
            # a potentially side-effecting model/process call.
            receipt = self.r6_adapter.invoke(self.r6_profile, prompt, **invoke_kwargs)
            raw = _receipt_projection(receipt)
            try:
                status, timed_out, produced, reason = _classify_r6_receipt(
                    request, self.bridge, receipt, prompt
                )
            except Exception as exc:
                status, timed_out, produced, reason = "failed", False, (), _safe_reason(exc)
            envelope = _r1_envelope(
                request,
                self.profile,
                status=status,
                produced_units=produced,
                reason=reason,
                candidate_payload=_receipt_candidate_payload(
                    status=status,
                    produced_units=produced,
                ),
            )
            return TransportExecution(
                raw_output=raw,
                stdout=json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                stderr="",
                return_code=0,
                timed_out=timed_out,
                cancelled=False,
                output_truncated=False,
                execution_id=str(_receipt_value(receipt, "invocation_id", request.attempt_id)),
                failure_reason=_safe_text(reason, limit=240),
            )
        except Exception as exc:
            reason = _safe_text(exc, limit=240)
            envelope = _r1_envelope(
                request,
                self.profile,
                status="failed",
                produced_units=(),
                reason=_safe_reason(exc),
                candidate_payload={
                    "source": "r6_invocation_receipt",
                    "status": "failed",
                    "produced_units": [],
                },
            )
            return TransportExecution(
                raw_output={"state": "failed", "failure_reason": reason},
                stdout=json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                return_code=0,
                failure_reason=reason,
            )
        finally:
            self._stop_renew_loop(stop, renew_thread)
            if temporary is not None:
                temporary.cleanup()

    def _run_commit_permitted(self, request: CapabilityRequest) -> bool:
        values = self._claim_for_request(request)
        if values is None:
            return not self._require_run_cas and self._run_claim is None
        run_id, revision, generation, owner = values
        # A final CAS renewal is the closest available atomic check before the
        # R1 journal write.  It is allowed in ``cancelling`` for the current
        # unit, but it cannot claim any next unit.
        return self._renew_claim(request)

    def _attempt_commit_permitted(self, request: CapabilityRequest) -> bool:
        if request.profile_fingerprint != self.bridge.r1_profile_fingerprint:
            return False
        journal = self._attempt_store
        if journal is None or not callable(getattr(journal, "get_capability_attempt", None)):
            return not self._require_run_cas and self._run_claim is None
        try:
            attempt = journal.get_capability_attempt(request.attempt_id)
        except Exception:
            return False
        if not isinstance(attempt, Mapping):
            return False
        now = time.time()
        if (
            attempt.get("request_hash") != request.request_hash
            or attempt.get("profile_fingerprint") != request.profile_fingerprint
            or int(attempt.get("manifest_revision", 0)) != request.manifest_revision
            or attempt.get("status") != "running"
            or attempt.get("owner_token") != self._journal_owner_token
            or attempt.get("lease_expires_at") is None
            or float(attempt.get("lease_expires_at")) <= now
        ):
            return False
        return self._run_commit_permitted(request)

    def _complete_durable_attempt(
        self,
        request: CapabilityRequest,
        result: CapabilityAttemptResult,
    ) -> None:
        if not self._attempt_commit_permitted(request):
            raise StaleAttemptError("R7 run/attempt/profile commit CAS rejected terminal result")
        super()._complete_durable_attempt(request, result)

    def cancel(self, attempt_id: str) -> bool:
        # The accepted R6 print adapter is one-shot and explicitly reports
        # cancel as unsupported.  Never claim that a local flag cancelled it.
        return False


# Compatibility aliases make the seam discoverable without creating another
# runtime implementation or another lifecycle authority.
R7HarnessCapabilityRuntime = HarnessCapabilityRuntime
CapabilityRuntimeBridge = HarnessCapabilityRuntime
R7ProfileReceiptBridge = ProfileReceiptBridge
ProfileBridge = ProfileReceiptBridge
build_r7_profile_receipt_bridge = build_profile_receipt_bridge
bridge_r6_profile_to_r1 = build_profile_receipt_bridge
cas_renew_inflight_lease = renew_inflight_lease


__all__ = [
    "BRIDGE_SCHEMA_VERSION",
    "PREFLIGHT_DIAGNOSIS_SCHEMA_VERSION",
    "INFLIGHT_CONTROL_TABLE",
    "INFLIGHT_LEASE_SECONDS",
    "INFLIGHT_RENEW_INTERVAL_SECONDS",
    "HarnessRuntimeError",
    "ProfileBridgeError",
    "PreflightRequiredError",
    "PreflightFailedError",
    "InflightLeaseError",
    "ProfileReceiptBridge",
    "R7ProfileReceiptBridge",
    "ProfileBridge",
    "PreflightDiagnosis",
    "HarnessCapabilityRuntime",
    "R7HarnessCapabilityRuntime",
    "CapabilityRuntimeBridge",
    "build_r1_execution_profile",
    "build_profile_receipt_bridge",
    "build_r6_prompt",
    "build_receipt_prompt",
    "classify_r6_receipt",
    "classify_receipt",
    "build_r7_profile_receipt_bridge",
    "bridge_r6_profile_to_r1",
    "bridge_from_run_binding",
    "build_preflight_diagnosis",
    "persist_preflight_diagnosis",
    "persist_profile_receipt_bridge",
    "inflight_lease_valid",
    "renew_inflight_lease",
    "cas_renew_inflight_lease",
]
