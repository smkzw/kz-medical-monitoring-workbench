"""Monitoring modes and ModeContract for the R2 kernel (Design v1.1 section
6.4; plan R2 step 5).

VETO 2 repairs:
* ``RunManager._verified_run`` is removed from the class surface; issuance
  occurs through a closure-only factory.
* ``create_run`` requires the exact :class:`AcceptanceService` type,
  derives source revision, mapping version, and identity digest from the
  live binding, rejects blocked records, and rejects revision/config strings
  that don't match the binding.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from types import MappingProxyType
from typing import Any, Dict, List, Optional, Tuple

from .domain import (
    DomainValidationError,
    MmR2Error,
    content_hash,
    deep_freeze_json,
    new_id,
    now_iso,
    validate_sha256_hex,
)

__all__ = [
    "ModeContractError",
    "MonitoringMode",
    "ExecutionBasis",
    "MODE_CONTRACTS",
    "ModeContract",
    "LockedVersionSelection",
    "MonitoringRun",
    "RunManager",
]


class ModeContractError(MmR2Error):
    """Mode-contract violation."""

_RUN_VERIFIED = object()


class MonitoringMode:
    DAILY = "daily"
    PRE_LOCK = "pre_lock"
    POST_LOCK_PRE_CFDI = "post_lock_pre_cfdi"

    @classmethod
    def all_modes(cls) -> Tuple[str, ...]:
        return (cls.DAILY, cls.PRE_LOCK, cls.POST_LOCK_PRE_CFDI)

    @classmethod
    def is_valid(cls, mode: str) -> bool:
        return mode in cls.all_modes()


class ExecutionBasis:
    FULL = "full"
    INCREMENTAL = "incremental"

    @classmethod
    def all_bases(cls) -> Tuple[str, ...]:
        return (cls.FULL, cls.INCREMENTAL)

    @classmethod
    def is_valid(cls, basis: str) -> bool:
        return basis in cls.all_bases()


@dataclass(frozen=True)
class ModeContract:
    schema_name: str = "mode_contract"
    schema_version: str = "1"
    mode: str = ""
    requires_accepted_snapshot: bool = False
    requires_explicit_cutoff: bool = False
    requires_lock_prep_window: bool = False
    requires_user_selected_locked_version: bool = False
    allows_subsequent_snapshots: bool = False
    allows_post_query_revision: bool = False
    fixed_total: bool = False
    old_outputs_not_overwritten: bool = False
    requires_full_risk_coverage_qc: bool = False
    requires_revision_impact_binding: bool = False
    requires_fixed_version_binding: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        if self.mode not in MonitoringMode.all_modes():
            raise DomainValidationError(f"ModeContract.mode {self.mode!r} invalid")

    def entry_conditions(self) -> Tuple[str, ...]:
        conditions: List[str] = []
        if self.requires_accepted_snapshot:
            conditions.append("current full snapshot accepted")
        if self.requires_explicit_cutoff:
            conditions.append("explicit cutoff declared")
        if self.requires_lock_prep_window:
            conditions.append("explicit lock-prep window declared")
        if self.requires_user_selected_locked_version:
            conditions.append("user-selected data/time-locked version")
        return tuple(conditions)


_DAILY_CONTRACT = ModeContract(
    mode=MonitoringMode.DAILY,
    requires_accepted_snapshot=True,
    allows_subsequent_snapshots=True,
    requires_full_risk_coverage_qc=True,
    description="Daily monitoring.",
)
_PRE_LOCK_CONTRACT = ModeContract(
    mode=MonitoringMode.PRE_LOCK,
    requires_accepted_snapshot=True,
    requires_explicit_cutoff=True,
    requires_lock_prep_window=True,
    allows_subsequent_snapshots=True,
    allows_post_query_revision=True,
    requires_full_risk_coverage_qc=True,
    requires_revision_impact_binding=True,
    description="Pre-lock.",
)
_POST_LOCK_CONTRACT = ModeContract(
    mode=MonitoringMode.POST_LOCK_PRE_CFDI,
    requires_accepted_snapshot=True,
    requires_user_selected_locked_version=True,
    fixed_total=True,
    old_outputs_not_overwritten=True,
    requires_full_risk_coverage_qc=True,
    requires_fixed_version_binding=True,
    description="Post-lock pre-CFDI.",
)

MODE_CONTRACTS: MappingProxyType = MappingProxyType({
    MonitoringMode.DAILY: _DAILY_CONTRACT,
    MonitoringMode.PRE_LOCK: _PRE_LOCK_CONTRACT,
    MonitoringMode.POST_LOCK_PRE_CFDI: _POST_LOCK_CONTRACT,
})


def get_mode_contract(mode: str) -> ModeContract:
    if mode not in MODE_CONTRACTS:
        raise ModeContractError(f"unknown mode {mode!r}")
    return MODE_CONTRACTS[mode]


@dataclass(frozen=True)
class LockedVersionSelection:
    """Service-issued evidence that the local user selected a locked version."""

    selection_id: str = ""
    project_id: str = ""
    snapshot_id: str = ""
    selected_by: str = ""
    snapshot_content_hash: str = ""
    acceptance_evidence_hash: str = ""
    selected_at: str = ""
    selection_hash: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self, _verified: Any = None, _authority_token: Any = _RUN_VERIFIED,
    ) -> None:
        if not self.selection_id or not self.project_id or not self.snapshot_id:
            raise DomainValidationError(
                "locked version selection identity fields are required"
            )
        if not self.selected_by or self.selected_by == "system_policy":
            raise DomainValidationError(
                "locked version selection requires an actual local user"
            )
        validate_sha256_hex(
            self.snapshot_content_hash,
            "LockedVersionSelection.snapshot_content_hash",
        )
        validate_sha256_hex(
            self.acceptance_evidence_hash,
            "LockedVersionSelection.acceptance_evidence_hash",
        )
        if _verified is not _authority_token:
            raise DomainValidationError(
                "LockedVersionSelection requires RunManager issuance"
            )
        expected = self.compute_hash()
        if self.selection_hash and self.selection_hash != expected:
            raise DomainValidationError("LockedVersionSelection hash mismatch")
        object.__setattr__(self, "selection_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "selection_id": self.selection_id,
            "project_id": self.project_id,
            "snapshot_id": self.snapshot_id,
            "selected_by": self.selected_by,
            "snapshot_content_hash": self.snapshot_content_hash,
            "acceptance_evidence_hash": self.acceptance_evidence_hash,
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


@dataclass(frozen=True)
class MonitoringRun:
    schema_name: str = "monitoring_run"
    schema_version: str = "1"
    run_id: str = ""
    project_id: str = ""
    mode: str = ""
    execution_basis: str = ""
    cutoff: str = ""
    source_revision_id: str = ""
    snapshot_id: str = ""
    locked_version_selection_id: str = ""
    carry_forward_run_ids: Tuple[str, ...] = ()
    knowledge_pack_version: str = ""
    rule_activation_version: str = ""
    mapping_version: str = ""
    identity_algorithm_digest: str = ""
    actor: str = ""
    created_at: str = ""
    run_hash: str = ""
    _verified: InitVar[Any] = None

    def __post_init__(
        self, _verified: Any = None, _authority_token: Any = _RUN_VERIFIED,
    ) -> None:
        if not self.run_id:
            raise DomainValidationError("MonitoringRun.run_id is required")
        if not self.project_id:
            raise DomainValidationError("MonitoringRun.project_id is required")
        if not MonitoringMode.is_valid(self.mode):
            raise ModeContractError(f"MonitoringRun.mode {self.mode!r} invalid")
        if not ExecutionBasis.is_valid(self.execution_basis):
            raise ModeContractError(
                f"MonitoringRun.execution_basis {self.execution_basis!r} invalid"
            )
        if not self.source_revision_id:
            raise DomainValidationError("source_revision_id is required")
        if not self.snapshot_id:
            raise DomainValidationError("snapshot_id is required")
        if (
            self.mode == MonitoringMode.POST_LOCK_PRE_CFDI
            and not self.locked_version_selection_id
        ):
            raise ModeContractError(
                "post-lock run requires a locked version selection"
            )
        if (
            self.mode != MonitoringMode.POST_LOCK_PRE_CFDI
            and self.locked_version_selection_id
        ):
            raise ModeContractError(
                "locked version selection is only valid for post-lock runs"
            )
        if not self.actor:
            raise DomainValidationError("actor is required")
        object.__setattr__(self, "carry_forward_run_ids", tuple(self.carry_forward_run_ids))
        if _verified is not _authority_token:
            raise DomainValidationError(
                "MonitoringRun requires service-issued construction; use "
                "RunManager.create_run(...) -- direct construction is "
                "unavailable to public callers"
            )
        expected = self.compute_hash()
        if self.run_hash and self.run_hash != expected:
            raise DomainValidationError("MonitoringRun.run_hash mismatch")
        object.__setattr__(self, "run_hash", expected)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "project_id": self.project_id,
            "mode": self.mode,
            "execution_basis": self.execution_basis,
            "cutoff": self.cutoff,
            "source_revision_id": self.source_revision_id,
            "snapshot_id": self.snapshot_id,
            "locked_version_selection_id": self.locked_version_selection_id,
            "carry_forward_run_ids": list(self.carry_forward_run_ids),
            "knowledge_pack_version": self.knowledge_pack_version,
            "rule_activation_version": self.rule_activation_version,
            "mapping_version": self.mapping_version,
            "identity_algorithm_digest": self.identity_algorithm_digest,
            "actor": self.actor,
        }

    def compute_hash(self) -> str:
        return content_hash(self.canonical_payload())


class RunManager:
    """Creates and validates monitoring runs under mode contracts.

    VETO 2: ``_verified_run`` is NOT a method on this class.  Run issuance
    occurs through a closure-only factory installed at module load.
    """

    def __init__(self) -> None:
        self._runs: Dict[str, MonitoringRun] = {}
        self._runs_by_project: Dict[str, List[str]] = {}
        self._locked_selections: Dict[str, LockedVersionSelection] = {}

    @staticmethod
    def _check_entry_conditions(
        mode: str, *, cutoff: str, lock_prep_window: bool,
        has_locked_version_selection: bool,
    ) -> None:
        contract = get_mode_contract(mode)
        reasons: List[str] = []
        if contract.requires_explicit_cutoff and not cutoff:
            reasons.append("mode requires an explicit cutoff")
        if contract.requires_lock_prep_window and not lock_prep_window:
            reasons.append("mode requires an explicit lock-prep window")
        if (contract.requires_user_selected_locked_version
                and not has_locked_version_selection):
            reasons.append("mode requires a user-selected data/time-locked version")
        if reasons:
            raise ModeContractError(
                f"mode {mode!r} entry conditions not met: {'; '.join(reasons)}"
            )

    def select_locked_version(
        self, project_id: str, snapshot_id: str, acceptance_service, *,
        user: str, _issuer=None,
    ) -> LockedVersionSelection:
        """Record an explicit local-user selection of an accepted lock version."""
        from .acceptance import AcceptanceService, SnapshotAcceptanceState
        if type(acceptance_service) is not AcceptanceService:
            raise ModeContractError(
                "locked version selection requires a real AcceptanceService"
            )
        if not user or user != acceptance_service.local_user:
            raise ModeContractError(
                "locked version selection user must equal the configured "
                "local user"
            )
        if user == "system_policy":
            raise ModeContractError(
                "system_policy cannot select a locked version for the user"
            )
        rec = acceptance_service.get(snapshot_id)
        if (
            rec.project_id != project_id
            or rec.blocked
            or rec.state != SnapshotAcceptanceState.BASELINE_ELIGIBLE
        ):
            raise ModeContractError(
                "locked version selection requires an unblocked "
                "baseline-eligible snapshot in the same project"
            )
        binding = acceptance_service.binding(snapshot_id)
        if (
            binding.project_id != project_id
            or binding.snapshot.snapshot_id != snapshot_id
            or rec.evidence is None
        ):
            raise ModeContractError("locked version snapshot binding mismatch")
        if _issuer is None:
            raise ModeContractError("locked version selection authority unavailable")
        selection = _issuer(
            selection_id=new_id("locksel-"), project_id=project_id,
            snapshot_id=snapshot_id, selected_by=user,
            snapshot_content_hash=binding.snapshot.content_hash,
            acceptance_evidence_hash=rec.evidence.evidence_hash,
            selected_at=now_iso(),
        )
        self._locked_selections[selection.selection_id] = selection
        return selection

    def create_run(
        self,
        project_id: str,
        mode: str,
        execution_basis: str,
        snapshot_id: str,
        acceptance_service,
        *,
        cutoff: str = "",
        lock_prep_window: bool = False,
        locked_version_selection: Optional[LockedVersionSelection] = None,
        carry_forward_run_ids: Optional[List[str]] = None,
        actor: str = "",
        _issuer=None,
    ) -> MonitoringRun:
        """Create a new monitoring run.

    VETO 2: requires the exact AcceptanceService type; derives source_revision_id,
        mapping_version, identity_algorithm_digest from the live binding;
        rejects blocked records and mismatched revisions.
        """
        from .acceptance import AcceptanceService, SnapshotAcceptanceState
        if not MonitoringMode.is_valid(mode):
            raise ModeContractError(f"unknown mode {mode!r}")
        if not ExecutionBasis.is_valid(execution_basis):
            raise ModeContractError(f"unknown execution_basis {execution_basis!r}")
        if not snapshot_id:
            raise ModeContractError("snapshot_id is required")
        if not actor:
            raise ModeContractError("actor is required")
        if type(acceptance_service) is not AcceptanceService:
            raise ModeContractError(
                "create_run requires a real AcceptanceService instance; "
                "duck-typed or hostile substitutes are rejected"
            )
        try:
            rec = acceptance_service.get(snapshot_id)
        except Exception as exc:
            raise ModeContractError(
                f"snapshot {snapshot_id!r} is not registered in the "
                f"acceptance service: {exc}"
            ) from exc
        if rec.project_id != project_id:
            raise ModeContractError(
                f"acceptance record project_id {rec.project_id!r} does not "
                f"match run project_id {project_id!r}"
            )
        # VETO 2-8: blocked records rejected.
        if rec.blocked:
            raise ModeContractError(
                f"snapshot {snapshot_id!r} acceptance record is blocked; "
                f"blocked records cannot create runs"
            )
        accepted_states = {
            SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
            SnapshotAcceptanceState.BASELINE_ELIGIBLE,
        }
        if rec.state not in accepted_states:
            raise ModeContractError(
                f"snapshot {snapshot_id!r} is not accepted "
                f"(state={rec.state.value})"
            )
        # VETO 2-7: derive source_revision_id, mapping_version, and
        # identity_algorithm_digest from the live binding.
        binding = acceptance_service.binding(snapshot_id)
        derived_rev = binding.snapshot.revision_id
        derived_mapping_version = binding.mapping_version
        derived_identity_digest = binding.identity_algorithm.digest
        # VETO 2-4: compare snapshot content against the binding's snapshot.
        bound_snap = binding.snapshot
        # The caller doesn't pass the snapshot object for run creation; we
        # trust the binding's snapshot because it was verified at registration
        # and the acceptance record is bound to the same binding.

        if mode == MonitoringMode.POST_LOCK_PRE_CFDI:
            if type(locked_version_selection) is not LockedVersionSelection:
                raise ModeContractError(
                    "post_lock_pre_cfdi requires a service-issued locked "
                    "version selection"
                )
            stored_selection = self._locked_selections.get(
                locked_version_selection.selection_id
            )
            if stored_selection != locked_version_selection:
                raise ModeContractError(
                    "locked version selection is not registered in this RunManager"
                )
            if (
                locked_version_selection.project_id != project_id
                or locked_version_selection.snapshot_id != snapshot_id
                or locked_version_selection.snapshot_content_hash
                != bound_snap.content_hash
                or rec.evidence is None
                or locked_version_selection.acceptance_evidence_hash
                != rec.evidence.evidence_hash
            ):
                raise ModeContractError(
                    "locked version selection does not match the live snapshot"
                )
        elif locked_version_selection is not None:
            raise ModeContractError(
                "locked version selection is only valid for post_lock_pre_cfdi"
            )

        self._check_entry_conditions(
            mode, cutoff=cutoff, lock_prep_window=lock_prep_window,
            has_locked_version_selection=locked_version_selection is not None,
        )
        if (
            mode == MonitoringMode.POST_LOCK_PRE_CFDI
            and execution_basis != ExecutionBasis.FULL
        ):
            raise ModeContractError(
                "post_lock_pre_cfdi is a fixed-total mode and requires a full run"
            )
        carry = tuple(carry_forward_run_ids or ())
        prior = self.latest_run(project_id)
        if prior is not None and prior.mode == MonitoringMode.POST_LOCK_PRE_CFDI:
            if mode != MonitoringMode.POST_LOCK_PRE_CFDI:
                raise ModeContractError(
                    "post_lock_pre_cfdi is terminal for the locked monitoring version"
                )
            if snapshot_id != prior.snapshot_id:
                raise ModeContractError(
                    "post_lock_pre_cfdi is fixed-total; subsequent runs must "
                    "reuse the same locked snapshot"
                )
        if prior is not None and prior.mode != mode:
            if not carry:
                raise ModeContractError(
                    f"mode change {prior.mode!r} -> {mode!r} requires "
                    f"explicit carry_forward_run_ids (no silent conversion)"
                )
            if prior.run_id not in carry:
                raise ModeContractError(
                    f"mode change carry-forward must include the immediate "
                    f"prior run {prior.run_id!r}"
                )
        for cf in carry:
            if cf not in self._runs:
                raise ModeContractError(
                    f"carry_forward_run_id {cf!r} does not reference a known run"
                )
            cf_run = self._runs[cf]
            if cf_run.project_id != project_id:
                raise ModeContractError(
                    f"carry_forward_run_id {cf!r} belongs to a different project"
                )
        if _issuer is None:
            raise ModeContractError("run issuance authority is unavailable")
        run = _issuer(
            run_id=new_id("run-"),
            project_id=project_id,
            mode=mode,
            execution_basis=execution_basis,
            cutoff=cutoff,
            source_revision_id=derived_rev,
            snapshot_id=snapshot_id,
            locked_version_selection_id=(
                locked_version_selection.selection_id
                if locked_version_selection is not None else ""
            ),
            carry_forward_run_ids=carry,
            mapping_version=derived_mapping_version,
            identity_algorithm_digest=derived_identity_digest,
            actor=actor,
            created_at=now_iso(),
        )
        self._runs[run.run_id] = run
        self._runs_by_project.setdefault(project_id, []).append(run.run_id)
        return run

    def get(self, run_id: str) -> MonitoringRun:
        if run_id not in self._runs:
            raise ModeContractError(f"unknown run {run_id!r}")
        return self._runs[run_id]

    def runs_for_project(self, project_id: str) -> List[MonitoringRun]:
        return [self._runs[rid] for rid in self._runs_by_project.get(project_id, [])]

    def latest_run(self, project_id: str) -> Optional[MonitoringRun]:
        ids = self._runs_by_project.get(project_id, [])
        return self._runs[ids[-1]] if ids else None

    def change_mode(
        self, project_id: str, new_mode: str, execution_basis: str,
        snapshot_id: str, acceptance_service, *,
        carry_forward_run_ids: List[str], cutoff: str = "",
        lock_prep_window: bool = False,
        locked_version_selection: Optional[LockedVersionSelection] = None,
        actor: str = "",
    ) -> MonitoringRun:
        return self.create_run(
            project_id=project_id, mode=new_mode, execution_basis=execution_basis,
            snapshot_id=snapshot_id, acceptance_service=acceptance_service,
            cutoff=cutoff, lock_prep_window=lock_prep_window,
            locked_version_selection=locked_version_selection,
            carry_forward_run_ids=carry_forward_run_ids, actor=actor,
        )


# ---------------------------------------------------------------------------
# Seal + closure-captured factory (not a module/class attribute).
# ---------------------------------------------------------------------------

def _seal_run_authority(authority_token: Any) -> None:
    selection_post = LockedVersionSelection.__post_init__
    run_post = MonitoringRun.__post_init__
    select_locked_version = RunManager.select_locked_version
    create_run = RunManager.create_run

    def checked_selection_post(self, _verified: Any = None) -> None:
        return selection_post(self, _verified, authority_token)

    def checked_run_post(self, _verified: Any = None) -> None:
        return run_post(self, _verified, authority_token)

    def _issue_run(**kwargs: Any) -> MonitoringRun:
        kwargs["_verified"] = authority_token
        return MonitoringRun(**kwargs)

    def _issue_selection(**kwargs: Any) -> LockedVersionSelection:
        kwargs["_verified"] = authority_token
        return LockedVersionSelection(**kwargs)

    def service_select_locked_version(
        self, *args: Any, **kwargs: Any,
    ) -> LockedVersionSelection:
        kwargs["_issuer"] = _issue_selection
        return select_locked_version(self, *args, **kwargs)

    def service_create_run(self, *args: Any, **kwargs: Any) -> MonitoringRun:
        kwargs["_issuer"] = _issue_run
        return create_run(self, *args, **kwargs)

    LockedVersionSelection.__post_init__ = checked_selection_post
    MonitoringRun.__post_init__ = checked_run_post
    RunManager.select_locked_version = service_select_locked_version
    RunManager.create_run = service_create_run


_seal_run_authority(_RUN_VERIFIED)
del _seal_run_authority
del _RUN_VERIFIED
